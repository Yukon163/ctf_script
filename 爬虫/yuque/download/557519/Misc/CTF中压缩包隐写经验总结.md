参考资料:[https://www.cnblogs.com/xishaonian/p/7713657.html](https://www.cnblogs.com/xishaonian/p/7713657.html)

[https://blog.csdn.net/kajweb/article/details/76474476](https://blog.csdn.net/kajweb/article/details/76474476)

# 1、zip伪加密
简单的话来阐述

　　zip伪协议的意思是说本来不需要密码的zip文件然后通过修改标志位，然后就可以达到有密码的效果对吗？但是他实际是没有密码。

**一个 ZIP 文件由三个部分组成：**

**　　压缩源文件数据区**+**压缩源文件目录区**+**压缩源文件目录结束标志 **

**　　详情：**[**http://blog.csdn.net/wclxyn/article/details/7288994**](http://blog.csdn.net/wclxyn/article/details/7288994)

****

**实例说明**<font style="color:#FFFFFF;">(http://ctf5.shiyanbar.com/stega/sim.jpg)</font>

分割出来文件以后有个zip

用Winhex工具打开查看其十六进制编码，图如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578792989355-50a86d47-9709-4f4f-9552-c59d525600c7.png)

**a.压缩源文件数据区：**

50 4B 03 04：这是头文件标记（0x04034b50） 

14 00：解压文件所需 pkware 版本 

00 00：全局方式位标记（有无加密） 

08 00：压缩方式 

5A 7E：最后修改文件时间 

F7 46：最后修改文件日期 

16 B5 80 14：CRC-32校验（1480B516） 

19 00 00 00：压缩后尺寸（25） 

17 00 00 00：未压缩尺寸（23） 

07 00：文件名长度 

00 00：扩展记录长度 

6B65792E7478740BCECC750E71ABCE48CDC9C95728CECC2DC849AD284DAD0500

**b.压缩源文件目录区:**

50 4B 01 02：目录中文件文件头标记(0x02014b50) 

3F 00：压缩使用的 pkware 版本 

14 00：解压文件所需 pkware 版本 

00 00：全局方式位标记<font style="color:#F5222D;">（有无加密，这个更改这里进行伪加密，改为09 00打开就会提示有密码了） </font>

08 00：压缩方式 

5A 7E：最后修改文件时间 

F7 46：最后修改文件日期 

16 B5 80 14：CRC-32校验（1480B516） 

19 00 00 00：压缩后尺寸（25） 

17 00 00 00：未压缩尺寸（23） 

07 00：文件名长度 

24 00：扩展字段长度 

00 00：文件注释长度 

00 00：磁盘开始号 

00 00：内部文件属性 

20 00 00 00：外部文件属性 

00 00 00 00：局部头部偏移量 

6B65792E7478740A00200000000000010018006558F04A1CC5D001BDEBDD3B1CC5D001BDEBDD3B1CC5D001

**c.压缩源文件目录结束标志:**

50 4B 05 06：目录结束标记 

00 00：当前磁盘编号 

00 00：目录区开始磁盘编号 

01 00：本磁盘上纪录总数 

01 00：目录区中纪录总数 

59 00 00 00：目录区尺寸大小 

3E 00 00 00：目录区对第一张磁盘的偏移量 

00 00 1A：ZIP 文件注释长度

将09改为00，再打开txt即可

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578792989471-e56f5051-cd19-4852-bdba-80a4d04c717e.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578792989491-a8d1d3f3-91c4-4b3e-b85e-8921702c514a.png)

zip伪加密在kali下执行binwalk -e命令即可分离出文件（当然，也可以尝试winrar的压缩包修复功能）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578794287127-a0820fac-f1a6-4595-87d3-f1ab5e92408e.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578794297029-1a8da553-23c8-4b90-b25e-7ec0ff543719.png)



**<font style="color:#F5222D;">我们还可以使用：zipcenop.jar</font>**

**使用检测伪加密的ZipCenOp.jar，解密后如果能成功打开zip包，则是伪加密，否则说明思路错误**

**ZipCenOp.jar的下载我已经传到了本地，点击**[**下载**](https://files.cnblogs.com/files/ECJTUACM-873284962/ZipCenOp.zip)**即可~**

下面举个例子，如下是个被加密的文件，理由很简单，文件夹后面跟了一个*~

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793601403-5ce4ede2-09f8-4fe5-b5d5-214523250ae0.png)

使用ZipCenOp.jar(需java环境)使用方法:

java -jar ZipCenOp.jar r xxx.zip

我们对其使用如上命令进行解包，得下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793601332-f724685a-bbca-41d0-9e73-6a8bf20067d9.png)

我们再看下这个文件：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793601360-2b5c77c5-36b0-44f3-a060-9b1ad634692e.png)

发现文件夹后面跟的*消失了，说明这个文件就是伪加密文件~

当然啦，我们也可以对Zip文件进行伪加密~

java -jar ZipCenOp.jar e xxx.zip

# 2、zip属性隐藏
可能很多人没有去注意文件属性一栏，往往有时候，加密者会把密码放在属性里面，例如下图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793556908-6fb45986-15ba-4ebb-833f-766c9361d84a.png)

我们可以看到，这个Zip压缩文件的密码就是www.cnblogs.com了~



# 3、暴力破解
顾名思义，就是逐个尝试选定集合中可以组成的所有密码，知道遇到正确密码~

而字典攻击的效率比爆破稍高，因为字典中存储了常用的密码，因此就避免了爆破时把时间浪费在脸滚键盘类的密码上~

而如果已知密码的某几位，如已知6位密码的第3位是a，那么可以构造 ??a??? 进行掩码攻击，掩码攻击的原理相当于构造了第3位为a的字典，因此掩码攻击的效率也比爆破高出不少~

对这一类的zip问题，Windows下我使用的是ARCHPR~

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793716673-b6b0471d-4a72-4f11-9e3c-7b0ee183cae4.png)

点击开始，进行爆破即可~下面是个演示，就花了4s的时间爆破出密码是MIT~

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793716705-83854608-6cec-4342-ac8a-c9a90d23f9de.png)

而所谓的字典攻击其实就是在字典选择合适的情况下，用很短的时间就能找到密码~

实例如下所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793716766-5947f3d4-d358-47d7-b634-8deba30c301e.png)

而掩码攻击就是通过已知密码的某几位进行构造，如下示例我们构造了??T进行爆破，仅花了81ms就破解了~

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793716741-70b16fea-1eac-4d15-8e1e-65a6d729d3c1.png)



# 4、明文攻击
明文攻击是一种较为高效的攻击手段，大致原理是当你不知道一个zip的密码，但是你有zip中的一个已知文件（文件大小要大于12Byte）或者已经通过其他手段知道zip加密文件中的某些内容时，因为同一个zip压缩包里的所有文件都是使用同一个加密密钥来加密的，所以可以用已知文件来找加密密钥，利用密钥来解锁其他加密文件~

此时我们可以尝试用ARCHPR或者pkcrack进行明文攻击~

我们可以看到readme.txt是加密压缩包里的readme.txt的明文，所以可以进行明文攻击~

将readme.txt压缩成.zip文件，然后在软件中填入相应的路径即可开始进行明文攻击，这里我们用ARCHPR进行演示~

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1578793716677-98d8d754-cca0-4ab3-99af-c14b83b1badd.jpeg)

可能有些朋友会说ARCHPR怎么行不通啊，一般是版本不对的问题~

如果还是有问题怎么办呢？那就尝试用下pkcrack

有些朋友在Windows下会出现如下错误：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793716686-d5971cbb-dc9a-4694-b41e-e9ccfc968e5a.png)

那是因为pkcrack只支持32位的，所以运行这个需要在XP系统下进行



# 5、CRC32碰撞
CRC32:CRC本身是“冗余校验码”的意思，CRC32则表示会产生一个32bit（8位十六进制数）的校验值。

在产生CRC32时，源数据块的每一位都参与了运算，因此即使数据块中只有一位发生改变也会得到不同的CRC32值，利用这个原理我们可以直接爆破出加密文件的内容~

具体算法实现参考百度百科：[https://baike.baidu.com/item/CRC32/7460858?fr=aladdin](https://baike.baidu.com/item/CRC32/7460858?fr=aladdin)

我们看个CRC32碰撞的例子：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793716848-fb8d76d1-de64-43fe-8b83-54dfc00ea891.png)

flag是4位数，且CRC32值为56EA988D

我们可以写出如下脚本：

<font style="color:#008000;">#</font><font style="color:#008000;">coding=utf=8</font>

<font style="color:#0000FF;">import</font><font style="color:#000000;"> binascii</font>

real = 0x56EA988D

<font style="color:#0000FF;">for</font><font style="color:#0000FF;"> y </font><font style="color:#0000FF;">in</font><font style="color:#0000FF;"> range</font><font style="color:#0000FF;">(</font><font style="color:#0000FF;">1000</font><font style="color:#0000FF;">,</font><font style="color:#0000FF;">9999</font><font style="color:#000000;">):</font>

    <font style="color:#0000FF;">if</font><font style="color:#0000FF;"> real </font><font style="color:#0000FF;">==</font><font style="color:#0000FF;"> </font><font style="color:#0000FF;">(</font><font style="color:#0000FF;">binascii</font><font style="color:#0000FF;">.</font><font style="color:#0000FF;">crc32</font><font style="color:#0000FF;">(</font><font style="color:#0000FF;">str</font><font style="color:#0000FF;">(</font><font style="color:#0000FF;">y</font><font style="color:#0000FF;">))</font><font style="color:#0000FF;"> </font><font style="color:#0000FF;">&</font><font style="color:#0000FF;"> </font><font style="color:#0000FF;">0xffffffff</font><font style="color:#000000;">):</font>

        <font style="color:#0000FF;">print</font><font style="color:#000000;">(</font><font style="color:#000000;">y</font><font style="color:#000000;">)</font>

<font style="color:#0000FF;">print</font><font style="color:#0000FF;">(</font><font style="color:#800000;">'</font><font style="color:#800000;">End</font><font style="color:#800000;">'</font><font style="color:#800000;">)</font>

在 <font style="color:#F5222D;">Python 2.x</font> 的版本中，binascii.crc32 所计算出來的 CRC 值域为[-2^31, 2^31-1] 之间的有符号整数，为了要与一般CRC 结果作比对，需要将其转为无符号整数，所以加上& 0xffffffff来进行转换。如果是 <font style="color:#F5222D;">Python 3.x</font> 的版本，其计算结果为 [0, 2^32-1] 间的无符号整数，因此不需额外加上& 0xffffffff 。

脚本的运行结果如下，即为压缩文件的内容：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1578793716764-ca90b3e4-212d-4e61-a3e7-09d75d04f86c.png)





