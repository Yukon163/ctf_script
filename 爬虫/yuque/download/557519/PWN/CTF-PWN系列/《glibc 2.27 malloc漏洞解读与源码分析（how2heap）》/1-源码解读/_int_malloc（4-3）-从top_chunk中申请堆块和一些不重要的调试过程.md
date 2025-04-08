# malloc(0x90)
接上一小节，第一个malloc终于调试完毕，该说的东西也很仔细的说过了。现在我们来看一下bin的情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616632809322-1b608e4d-b4af-4e9c-af04-1f3751827aac.png)

现在我们还没有看过free的代码，因此我们直接单步步过free，来看一下结果：

```c
pwndbg> bins
tcachebins
empty
fastbins
......empty
unsortedbin
all: 0x555555756bf0 —▸ 0x5555557562f0 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555756bf0
smallbins
empty
largebins
0x500: 0x5555557566b0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555756000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x555555756250
Size: 0xa1

Free chunk (unsortedbin) | PREV_INUSE
Addr: 0x5555557562f0
Size: 0x391
fd: 0x7ffff7dcdca0
bk: 0x555555756bf0

Allocated chunk
Addr: 0x555555756680
Size: 0x30

Free chunk (largebins) | PREV_INUSE
Addr: 0x5555557566b0
Size: 0x511
fd: 0x7ffff7dce0d0
bk: 0x7ffff7dce0d0
fd_nextsize: 0x5555557566b0
bk_nextsize: 0x5555557566b0

Allocated chunk
Addr: 0x555555756bc0
Size: 0x30
										//在释放前：
Free chunk (unsortedbin) | PREV_INUSE   //Allocated chunk | PREV_INUSE
Addr: 0x555555756bf0 					//Addr: 0x555555756bf0
Size: 0x511								//Size: 0x511
fd: 0x5555557562f0						//
bk: 0x7ffff7dcdca0						//

Allocated chunk
Addr: 0x555555757100
Size: 0x30

Top chunk | PREV_INUSE
Addr: 0x555555757130
Size: 0x1fed1

pwndbg> 
```

接下来我们开始调试void *p5 = malloc(0x90)，再完整的过一遍流程但会省略一些不太重要的步骤。由于此时的tcachebin中为空，因此不会使用tcache chunk；在_int_malloc函数中将输入的bytes进行对齐：

```c
  checked_request2size (bytes, nb); //bytes==0x90；nb==0xa0
```

然后判断是否在fastbin和smallbin的范围内：

```c
  if ((unsigned long) (nb) <= (unsigned long) (get_max_fast ()))
    { //no
      ......
    }
  if (in_smallbin_range (nb))
    { //yes
       ......
    }
```

在smallbin的范围内，进入if语句：

```c
  /*
     If a small request, check regular bin.  Since these "smallbins"
	......
   */

  if (in_smallbin_range (nb))
    {
	  idx = smallbin_index (nb);  //获取idx
      bin = bin_at (av, idx);	  //获取main_arena指针

      if ((victim = last (bin)) != bin)//判断smallbin中是否有free chunk
        {//很显然smallbin中没有free chunk，因此不会进入此if语句
          ......
        }
    }

  /*
     If this is a large request, consolidate fastbins before continuing.
	  ......
   */

  else //现在程序会执行else
    {
      idx = largebin_index (nb);  //idx==10
      if (atomic_load_relaxed (&av->have_fastchunks))  //av->have_fastchunks==0,现在fastbin所拥有的所有链表都为空
        malloc_consolidate (av);
    }
```

else语句执行完毕后，开始执行宏定义代码：

```c
#if USE_TCACHE
  INTERNAL_SIZE_T tcache_nb = 0;
  size_t tc_idx = csize2tidx (nb);  //获取tcache chunk index
  if (tcache && tc_idx < mp_.tcache_bins)  //判断是否在tcache的范围内
    tcache_nb = nb;  	 //tcache_nb==nb==0xa0
  int return_cached = 0; //return_cached用来判断在遍历unsortedbin之后是否有大小适配的unsorted free chunk进入了tcache 

  tcache_unsorted_count = 0;//表示已经将原来的unsorted free chunk移到tcache的个数
#endif
```

经过一系列的赋值之后，进入while大循环：

```c
此时的bins：
unsortedbin
all: 0x555555756bf0 —▸ 0x5555557562f0 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555756bf0
smallbins
empty
largebins
0x500: 0x5555557566b0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
----------------------------------------------------------------------------------------------------
	for (;; )  //无条件进入
    {
      int iters = 0;  //表示while循环的次数
      while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av))  //获取unsortedbin是否有free chunk
        {	//victim==(mchunkptr) 0x5555557562f0
          bck = victim->bk; //获取victim的bk指针：bck==（mchunkptr) 0x555555756bf0
			//victim：倒数第二个进入unsortedbin的chunk；bck：最后进入unsortedbin的chunk
            //bck在这里会指向最后一个chunk，但也有可能指向main_arena
          if (__builtin_expect (chunksize_nomask (victim) <= 2 * SIZE_SZ, 0) //victim不能小于等于2 * SIZE_SZ
              || __builtin_expect (chunksize_nomask (victim)  //victim不能超过现在堆区的大小
				   > av->system_mem, 0))
            malloc_printerr ("malloc(): memory corruption"); //两者其一就会触发异常
          size = chunksize (victim);  //获取victim size:0x390

          /*
             If a small request, try to use last remainder if it is the
             only chunk in unsorted bin.  This helps promote locality for
             runs of consecutive small requests. This is the only
             exception to best-fit, and applies only when there is
             no exact fit for a small chunk.
           */

          if (in_smallbin_range (nb) &&       //判断要申请的chunk是否在smallbin的范围内(True)
              bck == unsorted_chunks (av) &&  //判断unsortedbin中是否只有一个unsortedbin free chunk（False）
              victim == av->last_remainder && //盘点victim是否是last_remainder(True)
              //此时的last_remainder==0x5555557562f0
              (unsigned long) (size) > (unsigned long) (nb + MINSIZE)) //判断victim size是否大小nb+MINSIZE
            {
				......(不会进入此if语句)
            }

          /* remove from unsorted list */
          unsorted_chunks (av)->bk = bck; //将victim从unsortedbin中移除
          bck->fd = unsorted_chunks (av);
---------------------------------------------------------------------------------
unsortedbin
all: 0x555555756bf0 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555756bf0
---------------------------------------------------------------------------------
          /* Take now instead of binning if exact fit */

          if (size == nb) //判断victim的大小是否恰好是nb
            {
              ......(进不去的，别想了)
            }

          /* place chunk in bin */

          if (in_smallbin_range (size))  //判断victim size是否在smallbin的范围内
            { //进入
              victim_index = smallbin_index (size); //获取victim在smallbin的victim_index==57
              bck = bin_at (av, victim_index);      //获取victim在main_arena中对应的指针，为下一步链入到smallbin中作准备
              fwd = bck->fd;                        //bck==fwd==(mchunkptr) 0x7ffff7dce020 <main_arena+992>
            }
          else
            {
              ......
            }

          mark_bin (av, victim_index); //设置对应的binmap，
----------------------------------------------------------------------------------------------
pwndbg> p av->binmap
$125 = {0, 33554432, 17, 0}
pwndbg> x/2t 0x7ffff7dce4a0
0x7ffff7dce4a0 <main_arena+2144>:00000000000000000000000000000000 （对应的bit位已设置）	
0x7ffff7dce4a0 <main_arena+2148>:00000010000000000000000000000000
0x7ffff7dce4a0 <main_arena+2152>:00000000000000000000000000010001 
0x7ffff7dce4a0 <main_arena+2156>:00000000000000000000000000000000
pwndbg> //二进制10000000000000000000000000==十进制33554432	
----------------------------------------------------------------------------------------------
          victim->bk = bck; //将chunk链入到smallbin中
          victim->fd = fwd;
          fwd->bk = victim;
          bck->fd = victim;
----------------------------------------------------------------------------------------------
unsortedbin
all: 0x555555756bf0 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555756bf0
smallbins
0x390: 0x5555557562f0 —▸ 0x7ffff7dce020 (main_arena+992) ◂— 0x5555557562f0  //victim已经链入到smallbin
largebins
0x500: 0x5555557566b0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
pwndbg> x/140gx 0x5555557562f0
0x5555557562f0:	0x0000000000000000	0x0000000000000391 //victim
0x555555756300:	0x00007ffff7dce020	0x00007ffff7dce020
0x555555756310:	0x0000000000000000	0x0000000000000000
......（数据为NULL）
0x555555756680:	0x0000000000000390	0x0000000000000030
0x555555756690:	0x0000000000000000	0x0000000000000000
0x5555557566a0:	0x0000000000000000	0x0000000000000000
0x5555557566b0:	0x0000000000000000	0x0000000000000511
0x5555557566c0:	0x00007ffff7dce0d0	0x00007ffff7dce0d0
0x5555557566d0:	0x00005555557566b0	0x00005555557566b0
......（数据为NULL）
0x555555756740:	0x0000000000000000	0x0000000000000000
pwndbg> x/6gx 0x7ffff7dce020
0x7ffff7dce020 <main_arena+992>:	0x00007ffff7dce010	0x00007ffff7dce010
0x7ffff7dce030 <main_arena+1008>:	0x00005555557562f0	0x00005555557562f0
0x7ffff7dce040 <main_arena+1024>:	0x00007ffff7dce030	0x00007ffff7dce030
pwndbg> 
----------------------------------------------------------------------------------------------
#if USE_TCACHE
      /* If we've processed as many chunks as we're allowed while
	 filling the cache, return one of the cached ones.  */   //之前的文章中说过，这里偷个懒
      ++tcache_unsorted_count;
      if (return_cached
	  && mp_.tcache_unsorted_limit > 0  //mp_.tcache_unsorted_limit一般为0，不会进入if
	  && tcache_unsorted_count > mp_.tcache_unsorted_limit)
	{
	  return tcache_get (tc_idx);
	}
#endif

#define MAX_ITERS       10000
          if (++iters >= MAX_ITERS)  //继续循环
            break;
        }
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616663503302-8b140ea5-9ca0-4f1e-9874-dda3ff99928f.png)

现在的对象victim变为0x555555756bf0，接下来会重复之前的步骤，将unsortedbin的free chunk移入到对应大小的bin中；结果就是victim被链入到largebin中；但是其中有一部分源码之前并未牵扯到，我们在这里说一下：

```c
          /* place chunk in bin */

          if (in_smallbin_range (size)) //判断是否在smallbin范围内；size==0x510==1296
            {
				......
            }
          else
            {  //在largebin范围内
              victim_index = largebin_index (size);  //获取largebin index：victim_index==68
              bck = bin_at (av, victim_index);       // bck==(mchunkptr) 0x7ffff7dce0d0 <main_arena+1168>
              fwd = bck->fd;                         //fwd==(struct malloc_chunk *) 0x5555557566b0
---------------------------------------------------------------------------------------------
pwndbg> x/6gx 0x7ffff7dce0d0
0x7ffff7dce0d0 <main_arena+1168>:	0x00007ffff7dce0c0	0x00007ffff7dce0c0
0x7ffff7dce0e0 <main_arena+1184>:	0x00005555557566b0	0x00005555557566b0
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
pwndbg> 
---------------------------------------------------------------------------------------------

              /* maintain large bins in sorted order */       //以下代码之前的文章并未涉及到
              if (fwd != bck) //判断victim在largebin中的链表是否为空  
                {   
                  ...... //从上一张图看到肯定不为空，进入此if语句
                }
              else
                victim->fd_nextsize = victim->bk_nextsize = victim;
            	}
```

首先来看if语句中的第一段代码

```c
              if (fwd != bck) //判断victim在largebin中的链表是否为空  
                {   //进入此if语句
                  /* Or with inuse bit to speed comparisons */  
                  //加速比较，应该不仅仅有这个考虑，因为链表里的chunk都会设置PREV_INUSE
                  size |= PREV_INUSE; //现在size==1297==0x511
                  /* if smaller than smallest, bypass loop below */
                  assert (chunk_main_arena (bck->bk)); 
```

这些代码中最重要的是这句话：

```c
                  assert (chunk_main_arena (bck->bk)); 
```

chunk_main_arena的宏定义如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616666298729-7ea8f34e-a221-4b05-be90-1d2d2de170c0.png)

注释中标注的很清楚，检查某一个chunk是否由main_arena进行分配，如果(((p)->mchunk_size & NON_MAIN_ARENA) == <font style="color:#6897bb;">0</font>)不成立（当chunk不由main_arena进行分配返回为0）时，则会触发断言<font style="color:#333333;">然后通过调用abort终止程序运行。现在fwd和bck情况如下：</font>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616666386912-3fca9b91-15b0-4fb3-8524-78d1cc082068.png)

<font style="color:#333333;">if(0==0)结果为True，不会触发断言，又是一个if：</font>

```c
                  if ((unsigned long) (size) 
		      < (unsigned long) chunksize_nomask (bck->bk)) //chunksize_nomask计算包括三个标志位（A、M、P）的大小
                    {
						......
                    }
                  else
                    {
						......
                    }
```

victim size==0x511，chunksize_nomask (bck->bk)结果为0x511

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616666958200-c97953e8-8b60-43e8-9bfb-885331e8b2cc.png)

```c
                  if ((unsigned long) (size)  //bck->bk总是存储着相应largebin链表中最小的chunk。
		      < (unsigned long) chunksize_nomask (bck->bk))  //这里判断要插入chunk的大小和largebin中最小的进行比较，因为largebin中的chunk总是由大到小排列的
                      //我们会对放入largebin的free chunk（现指victim）找到合适的位置进行插入
                    {
                      fwd = bck;
                      bck = bck->bk;

                      victim->fd_nextsize = fwd->fd;
                      victim->bk_nextsize = fwd->fd->bk_nextsize;
                      fwd->fd->bk_nextsize = victim->bk_nextsize->fd_nextsize = victim;
                    }
                  else  //进入else
                    { //victim size==0x511，chunksize_nomask (bck->bk)==0x511
                      assert (chunk_main_arena (fwd)); //fwd是largebin中第一个free chunk，判断fwd是否由main_arena分配，fwd== (mchunkptr) 0x5555557566b0
------------------------------------------------------------------------------------------------------------------------------
smallbins
0x390: 0x5555557562f0 —▸ 0x7ffff7dce020 (main_arena+992) ◂— 0x5555557562f0
largebins
0x500: 0x5555557566b0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
------------------------------------------------------------------------------------------------------------------------------
						......
                    }
```

我们来看最后一段代码：

```c
                      while ((unsigned long) size < chunksize_nomask (fwd))  //size==0x511,chunksize_nomask (fwd)==0x511
                        {   //这里相当于遍历找到一个合适的插入位置，从链表的头部开始进行遍历
                          fwd = fwd->fd_nextsize;
			  assert (chunk_main_arena (fwd));
                        }

                      if ((unsigned long) size   //假如说要插入的victim与fwd大小相等
			  == (unsigned long) chunksize_nomask (fwd))
                        /* Always insert in the second position.  */
                        fwd = fwd->fd; //直接将victim chunk 插入到该chunk的后面，并不修改nextsize指针
                      else
                        {
                          victim->fd_nextsize = fwd;
                          victim->bk_nextsize = fwd->bk_nextsize;
                          fwd->bk_nextsize = victim;
                          victim->bk_nextsize->fd_nextsize = victim;
                        }
                      bck = fwd->bk;
```

```c
unsortedbin
all: 0x0
smallbins
0x390: 0x5555557562f0 —▸ 0x7ffff7dce020 (main_arena+992) ◂— 0x5555557562f0
largebins
0x500: 0x5555557566b0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
pwndbg> x/6gx 0x7ffff7dce0d0
0x7ffff7dce0d0 <main_arena+1168>:	0x00007ffff7dce0c0	0x00007ffff7dce0c0
0x7ffff7dce0e0 <main_arena+1184>:	0x00005555557566b0	0x00005555557566b0
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
pwndbg> x/8gx 0x5555557566b0
0x5555557566b0:	0x0000000000000000	0x0000000000000511
0x5555557566c0:	0x00007ffff7dce0d0	0x00007ffff7dce0d0
0x5555557566d0:	0x00005555557566b0	0x00005555557566b0
0x5555557566e0:	0x0000000000000000	0x0000000000000000
pwndbg> p bck
$151 = (mchunkptr) 0x5555557566b0
pwndbg> p fwd
$152 = (mchunkptr) 0x7ffff7dce0d0 <main_arena+1168>
pwndbg>
```

最终链入到largebin：

```c
          mark_bin (av, victim_index); //标记bit
          victim->bk = bck; //开始链入到largebin中
          victim->fd = fwd;
          fwd->bk = victim;
          bck->fd = victim;
```

```c
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
0x390: 0x5555557562f0 —▸ 0x7ffff7dce020 (main_arena+992) ◂— 0x5555557562f0
largebins
0x500: 0x5555557566b0 —▸ 0x555555756bf0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
pwndbg> x/6gx 0x7ffff7dce0d0
0x7ffff7dce0d0 <main_arena+1168>:	0x00007ffff7dce0c0	0x00007ffff7dce0c0
0x7ffff7dce0e0 <main_arena+1184>:	0x00005555557566b0	0x0000555555756bf0
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
pwndbg> x/8gx 0x5555557566b0
0x5555557566b0:	0x0000000000000000	0x0000000000000511
0x5555557566c0:	0x0000555555756bf0	0x00007ffff7dce0d0
0x5555557566d0:	0x00005555557566b0	0x00005555557566b0
0x5555557566e0:	0x0000000000000000	0x0000000000000000
pwndbg> x/8gx 0x555555756bf0
0x555555756bf0:	0x0000000000000000	0x0000000000000511
0x555555756c00:	0x00007ffff7dce0d0	0x00005555557566b0
0x555555756c10:	0x0000000000000000	0x0000000000000000
0x555555756c20:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

继续执行：

```c
#if USE_TCACHE
      /* If we've processed as many chunks as we're allowed while
	 filling the cache, return one of the cached ones.  */
      ++tcache_unsorted_count;
      if (return_cached  
	  && mp_.tcache_unsorted_limit > 0  //不会进入if
	  && tcache_unsorted_count > mp_.tcache_unsorted_limit)
	{
	  return tcache_get (tc_idx);
	}
#endif

#define MAX_ITERS       10000
          if (++iters >= MAX_ITERS) //不满足条件，继续while循环
            break;
        }
```

```c
 while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av)) //此时unsortedbin已为空，终止while循环
```

在跳出循环之后，继续向下调试：

```c
#if USE_TCACHE
      /* If all the small chunks we found ended up cached, return one now.  */
      if (return_cached)   //不会进入
	{
	  return tcache_get (tc_idx); //从tcachebin中取出chunk并且返回
	}
#endif

      /*
         If a large request, scan through the chunks of current bin in
         sorted order to find smallest that fits.  Use the skip list for this.
       */

      if (!in_smallbin_range (nb)) //判断是否在largebin中：nb==160==0xa0
        {
 			.......(不会进入此if)
        }
      /*
         Search for a chunk by scanning bins, starting with next largest
		......
       */

      ++idx; //idx是nb在largebin的index（执行前idx==10）：目的是为了移动到下一条更大的largebin链
      bin = bin_at (av, idx);  //idx==11，获取main_arena指针
      block = idx2block (idx);  
      map = av->binmap[block];
      bit = idx2bit (idx); //设置bit
```

备份一下现在的情况，方便之后的对比。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616725675115-015b98cb-86b9-487c-a471-2d891fded58b.png)

```c
pwndbg> p av->binmap
$125 = {0, 33554432, 17, 0}
pwndbg> x/2t 0x7ffff7dce4a0  #binmap
							   //00000000000000000000100000000000（bit）
0x7ffff7dce4a0 <main_arena+2144>:00000000000000000000000000000000
0x7ffff7dce4a4 <main_arena+2148>:00000010000000000000000000000000 //33554432 
0x7ffff7dce4b0 <main_arena+2152>:00000000000000000000000000010001 
0x7ffff7dce4a0 <main_arena+2156>:00000000000000000000000000000000
pwndbg>
```

由于在当前的block中没有free chunk，在下面的遍历中我们会寻找其他可用的block，超大循环：

```c
      for (;; )
        {
          /* Skip rest of block if there are no more set bits in this block.  */
          if (bit > map || bit == 0)  //bit=2048;map==0
            { // 如果bit>map，则表示该map中没有比当前所需要chunk大的空闲块
              // 如果bit为0，那么说明，上面idx2bit带入的参数为0。
              do
                {
                  if (++block >= BINMAPSIZE) /* out of bins */  //block++之后判断，遍历largebin链上的chunk
                    goto use_top;  //如果大小都不满足，则对top_chunk进行分割
                }
              while ((map = av->binmap[block]) == 0); //赋值后map==av->binmap[block(block==0)]==33554432

              bin = bin_at (av, (block << BINMAPSHIFT)); //此时bin== (mbinptr) 0x7ffff7dcde90 <main_arena+592>
              bit = 1; //设置bit
            }

          /* Advance to bin with set bit. There must be one. */
          while ((bit & map) == 0)  //使用此循环找到有效的bin bit=1；map==33554432 
            { //进入此循环
              bin = next_bin (bin);   
              bit <<= 1; 			  
              assert (bit != 0);      //正常情况下bit不可能为0
            }
-----------------------------------------------------------------------------------------------------------------
//bin==(mbinptr) 0x7ffff7dcdea0 <main_arena+608> //第二次循环：bin==0x7ffff7dcdeb0 //第三次：0x7ffff7dcdec0  //0x7ffff7dcded0 //0x7ffff7dcdee0 //...
//bit=bit<<1之后bit==2  //第二次循环bit==4 //bit==8 //bit==16 //bit==32  ....
一直循环直到：
pwndbg> x/16gx bin
0x7ffff7dce020 <main_arena+992>:	0x00007ffff7dce010	0x00007ffff7dce010
0x7ffff7dce030 <main_arena+1008>:	0x00005555557562f0	0x00005555557562f0
0x7ffff7dce040 <main_arena+1024>:	0x00007ffff7dce030	0x00007ffff7dce030
0x7ffff7dce050 <main_arena+1040>:	0x00007ffff7dce040	0x00007ffff7dce040
0x7ffff7dce060 <main_arena+1056>:	0x00007ffff7dce050	0x00007ffff7dce050
0x7ffff7dce070 <main_arena+1072>:	0x00007ffff7dce060	0x00007ffff7dce060
0x7ffff7dce080 <main_arena+1088>:	0x00007ffff7dce070	0x00007ffff7dce070
0x7ffff7dce090 <main_arena+1104>:	0x00007ffff7dce080	0x00007ffff7dce080
pwndbg>
-----------------------------------------------------------------------------------------------------------------    
          /* Inspect the bin. It is likely to be non-empty */
          victim = last (bin);  //victim==0x5555557562f0  

          /*  If a false alarm (empty bin), clear the bit. */
          if (victim == bin) //检查这个bin，它有可能是空的（我们之前说过，当一个bin为空时，它对应的binmap项并不会立即被clear）
            { //如果这个bin是空的，那么将其对应的binmap项clear，然后进入下一次for循环，知道找到可用的链表
              av->binmap[block] = map &= ~bit; /* Write through */
              bin = next_bin (bin);
              bit <<= 1;
            }

          else
            {
              size = chunksize (victim);

              /*  We know the first chunk in this bin is big enough to use. */
              assert ((unsigned long) (size) >= (unsigned long) (nb));

              remainder_size = size - nb;  //remainder_size==0x2f0

              /* unlink */
              unlink (av, victim, bck, fwd); //对smallbin中的victim进行unlink

              /* Exhaust */
              if (remainder_size < MINSIZE) //如果remainder_size小于MINSIZE（最小堆块的大小）
                {  //不在对堆块victim进行
                  set_inuse_bit_at_offset (victim, size);
                  if (av != &main_arena)
		    set_non_main_arena (victim);
                }

              /* Split */
              else   //对victim进行分割，之前说过，这里就省略了
                { //分割后剩下的free chunk会扔到unsortedbin中
					......
              return p;
            }
        }
```

对victim切割之后我们会将余下的部分放入last_remainder中，最终效果如下：

```c
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
all: 0x555555756390 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555756390
smallbins
empty
largebins
0x500: 0x5555557566b0 —▸ 0x555555756bf0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
pwndbg> x/160gx 0x5555557562f0
0x5555557562f0:	0x0000000000000000	0x00000000000000a1 
0x555555756300:	0x00007ffff7dce020	0x00007ffff7dce020
......
0x555555756390:	0x0000000000000000	0x00000000000002f1 #smallbin
0x5555557563a0:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......
0x555555756680:	0x00000000000002f0	0x0000000000000030
0x555555756690:	0x0000000000000000	0x0000000000000000
0x5555557566a0:	0x0000000000000000	0x0000000000000000
0x5555557566b0:	0x0000000000000000	0x0000000000000511
0x5555557566c0:	0x0000555555756bf0	0x00007ffff7dce0d0
0x5555557566d0:	0x00005555557566b0	0x00005555557566b0
......
0x5555557567e0:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x7ffff7dcdca0
0x7ffff7dcdca0 <main_arena+96>:	0x0000555555757130	0x0000555555756390 
    												#unsortedbin（last_remainder）
0x7ffff7dcdcb0 <main_arena+112>:	0x0000555555756390	0x0000555555756390
0x7ffff7dcdcc0 <main_arena+128>:	0x00007ffff7dcdcb0	0x00007ffff7dcdcb0
0x7ffff7dcdcd0 <main_arena+144>:	0x00007ffff7dcdcc0	0x00007ffff7dcdcc0
0x7ffff7dcdce0 <main_arena+160>:	0x00007ffff7dcdcd0	0x00007ffff7dcdcd0
0x7ffff7dcdcf0 <main_arena+176>:	0x00007ffff7dcdce0	0x00007ffff7dcdce0
0x7ffff7dcdd00 <main_arena+192>:	0x00007ffff7dcdcf0	0x00007ffff7dcdcf0
0x7ffff7dcdd10 <main_arena+208>:	0x00007ffff7dcdd00	0x00007ffff7dcdd00
pwndbg> p &av->last_remainder 
$195 = (mchunkptr *) 0x7ffff7dcdca8 <main_arena+104>
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555756000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x555555756250
Size: 0xa1

Allocated chunk | PREV_INUSE
Addr: 0x5555557562f0
Size: 0xa1

Free chunk (unsortedbin) | PREV_INUSE
Addr: 0x555555756390
Size: 0x2f1
fd: 0x7ffff7dcdca0
bk: 0x7ffff7dcdca0

Allocated chunk
Addr: 0x555555756680
Size: 0x30

Free chunk (largebins) | PREV_INUSE
Addr: 0x5555557566b0
Size: 0x511
fd: 0x555555756bf0
bk: 0x7ffff7dce0d0
fd_nextsize: 0x5555557566b0
bk_nextsize: 0x5555557566b0

Allocated chunk
Addr: 0x555555756bc0
Size: 0x30

Free chunk (largebins) | PREV_INUSE
Addr: 0x555555756bf0
Size: 0x511
fd: 0x7ffff7dce0d0
bk: 0x5555557566b0
fd_nextsize: 0x00
bk_nextsize: 0x00

Allocated chunk
Addr: 0x555555757100
Size: 0x30

Top chunk | PREV_INUSE
Addr: 0x555555757130
Size: 0x1fed1

pwndbg> 
```

附：之前的解析PPT：

 

[4-2小节和4-3小节解析.pptx](https://www.yuque.com/attachments/yuque/0/2021/pptx/574026/1617868557269-6b5f634f-5877-4f7a-9477-1764493f0904.pptx)

# 
# malloc(0x1000)
## 常规流程
接下来开始分析void *p6 = malloc(0x1000);【之前提到过的代码不在仔细分析，但是我们会对齐进行注释】

```c
  for (;; ) //超级外层大循环：目的是为了重新分配smallbin chunk（因为在之前的malloc_consolidate将fastbin合并为unsortedbin）
    {    
      int iters = 0;
      while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av)) //现在对unsortedbin进行遍历
        {  
          bck = victim->bk;  
          if (__builtin_expect (chunksize_nomask (victim) <= 2 * SIZE_SZ, 0) 
              || __builtin_expect (chunksize_nomask (victim)  
				   > av->system_mem, 0))
            malloc_printerr ("malloc(): memory corruption");
          size = chunksize (victim);   //victim size对齐:size==0x23c  victim==(mchunkptr) 0x555555756390

          /*
             If a small request, try to use last remainder if it is the
             only chunk in unsorted bin.  This helps promote locality for
             runs of consecutive small requests. This is the only
             exception to best-fit, and applies only when there is
             no exact fit for a small chunk.
           */

          if (in_smallbin_range (nb) &&   //判断要申请的chunk大小是否在smallbin的范围内（false）
              bck == unsorted_chunks (av) &&  
              victim == av->last_remainder &&   
              (unsigned long) (size) > (unsigned long) (nb + MINSIZE))  
            {  
				......
            }

          /* remove from unsorted list */   //无法进入if说明last remainder不存在或者不满足要求或者申请的大小为large chunk
          unsorted_chunks (av)->bk = bck;   //将victim从unsortedbin移除
          bck->fd = unsorted_chunks (av);

          /* Take now instead of binning if exact fit */

          if (size == nb)  //（false）
            {
				......
            }

          /* place chunk in bin */
                        				  //如果要申请的大小和unsortedbin中的victim大小不相同
          if (in_smallbin_range (size))   //判断victim（在unsortedbin中）大小是否在smallbin范围中
            {  //av->binmap=={0, 33554432, 17, 0}
              victim_index = smallbin_index (size);  //准备将其放入双向链表smallbin中
              bck = bin_at (av, victim_index);
              fwd = bck->fd;
            }
          else
            {  //不在smallbin范围内，准备放入largebin中
				......
            }

          mark_bin (av, victim_index); //执行后：av->binmap== {0, 33587200, 17, 0}
          victim->bk = bck; //将其链入smallbin中
          victim->fd = fwd;
          fwd->bk = victim;
          bck->fd = victim;
-----------------------------------------------------------------------------------------------------------------
smallbins
0x2f0: 0x555555756390 —▸ 0x7ffff7dcdf80 (main_arena+832) ◂— 0x555555756390
largebins
0x500: 0x5555557566b0 —▸ 0x555555756bf0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
pwndbg> 
-----------------------------------------------------------------------------------------------------------------
#if USE_TCACHE
      /* If we've processed as many chunks as we're allowed while
	 filling the cache, return one of the cached ones.  */
      ++tcache_unsorted_count;
      if (return_cached
	  && mp_.tcache_unsorted_limit > 0   //不可能进入
	  && tcache_unsorted_count > mp_.tcache_unsorted_limit)
	{
	  return tcache_get (tc_idx);
	}
#endif

#define MAX_ITERS       10000
          if (++iters >= MAX_ITERS)
            break;
        }

#if USE_TCACHE
      /* If all the small chunks we found ended up cached, return one now.  */
      if (return_cached)  //现在没有从unsortedbin放入tcachebin的free chunk
	{ //不会进入
	  return tcache_get (tc_idx);
	}
#endif

      /*
         If a large request, scan through the chunks of current bin in
         sorted order to find smallest that fits.  Use the skip list for this.
       */

      if (!in_smallbin_range (nb))  //在largebin范围内
        { //申请堆块的大小nb==0x1010
          bin = bin_at (av, idx);

          /* skip scan if empty or largest chunk is too small */
          if ((victim = first (bin)) != bin  //判断链表是否为空（为空）
	      && (unsigned long) chunksize_nomask (victim)  
	        >= (unsigned long) (nb)) //判断大小是否满足
            {
    			......
            }
        }

      /*
         Search for a chunk by scanning bins, starting with next largest
         bin. This search is strictly by best-fit; i.e., the smallest
         (with ties going to approximately the least recently used) chunk
         that fits is selected.

         The bitmap avoids needing to check that most blocks are nonempty.
         The particular case of skipping all bins during warm-up phases
         when no chunks have been returned yet is faster than it might look.
       */

      ++idx;  //idx++，准备遍历下一条largebin链表
      bin = bin_at (av, idx);
      block = idx2block (idx);
      map = av->binmap[block];
      bit = idx2bit (idx);

      for (;; )
        {
          /* Skip rest of block if there are no more set bits in this block.  */
          if (bit > map || bit == 0)
            {
              do
                {
                  if (++block >= BINMAPSIZE) /* out of bins */
                    goto use_top;   //进入use_top，对top_chunk进行切割分配内存
                }		//下面的代码不再重要，因为在use_top中会直接返回
              while ((map = av->binmap[block]) == 0);

              bin = bin_at (av, (block << BINMAPSHIFT));
              bit = 1;
            }

			......
        }
```

## 向top_chunk申请内存
这个use_top的代码之前没有说过，当然，现在你肯定可以看得懂大部分源码了：

```c
    use_top:
      /*
         If large enough, split off the chunk bordering the end of memory
         (held in av->top). Note that this is in accord with the best-fit
         search rule.  In effect, av->top is treated as larger (and thus
         less well fitting) than any other available chunk since it can
         be extended to be as large as necessary (up to system
         limitations).

         We require that av->top always exists (i.e., has size >=
         MINSIZE) after initialization, so if it would otherwise be
         exhausted by current request, it is replenished. (The main
         reason for ensuring it exists is that we may need MINSIZE space
         to put in fenceposts in sysmalloc.)
       */

      victim = av->top; //获取top_chunk的地址：victim==(mchunkptr) 0x555555757130
      size = chunksize (victim); //size==0x1fed0（chunksize()不包括三个标志位）

      if ((unsigned long) (size) >= (unsigned long) (nb + MINSIZE)) //判断top_chunk的大小是否可以满足要申请的chunk，nb + MINSIZE==0x1030
        {	//开始对top_chunk进行分割
          remainder_size = size - nb; //获取切割后余下的top_chunk大小  remainder_size==0x1eec0
          remainder = chunk_at_offset (victim, nb); //获取切割后的地址：remainder==(mchunkptr) 0x555555757130
          av->top = remainder; //设置av中的top_chunk
          set_head (victim, nb | PREV_INUSE |
                    (av != &main_arena ? NON_MAIN_ARENA : 0)); //设置切割后victim的head
          set_head (remainder, remainder_size | PREV_INUSE); //设置top_chunk的size域；remainder(top_chunk)==0x555555758140
          
          check_malloced_chunk (av, victim, nb);
          void *p = chunk2mem (victim);
          alloc_perturb (p, bytes);
          return p;
        }

      /* When we are using atomic ops to free fast chunks we can get
         here for all block sizes.  */
      else if (atomic_load_relaxed (&av->have_fastchunks))  //av->have_fastchunks表示现在的fastbin中是否有fastbin free chunk
        { //若fastbin中有free chunk
          malloc_consolidate (av); //将fastbin中的free chunk整理放入unsortedbin中
          /* restore original bin index */
          if (in_smallbin_range (nb))
            idx = smallbin_index (nb);
          else
            idx = largebin_index (nb);
        }

      /*
         Otherwise, relay to handle system-dependent cases
       */
      else //若上述if条件都不满足，向系统申请内存
        {
          void *p = sysmalloc (nb, av);
          if (p != NULL)
            alloc_perturb (p, bytes);
          return p;
        }
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616824734346-863e11dd-c3c0-4a67-bc47-7c0e94f9647e.png)

# 其他的一些调试
现在开始调试void *p7 = malloc(0x30);根据之前的调试经验来看，在向内存申请堆块时，首先将smallbin中的free chunk进行解链并链入到unsortedbin中，然后对这个free chunk进行解链切块，结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616825008190-cd886316-802e-49d9-80dd-77672cf848a6.png)

继续调试这个：void *p8 = malloc(0x40);，在进入到第一个超大for循环后有一段之前没有调试过的代码：

```c
  /*
     Process recently freed or remaindered chunks, taking one only if
     it is exact fit, or, if this a small request, the chunk is remainder from
     the most recent non-exact fit.  Place other traversed chunks in
     bins.  Note that this step is the only place in any routine where
     chunks are placed in bins.

     The outer loop here is needed because we might not realize until
     near the end of malloc that we should have consolidated, so must
     do so and retry. This happens at most once, and only when we would
     otherwise need to expand memory to service a "small" request.
   */

	......

  for (;; )
    {
      int iters = 0;
      while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av))
        {
          bck = victim->bk;
          if (__builtin_expect (chunksize_nomask (victim) <= 2 * SIZE_SZ, 0)
              || __builtin_expect (chunksize_nomask (victim)
				   > av->system_mem, 0))
            malloc_printerr ("malloc(): memory corruption");
          size = chunksize (victim);

          /*
             If a small request, try to use last remainder if it is the
             only chunk in unsorted bin.  This helps promote locality for
             runs of consecutive small requests. This is the only
             exception to best-fit, and applies only when there is
             no exact fit for a small chunk.
           */

          if (in_smallbin_range (nb) && //nb==80==0x50
              bck == unsorted_chunks (av) && //bck==(mchunkptr) 0x7ffff7dcdca0 <main_arena+96>
              victim == av->last_remainder && //victim==(mchunkptr) 0x5555557563d0
              (unsigned long) (size) > (unsigned long) (nb + MINSIZE)) //size==0x2b0
            {  //进入此if语句  现在的remainder:av->lastremainder== (mchunkptr) 0x5555557563d0
              /* split and reattach remainder */  //准备切割last_remainder
              remainder_size = size - nb;   //获取切割后余下的堆块大小：remainder_size==0x260
              remainder = chunk_at_offset (victim, nb);  //获取切割后余下堆块的起始地址
#unsortedbin
#all: 0x5555557563d0 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x5555557563d0
#smallbins
#empty
#largebins
#0x500: 0x5555557566b0 —▸ 0x555555756bf0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0              
              unsorted_chunks (av)->bk = unsorted_chunks (av)->fd = remainder; //更新unsortedbin           
              av->last_remainder = remainder;  //设置新的last_remainder 现在last_remainder== (mchunkptr) 0x555555756420
              remainder->bk = remainder->fd = unsorted_chunks (av); //更新last_remainder指针
#unsortedbin
#all: 0x555555756420 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555756420 /* ' duUUU' */
#smallbins
#empty
#largebins
#0x500: 0x5555557566b0 —▸ 0x555555756bf0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
              if (!in_smallbin_range (remainder_size))  //如果last_remainder 是largebin chunk，由于不在largebin链表中，清空fd_nextsize和bk_nextsize
                {	//不会进入此if
                  remainder->fd_nextsize = NULL;
                  remainder->bk_nextsize = NULL;
                }

              set_head (victim, nb | PREV_INUSE | 	//设置victim和remainder的header，以及remainder的下一个毗邻块的prev size
                        (av != &main_arena ? NON_MAIN_ARENA : 0));
              set_head (remainder, remainder_size | PREV_INUSE);
              set_foot (remainder, remainder_size);
              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim);
              alloc_perturb (p, bytes);
              return p;  //返回申请到的victim chunk
            }
          ......
      }
```

最终结果如下：

```c
pwndbg> x/20gx 0x5555557563d0
0x5555557563d0:	0x0000000000000000	0x0000000000000051 #victim
0x5555557563e0:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
0x5555557563f0:	0x0000000000000000	0x0000000000000000
0x555555756400:	0x0000000000000000	0x0000000000000000
0x555555756410:	0x0000000000000000	0x0000000000000000
0x555555756420:	0x0000000000000000	0x0000000000000261 #last_remainder
0x555555756430:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
0x555555756440:	0x0000000000000000	0x0000000000000000
0x555555756450:	0x0000000000000000	0x0000000000000000
0x555555756460:	0x0000000000000000	0x0000000000000000
unsortedbin
all: 0x555555756420 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555756420 /* ' duUUU' */
smallbins
empty
largebins
0x500: 0x5555557566b0 —▸ 0x555555756bf0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
pwndbg> p av->last_remainder 
$218 = (mchunkptr) 0x555555756420
pwndbg> 
```

剩下的两个malloc语句就不调试了，感兴趣的话可以亲自上手。

