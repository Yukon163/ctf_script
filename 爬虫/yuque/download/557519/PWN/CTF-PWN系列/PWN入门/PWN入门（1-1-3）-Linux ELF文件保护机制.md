> [https://blog.csdn.net/weixin_44932880/article/details/104092620](https://blog.csdn.net/weixin_44932880/article/details/104092620)
>
> [https://blog.csdn.net/RChaos/article/details/104344276](https://blog.csdn.net/RChaos/article/details/104344276)
>
> [https://blog.csdn.net/qq_41202237/article/details/105913071](https://blog.csdn.net/qq_41202237/article/details/105913071)
>

Linux ELF文件的保护主要有四种：Canary、NX、PIE、RELRO

# 一：Canary
Canary是金丝雀的意思。技术上表示最先的测试的意思。这个来自以前挖煤的时候，矿工都会先把金丝雀放进矿洞，或者挖煤的时候一直带着金丝雀。金丝雀对甲烷和一氧化碳浓度比较敏感，会先报警。所以大家都用Canary来搞最先的测试。**<font style="color:#F5222D;">S</font>****<font style="color:#F5222D;">tack Canary表示栈的报警保护</font>**。

在函数返回值之前添加的一串随机数（不超过机器字长）（也叫做cookie），末位为/x00（提供了覆盖最后一字节输出泄露Canary的可能），如果出现缓冲区溢出攻击，覆盖内容覆盖到Canary处，就会改变原本该处的数值**<font style="color:#F5222D;">，当程序执行到此处时，会检查Canary值是否跟开始的值一样，如果不一样，程序会崩溃，从而达到保护返回地址的目的。</font>**

**<font style="color:#F5222D;">  
</font>**![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597912626758-4ec5f40a-8913-487e-ab22-8504e524da42.png)

> 总的来说，Canary参数表示着对栈的保护，防止栈溢出的一种保护，即在栈靠近栈底某个位置设置初值，防止栈溢出的一种保护
>



GCC用法：

```c
gcc -o test test.c // 默认情况下，不开启Canary保护
gcc -fno-stack-protector -o test test.c //禁用栈保护
gcc -fstack-protector -o test test.c //启用堆栈保护，不过只为局部变量中含有 char 数组的函数插入保护代码
gcc -fstack-protector-all -o test test.c //启用堆栈保护，为所有函数插入保护代码
-fno-stack-protector /-fstack-protector / -fstack-protector-all (关闭 / 开启 / 全开启)
```

> + **<font style="color:#DF2A3F;">2023年10月06日更新：canary在不同编译器或不同系统下的实现可能有所不同，上面图片仅是展示了canary和ebp的相对位置，即canary相对于ebp而言在低地址，并不是说canary与ebp相邻；比如ubuntu gcc编译出来程序的canary位置在</font>**`**<font style="color:#DF2A3F;">ebp - 0xc</font>**`**<font style="color:#DF2A3F;">（32位程序，canary与ebp不相邻）或</font>**`**<font style="color:#DF2A3F;">rbp - 0x8</font>**`**<font style="color:#DF2A3F;">（64位程序，canary与rbp相邻）。详见文章</font>**`[**<font style="color:#DF2A3F;">https://www.yuque.com/cyberangel/rg9gdm/cx5zci</font>**](https://www.yuque.com/cyberangel/rg9gdm/cx5zci)`**<font style="color:#DF2A3F;">的对该问题的发现与描述。</font>**
>
> ![](https://cdn.nlark.com/yuque/0/2023/png/574026/1696594075012-7ab03177-4eba-478a-8892-9cb0d96b8539.png)
>

# 二：NX
NX即No-eXecute（不可执行）的意思，NX（DEP）的基本原理是将数据所在内存页标识为不可执行，当程序溢出成功转入shellcode时，程序会尝试在数据页面上执行指令，此时CPU就会抛出异常，而不是去执行恶意指令。

正常在栈溢出时通过跳转指令跳转至shellcode，但是NX开启后CPU会对数据区域进行检查，当发现正常程序不执行，并跳转至其他地址后会抛出异常，接下来不会继续执行shellcode，而是去转入异常处理，处理后会禁止shellcode继续执行



GCC 用法：

```c
gcc -o test test.c // 默认情况下，开启NX保护
gcc -z execstack -o test test.c // 禁用NX保护
gcc -z noexecstack -o test test.c // 开启NX保护
-z execstack / -z noexecstack (关闭 / 开启)
```

# 三：PIE（ASLR）
一般情况下NX（Windows平台上称为DEP）和地址空间分布随机化（PIE/ASLR）（address space layout randomization）会同时工作。内存地址随机化机制有三种情况：

> 0 - 表示关闭进程地址空间随机化。
>
> 1 - 表示将mmap的基地址，栈基地址和.so地址随机化
>
> 2 - 表示在1的基础上增加heap的地址随机化
>

**<font style="color:#F5222D;">该保护能使每次运行的程序的地址都不同，</font>****<font style="color:#F5222D;">防止根据固定地址来写exp执行攻击。</font>**

> 可以防止Ret2libc方式针对DEP的攻击。ASLR和DEP配合使用，能有效阻止攻击者在堆栈上运行恶意代码
>

**liunx下关闭PIE的命令如下：**

```bash
sudo -s echo 0 > /proc/sys/kernel/randomize_va_space
```

GCC用法：

```c
gcc -o test test.c // 默认情况下，不开启PIE
gcc -fpie -pie -o test test.c // 开启PIE，此时强度为1
gcc -fPIE -pie -o test test.c // 开启PIE，此时为最高强度2
gcc -fpic -o test test.c // 开启PIC，此时强度为1，不会开启PIE
gcc -fPIC -o test test.c // 开启PIC，此时为最高强度2，不会开启PIE
-no-pie / -pie (关闭 / 开启)
```

# 四：RELRO
Relocation Read-Only (RELRO) 可以使程序某些部分成为只读的。它分为两种：Partial RELRO 和 Full RELRO，即：部分RELRO 和 完全RELRO。

**部分RELRO** 是 GCC 的默认设置，几乎所有的二进制文件都至少使用部分RELRO。这样仅仅只能防止全局变量上的缓冲区溢出从而覆盖 GOT。

**完全RELRO** 使整个 GOT 只读，从而无法被覆盖，但这样会大大增加程序的启动时间，因为程序在启动之前需要解析所有的符号。

>  在Linux系统安全领域数据可以写的存储区就会是攻击的目标，尤其是存储函数指针的区域。所以在安全防护的角度应尽量减少可写的存储区域
>
> RELRO会设置符号重定向表格为只读或者程序启动时就解析并绑定所有动态符号，从而减少对GOT表的攻击。如果RELRO为Partial RELRO，就说明对GOT表具有写权限
>

---

> 主要用来保护重定位表段对应数据区域，默认可写
>
> Partial RELRO：.<font style="background-color:transparent;">got不可写，got.plt可写</font>
>
> Full RELRO：.<font style="background-color:transparent;">got和got.plt不可写</font>
>
> <font style="background-color:transparent;">got.plt可以简称为got表</font>
>

GCC用法：

```c
gcc -o test test.c // 默认情况下，是Partial RELRO
gcc -z norelro -o test test.c // 关闭，即No RELRO
gcc -z lazy -o test test.c // 部分开启，即Partial RELRO
gcc -z now -o test test.c // 全部开启
-z norelro / -z lazy / -z now (关闭 / 部分开启 / 完全开启)
```

> GOT表和PLT表将在下一节进行介绍
>

# 五、FORTIFY
 fortify是轻微的检查，用于检查是否存在缓冲区溢出的错误。适用于程序采用大量的字符串或者内存操作函数，如:

```c
>>> memcpy():
	描述：void *memcpy(void *str1, const void *str2, size_t n)
    	 从存储区str2复制n个字符到存储区str1
  参数：str1 -- 指向用于存储复制内容的目标数组，类型强制转换为 void* 指针
    	 str2 -- 指向要复制的数据源，类型强制转换为 void* 指针
    	 n -- 要被复制的字节数
  返回值：该函数返回一个指向目标存储区 str1 的指针
---------------------------------------------------------------------------------------
>>> memset():
  描述：void *memset(void *str, int c, size_t n)
    	 复制字符 c（一个无符号字符）到参数 str 所指向的字符串的前 n 个字符
  参数：str -- 指向要填充的内存块
    	 c -- 要被设置的值。该值以 int 形式传递，但是函数在填充内存块时是使用该值的无符号字符形式
    	 n -- 要被设置为该值的字节数
  返回值：该值返回一个指向存储区 str 的指针
---------------------------------------------------------------------------------------
>>> strcpy():
  描述：char *strcpy(char *dest, const char *src)
    	 把 src 所指向的字符串复制到 dest，容易出现溢出
  参数：dest -- 指向用于存储复制内容的目标数组
    	 src -- 要复制的字符串
  返回值：该函数返回一个指向最终的目标字符串 dest 的指针
-------------------------------------------------------------------------------------->>> stpcpy():
  描述：extern char *stpcpy(char *dest,char *src)
    	 把src所指由NULL借宿的字符串复制到dest所指的数组中
  说明：src和dest所指内存区域不可以重叠且dest必须有足够的空间来容纳src的字符串返回指向dest结尾处字符（NULL）的指针	 
  返回值：
---------------------------------------------------------------------------------------    >>> strncpy():
  描述：char *strncpy(char *dest, const char *src, size_t n)
    	 把 src 所指向的字符串复制到 dest，最多复制 n 个字符。当 src 的长度小于 n 时，dest 的剩余部分将用空字节填充
  参数：dest -- 指向用于存储复制内容的目标数组
    	 src -- 要复制的字符串
    	 n -- 要从源中复制的字符数
  返回值：该函数返回最终复制的字符串
--------------------------------------------------------------------------------------->>> strcat():
  描述：char *strcat(char *dest, const char *src)
    	 把 src 所指向的字符串追加到 dest 所指向的字符串的结尾
  参数：dest -- 指向目标数组，该数组包含了一个 C 字符串，且足够容纳追加后的字符串
    	 src -- 指向要追加的字符串，该字符串不会覆盖目标字符串
  返回值：
--------------------------------------------------------------------------------------->>> strncat():
  描述：char *strncat(char *dest, const char *src, size_t n)
    	 把 src 所指向的字符串追加到 dest 所指向的字符串的结尾，直到 n 字符长度为止
  参数：dest -- 指向目标数组，该数组包含了一个 C 字符串，且足够容纳追加后的字符串，包括额外的空字符
    	 src -- 要追加的字符串
    	 n -- 要追加的最大字符数
  返回值：该函数返回一个指向最终的目标字符串 dest 的指针
--------------------------------------------------------------------------------------->>> sprintf():PHP
  描述：sprintf(format,arg1,arg2,arg++)
    	 arg1、arg2、++ 参数将被插入到主字符串中的百分号（%）符号处。该函数是逐步执行的。在第一个 % 符号处，插入 arg1，在第二个 % 符号处，插入 arg2，依此类推
  参数：format -- 必需。规定字符串以及如何格式化其中的变量
    	 arg1 -- 必需。规定插到 format 字符串中第一个 % 符号处的参
    	 arg2 -- 可选。规定插到 format 字符串中第二个 % 符号处的参数
    	 arg++ -- 可选。规定插到 format 字符串中第三、四等等 % 符号处的参数
  返回值：返回已格式化的字符串
--------------------------------------------------------------------------------------->>> snprintf():
  描述：int snprintf ( char * str, size_t size, const char * format, ... )
    	 设将可变参数(...)按照 format 格式化成字符串，并将字符串复制到 str 中，size 为要写入的字符的最大数目，超过 size 会被截断
  参数：str -- 目标字符串
    	 size -- 拷贝字节数(Bytes)如果格式化后的字符串长度大于 size
    	 format -- 格式化成字符串
  返回值：如果格式化后的字符串长度小于等于 size，则会把字符串全部复制到 str 中，并给其后添加一个字符串结束符 \0。 如果格式化后的字符串长度大于 size，超过 size 的部分会被截断，只将其中的 (size-1) 个字符复制到 str 中，并给其后添加一个字符串结束符 \0，返回值为欲写入的字符串长度
--------------------------------------------------------------------------------------->>> vsprintf():PHP
  描述：vsprintf(format,argarray) 
    	 与 sprintf() 不同，vsprintf() 中的参数位于数组中。数组元素将被插入到主字符串中的百分号（%）符号处。该函数是逐步执行的
  参数：format -- 必需。规定字符串以及如何格式化其中的变量
    	 argarray -- 必需。带有参数的一个数组，这些参数会被插到 format 字符串中的 % 符号处
  返回值：以格式化字符串的形式返回数组值
--------------------------------------------------------------------------------------->>> vsnprintf():
  描述：int vsnprintf (char * s, size_t n, const char * format, va_list arg )
    	 将格式化数据从可变参数列表写入大小缓冲区
如果在printf上使用格式，则使用相同的文本组成字符串，但使用由arg标识的变量参数列表中的元素而不是附加的函数参数，并将结果内容作为C字符串存储在s指向的缓冲区中 （以n为最大缓冲区容量来填充）。如果结果字符串的长度超过了n-1个字符，则剩余的字符将被丢弃并且不被存储，而是被计算为函数返回的值。在内部，函数从arg标识的列表中检索参数，就好像va_arg被使用了一样，因此arg的状态很可能被调用所改变。在任何情况下，arg都应该在调用之前的某个时刻由va_start初始化，并且在调用之后的某个时刻，预计会由va_end释放
  参数：s -- 指向存储结果C字符串的缓冲区的指针，缓冲区应至少有n个字符的大小
    	 n -- 在缓冲区中使用的最大字节数，生成的字符串的长度至多为n-1，为额外的终止空字符留下空，size_t是一个无符号整数类型
    	 format -- 包含格式字符串的C字符串，其格式字符串与printf中的格式相同
     	 arg -- 标识使用va_start初始化的变量参数列表的值
  返回值：如果n足够大，则会写入的字符数，不包括终止空字符。如果发生编码错误，则返回负数。注意，只有当这个返回值是非负值且小于n时，字符串才被完全写入
--------------------------------------------------------------------------------------->>> gets():
  描述：char *gets(char *str)
    	 从标准输入 stdin 读取一行，并把它存储在 str 所指向的字符串中。当读取到换行符时，或者到达文件末尾时，它会停止，具体视情况而定
  参数：str -- 这是指向一个字符数组的指针，该数组存储了 C 字符串
  返回值：如果成功，该函数返回 str。如果发生错误或者到达文件末尾时还未读取任何字符，则返回 NULL 	
```

GCC用法：

```c
gcc -D_FORTIFY_SOURCE=1  仅仅只在编译时进行检查（尤其是#include <string.h>这种文件头）
gcc -D_FORTIFY_SOURCE=2  程序执行时也会进行检查（如果检查到缓冲区溢出，就会终止程序）
```

在-D_FORTIFY_SOURCE=2时，通过对数组大小来判断替换strcpy、memcpy、memset等函数名，从而达到防止缓冲区溢出的作用

