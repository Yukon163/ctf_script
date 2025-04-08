> 程序的编译和运行以及exp的攻击均在ubuntu 16.04进行
>
> 文中的图片部分以及行文思路来自：[https://blog.csdn.net/qq_41202237/article/details/108320408](https://blog.csdn.net/qq_41202237/article/details/108320408)
>
> 附件下载：
>
> 链接：[https://pan.baidu.com/s/1DOoLEGk4t9T2utXT8srMBg](https://pan.baidu.com/s/1DOoLEGk4t9T2utXT8srMBg)
>
> 提取码：sttw
>

# 漏洞利用的必要条件
chunk extend 是堆漏洞的一种常见利用手法，通过extend可以实现chunk overlapping（块重叠）的效果。这种利用方法需要以下的时机和条件：

+ **<font style="color:#F5222D;">程序中存在基于堆的漏洞</font>**
+ **<font style="color:#F5222D;">漏洞可以控制 chunk header 中的数据</font>**

## 基本示例 1：对 inuse 的 fastbin 进行 extend
源码如下：

```c
//gcc -g test1.c -o test1
#include<stdio.h>
int main(void){
    void *p, *q;
    p = malloc(0x10);//分配第一个0x10的chunk
    malloc(0x10);//分配第二个0x10的chunk
    *(long long *)((long long)p - 0x8) = 0x41;// 修改第一个块的size域
    free(p);
    q = malloc(0x30);// 实现extend，控制了第二个块的内容
    return 0;
}
```

编译一下，执行命令：“gcc -g test1.c -o test1”

再来看一下文件的保护：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600160078513-5b74ebe5-de10-48ef-b0d2-243f48778823.png)

由于在编译阶段我们使用了“-g”参数，因此可以在gdb调试的时候在任意行下断点。方法：b + 行号

### 在代码第8行下断点
进入gdb调试，在第8行下断点，然后运行：

```powershell
➜  Desktop gdb test1 
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
Reading symbols from test1...done.
pwndbg> b 8
Breakpoint 1 at 0x400586: file test1.c, line 8.
pwndbg> r
Starting program: /home/ubuntu/Desktop/test1 

Breakpoint 1, main () at test1.c:8
warning: Source file is more recent than executable.
8	    *(long long *)((long long)p - 0x8) = 0x41;// 修改第一个块的size域
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────────────[ REGISTERS ]──────────────────────────────────────────────
 RAX  0x602030 ◂— 0x0
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RDX  0x602030 ◂— 0x0
 RDI  0x0
 RSI  0x602040 ◂— 0x0
 R8   0x602000 ◂— 0x0
 R9   0xd
 R10  0x7ffff7dd1b78 (main_arena+88) —▸ 0x602040 ◂— 0x0
 R11  0x0
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf20 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
 RIP  0x400586 (main+32) ◂— mov    rax, qword ptr [rbp - 0x10]
───────────────────────────────────────────────[ DISASM ]────────────────────────────────────────────────
 ► 0x400586 <main+32>    mov    rax, qword ptr [rbp - 0x10]
   0x40058a <main+36>    sub    rax, 8
   0x40058e <main+40>    mov    qword ptr [rax], 0x41
   0x400595 <main+47>    mov    rax, qword ptr [rbp - 0x10]
   0x400599 <main+51>    mov    rdi, rax
   0x40059c <main+54>    call   free@plt <free@plt>
 
   0x4005a1 <main+59>    mov    edi, 0x30
   0x4005a6 <main+64>    call   malloc@plt <malloc@plt>
 
   0x4005ab <main+69>    mov    qword ptr [rbp - 8], rax
   0x4005af <main+73>    mov    eax, 0
   0x4005b4 <main+78>    leave  
────────────────────────────────────────────[ SOURCE (CODE) ]────────────────────────────────────────────
In file: /home/ubuntu/Desktop/test1.c
    3 int main(void)
    4 {
    5     void *p, *q;
    6     p = malloc(0x10);//分配第一个0x10的chunk
    7     malloc(0x10);//分配第二个0x10的chunk
 ►  8     *(long long *)((long long)p - 0x8) = 0x41;// 修改第一个块的size域
    9     free(p);
   10     q = malloc(0x30);// 实现extend，控制了第二个块的内容
   11     return 0;
   12 }
────────────────────────────────────────────────[ STACK ]────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
01:0008│      0x7fffffffde38 ◂— 0x0
02:0010│ rbp  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffde48 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffde50 ◂— 0x1
05:0028│      0x7fffffffde58 —▸ 0x7fffffffdf28 —▸ 0x7fffffffe2a1 ◂— '/home/ubuntu/Desktop/test1'
06:0030│      0x7fffffffde60 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffde68 —▸ 0x400566 (main) ◂— push   rbp
──────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────
 ► f 0           400586 main+32
   f 1     7ffff7a2d840 __libc_start_main+240
─────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

看一下堆段的起始地址：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600169378459-138daac6-38ca-4e5f-b1de-47d02ab0ff34.png)

从上图中可以看到，heap的起始地址为0x602000，查看堆段的内存地址：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600169738591-943ee30b-fb8d-47e1-83ac-46768bb2192e.png)

堆块的结构分为prev_size、size、user_data，拿上面这个64位的程序举例：

程序执行了malloc(0x10)，并且prev_size和size部分各占8个字节，而size记录的是整个堆块的大小，并且size的最后一位用来记录前一个块的状态，所以

堆块的总大小 = 0x8(prev_size) + 0x8(size) + 0x10(内容) + 0x1(标志位) = 0x21

> 具体详见下面这篇文章
>

[PWN入门（3-1-1）-堆入门概述](https://www.yuque.com/cyberangel/rg9gdm/uhdudz)

看一下指针p指向的地址，执行“info local”，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600170074289-2f0b62c0-5822-4195-bbc2-5ae895b84298.png)

可以看到，p指针指向了user_data的起始地址，chunk1和chunk2的范围在上图已经标出，这里不再细说。

### 在代码第9行下断点
在终端输入“b 9”，紧接着输入c继续执行代码

```powershell
pwndbg> b 9
Breakpoint 2 at 0x400595: file test1.c, line 9.
pwndbg> c
Continuing.

Breakpoint 2, main () at test1.c:9
9	    free(p);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────────────[ REGISTERS ]──────────────────────────────────────────────
*RAX  0x602008 ◂— 0x41 /* 'A' */
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RDX  0x602030 ◂— 0x0
 RDI  0x0
 RSI  0x602040 ◂— 0x0
 R8   0x602000 ◂— 0x0
 R9   0xd
 R10  0x7ffff7dd1b78 (main_arena+88) —▸ 0x602040 ◂— 0x0
 R11  0x0
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf20 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
*RIP  0x400595 (main+47) ◂— mov    rax, qword ptr [rbp - 0x10]
───────────────────────────────────────────────[ DISASM ]────────────────────────────────────────────────
   0x400586 <main+32>    mov    rax, qword ptr [rbp - 0x10]
   0x40058a <main+36>    sub    rax, 8
   0x40058e <main+40>    mov    qword ptr [rax], 0x41
 ► 0x400595 <main+47>    mov    rax, qword ptr [rbp - 0x10]
   0x400599 <main+51>    mov    rdi, rax
   0x40059c <main+54>    call   free@plt <free@plt>
 
   0x4005a1 <main+59>    mov    edi, 0x30
   0x4005a6 <main+64>    call   malloc@plt <malloc@plt>
 
   0x4005ab <main+69>    mov    qword ptr [rbp - 8], rax
   0x4005af <main+73>    mov    eax, 0
   0x4005b4 <main+78>    leave  
────────────────────────────────────────────[ SOURCE (CODE) ]────────────────────────────────────────────
In file: /home/ubuntu/Desktop/test1.c
    4 {
    5     void *p, *q;
    6     p = malloc(0x10);//分配第一个0x10的chunk
    7     malloc(0x10);//分配第二个0x10的chunk
    8     *(long long *)((long long)p - 0x8) = 0x41;// 修改第一个块的size域
 ►  9     free(p);
   10     q = malloc(0x30);// 实现extend，控制了第二个块的内容
   11     return 0;
   12 }
────────────────────────────────────────────────[ STACK ]────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
01:0008│      0x7fffffffde38 ◂— 0x0
02:0010│ rbp  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffde48 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffde50 ◂— 0x1
05:0028│      0x7fffffffde58 —▸ 0x7fffffffdf28 —▸ 0x7fffffffe2a1 ◂— '/home/ubuntu/Desktop/test1'
06:0030│      0x7fffffffde60 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffde68 —▸ 0x400566 (main) ◂— push   rbp
──────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────
 ► f 0           400595 main+47
   f 1     7ffff7a2d840 __libc_start_main+240
─────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

此时，程序已经执行了代码：*(long long *)((long long)p - 0x8) = 0x41，来看一下堆的内容：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600170930672-a7b42a2e-7df1-4df1-982c-29aff45dfbe1.png)

从上图中可以看出，chunk1的size已经变为了0x41，这是因为执行了*(long long *)((long long)p - 0x8) = 0x41，简单的说一下这行代码的意思：p指针指向的地址再减0x8的位置修改成0x41，也就是说chunk1的size从0x21被修改成0x41。整整扩大了32字节，chunk1与chunk2的范围如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600171299948-5849e1ee-ba2b-43d6-a17c-f66758bffc1a.png)

这一改不要紧，chunk1倒是乐呵了，自己的空间变大了 。但是chunk2就遭殃了，因为chunk1延展的空间正好是chunk2的空间，chunk2被chunk1包含占有了。

### 在第10行下断点
接下来我们把断点下在第10行b 10，然后运行程序：

```powershell
pwndbg> b 10
Breakpoint 3 at 0x4005a1: file test1.c, line 10.
pwndbg> c
Continuing.

Breakpoint 3, main () at test1.c:10
10	    q = malloc(0x30);// 实现extend，控制了第二个块的内容
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────────────[ REGISTERS ]──────────────────────────────────────────────
*RAX  0x0
 RBX  0x0
*RCX  0x7ffff7dd1b00 (__memalign_hook) —▸ 0x7ffff7a92ea0 (memalign_hook_ini) ◂— push   r12
*RDX  0x0
*RDI  0xffffffff
*RSI  0x7ffff7dd1b38 (main_arena+24) —▸ 0x602000 ◂— 0x0
*R8   0x602010 ◂— 0x0
*R9   0x0
*R10  0x8b8
*R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf20 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
*RIP  0x4005a1 (main+59) ◂— mov    edi, 0x30
───────────────────────────────────────────────[ DISASM ]────────────────────────────────────────────────
   0x40058a <main+36>    sub    rax, 8
   0x40058e <main+40>    mov    qword ptr [rax], 0x41
   0x400595 <main+47>    mov    rax, qword ptr [rbp - 0x10]
   0x400599 <main+51>    mov    rdi, rax
   0x40059c <main+54>    call   free@plt <free@plt>
 
 ► 0x4005a1 <main+59>    mov    edi, 0x30
   0x4005a6 <main+64>    call   malloc@plt <malloc@plt>
 
   0x4005ab <main+69>    mov    qword ptr [rbp - 8], rax
   0x4005af <main+73>    mov    eax, 0
   0x4005b4 <main+78>    leave  
   0x4005b5 <main+79>    ret    
────────────────────────────────────────────[ SOURCE (CODE) ]────────────────────────────────────────────
In file: /home/ubuntu/Desktop/test1.c
    5     void *p, *q;
    6     p = malloc(0x10);//分配第一个0x10的chunk
    7     malloc(0x10);//分配第二个0x10的chunk
    8     *(long long *)((long long)p - 0x8) = 0x41;// 修改第一个块的size域
    9     free(p);
 ► 10     q = malloc(0x30);// 实现extend，控制了第二个块的内容
   11     return 0;
   12 }
────────────────────────────────────────────────[ STACK ]────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
01:0008│      0x7fffffffde38 ◂— 0x0
02:0010│ rbp  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffde48 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffde50 ◂— 0x1
05:0028│      0x7fffffffde58 —▸ 0x7fffffffdf28 —▸ 0x7fffffffe2a1 ◂— '/home/ubuntu/Desktop/test1'
06:0030│      0x7fffffffde60 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffde68 —▸ 0x400566 (main) ◂— push   rbp
──────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────
 ► f 0           4005a1 main+59
   f 1     7ffff7a2d840 __libc_start_main+240
─────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

现在程序已经执行了free(p)，查看堆内容：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600171617524-46ad8d2b-f2ae-48a4-b649-bafacdbb778b.png)

再来看一下bin的内容：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600171904249-f79d5a11-ad8d-4f28-934e-9b050d99093c.png)

> 可以得出一个结论，free(指针)只是将目标的堆内存标记为释放状态，其内容并没有清空
>

在执行完free(p)后，chunk1与chunk2**<font style="color:#F5222D;">被合并成</font>**0x41的chunk放进了fastbin中。关于回收和重新分配堆内存，请移步至：

[PWN入门（3-1-1）-堆入门概述](https://www.yuque.com/cyberangel/rg9gdm/uhdudz)

### 在第11行下断点
最后执行一下 q = malloc(0x30)：

```powershell
pwndbg> b 11
Breakpoint 4 at 0x4005af: file test1.c, line 11.
pwndbg> c
Continuing.

Breakpoint 4, main () at test1.c:11
11	    return 0;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────────────[ REGISTERS ]──────────────────────────────────────────────
*RAX  0x602010 ◂— 0x0
 RBX  0x0
*RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x0
*RDX  0x602010 ◂— 0x0
*RDI  0x2
*RSI  0x7ffff7dd1b30 (main_arena+16) ◂— 0x0
*R8   0x0
 R9   0x0
 R10  0x8b8
 R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf20 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
*RIP  0x4005af (main+73) ◂— mov    eax, 0
───────────────────────────────────────────────[ DISASM ]────────────────────────────────────────────────
   0x400599       <main+51>                  mov    rdi, rax
   0x40059c       <main+54>                  call   free@plt <free@plt>
 
   0x4005a1       <main+59>                  mov    edi, 0x30
   0x4005a6       <main+64>                  call   malloc@plt <malloc@plt>
 
   0x4005ab       <main+69>                  mov    qword ptr [rbp - 8], rax
 ► 0x4005af       <main+73>                  mov    eax, 0
   0x4005b4       <main+78>                  leave  
   0x4005b5       <main+79>                  ret    
    ↓
   0x7ffff7a2d840 <__libc_start_main+240>    mov    edi, eax
   0x7ffff7a2d842 <__libc_start_main+242>    call   exit <exit>
 
   0x7ffff7a2d847 <__libc_start_main+247>    xor    edx, edx
────────────────────────────────────────────[ SOURCE (CODE) ]────────────────────────────────────────────
In file: /home/ubuntu/Desktop/test1.c
    6     p = malloc(0x10);//分配第一个0x10的chunk
    7     malloc(0x10);//分配第二个0x10的chunk
    8     *(long long *)((long long)p - 0x8) = 0x41;// 修改第一个块的size域
    9     free(p);
   10     q = malloc(0x30);// 实现extend，控制了第二个块的内容
 ► 11     return 0;
   12 }
────────────────────────────────────────────────[ STACK ]────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
... ↓
02:0010│ rbp  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffde48 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffde50 ◂— 0x1
05:0028│      0x7fffffffde58 —▸ 0x7fffffffdf28 —▸ 0x7fffffffe2a1 ◂— '/home/ubuntu/Desktop/test1'
06:0030│      0x7fffffffde60 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffde68 —▸ 0x400566 (main) ◂— push   rbp
──────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────
 ► f 0           4005af main+73
   f 1     7ffff7a2d840 __libc_start_main+240
─────────────────────────────────────────────────────────────────────────────────────────────────────────
```

查看堆内存及bin：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600172599575-3b2eadde-d13b-4c4e-b235-6513f3ee7180.png)

当我们重新申请申请一个大小为0x30的chunk时，fastbin中刚好有大小合适的chunk，这个时候**<font style="color:#F5222D;">chunk1与chunk2合并的新chunk1就会重新被启用</font>**，启用的同时原有chunk2中的内容也会连带着被启用，然后就可以直接通过这个新申请的块来对chunk2中的内容进行操作了.

## 基本示例 2：对 inuse 的 smallbin 进行 extend
源代码如下：

```c
//gcc -g test2.c -o test2
#include<stdio.h>
int main()
{首先在第9行下断点b 9，我们看一下申请完三个chunk之后内存中的样子：
    void *p, *q;
    p = malloc(0x80);//分配第一个 0x80 的chunk1
    malloc(0x10); //分配第二个 0x10 的chunk2
    malloc(0x10); //防止与top chunk合并
    *(long *)((long)p-0x8) = 0xb1;
    free(p);
    q = malloc(0xa0);
}
```

### 在第9行下断点
首先在第9行下断点，运行程序：

```powershell
➜  ~ cd Desktop/
➜  Desktop gdb test2  
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
Reading symbols from test2...done.
pwndbg> b 9
Breakpoint 1 at 0x400590: file test2.c, line 9.
pwndbg> r
Starting program: /home/ubuntu/Desktop/test2 

Breakpoint 1, main () at test2.c:9
9	    *(long *)((long)p-0x8) = 0xb1;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0x6020c0 ◂— 0x0
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RDX  0x6020c0 ◂— 0x0
 RDI  0x0
 RSI  0x6020d0 ◂— 0x0
 R8   0x602000 ◂— 0x0
 R9   0xd
 R10  0x7ffff7dd1b78 (main_arena+88) —▸ 0x6020d0 ◂— 0x0
 R11  0x0
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf20 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
 RIP  0x400590 (main+42) ◂— mov    rax, qword ptr [rbp - 0x10]
───────────────────────────────────[ DISASM ]───────────────────────────────────
 ► 0x400590 <main+42>    mov    rax, qword ptr [rbp - 0x10]
   0x400594 <main+46>    sub    rax, 8
   0x400598 <main+50>    mov    qword ptr [rax], 0xb1
   0x40059f <main+57>    mov    rax, qword ptr [rbp - 0x10]
   0x4005a3 <main+61>    mov    rdi, rax
   0x4005a6 <main+64>    call   free@plt <free@plt>
 
   0x4005ab <main+69>    mov    edi, 0xa0
   0x4005b0 <main+74>    call   malloc@plt <malloc@plt>
 
   0x4005b5 <main+79>    mov    qword ptr [rbp - 8], rax
   0x4005b9 <main+83>    mov    eax, 0
   0x4005be <main+88>    leave  
───────────────────────────────[ SOURCE (CODE) ]────────────────────────────────
In file: /home/ubuntu/Desktop/test2.c
    4 {
    5     void *p, *q;
    6     p = malloc(0x80);//分配第一个 0x80 的chunk1
    7     malloc(0x10); //分配第二个 0x10 的chunk2
    8     malloc(0x10); //防止与top chunk合并
 ►  9     *(long *)((long)p-0x8) = 0xb1;
   10     free(p);
   11     q = malloc(0xa0);
   12 }
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
01:0008│      0x7fffffffde38 ◂— 0x0
02:0010│ rbp  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffde48 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffde50 ◂— 0x1
05:0028│      0x7fffffffde58 —▸ 0x7fffffffdf28 —▸ 0x7fffffffe2a2 ◂— '/home/ubuntu/Desktop/test2'
06:0030│      0x7fffffffde60 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffde68 —▸ 0x400566 (main) ◂— push   rbp
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0           400590 main+42
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

看一下申请完三个chunk之后内存中的样子：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600173442992-8bef94ee-b187-42ab-82ee-bb29e6db9f89.png)

### 在第10行下断点
下断点之后，程序将会执行*(int *)((int)hollk-0x8) = 0xb1;这段代码

```powershell
pwndbg> b 10
Breakpoint 2 at 0x40059f: file test2.c, line 10.
pwndbg> c
Continuing.

Breakpoint 2, main () at test2.c:10
10	    free(p);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
*RAX  0x602008 ◂— 0xb1
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RDX  0x6020c0 ◂— 0x0
 RDI  0x0
 RSI  0x6020d0 ◂— 0x0
 R8   0x602000 ◂— 0x0
 R9   0xd
 R10  0x7ffff7dd1b78 (main_arena+88) —▸ 0x6020d0 ◂— 0x0
 R11  0x0
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf20 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
*RIP  0x40059f (main+57) ◂— mov    rax, qword ptr [rbp - 0x10]
───────────────────────────────────[ DISASM ]───────────────────────────────────
   0x400590 <main+42>    mov    rax, qword ptr [rbp - 0x10]
   0x400594 <main+46>    sub    rax, 8
   0x400598 <main+50>    mov    qword ptr [rax], 0xb1
 ► 0x40059f <main+57>    mov    rax, qword ptr [rbp - 0x10]
   0x4005a3 <main+61>    mov    rdi, rax
   0x4005a6 <main+64>    call   free@plt <free@plt>
 
   0x4005ab <main+69>    mov    edi, 0xa0
   0x4005b0 <main+74>    call   malloc@plt <malloc@plt>
 
   0x4005b5 <main+79>    mov    qword ptr [rbp - 8], rax
   0x4005b9 <main+83>    mov    eax, 0
   0x4005be <main+88>    leave  
───────────────────────────────[ SOURCE (CODE) ]────────────────────────────────
In file: /home/ubuntu/Desktop/test2.c
    5     void *p, *q;
    6     p = malloc(0x80);//分配第一个 0x80 的chunk1
    7     malloc(0x10); //分配第二个 0x10 的chunk2
    8     malloc(0x10); //防止与top chunk合并
    9     *(long *)((long)p-0x8) = 0xb1;
 ► 10     free(p);
   11     q = malloc(0xa0);
   12 }
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
01:0008│      0x7fffffffde38 ◂— 0x0
02:0010│ rbp  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffde48 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffde50 ◂— 0x1
05:0028│      0x7fffffffde58 —▸ 0x7fffffffdf28 —▸ 0x7fffffffe2a2 ◂— '/home/ubuntu/Desktop/test2'
06:0030│      0x7fffffffde60 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffde68 —▸ 0x400566 (main) ◂— push   rbp
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0           40059f main+57
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

看一下堆内存

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600174069801-bca6c679-696a-467e-be49-609153eb6d0f.png)

和前面的例子一样，*(int *)((int)hollk-0x8) = 0xb1;这段代码也是将chunk1的size部分进行了更改，将原有的0x90扩展到了0xb0。这就导致了chunk2被chunk1所包含。

### 在第11行下断点
下完断点运行程序，会执行代码free(p);

```powershell
pwndbg> b 11
Breakpoint 3 at 0x4005ab: file test2.c, line 11.
pwndbg> c
Continuing.

Breakpoint 3, main () at test2.c:11
11	    q = malloc(0xa0);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
*RAX  0x1
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
*RDX  0x0
*RDI  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
*RSI  0x0
 R8   0x602000 ◂— 0x0
*R9   0x1
*R10  0x8b8
*R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf20 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde30 —▸ 0x602010 —▸ 0x7ffff7dd1b78 (main_arena+88) —▸ 0x6020d0 ◂— 0x0
*RIP  0x4005ab (main+69) ◂— mov    edi, 0xa0
───────────────────────────────────[ DISASM ]───────────────────────────────────
   0x400594 <main+46>    sub    rax, 8
   0x400598 <main+50>    mov    qword ptr [rax], 0xb1
   0x40059f <main+57>    mov    rax, qword ptr [rbp - 0x10]
   0x4005a3 <main+61>    mov    rdi, rax
   0x4005a6 <main+64>    call   free@plt <free@plt>
 
 ► 0x4005ab <main+69>    mov    edi, 0xa0
   0x4005b0 <main+74>    call   malloc@plt <malloc@plt>
 
   0x4005b5 <main+79>    mov    qword ptr [rbp - 8], rax
   0x4005b9 <main+83>    mov    eax, 0
   0x4005be <main+88>    leave  
   0x4005bf <main+89>    ret    
───────────────────────────────[ SOURCE (CODE) ]────────────────────────────────
In file: /home/ubuntu/Desktop/test2.c
    6     p = malloc(0x80);//分配第一个 0x80 的chunk1
    7     malloc(0x10); //分配第二个 0x10 的chunk2
    8     malloc(0x10); //防止与top chunk合并
    9     *(long *)((long)p-0x8) = 0xb1;
   10     free(p);
 ► 11     q = malloc(0xa0);
   12 }
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffde30 —▸ 0x602010 —▸ 0x7ffff7dd1b78 (main_arena+88) —▸ 0x6020d0 ◂— 0x0
01:0008│      0x7fffffffde38 ◂— 0x0
02:0010│ rbp  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffde48 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffde50 ◂— 0x1
05:0028│      0x7fffffffde58 —▸ 0x7fffffffdf28 —▸ 0x7fffffffe2a2 ◂— '/home/ubuntu/Desktop/test2'
06:0030│      0x7fffffffde60 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffde68 —▸ 0x400566 (main) ◂— push   rbp
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0           4005ab main+69
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600174529043-508397b9-4ad0-4f44-9221-94511dbf200c.png)

看一下bin：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600174577837-7ced17be-8829-4131-b2fc-557b4306ac41.png)

这里解释一下为什么进的是unsortbin，有**<font style="color:#F5222D;">两种情况下进unsortbin</font>**：

+ 当一个较大的 chunk 被分割成两半后，如果剩下的部分大于 MINSIZE，就会被放到 unsorted bin 中
+ 释放一个不属于 fastbin 的 chunk，并且该 chunk 不和 top chunk 紧邻时，该 chunk 会被首先放到 unsorted bin 中

那么这个例子**<font style="color:#F5222D;">就满足第二种情况</font>**，不属于fastbin中的空闲块，并且不和top chunk相邻。其实这个例子和第一个例子差不多，因为chunk1和chunk2合并之后的chunk的大小超过了fast bin的最大接收值，所以不进fast bin，并且chunk3的size标志位变成了0，证明前一个块chunk2是一个释放的状态。**接下来的过程也是一样的，再次申请一个0xa0大小的chunk时，会从unsort bin中提取。连带着chunk2中的内容也会被提取出来，这样一来再次对chunk1进行操作，从而达到操作chunk2的目的。**

## 基本示例 3：对 free 的 smallbin 进行 extend
源代码如下：

```c
//gcc -g test3 -o test3
 #include<stdio.h>
 int main()
 {
    void *p, *q;
    p = malloc(0x80);//分配第一个0x80的chunk1
    malloc(0x10);//分配第二个0x10的chunk2
    free(p);//首先进行释放，使得chunk1进入unsorted bin
    *(long *)((long)p - 0x8) = 0xb1;
    q = malloc(0xa0);
}
```

第三个例子和前面两个有一些区别，前面两个都是先修改chunk1的size大小然后进行释放，但是这个例子是先进行释放，然后重新修改chunk1的size大小，依然还是一步一步来

### 在第8行下断点
下断点之后，然后运行程序：

```powershell
➜  Desktop gdb test3 
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
Reading symbols from test3...done.
pwndbg> b 8
Breakpoint 1 at 0x400586: file test3.c, line 8.
pwndbg> r
Starting program: /home/ubuntu/Desktop/test3 

Breakpoint 1, main () at test3.c:8
8	    free(p);//首先进行释放，使得chunk1进入unsorted bin
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0x6020a0 ◂— 0x0
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RDX  0x6020a0 ◂— 0x0
 RDI  0x0
 RSI  0x6020b0 ◂— 0x0
 R8   0x602000 ◂— 0x0
 R9   0xd
 R10  0x7ffff7dd1b78 (main_arena+88) —▸ 0x6020b0 ◂— 0x0
 R11  0x0
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf20 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
 RIP  0x400586 (main+32) ◂— mov    rax, qword ptr [rbp - 0x10]
───────────────────────────────────[ DISASM ]───────────────────────────────────
 ► 0x400586 <main+32>    mov    rax, qword ptr [rbp - 0x10]
   0x40058a <main+36>    mov    rdi, rax
   0x40058d <main+39>    call   free@plt <free@plt>
 
   0x400592 <main+44>    mov    rax, qword ptr [rbp - 0x10]
   0x400596 <main+48>    sub    rax, 8
   0x40059a <main+52>    mov    qword ptr [rax], 0xb1
   0x4005a1 <main+59>    mov    edi, 0xa0
   0x4005a6 <main+64>    call   malloc@plt <malloc@plt>
 
   0x4005ab <main+69>    mov    qword ptr [rbp - 8], rax
   0x4005af <main+73>    mov    eax, 0
   0x4005b4 <main+78>    leave  
───────────────────────────────[ SOURCE (CODE) ]────────────────────────────────
In file: /home/ubuntu/Desktop/test3.c
    3  int main()
    4  {
    5     void *p, *q;
    6     p = malloc(0x80);//分配第一个0x80的chunk1
    7     malloc(0x10);//分配第二个0x10的chunk2
 ►  8     free(p);//首先进行释放，使得chunk1进入unsorted bin
    9     *(long *)((long)p - 0x8) = 0xb1;
   10     q = malloc(0xa0);
   11 }
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffde30 —▸ 0x602010 ◂— 0x0
01:0008│      0x7fffffffde38 ◂— 0x0
02:0010│ rbp  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffde48 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffde50 ◂— 0x1
05:0028│      0x7fffffffde58 —▸ 0x7fffffffdf28 —▸ 0x7fffffffe2a2 ◂— '/home/ubuntu/Desktop/test3'
06:0030│      0x7fffffffde60 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffde68 —▸ 0x400566 (main) ◂— push   rbp
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0           400586 main+32
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

此时程序已经申请完堆空间，来看一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600218582490-8478ec71-fcb7-4b2b-8bea-522af3cd7d94.png)

### 在第9行下断点
下断点之后运行程序，使程序完成chunk1的释放：

```powershell
pwndbg> b 9
Breakpoint 2 at 0x400592: file test3.c, line 9.
pwndbg> c
Continuing.

Breakpoint 2, main () at test3.c:9
9	    *(long *)((long)p - 0x8) = 0xb1;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────────[ REGISTERS ]───────────────────────────────────────────
*RAX  0x1
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
*RDX  0x0
*RDI  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
*RSI  0x0
 R8   0x602000 ◂— 0x0
*R9   0x1
*R10  0x8b8
*R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf20 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde30 —▸ 0x602010 —▸ 0x7ffff7dd1b78 (main_arena+88) —▸ 0x6020b0 ◂— 0x0
*RIP  0x400592 (main+44) ◂— mov    rax, qword ptr [rbp - 0x10]
────────────────────────────────────────────[ DISASM ]────────────────────────────────────────────
   0x400586 <main+32>    mov    rax, qword ptr [rbp - 0x10]
   0x40058a <main+36>    mov    rdi, rax
   0x40058d <main+39>    call   free@plt <free@plt>
 
 ► 0x400592 <main+44>    mov    rax, qword ptr [rbp - 0x10]
   0x400596 <main+48>    sub    rax, 8
   0x40059a <main+52>    mov    qword ptr [rax], 0xb1
   0x4005a1 <main+59>    mov    edi, 0xa0
   0x4005a6 <main+64>    call   malloc@plt <malloc@plt>
 
   0x4005ab <main+69>    mov    qword ptr [rbp - 8], rax
   0x4005af <main+73>    mov    eax, 0
   0x4005b4 <main+78>    leave  
────────────────────────────────────────[ SOURCE (CODE) ]─────────────────────────────────────────
In file: /home/ubuntu/Desktop/test3.c
    4  {
    5     void *p, *q;
    6     p = malloc(0x80);//分配第一个0x80的chunk1
    7     malloc(0x10);//分配第二个0x10的chunk2
    8     free(p);//首先进行释放，使得chunk1进入unsorted bin
 ►  9     *(long *)((long)p - 0x8) = 0xb1;
   10     q = malloc(0xa0);
   11 }
────────────────────────────────────────────[ STACK ]─────────────────────────────────────────────
00:0000│ rsp  0x7fffffffde30 —▸ 0x602010 —▸ 0x7ffff7dd1b78 (main_arena+88) —▸ 0x6020b0 ◂— 0x0
01:0008│      0x7fffffffde38 ◂— 0x0
02:0010│ rbp  0x7fffffffde40 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffde48 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffde50 ◂— 0x1
05:0028│      0x7fffffffde58 —▸ 0x7fffffffdf28 —▸ 0x7fffffffe2a2 ◂— '/home/ubuntu/Desktop/test3'
06:0030│      0x7fffffffde60 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffde68 —▸ 0x400566 (main) ◂— push   rbp
──────────────────────────────────────────[ BACKTRACE ]───────────────────────────────────────────
 ► f 0           400592 main+44
   f 1     7ffff7a2d840 __libc_start_main+240
──────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

再来看一下堆空间：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600219020622-38c0ef09-7dd1-4d28-99ad-fe54d308c0de.png)

这里堆块并没有回收到unsorted bin中，猜测可能与libc版本有关

这里我们假设一下chunk被回收到了unsorted bin中，大致情况如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600219432893-20bd5a47-8518-48ad-a4ea-65c86b718f5c.png)

从上图可以看出，释放后的chunk1依然进入了unsorted bin中，接下来 我们将断点下到第10行，**<font style="color:#F5222D;">需要注意的是此时更改size大小的操作是在free之后完成的：</font>**

### 在第10行下断点
下断点运行程序，会执行代码 *(long *)((long)p - 0x8) = 0xb1;

详细信息如下：

```powershell
pwndbg> b 10
Breakpoint 2 at 0x4005a1: file test3.c, line 10.
pwndbg> c
Continuing.

Breakpoint 2, main () at test3.c:10
10	    q = malloc(0xa0);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────────[ REGISTERS ]───────────────────────────────────────────
*RAX  0x602008 ◂— 0xb1
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RDX  0x0
 RDI  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RSI  0x0
 R8   0x602000 ◂— 0x0
 R9   0x1
 R10  0x8b8
 R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffe680 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffe5a0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffe590 —▸ 0x602010 —▸ 0x7ffff7dd1b78 (main_arena+88) —▸ 0x6020b0 ◂— 0x0
*RIP  0x4005a1 (main+59) ◂— mov    edi, 0xa0
────────────────────────────────────────────[ DISASM ]────────────────────────────────────────────
   0x400592 <main+44>            mov    rax, qword ptr [rbp - 0x10]
   0x400596 <main+48>            sub    rax, 8
   0x40059a <main+52>            mov    qword ptr [rax], 0xb1
 ► 0x4005a1 <main+59>            mov    edi, 0xa0
   0x4005a6 <main+64>            call   malloc@plt <malloc@plt>
 
   0x4005ab <main+69>            mov    qword ptr [rbp - 8], rax
   0x4005af <main+73>            mov    eax, 0
   0x4005b4 <main+78>            leave  
   0x4005b5 <main+79>            ret    
 
   0x4005b6                      nop    word ptr cs:[rax + rax]
   0x4005c0 <__libc_csu_init>    push   r15
────────────────────────────────────────[ SOURCE (CODE) ]─────────────────────────────────────────
In file: /home/ubuntu/Desktop/test3.c
    5     void *p, *q;
    6     p = malloc(0x80);//分配第一个0x80的chunk1
    7     malloc(0x10);//分配第二个0x10的chunk2
    8     free(p);//首先进行释放，使得chunk1进入unsorted bin
    9     *(long *)((long)p - 0x8) = 0xb1;
 ► 10     q = malloc(0xa0);
   11 }
────────────────────────────────────────────[ STACK ]─────────────────────────────────────────────
00:0000│ rsp  0x7fffffffe590 —▸ 0x602010 —▸ 0x7ffff7dd1b78 (main_arena+88) —▸ 0x6020b0 ◂— 0x0
01:0008│      0x7fffffffe598 ◂— 0x0
02:0010│ rbp  0x7fffffffe5a0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffe5a8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffe5b0 ◂— 0x1
05:0028│      0x7fffffffe5b8 —▸ 0x7fffffffe688 —▸ 0x7fffffffe8ae ◂— '/home/ubuntu/Desktop/test3'
06:0030│      0x7fffffffe5c0 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffe5c8 —▸ 0x400566 (main) ◂— push   rbp
──────────────────────────────────────────[ BACKTRACE ]───────────────────────────────────────────
 ► f 0           4005a1 main+59
   f 1     7ffff7a2d840 __libc_start_main+240
──────────────────────────────────────────────────────────────────────────────────────────────────
```

看一下内存空间：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600219344325-50e3e38a-0f2b-45fb-b030-b1ac6221ecfd.png)

类似的，由于我们上面未出现unsorted bin，只好借用一下hollk大佬的图片：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600219589675-fdd083d5-1239-4950-bb31-a0e662a6df4b.png)

> 上面这张图片是执行malloc之后的图片
>

在修改完size之后重新申请0xa0的时候会从unsort bin中申请，这个时候大家需要总结一下，其实各个bin中存放的只有chunk的首地址，真正判断多大还得是去看这个chunk的size大小，所以再次申请的时候依然还可以对chunk2进行控制。

## 基本示例 4：通过 extend 后向 overlapping
这里展示通过 extend 进行后向 overlapping，这也是在 CTF 中最常出现的情况，通过 overlapping 可以实现其它的一些利用。

```c
//gcc -g test4.c -o test4
#include<stdio.h>
int main()
{
    void *p, *q;
    p = malloc(0x10);//分配第1个 0x80 的chunk1
    malloc(0x10); //分配第2个 0x10 的chunk2
    malloc(0x10); //分配第3个 0x10 的chunk3
    malloc(0x10); //分配第4个 0x10 的chunk4    
    *(long *)((long)p - 0x8) = 0x61;
    free(p);
    q = malloc(0x50);
}
```

在 malloc(0x50) 对 extend 区域重新占位后，其中 0x10 的 fastbin 块依然可以正常的分配和释放，此时已经构成 overlapping，通过对 overlapping 的进行操作可以实现 fastbin attack

## 基本示例 5：通过 extend 前向 overlapping
这里展示通过修改 pre_inuse 域和 pre_size 域实现合并前面的块

```c
//gcc -g test5.c -o test5
#include<stdio.h>
int main(void)
{
    void *p, *q, *r, *t;
    p = malloc(128);//smallbin1
    q = malloc(0x10);//fastbin1
    r = malloc(0x10);//fastbin2
    t = malloc(128);//smallbin2
    malloc(0x10);//防止与top合并
    free(p);
    *(int *)((long long)t - 0x8) = 0x90;//修改pre_inuse域
    *(int *)((long long)t - 0x10) = 0xd0;//修改pre_size域
    free(t);//unlink进行前向extend
    malloc(0x150);//占位块
}
```

前向 extend 利用了 smallbin 的 unlink 机制，通过修改 pre_size 域可以跨越多个 chunk 进行合并实现 overlapping

> `pre_size`, 如果该 chunk 的物理相邻的前一地址 chunk（两个指针的地址差值为前一chunk 大小）是**<font style="color:#F5222D;">空闲</font>**的话，**那该字段记录的是前一个 chunk 的****<font style="color:#F5222D;">大小</font>**** (包括 chunk 头)**。否则，该字段**<font style="color:#F5222D;">可以用来存储物理相邻的前一个 chunk 的</font>****<font style="color:#F5222D;">数据</font>**。这里的前一chunk 指的是较低地址的 chunk 。**<font style="color:#F5222D;">前面一个堆块在使用时并且pre_size为储存前面chunk的数据时，他的值始终为 0</font>**
>
> `size字段中的P（PREV_INUSE）`：记录前一个 chunk 块是否被分配。一般来说，堆中第一个被分配的内存块的 size 字段的 P 位都会被设置为 1，以便于防止访问前面的非法内存。当一个 chunk 的 size 的 P 位为 0 时，我们能通过 prev_size 字段来获取上一个 chunk 的大小以及地址。这也方便进行空闲 chunk 之间的合并。
>

下一小节将开始讲解题目

