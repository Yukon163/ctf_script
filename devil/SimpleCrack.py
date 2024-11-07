'''
简单加密方式爆破
下标i,常数n(-256~256)
1.+n
2.^n
3.^i^n
4.+i+n
5.-i+n
6.(-i)^i
7.^i-i
8.(+i)^i
9.^i+i
'''
from string import printable,hexdigits
table="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-{}!?"
# table = printable
Min=-256
Max=256
flag=""
def hexdigitscheck(string):
    for i in string:
        if i not in hexdigits:
            return False
    return True
def checkenc(string):
    if "h" in string or "H" in string:
        string=string.replace("h", "").replace("H", "").replace(",", "")
    try:
        data=[]
        if "," in string:
            data=eval("["+string+"]")
        elif len(string)%2==0 and hexdigitscheck(string):
             for i in range(0,len(string),2):
                data.append(int(string[i:i+2],16))
        else:
            for i in string:
                data.append(ord(i))
        return data
    except:
        return None
def printablecheck(string):
    for i in string:
        if i not in printable:
            return False
    return True
def tablecheck(string):
    for i in string:
        if i not in table:
            return False
    return True
def checkflag(data):
    try:
        m="".join(map(chr,data))
        if printablecheck(m):
            return m
    except:
        return None
def makesure():
    return
    # print("Y or N:")
    # ans="s"
    # while ans not in "YyNn":
    #     ans=input()
    #     if ans=="Y" or ans=="y":
    #         exit()
    #     elif ans=="N" or ans=="n":
    #         return
def select(string):
    if string==None:
        return None
    if "flag" in string or "ctf" in string or flag in string or tablecheck(string):
        return string
    return None
def caesarn(data,n):
    data=[data[i]+n for i in range(len(data))]
    return select(checkflag(data))
def xorn(data,n):
    data=[data[i]^n for i in range(len(data))]
    return select(checkflag(data))
def xorin(data,n):
    data = [data[i] ^ i^n for i in range(len(data))]
    return select(checkflag(data))
def addin(data,n):
    data = [data[i]+i+n for i in range(len(data))]
    return select(checkflag(data))
def subin(data,n):
    data = [data[i]-i+n for i in range(len(data))]
    return select(checkflag(data))
def subixorin(data,n):
    data = [(data[i]-i)^i+n for i in range(len(data))]
    return select(checkflag(data))
def xorisubin(data,n):
    data = [data[i]^i-i+n for i in range(len(data))]
    return select(checkflag(data))
def addixorin(data,n):
    data = [(data[i]+i)^i+n for i in range(len(data))]
    return select(checkflag(data))
def xoriaddin(data,n):
    data = [data[i]^i+i+n for i in range(len(data))]
    return select(checkflag(data))
def SimpleCrack(data,n="flag"):
    global flag
    flag=n
    for i in range(Min,Max+1):
        m=caesarn(data,i)
        if m!=None:
            print(m)
            makesure()
    for i in range(Min,Max+1):
        m=xorn(data,i)
        if m!=None:
            print(m)
            makesure()
    for i in range(Min,Max+1):
        m=xorin(data,i)
        if m!=None:
            print(m)
            makesure()
    for i in range(Min,Max+1):
        m=addin(data,i)
        if m!=None:
            print(m)
            makesure()
    for i in range(Min,Max+1):
        m=subin(data,i)
        if m!=None:
            print(m)
            makesure()
    for i in range(Min,Max+1):
        m=subixorin(data,i)
        if m!=None:
            print(m)
            makesure()
    for i in range(Min,Max+1):
        m=xorisubin(data,i)
        if m!=None:
            print(m)
            makesure()
    for i in range(Min,Max+1):
        m=addixorin(data,i)
        if m!=None:
            print(m)
            makesure()
    for i in range(Min,Max+1):
        m=xoriaddin(data,i)
        if m!=None:
            print(m)
            makesure()