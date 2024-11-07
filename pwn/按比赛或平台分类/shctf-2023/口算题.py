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
# io = remote("node4.buuoj.cn", 29323)
# io = remote("node5.anna.nssctf.cn", 28604)
io = remote("112.6.51.212", 31137)


# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
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


def r():
    return (io.recv())


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


# context(os='linux', arch='amd64')
# context(os='linux', arch='amd64', log_level="debug")

ru("Press Enter to start...")
sl("")

optr_list = ["%", "×", "÷", "**", "+", "-"]

ru("Round:")
rl()
# print(rl())

while 1:
    # ru("Round:")
    # print(rl())

    recv_op = rl().decode('utf-8').split("=")[0]
    # print(recv_op)

    for i in range(len(optr_list)):
        if optr_list[i] in recv_op:
            # print("ok")
            opnd1 = int(recv_op.split(optr_list[i])[0])
            opnd2 = int(recv_op.split(optr_list[i])[1])
            optr = optr_list[i]
            break
    # print(opnd1, optr_list[i], opnd2)

    if optr == "%":
        result = opnd1 % opnd2
    elif optr == "×":
        result = opnd1 * opnd2
    elif optr == "÷":
        if opnd2 != 0:
            result = opnd1 / opnd2
        else:
            print("除数不能为零")
    elif optr == "**":
        result = opnd1 ** opnd2
    elif optr == "+":
        result = opnd1 + opnd2
    elif optr == "-":
        result = opnd1 - opnd2
    else:
        print("无效的运算符")
    sl(str(result))
    rl()
    recv_flag = rl()
    if b'flag' in recv_flag:
        print(recv_flag)
        break

inter()
