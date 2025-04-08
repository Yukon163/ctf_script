参考资料：[https://www.imooc.com/article/details/id/29111](https://www.imooc.com/article/details/id/29111)

    [https://www.cnblogs.com/yinguohai/p/11152366.html](https://www.cnblogs.com/yinguohai/p/11152366.html)

    [https://www.cnblogs.com/yinguohai/p/11158492.html](https://www.cnblogs.com/yinguohai/p/11158492.html)

    [https://docs.python.org/3.7/library/dis.html](https://docs.python.org/3.7/library/dis.html)（官方文档）

# 例题：
[2020HGame-Week2-babypy（Python字节码）](https://www.yuque.com/go/doc/6284850)

# 零、速查：
转化后的字节码格式如下：

> 源码行号  |  指令**偏移量**  | 指令符号 | 指令参数  |  实际参数值
>

**变量 — _const**

<font style="color:#FB1803;">LOAD_CONST</font><font style="color:#333333;"> ：加载</font><font style="color:#FC0903;">const</font><font style="color:#333333;"> 变量，比如数值，字符串等等， 一般用于传递给函数作为参数</font>

**局部变量 — _FAST**

<font style="color:#D83910;">LOAD_FAST</font> ：一般用于加载局部变量的值，也就是读取值，用于计算或者函数调用传传等

<font style="color:#B92916;">STORE_FAST</font> ：一般用于保存值到局部变量

**全局变量 — _GLOBAL**

<font style="color:#B32916;">LOAD_GLOBAL</font> ： 用来加载全局变量， 包括制定函数名，类名，模块名等全局符号

<font style="color:#AD2317;">STORE_GLOBAL</font> ：用来给全局变量赋值

**常用数据类型**

**1.list**

<font style="color:#AB2B16;">BUILD_LIST</font> :  用于创建一个 list 结构

**2.dict**

<font style="color:#C52315;">BUILD_MAP</font> : 用于创建一个空的dict 

<font style="color:#C83014;">STORE_MAP</font> : 用于初始化 dict 中的内容，赋值给变量

**3.slice**

<font style="color:#CC5115;">BUILD_SLICE</font> :        用于创建切片， 对于 list ， tuple ， 字符串都可以使用slice 的方式进行访问

<font style="color:#D75713;">BINARY_SUBSCR</font> : 读取slice 的值

<font style="color:#D57D11;">STORE_SUBSCR</font> :   slice 的值赋值给变量。

**4.循环**

<font style="color:#CB4914;">SETUP_LOOP</font> ：用于开始一个循环。 

<font style="color:#D14D11;">JUMP_ABSOLUTE</font>: 结束循环

**5.if**

<font style="color:#D74C11;">POP_JUMP_IF_FALSE</font> : 条件结果为 FALSE  则跳出 目标的偏移指令

<font style="color:#D74C11;">JUMP_FORWARD</font> :       直接跳转到目标便宜指令

<font style="color:#D85E11;">COMPARE_OP</font>:             比较指令

# 一、前言
如果你跟我一样，对Python的字节码感兴趣~~（要解CTF的Reverse）~~，想了解Python的代码在内存中到底是怎么去运行的，那么你可以继续往下看。

## Python如何工作
Python经常被称为是一种解释型语言—— 一种源代码在程序运行时被即时翻译成原生CPU指令的语言 - 但这只说对了一部分。与其他许多解释型语言一样，Python实际上将源代码编译为一组虚拟机指令，Python的解释器就是该虚拟机的一个具体实现。这种跑在虚拟机内部的中间格式被称为“字节码”。

因此，Python留下的.pyc文件不仅仅是源代码的一个“更快”或“优化”版本; 实际上，它们是在程序运行时由Python的虚拟机来执行的字节码指令。

我们来看一个例子。这是一个用Python编写的经典的“Hello, World!” ：

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1587351490997-9773063f-de2c-43e1-a260-a1950fa36e19.jpeg)

下面是转换后的字节码（转换成可读形式）：

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1587351491059-e6ea1a0d-5727-4ca6-b9f2-7077ea7f7a5d.jpeg)

如果您键入该hello()函数并使用CPython解释器运行它，则上面就是Python所执行的内容。不过，这些似乎看起来有点奇怪，所以让我们深入了解一下Python内部发生了什么。

## Python虚拟机内部
CPython使用的是基于栈的虚拟机。也就是说，它完全围绕着栈数据结构来运行（您可以将一项内容“压入”栈，放到栈结构的“顶部”，或者从栈“顶部”“弹出”一项内容）。

CPython使用三种类型的堆栈：

    1. 调用栈。这是Python程序运行的主要结构。它具有一项内容->“栈帧” ，栈的底部就是程序的入口，对于每个当前激活的函数调用，该调用都会压入一个新栈帧到调用栈中，并且每次函数调用结束返回时，对应的栈帧都会被弹出。
    2. 在每一栈帧中，都有一个执行栈（也称为数据栈）。这个栈是执行Python函数的地方，执行Python代码主要包括把相关数据压入栈，执行逻辑操作，结束后从栈中弹出。
    3. 同样在每一栈帧中，都有一个块堆栈。Python使用它来跟踪某些类型的控制结构：循环块，try/except块和with块将所有相关内容都压入块堆栈，当退出一个结构时，块堆栈则弹出相应内容。该操作有助于Python在任何特定时刻知道哪些块处于活动状态，例如，像continue或break语句就需要知道操作哪个具体的逻辑块，否则可能影响逻辑块的正确性。

---

尽管有一些指令用于执行其他操作（如跳转到特定指令或操作块堆栈），但Python的大部分字节码指令都是用来操作当前调用栈帧中的执行栈

为了感受这一点，假设我们有一些调用函数的代码，如：

```python
my_function(my_variable, 2)
```

Python会将其转换为四个字节码指令序列：

    1. 一条 LOAD_NAME 指令，查找函数对象my_function并将其压入到执行栈顶。
    2. 另一条 LOAD_NAME 指令，查找变量my_variable并将其压入到执行栈顶
    3. 一条 LOAD_CONST 指令，将常量数值2压入到执行栈顶
    4. 一条 CALL_FUNCTION 指令

**该“****CALL_FUNCTION****”指令的参数为2，表示Python需要从栈顶部弹出两个位置参数**；那么被调用的函数将位于最前面，并且它也可以被弹出（对于涉及关键字参数的函数，会使用不同的指令 -- **CALL_FUNCTION_KW** - - 但操作原理类似，并且第三条指令会使用 **CALL_FUNCTION_EX** 来处理*或**相关的参数的拆包操作）。一旦Python准备就绪，将在调用栈上分配一个新栈帧，为函数调用准备局部变量，并在该栈帧中执行my_function内的字节码。一旦完成，该栈帧将从调用栈中弹出，并在原来的栈帧中将my_function 返回值压入到执行栈顶部。

## 访问和理解Python字节码
如果想了解Python字节码，Python标准库中的dis模块就非常有用了; dis模块为Python字节码提供了一个“反汇编程序”，从而可以轻松获取人为可读的版本并查找各种字节码指令。dis模块的文档涵盖了相关内容，并提供了字节码指令以及它们的作用和参数的完整清单。

例如，要获取之前hello()函数的字节码列表，将它键入Python解释器中，然后运行：

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1587351748552-2fa18a9c-6984-4465-a05e-64b6d7f12901.jpeg)

函数dis.dis()会对函数，方法，类，模块，编译过的Python代码对象或包含有源代码的字符串文字进行反汇编，并打印出可读的版本。dis模块中另一个方便的功能是distb()。您可以将它传递给Python traceback对象，或者在引发异常之后调用它，它会在异常时反编译调用栈中的最顶层函数，打印其字节码，并在指令中插入一个指向引发异常指令的指针。

此外，它对于查看Python为每个函数所构建的编译过的代码对象也很有用，因为执行函数有时会用到这些代码对象的属性。以下是查看该hello()功能的示例：

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1587351748412-0927221e-439b-45d4-8618-07c0375ea729.jpeg)

代码对象可以通过函数的__code__属性来进行访问，并包含一些其他的重要的属性：

    - co_consts 是一个包含有函数体中出现的任何字面常量的元组，
    - co_varnames 是一个包含函数体中使用的任何局部变量名称的元组
    - co_names 是一个包含函数体中引用的任何非本地变量名称的元组

许多字节码指令 - 尤其是那些涉及到需要压入堆栈加载内容或将内容存储到变量和属性中的指令 - 将会使用这些元组中的索引作为它们的参数。

所以现在我们可以了解该hello()函数的字节码列表：

    1. LOAD_GLOBAL 0：告诉Python在co_names（print函数）的索引0处通过引用的名称寻找全局对象并将其压入到执行栈
    2. LOAD_CONST 1：将co_consts索引1处的字面常量取出并将其压入栈（co_consts中索引0处的值是None，因为Python函数中如果没有显式的return表达式，将会使用隐式调用，返回None值）
    3. CALL_FUNCTION 1：告诉Python调用一个函数; 它需要从堆栈中弹出一个位置参数，然后新的堆栈顶部将是要调用的函数。

“原始”字节码 - 不具有可读性字节码 - 可以通过代码对象的co_code的属性来访问。如果您想尝试手动反汇编函数，则可以使用列表dis.opname从十进制字节值中查找相应字节码指令的名称。

## 字节码的用处
现在，你已经了解的足够多了，你可能会想 “OK，我认为它很酷，但是知道这些有什么实际价值呢？”由于对    它很好奇，我们去了解它，但是除了好奇之外，Python 字节码在几个方面还是非常有用的。

首先，理解 Python 的运行模型可以帮你更好地理解你的代码。人们都开玩笑说，C 是一种 “可移植汇编器”，你可以很好地猜测出一段 C 代码转换成什么样的机器指令。理解 Python 字节码之后，你在使用 Python 时也具备同样的能力 —— 如果你能预料到你的 Python 源代码将被转换成什么样的字节码，那么你可以知道如何更好地写和优化 Python 源代码。

第二，理解字节码可以帮你更好地回答有关 Python 的问题。为什么某些结构比其它结构运行的更快？（比如，为什么 {} 比 dict() 快）。知道如何去访问和阅读 Python 字节码将让你很容易回答这样的问题（尝试对比一下： dis.dis("{}") 与 dis.dis("dict()") 就会明白）。

最后，理解字节码和 Python 如何运行它，为 Python 程序员不经常使用的一种特定的编程方式提供了有用的视角：面向栈的编程。如果你以前从来没有使用过像 FORTH 或 Fator 这样的面向栈的编程语言，它们可能有些古老，但是，如果你不熟悉这种方法，学习有关 Python 字节码的知识，以及理解面向栈的编程模型是如何工作的，将有助你开拓你的编程视野。

## Python代码的执行过程
1. Python源码编译成字节码【类似于汇编指令的中间语言】
2. Python虚拟机来执行编译后的字节码

**说明:**

**<font style="color:#F5222D;">一条</font>**Python语句会对**<font style="color:#F5222D;">应若个</font>**字节码指令，每个字节指令又对应着**<font style="color:#F5222D;">一个</font>**函数偏移量，可以理解为指令的ID。

虚拟机一条一条执行字节码指令，从而完成程序的执行，而dis模块可以对CPython代码进行反汇编，生成字节码指令。

## dis.dis() 转化后的字节码格式
> 源码行号  |  指令**偏移量**  | 指令符号 | 指令参数  |  实际参数值
>

说明： 不同版本的CPython 指令长度可能不同，但是 3.7的每条指令是2个字节，所以我们去看dis 生成的字节码指令集的时候，指令偏移量总是从0开始，每增加一条在原来的偏移量上增加2。故，指令偏移量的值，一般都是： 0 ， 2 ， 4， 6 ， 8 ， ... , 2n ( n>=0 )

> CPython的概念：
>
> CPython是用C语言实现的Python解释器，也是官方的并且是最广泛使用的Python解释器。CPython是使用字节码的解释器，任何程序源代码在执行之前先要编译成字节码。它还有和几种其它语言（包括C语言）交互的外部函数接口。
>

# 二、变量指令解析
## 变量 — _const
<font style="color:#FB1803;">LOAD_CONST</font> ：加载<font style="color:#FC0903;">const</font> 变量，比如数值，字符串等等， 一般用于传递给函数作为参数

 

案例一：

```python
test(2,'hello')
```

对应的字节码指令：

>  源码行号  |  指令**偏移量**  | 指令符号 | 指令参数  |  实际参数值
>

```python
1             0 LOAD_NAME                0 (test)    
              2 LOAD_CONST               0 (2)
              4 LOAD_CONST               1 ('hello')
              6 CALL_FUNCTION            2            
              8 POP_TOP
              10 LOAD_CONST              2 (None)
              12 RETURN_VALUE
```

## 局部变量 — _FAST
<font style="color:#D83910;">LOAD_FAST</font> ：一般用于加载局部变量的值，也就是读取值，用于计算或者函数调用传传等

<font style="color:#B92916;">STORE_FAST</font> ：一般用于保存值到局部变量

案例二：

```python
n = n / p
```

<font style="color:#333333;">对应的字节码指令：</font>

```python
1             0 LOAD_NAME                0 (n)
              2 LOAD_NAME                1 (p)
              4 BINARY_TRUE_DIVIDE
              6 STORE_NAME               0 (n)
              8 LOAD_CONST               0 (None)
             10 RETURN_VALUE
```

<font style="color:#F5222D;">说明： 函数的形参也是局部变量，那么如何区分局部变量中的形参呢？</font>

形参是没有初始化的，所以如果发现发现操作的一个局部变量只有 LOAD_FAST 而没有 STORE_FAST,那么这个变量就是形参了。而其它的局部变量在使用之前肯定会使用STORE_FAST进行初始化。

<font style="color:#333333;">案例三：</font>

```python
def test(arg1):
     num = 0
     print(num, arg1)
```

```python
 1            0 LOAD_CONST               0 (<code object test at 0x10546c150, file "code.py", line 1>)
              2 LOAD_CONST               1 ('test')
              4 MAKE_FUNCTION            0
              6 STORE_NAME               0 (test)
              8 LOAD_CONST               2 (None)
             10 RETURN_VALUE
 
Disassembly of <code object test at 0x10546c150, file "code.py", line 1>:
 2            0 LOAD_CONST               1 (0)
              2 STORE_FAST               1 (num)
 
 3            4 LOAD_GLOBAL              0 (print)
              6 LOAD_FAST                1 (num)
              8 LOAD_FAST                0 (arg1).  #只有LOAD_FAST ,没有 STORE_FAST，是形参
             10 CALL_FUNCTION            2
             12 POP_TOP
             14 LOAD_CONST               0 (None)
             16 RETURN_VALUE
```

## 全局变量 — _GLOBAL
<font style="color:#B32916;">LOAD_GLOBAL</font> ： 用来加载全局变量， 包括制定函数名，类名，模块名等全局符号

<font style="color:#AD2317;">STORE_GLOBAL</font> ：用来给全局变量赋值

案例四：

```python
def test(arg1):
     global age
     age = 20
     print(age)
```

<font style="color:#333333;">对应的字节码指令：</font>

```python
 1            0 LOAD_CONST               0 (<code object test at 0x1056e3150, file "code.py", line 1>)
              2 LOAD_CONST               1 ('test')
              4 MAKE_FUNCTION            0
              6 STORE_NAME               0 (test)
              8 LOAD_CONST               2 (None)
             10 RETURN_VALUE
 
Disassembly of <code object test at 0x1056e3150, file "code.py", line 1>:
 3            0 LOAD_CONST               1 (20)
              2 STORE_GLOBAL             0 (age)
 
 4            4 LOAD_GLOBAL              1 (print)
              6 LOAD_GLOBAL              0 (age)
              8 CALL_FUNCTION            1
             10 POP_TOP
             12 LOAD_CONST               0 (None)
             14 RETURN_VALUE
```

# 三、常用数据类型
## 1.list（列表）
<font style="color:#AB2B16;">BUILD_LIST</font> :  用于创建一个 list 结构

<font style="color:#333333;">案例五</font>

```python
a = [1, 2]
```

<font style="color:#333333;">对应的字节码指令：</font>

```python
 1            0 LOAD_CONST               0 (1)
              2 LOAD_CONST               1 (2)
              4 BUILD_LIST               2
              6 STORE_NAME               0 (a)
              8 LOAD_CONST               2 (None)
             10 RETURN_VALUE                      //程序结束
```

<font style="color:#333333;">案例六</font>

```python
[ x for x in range(4) if x > 2 ]
```

<font style="color:#333333;">对应的字节码：</font>

```python
  1           0 LOAD_CONST               0 (<code object <listcomp> at 0x10bffa150, file "code.py", line 1>)
              2 LOAD_CONST               1 ('<listcomp>')
              4 MAKE_FUNCTION            0
              6 LOAD_NAME                0 (range)
              8 LOAD_CONST               2 (4)
             10 CALL_FUNCTION            1
             12 GET_ITER
             14 CALL_FUNCTION            1
             16 POP_TOP
             18 LOAD_CONST               3 (None)
             20 RETURN_VALUE
 
Disassembly of <code object <listcomp> at 0x10bffa150, file "code.py", line 1>:
  1           0 BUILD_LIST               0              //创建 list , 为赋值给某变量，这种时候一般都是语法糖结构了
              2 LOAD_FAST                0 (.0)        
        >>    4 FOR_ITER                16 (to 22)      //开启迭代循环
              6 STORE_FAST               1 (x)          //局部变量x
              8 LOAD_FAST                1 (x)          // 导入 x
             10 LOAD_CONST               0 (2)          // 导入 2
             12 COMPARE_OP               4 (>)          // x 与 2 进行比较，比较符号为 >
             14 POP_JUMP_IF_FALSE        4              // 不满足条件就跳过 “出栈“ 动作，既，continue 到 " >>  4 FOR_ITER. “ 处
             16 LOAD_FAST                1 (x)          // 读取满足条件的局部变量x
             18 LIST_APPEND              2              // 把满足条件的x 添加到list中
             20 JUMP_ABSOLUTE            4              
        >>   22 RETURN_VALUE                            //程序结束
```

## 2.dict（字典）
<font style="color:#C52315;">BUILD_MAP</font> : 用于创建一个空的dict 

<font style="color:#C83014;">STORE_MAP</font> : 用于初始化 dict 中的内容，赋值给变量

案例七

```python
k = {'a': 1}
```

<font style="color:#333333;">对应的字节码：</font>

```python
 1            0 LOAD_CONST               0 ('a')
              2 LOAD_CONST               1 (1)
              4 BUILD_MAP                1
              6 STORE_NAME               0 (k)
              8 LOAD_CONST               2 (None)
             10 RETURN_VALUE
```

## 3.slice（切片）
<font style="color:#CC5115;">BUILD_SLICE</font> :        用于创建切片， 对于 list ， tuple ， 字符串都可以使用slice 的方式进行访问

<font style="color:#D75713;">BINARY_SUBSCR</font> : 读取slice 的值

<font style="color:#D57D11;">STORE_SUBSCR</font> :   slice 的值赋值给变量。

<font style="color:#333333;">案例八</font>

```python
num = [1, 2, 3]
a = num[1:2]
b = num[0:1:1]
num[1:2] = [10, 11]
```

<font style="color:#333333;">对应的字节码：</font>

```python
 1            0 LOAD_CONST               0 (1)
              2 LOAD_CONST               1 (2)
              4 LOAD_CONST               2 (3)
              6 BUILD_LIST               3
              8 STORE_NAME               0 (num)
 
  2          10 LOAD_NAME                0 (num)
             12 LOAD_CONST               0 (1)
             14 LOAD_CONST               1 (2)
             16 BUILD_SLICE              2       #创建了一个切片
             18 BINARY_SUBSCR                    #读取切片中的值
             20 STORE_NAME               1 (a)   #将读取切片中的值赋值给变量 a
 
  3          22 LOAD_NAME                0 (num)
             24 LOAD_CONST               3 (0)
             26 LOAD_CONST               0 (1)
             28 LOAD_CONST               0 (1)
             30 BUILD_SLICE              3
             32 BINARY_SUBSCR
             34 STORE_NAME               2 (b)
 
  4          36 LOAD_CONST               4 (10)
             38 LOAD_CONST               5 (11)
             40 BUILD_LIST               2
             42 LOAD_NAME                0 (num)
             44 LOAD_CONST               0 (1)
             46 LOAD_CONST               1 (2)
             48 BUILD_SLICE              2
             50 STORE_SUBSCR
             52 LOAD_CONST               6 (None)
             54 RETURN_VALUE
```

## 4.循环
<font style="color:#CB4914;">SETUP_LOOP</font> ：用于开始一个循环。 

<font style="color:#D14D11;">JUMP_ABSOLUTE</font>: 结束循环

<font style="color:#333333;">案例九</font>

```python
i = 0
while i < 10:
    i += 1
```

<font style="color:#333333;">对应的字节码：</font>

```python
  1           0 LOAD_CONST               0 (0)
              2 STORE_NAME               0 (i)
 
  2           4 SETUP_LOOP              20 (to 26)   // 循环开始处，26表示循环结束点
        >>    6 LOAD_NAME                0 (i)       // “>>" 表示循环切入点
              8 LOAD_CONST               1 (10)
             10 COMPARE_OP               0 (<)
             12 POP_JUMP_IF_FALSE       24
 
  3          14 LOAD_NAME                0 (i)
             16 LOAD_CONST               2 (1)
             18 INPLACE_ADD
             20 STORE_NAME               0 (i)
             22 JUMP_ABSOLUTE            6          // 逻辑上，循环在此处结束
        >>   24 POP_BLOCK                          
        >>   26 LOAD_CONST               3 (None)
             28 RETURN_VALUE 
```

<font style="color:#333333;">案例十</font>

```python
num = 0
for i in range(5):
    num += i
```

对应的字节码：

```python
  1           0 LOAD_CONST               0 (0)
              2 STORE_NAME               0 (num)
 
  2           4 SETUP_LOOP              24 (to 30)  //开始循环
              6 LOAD_NAME                1 (range)
              8 LOAD_CONST               1 (5)
             10 CALL_FUNCTION            1          //调用range 函数
             12 GET_ITER                            //获取迭代 range 的 iter 
        >>   14 FOR_ITER                12 (to 28)  //开始进行 range 的迭代
             16 STORE_NAME               2 (i)
 
  3          18 LOAD_NAME                0 (num)
             20 LOAD_NAME                2 (i)
             22 INPLACE_ADD
             24 STORE_NAME               0 (num)
             26 JUMP_ABSOLUTE           14
        >>   28 POP_BLOCK
        >>   30 LOAD_CONST               2 (None)
             32 RETURN_VALUE

```

## 5.if语句
<font style="color:#D74C11;">POP_JUMP_IF_FALSE</font> : 条件结果为 FALSE  则跳出 目标的偏移指令

<font style="color:#D74C11;">JUMP_FORWARD</font> :       直接跳转到目标便宜指令

<font style="color:#D85E11;">COMPARE_OP</font>:             比较指令

<font style="color:#333333;">案例十一：</font>

```python
num = 20
if num < 10:
    print('lt 10')
elif num > 10:
    print('gt 10')
else:
    print('eq 10')

```

<font style="color:#333333;">对应的字节码：</font>

```python
  1           0 LOAD_CONST               0 (20)
              2 STORE_NAME               0 (num)
 
  2           4 LOAD_NAME                0 (num)
              6 LOAD_CONST               1 (10)
              8 COMPARE_OP               0 (<)
             10 POP_JUMP_IF_FALSE       22
 
  3          12 LOAD_NAME                1 (print)
             14 LOAD_CONST               2 ('lt 10')
             16 CALL_FUNCTION            1
             18 POP_TOP
             20 JUMP_FORWARD            26 (to 48)
 
  4     >>   22 LOAD_NAME                0 (num)
             24 LOAD_CONST               1 (10)
             26 COMPARE_OP               4 (>)
             28 POP_JUMP_IF_FALSE       40
 
  5          30 LOAD_NAME                1 (print)
             32 LOAD_CONST               3 ('gt 10')
             34 CALL_FUNCTION            1
             36 POP_TOP
             38 JUMP_FORWARD             8 (to 48)
 
  7     >>   40 LOAD_NAME                1 (print)
             42 LOAD_CONST               4 ('eq 10')
             44 CALL_FUNCTION            1
             46 POP_TOP
        >>   48 LOAD_CONST               5 (None)
             50 RETURN_VALUE 
```



