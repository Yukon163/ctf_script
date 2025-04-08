> 附件下载：
>
> 链接: [https://pan.baidu.com/s/17v3SBTEi6WPdF0wZYn7fdA](https://pan.baidu.com/s/17v3SBTEi6WPdF0wZYn7fdA)  密码: csgs
>
> --来自百度网盘超级会员V3的分享
>

# 前言
之前我们说过fastbin中的house of spirit，tcache中的house of spirit和fastbin中的类似，接下来我们来学习它。

# 回顾fastbin_house_of_spirit
首先我们先来回顾一下fastbin_attack中的house of spirit：

House of Spirit的利用关键在于能够**<font style="color:#F5222D;">覆盖一个堆指针变量</font>**（也就是调用malloc之后堆块中malloc_data返回的地址），让其指向可以控制的区域。

来看一下它的利用思路：

1. 首先我们需要伪造一个堆块，伪造堆块时需要注意绕过之后的五个检测。

2. 覆盖堆指针指向上一步伪造的堆块

3. 释放堆块，将伪造的堆块放入fastbin的单链表里面（需要绕过检测）

4. 申请堆块，将刚才释放的堆块申请出来，最终可以使得向目标区域中写入数据，以达到控制内存的目的。

这是5个检测，需要绕过他们：

+ fake chunk 的 ISMMAP 位不能为 1，因为 free 时，如果是 mmap 的 chunk，会单独处理。
+ fake chunk 地址需要对齐， MALLOC_ALIGN_MASK
+ fake chunk 的 size 大小需要满足对应的 fastbin 的需求，同时也得对齐。
+ fake chunk 的 **<font style="color:#F5222D;">next chunk </font>**的大小不能小于 2 * SIZE_SZ，同时也不能大于av->system_mem 。
+ fake chunk 对应的 fastbin 链表头部不能是该 fake chunk，即不能构成 double free 的情况。

# tcache_house_of_spirit
还记得之前的一句话吗：tcache makes heap exploitation easy again

放在这里同样适用，因为tcache中的house_of_spirit的检测相较于fastbin中的要少（主要是由于tcache_put函数几乎没有检查），因此构造fake tcache chunk内存时需要绕过的检查更加宽松，具体如下：

+ fake chunk的size在tcache的范围中（64位程序中是32字节到410字节），且其ISMMAP位不为1
+ fake chunk的地址对齐
+ 无需构造next chunk的size（无需伪造fake_chunk）
+ 无需考虑double free的情况，因为free堆块到tcache中的时候不会进行这些检查

# Demo
来看一个示例，**<font style="color:#F5222D;">感谢@yichen师傅</font>**的汉化：

```c
//gcc -g -fno-stack-protector -z execstack -no-pie -z norelro test.c -o test
#include <stdio.h>
#include <stdlib.h>

int main()
{
    malloc(1);
    unsigned long long *a;
    unsigned long long fake_chunks[10];
    fprintf(stderr, "fake_chunks[1] 在 %p\n", &fake_chunks[1]);
    fprintf(stderr, "fake_chunks[1] 改成 0x40 \n");
    fake_chunks[1] = 0x40;
    fprintf(stderr, "把 fake_chunks[2] 的地址赋给 a, %p.\n", &fake_chunks[2]);
    a = &fake_chunks[2];
    fprintf(stderr, "free 掉 a\n");
    free(a);
    fprintf(stderr, "再去 malloc(0x30)，在可以看到申请来的结果在: %p\n", malloc(0x30));
    fprintf(stderr, "Finish\n");
    return 0;
}
```

linux环境：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606980749062-c77e0384-ed85-413c-ad23-f8bd21111a4b.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606980772400-fc7db0bd-407e-4c8a-adaa-8db9b922fe24.png)

开始gdb调试，对代码的第8行下断点，运行程序：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x601250
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> x/100gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000000000	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000020d91 #top_chunk
......(省略内容均为空)
0x601310:	0x0000000000000000	0x0000000000000000
pwndbg> info local 
a = 0x0
fake_chunks = {8, 140737351874144, 140737488347144, 240, 1, 4196141, 140737351932400, 0, 4196064, 4195568}
pwndbg> x/16gx &fake_chunks
0x7fffffffdf90:	0x0000000000000008	0x00007ffff7dd7660 #fake_chunk
0x7fffffffdfa0:	0x00007fffffffe008	0x00000000000000f0
0x7fffffffdfb0:	0x0000000000000001	0x000000000040072d
0x7fffffffdfc0:	0x00007ffff7de59f0	0x0000000000000000
0x7fffffffdfd0:	0x00000000004006e0	0x00000000004004f0
0x7fffffffdfe0:	0x00007fffffffe0d0	0x0000000000000000
0x7fffffffdff0:	0x00000000004006e0	0x00007ffff7a05b97
0x7fffffffe000:	0x0000000000000001	0x00007fffffffe0d8
pwndbg> 
```

对第13行下断点，继续调试：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x601250
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> x/100gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000000000	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000020d91 #top_chunk
......(省略内容均为空)
0x601310:	0x0000000000000000	0x0000000000000000
pwndbg> info local 
a = 0x0
fake_chunks = {8, 64, 140737488347144, 240, 1, 4196141, 140737351932400, 0, 4196064, 4195568}
pwndbg> x/16gx &fake_chunks
0x7fffffffdf90:	0x0000000000000008	0x0000000000000040 #fake_chunk
									#修改了这里
0x7fffffffdfa0:	0x00007fffffffe008	0x00000000000000f0
0x7fffffffdfb0:	0x0000000000000001	0x000000000040072d
0x7fffffffdfc0:	0x00007ffff7de59f0	0x0000000000000000
0x7fffffffdfd0:	0x00000000004006e0	0x00000000004004f0
0x7fffffffdfe0:	0x00007fffffffe0d0	0x0000000000000000
0x7fffffffdff0:	0x00000000004006e0	0x00007ffff7a05b97
0x7fffffffe000:	0x0000000000000001	0x00007fffffffe0d8
pwndbg> 
```

然后fake_chunk_data的地址赋值到a指针，对代码第15行下断点，继续调试：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x601250
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> x/100gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000000000	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000020d91 #top_chunk
......(省略内容均为空)
0x601310:	0x0000000000000000	0x0000000000000000
pwndbg> info local
a = 0x7fffffffdfa0 #指向fake_chunks_data
fake_chunks = {8, 64, 140737488347144, 240, 1, 4196141, 140737351932400, 0, 4196064, 4195568}
pwndbg> x/16gx &fake_chunks
0x7fffffffdf90:	0x0000000000000008	0x0000000000000040
0x7fffffffdfa0:	0x00007fffffffe008	0x00000000000000f0
0x7fffffffdfb0:	0x0000000000000001	0x000000000040072d
0x7fffffffdfc0:	0x00007ffff7de59f0	0x0000000000000000
0x7fffffffdfd0:	0x00000000004006e0	0x00000000004004f0
0x7fffffffdfe0:	0x00007fffffffe0d0	0x00007fffffffdfa0
0x7fffffffdff0:	0x00000000004006e0	0x00007ffff7a05b97
0x7fffffffe000:	0x0000000000000001	0x00007fffffffe0d8
pwndbg> 
```

接下来对fake_chunks进行free：对代码第17行下断点，继续运行程序：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x601250
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> x/100gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000010000	0x0000000000000000
    		#tcache_bin_count
......(省略内容均为空)
0x601050:	0x0000000000000000	0x0000000000000000
0x601060:	0x00007fffffffdfa0	0x0000000000000000
    		#指向fake_chunks_data
0x601070:	0x0000000000000000	0x0000000000000000
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000021
0x601260:	0x0000000000000000	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000020d91
......(省略内容均为空)
0x601310:	0x0000000000000000	0x0000000000000000
pwndbg> info local
a = 0x7fffffffdfa0
fake_chunks = {8, 64, 0, 240, 1, 4196141, 140737351932400, 0, 4196064, 4195568}
pwndbg> x/16gx &fake_chunks
0x7fffffffdf90:	0x0000000000000008	0x0000000000000040
0x7fffffffdfa0:	0x0000000000000000	0x00000000000000f0
0x7fffffffdfb0:	0x0000000000000001	0x000000000040072d
0x7fffffffdfc0:	0x00007ffff7de59f0	0x0000000000000000
0x7fffffffdfd0:	0x00000000004006e0	0x00000000004004f0
0x7fffffffdfe0:	0x00007fffffffe0d0	0x00007fffffffdfa0
0x7fffffffdff0:	0x00000000004006e0	0x00007ffff7a05b97
0x7fffffffe000:	0x0000000000000001	0x00007fffffffe0d8
pwndbg> bin
tcachebins
0x40 [  1]: 0x7fffffffdfa0 ◂— 0x0
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

对代码第18行下断点，当我们malloc之后，就会控制栈上的地址，继续调试程序：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x601250
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> x/100gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000000000	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000020d91 #top_chunk
......(省略内容均为空)
0x601310:	0x0000000000000000	0x0000000000000000
pwndbg> info local
a = 0x7fffffffdfa0
fake_chunks = {8, 64, 0, 240, 1, 4196141, 140737351932400, 0, 4196064, 4195568}
pwndbg> x/16gx &fake_chunks
0x7fffffffdf90:	0x0000000000000008	0x0000000000000040 #现在我们可以控制这里了
0x7fffffffdfa0:	0x0000000000000000	0x00000000000000f0
0x7fffffffdfb0:	0x0000000000000001	0x000000000040072d
0x7fffffffdfc0:	0x00007ffff7de59f0	0x0000000000000000
0x7fffffffdfd0:	0x00000000004006e0	0x00000000004004f0
0x7fffffffdfe0:	0x00007fffffffe0d0	0x00007fffffffdfa0
0x7fffffffdff0:	0x00000000004006e0	0x00007ffff7a05b97
0x7fffffffe000:	0x0000000000000001	0x00007fffffffe0d8
pwndbg> bin
tcachebins
empty
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

现在我们可以控制栈上的内存地址。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606982839624-3c9d026c-6149-4cea-ab13-87b39f2fbe38.png)

finish！

