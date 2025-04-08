本篇文章使用ais3_crackme为例，来说明如何进行命令行输入。

示例下载地址：[https://github.com/angr/angr-doc/tree/master/examples/ais3_crackme](https://github.com/angr/angr-doc/tree/master/examples/ais3_crackme)

首先第一个问题我们要搞懂什么是命令行输入?

所谓的命令行输入,说白了就是在运行程序的过程前程序要求输入的参数

还不明白?举个例子,假设有一个名为Cyberangel的程序,

不要求命令行输入的程序:

```bash
ubuntu@ubuntu:~/Desktop/angr$ ./Cyberangel
plz input password:
123
incorrect!
```

要求命令行输入的程序:

```bash
ubuntu@ubuntu:~/Desktop/angr$ ./Cyberangel
plz input password!
ubuntu@ubuntu:~/Desktop/angr$ ./Cyberangel 123
incorrect!
```

这样就好理解多了,我们先来看一下官方的angr脚本：

```python
#!/usr/bin/env python


'''
ais3_crackme has been developed by Tyler Nighswander (tylerni7) for ais3.
It is an easy crackme challenge. It checks the command line argument.
'''

import angr
import claripy


def main():
    project = angr.Project("./ais3_crackme")

    #create an initial state with a symbolic bit vector as argv1
    argv1 = claripy.BVS("argv1",100*8) #since we do not the length now, we just put 100 bytes
    initial_state = project.factory.entry_state(args=["./crackme1",argv1])

    #create a path group using the created initial state 
    sm = project.factory.simulation_manager(initial_state)

    #symbolically execute the program until we reach the wanted value of the instruction pointer
    sm.explore(find=0x400602) #at this instruction the binary will print(the "correct" message)

    found = sm.found[0]
    #ask to the symbolic solver to get the value of argv1 in the reached state as a string
    solution = found.solver.eval(argv1, cast_to=bytes)

    print(repr(solution))
    solution = solution[:solution.find(b"\x00")]
    print(solution)
    return solution

def test():
    res = main()
    assert res == b"ais3{I_tak3_g00d_n0t3s}"


if __name__ == '__main__':
    print(repr(main()))
```

我们来翻译，并粗略的看一下（机器翻译不太准确，之后会有详细的解释）

```python
#!/usr/bin/env python


'''
ais3_crackme是由Tyler Nighswander (tylerni7)为ais3开发的。
这是一个简单的挑战。它检查命令行参数。
'''

import angr
import claripy


def main():
    project = angr.Project("./ais3_crackme")#加载二进制程序
	
    #用符号位向量创建一个初始状态赋值给angr1，因为我们现在不知道长度，所以我们只放入100个字节（足够了）
    argv1 = claripy.BVS("argv1",100*8) 
    #接着创建一个状态赋值给初始状态，默认就是程序的入口地址，也可以指定一个地址作为入口地址
    initial_state = project.factory.entry_state(args=["./crackme1",argv1])

    #使用创建的初始状态创建路径组
    sm = project.factory.simulation_manager(initial_state)

    #象征性地执行程序（也就是不会实际的执行程序），直到我们到达指令指针的期望值为止（直到到达我们期望的正确的终点为止）
    sm.explore(find=0x400602) #在这条指令下，二进制文件将打印(“正确”的消息)

    found = sm.found[0]
    #请求符号求解器获取到达状态的argv1的值作为字符串
    solution = found.solver.eval(argv1, cast_to=bytes)

    print(repr(solution))
    solution = solution[:solution.find(b"\x00")]
    print(solution)
    return solution

def test():
    res = main()
    assert res == b"ais3{I_tak3_g00d_n0t3s}"


if __name__ == '__main__':
    print(repr(main()))
```



首先进入angr的虚拟环境：

```bash
ubuntu@ubuntu:~/Desktop/angr$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/angr$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/angr$ workon
angr
ubuntu@ubuntu:~/Desktop/angr$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

开始在Linux中运行程序，我们知道在运行程序时需要传入参数，因此随便输入一个就行了

```bash
(angr) ubuntu@ubuntu:~/Desktop/angr$ ./ais3_crackme Cyberangel
I'm sorry, that's the wrong secret key!
```

它提示我们输入的key不正确，载入IDA中，我们查看一下程序的逻辑：

逻辑十分的简单，不再细说

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592277268417-023c5825-fade-4e99-ad5a-9fd378ad2622.png)

> **<font style="color:#F5222D;">注意，要先检查一下PIE是否开启</font>**
>

**<font style="color:#F5222D;">需要注意的是：</font>****<font style="color:#F5222D;">在</font>**`**<font style="color:#F5222D;">angr==8.18.10.25</font>**`**<font style="color:#F5222D;">版本中，需要通过</font>**`**<font style="color:#F5222D;">claripy</font>**`**<font style="color:#F5222D;">模块，来构造输入。</font>**

<font style="color:#333333;">和</font>`z3`<font style="color:#333333;">类似，</font>`claripy`<font style="color:#333333;">是一个符号求解引擎</font><font style="color:#333333;">，</font><font style="color:#333333;">我们完全可以将其当成是</font>`z3`<font style="color:#333333;">进行使用。</font>



claripy关于变量的定义在claripy.ast.bv.BV当中，看一下官方的文档：[http://angr.io/api-doc/claripy.html](http://angr.io/api-doc/claripy.html)

> 进入网站请自带梯子
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592277732536-955536a1-d3b7-4c23-95d6-b7b9652d5b3e.png)

看不懂？没关系，我们使用google翻译来看一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592277782329-8f71d0e9-1c42-49cb-af16-0a1bf55a2523.png)

bb了这么多，就是要告诉我们要使用BVS或BVV构造符号和值(也就是构造传入的参数)，然后使用操作构造更复杂的表达式。

继续看：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592277966671-bd51e2d6-5d62-46ba-8499-5f966d88624f.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592277970303-861558c3-9f83-47bd-b1cb-f8d0fec31ac7.png)

在这里我们主要知道了：**<font style="color:#F5222D;">通常使用</font>**`**<font style="color:#F5222D;">claripy.BVS()</font>**`**<font style="color:#F5222D;">创建位向量符号和里面的参数</font>**<font style="color:#333333;">，继续：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592278090701-37c7016a-057c-453a-839c-819b7ab711fc.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592278093831-f6ccc518-e7d4-4670-9ca5-3d54598a2782.png)

<font style="color:#333333;">在此处我们了解到了要</font><font style="color:#333333;">使用</font>`claripy.BVV()`<font style="color:#333333;">创建位向量值</font>

> Q：位向量是什么？
>
> A：简而言之，位向量（bit vector）就是由一些二进制位组成的向量。
>
> 位向量是比特序列，既可以表示具体值，也可以是符号变量。
>
> 通过 `BVV(value,size)` 和 `BVS(name, size)` 接口创建位向量
>

**<font style="color:#F5222D;">总结：使用</font>**`**<font style="color:#F5222D;">claripy.BVS()</font>**`**<font style="color:#F5222D;">创建位向量符号，</font>**`**<font style="color:#F5222D;">claripy.BVV()</font>**`**<font style="color:#F5222D;">创建位向量值</font>**

如果你对上面的位向量一头雾水，那就先不用管他,一点一点的剖析angr脚本就好

```bash
import angr
import claripy
```

这里是导入angr和clarity库，这好比写字的时候需要笔，angr和clarify就好比那支笔一样。

```python
project = angr.Project("./ais3_crackme")
```

这里是加载二进制程序，angr.Project中省略了一些参数，参数在解题需要的时候加上即可，详见官方文档

```python
argv1 = claripy.BVS("argv1",100*8) 
```

> 在上面提到过**<font style="color:#F5222D;">使用</font>**`**<font style="color:#F5222D;">claripy.BVS()</font>**`**<font style="color:#F5222D;">创建位向量符号</font>**
>

第二个(也就是引号中的)argv1是符号名称(这里的符号名称应该可以是任意的)，100*8是长度以bit为单位，这里是**输入了100个字节**（1byte=8bit），位向量肯定是以位（bit）为单位。因为我们不知道正确答案是多少，所以长一点最好。（通常来说在做题时，flag的长度还是很好判断的。具体情况具体分析）

```python
initial_state = p.factory.entry_state()
或者是之前一直写的:
state = proj.factory.entry_state() 
#接着创建一个状态，默认就是程序的入口地址，也可以指定一个地址作为入口地址
#这两个语句相同,只是变量名称不同罢了,习惯写哪个就写那个
```

看看代码中的“["./ais3_crackme",argv1]”像什么？没错，他就像我们在执行Linux程序时在终端中输入的命令：

```python
ubuntu@ubuntu:~/Desktop/angr$ ././ais3_crackme 123
incorrect!
```

argv1是其中的参数，也就是前面的“argv1 = claripy.BVS("argv1",100*8) ”。

> github的initial_state = project.factory.entry_state(args=["./crackme1",argv1])应该改为“initial_state = p.factory.entry_state(args=["./ais3_crackme",argv1])”，因为没有crackme1这个可执行文件
>

```python
sm = project.factory.simulation_manager(initial_state)
```

紧接着创建一个模拟器（factory.simulation_manager)用来模拟程序执行

> simulation的中文意思是模拟
>

```python
sm.explore(find=0x400602)
```

使用explore执行模拟器，find和avoid用来作为约束条件。

**<font style="color:#F5222D;">那么此时我们不能像之前那样通过</font>**`**<font style="color:#F5222D;">posix.dump(0)</font>**`**<font style="color:#F5222D;">来打印出结果，</font>****<font style="color:#F5222D;">因为我们是通过命令行传参</font>**，是手动输入的数据，那么此时使路径正确的数据保存在哪里呢？

我们需要继续查看`SimState`都由哪些属性。

> 这里的SimState指的是“simulation state”的缩写，即代码中的“sm”
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592280084209-0eaef863-2c96-4620-8b1c-d345c866d93c.png)

之前提到过`claripy`是类似于`z3`的符号执行引擎，所以可以看到`solver`属性

`:ivar solver: The symbolic solver and variable manager for this state`

> ` The symbolic solver and variable manager for this state`
>
> 翻译:此状态的符号求解器和变量管理器
>

同样的我们查看`found.solver`都有哪些属性和方法。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592280084144-14bf0fac-d9fd-4b72-8754-bb97de437a48.png)

**<font style="color:#F5222D;">为了能正确的将</font>**`**<font style="color:#F5222D;">found</font>**`**<font style="color:#F5222D;">中保存的符号执行的结果打印出来，我们可以使用</font>**`**<font style="color:#F5222D;">eval</font>**`**<font style="color:#F5222D;">方法。</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592280084196-b1ad4b62-d3ff-4fd4-a0f1-ebee66fce203.png)

并且可以使用`cast_to`参数对需要打印的值进行**<font style="color:#F5222D;">类型转换</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592280084175-5119b976-1037-46cc-9da4-ac0726cc351e.png)

通常来说只要找到了找到了正确的路径，那么打印结果并不是太大的问题。

修改后的完整脚本如下：

```python
import angr
import claripy

project = angr.Project("./ais3_crackme")
argv1 = claripy.BVS("argv1", 100 * 8)  # 构造了100个字节(不知道真实值的长度，所以大一点)
initial_state = project.factory.entry_state(args=["./ais3_crackme", argv1])  
# 构造程序入口点的参数 ,第一个是filename，第二开始是程序参数

sm = project.factory.simulation_manager(initial_state)  
# 从入口点出创建一个模拟器来进行符号执行

sm.explore(find=0x400602)
found = sm.found[0]

# 获得正确结果中相对应的argv1符号的值，转换成bytes. cast_to支持的类型有int和bytes
solution = found.solver.eval(argv1, cast_to=bytes)  

print(bytes.decode(solution).strip('\x00')) # 先解码转换成str，再去掉\x00
```

保存为1.py，尝试着执行一下：

```python
(angr) ubuntu@ubuntu:~/Desktop/angr$ python 1.py
ais3{I_tak3_g00d_n0t3s}
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

flag：ais3{I_tak3_g00d_n0t3s}

