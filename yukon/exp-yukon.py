from pwn import *
from pwncli import *
from struct import pack
from ctypes import *

elf_name = "./dasctf_sixbytes"
io = process(elf_name)
libc = elf.libc
# io = remote("3.1.2.3", 8888)
context(os="linux", arch="amd64")
# context(os="linux", arch="amd64", log_level="debug")
elf = ELF(elf_name)
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
lg = lambda data : io.success('%s -> 0x%x' % (data, eval(str(data))))
ia = lambda: io.interactive()

def log_all():
    for lg_info in lg_infos:
        lg(lg_info)


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
def cmd(a):
    sla(menu, strencode(a))


def add(size):
    sla(menu, b"1")
    sla(b"Enter your commodity size \n", strencode(size))


def delete(idx):
    sla(menu, b"2")
    sla(b"Enter which to delete: \n", strencode(idx))

def edit(idx, content):
    sla(menu, b"3")
    sla(b"Enter which to edit: \n", strencode(idx))
    sla(b"Input the content \n", content)


def show(idx):
    sla(menu, b"4")
    sla(b"Enter which to show: \n", strencode(idx))

def g(gdb_sript = '''
    set debug-file-directory /home/yukon/glibc-all-in-one/libs/2.35-0ubuntu3.7_amd64/.debug\n
    file %s\n
    sharedlibrary\n
    file\n
    sharedlibrary\n
    ''' % elf_name):
    # gdb.attach(io)
    # gdb.attach(io, 'b printf')
    log_all()
    gdb.attach(io, gdb_sript)




ia()
# io\.recvuntil\("(.*?)"\)
# io\.recvuntil\(b"$1"\)
# io\.sendline\(str\((.*?)\)\)
# io\.sendline\(str\($1\)\.encode\(\)\)