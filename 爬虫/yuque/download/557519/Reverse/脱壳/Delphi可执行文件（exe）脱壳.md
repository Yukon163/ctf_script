注：此文章摘选并略微改动自Cyberangel的“熊猫烧香病毒样本分析（1）：setup.exe”，如有错误请指正。

## 1、查壳
运行吾爱破解工具包中的PEID和Exeinfo PE，将文件分别载入，结果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583316744000-c6aa685b-cf7c-4be1-a8f9-83797bed1309.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583316876468-b2d383b1-d69f-4b05-854e-842afacd3af9.png)

提示有FSG v2.0的壳，并且在Detect It Easy中显示样本是由Delphi编写的

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583317048634-3407bc81-43ea-4cc0-8cf6-a58dfed9f0fe.png)

## 2、手动脱壳
将exe文件拖入到OD中，往下拖动鼠标，发现代码不多，因此使用单步法脱壳

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583371872704-fa88641a-5376-4277-a8fd-3db8028d8492.png).当OD执行到地址4001D1处，可以看到有特殊的跳转。按F8单步步过并按Ctrl+A进行强制分析后，向下拉动窗口可以看到病毒样本的主函数（请结合IDA分析），那么地址0040D278应该就是样本的OEP。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583372011553-80cf1e08-8d08-4665-b090-605379ce974a.png)

在0040D278处，Dump此处内存：OD->插件->OllyDump->脱壳在当前调试的进程，设置选项如下图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583373355582-1b0a3a7b-df8f-4026-b4e9-d1b0a894670f.png)

确定，另存为1.exe，尝试运行一下，出现错误：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583373466259-a754728c-a63f-40e4-b107-0bfda9d4a082.png)

报错0xC0000005.内存访问异常,应该是FSG壳对<font style="color:#333333;">导入地址表</font>做了处理,导致我们dump下来的文件无法正常运行，那么接下来换一种方式进行dump。

确定好OEP（0040D278）后,我们使用Scylla x86（IAT脱壳修复工具）来进行操作：

打开吾爱破解工具包中的Scylla x86，附加活动进程setup.exe，填写OEP为“0040D278”，自动查找IAT，若出现下面弹窗则选否，然后选择ok.

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583377303342-b41175df-41b9-4a60-b6f1-9e43241441fb.png)

再点击获取输入表，结果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583377392625-593af4fd-c83b-40a7-aad1-2d8136691ad8.png)

单击转储到文件，保存为“setup_dump.exe”。之后修复转储的文件，选择“setup_dump.exe”，修复后会自动保存为“setup_dump_SCY.exe”。检查脱壳后的文件，显示无壳，脱壳成功，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1583377574244-9cf58dd5-554d-4e79-b5f9-185baac62fc3.png)

