> 文章改动自：[https://www.52pojie.cn/thread-1117330-1-1.html](https://www.52pojie.cn/thread-1117330-1-1.html)
>

下面我们使用IDApython来解题看看它的威力究竟如何：

# XCTF simple-unpack
首先看一下文件的信息，发现加了upx的壳，使用官方工具进行脱壳

```powershell
PS D:\南阳理工学院\NYSEC战队\CTF\CTF-TOOLS\Reverse\upx-3.96-win64> ./upx -d simple-unpack
                       Ultimate Packer for eXecutables
                          Copyright (C) 1996 - 2020
UPX 3.96w       Markus Oberhumer, Laszlo Molnar & John Reiser   Jan 23rd 2020

        File size         Ratio      Format      Name
   --------------------   ------   -----------   -----------
    912808 <-    352624   38.63%   linux/amd64   simple-unpack

Unpacked 1 file.
PS D:\南阳理工学院\NYSEC战队\CTF\CTF-TOOLS\Reverse\upx-3.96-win64>
```

拖入IDA进行分析：

说实话，这道题使用IDA-python进行解题有点大材小用了，因为上来就可以得到flag。。。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593418200853-d72992cf-d450-4084-80ea-df8d0a3a7eaa.png)

图中的flag就是flag：flag{Upx_1s_n0t_a_d3liv3r_c0mp4ny}

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593418282361-ffa31fae-0137-4ed7-a6c4-92e4ef7c34b4.png)

当然，由于我们学习的是IDA python，因此我们还得看一下代码怎么写（请假装我们不知道flag）。

先打开汇编：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593418483468-13c390c8-516d-4b4b-92db-1c460c9e29ed.png)

可以看到：

```plain
.text:00000000004009DF                 mov     esi, offset flag ; "flag{Upx_1s_n0t_a_d3liv3r_c0mp4ny}"
```

当使用脚本找到“mov esi,offset flag"时，可以通过取值函数获得flag所在的地址，进而通过循环结构获取flag整个字符串。

```python
def GetStr(start,end):
    flag=''
    for addr in range(start,end):
        #判断有没有找到'mov  esi, offset flag'
        if GetOpnd(addr,0)=='esi' and 'flag' in GetOpnd(addr,1):
            address=hex(Dword(addr))[0:8]#获取flag所在的地址
            taddress=int(address,16)#把地址转换成十进制数
            while(1):#使用循环结构获取flag
                flag+=chr(Byte(taddress))
                #判断flag读取是否结束
                if chr(Byte(taddress))=='}':
                    break
                taddress+=1
            print flag
            break
# 遍历所有的段
for seg in Segments():  
    #如果为代码段，则调用GetStr
    if SegName(seg) == '.text':
        GetStr(seg,SegEnd(seg))
```

> **<font style="color:#F5222D;">idc.GetOpnd(ea, n)- 返回操作数，n表示第几个操作数</font>****<font style="color:#F5222D;">，从0开始，如：</font>**
>
> **<font style="color:#F5222D;">mov  esi, offset flag</font>**
>
> **<font style="color:#F5222D;"> GetOpnd(addr,0)=='esi' and 'flag' in GetOpnd(addr,1)</font>**
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593419426231-1a6f6da0-3b28-45c5-b162-7aa2b751f19b.png)

# XCTF Shuffle
将文件拖入IDA中，来到main函数

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  time_t v3; // ebx
  __pid_t v4; // eax
  unsigned int v5; // ST18_4
  unsigned int v6; // ST1C_4
  char v7; // ST20_1
  signed int i; // [esp+14h] [ebp-44h]
  char s; // [esp+24h] [ebp-34h]
  char v11; // [esp+25h] [ebp-33h]
  char v12; // [esp+26h] [ebp-32h]
  char v13; // [esp+27h] [ebp-31h]
  char v14; // [esp+28h] [ebp-30h]
  char v15; // [esp+29h] [ebp-2Fh]
  char v16; // [esp+2Ah] [ebp-2Eh]
  char v17; // [esp+2Bh] [ebp-2Dh]
  char v18; // [esp+2Ch] [ebp-2Ch]
  char v19; // [esp+2Dh] [ebp-2Bh]
  char v20; // [esp+2Eh] [ebp-2Ah]
  char v21; // [esp+2Fh] [ebp-29h]
  char v22; // [esp+30h] [ebp-28h]
  char v23; // [esp+31h] [ebp-27h]
  char v24; // [esp+32h] [ebp-26h]
  char v25; // [esp+33h] [ebp-25h]
  char v26; // [esp+34h] [ebp-24h]
  char v27; // [esp+35h] [ebp-23h]
  char v28; // [esp+36h] [ebp-22h]
  char v29; // [esp+37h] [ebp-21h]
  char v30; // [esp+38h] [ebp-20h]
  char v31; // [esp+39h] [ebp-1Fh]
  char v32; // [esp+3Ah] [ebp-1Eh]
  char v33; // [esp+3Bh] [ebp-1Dh]
  char v34; // [esp+3Ch] [ebp-1Ch]
  char v35; // [esp+3Dh] [ebp-1Bh]
  char v36; // [esp+3Eh] [ebp-1Ah]
  char v37; // [esp+3Fh] [ebp-19h]
  char v38; // [esp+40h] [ebp-18h]
  char v39; // [esp+41h] [ebp-17h]
  char v40; // [esp+42h] [ebp-16h]
  char v41; // [esp+43h] [ebp-15h]
  char v42; // [esp+44h] [ebp-14h]
  char v43; // [esp+45h] [ebp-13h]
  char v44; // [esp+46h] [ebp-12h]
  char v45; // [esp+47h] [ebp-11h]
  char v46; // [esp+48h] [ebp-10h]
  char v47; // [esp+49h] [ebp-Fh]
  char v48; // [esp+4Ah] [ebp-Eh]
  char v49; // [esp+4Bh] [ebp-Dh]
  unsigned int v50; // [esp+4Ch] [ebp-Ch]

  v50 = __readgsdword(0x14u);
  s = 83;
  v11 = 69;
  v12 = 67;
  v13 = 67;
  v14 = 79;
  v15 = 78;
  v16 = 123;
  v17 = 87;
  v18 = 101;
  v19 = 108;
  v20 = 99;
  v21 = 111;
  v22 = 109;
  v23 = 101;
  v24 = 32;
  v25 = 116;
  v26 = 111;
  v27 = 32;
  v28 = 116;
  v29 = 104;
  v30 = 101;
  v31 = 32;
  v32 = 83;
  v33 = 69;
  v34 = 67;
  v35 = 67;
  v36 = 79;
  v37 = 78;
  v38 = 32;
  v39 = 50;
  v40 = 48;
  v41 = 49;
  v42 = 52;
  v43 = 32;
  v44 = 67;
  v45 = 84;
  v46 = 70;
  v47 = 33;
  v48 = 125;
  v49 = 0;
  v3 = time(0);
  v4 = getpid();
  srand(v3 + v4);
  for ( i = 0; i <= 99; ++i )
  {
    v5 = rand() % 0x28u;
    v6 = rand() % 0x28u;
    v7 = *(&s + v5);
    *(&s + v5) = *(&s + v6);
    *(&s + v6) = v7;
  }
  puts(&s);
  return 0;
}
```

经过分析，最下面的代码全部都是花指令，没有什么用，我们对上面的值转换一下即可得到flag

<font style="color:#444444;">那么用IDA-python脚本，转换这些数字，该脚本遍历代码段的指令，找到含有这些数字的指令，取出进行转换就可获取flag。代码如下：</font>

```python
def GetAns(start,end):
    flag=''
    for addr in range(start-4,end):
        #当前地址的下一个地址
        #判断下一个地址所在的指令是否为mov [esp+xxh], al
        if GetOpnd(addr,1)=='al' and 'esp' in GetOpnd(addr,0):
            #判断当前地址所有的指令是否是'mov  eax, xxh'
            if GetOpnd(addr-5,0)=='eax':
                #获取十六进制数
                hex=GetOpnd(addr-4,1)[:2]
                #转换成10进制数
                Int=int(hex,16)
                flag+=chr(Int)
                if chr(Int)=='}':
                    break
    print flag
# 遍历所有的段
for seg in Segments():  
    #如果为代码段，则调用GetAns
    if SegName(seg) == '.text':
        GetAns(seg,SegEnd(seg))
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593420022447-f1fdf6f9-d783-41cd-9c8d-ecbdc2749236.png)

# XCTF re2-cpp-is-awesome
先用以下脚本判断IDA中的循环结构，**<font style="color:#F5222D;">当跳转指令后面接的地址高于跳转指令所在的地址时，该跳转指令为循环跳转指令并加注释</font>**，代码如下。使用该脚本后可以看到关键的循环函数，在该循环里有程序自定义的数组。

> **<font style="color:#F5222D;">这是通用脚本</font>**
>

```python
# -*- coding:utf-8 -*-
#把大写字母转换成小写
def SwapToXiao(c):
    t=32
    return chr(ord(c)+t)
def isJmp(addr):
    SzOp=['JO','JNO','JB','JNB','JE','JNE','JBE','JA','JS','JNS','JP','JNP','JL','JNL','JNG','JG','JCXZ','JECXZ','JMP','JMPE']
    llen=len(SzOp)
    for i in range(0,llen):
        SwapAns=''
        #把SzOp数组中所有字符串转换成小写字符串
        for c in SzOp[i]:
            SwapAns+=SwapToXiao(c)
        #加到SzOp数组中
        SzOp.append(SwapAns)
    #获取操作指令
    Op=GetMnem(addr)
    #判断是否是操作指令
    if isCode(GetFlags(addr)):
        #判断是否是跳转指令
        for Sin in SzOp:
            if Sin==Op:
                return 1
    return 0
def isCir(start,end):
    for ea in range(start,end):
        if isJmp(ea)==1:
            #获取跳转地址
            new_addr=GetDisasm(ea)[-6:]
            #判断是否为跳转地址
            if new_addr[-1:]<='9' and new_addr[-1:]>='0':
                if int(new_addr,16)<ea:
                    #添加注释
                    MakeComm(ea,"循环跳转指令")
# 遍历所有的段
for seg in Segments():  
    #如果为代码段
    if SegName(seg) == '.text':
        isCir(seg,SegEnd(seg))
```

效果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593421319631-be2b3a95-8593-4e03-b8b6-94c5a72bc748.png)

按F5，看到关键代码

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593421455776-24f8cc39-494d-4e87-895b-901d51930701.png)

接着使用脚本获取这两个数组并获取flag，代码如下：

```python
szint=[]
#该函数获取flag
def GetAns(start,end,tstr):
    flag=''
    for i in szint:
        flag+=tstr[i]
    print flag
#该函数获取str字符串
def GetStr():
    str_addr=0x400E58
    tstr=''
    while(1):
        #判断循环是否结束
        if hex(Byte(str_addr))=='0x0' and hex(Byte(str_addr+1))=='0x0':
            break
        #叠加字符串字符生成字符串
        tstr+=chr(Byte(str_addr))
        str_addr+=1
    return tstr
#获取整数数组
def getSzInt(start,end):
    for addr in range(start,end): #rax*4
        #判断是否是mov eax, IntSz[rax*4]指令语句，在该语句中可以获取整数数组的地址
        if 'rax*4' in GetOpnd(addr,1):
            #获取整数数组的地址
            address=hex(Dword(addr+3))[0:8]
            taddress=int(address,16)
            #获取整数数组
            while(1):
                if Dword(taddress)>0x7f:
                    break
                szint.append(Dword(taddress))
                taddress+=4
            break
for seg in Segments():
    if SegName(seg) == '.text':
        getSzInt(seg,SegEnd(seg))
        str1=GetStr()
        GetAns(seg,SegEnd(seg),str1)
```

显示结果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593421521020-d5cf9ebe-d6f3-4718-a5c5-2b0dab599c4b.png)

# 2018 TSRC 团队赛 第二题 半加器
在x64dbg中运行，搜索字符串后发现'invalid argument'字符串，并且该字符串传入到函数的参数中，那么程序运行时处理了该字符串。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593421521064-74f48965-9ba7-4d8b-92e2-ea3f8000eb36.png)

invalid argument'字符串在只读数据段中，使用如下脚本可以找到该字符串，随后找到调用它的地方。该脚本从只读数据段开始遍历，找到字符串后跳转到相应的地址，使用XrefsTo函数找到调用它的位置并在右边加上注释，跳转到调用的位置。

```python
#invalid argument的前12个字符序列
str1='69 6E 76 61 6C 69 64 20 61 72 67 75'
def GetStrPos(start,end):
    #查找str2字符串所在的位置
    BinaryAddr=FindBinary(start,SEARCH_DOWN,str1)
    #判断查找是否失败
    if hex(BinaryAddr)=='0xffffffffL':
        print 'not bin'
    else:
        print 'Binary ',hex(BinaryAddr)
        #跳转到字符串所在的位置
        Jump(BinaryAddr)
    #遍历调用该字符串的位置
    for refhs in XrefsTo(BinaryAddr, flags=0):
        print "x: %s x.frm 0x%x"%(refhs,refhs.frm)
        Jump(refhs.frm)
        #做注释
        MakeComm(refhs.frm,"使用了invalid argument字符串")
        #询问用户
        AskYN(1,'看完'+hex(refhs.frm)+'地址处的代码吗？')
 
for seg in Segments():  
    #如果为只读数据段，则调用GetStrPos
    if SegName(seg) == '.rdata':
        #print 'seg ',hex(seg)
        GetStrPos(seg,SegEnd(seg))
```

运行结果：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593421521020-3e6dcbb0-561d-447c-a908-8df5d8b86e22.png)

那么接下来寻找程序中的算术或者逻辑操作码，找到后，添加注释并输出地址。我使用GetDisasm()函数获取某地址处的字符串(包括指令和注释),随后清除字符串的空格和判断程序中是否含有注释。

```python
import re
#算术逻辑操作码
CalOp=['mul','imul','or','not','div','xor']
def isCalOp(Op):
    for i in CalOp:
        if Op==i:
            return 1
    return 0
#清空字符串中的空格
def clearspace(str1):
    str2=''
    for i in str1:
        if i==' ':
            continue
        else:
            str2+=i
    return str2
#判断整个指令是否有注释
def isComment(str):
    for i in str:
        if i==';':
            return True
    return False
#判断算术逻辑指令有没有使用十六进制数进行计算
def isHex(str1):
    #使用正则表达式构造匹配十六进制数的字符串
    pattern= re.compile(r'[-]*[0-9a-fA-F]+')
    sNum=''
    try:
        if isComment(str1):
            xb=str1.rindex(';')
            sNum=str1[str1.rindex(',')+1:xb]
        else:
            sNum=str1[str1.rindex(',')+1:]
        #找到十六进制字符串，若没有找到，则抛出异常
        ans=pattern.match(sNum)
        #判断找到的十六进制数是否准确
        if ans.group(0)==sNum and sNum!='0':
            return 1
    except:
        return 0
    else:
        return 0
```

随后判断算术逻辑指令中是否含有十六进制操作数，如果含有则输出地址，判断的思路是：获取最后一个操作数，通过正则表达式的方式判断该操作数是否为十六进制操作数。

```python
import re
#算术逻辑操作码
CalOp=['mul','imul','or','not','div','xor']
def isCalOp(Op):
    for i in CalOp:
        if Op==i:
            return 1
    return 0
#清空字符串中的空格
def clearspace(str1):
    str2=''
    for i in str1:
        if i==' ':
            continue
        else:
            str2+=i
    return str2
#判断整个指令是否有注释
def isComment(str):
    for i in str:
        if i==';':
            return True
    return False
#判断算术逻辑指令有没有使用十六进制数进行计算
def isHex(str1):
    #使用正则表达式构造匹配十六进制数的字符串
    pattern= re.compile(r'[-]*[0-9a-fA-F]+')
    sNum=''
    try:
        if isComment(str1):
            xb=str1.rindex(';')
            sNum=str1[str1.rindex(',')+1:xb]
        else:
            sNum=str1[str1.rindex(',')+1:]
        #找到十六进制字符串，若没有找到，则抛出异常
        ans=pattern.match(sNum)
        #判断找到的十六进制数是否准确
        if ans.group(0)==sNum and sNum!='0':
            return 1
    except:
        return 0
    else:
        return 0
```

分析地址中的算术逻辑指令，双击输出的地址就能跳转到汇编窗口，发现有三个地方的指令起到关键作用，据此写下求flag的脚本。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593421521019-9fa60507-0c8c-453b-a135-0e3db3386377.png)



![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593421521054-e103e4d8-866f-4c11-aec9-1e316d1369e9.png)



![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593421521117-8a2dc9f7-654a-455c-996e-0397dfd44124.png)

```python
def GetOp(start,end):
for addr in range(start,end):
#获取操作指令
Op=GetMnem(addr)
#判断是否是操作指令
if isCode(GetFlags(addr)):
if isCalOp(Op)==1:
#获取某地址处的字符串，包括指令和注释
Comm=GetDisasm(addr)
Comm=clearspace(Comm)
if isHex(Comm)==1:
#往ida中添加注释
MakeComm(addr,"使用了操作码："+Op)
print "Op_addr ",hex(addr)
for seg in Segments(): 
#是否为代码段
if SegName(seg) == '.text':
GetOp(seg,SegEnd(seg))
```

<font style="color:#444444;">运行结果：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593421521088-71d5dbd1-5b87-423a-93b3-3c6ac2661683.png)

