DLL注入（DLL Injection)是渗透其他进程的最简单有效的方法，本章将详细讲解DLL注入的有关内容。借助DLL注入技术，可以钩取API、改进程序、修复Bug等。

# 23.1 DLL注入
**DLL注入指的是向运行中的其他进程强制插入特定的DLL文件。**从技术细节来说，DLL注入命令其他进程自行调用LoadLibrary）API，加载（Loading)用户指定的DLL文件。**DLL注入与一般DLL加载的区别在于，加载的目标进程是其自身或其他进程。**图23-1描述了DLL注入的概念。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581579324684-59444e9f-3d6b-4c7c-bd62-256dc01e891c.png)

从图23-1中可以看到，myhack.dll已被强制插入notepad进程（本来notepad并不会加载myhack.dll）。加载到notepad.exe进程中的myhack.dll与已经加载到notepad.exe进程中的DLL（kernel32.dll、user32.dll)一样，拥有访问notepad.exe进程内存的（正当的）权限，这样用户就可以做任何想做的事了（比如：向notepad添加通信功能以实现Messenger、文本网络浏览器等）。

DLL（Dynamic Linked Library,动态链接库）-------------------------------------------------------------------------

**DLL被加载到进程后会自动运行DlIMain()函数，用户可以把想执行的代码放到DllMain()函数，每当加载DLL时，添加的代码就会自然而然得到执行。利用该特性可修复程序Bug，或向程序添加新功能。**

-----------------------------------------------------------------------------------------------------------------------

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582077500929-cbf70b5e-d6c7-4393-9324-0371f96eab8e.png)

# 23.2 DLL注入示例
使用LoadLibrary()API加载某个DLL时，该DLL中的DlIMain()函数就会被调用执行。DLL注入的工作原理就是从外部促使目标进程调用LoadLibrary()API（与一般DLL加载相同），所以会强制调用执行DLL的DllMain()函数。并且，被注入的DLL拥有目标进程内存的访问权限，用户可以随意操作（修复Bug、添加功能等）。下面看一些使用DLL注入技术的示例。

## 23.2.1改善功能与修复Bug
DLL注入技术可用于改善功能与修复Bug。没有程序对应的源码，或直接修改程序比较困难时，就可以使用DLL注入技术为程序添加新功能（类似于插件），或者修改有问题的代码、数据。

## 23.2.2消息钩取
**Windows OS默认提供的消息钩取功能应用的就是一种DLL注入技术。与常规的DLL注入唯一的区别是，OS会直接将已注册的钩取DLL注入目标进程。**

提示------------------------------------------------------------------------------------------------------------------

我曾经从网上下载过一个HexEditor，它不支持鼠标滚轮滑动，所以我用消息钩取技术为其添加了鼠标滚轮支持。虽然可以下载更多、更好用的Hex Editor，但是利用学到的技术改善、扩展程序功能是一种非常妙的体验。这样不仅能解决问题，还锻炼了我们灵活应用技术的能力（此后我就开始对使用逆向技术改善已有程序的功能产生了浓厚兴趣）。

-----------------------------------------------------------------------------------------------------------------------

## 23.2.3API钩取
API钩取广泛应用于实际的项目开发，而进行API钩取时经常使用DLL注入技术。先创建好DLL形态的钩取函数，再将其轻松注入要钩取的目标进程，这样就完成了API钩取。这灵活运用了“**被注入的DLL拥有目标进程内存访问权限**”这一特性。

## 23.2.4其他应用程序
DLL注入技术也应用于监视、管理PC用户的应用程序。比如，用来阻止特定程序（像游戏、股票交易等）运行、禁止访问有害网站，以及监视PC的使用等。管理员（或者父母）主要安装这类拦截/阻断应用程序来管理/监视。受管理/监视的一方当然千方百计地想关闭这些监视程序，但由于这些监视程序采用DLL注入技术，它们可以隐藏在正常进程中运行，所以管理员一般不用担心被发现或被终止（若用户强制终止Windows系统进程，也会一并关闭系统，最后也算达成了拦截/阻断这一目标）。

## 23.2.5恶意代码
恶意代码制作者们是不会置这么好的技术于不顾的，他们积极地把DLL注入技术运用到自己制作的恶意代码中。这些人把自己编写的恶意代码隐藏到正常进程（winlogon.exe、services.exe、svchost.exe、explorer.exe等），打开后门端口（Backdoor port)，尝试从外部连接，或通过键盘偷录（Keylogging)功能将用户的个人信息盗走。只有了解恶意代码制作者们使用的手法，才能拿出相应的对策。

23.3DLL注入的实现方法

向某个进程注入DLL时主要使用以下三种方法：

   DLL注入方法

    - 创建远程线程（CreateRemote Thread()API)
    - 使用注册表（AppInit_DLLs值）
    - 消息钩取（SetWindowsHookEx()API）

# 23.4 CreateRemote Thread()
本方法是《Windows核心编程》一书（素有“Windows编程圣经”之称）中介绍过的。本节通过一个简单的示例来演示如何通过创建远程线程完成DLL注入。

## 23.4.1练习示例myhack.dll
本示例将把myhack.dll注入notepad.exe进程，被注入的myhack.dll是用来联网并下载http://www.naver.com/index.html文件的。

   复制练习文件首先将练习文件（InjectDll.exe、myhack.dll)分别复制到工作文件夹（C:\Work)，如图23-2所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582078213598-db70a134-b738-4897-8e89-29da135a99ac.png)

图23-2复制练习文件

**运行notepad.exe程序**

先运行notepad.exe（日记本）程序，再运行Process Explorer（或者Windows任务管理器）获取notepad.exe进程的PID。

可以看到图23-3中notepad.exe进程的PID值为9080。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582078365695-8150adaa-46c0-4c93-9ff0-e7a7d6697d68.png)

图23-3 Process Explorer

**运行DebugView**

DebugView是一个非常有用的实用程序，它可以用来捕获并显示系统中运行的进程**输出的所有调试字符串**，由大名鼎鼎的Process Explorer制作人Mark Russinovich开发而成。请访问下面URL下载。

http://technet.microsoft.com/en-us/sysinternals/bb896647

示例中的DLL文件被成功注入notepad.exe进程时，就会输出调试字符串，此时使用DebugView即可查看，如图23-4所示。

提示------------------------------------------------------------------------------------------------------------------

应当养成在应用程序开发中灵活使用DebugView查看调试日志的好习惯。

-----------------------------------------------------------------------------------------------------------------------

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582078669190-fa9ddb67-5bf9-49ef-8d3f-1763afcf40f2.png)

图23-4 DebugView

**myhack.dll注入**

InjectDll.exe是用来向目标进程注入DLL文件的实用小程序（后面会详细讲解工作原理及源代码）。如图23-5所示，打开命令窗口并输入相应参数即可运行InjectDll.exe。

**（要以管理员权限运行）**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582079264504-15f5e81b-eb0f-4e97-a514-a2d2f3b362d0.png)

图23-5运行InjectDll.exe

**确认DLL注入成功**

下面要检查myhack.dll文件是否成功注入notepad.exe进程。首先查看DebugView日志，如图23-6所示。

（此处我的DebugView没有日志，注入失败...）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582079520932-436f0ae4-027b-4d50-86af-1fed7c43e63d.png)

DebugView中显示出调试字符串，该字符串是由PID：1016进程输出的。PID：1016进程就是注入myhack.dll的notepad.exe进程。成功注入myhack.dll时，就会调用执行DllMain()函数的 OutputDebugString()API。

在Process Explorer中也可以看到myhack.dll已经成功注入notepad.exe进程。在Process Explorer的View菜单中，选择Show Lower Pane与Lower Pane Views-DLLs项，然后选择notepad.exe进程，就会列出所有加载到notepad.exe进程中的dll，如图23-7所示。在图中可以看到已经成功注入notepad.exe的myhack.dll文件。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582079757105-3823d23a-800b-495f-a33f-a0447bb3cb19.png)

**结果确认**

下面确认一下指定网站的index.html文件下载是否正常。

双击图23-8中的Index.html文件，在IE浏览器中查看页面。

图23-9看上去虽然与实际网站的主页面有些不同，但可以肯定它就是该网站的index.html文件。![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582079886831-6950e91e-3300-4784-8a1e-6b61fa644e09.png)

图23-9看上去虽然与实际网站的主页面有些不同，但可以肯定它就是该网站的index.html文件。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582079968309-9357dc5b-3aed-4eae-b83e-cdbc8ff2fe0d.png)

提示------------------------------------------------------------------------------------------------------------------

有时会因系统用户权限、安全设置等导致无法下载 index.html 文件

-----------------------------------------------------------------------------------------------------------------------

就像在上述示例中看到的一样，借助创建远程线程的方法可以成功“渗透”指定进程，进而可以随意操作。下面继续分析示例源代码，进一步学习使用CreateRemote Thread()API实施DLL注入的原理与实现方法。

## 23.4.2分析示例源代码
提示------------------------------------------------------------------------------------------------------------------

以下介绍的源代码是用Micosoft Visual C++Express2010编写的，在Windows XP/7 32位操作系统中通过测试。

-----------------------------------------------------------------------------------------------------------------------

**Myhack.cpp**

先分析一下myhack.dl源代码（myhack.cpp)。

**<font style="color:#c586c0;">#include</font>****<font style="color:#569cd6;"> </font>****<font style="color:#ce9178;">"windows.h"</font>**

**<font style="color:#c586c0;">#include</font>****<font style="color:#569cd6;"> </font>****<font style="color:#ce9178;">"tchar.h"</font>**



**<font style="color:#c586c0;">#pragma</font>****<font style="color:#569cd6;"> </font>****<font style="color:#9cdcfe;">comment</font>****<font style="color:#569cd6;">(</font>****<font style="color:#9cdcfe;">lib</font>****<font style="color:#569cd6;">, "</font>****<font style="color:#9cdcfe;">urlmon</font>****<font style="color:#569cd6;">.</font>****<font style="color:#9cdcfe;">lib</font>****<font style="color:#569cd6;">")</font>**



**<font style="color:#c586c0;">#define</font>****<font style="color:#569cd6;"> DEF_URL         (</font>****<font style="color:#9cdcfe;">L</font>****<font style="color:#569cd6;">"http://www.naver.com/index.html")</font>**

**<font style="color:#c586c0;">#define</font>****<font style="color:#569cd6;"> DEF_FILE_NAME   (</font>****<font style="color:#9cdcfe;">L</font>****<font style="color:#569cd6;">"index.html")</font>**



**<font style="color:#d4d4d4;">HMODULE g_hMod = </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">;</font>**



**<font style="color:#d4d4d4;">DWORD WINAPI </font>****<font style="color:#dcdcaa;">ThreadProc</font>****<font style="color:#d4d4d4;">(LPVOID lParam)</font>**

**<font style="color:#d4d4d4;">{</font>**

**<font style="color:#d4d4d4;">    TCHAR </font>****<font style="color:#9cdcfe;">szPath</font>****<font style="color:#d4d4d4;">[_MAX_PATH] = {</font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">,};</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( !</font>****<font style="color:#dcdcaa;">GetModuleFileName</font>****<font style="color:#d4d4d4;">( g_hMod, szPath, MAX_PATH ) )</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> FALSE;</font>**

**<font style="color:#d4d4d4;">    </font>**

**<font style="color:#d4d4d4;">    TCHAR *p = </font>****<font style="color:#dcdcaa;">_tcsrchr</font>****<font style="color:#d4d4d4;">( szPath, </font>****<font style="color:#ce9178;">'</font>****<font style="color:#d7ba7d;">\\</font>****<font style="color:#ce9178;">'</font>****<font style="color:#d4d4d4;"> );</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( !p )</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> FALSE;</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#dcdcaa;">_tcscpy_s</font>****<font style="color:#d4d4d4;">(p+</font>****<font style="color:#b5cea8;">1</font>****<font style="color:#d4d4d4;">, _MAX_PATH, DEF_FILE_NAME);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#dcdcaa;">URLDownloadToFile</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">, DEF_URL, szPath, </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">, </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">}</font>**



**<font style="color:#d4d4d4;">BOOL WINAPI </font>****<font style="color:#dcdcaa;">DllMain</font>****<font style="color:#d4d4d4;">(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved)</font>**

**<font style="color:#d4d4d4;">{</font>**

**<font style="color:#d4d4d4;">    HANDLE hThread = </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">;</font>**



**<font style="color:#d4d4d4;">    g_hMod = (HMODULE)hinstDLL;</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">switch</font>****<font style="color:#d4d4d4;">( fdwReason )</font>**

**<font style="color:#d4d4d4;">    {</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">case</font>****<font style="color:#d4d4d4;"> DLL_PROCESS_ATTACH : </font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">OutputDebugString</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#ce9178;">L"<myhack.dll> Injection!!!"</font>****<font style="color:#d4d4d4;">);</font>**

**<font style="color:#d4d4d4;">        hThread = </font>****<font style="color:#dcdcaa;">CreateThread</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">, </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">, ThreadProc, </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">, </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">, </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">);</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">CloseHandle</font>****<font style="color:#d4d4d4;">(hThread);</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">break</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">    }</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> TRUE;</font>**

**<font style="color:#d4d4d4;">}</font>****<font style="color:#d4d4d4;">  
</font>**    在DllMain()函数中可以看到，该DLL被加载（DLL_PROCESS_ATTACH)时，先输出一个调试字符串（“myhack.dll Injection!!！”），然后创建线程调用函数（ThreadProc）。在ThreadProc()函数中通过调用urlmon!URLDownloadToFile()API来下载指定网站的index.html文件。**前面提到过，向进程注入DLL后就会调用执行该DLL的DlIMain****()****函数。所以当myhack.dll注入notepad.exe进程后，最终会调用执行URLDownloadToFile****()****API。**

**InjectDll.cpp**

InjectDll.exe程序用来将myhack.dll注入notepad.exe进程，下面看一下其源代码。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582080496224-758f4e0a-4852-4d6e-821c-42c1b2f76e2a.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582080498682-25012421-6609-4c10-8f87-bedf912296d4.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582080501013-4e8b7ec4-919a-43e1-bc46-745e11d39b7d.png)

main()函数的主要功能是检查输入程序的参数，然后调用InjectDll()函数。InjectDll()函数是用来实施DLL注入的核心函数，其功能是命令目标进程（notepad.exe）自行调用LoadLibrary（“myhack.dll”)API。下面逐行详细查看InjectDll()函数。

**获取目标进程句柄**

hProcess=OpenProcess(PROCESS_ALL_ACCESS,FALSE,dwPID))

调用OpenProcess()API，借助程序运行时以参数形式传递过来的dwPID值，获取notepad.exe进程的句柄（PROCESS_ALL_ACCESS权限）。得到PROCESS_ALL_ACCESS权限后，就可以使用获取的句柄（hProcess)控制对应进程（notepad.exe）。

**将要注入的DLL路径写入目标进程内存  **     

pRemoteBuf=VirtualAllocEx(hProcess,NULL,dwBufSize,MEM_COMMIT,PAGE_READWRITE);

需要把即将加载的DLL文件的路径（字符串）告知目标进程（notepad.exe)。**因为任何内存空间都无法进行写入操作，故先使用VirtualAllocEx()API在目标进程（notepad.exe)的内存空间中分配一块缓冲区，且指定该缓冲区的大小为DLL文件路径字符串的长度（含Terminating NULL）即可。**

**<font style="color:#F5222D;">提示-----------------------------------------------------------------------------------------------------------------</font>**

**<font style="color:#F5222D;">VirtualAllocEx()函数的返回值（pRemoteBuf）为分配所得缓冲区的地址。该地址并不是程序（Inject.exe）自身进程的内存地址，而是hProcess句柄所指目标进程（notepad.exe)的内存地址，请务必牢记这一点。</font>**

**<font style="color:#F5222D;">----------------------------------------------------------------------------------------------------------------------</font>**

WriteProcessMemory(hProcess,pRemoteBuf,(LPVOID)szDlLName,dwBufSize,NULL);

使用WriteProcessMemory()API将DLL路径字符串（“C：\work\myhack.dll”）写入分配所得缓冲区（pRemoteBuf)地址。WriteProcessMemory()API所写的内存空间也是hProcess句柄所指的目标进程（notepad.exe）的内存空间。这样，要注入的DLL文件的路径就被写入目标进程（notepad.exe）的内存空间。

调试API---------------------------------------------------------------------------------------------------------------

**Windows操作系统提供了调试API，借助它们可以访问其他进程的内存空间。**其中具有代表性的有VirtualAllocEx()、VirtualFreeEx()、WriteProcessMemory()、ReadProcessMemory()等。

-----------------------------------------------------------------------------------------------------------------------

获取LoadLibraryW()API地址

hMod=GetModuleHandle("kernel32.dll");

pThreadProc=(LPTHREAD_START_ROUTINE)GetProcAddress(hMod,"LoadLibraryw");

调用LoadLibrary()API前先要获取其地址**（LoadLibraryW****()****是LoadLibrary****()****的Unicode字符串版本）。**

最重要的是理解好以上代码的含义。我们的目标明明是获取加载到notepad.exe进程的kernel32.dll的LoadLibraryW()API的起始地址，但上面的代码却用来获取加载到InjectDll.exe进程的kernel32.dll的LoadLibraryW()API的起始地址。如果加载到notepad.exe进程中的kernel32.dll的地址与加载到InjectDll.exe进程中的kernel32.dll的地址相同，那么上面的代码就不会有什么问题。但是如果kernel32.dll在每个进程中加载的地址都不同，那么上面的代码就错了，执行时会发生内存引用错误。

> **其实在Windows系统中，kernel32.dll在每个进程中的加载地址都是相同的。**
>

《Windows核心编程》一书中对此进行了介绍，此后这一特性被广泛应用于DLL注入技术。

提示------------------------------------------------------------------------------------------------------------------

**根据OS类型、语言、版本不同，kernel32.dll加载的地址也不同。并且Vista/7中应用了新的ASLR功能，每次启动时，系统DLL加载的地址都会改变。但是在系统运行期间它都会被映射（Mapping）到每个进程的相同地址。Windows操作系统中，DLL首次进入内存称为“加载”（Loading），以后其他进程需要使用相同DLL时不必再次加载，只要将加载过的DLL代码与资源映射一下即可，这种映射技术有利于提高内存的使用效率。**

-----------------------------------------------------------------------------------------------------------------------

像上面这样，OS核心DLL会被加载到自身固有的地址，DLL注入利用的就是Windows OS的这一特性（该特性也可能会被恶意使用，成为Windows安全漏洞）。所以，导入InjectDll.exe进程中的LoadLibraryW()地址与导入notepad.exe进程中的LoadLibraryW()地址是相同的。

提示------------------------------------------------------------------------------------------------------------------

一般而言，DLL文件的ImageBase默认为0x10000000，依次加载a.dll与b.dll时，先加载的a.dll被正常加载到0x10000000地址处，后加载的b.dll无法再被加载到此，而是加载到其他空白地址空间，也就是说，该过程中发生了DLL重定位（因为a.dll已经先被加载到它默认的地址处）。

   若kernel32.dll加载到各个进程时地址各不相同，那么上述代码肯定是错误的。但实际在Windows操作系统中，**kernel32.dll不管在哪个进程都会被加载至相同地址。**为什么会这样呢?我借助PEView软件查看了Windows操作系统的核心DLL文件的ImageBase值，罗列如下表（WindowsXPSP3版本，根据Windows更新不同，各值会有变化）。

-----------------------------------------------------------------------------------------------------------------------

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582081490989-e267ae31-169d-497e-9361-13ce84f558e8.png)

微软整理了一份OS核心DLL文件的ImageBase值，防止各DLL文件加载时出现区域重合，这样加载DLL就不会发生DLL重定位了。

-----------------------------------------------------------------------------------------------------------------------

**在目标进程中运行远程线程（Remote Thread）  **

hThread=CreateRemoteThread(hProcess,NULL,0,pThreadProc,pRemoteBuf,0,NULL);

pThreadProc=notepad.exe进程内存中的LoadLibraryw()地址

pRemoteBuf=notepad.exe进程内存中的“c:\work\myhack.dll”字符串地址

一切准备就绪后，最后向notepad.exe发送一个命令，让其调用LoadLibraryW()API函数加载指定的DLL文件即可，遗憾的是Windows并未直接提供执行这一命令的API。但是我们可以另辟蹊径，使用CreateRemote Thread()这个API（在DLL注入时几乎总会用到）。CreateRemote Thread()API用来在目标进程中执行其创建出的线程，其函数原型如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582081691137-e9594e98-3934-4ac6-9c5d-b74b9fa60b25.png)

除第一个参数hProcess外，其他参数与CreateThread()函数完全一样。hProcess参数是要执行线程的目标进程（或称“远程进程”、“宿主进程”）的句柄。lpStartAddress与IpParameter参数分别给出线程函数地址与线程参数地址。需要注意的是，这2个地址都应该在目标进程虚拟内存空间中（这样目标进程才能认识它们）。

初次接触DLL注入技术的读者朋友可能会头昏脑涨、不知所云。本来想向其他进程注入DLL文件，这里为何突然出现线程运行函数呢？仔细观察线程函数ThreadProc()与LoadLibrary()API，可以从中得到一些启示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582081866890-bb0bd772-ac40-4ec4-99db-e3245933b114.png)

两函数都有一个4字节的参数，并返回一个4字节的值。也就是说，二者形态结构完全一样，灵感即源于此。调用CreateRemoteThread()时，只要将LoadLibrary()函数的地址传递给第四个参数lpStartAddress,把要注入的DLL的路径字符串地址传递给第五个参数lpParameter即可（必须是目标进程的虚拟内存空间中的地址）。由于前面已经做好了一切准备，现在调用该函数使目标进程加载指定的DLL文件就行了。

其实，CreateRemote Thread()函数最主要的功能就是驱使目标进程调用LoadLibrary()函数，进而加载指定的DLL文件。

## 23.4.3调试方法
本节将介绍如何从DLL文件注入目标进程就开始调试。首先重新运行notepad.exe，然后使用OllyDbg2的Attach（文件->附加）命令附加新生成的notepad.exe进程（我的没有！！！）（使用最新版本的OllyDbg2进行DLL注入调试更方便）。

如图23-10所示，使用调试器中的Attach命令附加运行中的进程后，进程就会暂停运行。按F9让notepad.exe运行起来。然后如图23-11所示，在Option对话框的Events中复选“Pause on newmodule(DLL)”一项。这样一来，每当有新的DLL被加载到notepad.exe进程，都会在该DLL的EP处暂停。同样，进行DLL注入时也会在该DLL的EP处暂停。使用InjectDll.exe将myhack.dll文件注入notepad.exe进程，此时调试器将暂停，如图23-12所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582082366499-b52f80f9-728f-499c-9640-b1cc2b8d47fe.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582082367991-a1943ea7-3ef5-4d7c-a329-07031e3a0d3f.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582082369325-3c5fccac-1327-4df0-ba1e-291bb0d97351.png)



调试器暂停的地方并不是myhack.dll的EP，而是一个名为MSASN1.dll模块的EP。加载myhack.dll前，需要先加载它导入的所有DLL文件，MSASN1.dl文件即在该过程中被加载。OllyDbg2的Pause on new module(DLL)被选中时，每当加载新的dll文件，都暂停在相应DLL文件的EP处。不断按（F9）运行键，直到在myhack.dll的EP处暂停。

图23-13显示的即是myhack.dll模块的EP入口处，接下来从该入口处调试就可以了（调试前，请先取消对Pause on new module(DLL)项的复选，恢复之前“未选中”状态）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582082478289-d0e8853a-c325-45d3-9ba4-e6eba623114a.png)

提示------------------------------------------------------------------------------------------------------------------       根据用户的系统环境，加载的DLL类型与个数可能有所不同。

-----------------------------------------------------------------------------------------------------------------------

至此，对于使用CreateRemoteThread()函数进行DLL注入技术的讲解就完成了。初学时可能不怎么理解，反复认真阅读前面的讲解，实际动手操作，就较容易掌握。

提示------------------------------------------------------------------------------------------------------------------  

使用CreateRemoteThread(）函数注入相应DLL后，如何再次卸载注入的DLL，这部分内容请参考第24章。

-----------------------------------------------------------------------------------------------------------------------

# 23.5AppInit_DLLs
进行DLL注入的第二种方法是使用注册表。Windows操作系统的注册表中默认提供了AppInt_DLLs与LoadAppInit_DLLs两个注册表项，如图23-14所示。

在注册表编辑器中，将要注入的DLL的路径字符串写入AppInit DLLs项目，然后把LoadApplait_DLLs的项目值设置为1。重启后，指定DLL会注入所有运行进程。该方法操作非常简单，但功能相当强大。

提示------------------------------------------------------------------------------------------------------------------  

上述方法的工作原理是，User32.dll被加载到进程时，会读取AppInit_DLLs注册表项，若有值，则调用LoadLibrary()API加载用户DLL。所以，严格地说，相应DLL并不会被加载到所有进程，而只是加载至加载user32.dll的进程。请注意，Windows XP会忽略LoadAppInit_DLLs注册表项。

-----------------------------------------------------------------------------------------------------------------------

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582082813081-003bfffa-daa0-4097-9c16-2645ccf35b51.png)图23-14注册表编辑器（regedit.exe)

## 23.5.1分析示例源码myhack2.cpp
下面分析一下myhack2.dll的源代码（myhack2.cpp)，如代码25-3所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582082931743-8889dd7c-1b08-4969-b2bd-234b728c5e86.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582082932970-ba609b81-8ce4-4a52-9d9c-c7192ea7910e.png)

myhack2.dl的源代码非常简单，若当前加载自己的进程为“notepad.exe”，则以隐藏模式运行IE，连接指定网站。这样就可以根据不同目的执行多种任务了。

## 23.5.2练习示例myhack2.dll
下面使用修改注册表项的方法做个DLL注入练习，注意操作顺序。

复制文件首先将要注入的DLL文件（myhack2.dll）复制到合适位置（在我电脑中的位置为C:\work\myhack2.dll)，如图23-15所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582083005406-4e64a290-8341-4822-bf61-0faeebc91c1a.png)

修改注册表项 运行注册表编辑器regedit.exe，进入如下路径。

HKEY_LOCAL MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows

编辑修改AppInit_DLLs表项的值，如图23-16所示（请输入myhack2.dll的完整路径）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582083087624-65fda240-642d-4b3f-ba4e-f8ecb91d215b.png)

然后修改LoadAppInit_DLLs注册表项的值为1，如图23-17所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582083088305-2963d3ea-b592-4620-9604-f66484281370.png)

**重启系统**

注册表项修改完毕后，重启系统，使修改生效。系统重启完成后，使用Process Explorer查看myhack2.dll是否被注入所有（加载user32.dll的）进程。

从图23-18可以看到，myhack2.dll成功注入所有加载user32.dll的进程。但由于它的目标进程仅是notepad.exe进程，所以在其他进程中不会执行任何动作。运行notepad.exe，可以看到IE被（以隐藏模式）执行，如图23-19所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582083241030-30e053b7-e8a5-4884-b825-eca17bf50a0a.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582083242587-c77fe45b-d5fd-4e2b-a708-66f2b3aeb594.png)

提示-----------------------------------------------------------------------------------------------------------------

**<font style="color:#F5222D;">Applnit_DLLs注册表键非常强大，通过它几乎可以向所有进程注入DLL文件。若波注入的DLL出现问题（Bug)，则有可能导致Windows无法正常启动，所以修改该AppInit_DLLs前务必彻查。</font>**

-----------------------------------------------------------------------------------------------------------------------

# 23.6 SetWindowsHookEx()
注入DLL的第三个方法就是消息钩取，即用SetWindowsHookEx()API安装好消息“钩子”，然后由OS将指定DLL（含有“钩子”过程）强制注入相应（带窗口的）进程。其工作原理与使用方法在第21章中已有详细讲解，请参考。

# 23.7小结
本章我们学习了有关DLL注人的概念及具体的实现方法。这些内容在代码逆向分析中占据着很大比重，学习时要重点理解DLL注入技术的内部工作原理。此外，进程钩取与“打补丁”中也广泛应用DLL注入技术。

# Q&A
Q.开始学习代码逆向分析前，是不是得先学汇编语言、C语言、Win32APl?

A.我开始学习代码逆向分析技术时，完全不懂汇编语言（可能大部分代码逆向分析人员都如此）。入门阶段重要的不是汇编知识，而是调试器的使用方法、Windows内部结构等内容。C语言与Win32API是一定要学好的，如果事先已经学过，那当然好；没学过也不要担心，遇到就随时查看并学习相关资料。初学时多碰壁反而是好事。



Q.我编写了一个DLL文件，想注入Explorer.exe进程，但杀毒软件总是报告病毒。

A.向系统进程注入DLL时，大部分杀毒软件会根据行为算法将其标识为病毒并查杀。



Q.前面的讲解中提到“CreateRemote Thread（）实际调用的是LoadLibrary(）”，实际生成的不是线程吗？

A.是的，会在目标进程中创建线程。与普通意义上的创建线程相比，调用LoadLibrary()占据了很大比重，所以才这样说的（这可能给大家造成了混乱）。



Q.进程A不具有串口通信功能，我想使用DLL注入技术为进程添加该功能，这可以实现吗？

A.从技术角度来说，问题不大。只要把串口通信功能放入要注入的DLL即可。但如需与原程序联动，设计时必须进行更准确的分析，找到合适的方案（我认为这个问题其实就是灵活运用代码逆向分析技术的一个示例，即通过代码逆向分析技术，向程序中添加新功能或修改不足之处）。

