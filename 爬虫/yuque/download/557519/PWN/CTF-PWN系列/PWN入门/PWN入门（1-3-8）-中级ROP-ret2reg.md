> 摘自：[https://blog.csdn.net/acsuccess/article/details/104465113](https://blog.csdn.net/acsuccess/article/details/104465113)
>
> [https://blog.csdn.net/linyt/article/details/43612409](https://blog.csdn.net/linyt/article/details/43612409)
>

前面介绍的攻击方法，EIP注入的地址必须是一个确定地址，否则无法攻击成功，为了与本文介绍的攻击方法形成比对，我将前面的方法称为ret2addr（return-to-address，返回到确定地址执行的攻击方法）。

安全人员为保护免受ret2addr攻击，想到了一个办法，那就是地址混淆技术。该述语英文称为 Address Space Layout Randomization，直译为地址随机化。该技术将栈，堆和动态库空间全部随机化。在32位系统上，随机量在64M范围；而在64位系统，它的随机量在2G范围，因此原来的ret2addr技术无法攻击成功。

很快攻击者想到另一种攻击方法ret2reg，即return-to-register，返回到寄存地址执行 的攻击方法。

此攻击方法之所以能成功，是因为函数内部实现时，溢出的缓冲区地址通常会加载到某个寄存器上，在后在的运行过程中不会修改。尽管栈空间具有随机性，但该寄存器的值与缓冲区地址的关系是确定的，在随机地址之上，建立了必然的地址关系。一句话就是 在随机性上找到地址的确定性关系。

### 原理
1. 查看栈溢出返回时哪个寄存器指向缓冲区空间。
2. 查找对应的call 寄存器或者jmp 寄存器指令，将EIP设置为该指令地址。
3. 将寄存器所指向的空间上注入shellcode（确保该空间是可以执行的，通常是栈上的）

#### 利用思路
+ 分析和调试汇编，查看溢出函数返回时哪个寄存器指向缓冲区地址
+ 向寄存器指向的缓冲区中注入shellcode
+ 查找call 该寄存器或者jmp 该寄存器指令，并将该指令地址覆盖ret

#### 防御方法
在函数ret之前，将所有赋过值的寄存器全部复位，清0，以避免此类漏洞

### Example
此类漏洞常见于strcpy字符串拷贝函数中。

> 网上没有合适的例子，以及ret2reg比较简单，因此具体内容略
>

