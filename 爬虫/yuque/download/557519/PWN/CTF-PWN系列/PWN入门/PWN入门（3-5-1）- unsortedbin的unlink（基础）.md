> 参考资料：[https://blog.csdn.net/qq_41202237/article/details/108481889](https://blog.csdn.net/qq_41202237/article/details/108481889)
>

# 前言
在做pwn题的时候，你一定听说过unlink的鼎鼎大名，那么unlink是什么？它对我们getshell能提供什么帮助？这一小节我们介绍unlink。

首先我们要知道link的意思，翻译过来就是

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600734739016-f6fa639c-4d8e-44f7-a2ab-c8ecbe3ec1f4.png)

那么，unlink就是link的反义词--断开。“断开”什么呢？先留个悬念，我们之后再说。

# unlink的介绍
如果你要学习pwn，那么一定离不了libc源码，看一下源码中的unlink的描述：

> 实验环境：Ubuntu 16.04.6，libc-2.23.so（堆的实际环境与讲解可能有差异，以你自己的环境为准）
>
> 源码下载地址：[http://ftp.gnu.org/gnu/glibc/](http://ftp.gnu.org/gnu/glibc/)，下载的目标文件为 glibc-2.23.tar.xz
>

文件下载完成之后，进行解压，来到malloc文件夹中的malloc.h

可以发现，unlink其实是malloc中的宏定义：（可以使用代码编辑器的搜索快速找到）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600735893904-776c2015-bcdd-4a42-8cd0-f1a51baac6b1.png)

看到上面的注释了吗？Take a chunk off a bin list：从bin中删除一个chunk，进一步说就是chunk空间的再利用，这就是上面问题的答案。

那么什么时候程序会执行unlink？向下搜索“_int_free”关键字，可以得到：

```c
/*
   ------------------------------ free ------------------------------
 */

static void
_int_free (mstate av, mchunkptr p, int have_lock)
{
  INTERNAL_SIZE_T size;        /* its size */
  mfastbinptr *fb;             /* associated fastbin */
  mchunkptr nextchunk;         /* next contiguous chunk */
  INTERNAL_SIZE_T nextsize;    /* its size */
  int nextinuse;               /* true if nextchunk is used */
  INTERNAL_SIZE_T prevsize;    /* size of previous contiguous chunk */
  mchunkptr bck;               /* misc temp for linking */
  mchunkptr fwd;               /* misc temp for linking */

  const char *errstr = NULL;
  int locked = 0;

  size = chunksize (p);

  /* Little security check which won't hurt performance: the
     allocator never wrapps around at the end of the address space.
     Therefore we can exclude some size values which might appear
     here by accident or by "design" from some intruder.  */
  if (__builtin_expect ((uintptr_t) p > (uintptr_t) -size, 0)
      || __builtin_expect (misaligned_chunk (p), 0))
    {
      errstr = "free(): invalid pointer";
    errout:
      if (!have_lock && locked)
        (void) mutex_unlock (&av->mutex);
      malloc_printerr (check_action, errstr, chunk2mem (p), av);
      return;
    }
  /* We know that each chunk is at least MINSIZE bytes in size or a
     multiple of MALLOC_ALIGNMENT.  */
  if (__glibc_unlikely (size < MINSIZE || !aligned_OK (size)))
    {
      errstr = "free(): invalid size";
      goto errout;
    }

  check_inuse_chunk(av, p);

  /*
    If eligible, place chunk on a fastbin so it can be found
    and used quickly in malloc.
  */

  if ((unsigned long)(size) <= (unsigned long)(get_max_fast ())

#if TRIM_FASTBINS
      /*
	If TRIM_FASTBINS set, don't place chunks
	bordering top into fastbins
      */
      && (chunk_at_offset(p, size) != av->top)
#endif
      ) {

    if (__builtin_expect (chunk_at_offset (p, size)->size <= 2 * SIZE_SZ, 0)
	|| __builtin_expect (chunksize (chunk_at_offset (p, size))
			     >= av->system_mem, 0))
      {
	/* We might not have a lock at this point and concurrent modifications
	   of system_mem might have let to a false positive.  Redo the test
	   after getting the lock.  */
	if (have_lock
	    || ({ assert (locked == 0);
		  mutex_lock(&av->mutex);
		  locked = 1;
		  chunk_at_offset (p, size)->size <= 2 * SIZE_SZ
		    || chunksize (chunk_at_offset (p, size)) >= av->system_mem;
	      }))
	  {
	    errstr = "free(): invalid next size (fast)";
	    goto errout;
	  }
	if (! have_lock)
	  {
	    (void)mutex_unlock(&av->mutex);
	    locked = 0;
	  }
      }

    free_perturb (chunk2mem(p), size - 2 * SIZE_SZ);

    set_fastchunks(av);
    unsigned int idx = fastbin_index(size);
    fb = &fastbin (av, idx);

    /* Atomically link P to its fastbin: P->FD = *FB; *FB = P;  */
    mchunkptr old = *fb, old2;
    unsigned int old_idx = ~0u;
    do
      {
	/* Check that the top of the bin is not the record we are going to add
	   (i.e., double free).  */
	if (__builtin_expect (old == p, 0))
	  {
	    errstr = "double free or corruption (fasttop)";
	    goto errout;
	  }
	/* Check that size of fastbin chunk at the top is the same as
	   size of the chunk that we are adding.  We can dereference OLD
	   only if we have the lock, otherwise it might have already been
	   deallocated.  See use of OLD_IDX below for the actual check.  */
	if (have_lock && old != NULL)
	  old_idx = fastbin_index(chunksize(old));
	p->fd = old2 = old;
      }
    while ((old = catomic_compare_and_exchange_val_rel (fb, p, old2)) != old2);

    if (have_lock && old != NULL && __builtin_expect (old_idx != idx, 0))
      {
	errstr = "invalid fastbin entry (free)";
	goto errout;
      }
  }

  /*
    Consolidate other non-mmapped chunks as they arrive.
  */

  else if (!chunk_is_mmapped(p)) {
    if (! have_lock) {
      (void)mutex_lock(&av->mutex);
      locked = 1;
    }

    nextchunk = chunk_at_offset(p, size);

    /* Lightweight tests: check whether the block is already the
       top block.  */
    if (__glibc_unlikely (p == av->top))
      {
	errstr = "double free or corruption (top)";
	goto errout;
      }
    /* Or whether the next chunk is beyond the boundaries of the arena.  */
    if (__builtin_expect (contiguous (av)
			  && (char *) nextchunk
			  >= ((char *) av->top + chunksize(av->top)), 0))
      {
	errstr = "double free or corruption (out)";
	goto errout;
      }
    /* Or whether the block is actually not marked used.  */
    if (__glibc_unlikely (!prev_inuse(nextchunk)))
      {
	errstr = "double free or corruption (!prev)";
	goto errout;
      }

    nextsize = chunksize(nextchunk);
    if (__builtin_expect (nextchunk->size <= 2 * SIZE_SZ, 0)
	|| __builtin_expect (nextsize >= av->system_mem, 0))
      {
	errstr = "free(): invalid next size (normal)";
	goto errout;
      }

    free_perturb (chunk2mem(p), size - 2 * SIZE_SZ);

    /* consolidate backward */
    if (!prev_inuse(p)) {
      prevsize = p->prev_size;
      size += prevsize;
      p = chunk_at_offset(p, -((long) prevsize));
      unlink(av, p, bck, fwd);
    }

    if (nextchunk != av->top) {
      /* get and clear inuse bit */
      nextinuse = inuse_bit_at_offset(nextchunk, nextsize);

      /* consolidate forward */
      if (!nextinuse) {
	unlink(av, nextchunk, bck, fwd);
	size += nextsize;
      } else
	clear_inuse_bit_at_offset(nextchunk, 0);

      /*
	Place the chunk in unsorted chunk list. Chunks are
	not placed into regular bins until after they have
	been given one chance to be used in malloc.
      */

      bck = unsorted_chunks(av);
      fwd = bck->fd;
      if (__glibc_unlikely (fwd->bk != bck))
	{
	  errstr = "free(): corrupted unsorted chunks";
	  goto errout;
	}
      p->fd = fwd;
      p->bk = bck;
      if (!in_smallbin_range(size))
	{
	  p->fd_nextsize = NULL;
	  p->bk_nextsize = NULL;
	}
      bck->fd = p;
      fwd->bk = p;

      set_head(p, size | PREV_INUSE);
      set_foot(p, size);

      check_free_chunk(av, p);
    }

    /*
      If the chunk borders the current high end of memory,
      consolidate into top
    */

    else {
      size += nextsize;
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

    if ((unsigned long)(size) >= FASTBIN_CONSOLIDATION_THRESHOLD) {
      if (have_fastchunks(av))
	malloc_consolidate(av);

      if (av == &main_arena) {
#ifndef MORECORE_CANNOT_TRIM
	if ((unsigned long)(chunksize(av->top)) >=
	    (unsigned long)(mp_.trim_threshold))
	  systrim(mp_.top_pad, av);
#endif
      } else {
	/* Always try heap_trim(), even if the top chunk is not
	   large, because the corresponding heap might go away.  */
	heap_info *heap = heap_for_ptr(top(av));

	assert(heap->ar_ptr == av);
	heap_trim(heap, mp_.top_pad);
      }
    }

    if (! have_lock) {
      assert (locked);
      (void)mutex_unlock(&av->mutex);
    }
  }
  /*
    If the chunk was allocated via mmap, release via munmap().
  */

  else {
    munmap_chunk (p);
  }
}
```

为什么我们要搜索“_int_free”关键字，因为在调用free函数的时候其实是调用了_int_free函数，在_int_free中调用了unlink宏定义。

他们之间的关系大概类似于这样：

```c
//注意，这个代码表示了三者之间的关系，在glibc中并不存在此代码
#define unlink(AV, P, BK, FD)
static void _int_free (mstate av, mchunkptr p, int have_lock)
free(){
	_int_free(){
		unlink();
	}
}
```

# 堆释放
关于unlink的介绍就先到这里，上面的源码看不懂没有关系，知道它们三者的联系就行了。

接下来看堆释放调用free函数的过程：

```c
//gcc -g test.c -o test
#include<stdio.h>、
int main(){
    long *p1 = malloc(0x80);
    long *first_chunk = malloc(0x80);
    long *p2 = malloc(0x80);
    long *second_chunk = malloc(0x80);
    long *p3 = malloc(0x80);
    long *third_chunk = malloc(0x80);
    long *p4 = malloc(0x80);
    free(first_chunk);
    free(second_chunk);
    free(third_chunk);
    return 0;
}
```

代码中向系统申请了7个malloc，然后依次释放了first_chunk、second_chunk、third_chunk。为什么要释放这几个特定的chunk？因为地址相邻的chunk释放之后会进行合并，而不相邻的chunk并不会合并。由于申请的是0x80的chunk，所以在释放之后不会进fastbin（单向链表）而是进unsoredtbin（双向链表）。

编译时我们使用了-g参数，so，可以在对代码行号进行下断点。

进行gdb动态调试，在代码的第14行下断点：

> 运行程序时请使用管理员身份运行，否则出现的堆情况与如下日志可能不一致。
>

```powershell
➜  unlink_data sudo gdb test
[sudo] password for ubuntu: 
GNU gdb (Ubuntu 7.11.1-0ubuntu1~16.5) 7.11.1
Copyright (C) 2016 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.  Type "show copying"
and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
<http://www.gnu.org/software/gdb/documentation/>.
For help, type "help".
Type "apropos word" to search for commands related to "word"...
pwndbg: loaded 187 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
Reading symbols from test...done.
pwndbg> b 14
Breakpoint 1 at 0x4005f4: file test.c, line 14.
pwndbg> r
Starting program: /home/ubuntu/Desktop/unlink_data/test 

Breakpoint 1, main () at test.c:14
14	    return 0;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]─────────────────────────────────
 RAX  0x1
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RDX  0x0
 RDI  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RSI  0x0
 R8   0x602000 ◂— 0x0
 R9   0x1
 R10  0x8b8
 R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffe660 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffe580 —▸ 0x400600 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffe540 ◂— 0x1
 RIP  0x4005f4 (main+142) ◂— mov    eax, 0
──────────────────────────────────[ DISASM ]───────────────────────────────────
 ► 0x4005f4       <main+142>                 mov    eax, 0
   0x4005f9       <main+147>                 leave  
   0x4005fa       <main+148>                 ret    
    ↓
   0x7ffff7a2d840 <__libc_start_main+240>    mov    edi, eax
   0x7ffff7a2d842 <__libc_start_main+242>    call   exit <exit>
 
   0x7ffff7a2d847 <__libc_start_main+247>    xor    edx, edx
   0x7ffff7a2d849 <__libc_start_main+249>    jmp    __libc_start_main+57 <__libc_start_main+57>
 
   0x7ffff7a2d84e <__libc_start_main+254>    mov    rax, qword ptr [rip + 0x3a8ebb] <0x7ffff7dd6710>
   0x7ffff7a2d855 <__libc_start_main+261>    ror    rax, 0x11
   0x7ffff7a2d859 <__libc_start_main+265>    xor    rax, qword ptr fs:[0x30]
   0x7ffff7a2d862 <__libc_start_main+274>    call   rax
───────────────────────────────[ SOURCE (CODE) ]───────────────────────────────
In file: /home/ubuntu/Desktop/unlink_data/test.c
    9     long *third_chunk = malloc(0x80);
   10     long *p4 = malloc(0x80);
   11     free(first_chunk);
   12     free(second_chunk);
   13     free(third_chunk);
 ► 14     return 0;
   15 }
───────────────────────────────────[ STACK ]───────────────────────────────────
00:0000│ rsp  0x7fffffffe540 ◂— 0x1
01:0008│      0x7fffffffe548 —▸ 0x602010 ◂— 0x0
02:0010│      0x7fffffffe550 —▸ 0x6020a0 —▸ 0x7ffff7dd1b78 (main_arena+88) —▸ 0x6023f0 ◂— 0x0
03:0018│      0x7fffffffe558 —▸ 0x602130 ◂— 0x0
04:0020│      0x7fffffffe560 —▸ 0x6021c0 —▸ 0x602090 ◂— 0x0
05:0028│      0x7fffffffe568 —▸ 0x602250 ◂— 0x0
06:0030│      0x7fffffffe570 —▸ 0x6022e0 —▸ 0x6021b0 ◂— 0x0
07:0038│      0x7fffffffe578 —▸ 0x602370 ◂— 0x0
─────────────────────────────────[ BACKTRACE ]─────────────────────────────────
 ► f 0           4005f4 main+142
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

看一下bin与heap的情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600738382701-f132e26a-9283-401b-87f3-115078fe190d.png)

> corrupted
>
> adj. 腐败的；毁坏的；崩溃的
>
> v. （使）腐败；（使）堕落（corrupt的过去分词）
>

可以看到三个chunk进入了unsortedbin：

+ 0x6022d0：third_chunk
+ 0x6021b0：second_chunk
+ 0x602090：first_chunk

main_arena情况如下：

```powershell
pwndbg> x/32gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x00000000006023f0 //top_chunk地址
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00000000006022d0 //third_chunk地址
0x7ffff7dd1b90 <main_arena+112>:	0x0000000000602090 //first_chunk	0x00007ffff7dd1b88
0x7ffff7dd1ba0 <main_arena+128>:	0x00007ffff7dd1b88	0x00007ffff7dd1b98
0x7ffff7dd1bb0 <main_arena+144>:	0x00007ffff7dd1b98	0x00007ffff7dd1ba8
0x7ffff7dd1bc0 <main_arena+160>:	0x00007ffff7dd1ba8	0x00007ffff7dd1bb8
```

看一下first_chunk的内存情况：

```powershell
pwndbg> x/16gx 0x602090
0x602090:	0x0000000000000000	0x0000000000000091 //prev_size;size
0x6020a0:	0x00007ffff7dd1b78	0x00000000006021b0 //fd(main_arena);bk(下一个堆的起始地址)
0x6020b0:	0x0000000000000000	0x0000000000000000 //fd_nextsize;bk_nextsize
0x6020c0:	0x0000000000000000	0x0000000000000000
0x6020d0:	0x0000000000000000	0x0000000000000000
0x6020e0:	0x0000000000000000	0x0000000000000000
0x6020f0:	0x0000000000000000	0x0000000000000000
0x602100:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

second_chunk：

```powershell
pwndbg> x/16gx 0x6021b0
0x6021b0:	0x0000000000000000	0x0000000000000091 //prev_size;size
0x6021c0:	0x0000000000602090	0x00000000006022d0 //fd(上一个堆的起始地址);bk（下一个堆的起始地址）
0x6021d0:	0x0000000000000000	0x0000000000000000 //fd_nextsize;bk_nextsize
0x6021e0:	0x0000000000000000	0x0000000000000000
0x6021f0:	0x0000000000000000	0x0000000000000000
0x602200:	0x0000000000000000	0x0000000000000000
0x602210:	0x0000000000000000	0x0000000000000000
0x602220:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

third_chunk：

```powershell
pwndbg> x/16gx 0x6022d0
0x6022d0:	0x0000000000000000	0x0000000000000091 //prev_size;size
0x6022e0:	0x00000000006021b0	0x00007ffff7dd1b78 //fd(上一个堆的起始地址);bk（main_arena）
0x6022f0:	0x0000000000000000	0x0000000000000000 //fd_nextsize;bk_nextsize
0x602300:	0x0000000000000000	0x0000000000000000
0x602310:	0x0000000000000000	0x0000000000000000
0x602320:	0x0000000000000000	0x0000000000000000
0x602330:	0x0000000000000000	0x0000000000000000
0x602340:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

> + `fd_nextsize`， `bk_nextsize`，是只有 chunk **<font style="color:#F5222D;">空闲</font>**的时候才使用，不过其用于较大的 chunk（large chunk）。
>     - **fd_nextsize** 指向前一个与当前 chunk 大小不同的第一个空闲块，**不包含 bin 的头指针**。
>     - **bk_nextsize** 指向后一个与当前 chunk 大小不同的第一个空闲块，**不包含 bin 的头指针**。
>

# unlink的过程及检查
CTF-Wiki上有这个讲解，但是那个讲解很难理解，下面我就按照自己的理解说吧：

> CTF-Wiki讲解：[https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/unlink-zh/](https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/unlink-zh/)
>

我们还是使用之前的例子，再次贴一下源码：

```c
//gcc -g test.c -o test
#include<stdio.h>、
int main(){
    long *p1 = malloc(0x80);
    long *first_chunk = malloc(0x80);
    long *p2 = malloc(0x80);
    long *second_chunk = malloc(0x80);
    long *p3 = malloc(0x80);
    long *third_chunk = malloc(0x80);
    long *p4 = malloc(0x80);
    free(first_chunk);
    free(second_chunk);
    free(third_chunk);
    return 0;
}
```

释放后的三个chunk在unsorted bin中的图形化如下：

**<font style="color:#F5222D;">高地址</font>**                                                                                                                                       **<font style="color:#F5222D;">低地址</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600742670126-b80a5502-2d02-4635-aff5-fb3d46ec1456.png)

> 1. second_fd = first_prev_addr
> 2. second_bk = third_prev_addr
> 3. first_bk = third_prev_addr  
> 4. third_fd = first_prev_addr 
>

unlink其实就是将unsorted bin中的second_chunk“摘掉”，但是怎么摘掉呢？

从前面对三个unsorted bin中的注释我们可以知道（针对中间被释放的chunk而言）：

+ fd指向前一个被释放chunk的prev_size地址：second_fd = first_prev_addr
+ bk指向后一个被释放chunk的prev_size地址：second_bk = third_prev_addr

如果second_chunk被“摘掉”，那么就会变成下面这样：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600743926724-c0657138-4e0b-4cf2-a44e-63184f5d03c2.png)



> 1. first_bk = third_prev_addr
> 2. third_fd = first_prev_addr
>

# chunk状态检查
现在我们用的大多数Linux都会对chunk状态进行检查，以免造成二次释放或二次申请的问题。但是这个检查的流程本身就存在着一些漏洞，从而可以让我们去利用。

回顾一下以往我们做的题，大部分都是修改栈或堆中的参数来改变程序的执行流程。unlink同样可以以这种方式进行利用，由于unlink是在free函数中调用的，所以我们只看chunk空闲的时候需要向其中写入什么。

还是拿前面的例子来说：

```c
//gcc -g test.c -o test
#include<stdio.h>、
int main(){
    long *p1 = malloc(0x80);
    long *first_chunk = malloc(0x80);
    long *p2 = malloc(0x80);
    long *second_chunk = malloc(0x80);
    long *p3 = malloc(0x80);
    long *third_chunk = malloc(0x80);
    long *p4 = malloc(0x80);
    free(first_chunk);
    free(second_chunk);
    free(third_chunk);
    return 0;
}
```

还是在14行下断点，查看一下second_chunk：（以sudo执行）

```c
➜  unlink_data sudo gdb test
[sudo] password for ubuntu: 
GNU gdb (Ubuntu 7.11.1-0ubuntu1~16.5) 7.11.1
Copyright (C) 2016 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.  Type "show copying"
and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
<http://www.gnu.org/software/gdb/documentation/>.
For help, type "help".
Type "apropos word" to search for commands related to "word"...
pwndbg: loaded 187 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
Reading symbols from test...done.
pwndbg> b 14
Breakpoint 1 at 0x4005f4: file test.c, line 14.
pwndbg> r
Starting program: /home/ubuntu/Desktop/unlink_data/test 

Breakpoint 1, main () at test.c:14
14	    return 0;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0x1
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RDX  0x0
 RDI  0x7ffff7dd1b20 (main_arena) ◂— 0x100000000
 RSI  0x0
 R8   0x602000 ◂— 0x0
 R9   0x1
 R10  0x8b8
 R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffe660 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffe580 —▸ 0x400600 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffe540 ◂— 0x1
 RIP  0x4005f4 (main+142) ◂— mov    eax, 0
───────────────────────────────────[ DISASM ]───────────────────────────────────
 ► 0x4005f4       <main+142>                 mov    eax, 0
   0x4005f9       <main+147>                 leave  
   0x4005fa       <main+148>                 ret    
    ↓
   0x7ffff7a2d840 <__libc_start_main+240>    mov    edi, eax
   0x7ffff7a2d842 <__libc_start_main+242>    call   exit <exit>
 
   0x7ffff7a2d847 <__libc_start_main+247>    xor    edx, edx
   0x7ffff7a2d849 <__libc_start_main+249>    jmp    __libc_start_main+57 <__libc_start_main+57>
 
   0x7ffff7a2d84e <__libc_start_main+254>    mov    rax, qword ptr [rip + 0x3a8ebb] <0x7ffff7dd6710>
   0x7ffff7a2d855 <__libc_start_main+261>    ror    rax, 0x11
   0x7ffff7a2d859 <__libc_start_main+265>    xor    rax, qword ptr fs:[0x30]
   0x7ffff7a2d862 <__libc_start_main+274>    call   rax
───────────────────────────────[ SOURCE (CODE) ]────────────────────────────────
In file: /home/ubuntu/Desktop/unlink_data/test.c
    9     long *third_chunk = malloc(0x80);
   10     long *p4 = malloc(0x80);
   11     free(first_chunk);
   12     free(second_chunk);
   13     free(third_chunk);
 ► 14     return 0;
   15 }
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffe540 ◂— 0x1
01:0008│      0x7fffffffe548 —▸ 0x602010 ◂— 0x0
02:0010│      0x7fffffffe550 —▸ 0x6020a0 —▸ 0x7ffff7dd1b78 (main_arena+88) —▸ 0x6023f0 ◂— 0x0
03:0018│      0x7fffffffe558 —▸ 0x602130 ◂— 0x0
04:0020│      0x7fffffffe560 —▸ 0x6021c0 —▸ 0x602090 ◂— 0x0
05:0028│      0x7fffffffe568 —▸ 0x602250 ◂— 0x0
06:0030│      0x7fffffffe570 —▸ 0x6022e0 —▸ 0x6021b0 ◂— 0x0
07:0038│      0x7fffffffe578 —▸ 0x602370 ◂— 0x0
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0           4005f4 main+142
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all [corrupted]
FD: 0x6022d0 —▸ 0x6021b0 —▸ 0x602090 —▸ 0x7ffff7dd1b78 (main_arena+88) ◂— 0x6022d0
BK: 0x602090 ◂— 0x0
smallbins
empty
largebins
empty
pwndbg> x/50gx 0x6021b0
//second_chunk_addr_start
0x6021b0:	0x0000000000000000	0x00000000000000(91) //prev_size;size
0x6021c0:  【0x0000000000602090】【0x00000000006022d0】 //fd;bk
0x6021d0:	0x0000000000000000	0x0000000000000000 
0x6021e0:	0x0000000000000000	0x0000000000000000
0x6021f0:	0x0000000000000000	0x0000000000000000
0x602200:	0x0000000000000000	0x0000000000000000
0x602210:	0x0000000000000000	0x0000000000000000
0x602220:	0x0000000000000000	0x0000000000000000
0x602230:	0x0000000000000000	0x0000000000000000
//second_chunk_addr_end
//p3_malloc_start
0x602240:	0x00000000000000(90)	0x00000000000000[90] //prev_size;size
0x602250:	0x0000000000000000	0x0000000000000000
0x602260:	0x0000000000000000	0x0000000000000000
0x602270:	0x0000000000000000	0x0000000000000000
0x602280:	0x0000000000000000	0x0000000000000000
0x602290:	0x0000000000000000	0x0000000000000000
0x6022a0:	0x0000000000000000	0x0000000000000000
0x6022b0:	0x0000000000000000	0x0000000000000000
0x6022c0:	0x0000000000000000	0x0000000000000000 
//p3_malloc_end    
//third_chunk_addr_start
0x6022d0:	0x0000000000000000	0x0000000000000091 
0x6022e0:	0x00000000006021b0	0x00007ffff7dd1b78
0x6022f0:	0x0000000000000000	0x0000000000000000
0x602300:	0x0000000000000000	0x0000000000000000
0x602310:	0x0000000000000000	0x0000000000000000
0x602320:	0x0000000000000000	0x0000000000000000
0x602330:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

本地变量的信息如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600751039208-7c52da39-f46e-4425-9791-492680e9fa8c.png)

+ **<font style="color:#F5222D;">检查1</font>**：检查与被释放chunk相邻**高地址**的chunk的prev_size的值是否等于被释放chunk的size大小。

可以看上面文本框的内容，上面的第一个()中的内容是second_chunk的size大小，下面第二个()是p3的prev_size，这两个数值是需要相等的（忽略P标志位）。wiki上基础部分有讲过，如果一个块属于空闲状态，那么相邻高地址块的prev_size为前一个块的大小

+ **<font style="color:#F5222D;">检查2</font>**：检查与被释放chunk相邻高地址的chunk的size的P标志位是否为0

上面[]中的内容是p3的size，p3的size的P标志位为0，代表着它前一个chunk(second_chunk)为空闲状态。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600752152092-5acd3272-8d86-4bb4-a3cf-42104e6143d9.png)

+ **<font style="color:#F5222D;">检查3</font>**：检查前后被释放chunk的fd和bk

可以看【】中的内容，这里是second_chunk的fd和bk。首先看fd，它指向的位置就是前一个被释放的块first_chunk，这里需要检查的是first_chunk的bk是否指向second_chunk的地址。再看second_chunk的bk，它指向的是后一个被释放的块third_chunk，这里需要检查的是third_chunk的fd是否指向second_chunk的地址



以上三点就是检查chunk是否空闲的三大标准。其实说到这我们依然还是不清楚到底应该怎么去利用这个unlink，我在一开始学的时候也很蒙。没有关系，在下一小结中我们拿题去理解。

