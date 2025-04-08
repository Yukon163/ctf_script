> github：[https://github.com/sashs/Ropper](https://github.com/sashs/Ropper)
>
> 官方网站：[https://scoding.de/ropper/](https://scoding.de/ropper/)
>

# 安装
> 注意：以下命令均在angr的python虚拟环境中安装
>

1. pip3 install capstone
2. pip3 install filebytes
3. pip3 install keystone-engine
4. pip3 install pyvex
5. git clone git[://github.com/sashs/Ropper](https://github.com/sashs/Ropper)
6. cd Ropper && python3 setup.py install

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636534424375-c3cf2a13-952c-4b76-9386-e4fc433b4a60.png)

# 各个功能的介绍
接下来我们详细的介绍一下ropper的各个功能。关于各个功能的命令可以使用<help commands>进行查看

## arch
如果ropper识别的可执行文件架构不正确，则可以使用arch命令手动对加载后的文件架构进行设置：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636534506824-4ba4294e-26a5-4a31-afdb-b81317ce824d.png)

## asm
将汇编指令转为对应的机器码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636534626637-e151b09d-0579-4340-a209-84f66cdca13a.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636534806174-bf0eb2af-4292-489c-87d2-5c8c78e917fa.png)

这个命令中-a参数是可选的，如未设置将会使用加载文件时ropper识别到的程序架构进行转换。支持转换的架构如下：

```bash
[ERROR] Architecture is not supported: sub
Supported architectures are: x86, x86_64, MIPS, MIPS64, ARM, ARMTHUMB, ARM64, PPC, PPC64, SPARC64
```

还可以对输出进行格式化，含义详见参考上面的“help asm”命令：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636535048477-9c0603ed-c75b-4ef8-a6a2-5a5520a8eea0.png)

## badbytes
相当于设置“坏字符（坏字节）”。在有的程序中的输入是不允许某些特殊字符传入的，我们将这些“特殊字符”称之为坏字节。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636535287599-04c67b34-0cd5-4b9d-916f-4614466b4c0c.png)

## clearcache
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636535399843-ffeb24cc-d328-4f31-923d-66227133d4e2.png)

当ropper运行时会在当前用户的目录下生成一个名为.ropper的隐藏文件夹，里面存放有ropper运行时的一些缓存数据：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636535481638-123e16b0-855a-4fd1-8f7d-f064845626a9.png)

当解析的数据发生异常则可以使用clearcache命令对缓存进行清除：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636535574843-aeb869cb-1b78-4532-9cac-37e291e31e2e.png)

## close
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636535656224-19c9322f-1e3c-4876-bdfa-a32de5e7f262.png)

ropper一次性可以加载多个文件，当某个可执行文件使用不到时可以使用close命令对打开的可执行文件进行关闭。

## color
打开或关闭ropper的终端彩色效果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636535796927-a5f6b2db-5904-499d-a6c7-3d4fcec04489.png)

这个功能或许对视障人士可能有所帮助。

## detailed
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636536006789-1a9f2dff-5eeb-4df2-b3f1-6500cd662bb7.png)

是否详细输出gadget的信息，该选项默认为off：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636536280677-0a5a8108-3303-499c-a58d-0e4b25310792.png)

> 该选项只对gadgets命令生效。
>

## disasm
将机器码转为汇编指令：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636536541668-6cfbde62-2503-4812-bd91-0a10a22ad630.png)

> 与asm选项不同的是该选项似乎并没有支持其他架构如MIPS，由于我没有MIPS可执行文件无法进行测试。
>

## disasm_address
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636536779451-4c0be06a-9cd2-4976-b998-a9af5c41c118.png)

获取某地址处的汇编指令，可以使用额外的参数L指定获取该地址之前或之后的L-1条汇编指令；如未指定L参数则只会返回该地址处的汇编指令：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636537313367-81edadef-bf6c-4c73-8075-1f8086a739d3.png)

该命令获取的汇编指令不一定正确，如：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636537406962-4a0a0a26-8a6a-47cb-b10e-751112c0a297.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636537431483-6de12a12-5c72-421a-b417-7a2b4be61840.png)

甚至有时候解析的地址发生漂移：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636537549714-d459be01-8f18-437e-801c-a19863f3b39a.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636537523001-e3af07bd-e132-4bc2-a41f-53ecbf31f9c5.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636537684836-15d6bb23-af21-4d77-8872-a33a0d397387.png)

> 0x8006e1本身就是个无效地址...
>

## file
使用file命令加载文件，一个ropper中可以加载多个可执行文件。

## gadgets
显示可执行文件中的gadgets：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636539013813-3759e20d-65e5-4518-b5cf-2a16071c6de8.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636539040740-be3cdf22-29de-4303-b6c8-35aee160cccc.png)

## help
显示ropper内置的帮助文件。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636539082289-7fb39637-20f3-402c-9d0b-869a5bd27f81.png)

## hex
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636539135237-d904adca-3868-421a-ae36-45c7c2e98da3.png)

打印可执行文件中对应section的hex，可以使用show sections显示可执行文件中的section：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636539237766-b3ddd5da-6982-4bff-abc3-bf222f4d1da8.png)

可以使用hex命令查看section对应的16进制编码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636539437715-5e58b4ce-0616-424b-8bda-c3cb09674ef8.png)

## imagebase
设置ropper中可执行文件的基地址，该设置对其他的命令起效：

```powershell
(test/ELF/x86_64)> imagebase
[INFO] Imagebase reseted
(test/ELF/x86_64)> jmp eax



JMP Instructions
================


0x0000000000400625: jmp rax; 
0x0000000000400673: jmp rax; 
0x00000000004006be: call rax; 

3 gadgets found
########################################################################################
(test/ELF/x86_64)> imagebase 0x0
[INFO] Imagebase set to 0x0
(test/ELF/x86_64)> jmp eax



JMP Instructions
================


0x0000000000000625: jmp rax; 
0x0000000000000673: jmp rax; 
0x00000000000006be: call rax; 

3 gadgets found
(test/ELF/x86_64)>
```

## inst
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636539771082-73edbad1-55ff-4940-9e1a-37bbc99bddc4.png)

在代码段中搜索某条汇编指令的地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636540193567-cbd84013-186a-46e7-bc31-224b516ada6b.png)

## jmp
查看能跳转到某个寄存器存放地址处的汇编指令：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636542471250-e0fb1b9f-036d-417a-8980-318fc8b962bb.png)

## load
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636542529568-cc2f7644-5fd9-4b51-91ab-757e27740015.png)

对所有在ropper中加载的可执行文件加载gadget，如果没有all参数则会加载当前文件中的gadget。

> 暂时不清楚该命令的作用。
>

## opcode
在可执行文件中搜索符合条件的opcode：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636543286011-fff6ee4f-72e9-47e6-84df-841a1edaa077.png)

## ppr
返回符合pop pop ret类型的gadget：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636543499750-d637bf84-8ed8-486d-9fa3-e30d0392dab0.png)

## quit
退出ropper：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636543543144-0cb892df-e313-4efd-8969-2c02ec62b602.png)

## ropchain
生成符合条件的rop链，在后续的文章中我们会详细介绍：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636543631133-05c0c442-9238-427f-b570-b6521b42de6d.png)

比如产生执行到execve的rop链：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636543674867-c2ba18c1-16e0-43f5-abb7-2478c0954f2c.png)

似乎这个rop链的生成有问题...

## search
寻找符合条件的汇编指令：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1636545984669-9cde7001-e776-4d18-91fb-10b923988dc8.png)









