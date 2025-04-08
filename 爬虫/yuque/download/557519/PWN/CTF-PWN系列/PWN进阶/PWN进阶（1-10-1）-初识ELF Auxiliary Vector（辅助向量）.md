> Auxiliary Vector（辅助向量）的简称为AUXV，为了方便在之后的文中统一称为AUXV；
>

# 简介
当一个ELF可执行文件被加载到内存中时，Linux内核需要向此程序传递一些信息如环境变量等；这里的辅助向量就是一种由内核向应用程序传递信息的方式。

# 引入
> 关闭系统的ALSR：echo 0 > /proc/sys/kernel/randomize_va_space
>

调试是一种虽麻烦但是一种很有用的方法，我们将如下的代码进行编译：

```c
#include<stdio.h>
int main(){
    printf("cyberangel\n");
    return 0;
}
```

> 为了凸显AUXV在之后的作用，这里选择在编译时保护全开：
>
> gcc -g -fstack-protector-all -z noexecstack -fPIE -pie -z now AUXV_test.c -O0 -o AUXV_test（-O0采用不优化编译）
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628660868409-4359182a-3c03-417d-87ae-28eb07a98ca1.png)

对代码的main下断点，开始调试后看一下此程序的AUXV：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628663661716-da9c876b-1cc8-447c-a79e-02fb10f55083.png)

乍一看好像没什么，这其中都存放着ELF装载时的信息， 但是其中的几条信息应该引起我们的注意，首先是AT_RANDOM：

```c
AT_RANDOM                0x7fffffffe519 ◂— 0x422d3fc9f0756b35
    25   AT_RANDOM            Address of 16 random bytes     0x7fffffffe519   
```

0x7fffffffe519地址存放的是一段随机数，说白了相当于程序的canary，在一些情况下可以用它来bypass canary：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628663690429-f7f89c3b-d60c-423c-ab47-54b3b1a8fa4f.png)

不过canary将AT_RANDOM的低1字节变为了\x00【防止利用打印函数（printf，puts等）进行泄露，它们遇到\x00会截断输出】。

还有一个需要注意的是AT_BASE：

```c
AT_BASE                  0x7ffff7dd3000 ◂— jg     0x7ffff7dd3047
7    AT_BASE              Base address of interpreter    0x7ffff7dd3000
```

AT_BASE和AT_SYSINFO_EHDR分别代表的是ld-2.27.so的代码段基址和vdso的基址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628662354720-fdcd82af-ba25-4bf1-81de-cd20d5cd381c.png)

AT_PHDR表示Program headers的起始地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628750101440-41159046-eea1-48f1-b619-87dab5c4557f.png)

AT_ENTRY表示程序的入口点地址（_start）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628750197286-ab18d789-1e15-4e4d-983a-8fe33d8813b7.png)

# AUXV所处位置
**AUXV的位置在stack上，所以它的信息是可以修改的；**为了方便描述AUXV所处的位置，这里还需要了解一下main函数的参数，在gdb中输入bt以查看栈帧：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628746302217-e3480c74-6239-44b5-927d-e9470012e9fc.png)

如上图所示，可以看到对main函数传入了两个参数，分别是argc和argv，但实际上main函数可以拥有三个参数：argc、argv、envp：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628746325894-9dccd5af-f498-40af-99e7-4257316c044f.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628746607859-9c58def2-7f53-466b-9b08-9f08320eb0a0.png)

广义上main函数的定义如下：

```c
int main( int argc, char *argv[], char *envp[] )==int main( int argc, char **argv, char *envp[] )
```

3个参数的作用分别如下；

+ argc（arguments count，参数计数）：表示传给main函数的参数总个数，当argc==1时表示传入argv的只有程序的名称；上面程序中的argv指针数组就只有/root/AUXV/AUXV_test这一个元素。
+ argv（arguments value/vector，参数值）：表示传给main函数的参数，其中每个元素代表一个参数，参数与参数之间使用\x00分隔。
+ envp：表示传入main函数的系统环境变量，这个很少用到。

并且如果我们选择不向main函数中传递参数或少传递也是可以的：

```c
int main();
int main(int argc, char *argv[]);
```

因为C语言的参数是有调用者压入栈的，是否使用这些参数是被调用者的事情，用或不用都和调用者没关系。接下来寻找一下AUXV的位置：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628746474468-a697dec2-3634-47c1-a9d9-b18670248cf4.png)

经核对，AUXV处于envp的正下方：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628746801076-2ce6a77c-ec46-4b12-9ed9-99cccb7640a0.png)

可以使用如下图片来概括一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628746930517-ced09a91-afb7-414f-93b1-c99cd55abb3a.png)

当然还有一种无需进入gdb的查看方式，但是只能查看成员所在的地址而无法查看某些成员的值：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628749196229-5db89c35-03f6-43fd-9c26-856259ffe5df.png)

# AUXV的定义
AUXV是由一系列ElfN_auxv_t构成，它定义在glibc-2.27/elf/elf.h中：

```c
/* Auxiliary vector.  */

/* This vector is normally only used by the program interpreter.  The
   usual definition in an ABI supplement uses the name auxv_t.  The
   vector is not usually defined in a standard <elf.h> file, but it
   can't hurt.  We rename it to avoid conflicts.  The sizes of these
   types are an arrangement between the exec server and the program
   interpreter, so we don't fully specify them here.  */

typedef struct
{
  uint32_t a_type;		/* Entry type */
  union
    {
      uint32_t a_val;		/* Integer value */
      /* We use to have pointer elements added here.  We cannot do that,
	 though, since it does not work when using 32-bit definitions
	 on 64-bit platforms and vice versa.  */
    } a_un;
} Elf32_auxv_t;

typedef struct
{
  uint64_t a_type;		/* Entry type */
  union
    {
      uint64_t a_val;		/* Integer value */
      /* We use to have pointer elements added here.  We cannot do that,
	 though, since it does not work when using 32-bit definitions
	 on 64-bit platforms and vice versa.  */
    } a_un;
} Elf64_auxv_t;
```

可以看到32位和64位都是由一个a_type和一个共用体组成，其中a_type指定了辅助向量的类型，a_val为辅助向量的值；这些辅助向量定义在Linux系统上的/usr/include/linux/auxvec.h中（非glibc文件夹）：

```c
/* SPDX-License-Identifier: GPL-2.0 WITH Linux-syscall-note */
#ifndef _LINUX_AUXVEC_H
#define _LINUX_AUXVEC_H

#include <asm/auxvec.h>

/* Symbolic values for the entries in the auxiliary table
   put on the initial stack */
#define AT_NULL   0     /* end of vector */
#define AT_IGNORE 1     /* entry should be ignored */
#define AT_EXECFD 2     /* file descriptor of program */
#define AT_PHDR   3     /* program headers for program */
#define AT_PHENT  4     /* size of program header entry */
#define AT_PHNUM  5     /* number of program headers */
#define AT_PAGESZ 6     /* system page size */
#define AT_BASE   7     /* base address of interpreter */
#define AT_FLAGS  8     /* flags */
#define AT_ENTRY  9     /* entry point of program */
#define AT_NOTELF 10    /* program is not ELF */
#define AT_UID    11    /* real uid */
#define AT_EUID   12    /* effective uid */
#define AT_GID    13    /* real gid */
#define AT_EGID   14    /* effective gid */
#define AT_PLATFORM 15  /* string identifying CPU for optimizations */
#define AT_HWCAP  16    /* arch dependent hints at CPU capabilities */
#define AT_CLKTCK 17    /* frequency at which times() increments */
/* AT_* values 18 through 22 are reserved */
#define AT_SECURE 23   /* secure mode boolean */
#define AT_BASE_PLATFORM 24     /* string identifying real platform, may
                                 * differ from AT_PLATFORM. */
#define AT_RANDOM 25    /* address of 16 random bytes */
#define AT_HWCAP2 26    /* extension of AT_HWCAP */

#define AT_EXECFN  31   /* filename of program */


#endif /* _LINUX_AUXVEC_H */
```



