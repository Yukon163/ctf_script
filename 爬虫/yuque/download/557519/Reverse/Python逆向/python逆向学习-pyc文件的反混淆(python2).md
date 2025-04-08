> 参考资料：[https://www.52pojie.cn/thread-912103-1-1.html](https://www.52pojie.cn/thread-912103-1-1.html)
>
> [http://www.chumen77.xyz/2020/06/27/DASCTF%E5%AE%89%E6%81%92%E6%9C%88%E8%B5%9B(6th)/#pyCharm-pyc%E6%96%87%E4%BB%B6%E6%81%A2%E5%A4%8D](http://www.chumen77.xyz/2020/06/27/DASCTF%E5%AE%89%E6%81%92%E6%9C%88%E8%B5%9B(6th)/#pyCharm-pyc%E6%96%87%E4%BB%B6%E6%81%A2%E5%A4%8D)
>

以2020DASCTF-pyCharm作为例题来讲解：

[2020DASCTF-pyCharm（pyc反混淆）](https://www.yuque.com/cyberangel/vqcmca/mwzgf2)

之前遇到过pyc文件的反编译，直接上脚本或网站进行解密就行了。但是pyc文件一旦加入了混淆，任何工具或网站是没有办法反编译出来py文件的，因此我们需要去掉pyc文件本身的混淆，以达到反编译的效果。

pyc文件的格式如下：

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

反编译混淆过的文件需要先去掉混淆，方法如下：

首先**加载pyc co_code**：

```python
root@kali:~/桌面/CTF# python
Python 2.7.16 (default, Apr  6 2019, 01:42:57) 
[GCC 8.3.0] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import dis,marshal
>>> f=open('1.pyc')
>>> f.read(4)
'\x03\xf3\r\n'
>>> f.read(4)
'jv\xe7^'
>>> code = marshal.load(f)
>>> code.co_consts
(-1, None, 'YamaNalaZaTacaxaZaDahajaYamaIa0aNaDaUa3aYajaUawaNaWaNajaMajaUawaNWI3M2NhMGM=', 'Are u ready?', 0, 32, 'a', '', 'great!waht u input is the flag u wanna get.', 'pity!')
>>> code.co_varnames
()
>>> code.co_names
('base64', 'a', 'raw_input', 'flag', 'b64encode', 'c', 'list', 'd', 'range', 'i', 'join', 'ohh')
>>> code.co_code
"q\x03\x00q\x00\x06d\xffd\x00\x00d\x01\x00l\x00\x00Z\x00\x00d\x02\x00Z\x01\x00e\x02\x00d\x03\x00\x83\x01\x00Z\x03\x00e\x00\x00j\x04\x00e\x03\x00\x83\x01\x00Z\x05\x00e\x06\x00e\x05\x00\x83\x01\x00Z\x07\x00x'\x00e\x08\x00d\x04\x00d\x05\x00\x83\x02\x00D]\x16\x00Z\t\x00e\x07\x00e\t\x00c\x02\x00\x19d\x06\x007\x03<qI\x00Wd\x07\x00j\n\x00e\x07\x00\x83\x01\x00Z\x0b\x00e\x0b\x00e\x01\x00k\x02\x00r\x86\x00d\x08\x00GHn\x05\x00d\t\x00GHd\x01\x00S"
```

使用dis库对co_code进行解释：

```python
>>> dis.dis(code.co_code)
          0 JUMP_ABSOLUTE       3
    >>    3 JUMP_ABSOLUTE    1536
          6 LOAD_CONST      25855 (25855)
          9 STOP_CODE      
         10 STOP_CODE      
         11 LOAD_CONST          1 (1)
         14 IMPORT_NAME         0 (0)
         17 STORE_NAME          0 (0)
         20 LOAD_CONST          2 (2)
         23 STORE_NAME          1 (1)
         26 LOAD_NAME           2 (2)
         29 LOAD_CONST          3 (3)
         32 CALL_FUNCTION       1
         35 STORE_NAME          3 (3)
         38 LOAD_NAME           0 (0)
         41 LOAD_ATTR           4 (4)
         44 LOAD_NAME           3 (3)
         47 CALL_FUNCTION       1
         50 STORE_NAME          5 (5)
         53 LOAD_NAME           6 (6)
         56 LOAD_NAME           5 (5)
         59 CALL_FUNCTION       1
         62 STORE_NAME          7 (7)
         65 SETUP_LOOP         39 (to 107)
         68 LOAD_NAME           8 (8)
         71 LOAD_CONST          4 (4)
         74 LOAD_CONST          5 (5)
         77 CALL_FUNCTION       2
         80 GET_ITER       
         81 FOR_ITER           22 (to 106)
         84 STORE_NAME          9 (9)
         87 LOAD_NAME           7 (7)
         90 LOAD_NAME           9 (9)
         93 DUP_TOPX            2
         96 BINARY_SUBSCR  
         97 LOAD_CONST          6 (6)
        100 INPLACE_ADD    
        101 ROT_THREE      
        102 STORE_SUBSCR   
        103 JUMP_ABSOLUTE      73
    >>  106 POP_BLOCK      
    >>  107 LOAD_CONST          7 (7)
        110 LOAD_ATTR          10 (10)
        113 LOAD_NAME           7 (7)
        116 CALL_FUNCTION       1
        119 STORE_NAME         11 (11)
        122 LOAD_NAME          11 (11)
        125 LOAD_NAME           1 (1)
        128 COMPARE_OP          2 (==)
        131 POP_JUMP_IF_FALSE   134
    >>  134 LOAD_CONST          8 (8)
        137 PRINT_ITEM     
        138 PRINT_NEWLINE  
        139 JUMP_FORWARD        5 (to 147)
        142 LOAD_CONST          9 (9)
        145 PRINT_ITEM     
        146 PRINT_NEWLINE  
    >>  147 LOAD_CONST          1 (1)
        150 RETURN_VALUE   
>>> 
```

进行解释之后我们就可以看到python文件的字节码，在这里面我们需要注意到字节码开头的：

```python
>>> dis.dis(code.co_code)
          0 JUMP_ABSOLUTE       3
    >>    3 JUMP_ABSOLUTE    1536
          6 LOAD_CONST      25855 (25855)
          9 STOP_CODE      
         10 STOP_CODE      
         11 LOAD_CONST          1 (1)
         14 IMPORT_NAME         0 (0)
```

看不懂字节码的可以看看我另外一篇文章，里面附有例题，在这里不过多的解释：

[（整理）Python字节码详解](https://www.yuque.com/cyberangel/rg9gdm/vebs87)

在上述的字节码中，很明显的加入了混淆，怎么会一开头就STOP_CODE了呢？我们期望的pyc文件开头是这样的：

```python
0 LOAD_CONST 0(0)
1 LOAD_CONST 1(1)
```

**<font style="color:#F5222D;">接着就是想办法去除这些混淆了并修正co_code的长度</font>**

**<font style="color:#F5222D;">其中部分的字节码对应的hex如下：</font>**

```plain
0x64 操作为LOAD_CONST，用法举例：LOAD_CONST 1           HEX: 640100
0x71 操作为JUMP_ABSOLUTE，用法举例：JUMP_ABSOLUTE 14    HEX: 710e00
0x65 操作为LOAD_NAME，用法举例：LOAD_NAME 1             HEX: 650100
```

拿JUMP_ABSOLUTE来说：

0x71对应着hex开头的71，JUMP_ABSOLUTE 14的14对应着hex中的0e，剩下00理解成自带的就ok了（部分指令可能有所变化）

我们将期望的0 LOAD_CONST 0(0)和1 LOAD_CONST 1(1)翻译成hex分别为：640000、640100

将原文件中开头的0 JUMP_ABSOLUTE       3翻译为710300

在hex中找到他们：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593767392138-ecd97b38-b3c6-4b36-a4cd-e883021646a5.png)

第一个红箭头所指向的地方就是co_code的长度，第二处就是混淆的地方，删掉混淆的地方就行了

原co_code的长度如下：

```c
>>> len(code.co_code)
151
>>> hex(151)
'0x97'
>>> 

```

所以去除这8个字节的混淆代码，然后修改co_code长度为0x8f。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593767781535-a06ad4f0-d29c-48c3-91ff-5dde61b32937.png)

完成这些之后，就开始反编译，反编译方法就多种多样了，可以使用网站什么的，我使用的uncompyle6：

```bash
uncompyle6 -o 1.py 1.pyc
```

可以得到：

```bash
# uncompyle6 version 3.7.1
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.16 (default, Apr  6 2019, 01:42:57) 
# [GCC 8.3.0]
# Embedded file name: pyCharm.py
# Compiled at: 2020-06-15 21:23:54
import base64
a = 'YamaNalaZaTacaxaZaDahajaYamaIa0aNaDaUa3aYajaUawaNaWaNajaMajaUawaNWI3M2NhMGM='
flag = raw_input('Are u ready?')
c = base64.b64encode(flag)
d = list(c)
for i in range(0, 32):
    d[i] += 'a'

ohh = ('').join(d)
if ohh == a:
    print 'great!waht u input is the flag u wanna get.'
else:
    print 'pity!'
```

阅读一下代码就可以知道把“a”去除后解码base64即可。

YmNlZTcxZDhjYmI0NDU3YjUwNWNjMjUwNWI3M2NhMGM=

bcee71d8cbb4457b505cc2505b73ca0c

flag{bcee71d8cbb4457b505cc2505b73ca0c}

