> 参考资料：CTF-wiki：[https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/tcache_attack-zh/#tcache-dup](https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/tcache_attack-zh/#tcache-dup)
>
> 代码汉化：@yichen：[https://www.yuque.com/hxfqg9/bin/qlry85#g5z3g](https://www.yuque.com/hxfqg9/bin/qlry85#g5z3g)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1X6PqMvKMTbeIlrv00FelAA](https://pan.baidu.com/s/1X6PqMvKMTbeIlrv00FelAA)  密码: u7pc
>
> --来自百度网盘超级会员V3的分享
>

Linux环境和上一篇文章所处的环境完全相同，这里不在多说。

# 漏洞原理
> 这里使用libc-2.27.so的源码进行分析
>

Tcache dup利用的是tcache_put()函数的不严谨：

```c
#代码第2923-2933行：
/* Caller must ensure that we know tc_idx is valid and there's room
   for more chunks.  */
static __always_inline void
tcache_put (mchunkptr chunk, size_t tc_idx)
{
  tcache_entry *e = (tcache_entry *) chunk2mem (chunk);
  assert (tc_idx < TCACHE_MAX_BINS);
  e->next = tcache->entries[tc_idx];
  tcache->entries[tc_idx] = e;
  ++(tcache->counts[tc_idx]);
}
```

从上面的代码可以看出，在libc-2.27版本中没有对tcache_put函数进行检查，甚至没有对tcache->counts[tc_idx] 的检查，在大幅度提高性能的同时安全性也下降来许多。

因为在这个函数中没有任何的检查，所以我们可以直接对同一个chunk进行多次free，造成cyclical list。

> Tcache dup类似于之前fastbin_attack中的double free，但是后者的检查要更多。
>

# Demo
接下来我们使用一个demo来进行说明。

```c
//gcc -g -fno-stack-protector -z execstack -no-pie -z norelro test.c -o test
#include <stdio.h>
#include <stdlib.h>

int main()
{
    fprintf(stderr, "先申请一块内存\n");
    int *a = malloc(8);

    fprintf(stderr, "申请的内存地址是: %p\n", a);
    fprintf(stderr, "对这块内存地址 free两次\n");
    free(a);
    free(a);

    fprintf(stderr, "这时候链表是这样的 [ %p, %p ].\n", a, a);
    fprintf(stderr, "接下来再去 malloc 两次: [ %p, %p ].\n", malloc(8), malloc(8));
    fprintf(stderr, "Finish!!!\n");
    return 0;
}
```

编译完成之后，使用pwndbg调试程序，首先对代码的第12行下断点，然后开始调试程序，此时的内存状况如下：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x601250
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> x/100gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000000000	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000020d91 #top_chunk
......(省略内容均为空)
0x601310:	0x0000000000000000	0x0000000000000000
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
pwndbg> x/16gx &main_arena
0x7ffff7dcfc40 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc50 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc60 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc70 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc80 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc90 <main_arena+80>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfca0 <main_arena+96>:	0x0000000000601270	0x0000000000000000
    							#指向top_chunk
0x7ffff7dcfcb0 <main_arena+112>:	0x00007ffff7dcfca0	0x00007ffff7dcfca0
pwndbg> 

```

由于在tcache_put函数中没有对堆块进行检查，接下来我们对malloc出的chunk进行多次free。

对代码的第15行下断点，继续调试：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x601250
Size: 0x21
fd: 0x601260

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> x/100gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x601010:	0x0000000000000002	0x0000000000000000
    		#count=2
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000601260	0x0000000000000000
    		#指向chunk1_data
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000601260	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000020d91 #top_chunk
......(省略内容均为空)
0x601310:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0x20 [  2]: 0x601260 ◂— 0x601260
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
pwndbg> x/16gx &main_arena
0x7ffff7dcfc40 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc50 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc60 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc70 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc80 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc90 <main_arena+80>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfca0 <main_arena+96>:	0x0000000000601270	0x0000000000000000
    							#指向top_chunk
0x7ffff7dcfcb0 <main_arena+112>:	0x00007ffff7dcfca0	0x00007ffff7dcfca0
pwndbg> 
```

从上面的内存中可以看出，对chunk1进行两次free之后，在tcache中形成了cyclical list，也就是说chunk1中的next指针指向其本身的chunk_data。

由于接下来有两次malloc，因此先来看第一次malloc之后的内存，对malloc下断点：

> 命令：b malloc
>

继续调试程序，由于对malloc下断点，因此程序会停在malloc的push rbp，也就是说程序并没有进行第一次malloc，因此我们输入c继续运行程序，结果如下：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x601250
Size: 0x21
fd: 0x601260

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> bin
tcachebins
0x20 [  1]: 0x601260 ◂— 0x601260
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
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x601250
Size: 0x21
fd: 0x601260

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> x/100gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x601010:	0x0000000000000001	0x0000000000000000
    		#count=1
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000601260	0x0000000000000000
......（省略内容均为空）
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000601260	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000020d91 #top_chunk
......（省略内容均为空）
0x601310:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0x20 [  1]: 0x601260 ◂— 0x601260
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
pwndbg> x/16gx &main_arena
0x7ffff7dcfc40 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc50 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc60 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc70 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc80 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc90 <main_arena+80>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfca0 <main_arena+96>:	0x0000000000601270	0x0000000000000000
    							#指向top_chunk
0x7ffff7dcfcb0 <main_arena+112>:	0x00007ffff7dcfca0	0x00007ffff7dcfca0
pwndbg> 
```

为了防止程序跑飞，接下来对代码的第17行下断点，看一下第二次malloc之后的结果：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x601250
Size: 0x21
fd: 0x601260

Top chunk | PREV_INUSE
Addr: 0x601270
Size: 0x20d91

pwndbg> bin
tcachebins
0x20 [  0]: 0x601260 ◂— ...
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
pwndbg> x/16gx &main_arena
0x7ffff7dcfc40 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc50 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc60 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc70 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc80 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfc90 <main_arena+80>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcfca0 <main_arena+96>:	0x0000000000601270	0x0000000000000000
0x7ffff7dcfcb0 <main_arena+112>:	0x00007ffff7dcfca0	0x00007ffff7dcfca0
pwndbg> x/100gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct 
0x601010:	0x0000000000000000	0x0000000000000000
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000601260	0x0000000000000000
    		#执行chunk1_data
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000021 #chunk1
0x601260:	0x0000000000601260	0x0000000000000000
0x601270:	0x0000000000000000	0x0000000000020d91 #top_chunk
......(省略内容均为空) 
0x601310:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

上面就是tcache_dup的攻击方式，看起来好像没有什么用，下篇文章中的例子会体现。

