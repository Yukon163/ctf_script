> 源码下载：[http://ftp.gnu.org/gnu/glibc/](http://ftp.gnu.org/gnu/glibc/)
>
> 参考资料：[https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/tcache_attack-zh/](https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/tcache_attack-zh/)
>
> [https://www.freebuf.com/news/topnews/217458.html](https://www.freebuf.com/news/topnews/217458.html)
>
> [https://xz.aliyun.com/t/7350](https://xz.aliyun.com/t/7350)
>
> [https://www.jianshu.com/p/3ef98e86a913](https://www.jianshu.com/p/3ef98e86a913)
>
> [https://www.yuque.com/u239977/cbzkn3/lkqwpl](https://www.yuque.com/u239977/cbzkn3/lkqwpl)
>
> 文章中采用的是：glibc-2.27源码
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1R9rbyAiImg5-UklJATFpcw](https://pan.baidu.com/s/1R9rbyAiImg5-UklJATFpcw)  密码: anko
>
> --来自百度网盘超级会员V3的分享
>

# Linux环境
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606207027910-a332d0cd-152a-44af-82c7-8644854bbdcf.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606108882806-b1846e61-5f3a-443d-81dc-7297dc7a481f.png)

Linux环境为Ubuntu 18.04.5，glibc版本为2.27

# Tcache overview
> CTFwiki上说“tcache makes heap exploitation easy again”。
>

tcache全名thread local caching，它为每个线程创建一个缓存（cache），从而实现无锁的分配算法，**增加了堆分配的效率，但也引入了更多的不安全性**，让之前很多的代码检查都不再起作用，可以很好的绕过。lib-2.26正式提供了该机制，并默认开启。

tcache和fastbin大致类似，前者每条链上最多可以有 7 个 chunk，free的时候当tcache满了才放入fastbin与unsorted bin。malloc的时候优先去tcache中找。

# tcache struct
tcache有两个相关结构体：tcache_entry 和 tcache_perthread_struct。

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

+ tcache_entry结构体中的值是一个指向tcache_entry结构体的指针，是一个单链表结构。
+ tcache_perthread_struct结构体是用来管理tcache链表的。**<font style="color:#F5222D;">其中的count是一个字节数组，大小共64个字节，对应64个tcache单向链表。每个链表最多7个节点(chunk)，chunk的大小在32bit上是12到512（8byte递增）；在64bits上是24（0x18）到1024（0x400）（16bytes递增）。</font>****<font style="color:#F5222D;">count中每一个字节表示的是tcache每一个链表中有多少个元素。</font>**entries是一个指针数组，数组中共64个元素，对应64个tcache链表，因此 tcache bin中最大为0x400字节），每一个指针指向的是对应tcache_entry结构体的地址。

有趣的是，tcache_perthread_struct结构一般是在heapbase的起始位置。对应tcache的数目是char类型。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606208435687-a94e0e29-3230-4721-b19d-fa726a03a8af.png)

# tcache_get() and tcache_put();
tcache有两个重要的函数，分别为tcache_get()和tcache_put();

> tcache_get是将被free掉的从tcache取出（malloc）
>
> tcache_put是将被free掉的chunk放入tcache单向链表中（free）
>

```c
#glibc-malloc源码中的第2923-29246行
/* Caller must ensure that we know tc_idx is valid and there's room
   for more chunks.  */
static __always_inline void
tcache_put (mchunkptr chunk, size_t tc_idx)
{
  tcache_entry *e = (tcache_entry *) chunk2mem (chunk);
  assert (tc_idx < TCACHE_MAX_BINS);
  e->next = tcache->entries[tc_idx];
  tcache->entries[tc_idx] = e;
  ++(tcache->counts[tc_idx]);
}

/* Caller must ensure that we know tc_idx is valid and there's
   available chunks to remove.  */
static __always_inline void *
tcache_get (size_t tc_idx)
{
  tcache_entry *e = tcache->entries[tc_idx];
  assert (tc_idx < TCACHE_MAX_BINS);
  assert (tcache->entries[tc_idx] > 0);
  tcache->entries[tc_idx] = e->next;
  --(tcache->counts[tc_idx]);
  return (void *) e;
}
```

**<font style="color:#F5222D;">这两个函数会在函数_int_free和_libc_malloc的开头被调用</font>**，其中tcache_put所请求的分配大小**<font style="color:#F5222D;">不大于0x408</font>**并且当给定大小的 tcache bin 未满时调用。**<font style="color:#F5222D;">一个 tcache bin 中的最大块数mp_.tcache_count是7，</font>**具体代码如下面所示：

```c
#一个 tcache bin 中的最大块数mp_.tcache_count是7。
/* This is another arbitrary limit, which tunables can change.  Each
   tcache bin will hold at most this number of chunks.  */
# define TCACHE_FILL_COUNT 7
#endif
```

再来看一下tcache_get()源码：

```c
/* Caller must ensure that we know tc_idx is valid and there's
   available chunks to remove.  */
static __always_inline void *
tcache_get (size_t tc_idx)
{
  tcache_entry *e = tcache->entries[tc_idx];//根据索引找到tcache链表的头指针
  assert (tc_idx < TCACHE_MAX_BINS);//tcache计数器检查1
  assert (tcache->entries[tc_idx] > 0);//tcache计数器检查2
  tcache->entries[tc_idx] = e->next;//将chunk取出
  --(tcache->counts[tc_idx]);//tcache计数器减一
  return (void *) e;
}
```

什么情况会**<font style="color:#13C2C2;">调用tcache_get</font>**函数呢（什么时候会用到tcache中空闲的chunk）？

1. 在调用malloc_hook之后，_int_malloc之前，如果tcache中有合适的chunk，那么就从tcache中取出：
2. 遍历完unsorted bin后，若tcachebin中有对应大小的chunk，从tcache中取出：
3. 遍历unsorted bin时，大小不匹配的chunk会被放入对应的bins，若达到tcache_unsorted_limit限制且之前已经存入过chunk则在此时取出（默认无限制）。

---

在内存分配的 malloc 函数中有多处，会将内存块移入 tcache 中。

**<font style="color:#F5222D;">tcache 为空时：</font>**

（1）首先，申请的内存块符合 fastbin 大小时并且在 fastbin 内找到可用的空闲块时，会把该 fastbin 链上的其他内存块放入 tcache 中。

（2）其次，申请的内存块符合 smallbin 大小时并且在 smallbin 内找到可用的空闲块时，会把该 smallbin 链上的其他内存块放入 tcache 中。

（3）当在 unsorted bin 链上循环处理时，当找到大小合适的链时，并不直接返回，而是先放到 tcache 中，继续处理。

上述3中情况将chunk放入tcache中后，在将符合申请条件的chunk返回利用。

在 tcache_get 中，仅仅检查了tc_idx。前面说过，**<font style="color:#F5222D;">可以将 tcache 当作一个类似于 fastbin 的单独链表，只是它的 check并没有 fastbin 那么复杂，因此我们可以利用这一点来进行attack。</font>**

# the <font style="color:#333333;">difference between </font>fastbin and tcache
来说一下tcache与fastbin链表的异同点：

+ tcachebin和fastbin都是通过chunk的fd字段来作为链表的指针。
+ **<font style="color:#F5222D;">tcachebin的链表指针是指向下一个chunk的fd字段，</font>****<font style="color:#F5222D;">fastbin</font>****<font style="color:#F5222D;">的链表指针是指向下一个chunk的pre_size字段</font>**
+ 在_int_free中，最开始就先检查chunk的size是否落在了tcache的范围内，且对应的tcache未满，将其放入tcache中。
+ **<font style="color:#13C2C2;">在_int_malloc中，如果从fastbin中取出了一个块，那么会把剩余的块放入tcache中直至填满tcache（smallbin中也是一样）</font>**
+ 如果进入了unsortedbin，且chunk的size和当前申请的大小精确匹配，那么在tcache未满的情况下会将其放入到tcachebin中

> 准确的来说，tcache中的“fd指针”应该改为“next指针”
>

# A demo about tcache
> 编译命令：gcc -g -fno-stack-protector -z execstack -no-pie -z norelro demo.c -o demo
>

```c
#include<stdio.h>
#include<stdlib.h>
int main(){
	void *p[10]={0};
	int i,j,m;
	for(i = 0 ;i < 10 ; i++){
		p[i]=malloc(0x10);
	}
	for(j = 0 ;j < 10 ; j++){
		free(p[j]);
		p[j]=NULL;
	}
	for(m = 0 ; m < 5;m++){
		p[m]=malloc(0x10);
	}
	return 0;
}
```

编译完成之后，使用gdb开始调试程序：

首先对代码的第9行下断点，然后运行程序，此时内存状况如下：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x601250
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x601270
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x601290
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x6012b0
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x6012d0
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x6012f0
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x601310
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x601330
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x601350
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x601370
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x601390
Size: 0x20c71

pwndbg> x/120gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000000000	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000000021 #chunk2
0x601280:	0x0000000000000000	0x0000000000000000
0x601290:	0x0000000000000000	0x0000000000000021 #chunk3
0x6012a0:	0x0000000000000000	0x0000000000000000
0x6012b0:	0x0000000000000000	0x0000000000000021 #chunk4
0x6012c0:	0x0000000000000000	0x0000000000000000
0x6012d0:	0x0000000000000000	0x0000000000000021 #chunk5
0x6012e0:	0x0000000000000000	0x0000000000000000
0x6012f0:	0x0000000000000000	0x0000000000000021 #chunk6
0x601300:	0x0000000000000000	0x0000000000000000
0x601310:	0x0000000000000000	0x0000000000000021 #chunk7
0x601320:	0x0000000000000000	0x0000000000000000
0x601330:	0x0000000000000000	0x0000000000000021 #chunk8
0x601340:	0x0000000000000000	0x0000000000000000
0x601350:	0x0000000000000000	0x0000000000000021 #chunk9
0x601360:	0x0000000000000000	0x0000000000000000
0x601370:	0x0000000000000000	0x0000000000000021 #chunk10
0x601380:	0x0000000000000000	0x0000000000000000
0x601390:	0x0000000000000000	0x0000000000020c71 #top_chunk
0x6013a0:	0x0000000000000000	0x0000000000000000
0x6013b0:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &main_arena
0x7ffff7dcfc40 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc50 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc60 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc70 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc80 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc90 <main_arena+80>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfca0 <main_arena+96>:	0x0000000000601390	0x0000000000000000
    							#top_chunk
0x7ffff7dcfcb0 <main_arena+112>:	0x00007ffff7dcfca0	0x00007ffff7dcfca0
pwndbg> info local
p = {0x601260, 0x601280, 0x6012a0, 0x6012c0, 0x6012e0, 0x601300, 0x601320, 0x601340, 0x601360, 0x601380}
i = 10
j = 0
m = 32767（注：m在定义时未被赋值，故数为随机值）
pwndbg> 
```

> 注意，第一个大小为0x251的chunk是tcache_perthread_struct结构体，其用来管理tcache链表
>

对代码的第11行下断点，由于这是个循环，逐步调试程序：

```c
#第一次循环：
tcachebins
0x20 [  1]: 0x601260 ◂— 0x0
#第二次循环
pwndbg> bin
tcachebins
0x20 [  2]: 0x601280 —▸ 0x601260 ◂— 0x0
#第三次循环
pwndbg> bin
tcachebins
0x20 [  3]: 0x6012a0 —▸ 0x601280 —▸ 0x601260 ◂— 0x0
#......
#第十次循环：
pwndbg> bin
tcachebins
0x20 [  7]: 0x601320 —▸ 0x601300 —▸ 0x6012e0 —▸ 0x6012c0 —▸ 0x6012a0 —▸ 0x601280 —▸ 0x601260 ◂— 0x0
fastbins
0x20: 0x601370 —▸ 0x601350 —▸ 0x601330 ◂— 0x0
```

逐步看一下tcache_perthread_struct结构体：

```c
#第一次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000001	0x0000000000000000
    		#tcache中chunk数量
            ......
0x601050:	0x0000000000601260	0x0000000000000000
    		#指向chunk1_data
---------------------------------------------------
#第二次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000002	0x0000000000000000
            ......
0x601050:	0x0000000000601280	0x0000000000000000
    		#指向chunk2_data
---------------------------------------------------
#第三次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000003	0x0000000000000000
            ......
0x601050:	0x00000000006012a0	0x0000000000000000
    		#指向chunk3_data
---------------------------------------------------
#第四次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000005	0x0000000000000000
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x00000000006012c0	0x0000000000000000
    		#指向chunk4_data
---------------------------------------------------
#第五次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000005	0x0000000000000000
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x00000000006012e0	0x0000000000000000
    		#指向chunk5_data
---------------------------------------------------
#第六次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000006	0x0000000000000000
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000601300	0x0000000000000000
    		#指向chunk6_data
---------------------------------------------------
#第七次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000007	0x0000000000000000
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000601320	0x0000000000000000
    		#指向chunk7_data
---------------------------------------------------
#第八次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000007	0x0000000000000000
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000601320	0x0000000000000000
    	    #指向chunk7_data
---------------------------------------------------
#第九次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000007	0x0000000000000000
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000601320	0x0000000000000000
			#指向chunk7_data
---------------------------------------------------
#第十次free
pwndbg> x/12gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000007	0x0000000000000000
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000601320	0x0000000000000000
    		#指向chunk7_data
pwndbg> 
```

在程序进行第7次free之后，tcache_perthread_struct中的指针所指向的地址不在变化，这是因为free 7次之后tcache中已经放满，故指针地址不会再变化。

从上面可以得出一个结论：当程序回收属于fastbin的堆块时，若tcache未满，程序会将free掉的chunk优先放入tcache中 。

再次查看内存的情况：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x601250
Size: 0x21
fd: 0x00

Free chunk (tcache) | PREV_INUSE
Addr: 0x601270
Size: 0x21
fd: 0x601260

Free chunk (tcache) | PREV_INUSE
Addr: 0x601290
Size: 0x21
fd: 0x601280

Free chunk (tcache) | PREV_INUSE
Addr: 0x6012b0
Size: 0x21
fd: 0x6012a0

Free chunk (tcache) | PREV_INUSE
Addr: 0x6012d0
Size: 0x21
fd: 0x6012c0

Free chunk (tcache) | PREV_INUSE
Addr: 0x6012f0
Size: 0x21
fd: 0x6012e0

Free chunk (tcache) | PREV_INUSE
Addr: 0x601310
Size: 0x21
fd: 0x601300

Free chunk (fastbins) | PREV_INUSE
Addr: 0x601330
Size: 0x21
fd: 0x00

Free chunk (fastbins) | PREV_INUSE
Addr: 0x601350
Size: 0x21
fd: 0x601330

Free chunk (fastbins) | PREV_INUSE
Addr: 0x601370
Size: 0x21
fd: 0x601350

Top chunk | PREV_INUSE
Addr: 0x601390
Size: 0x20c71
-----------------------------------------------------------------------
#跳出循环后
pwndbg> info local
p = {0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}
i = 10
j = 10
m = 32767
```

> 吐槽一句ubuntu 18中的pwndbg真好用，在ubuntu 16中简直是个残废。。。
>

跳出循环后，看一下具体的内存：

```c
pwndbg> x/120gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x601010:	0x0000000000000007	0x0000000000000000
    		#tcache中chunk的数量
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000601320	0x0000000000000000		
......（省略内容均为空）
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000000000	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000000021 #chunk2
0x601280:	0x0000000000601260	0x0000000000000000
0x601290:	0x0000000000000000	0x0000000000000021 #chunk3
0x6012a0:	0x0000000000601280	0x0000000000000000
0x6012b0:	0x0000000000000000	0x0000000000000021 #chunk4
0x6012c0:	0x00000000006012a0	0x0000000000000000
0x6012d0:	0x0000000000000000	0x0000000000000021 #chunk5
0x6012e0:	0x00000000006012c0	0x0000000000000000
0x6012f0:	0x0000000000000000	0x0000000000000021 #chunk6
0x601300:	0x00000000006012e0	0x0000000000000000
0x601310:	0x0000000000000000	0x0000000000000021 #chunk7
0x601320:	0x0000000000601300	0x0000000000000000
0x601330:	0x0000000000000000	0x0000000000000021 #chunk8
0x601340:	0x0000000000000000	0x0000000000000000
0x601350:	0x0000000000000000	0x0000000000000021 #chunk9
0x601360:	0x0000000000601330	0x0000000000000000
0x601370:	0x0000000000000000	0x0000000000000021 #chunk10
0x601380:	0x0000000000601350	0x0000000000000000
0x601390:	0x0000000000000000	0x0000000000020c71 #top_chunk
0x6013a0:	0x0000000000000000	0x0000000000000000
0x6013b0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

对代码的第14行下断点，继续调试。这里直接说结论吧：

```c
第一次malloc会使用chunk7
第二次malloc会使用chunk6
......
第五次malloc会使用chunk3
```

再结合一下前面放入tcache中chunk的顺序，可以总结出结论：

**<font style="color:#F5222D;">当申请属于fastbin大小的chunk时，若tcache中仍有chunk，首先将tcache末尾的chunk取出</font>**

**<font style="color:#13C2C2;">tcache的特性：后进先出</font>**

# tcache attack
## Tcache dup
fastbin中double free的利用，我们需要构成a->b->a这种形式的free链。而在tcache中，利用的是 tcache_put函数的不严谨，所以我们可以对同一个 chunk 多次 free，造成 cycliced list。

## Tcache_house_of_spirit
与fastbin的house_of_spirit类似。free掉伪造的chunk，再次malloc获得可操作的地址。**<font style="color:#F5222D;">同样的，</font>****<font style="color:#F5222D;">但是</font>****<font style="color:#F5222D;">这里更简单，free的时候不会对size做前后堆块的安全检查，所以只需要size满足对齐就可以成功free掉伪造的chunk（其实就是一个地址）。</font>**

## Tcache_overlapping_chunks
可以说和house of spirit是一个原因，由于size的不安全检查，我们可以修改将被free的chunk的size改为一个较大的值（将别的chunk包含进来），再次分配就会得到一个包含了另一个chunk的大chunk。同样的道理，也可以改写pre_size向前overlapping。

## Tcache_poisoning
这个着眼于tcache新的结构，前面提到过tcachebin中的next指针其实相当于fastbin下的fd指针（而且两者都没有很多的检查），将已经在tcache链表中的chunk的fd改写到目的地址，就可以malloc合适的size得到控制权。

## Tcache_perthread_corruption
tcache_perthread_struct 是整个 tcache 的管理结构，如果能控制这个结构体，那么无论malloc 的 size 是多少，地址都是可控的。



各个攻击方式将在后续文章中慢慢介绍。



