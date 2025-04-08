> 文章思路来源：[https://www.jianshu.com/p/68e8144fe068](https://www.jianshu.com/p/68e8144fe068)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1UysHWV8TCfyXvl7gQbuXaA](https://pan.baidu.com/s/1UysHWV8TCfyXvl7gQbuXaA)  密码: ih6n
>
> --来自百度网盘超级会员V3的分享
>

若修改__malloc_hook和__free_hook的内容，就会在malloc或free的时候执行其中的内容（函数）。

但是在前面的文章中并没有细说，这片文章就来说一下这些。

# Linux环境
来看一下我本机的Linux环境：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605774840688-2835c669-67f2-4252-b07c-82d35ab21b3f.png)

> 图中的工具见之前的文章。
>

Ubuntu 16.04.7、libc版本为2.23。

# Demo1--__free_hook
首先看一下glibc中__free_hook源码（libc版本为2.23）：

```c
#malloc.c中第1851-1852行
void weak_variable (*__free_hook) (void *__ptr,
                                   const void *) = NULL;
#malloc.c中第2933-2948行
void
__libc_free (void *mem)
{
  mstate ar_ptr;
  mchunkptr p;                          /* chunk corresponding to mem */

  void (*hook) (void *, const void *)
    = atomic_forced_read (__free_hook);
  if (__builtin_expect (hook != NULL, 0))
    {
      (*hook)(mem, RETURN_ADDRESS (0));
      return;
    }

  if (mem == 0)                              /* free(0) has no effect */
    return;
```

上面是_free_hook的定义。也可以看出当__free_hook中的内容不为空时，就会去执行里面的地址。

下面是Demo1的源码

```c
// gcc -g -fno-stack-protector -z execstack -no-pie -z norelro __free_hook.c -o __free_hook

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

extern void (*__free_hook) (void *__ptr,const void *); //与上面__free_hook的定义相照应

int main()
{
    char *str = malloc(160);
    strcpy(str,"/bin/sh");
    printf("/bin/sh的地址为：0x%016X\n",str);
    printf("__free_hook的地址为：0x%016X\n",&__free_hook);
    printf("system函数的地址为：0x%016X\n",&system);
    // 劫持__free_hook
    __free_hook = system;

    free(str);
    return 0;
}

```

编译完成之后，试着来调试一下，首先对代码的第14行下断点，运行程序：

```c
ubuntu@ubuntu:~/Desktop/__malloc(__free)_hook$ gdb __free_hook 
GNU gdb (Ubuntu 7.11.1-0ubuntu1~16.5) 7.11.1
Copyright (C) 2016 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.  Type "show copying"
and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
<http://www.gnu.org/software/gdb/documentation/>.
For help, type "help".
Type "apropos word" to search for commands related to "word"...
pwndbg: loaded 192 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
Reading symbols from __free_hook...done.
pwndbg> b 14
Breakpoint 1 at 0x400643: file __free_hook.c, line 14.
pwndbg> r
Starting program: /home/ubuntu/Desktop/__malloc(__free)_hook/__free_hook 
/bin/sh的地址为：0x0000000000601010

Breakpoint 1, main () at __free_hook.c:14
14	    printf("__free_hook的地址为：0x%016X\n",&__free_hook);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
 RAX  0x29
 RBX  0x0
 RCX  0x7fffffd7
 RDX  0x7ffff7dd3780 (_IO_stdfile_1_lock) ◂— 0
 RDI  0x1
 RSI  0x1
 R8   0x0
 R9   0x29
 R10  0xa
 R11  0x246
 R12  0x400510 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffde40 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffdd60 —▸ 0x400690 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffdd50 —▸ 0x7fffffffde40 ◂— 0x1
 RIP  0x400643 (main+61) ◂— mov    esi, 0x600af0
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
 ► 0x400643 <main+61>     mov    esi, __free_hook@@GLIBC_2.2.5 <0x600af0>
   0x400648 <main+66>     mov    edi, 0x400738
   0x40064d <main+71>     mov    eax, 0
   0x400652 <main+76>     call   printf@plt <printf@plt>
 
   0x400657 <main+81>     mov    esi, system@plt <0x4004c0>
   0x40065c <main+86>     mov    edi, 0x400760
   0x400661 <main+91>     mov    eax, 0
   0x400666 <main+96>     call   printf@plt <printf@plt>
 
   0x40066b <main+101>    mov    qword ptr [rip + 0x20047a], 0x4004c0
   0x400676 <main+112>    mov    rax, qword ptr [rbp - 8]
   0x40067a <main+116>    mov    rdi, rax
───────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]───────────────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/__malloc(__free)_hook/__free_hook.c
    9 int main()
   10 {
   11     char *str = malloc(160);
   12     strcpy(str,"/bin/sh");
   13     printf("/bin/sh的地址为：0x%016X\n",str);
 ► 14     printf("__free_hook的地址为：0x%016X\n",&__free_hook);
   15     printf("system函数的地址为：0x%016X\n",&system);
   16     // 劫持__free_hook
   17     __free_hook = system;
   18 
   19     free(str);
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffdd50 —▸ 0x7fffffffde40 ◂— 0x1
01:0008│      0x7fffffffdd58 —▸ 0x601010 ◂— 0x68732f6e69622f /* '/bin/sh' */
02:0010│ rbp  0x7fffffffdd60 —▸ 0x400690 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffdd68 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffdd70 ◂— 0x1
05:0028│      0x7fffffffdd78 —▸ 0x7fffffffde48 —▸ 0x7fffffffe1df ◂— '/home/ubuntu/Desktop/__malloc(__free)_hook/__free_hook'
06:0030│      0x7fffffffdd80 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffdd88 —▸ 0x400606 (main) ◂— push   rbp
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0           400643 main+61
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

程序已经输出：“/bin/sh的地址为：0x0000000000601010”

看一下此时的堆内容

```c
pwndbg> x/200gx 0x601000
0x601000:	0x0000000000000000	0x00000000000000b1 #malloc_chunk
0x601010:	0x0068732f6e69622f	0x0000000000000000
    		#hs/nib/
......（省略内容均为空）
0x6010b0:	0x0000000000000000	0x0000000000000411 #malloc_buffer
0x6010c0:	0xe768732f6e69622f	0x809de5b09ce5849a
0x6010d0:	0x78309abcefbab8e4	0x3030303030303030
0x6010e0:	0x3031303130363030	0x000000000000000a
0x6010f0:	0x0000000000000000	0x0000000000000000
......（省略内容均为空）
0x6014c0:	0x0000000000000000	0x0000000000020b41 #top_chunk
......（省略内容均为空）
0x601630:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

malloc_chunk是malloc出来的堆空间，malloc_buffer是程序在向屏幕打印内容时所申请的空间，这里不用管它。

/bin/sh已经写入到了堆空间中。

此时的__free_hook为空：

```c
pwndbg> x/16gx &__free_hook
0x600af0 <__free_hook@@GLIBC_2.2.5>:	0x0000000000000000	0x0000000000000000
0x600b00:	0x0000000000000000	0x0000000000000000
0x600b10:	0x0000000000000000	0x0000000000000000
0x600b20:	0x0000000000000000	0x0000000000000000
0x600b30:	0x0000000000000000	0x0000000000000000
0x600b40:	0x0000000000000000	0x0000000000000000
0x600b50:	0x0000000000000000	0x0000000000000000
0x600b60:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

对代码第19行下断点，继续运行程序，程序会输出内容：

```c
pwndbg> c
Continuing.
__free_hook的地址为：0x0000000000600AF0
system函数的地址为：0x00000000004004C0
```

此时__free_hook：

```c
pwndbg> x/16gx &__free_hook
0x600af0 <__free_hook@@GLIBC_2.2.5>:	0x00000000004004c0	0x0000000000000000
    									#指向system函数
0x600b00:	0x0000000000000000	0x0000000000000000
0x600b10:	0x0000000000000000	0x0000000000000000
0x600b20:	0x0000000000000000	0x0000000000000000
0x600b30:	0x0000000000000000	0x0000000000000000
0x600b40:	0x0000000000000000	0x0000000000000000
0x600b50:	0x0000000000000000	0x0000000000000000
0x600b60:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

现在__free_hook中已经有“内容”了，并且这个“内容”指向system函数。

我们回头看一下__free_hook函数的定义：

```c
#malloc.c中第1851-1852行
void weak_variable (*__free_hook) (void *__ptr,
                                   const void *) = NULL;
```

第一个参数void *__ptr指向堆中“/bin/sh”

第二个参数const void *指向“system函数地址”

这两个参数准备好，当再次free任意的内容时就会触发__free_hook中的system函数，从而getshell。

# Demo2--__malloc_hook
和Demo1原理相同，这里就不细说了：

```c
// gcc -g -fno-stack-protector -z execstack -no-pie -z norelro __malloc_hook.c -o __malloc_hook

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

extern void (*__malloc_hook) (size_t __size, const void *);

int main()
{
    char *str = malloc(160);
    strcpy(str,"/bin/sh");
    printf("/bin/sh的地址为：0x%016X\n",str);
    printf("__malloc_hook的地址为：0x%016X\n",&__malloc_hook);
    printf("system函数的地址为：0x%016X\n",&system);
    // 劫持__malloc_hook
    __malloc_hook = system;

    malloc(str);
    return 0;
}
```

编译之后直接运行即可getshell。

# 疑难
> 以下疑难在ubuntu 16.04和ubuntu 18.04验证，其他Linux版本未知。
>
> 使用编译完成的__free_hook进行说明，__malloc_hook文件同样会造成以下情况。
>

## 疑难1--程序的内存分布
假若没有关闭ALSR，正常运行程序就会出现下面的情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605780976041-8e591408-a27d-41eb-8f4f-c76ce6c3893b.png)

从上面的图中可以看到：“/bin/sh”所在的堆地址是随机的。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605781041595-48343654-5050-4756-b05a-c0a79126f19e.png)

从上面可以看出，编译完成的两个文件是关闭PIE保护的。

使用gdb调试看一下内存分布，第一次调试：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605781177038-f482d981-be6a-40a0-95f6-899adb8af7a6.png)

第二次调试：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605781292283-5d9e48a2-4080-4ae4-93ca-ea386552ccd6.png)

可以看到在调试时，程序的堆地址并没有发生改变。

emmm...如果我关闭系统的ALSR呢？

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605781420064-c9133978-a761-4c3a-898c-9ca8bcae28af.png)

> 上图说明系统的ALSR已经关闭，重启会还原。
>

再次运行程序：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605781599419-e6231a80-ca0a-4977-b8b8-baf0f71a9c05.png)

关闭ASLR之后堆地址不在随机。

## 得出结论1
**<font style="color:#F5222D;">当randomize_va_space=2（ALSR全开启）时，且Linux可执行文件未开启PIE保护：</font>**

+ **<font style="color:#F5222D;">正常运行程序（包括root权限）：堆地址会随机化，代码段不会随机化</font>**
+ **<font style="color:#F5222D;">gdb调试程序</font>****<font style="color:#F5222D;">（包括root权限）</font>****<font style="color:#F5222D;">：程序的内存分布不会随机化</font>**

**<font style="color:#F5222D;">当randomize_va_space=0（ALSR未开启）时，</font>****<font style="color:#F5222D;">且Linux可执行文件未开启PIE保护：</font>**

+ **<font style="color:#F5222D;">正常运行程序</font>****<font style="color:#F5222D;">（包括root权限）</font>****<font style="color:#F5222D;">：堆地址不会随机化，代码段不会随机化</font>**
+ **<font style="color:#F5222D;">gdb调试程序</font>****<font style="color:#F5222D;">（包括root权限）</font>****<font style="color:#F5222D;">：程序的内存分布不会随机化</font>**

# 疑难2--pwndbg导致shell崩溃
使用pwndbg调试程序getshell时程序和gdb会崩溃退出，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605782134831-1c4f6b47-e1f4-4011-acc8-c99682c613f6.png)

> 未在网络中搜索到解决方案及发生原因。
>

而gdb中不会出现这种情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605782296836-8823540b-c35d-4a93-ae9c-30c9189890c8.png)

> 已排查：崩溃原因和root权限无关
>

暂不清楚这种情况是否影响所有第三方的gdb，如：peda-gdb、gef-gdb等



