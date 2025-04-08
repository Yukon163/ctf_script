**IDC语言为IDA的一种脚本引擎，它之所以叫做IDC是因为它的语法与C语言很相似，下面介绍一些IDC常用的基本语法。**



1.IDC的变量没有明确的类型，IDC关键字auto用于引入一个局部变量的声明，用extern关键字引入全局变量的声明，不能在声明全局变量时为其提供初始值。

Example1:

```c
auto addr, reg, val;    //没有初始化声明的多个变量
auto count = 0;         //已声明和初始化
```

Example2:

```c
extern outsideGlobal;
static main()
{
	extern insideGlobal;
	outsideGlobal = “Global”;
	insideGlobal = 1;
}
```

2.IDC几乎支持C中的所有运算和逻辑操作符，所有整数操作数均作为有符号的值处理。这会影响到整数比较与右移位运算。如果需要进行逻辑右移位运算，你必须修改结果的最高位，自己移位，如下代码：

Example3:

```c
result = ( x >> 1 ) & 0x7fffffff;   //将最大有效位设置为0
```

> 关于0x7fffffff :
>
> 每个十六进制数为4bit，因此8位16进制是4个字节，刚好是一个int整型，F的二进制码为 1111，7的二进制码为 0111。这样一来，整个整数 0x7FFFFFFF 的二进制表示就是除了首位是 0，其余都是1。也就是说，这是最大的整型数 int（因为第一位是符号位，0 表示他是正数）。
>

3.虽然IDC没有数组数据类型,但你可以使用分片运算符来处理IDC字符串,就好像他们是数组一样,IDC分片的用法：

Example4:

```c
auto str = “String to slice”;
auto s1, s2, s3, s4;
s1 = str[7:9];          //'to'
s2 = str[ :6];     //'String'
s3 = str[10: ];     //'slice'
s4 = str[5];         //'g'
```

4.与C语言一样，IDC所有简单语句均以分号结束。Switch语句是IDC唯一不支持的C风格复合语句。在使用for语句时IDC不支持复合赋值运算符，如果你希望以除1以外的其他值为单位进行计数，就需要注意这一点，如下代码：

Example5:

```c
auto i;
for (i = 0; i < 10; i += 2) {}       //不合法，不支持 +=
for (i = 0; i < 10; i = i + 2) {}    //合法
```

5.输出语句（Message函数类似于C中的printf函数）

Example6:

```c
auto i = 10;
auto j = 20;
Message(“i = %d\n”, i）;
Message(“j = %d\n”, j）;
```

6.IDC文件仅仅在独立程序(.idc文件)支持用户自定义的函数，IDC命令对话框不支持。IDC程序文件的基本结构：

Example7:

```c
#include<idc.idc>   //头文件
static main()
{
	//do something fun here
}
```

7.一些常用函数：





```c
1）void PatchByte(long addr , long val)//设置虚拟地址addr处的一个字节值，PatchByte可更换为PatchWord，PatchDword设置虚拟地址addr处的2字节和4字节值。
2）long Byte（long addr//从虚拟地址addr读取一个字节值，Byte可更换为Word，Dword读取2字节和4字节值。
3）void Message（string format , …）//在输出窗口打印一条格式化消息。
4）void print（…）//在输出窗口中打印每个参数的字符串表示形式。
5）long atol（string val）//将10进制val转化成对应整数值。
6）long xtol（string val）//将16进制val转化成对应整数值。
7）long ord（string ch）//返回单字符字符串ch的ASCII值。
8）string Name（long addr）//返回与给定地址有关的名称，如果该位置没有名称，则返回空字符串。
```

另外，还有一些函数值得我们注意：

| 返回值 | 函数名 | 参数 | 注释 |
| :---: | :---: | :---: | --- |
| long | Byte | long addr | 从虚拟地址addr处读取一个字节 |
| long | Word | long addr | 从虚拟地址addr处读取两个字节 |
| long | Dword | long addr | 从虚拟地址addr处读取四个字节 |
| void | PatchByte | long addr, long val | 设置虚拟地址addr处的一个字节值 |
| void | PatchWord | long addr, long val | 设置虚拟地址addr处的两个字节值 |
| void | PatchWord | long addr, long val | 设置虚拟地址addr处的两个字节值 |
| void | PatchDword | long addr, long val | 设置虚拟地址addr处四个字节值 |
| bool | isLoaded | long addr | 如果addr包含有效数据，则返回1，否则0；如果提供一个无效的地址也会返回0xff，所以isloaded可以判断是否有数据 |
| void | Message | string format,.... | 在输出窗口打印一条格式化字符串 |
| void | print | .... | 在输出窗口打印每个参数的字符串表示形式 |
| void | Warning | string format,.... | 在对话框中显示一条格式化消息 |
| string | AskStr | string default, string prompt | 显示一个输入框，要求用户输入一个字符串。如果操作成功<br/>返回用户字符串，如果取消则返回0 |
| string | AskFile | long doSave, string mask,string prompt | 显示一个文件选择对话框，以简化选择文件任务，如果操作成功，返回选择文件的名称，如果取消，返回0 |
| long | AskYN | long default, string prompt | 用一个答案为是或否提问，1为是，0为否，-1取消 |
| long | ScreenEA |  | 返回当前光标所在位置的虚拟地址 |
| bool | Jump | long addr | 跳转到反汇编窗口指定地址 |
| string | form | string format,.... | 返回一个新字符串，由所提供的值格式化 |
| string | sprintf | string format,.... | 在ida5.6代替form |
| long | atol | string val | 十进制转换为整数 |
| long | xtol | string val | 转换为16进制 |
| string | ltoa | long val, long radix | 以指定进制返回val |
| long | ord | string ch | 返回单个字符串 ASCII |
| long | strlen | string str | 返回字符串长度 |
| long | strstr | string str, string substr | 返回str中substr的索引 |
| string | substr | string str, long start ,long end | 返回start到end-1的字符串 |
| long | fopen | string filename, string mode | 返回文件句柄，和c语言一样 |
| void | fclose | long handle | 关闭文件 |
| long | filelength | long handle | 返回指定文件长度，如果错误-1 |
| long | fgetc | long handle | 从文件中读取一个字节 |
| long | fputc | long val, long handle | 写入一个字节，成功则0，失败-1 |
| long | fprintf | long handle,string format, ... | 一个格式化字符串写入给定文件 |
| long | writestr | long handle, string str | 指定字符串写入文件 |
| string/long | readstr | long handle | 从给定文件中读取一个字符串，读到一个换行符为止，包括换行符，末尾返回-1 |
| long | Dfirst | long from | 返回给定地址应用一个数据值的第一个位置。没有返回-1 |
| long | Dnext | long from,long current | 如果已经有一个位置，可以利用当前位置，搜索下一个位置。错误返回-1 |
| long | XrefType |  | 返回最后一个交叉引用查询函数返回的类型 |
| long | DfirstB | long to | 返回给顶地址作为数据引用的第一个位置，不存在返回-1 |
| long | DnextB | long to, long current | 如果已经有一个位置，可以利用当前位置，搜索下一个位置。错误返回-1 |
| long | FindCode | long addr, long flags | flag指定查找行为，SEARCH_DOWN,扫描高位地址，SEARCH_NEXT跳过当前匹配，搜索下一个，SEARCH_CASE以区分大小写方式扫描二进制文本<br/>从给定地址搜索一条指令 |
| long | FindeData | long addr, long flags | 从给定地址搜索一个数据项 |
| long | FindBinary | long addr, long flags, string binary | 从给定地址搜索一个字节序列 |




