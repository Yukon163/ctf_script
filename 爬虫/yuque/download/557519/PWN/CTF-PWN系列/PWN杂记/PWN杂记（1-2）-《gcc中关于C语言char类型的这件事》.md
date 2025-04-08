> 附件下载：
>
> 链接: [https://pan.baidu.com/s/1UtQYcgZS_vQkIPUV5T5C5w](https://pan.baidu.com/s/1UtQYcgZS_vQkIPUV5T5C5w)  密码: e49d
>
> --来自百度网盘超级会员V3的分享
>

# 研究对象![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611826067279-14dd4f5e-064e-43da-9cd0-f58492bf1f68.png)
研究的gcc版本为：gcc version 5.4.0 20160609 (Ubuntu 5.4.0-6ubuntu1~16.04.12) 

不同版本的gcc编译出来的程序可能不同。

**<font style="color:#F5222D;">本文旨在了解char数组和char *的区别</font>**

# 前言
很早之前就想研究一下C中char类型的变量了，因为char、char[]、char *等实在容易搞混，所以就想从内存的角度来研究一下。

> 注意：char（char []）只能容纳字符，并不能容纳字符串。
>

# 代码编译
> 下面的代码是容易搞混的，我们使用gcc编译一下。
>

```c
#include<stdio.h>
#include<string.h>
int main(){
	char a[10]={'a','a','a','a','a','a','a'};
	char m[]={'a',"b",'c','d'};
	char n[]={'m',"nnnn",'o','d','p',"q"};
	char* b="bbbbbbb";
	char c[10]="ccccccc";
	char* d[10]={'a','b','c','d','e','f','g'};
	char* e[10]={"a","b","c","d","e","f","g"};
	const char f[10]={"fffffff"};
	const char* g="ggggggg";
	char* const h="hhhhhhh";
	const char* const i = "iiiiiii";
	return 0;
}
```

> 编译命令：gcc -g test1.c -o test1
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611713880162-d4dd88bd-52f1-4d29-bf1d-e39549da877e.png)

代码中有不合规的写法，产生了警告信息，这里先不用管它。

# 调试
gdb调试程序断在return 0处

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611714100639-c4ac8c52-a8f0-4445-a498-f0a961036a6e.png)

看一下本地变量：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611714159951-cdee24d1-0b34-425a-9415-860f5286763d.png)

有点乱，看一下内存可能更清楚：

```c
pwndbg> x/30gx 0x7fffffffdcb0
0x7fffffffdc90:	0x000000000040078d	0x00000000004007a1
    			#char* b			#const char* g
0x7fffffffdca0:	0x00000000004007a9	0x00000000004007b1
    			#char* const h		#const char* const i
0x7fffffffdcb0:	0x0000000000000061	0x0000000000000062 #char* d[10]
    			#char* d[1]		    #char* d[2]
0x7fffffffdcc0:	0x0000000000000063	0x0000000000000064
        		#char* d[3]			#char* d[4]
0x7fffffffdcd0:	0x0000000000000065	0x0000000000000066
    			#char* d[5]			#char* d[6]
0x7fffffffdce0:	0x0000000000000067	0x0000000000000000
    			#char* d[7]				
0x7fffffffdcf0:	0x0000000000000000	0x0000000000000000
0x7fffffffdd00:	0x0000000000400795	0x0000000000400784 #char* e[10]
    			#char* e[1]         #char* e[2]
0x7fffffffdd10:	0x0000000000400797	0x0000000000400799
    			#char* e[3]         #char* e[4]
0x7fffffffdd20:	0x000000000040079b	0x000000000040079d
    			#char* e[5]         #char* e[6]
0x7fffffffdd30:	0x000000000040079f	0x0000000000000000
    			#char* e[7]                  
0x7fffffffdd40:	0x0000000000000000	0x0000000000000000
0x7fffffffdd50:	0x0000000064638461	0x00007fffffffddd0
0x7fffffffdd60:	0x00008b70646f866d	0x00000000000000f0
0x7fffffffdd70:	0x0061616161616161	0x0000000000400000
    			#char a[10]
0x7fffffffdd80:	0x0063636363636363	0x0000000000000000
    			#char c[10]
0x7fffffffdd90:	0x0066666666666666	0x0000000000400000
    			#const char f[10]
pwndbg>
```

# 分析 
为了说明的更清楚，我们结合IDA将所有的变量分析一下。

## 栈空间初始化
```c
.text:0000000000400546                 push    rbp
.text:0000000000400547                 mov     rbp, rsp
.text:000000000040054A                 sub     rsp, 120h  //开辟所需要的栈空间
.text:0000000000400551                 mov     rax, fs:28h
.text:000000000040055A                 mov     [rbp+var_8], rax //保存canary
```

> 变量所需的空间是一步就初始化完成的。
>

sub rsp, 120h之前：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611720870228-2fb4d1ff-8e13-4c33-80f7-a167c407da3a.png)

sub rsp, 120h之后：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611720974424-ecc21ea2-7c77-479a-b447-6246515255f4.png)

> 栈的生长方向是由高地址到低地址。
>

```c
pwndbg> x/40gx 0x7fffffffdc90
0x7fffffffdc90:	0x00007ffff7fd9700	0x0000000000000000
#现rsp
0x7fffffffdca0:	0x00007ffff7ffea88	0x00007fffffffdce0
0x7fffffffdcb0:	0x0000000000000980	0x00007fffffffdcd0
0x7fffffffdcc0:	0x000000006562b026	0x00007ffff7b996e7
0x7fffffffdcd0:	0x00000000ffffffff	0x00007ffff7ffe718
0x7fffffffdce0:	0x00007ffff7ffa280	0x00007ffff7ffe700
0x7fffffffdcf0:	0x00007fffffffdd01	0x00000ee90c4b5e16
0x7fffffffdd00:	0x0000000000000000	0x0000000000000000
0x7fffffffdd10:	0x0000000000000000	0x0000000000000000
0x7fffffffdd20:	0x0000000000000000	0x0000000000000000
0x7fffffffdd30:	0x00007fffffffdea8	0x0000000000000000
0x7fffffffdd40:	0x0000000000000001	0x00007fffffffdea8
0x7fffffffdd50:	0x0000000000000001	0x00007fffffffddd0
0x7fffffffdd60:	0x00007ffff7ffe168	0x00000000000000f0
0x7fffffffdd70:	0x0000000000000001	0x000000000040074d
0x7fffffffdd80:	0x00007fffffffddae	0x0000000000000000
0x7fffffffdd90:	0x0000000000400700	0x0000000000400450
0x7fffffffdda0:	0x00007fffffffde90	0x0000000000000000
0x7fffffffddb0:	0x0000000000400700	0x00007ffff7a2d840
#原rsp（现rbp）
0x7fffffffddc0:	0x0000000000000001	0x00007fffffffde98
pwndbg>
```

“sub rsp, 120h”只是构造了main函数所需要的栈帧，并没有将原有的数据清空。

## char a[10]={'a','a','a','a','a','a','a'};
首先来看一下a变量，这里定义了一个char类型的数组，然后将数组的前7个值赋值为字符'a'，看一下程序是怎么对a赋值的： 

```c
.text:000000000040055E                 xor     eax, eax
.text:0000000000400560                 mov     qword ptr [rbp+a], 0
.text:0000000000400568                 mov     word ptr [rbp+a+8], 0
.text:000000000040056E                 mov     [rbp+a], 61h
.text:0000000000400572                 mov     [rbp+a+1], 61h
.text:0000000000400576                 mov     [rbp+a+2], 61h
.text:000000000040057A                 mov     [rbp+a+3], 61h
.text:000000000040057E                 mov     [rbp+a+4], 61h
.text:0000000000400582                 mov     [rbp+a+5], 61h
.text:0000000000400586                 mov     [rbp+a+6], 61h
```

向内存填充数据之前：

```c
pwndbg> x/4gx 0x7fffffffdd70
0x7fffffffdd70:	0x0000000000000001	0x000000000040074d #a的栈空间
0x7fffffffdd80:	0x00007fffffffddae	0x0000000000000000
pwndbg> 
```

可以看到，a变量的栈空间是有数据的，因此在使用前需要根据a变量所需的空间大小清空a空间中原有的数据：

```c
.text:0000000000400560                 mov     qword ptr [rbp+a], 0
.text:0000000000400568                 mov     word ptr [rbp+a+8], 0
```

执行mov qword ptr [rbp+a], 0：

```c
pwndbg> x/4gx 0x7fffffffdd70
0x7fffffffdd70:	0x0000000000000000	0x000000000040074d #a的栈空间
				# $$$$$$$$$$$$$$$$
				#a的栈空间起始地址
0x7fffffffdd80:	0x00007fffffffddae	0x0000000000000000
pwndbg> 
```

> 这里的'$'代表执行mov qword ptr [rbp+a],0后所影响的内存；1qword=4word=8byte=16个'$'
>

执行mov  word ptr [rbp+a+8], 0

```c
pwndbg> x/4gx 0x7fffffffdd70
0x7fffffffdd70:	0x0000000000000000	0x0000000000400000 #a的栈空间
									#             $$$$
0x7fffffffdd80:	0x00007fffffffddae	0x0000000000000000
pwndbg> 
```

> 1word=2byte=8个$
>

现在a变量的空间已经全部清零，现在向这个空间中逐个写入字符'a'（0x61）就可以了：

```c
pwndbg> x/4gx 0x7fffffffdd70
0x7fffffffdd70:	0x0061616161616161	0x0000000000400000
    			# @@@@@@@@@@@@@@@@  #             @@@@
0x7fffffffdd80:	0x00007fffffffddae	0x0000000000000000
pwndbg> 
```

> @代表a变量的总空间
>

**<font style="color:#F5222D;">因此char a[10]={'a','a','a','a','a','a','a'};的意思是在一片连续的栈空间中初始化10字节（byte）的空间，然后将对应数量的字符a逐个写入即可。同时说明程序编译之后变量a的内容可以被修改。</font>****<font style="color:#F5222D;"></font>**

```c
pwndbg> x/4gx &a[0]
0x7fffffffdd70:	0x0061616161616161	0x0000000000400000
0x7fffffffdd80:	0x00007fffffffddae	0x0000000000000000
#如果使用x/gx &a[?]来查看变量的值时：
#0x7fffffffdd70:	0x0061616161616161
    								??
#??处代表数组中某个下标（&a[?]）对应的值
#但是由于char中存放的是字符，推荐使用x/bx &a[1]来查看：
#pwndbg> x/bx &a[1]
#0x7fffffffdd71:	0x61
-------------------------------------------------------------
pwndbg> x/bx *a[0]
Cannot access memory at address 0x61
pwndbg>
#x/bx *a[0]代表的含义是查看数组a[0]中的值，然后以这个值为地址查看其中的内容。
#x/bx &a[0]代表的含义是查看数组a[0]中的值（查看a[0]地址处所存放的值）。
```

## char m[]={'a',"b",'c','d'};（ERROR）
首先说明，char数组中存放字符串是一种错误的写法，初学者很容易犯这个错误，否则在编译程序时会出现警告：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611724940879-998dff3d-5cd4-4b5d-a339-c7dd8e3b1acd.png)

```c
.text:000000000040058A                 mov     [rbp+m], 61h
.text:000000000040058E                 mov     eax, offset unk_400784
.text:0000000000400593                 mov     [rbp+m+1], al
.text:0000000000400596                 mov     [rbp+m+2], 63h
.text:000000000040059A                 mov     [rbp+m+3], 64h
```

地址0x400784存放的是“数据0x62”，如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611724562140-fd7fa781-0da3-4fff-87c4-80d0a7e0e4ae.png)

对比m变量写入内容的前后：

```c
pwndbg> x/4gx &m
0x7fffffffdda0:	0x0000000000000001	0x00007fffffffde20
0x7fffffffddb0:	0x00007ffff7ffe168	0x00000000000000f0
pwndbg> 
----------------------------------------------------------
pwndbg> x/4gx &m
0x7fffffffdda0:	0x0000000064638461	0x00007fffffffde20
0x7fffffffddb0:	0x00007ffff7ffe168	0x00000000000000f0
pwndbg> 
```

> **<font style="color:#F5222D;">char a[10]={data}会将a变量所占有的栈空间初始化为0，但是char m[]={data}并不会。</font>**
>

来观察一下上面的内存，“数据"b"”写入时发生了错误，本应写入0x0000000064636261，但实际上写入的是0x0000000064638461，这是发生了什么原因？来看一下汇编代码：

```c
.text:000000000040058E                 mov     eax, offset unk_400784
.text:0000000000400593                 mov     [rbp+m+1], al
-------------------------------------------------------------------------
.rodata:0000000000400784 unk_400784      db  62h ; b             ; DATA XREF: main+48↑o
```

首先程序将"数据0x62"放入到了eax中，然后将eax的低8位中的数据再放入栈中，这也许就是数据发生错误的原因，调试跟踪一下：

```c
数据放入eax前，RAX寄存器的值为空：
RAX  0x0
单步，数据放入之后：
*RAX  0x400784 ◂— 0x71006e6e6e6e0062 /* 'b' */
现在RAX中存放的是地址0x400784，这个地址存放的数据为字符'b',看一下此时寄存器状况：
pwndbg> x/gx $rax
0x400784:	0x71006e6e6e6e0062
pwndbg> x/gx $al
0xffffffffffffff84:	Cannot access memory at address 0xffffffffffffff84
al显示的是0xffffffffffffff84，应该是从rax到al的数据转换出现了问题才导致的错误。
```

**<font style="color:#F5222D;">综上，char数组中不可以有字符串的出现，否则会导致数据错误。</font>**

## char n[]={'m',"nnnn",'o','d','p',"q"};（ERROR）
继续来看汇编：

```c
.text:000000000040059E                 mov     [rbp+n], 6Dh
.text:00000000004005A2                 mov     eax, offset aNnnn ; "nnnn"
.text:00000000004005A7                 mov     [rbp+n+1], al
.text:00000000004005AA                 mov     [rbp+n+2], 6Fh
.text:00000000004005AE                 mov     [rbp+n+3], 64h
.text:00000000004005B2                 mov     [rbp+n+4], 70h
.text:00000000004005B6                 mov     eax, offset aQ  ; "q"
.text:00000000004005BB                 mov     [rbp+n+5], al
-----------------------------------------------------------------------
.rodata:0000000000400786 aNnnn           db 'nnnn',0             ; DATA XREF: main+5C↑o
.rodata:000000000040078B aQ              db 'q',0                ; DATA XREF: main+70↑o
```

由于这个char数组中仍然存在两个字符串，因此写入之后会导致错误：

```c
pwndbg> x/2gx &n
0x7fffffffddb0:	0x00008b70646f866d	0x00000000000000f0 #??表示数据出错的地方。
    		   #0x    ??70646f??6d 
pwndbg>
```

> 和之前一样，使用char n[]不会初始化n变量栈空间为0，并且数据都是直接写入栈的，同时也暗示了char n[]={data}中的data在定义后可以被修改。
>
> 无论定义时字符串的长度为多少，都会被al寄存器截断为1byte。
>

## char* b="bbbbbbb";
汇编如下：

```c
.text:00000000004005BE        mov     [rbp+b], offset aBbbbbbb ; "bbbbbbb"
---------------------------------------------------------------------------
.rodata:000000000040078D aBbbbbbb        db 'bbbbbbb',0          ; DATA XREF: main+78↑o
```

写入内存之后：

```c
pwndbg> x/4gx &b
0x7fffffffdce0:	0x000000000040078d	0x0000000000000000
0x7fffffffdcf0:	0x00007ffff7ffea88	0x00007fffffffdd30
pwndbg> x/2gx 0x000000000040078d
0x40078d:	0x0062626262626262	0x0065006400630061
pwndbg> x/4gx b
0x40078d:	0x0062626262626262	0x0065006400630061
0x40079d:	0x6767676700670066	0x6868686800676767
pwndbg> x/4gx *b
0x62:	Cannot access memory at address 0x62
pwndbg> 
```

在之前的调试中，x/4gx &b和x/4gx b得到的结果是相同的（之后的篇幅未说明则相同），但是这里却发生了变化，推测这是由于定义变量时使用了char *导致的；仔细观察可以得出一个简单结论：

b变量被定义为char* b（char *b），因此b是一个指针，它指向存放于.rodata段的'bbbbbbb'，而gdb中的x/4gx &b指的是查看b指针存放的地址，x/4gx b是查看b指针指向的内容。进一步，“ mov [rbp+b], offset aBbbbbbb ;”的意思是将'bbbbbbb'所存放的地址写入到[rbp+b]中（也可以理解为指针）。

> .rodata段即read only data，存放于该段的数据是只读的。
>
> 注：存放于栈的指针b可以被修改，但是指向的数据’bbbbbbb'无法更改，和之后的const char* g效果相同
>

## char c[10]="ccccccc";
```c
.text:00000000004005C9                 mov     rax, 63636363636363h
.text:00000000004005D3                 mov     qword ptr [rbp+c], rax
.text:00000000004005D7                 mov     word ptr [rbp+c+8], 0
```

看一下写入之前之后的内存：

```c
写入之前：
pwndbg> x/2gx &c
0x7fffffffddd0:	0x00007fffffffddfe	0x0000000000000000
pwndbg>
写入之后：
pwndbg> x/2gx &c
0x7fffffffddd0:	0x0063636363636363	0x0000000000000000
               	#mov qword ptr [rbp+c], rax ->0x??63636363636363
    			#mov word ptr [rbp+c+8], 0 ->0x00??????????????
    			#上面的??代表执行汇编指令后0x7fffffffddd0未受影响到的内存
pwndbg>
```

**<font style="color:#F5222D;">和之前char *b不同的是，由于变量c的数据是由寄存器直接mov到栈的，因此数据可读可修改。</font>**

## char* d[10]={'a','b','c','d','e','f','g'};（ERROR）
这个也是编译时发生警告的地方，说明这种定义方法不恰当。

# ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611810278033-212d891c-1924-49ad-b377-f7acbb957b43.png)
先来看第一部分的汇编：

```c
.text:00000000004005DD                 lea     rdx, [rbp+d]
.text:00000000004005E4                 mov     eax, 0
.text:00000000004005E9                 mov     ecx, 0Ah
.text:00000000004005EE                 mov     rdi, rdx
.text:00000000004005F1                 rep stosq
#rep指令的目的是重复其上面的指令.ECX的值是重复的次数.
#STOS指令的作用是将rax中的值拷贝到ES:RDI指向的地址.
#q代表qword
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611810661650-3c070875-8175-4ae3-b35e-ee79cfeb82c7.png)

```c
pwndbg> x/20gx &d 
0x7fffffffdd00:	0x0000000000000980	0x00007fffffffdd20
0x7fffffffdd10:	0x000000006562b026	0x00007ffff7b996e7
0x7fffffffdd20:	0x00000000ffffffff	0x00007ffff7ffe718
0x7fffffffdd30:	0x00007ffff7ffa280	0x00007ffff7ffe700
0x7fffffffdd40:	0x00007fffffffdd01	0x00003ee6c929dc69
0x7fffffffdd50:	0x0000000000000000	0x0000000000000000
0x7fffffffdd60:	0x0000000000000000	0x0000000000000000
0x7fffffffdd70:	0x0000000000000000	0x0000000000000000
0x7fffffffdd80:	0x00007fffffffdef8	0x0000000000000000
0x7fffffffdd90:	0x0000000000000001	0x00007fffffffdef8
pwndbg> 
-------------------------------------------------------------#执行之后：
pwndbg> x/20gx &d 
0x7fffffffdd00:	0x0000000000000000	0x0000000000000000 #changed
0x7fffffffdd10:	0x0000000000000000	0x0000000000000000 #changed
0x7fffffffdd20:	0x0000000000000000	0x0000000000000000 #changed
0x7fffffffdd30:	0x0000000000000000	0x0000000000000000 #changed
0x7fffffffdd40:	0x0000000000000000	0x0000000000000000 #changed
0x7fffffffdd50:	0x0000000000000000	0x0000000000000000 #nochanged
0x7fffffffdd60:	0x0000000000000000	0x0000000000000000 #nochanged
0x7fffffffdd70:	0x0000000000000000	0x0000000000000000 #nochanged
0x7fffffffdd80:	0x00007fffffffdef8	0x0000000000000000 #nochanged
0x7fffffffdd90:	0x0000000000000001	0x00007fffffffdef8 #nochanged
pwndbg> 
```

易得：这段代码的作用是将之后所需要的栈空间进行清空，防止受原来的数据干扰。之后就是将数据写入内存中：

```c
.text:00000000004005F4                 mov     [rbp+d], 61h
.text:00000000004005FF                 mov     [rbp+d+8], 62h
.text:000000000040060A                 mov     [rbp+d+10h], 63h
.text:0000000000400615                 mov     [rbp+d+18h], 64h
.text:0000000000400620                 mov     [rbp+d+20h], 65h
.text:000000000040062B                 mov     [rbp+d+28h], 66h
.text:0000000000400636                 mov     [rbp+d+30h], 67h
```

```c
pwndbg> x/20gx &d
0x7fffffffdd00:	0x0000000000000061	0x0000000000000062 #changed
0x7fffffffdd10:	0x0000000000000063	0x0000000000000064 #changed
0x7fffffffdd20:	0x0000000000000065	0x0000000000000066 #changed
0x7fffffffdd30:	0x0000000000000067	0x0000000000000000 #changed
0x7fffffffdd40:	0x0000000000000000	0x0000000000000000 
......(未受影响的内存)
0x7fffffffdd90:	0x0000000000000001	0x00007fffffffdef8
pwndbg> 
```

写入数据的方式和之前的都不相同，为了研究这种情况，我们继续向下走。

## char* e[10]={"a","b","c","d","e","f","g"};
和之前的一样，所需的栈空间清零：

```c
.text:0000000000400641                 lea     rdx, [rbp+e]
.text:0000000000400648                 mov     eax, 0
.text:000000000040064D                 mov     ecx, 0Ah
.text:0000000000400652                 mov     rdi, rdx
.text:0000000000400655                 rep stosq
```

开始写入数据：

```c
.text:0000000000400658                 mov     [rbp+e], offset aA ; "a"
.text:0000000000400663                 mov     [rbp+e+8], offset unk_400784
.text:000000000040066E                 mov     [rbp+e+10h], offset aC ; "c"
.text:0000000000400679                 mov     [rbp+e+18h], offset aD ; "d"
.text:0000000000400684                 mov     [rbp+e+20h], offset aE ; "e"
.text:000000000040068F                 mov     [rbp+e+28h], offset asc_40079D ; "f"
.text:000000000040069A                 mov     [rbp+e+30h], offset aG ; "g"
```

```c
pwndbg> x/16gx &e
0x7fffffffdd50:	0x0000000000400795	0x0000000000400784 #changed
0x7fffffffdd60:	0x0000000000400797	0x0000000000400799 #changed
0x7fffffffdd70:	0x000000000040079b	0x000000000040079d #changed
0x7fffffffdd80:	0x000000000040079f	0x0000000000000000 #changed
0x7fffffffdd90:	0x0000000000000000	0x0000000000000000 #changed
......
pwndbg>
```

总结：**<font style="color:#F5222D;">char* e[10]={}要求写入的是字符串（指针）而不是字符，定义后数据不可更改：</font>**

```c
.rodata:0000000000400795 aA              db 'a',0                ; DATA XREF: main+112↑o
.rodata:0000000000400797 aC              db 'c',0                ; DATA XREF: main+128↑o
.rodata:0000000000400799 aD              db 'd',0                ; DATA XREF: main+133↑o
.rodata:000000000040079B aE              db 'e',0                ; DATA XREF: main+13E↑o
.rodata:000000000040079D asc_40079D      db 'f',0                ; DATA XREF: main+149↑o
.rodata:000000000040079F aG              db 'g',0                ; DATA XREF: main+154↑o
```

## const char f[10]={"fffffff"};
> C语言中const关键字是constant的缩写，其作用是将变量定义为不可修改的常量变量（得看情况）。
>

```c
.text:00000000004006A2                 mov     rax, 66666666666666h
.text:00000000004006AC                 mov     qword ptr [rbp+f], rax
.text:00000000004006B0                 mov     word ptr [rbp+f+8], 0
```

写入之后内存如下：

```c
pwndbg> x/8gx &f
0x7fffffffdde0:	0x0000000000400700	0x0000000000400450
0x7fffffffddf0:	0x00007fffffffdee0	0x9fa1dc511b787e00
0x7fffffffde00:	0x0000000000400700	0x00007ffff7a2d840
0x7fffffffde10:	0x0000000000000001	0x00007fffffffdee8
pwndbg>
-------------------------------------------------------------#执行之后：
pwndbg> x/8gx &f
0x7fffffffdde0:	0x0066666666666666	0x0000000000400000
    		   #0x????????????????  0x            ????
0x7fffffffddf0:	0x00007fffffffdee0	0x9fa1dc511b787e00
0x7fffffffde00:	0x0000000000400700	0x00007ffff7a2d840
0x7fffffffde10:	0x0000000000000001	0x00007fffffffdee8
pwndbg> 
```

> ??代表受影响的内存
>

在gcc的环境下，虽然我们利用const想让变量变为不可修改，但是在这个例子中，加入const后变量仍然可读，因为栈内存是可读可写的。

## const char*
+ const char* g="ggggggg";
+ char* const h="hhhhhhh";
+ const char* const i = "iiiiiii";

最后这三个是一样的类型，统一来说一下：

```c
.text:00000000004006B6                 mov     [rbp+g], offset aGgggggg ; "ggggggg"
.text:00000000004006C1                 mov     [rbp+h], offset aHhhhhhh ; "hhhhhhh"
.text:00000000004006CC                 mov     [rbp+i], offset aIiiiiii ; "iiiiiii"
----------------------------------------------------------------------------------
.rodata:00000000004007A1 aGgggggg        db 'ggggggg',0          ; DATA XREF: main+170↑o
.rodata:00000000004007A9 aHhhhhhh        db 'hhhhhhh',0          ; DATA XREF: main+17B↑o
.rodata:00000000004007B1 aIiiiiii        db 'iiiiiii',0          ; DATA XREF: main+186↑o
```

执行代码前后：

```c
pwndbg> x/8gx &g
0x7fffffffdce8:	0x0000000000000000	0x00007ffff7ffea88
0x7fffffffdcf8:	0x00007fffffffdd30	0x0000000000000061
0x7fffffffdd08:	0x0000000000000062	0x0000000000000063
0x7fffffffdd18:	0x0000000000000064	0x0000000000000065
------------------------------------------------------------
pwndbg> x/8gx &g
0x7fffffffdce8:	0x00000000004007a1	0x00000000004007a9
    			#g					#h
0x7fffffffdcf8:	0x00000000004007b1	0x0000000000000061
    			#i
0x7fffffffdd08:	0x0000000000000062	0x0000000000000063
0x7fffffffdd18:	0x0000000000000064	0x0000000000000065
pwndbg> x/8gx g
0x4007a1:	0x0067676767676767	0x0068686868686868
0x4007b1:	0x0069696969696969	0x303b031b01000000
0x4007c1:	0x5400000005000000	0x940000007cfffffc
0x4007d1:	0x8a0000004cfffffc	0x44000000a4fffffd
pwndbg> x/8gx *g
0x67:	Cannot access memory at address 0x67
pwndbg>
#上面的x/8gx g、x/8gx &g、x/8gx *g都是一样的效果。
```

写入的数据都是指针，而指针指向的数据是.rodata段（read only data）,因此指针可以更改（栈空间），而字符串不可更改。

# 一些补充
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611825888973-89309570-b6ab-4127-b247-822db3608f6e.png)

> [https://www.geeksforgeeks.org/whats-difference-between-char-s-and-char-s-in-c/](https://www.geeksforgeeks.org/whats-difference-between-char-s-and-char-s-in-c/)
>

```c
#include<stdio.h>
#include<string.h>

int main(){
	char str1[20] = {"hello world6666666"};
	const char str1[20] = {"hello world6666666"};
	//char str2[10] = {"hello","world"}; Error 没有这种写法
	//const char str4[10] = {"hello","world"}; Error 没有这种写法
	return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611825929033-ecf637cc-242b-4403-9d26-cc3ca027277e.png)

原本以为之前的const char f[10]={"fffffff"};中的const无效是由于字符串长度不够长，看来不是这样。****

