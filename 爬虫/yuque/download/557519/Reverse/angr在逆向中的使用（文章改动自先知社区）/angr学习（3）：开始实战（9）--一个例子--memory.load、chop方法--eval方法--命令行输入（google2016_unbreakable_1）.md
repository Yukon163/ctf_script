[https://github.com/angr/angr-doc/tree/master/examples/google2016_unbreakable_1](https://github.com/angr/angr-doc/tree/master/examples/google2016_unbreakable_1)

老规矩先载入IDA中，看看main流程：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592726019251-2c0355e8-aede-4ad3-99c2-1d12efef72f1.png)

上来就call了一堆的函数，2333

看了一下官方的py，比较麻烦，我们用之前的方法就可以解决（通过命令行输入）

```bash
p = angr.Project('unbreakable',load_options={"auto_load_libs": False})

argv = claripy.BVS("argv",0x43*8)

state = p.factory.entry_state(args={"./unbreakable",argv},add_options={angr.options.LAZY_SOLVES})
state.libc.buf_symbolic_bytes=0x43 + 1

for byt in argv.chop(8):
    state.add_constraints(state.solver.And(byt >= ord(' '),byt <= ord('~')))
```

其中的`state.libc.buf_symbolic_bytes=0x43 + 1`是非常有必要的，我看官方所说，**<font style="color:#F5222D;">angr默认的</font>**`**<font style="color:#F5222D;">symbolic_bytes</font>**`**<font style="color:#F5222D;">只有60bytes，对于这题来说太小了。也就是说如果命令行传入的大小大于默认的值，所以需要手动调整大小。</font>**

<font style="color:#4C4948;">这里添加了一个 </font>`LAZY_SOLVES`<font style="color:#4C4948;"> 选项，查看</font>[文档](https://docs.angr.io/appendix/options)<font style="color:#4C4948;">可以知道这是一个“除非绝对必要，否则不要检查可满足性”（Don’t check satisfiability until absolutely necessary）的选项。这个选项可以加快分析的速度，而且只有在路径分析完之后才会检查可满足性，如果没有加载这个选项的话，很有可能会路径爆炸</font>

而且条件约束也是十分有必要的，这里说明一下`chop`方法：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592726717559-f1dbe2be-ba94-4499-a6ca-71f2d05120dd.png)

意思就是**<font style="color:#F5222D;">截取</font>**，所以我们每8bits（英文字母和数字每个占8bit）截取，然后进行条件约束。

**<font style="color:#F5222D;">state.memory.load：</font>**（从某个地址中加载位字节）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592727566546-f2fd446a-556b-48b7-8fbf-5ecb3457beb4.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592728936226-da0f02b8-8ab7-4085-bb17-ae26da54fb80.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592728877625-036f2b28-bd5e-4764-b8ad-e5816739c295.png)

完整脚本如下：

```python
import angr
import claripy

AVOID_ADDR = 0x400850 # address of function that prints wrong
FIND_ADDR = 0x400830 # address of function that prints correct
INPUT_ADDR = 0x6042c0 # location in memory of user input
INPUT_LENGTH = 0xf2 - 0xc0 + 1 # derived from the first and last character
                               # reference in data

def extract_memory(state):
    """Convience method that returns the flag input memory."""
    return state.solver.eval(state.memory.load(INPUT_ADDR, INPUT_LENGTH), cast_to=bytes)

def main():
    p = angr.Project('unbreakable',load_options={"auto_load_libs": False})

    argv = claripy.BVS("argv",0x43*8)

    state = p.factory.entry_state(args={"./unbreakable",argv},add_options={angr.options.LAZY_SOLVES})
    state.libc.buf_symbolic_bytes=0x43 + 1

    for byt in argv.chop(8):
        state.add_constraints(state.solver.And(byt >= ord(' '),byt <= ord('~')))


    ex = p.factory.simulation_manager(state)


    ex.explore(find=(FIND_ADDR,), avoid=(AVOID_ADDR,))

    flag = extract_memory(ex.found[0]) # ex.one_found is equiv. to ex.found[0]

    print(flag)

if __name__ == '__main__':
    main()
```

日志如下：

```python
ubuntu@ubuntu:~/Desktop/angr$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/angr$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/angr$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/angr$ python 1.py
WARNING | 2020-06-21 01:35:34,225 | angr.state_plugins.symbolic_memory | The program is accessing memory or registers with an unspecified value. This could indicate unwanted behavior.
WARNING | 2020-06-21 01:35:34,225 | angr.state_plugins.symbolic_memory | angr will cope with this by generating an unconstrained symbolic variable and continuing. You can resolve this by:
WARNING | 2020-06-21 01:35:34,225 | angr.state_plugins.symbolic_memory | 1) setting a value to the initial state
WARNING | 2020-06-21 01:35:34,225 | angr.state_plugins.symbolic_memory | 2) adding the state option ZERO_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to make unknown regions hold null
WARNING | 2020-06-21 01:35:34,225 | angr.state_plugins.symbolic_memory | 3) adding the state option SYMBOL_FILL_UNCONSTRAINED_{MEMORY_REGISTERS}, to suppress these messages.
WARNING | 2020-06-21 01:35:34,225 | angr.state_plugins.symbolic_memory | Filling memory at 0x7fffffffffefff8 with 150 unconstrained bytes referenced from 0x1000000 (strncpy+0x0 in extern-address space (0x0))
b'CTF{0The1Quick2Brown3Fox4Jumped5Over6The7Lazy8Fox9}'
(angr) ubuntu@ubuntu:~/Desktop/angr$ 

```

flag：CTF{0The1Quick2Brown3Fox4Jumped5Over6The7Lazy8Fox9}

