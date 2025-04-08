> 文章略改动于：[https://www.jianshu.com/p/03d81eb9ac9b](https://www.jianshu.com/p/03d81eb9ac9b)
>

附件:

> 链接：[https://pan.baidu.com/s/1TT6siGqPrq52hAa6wemD_g](https://pan.baidu.com/s/1TT6siGqPrq52hAa6wemD_g)
>
> 提取码：j0ht 
>

复制这段内容后打开百度网盘手机App，操作更方便哦

这篇文章只是纯粹分析python pyc文件格式，主要是关于pyc在文件中的存储方式进行了解析。**<font style="color:#F5222D;">pyc是python字节码在文件中存储的方式，而在虚拟机运行时环境中对应PyCodeObject对象。</font>**关于PyFrameObject以及PyFunctionObject等运行时结构，后续希望学习透彻了能够一并分析。

我用的是python2，基本信息如下：

```powershell
root@kali:~/桌面/CTF# python2
Python 2.7.16 (default, Apr  6 2019, 01:42:57) 
[GCC 8.3.0] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> 
```

## 1.示例文件
源文件test.py（python2）



```python
s = "hello"                                                                                                                                                    
def func():
  a = 3 
  print s
func()
```

通过执行`python -m test.py` 可以生成编译好的pyc文件（虽然会报错，但文件仍然可以正常生成）

```powershell
root@kali:~/桌面/CTF# python -m test.py
hello
/usr/bin/python: No module named test.py
```

得到test.pyc后，执行hexdump -C test.pyc可以得到如下二进制字符流。

```plain
00000000  03 f3 0d 0a 23 00 ff 5e  63 00 00 00 00 00 00 00  |....#..^c.......|
00000010  00 01 00 00 00 40 00 00  00 73 1a 00 00 00 64 00  |.....@...s....d.|
00000020  00 5a 00 00 64 01 00 84  00 00 5a 01 00 65 01 00  |.Z..d.....Z..e..|
00000030  83 00 00 01 64 02 00 53  28 03 00 00 00 74 05 00  |....d..S(....t..|
00000040  00 00 68 65 6c 6c 6f 63  00 00 00 00 01 00 00 00  |..helloc........|
00000050  01 00 00 00 43 00 00 00  73 0f 00 00 00 64 01 00  |....C...s....d..|
00000060  7d 00 00 74 00 00 47 48  64 00 00 53 28 02 00 00  |}..t..GHd..S(...|
00000070  00 4e 69 03 00 00 00 28  01 00 00 00 74 01 00 00  |.Ni....(....t...|
00000080  00 73 28 01 00 00 00 74  01 00 00 00 61 28 00 00  |.s(....t....a(..|
00000090  00 00 28 00 00 00 00 73  07 00 00 00 74 65 73 74  |..(....s....test|
000000a0  2e 70 79 74 04 00 00 00  66 75 6e 63 02 00 00 00  |.pyt....func....|
000000b0  73 04 00 00 00 00 01 06  01 4e 28 02 00 00 00 52  |s........N(....R|
000000c0  01 00 00 00 52 03 00 00  00 28 00 00 00 00 28 00  |....R....(....(.|
000000d0  00 00 00 28 00 00 00 00  73 07 00 00 00 74 65 73  |...(....s....tes|
000000e0  74 2e 70 79 74 08 00 00  00 3c 6d 6f 64 75 6c 65  |t.pyt....<module|
000000f0  3e 01 00 00 00 73 04 00  00 00 06 01 09 03        |>....s........|
000000fe
```

## 2.PyCodeObject结构
PyCodeObject格式如下：

```c
[compile.h]
/* Bytecode object */
typedef struct {
    PyObject_HEAD
    int co_argcount;        /* #arguments, except *args */
    int co_nlocals;     /* #local variables */
    int co_stacksize;       /* #entries needed for evaluation stack */
    int co_flags;       /* CO_..., see below */
    PyObject *co_code;      /* instruction opcodes */
    PyObject *co_consts;    /* list (constants used) */
    PyObject *co_names;     /* list of strings (names used) */
    PyObject *co_varnames;  /* tuple of strings (local variable names) */
    PyObject *co_freevars;  /* tuple of strings (free variable names) */
    PyObject *co_cellvars;      /* tuple of strings (cell variable names) */
    /* The rest doesn't count for hash/cmp */
    PyObject *co_filename;  /* string (where it was loaded from) */
    PyObject *co_name;      /* string (name, for reference) */
    int co_firstlineno;     /* first source line number */
    PyObject *co_lnotab;    /* string (encoding addr<->lineno mapping) */
} PyCodeObject;
```

## 3.Pyc格式解析
```plain
00000000  03 f3 0d 0a 23 00 ff 5e  63 00 00 00 00 00 00 00  |....#..^c.......|
00000010  00 01 00 00 00 40 00 00  00 73 1a 00 00 00 64 00  |.....@...s....d.|
00000020  00 5a 00 00 64 01 00 84  00 00 5a 01 00 65 01 00  |.Z..d.....Z..e..|
00000030  83 00 00 01 64 02 00 53  28 03 00 00 00 74 05 00  |....d..S(....t..|
00000040  00 00 68 65 6c 6c 6f 63  00 00 00 00 01 00 00 00  |..helloc........|
00000050  01 00 00 00 43 00 00 00  73 0f 00 00 00 64 01 00  |....C...s....d..|
00000060  7d 00 00 74 00 00 47 48  64 00 00 53 28 02 00 00  |}..t..GHd..S(...|
00000070  00 4e 69 03 00 00 00 28  01 00 00 00 74 01 00 00  |.Ni....(....t...|
00000080  00 73 28 01 00 00 00 74  01 00 00 00 61 28 00 00  |.s(....t....a(..|
00000090  00 00 28 00 00 00 00 73  07 00 00 00 74 65 73 74  |..(....s....test|
000000a0  2e 70 79 74 04 00 00 00  66 75 6e 63 02 00 00 00  |.pyt....func....|
000000b0  73 04 00 00 00 00 01 06  01 4e 28 02 00 00 00 52  |s........N(....R|
000000c0  01 00 00 00 52 03 00 00  00 28 00 00 00 00 28 00  |....R....(....(.|
000000d0  00 00 00 28 00 00 00 00  73 07 00 00 00 74 65 73  |...(....s....tes|
000000e0  74 2e 70 79 74 08 00 00  00 3c 6d 6f 64 75 6c 65  |t.pyt....<module|
000000f0  3e 01 00 00 00 73 04 00  00 00 06 01 09 03        |>....s........|
000000fe
```

hex开头4个字节是magic number（**<font style="color:#F5222D;">pyc的文件头</font>**）：03 f3 0d 0a ，接下来4个字节是时间，这里是23 00 ff 5e，注意到是小端模式，所以实际是0x5eff0032，可以发现是我开始**<font style="color:#F5222D;">编译的时间</font>**。然后就是PyCodeObject对象了。首先是对象标识**<font style="color:#F5222D;">TYPE_CODE</font>**，也就是0x63.然后4个字节是全局code block的位置参数个数**<font style="color:#F5222D;">co_argument</font>**，这里是00 00 00 00.再接着4个字节(00 00 00 00)是全局code block中的局部变量个数**<font style="color:#F5222D;">co_nlocals</font>**，这里是0.接着4个字节是code block需要的栈空间**<font style="color:#F5222D;">co_stacksize</font>**，这里值为1.然后4个字节是**<font style="color:#F5222D;">co_flags</font>**，这里是0x40.

接下来从0x73开始就是code block的字节码序列co_code。注意到它是PyStringObject形式存在，因此，开始写PyStringObject，注意到首先写1个字节的类型标识TYPE_STRING， 即s，对应0x73。然后**<font style="color:#F5222D;">4个字节标识长度为1a</font>**，也就是26个字节。从0x64开始就是co_code内容了。通过dis命令来看一下内容：

```plain
root@kali:~/桌面/CTF# python
Python 2.7.16 (default, Apr  6 2019, 01:42:57) 
[GCC 8.3.0] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> source = open("test.py").read()
>>> co = compile(source, 'test.py', 'exec')
>>> co.co_consts
('hello', <code object func at 0x7fc87511e130, file "test.py", line 2>, None)
>>> co.co_names
('s', 'func')
>>> import dis
>>> dis.dis(co)
  1           0 LOAD_CONST               0 ('hello')
              3 STORE_NAME               0 (s)

  2           6 LOAD_CONST               1 (<code object func at 0x7fc87511e130, file "test.py", line 2>)
              9 MAKE_FUNCTION            0
             12 STORE_NAME               1 (func)

  5          15 LOAD_NAME                1 (func)
             18 CALL_FUNCTION            0
             21 POP_TOP             
             22 LOAD_CONST               2 (None)
             25 RETURN_VALUE        
>>> len(co.co_code)
26
>>> hex(26)
'0x1a'
>>> 
```

果然是正好26个字节，其中内容分别对应这些指令，其中第一列是在源码中的行数，第二列是该指令在co_code中的偏移，第三列是opcode，分为有操作数和无操作数两种，是一个字节的整数。第四列是操作数，占两个字节。

那么这些指令对应的就是我们看到的pyc文件中的内容了，具体意义参见开头所引用的文章。**LOAD_CONST指令为0x64**，然后两个字节操作数是0。接下来是**STORE_NAME指令0x5a**，操作数是0。其他以此类推.

接下来从0x28开始是**co.co_consts**内容，我们知道这是一个PyTupleObject对象，保存着code block的常量，如在前面看到的那样，我们知道它有3个元素，分别是字符串hello，code object对象func以及None。那么PyTupleObject跟PyListObject类似，首先是记录类型标示TYPE_TUPLE，即'(',也就是0x28了。接下来4个字节是长度，这里是0x3表示有3个元素。然后是元素内容，第一个是'hello',它是PyStringObject对象，因此，先写入标记TYPE_INTERNED,即't'，也就是上面的0x74了，然后呢，是写入4个字节的长度，共5个字节，所以这是0x5，接着就是hello这5个字节。

第二个是code object，好吧，这个就相当于跟之前的流程再来一遍了。

0x63跟之前的一样是TYPE_CODE的标示'c'，然后就是code object的各个字段了。还是来一遍，分别如下

| First Header | Second Header |
| --- | --- |
| co_argcount | 0 |
| co_nlocals | 1 |
| co_stacksize | 1 |
| co_flags | 67 |
| co_code | 标示0x73，即TYPE_STRING。长度0x0f，即15个字节长度。然后从0x64开始就是co_code内容。 |


下面分析下func的co_code，首先看下dis的结果:

> 由于本人不知道如何看子函数func的dis,现列出原作者文章中的dis
>

```plain
In [63]: func.co_nlocals
Out[63]: 1
In [64]: func.co_consts
Out[64]: (None, 3)
In [65]: func.co_names
Out[65]: ('s',)
In [66]: func.co_varnames
Out[66]: ('a',)
In [62]: dis.dis(func)
  4           0 LOAD_CONST               1 (3)  #将func.co_consts[1]即3压栈
              3 STORE_FAST               0 (a)  #存储3在变量a中
  5           6 LOAD_GLOBAL              0 (s) #压入全局变量s
              9 PRINT_ITEM               ##打印s
             10 PRINT_NEWLINE            ##打印换行
             11 LOAD_CONST               0 (None) #None压栈
             14 RETURN_VALUE             #函数返回None
```

```plain
00000060  7d 00 00 74 00 00 47 48  64 00 00 53 28 02 00 00  |}..t..GHd..S(...|
00000070  00 4e 69 03 00 00 00 28  01 00 00 00 74 01 00 00  |.Ni....(....t...|
00000080  00 73 28 01 00 00 00 74  01 00 00 00 61 28 00 00  |.s(....t....a(..|
00000090  00 00 28 00 00 00 00 73  07 00 00 00 74 65 73 74  |..(....s....test|
000000a0  2e 70 79 74 04 00 00 00  66 75 6e 63 02 00 00 00  |.pyt....func....|
000000b0  73 04 00 00 00 00 01 06  01 4e 28 02 00 00 00 52  |s........N(....R|
000000c0  01 00 00 00 52 03 00 00  00 28 00 00 00 00 28 00  |....R....(....(.|
000000d0  00 00 00 28 00 00 00 00  73 07 00 00 00 74 65 73  |...(....s....tes|
000000e0  74 2e 70 79 74 08 00 00  00 3c 6d 6f 64 75 6c 65  |t.pyt....<module|
000000f0  3e 01 00 00 00 73 04 00  00 00 06 01 09 03        |>....s........|
000000fe
```

接下来就是func的co_consts字段了，同样是PyTupleObject对象，先是类型标示0x28，然后4个字节为长度2.接着第一个元素是None(N)，即0x4e，然后是第二个元素3，类型标示是TYPE_INT(i)，即0x69.后面4个字节是整数3.

再接着就是co_names，同样是PyTupleObject对象，显示标示0x28，然后4个字节为长度1，然后字符s是TYPE_INTERNED类型，于是接着是标示't'，即0x74，然后是字符内容s(0x73)。

接下来是co_varnames，同样是PyTupleObject，类型是0x28，然后4个字节为长度1，然后是字符a。再后面是闭包相关的东西co_freevars，为空的PyTupleObject，类型0x28后面4个字节长度为0。然后是code block内部嵌套函数引用的局部变量名集合co_cellvars，同样是空的PyTupleObject对象。

接着0x73开始就是co_filename了，这是PyStringObject对象，先是对象标示s，然后是长度0x07.后面是对应的文件的完整路径"test.py"。

接着是co_name，即函数名或者类名，这里就是func了，首先也是对象标示't'(0x74)，后面跟着长度0x4，然后是'func'这四个字节。

然后是co_firstlineno，这里直接写的整数0x2.

然后是字节码指令与源文件行号对应关系co_lnotab，以PyStringObject对象存储。先是标示's'(0x73)，然后是长度4个字节，然后是内容0x00010601.

好吧，至此，func这个code object分析完成。我们回到全局的code object。

全局code object从co_consts[2]开始,这是None，如前面一样，标示为0x4e。接着就是co_names，co_varnames等，分析跟前面func的类似，不再赘述。注意的是这里的co_names对应的's'和’func'类型不再是TYPE_INTERNED，而是TYPE_STRINGREF('R'),值是0x52.还有就是co_lnotab是0x06010903

