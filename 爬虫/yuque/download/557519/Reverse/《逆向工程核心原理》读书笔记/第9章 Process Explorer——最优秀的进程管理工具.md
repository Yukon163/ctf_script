# 9.1 Process Explorer
Process Explorer是Windows操作系统下最优秀的<font style="color:#F5222D;">进程管理工具</font>。

https://technet.microsoft.com/en-us/sysinternals/bb896653.aspx

它是Mark Russinovich开发的进程管理实用程序。Mark Russinovich创办了著名的sysinternals（目前已并入微软旗下），他有着渊博的Windows操作系统知识，开发并公布了许多实用程序（FileMon、RegMon、TcpView、Dbg View、AutoRuns、RootKit Revealer等），也是《深入解析Windows操作系统》一书的合著者。他曾公开过FileMon与RegMon的源代码。在Windows操作系统缺乏各种信息资料的早期，这些源码对系统驱动开发者而言就像沙漠中的绿洲。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581151325053-9884fd7b-3179-4223-ae66-e3d859ad8337.png)

图9-1 Process Explore 运行画面

言归正传，一起看一下Process Explorer的运行界面（参考图9-1）。它拥有Windows任务管理器无法比拟的优秀界面组织结构。画面左上侧以Parent/Child的树结构显示当前运行的进程。右侧显示各进程的PID、CPU占有率、注册信息等（可通过Option添加）。画面下方（选项）显示的是加载到所选进程中的DLL信息，或者当前选中进程的所有对象的句柄。

# 9.2 具体有哪些优点呢
用户界面看上去更漂亮了，各位一定想知道具体有哪些优点。我在逆向分析代码时常常会同时打开Process Explorer，原因就在于它有以下这些优点。

+    Parent/Child进程树结构。
+    以不同颜色（草绿/红色）显示进程运行/终止。
+    进程的Suspend/Resume功能（挂起/恢复运行）。
+    进程终止（kill）功能（支持Kill Process Tree功能）。
+    检索DLL/Handle（检索加载到进程中的DLL或进程占有的句柄）。

此外还提供了其他多样化的功能，但是上面列举的这些是代码逆向分析时最常用的。该软件还可以不断更新（修正Bug、添加新功能），这也是非常大的优点。

# 9.3 sysinternals
https://technet.microsoft.com/en-us/sysinternals/default.aspx

进入上述网站，你会看到迷你控制台版本的Process Explorer（PsKill、PsSuspend、PsList等）。请下载并运行这些实用小程序。它们是非常棒的控制台版本小程序，对ProcessExplorer的功能做了删减。

那些因学习代码逆向技术而学习Windows内部结构的读者，可以学习并尝试编写这些控制台程序。这能够加深各位对进程与DLL等的理解（从经验来说，跟着动手操作是提高自身技术水平的最好方法）。



火绒的火绒剑也不错哦：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581151530393-2cd51f18-3c3a-446e-acc6-b726781a8288.png)

