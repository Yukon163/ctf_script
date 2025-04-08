**参考资料：**[http://www.manongjc.com/article/68188.html](http://www.manongjc.com/article/68188.html)

此篇文章翻译自：[https://docs.angr.io/](https://docs.angr.io/)

# Angr Documentation
# ①导入angr模块以及加载二进制程序
```python
>>> import angr
>>> proj = angr.Project('/bin/true')
```

# ②了解导入的二进制程序的基本信息
```python
>>> proj.arch #架构
>>> proj.entry #二进制程序入口点
>>> proj.filename #程序名称以及位置
```

# ③二进制程序在虚拟地址空间的表示
```python
>>> proj.loader#是通过CLE模块将二进制对象加载并映射带单个内存空间
>>> proj.loader.min_addr#proj.loader 的低位地址
>>> proj.loader.max_addr#proj.loader 的高位地址
>>> proj.loader.all_objects #CLE加载的对象的完整列表
>>> proj.loader.shared_objects#这是一个从共享对象名称到对象的字典映射
>>> proj.loader.all_elf_objects#这是从ELF文件中加载的所有对象
>>> proj.loader.all_pe_objects#加载一个windows程序
>>> proj.loader.main_object#加载main对象
>>> proj.loader.main_object.execstack#这个二进制文件是否有可执行堆栈
>>> proj.loader.main_object.pic#这个二进制位置是否独立
>>> proj.loader.extern_object#这是“externs对象”，我们使用它来为未解析的导入和angr内部提供地址
>>> proj.loader.kernel_object#此对象用于为模拟的系统调用提供地址
>>> proj.loader.find_object_containing(0x400000)#获得对给定地址的对象的引用
```

直接与这些对象交互以从中提取元数据

```python
>>> obj = proj.loader.main_object#指向一个对象
>>> obj.entry#获取地址
>>> obj.min_addr, obj.max_addr#地址的地位和高位
>>> obj.segments#检索该对象的段
>>> obj.sections#检索该对象的节
>>> obj.find_segment_containing(obj.entry)#通过地址获得单独的段
>>> obj.find_section_containing(obj.entry)#通过地址获得单独的节
>>> addr = obj.plt['abort']#通过符号获取地址
>>> obj.reverse_plt[addr]#通过地址获取符号
>>> obj.linked_base
>>> obj.mapped_base#显示对象的预链接基以及CLE实际映射到内存中的位置
```

```python
>>> malloc = proj.loader.find_symbol('malloc')#接受一个名称或地址并返回一个符号对象
>>> malloc.name#获取符号名称
>>> malloc.owner_obj
>>> malloc.rebased_addr#全局地址空间中的地址
>>> malloc.linked_addr#相对于二进制的预链接基的地址
>>> malloc.relative_addr#相对于对象库的地址
 
>>> malloc.is_export
>>> malloc.is_import#这两个判断符号是import还是export
 
>>> main_malloc = proj.loader.main_object.get_symbol("malloc")#不同于loader上的符号查找，在单个对象上，通过get_symbol获取给定名称的符号。
>>> main_malloc.resolvedby#提供了对用于解析符号的符号的引用
```

 注意：proj = angr.Project('example',load_options={"auto_load_libs":False})

auto_load_libs，支持或禁用CLE自动解析共享库依赖关系的尝试，并且默认为on。

except_missing_libs为true，当二进制文件有无法解析的共享库依赖项时，将引发异常。

将字符串列表传递给force_load_libs，所列出的内容将作为未解析的共享库依赖项处理，

将字符串列表传递给skip_libs，以防止将该名称的任何库解析为依赖项。

main_opts是一个从选项名到选项值的映射，

lib_opts是一个从库名到字典的映射，将选项名映射到选项值。

> 例：angr.Project(main_opts={'backend': 'ida', 'arch': 'i386'}, lib_opts={'libc.so.6': {'backend': 'elf'}})<font style="background-color:transparent;"> </font>
>



angr.sim_procedure#替换对库函数的外部调用，就是模仿库函数对状态的影响的python函数

```python
>>> stub_func = angr.SIM_PROCEDURES['stubs']['ReturnUnconstrained'] #这是一个类
>>> proj.hook(0x10000, stub_func())#与类的实例挂钩
>>> proj.is_hooked(0x10000)#是否挂钩
>>> proj.unhook(0x10000)
>>> proj.hooked_by(0x10000)#这三条均是一些验证性的指令
```

```python
>>> proj.hook(0x20000, length=5)
... def my_hook(state):
... state.regs.rax = 1
```

#通过使用project .hook(addr)作为函数装饰器，可以指定现成函数作为钩子使用。还可以选择指定length关键字参数，使执行在钩子完成后向前跳转一些字节。

```python
>>> proj.is_hooked(0x20000)
True
```

使用proj.hook_symbol(name, hook)，它提供了一个符号的名称作为第一个参数，用于钩住该符号所在的地址

# ④：factory
为了方便分析，foctory提供了几个常用的函数

## 4.1 Block：用于从给定地址提取基本代码块，angr以基本块为单位分析代码。。
```python
>>> block = proj.factory.block(proj.entry)#从程序的入口点提取一段代码
>>> block.pp()  #打印代码块
>>> block.instructions#该代码块共有多少条指令
>>> block.instruction_addrs#每条指令的地址
>>> block.capstone#capstone disassembly
>>> block.vex#VEX IRSB(这是python的内部地址，不是程序地址)
```

## 4.2 States：proj = angr.Project('/bin/true')
这仅仅是一个初始化映像，但是要执行符号执行，还需要simstate，表示模拟程序状态的特定对象

```python
>>> state = proj.factory.entry_state()#即就是simstate，SimState包含程序的内存、寄存器、文件系统数据……任何可以通过执行更改的“实时数据”均在SimState。
```

.entry_state（）的替换：

.blank_state()#构造了一个“空白石板”空白状态，其大部分数据未初始化。

full_init_state()构造一个状态，该状态可以通过需要在主二进制的入口点之前运行的任何初始化程序执行，例如共享库构造函数或预初始化程序。

.call_state()构造准备执行给定函数的状态。

```python
>>> s = proj.factory.blank_state()
>>> s.memory.store(0x4000, s.solver.BVV(0x0123456789abcdef0123456789abcdef, 128))#使用.memory.store(addr,val)方法将数据保存在内存中
>>> s.memory.load(0x4004, 6) #
 
>>> state.regs.rip#获取当前指令指针
>>> state.regs.rax
>>> state.regs.rbp = state.regs.rsp#将寄存器rsp的值给rbp
>>> state.mem[proj.entry].int.resolved#将入口点的内存解释为C int
```

注意：那些不是python int 型!那些是bitvectors式，因此需要对其进行置换。

```python
>>> state.mem[0x1000].uint64_t = state.regs.rdx#将rdx的值存储在内存的0x1000位置
>>> state.regs.rbp = state.mem[state.regs.rbp].uint64_t.resolved#放弃rbp
>>> state.regs.rax += state.mem[state.regs.rsp + 8].uint64_t.resolved#加rax
 
>>> bv = state.solver.BVV(0x1234, 32)#创建一个32位宽，值为0x1234的bitvectors，
>>> y = state.solver.BVS("y", 64)#创建一个名为“y”的位向量符号，长度为64位
```

在位数相同的情况下，可以实现对符号的计算

```python
>>> state.solver.eval(bv)  #转换成python int
>>> state.regs.rsi = state.solver.BVV(3, 64)#将64位宽，值为3的bitvectors存入寄存器和内存
>>> state.mem[0x1000].long = 4#您可以直接存储python int，它将被转换成适当大小的位向量
>>> state.mem[0x1000].long.resolved
```

注意，mem可以通过.resolved，来以bitvectors获取该值；也可以通过.concrete，来以python int获取该值

一个通过符号值来求解的过程，注意仅适用于bit向量

```python
>>> state = proj.factory.entry_state()
>>> input = state.solver.BVS('input', 64)
>>> operation = (((input + 4) * 3) >> 1) + input
>>> output = 200
>>> state.solver.add(operation == output)
>>> state.solver.eval(input)
0x3333333333333381
```

注意：eval是一种通用方法，它可以将任何位向量转换成python原语

上面的BVS是bit向量，下面的通过FPV来创建浮点型向量

```python
>>> a = state.solver.FPV(3.2, state.solver.fp.FSORT_DOUBLE)
```

raw_to_bv和raw_to_fp方法将位向量解释为浮点数，反之亦然: 

solver.eval(expression)#将为给定的表达式提供一种可能的解决方案。

solver.eval_one(expression)#将给出给定表达式的解决方案，如果可能有多个解决方案，则抛出一个错误。

solver.eval_upto(expression, n)#将给出给定表达式的n个解，如果可能返回的结果小于n，则返回的结果小于n。

solver.eval_atleast(expression, n)#将为给定的表达式提供n个解决方案，如果可能小于n，则抛出一个错误。

solver.eval_exact(expression, n)#将为给定的表达式提供n个解决方案，如果少于或大于可能，则抛出错误。

solver.min(expression) #将给出给定表达式的最小可能解。

solver.max(expression) #将给出给定表达式的最大可能解。

其他关键词：

extra_constraints：可以作为约束的元组传递。

cast_to可以传递一个数据类型来转换结果。

## 4.3  Simulation Managers 模拟管理器
```python
>>> simgr = proj.factory.simulation_manager(state)#首先，我们创建将要使用的模拟管理器。构造函数可以接受状态或状态列表。
state被组织成stash，可以forward, filter, merge, and move 。
>>> simgr.active#用于存储操作
>>> simgr.step()#执行一个基本块的符号执行，即就是所有状态向前推进一个基本块
>>> simgr.active##更新存储
 
>>> while len(simgr.active) == 1:#直到第一个符号分支，并查看两个存储
... simgr.step()
>>> simgr
<SimulationManager with 2 active>
>>> simgr.active
[<SimState @ 0x400692>, <SimState @ 0x400699>]
 
>>> simgr.run()#直接执行程序，直到一切结束，查看会返回死循环数目
>>> simgr
<SimulationManager with 3 deadended>
 
>>> simgr.move(from_stash='deadended', to_stash='authenticated', filter_func=lambda s: b'Welcome' in s.posix.dumps(1))#,move(start，end，optional)，可以将start状态的optional信息移动到end状态
>>> simgr
<SimulationManager with 2 authenticated, 1 deadended>
```

一些存储的类型:

active#此存储区包含默认情况下将逐步执行的状态，除非指定了备用存储区。

deadended#当一个状态由于某种原因不能继续执行时，包括没有任何有效指令、所有后续的未sat状态或无效的指令指针，它就会进入死区隐藏。

pruned#当在lazy_resolve存在的情况下发现一个状态未sat时，将遍历该状态层次结构，以确定在其历史上，它最初何时成为unsat。所有这一观点的后裔州(也将被取消sat，因为一个州不能成为取消sat)都将被修剪并放入这一储备中。

unconstrained#无约束的状态(即，由用户数据或其他符号数据来源控制的指令指针)放在这里。

unsat#不可满足的状态(即，它们有相互矛盾的约束，比如输入必须同时为“AAAA”和“BBBB”)。

 

.explore()#方法：

查找到达某个地址的状态，同时丢弃经过另一个地址的所有状态

```python
>>> proj = angr.Project('examples/CSCI-4968MBE/challenges/crackme0x00a/crackme0x00a')
>>> simgr = proj.factory.simgr()
>>> simgr.explore(find=lambda s: b"Congrats" in s.posix.dumps(1))#匹配到赢得方法
```

## 4.4 Analyses 用于程序分析过程
```python
>>> p.analyses
```

p.analyses.BackwardSlice        

p.analyses.Reassembler

p.analyses.BinDiff               

p.analyses.StaticHooker

p.analyses.BinaryOptimizer      

p.analyses.VFG

p.analyses.BoyScout              

p.analyses.VSA_DDG

p.analyses.CDG                   

p.analyses.VariableRecovery

p.analyses.CFB                  

p.analyses.VariableRecoveryFast

p.analyses.CFBlanket            

p.analyses.Veritesting

p.analyses.CFG                   

p.analyses.discard_plugin_preset

p.analyses.CFGAccurate           

p.analyses.get_plugin

p.analyses.CFGFast               

p.analyses.has_plugin

p.analyses.CalleeCleanupFinder   

p.analyses.has_plugin_preset

p.analyses.CallingConvention     

p.analyses.plugin_preset

p.analyses.CongruencyCheck       

p.analyses.project

p.analyses.DDG                   

p.analyses.register_default

p.analyses.Disassembly           

p.analyses.register_plugin

p.analyses.GirlScout             

p.analyses.register_preset

p.analyses.Identifier           

p.analyses.release_plugin

p.analyses.LoopFinder            

p.analyses.reload_analyses

p.analyses.ReachingDefinitions   

p.analyses.use_plugin_preset

# ⑤ 插件
state.globals实现了标准python dict的接口，允许您在状态上存储任意数据。

state.history存储关于状态在执行过程中所采取的路径的历史数据,实际上是由几个历史节点组成的链表，每个节点代表一轮执行——使用state.history.parent.parent遍历这个列表

history.description#是在状态上执行的每一轮执行的字符串描述的列表。

history.bbl_addrs#是由状态执行的基本块地址的列表

history.jumpkinds#是状态历史中每个控制流转换的处理的列表

history.guards#是保护状态遇到的每个分支的条件的列表。

history.events#是执行过程中发生的“有趣事件”的语义列表，如出现符号跳转条件、程序弹出消息框或执行以退出代码结束。

history.actions#通常为空，但如果添加了angr.options.refs选项，它将弹出一个日志，记录程序执行的所有内存、寄存器和临时值访问。

state.callstack跟踪模拟程序的调用堆栈

callstack.func_addr#当前正在执行的函数的地址

callstack.call_site_addr#调用当前函数的基本块的地址

callstack.call_site_addr#从当前函数开始的堆栈指针的值

callstack.call_site_addr#如果当前函数返回，返回的位置

此外，还有其他的插件

# ⑥ 其他
## 1.符号引擎
failure engine#故障引擎

syscall engine#系统调用引擎

hook engine#钩子引擎

unicorn engine#project.factory.successors(state, **kwargs)#依次尝试所有引擎的代码

## 2.断点
```python
>>> import angr
>>> b = angr.Project('examples/fauxware/fauxware')
>>> s = b.factory.entry_state()#获取状态
>>> s.inspect.b('mem_write')#以下3条都是插入断点
>>> s.inspect.b('mem_write', when=angr.BP_AFTER, action=debug_func)
>>> s.inspect.b('mem_write', when=angr.BP_AFTER, action=angr.BP_IPYTHON)
```

断点总结：

mem_read#正在读取内存。

mem_write#正在写内存。

reg_read#正在读取寄存器。

reg_write#正在写取寄存器。

tmp_read#正在读取临时变量。

tmp_write#正在写取临时变量。

expr#正在创建一个表达式

statement#正在翻译IR语句。

instruction#正在翻译一条新的指令

irsb#一个新的基本块正在被翻译。

constraints#新的约束被添加到状态中。

exit#从执行中生成一个后继。

symbolic_variable#正在创建一个新的符号变量。

call#调用指令被命中。

address_concretization#正在解析符号内存访问

同时，这些类型还有不同的属性，见 [https://docs.angr.io/core-concepts/simulation](https://docs.angr.io/core-concepts/simulation)

