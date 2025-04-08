上一小节我们讲述了fastbin_attack中的基本原理，接下来仔细说说fastbin_double_free。

> 参考资料：[https://wiki.x10sec.org/pwn/heap/fastbin_attack/](https://wiki.x10sec.org/pwn/heap/fastbin_attack/)
>
> 附件下载：
>
> 链接：[https://pan.baidu.com/s/16vNLYoEUwF_PI7bm-SXqiA](https://pan.baidu.com/s/16vNLYoEUwF_PI7bm-SXqiA)
>
> 提取码：jfxq 
>

> 复制这段内容后打开百度网盘手机App，操作更方便哦
>

# 简介
fastbin double free是fastbin_attack中的一种，顾名思义就是fastbin中的chunk可以多次释放，因此可以在fastbin单链表中可以存在多次。这样导致的后果是多次分配可以从fastbin链表中取出同一个堆块，相当于多个指针指向同一堆块，结合堆块中的数据内容可以实现类似于类型混淆（type confused）的效果。

**Fastbin Double Free 能够成功利用主要有两部分的原因**

1. **fastbin 的堆块被释放后 next_chunk 的 pre_inuse 位不会被清空**
2. **fastbin 在执行 free 的时候仅验证了 main_arena 直接指向的块，即链表指针头部的块。对于链表后面的块，并没有进行验证。**

在libc-2.23.so中的源代码如下：

```c
/* Check that the top of the bin is not the record we are going to add
	   (i.e., double free).  */
	if (__builtin_expect (old == p, 0))
	  {
	    errstr = "double free or corruption (fasttop)";
	    goto errout;
	  }
```

# 演示
下列的示例可以说明系统检测fastbin double free的机制：

> 编译：gcc -g test2.c -o test2
>

```c
#include<stdio.h>
int main()
{
    void *chunk1,*chunk2,*chunk3;
    chunk1=malloc(0x10);
    chunk2=malloc(0x10);
    free(chunk1);
    free(chunk1);
    return 0;
}
```

编译之后运行一下，如果不出意外的话会出现如下情况：

```c
➜  fastbin_double_free ./test2
*** Error in `./test2': double free or corruption (fasttop): 0x0000000000632010 ***
======= Backtrace: =========
/lib/x86_64-linux-gnu/libc.so.6(+0x777f5)[0x7f53c88a57f5]
/lib/x86_64-linux-gnu/libc.so.6(+0x8038a)[0x7f53c88ae38a]
/lib/x86_64-linux-gnu/libc.so.6(cfree+0x4c)[0x7f53c88b258c]
./test2[0x4005a2]
/lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0xf0)[0x7f53c884e840]
./test2[0x400499]
======= Memory map: ========
00400000-00401000 r-xp 00000000 08:01 2106612                            /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/test2
00600000-00601000 r--p 00000000 08:01 2106612                            /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/test2
00601000-00602000 rw-p 00001000 08:01 2106612                            /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/test2
00632000-00653000 rw-p 00000000 00:00 0                                  [heap]
7f53c4000000-7f53c4021000 rw-p 00000000 00:00 0 
7f53c4021000-7f53c8000000 ---p 00000000 00:00 0 
7f53c8618000-7f53c862e000 r-xp 00000000 08:01 1313748                    /lib/x86_64-linux-gnu/libgcc_s.so.1
7f53c862e000-7f53c882d000 ---p 00016000 08:01 1313748                    /lib/x86_64-linux-gnu/libgcc_s.so.1
7f53c882d000-7f53c882e000 rw-p 00015000 08:01 1313748                    /lib/x86_64-linux-gnu/libgcc_s.so.1
7f53c882e000-7f53c89ee000 r-xp 00000000 08:01 1313436                    /lib/x86_64-linux-gnu/libc-2.23.so
7f53c89ee000-7f53c8bee000 ---p 001c0000 08:01 1313436                    /lib/x86_64-linux-gnu/libc-2.23.so
7f53c8bee000-7f53c8bf2000 r--p 001c0000 08:01 1313436                    /lib/x86_64-linux-gnu/libc-2.23.so
7f53c8bf2000-7f53c8bf4000 rw-p 001c4000 08:01 1313436                    /lib/x86_64-linux-gnu/libc-2.23.so
7f53c8bf4000-7f53c8bf8000 rw-p 00000000 00:00 0 
7f53c8bf8000-7f53c8c1e000 r-xp 00000000 08:01 1313740                    /lib/x86_64-linux-gnu/ld-2.23.so
7f53c8e02000-7f53c8e05000 rw-p 00000000 00:00 0 
7f53c8e1c000-7f53c8e1d000 rw-p 00000000 00:00 0 
7f53c8e1d000-7f53c8e1e000 r--p 00025000 08:01 1313740                    /lib/x86_64-linux-gnu/ld-2.23.so
7f53c8e1e000-7f53c8e1f000 rw-p 00026000 08:01 1313740                    /lib/x86_64-linux-gnu/ld-2.23.so
7f53c8e1f000-7f53c8e20000 rw-p 00000000 00:00 0 
7ffecbc51000-7ffecbc72000 rw-p 00000000 00:00 0                          [stack]
7ffecbc98000-7ffecbc9b000 r--p 00000000 00:00 0                          [vvar]
7ffecbc9b000-7ffecbc9d000 r-xp 00000000 00:00 0                          [vdso]
ffffffffff600000-ffffffffff601000 r-xp 00000000 00:00 0                  [vsyscall]
[1]    6002 abort (core dumped)  ./test2
➜  fastbin_double_free 
```

这正是 _int_free 函数检测到了 fastbin 的 double free，但是我们将代码稍微改动一下呢？

```c
#include<stdio.h>
int main()
{
    void *chunk1,*chunk2,*chunk3;
    chunk1=malloc(0x10);
    chunk2=malloc(0x10);
    free(chunk1);
    free(chunk2);
    free(chunk1);
    return 0;
}
```

> 编译：gcc -g test3.c -o test3
>

使用gdb进行调试，将断点在在程序的第10行：

```c
➜  fastbin_double_free gdb test3
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
Reading symbols from test3...done.
pwndbg> b 10
Breakpoint 1 at 0x4005ae: file test3.c, line 10.
pwndbg> r
Starting program: /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/test3 

Breakpoint 1, main () at test3.c:10
10	    return 0;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0x602020 ◂— 0x0
 RBX  0x0
 RCX  0x7ffff7dd1b00 (__memalign_hook) —▸ 0x7ffff7a92ea0 (memalign_hook_ini) ◂— push   r12
 RDX  0x602020 ◂— 0x0
 RDI  0xffffffff
 RSI  0x7ffff7dd1b28 (main_arena+8) —▸ 0x602000 ◂— 0x0
 R8   0x602010 —▸ 0x602020 ◂— 0x0
 R9   0x0
 R10  0x8b8
 R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffde70 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffdd90 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffdd80 —▸ 0x602010 —▸ 0x602020 ◂— 0x0
 RIP  0x4005ae (main+72) ◂— mov    eax, 0
───────────────────────────────────[ DISASM ]───────────────────────────────────
 ► 0x4005ae       <main+72>                  mov    eax, 0
   0x4005b3       <main+77>                  leave  
   0x4005b4       <main+78>                  ret    
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
In file: /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/test3.c
    5     chunk1=malloc(0x10);
    6     chunk2=malloc(0x10);
    7     free(chunk1);
    8     free(chunk2);
    9     free(chunk1);
 ► 10     return 0;
   11 }
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffdd80 —▸ 0x602010 —▸ 0x602020 ◂— 0x0
01:0008│      0x7fffffffdd88 —▸ 0x602030 —▸ 0x602000 ◂— 0x0
02:0010│ rbp  0x7fffffffdd90 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffdd98 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffdda0 ◂— 0x1
05:0028│      0x7fffffffdda8 —▸ 0x7fffffffde78 —▸ 0x7fffffffe1f3 ◂— '/home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/test3'
06:0030│      0x7fffffffddb0 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffddb8 —▸ 0x400566 (main) ◂— push   rbp
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0           4005ae main+72
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg>
```

heap和bin的详细状况如下：

> 这里heap和bin的数据并不准确，这里看看就好
>

```c
pwndbg> heap
Allocated chunk
Addr: 0x602000
Size: 0x602020

pwndbg> bin
fastbins
0x20: 0x602000 ◂— 0x21 /* '!' */
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

内存的详细状况：

```c
pwndbg> x/20gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000602020	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000021 #chunk2
0x602030:	0x0000000000602000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000020fc1 #top_chunk
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
0x602080:	0x0000000000000000	0x0000000000000000
0x602090:	0x0000000000000000	0x0000000000000000
pwndbg> x/20gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000602000 #指向chunk1
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602040 #指向top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
0x7ffff7dd1ba0 <main_arena+128>:	0x00007ffff7dd1b88	0x00007ffff7dd1b98
0x7ffff7dd1bb0 <main_arena+144>:	0x00007ffff7dd1b98	0x00007ffff7dd1ba8
pwndbg> 
```

<font style="color:rgba(0, 0, 0, 0.87);">第一次释放</font>`free(chunk1)`

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601945211432-fca87526-fc1d-433d-9a72-054b538fb33b.png)

第二次释放`free(chunk2)`

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601945211445-ad96e4f9-dd69-411c-8cd3-0f958be3fdd6.png)

第三次释放`free(chunk1)`

注意因为chunk1被再次释放，因此其fd的值不再为0而是指向chunk2（请仔细理解下这句话），这时如果我们可以控制chunk1的内容，便可以写入其fd指针从而实现在任意地址分配fastbin块。下面的这个示例就演示了一点，首先和前面一样构造如下图的链表，然后第一次调用malloc返回chunk1，之后修改chunk1的fd的指针指向bss段上的bss_chunk，之后我们可以看到fastbin会把堆块分配到bss_chunk：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601945211476-e5e0cac9-2d57-48f8-91b0-428b945add91.png)

> 演示源代码如下：
>
> 编译：gcc -g test4.c -o test4
>

```c
#include<stdio.h>
typedef struct _chunk
{
    long long pre_size;
    long long size;
    long long fd;
    long long bk;  
} CHUNK,*PCHUNK;

CHUNK bss_chunk;

int main()
{
    void *chunk1,*chunk2,*chunk3;
    void *chunk_a,*chunk_b;

    bss_chunk.size=0x21;
    chunk1=malloc(0x10);
    chunk2=malloc(0x10);

    free(chunk1);
    free(chunk2);
    free(chunk1);

    chunk_a=malloc(0x10);
    *(long long *)chunk_a=&bss_chunk;
    malloc(0x10);
    malloc(0x10);
    chunk_b=malloc(0x10);
    printf("%p\n",chunk_b);
    return 0;
}
```

编译好之后gdb调试，下断点在代码的第31行，然后运行：

```c
➜  fastbin_double_free gdb test4
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
Reading symbols from test4...done.
pwndbg> b 31
Breakpoint 1 at 0x40065b: file test4.c, line 31.
pwndbg> r
Starting program: /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/test4 
0x601090

Breakpoint 1, main () at test4.c:31
31	    return 0;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0x9
 RBX  0x0
 RCX  0x7ffffff7
 RDX  0x7ffff7dd3780 (_IO_stdfile_1_lock) ◂— 0x0
 RDI  0x1
 RSI  0x1
 R8   0x0
 R9   0x9
 R10  0x0
 R11  0x246
 R12  0x4004c0 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffde70 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffdd90 —▸ 0x400670 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffdd70 —▸ 0x602010 —▸ 0x601080 (bss_chunk) ◂— 0x0
 RIP  0x40065b (main+165) ◂— mov    eax, 0
───────────────────────────────────[ DISASM ]───────────────────────────────────
 ► 0x40065b       <main+165>                 mov    eax, 0
   0x400660       <main+170>                 leave  
   0x400661       <main+171>                 ret    
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
In file: /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/test4.c
   26     *(long long *)chunk_a=&bss_chunk;
   27     malloc(0x10);
   28     malloc(0x10);
   29     chunk_b=malloc(0x10);
   30     printf("%p\n",chunk_b);
 ► 31     return 0;
   32 }
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffdd70 —▸ 0x602010 —▸ 0x601080 (bss_chunk) ◂— 0x0
01:0008│      0x7fffffffdd78 —▸ 0x602030 —▸ 0x602000 ◂— 0x0
02:0010│      0x7fffffffdd80 —▸ 0x602010 —▸ 0x601080 (bss_chunk) ◂— 0x0
03:0018│      0x7fffffffdd88 —▸ 0x601090 (bss_chunk+16) ◂— 0x0
04:0020│ rbp  0x7fffffffdd90 —▸ 0x400670 (__libc_csu_init) ◂— push   r15
05:0028│      0x7fffffffdd98 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
06:0030│      0x7fffffffdda0 ◂— 0x1
07:0038│      0x7fffffffdda8 —▸ 0x7fffffffde78 —▸ 0x7fffffffe1f3 ◂— '/home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/test4'
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0           40065b main+165
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg>
```

> 程序输出的bss段中的CHUNK bss_chunk地址为：0x601090
>

看一下内存情况：

```c
pwndbg> x/16gx 0x601080
0x601080 <bss_chunk>:	0x0000000000000000	0x0000000000000021
0x601090 <bss_chunk+16>:	0x0000000000000000	0x0000000000000000
0x6010a0:	0x0000000000000000	0x0000000000000000
0x6010b0:	0x0000000000000000	0x0000000000000000
0x6010c0:	0x0000000000000000	0x0000000000000000
0x6010d0:	0x0000000000000000	0x0000000000000000
0x6010e0:	0x0000000000000000	0x0000000000000000
0x6010f0:	0x0000000000000000	0x0000000000000000
pwndbg> x/150gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000601080	0x0000000000000000
            #指向 <bss_chunk>
0x602020:	0x0000000000000000	0x0000000000000021 #chunk2
0x602030:	0x0000000000602000	0x0000000000000000
            #指向chunk1
0x602040:	0x0000000000000000	0x0000000000000411
0x602050:	0x3039303130367830	0x000000000000000a
            #0x601090 指向 <bss_chunk+16>
......(省略内容均为空)
0x602450:	0x0000000000000000	0x0000000000020bb1 #top_chunk
......(省略内容均为空)
0x6024a0:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602450 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg>
```

在IDA中查看一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601947002815-bba6b8a6-ecfd-4bb9-ba53-30d5ceab3335.png)

程序中的指针情况如下：

```c
pwndbg> info local
chunk1 = 0x602010
chunk2 = 0x602030
chunk_a = 0x602010
chunk_b = 0x601090 <bss_chunk+16>
pwndbg> 
```

再次借用一下前面的图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601945211476-e5e0cac9-2d57-48f8-91b0-428b945add91.png)

> fastbin特性：
>
> 当程序需要重新 malloc 内存并且需要从fastbin 中挑选堆块时，**会选择后面新加入的堆块拿来先进行内存分配**
>

为了探究程序的整体运作过程和fastbin_double_free的原理，我们重新进行调试，下断点在free(chunk)之后，运行程序：

```c
pwndbg> bin
fastbins
0x20: 0x602000 ◂— 0x0 #不准确，看看就好
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
Allocated chunk
Addr: 0x602000
Size: 0x00

pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000602000 #chunk1
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602040
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> top_chunk
Top chunk
Addr: 0x602040
Size: 0x00
pwndbg> x/100gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000602020	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000021 #chunk2
0x602030:	0x0000000000602000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000020fc1 #top_chunk
......(省略内容均为空)
0x602310:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

在第26行下断点，让程序执行：chunk_a=malloc(0x10);看看：

```c
pwndbg> bin
fastbins
0x20: 0x602020 ◂— 0x0
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
Allocated chunk
Addr: 0x602000
Size: 0x00

pwndbg>  x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000602020 #chunk2
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602040
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> pwndbg> x/100gx 0x602000
Undefined command: "pwndbg>".  Try "help".
pwndbg> x/100gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000602020	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000021 #chunk2
0x602030:	0x0000000000602000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000020fc1 #top_chunk
......(省略内容均为空)
0x602310:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

可以看到，main_arena从原来指向的chunk1更改为指向的chunk2，chunk1从fastbin中的单向链表摘除，图解如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601951731647-5d61c504-9b03-4891-b7fc-e8d8d6ecf265.png)

此时本地变量指针内容如下：

```c
pwndbg> info local
chunk1 = 0x602010
chunk2 = 0x602030
chunk_a = 0x602010 #指向chunk1的user_data段，这说明此次的malloc使用了fastbin中的chunk1空间
chunk_b = 0x0
pwndbg> 
```

所以，这张图应该改为：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601954086909-29810ca9-f1f7-4d1a-8854-56118fb6c21b.png)

> 注意：chunk1其实已经被malloc使用，但是在fastbin中的chunk2仍然指向它。
>

重复此步骤，在第27行下断点，让程序执行*(long long *)chunk_a=&bss_chunk;

```c
pwndbg> bin
fastbins
0x20: 0x602020 ◂— 0x0
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
Allocated chunk
Addr: 0x602000
Size: 0x00

pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000602020 #chunk2
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602040 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> x/100gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000601080	0x0000000000000000
             #<bss_chunk>
             #*(long long *)chunk_a=&bss_chunk;
0x602020:	0x0000000000000000	0x0000000000000021 #chunk2
0x602030:	0x0000000000602000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000020fc1 #top_chunk
......
pwndbg> x/16gx 0x601080
0x601080 <bss_chunk>:	0x0000000000000000	0x0000000000000021
0x601090 <bss_chunk+16>:	0x0000000000000000	0x0000000000000000
0x6010a0:	0x0000000000000000	0x0000000000000000
0x6010b0:	0x0000000000000000	0x0000000000000000
0x6010c0:	0x0000000000000000	0x0000000000000000
0x6010d0:	0x0000000000000000	0x0000000000000000
0x6010e0:	0x0000000000000000	0x0000000000000000
0x6010f0:	0x0000000000000000	0x0000000000000000
```

来解释一下这行代码：*(long long *)chunk_a=&bss_chunk;

由于chunk_a这个指针指向了chunk1的user_data段（malloc返回的指针指向chunk的user_data段），因此执行了上述代码之后会将data段的起始内容覆盖为&bss_chunk的地址，也就是变成了chunk1的fd指针。

> 如果不理解这个代码，说明你的C语言指针学的不牢固啊。
>

再次修改上面的那张图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601955339175-d877d818-ed7f-44e3-9489-3e2f5bf060a2.png)

在代码的第29行下断点，执行完两个malloc(0x10)语句，来看一下：

```c
pwndbg> bin
fastbins
0x20: 0x601080 (bss_chunk) ◂— 0x0
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
Allocated chunk
Addr: 0x602000
Size: 0x00

pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000601080 #bss_chunk
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602040 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> x/100gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021
0x602010:	0x0000000000601080	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000021
0x602030:	0x0000000000602000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000020fc1
......
0x602310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x601080
0x601080 <bss_chunk>:	0x0000000000000000	0x0000000000000021
0x601090 <bss_chunk+16>:	0x0000000000000000	0x0000000000000000
0x6010a0:	0x0000000000000000	0x0000000000000000
0x6010b0:	0x0000000000000000	0x0000000000000000
0x6010c0:	0x0000000000000000	0x0000000000000000
0x6010d0:	0x0000000000000000	0x0000000000000000
0x6010e0:	0x0000000000000000	0x0000000000000000
0x6010f0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

注意，此时main_arena发生了变化：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601955869456-c1127491-b229-448c-863f-66b31f20fe60.png)

说明这两个malloc使用了chunk2和chunk1的空间。

这时如果程序执行代码chunk_b=malloc(0x10);的话就会控制bss_chunk的空间，**<font style="color:#F5222D;">放大点来说就会控制任意内存的空间。</font>**

值得注意的是，我们在 main 函数的第一步就进行了bss_chunk.size=0x21;的操作，这是因为_int_malloc会对欲分配位置的 size 域进行验证，如果其 size 与当前 fastbin 链表应有 size 不符就会抛出异常。

```c
//_int_malloc 中的校验:
if (__builtin_expect (fastbin_index (chunksize (victim)) != idx, 0))
    {
      errstr = "malloc(): memory corruption (fast)";
    errout:
      malloc_printerr (check_action, errstr, chunk2mem (victim));
      return NULL;
}
```

在代码的30行下断点，执行：

```c
pwndbg> info local
chunk1 = 0x602010
chunk2 = 0x602030
chunk_a = 0x602010
chunk_b = 0x601090 <bss_chunk+16>
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
all: 0x0
smallbins
empty
largebins
empty
pwndbg> heap
Allocated chunk
Addr: 0x602000
Size: 0x00

pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602040 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> x/100gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021 #chunk1
0x602010:	0x0000000000601080	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000021 #chunk2
0x602030:	0x0000000000602000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000020fc1 #top_chunk
......
0x602310:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x601080
0x601080 <bss_chunk>:	0x0000000000000000	0x0000000000000021
0x601090 <bss_chunk+16>:	0x0000000000000000	0x0000000000000000
0x6010a0:	0x0000000000000000	0x0000000000000000
0x6010b0:	0x0000000000000000	0x0000000000000000
0x6010c0:	0x0000000000000000	0x0000000000000000
0x6010d0:	0x0000000000000000	0x0000000000000000
0x6010e0:	0x0000000000000000	0x0000000000000000
0x6010f0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

最后执行完 printf("%p",chunk_b);，这样就会打印出bss_chunk的地址。

原理说完了，下一篇文章开始实战。

