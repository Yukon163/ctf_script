> 文章整合：
>
> [https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/](https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/)
>
> [https://baijiahao.baidu.com/s?id=1665277270769279870&wfr=spider&for=pc](https://baijiahao.baidu.com/s?id=1665277270769279870&wfr=spider&for=pc)
>

# 0x01 前言
在了解栈溢出后，我们再从原理和方法两方面深入理解基本ROP。

# 0x02 什么是ROP
ROP的全称为Return-oriented programming（返回导向编程），这是一种高级的内存攻击技术可以用来绕过现代操作系统的各种通用防御（比如内存不可执行和代码签名等）。**通过上一篇文章栈溢出漏洞原理详解与利用，我们可以发现栈溢出的控制点是ret处**，**<font style="color:#F5222D;">那么ROP的核心思想就是利用以ret结尾的指令序列把栈中的应该返回EIP的地址更改成我们需要的值，从而控制程序的执行流程。</font>**

# 0x03 为什么要ROP
探究原因之前，我们先看一下什么是NX(DEP) NX即No-execute（不可执行）的意思，**<font style="color:#F5222D;">NX（DEP）的基本原理是将数据所在内存页标识为不可执行，当程序溢出成功转入shellcode时，程序会尝试在数据页面上执行指令，此时CPU就会抛出异常，而不是去执行恶意指令。</font>****随着 NX 保护的开启，以往直接向栈或者堆上直接注入代码的方式难以继续发挥效果。**所以就有了各种绕过办法，rop就是一种。

ROP(Return Oriented Programming)，其主要思想是在栈**<font style="color:#F5222D;">缓冲区溢出的基础上</font>**，**利用程序中已有的小片段( gadgets )来改变某些寄存器或者变量的值，从而控制程序的执行流程。****<font style="color:#F5222D;">所谓gadgets 就是以 ret 结尾的指令序列，</font>**通过这些指令序列，我们可以修改某些地址的内容，方便控制程序的执行流程。

之所以称之为 ROP，是因为核心在于利用了指令集中的 ret 指令，改变了指令流的执行顺序。

**<font style="color:#F5222D;">ROP 攻击一般得满足如下条件</font>**

+ 程序存在溢出，并且可以控制返回地址。
+ 可以找到满足条件的 gadgets 以及相应 gadgets 的地址。

如果 gadgets 每次的地址是不固定的，那我们就需要想办法动态获取对应的地址了。

# 0x04 基本ROP
**基本的ROP有：**ret2text**、**ret2shellcode、ret2syscall、ret2libc

详细的将在下一节进行介绍

