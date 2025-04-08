DLL卸载（DLLEjection)是将强制插入进程的DLL弹出的一种技术，其基本工作原理与使用CreateRemoteThreadAPI进行DLL注入的原理类似。

# 24.1DLL卸载的工作原理
前面我们学习过使用CreateRemote Thread()API进行DLL注入的工作原理，概括如下：

> 驱使目标进程调用LoadLibrary()API
>

同样，DLL卸载工作原理也非常简单：

> 驱使目标进程调用FreeLibrary()API
>

也就是说，将FreeLibrary()API的地址传递给CreateRemote Thread()的IpStartAddress参数，并把要卸载的DLL的句柄传递给IpParameter参数。

提示------------------------------------------------------------------------------------------------------------------

每个Windows内核对象（KernelObject)都拥有一个**引用计数（Reference Count)**，代表对象被使用的次数。调用10次**LoadLibrary**（“a.dll”），a.dll的引用计数就变为10，卸载a.dll时同样需要调用10次**Freelibrary**）（每调用一次LoadLibrary），引用计数会加1；而每调用一次Freelibrary()，引用计数会减1）。因此，卸载DLL时要充分考虑好“引用计数”这个因素。

-----------------------------------------------------------------------------------------------------------------------

# 24.2实现DLL卸载
提示------------------------------------------------------------------------------------------------------------------

下面介绍的源代码使用Microsoft Visual C++Express2010编写而成，并在WindowsXP/7 32位系统中通过测试。

-----------------------------------------------------------------------------------------------------------------------

首先分析一下EjectDll.exe程序，它用来从目标进程（notepad.exe)卸载指定的DLL文件（myhack.dll，已注入目标进程），程序源代码（EjectDll.cpp）如下所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582096938301-12ce5cae-ac44-4411-b3c4-97c765247309.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582096939760-d3c2269b-0c27-4e5d-ada1-4da23d18ecf7.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582096943082-255faeed-cbb4-49a0-a6ff-f84ff919a735.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582096944205-d89df3c3-1938-4a84-9dcc-b92cffeefe9c.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582096945417-c2bb1bbb-3715-48b5-afae-5c44230632ff.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582096946423-54a1bc67-9aa9-4904-aab6-bd40c56e0a11.png)

前面介绍过，卸载DLL的原理是驱使目标对象自己调用FreeLibrary0API，上述代码中的EjectDllO函数就是用来卸载DLL的。下面仔细分析一下EjectDll0函数。

## 24.2.1获取进程中加载的DLL信息
> hsnapshot=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE,dwPID);
>

使用Create Toolhelp32Snapshot()API可以获取加载到进程的模块（DLL）信息。将获取的hSnapshot句柄传递给Module32First()/Module32Next()函数后，即可设置与MODULEENTRY32结构体相关的模块信息。代码24-2是MODULEENTRY32结构体的定义。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582097093937-95032a41-1f2f-482f-8d78-35c1029a5e13.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582097094974-0d7dd360-cf68-4aff-9e84-1e28eced0a42.png)

szModule成员表示DLL的名称，modBaseAddr成员表示相应DLL被加载的地址（进程虚拟内存）。在EjectDll()函数的for循环中比较szModule与希望卸载的DLL文件名称，能够准确查找到相应模块的信息。

## 24.2.2获取目标进程的句柄
> hProcess=openProcess(PROCESS_ALL _ACCESS,FALSE,dWPID);
>

该语句使用进程ID来获取目标进程（notepad）的进程句柄（下面用获得的进程句柄调用CreateRemote Thread()API)。

## 24.2.3获取FreeLibrary()API地址
> hModule=GetModuleHandle(L"kernel32.dll");
>
> pThreadProc=(LPTHREAD_START_ROUTINE)GetProcAddress(hModule,"FreeLibrary");
>

若要驱使notepad进程自己调用FreeLibrary()API，需要先得到FreeLibrary()的地址。然而上述代码获取的不是加载到notepad.exe进程中的Kernel32!FreeLibrary地址，而是加载到EjectDll.exe进程中的Kernel32!FreeLibrary地址。如果理解了前面学过的有关DLL注入的内容，那么各位应该能 猜出其中缘由——FreeLibrary地址在所有进程中都是相同的。

## 24.2.4在目标进程中运行线程
> hThread=CreateRemoteThread(hProcess,NULL,0,pThreadProc,me.modBaseAddr,0,NULL)；
>

pThreadProc参数是FreeLibrary()API的地址，me.modBaseAddr参数是要卸载的DLL的加载地址。将线程函数指定为FreeLibrary函数，并把DLL加载地址传递给线程参数，这样就在目标进程中成功调用了FreeLibrary()API（CreateRemote Thread()API原意是在外部进程调用执行线程函数，只不过这里的线程函数换成了FreeLibrary()函数）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582097617446-1c27d418-214d-476c-9e93-7b4193516e4c.png)

ThreadProc函数与FreeLibrary函数都只有1个参数，以上方法的灵感即源于此。

# 24.3DLL卸载练习
本节一起做个练习，先将myhack.dll注入notepad.exe进程，随后再将其卸载。

## 24.3.1复制文件及运行notepad.exe
首先，复制下面3个文件到工作文件p夹（c:\work），如图24-1所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582098019282-d7281ed3-55dd-43be-8a1f-65d78cdd3116.png)

然后，运行notepad.exe并查看其PID，如图24-2所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582098062088-56c24f3b-34a7-4974-a332-c69ca325364d.png)

我的电脑环境中，notepad.exe的PID为2832。

## 24.3.2注入myhack.dll
打开命令行窗口（cmd.exe)，输入如下参数，将myhack.dll文件注入notepad.exe进程，如图24-3所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582098161983-3089632c-b464-4b7b-91e5-5335dcfc477e.png)

可以在Process Explorer中看到myhack.dll注入成功，如图24-4所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582098222038-5d65acdb-5154-4d54-81e7-7a5f5799f29d.png)

## 24.3.3卸载myhack.dll
打开命令行窗口（cmd.exe)，输入如下参数，将注入notepad.exe进程的myhack.dll文件卸载下来，如图24-5所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582098280829-7de6b9d5-4a23-4480-bfb2-f2a92e8e2959.png)

请使用Process Explorer查看是否成功卸载。DLL卸载的基本原理与DLL注入的原理相同，理解起来非常容易。请各位认真阅读上面的内容并亲自操作。

# Q&A
Q.使用FreeLibrary()卸载DLL的方法好像仅适用于使用CreateRemote Thread()注入的DLL文件，有没有什么方法可以将加载的普通DLL文件卸载下来呢?

A.正如您所说，使用FreeLibrary()的方法仅适用于卸载自己强制注入的DLL文件。PE文件直接导入的DLL文件是无法在进程运行过程中卸载的。

