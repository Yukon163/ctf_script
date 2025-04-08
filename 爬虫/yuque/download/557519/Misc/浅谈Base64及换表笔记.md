参考资料：

[https://www.cnblogs.com/sylar-liang/p/4567792.html](https://www.cnblogs.com/sylar-liang/p/4567792.html)

[https://www.cnblogs.com/dyhaohaoxuexi/p/11025985.html](https://www.cnblogs.com/dyhaohaoxuexi/p/11025985.html)

wp说是base64换表，那就是base64换表，反正也不会。。。

-----------------------------------------------------------------------------------------------------------------------

python代码：（网上抄的）<font style="color:#C586C0;"></font>



```python
import base64
import string
str1 = "0g371wvVy9qPztz7xQ+PxNuKxQv74B/5n/zwuPfX"#待解密的字符串
string1 = "abcdefghijklmnopqrstuvwxyz0123456789+/ABCDEFGHIJKLMNOPQRSTUVWXYZ"#base64换过之后的表
string2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"#默认表，无需改动
print (base64.b64decode(str1.translate(str.maketrans(string1,string2))))
#运行结果：b'hgame{b45e6a_i5_50_eazy_6VVSQ}'
```

-----------------------------------------------------------------------------------------------------------------------

C语言代码：（wp中的，网上也有）//Apple iOS的base64编解码



```c
#include <string.h>
#include <stdio.h>
static const char basis_64[] =
    "abcdefghijklmnopqrstuvwxyz0123456789+/ABCDEFGHIJKLMNOPQRSTUVWXYZ";//base64换过后的表
unsigned char pr2six[256] =
    {
        /* ASCII table */
  //无需更改，说实话，这个表没看懂
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 62, 64, 64, 64, 63,
        52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 64, 64, 64, 64, 64, 64,
        64,   0,   1,   2,   3,   4,   5,   6,   7,   8,  9, 10, 11, 12, 13, 14,
        15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 64, 64, 64, 64, 64,
        64, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
        41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
        64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64};
int Base64decode_len(const char *bufcoded)
{
  int nbytesdecoded;
  register const unsigned char *bufin;
  register int nprbytes;
  bufin = (const unsigned char *)bufcoded;
  while (pr2six[*(bufin++)] <= 63)
    ;
  nprbytes = (bufin - (const unsigned char *)bufcoded) - 1;
  nbytesdecoded = ((nprbytes + 3) / 4) * 3;
  return nbytesdecoded + 1;
}
int Base64decode(char *bufplain, const char *bufcoded)
{
  auto l = strlen(basis_64);
  for (int i = 0; i < l; ++i)
  {
    pr2six[basis_64[i]] = i;
  }
  int nbytesdecoded;
  register const unsigned char *bufin;
  register unsigned char *bufout;
  register int nprbytes;
  bufin = (const unsigned char *)bufcoded;
  while (pr2six[*(bufin++)] <= 63)
    ;
  nprbytes = (bufin - (const unsigned char *)bufcoded) - 1;
  nbytesdecoded = ((nprbytes + 3) / 4) * 3;
  bufout = (unsigned char *)bufplain;
  bufin = (const unsigned char *)bufcoded;
  while (nprbytes > 4)
  {
    *(bufout++) =
        (unsigned char)(pr2six[*bufin] << 2 | pr2six[bufin[1]] >> 4);
    *(bufout++) =
        (unsigned char)(pr2six[bufin[1]] << 4 | pr2six[bufin[2]] >> 2);
    *(bufout++) =
        (unsigned char)(pr2six[bufin[2]] << 6 | pr2six[bufin[3]]);
    bufin += 4;
    nprbytes -= 4;
  }
  /* Note: (nprbytes == 1) would be an error, so just ingore that case */
  if (nprbytes > 1)
  {
    *(bufout++) =
        (unsigned char)(pr2six[*bufin] << 2 | pr2six[bufin[1]] >> 4);
  }
  if (nprbytes > 2)
  {
    *(bufout++) =
        (unsigned char)(pr2six[bufin[1]] << 4 | pr2six[bufin[2]] >> 2);
  }
  if (nprbytes > 3)
  {
    *(bufout++) =
        (unsigned char)(pr2six[bufin[2]] << 6 | pr2six[bufin[3]]);
  }
  *(bufout++) = '\0';
  nbytesdecoded -= (4 - nprbytes) & 3;
  return nbytesdecoded;
}
int main()
{
  char buffer[0x100] = {};
  Base64decode(buffer, "0g371wvVy9qPztz7xQ+PxNuKxQv74B/5n/zwuPfX");//待解密的字符串
  printf("%s", buffer);//输出：hgame{b45e6a_i5_50_eazy_6VVSQ}
}
```

**<font style="color:#D4D4D4;"></font>**

-----------------------------------------------------------------------------------------------------------------------

**浅谈base64编码算法：****  
**一、什么是编码解码**（**[https://www.cnblogs.com/xqxacm/p/4886299.html](https://www.cnblogs.com/xqxacm/p/4886299.html)**）**

　　编码：利用特定的算法，对原始内容进行处理，生成运算后的内容，形成另一种数据的表现形式，可以根据算法，再还原回来，这种操作称之为编码。

　　解码：利用编码使用的算法的逆运算，对经过编码的数据进行处理，还原出原始数据，这种操作称之为解码。

二、什么是Base64编码算法**（**[https://www.cnblogs.com/xqxacm/p/4886299.html](https://www.cnblogs.com/xqxacm/p/4886299.html)**）**

　　可以将<font style="color:#FF0000;">任意的字节数组</font>数据，通过算法，生成只有（大小写英文、数字、+、/）内容表示的<font style="color:#FF0000;">字符串数据</font>。

　　即：将任意的内容转换为可见的字符串形式。

三、Base64算法的由来（[https://www.cnblogs.com/yanzi-meng/p/10689279.html](https://www.cnblogs.com/yanzi-meng/p/10689279.html)）

　　目前Base64已经成为网络上常见的传输8Bit字节代码的编码方式之一。在做支付系统时，系统之间的报文交互都需要使用Base64对明文进行转码，然后再进行签名或加密，之后再进行（或再次Base64）传输。那么，Base64到底起到什么作用呢？

在参数传输的过程中经常遇到的一种情况：使用全英文的没问题，但一旦涉及到中文就会出现乱码情况。与此类似，网络上传输的字符并不全是可打印的字符，比如二进制文件、图片等。Base64的出现就是为了解决此问题，它是基于64个可打印的字符来表示二进制的数据的一种方法。

电子邮件刚问世的时候，只能传输英文，但后来随着用户的增加，中文、日文等文字的用户也有需求，但这些字符并不能被服务器或网关有效处理，因此Base64就登场了。随之，Base64在URL、Cookie、网页传输少量二进制文件中也有相应的使用。

四、Base64原理**（**[https://www.cnblogs.com/xqxacm/p/4886299.html](https://www.cnblogs.com/xqxacm/p/4886299.html)**）**

1、将数据按照**<font style="color:#FF0000;">3个字节</font>**一组的形式进行处理，每三个字节在编码之后被转换为<font style="color:#FF0000;">4个字节</font>。

　　即：如果一个数据有6个字节，可编码后将包含6/3*4=8个字节

2、当数据的长度无法满足3的倍数的情况下，**最后的数据**需要进行填充操作，即补“=” ，<font style="color:#FF0000;">这里“=”是填充字符，不要理解为第65个字符</font>

<font style="color:#000000;">eg: 三个字节，转换成 4个字节的过程：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1580876349562-eb7ce9e1-3451-4ad1-99bd-5f2133b3b330.png)

 

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1580876349595-c76d393d-0857-4f10-a3ca-e0aa41757d0a.png)

可以看出，将原始数据的每三个字节分为一组，按位进行分割为每6位一个字节的形式，进行转换，形成新的4个字节。这四个字节才通过Base64编码表进行映射，形成最后实际的Base64编码结果。

如果原始数据最后无法凑成3个字节，则补填充，以“=”作为替换，代表没有数据

最后总结一下具体的转换步骤：（[https://www.cnblogs.com/yanzi-meng/p/10689279.html](https://www.cnblogs.com/yanzi-meng/p/10689279.html)）

+ 第一步，将待转换的字符串每三个字节分为一组，每个字节占8bit，那么共有24个二进制位。
+ 第二步，将上面的24个二进制位每6个一组，共分为4组。
+ 第三步，在每组前面添加两个0，每组由6个变为8个二进制位，总共32个二进制位，即四个字节。
+ 第四步，根据Base64编码对照表（见下图）获得对应的值。

从上面的步骤我们发现：

+ Base64字符表中的字符原本用6个bit就可以表示，现在前面添加2个0，变为8个bit，会造成一定的浪费。因此，Base64编码之后的文本，要比原文大约三分之一。
+ 为什么使用3个字节一组呢？因为6和8的最小公倍数为24，三个字节正好24个二进制位，每6个bit位一组，恰好能够分为4组。

五、Base64编码的示例：

以下图的表格为示例，我们具体分析一下整个过程。

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1580876976947-46c67dd3-9597-4ec3-8a2e-1e2ecba807e0.jpeg)

+ 第一步：“M”、“a”、”n”对应的ASCII码值分别为77，97，110，对应的二进制值是01001101、01100001、01101110。如图第二三行所示，由此组成一个24位的二进制字符串。
+ 第二步：如图红色框，将24位每6位二进制位一组分成四组。
+ 第三步：在上面每一组前面补两个0，扩展成32个二进制位，此时变为四个字节：00010011、00010110、00000101、00101110。分别对应的值（Base64编码索引）为：19、22、5、46。
+ 第四步：用上面的值在Base64编码表中进行查找，分别对应：T、W、F、u。因此“Man”Base64编码之后就变为：TWFu。

再举一个中文的例子，汉字"严"如何转化成Base64编码？

这里需要注意，汉字本身可以有多种编码，比如gb2312、utf-8、gbk等等，每一种编码的Base64对应值都不一样。下面的例子以utf-8为例。

首先，"严"的utf-8编码为E4B8A5，写成二进制就是三字节的"11100100 10111000 10100101"。将这个24位的二进制字符串，按照第3节中的规则，转换成四组一共32位的二进制值"00111001 00001011 00100010 00100101"，相应的十进制数为57、11、34、37，它们对应的Base64值就为5、L、i、l。

所以，汉字"严"（utf-8编码）的Base64值就是5Lil。

**那遇到位数不足的情况该怎么办？**

上面是按照三个字节来举例说明的，如果字节数不足三个，那么该如何处理？

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1580876976345-2f46af37-ec7d-41ae-9dfe-68a465b7d15c.png)

+ 两个字节：两个字节共16个二进制位，依旧按照规则进行分组。此时总共16个二进制位，每6个一组，则第三组缺少2位，用0补齐，得到三个Base64编码，第四组完全没有数据则用“=”补上。因此，上图中“BC”转换之后为“QKM=”；
+ 一个字节：一个字节共8个二进制位，依旧按照规则进行分组。此时共8个二进制位，每6个一组，则第二组缺少4位，用0补齐，得到两个Base64编码，而后面两组没有对应数据，都用“=”补上。因此，上图中“A”转换之后为“QQ==”；

也就是说：（[https://my.oschina.net/amince/blog/266806](https://my.oschina.net/amince/blog/266806)）

1.先使用0字节值在末尾补足，使其能够被3整除，

2.然后再进行base64的编码。

3.最后在编码后的base64文本后加上一个或两个'='号，代表补足的字节数。

    a.当最后剩余一个字节时，最后一个6位的base64字节块有四位是0值，编码结果后加上两个'='号；

    b.当最后剩余两个字节时，最后一个6位的base字节块有两位是0值，编码结果后加上一个'='号。 

六、Base64编码索引表**（**[https://www.cnblogs.com/xqxacm/p/4886299.html](https://www.cnblogs.com/xqxacm/p/4886299.html)**）**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1580876586006-e5dd8912-4ec5-40a9-b8d8-8dea81572a8f.png)

七、注意点

**（**[https://www.cnblogs.com/xqxacm/p/4886299.html](https://www.cnblogs.com/xqxacm/p/4886299.html)**）（**[https://www.cnblogs.com/yanzi-meng/p/10689279.html](https://www.cnblogs.com/yanzi-meng/p/10689279.html)**）**

1、Base64是编码算法，不是加密算法，只是用来编码字节数组，形成字符串的，并提供了解码功能

+ 大多数编码都是由字符串转化成二进制的过程，而Base64的编码则是从二进制转换为字符串。与常规恰恰相反，
+ Base64编码主要用在传输、存储、表示二进制领域，不能算得上加密，只是无法直接看到明文。也可以通过打乱Base64编码来进行加密。
+ 中文有多种编码（比如：utf-8、gb2312、gbk等），不同编码对应Base64编码结果都不一样

在PHP语言中，有一对专门的函数用于Base64转换：base64_encode()用于编码、base64_decode()用于解码。

这对函数的特点是，它们不管输入文本的编码是什么，都会按照规则进行Base64编码。因此，如果你想得到utf-8编码下的Base64对应值，你就必须自己保证，输入的文本是utf-8编码的。

八、延伸

<font style="color:#333333;">上面我们已经看到了Base64就是用6位（2的6次幂就是64）表示字符，因此成为Base64。同理，Base32就是用5位，Base16就是用4位。大家可以按照上面的步骤进行演化一下。</font>

-----------------------------------------------------------------------------------------------------------------

解码过程是编码过程的逆过程,大致流程：[https://my.oschina.net/amince/blog/266806](https://my.oschina.net/amince/blog/266806)

1、首先确认需要解码的 base64编码字串 所有字符是否在上面索引表中，如果不是，则只解析前面满足部分，否则报错;

2、编码时通过索引值找到对应字符，解码的时候通过对应字符找到对应索引值，参考下表。

3、通过4个索引值，进行位操作组成3字节数值。最后对照ASCII表进行对应即可。

例如:解码"TWFu" 过程:

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1580896134809-456a1887-fada-4427-b550-3bb81da07329.jpeg)

解码特殊处理：因为编码有特殊处理，所以理论上编码文本字节数是4的倍数，解码完成后，根据编码文本最后有多少个"="号，去掉对应个字节字符。

base64索引表：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1580876586006-e5dd8912-4ec5-40a9-b8d8-8dea81572a8f.png)

