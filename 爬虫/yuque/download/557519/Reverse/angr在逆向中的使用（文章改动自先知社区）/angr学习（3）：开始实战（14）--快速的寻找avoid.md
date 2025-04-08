# 前言
就我感觉angr比较适合用来解决混淆的题目，面对混淆题去混淆感觉自己能力不够，直接动态调试，又觉得非常浪费时间，那么这时angr可以成为非常好的帮手。

## 如何快速的寻找find和avoid
在解题时我们时常会遇到带有强混淆的程序，这类程序要找出所有的find和avoid是一件耗时耗力的事情，那么我们可以采取何种高效的办法进行寻找呢？

这里以`hackcon2016_angry-reverser`为例。

[https://github.com/angr/angr-doc/tree/master/examples/hackcon2016_angry-reverser](https://github.com/angr/angr-doc/tree/master/examples/hackcon2016_angry-reverser)

IDA载入

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593228982233-2c66aadb-bec3-4de9-b7da-f4b016cd375b.png)

很明显的混淆，如果自己分析一遍，然后去除混淆也是需要费点时间的，不过如果你掌握了angr，那么只需要几分钟就可以解决此题，根本不要关心其使用了何种加密方式。

此题中，正确的路径只有一条`find=0x405a6e`,需要避免的路径则有很多，我们可以通过如下代码，得到所有需要avoid的地址。

```plain
e = open('./yolomolo', 'rb').read()
avoids = []
index = 0
while True:
    index = e.find(b'\xB9\x00\x00\x00\x00',index+1)
    if index == -1:
        break
    addr = 0x400000 + index
    avoids.append()
print (len(avoids))
print (avoids)
```

其中`\xB9\x00\x00\x00\x00`是`mov ecx 0`的机器码，因此完整代码可以如下组织：

```python
import angr
import claripy
def main():
    flag    = claripy.BVS('flag', 20*8, explicit_name=True)
    buf     = 0x606000
    crazy   = 0x400646
    find    = 0x405a6e
    e = open('./yolomolo', 'rb').read()
    avoids = []
    index = 0
    while True:
        index = e.find(b'\xB9\x00\x00\x00\x00',index+1)
        if index == -1:
            break
        addr = 0x400000 + index
        avoids.append(addr)
    proj = angr.Project('./yolomolo')
    state = proj.factory.blank_state(addr=crazy, add_options={angr.options.LAZY_SOLVES})
    state.memory.store(buf, flag, endness='Iend_BE')
    state.regs.rdi = buf
    for i in range(19):
        state.solver.add(flag.get_byte(i) >= 0x30)
        state.solver.add(flag.get_byte(i) <= 0x7f)
    simgr = proj.factory.simulation_manager(state)
    simgr.explore(find=find, avoid=avoids)
    found = simgr.found[0]
    return found.solver.eval(flag, cast_to=bytes)
if __name__ in '__main__':
    import logging
    logging.getLogger('angr.sim_manager').setLevel(logging.DEBUG)
    print(main())
```

## 例题
其实angr最适合拿来解决线性的程序。

就比如说这题`ekopartyctf2016_rev250`

[https://github.com/angr/angr-doc/tree/master/examples/ekopartyctf2016_rev250](https://github.com/angr/angr-doc/tree/master/examples/ekopartyctf2016_rev250)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593228982141-f8b88029-cf36-4e4a-b54f-693bea998990.png)

如果去混淆，不一定能去除成功，如果动态调试，必定会耗费相当多的时间。如果你会使用angr，那么使用angr是在容易不过的事情了。

**<font style="color:#F5222D;">由于需要调用当前的动态库，我们可以这样运行</font>**`**<font style="color:#F5222D;">LD_LIBRARY_PATH=./ ./FUck_binary</font>**`

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593228982153-a627c122-b769-4627-9c53-79eca8f1f3dc.png)

OK，并不是命令行参数输入。

通过IDA，获取更多的信息。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593228982137-8ebd0210-bcba-446a-b948-8b90e606bde5.png)

最终的`find`应该在这里。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593228982215-61b00a40-c9f7-4560-865c-78a93152bdee.png)

需要避免的分支`0x403ABA`,`403A7E`等

我们可以通过之前提到过的方法提取出所有的`avoid`分支。

```plain
avoids = []
def get_avoids():
    file_bytes = open('./FUck_binary','rb').read()
    index = 0
    while True:
        index = file_bytes.find(b'\x66\x90',index+1)
        if index == -1:
            break
        if index < 0x3a7e:
            continue
        addr = 0x400000+index
        avoids.append(addr)
```

在对输入进行条件约束时我们可以这么组织，这是常用的限制可打印字符的方式。

`state.solver.And(c <= '~', c >= ' ')`

跑了一下结果还以为代码写错了，这答案也太让人摸不着头脑了。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593228982192-4dad9c77-f81c-44cf-bbfe-55f90ae27a3f.png)

代码如下：

```python
import angr
import claripy
BUF_LEN = 100
avoids = []
def get_avoids():
    file_bytes = open('./FUck_binary','rb').read()
    index = 0
    while True:
        index = file_bytes.find(b'\x66\x90',index+1)
        if index == -1:
            break
        if index < 0x3a7e:
            continue
        addr = 0x400000+index
        avoids.append(addr)
def main():
    p = angr.Project('FUck_binary')
    flag = claripy.BVS('flag', BUF_LEN*8)
    state = p.factory.entry_state(stdin=flag)
    for c in flag.chop(8):
        state.solver.add(state.solver.And(c <= '~', c >= ' '))
    ex = p.factory.simulation_manager(state)
    ex.explore(find=0x403a40,avoid=avoids)
    found = ex.found[0]
    print(found.posix.dumps(0))
if __name__ == '__main__':
    #main()
    get_avoids()
    main()
```

# 总结
> 既然选择了angr，便只顾风雨兼程
>

