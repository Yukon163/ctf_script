> 参考文章：[https://blog.csdn.net/qq_33438733/article/details/80276628](https://blog.csdn.net/qq_33438733/article/details/80276628)
>
> [https://www.jianshu.com/p/755e52d48a77](https://www.jianshu.com/p/755e52d48a77)
>
> demo下载链接：
>
> 链接：[https://pan.baidu.com/s/1wHDZTgKMIujsaLnSztH7VA](https://pan.baidu.com/s/1wHDZTgKMIujsaLnSztH7VA)
>
> 提取码：9epn
>

自己先写一个demo，代码如下：

```c
#include <stdio.h>
#include <string.h>
void success()
{
    printf("success\n");
}
void failed()
{
    printf("fail\n");
}
int main(void)
{
    char name[10] = "";
    printf("plz input your name:");
    scanf("%s", &name);
    if (!strcmp(name, "Cyberangel"))
    {
        success();
    }
    else
    {
        failed();
    }
    return 0;
}
```

> 注意：angr不会真的把程序加载到内存中执行，他只是利用模拟器模拟执行
>

<font style="color:#4D4D4D;">注意编译的时候要先关闭PIE（下文会介绍PIE的概念），毕竟是作为demo用来学习angr的(你也不想在入门angr的时候给自己添麻烦)，</font>可以用checksec这个工具检查一下开启了哪些保护。

> **原文章作者注：在刚开始用的是****<font style="color:#F5222D;">gets</font>****结果坑了自己一把，不信你可以去试试（****<font style="color:#F5222D;">会造成符号传递中断</font>****）**。
>

<font style="color:#4D4D4D;">首先执行命令安装checksec，日志如下：</font>

```bash
ubuntu@ubuntu:~/Desktop/angr$ sudo apt install checksec
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following additional packages will be installed:
  curl gawk libsigsegv2
Suggested packages:
  gawk-doc
The following NEW packages will be installed:
  checksec curl gawk libsigsegv2
0 upgraded, 4 newly installed, 0 to remove and 73 not upgraded.
Need to get 614 kB of archives.
After this operation, 2,267 kB of additional disk space will be used.
Do you want to continue? [Y/n] Y
Get:1 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libsigsegv2 amd64 2.12-2 [13.9 kB]
Get:2 http://us.archive.ubuntu.com/ubuntu focal/main amd64 gawk amd64 1:5.0.1+dfsg-1 [418 kB]
Get:3 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 checksec all 2.1.0+git20191113.bf85698-2 [21.7 kB]
Get:4 http://us.archive.ubuntu.com/ubuntu focal/main amd64 curl amd64 7.68.0-1ubuntu2 [161 kB]
Fetched 614 kB in 11s (57.6 kB/s)
Selecting previously unselected package libsigsegv2:amd64.
(Reading database ... 186399 files and directories currently installed.)
Preparing to unpack .../libsigsegv2_2.12-2_amd64.deb ...
Unpacking libsigsegv2:amd64 (2.12-2) ...
Setting up libsigsegv2:amd64 (2.12-2) ...
Selecting previously unselected package gawk.
(Reading database ... 186406 files and directories currently installed.)
Preparing to unpack .../gawk_1%3a5.0.1+dfsg-1_amd64.deb ...
Unpacking gawk (1:5.0.1+dfsg-1) ...
Selecting previously unselected package checksec.
Preparing to unpack .../checksec_2.1.0+git20191113.bf85698-2_all.deb ...
Unpacking checksec (2.1.0+git20191113.bf85698-2) ...
Selecting previously unselected package curl.
Preparing to unpack .../curl_7.68.0-1ubuntu2_amd64.deb ...
Unpacking curl (7.68.0-1ubuntu2) ...
Setting up gawk (1:5.0.1+dfsg-1) ...
Setting up checksec (2.1.0+git20191113.bf85698-2) ...
Setting up curl (7.68.0-1ubuntu2) ...
Processing triggers for man-db (2.9.1-1) ...
Processing triggers for libc-bin (2.31-0ubuntu9) ...
ubuntu@ubuntu:~/Desktop/angr$ 
```

接下来使用Linux的gcc工具对cpp文件进行编译，将angr.cpp放入到Linux的Desktop/angr/（**编译不要使用PIE**）

```bash
ubuntu@ubuntu:~/Desktop/angr$ gcc angr.cpp -no-pie -o angr
angr.cpp: In function ‘int main()’:
angr.cpp:15:13: warning: format ‘%s’ expects argument of type ‘char*’, but argument 2 has type ‘char (*)[10]’ [-Wformat=]
   15 |     scanf("%s", &name);
      |            ~^   ~~~~~
      |             |   |
      |             |   char (*)[10]
      |             char*
ubuntu@ubuntu:~/Desktop/angr$
```

检查一下是否关闭了PIE

```bash
ubuntu@ubuntu:~/Desktop/angr$ checksec --file=angr
RELRO           STACK CANARY      NX            PIE             RPATH      RUNPATH	Symbols		FORTIFY	Fortified	Fortifiable  FILE
Partial RELRO   Canary found      NX enabled    No PIE          No RPATH   No RUNPATH   69 Symbols     Yes	0		1	angr
ubuntu@ubuntu:~/Desktop/angr$ 
```

**下面我们来介绍一下checksec工具究竟可以干什么**

简单的来说，checksec可以检查可执行文件的保护情况，在pwn中有广泛的应用，它可以检查的参数如下

**Arch**

程序架构信息。判断是拖进64位IDA还是32位？exp编写时p64还是p32函数？

**RELRO**

Relocation Read-Only (RELRO)  此项技术主要针对 GOT 改写的攻击方式。它分为两种，Partial RELRO 和 Full RELRO。

部分RELRO 易受到攻击，例如攻击者可以**atoi.got为system.plt，进而输入/bin/sh\x00获得shell**

完全RELRO 使整个 GOT 只读，从而无法被覆盖，但这样会大大增加程序的启动时间，因为程序在启动之前需要解析所有的符号。

**Stack-canary**

栈溢出保护是一种缓冲区溢出攻击缓解手段，当函数存在缓冲区溢出攻击漏洞时，攻击者可以覆盖栈上的返回地址来让shellcode能够得到执行。当启用栈保护后，函数开始执行的时候会先往栈里插入类似cookie的信息，当函数真正返回的时候会验证cookie信息是否合法，如果不合法就停止程序运行。攻击者在覆盖返回地址的时候往往也会将cookie信息给覆盖掉，导致栈保护检查失败而阻止shellcode的执行。在Linux中我们将cookie信息称为canary。

**NX**

NX enabled如果这个保护开启就是意味着栈中数据没有执行权限，如此一来, 当攻击者在堆栈上部署自己的 shellcode 并触发时, 只会直接造成程序的崩溃，但是可以利用rop这种方法绕过

**PIE**

PIE(Position-Independent Executable, 位置无关可执行文件)技术与 ASLR 技术类似,ASLR 将程序运行时的堆栈以及共享库的加载地址随机化, 而 PIE 技术则在编译时将程序编译为位置无关, 即程序运行时各个段（如代码段等）加载的虚拟地址也是在装载时才确定。这就意味着, 在 PIE 和 ASLR 同时开启的情况下, 攻击者将对程序的内存布局一无所知, 传统的改写GOT 表项的方法也难以进行, 因为攻击者不能获得程序的.got 段的虚地址。

若开启一般需在攻击时泄露地址信息

RPATH/RUNPATH

程序运行时的环境变量，运行时所需要的共享库文件优先从该目录寻找，可以fake lib造成攻击

**FORTIFY**

这是一个由GCC实现的源码级别的保护机制，其功能是在编译的时候检查源码以避免潜在的缓冲区溢出等错误。简单地说，加了这个保护之后,一些敏感函数如read, fgets,memcpy, printf等等可能导致漏洞出现的函数都会被替换成__read_chk,__fgets_chk, __memcpy_chk, __printf_chk等。这些带了chk的函数会检查读取/复制的字节长度是否超过缓冲区长度，通过检查诸如%n之类的字符串位置是否位于可能被用户修改的可写地址，避免了格式化字符串跳过某些参数（如直接%7$x）等方式来避免漏洞出现。开启了FORTIFY保护的程序会被checksec检出，此外，在反汇编时直接查看got表也会发现chk函数的存在,这种检查是默认不开启的，可以通过



```plain
gcc -D_FORTIFY_SOURCE=2 -O1
开启fortity检查，开启后会替换strcpy等危险函数。
```



已关闭PIE保护，将编译之后的文件载入到IDA中，可以发现只有两条路径：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589509260328-a9a1e405-96df-4ae7-9185-2f9e73157fd8.png)

来到文本视图，注意两个地址，这是程序流的分支，分别流向success和failed，在C语言中的语句就是判断语句：if (!strcmp(name, "Cyberangel"))

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589509420472-5dacb259-f621-448c-ae81-39f287bb821c.png)

在Ubuntu中进入angr的虚拟环境：

```bash
ubuntu@ubuntu:~/Desktop/angr$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/angr$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/angr$ workon
angr
ubuntu@ubuntu:~/Desktop/angr$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

编写的angr脚本如下：

```bash
ubuntu@ubuntu:~/Desktop/angr$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/angr$ python
Python 3.8.2 (default, Apr 27 2020, 15:53:34) 
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import angr
>>> p=angr.Project("angr",auto_load_libs=False)
>>> state=p.factory.entry_state()
>>> sm=p.factory.simulation_manager(state)
>>> res=sm.explore(find=0x40124d,avoid=0x401254) 
WARNING | 2020-05-14 19:32:18,273 | angr.state_plugins.symbolic_memory | The program is accessing memory or registers with an unspecified value. This could indicate unwanted behavior.
WARNING | 2020-05-14 19:32:18,273 | angr.state_plugins.symbolic_memory | angr will cope with this by generating an unconstrained symbolic variable and continuing. You can resolve this by:
WARNING | 2020-05-14 19:32:18,273 | angr.state_plugins.symbolic_memory | 1) setting a value to the initial state
WARNING | 2020-05-14 19:32:18,273 | angr.state_plugins.symbolic_memory | 2) adding the state option ZERO_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to make unknown regions hold null
WARNING | 2020-05-14 19:32:18,274 | angr.state_plugins.symbolic_memory | 3) adding the state option SYMBOL_FILL_UNCONSTRAINED_{MEMORY_REGISTERS}, to suppress these messages.
WARNING | 2020-05-14 19:32:18,274 | angr.state_plugins.symbolic_memory | Filling memory at 0x7fffffffffefff8 with 86 unconstrained bytes referenced from 0x1000020 (strcmp+0x0 in extern-address space (0x20))
>>> res.found[0].posix.dumps(0)
b'Cyberangel\x00\x00\x00\x02\x01\x00\x02\x02\x1a\x1a\x0e\x08\x89\x02\x19\x02I\x01)\x02\x01\x01I\x02\x01\x01\x02\x02\x02\x02\x00\x08\x01\x08\x00\x80\x00\x00\x80\x80\x80\x80\x01\x08\x08\x00\x08\x08\x08\x00'
>>> 

```

可以看出angr已经给出了答案：Cyberangel

上面的脚本看不懂？接下来我们注释一下脚本：

```python
import angr #导入angr库

p=angr.Project("angr",auto_load_libs=False) # 加载二进制程序，相当于在运行Windows程序时的双击鼠标
state=p.factory.entry_state() #创建一个状态，默认是程序的入口地址，也可以指定一个地址作为入口地址
sm=p.factory.simulation_manager(state) #创建一个模拟器用来模拟程序执行
res=sm.explore(find=0x40124d,avoid=0x401254) #使用explore执行模拟器，find和avoid用来作为约束条件，上面提到过这两个地址

if len(res.found) > 0: #如果angr寻找到的结果数目大于0
    print (res.found[0].posix.dumps(0))#打印found的第一个结果
```

> + res.found[0].posix.dumps(0)代表该状态执行路径的**<font style="color:#F5222D;">输入</font>**
> + res.found[0].posix.dumps(1)代表该状态执行路径的**<font style="color:#F5222D;">输出</font>**
>
> **<font style="color:#F5222D;">注意：</font>****<font style="color:#F5222D;">res.found[0].posix.dumps(0)只能打印found的第一个结果，如需打印更多的结果请使用循环语句</font>**
>
> **<font style="color:#F5222D;">因为我们这里要求输入的东西，因此我们使用</font>****<font style="color:#F5222D;">res.found[0].posix.dumps(0)</font>**
>

脚本运行结果：

```python
(angr) ubuntu@ubuntu:~/Desktop/angr$ python 1.py
WARNING | 2020-05-14 20:03:39,344 | angr.state_plugins.symbolic_memory | The program is accessing memory or registers with an unspecified value. This could indicate unwanted behavior.
WARNING | 2020-05-14 20:03:39,344 | angr.state_plugins.symbolic_memory | angr will cope with this by generating an unconstrained symbolic variable and continuing. You can resolve this by:
WARNING | 2020-05-14 20:03:39,345 | angr.state_plugins.symbolic_memory | 1) setting a value to the initial state
WARNING | 2020-05-14 20:03:39,345 | angr.state_plugins.symbolic_memory | 2) adding the state option ZERO_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to make unknown regions hold null
WARNING | 2020-05-14 20:03:39,345 | angr.state_plugins.symbolic_memory | 3) adding the state option SYMBOL_FILL_UNCONSTRAINED_{MEMORY_REGISTERS}, to suppress these messages.
WARNING | 2020-05-14 20:03:39,345 | angr.state_plugins.symbolic_memory | Filling memory at 0x7fffffffffefff8 with 86 unconstrained bytes referenced from 0x1000020 (strcmp+0x0 in extern-address space (0x20))
b'Cyberangel\x00\x00\x00\x02\x01\x00\x02\x02\x1a\x1a\x0e\x08\x89\x02\x19\x02I\x01)\x02\x01\x01I\x02\x01\x01\x02\x02\x02\x02\x00\x08\x01\x08\x00\x80\x00\x00\x80\x80\x80\x80\x01\x08\x08\x00\x08\x08\x08\x00'
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

程序执行时部分截图如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589510785938-57a15559-5d53-4476-97d7-0a55ec22c6f2.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589510839686-13ae0b20-ce07-4b45-b261-0c6bde34c3f9.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589510786586-e7b39f5b-f435-43f2-bc42-3a5e44cc7dec.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589510787253-0b3cfded-302f-44ab-b4ed-677f5da1b546.png)

