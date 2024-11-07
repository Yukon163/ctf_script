from pwn import *

elf = ELF('./PWN2')
# io = process("./PWN2")

name_list = [
             "gets",
             "puts",
             "setvbuf",
             # "write"
             ]


for i in range(len(name_list)):
    print(f"{name_list[i]}_plt = ", hex(elf.plt[name_list[i]]))
    print(f"{name_list[i]}_got = ", hex(elf.got[name_list[i]]))
