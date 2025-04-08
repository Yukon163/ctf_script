> 构造堆栈的核心为：找到函数调用前的esp情况和调用后的esp情况，以及输入的地址
>

例题在此：[https://github.com/angr/angr-doc/tree/master/examples/flareon2015_2](https://github.com/angr/angr-doc/tree/master/examples/flareon2015_2)

<font style="color:#333333;">例题来自</font>`flareon2015_2`

将程序下载下来载入到IDA中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592641747987-8be3512b-ff40-4533-b839-d0e31c52d342.png)

只有这几个函数，加壳了？

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592641768703-5ec00f62-465e-4c3d-a1c5-10e3a5275e97.png)

好吧，没有加壳，Windows exe可执行文件，添加扩展名为exe，打开程序：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592641872974-3b9413a6-29c2-43a1-a0b4-5c7a919e2290.png)

根据程序的字符串在IDA中来到sub_401000，逻辑很简单，输入password，判断对错

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592642158588-262a83ae-0b2e-4e31-80d9-6f79ca27ce08.png)

看下sub_401000伪代码：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592642265318-e13c610e-50e2-4cd4-a442-f4c758cfd096.png)

解决办法：[https://www.yuque.com/cyberangel/rg9gdm/br027e](https://www.yuque.com/cyberangel/rg9gdm/br027e)

当然，你可以选择不解决，

接下来大致了解一下官方的angr脚本中写了什么：

```python
#!/usr/bin/env python
import angr

def main():
    b = angr.Project("very_success", load_options={"auto_load_libs":False})
    # create a state at the checking function
    # Since this is a windows binary we have to start after the windows library calls
    # remove lazy solves since we don't want to explore unsatisfiable paths
    s = b.factory.blank_state(addr=0x401084)
    # set up the arguments on the stack
    s.memory.store(s.regs.esp+12, s.solver.BVV(40, s.arch.bits))
    s.mem[s.regs.esp+8:].dword = 0x402159
    s.mem[s.regs.esp+4:].dword = 0x4010e4
    s.mem[s.regs.esp:].dword = 0x401064
    # store a symbolic string for the input
    s.memory.store(0x402159, s.solver.BVS("ans", 8*40))
    # explore for success state, avoiding failure
    sm = b.factory.simulation_manager(s)
    sm.explore(find=0x40106b, avoid=0x401072)
    # print(the string)
    found_state = sm.found[0]
    return found_state.solver.eval(found_state.memory.load(0x402159, 40), cast_to=bytes).strip(b'\0')

def test():
    assert main() == b'a_Little_b1t_harder_plez@flare-on.com'

if __name__ == '__main__':
    print(main())
```

手动翻译如下（有删改，为了行文流畅）：

```python
#!/usr/bin/env python
import angr

def main():
    b = angr.Project("very_success", load_options={"auto_load_libs":False})
    # 创建一个angr项目并且禁用CLE自动解析共享库依赖关系（说白了就是不自动加载C函数的库文件）
    # 因为这是一个Windows的二进制文件，为了避免调用Windows的API，
    # 我们需要从0x401084设为起始状态，并且设置好传入的参数。
    
    s = b.factory.blank_state(addr=0x401084)#创建一个空白的状态，起始地址为0x401084
    
    # 设置堆栈上的参数
    s.memory.store(s.regs.esp+12, s.solver.BVV(40, s.arch.bits))
    s.mem[s.regs.esp+8:].dword = 0x402159
    s.mem[s.regs.esp+4:].dword = 0x4010e4
    s.mem[s.regs.esp:].dword = 0x401064
    
    # 为输入存储一个符号字符串，因为此时的输入是空白的
    s.memory.store(0x402159, s.solver.BVS("ans", 8*40))
   
	# 创建模拟执行器
    sm = b.factory.simulation_manager(s)
    sm.explore(find=0x40106b, avoid=0x401072)#分别是success和failure
    
    # 打印字符串
    found_state = sm.found[0]
    return found_state.solver.eval(found_state.memory.load(0x402159, 40), cast_to=bytes).strip(b'\0')

def test():
    assert main() == b'a_Little_b1t_harder_plez@flare-on.com'

if __name__ == '__main__':
    print(main())
```

**<font style="color:#F5222D;">为了避免调用</font>**`**<font style="color:#F5222D;">windows</font>**`**<font style="color:#F5222D;">的API，我们需要从</font>**`**<font style="color:#F5222D;">0x401084</font>**`**<font style="color:#F5222D;">设为起始状态，并且设置好传入的参数。</font>**

> 0x401084为函数sub_401084校验输入的地方
>

通过上下文，可以知道`0x402159`存放的是输入的数据，这个angr代码主要看这里：

```python
    # 设置堆栈上的参数
    s.memory.store(s.regs.esp+12, s.solver.BVV(40, s.arch.bits))
    s.mem[s.regs.esp+8:].dword = 0x402159
    s.mem[s.regs.esp+4:].dword = 0x4010e4
    s.mem[s.regs.esp:].dword = 0x401064
```

根据windows 32 位参数传递规则，我们可以如上进行构造。angr支持许多类型的数据，包括dword,word,long,int,uint8_t,uint32_t等等。我建议只要对自己的理解不产生影响，选取合适类型即可。

> 作者注：我通常会选择uint8_t之类的数据类型，毕竟对linux编程比较熟悉。
>

为什么可以这样构造？

根据前面的 `ReadFile` 函数，我们可以判断出 0x402159 处存放的是我们输入的数据，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592645192355-9535a341-3874-494b-9e2c-662cba02fe3d.png)

> ReadFile：从文件指针指向的位置开始将数据读出到一个文件中, 且支持同步和异步操作,
>
> WriteFile是一个函数，可以将数据写入一个文件或者I/O设备。
>

校验输入最终的判断依据为00401067的test eax, eax和jz short loc_401072

> text eax,eax是与运算，只有当eax为00000000才能保证0标志位ZF=1 即满足下面的跳转 换言之 这个是测试eax是否为0，为0则跳
>
> JZ(Jump if Zero)是此前的运算结果为0时跳转。 若此前运算结果不为0,则不跳转,
>
> **<font style="color:#F5222D;">不要被IDA的红绿箭头所搞晕</font>**
>

因为在脚本的一开始我们有s = b.factory.blank_state(addr=0x401084)，直接从地址0x401084起跳，并没有调用函数sub_401000，因此我们需要根据参数构造（模仿）sub_401084函数调用前和调用后的堆栈。参照的压栈顺序：

```plain
.text:00401051                 push    eax             ; lpNumberOfBytesWritten
.text:00401052                 push    11h             ; nNumberOfBytesToWrite
.text:00401054                 push    dword ptr [ebp-4]
.text:00401057                 push    offset unk_402159
.text:0040105C                 push    dword ptr [ebp-10h]
.text:0040105F                 call    sub_401084
.text:00401064                 add     esp, 0Ch
```

题解给的构造方法如下：

```python
s.memory.store(s.regs.esp+12, s.solver.BVV(40, s.arch.bits))
```

对于这一句，它创建了一个值为 40，大小（以 bits 为单位）为 s.arch.bits 的位向量值（BVV）。其中 s.arch.bits 的值为 32（这是一个 32 位的程序），

```python
In [4]: s.arch
Out[4]: <Arch X86 (LE)>
In [5]: s.arch.bits
Out[5]: 32
```

接着它将该值载入到 esp+12 （esp+C）的位置上。对于这个地址，我们可以看到它原本是 push dword ptr [ebp-4]。在IDA中往前看并没有找到它的具体的值，这里也就顺便传了一个符号进去，**<font style="color:#F5222D;">保存函数call sub_401084调用后的堆栈情况。</font>**

再来看这个：

```python
s.mem[s.regs.esp+8:].dword = 0x402159   # 输入的数据存放的地址
s.mem[s.regs.esp+4:].dword = 0x4010e4   # 函数调用前[ebp-10h]存放的地址，我们逆过去能找到它
s.mem[s.regs.esp:].dword = 0x401064     # 返回值地址，确切的来说是 call 调用之后EIP的地址
```

> s.mem[s.regs.esp:].dword表示的是esp寄存器所存放的地址
>

我们以地址0x401064为基准来用esp表示0x402159、0x4010e4



有关那个 0x4010e4 的地址，实际上我们看它压入的是 [ebp-10h]，我们从push dword ptr [ebp-10h]向前追溯，在 0x401007 有一段 mov [ebp-10h], eax，我们再往前看，0x401000 有一段 pop eax。接下来再向前找就只能找到 .text:004010DF call sub_401000 了。因此这里的值是 0x4010e4，**<font style="color:#F5222D;">保存函数</font>****<font style="color:#F5222D;">sub_401084</font>****<font style="color:#F5222D;">调用前的堆栈</font>**。

当然如果你懒的话动态调试也可以堆栈的情况得到：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593255538376-f8a87b14-2d7d-42e3-a412-a9f6fbb87601.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593255539186-49681ceb-c635-4ba1-a974-987c1556ecd6.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592646860037-4f7dbdf0-f424-4faa-8a5b-204b56e602aa.png)

<font style="color:#4C4948;">接下来就创建 simulation manager，设置 find 和 avoid 即可：</font>

```python
sm = b.factory.simulation_manager(s)
sm.explore(find = 0x40106b, avoid = 0x401072)
```

<font style="color:#4C4948;">最后输出即可。</font>

```python
found_state = sm.found[0]
found_state.solver.eval(found_state.memory.load(0x402159, 40), cast_to=bytes).strip(b'\0')
```

整理脚本如下：

```python
#!/usr/bin/env python
import angr

def main():
    b = angr.Project("very_success", load_options={"auto_load_libs":False})
    # 创建一个angr项目并且禁用CLE自动解析共享库依赖关系（说白了就是不自动加载C函数的库文件）
    # 因为这是一个Windows的二进制文件，为了避免调用Windows的API，
    # 我们需要从0x401084设为起始状态，并且设置好传入的参数。
    
    s = b.factory.blank_state(addr=0x401084)#创建一个空白的状态，起始地址为0x401084
    
    # 设置堆栈上的参数
    s.memory.store(s.regs.esp+12, s.solver.BVV(40, s.arch.bits))
    s.mem[s.regs.esp+8:].dword = 0x402159
    s.mem[s.regs.esp+4:].dword = 0x4010e4
    s.mem[s.regs.esp:].dword = 0x401064
    
    # 为输入存储一个符号字符串，因为此时的输入是空白的
    s.memory.store(0x402159, s.solver.BVS("ans", 8*40))
   
	# 创建模拟执行器
    sm = b.factory.simulation_manager(s)
    sm.explore(find=0x40106b, avoid=0x401072)#分别是success和failure
    
    # 打印字符串
    found_state = sm.found[0]
    return found_state.solver.eval(found_state.memory.load(0x402159, 40), cast_to=bytes).strip(b'\0')

def test():
    assert main() == b'a_Little_b1t_harder_plez@flare-on.com'

if __name__ == '__main__':
    print(main())

```

日志如下：

```python
ubuntu@ubuntu:~/Desktop/angr$  export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/angr$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/angr$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/angr$ python 1.py
WARNING | 2020-06-20 03:20:16,888 | angr.state_plugins.symbolic_memory | The program is accessing memory or registers with an unspecified value. This could indicate unwanted behavior.
WARNING | 2020-06-20 03:20:16,888 | angr.state_plugins.symbolic_memory | angr will cope with this by generating an unconstrained symbolic variable and continuing. You can resolve this by:
WARNING | 2020-06-20 03:20:16,888 | angr.state_plugins.symbolic_memory | 1) setting a value to the initial state
WARNING | 2020-06-20 03:20:16,888 | angr.state_plugins.symbolic_memory | 2) adding the state option ZERO_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to make unknown regions hold null
WARNING | 2020-06-20 03:20:16,888 | angr.state_plugins.symbolic_memory | 3) adding the state option SYMBOL_FILL_UNCONSTRAINED_{MEMORY_REGISTERS}, to suppress these messages.
WARNING | 2020-06-20 03:20:16,889 | angr.state_plugins.symbolic_memory | Filling register ebp with 4 unconstrained bytes referenced from 0x401084 (offset 0x1084 in very_success (0x401084))
WARNING | 2020-06-20 03:20:16,890 | angr.state_plugins.symbolic_memory | Filling register edi with 4 unconstrained bytes referenced from 0x40108a (offset 0x108a in very_success (0x40108a))
WARNING | 2020-06-20 03:20:16,891 | angr.state_plugins.symbolic_memory | Filling register esi with 4 unconstrained bytes referenced from 0x40108b (offset 0x108b in very_success (0x40108b))
WARNING | 2020-06-20 03:20:16,903 | angr.state_plugins.symbolic_memory | Filling register 10 with 2 unconstrained bytes referenced from 0x4010ad (offset 0x10ad in very_success (0x4010ad))
b'a_Little_b1t_harder_plez@flare-on.com'
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

flag{a_Little_b1t_harder_plez@flare-on.com}

