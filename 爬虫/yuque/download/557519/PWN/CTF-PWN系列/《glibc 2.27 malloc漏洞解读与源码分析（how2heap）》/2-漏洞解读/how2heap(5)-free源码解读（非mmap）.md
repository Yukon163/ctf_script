+ 主要针对点：单线程

# __libc_free源码
```c
void
__libc_free (void *mem) //传入要释放堆块的指针
{
  mstate ar_ptr;
  mchunkptr p;                          /* chunk corresponding to mem */

  void (*hook) (void *, const void *)  
    = atomic_forced_read (__free_hook);
  if (__builtin_expect (hook != NULL, 0))
    {
      (*hook)(mem, RETURN_ADDRESS (0));
      return;
    } //以上都是关于__free_hook的代码

  if (mem == 0)  //free(0)会直接在这里返回                 
    return;

  p = mem2chunk (mem);

  if (chunk_is_mmapped (p))                       /* release mmapped memory. */
    {
		//省略释放由mmap分配堆块的代码......
    }

  MAYBE_INIT_TCACHE (); //检查是否初始化了tcache，如果没有初始化则初始化

  ar_ptr = arena_for_chunk (p);  //获取对应的arena地址，在单线程中为main_arena
  _int_free (ar_ptr, p, 0); //调用_int_free
}
libc_hidden_def (__libc_free)
```

# _int_free源码
首先说明：

```c
pwndbg> x/16gx 0x555555756250
0x555555756250:	0x0000000000000000	0x0000000000000021 #前一个堆块：chunk    （前）
0x555555756260:	0x0000000000000000	0x0000555555756010
0x555555756270:	0x0000000000000000	0x0000000000000031 #p
0x555555756280:	0x0000000000000000	0x0000000000000000
0x555555756290:	0x0000000000000000	0x0000000000000000
0x5555557562a0:	0x0000000000000000	0x0000000000000041 #后一个堆块：nextchunk（后）
0x5555557562b0:	0x0000000000000000	0x0000000000000000
0x5555557562c0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

```c
/*
   ------------------------------ free ------------------------------
 */

static void
_int_free (mstate av, mchunkptr p, int have_lock) 
{ //此函数传入的参数分别为main_arena，待释放堆块的指针，和锁have_lock
  INTERNAL_SIZE_T size;        /* its size */
  mfastbinptr *fb;             /* associated fastbin */
  mchunkptr nextchunk;         /* next contiguous chunk */
  INTERNAL_SIZE_T nextsize;    /* its size */
  int nextinuse;               /* true if nextchunk is used */
  INTERNAL_SIZE_T prevsize;    /* size of previous contiguous chunk */
  mchunkptr bck;               /* misc temp for linking */
  mchunkptr fwd;               /* misc temp for linking */

  size = chunksize (p); //获取待释放堆块的大小

  /* Little security check which won't hurt performance: the
     allocator never wrapps around at the end of the address space.
     Therefore we can exclude some size values which might appear
     here by accident or by "design" from some intruder.  */
  if (__builtin_expect ((uintptr_t) p > (uintptr_t) -size, 0) //检查堆块指针的有效性
      || __builtin_expect (misaligned_chunk (p), 0))
    malloc_printerr ("free(): invalid pointer");
  /* We know that each chunk is at least MINSIZE bytes in size or a
     multiple of MALLOC_ALIGNMENT.  */
  if (__glibc_unlikely (size < MINSIZE || !aligned_OK (size))) //检查堆块的大小是否合法
    malloc_printerr ("free(): invalid size");

  check_inuse_chunk(av, p);

#if USE_TCACHE
 	//关于tcachebin的代码在这里省略，因为之前说过......
#endif

  /*
    If eligible, place chunk on a fastbin so it can be found
    and used quickly in malloc.
  */

  if ((unsigned long)(size) <= (unsigned long)(get_max_fast ())
    	//有关于fastbin的代码已省略，因为之前也说过......

  /*
    Consolidate other non-mmapped chunks as they arrive.
  */
  #接下来的代码才是重头戏
  else if (!chunk_is_mmapped(p)) {
	 //若待释放的chunk不由mmap进行分配
    /* If we're single-threaded, don't lock the arena.  */
    //如果此程序是单线程，不会对main_arena加锁
    if (SINGLE_THREAD_P) 
      have_lock = true; //单线程执行：have_lock=true

    if (!have_lock)
      __libc_lock_lock (av->mutex); //多线程获得锁

    nextchunk = chunk_at_offset(p, size); //获取p chunk相邻高地址的chunk地址

    /* Lightweight tests: check whether the block is already the
       top block.  */
    if (__glibc_unlikely (p == av->top))   //安全性检查：p不能为top_chunk
      malloc_printerr ("double free or corruption (top)");
    /* Or whether the next chunk is beyond the boundaries of the arena.  */
    if (__builtin_expect (contiguous (av) 
			  && (char *) nextchunk //安全性检查：当前free的chunk的相邻下一个chunk不能超过arena的边界
			  >= ((char *) av->top + chunksize(av->top)), 0))
	malloc_printerr ("double free or corruption (out)");
    /* Or whether the block is actually not marked used.  */
    if (__glibc_unlikely (!prev_inuse(nextchunk))) //获取nextchunk的PREV_INUSE标志位
        						//如果标志位为0则说明p堆块处于free状态，会触发异常
        						//或者说明我们伪造的堆块不成功（😁）
      malloc_printerr ("double free or corruption (!prev)");

    nextsize = chunksize(nextchunk); //获取nextchunk的大小（不包括三个标志位）
    if (__builtin_expect (chunksize_nomask (nextchunk) <= 2 * SIZE_SZ, 0)
	|| __builtin_expect (nextsize >= av->system_mem, 0)) //检查nextchunk的大小是否正常
      malloc_printerr ("free(): invalid next size (normal)");

    free_perturb (chunk2mem(p), size - 2 * SIZE_SZ); //默认清空堆块中user_data的内容
      //#define chunk2mem(p)   ((void*)((char*)(p) + 2*SIZE_SZ))
    /* consolidate backward */ //向后合并
    if (!prev_inuse(p)) { //获取pchunk的PREV_INUSE标志位
        //如果标志位为0则说明p之前的堆块处于free状态（tcachebin、fastbin除外）
        //我们开始对p和前一个相邻的free chunk进行合并
      prevsize = prev_size (p); //获取p堆块的mchunk_prev_size
        //如果前一个堆块处于unsortedbin、smallbin、largebin则p的mchunk_prev_size置位
        //和之前的if (!prev_inuse(p))相照应
        //这里的prevsize指的是前一个堆块的大小
      size += prevsize; //size=size+prevsize
      p = chunk_at_offset(p, -((long) prevsize));  //p现在指向前一个堆块
      unlink(av, p, bck, fwd); //对前一个堆块进行unlink
    }

    if (nextchunk != av->top) { //检查p堆块是否和top_chunk相邻
      /* get and clear inuse bit */ //如果不和top_chunk相邻
      nextinuse = inuse_bit_at_offset(nextchunk, nextsize); 
        	//获取nextchunk的下一个紧邻的堆块的PREV_INUSE标志位
        	//这个标志位代表着nextchunk的状态

      /* consolidate forward */ //向前合并
      if (!nextinuse) { //如果nextchunk处于unsortedbin、smallbin、largebin中
	unlink(av, nextchunk, bck, fwd); //对nextchunk进行unlink
	size += nextsize; //size=size+nextsize
      } else
	clear_inuse_bit_at_offset(nextchunk, 0); //将nextchunk的PREV_INUSE标志位置0

      /*
	Place the chunk in unsorted chunk list. Chunks are
	not placed into regular bins until after they have
	been given one chance to be used in malloc.
      */ //将堆块放入到unsortedbin链表中，我们会在调用malloc函数时对其中的free chunk进行整理

      bck = unsorted_chunks(av);  //bck指向unsortedbin的main_arena
        //为了形容方便，我们使用左右这个概念来区分
        //unsortedbin
        //all: 0x555555757760 —▸ 0x555555758100 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x555555757760 /* '`wuUUU' */
        //           左                  右
      fwd = bck->fd;  //fwd指向最左边的堆块 
      if (__glibc_unlikely (fwd->bk != bck)) //检查双向链表的完整性
	malloc_printerr ("free(): corrupted unsorted chunks");
      p->fd = fwd; //设置p堆块的fd
      p->bk = bck; //设置p堆块的bk
      if (!in_smallbin_range(size))
	{
	  p->fd_nextsize = NULL;
	  p->bk_nextsize = NULL;
	}
      bck->fd = p; //链入unsortedbin【1】:在最左边插入
      fwd->bk = p; //链入unsortedbin【2】

      set_head(p, size | PREV_INUSE); //设置p的size
      set_foot(p, size); //设置相邻下一个堆块的mchunk_prev_size

      check_free_chunk(av, p); 
    }

    /*
      If the chunk borders the current high end of memory,
      consolidate into top
    */

    else { //如果p堆块和top_chunk相邻
      size += nextsize; //步骤很简单，与top_chunk进行合并
      set_head(p, size | PREV_INUSE);
      av->top = p;
      check_chunk(av, p);
    }

    /*
      If freeing a large space, consolidate possibly-surrounding
      chunks. Then, if the total unused topmost memory exceeds trim
      threshold, ask malloc_trim to reduce top.

      Unless max_fast is 0, we don't know if there are fastbins
      bordering top, so we cannot tell for sure whether threshold
      has been reached unless fastbins are consolidated.  But we
      don't want to consolidate on each free.  As a compromise,
      consolidation is performed if FASTBIN_CONSOLIDATION_THRESHOLD
      is reached.
    */
    //现在p chunk已经和其他堆块合并完成
    if ((unsigned long)(size) >= FASTBIN_CONSOLIDATION_THRESHOLD) {
        //如果合并之后的堆块大小大于FASTBIN_CONSOLIDATION_THRESHOLD(65536UL)
        //一般合并到top chunk都会执行这部分代码。
      if (atomic_load_relaxed (&av->have_fastchunks)) //判断fastbin中是否有free chunk
	malloc_consolidate(av); //调用malloc_consolidate对fastbin free chunk进行合并

      if (av == &main_arena) { //在单线程中av总是指向main_arena
#ifndef MORECORE_CANNOT_TRIM
          //主分配区，如果当前top_chunk大小大于heap的收缩阈值，就会调用systrim收缩heap
	if ((unsigned long)(chunksize(av->top)) >=
	    (unsigned long)(mp_.trim_threshold))
	  systrim(mp_.top_pad, av);
#endif
      } else { //非主分配区，收缩调用heap_trim收缩heap段
	/* Always try heap_trim(), even if the top chunk is not
	   large, because the corresponding heap might go away.  */
	heap_info *heap = heap_for_ptr(top(av));

	assert(heap->ar_ptr == av);
	heap_trim(heap, mp_.top_pad);
      }
    }

    if (!have_lock)
      __libc_lock_unlock (av->mutex);
  }
  /*
    If the chunk was allocated via mmap, release via munmap().
  */

  else { //如果free chunk由mmap进行分配
    munmap_chunk (p);//调用munmap_chunk用来回收mmap分配的空间（堆块）。
  }
}
```

