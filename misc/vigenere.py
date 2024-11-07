# 密文
ctext = 'ivikdkdqmjglpwlzgmpfbjiidbbysljdxfgbiwwehapheysgnccyootstzabcobvrtazeywvwwazaidgazpethpvbpwobvjxgfmdobcgpfkxkszzaigcjrpetacjhuthpvhkjhpzhfpmevzeqsbyomhsdvftasfgztcobzcghfmdobcwvnvbrvkrgxdbmkfbtgbvgmptbvfmtgblbmxzweshgcbyskdtbysfwoarqhcjqeqbcuidcnchwwgnedwihptkqczgdkigdenhpzgigwvtwiasbfhatqijsbcdwzbmpgqkkthtqigmefmjsgislkcfthpvfxlszvhagsmgclhwjcsxmdtrbtiwweghuhpvgxrzcjwhcczzbvpfkvftiwwecyivqjuxchtvatcwvrbhjhpfiltcnywluobyskhaiegbdbbysktkijhatsfgztcobzcgivikvxloazbaxrqeuydfitfbbswihaphpvkthaiuogshprhmwsgnwlwslkctkcquogpggcifdfbyomwsprrldamuwltoavkaxqptonhslywlhsoiszphqfbbrcccrmwwvbcyccwkvxgolvenphmjcejhqfblivmjsmwsvyowicjvgbuhmuogspicogrslrutxbakstrvwkvxg'

# 破解密钥长度 计算重合指数

ctext.lower()
clen = len(ctext)
print("密文长度为：", clen)
maxlenkey = int(input("输入测试密钥长度上限："))
lenkey = 0


def groupzmexist(lenkey, list):  # 统计'第list'组中各字母出现次数，以数组形式返回
    zmexist = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(list - 1, clen, lenkey):
        for j in range(0, 26):
            if (ctext[i] == chr(97 + j) or ctext[i] == chr(65 + j)):
                zmexist[j] = zmexist[j] + 1
    return zmexist


#######   sum(groupzmexist(lenkey,m))   key长lenkey时第m组字符个数
#######      groupzmexist(lenkey,m)    key长lenkey时第m组各个字母出现次数数组
def count_ic(lenkey):  # 密钥长lenkey，返回该密钥长度时平均IC
    average = 0.0
    for m in range(1, lenkey + 1):
        ic = 0.0
        for i in range(0, 26):
            ic = ic + (groupzmexist(lenkey, m)[i] * (groupzmexist(lenkey, m)[i] - 1)) / (
                        sum(groupzmexist(lenkey, m)) * (sum(groupzmexist(lenkey, m)) - 1))
        average = ic + average
    return (average / lenkey)


max = 0  # IC取>0.06中最大的数
for i in range(1, maxlenkey + 1):  # 计算密钥长
    num = count_ic(i)
    if (num >= 0.06 and num > max):  # 取>0.06中最大的数
        max = num
        print("最可能密钥长度为：", i)
        lenkey = i

# 确定密钥长度后计算互重合指数确定偏移量

frame = [0 for _ in range(lenkey)]  # 相对偏移数组
judge = float(input("重合互指数判定标准："))


def count_mic(m, n, s):  # 计算第m组和第n组偏移为s(t、t+s字符相同)时的互重合指数
    mic = 0  ########组数从1开始到第lenkey组############
    for i in range(0, 26):
        mic = mic + (groupzmexist(lenkey, m)[i] * groupzmexist(lenkey, n)[(i + s) % 26]) / (
                    sum(groupzmexist(lenkey, m)) * sum(groupzmexist(lenkey, n)))  # m中第t个字符和n中第t+s个字符
    return mic


# ----------------最终计算和0.065相近的mic应该有lenkey+1个--------------------------#
count = 0  # 符合条件的mic个数
while (count < lenkey):
    for i in range(1, lenkey + 1):  # 1-lenkey个数组
        for j in range(1, lenkey + 1):  # 1-lenkey个数组
            if (i == j):
                break
            else:
                for s in range(0, 26):
                    if (count_mic(i, j, s) >= judge):  # 第i组和第j组相对位移为S成立
                        count = count + 1
                        frame[j - 1] = (frame[i - 1] + s) % 26
                        break


# 已知密钥长度和相对偏移，列出26种可能

def decrypt(cipher, key):  # 解密函数
    message = ''
    non_alpha_count = 0
    for i in range(len(cipher)):  # 遍历
        if cipher[i].isalpha():
            if cipher[i].islower():
                offset = ord(key[(i - non_alpha_count) % len(key)]) - ord('a')
                message += chr((ord(cipher[i]) - ord('a') - offset) % 26 + ord('a'))
            else:
                offset = ord(key[(i - non_alpha_count) % len(key)]) - ord('a')
                message += chr((ord(cipher[i]) - ord('A') - offset) % 26 + ord('A'))
        else:
            message += cipher[i]
            non_alpha_count += 1
    return message


for i in range(0, 26):  # 26种密钥情况和对应明文
    key = ['' for _ in range(0, lenkey)]
    for j in range(0, lenkey):
        key[j] = chr(97 + (frame[j] + i) % 26)
    print("密钥：", key)
    print("对应明文：")
    print(decrypt(ctext, key).lower())
    print()
    # 重合互指数判定标准：0.065