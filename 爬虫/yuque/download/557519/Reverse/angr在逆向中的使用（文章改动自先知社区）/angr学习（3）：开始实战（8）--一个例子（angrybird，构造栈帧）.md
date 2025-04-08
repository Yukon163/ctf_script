常见寄存器

寄存器	     16位	32位 64位

累加寄存器	AX	EAX	RAX

基址寄存器	BX	EBX	RBX

计数寄存器	CX	ECX	RCX

数据寄存器	DX	EDX	RDX

堆栈基指针	BP	EBP	RBP

变址寄存器	SI	ESI	RSI

堆栈顶指针	SP	ESP	RSP

指令寄存器	IP	EIP	RIP

下载链接：[https://github.com/angr/angr-doc/tree/master/examples/codegate_2017-angrybird](https://github.com/angr/angr-doc/tree/master/examples/codegate_2017-angrybird)

首先将文件下载下来，载入到IDA中，大致看一下main的流程：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592701715582-d4d54d89-c414-4eca-bbd1-f9aaed6ceb25.png)

2333，什么鬼东西，不过angr最喜欢的就是这种线性结构

在虚拟机中尝试运行一下，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592702031176-972e04c3-abab-47af-9a6e-ad805d7a6828.png)

程序无法运行起来？查看main函数的流程图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592702135788-964b3f5c-2e44-4284-99f1-150c2ba506d6.png)

学过汇编的都知道，xor eax eax->eax=0；cmp eax,0->ZF=1（寄存器标志位，zero flag）；jz即零标志为1就跳转。

因此，开头就是一个反调试，i了i了。

遇到反调试我们通常用patch的方法绕过，比如jz改为jnz。但是在这里，我们要使用angr进行解决，所以这里就不进行patch。

这里多说一句，反编译什么都看不出来：

```c
void __fastcall main(int a1, char **a2, char **a3)
{
  unsigned __int64 v3; // [rsp+78h] [rbp-8h]

  v3 = __readfsqword(0x28u);
  exit(a1);
}
```

接下来我们看一下反调试下面的流程：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592702710780-4101d4b2-e4a1-4f03-8c7d-e6b346b011f2.png)

单独摘出来看一下：

```plain
mov     [rbp+var_70], offset off_606018
mov     [rbp+var_68], offset off_606020
mov     [rbp+var_60], offset off_606028
mov     [rbp+var_58], offset off_606038
mov     eax, 0
call    sub_4006F6 //puts("you should return 21 not 1 :(")
mov     [rbp+n], eax
mov     eax, 0
call    sub_40070C // puts("stack check");
mov     eax, 0
call    sub_40072A //strncmp((const char *)&off_606038, "hello", 5uLL);
mov     rdx, cs:stdin   ; stream
mov     ecx, [rbp+n]
lea     rax, [rbp+s]
mov     esi, ecx        ; n
mov     rdi, rax        ; s
call    _fgets
movzx   edx, [rbp+s]
movzx   eax, [rbp+var_4F]
xor     eax, edx
mov     [rbp+var_30], al
movzx   eax, [rbp+var_30]
cmp     al, 0Fh
jg      short loc_400803
```

+ 第一段的call    sub_4006F6要求返回 21，但是函数会返回 1；
+ 第二段会尝试引用不存在的地址；
+ 第三段会将 `__lib_start_main` 地址上的值与 `hello` 进行比较

这几处全都是反调试当然，用了 angr 之后我们可以不关心这些（不需要手动 patch），

我们可以从 0x4007C2 开始（mov rdx, cs:stdin   ; stream，即，标准输入接收数据开始执行）。当然，从这里开始的话我们需要设置一些值。

首先我们先来看一下栈上面的情况：

```bash
.text:0000000000400781                 mov     [rbp+var_70], offset off_606018
.text:0000000000400789                 mov     [rbp+var_68], offset off_606020
.text:0000000000400791                 mov     [rbp+var_60], offset off_606028
.text:0000000000400799                 mov     [rbp+var_58], offset off_606038
```

<font style="color:#4C4948;">它们其实是把一部分函数表的值载入到了栈上：</font>

```bash
.got.plt:0000000000606008 qword_606008    dq 0                    ; DATA XREF: sub_400570↑r
.got.plt:0000000000606010 qword_606010    dq 0                    ; DATA XREF: sub_400570+6↑r
.got.plt:0000000000606018 off_606018      dq offset strncmp       ; DATA XREF: _strncmp↑r
.got.plt:0000000000606018                                         ; main+20↑o
.got.plt:0000000000606020 off_606020      dq offset puts          ; DATA XREF: _puts↑r
.got.plt:0000000000606020                                         ; main+28↑o
.got.plt:0000000000606028 off_606028      dq offset __stack_chk_fail
.got.plt:0000000000606028                                         ; DATA XREF: ___stack_chk_fail↑r
.got.plt:0000000000606028                                         ; main+30↑o
.got.plt:0000000000606030 off_606030      dq offset printf        ; DATA XREF: _printf↑r
.got.plt:0000000000606038 off_606038      dq offset __libc_start_main
.got.plt:0000000000606038                                         ; DATA XREF: ___libc_start_main↑r
.got.plt:0000000000606038                                         ; sub_40072A+8↑o ...
.got.plt:0000000000606040 off_606040      dq offset fgets         ; DATA XREF: _fgets↑r
.got.plt:0000000000606048 off_606048      dq offset exit          ; DATA XREF: _exit↑r
```

同时为了执行程序还应该设置mov rbp, rsp，这几步是必不可少的，因为跳过反调试，需要一定的代价。

因此初始化部分代码如下

```python
	state.regs.rbp = state.regs.rsp
    # this is the length for the read
    state.mem[state.regs.rbp - 0x74].int = 0x40 
    # using the same values as the binary doesn't work for these variables, I
    # think because they point to the GOT and the binary is using that to try
    # to fingerprint that it's loaded in angr. Setting them to pointers to
    # symbolic memory works fine.
    state.mem[state.regs.rbp - 0x70].long = 0x1000
    state.mem[state.regs.rbp - 0x68].long = 0x1008
    state.mem[state.regs.rbp - 0x60].long = 0x1010
    state.mem[state.regs.rbp - 0x58].long = 0x1018
```

注，main函数的一开始我们可以查到

```plain
var_70= qword ptr -70h
var_68= qword ptr -68h
var_60= qword ptr -60h
var_58= qword ptr -58h
```

按照它的注释，这是因为：

> 对于这些变量，使用与二进制文件相同的值不起作用，我认为是因为它们指向 GOT，而二进制文件则使用该值来尝试识别它在 angr 中加载的指纹。将它们设置为指向符号存储器的指针可以正常工作。
>

然而我尝试把它们修改成 0x0, 0x8, 0x10, 0x18，发现它们一样可以工作；我又试着修改成 0x20xx，发现也可以；可以将原作者关于state.mem[state.regs.rbp - 0x70].long = 0x1000的四条语句都注释掉，还是可以得到正确的结果。它们的 Warning 虽然大同小异，但很有可能最开始就没设置为正确的值。或许我们初始化为某些值可能就可以输出正确的答案，而注释中的原因可能是站不住脚的。

同时我们发现与以往套路中的符号执行多了一个语句：state.regs.rbp = state.regs.rsp

这是由于main函数的起始语句包括：push    rbp 和 mov rbp, rsp

接下来，对于 `_fgets` 函数：

```c
char *fgets(char *s, int n, FILE *stream)
{
  return fgets(s, n, stream);
}
```

它的参数 `esi` 向前可追溯到 `[rbp+n]`。而通过 `.text:00000000004007AB mov [rbp+n], eax和sub_4006F6，`因为sub_4006F6函数返回的要求必须为21，可以猜测它的值为 21。

最后，再简单的完成最后的步骤就行了：

```python
    sm = proj.factory.simulation_manager(state)  # Create the SimulationManager.
    sm.explore(find=FIND_ADDR)  # This will take a couple minutes. Ignore the warning message(s), it's fine.
    found = sm.found[-1]
    flag = found.posix.dumps(0)

    # This trims off anything that's not printable.
    return flag[:20]
```

官方完整脚本如下：

```python
#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: David Manouchehri
# Runtime: ~3 minutes

import angr

START_ADDR = 0x4007c2
FIND_ADDR = 0x404fab  # This is right before the printf

def main():
    proj = angr.Project('angrybird')
    # There's a couple anti-run instructions in this binary.
    # Yes, anti-run. That's not a typo.

    # Because I'm not interested in fixing a weird binary, I'm going to skip
    # all the beginning of the program.
    # this also skips a bunch of initialization, so let's fix that:
    state = proj.factory.entry_state(addr=START_ADDR)
    state.regs.rbp = state.regs.rsp
    # this is the length for the read
    state.mem[state.regs.rbp - 0x74].int = 0x40

    # using the same values as the binary doesn't work for these variables, I
    # think because they point to the GOT and the binary is using that to try
    # to fingerprint that it's loaded in angr. Setting them to pointers to
    # symbolic memory works fine.
    state.mem[state.regs.rbp - 0x70].long = 0x1000
    state.mem[state.regs.rbp - 0x68].long = 0x1008
    state.mem[state.regs.rbp - 0x60].long = 0x1010
    state.mem[state.regs.rbp - 0x58].long = 0x1018

    sm = proj.factory.simulation_manager(state)  # Create the SimulationManager.
    sm.explore(find=FIND_ADDR)  # This will take a couple minutes. Ignore the warning message(s), it's fine.
    found = sm.found[-1]
    flag = found.posix.dumps(0)

    # This trims off anything that's not printable.
    return flag[:20]

def test():
    assert main() == b'Im_so_cute&pretty_:)'

if __name__ == '__main__':
    print(main())
```

日志如下：

```bash
ubuntu@ubuntu:~/Desktop/angr$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/angr$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/angr$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/angr$ python 1.py
WARNING | 2020-06-20 19:18:39,374 | angr.state_plugins.symbolic_memory | The program is accessing memory or registers with an unspecified value. This could indicate unwanted behavior.
WARNING | 2020-06-20 19:18:39,374 | angr.state_plugins.symbolic_memory | angr will cope with this by generating an unconstrained symbolic variable and continuing. You can resolve this by:
WARNING | 2020-06-20 19:18:39,374 | angr.state_plugins.symbolic_memory | 1) setting a value to the initial state
WARNING | 2020-06-20 19:18:39,374 | angr.state_plugins.symbolic_memory | 2) adding the state option ZERO_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to make unknown regions hold null
WARNING | 2020-06-20 19:18:39,374 | angr.state_plugins.symbolic_memory | 3) adding the state option SYMBOL_FILL_UNCONSTRAINED_{MEMORY_REGISTERS}, to suppress these messages.
WARNING | 2020-06-20 19:18:39,375 | angr.state_plugins.symbolic_memory | Filling memory at 0x1018 with 1 unconstrained bytes referenced from 0x400a33 (PLT.__gmon_start__+0x443 in angrybird (0x400a33))
WARNING | 2020-06-20 19:18:40,292 | angr.state_plugins.symbolic_memory | Filling memory at 0x1000 with 1 unconstrained bytes referenced from 0x400c49 (PLT.__gmon_start__+0x659 in angrybird (0x400c49))
WARNING | 2020-06-20 19:18:40,824 | angr.state_plugins.symbolic_memory | Filling memory at 0x1008 with 1 unconstrained bytes referenced from 0x400e3e (PLT.__gmon_start__+0x84e in angrybird (0x400e3e))
WARNING | 2020-06-20 19:18:40,926 | angr.state_plugins.symbolic_memory | Filling memory at 0x101c with 1 unconstrained bytes referenced from 0x400e97 (PLT.__gmon_start__+0x8a7 in angrybird (0x400e97))
WARNING | 2020-06-20 19:18:41,365 | angr.state_plugins.symbolic_memory | Filling memory at 0x1011 with 1 unconstrained bytes referenced from 0x401037 (PLT.__gmon_start__+0xa47 in angrybird (0x401037))
WARNING | 2020-06-20 19:18:41,955 | angr.state_plugins.symbolic_memory | Filling memory at 0x100a with 1 unconstrained bytes referenced from 0x401207 (PLT.__gmon_start__+0xc17 in angrybird (0x401207))
WARNING | 2020-06-20 19:18:44,897 | angr.state_plugins.symbolic_memory | Filling memory at 0x101b with 1 unconstrained bytes referenced from 0x401a98 (PLT.__gmon_start__+0x14a8 in angrybird (0x401a98))
WARNING | 2020-06-20 19:18:47,577 | angr.state_plugins.symbolic_memory | Filling memory at 0x1019 with 1 unconstrained bytes referenced from 0x402240 (PLT.__gmon_start__+0x1c50 in angrybird (0x402240))
WARNING | 2020-06-20 19:18:49,001 | angr.state_plugins.symbolic_memory | Filling memory at 0x101a with 1 unconstrained bytes referenced from 0x40270b (PLT.__gmon_start__+0x211b in angrybird (0x40270b))
b'Im_so_cute&pretty_:)'
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

flag{Im_so_cute&pretty_:)}

