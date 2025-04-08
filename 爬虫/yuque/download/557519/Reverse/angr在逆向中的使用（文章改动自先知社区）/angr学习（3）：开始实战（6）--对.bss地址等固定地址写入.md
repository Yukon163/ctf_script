

**<font style="color:#F5222D;">对于.bss段等固定地址的变量我们可以利用直接claripy地址写入，进行state初始化。</font>**

下面我通过一个例子进行简单说明。

例题来自于sym-write:[https://github.com/angr/angr-doc/tree/master/examples/sym-write](https://github.com/angr/angr-doc/tree/master/examples/sym-write)

将文件下载下来之后,载入IDA,来的main函数:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592360580176-f06ffab1-81dd-4ba3-b0ca-fe2dffdf12c2.png)

看一下它的伪代码吧:

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  _BOOL4 v3; // eax
  signed int i; // [esp+0h] [ebp-18h]
  int v6; // [esp+4h] [ebp-14h]
  int v7; // [esp+8h] [ebp-10h]
  unsigned int v8; // [esp+Ch] [ebp-Ch]

  v8 = __readgsdword(0x14u);
  v6 = 0;
  v7 = 0;
  for ( i = 0; i <= 7; ++i )
  {
    v3 = ((u >> i) & 1) != 0;
    ++*(&v6 + v3);
  }
  if ( v6 == v7 )
    printf("you win!");
  else
    printf("you lose!");
  return 0;
}
```

这里是根据u的值来决定程序跳转的方向,其中的变量u我们双击进去看一下:

> 请注意，输入u的地方并不在main函数
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592360743150-5cca42cb-1ac4-422e-9992-e673072a68d6.png)

**<font style="color:#F5222D;">为了写入符号地址，我们在初始化 </font>**`**<font style="color:#F5222D;">simulation_manager</font>**`**<font style="color:#F5222D;"> 的 </font>**`**<font style="color:#F5222D;">state</font>**`**<font style="color:#F5222D;"> 时需要添加参数 </font>**`**<font style="color:#F5222D;">add_options={"SYMBOLIC_WRITE_ADDRESSES"}</font>**`**<font style="color:#F5222D;">。</font>**

```python
state = p.factory.entry_state(add_options={angr.options.SYMBOLIC_WRITE_ADDRESSES})
```

**<font style="color:#F5222D;">其中变量</font>**`**<font style="color:#F5222D;">u</font>**`**<font style="color:#F5222D;">位于</font>**`**<font style="color:#F5222D;">.bss</font>**`**<font style="color:#F5222D;">段，是</font>****<font style="color:#F5222D;">未初始化的变量</font>****<font style="color:#F5222D;">，我们可以在</font>**`**<font style="color:#F5222D;">state</font>**`**<font style="color:#F5222D;">状态，初始化</font>**`**<font style="color:#F5222D;">simulation_manager</font>**`**<font style="color:#F5222D;">的</font>**`**<font style="color:#F5222D;">state</font>**`**<font style="color:#F5222D;">时，将其设置。</font>**

```python
sm = p.factory.simulation_manager(state)
```



**<font style="color:#F5222D;">angr提供了</font>**`**<font style="color:#F5222D;">SimMemory</font>**`**<font style="color:#F5222D;">类对内存进行操作:</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592361136516-47634e9e-67ff-4778-879b-97dda5cf23ee.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592361138075-63f3579f-9ca4-4367-a057-b291c0513775.png)<font style="color:#333333;">并且提供了两种方法:</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592361289076-919416a6-adaa-40b9-a257-58ea9c360e4c.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592361290558-548e34ee-d474-405c-babe-1b5ecc922d4f.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592361300514-6cf2b49e-6961-4cb1-b82d-d86df88edbd1.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592361301967-cff7c966-3d87-4b34-97e2-5bf11ea9e0d9.png)

<font style="color:#4C4948;">接下来创建 </font>`u`<font style="color:#4C4948;"> 的位向量符号并写入内存：</font>

```python
u = claripy.BVS("u", 8)
state.memory.store(0x804a021, u)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592361393530-b39004c9-239f-4805-984c-6b1fa51d07dd.png)这里用到了 `store` 方法，向 bss 段中的该地址写入了符号 `u`就可以正常创建 `simulation manager` 了。

接下来就是设置 `find` 和 `avoid` 了.

然后设置需要到达的路径即可

`sm.explore(find=0x80484e3, avoid=0x80484f5)`

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592361393499-4f176407-1c75-4449-8704-d0c86d8e8cd2.png)

然后打印出来即可:sm.found[0].solver.eval(u)

整理一下脚本:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import angr
import claripy
 #新建一个工程，导入二进制文件，issue就是文件的名字，后面的选项是选择不自动加载依赖项
p = angr.Project('./issue', load_options={"auto_load_libs": False})#加载二进制程序

#创建一个SimState对象，这也就是我们进行符号执行的核心对象，包括了符号信息、内存信息、寄存器信息等
state = p.factory.entry_state(add_options={angr.options.SYMBOLIC_WRITE_ADDRESSES})
#add_options={angr.options.SYMBOLIC_WRITE_ADDRESSES}是为了写入符号地址需要添加参数

#创建一个符号变量，这个符号变量以8位bitvector形式存在，名称为u
u = claripy.BVS("u", 8)#通过claripy.BVS构造的符号变量是一个bit向量

#把符号变量保存到指定的地址中，这个地址是和二进制文件相关联的，使用IDA打开，此地址对应的.bss段全局变量u的地址
state.memory.store(0x804a021, u)#这里用到了 store 方法，向 bss 段中的该地址写入了符号u

#创建一个Simulation Manager对象，这个对象和我们的状态有关系
sm = p.factory.simulation_manager(state)
sm.explore(find=0x80484e3, avoid=0x80484f5)
print(sm.found[0].solver.eval(u))#打印u的结果

'''
根据官方的解释，我们可以知道第37行sm.explore(find=0x80484e3, avoid=0x80484f5)的含义是，
寻找到满足correct条件且不满足wrong条件的state，即我们最终所要的校验成功的state。
获得到state之后，运行state.solver.eval(u)求解u的值。
'''

```

> <font style="color:#4D4D4D;">在Angr中，我们使用state表示程序（二进制文件）的运行状态，这个状态机就包括内存、寄存器等。在Angr 7.9.2.21的API文档中，对entry_state函数的定义如下：</font>
>
> entry_state(**kwargs)
>
> 返回一个代表着程序入口点的state对象。所有的参数都是可选的。
>

> 参数： .addr-state开始的程序地址（非入口点）
>

>    .initial_prefix-如果提供了这个参数，所有的符号化寄存器以及符号变量的名字前面都带有此字符串
>

>    .fs-一个字典，字典的键为文件名，值为SimFile对象
>

>    .concrete_fs-boolean；指明了在打开文件时，主文件系统是否应该被询问
>

>    .chroot- 一个伪造的root路径，和真实chroot指令等效。只有在concrete_fs为True时生效
>

>    .argc- 程序所需要的argc。可以是int或者bitvector。如果不提供，默认为args的长度
>

>    .args- 程序所需要的参数列表。可以是string或者bitvector
>

>    .env- 字典；用于指明程序运行环境，键和值都可以是strings或者bitvector
>

> 返回值：初始状态
>

> 返回类型：SiMState
>

> 
>

保存为1.py运行一下:

```python
(angr) ubuntu@ubuntu:~/Desktop/angr$ python 1.py
WARNING | 2020-06-16 20:28:40,192 | angr.state_plugins.symbolic_memory | The program is accessing memory or registers with an unspecified value. This could indicate unwanted behavior.
WARNING | 2020-06-16 20:28:40,193 | angr.state_plugins.symbolic_memory | angr will cope with this by generating an unconstrained symbolic variable and continuing. You can resolve this by:
WARNING | 2020-06-16 20:28:40,193 | angr.state_plugins.symbolic_memory | 1) setting a value to the initial state
WARNING | 2020-06-16 20:28:40,193 | angr.state_plugins.symbolic_memory | 2) adding the state option ZERO_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to make unknown regions hold null
WARNING | 2020-06-16 20:28:40,193 | angr.state_plugins.symbolic_memory | 3) adding the state option SYMBOL_FILL_UNCONSTRAINED_{MEMORY_REGISTERS}, to suppress these messages.
WARNING | 2020-06-16 20:28:40,193 | angr.state_plugins.symbolic_memory | Filling register edi with 4 unconstrained bytes referenced from 0x8048521 (__libc_csu_init+0x1 in issue (0x8048521))
WARNING | 2020-06-16 20:28:40,195 | angr.state_plugins.symbolic_memory | Filling register ebx with 4 unconstrained bytes referenced from 0x8048523 (__libc_csu_init+0x3 in issue (0x8048523))
29
(angr) ubuntu@ubuntu:~/Desktop/angr$
```

实际上,答案不只是29这一个,在文章的最末尾可以看看官方的代码,下面看看官方代码中的部分语句

```python
def correct(state):
    try:
        return b'win' in state.posix.dumps(1)
    except:
        return False

def wrong(state):
    try:
        return b'lose' in state.posix.dumps(1)
    except:
        return False
```

也就是根据输出判断正确性。当然我们也可以硬编码，但是根据输出判断可能会对一些开启地址随机化的题目有所帮助。

接下来输出即可，它的输出可能会有很多解。

官方的完整脚本如下:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: xoreaxeaxeax
Modified by David Manouchehri <manouchehri@protonmail.com>
Original at https://lists.cs.ucsb.edu/pipermail/angr/2016-August/000167.html
The purpose of this example is to show how to use symbolic write addresses.
"""

import angr
import claripy

def main():
	p = angr.Project('./issue', load_options={"auto_load_libs": False})

	# By default, all symbolic write indices are concretized.
	state = p.factory.entry_state(add_options={angr.options.SYMBOLIC_WRITE_ADDRESSES})

	u = claripy.BVS("u", 8)
	state.memory.store(0x804a021, u)

	sm = p.factory.simulation_manager(state)

	def correct(state):
		try:
			return b'win' in state.posix.dumps(1)
		except:
			return False
	def wrong(state):
		try:
			return b'lose' in state.posix.dumps(1)
		except:
			return False

	sm.explore(find=correct, avoid=wrong)

	# Alternatively, you can hardcode the addresses.
	# sm.explore(find=0x80484e3, avoid=0x80484f5)

	return sm.found[0].solver.eval_upto(u, 256)


def test():
	good = set()
	for u in range(256):
		bits = [0, 0]
		for i in range(8):
			bits[u&(1<<i)!=0] += 1
		if bits[0] == bits[1]:
			good.add(u)

	res = main()
	assert set(res) == good

if __name__ == '__main__':
	print(repr(main()))
```

运行结果:

```python
(angr) ubuntu@ubuntu:~/Desktop/angr$ python 1.py
WARNING | 2020-06-16 20:21:13,363 | angr.state_plugins.symbolic_memory | The program is accessing memory or registers with an unspecified value. This could indicate unwanted behavior.
WARNING | 2020-06-16 20:21:13,363 | angr.state_plugins.symbolic_memory | angr will cope with this by generating an unconstrained symbolic variable and continuing. You can resolve this by:
WARNING | 2020-06-16 20:21:13,363 | angr.state_plugins.symbolic_memory | 1) setting a value to the initial state
WARNING | 2020-06-16 20:21:13,363 | angr.state_plugins.symbolic_memory | 2) adding the state option ZERO_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to make unknown regions hold null
WARNING | 2020-06-16 20:21:13,363 | angr.state_plugins.symbolic_memory | 3) adding the state option SYMBOL_FILL_UNCONSTRAINED_{MEMORY_REGISTERS}, to suppress these messages.
WARNING | 2020-06-16 20:21:13,363 | angr.state_plugins.symbolic_memory | Filling register edi with 4 unconstrained bytes referenced from 0x8048521 (__libc_csu_init+0x1 in issue (0x8048521))
WARNING | 2020-06-16 20:21:13,365 | angr.state_plugins.symbolic_memory | Filling register ebx with 4 unconstrained bytes referenced from 0x8048523 (__libc_csu_init+0x3 in issue (0x8048523))
[51, 57, 240, 60, 75, 139, 78, 197, 23, 142, 90, 29, 209, 154, 99, 212, 163, 102, 108, 166, 172, 105, 169, 114, 120, 53, 178, 184, 71, 135, 77, 83, 89, 141, 147, 86, 92, 153, 150, 156, 202, 101, 165, 43, 113, 226, 46, 177, 116, 232, 180, 45, 58, 198, 195, 201, 15, 85, 204, 30, 149, 210, 27, 39, 216, 106, 225, 170, 228, 54]
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```



