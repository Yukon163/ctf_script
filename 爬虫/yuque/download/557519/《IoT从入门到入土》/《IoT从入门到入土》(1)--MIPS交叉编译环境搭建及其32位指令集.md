> 附件：链接: [https://pan.baidu.com/s/1RJZX6so7KBTPS_5qhr4WrA](https://pan.baidu.com/s/1RJZX6so7KBTPS_5qhr4WrA) 提取码: 3i9f
>

之前一直接触到的指令集是INTEL的x86，并没有接触过MIPS指令集，所以想趁着入门IoT的时间里将这两个指令集熟悉一下。当然了，大佬们看到这里就可以关闭这个网页了，因为下面记述的内容全部都是很基础的东西。

# 1、MIPS交叉编译环境搭建
本篇中使用的是截止到目前为止最新的ubuntu版本--`ubuntu 22.04 LTS`，kernel版本为`5.15.0-25`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657336115290-50b863eb-a66c-441e-b79b-de59e1434583.png)

实现交叉编译所需要的依赖库如下：

```c
#!/bin/sh

# qemu安装
sudo apt install qemu
sudo apt install qemu-system qemu-user-static binfmt-support

# 顺带也将ARM依赖库安装一下
sudo apt install libncurses5-dev gcc-arm-linux-gnueabi build-essential synaptic gcc-aarch64-linux-gnu

# mips依赖库
sudo apt-get install gcc-mips-linux-gnu
sudo apt-get install gcc-mipsel-linux-gnu
sudo apt-get install gcc-mips64-linux-gnuabi64
sudo apt-get install gcc-mips64el-linux-gnuabi64

#多架构（multiarch）gdb调试依赖
sudo apt install gdb-multiarch
```

使用的gdb为pwndbg和pwntools，安装方法就不再多说了。

# 2、MIPS交叉编译环境测试
安装完成之后我们对环境进行测试，测试代码如下：

```c
#include <stdio.h>
#include <unistd.h>

int main(){
	char buffer[0x10];
	printf("cyberangel\n");
	read(0,buffer,0x10);
	printf("%s",buffer);
	return 0;
}
```

## ①、测试编译环境
和x86相同，MIPS也分为大端序和小端序、32位和64位，编译不同类型的可执行文件所需要的命令如下：

+ 32位小端序：`mipsel-linux-gnu-gcc -g test.c -o test_mipsel_32`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657337128453-98a45359-f972-4cf1-ac4b-b2512a8b2d50.png)

+ 32位大端序：`mips-linux-gnu-gcc -g test.c -o test_mips_32`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657337180751-6d8b3bd3-0135-4870-abe2-76da4ff8d5f1.png)

+ 64位小端序：`mips64el-linux-gnuabi64-gcc -g test.c -o test_mipsel_64`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657337369812-f68c1ca4-fe97-4e0d-904c-d0bab99cf1ab.png)

+ 64位大端序：`mips64-linux-gnuabi64-gcc -g test.c -o test_mips_64`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657337483021-a433e28e-67bf-439c-ba93-2ba0e625922c.png)

编译出的文件保护均为开启Canary、半开RELRO，其他保护均为关闭状态。

## ②、测试qemu运行环境
可以挑选其中的`test_mipsel_32`使用qemu模拟运行，该可执行文件是动态链接，所以需要在运行时额外指定对应的动态链接库：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657345895016-f49b6497-014b-4baa-a74d-bfea82663a35.png)

ubuntu下依赖的动态链接库存放在`/usr/`目录下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657345945018-397bc909-5098-433f-bc5f-3e8fa94a4885.png)

# 3、32位MIPS指令集
## ①、MIPS寄存器
无论32位还是64位，在MIPS中均有32个`通用寄存器（General-Purpose Register）`，我们可以从$0到$31给他们编号，各个通用寄存器的详细信息如下表所示：

| 寄存器编号 | 名称 | 功能 |
| --- | --- | --- |
| $0 | $zero | `常量寄存器（Constant Value 0）`，永远为0 |
| $1 | $at | `汇编暂存器（Assembly Temporary）`，用于处理在加载16位以上的大常数时使用，编译器或汇编程序需要把大常数拆开，然后重新组合到寄存器里；除此之外程序员也可以显式的使用这个寄存器。 |
| $2 ~ $3 | $v0 ~ $v1 | 用于存储表达式或者函数返回的`值（value）` |
| $4 ~ $7 | $a0 ~ $a3 | 存放函数调用时的`参数（Arguments）` |
| $8 ~ $15 | $t0 ~ $t7 | 存放`临时变量（Temporary variable）` |
| $16 ~ $23 | $s0 ~ $s7 | `保存（Saved）`寄存器，在函数调用和返回时可能需要保存和恢复调用者寄存器的值。 |
| $24 ~ $25 | $t8 ~ $t9 | 同t0 ~ t7 |
| $26 ~ $27 | $k0 ~ $k1 | 使用编译器编译出来的程序不会使用这两个寄存器，这两个用于保存异常处理和中断的返回值，为操作系统`保留（Keep）`使用。 |
| $28 | $gp | `全局指针（Global Pointer）` |
| $29 | $sp | `栈指针（Stack Pointer）`，指向栈顶 |
| $30 | $fp/$s8 | $30可以当做第9个Saved寄存器`$s8`，也可以当做栈帧指针（Frame Pointer）`$fp`使用，这得看编译器的类型。 |
| $31 | $ra | 保存函数的`返回地址（Return Address）` |


> 笔者注：
>
> 1. 在x86指令集并没有寄存器编号这一说
> 2. $fp和x86的ebp/rbp还是不一样的，这一点我们之后会详细说明。
>

除了上面的通用寄存器之外还有其他的寄存器，这里只介绍其中的一小部分：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657421833003-c8ae8e5f-5e18-47c8-a89a-914c3f3bfc26.png)

MIPS架构最多支持4个`协处理器（Co-Processor）`，该架构强制要求存在协处理器CP0，因为MMU、异常处理、Cache控制、断点控制等功能都依赖于CP0实现：

+ `$sr`：全称`Status Register（状态寄存器）`，它位于CP0的Reg12，该寄存器可以反应CPU的状态以及控制CPU，下图中最显眼的是8个中断控制标志位`IM（Interrupt Mask）`和标识着处理器大小端的`RE（Reverse Endianess）`

| Table 9.1 Coprocessor 0 Registers in Numerical Order | | | | | |
| --- | --- | --- | --- | --- | --- |
| Register Number（寄存器号码） | Sel1 | Register Name（寄存器名称） | Function（功能） | Reference（可参考的资料） | Compliance Level |
| 12 | 0 | Status | Processor status and control | Section 9.20 on page 120 | Required |


![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657501062769-e16e0cd0-0e40-4b14-a3c6-3e1fc2e674cd.png)

在gdb中可以使用`p/x $sr`查看Status Register的值：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657501248234-d134c193-97bf-4a4a-ac38-77c30d5f18cd.png)

+ `$lo、$hi`：这两个寄存器用来存放`整数乘除法的结果`，可以使用`mthi`和`mtlo`指令对`$hi、$lo`寄存器进行操作。特别的，在除法计算中，`$lo`存放运算之后的商，而`$hi`寄存器存放余数。注意两者均不是通用寄存器，除了乘除法之外，不能用作其他的操作。
+ `$pc`：`Program Counter（程序计数器）`，类似于x86的eip，标志着当前要执行的指令。
+ `$f0 ~ $f31`表示`浮点寄存器（floating-point register）`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657506152939-61b0c81a-2e5d-45b1-83ef-2465e097ddca.png)

## ②、MIPS指令
```c
// 编译命令：mipsel-linux-gnu-gcc -g MIPSEL_32.c -o MIPSEL_32
#include <stdio.h>
#include <stdlib.h>

void funny_function(int var1,char* var2, \
    char* var3,char* var4,char* var5,float var6,void* var7,char var8[],char* var9){
    char buffer[0x100];
    sprintf(buffer,"%d%s%s%s%s%f%p%s%s",var1,var2,var3,var4,var5,var6,var7,var8,var9);
    
}
int main(){
    int var1 = 0xdeadbeef;
    char *var2 = "NYSEC-ChaMD5";
    char *var3 = "qemu-MIPS";
    char *var4 = "yuque.com/cyberangel";
    char *var5 = "www.cyberangel.cn";
    float var6 = 3.1415926;
    void *var7 = malloc(0x10);
    char var8[10] = "cyberangel";
    char *var9 = "www.cyberangel.cn";
    funny_function(var1,var2,var3,var4,var5,var6,var7,var8,var9);
    return 0;
}
```

将上面的代码编译后启动gdb以调试：`qemu-mipsel-static -L /usr/mipsel-linux-gnu -g 1234 ./MIPSEL_32`，也可以写一个gdb调试脚本：

```bash
file ./MIPSEL_32				# gdb加载可执行文件MIPSEL
set architecture mips		# 只需将架构设置为MIPS即可
b *0x4008A0						  # 对main开头函数下断点
target remote :1234
c												# 让程序执行到我们下的main函数断点
```

新建终端窗口，执行`gdb-multiarch -x leaf_function_MIPSEL_32_gdbscript.gdb`启动调试：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657359744437-77069a13-e0e7-4e71-bbbe-9552856cd526.png)

这里我们着重的讲解MIPS架构中一些常见的指令，main函数的第一段汇编如下：

```c
.text:004008A0 98 FF BD 27                   addiu   $sp, -0x68
.text:004008A4 64 00 BF AF                   sw      $ra, 0x60+var_s4($sp)
.text:004008A8 60 00 BE AF                   sw      $fp, 0x60+var_s0($sp)
.text:004008AC 25 F0 A0 03                   move    $fp, $sp
.text:004008B0 42 00 1C 3C 10 90 9C 27       li      $gp, (_GLOBAL_OFFSET_TABLE_+0x7FF0)
.text:004008B8 28 00 BC AF                   sw      $gp, 0x60+var_38($sp)
.text:004008BC 3C 80 82 8F                   la      $v0, __stack_chk_guard
.text:004008C0 00 00 42 8C                   lw      $v0, (__stack_chk_guard - 0x411088)($v0)
```

+ `addiu`：`add immediate unsigned`，即，为左侧操作数加上立即数，但与`addi`不同的是`addiu`不会检测最终结果是否溢出。举例：`addiu  $sp, -0x68`等价于`$sp = $sp - 0x68（伪C代码，赋值语句，下同）`。
+ `sw`：`store word`，将寄存器的值保存到某地址。举例：`sw  $ra, 0x60+var_s4($sp)`等价于`*($sp + 0x60 + var_s4) = $ra`。
+ `move`：英文本意，用于寄存器之间值的传递。举例：`move  $fp, $sp`等价于`$fp = $sp（赋值语句）`
+ `li`：`load <font style="color:rgb(51, 51, 51);">immediate</font>`，用于将立即数传送给寄存器。举例：`li  $gp, (_GLOBAL_OFFSET_TABLE_+0x7FF0)`等价于`$gp = (_GLOBAL_OFFSET_TABLE_+0x7FF0)`
+ `la`：`load address`，用于将地址传送至寄存器中, 多用于通过地址获取数据段中的地址。
+ `lw`：`load word`，从某地址加载一个word类型的值到寄存器中。举例：`lw  $gp, 0x10($fp)`等价于`$gp = *($fp + 0x10)`。

下面我们来调试验证：

| MIPS指令 | 指令牵扯到的寄存器 | 执行前 | 执行后 | 伪C语言形式 |
| --- | --- | --- | --- | --- |
| `addiu   $sp, -0x68` | + $sp：Stack Pointer | + `$sp == 0x40800028` | `$sp == 0x407fffc0` | `$sp = $sp - 0x68 == 0x40800028 - 0x68 == 0x407fffc0` |
| `sw      $ra, 0x60+var_s4($sp)` | + $ra：Return Address<br/>+ $sp：Stack Pointer | + `$ra == 0x3fdf47a4`<br/>+ `$sp == 0x407fffc0` | 不变 | `*($sp + 0x64) == *(0x40800024) = $ra`<br/>即，执行之后地址0x40800024下存放的数据为0x3fdf47a4 |
| `sw      $fp, 0x60+var_s0($sp)` | + $fp：Frame Pointer<br/>+ $sp：Stack Pointer | + `$fp == 0x40800028`<br/>+ `$sp == 0x407fffc0` | 不变 | `<font style="color:#E8323C;">*($sp + 0x60) == *(0x40800020) = $fp($s8) == 0x0</font>`<br/>即，执行之后地址0x40800020存放的数据为0x00000000 |
| `move    $fp, $sp` | + $fp：Frame Pointer<br/>+ $sp：Stack Pointer | + `$fp == 0x40800028`<br/>+ `$sp == 0x407fffc0` | `<font style="color:#E8323C;">$fp == 0x40800028（不变）</font>`<br/>`<font style="color:#E8323C;">$sp == 0x407fffc0（不变）</font>`<br/>`<font style="color:#E8323C;">$s8 == 0x407fffc0（$s8原值为0）</font>` | `$fp($s8) = $sp ` |
| `li      $gp, (_GLOBAL_OFFSET_TABLE_+0x7FF0)` | + $gp：Global Pointer | + `$gp == 0x3fface20` | `$gp == 0x419010` | `$gp = 0x411020 + 0x7FF0 == 0x419010` |
| `sw      $gp, 0x60+var_38($sp)` | + $gp：Global Pointer<br/>+ $sp：Stack Pointer | + `$gp == 0x419010`<br/>+ `$sp == 0x407fffc0` | 不变 | `*($sp + 0x28) == *(0x407fffe8) = $gp`<br/>即，执行之后地址0x407fffe8存放的数据为0x419010 |
| `la      $v0, __stack_chk_guard` | + $v0：Value | + `$v0 == 0x3ffd23e0` | `$v0 == 0x3fffedfc` | `$v0 = __stack_chk_guard == 0x3fffedfc` |
| `lw      $v0, (__stack_chk_guard - 0x411088)($v0)` | + $v0：Value | + `$v0 == 0x3fffedfc` | `$v0 == 0xd9584c00（Canary值）` | `$v0 = *($v0 + __stack_chk_guard - 0x411088) == *v0 == 0xd9584c00` |


> + **<font style="color:#F5222D;">上面表格中"=="为等号，"="为赋值。</font>**
> + **<font style="color:#F5222D;">伪C语言看一个大概就行，我没有表明具体的数据类型。</font>**
> + **<font style="color:#F5222D;">注意$s8和$fp变化情况，具体会在稍后讲解，这里只要知道在gdb的眼中，对$fp操作时实际是对$s8操作。</font>**
>

第二段汇编代码如下：

```c
.text:004008C4 5C 00 C2 AF                   sw      $v0, 0x60+var_4($fp)			  
.text:004008C8 AD DE 02 3C EF BE 42 34       li      $v0, 0xDEADBEEF
.text:004008D0 30 00 C2 AF                   sw      $v0, 0x60+var1($fp)
.text:004008D4 40 00 02 3C 14 0B 42 24       li      $v0, aNysecChamd5                # "NYSEC-ChaMD5"
.text:004008DC 34 00 C2 AF                   sw      $v0, 0x60+var2($fp)
.text:004008E0 40 00 02 3C 24 0B 42 24       li      $v0, aQemuMips                   # "qemu-MIPS"
.text:004008E8 38 00 C2 AF                   sw      $v0, 0x60+var3($fp)
.text:004008EC 40 00 02 3C 30 0B 42 24       li      $v0, aYuqueComCybera             # "yuque.com/cyberangel"
.text:004008F4 3C 00 C2 AF                   sw      $v0, 0x60+var4($fp)
.text:004008F8 40 00 02 3C 48 0B 42 24       li      $v0, aWwwCyberangelC             # "www.cyberangel.cn"
.text:00400900 40 00 C2 AF                   sw      $v0, 0x60+var5($fp)
.text:00400904 40 00 02 3C                   lui     $v0, 0x40  # '@'
.text:00400908 68 0B 40 C4                   lwc1    $f0, flt_400B68
.text:0040090C 44 00 C0 E7                   swc1    $f0, 0x60+var6($fp)
.text:00400910 10 00 04 24                   li      $a0, 0x10                        # size
.text:00400914 34 80 82 8F                   la      $v0, malloc
.text:00400918 25 C8 40 00                   move    $t9, $v0
.text:0040091C 09 F8 20 03                   jalr    $t9 ; malloc
.text:00400920 00 00 00 00                   nop
```

| MIPS指令 | 指令牵扯到的寄存器 | 执行前 | 执行后 | 指令的伪C语言形式 |
| --- | --- | --- | --- | --- |
| `sw      $v0, 0x60+var_4($fp)` | + $v0：Value<br/>+ $fp：Frame Pointer | + `$v0 == 0xd9584c00（Canary值）`<br/>+ `$fp == 0x40800028`<br/>+ `<font style="color:#E8323C;">$s8 == 0x407fffc0</font>` | 不变 | `*($fp + 0x5c) == *(<font style="color:#F5222D;">$s8</font> + 0x5c) = 0xd9584c00`<br/>即，执行之后地址0x4080001c存放的数据为0xd9584c00<font style="color:#F5222D;"></font> |
| `li      $v0, 0xDEADBEEF` | + $v0：Value | + `$v0 == 0xd9584c00（Canary值）` | $v0 == 0xdeadbeef | $v0 = 0xdeadbeef |
| `sw      $v0, 0x60+var1($fp)` | + $v0：Value<br/>+ $fp：Frame Pointer | + `$v0 = 0xdeadbeef`<br/>+ `$fp = 0x40800028`<br/>+ `<font style="color:#E8323C;">$s8 = 0x407fffc0</font>` | 不变 | `*($fp + 0x5c) == *(<font style="color:#F5222D;">$s8</font> + 0x30) == *(0x407ffff0) = 0xdeadbeef`<br/>即，执行之后地址`0x407ffff0`存放的数据为0xdeadbeef |
| `li      $v0, aNysecChamd5 ` | + $v0：Value | + `$v0 = 0xdeadbeef`<br/>+ `$fp = 0x40800028`<br/>+ `<font style="color:#E8323C;">$s8 = 0x407fffc0</font>` | $v0 == 0x00400B14 | $v0 = 0x00400B14（0x00400B14下存放着字符串） |
| `sw      $v0, 0x60+var2($fp)` | + $v0：Value<br/>+ $fp：Frame Pointer | + `$v0 = 0x00400B14`<br/>+ `$fp = 0x40800028`<br/>+ `<font style="color:#E8323C;">$s8 = 0x407fffc0</font>` | 不变 | `*($fp + 0x34) == *($<font style="color:#E8323C;">s8</font> + 0x34) == *0x407ffff4 = 0x00400B14`<br/>即，执行之后地址`0x407ffff4`存放的数据为`0x00400B14` |
| ......（省略之间说过的指令） | ...... | ...... | ...... | ...... |
| `sw      $v0, 0x60+var5($fp)` | ...... | ...... | ...... | ....... |


执行完地址0x0400900的语句`sw  $v0, 0x60+var5($fp)`后，当前寄存器和部分内存如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657420479465-69cf204c-cbbf-4ba9-88c5-fd6423fc8c43.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657420578890-07c75f8a-6b63-4229-9a55-832b72a96ca6.png)

| MIPS指令 | 指令牵扯到的寄存器 | 执行前 | 执行后 | 指令的伪C语言形式 |
| --- | --- | --- | --- | --- |
| `lui     $v0, 0x40  # '@'` | + $v0：Value | + `$v0 == 0x00400b48（字符串地址）` | `$v0 == 0x00400000` | |
| `lwc1    $f0, flt_400B68` | + $f0：Float | + `$f0 == 0` | `$f0 == 3.1415925` | `$f0 = *(0x400B68) == .float 3.1415925`<br/>注：地址0x400B68下存放浮点数的16进制：0x40490fda |
| `swc1    $f0, 0x60+var6($fp)` | + $f0：Float<br/>+ $fp：Frame Pointer | + `$f0 == 3.1415925`<br/>+ `$fp == 0x40800028`<br/>+ `<font style="color:#E8323C;">$s8 == 0x407fffc0</font>` | 不变 | `*($fp+0x44) == *($s8+0x44) == *(0x40800004) = $f0`<br/>即，执行之后地址`0x40800004`存放的数据为`0x40490fda` |
| `li      $a0, 0x10` | + $a0：Arguments | + `$a0 == 0x1` | `$a0 == 0x10` | $a0 = 0x10 |
| `la      $v0, malloc` | + $v0：Value | + `$v0 == 0x00400000` | `$v0 == 0x00400A70` | $v0 = malloc == 0x00400A70 |
| `move    $t9, $v0` | + $t9：Temporary variable<br/>+ $v0：Value | + `$v0 == 0x00400A70`<br/>+ `$t9 == 004008A0（main函数起始地址）` | `$t9 == 00400A70（malloc函数起始地址）`<br/> | $t9 = $v0 |
| `jalr    $t9 ; malloc` | + $t9：Temporary variable | + `$ra == 0x3fdf47a4（main函数返回地址）` | -- | malloc(0x10) |
| `nop` | -- | -- | -- | -- |


+ `lui`：`load upper immediate`，取立即数并放到寄存器的高16位，剩下的低16位使用0填充。
+ `lwc1`：`load word coprocessor 1`，将浮点数加载到`浮点寄存器（floating-point register）`中。
+ `swc1`：`store word coprocessor 1`，将浮点寄存器的数据保存到相应的内存。
+ `jalr`：`jump and link register`，其格式为`jalr oprd1 oprd2`或`jalr oprd1`，当格式为前者时在调用函数后会将返回地址存入到`oprd2`中；当格式为后者时返回地址将保存到$ra寄存器。
+ `nop`：和x86的含义一样，滑动指令。

调用库函数malloc之后，接下来程序要为调用`funny_fucntion`做准备，如下图所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657430512018-ebf551b1-a355-4770-a771-528f31d396f4.png)

这里我只着重的说一下之前未出现的指令：

+ `lhu`：`load halfword unsigned`，加载半个字（1字节）的数据到目标寄存器。
+ `sh`：`store halfword`：传送半个字到目标内存。

| MIPS指令 | 指令牵扯到的寄存器 | 执行前 | 执行后 | 指令的伪C语言形式 |
| --- | --- | --- | --- | --- |
| `lhu     $v0, (word_400B64 - 0x400B5C)($v0)` | + $v0：Value | + `$v0 == 0x400b5c（"字符串cyberangel地址"）` | $v0 == 0x6c65（字符串"el"） | `$v0 = *(0x400b5c + 0x8) == *0x400b64 == 0x6c65` |
| `sh      $v0, 0x60+var8+8($fp)` | + $v0：Value<br/>+ $fp：Frame Pointer | + `$v0 == 0x6c65`<br/>+ `$s8 == 0x407fffc0`<br/>+ `$fp == 0x40800028` | 不变 | --（懒的写了） |


中间的语句就不再仔细的讲解了，我们直接跳过这部分，来到0x4007a0：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657432318254-a511e8e6-59fc-46e1-b6ab-72b9d424687a.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657432570010-53825b73-f116-4299-a542-cb923d8a864e.png)

**<font style="color:#E8323C;">从上面两张图可以看出，在MIPS32位下进行函数调用时，前四个参数分别依次通过A0、A1、A2、A3寄存器传递，剩下的参数使用stack进行传递；而且虽然前四个参数没有使用栈传递，但是栈上仍旧保留了这四个函数的位置。</font>**

好了，下面进入`funny_function`函数，**<font style="color:#E8323C;">在函数调用的开头会将通过寄存器传入的参数复制到stack上，并且通过stack传送的参数要复制到新的栈帧中</font>**：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657509149486-ccba0158-fba9-4585-a2f0-baf9c66a32fc.png)

下面这张图是在复制var_5时的结果：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657508916856-f2a01620-f7ba-4e9b-a9b4-73ddafe7b86b.png)

MIPS的函数在准备好参数之后，因为该文件开启了Canary保护，所以还要准备一下Canary的值：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657516142127-583e67ac-0dac-4277-9571-31dbedfcb56b.png)

上面有3个指令值得说一下：

+ `cvt.d.s $f0, $f1`：该指令的全称为`Convert Double to Single`，将寄存器$f1的浮点数转换为整型保存在浮点寄存器$f0中。
+ `addiu   $v1, $fp, 0x168+buffer`：前面见到的addiu只有两个操作数，而这里有3个操作数，当出现后者这种情况时，表示`$v1 = $fp + 0x168 + buffer（buffer的地址）`
+ `sdc1    $f0, 0x168+var_148($sp)`，很好理解将浮点寄存器$f0的数据存到内存地址`0x168+var_148($sp)`中。

最后一段代码是关于检查Canary是否被篡改，自己可以看看：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657516303577-753f8c7a-8573-4015-9be2-17aaadbd4db4.png)

## ③、MIPS的函数调用
在上面的讲解中只关注了每个MIPS指令的含义和函数的传参方式，但是并没有说函数在发生调用时的细节；和x86不同的是，讲解这些内容需要引入`叶子函数、非叶子函数`这两个概念。这里的叶子和“数据结构--树的叶子”完全相同，即：

+ 叶子函数：某个函数中不会再调用其他的函数，称为“叶子函数”。
+ 非叶子函数：某个函数会调用其他函数，也就是会发生函数嵌套，可以将这个函数称为“非叶子函数”。

我们还是以一个新demo来举例：

```c
// mipsel-linux-gnu-gcc -g -fno-stack-protector -z execstack -no-pie -z norelro leaf_function.c -o leaf_function_MIPSEL_32
#include <stdio.h>

char* child1_func1(char* buffer){
    return buffer;
}

void parent_func(){
    char *name = "cyberangel";
    printf("I'm parent function\n");
    printf("%s",child1_func1(name));

}
int main(){
    parent_func();
    return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657759208951-4ca0ae3f-8915-4625-bee9-8f862a244063.png)

按照概念，`parent_func`属于非叶子函数，`child1_func1`则为叶子函数。

> 为了避免受到Canary的`__stack_chk_fail`函数影响，所以这里我在编译程序时将该保护关闭；当然你也可以看看在保护开启时函数如`child1_func1`是否会变为非叶子函数。
>

gdb脚本如下：

```c
file ./leaf_function_MIPSEL_32
set architecture mips
b *0x0400798			
target remote :1234
c
```

> + qemu模拟执行：`qemu-mipsel-static -L /usr/mipsel-linux-gnu/ -g 1234 ./leaf_function_MIPSEL_32`
> + gdb远程调试：`gdb-multiarch -x ./leaf_function_MIPSEL_32_gdbscript.gdb`
> + 0x0400798为main函数的起始地址
>

启动gdb开始调试，跑起来之后会断到main函数的开头，**现在开始执行main函数**：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657526893304-59667e8a-87de-4230-9307-7bf88adbb0d6.png)

+ 开辟main函数栈帧：`addiu  $sp, $sp, -0x20`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657760305789-ec68ed5a-19cf-46b0-a3a8-020ca983bc8d.png)

+ 保存main函数的返回地址`$ra（Return Address Register）`到stack中`0x1c($sp)`，`sw      $ra, 0x18+var_s4($sp)`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657761282621-92f9cb58-3eda-49b7-abf8-19643bb71153.png)

+ `sw $fp, 0x18($sp)`与`move   $fp, $sp`这两条语句十分的关键，因为`$fp`和`$s8`这两个寄存器在IDA和gdb中的表述方式不同，我们先来看IDA中的描述：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657540800572-9fad6477-d6a5-4719-a8b9-aa0d72ccefa5.png)

    - 执行`sw  $fp, 0x18+var_s0($sp)`之后：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657541002707-d7158911-4f55-46c7-9ed5-d13059b90747.png)

    - `move $fp, $sp`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657541100444-8b44e551-32fa-430a-920c-ee07d6c04d47.png)

**<font style="color:#E8323C;">IDA总结：IDA并不会将</font>**`**<font style="color:#E8323C;">$s8</font>**`**<font style="color:#E8323C;">显示出来，所以对$fp的操作影响的都是</font>**`**<font style="color:#E8323C;">$fp</font>**`**<font style="color:#E8323C;">而非</font>**`**<font style="color:#E8323C;">$s8</font>**`**<font style="color:#E8323C;">。</font>**下面是gdb**<font style="color:#E8323C;">，</font>**与IDA不同的是，gdb会将`$s8`和`$fp`寄存器一起显示出来，<u>在某些情况下可能会对初学者造成困惑</u>（比如我这个垃圾：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657541354582-c15236c7-78c7-449e-8151-2206cb17539f.png)

    - `sw  $fp, 0x18($sp)`，**注意执行后在stack上保存的是寄存器**`**$s8**`**的值而非**`**$fp**`：

![在stack上保存的$fp栈底地址为0？？？？别急，我们继续往下分析。](https://cdn.nlark.com/yuque/0/2022/png/574026/1657541628071-db74a76a-5091-4d01-9fb5-b84dc0e5bcec.png)

    - `move $fp, $sp`，修改之前`$s8 == 0`，修改时修改的是`**$s8**`**不是**`**$fp**`**：**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657584897214-0f4bdf1c-1b73-4c8a-b7f1-593d5290d829.png)

**<font style="color:#E8323C;">gdb总结：gdb多显示了$s8寄存器，基本上所有对$fp的操作都是对$s8的操作，比如当使用$fp寻址时用的是$s8而不是$fp里面的值，赋值时也是$s8，等等...</font>**

---

为什么会出现这种描述混乱的情况？在这篇文章的开头有如下表格：

| $30 | $fp/$s8 | $30可以当做第9个Saved寄存器`$s8`，也可以当做栈帧指针（Frame Pointer）`$fp`使用，这得看编译器的类型。 |
| --- | --- | --- |


第30号通用寄存器可以被叫做$fp寄存器或者是$s8寄存器，所以它们用的是同一个"实体物理结构"，造成这种混乱的原因得归结于不同编译器对该"物理结构"的使用，<font style="background-color:#FADB14;">GNU MIPS C编译器将它用作帧指针（frame pointer）【$fp】，而SGI的C编译器则将其当做保存寄存器使用【$s8】，后者的使用方式虽然节省了调用和返回开销，但增加了代码生成的复杂性。</font>本篇文章中的所有demo都使用的是GNU编译器：  
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657584979848-2a3788b6-1669-4b98-b290-51e5c8879922.png)

所以我们不妨可以得出几个结论：

+ **<font style="color:#E8323C;">寄存器$s8和$fp本身就是同一个寄存器，只不过它由两个名字罢了，这个寄存器既可以用于Saved也可以用于Frame Pointer。</font>**
+ **<font style="color:#E8323C;">就使用GNU编译的可执行程序而言，在IDA中只会显示$fp寄存器，猜测这才是比较正统的显示方式，因为像</font>**`**<font style="color:#E8323C;">move $fp, $sp</font>**`**<font style="color:#E8323C;">这种指令可以更好的理解，一看修改的就是$fp寄存器而不是$s8。</font>**
+ **<font style="color:#E8323C;">gdb的显示寄存器的方式估计是为了对SGI编译出来的程序有更好的兼容性，并且在调试GNU的程序时需要gdb自己协调$fp和$s8的显示方式与显示关系，因为每个指令语句的含义都是相同的。</font>**
+ **<font style="color:#E8323C;">gdb这样的显示方式还有一个好处，这一点请你继续向下阅读。</font>**

---

这里我们要注意，在执行main函数时无论是哪一种表述方式，`sw  $fp, 0x18($sp)`存放到栈上的`$fp（$s8）`均为0，指令`move $fp, $sp`之后`$fp（$s8）`和`$sp`指向同一个栈内存地址，即，MIPS的函数在addiu开栈帧之后会立刻move移动$fp到$sp的位置；这一点与x86不同：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657768866698-a7f0d13e-5e83-4740-a7df-1757c9e744f1.png)

**<font style="color:#E8323C;">所以x86和MIPS_32的开辟栈帧的方式是不同的，但是最终的栈帧结构相同</font>**，且均可以将$sp和$fp可以类比为$esp和$ebp，对比如下：

| MIPS指令 | 指令说明 | 等价的x86指令 |  正常的x86指令顺序 | x86指令补充说明 |
| --- | --- | --- | --- | --- |
| `addiu   $sp, -0x28`【1】 | 开辟栈帧空间 | `sub     esp, 14h` | 【4】 | -- |
| `sw      $ra, 0x20+var_s4($sp)`【2】 | 存放返回地址 | `call    main` | 【1】 | 这里只针对call在调用时发生的返回地址压栈操作 |
| `sw      $fp, 0x20+var_s0($sp)`【3】 | 保存$fp到栈 | `push    ebp` | 【2】 | -- |
| `move    $fp, $sp`【4】 | 保存$sp到$fp | `mov     ebp, esp` | 【3】 | -- |


总结：`帧指针（Frame Point、$fp）`在调用过程中起着锚定的作用，在子过程被调用时会将旧的`$fp`压栈，再将`$fp`指向新产生栈帧固定位置，这样当前栈帧中就有了`$fp`当做一个哨兵，其承担两个关键任务：

+ 无论`$sp`怎么变，但只要知道栈中保存的数据相对于`$fp`的偏移，就可以将内存中的数据顺利取出（我写的demo中没有体现这一点）。
+ 如果`$sp`在子过程为自己分配了栈空间后又发生了变化，那么在子过程返回前，`$fp`还需要帮`$sp`恢复原值（`$sp`恢复原值也就是释放了当前子过程占用的栈空间）。

---

正是因为gdb的显示方式不太一样，所以某些指令要多进行一步操作，这一点会在下面的篇幅中体现。

+ `jal  parent_func (jal 0x400888) 与 nop`：

调用非叶子函数`parent_func`，还是先看IDA：执行jal指令后会将`jal指令+0xC`即返回地址存入到`$ra`中：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657527452048-adaaffaa-5f27-4be2-b978-06723d902f87.png)

然后nop滑动到`parent_func`函数执行代码：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657527477337-6d2896ab-126c-40f3-97e7-a698201451a6.png)

**<font style="color:#E8323C;">总之，在IDA的眼中，当函数A调用其他函数B时，函数调用指令如jal会将函数B的返回地址存入$ra中，然后nop滑动执行函数B；调用前后$sp和$fp值不变且相等。出现nop滑动时可能与MIPS的“流水线”这个概念有关，先挖个坑...（</font>****<font style="color:#E8323C;">🕊</font>**

**<font style="color:#E8323C;">然后来看gdb，与IDA显示的不同，在调试时我们不能对nop指令下断点，否则会直接跑飞：</font>**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657586595770-c9f9950a-c64c-4019-97dd-d570418f9751.png)

所以我们只能对`parent_func`的起始地址`0x0400708`下断点，调用后除了和IDA一样的$ra变化以外，**<font style="color:#E8323C;">gdb显示的$fp也发生了变化</font>**，此时的$fp、$s8、$fp值相同：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657586952931-6558bd38-d8fc-4b12-8ad3-bdc491aae4d1.png)

要想习惯gdb的这种显示方式，就要时刻注意`$s8`和`$fp`这两个东西的变化。紧接着执行：

    1. `addiu  $sp, $sp, -0x28`
    2. `sw     $ra, 0x24($sp)：保存返回地址到stack上`
    3. `sw     $fp, 0x20($sp)：保存栈底到stack上`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657587641798-992aeb84-438e-489d-aee9-c102e9fbcd5d.png)

这下就正常了嘛，保存的`parent_func`栈底不再为0，究其原因在函数调用时保存的是$s8而不是$fp，**<font style="color:#E8323C;">看来只有在调用main函数时保存的栈底才是0</font>**。另外，gdb的这种方式的确害人，让我这种的初学者感到晕头转向，move之后：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657588512791-ad08adee-b22e-4f1f-8e9a-efccc6931241.png)

所以这种显示方式：

    1. `**<font style="color:#F5222D;">$s8</font>**`**<font style="color:#F5222D;">成为事实上的栈底。</font>**
    2. `**<font style="color:#F5222D;">$fp</font>**`**<font style="color:#F5222D;">表示指向旧的</font>**`**<font style="color:#F5222D;">$fp</font>**`**<font style="color:#F5222D;">。</font>**
    3. `**<font style="color:#F5222D;">$sp</font>**`**<font style="color:#F5222D;">还是意义上的栈顶。</font>**

下图是x86的parent_func：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657589236340-ccccade2-4828-4a8a-a94a-1bbfec2f0a2d.png)

移动栈底后开始调用puts函数：

```c
// mipsel-linux-gnu-gcc -g -fno-stack-protector -z execstack -no-pie -z norelro leaf_function.c -o leaf_function_MIPSEL_32
#include <stdio.h>

char* child1_func1(char* buffer){
    return buffer;
}

void parent_func(){
    char *name = "cyberangel";
    printf("I'm parent function\n");	// -> 调用printf函数(编译器的优化结果为puts)
    printf("%s",child1_func1(name));

}
int main(){
    parent_func();
    return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657848077295-905aeb23-98d3-4ba4-bc95-adba82f4984b.png)

+ 准备调用`child_func1`函数：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657848152098-6860cfbc-f434-4fc7-aef3-751060fe625b.png)

+ 调用`child_func1`叶子函数

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657539271241-963073d6-388f-4fb4-a566-5424c633bc0a.png)

**<font style="color:#F5222D;">可以看到叶子函数只保存了</font>**`**<font style="color:#F5222D;">$fp</font>**`**<font style="color:#F5222D;">，并没有保存返回地址$ra到stack上。</font>**

+ 函数将要结束，执行`0x4006F4：move $sp,$fp`以恢复原$sp，并`addiu $sp,8`以回收栈帧，保持栈平衡：

![move $sp,$fp](https://cdn.nlark.com/yuque/0/2022/png/574026/1657590783057-38169281-1a3b-4e3d-89cf-90cee5789468.png)

![addiu $sp,8](https://cdn.nlark.com/yuque/0/2022/png/574026/1657590805975-b541429c-8b60-41a2-9ba8-efa35fc7ff9a.png)

| MIPS指令 | 指令说明 | 等价的x86指令 |  正常的x86指令顺序 | x86指令补充说明 |
| --- | --- | --- | --- | --- |
| `addiu   $sp, -8` | 开辟栈帧空间 | -- |  | x86没有为该函数开辟栈，其使用寄存器传递参数 |
| `sw      $fp, 4+var_s0($sp)` | 保存旧的$fp到栈 | `push    ebp` | 【1】 | -- |
| `move    $fp, $sp` | 保存$sp到$fp | `mov     ebp, esp` | 【2】 | -- |
| `sw      $a0, 4+buffer($fp)` | 变量在寄存器间移动 | `mov     eax, [ebp+buffer]` | 【3】 | x86没有为该函数开辟栈，其使用寄存器传递参数 |
| `lw      $v0, 4+buffer($fp)` | | | | |
| `move    $sp, $fp` | 恢复$sp | -- | | x86没有为该函数开辟栈，其使用寄存器传递参数，$esp指针未修改 |
| `lw      $fp, 4+var_s0($sp)` | 恢复旧的$fp | `pop     ebp` | 【4】 | -- |
| `addiu   $sp, 8` | 回收栈帧 | -- |  | x86没有为该函数开辟栈，其使用寄存器传递参数 |
| `jr      $ra` | 返回 | `retn` | 【5】 | `pop eip` |
| `nop` | -- | -- | | -- |


> 表格的“等价的x86指令”指的是行为类似的指令，不代表两个架构的指令完全相同。
>

![x86](https://cdn.nlark.com/yuque/0/2022/png/574026/1657850117052-5ede1ff8-9c47-42d6-8883-afe2c5ceafd9.png)

**<font style="color:#F5222D;">叶子函数和非叶子函数的返回方式不相同，现在A函数调用了B函数，如果函数B是叶子函数，则直接使用</font>**`**<font style="color:#F5222D;">jr $ra</font>**`**<font style="color:#F5222D;">指令返回函数A；如果函数B是非叶子函数，则函数B先从堆栈中取出被保存在堆栈上的返回地址，然后将返回地址存入寄存器$ra，再使用“jr $ra”指令返回函数A：</font>**

![parent_func（非叶子函数）的返回](https://cdn.nlark.com/yuque/0/2022/png/574026/1657850597165-5c85c054-b41e-4db3-b202-380dbc32dc9d.png)

完 ~

[  
](https://loongson.github.io/LoongArch-Documentation/LoongArch-ELF-ABI-CN.html#_e_flags_abi_%E7%B1%BB%E5%9E%8B%E5%92%8C%E7%89%88%E6%9C%AC%E6%A0%87%E8%AE%B0)

