首先回顾一下PIE文件保护的概念：

PIE(Position-Independent Executable, 位置无关可执行文件)技术与 ASLR 技术类似,ASLR 将程序运行时的堆栈以及共享库的加载地址随机化, 而 PIE 技术则在编译时将程序编译为位置无关, 即程序运行时各个段（如代码段等）加载的虚拟地址也是在装载时才确定。这就意味着, 在 PIE 和 ASLR 同时开启的情况下, 攻击者将对程序的内存布局一无所知, 传统的改写GOT 表项的方法也难以进行, 因为攻击者不能获得程序的.got 段的虚地址。



之前做的题都是开启了PIE的文件，但是开启了之后就无法使用angr了吗？

我原以为答案是肯定的，直到我无意间看到了这篇文章的某段话：

摘自[http://www.360doc.com/content/19/0619/10/7377734_843462259.shtml](http://www.360doc.com/content/19/0619/10/7377734_843462259.shtml)：

> 8.实际情况中，**<font style="color:#F5222D;">对有PIE保护的ELF,IDA静态分析时会以加载基址=0加载</font>**，angr在加载这样的elf时会以加载基址=0x400000加载到虚拟内存中进行符号执行，也即**<font style="color:#F5222D;">angr会强制将有pie保护的elf加载到0x400000</font>**处去，这样就相当于去掉了pie的每次加载基址不同（aslr)的特性
>

angr将会强制将带有PIE保护的ELF文件加载到0x400000，tql

接下来我们以BUUCTF的SoulLike一题作为例子进行说明：

首先检查一下文件的保护情况：

```bash
ubuntu@ubuntu:~/Desktop/CTF$ checksec --file=SoulLike
RELRO           STACK CANARY      NX            PIE             RPATH      RUNPATH	Symbols		FORTIFY	Fortified	Fortifiable  FILE
Full RELRO      Canary found      NX enabled    PIE enabled     No RPATH   No RUNPATH   No Symbols      Yes	0		1	SoulLike
ubuntu@ubuntu:~/Desktop/CTF$ 
```

可以看到，文件在编译的时候打开了PIE保护，但是这对angr没有影响，在IDA中找到success的地址：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1594872255297-097798f2-0a21-449b-9638-824265829e17.png)

在angr的虚拟地址应该为0x41117A，写下angr脚本：

```bash
import angr 

p=angr.Project("SoulLike",auto_load_libs=False) 
state=p.factory.entry_state()
sm=p.factory.simulation_manager(state) 
res=sm.explore(find=0x41117A) 

if len(res.found) > 0: 
    print (res.found[0].posix.dumps(0))
```

运行结果如下：

```bash
ubuntu@ubuntu:~/Desktop/CTF$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/CTF$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/CTF$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/CTF$ python 2.py
WARNING | 2020-07-15 20:49:48,881 | cle.loader | The main binary is a position-independent executable. It is being loaded with a base address of 0x400000.
b'actf{b0Nf|Re_LiT!}\x00\x00\x00\x0e\x0c\x00\x02\x00\x02\x08\x00I\x01\x02)\x02\x02\x02\x02\x08\x08\x00*\x02\x02*\x02\x01\x02\x02\x00\x01\x02\x00\x08\x08\x08\x02\x01\x08\x08\x00'
(angr) ubuntu@ubuntu:~/Desktop/CTF$ 
```

flag：actf{b0Nf|Re_LiT!}

还有一种爆破的方法，详情请见知识库：Reverse

