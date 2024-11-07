from pwn import *
# context(arch='amd64', os='linux', log_level='debug')

# def s(a):
#     io.send(a)
# def sa(a, b):
#     io.sendafter(a, b)
# def sl(a):
#     io.sendline(a)
# def sal(a, b):
#     io.sendlineafter(a, b)
# def r():
#     print(io.recv())
# def ru(a):
#     io.recvuntil(a)
# def rl():
#     io.recvline()
# def sla(a, b):
#     p.sendlineafter(a, b)
# def debug():
#     gdb.attach(io)
#     pause()
# def get_addr():
#     return u64(io.recvuntil(b'\x7f')[-6:].ljust(8, b'\x00'))
# def inter():
#     return io.interactive()

# context(os='linux', arch=arch)

# def padding_string(offset, bits = 64):
#     if(bits == 64):
#         return b'a' (offset - 8) + b'b' * 8
#     return (b'a' * offset - 4 + b'b' * 4)
# r = lambda x: io.recv(x)
# ra = lambda: io.recvall()
# rl = lambda: io.recvline(keepends=True)
# ru = lambda x: io.recvuntil(x, drop=True)
# s = lambda x: io.send(x)
# sl = lambda x: io.sendline(x)
# sa = lambda x, y: io.sendafter(x, y)
# sla = lambda x, y: io.sendlineafter(x, y)
# ia = lambda: io.interactive()
# c = lambda: io.close()
# li = lambda x: log.info(x)
# db = lambda x: gdb.attach(io, x)
# p = lambda x, y: success(x + '-->' + hex(y))

# def get_sb():
#     return libc_base + libc.sym['system'], libc_base + next(libc.search(b'/bin/sh\x00'))

s = lambda data: io.send(data)
sl = lambda data: io.sendline(data)
sa = lambda text, data: io.sendafter(text, data)
sla = lambda text, data: io.sendlineafter(text, data)
r = lambda: io.recv()
rl = lambda: io.recvline()
ru = lambda text: io.recvuntil(text)
uu32 = lambda: u32(io.recvuntil(b"\xff")[-4:].ljust(4, b'\x00'))
uu64 = lambda: u64(io.recvuntil(b"\x7f")[-6:].ljust(8, b"\x00"))
iuu32 = lambda: int(io.recv(10), 16)
iuu64 = lambda: int(io.recv(6), 16)
uheap = lambda: u64(io.recv(6).ljust(8, b'\x00'))
lg = lambda addr: log.info(addr)
ia = lambda: io.interactive()
# lg = lambda data : io.success('%s -> 0x%x' % (data, eval(data)))
# exec 1>&0
# puts_got_addr = io.recv()# 接收函数的got地址,比如我这里拿到puts的地址
# libc = LibcSearcher('puts',puts_got_addr)
# libc_base = puts_got_addr - libc.dump('puts')
# system = libc_base + libc.dump('system')
# binsh = libc_base + libc.dump('str_bin_sh')






