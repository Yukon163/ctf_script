对于angr来说，执行到正确的路径并不难，但对于我们来说，要想正确的打印出flag，恐怕还得废一番功夫。

这里以`asisctffinals2015_fake`为例。

[https://github.com/angr/angr-doc/tree/master/examples/asisctffinals2015_fake](https://github.com/angr/angr-doc/tree/master/examples/asisctffinals2015_fake)

下载下来，将文件载入到IDA中，来到main函数，查看伪代码：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592300333607-f92b3994-e1f3-4b57-b4d6-0aee5de52680.png)

这是什么玩意儿。。。

从题目来看，其大概逻辑是通过输入正确的值，经过计算，最后会输出由`v5 v6 v7 v8 v9`所组成的字符串，也就是flag。

可以看看程序运行的过程:

```bash
ubuntu@ubuntu:~/Desktop/angr$ ./fake 123
��3
ubuntu@ubuntu:~/Desktop/angr$ ./fake 1234567890
BٜLx�r�c����^��l�#��-Y�dh��I��|�
```

就此题而言，仅仅设置BVS和find是远远不够的(对输入进行约束)，因为我们也不知道输出的flag究竟是什么，因此需要对结果进行条件约束，从而打印出正确的flag。

我们跳过前面的命令行输入部分，直接从`0x4004AC`开始，因为`**<font style="color:#F5222D;">strtol</font>**`**<font style="color:#F5222D;">用于将字符串转化为整数</font>**，而**<font style="color:#F5222D;">我们通过</font>**`**<font style="color:#F5222D;">claripy.BVS</font>**`**<font style="color:#F5222D;">构造的符号变量是一个bit向量</font>**，无法使用`strtol`转换。当然如果你不闲麻烦，可以将`strtol`nop掉，然后使用之前所说的命令行传参的方法，这里就不nop了

初始化状态如下设置：

> state = p.factory.blank_state(addr=0x4004AC)
>

<font style="color:#1A1A1A;">这会创建一个 blank_state 对象，这个对象里面很多东西都是未初始化的，当程序访问未初始化的数据时，会返回一个不受约束的符号量</font>

> **使用人话来说，因为在初始化BVS之前输入是空白的状态，并且跳过了strtol函数，因此要使用p.factory.blank_state(addr=0x4004AC)**
>

**blank->形容词，空白的**

```python
state = p.factory.blank_state(addr=0x4004AC)
inp = state.solver.BVS('inp', 8*8)
state.regs.rax = inp

simgr= p.factory.simulation_manager(state)
simgr.explore(find=0x400684)
found = simgr.found[0]
```

接下来创建了一个名称为 `inp`，长度为 8*8bit = 8bytes 的位向量符号，并将其值赋值给 `rax`，**<font style="color:#F5222D;">因为调用</font>****<font style="color:#F5222D;">函数(</font>****strtol****<font style="color:#F5222D;">)</font>****<font style="color:#F5222D;">后的返回值是依赖 </font>**`**<font style="color:#F5222D;">rax</font>**`**<font style="color:#F5222D;"> 返回的，</font>**<font style="color:#000000;">要保证寄存器不会错乱，如下图所示：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592301736700-38b4343c-d9ef-4f8c-a643-5933739fe300.png)

在我们设置好 explore 和 found 之后，它会停在 0x400684。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592300863842-f9209360-ea89-4308-a191-fe971f54b016.png)

此时的状态是`0x400684`时，`put`将要打印`edi`寄存器的值.

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592302350339-fdb3ae66-4f66-472c-a33b-5b15e8d994fd.png)

为了对结果设置条件约束，我们需要如下设置：

```python
flag_addr = found.regs.rdi
found.add_constraints(found.memory.load(flag_addr, 5) == int(binascii.hexlify(b"ASIS{"), 16))
```

> constraints 名词->限定，约束
>
> binascii.hexlify作用是返回的二进制数据的十六进制表示。每个字节的数据转换成相应的 2 位十六进制表示。因此产生的字符串是原数据的**<font style="color:#F5222D;">两倍长度</font>**
>

这里添加的约束是从 flag_addr 载入的 5bytes 大小的地址中的内容是否和 ASIS{ 一致。

根据题目条件可以知道flag的长度应该为38(5+32+1)字节，并且的前5个字节是`ASIS{`,最后一个字节是`}`其余也都应该是可打印字符,这时可以进行如下约束：

```python
flag = found.memory.load(flag_addr, 40)
    for i in range(5, 5+32):
        cond_0 = flag.get_byte(i) >= ord('0')
        cond_1 = flag.get_byte(i) <= ord('9')
        cond_2 = flag.get_byte(i) >= ord('a')
        cond_3 = flag.get_byte(i) <= ord('f')
        cond_4 = found.solver.And(cond_0, cond_1)
        cond_5 = found.solver.And(cond_2, cond_3)
        found.add_constraints(found.solver.Or(cond_4, cond_5))
```

> **<font style="color:#F5222D;">可以使用found.memory.load方法来提取内存中的字符串</font>**
>

这里就是添加约束了，看起来还蛮好理解的。分别是限制为数字和字母。接下来我们再添加最后一个限制，以 `}` 结尾：

```python
found.add_constraints(flag.get_byte(32+5) == ord('}'))
```

最后将结果通过`eval`输出即可.

`flag_str = found.solver.eval(flag, cast_to=bytes)`

> 实际上，放置较少的约束（例如，仅约束前几个字符）足以获取最终的flag，并且如果约束较少，则 z3 的运行速度更快。我添加了所有约束，只是为了安全起见。
>

接下来我们用 `eval` 方法找到 flag 并输出：

```python
flag_str = found.solver.eval(flag, cast_to=bytes)
print(flag_str.rstrip(b'\0'))
```

> ## 描述
> Python rstrip() 删除 string 字符串末尾的指定字符（默认为空格）.
>
> ## 语法
> rstrip()方法语法：
>

> <font style="color:#000000;">str</font><font style="color:#666600;">.</font><font style="color:#000000;">rstrip</font><font style="color:#666600;">([</font><font style="color:#000000;">chars</font><font style="color:#666600;">])</font>
>

> ## 参数

> + chars -- 指定删除的字符（默认为空格）
>

> ## 返回值

> 返回删除 string 字符串末尾的指定字符后生成的新字符串。
>

即可得到输出值:

b'ASIS{f5f7af556bd6973bd6f2687280a243d9}'

完整脚本如下:

```python
import angr
import binascii

def main():
    p = angr.Project("fake", auto_load_libs=False)

    state = p.factory.blank_state(addr=0x4004AC)
    inp = state.solver.BVS('inp', 8*8)
    state.regs.rax = inp

    simgr= p.factory.simulation_manager(state)
    simgr.explore(find=0x400684)
    found = simgr.found[0]

    # We know the flag starts with "ASIS{"
    flag_addr = found.regs.rdi
    found.add_constraints(found.memory.load(flag_addr, 5) == int(binascii.hexlify(b"ASIS{"), 16))

    # More constraints: the whole flag should be printable
    flag = found.memory.load(flag_addr, 40)
    for i in range(5, 5+32):
        cond_0 = flag.get_byte(i) >= ord('0')
        cond_1 = flag.get_byte(i) <= ord('9')
        cond_2 = flag.get_byte(i) >= ord('a')
        cond_3 = flag.get_byte(i) <= ord('f')
        cond_4 = found.solver.And(cond_0, cond_1)
        cond_5 = found.solver.And(cond_2, cond_3)
        found.add_constraints(found.solver.Or(cond_4, cond_5))

    # And it ends with a '}'
    found.add_constraints(flag.get_byte(32+5) == ord('}'))

    # In fact, putting less constraints (for example, only constraining the first 
    # several characters) is enough to get the final flag, and Z3 runs much faster 
    # if there are less constraints. I added all constraints just to stay on the 
    # safe side.

    flag_str = found.solver.eval(flag, cast_to=bytes)
    return flag_str.rstrip(b'\0')

    #print("The number to input: ", found.solver.eval(inp))
    #print("Flag:", flag)

    # The number to input:  25313971399
    # Flag: ASIS{f5f7af556bd6973bd6f2687280a243d9}

def test():
    a = main()
    assert a == b'ASIS{f5f7af556bd6973bd6f2687280a243d9}'

if __name__ == '__main__':
    import logging
    logging.getLogger('angr.sim_manager').setLevel(logging.DEBUG)
    print(main())
```



