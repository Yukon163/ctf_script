除了前面讲过的DLL动态注入技术外，还可以采用“手工修改可执行文件”的方式加载用户指定的DLL文件，本章将向各位介绍这种方法。学习这种技术前，首先要掌握有关PE文件格式的知识。

前面我们学过向“运行中的进程”强制注入指定DLL文件的方法。下面我们将换用另外一种方法，通过“直接修改目标程序的可执行文件”，使其运行时强制加载指定的DLL文件。这种方法只要应用过一次后（不需要另外的注入操作），每当进程开始运行时就会自动加载指定的DLL文件。其实，这是一种破解的方法。

# 25.1练习文件
本节将做个简单练习以帮助大家更好地理解要学习的内容。我们的目标是，直接修改TextView.exe文件，使其在运行时自动加载myhack3.dll文件（这需要各位事先掌握修改PE文件头的相关知识与技术）。

## 25.1.1 TextView.exe
TextView.exe是一个非常简单的文本查看程序，只要用鼠标将要查看的文本文件（myhack3.cpp）拖动（Drop）到其中，即可通过它查看文本文件的内容，如图25-1所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582098766267-b031b8d0-7b19-44bf-901a-30db3ed757c3.png)

各位可将任意一个文本文件拖入其中测试。接下来，使用PEView工具查看TextView.exe可执行文件的IDT（Import Directory Table，导入目录表）。

从图25-2中可以看到，TextView.exe中直接导入的DLL文件为KERNEL32.dll、USER32.dll、 GDI32.dll、SHELL32.dll。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582098914745-f4945aeb-6d61-4685-82bf-40e0455865ad.png)

图25-2PEView：TextView.exe的IDT

## 25.1.2 TextView_patched.exe
TextView_patched.exe是修改TextView.exe文件的IDT后得到的文件，即在IDT中添加了导入 myhack3.dll的部分，运行时会自动导入myhakc3.dll文件。使用PEView工具查看TextView_ patched.exe的IDT，如图25-3所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582099084335-ad061d4f-c27e-429d-a55f-c8852a40ddc0.png)

图25-3 PEView:TextView _Patched.exe的IDT

从图25-3可以看到，IDT中除了原来的4个DLL文件外，还新增了一个myhack3.dll文件。这样，运行TextView_Patched.exe文件时程序就会自动加载myhack3.dl文件。下面运行TextView_Patched.exe看看是否如此。

运行程序并稍等片刻，指定的index.html文件会被下载到工作目录，同时，文本查看程序会自动将其打开，如图25-4所示（运行程序后会自动加载myhack3.dll，尝试连接Google网站，下载网站的index.html文件，并将其拖放到TextView_Patched.exe程序）。进入工作目录，使用网络浏览器打开下载的index.html文件，如图25-5所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582099225801-2c2aef59-9617-4935-8353-9052c045ad06.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582099226993-a0b2654a-dd98-4318-a2cf-ff0643b21ef7.png)

从图25-5中可以看到，下载的的确是谷歌的index.html文件。

提示------------------------------------------------------------------------------------------------------------------

系统环境不同（网络、防火墙策略、安全/管理程序等），可能导致index.html文件无法下载。若正常运行仍无法成功下载index.html文件，建议更换不同的系统环境再次测试。

-----------------------------------------------------------------------------------------------------------------------

# 25.2源代码-myhack3.cpp
本节将分析myhack3.dll的源代码（myhack3.cpp)。

提示------------------------------------------------------------------------------------------------------------------

所有源代码均使用MS Visual C++2010 Express Edition编写而成，在WindowsXP/7 32位环境中通过测试。

-----------------------------------------------------------------------------------------------------------------------

## 25.2.1 DlIMain()
**<font style="color:#c586c0;">#include</font>****<font style="color:#569cd6;"> </font>****<font style="color:#ce9178;">"stdio.h"</font>**

**<font style="color:#c586c0;">#include</font>****<font style="color:#569cd6;"> </font>****<font style="color:#ce9178;">"windows.h"</font>**

**<font style="color:#c586c0;">#include</font>****<font style="color:#569cd6;"> </font>****<font style="color:#ce9178;">"shlobj.h"</font>**

**<font style="color:#c586c0;">#include</font>****<font style="color:#569cd6;"> </font>****<font style="color:#ce9178;">"Wininet.h"</font>**

**<font style="color:#c586c0;">#include</font>****<font style="color:#569cd6;"> </font>****<font style="color:#ce9178;">"tchar.h"</font>**



**<font style="color:#c586c0;">#pragma</font>****<font style="color:#569cd6;"> </font>****<font style="color:#9cdcfe;">comment</font>****<font style="color:#569cd6;">(</font>****<font style="color:#9cdcfe;">lib</font>****<font style="color:#569cd6;">, "</font>****<font style="color:#9cdcfe;">Wininet</font>****<font style="color:#569cd6;">.</font>****<font style="color:#9cdcfe;">lib</font>****<font style="color:#569cd6;">")</font>**



**<font style="color:#c586c0;">#define</font>****<font style="color:#569cd6;"> DEF_BUF_SIZE            (4096)</font>**

**<font style="color:#c586c0;">#define</font>****<font style="color:#569cd6;"> DEF_URL                 </font>****<font style="color:#ce9178;">L"http://www.google.com/index.html"</font>**

**<font style="color:#c586c0;">#define</font>****<font style="color:#569cd6;"> DEF_INDEX_FILE          </font>****<font style="color:#ce9178;">L"index.html"</font>**



**<font style="color:#d4d4d4;">HWND g_hWnd = </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">;</font>**



**<font style="color:#c586c0;">#ifdef</font>****<font style="color:#569cd6;"> __cplusplus</font>**

**<font style="color:#569cd6;">extern</font>****<font style="color:#d4d4d4;"> </font>****<font style="color:#ce9178;">"C"</font>****<font style="color:#d4d4d4;"> {</font>**

**<font style="color:#c586c0;">#endif</font>**

**<font style="color:#6a9955;">// IDT 형식을 위한 dummy export function...</font>**

**<font style="color:#d4d4d4;">__declspec(</font>****<font style="color:#4ec9b0;">dllexport</font>****<font style="color:#d4d4d4;">) </font>****<font style="color:#569cd6;">void</font>****<font style="color:#d4d4d4;"> </font>****<font style="color:#dcdcaa;">dummy</font>****<font style="color:#d4d4d4;">()</font>**

**<font style="color:#d4d4d4;">{</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">}</font>**

**<font style="color:#c586c0;">#ifdef</font>****<font style="color:#569cd6;"> __cplusplus</font>**

**<font style="color:#d4d4d4;">}</font>**

**<font style="color:#c586c0;">#endif</font>**

DlIMain()函数的功能非常简单，创建线程运行指定的线程过程，在线程过程（ThreadProc)中调用DownloadURL()与DropFile()函数，下载指定的网页并将其拖放到文本查看程序。下面分别详细查看这2个函数。

## 25.2.2 DownloadURL()
**<font style="color:#4ec9b0;">BOOL </font>****<font style="color:#dcdcaa;">DownloadURL</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#4ec9b0;">LPCTSTR</font>****<font style="color:#d4d4d4;"> </font>****<font style="color:#9cdcfe;">szURL</font>****<font style="color:#d4d4d4;">, </font>****<font style="color:#4ec9b0;">LPCTSTR</font>****<font style="color:#d4d4d4;"> </font>****<font style="color:#9cdcfe;">szFile</font>****<font style="color:#d4d4d4;">)</font>**

**<font style="color:#d4d4d4;">{</font>**

**<font style="color:#d4d4d4;">    BOOL            bRet = FALSE;</font>**

**<font style="color:#d4d4d4;">    HINTERNET       hInternet = </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">, hURL = </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">    BYTE            </font>****<font style="color:#9cdcfe;">pBuf</font>****<font style="color:#d4d4d4;">[DEF_BUF_SIZE] = {</font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">,};</font>**

**<font style="color:#d4d4d4;">    DWORD           dwBytesRead = </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">    FILE            *pFile = </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#4ec9b0;">errno_t</font>****<font style="color:#d4d4d4;">         err = </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">;</font>**



**<font style="color:#d4d4d4;">    hInternet = </font>****<font style="color:#dcdcaa;">InternetOpen</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#ce9178;">L"ReverseCore"</font>****<font style="color:#d4d4d4;">, </font>**

**<font style="color:#d4d4d4;">                             INTERNET_OPEN_TYPE_PRECONFIG, </font>**

**<font style="color:#d4d4d4;">                             </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">, </font>**

**<font style="color:#d4d4d4;">                             </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">, </font>**

**<font style="color:#d4d4d4;">                             </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">);</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;"> == hInternet )</font>**

**<font style="color:#d4d4d4;">    {</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">OutputDebugString</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#ce9178;">L"InternetOpen() failed!"</font>****<font style="color:#d4d4d4;">);</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> FALSE;</font>**

**<font style="color:#d4d4d4;">    }</font>**



**<font style="color:#d4d4d4;">    hURL = </font>****<font style="color:#dcdcaa;">InternetOpenUrl</font>****<font style="color:#d4d4d4;">(hInternet,</font>**

**<font style="color:#d4d4d4;">                           szURL,</font>**

**<font style="color:#d4d4d4;">                           </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">,</font>**

**<font style="color:#d4d4d4;">                           </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">,</font>**

**<font style="color:#d4d4d4;">                           INTERNET_FLAG_RELOAD,</font>**

**<font style="color:#d4d4d4;">                           </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">);</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;"> == hURL )</font>**

**<font style="color:#d4d4d4;">    {</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">OutputDebugString</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#ce9178;">L"InternetOpenUrl() failed!"</font>****<font style="color:#d4d4d4;">);</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">goto</font>****<font style="color:#d4d4d4;"> _DownloadURL_EXIT;</font>**

**<font style="color:#d4d4d4;">    }</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( err = </font>****<font style="color:#dcdcaa;">_tfopen_s</font>****<font style="color:#d4d4d4;">(&pFile, szFile, </font>****<font style="color:#ce9178;">L"wt"</font>****<font style="color:#d4d4d4;">) )</font>**

**<font style="color:#d4d4d4;">    {</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">OutputDebugString</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#ce9178;">L"fopen() failed!"</font>****<font style="color:#d4d4d4;">);</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">goto</font>****<font style="color:#d4d4d4;"> _DownloadURL_EXIT;</font>**

**<font style="color:#d4d4d4;">    }</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">while</font>****<font style="color:#d4d4d4;">( </font>****<font style="color:#dcdcaa;">InternetReadFile</font>****<font style="color:#d4d4d4;">(hURL, pBuf, DEF_BUF_SIZE, &dwBytesRead) )</font>**

**<font style="color:#d4d4d4;">    {</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( !dwBytesRead )</font>**

**<font style="color:#d4d4d4;">            </font>****<font style="color:#c586c0;">break</font>****<font style="color:#d4d4d4;">;</font>**



**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">fwrite</font>****<font style="color:#d4d4d4;">(pBuf, dwBytesRead, </font>****<font style="color:#b5cea8;">1</font>****<font style="color:#d4d4d4;">, pFile);</font>**

**<font style="color:#d4d4d4;">    }</font>**



**<font style="color:#d4d4d4;">    bRet = TRUE;</font>**



**<font style="color:#c8c8c8;">_DownloadURL_EXIT</font>****<font style="color:#d4d4d4;">:</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( pFile )</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">fclose</font>****<font style="color:#d4d4d4;">(pFile);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( hURL )</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">InternetCloseHandle</font>****<font style="color:#d4d4d4;">(hURL);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( hInternet )</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">InternetCloseHandle</font>****<font style="color:#d4d4d4;">(hInternet);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> bRet;</font>**

**<font style="color:#d4d4d4;">}</font>**

DownloadURL()函数会下载参数szURL中指定的网页文件，并将其保存到szFile目录。示例中， 该函数用来连接谷歌网站（www.google.com)，并下载网站的index.html文件。

提示------------------------------------------------------------------------------------------------------------------  

实际上，上述示例中的DownloadURL()函数是使用InternetOpen()、InternetOpenUrl()、 InternetReadFile()API对URLDownloadToFile()API的简单实现。InternetOpen()、 InternetOpenUrl()、InternetReadFile()API均在wininet.dll中提供，而URLDownloadToFile()API在urlmon.dll中提供。

-----------------------------------------------------------------------------------------------------------------------

## 25.2.3 DropFile()
**<font style="color:#d4d4d4;">BOOL CALLBACK </font>****<font style="color:#dcdcaa;">EnumWindowsProc</font>****<font style="color:#d4d4d4;">(HWND hWnd, LPARAM lParam)</font>**

**<font style="color:#d4d4d4;">{</font>**

**<font style="color:#d4d4d4;">    DWORD dwPID = </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">;</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#dcdcaa;">GetWindowThreadProcessId</font>****<font style="color:#d4d4d4;">(hWnd, &dwPID);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( dwPID == (DWORD)lParam )</font>**

**<font style="color:#d4d4d4;">    {</font>**

**<font style="color:#d4d4d4;">        g_hWnd = hWnd;</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> FALSE;</font>**

**<font style="color:#d4d4d4;">    }</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> TRUE;</font>**

**<font style="color:#d4d4d4;">}</font>**



**<font style="color:#4ec9b0;">HWND</font>****<font style="color:#d4d4d4;"> </font>****<font style="color:#dcdcaa;">GetWindowHandleFromPID</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#4ec9b0;">DWORD</font>****<font style="color:#d4d4d4;"> </font>****<font style="color:#9cdcfe;">dwPID</font>****<font style="color:#d4d4d4;">)</font>**

**<font style="color:#d4d4d4;">{</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#dcdcaa;">EnumWindows</font>****<font style="color:#d4d4d4;">(EnumWindowsProc, dwPID);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> g_hWnd;</font>**

**<font style="color:#d4d4d4;">}</font>**



**<font style="color:#4ec9b0;">BOOL</font>****<font style="color:#d4d4d4;"> </font>****<font style="color:#dcdcaa;">DropFile</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#4ec9b0;">LPCTSTR</font>****<font style="color:#d4d4d4;"> </font>****<font style="color:#9cdcfe;">wcsFile</font>****<font style="color:#d4d4d4;">)</font>**

**<font style="color:#d4d4d4;">{</font>**

**<font style="color:#d4d4d4;">    HWND            hWnd = </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">    DWORD           dwBufSize = </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">    BYTE            *pBuf = </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">; </font>**

**<font style="color:#d4d4d4;">    DROPFILES       *pDrop = </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#569cd6;">char</font>****<font style="color:#d4d4d4;">            </font>****<font style="color:#9cdcfe;">szFile</font>****<font style="color:#d4d4d4;">[MAX_PATH] = {</font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">,};</font>**

**<font style="color:#d4d4d4;">    HANDLE          hMem = </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">;</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#dcdcaa;">WideCharToMultiByte</font>****<font style="color:#d4d4d4;">(CP_ACP, </font>****<font style="color:#b5cea8;">0</font>****<font style="color:#d4d4d4;">, wcsFile, -</font>****<font style="color:#b5cea8;">1</font>****<font style="color:#d4d4d4;">,</font>**

**<font style="color:#d4d4d4;">                        szFile, MAX_PATH, </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">, </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">);</font>**



**<font style="color:#d4d4d4;">    dwBufSize = </font>****<font style="color:#569cd6;">sizeof</font>****<font style="color:#d4d4d4;">(DROPFILES) + </font>****<font style="color:#dcdcaa;">strlen</font>****<font style="color:#d4d4d4;">(szFile) + </font>****<font style="color:#b5cea8;">1</font>****<font style="color:#d4d4d4;">;</font>**

**<font style="color:#d4d4d4;">    </font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( !(hMem = </font>****<font style="color:#dcdcaa;">GlobalAlloc</font>****<font style="color:#d4d4d4;">(GMEM_ZEROINIT, dwBufSize)) )</font>**

**<font style="color:#d4d4d4;">    {</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">OutputDebugString</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#ce9178;">L"GlobalAlloc() failed!!!"</font>****<font style="color:#d4d4d4;">);</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> FALSE;</font>**

**<font style="color:#d4d4d4;">    }</font>**



**<font style="color:#d4d4d4;">    pBuf = (LPBYTE)</font>****<font style="color:#dcdcaa;">GlobalLock</font>****<font style="color:#d4d4d4;">(hMem);</font>**



**<font style="color:#d4d4d4;">    pDrop = (DROPFILES*)pBuf; </font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#9cdcfe;">pDrop</font>****<font style="color:#d4d4d4;">-></font>****<font style="color:#9cdcfe;">pFiles</font>****<font style="color:#d4d4d4;"> = </font>****<font style="color:#569cd6;">sizeof</font>****<font style="color:#d4d4d4;">(DROPFILES);</font>**

**<font style="color:#d4d4d4;">    </font>****<font style="color:#dcdcaa;">strcpy_s</font>****<font style="color:#d4d4d4;">((</font>****<font style="color:#569cd6;">char</font>****<font style="color:#d4d4d4;">*)(pBuf + </font>****<font style="color:#569cd6;">sizeof</font>****<font style="color:#d4d4d4;">(DROPFILES)), </font>****<font style="color:#dcdcaa;">strlen</font>****<font style="color:#d4d4d4;">(szFile)+</font>****<font style="color:#b5cea8;">1</font>****<font style="color:#d4d4d4;">, szFile);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#dcdcaa;">GlobalUnlock</font>****<font style="color:#d4d4d4;">(hMem);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">if</font>****<font style="color:#d4d4d4;">( !(hWnd = </font>****<font style="color:#dcdcaa;">GetWindowHandleFromPID</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#dcdcaa;">GetCurrentProcessId</font>****<font style="color:#d4d4d4;">())) )</font>**

**<font style="color:#d4d4d4;">    {</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#dcdcaa;">OutputDebugString</font>****<font style="color:#d4d4d4;">(</font>****<font style="color:#ce9178;">L"GetWndHandleFromPID() failed!!!"</font>****<font style="color:#d4d4d4;">);</font>**

**<font style="color:#d4d4d4;">        </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> FALSE;</font>**

**<font style="color:#d4d4d4;">    }</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#dcdcaa;">PostMessage</font>****<font style="color:#d4d4d4;">(hWnd, WM_DROPFILES, (WPARAM)pBuf, </font>****<font style="color:#569cd6;">NULL</font>****<font style="color:#d4d4d4;">);</font>**



**<font style="color:#d4d4d4;">    </font>****<font style="color:#c586c0;">return</font>****<font style="color:#d4d4d4;"> TRUE;</font>**

**<font style="color:#d4d4d4;">}</font>**

DropFile()函数将下载的index.html文件拖放到TextView_Patch.exe进程并显示其内容。为此，需要先获取TextView Patch.exe进程的主窗口句柄，再传送WM_DROPFILES消息。总之，DropFile()函数的主要功能是，使用PID获取窗口句柄，再调用postMessage(WM_DROPFILES)API将消息放入消息队列（此处省略有关API的详细说明）。

## 25.2.4 dummy()
在myhack3.cpp源代码中还要注意dummy()这个函数。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582100105145-ee5e6e10-6373-44b4-9caf-4f06a8dcc326.png)

dummy()函数是myhack3.dll文件向外部提供服务的导出函数，但正如所见，它没有任何功能。

既然如此，为何还要将其导出呢？这是为了保持形式上的完整性，使myhack3.dll能够顺利添加到TextView.exe文件的导入表。

**在PE文件中导入某个DLL，实质就是在文件代码内调用该DLL提供的导出函数。**PE文件头中记录着DLL名称、函数名称等信息。因此，myhack3.dll至少要向外提供1个以上的导出函数才能保持形式上的完整性。

一般而言，向导入表中添加DLL是由程序的构建工具（VC++、VB、Delphi等）完成的，但下面我们将直接使用PE Viewer与Hex Editor两个工具修改TextView.exe的导入表，以便更好地学习代码逆向分析知识。

# 25.3修改TextView.exe文件的准备工作
## 25.3.1修改思路
如前所见，PE文件中导入的DLL信息以结构体列表形式存储在IDT中。只要将myhack3.dll添加到列表尾部就可以了。当然，此前要确认一下IDT中有无足够空间。

## 25.3.2查看IDT是否有足够空间
首先，使用PEView查看TextView.exe的IDT地址（PE文件头的IMAGE_OPTIONAL_HEADER结构体中导入表RVA值即为IDT的RVA）。

从图25-6可知，IDT的地址（RVA）为84CC。接下来，在PEView中直接查看IDT（在PEView工具栏中设置地址视图选项为RVA）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582101035408-e905aec6-16f2-418f-9754-af184622f3e9.png)

图25-6 PEView:IMAGE_OPTIONAL_HEADER中IDT的RVA值

从图中可以看到，TextView.exe的IDT存在于.rdata节区。我们在前面学过PE文件头的知识，**知道IDT是由IMAGE_IMPORT_DESCRIPTOR（以下称****I****I****D）结构体组成的数组，且数组末尾以NULL结构体结束。**由于每个导入的DLL文件都对应1个IID结构体（每个IID结构体的大小为14个字节），所以图25-7中整个IID区域为RVA：84CC~852F（整体大小为14*5=64）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582101001540-d181b84b-ac42-46e4-acb6-e1578b487e16.png)

图25-7 PEView:IDT

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582101333555-5f5e09a3-17e0-4727-b64f-61b78fa01918.png)

在PEView工具栏中将视图改为File Offset，可以看到IDT的文件偏移为76CC，如图25-8所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582101684988-031d00ed-b737-4ee7-8e25-0dfc7c39b799.png)

使用HxD实用工具打开TextView.exe文件，找到76CC地址处，如图25-9所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582101942686-da96651a-e1ee-4ea4-a2e0-1297c7bdc2ea.png)

图25-9HxD:Import Directory Table

IDT的文件偏移为76CC~772F，整个大小为64字节，共有5个ID结构体，其中最后一个为NULL结构体。从图中可以看出IDT尾部存在其他数据，没有足够空间来添加myhack3.dll的IID结构体。

## 25.3.3移动IDT
在这种情形下，我们要先把整个IDT转移到其他更广阔的位置，然后再添加新的ID。确定移动的目标位置时，可以使用下面三种方式：

+ 查找文件中的空白区域；
+ 增加文件最后一个节区的大小；
+ 在文件末尾添加新节区。

首先尝试第一种方法，即查找文件中的空白区域（程序运行时未使用的区域）。正如在图25-10中看到的一样，.rdata节区尾部恰好存在大片空白区域（一般说来，节区或文件末尾都存在空白区域，PE文件中这种空白区域称为Null-Padding区域）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582102150429-006279ae-09d9-4e5d-bb39-80017c72ff53.png)

图25-10PEView:.rdata节区尾部的Null-Padding区域

接下来，把原IDT移动到该Null-Padding区域（RVA：8C60~8DFF)中合适位置就行了。在此之前，先要确认一下该区域（RVA：8C60~8DFF）是否全是空白可用区域（Null-Padding区域）。

请注意，并不是文件中的所有区域都会被无条件加载到进程的虚拟内存，只有节区头中明确记录的区域才会被加载。使用PEView工具查看TextView.exe文件的.rdata节区头，如图25-11所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582102323457-109dc1e9-ba31-474b-abd2-c4f10506fa2f.png)

节区头中存储着对应节区的位置、大小、属性等信息。参照图25-11，整理.rdata节区头中信息如表25-1。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582102400281-e88d6b67-bb84-4607-9a0f-60ed9ec741ad.png)

从节区头中信息可以看出，.rdata节区在磁盘文件与内存中的大小是不同的。

.rdata节区在磁盘文件中的大小为2E00，而文件执行后被加载到内存时，程序实际使用的数据大小（映射大小）仅为2C56，剩余未被使用的区域大小为1AA（2E00-2C56）。在这段空白区域创建IDT是不会有什么问题的。

提示------------------------------------------------------------------------------------------------------------------

**PE文件尾部有些部分填充着NULL，但这并不意味着这些部分一定就是Null-Padding区域（空白可用区域）。这些区域也有可能是程序使用的区域，且并非所有Null-Padding区域都会加载到内存。只有分析节区头信息后才能判断。如果示例中TextView.exe的Null-Padding区域很小，无法容纳IDT，那么就要增加最后节区的尺寸或添加新节区，以保证有足够空间存放IDT。**

-----------------------------------------------------------------------------------------------------------------------

由于图25-10中的Null-Padding区域可以使用，接下来，我们要在RVA：8C80（RAW：7E80）位置创建IDT（请记住这个位置）。

# 25.4修改TextView.exe
先把TextView.exe复制到工作文件夹，重命名为TextView Patch.exe。下面使用TextView_Patch.exe文件练习打补丁。基本的操作步骤是：先使用PEView打开TextView.exe原文件，查看各种PE信息，然后使用HxD打开TextView Patch.exe文件进行修改。

## 25.4.1修改导入表的RVA值
**IMAGE_OPTIONAL_HEADER的导入表结构体成员用来指出IDT的位置（RVA）与大小**，如图25-12所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582102962143-bc8f06e6-e9b2-4608-a05e-b1cc735b98c0.png)

TextView.exe文件中，导入表的RVA值为84CC。接下来，将导入表的RVA值更改为新IDT的RVA值8C80，在Size原值64字节的基础上加14个字节（IID结构体的大小），修改为78字节（参考图25-13）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582103033615-8eb19b41-acf8-4ee1-9912-7c0ecf3a04dd.png)

从现在开始，导入表位于RVA：8C80（RAW：7E80）地址处。

## 25.4.2删除绑定导入表
BOUND_IMPORT_TABLE(绑定导入表）是一种提高DLL加载速度的技术，如图25-14所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582103214957-f3f974e8-9dff-4fa3-af47-ae40ab0ff2a1.png)

若想正常导入myhack3.dll，需要向绑定导入表添加信息。但幸运的是，该绑定导入表是个可选项，不是必须存在的，所以可删除（修改其值为0即可）以获取更大便利。当然，绑定导入表完全不存在也没关系，但若存在，且其内信息记录错误，则会在程序运行时引发错误。本示例TextView.exe文件中，绑定导入表各项的值均为0，不需要再修改。修改其他文件时，一定要注意检查绑定导入表中的数据。 

## 25.4.3创建新IDT
先使用Hex Editor完全复制原IDT（RAW：76CC~772F)，然后覆写（Paste write)到IDT的新位置（RAW：7E80），如图25-15所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582103333236-2883ed8c-15e5-4069-80cc-c3a75edc67f4.png)

然后在新IDT尾部（RAW：7ED0）添加与myhack3.dll对应的ID（后面会单独讲解各成员的数据）：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582103411837-ca9a52b9-db7b-4752-aed7-4b39c0ff6ba4.png)

在准确位置（RAW：7ED0）写入相关数据，如图25-16所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582103474538-42ecc50c-9492-4da2-9dd8-38d44ead67d6.png)

## 25.4.4设置Name、INT、IAT
前面添加的IID结构体成员拥有指向其他数据结构（INT、Name、IAT）的RVA值。因此，必须准确设置这些数据结构才能保证TextView_Patch.exe文件正常运行。由前面设置可知INT、Name、IAT的RVA/RAW的值，整理如表25-2所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582103565393-45aa4808-14cc-4db6-a106-e2ce8d1961c0.png)

提示------------------------------------------------------------------------------------------------------------------

RVA与RAW（文件偏移）间的转换可以借助PEView。但是建议各位掌握它们之间的转换方法，亲自计算（请参考第13章）。

-----------------------------------------------------------------------------------------------------------------------

这些地址（RVA：8D00，8D10，8D20)就位于新创建的IDT（RVA：8C80）下方。我为了操作方便才选定该区域，各位选择其他位置也没关系。在HxD编辑器中转到7F00地址处，输入相应值，如图25-17所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582103720329-f9fd3eb7-2190-4ce3-b849-f385b6863676.png)

下面讲解图25-18中显示的各值意义。

8CD0地址处存在着myhack3.dl的IID结构体，其中3个主要成员（RVAofINT、RVA of Name、RVA ofIAT）的值分别是实际INT、Name、IAT的指针。

简单地说，INT（Import Name Table，导入名称表）是RVA数组，数组的各个元素都是一个RVA地址，该地址由导入函数的Ordinal（2个字节）+Func Name String结构体构成，数组的末尾为NULL。上图中INT有1个元素，其值为8D30，该地址处是要导入的函数的Ordinal（2个字节）与函数的名称字符串（“dummy”）。

Name是包含导入函数的DLL文件名称字符串，在8D10地址处可以看到“myhack3.dll”字符串。

IAT也是RVA数组，各元素既可以拥有与INT相同的值，也可以拥有其他不同值（若INT中的数据准确，IAT也可拥有其他不同值）。反正实际运行时，PE装载器会将虚拟内存中的IAT替换为实际函数的地址。

提示------------------------------------------------------------------------------------------------------------------

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582104068987-b2f17030-c56e-4542-a988-32b27034ca29.png)

-----------------------------------------------------------------------------------------------------------------------

## 25.4.5修改IAT节区的属性值
加载PE文件到内存时，PE装载器会修改IAT，写入函数的实际地址，所以相关节区一定要拥有WRITE（可写）属性。只有这样，PE装载器才能正常进行写入操作。使用PEView查看.rdata节区头，如图25-19所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582104150175-a4e92e9a-9a95-4062-99a8-cf4d9c61482e.png)

向原属性值（Characteristics）40000040添加IMAGE_SCN_MEM_WRITE(80000000)属性值。执行bit OR运算，最终属性值变为C0000040，如图25-20所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582104240975-6069970b-36ac-4bb8-a7c9-fdc04fccd601.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582104339867-c00f7837-d90c-4875-88e8-804aa20f99e5.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582104341720-a8b77cd8-8a5e-4de4-a98d-0b11f49c6c48.png)

# 25.5检测验证
首先使用PEView工具打开修改后的TextView_Patch.exe文件，查看其IDT，如图25-23所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582104459749-49d71f0c-432f-4095-b012-e7fcb43a80ef.png)

向IDT导入myhack3.dll的IID结构体已设置正常。在图25-24中可以看到，myhack3.dll的dummy()函数被添加到INT。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582104545744-e744657d-8ec9-4fca-8ffa-f5e8eceb1aa4.png)

从文件的结构分析来看，修改成功。接下来，直接运行文件看看程序能否正常运行。先将TextView_Patch.exe与myhack3.dl放入相同文件夹，然后运行TextViewPatch.exe文件，如图25-25所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1582104547172-96550da9-d882-4444-85dd-8c7606ad2716.png)

使用Process Explorer工具查看TextView_Patch.exe进程中加载的DLL文件，可以看到已经成功加载myhack3.dll，且被加载的myhack3.dl文件下载了指定网站的index.html文件，并在TextView Patch.exe中显示。

# 25.6小结
本章我们一起学习了直接修改PE文件来加载指定DLL文件的方法，其基本原理是将要加载的dll添加到IDT，这样程序运行时就会自动加载。只要理解了这一基本原理，再结合前面学过的有关PE文件头的知识，相信大家能够非常容易理解（关于PE文件头的知识请参考第13章）。

