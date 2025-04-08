> 参考资料：
>
> [https://bbs.pediy.com/thread-257742.htm](https://bbs.pediy.com/thread-257742.htm)
>
> [https://ctf-wiki.org/pwn/linux/glibc-heap/heap_structure/#small-bin](https://ctf-wiki.org/pwn/linux/glibc-heap/heap_structure/#small-bin) #smallbin注释
>
> [https://ctf-wiki.org/pwn/linux/glibc-heap/house_of_force/](https://ctf-wiki.org/pwn/linux/glibc-heap/house_of_force/) #top_chunk注释
>
> [https://blog.csdn.net/qq_41453285/article/details/97627411](https://blog.csdn.net/qq_41453285/article/details/97627411)
>
> **<font style="color:#F5222D;">研究对象为glibc 2.23源码（无tcachebin）。</font>**
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/15k8gxjH_cw8YZ9HtvG_aXg](https://pan.baidu.com/s/15k8gxjH_cw8YZ9HtvG_aXg)  密码: q5bf
>
> --来自百度网盘超级会员V3的分享
>

# 前言
由于smallbin会牵扯到fastbin的合并问题，因此在了解smallbin_attack之前，先来研究一下fastbin的合并问题。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1614050546386-9cc1c01f-e23d-475d-81e6-5cc7ca0f0dd1.png)

> 测试环境
>

# fastbin回顾
放入fastbin的chunk要求在0x20到0x80字节，fastbin有两个特点：

+ fastbin由单链表构成，链表的总个数为10，总称为fastbinY数组。
+ 在fastbin中，无论是添加还是移除chunk，都对**<font style="color:#F5222D;">链表尾</font>**进行操作，采取**<font style="color:#F5222D;">后入先出</font>**算法。fastbinsY数组中每个fastbin元素均指向了该链表的尾结点，而尾结点通过其fd指针指向前一个结点。

如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611545660952-e21ca201-8ab9-44d5-ac2e-855900760b3c.png)

> 注：fastbinY数组可以在main_arena开头找到。
>

# <font style="background-color:#FEFEFE;">smallbin的介绍</font>
<font style="background-color:#FEFEFE;">首先来了解一下smallbin：</font>

<font style="background-color:#FEFEFE;">smallbins是最容易理解的基础bin。在32/64位系统上小于512字节（0x200）/1024字节（0x400）的每个chunk都有一个对应的smallbin。 由于每个small bin仅存储一个大小的chunk，因此在这些列表中插入和删除条目的速度非常快。</font>

<font style="background-color:#FEFEFE;">smallbins中每个chunk的大小与其所在的bin的index的关系为：chunk_size = 2*SIZE_SZ *index，具体如下：</font>

| 下标（index） | SIZE_SZ=4（32 位） | SIZE_SZ=8（64 位） |
| :--- | :--- | :--- |
| 2 | 16 | 32 |
| 3 | 24 | 48 |
| 4 | 32 | 64 |
| 5 | 40 | 80 |
| x | 2*4*x | 2*8*x |
| 63 | 504 | 1008 |


smallbins中一共有 **<font style="color:#F5222D;">62 </font>**个**<font style="color:#F5222D;">循环双向链表</font>**，**<font style="color:#F5222D;">每个链表中存储的 chunk 大小都一致</font>**。比如对于32位系统来说，下标2 对应的双向链表中存储的chunk大小为均为 16 字节。每个链表都有链表头结点，这样可以方便对于链表内部结点的管理。此外，**smallbins中每个 bin 对应的链表采用 FIFO（先入先出）的规则**，所以同一个链表中先被释放的chunk会先被分配出去。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1614071895874-bc1b2e2d-9a63-4e4b-b0de-77797c487aeb.png)

smallbin相关的宏如下：

```c
#define NSMALLBINS 64
#define SMALLBIN_WIDTH MALLOC_ALIGNMENT
// 是否需要对small bin的下标进行纠正
#define SMALLBIN_CORRECTION (MALLOC_ALIGNMENT > 2 * SIZE_SZ)
#define MIN_LARGE_SIZE ((NSMALLBINS - SMALLBIN_CORRECTION) * SMALLBIN_WIDTH)
//判断chunk的大小是否在small bin范围内
#define in_smallbin_range(sz)                                                  \
    ((unsigned long) (sz) < (unsigned long) MIN_LARGE_SIZE)
// 根据chunk的大小得到small bin对应的索引。
#define smallbin_index(sz)                                                     \
    ((SMALLBIN_WIDTH == 16 ? (((unsigned) (sz)) >> 4)                          \
                           : (((unsigned) (sz)) >> 3)) +                       \
     SMALLBIN_CORRECTION)
```

**或许可能会疑惑，那fastbin与small bin中chunk的大小会有很大一部分重合啊，那smallbin中对应大小的bin是不是就没有什么作用？** 其实不然，fastbin中的chunk是有可能被放到smallbin中去的，在后面分析具体的源代码时会有深刻的体会。

# <font style="background-color:#FEFEFE;">合并时机</font>
<font style="background-color:#FEFEFE;">fastbin会在以下情况下进行合并（合并是对所有fastbin中的已经释放的chunk而言）。</font>

## malloc
+ 在申请large chunk时，fastbin会进行合并
+ 申请的chunk大小大于等于top_chunk的大小时。

## free
+ free的堆块大小大于fastbin中的最大size。（**<font style="color:#F5222D;">注意：这里并不是指当前fastbin中最大chunk的size，而是指fastbin中所定义的最大chunk的size，是一个固定值。</font>**）

<font style="background-color:#FEFEFE;">另外：malloc_consolidate既可以作为fastbin的初始化函数，也可以作为fastbin的合并函数。</font>

> <font style="background-color:#FEFEFE;">consolidate (v.)合并</font>
>

# 情况分析
## malloc-申请large chunk
> 在申请large chunk时，fastbin会进行合并
>

这种情况的相关malloc代码如下：

```c
#malloc.c中第3405-3434行
  if (in_smallbin_range (nb)) //nb为所申请的chunk的真实大小。
    {//若申请的chunk大小在smallbin中
      idx = smallbin_index (nb);//获取smallbin的索引
      bin = bin_at (av, idx); //获取smallbinb中的chunk指针

      if ((victim = last (bin)) != bin)
        {// 先执行 victim= last(bin)，获取 small bin 的最后一个 chunk
         // 如果 victim = bin ，那说明该 bin 为空。
         // 如果不相等，那么会有两种情况
          
          if (victim == 0) /* initialization check */ //第一种情况，smallbin还没有初始化。
            
              malloc_consolidate (av);  //执行初始化，fastbin中的chunk进行合并
          else //第二种情况，smallbin中存在空闲的 chunk
            {
              bck = victim->bk; //获取 small bin 中倒数第二个 chunk 。
	if (__glibc_unlikely (bck->fd != victim)) // 检查 bck->fd 是不是 victim，防止伪造
                {
                  errstr = "malloc(): smallbin double linked list corrupted";
                  goto errout;
                }
              set_inuse_bit_at_offset (victim, nb); // 设置 victim 对应的 inuse 位
              bin->bk = bck; //修改 smallbin 链表，将 small bin 的最后一个 chunk 取出来
              bck->fd = bin;

              if (av != &main_arena)// 如果不是 main_arena，设置对应的标志
                victim->size |= NON_MAIN_ARENA;
              check_malloced_chunk (av, victim, nb);// 细致的检查
              void *p = chunk2mem (victim);// 将申请到的 chunk 转化为对应的 mem 状态
              alloc_perturb (p, bytes);// 如果设置了 perturb_type , 则将获取到的chunk初始化为 perturb_type ^ 0xff
              return p;
            }
        }
    }
  else //若申请的大小不在smallbin中
    {
      idx = largebin_index (nb); //获取largebin中的索引
      if (have_fastchunks (av))	 //判断是否有fastbin chunk
        malloc_consolidate (av);  //整理fastbin
    }
```

在第一个if语句首先判断利用in_smallbin_range (nb)来判断申请的chunk是否在smallbin的范围内，若如果smallbin还未初始化，就调用malloc_consolidate (av);合并fastbin来初始化smallbin；若申请的chunk不在smallbin的范围中，获取要申请的堆块大小在largebin中的索引，然后对fastbin进行整理。

示例程序如下：

> 编译命令：gcc - g test1.c -o test1
>

```c
#include<string.h>
#include<stdio.h>
#include<stdlib.h>
int main(){
    void *ptr1,*ptr2,*ptr3,*ptr4;
    ptr1 = malloc(0x20);
    ptr2 = malloc(0x20);
    ptr3 = malloc(0x30);          //avoid merge with top chunk
    strcpy(ptr1,"aaaaaaaa");
    strcpy(ptr2,"bbbbbbbb");
    strcpy(ptr3,"cccccccc");
    free(ptr1);
    free(ptr2);
    ptr4 = malloc(0x500);
}
```

> malloc(0x30)的作用是防止前两个chunk和top_chunk进行接触
>

在free了ptr1与ptr2之后，此时的堆情况：

```c
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x602030 —▸ 0x602000 ◂— 0x0
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

在malloc了一个large chunk之后，此时的堆情况：

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
all: 0x0
smallbins
0x60 [corrupted]
FD: 0x602000 —▸ 0x7ffff7dd1bc8 (main_arena+168) ◂— 0x602000
BK: 0x602000 ◂— 0x0
largebins
empty
pwndbg> 
```

我们发现fastbin已经进行了合并到了smallbin中。

这里有人可能觉得这么做太激进了，因为可能在我们申请large chunk的时候根本用不上这些释放的空间，但是首先这能很好的解决碎片化问题，其次程序很少会连续的既使用小堆块，又使用大堆块，因此这种情况发生的并不多。

## <font style="background-color:#FEFEFE;">malloc-扩展top_chunk</font>
<font style="background-color:#FEFEFE;">关键代码如下：</font>

```c
#malloc.c：第3777-3832行
	use_top:
		#......（注释略）
      victim = av->top;
      size = chunksize (victim); // 获取当前的top chunk，并计算其对应的大小

      if ((unsigned long) (size) >= (unsigned long) (nb + MINSIZE)) 
        { //判断top_chunk_size
          remainder_size = size - nb;
          remainder = chunk_at_offset (victim, nb);
          av->top = remainder;
          set_head (victim, nb | PREV_INUSE |
                    (av != &main_arena ? NON_MAIN_ARENA : 0));
          set_head (remainder, remainder_size | PREV_INUSE);

          check_malloced_chunk (av, victim, nb);
          void *p = chunk2mem (victim);
          alloc_perturb (p, bytes);
          return p;
        }

      /* When we are using atomic ops to free fast chunks we can get
         here for all block sizes.  */
      else if (have_fastchunks (av))  //假若存在fast_chunk
        {
          malloc_consolidate (av);    //对fastbin中的chunk进行合并
          /* restore original bin index */
          if (in_smallbin_range (nb))   
            idx = smallbin_index (nb);
          else
            idx = largebin_index (nb);
        }

      /*
         Otherwise, relay to handle system-dependent cases
       */
      else
        {
          void *p = sysmalloc (nb, av);  //扩展top_chunk
          if (p != NULL)
            alloc_perturb (p, bytes);
          return p;
        }
```

首先判断top chunk的size是否足够我们进行下一次的分配，如果不够，那么判断是否有fastbin的存在，如果存在fastbin，那么则进行合并，然后再去与smallbin和largebin匹配。如果都不匹配，则扩展top chunk。

> 建议看一下上面的源码更容易理解。
>

我们还是通过一个小程序来说明:

```c
#include<string.h>
#include<stdio.h>
#include<stdlib.h>
int main(){
        void *ptr1,*ptr2,*ptr3,*ptr4,*ptr5;
        ptr1 = malloc(0x20);
        ptr2 = malloc(0x20);
        ptr3 = malloc(0x20f00);
        ptr4 = malloc(0x30);         
        strcpy(ptr1,"aaaaaaaa");
        strcpy(ptr2,"bbbbbbbb");
        strcpy(ptr3,"cccccccc");
        free(ptr1);
        free(ptr2);
        ptr5 = malloc(0x70);
}
```

在malloc(0x70)之前,此时top chunk的size已经小于0x70：

```c
pwndbg> bins
fastbins
0x20: 0x0
0x30: 0x602030 —▸ 0x602000 ◂— 0x0
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
pwndbg> top_chunk
Top chunk
Addr: 0x622fb0
Size: 0x00
pwndbg> x/4gx 0x622fb0
0x622fb0:	0x0000000000000000	0x0000000000000051 #top_chunk_size
0x622fc0:	0x0000000000000000	0x0000000000000000
pwndbg>
```

然后我们再申请一个比较小但是大于top size的chunk：

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
all: 0x0
smallbins
0x60 [corrupted]
FD: 0x602000 —▸ 0x7ffff7dd1bc8 (main_arena+168) ◂— 0x602000
BK: 0x602000 ◂— 0x0
largebins
empty
pwndbg> top_chunk
Top chunk
Addr: 0x623030
Size: 0x00
pwndbg> x/4gx 0x623030
0x623030:	0x0000000000000000	0x0000000000020fd1
0x623040:	0x0000000000000000	0x0000000000000000
pwndbg>
```

<font style="background-color:#FEFEFE;">此时对fastbin进行了合并，合并到了smallbin中。</font>

## <font style="background-color:#FEFEFE;">free-over FASTBIN_CONSOLIDATION_THRESHOLD</font>
> <font style="background-color:#FEFEFE;">在free(chunk)的时候，如果chunk的大小大于fastbin中所定义的最大堆块的大小，则进行合并。</font>
>

首先要弄清楚FASTBIN_CONSOLIDATION_THRESHOLD这一长串的鬼东西是什么，直译来说就是fastbin合并阈值，这个东西定义在malloc.c的第1621行：

```c
#define FASTBIN_CONSOLIDATION_THRESHOLD  (65536UL)
```

```c
#malloc.c 第4074-4076行
	if ((unsigned long)(size) >= FASTBIN_CONSOLIDATION_THRESHOLD) {
      if (have_fastchunks(av))
	malloc_consolidate(av); //合并fastbin_chunk
```

+ **<font style="color:#3399EA;">为什么设计这个宏定义：</font>**fastbins中的chunk本来就定义为不会进行合并，但是当被free的fastbin_chunk与该chunk相邻的chunk合并后的大小大于FASTBIN_CONSOLIDATION_THRESHOLD时，此时内存碎片可能就比较多了，我们就需要将fastbins中的chunk都进行合并（调用malloc_consolidate函数）以减少内存碎片
+ **<font style="color:#3399EA;">何处使用：</font>**在_int_free函数中被使用，malloc_consolidate函数可以将fastbins中能和其它chunk合并的fast_chunk进行合并，然后将合并后的碎片进行consolidate

一个示例：

```c
#include<string.h>
#include<stdio.h>
#include<stdlib.h>
int main(){
        void *ptr1,*ptr2,*ptr3,*ptr4;
        ptr1 = malloc(0x70);
        ptr2 = malloc(0x70);
        ptr3 = malloc(0x70);  // avoid merge with top chunk
        ptr4 = malloc(0x100);
        strcpy(ptr1,"aaaaaaaa");
        strcpy(ptr2,"bbbbbbbb");
        strcpy(ptr3,"cccccccc");
        free(ptr1);
        free(ptr2);
        free(ptr4);
}
```

在free(ptr1),free(ptr2)之后，此时的堆情况：

```c
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x602080 —▸ 0x602000 ◂— 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg> 
```

在free(ptr4)以后的堆情况：

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
FD: 0x602000 —▸ 0x7ffff7dd1b78 (main_arena+88) ◂— 0x602000
BK: 0x602000 ◂— 0x0
smallbins
empty
largebins
empty
pwndbg> 
```

可以看到fastbin被合并了。需要注意由于是合并到了unsortedbin中，所以有时我们可以利用这里泄漏出libc基地址。

```c
pwndbg> x/6gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000101
0x602010:	0x00007ffff7dd1b78	0x00007ffff7dd1b78
0x602020:	0x0000000000000000	0x0000000000000000
pwndbg>
```

# 探究fastbin合并过程-malloc_consolidate
在前面我们知道malloc_consolidate函数的作用是对堆中的碎片chunk进行合并整理，减少堆中的碎片。

首先要说明一点，malloc_consolidate是由于unsortedbin的机制而存在的，因为unsortedbin的unsorted的意思本身就是杂乱无章的，没有分类的。通过malloc_consolidate机制来将unsortedbin中的堆块整理到largebin和smallbin中。

那么fastbin到底是怎么在进行合并的呢？这里我们结合malloc_consolidate函数来分析：

```c
static void malloc_consolidate(mstate av)
{
  mfastbinptr*    fb;                 /* current fastbin being consolidated */
  mfastbinptr*    maxfb;              /* last fastbin (for loop control) */
  mchunkptr       p;                  /* current chunk being consolidated */
  mchunkptr       nextp;              /* next chunk to consolidate */
  mchunkptr       unsorted_bin;       /* bin header */
  mchunkptr       first_unsorted;     /* chunk to link to */

  /* These have same use as in free() */
  mchunkptr       nextchunk;
  INTERNAL_SIZE_T size;
  INTERNAL_SIZE_T nextsize;
  INTERNAL_SIZE_T prevsize;
  int             nextinuse;
  mchunkptr       bck;
  mchunkptr       fwd;

  /*
    If max_fast is 0, we know that av hasn't
    yet been initialized, in which case do so below
  */

  if (get_max_fast () != 0) {
    clear_fastchunks(av);

    unsorted_bin = unsorted_chunks(av);

    /*
      Remove each chunk from fast bin and consolidate it, placing it
      then in unsorted bin. Among other reasons for doing this,
      placing in unsorted bin avoids needing to calculate actual bins
      until malloc is sure that chunks aren't immediately going to be
      reused anyway.
    */

    maxfb = &fastbin (av, NFASTBINS - 1);
    fb = &fastbin (av, 0);
    do {
      p = atomic_exchange_acq (fb, 0);
      if (p != 0) {
	do {
	  check_inuse_chunk(av, p);
	  nextp = p->fd;

	  /* Slightly streamlined version of consolidation code in free() */
	  size = p->size & ~(PREV_INUSE|NON_MAIN_ARENA);
	  nextchunk = chunk_at_offset(p, size);
	  nextsize = chunksize(nextchunk);

	  if (!prev_inuse(p)) {
	    prevsize = p->prev_size;
	    size += prevsize;
	    p = chunk_at_offset(p, -((long) prevsize));
	    unlink(av, p, bck, fwd);
	  }

	  if (nextchunk != av->top) {
	    nextinuse = inuse_bit_at_offset(nextchunk, nextsize);

	    if (!nextinuse) {
	      size += nextsize;
	      unlink(av, nextchunk, bck, fwd);
	    } else
	      clear_inuse_bit_at_offset(nextchunk, 0);

	    first_unsorted = unsorted_bin->fd;
	    unsorted_bin->fd = p;
	    first_unsorted->bk = p;

	    if (!in_smallbin_range (size)) {
	      p->fd_nextsize = NULL;
	      p->bk_nextsize = NULL;
	    }

	    set_head(p, size | PREV_INUSE);
	    p->bk = unsorted_bin;
	    p->fd = first_unsorted;
	    set_foot(p, size);
	  }

	  else {
	    size += nextsize;
	    set_head(p, size | PREV_INUSE);
	    av->top = p;
	  }

	} while ( (p = nextp) != 0);

      }
    } while (fb++ != maxfb);
  }
  else {
    malloc_init_state(av);
    check_malloc_state(av);
  }
}
```

大概过程（会循环fastbin中的每一块）：

1、首先将与该块相邻的下一块的PREV_INUSE置为1。

2、如果相邻的上一块未被占用，则合并，再判断相邻的下一块是否被占用，若未被占用，则合并。

3、**<font style="color:#F5222D;">不管是否完成合并，都会把fastbin或者完成合并以后的bin放到unsortedbin中。</font>**（如果与top_hunk相邻，则合并到top_chunk中）。

还是通过小程序来演示：

```c
#include<string.h>
#include<stdio.h>
#include<stdlib.h>
int main(){
    void *ptr1,*ptr2,*ptr3,*ptr4,*ptr5,*ptr6,*ptr7;
    ptr1 = malloc(0x20);
    ptr2 = malloc(0x20);
    ptr3 = malloc(0x20);
    ptr4 = malloc(0x20);
    ptr5 = malloc(0x20);
    ptr6 = malloc(0x100);
    strcpy(ptr1,"aaaaaaaa");
    strcpy(ptr2,"bbbbbbbb");
    strcpy(ptr3,"cccccccc");
    strcpy(ptr4,"dddddddd");
    strcpy(ptr5,"eeeeeeee");
    strcpy(ptr6,"ffffffff");
    free(ptr1);
    free(ptr2);
    free(ptr4);
    free(ptr6);
}
```

在没有合并之前的堆：（对21行下断点）

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611566270093-0ddea57e-7ddc-4450-aac4-31ddd774e88f.png)

```c
pwndbg> x/100gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000031 #malloc(0x20)
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000000
0x602030:	0x0000000000000000	0x0000000000000031 #malloc(0x20)
0x602040:	0x0000000000602000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000031 #malloc(0x20)
0x602070:	0x6363636363636363	0x0000000000000000
0x602080:	0x0000000000000000	0x0000000000000000
0x602090:	0x0000000000000000	0x0000000000000031 #malloc(0x20)
0x6020a0:	0x0000000000602030	0x0000000000000000
0x6020b0:	0x0000000000000000	0x0000000000000000
0x6020c0:	0x0000000000000000	0x0000000000000031 #malloc(0x20)
0x6020d0:	0x6565656565656565	0x0000000000000000
0x6020e0:	0x0000000000000000	0x0000000000000000
0x6020f0:	0x0000000000000000	0x0000000000000111 #malloc(0x100)
0x602100:	0x6666666666666666	0x0000000000000000
......
0x602200:	0x0000000000000000	0x0000000000020e01 #top_chunk
......
0x602310:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

合并之后的堆：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611566301796-bc4f5713-2b7b-4d5b-abe8-8dad7705c73a.png)

```c
pwndbg> x/100gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000061 #free(0x20) -unsortedbin
0x602010:	0x0000000000602090	0x00007ffff7dd1b78
0x602020:	0x0000000000000000	0x0000000000000000
0x602030:	0x0000000000000000	0x0000000000000031 #原free(0x20)
0x602040:	0x0000000000602090	0x00007ffff7dd1b78
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000060	0x0000000000000030 #malloc(0x20)
0x602070:	0x6363636363636363	0x0000000000000000
0x602080:	0x0000000000000000	0x0000000000000000
0x602090:	0x0000000000000000	0x0000000000000031 #free(0x20）-unsortedbin
0x6020a0:	0x00007ffff7dd1b78	0x0000000000602000
0x6020b0:	0x0000000000000000	0x0000000000000000
0x6020c0:	0x0000000000000030	0x0000000000000030 #malloc(0x20)
0x6020d0:	0x6565656565656565	0x0000000000000000
0x6020e0:	0x0000000000000000	0x0000000000000000
0x6020f0:	0x0000000000000000	0x0000000000020f11 #top_chunk
0x602100:	0x6666666666666666	0x0000000000000000
......
0x602200:	0x0000000000000000	0x0000000000020e01 #old_top_chunk
......
0x602310:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

由于malloc(0x100)与top_chunk相邻，因此在free之后top_chunk会向前合并。

可以发现相邻的fastbin已经进行了合并并放入到unsortbin中，单独的fastbin也放入到了unsortbin中。

**<font style="color:#F5222D;">fastbin只能和fastbin进行合并吗？显然是否定的，只要相邻的chunk是空闲的，我们就可以将其合并。</font>**

```c
#include<string.h>
#include<stdio.h>
#include<stdlib.h>
int main(){
    void *ptr1,*ptr2,*ptr3,*ptr4;
    ptr1 = malloc(0x100);
    ptr2 = malloc(0x20);
    ptr3 = malloc(0x20);
    ptr4 = malloc(0x100);
    strcpy(ptr1,"aaaaaaaa");
    strcpy(ptr2,"bbbbbbbb");
    strcpy(ptr3,"cccccccc");
    free(ptr1);
    free(ptr2);
    free(ptr4);
}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611566425142-21120fd8-7c9f-4095-a391-6b20e9d62edf.png)

合并后的堆：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611566474211-f9e6d8c3-ec6d-4217-bb6b-d632bf9294b9.png)我们可以看到fastbin已经被合并进了相邻的unsortedbin中。

