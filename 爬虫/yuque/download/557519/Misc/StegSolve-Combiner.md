就以NCTF（南邮CTF）的a_good_idea为例子，当我们找到两张极其相似的图片时：要想到盲水印、StegSolve，以及linux的compare命令



参考资料：[https://blog.csdn.net/dyw_666666/article/details/88650738](https://blog.csdn.net/dyw_666666/article/details/88650738)

在这篇文章中我们先来介绍：StegSolve中的Combiner

先简单的了解一下StegSolve的大致功能：（需要Java环境）

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1574735317174-bc736a9a-e983-47a9-986a-5f1c8c3bcc75.png)

上图是StegSolve-Analyse的主要功能：

File Format: 文件格式，这个主要是查看图片的具体信息

Data Extract: 数据抽取，图片中隐藏数据的抽取

Frame Browser: 帧浏览器，主要是对GIF之类的动图进行分解，动图变成一张张图片，便于查看

Image Combiner: 拼图，图片拼接



Image Combiner的原理：<font style="color:#333333;">比较两个图片，可以把两个图片进行XOR、OR、AND等操作，以便于发现两张类似图片中隐含的信息</font>

题目：

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1574735481155-1dc4b922-9dab-43e3-9fb2-e547185c00ef.png)![](https://cdn.nlark.com/yuque/0/2019/png/574026/1574735482200-01ded5b2-34b5-43b9-8ac5-4f05251a5841.png)

to.png                                                         to_do.png



这道题可以执行linux中的compare命令，在这里就不说了，可以见a_good_idea的writeup



首先在StegSolve里打开to.png

然后：StegSolve->Image Combiner再打开另外一张图片

连续单击下面的箭头，没有任何的发现



将两张图片换一下加载顺序，在左右切换图片

出现这血红色的二维码（颜色挺吓人的）

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1574735848804-22c34616-d66a-499a-a903-a4945b4840e4.png)

