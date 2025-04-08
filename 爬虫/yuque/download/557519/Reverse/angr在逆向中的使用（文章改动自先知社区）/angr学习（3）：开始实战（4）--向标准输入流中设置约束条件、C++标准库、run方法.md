

> 本章存疑：
>
> flag_chars = [claripy.BVS('flag_%d' % i, 8) for i in range(28)]
>
> 这条语句中的'flag_%d' % i是什么意思？for循环前可以添加语句？
>

欢迎回来，接下来我们使用angr的官方例题csaw_wyvern来演示：

[https://github.com/angr/angr-doc/tree/master/examples/csaw_wyvern](https://github.com/angr/angr-doc/tree/master/examples/csaw_wyvern)

我们首先来看一下官方的解题脚本：

```python
#!/usr/bin/env python
# coding: utf-8
import angr
import claripy
import time

def main():
    # Load the binary. This is a 64-bit C++ binary, pretty heavily obfuscated.
    # its correct emulation by angr depends heavily on the libraries it is loaded with,
    # so if this script fails, try copying to this dir the .so files from our binaries repo:
    # https://github.com/angr/binaries/tree/master/tests/x86_64
    p = angr.Project('wyvern')

    # It's reasonably easy to tell from looking at the program in IDA that the key will
    # be 29 bytes long, and the last byte is a newline. Let's construct a value of several
    # symbols that we can add constraints on once we have a state.
    flag_chars = [claripy.BVS('flag_%d' % i, 8) for i in range(28)]
    flag = claripy.Concat(*flag_chars + [claripy.BVV(b'\n')])
    # This block constructs the initial program state for analysis.
    # Because we're going to have to step deep into the C++ standard libraries
    # for this to work, we need to run everyone's initializers. The full_init_state
    # will do that. In order to do this peformantly, we will use the unicorn engine!
    st = p.factory.full_init_state(
            args=['./wyvern'],
            add_options=angr.options.unicorn,
            stdin=flag,
    )
    # Constrain the first 28 bytes to be non-null and non-newline:
    for k in flag_chars:
        st.solver.add(k != 0)
        st.solver.add(k != 10)
    # Construct a SimulationManager to perform symbolic execution.
    # Step until there is nothing left to be stepped.
    sm = p.factory.simulation_manager(st)
    sm.run()
    # Get the stdout of every path that reached an exit syscall. The flag should be in one of these!
    out = b''
    for pp in sm.deadended:
        out = pp.posix.dumps(1)
        if b'flag{' in out:
            return next(filter(lambda s: b'flag{' in s, out.split()))
    # Runs in about 15 minutes!
def test():
    assert main() == b'flag{dr4g0n_or_p4tric1an_it5_LLVM}'
if __name__ == "__main__":
    before = time.time()
    print(main())
    after = time.time()
    print("Time elapsed: {}".format(after - before))
```

尝试使用机器翻译来理解一下：

```python
#!/usr/bin/env python
# coding: utf-8
import angr
import claripy
import time

def main():
    ＃加载二进制文件。这是一个64位C ++二进制文件，非常模糊。
    ＃angr对它的正确模拟在很大程度上取决于所加载的库，
    ＃因此，如果此脚本失败，请尝试从我们的二进制存储库中将.so文件复制到该目录：
    ＃https://github.com/angr/binaries/tree/master/tests/x86_64
    p = angr.Project('wyvern')

    ＃通过查看IDA中的程序可以很容易地看出密钥将
    ＃为29个字节长，最后一个字节为换行符。让我们构造一个值
    ＃符号，一旦有状态，便可以添加约束。
    flag_chars = [claripy.BVS('flag_%d' % i, 8) for i in range(28)]
    flag = claripy.Concat(*flag_chars + [claripy.BVV(b'\n')])
     ＃此块构造初始程序状态以进行分析。
    ＃因为我们将不得不深入C ++标准库
    ＃为了使其正常工作，我们需要运行每个人的初始化程序。full_init_state
    ＃会做到的。为了做到这一点，我们将使用独角兽引擎！
    st = p.factory.full_init_state(
            args=['./wyvern'],
            add_options=angr.options.unicorn,
            stdin=flag,
    )
    ＃将前28个字节限制为非null和非换行符：
    for k in flag_chars:
        st.solver.add(k != 0)
        st.solver.add(k != 10)
    ＃构造一个SimulationManager来执行符号执行。
    ＃步进，直到没有要踩的东西为止。
    sm = p.factory.simulation_manager(st)
    sm.run()
    ＃获取到达出口syscall的每个路径的标准输出。标志应该在其中之一中！
    for pp in sm.deadended:
        out = pp.posix.dumps(1)
        if b'flag{' in out:
            return next(filter(lambda s: b'flag{' in s, out.split()))
    ＃运行约15分钟！
def test():
    assert main() == b'flag{dr4g0n_or_p4tric1an_it5_LLVM}'
if __name__ == "__main__":
    before = time.time()
    print(main())
    after = time.time()
    print("Time elapsed: {}".format(after - before))
```

从翻译中我们可以模糊的知道：这道题的elf文件是由C++编译而来的64位文件，angr对它的正确执行在很大程度上取决于所加载的库，并且脚本也复杂了许多。

首先将文件载入IDA中，发现的确像脚本所说的那样文件使用了C++的库文件进行编写，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592293966684-d990a0f9-11f8-42ad-bf34-6979643488b4.png)

<font style="color:#333333;">由于</font>`angr`<font style="color:#333333;">是只实现了C库，为了深入C++标准库中，</font>**<font style="color:#F5222D;">我们需要在设置state时需要使用</font>**`**<font style="color:#F5222D;">full_init_state</font>**`**<font style="color:#F5222D;">方法，并且设置</font>**`**<font style="color:#F5222D;">unicorn</font>**`**<font style="color:#F5222D;">引擎.</font>**

**<font style="color:#F5222D;">这样吧,我们先运行程序试试:</font>**

```bash
ubuntu@ubuntu:~/Desktop/angr$ ./wyvern
+-----------------------+
|    Welcome Hero       |
+-----------------------+

[!] Quest: there is a dragon prowling the domain.
	brute strength and magic is our only hope. Test your skill.

Enter the dragon's secret: 123

[-] You have failed. The dragon's power, speed and intelligence was greater.
ubuntu@ubuntu:~/Desktop/angr$ 
```

<font style="color:#000000;">载入IDA来到main函数，查看伪代码：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592294211183-12ab0300-6218-48fb-a6f5-f6e7ae90f080.png)

<font style="color:#000000;">首先打印了一堆情景字符串，然后通过调用fgets获取输入保存到变量s，</font><font style="color:#000000;">进入黄色光标位置的start_quest函数,对输入进行处理，出现了一堆的push_back函数,这里看不懂,先不用管他。</font><font style="color:#000000;"></font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592294440314-2116d3b3-fe11-46cd-81cc-9f50e0914562.png)

<font style="color:#000000;">双击进入任意一个</font>secret:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592463343184-c7d6a3fc-7407-4f46-a67b-52ee29742be5.png)

我们可以看到secret中保存着一些已知数据，可以猜测这些数据是为后面的运算打基础(比如进行异或之类的)。push_back的主要信息如下:



![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592294573473-67db3163-dee2-47ec-ab19-1d6e4b675b18.png)

这里大胆的猜测一下flag应该为为29个byte长（最后一个字节为换行符），原因如下：

通过v7 = std::string::length(v12) - 1LL != legend >> 2;可以知道这里判断输入字符串的长度是不是 28 

（ fgets 会把 输入的字符串 + \n 保存到缓冲区，题目中legend>>2 为 28，legend的值为73h）

所以要求输入的字符串的长度应该为 28 个字节，且 每个字节都不是 \x00 或者 \n ；第 29 个字节为 \n，表示输入完成。

因此我们构造长度为28的BVS变量，并在结尾加上`\n`。接下来开始一点一点的剖析脚本（<font style="color:#4C4948;">实际上它最多可以输入 256 位，但是flag没有那么长。输入的字符串会被转换为 string 类型，传入函数 </font>`start_quest(std::string *a1)`<font style="color:#4C4948;"> 中</font><font style="color:#4C4948;">。）</font>

<font style="color:#4C4948;">下面开始一步一步的分析脚本</font>

```python
import angr
import claripy
import time
```

在这里导入了这三个库，不再细说，（导入time库是为了计算脚本所运行的时间，在if __name__ == '__main__'函数可以体现出来，可以不要）。

if __name__ == '__main__'函数如下：

```python
if __name__ == "__main__":
    before = time.time()
    print(main())
    after = time.time()
    print("Time elapsed: {}".format(after - before))
```

> `if __name__ == '__main__'`<font style="color:#4D4D4D;">的意思是：</font>**当.py文件被直接运行时，**`**if __name__ == '__main__'**`**之下的代码块将被运行；当.py文件以模块形式被导入时，**`**if __name__ == '__main__'**`**之下的代码块不被运行。**
>
> elapsed-><font style="color:#999999;">v.</font>(时间) 消逝，流逝;
>

def main():(main函数)

```python
p = angr.Project('./wyvern')
```

这里是加载二进制程序，相当于在终端中输入./wyvern并回车，开始运行程序。

```python
flag_chars = [claripy.BVS('flag_%d' % i, 8) for i in range(28)]
    flag = claripy.Concat(*flag_chars + [claripy.BVV(b'\n')])
    #设置 stdin 的约束条件， 使其 前 28 个字节 不能为 \x00 或者 \n
```

这里是通过`claripy`<font style="color:#333333;">构造输入变量，</font>claripy.Concat方法用于bitVector（位向量）的连接

> 在上一节我们就已经提到了使用claripy.BVS来构造位向量符号（即输入）
>

继续：

```python
 st = p.factory.full_init_state(
            args=['./wyvern'],
            add_options=angr.options.unicorn,
            stdin=flag,
    )
```

首先创建一个 full_init_state ，因为这里是 c++ 代码， 而 angr 只是 实现了一些常用的 c函数，所以得加载所有的库， c++ 的函数在底层才会去调用 c 的函数。创建 full_init_state后 angr 就会跟进 c++ 函数里面。

<font style="color:#333333;">在参数中初始化</font>`state`<font style="color:#333333;">时设置</font>`stdin`<font style="color:#333333;">参数（构造的stdin变量flag），</font>`add_options=angr.options.unicorn，`是为了设置`unicorn`引擎。

我们现在已经初始化了`state`，`angr`已经可以正常工作了，但是为了提高`angr`的执行效率，我们有必要进行条件约束。

设置起来并不麻烦：对stdin设置约束条件， 使其 前 28 个字节 不能为 \x00 或者 \n

```python
for k in flag_chars:
        st.solver.add(k != 0)
        st.solver.add(k != 10)
```

而后便可以执行了。这里先不设置`find`，直接通过`run()`方法运行，这样可以得到29个`deadended`分支。

```python
sm = p.factory.simulation_manager(st)#创建模拟器进行执行
sm.run()#运行模拟器
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592296724868-b1780b37-5125-439b-904f-8dda0a03d572.png)

这里有必要再说一下`SimulationManager`的三种运行方式：

`**<font style="color:#F5222D;">step()</font>**`**<font style="color:#F5222D;">每次向前运行一个基本块，并返回进行分类</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592296724894-a9b91c18-4ef0-4afa-840f-3722003f9f31.png)

`**<font style="color:#F5222D;">run()</font>**`**<font style="color:#F5222D;">运行完所有的基本块，然后会出现</font>**`**<font style="color:#F5222D;">deadended</font>**`**<font style="color:#F5222D;">的状态，此时我们通常访问最后一个状态来获取我们所需要的信息。</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592296724891-e4176f9f-2821-4a48-804c-4f7776532242.png)

`**<font style="color:#F5222D;">explore()</font>**`**<font style="color:#F5222D;">根据</font>**`**<font style="color:#F5222D;">find</font>**`**<font style="color:#F5222D;">和</font>**`**<font style="color:#F5222D;">avoid</font>**`**<font style="color:#F5222D;">进行基本块的执行，最后会返回</font>**`**<font style="color:#F5222D;">found</font>**`**<font style="color:#F5222D;">和</font>**`**<font style="color:#F5222D;">avoid</font>**`**<font style="color:#F5222D;">状态</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592296724929-6363cdc1-acf9-4511-bc7f-11950dc1e4c8.png)

> 一般来说我们使用`explore()`方法即可。
>

此时的flag应该就在这29个`deadended`分支中某个分支的`stdout`中，**<font style="color:#F5222D;">我们得想办法将其取出，通常来说是在最后一个分支当中。</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592296841489-a042d457-7211-4ab7-921f-68d8258a0528.png)

当然我们还是通过代码将其约束取出

```python
out = b''
    for pp in sm.deadended:
        out = pp.posix.dumps(1)
        if b'flag{' in out:
            return out[out.find(b"flag{"):]
```

> **<font style="color:#F5222D;">在前面我们提到过:</font>**
>
> + posix.dumps(0)代表该状态执行路径的**<font style="color:#F5222D;">输入</font>**
> + posix.dumps(1)代表该状态执行路径的**<font style="color:#F5222D;">输出</font>**
>
> **<font style="color:#F5222D;">这里要找的是正确的输出</font>**
>

**<font style="color:#F5222D;">如果不用</font>**`**<font style="color:#F5222D;">run()</font>**`**<font style="color:#F5222D;">方法，而是通过</font>**`**<font style="color:#F5222D;">explore()</font>**`**<font style="color:#F5222D;">运行，也是可以的。</font>**

在IDA中找到最终正确的分支`0x0x4037FD`

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592296841426-d5e1ddec-5eac-488a-93cb-dbb3e29594b9.png)

如下设置：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592296841474-5f4dc214-f875-4219-81de-886c12a56562.png)

最后在`found[0].posix.dumps(0)`打印出flag值

**通过run方法来执行，改动的官方脚本如下：**

```python
#!/usr/bin/env python
# coding: utf-8
import angr
import claripy
import time

def main():
    p = angr.Project('wyvern')

    flag_chars = [claripy.BVS('flag_%d' % i, 8) for i in range(28)]
    flag = claripy.Concat(*flag_chars + [claripy.BVV(b'\n')])

    st = p.factory.full_init_state(
            args=['./wyvern'],
            add_options=angr.options.unicorn,
            stdin=flag,
    )

    for k in flag_chars:
        st.solver.add(k != 0)
        st.solver.add(k != 10)

    sm = p.factory.simulation_manager(st)
    sm.run()

    # Get the stdout of every path that reached an exit syscall. The flag should be in one of these!
    out = b''
    for pp in sm.deadended:
        out = pp.posix.dumps(1)
        if b'flag{' in out:
            return out[out.find(b"flag{"):] #更简单的语句 
            #return next(filter(lambda s: b'flag{' in s, out.split())) 更复杂的语句

if __name__ == "__main__":
    before = time.time()
    print(main())
    after = time.time()
    print("Time elapsed: {}".format(after - before))
```

使用explore()运行：

```python
#!/usr/bin/env python
# coding: utf-8
import angr
import claripy
import time

def main():
    p = angr.Project('./wyvern')#加载二进制程序
    flag_chars = [claripy.BVS('flag_%d' % i, 8) for i in range(28)]
    #这里可以类比:argv1 = claripy.BVS("argv1",100*8)
    flag = claripy.Concat(*flag_chars + [claripy.BVV(b'\n')])
    #字符串链接
    
    st = p.factory.full_init_state(
            args=['./wyvern'],
            add_options=angr.options.unicorn,
            stdin=flag,
    )
    for k in flag_chars:
        st.solver.add(k != 0)
        st.solver.add(k != 10)
    sm = p.factory.simulation_manager(st)
    sm.explore(find=0x4037fd)
    sm.found[0].posix.dumps(1)
   
if __name__ == "__main__":
    before = time.time()
    print(main())
    after = time.time()
    print("Time elapsed: {}".format(after - before))
```

分别保存为run.py和explore.py,运行试试。

> Python assert（断言）用于判断一个表达式，在表达式条件为 false 的时候触发异常。
>
> 断言可以在条件不满足程序运行的情况下直接返回错误，而不必等待程序运行后出现崩溃的情况，例如我们的代码只能在 Linux 系统下运行，可以先判断当前系统是否符合条件。
>
> ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592297565065-2defb0fb-9f90-4c1d-9eb2-c2fdb0e724cd.png)
>
> **<font style="color:#F5222D;">注意：脚本没有任何问题，但是angr给出的情况均为空。。。</font>**
>
> **<font style="color:#F5222D;">。。。。。。</font>**
>



