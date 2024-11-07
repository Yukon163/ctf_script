f = open(r'C:\Users\Yukon\Desktop\RELab2\The Garden of sinners.jpg','rb')
res = open(r'C:\Users\Yukon\Desktop\RELab2\Garden_1.jpg','wb')
i = 1
while i <= 0x6f8c:
    # 每读入4字节作异或操作
    t = int.from_bytes(f.read(4),byteorder='big') ^ 0x78563412
    res.write(t.to_bytes(4,byteorder='big'))
    i += 1
f.close()
res.close()
