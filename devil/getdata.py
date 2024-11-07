def eqdata(s):
    s = s.replace(";", "").replace(" ", "").split("\n")
    data = []
    for i in s:
        ins = i.split("=")
        data.append(eval(ins[1]))
    return data


def eqLLdata(s):
    data = []
    for i in s.replace("LL", "").split(";"):
        if "0x" in i.strip():
            ins = i.split("0x")
            datas = ins[1][::-1]
            for j in range(0, len(datas), 2):
                data.append(int(datas[j:j + 2], 16))
    return data


def texttoascii(string):
    data = [ord(i) for i in string]
    return data


def asciitotext(data):
    m = "".join(map(chr, data))
    return m


def hextotext(string):
    flag = ""
    for i in range(0, len(string), 2):
        flag += chr(int(string[i:i + 2], 16))
    return flag


def reversetext(string, n=4):
    flag = ""
    for i in range(0, len(string), n):
        flag += string[i:i + n][::-1]
    return flag
