> 参考资料：
>
> [http://blog.eonew.cn/archives/958](http://blog.eonew.cn/archives/958)
>
> [https://www.cnblogs.com/Rookle/p/12871878.html](https://www.cnblogs.com/Rookle/p/12871878.html)
>
> 附件：
>
> 链接：[https://pan.baidu.com/s/1KyGCTr19u8svKfHKjCZWhw](https://pan.baidu.com/s/1KyGCTr19u8svKfHKjCZWhw)
>
> 提取码：8q2t 
>

> **注：附件中的libc文件仅供参考，程序运行时会调用本机的libc文件。**
>

# 前言
不知道你是否曾经遇到过这样的情况：

做某一道关于stack上的pwn题，但你不会做，当在网上寻找这个题目的payload时，有一大部分的payload在你的虚拟机中无法getshell并导致可执行文件直接crash，而只有少数的payload才能getshell。

或者是在ubuntu 16（低版本）中可以getshell，在ubuntu 18（高版本）中无法getshell。

程序的crash大概类似于下面这种情况：

```powershell
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────
 RAX  0x7f134ab60e97 ◂— sub    eax, 0x622f0063 /* '-c' */
 RBX  0x0
 RCX  0x7f134ab60e9f ◂— jae    0x7f134ab60f09 /* 'sh' */
 RDX  0x0
 RDI  0x2
 RSI  0x7f134ad9a6a0 (intr) ◂— 0x0
 R8   0x7f134ad9a600 (quit) ◂— 0x0
 R9   0x10
 R10  0x8
 R11  0x246
 R12  0x7f134ab60e9a ◂— 0x68732f6e69622f /* '/bin/sh' */
 R13  0x7ffe3e3eb140 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x601ce1 ◂— 0x0
 RSP  0x601c81 ◂— 0x0
 RIP  0x7f134a9fc2f6 (do_system+1094) ◂— movaps xmmword ptr [rsp + 0x40], xmm0
──────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────
 ► 0x7f134a9fc2f6 <do_system+1094>    movaps xmmword ptr [rsp + 0x40], xmm0
   0x7f134a9fc2fb <do_system+1099>    call   sigaction <0x7f134a9ec110>

   0x7f134a9fc300 <do_system+1104>    lea    rsi, [rip + 0x39e2f9] <0x7f134ad9a600>
   0x7f134a9fc307 <do_system+1111>    xor    edx, edx
   0x7f134a9fc309 <do_system+1113>    mov    edi, 3
   0x7f134a9fc30e <do_system+1118>    call   sigaction <0x7f134a9ec110>

   0x7f134a9fc313 <do_system+1123>    xor    edx, edx
   0x7f134a9fc315 <do_system+1125>    mov    rsi, rbp
   0x7f134a9fc318 <do_system+1128>    mov    edi, 2
   0x7f134a9fc31d <do_system+1133>    call   sigprocmask <0x7f134a9ec140>

   0x7f134a9fc322 <do_system+1138>    mov    rax, qword ptr [rip + 0x39bb7f]
───────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────
00:0000│ rsp  0x601c81 ◂— 0x0
01:0008│      0x601c89 —▸ 0x7f134ab60e97 ◂— sub    eax, 0x622f0063 /* '-c' */
02:0010│      0x601c91 ◂— 0x0
... ↓
04:0020│      0x601ca1 —▸ 0x7f134a9fc360 (cancel_handler) ◂— push   rbx
05:0028│      0x601ca9 —▸ 0x601c9d ◂— 0x4a9fc36000000000
06:0030│      0x601cb1 ◂— 0x0
... ↓
─────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────
 ► f 0     7f134a9fc2f6 do_system+1094
   f 1                a
   f 2                0
Program received signal SIGSEGV (fault address 0x0)
```

# 原因
在讲述原因之前，先来展示一下笔者的虚拟机中的大致情况：

> libc版本情况：libc-2.27.so
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603002047655-4508272c-6b62-4d2c-86e7-5ae69610b4d4.png)

> ubuntu版本：ubuntu 18.04.5
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603002107919-3f752ed6-3127-422d-b8f3-22c8cb499394.png)

我们将虚拟机中的libc-2.27.so文件提取出来，放入到IDA中查看一下system函数：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603002322749-0a6c7ec2-9889-4cde-9b7d-4705dfaf9822.png)

双击进入函数sub_4EF50查看一下，找到此函数的结尾：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603002556932-c0e6a5f9-3459-47c9-96dd-aa193e1dd5d4.png)

起始程序是否崩溃的关键原因在于：

```powershell
.text:000000000004F391                 movhps  xmm0, [rsp+198h+var_190]
.text:000000000004F396                 movaps  [rsp+198h+var_158], xmm0（请注意此处）
.text:000000000004F39B                 call    sigaction
```

> 只要知道xmm0是一个寄存器就行了，感兴趣的话可以上网搜索一下。
>

请注意0x4F396处的指令movaps  [rsp+198h+var_158], xmm0：

这个指令要求rsp+198h+var_158的值是16byte（0x10byte）的，否则就会触发中断从而使程序crash。

# 演示
```c
// compiled: gcc -g -no-pie -Og shell.c -o shell
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main()
{
    system("/bin/sh");
    return 0;
}
```

这个程序编译之后会正常运行，但是这里我们让它不正常运行，使其crash。

使用pwndbg进行附加调试：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603003442584-b879c8fb-041b-4466-aec3-c7ebf2287c51.png)

对程序中的system函数下断点，然后运行程序：

```powershell
pwndbg> b system
Breakpoint 1 at 0x4003f0
pwndbg> r
Starting program: /home/ubuntu/Desktop/x64 system crash(stack)/shell 

Breakpoint 1, __libc_system (line=line@entry=0x400594 "/bin/sh") at ../sysdeps/posix/system.c:180
180	../sysdeps/posix/system.c: No such file or directory.
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0x4004e7 (main) ◂— 0xa23d8d4808ec8348
 RBX  0x0
 RCX  0x400510 (__libc_csu_init) ◂— 0x41d7894956415741
 RDX  0x7fffffffe5e8 —▸ 0x7fffffffe82b ◂— 0x524f4c4f435f534c ('LS_COLOR')
 RDI  0x400594 ◂— 0x68732f6e69622f /* '/bin/sh' */
 RSI  0x7fffffffe5d8 —▸ 0x7fffffffe7f8 ◂— '/home/ubuntu/Desktop/x64 system crash(stack)/shell'
 R8   0x7ffff7dd0d80 (initial) ◂— 0x0
 R9   0x7ffff7dd0d80 (initial) ◂— 0x0
 R10  0x3
 R11  0x7ffff7a334e0 (system) ◂— test   rdi, rdi
 R12  0x400400 (_start) ◂— 0x89485ed18949ed31
 R13  0x7fffffffe5d0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x400510 (__libc_csu_init) ◂— 0x41d7894956415741
 RSP  0x7fffffffe4e8 —▸ 0x4004f7 (main+16) ◂— 0xc4834800000000b8
 RIP  0x7ffff7a334e0 (system) ◂— test   rdi, rdi
───────────────────────────────────[ DISASM ]───────────────────────────────────
 ► 0x7ffff7a334e0 <system>          test   rdi, rdi
   0x7ffff7a334e3 <system+3>        je     system+16 <system+16>
 
   0x7ffff7a334e5 <system+5>        jmp    do_system <do_system>
    ↓
   0x7ffff7a32f50 <do_system>       push   r12
   0x7ffff7a32f52 <do_system+2>     push   rbp
   0x7ffff7a32f53 <do_system+3>     mov    r12, rdi
   0x7ffff7a32f56 <do_system+6>     push   rbx
   0x7ffff7a32f57 <do_system+7>     mov    ecx, 0x10
   0x7ffff7a32f5c <do_system+12>    mov    esi, 1
   0x7ffff7a32f61 <do_system+17>    sub    rsp, 0x180
   0x7ffff7a32f68 <do_system+24>    lea    rbx, [rsp + 0xe0]
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffe4e8 —▸ 0x4004f7 (main+16) ◂— 0xc4834800000000b8
01:0008│      0x7fffffffe4f0 ◂— 0x0
02:0010│      0x7fffffffe4f8 —▸ 0x7ffff7a05b97 (__libc_start_main+231) ◂— mov    edi, eax
03:0018│      0x7fffffffe500 ◂— 0x1
04:0020│      0x7fffffffe508 —▸ 0x7fffffffe5d8 —▸ 0x7fffffffe7f8 ◂— '/home/ubuntu/Desktop/x64 system crash(stack)/shell'
05:0028│      0x7fffffffe510 ◂— 0x100008000
06:0030│      0x7fffffffe518 —▸ 0x4004e7 (main) ◂— 0xa23d8d4808ec8348
07:0038│      0x7fffffffe520 ◂— 0x0
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0     7ffff7a334e0 system
   f 1           4004f7 main+16
   f 2     7ffff7a05b97 __libc_start_main+231
────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

从上面的汇编代码可以看出程序已经断在了system函数的内部，再来看一下程序的内存分布：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603003732156-ed50499f-a76b-4170-85ad-7fb324607542.png)

在结合：0x7ffff7a334e0 <system>          test   rdi, rdi

可以得到内存中关键指令的起始地址为：

> 0x7ffff79e4000+0x4F38C=0x7FFFF7A3338C
>

```powershell
------------------------------------------------------------------------//静态
.text:000000000004F38C                 mov     [rsp+198h+var_190], rax
.text:000000000004F391                 movhps  xmm0, [rsp+198h+var_190]
.text:000000000004F396                 movaps  [rsp+198h+var_158], xmm0
------------------------------------------------------------------------//动态
.text:0x007FFFF7A3338C                 mov     [rsp+198h+var_190], rax
.text:0x007FFFF7A4F391                 movhps  xmm0, [rsp+198h+var_190]
.text:0x007FFFF7A4F396                 movaps  [rsp+198h+var_158], xmm0
------------------------------------------------------------------------
```

对地址0x007FFFF7A3338C进行下断点，继续运行程序：

```powershell
pwndbg> b *0x007FFFF7A3338C
Breakpoint 2 at 0x7ffff7a3338c: file ../sysdeps/posix/system.c, line 125.
pwndbg> c
Continuing.
[New process 5574]
[Switching to process 5574]

Thread 2.1 "shell" hit Breakpoint 2, 0x00007ffff7a3338c in do_system (line=line@entry=0x400594 "/bin/sh") at ../sysdeps/posix/system.c:125
125	in ../sysdeps/posix/system.c
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────────────────[ REGISTERS ]──────────────────────────────────────────────────
 RAX  0x7ffff7b980f7 ◂— sub    eax, 0x622f0063 /* '-c' */
 RBX  0x0
 RCX  0x7ffff7b980ff ◂— jae    0x7ffff7b98169 /* 'sh' */
 RDX  0x0
 RDI  0x2
 RSI  0x7ffff7dd16a0 (intr) ◂— 0x0
 R8   0x7ffff7dd1600 (quit) ◂— 0x0
 R9   0x7ffff7dd0d80 (initial) ◂— 0x0
 R10  0x8
 R11  0x246
 R12  0x400594 ◂— 0x68732f6e69622f /* '/bin/sh' */
 R13  0x7fffffffe5d0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffe3b0 ◂— 0x0
 RSP  0x7fffffffe350 ◂— 0x0
 RIP  0x7ffff7a3338c (do_system+1084) ◂— mov    qword ptr [rsp + 8], rax
───────────────────────────────────────────────────[ DISASM ]────────────────────────────────────────────────────
 ► 0x7ffff7a3338c <do_system+1084>    mov    qword ptr [rsp + 8], rax
   0x7ffff7a33391 <do_system+1089>    movhps xmm0, qword ptr [rsp + 8]
   0x7ffff7a33396 <do_system+1094>    movaps xmmword ptr [rsp + 0x40], xmm0
   0x7ffff7a3339b <do_system+1099>    call   sigaction <sigaction>
 
   0x7ffff7a333a0 <do_system+1104>    lea    rsi, [rip + 0x39e259] <0x7ffff7dd1600>
   0x7ffff7a333a7 <do_system+1111>    xor    edx, edx
   0x7ffff7a333a9 <do_system+1113>    mov    edi, 3
   0x7ffff7a333ae <do_system+1118>    call   sigaction <sigaction>
 
   0x7ffff7a333b3 <do_system+1123>    xor    edx, edx
   0x7ffff7a333b5 <do_system+1125>    mov    rsi, rbp
   0x7ffff7a333b8 <do_system+1128>    mov    edi, 2
────────────────────────────────────────────────────[ STACK ]────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffe350 ◂— 0x0
01:0008│      0x7fffffffe358 —▸ 0x7ffff7b980ff ◂— jae    0x7ffff7b98169 /* 'sh' */
02:0010│      0x7fffffffe360 ◂— 0x0
... ↓
04:0020│      0x7fffffffe370 —▸ 0x7ffff7a33400 (cancel_handler) ◂— push   rbx
05:0028│      0x7fffffffe378 —▸ 0x7fffffffe36c ◂— 0xf7a3340000000000
06:0030│      0x7fffffffe380 —▸ 0x7ffff7ffe738 —▸ 0x7ffff7ffe710 —▸ 0x7ffff7ffb000 ◂— jg     0x7ffff7ffb047
07:0038│      0x7fffffffe388 ◂— 0x0
──────────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────────
 ► f 0     7ffff7a3338c do_system+1084
   f 1     7ffff7a334ea system+10
   f 2           4004f7 main+16
   f 3     7ffff7a05b97 __libc_start_main+231
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

继续单步步过（ni）运行到：0x7ffff7a33396 <do_system+1094>    movaps xmmword ptr [rsp + 0x40], xmm0

```powershell
pwndbg> ni
0x00007ffff7a33396	125	in ../sysdeps/posix/system.c
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────────────────[ REGISTERS ]──────────────────────────────────────────────────
 RAX  0x7ffff7b980f7 ◂— sub    eax, 0x622f0063 /* '-c' */
 RBX  0x0
 RCX  0x7ffff7b980ff ◂— jae    0x7ffff7b98169 /* 'sh' */
 RDX  0x0
 RDI  0x2
 RSI  0x7ffff7dd16a0 (intr) ◂— 0x0
 R8   0x7ffff7dd1600 (quit) ◂— 0x0
 R9   0x7ffff7dd0d80 (initial) ◂— 0x0
 R10  0x8
 R11  0x246
 R12  0x400594 ◂— 0x68732f6e69622f /* '/bin/sh' */
 R13  0x7fffffffe5d0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffe3b0 ◂— 0x0
 RSP  0x7fffffffe350 ◂— 0x0
*RIP  0x7ffff7a33396 (do_system+1094) ◂— movaps xmmword ptr [rsp + 0x40], xmm0
───────────────────────────────────────────────────[ DISASM ]────────────────────────────────────────────────────
   0x7ffff7a3338c <do_system+1084>    mov    qword ptr [rsp + 8], rax
   0x7ffff7a33391 <do_system+1089>    movhps xmm0, qword ptr [rsp + 8]
 ► 0x7ffff7a33396 <do_system+1094>    movaps xmmword ptr [rsp + 0x40], xmm0
   0x7ffff7a3339b <do_system+1099>    call   sigaction <sigaction>
 
   0x7ffff7a333a0 <do_system+1104>    lea    rsi, [rip + 0x39e259] <0x7ffff7dd1600>
   0x7ffff7a333a7 <do_system+1111>    xor    edx, edx
   0x7ffff7a333a9 <do_system+1113>    mov    edi, 3
   0x7ffff7a333ae <do_system+1118>    call   sigaction <sigaction>
 
   0x7ffff7a333b3 <do_system+1123>    xor    edx, edx
   0x7ffff7a333b5 <do_system+1125>    mov    rsi, rbp
   0x7ffff7a333b8 <do_system+1128>    mov    edi, 2
────────────────────────────────────────────────────[ STACK ]────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffe350 ◂— 0x0
01:0008│      0x7fffffffe358 —▸ 0x7ffff7b980f7 ◂— sub    eax, 0x622f0063 /* '-c' */
02:0010│      0x7fffffffe360 ◂— 0x0
... ↓
04:0020│      0x7fffffffe370 —▸ 0x7ffff7a33400 (cancel_handler) ◂— push   rbx
05:0028│      0x7fffffffe378 —▸ 0x7fffffffe36c ◂— 0xf7a3340000000000
06:0030│      0x7fffffffe380 —▸ 0x7ffff7ffe738 —▸ 0x7ffff7ffe710 —▸ 0x7ffff7ffb000 ◂— jg     0x7ffff7ffb047
07:0038│      0x7fffffffe388 ◂— 0x0
──────────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────────
 ► f 0     7ffff7a33396 do_system+1094
   f 1     7ffff7a334ea system+10
   f 2           4004f7 main+16
   f 3     7ffff7a05b97 __libc_start_main+231
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

然后来看一下rsp + 0x40的值：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603004397626-7c7f517a-8d4b-4474-9bb7-f2f39b36535f.png)

可以看到此时的值是对齐的，所以可以正常运行，我们尝试对rsp加1，看看会不会crash。

```powershell
pwndbg> set $rsp=$rsp+1
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────────────────[ REGISTERS ]──────────────────────────────────────────────────
 RAX  0x7ffff7b980f7 ◂— sub    eax, 0x622f0063 /* '-c' */
 RBX  0x0
 RCX  0x7ffff7b980ff ◂— jae    0x7ffff7b98169 /* 'sh' */
 RDX  0x0
 RDI  0x2
 RSI  0x7ffff7dd16a0 (intr) ◂— 0x0
 R8   0x7ffff7dd1600 (quit) ◂— 0x0
 R9   0x7ffff7dd0d80 (initial) ◂— 0x0
 R10  0x8
 R11  0x246
 R12  0x400594 ◂— 0x68732f6e69622f /* '/bin/sh' */
 R13  0x7fffffffe5d0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffe3b0 ◂— 0x0
*RSP  0x7fffffffe351 ◂— 0xf700000000000000
*RIP  0x7ffff7a33396 (do_system+1094) ◂— movaps xmmword ptr [rsp + 0x40], xmm0
───────────────────────────────────────────────────[ DISASM ]────────────────────────────────────────────────────
   0x7ffff7a3338c <do_system+1084>    mov    qword ptr [rsp + 8], rax
   0x7ffff7a33391 <do_system+1089>    movhps xmm0, qword ptr [rsp + 8]
 ► 0x7ffff7a33396 <do_system+1094>    movaps xmmword ptr [rsp + 0x40], xmm0
   0x7ffff7a3339b <do_system+1099>    call   sigaction <sigaction>
 
   0x7ffff7a333a0 <do_system+1104>    lea    rsi, [rip + 0x39e259] <0x7ffff7dd1600>
   0x7ffff7a333a7 <do_system+1111>    xor    edx, edx
   0x7ffff7a333a9 <do_system+1113>    mov    edi, 3
   0x7ffff7a333ae <do_system+1118>    call   sigaction <sigaction>
 
   0x7ffff7a333b3 <do_system+1123>    xor    edx, edx
   0x7ffff7a333b5 <do_system+1125>    mov    rsi, rbp
   0x7ffff7a333b8 <do_system+1128>    mov    edi, 2
────────────────────────────────────────────────────[ STACK ]────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffe351 ◂— 0xf700000000000000
01:0008│      0x7fffffffe359 ◂— 0x7ffff7b980
02:0010│      0x7fffffffe361 ◂— 0x0
... ↓
04:0020│      0x7fffffffe371 ◂— 0x6c00007ffff7a334
05:0028│      0x7fffffffe379 ◂— 0x3800007fffffffe3
06:0030│      0x7fffffffe381 ◂— 0x7ffff7ffe7
07:0038│      0x7fffffffe389 ◂— 0x100000000000000
──────────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────────
 ► f 0     7ffff7a33396 do_system+1094
   f 1             4004
   f 2 9700000000000000
   f 3  100007ffff7a05b
   f 4 d800000000000000
   f 5       7fffffffe5
   f 6 e700000001000080
   f 7             4004
   f 8 fd00000000000000
   f 9   47737fdd90836e
   f 10 d000000000004004
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

继续来查看rsp + 0x40的值。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603004603764-ca478da5-e21f-430e-9525-caaaa55ea71d.png)

可以看到此时已经不对齐了，那么继续运行。

```powershell
pwndbg> c
Continuing.

Thread 2.1 "shell" received signal SIGSEGV, Segmentation fault.
0x00007ffff7a33396 in do_system (line=0x400594 "/bin/sh") at ../sysdeps/posix/system.c:125
125	in ../sysdeps/posix/system.c
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
────────────────────────────────────────────────────────────────────────────────────────────[ REGISTERS ]────────────────────────────────────────────────────────────────────────────────────────────
 RAX  0x7ffff7b980f7 ◂— sub    eax, 0x622f0063 /* '-c' */
 RBX  0x0
 RCX  0x7ffff7b980ff ◂— jae    0x7ffff7b98169 /* 'sh' */
 RDX  0x0
 RDI  0x2
 RSI  0x7ffff7dd16a0 (intr) ◂— 0x0
 R8   0x7ffff7dd1600 (quit) ◂— 0x0
 R9   0x7ffff7dd0d80 (initial) ◂— 0x0
 R10  0x8
 R11  0x246
 R12  0x400594 ◂— 0x68732f6e69622f /* '/bin/sh' */
 R13  0x7fffffffe5d0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffe3b0 ◂— 0x0
 RSP  0x7fffffffe351 ◂— 0xf700000000000000
 RIP  0x7ffff7a33396 (do_system+1094) ◂— movaps xmmword ptr [rsp + 0x40], xmm0
─────────────────────────────────────────────────────────────────────────────────────────────[ DISASM ]──────────────────────────────────────────────────────────────────────────────────────────────
   0x7ffff7a3338c <do_system+1084>    mov    qword ptr [rsp + 8], rax
   0x7ffff7a33391 <do_system+1089>    movhps xmm0, qword ptr [rsp + 8]
 ► 0x7ffff7a33396 <do_system+1094>    movaps xmmword ptr [rsp + 0x40], xmm0
   0x7ffff7a3339b <do_system+1099>    call   sigaction <sigaction>
 
   0x7ffff7a333a0 <do_system+1104>    lea    rsi, [rip + 0x39e259] <0x7ffff7dd1600>
   0x7ffff7a333a7 <do_system+1111>    xor    edx, edx
   0x7ffff7a333a9 <do_system+1113>    mov    edi, 3
   0x7ffff7a333ae <do_system+1118>    call   sigaction <sigaction>
 
   0x7ffff7a333b3 <do_system+1123>    xor    edx, edx
   0x7ffff7a333b5 <do_system+1125>    mov    rsi, rbp
   0x7ffff7a333b8 <do_system+1128>    mov    edi, 2
──────────────────────────────────────────────────────────────────────────────────────────────[ STACK ]──────────────────────────────────────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffe351 ◂— 0xf700000000000000
01:0008│      0x7fffffffe359 ◂— 0x7ffff7b980
02:0010│      0x7fffffffe361 ◂— 0x0
... ↓
04:0020│      0x7fffffffe371 ◂— 0x6c00007ffff7a334
05:0028│      0x7fffffffe379 ◂— 0x3800007fffffffe3
06:0030│      0x7fffffffe381 ◂— 0x7ffff7ffe7
07:0038│      0x7fffffffe389 ◂— 0x100000000000000
────────────────────────────────────────────────────────────────────────────────────────────[ BACKTRACE ]────────────────────────────────────────────────────────────────────────────────────────────
 ► f 0     7ffff7a33396 do_system+1094
   f 1             4004
   f 2 9700000000000000
   f 3  100007ffff7a05b
   f 4 d800000000000000
   f 5       7fffffffe5
   f 6 e700000001000080
   f 7             4004
   f 8 fd00000000000000
   f 9   47737fdd90836e
   f 10 d000000000004004
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

从上面的信息中可以看出程序已经崩溃。

# 解决办法
核心思想就是改变栈的地址：

1. 改变payload长度
2. 栈转移

## 改变payload长度或填充一些ret指令
1. 直接更改我们的payload长度，在栈溢出的时候栈的地址自然不同，然后将栈地址`+1`，如果不行的话，就继续增加，最多也就改16次就一定会遇到栈对齐的情况。
2. 填充一些ret指令

```cpp
//原本的payload，运行后栈如下
ret  pop_rdi_ret
     bin_sh
     system
    
//我们增加一些额外的指令，ret,ret 1,ret 2,ret 3等等
ret  ret
     pop_rdi_ret
     bin_sh
     system
```

3. 如果有现成的后门可以用，改变返回地址的值在调用system函数，如下图我们可以尝试ret的地址为箭头的地址。与1的思路差不多。

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1603004973199-12ed9f3f-9d61-4ed7-98ec-b2141e07bfea.jpeg)

## 栈转移
当payload有长度限制的时候，我们可以尝试进行栈转移来进行栈地址的改变，如果遇到了没有对齐的情况就继续将栈地址`+1`，直到遇到栈对齐的情况。

## 调用execve
用execve函数来替换system函数，这个要求就更高，应为他需要三个参数才能正常调用。也就是说我们需要构造`rdi`、`rsi`、`rdx`这三个参数。

```plain
int execve(const char * filename,char * const argv[ ],char * const envp[ ]);
```

# 总结
遇到问题就多多调试。

