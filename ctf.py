# 1.lsb隐写
# import PIL.Image as Image
# img = Image.open('/Users/wangyu/Downloads/SI_Tree/flag.bmp')
# img_tmp = img.copy()
# pix = img_tmp.load()
# width,height = img_tmp.size
# for w in range(width):
#    for h in range(height):
#       if pix[w,h]&1 == 0:
#          pix[w,h] = 0
#       else:
#          pix[w,h] = 255
# img_tmp.show()

# 1.2最低有效位
# import cv2
# # ①读取图像
# img = cv2.imread('/Users/wangyu/Desktop/ctf acdic rubish/mmm.png', 0)
# # ②把最低有效位清空
# img -= cv2.bitwise_and(img, 0x01)
# # ③准备需要隐写的信息M
# M = cv2.imread('qrcode.jpg', 0)
# M = cv2.resize(M, img.shape)
# # 把二维码转换成0-1矩阵
# _, M = cv2.threshold(M, 30, 1, cv2.THRESH_BINARY)
# # ④将要隐写的数据设置到图像最低有效位
# img += M
# # ⑥以无损的方式保存隐写后的
# cv2.imwrite('dst.png', img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

# # 2.CRC图片宽高爆破
# import os
# import binascii
# import struct
#
# crcbp = open("/Users/wangyu/Downloads/羽毛球.png", "rb").read()  # 打开图片
# crc32frombp = int(crcbp[29:33].hex(), 16)  # 读取图片中的CRC校验值
# print(crc32frombp)
#
# for i in range(4000):  # 宽度1-4000进行枚举
#     for j in range(4000):  # 高度1-4000进行枚举
#         data = crcbp[12:16] + \
#                struct.pack('>i', i) + struct.pack('>i', j) + crcbp[24:29]
#         crc32 = binascii.crc32(data) & 0xffffffff
#         # print(crc32)
#         if (crc32 == crc32frombp):  # 计算当图片大小为i:j时的CRC校验值，与图片中的CRC比较，当相同，则图片大小已经确定
#             print(i, j)
#             print('hex:', hex(i), hex(j))

# 3.猫眼变化（用不了）
# import os
# import cv2
# import argparse
# import numpy as np
# from PIL import Image
#
#
# parser = argparse.ArgumentParser()
# parser.add_argument('-t', type=str, default=None, required=True, choices=["encode", "decode"],
#                     help='encode | decode')
# parser.add_argument('-f', type=str, default=None, required=True,
#                     help='输入文件名称')
# parser.add_argument('-n', type=int, default=1, required=False,
#                     help='输入参数n')
# parser.add_argument('-a', type=int, default=None, required=True,
#                     help='输入参数a')
# parser.add_argument('-b', type=int, default=None, required=True,
#                     help='输入参数b')
# args  = parser.parse_args()
#
#
# def arnold(img, a, b):
#     new_img = np.zeros((r, c, 3), np.uint8)
#
#     for _ in range(n):
#         for i in range(r):
#             for j in range(c):
#                 x = (i + b * j) % r
#                 y = (a * i + (a * b + 1) * j) % c
#                 new_img[x, y] = img[i, j]
#         img = np.copy(new_img)
#     return new_img
#
# def dearnold(img, n, a, b):
#     new_img = np.zeros((r, c, 3), np.uint8)
#
#     for _ in range(n):
#         for i in range(r):
#             for j in range(c):
#                 x = ((a * b + 1) * i - b * j) % r
#                 y = (-a * i + j) % c
#                 new_img[x, y] = img[i, j]
#         img = np.copy(new_img)
#     return new_img
#
# if __name__ == '__main__':
#     img_path = os.path.abspath(args.f)
#     file_name = os.path.splitext(img_path)[0].split("\\")[-1]
#     img = np.array(Image.open(img_path), np.uint8)[:,:,::-1]
#     r, c = img.shape[:2]
#     n, a, b = args.n, args.a, args.b
#
#     if args.t == "encode":
#         new_img = arnold(img, a, b)
#     elif args.t == "decode":
#         new_img = dearnold(img, n, a, b)
#     else:
#         print("[-] 图片宽高不一致, 无法进行猫脸变化!")
#         exit()
#
#     cv2.imwrite(f"./{file_name}_{n}_{a}_{b}.png", new_img)

# 3.1猫脸变换2
# import numpy as np
# import matplotlib.pyplot as plt
# import pandas as pd
#
# '''
# 功能：计算Arnold变换周期,默认为狭义Arnold变换
# 参数：
# N--正方形图像宽的像素数
# Arnold变换矩阵参数，a、b、c、d
# '''
#
#
# def Arnold_period(N, a=1, b=1, c=1, d=2):
#     # 计算(posx,posy)位置Arnold变换的周期(与整个图像Arnold周期应该一致，待证)
#     posx = 0
#     posy = 1
#     # 变换的初始位置
#     x0 = posx
#     y0 = posy
#     T = 0
#     while True:
#         x = (a * x0 + b * y0) % N
#         y = (c * x0 + d * y0) % N
#         # x0，y0同时更新
#         x0, y0 = x, y
#         T += 1
#         if (x == posx and y == posy):
#             break
#     return T
#
#
# def main():
#     N = []
#     T = []
#     for i in range(1, 11):
#         N.append(2 ** i)
#         T.append(Arnold_period(2 ** i, 1, 1, 1, 2))
#     plt.axis('off')
#     # 绘制表格展示结果
#     data = dict()
#     data['N'] = N
#     data['T'] = T
#     print(data)
#     df = pd.DataFrame(data)
#     plt.table(cellText=df.values, colLabels=df.columns, bbox=[0, 0, 1, 1], loc='center')
#     plt.show()
#
#
# if __name__ == '__main__':
#     main()

# import cv2
# import numpy as np
# import matplotlib.image as mpimg
# def de_arnold(img,shuffle_time,a,b):
#     r, c, d = img.shape
#     dp = np.zeros(img.shape, np.uint8)
#     for s in range(shuffle_time):
#         for i in range(r):
#             for j in range(c):
#                 x = ((a * b + 1) * i - b * j) % r
#                 y = (-a * i + j) % c
#                 dp[x, y, :] = img[i, j, :]
#         img = np.copy(dp)
#     return img
# img = mpimg.imread('flag.bmp')
# img = img[:, :, ::-1]
# new = de_arnold(img, 2, 1, 2)
# cv2.imshow('picture', new)
# cv2.waitKey(0)

# 4.base64隐写
# import base64
#
# txt = "/Users/wangyu/Downloads/flag-2.txt"
# bin_str = ""
# b64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
# fo = open(txt, "r")
# lines = fo.readlines()
# # print(lines)
# for line in lines:
#     s64 = "".join(line.split())
#     # print(s64)
#     r64 = "".join(str(base64.b64encode(base64.b64decode(s64)), 'utf-8').split())
#     offset = abs(b64chars.index(s64.replace('=', '')[-1]) - b64chars.index(r64.replace('=', '')[-1]))
#     equal = line.count('=')
#     if equal:
#         bin_str += bin(offset)[2:].zfill(equal * 2)
# print(''.join([chr(int(bin_str[i:i + 8], 2)) for i in range(0, len(bin_str), 8)]))
# fo.close()

# 5.gif分解脚本
# from PIL import Image
#
# savepath = "/Users/wangyu/Desktop/ctf acdic rubish/" #保存路径
#
# im = Image.open('/Users/wangyu/Desktop/ctf acdic rubish/out.gif')   #从文件加载图像
# try:
#     im.save(savepath+'{:d}.png'.format(im.tell())) #读取每一帧
#     while True:
#         im.seek(im.tell()+1) #在不同帧之间移动
#         im.save(savepath+'{:d}.png'.format(im.tell()))  #保存文件
# except:
#     pass

# 5.1gif合并每一帧脚本
# from PIL import Image
#
# path = "/Users/wangyu/Desktop/ctf acdic rubish/out.pngs/"
# save_path = '/Users/wangyu/Desktop/ctf acdic rubish/'
#
# im = Image.new('RGBA', (2 * 201, 600))  # 创建新照片
#
# imagefile = []  # 存储所有的图像的名称
# width = 0
# for i in range(0, 201):
#     imagefile.append(Image.open(path + str(i) + '.png'))  # 遍历，将图像名称存入imagfile
#
# for image in imagefile:
#     im.paste(image, (width, 0, 2 + width, 600))  # 将图片张贴到另一张图片上
#     width = width + 2
# im.save(save_path + 'flag666.png')
# im.show()

# 6.八进制转字符串
# string = '0126 062 0126 0163 0142 0103 0102 0153 0142 062 065 0154 0111 0121 0157 0113 0111 0105 0132 0163 0131 0127 0143 066 0111 0105 0154 0124 0121 060 0116 067 0124 0152 0102 0146 0115 0107 065 0154 0130 062 0116 0150 0142 0154 071 0172 0144 0104 0102 0167 0130 063 0153 0167 0144 0130 060 0113'
#
# data = string.split(' ')
# print(data)
# octs = ''
# for i in range(len(data)):
#     octs += chr(int(data[i], 8))
# print(octs)

# 7.解析二维码
# import numpy as np
# from PIL import Image
# from pyzbar import pyzbar
# import zbar
#
# # 读取文件，转成数组
# im = np.array(Image.open("/Users/wangyu/Downloads/tmp/近在眼前/hint.jpeg"))
# print(pyzbar.decode(im))
# # 返回的信息还是很多的
# """
# [
#    Decoded(data=b'http://www.bilibili.com',
#        type='QRCODE',
#        rect=Rect(left=35, top=35, width=263, height=264),
#        polygon=[Point(x=35, y=35), Point(x=35, y=297), Point(x=297, y=299), Point(x=298, y=35)])
# ]
# """
#
# # 拿到内容
# print(pyzbar.decode(im)[0].data.decode("utf-8"))  # http://www.bilibili.com

# 8.字频统计
# alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+- =\\{\\}[]"
# strings = open('/Users/wangyu/Desktop/ctf acdic rubish/CVE-2018-1160/read/11.txt').read()
#
# result = {}
# for i in alphabet:
#     counts = strings.count(i)
#     i = '{0}'.format(i)
#     result[i] = counts
#
# res = sorted(result.items(), key=lambda item: item[1], reverse=True)
# for data in res:
#     print(data)
#
# for i in res:
#     flag = str(i[0])
#     print(flag[0], end="")

# 9.gzip(2022年省赛misc)
# import gzip
# if __name__ == "__main__":
#     text = b''
#     for s in range(1, 242):
#         with gzip.open("/Users/wangyu/Desktop/ctf acdic rubish/666/" + str(s), "rb") as f_in:
#             text += f_in.read()
#     print(text)

# 10.批量重命名
# import os
#
# path = '/Users/wangyu/Desktop/ctf acdic rubish/吹着贝斯扫二维码'
# for i in os.listdir('/Users/wangyu/Desktop/ctf acdic rubish/吹着贝斯扫二维码'):
#     if i == 'flag.zip':
#         continue
#     else:
#         oldname = os.path.join(path, i)
#         newname = os.path.join(path, i + '.jpg')
#         os.rename(oldname, newname)

# 11.十六进制、字符串互转
# def GetList(string):
#     '''输入字符串，两两组合返回列表'''
#     result = []
#     now = ""
#     time = 1
#     for i in string:
#         now += i
#         if time%2==0:
#             result.append(now)
#             now = ""
#         time += 1
#     return result
# # print(GetList("123456"))
# def CharToStr(hex_num):
#     '''输入十六进制，输出十进制ascii对应的字符'''
#     return chr(int(hex_num,16))
# # print(CharToStr("2c"))
# def ToStr(string):
#     '''Hex转Str'''
#     result = ""
#     lis = GetList(string.replace("0x",""))
#     for i in lis:
#         result += CharToStr(i)
#     return result
# # print(ToStr("28372c37"))
# def FileToStr(path,save):
#     '''读取Hex文件，输出Str结果'''
#     result = ""
#     with open(path,"r") as fp:
#         string = fp.read().replace("\n","")
#         lis = GetList(string.replace("0x", ""))
#         for i in lis:
#             result += CharToStr(i)
#     with open(save,"w") as fp:
#         fp.write(result)
# # FileToStr("1.txt","2.txt")
# def CharToHex(string):
#     '''输入字符，输出十六进制，不支持输入字符串'''
#     return str(hex(ord(string))).replace("0x", "")
# # print(CharToHex(","))
# def ToHex(string):
#     '''Str转Hex'''
#     result = ""
#     for i in string:
#         result += CharToHex(i)
#     return result
# # print(ToHex("7"))
# def FileToHex(path,save):
#     '''读取Str文件，输出Hex结果'''
#     result = ""
#     with open(path, "r") as fp:
#         string = fp.read().replace("\n", "")
#         for i in string:
#             result += CharToHex(i)
#     with open(save, "w") as fp:
#         fp.write(result)
# # FileToHex("3.txt","4.txt")
# if __name__ =='__main__':#主函数
#     while True:
#         print("==============================")
#         print("     0. 退出")
#         print("     1. Hex转Str")
#         print("     2. Hex转Str(文件读取)")
#         print("     3. Str转Hex")
#         print("     4. Str转Hex(文件读取)")
#         print("==============================")
#         flag = int(input("请选择："))
#         if flag==1:
#             Hex = input("Hex:")
#             print("Str:\n",ToStr(Hex))
#         elif flag==2:
#             Hex_path = input("Hex文件路径:")
#             Save_path = input("Str保存路径:")
#             FileToStr(Hex_path,Save_path)
#             print("处理结束!")
#         elif flag==3:
#             Str = input("Str:")
#             print("Hex:\n", ToHex(Str))
#         elif flag==4:
#             Str_path = input("Str文件路径:")
#             Save_path = input("Hex保存路径:")
#             FileToHex(Str_path,Save_path)
#             print("处理结束!")
#         else:
#             break

# 11.1十六进制转十进制
# hex_string = "0x370a05303c290e045005031c2b1858473a5f052117032c39230f005d1e17"
# decimal_number = int(hex_string, 16)
# binary_string = bin(decimal_number)
#
# print("十六进制:", hex_string)
# print("十进制:", decimal_number)
# print("二进制:", binary_string)

# 12.加密破解：使用pyshark来破解加密的网络流量；
# import pyshark
# from Behinder import*
# cap=pyshark.FileCapture("C:\\Users\\86139\\Desktop\\hacker.pcapng",display_filter="http.content_length")
# tmp=[]
# for c in cap:
#     for i in c:
#         try:
#             tmp.append(i.file_data)
#         except:
#             continue
# decrypter=PHP(key='bbc49d5f83e5ZTI2NGM1NWJlCi92YXIvdG1wL3Bhc3N3b3JkMXNHdWlfMXNfc2h1bXUKYTdlYjNkZjg3NGUKae13e2ed')
# for i in tmp:
#     try:
#         data=decrypter.decrypt_req_payload(i.encode())
#         print(data)
#     except:
#         try:
#             data=decrypter.decrypt_res_payload(i.encode())
#             print(data)
#         except:
#             continue

# 13.B神的通道分离channel-split（代替stegsolve）
# import os
# import cv2
# import shutil
# import argparse
# import itertools
# import numpy as np
# from PIL import Image
#
# parser = argparse.ArgumentParser()
# parser.add_argument('-f', type=str, default=1,
#                     help='图片路径')
# parser.add_argument('-size', type=int, default=1,
#                     help='图片放大倍数(默认1倍) 待开发')
# parser.add_argument('-inversion', nargs='?', const=True, default=False,
#                     help='是否图片反色(默认关闭)')
# args = parser.parse_args()
# # INTER_NEAREST
#
# file_path = input("file_path:")
# # file_name = input("file_mame:")
# save_path = file_path + "_ChannelSplited"
#
#
# def get_channel_dic(shape):
#     try:
#         if shape[2] == 3:
#             channel_dic = ["Blue", "Green", "Red"]
#         elif shape[2] == 4:
#             channel_dic = ["Alpha", "Blue", "Green", "Red"]
#     except IndexError:
#         return ["Gray"]
#     return channel_dic
#
#
# def split_channel_bit(img, height, width):
#     '''
#     分离图片通道，依次8bit分离
#     '''
#     np_bit = [[int(i) for i in bin(img[y, x])[2:].zfill(8)] for y, x in itertools.product(range(height), range(width))]
#     np_bit = np.array(np_bit)
#     np_bit = np.where(np_bit == 0, 0, 255)  # 如果为0就是0黑色，如果为1就为255白色
#     np_bit.astype(np.uint8)  # 类型转换
#     return np_bit
#
#
# def colour_inversion(img):
#     return 255 ^ img
#
#
# if __name__ == '__main__':
#     # delete target and makedirs
#     if os.path.exists(save_path):
#         shutil.rmtree(save_path)
#     os.makedirs(save_path)
#
#     # read img
#     img = Image.open(file_path)
#     img = np.array(img, np.uint8)[:, :, ::-1]
#     # img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
#     height, width = img.shape[:2]
#     print(img.shape)
#
#     # image inversion
#     if args.inversion:
#         save_img = colour_inversion(img)
#         save_img = Image.fromarray(save_img)
#         save_img.save(os.path.join(save_path, "Colour Inversion.png"))
#
#     # split channel
#     channel_dic = get_channel_dic(img.shape)
#     for channel, channel_str in enumerate(channel_dic):
#         channel_img = img[:, :] if len(channel_dic) == 1 else img[:, :, channel]
#         np_bit = split_channel_bit(channel_img, height, width)
#         for i in range(8):
#             save_img = np_bit[:, 7 - i].reshape(height, width).astype(np.uint8)
#             save_img = Image.fromarray(save_img, "L")
#             save_img.save(os.path.join(save_path, f"{channel_str} plane {i}.png"))

# 14.1 zip-CRC32破解（4位）
# import zipfile
# import string
# import binascii
#
#
# def CrackCrc(crc):
#     for i in dic:
#         for j in dic:
#             for k in dic:
#                 for h in dic:
#                     s = i + j + k + h
#                     if crc == (binascii.crc32(s.encode())):
#                         f.write(s)
#                         return
#
#
# def CrackZip():
#     for i in range(0, 68):
#         file = '/Users/wangyu/Desktop/ctf acdic rubish/crc/out' + str(i) + '.zip'
#         crc = zipfile.ZipFile(file, 'r').getinfo('data.txt').CRC
#         CrackCrc(crc)
#
# dic = string.ascii_letters + string.digits + '+/='
#
# f = open('/Users/wangyu/Desktop/ctf acdic rubish/out.txt', 'w')
# CrackZip()
# print("CRC32碰撞完成")
# f.close

# 14.2 zip-CRC32破解（5位）

# 15套娃zip（密码就是zip名）
# import zipfile
# import os
#
# path = r"C:\xxxx\CVE-2018-1160 (4)\0573\0114\0653\0234\0976\0669\0540\0248\0275\0149\0028\0099\0894\0991\0414\0296\0241\0914"  # 这个自己把控想在哪里开始使用脚本
# file = "0140.zip"
#
#
# def un_zip(Path, File_name):  # 传入一个路径和当前路径的压缩包名字，返回解压缩后的文件名字
#     current_file = Path + os.sep + File_name  # 路径+'/'+文件名
#     # new_path=''
#     os.chdir(Path)  # 改变当前工作路径，方便添加文件夹
#
#     zip_file = zipfile.ZipFile(current_file)
#     # print(zip_file.namelist()[0])
#     new_file = zip_file.namelist()[0]  # 新解压的压缩文件为新的路径名字
#
#     # new_path=current_path + os.sep + new_file
#     # os.mkdir(new_path) #新建一个以解压出来的压缩包为名字的文件夹
#
#     # os.chdir(new_path)
#     zip_file.extractall(path=Path, members=zip_file.namelist(), pwd=File_name[0:-4].encode())  # 因为密码就是文件名
#     zip_file.close()
#
#     return new_file
#
#
# new = file
# new1 = ''
# while (1):
#     # new1=un_zip(path,new) #第一次解压出来了new1
#     if (new == ''):  # 判断是否解压完毕，是则直接退出
#         print("end:" + new1)
#         break
#
#     else:  # 否则就开始新的解压
#         new1 = un_zip(path, new)
#         print("continue:" + new1)
#         new = new1

# 16.crc宽高爆破
# import os
# import binascii
# import struct
#
# crcbp = open("/Users/wangyu/Desktop/ctf acdic rubish/dasctf/topic/output/png/00000206.png", "rb").read()    #打开图片
# crc32frombp = int(crcbp[29:33].hex(), 16)  #读取图片中的CRC校验值
# print(crc32frombp)
#
# for i in range(4000):    #宽度1-4000进行枚举
#     for j in range(4000):   #高度1-4000进行枚举
#         data = crcbp[12:16] + \
#             struct.pack('>i', i)+struct.pack('>i', j)+crcbp[24:29]
#         crc32 = binascii.crc32(data) & 0xffffffff
#         #print(crc32)
#         if(crc32 == crc32frombp):    #计算当图片大小为i:j时的CRC校验值，与图片中的CRC比较，当相同，则图片大小已经确定
#             print(i, j)
#             print('hex:', hex(i), hex(j))

# 17.二进制转二维码
# from PIL import Image
#
# MAX = 25
# pic = Image.new("RGB", (MAX, MAX))
# str = "1111111011111001001111111100000100000000110100000110111010001000101010111011011101010011110001011101101110100111001010101110110000010001110010010000011111111010101010101111111000000000011000100000000000101110110111010100010011110100111100111010101001011000110001000011011101100001001000010101111000100001001111110100110001001000100011000010111010101010011110000101111010110110101010001010010100000010100100101110011111111100100000000110111001000100011111111001100010101011011100000101111100110001100010111010110010101111110001011101000001110010111010101110101100100011111010110000010011010010011100101111111000010001000011011"
# i = 0
# for y in range(0, MAX):
#     for x in range(0, MAX):
#         if (str[i] == '0'):
#             pic.putpixel([x, y], (0, 0, 0))
#         else:
#             pic.putpixel([x, y], (255, 255, 255))
#         i = i + 1
# pic.show()
# pic.save("/Users/wangyu/Desktop/ctf acdic rubish/flag666.png")

# 18.已知像素值(255,255)、(0.0)绘图
# from PIL import Image
#
# file = open('/Users/wangyu/Desktop/ctf acdic rubish/qr.txt')
# MAX = 200
#
# picture = Image.new("RGB", (MAX, MAX))
# for y in range(MAX):
#     for x in range(MAX):
#         string = file.readline()
#         picture.putpixel([x, y], eval(string))  # 直接使用eval()可以转为元组
# picture.show()

# 19.TTL隐写（一堆63,127,255）
# import binascii
# count = 0
# str = ""
# with open('/Users/wangyu/Desktop/ctf acdic rubish/hello/output/zip/out.txt', 'r') as f:
#     for line in f:
#         num = int(line)
#         ss = bin(num)
#         while len(ss) < 10:
#             ss = ss[:2] + '0' + ss[2:]
#         # print(ss)
#         str = str + ss[2:4]
#         count += 1
#         if count == 4:
#             count = 0
#             sum = 0
#             # print(str)
#             for i in range(len(str)):
#                 if str[i] == '1':
#                     sum = sum * 2 + 1
#                 else:
#                     sum = sum * 2
#             # print(sum)
#             print(chr(sum), end="")
#             fi = open('/Users/wangyu/Desktop/ctf acdic rubish/flag.zip', "wb")
#             fi.write(binascii.unhexlify(chr(sum)))
#             fi.close()
#             str = ""

# 20.云影密码（01248）
# a="8842101220480224404014224202480122"
# s=a.split('0')
# l=[]
# print(s)
# for i in s:
#     sum=0
#     for j in i:
#         sum+=eval(j)
#     l.append(chr(sum+64))
# for i in range(len(l)):
#     print(l[i],end="")

# 21.base64套娃(适用于文件类)
# import base64
# def decode(f):
#     n = 0;
#     while True:
#         try:
#             f = base64.b64decode(f)
#             n += 1
#         except:
#             print('[+]Base64共decode了{0}次，最终解码结果如下:'.format(n))
#             print(str(f, 'utf-8'))
#             break
#
# if __name__ == '__main__':
#     f = open('/Users/wangyu/Desktop/ctf acdic rubish/_MISC-神奇的二维码-BitcoinPay.png.extracted/flag.doc', 'r').read()
#     decode(f)

# 22.各种编码的base16,32,64,85自动解码脚本
# import base64
# import re
#
#
# def baseDec(text, type):
#     if type == 1:
#         return base64.b16decode(text)
#     elif type == 2:
#         return base64.b32decode(text)
#     elif type == 3:
#         return base64.b64decode(text)
#     elif type == 4:
#         return base64.b85decode(text)
#     else:
#         pass
#
#
# def detect(text):
#     try:
#         if re.match("^[0-9A-F=]+$", text.decode()) is not None:
#             return 1
#     except:
#         pass
#
#     try:
#         if re.match("^[A-Z2-7=]+$", text.decode()) is not None:
#             return 2
#     except:
#         pass
#
#     try:
#         if re.match("^[A-Za-z0-9+/=]+$", text.decode()) is not None:
#             return 3
#     except:
#         pass
#
#     return 4
#
#
# def autoDec(text):
#     while True:
#         if b"{" in text:
#             print("\n" + text.decode())
#             break
#
#         code = detect(text)
#         text = baseDec(text, code)
#
#
# # with open("", 'rb') as f:
# #     flag = f.read()
# flag = b"bYeNQXYZXbXZQfW31FGzzD0m0FHQ9RR85FFQYMB9M=lmo2ku11z0uiz="
#
# autoDec(flag)

# 23.转ascii码
# s = '10210897103375566531005253102975053545155505050521025256555254995410298561015151985150375568'
# temp = ''
#
# while len(s):
#     if int(s[:3]) < 127:
#         temp += chr(int(s[:3]))
#         s = s[3:]
#     else:
#         temp += chr(int(s[:2]))
#         s = s[2:]
# print(temp)

# 24.RGB转图片
# from PIL import Image
#
# # load image_list from your data or use the existing one
# image_list = [
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
#      255, 255, 255, 255, 255, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
#      255, 255, 255, 255, 255, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
#      255, 255, 255, 255, 255, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
#      255, 255, 255, 255, 255, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0, 0, 255, 0, 0, 0, 255, 255, 0, 0, 0, 0, 0, 0, 0, 255, 255,
#      255, 255],
#     [255, 255, 255, 255, 0, 255, 255, 255, 255, 255, 0, 255, 0, 255, 255, 0, 255, 0, 0, 255, 255, 255, 0, 255, 255, 255,
#      255, 255, 0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 0, 0, 0, 255, 0, 255, 255, 0, 0, 255, 255, 0, 0, 0, 255, 255, 0, 255, 0, 0, 0, 255, 0,
#      255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 0, 0, 0, 255, 0, 255, 0, 0, 255, 0, 0, 255, 0, 0, 0, 255, 0, 255, 0, 0, 0, 255, 0, 255,
#      255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 0, 0, 0, 255, 0, 255, 0, 255, 255, 255, 255, 255, 255, 255, 255, 255, 0, 255, 0, 0, 0,
#      255, 0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 255, 255, 255, 255, 0, 255, 0, 255, 255, 255, 0, 255, 255, 0, 255, 255, 0, 255, 255,
#      255, 255, 255, 0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 0, 0, 0, 0, 0, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 0, 0, 0, 0, 0, 0, 255,
#      255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 0, 0, 0, 255, 255, 255, 255, 255, 255, 255, 255,
#      255, 255, 255, 255, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 0, 255, 255, 0, 255, 255, 255, 255, 0, 0, 0, 0, 255, 255, 255, 255, 0, 0, 0,
#      255, 0, 0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 0, 255, 255, 255, 0, 0, 255, 0, 0, 0, 0, 255, 255, 255, 0, 0, 255, 255, 255, 0,
#      0, 0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 0, 255, 255, 255, 0, 255, 255, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 255, 255, 255,
#      255, 0, 0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 0, 0, 255, 255, 0, 0, 0, 255, 255, 0, 0, 0, 255, 255, 255, 255, 255, 0, 255,
#      255, 0, 0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 0, 255, 255, 0, 255, 0, 0, 255, 255, 255, 255, 255, 255, 255, 255, 0, 0, 0, 255, 255, 255,
#      255, 0, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 0, 0, 255, 255, 0, 255, 255, 255, 255, 0, 0, 0, 0, 255, 0, 255, 255, 0, 0, 255, 0, 0, 0,
#      0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 255, 0, 255, 255, 0, 0, 255, 255, 255, 0, 255, 0, 0, 0, 0, 255, 0, 0, 255, 0, 0, 255,
#      0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 0, 0, 0, 0, 255, 255, 0, 255, 255, 255, 0, 0, 0, 255, 255, 0, 0, 255, 0, 0, 255, 255, 0,
#      255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 0, 0, 255, 255, 255, 0, 255, 0, 0, 0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 0, 255,
#      255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 0, 0, 0, 0, 255, 0, 0, 255, 0, 255, 255, 255, 0, 0,
#      255, 0, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 0, 0, 0, 0, 0, 0, 255, 255, 255, 0, 0, 0, 0, 255, 255, 0, 255, 0, 255, 0, 255, 255, 0, 0,
#      255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 255, 255, 255, 255, 0, 255, 255, 255, 255, 0, 255, 0, 0, 0, 0, 255, 255, 255, 0, 255,
#      0, 255, 0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 0, 0, 0, 255, 0, 255, 255, 255, 255, 0, 0, 0, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 255,
#      255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 0, 0, 0, 255, 0, 255, 0, 255, 255, 255, 0, 0, 255, 255, 255, 0, 255, 0, 0, 255, 0, 0,
#      255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 0, 0, 0, 255, 0, 255, 255, 255, 255, 255, 0, 255, 0, 255, 255, 255, 0, 255, 0, 0, 0,
#      255, 0, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 255, 255, 255, 255, 255, 0, 255, 255, 0, 255, 0, 0, 255, 255, 0, 255, 0, 0, 0, 255, 255,
#      255, 255, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 0, 0, 0, 0, 0, 0, 0, 255, 255, 0, 0, 0, 255, 255, 255, 0, 255, 255, 255, 0, 255, 255, 0, 0, 0,
#      255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
#      255, 255, 255, 255, 255, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
#      255, 255, 255, 255, 255, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
#      255, 255, 255, 255, 255, 255, 255, 255, 255, 255],
#     [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
#      255, 255, 255, 255, 255, 255, 255, 255, 255, 255]]
# height = len(image_list)
# width = len(image_list[0])
#
# # create a new image
# new_image = Image.new("RGB", (width, height))
#
# # set the pixels of the new image
# for y in range(height):
#     for x in range(width):
#         new_image.putpixel((x, y), image_list[y][x])
#
# # save the new image
# new_image.save("/Users/wangyu/Desktop/ctf acdic rubish/new_flag.png")

# 25.流量题提取icmp数据包
# from scapy.all import *
# from scapy.layers.inet import ICMP
#
# packets = rdpcap('/Users/wangyu/Desktop/ctf acdic rubish/buu/CVE-2018-1160.pcapng')  # rdpcap()读取pcapng文件
# for packet in packets:  # 遍历每一个数据包
#     if packet.haslayer(ICMP):  # haslayer()判断数据包的类型，此处为ICMP
#         if packet[ICMP].type == 0:  # 每一个ICMP的type值为0的包
#             print((packet[ICMP].load[-8:]).decode('utf-8'),end="")
#             # 每个数据包的最后8位是有效数据

# 26.pickle反序列化
# import pickle
# with open("/Users/wangyu/Desktop/ctf acdic rubish/buu/pickle.txt", "rb+") as fp: #pickle序列化之后转化回字符串
#     a=pickle.load(fp)
#     pickle=str(a)
#     with open("/Users/wangyu/Desktop/ctf acdic rubish/buu/pickle", "w") as fw:
#         fw.write(pickle)

# 27.python图片切分（一张图片切分为多张小图片）
# -*- coding: utf-8 -*-
# """
# Spyder Editor
#
# This is a temporary script file.
# """
#
# import os
# from PIL import Image
#
# def splitimage(src, rownum, colnum, dstpath):
#     img = Image.open(src)
#     w, h = img.size
#     if rownum <= h and colnum <= w:
#         print('Original image info: %sx%s, %s, %s' % (w, h, img.format, img.mode))
#         print('开始处理图片切割, 请稍候...')
#
#         s = os.path.split(src)
#         if dstpath == '':
#             dstpath = s[0]
#         fn = s[1].split('.')
#         basename = fn[0]
#         ext = fn[-1]
#
#         num = 0
#         rowheight = h // rownum
#         colwidth = w // colnum
#         for r in range(rownum):
#             for c in range(colnum):
#                 box = (c * colwidth, r * rowheight, (c + 1) * colwidth, (r + 1) * rowheight)
#                 img.crop(box).save(os.path.join(dstpath, basename + '_' + str(num) + '.' + ext), ext)
#                 num = num + 1
#
#         print('图片切割完毕，共生成 %s 张小图片。' % num)
#     else:
#         print('不合法的行列切割参数！')
#
# src = input('请输入图片文件路径：')
# if os.path.isfile(src):
#     dstpath = input('请输入图片输出目录（不输入路径则表示使用源图片所在目录）：')
#     if (dstpath == '') or os.path.exists(dstpath):
#         row = int(input('请输入切割行数：'))
#         col = int(input('请输入切割列数：'))
#         if row > 0 and col > 0:
#             splitimage(src, row, col, dstpath)
#         else:
#             print('无效的行列切割参数！')
#     else:
#         print('图片输出目录 %s 不存在！' % dstpath)
# else:
#     print('图片文件 %s 不存在！' % src)

# 轮异或
# key = "youshouldusethistoxorsomething"
# data = "0x370a05303c290e045005031c2b1858473a5f052117032c39230f005d1e17"[2:]
# c = [int(data[i:i + 2], 16) for i in range(0, len(data), 2)]
# for i in range(len(c)):
#     c[i] ^= ord(key[i % len(key)])
# print("".join(map(chr, c)))