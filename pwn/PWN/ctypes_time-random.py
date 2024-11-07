from pwn import *
from ctypes import *
libc = cdll.LoadLibrary("libc.so.6")
libc.srand(libc.time(0))
libc.rand()