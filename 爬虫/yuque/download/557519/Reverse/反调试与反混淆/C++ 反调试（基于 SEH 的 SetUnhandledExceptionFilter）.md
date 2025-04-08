> 参考资料：
>
> [https://blog.csdn.net/Simon798/article/details/101028924](https://blog.csdn.net/Simon798/article/details/101028924)
>
> [https://blog.csdn.net/Simon798/article/details/101049659](https://blog.csdn.net/Simon798/article/details/101049659)
>

配置好VS中的asm后，在VS中复制以下代码：

```c
#include <iostream>
#include <tchar.h>
#include <Windows.h>
#include <stdio.h>
#include <exception> 


#pragma region 全局变量 
#pragma endregion

#pragma region 依赖函数 
#pragma endregion

#pragma region 功能函数 

/*
异常记录结构体：
	typedef struct _EXCEPTION_POINTERS {
	  PEXCEPTION_RECORD ExceptionRecord;	// 指向 EXCEPTION_RECORD 结构的指针（异常描述结构体）
	  PCONTEXT          ContextRecord;		// 指向 CONTEXT 结构的指针（寄存器结构体）
	} EXCEPTION_POINTERS, *PEXCEPTION_POINTERS;
*/
// 顶级异常筛选函数，不能把功能代码放在这个函数内（会死循环）,非调试模式下回运行这里的代码
LONG WINAPI ExceptionFilter(PEXCEPTION_POINTERS pExcept)
{
	// 跳过下面两行代码：
	// 8900    MOV DWORD PTR DS:[EAX], EAX  
	// FFE0    JMP EAX  
	pExcept->ContextRecord->Eip += 4;

	// 忽略异常，否则程序会退出
	return EXCEPTION_CONTINUE_EXECUTION;
}

#pragma endregion

int _tmain(int argc, _TCHAR* argv[])
{
	// 接管顶级异常处理程序
	SetUnhandledExceptionFilter(ExceptionFilter);

	// 防止在 OD 中点击运行后直接终止，留一个反应时间
	MessageBox(NULL, L"如果程序正在调试，则即将触发断点...", L"MessageBoxW", NULL);

	// 主动制造 "非法地址" 异常，防止程序被调试	mov dword ptr [eax], eax
	__asm {
		xor eax, eax
		mov dword ptr[eax], eax
		jmp eax
	}

	// 验证程序是否正常执行
	MessageBox(NULL, L"只有没有被调试时才能看到我", L"MessageBoxW", NULL);

	getchar();
	return 0;
}
```

看一下这段代码,在被调试时,首先函数执行SetUnhandledExceptionFilter(ExceptionFilter),然后会弹出来"如果程序正在调试，则即将触发断点...",接下来会运行asm代码,在执行mov dword ptr[eax], eax后出发异常(因为所在的内存区域无权限访问),此时EIP指向mov语句,这时候因为ExceptionFilter函数只能在非调试模式下运行,无法处理异常,程序崩溃退出

OD和xdbg中遇到SEH的反应不同，OD在捕获异常之后会直接退出程序，而xdbg则不同，在捕获异常之后会将程序断下来，不会退出。

在VS中编译运行：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595232852721-3e4842db-fc16-4bfe-a319-1c3c02d7b1fa.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595232854082-77b5c03f-2b1f-4542-8cf4-38e7a521333b.png)

解决办法是在调试程序的过程中,遇到这3行汇编代码之后,将EIP设置为3行代码之后的下一行代码,或者是对这3行代码进行nop

直接运行程序的效果如下:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595233083775-d6ed566c-d034-43ad-941b-d7b528ac65e1.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595233084696-33532415-2b5f-4655-8aa6-0ada2629d4ea.png)

出现SEH的题目:

[BUUCTF-安洵杯 2019-crackMe(hook、SM4加密，SEH，base64换表、极其难)](https://www.yuque.com/go/doc/9767260)



