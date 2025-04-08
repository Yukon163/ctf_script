粘贴自：[https://jingyan.baidu.com/article/9f7e7ec0b0aea36f281554df.html](https://jingyan.baidu.com/article/9f7e7ec0b0aea36f281554df.html)

当电脑频繁蓝屏时我们需要软件来查找蓝屏原因，此时可以使用Windbg软件对蓝屏文件进行分析查找原因。

## 工具/原料
## 
+ Windbg软件

## 方法/步骤
## 
1. 首先我们要保证我们设置了蓝屏转储，这样当蓝屏时系统会以**.dmp**文件方式保留蓝屏故障原因，我们需要查询是否设置内存转储和蓝屏文件存放位置。右键单击桌面计算机图标--选择**属性**，单击**高级系统设置**，在**启动和故障恢复**栏中单击**设置**，在**写入调试信息**栏中选择**小内存转储**（如果已经设置了可忽略此步骤），**小转储目录**为**%SystemRoot%\Minidump**(蓝屏文件存放位置)，即为**C:\Windows\Minidump**文件夹。  
![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575938009745-10517254-520f-4f99-96d6-0f8ecef15510.png)
2. 查看完毕后打开**Windbg**软件，首先需要为Windbg软件设置符号表路径，作为蓝屏原因分析数据库，否则软件将没有作用。单击**File**--选择**Symbol File Path**，在弹出的对话框Symbol Path文本框中输入**SRV*C:\Symbols*http://msdl.microsoft.com/download/symbols**，单击**OK**。  
![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575938009744-5e0823bb-b3a0-46f2-b332-4acac8f2759c.png)  
![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575938009767-f66dfa92-f68a-4936-a831-9e116fb32622.png)
3. 设置完毕后单击**File**--选择**Open Crash Dump**来打开蓝屏文件，在弹出的对话框中点选到**C:\Windows\Minidump**文件夹，单击我们要分析的蓝屏文件，单击**打开**。  
![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575938009746-2fd7ce29-4378-41de-9792-1328ba9472dc.png)
4. 在弹出的对话框Save Information for workspace？（是否保存信息到工作区）中单击Yes。（如果下次不想再被提示，可以勾选Don't ask again in the WinDbg session）。  
![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575938009763-595f7fca-bb9e-41dc-859c-3a2e54cd4486.png)
5. 接下来就是对文件进行分析，这需要一定的经验和知识。这里我们着重可以看一下**System Uptime**（开机时间）和**Probably Caused By**（可能引起故障的原因是）。  
![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575938009741-ed2fb368-191f-4b1a-8a59-6dfbfa7379a2.png)
6. 需要进一步分析，可以单击**!analyze -v**,此时我们可以从中提取到蓝屏错误代码和引起蓝屏的程序名称，再通过网络搜索这些程序名和代码等方式弄清原因。  
![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575938009768-ef535380-9920-426a-8614-0193ea520dc4.png)  
![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575938009743-40d6675c-277a-4427-838f-494e7bd8b239.png)  
<font style="color:#CCCCCC;">END</font>

## 注意事项
## 
+ Windbg不一定能保证发现蓝屏错误，还需要结合一些推理或其他资料

