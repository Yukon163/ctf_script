import os
# os.chdir("C:\\Users\\86139\\Desktop")
import subprocess
from string import printable
def ByteCrack(filename,flag,length,wish,iv=0,mode=0,padding='b'):
    data = list(open(filename, 'rb').read())
    cmd=flag.split()
    cmdset={eval("0x"+i) for i in cmd}
    addr=0
    for i in range(len(data)):
        if set(data[i:i+len(cmdset)])==cmdset:
            addr=i+len(cmdset)+1
            break
    print(addr)
    print(hex(data[addr]))
    # base=""
    # for i in range(length):
    #     data[addr] = i+iv
    #     open(filename, 'wb').write(bytes(data))
    #     found=False
    #     for j in printable:
    #         if mode:
    #             try_data = (base+j).ljust(22,padding)
    #         else:
    #             try_data = (base + j)
    #         print(try_data)
    #         process = subprocess.Popen(filename, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    #                                    stderr=subprocess.PIPE)
    #         input_bytes = try_data.encode('utf-8')  # 将输入数据转换为字节
    #         process.stdin.write(input_bytes)
    #         process.stdin.flush()  # 刷新输入缓冲区
    #         # 获取输出
    #         output, error = process.communicate()
    #         s = output.decode('gbk')
    #         if wish in s:
    #             base=try_data.rstrip(padding)
    #             found=True
    #             print(base)
    #             break
    #     if found==False:
    #         print("not found")
    #         return
