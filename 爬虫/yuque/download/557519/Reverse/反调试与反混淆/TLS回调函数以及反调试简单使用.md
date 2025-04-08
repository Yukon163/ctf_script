> 参考资料：[https://www.cnblogs.com/2f28/p/10051042.html](https://www.cnblogs.com/2f28/p/10051042.html)
>

TLS回调函数是指，每当创建/终止进程的线程时会自动调用执行的函数。创建的主线程也会自动调用回调函数，**<font style="color:#F5222D;">且其调用执行先于EP代码。</font>**

由于TLS优先于EP代码执行，因此我们可以使用来做反调试。但是这个反调试的手法有一定的局限性，因为 TLS （线程局部存储）只是优先于 main 函数运行而已，并不是专门的反调试，所以——这种反调试只能防止原版OD打开，而不能防止OD附加。

下面我们来创建一个TLS调用实例来看看这个过程会发生什么。

程序如下：

```c
#include <iostream>
#include<windows.h>

//声明要使用TLS
#pragma comment(linker,"/INCLUDE:__tls_used")

void print_consoleA(const char* szMsg){
	HANDLE hStdout = GetStdHandle(STD_OUTPUT_HANDLE);
	WriteConsoleA(hStdout, szMsg, strlen(szMsg), NULL, NULL);
}
//定义两个TLS回调函数
//注意一下这个回调函数的参数表，和DLLmain一样的
//Reason的值分别有四种
// #define DLL_PROCESS_ATTACH   1
// #define DLL_THREAD_ATTACH    2
//#define DLL_THREAD_DETACH    3
//#define DLL_PROCESS_DETACH   0

void NTAPI TLS_CALLBACK1(PVOID Dllhandle, DWORD Reason, PVOID Reserved){
	char szMsg[80] = { 0, };
	wsprintfA(szMsg, "TLS_CALLBACK1():DllHandle =%X,Reason=%d\n", Dllhandle, Reason);
	print_consoleA(szMsg);
}

void NTAPI TLS_CALLBACK2(PVOID Dllhandle, DWORD Reason, PVOID Reserved){
	char szMsg[80] = { 0, };
	wsprintfA(szMsg, "TLS_CALLBACK2():DllHandle =%X,Reason=%d\n", Dllhandle, Reason);
	print_consoleA(szMsg);

}

//在数据段注册两个TLS回调函数
#pragma data_seg(".CRT$XLX")
PIMAGE_TLS_CALLBACK pTLS_CALLBACK[] = { TLS_CALLBACK1,TLS_CALLBACK2 ,0 };
#pragma data_seg()


//新建线程
DWORD WINAPI ThreadProc(LPVOID lParam){
	print_consoleA("ThreadProc() start\n");
	print_consoleA("ThreadProc() end\n");
	return 0;

}
int main(){
	HANDLE hThread = NULL;
	print_consoleA("main() start\n");
	hThread = CreateThread(NULL, 0, ThreadProc, NULL, 0, NULL);
	WaitForSingleObject(hThread, 60 * 1000);
	CloseHandle(hThread);
	print_consoleA("main() end\n");
}
```

编译程序，记住要在VS中的debug模式下编译，不然无法打印出完整的日志信息。

release：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595236529144-27795c12-705d-4db4-b304-ad143ef46f0e.png)

debug：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595236556777-ee1896ac-c0ac-4c7d-8bfb-e0347f057e06.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595302077989-3dfae912-a5e9-412a-8392-5c0c29e2fc30.png)

可以看到，在debug中回调函数中TLS函数优于main函数执行

> 代码看不懂没有关系，只需要知道TLS函数的特性就行了
>

由上述log信息可以知道TLS回调函数是在进程或者线程开始前就已经执行了，在进程或者线程结束后也结束。

接下来使用C++编写简单的反调试程序，程序如下：

```c
#include <iostream>
#include<windows.h>

//声明使用TLS回调函数
#pragma comment(linker,"/INCLUDE:__tls_used")

//定义回调函数
void NTAPI TLS_CallBack(PVOID Dllhandle, DWORD Reason, PVOID Reserved){
	//发现被调试就退出，使用这个API来侦察反调试已经完全不管用了
	//吾爱的OD和看雪的OD已经可以屏蔽这个API了，所以起不到反调试的作用，API仅做原理演示用
	if (IsDebuggerPresent()){
		MessageBoxA(NULL, "Debugger Detect！！", "TLS_CALLBACK", MB_OK);
		ExitProcess(1);
	}
}

//注册TLS回调函数
#pragma data_seg(".CRT$XLX")
PIMAGE_TLS_CALLBACK pTls_CallBack[] = { TLS_CallBack,0 };
#pragma data_seg()

int main(void){
	MessageBoxA(NULL, "No Debugger!", "main()", MB_OK);
}
```

release效果：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595237605484-207d5313-23cb-41b5-a031-e7721515cc8c.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595301271297-533ed9ac-8fbc-4a6f-b157-84873582ebf4.png)

> 注：在这里要注意的是吾爱的OD和看雪的OD已经可以屏蔽这个API了，所以起不到反调试的作用，只有原版的OD才能实现反调试。
>

上图可以看出，TLS已经先调用来检测是否被调试。

