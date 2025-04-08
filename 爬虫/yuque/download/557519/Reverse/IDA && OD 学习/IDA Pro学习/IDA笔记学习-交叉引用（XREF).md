# XREF的简介
交叉引用cross reference是指某个地址的数据或代码引用了哪个地址以及被哪些地址的代码所引用。引用了哪个地址，在反汇编就能看出来，一行汇编代码自然只会引用一个地址。但被引用是一对多的关系，正如一个函数可以被很多函数在内部调用。查看“被引用”是静态分析中得到堆栈的方法，当然，因为一对多的关系，还需要猜。这主要是看分析的目的是什么，与运行时动态分析相比各有好处，静态分析能得到完整的调用关系图。**在IDA里，cross reference也会缩写成XREF。**

XREF主要是两种，数据引用（DATA XREF）和代码引用（CODE XREF），只要看见有**分号**注释的 XREF 的地方，把鼠标悬停上去，都能看到部分交叉引用的代码。如果被引用的地方有很多，还可以通过快捷键**Ctrl+X**或菜单，得到更完整的交叉引用信息。例如在图中的Data XREF右键单击，弹出：

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1588663315887-f45a882b-b6e9-4c5f-b630-bced9bfbce08.jpeg)

选择Jump to cross reference，弹出对话框：

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1588663314689-11647001-ebfe-4559-b957-00ae14e4adfc.jpeg)

可以看到它被9个位置的代码引用。选中其中一条点击ok，即会跳转到那个地址。

# XREF的描述含义
为了更方便说明XREF的描述含义，我们举个例子来说明：

> .text:00404C100 sub 401000 proc near ; CODEXREF: main+2A<font style="color:rgba(0, 0, 0, 0.75);">↓P</font>
>

我们可以得出一些结论：

+ 这是个代码交叉引用（.text）
+ sub401000是被引用者，**main+2A是引用者**（引用sub401000的位置)
+ 下箭头表示引用者的地址比sub401000高，你需要向下滚动才能到达引用者地址（main+2A)，上行反之。
+ 每个交叉引用注释都包含一个单字符后缀（箭头后面），用以说明**交叉引用的类型**，这里是↓P

# CODE XREF
代码交叉引用用于表示一条指令将控制权转交给另一条指令。在IDA中，指令转交控制权的方式叫做**流（flow）**，**IDA中有3种基本流：普通流，调用流，跳转流**，接下来我们使用一个示例来说明：

示例代码：

```c
int read_it; 
int write_it; 
int ref_it; 
void callflow() {} 

int main()
{
    int *p = &ref_it;
    *p = read_it;
    write_it = *p;
    callflow();
    if (read_it == 3)
    {
        write_it = 2;
    }
    else
    {
        write_it = 1;
    }
    callflow();
}
```

示例汇编：

```plain
.text:00401010 ; int __cdecl main(int argc, const char **argv, const char **envp)
.text:00401010 _main           proc near               ; CODE XREF: __tmainCRTStartup+10A↓p
.text:00401010
.text:00401010 p               = dword ptr -4
.text:00401010 argc            = dword ptr  8
.text:00401010 argv            = dword ptr  0Ch
.text:00401010 envp            = dword ptr  10h
.text:00401010
.text:00401010                 push    ebp
.text:00401011                 mov     ebp, esp
.text:00401013                 push    ecx
.text:00401014                 mov     [ebp+p], offset int ref_it
.text:0040101B                 mov     eax, [ebp+p]
.text:0040101E                 mov     ecx, int read_it
.text:00401024                 mov     [eax], ecx
.text:00401026                 mov     edx, [ebp+p]
.text:00401029                 mov     eax, [edx]
.text:0040102B                 mov     int write_it, eax
.text:00401030                 ③call    callflow(void)
.text:00401035                 cmp     int read_it, 3
.text:0040103C                 jnz     short loc_40104A
.text:0040103E                 mov     int write_it, 2
.text:00401048                 jmp     short loc_401054
.text:0040104A ; ---------------------------------------------------------------------------
.text:0040104A
.text:0040104A loc_40104A:                             ; CODE XREF: _main+2C↑j
.text:0040104A                 mov     int write_it, 1
.text:00401054
.text:00401054 loc_401054:                             ; CODE XREF: _main+38↑j
.text:00401054                 ③call    callflow(void)
.text:00401059                 xor     eax, eax
.text:0040105B                 mov     esp, ebp
.text:0040105D                 pop     ebp
.text:0040105E                 retn
.text:0040105E _main           endp
.text:0040105E
```

## 普通流
普通流表示由一条指令到另一条指令的顺序流。这是所有非分支指令（如ADD）的默认执行流。

## 调用流
如果IDA认为某个函数并不返回（在分析阶段确定,注意不是运行阶段），那么，在调用该函数时，它就不会为该函数分配普通流

```plain
.text:00401030                 ③call    callflow(void)
.text:00401054                 ③call    callflow(void)
```

指令用于调用函数，如③处的 call指令，它分配到一个调用流（call flow），表示控制权被转交给目标函数

callflow函数的反汇编：

```plain
.text:00401000 void __cdecl callflow(void) proc near   ; ①CODE XREF: _main+20↓p
.text:00401000                                         ; ①_main:loc_401054↓p
.text:00401000                 push    ebp
.text:00401001                 mov     ebp, esp
.text:00401003                 pop     ebp
.text:00401004                 retn
.text:00401004 void __cdecl callflow(void) endp
```

callflow所在的位置显示了两个交叉引用(①处)，表示这个函数被调用了两次。

> 由函数调用导致的交叉引用使用后缀↓p（看做是Procedure）。
>

## 跳转流
每个无条件分支指令和条件分支指令将分配到一个跳转流（jump flow）

```plain
.text:00401048                 jmp     short loc_401054
.text:0040104A ; ---------------------------------------------------------------------------
.text:0040104A
```

无条件分支并没有相关的普通流，因为它总会进入分支。上处的虚线表示相邻的两条指令之间并不存在普通流（也就是00401048后没有跟着顺序执行的指令）

> 跳转交叉引用使用后缀↑j（看做是Jump）。
>

# DATA XREF
数据交叉引用用于跟踪二进制文件访问数据的方式。数据交叉引用与IDA数据库中任何牵涉到虚拟地址的字节有关（换言之，数据交叉引用与栈变量毫无关系）

最常用的3种数据交叉引用：address何时被读取(读取交叉引用)、address何时被写入(写入交叉引用)、address何时被引用(偏移量交叉引用)

```plain
.data:00403378 int ref_it      db    ? ;               ; DATA XREF: _main+4↑o
.data:00403379                 db    ? ;
.data:0040337A                 db    ? ;
.data:0040337B                 db    ? ;
.data:0040337C int write_it    dd ?                    ; DATA XREF: _main+1B↑w
.data:0040337C                                         ; _main+2E↑w ...
.data:00403380 int read_it     dd ?                    ; DATA XREF: _main+E↑r
.data:00403380                                         ; _main+25↑r
```

## 读取交叉引用
读取交叉引用（read cross-reference）表示访问的是某个内存位置的内容,可以看到read_it在_main+E处、_main+25被读取，如下所示：

```plain
.text:0040101E                 mov     ecx, int read_it
.text:00401035                 cmp     int read_it, 3
```

> 读取交叉引用使用后缀↑r（看做是Read）。
>

## 写入交叉引用
写入交叉引用指出了修改变量内容的程序位置，可以看到write_it在_main+1B、_main+2E处被写入，如下

```plain
.text:0040102B                 mov     int write_it, eax
.text:0040103E                 mov     int write_it, 2
```

> 写入交叉引用使用后缀↑w（看做是Write）。
>

## 偏移量交叉引用
偏移量交叉引用表示引用的是某个位置的地址（而非内容），可以看到ref_it在_main+4处被引用

```plain
.text:00401014                 mov     [ebp+p], offset int ref_it
```

> 偏移量交叉引用使用后缀↑o（看做是Offset）。
>

与仅源自于指令位置的读取和写入交叉引用不同，偏移量交叉引用可能源于指令位置或数据位置，例如虚表

回溯偏移量交叉引用是一种有用的技术，可迅速在程序的数据部分定位C++虚表。



