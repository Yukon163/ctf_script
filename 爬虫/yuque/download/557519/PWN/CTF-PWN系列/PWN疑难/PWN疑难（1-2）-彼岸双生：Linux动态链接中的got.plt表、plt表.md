> 附件下载：
>
> 链接: [https://pan.baidu.com/s/1e-lNpJPv_DG7QY9aQwEPCw](https://pan.baidu.com/s/1e-lNpJPv_DG7QY9aQwEPCw)  密码: iadh
>
> --来自百度网盘超级会员V3的分享
>

作为一个资深的崩坏3玩家，觉得使用彼岸双生这个词来比喻got.plt和plt的关系再合适不过了。

> 前置知识：
>
> [https://www.yuque.com/cyberangel/rg9gdm/yklqa0](https://www.yuque.com/cyberangel/rg9gdm/yklqa0)
>
> [https://www.yuque.com/cyberangel/rg9gdm/uvfhz5](https://www.yuque.com/cyberangel/rg9gdm/uvfhz5)
>
> **<font style="color:#F5222D;">got.plt以下简称got</font>**
>

回顾一下ret2libc3攻击方式的核心：

> 我们要泄露函数的真实地址，一般的方法是采用got表泄露，因为只要之前执行过puts函数，got表里存放着就是函数的真实地址了，这里我用的是puts函数，因为程序里已经运行过了puts函数，真实地址已经存放到了got表内。我们得到puts函数的got地址后，可以把这个地址作为参数传递给puts函数，则会把这个地址里的数据，即puts函数的真实地址给输出出来，这样我们就得到了puts函数的真实地址。
>

简而言之，当程序初次执行某一个函数时（如puts，system之类的），程序会自动寻找这个函数在内存中的真实地址并将真实地址存放在这个函数的got表中（动态链接过程），然后去执行它；当第二次执行这个函数时，由于此函数的got表中已经存放这个函数的真实地址，程序会自动jmp然后去执行它。通过动态链接这种方式，大大提高了程序的执行效率

> 注：以上说的真实地址指的是：libc_base(libc在内存中的基地址)+libc.symbol['function_name']（函数在libc文件中的偏移）
>

为了体现程序动态链接的这种方式，我写了一个demo：

```c
#include<stdio.h>
#include<string.h>
int main(){
	sleep(0);
	puts("aaaaaaaaa");
	sleep(0);
	puts("bbbbbbbbb");
	sleep(0);
	return 0;
}
```

> 编译方式：gcc -g -z execstack -fno-stack-protector test.c -o test
>
> sleep函数只是为了方便下断点而已，没有别的作用。
>
> 我本机Linux环境：
>
> ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608877065731-43913d02-3379-4db6-b77b-85e2d0c08462.png)
>
> 并将地址随机化关闭：
>
> ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608877129966-7d91368d-1a43-494f-af29-7a72080387e3.png)
>

编译完成之后，开始使用pwndbg进行调试，先来看一下程序的内存分布：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608879132761-dadea9f0-dc94-4bc0-90f5-7df8074dfc35.png)

对sleep下断点，开始运行程序，程序会自动断在sleep函数内部，输入finish跳出sleep函数到main函数中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608877521160-8db01a4d-0063-4fa7-9bd7-dd9926f909c9.png)

然后将程序拖入到IDA中，熟悉一下程序，易得到：

```c
.text:000000000040057E                 call    _puts
-------------------------------------------------------------------------
.plt:0000000000400430 ; int puts(const char *s)
.plt:0000000000400430 _puts           proc near               ; CODE XREF: main+18↓p
.plt:0000000000400430                                         ; main+31↓p
.plt:0000000000400430                 jmp     cs:off_601018
.plt:0000000000400430 _puts           endp
-------------------------------------------------------------------------
.got.plt:0000000000601018 off_601018      dq offset puts          ; DATA XREF: _puts↑r
-------------------------------------------------------------------------
extern:0000000000601050 ; int puts(const char *s)
extern:0000000000601050                 extrn puts:near         ; DATA XREF: .got.plt:off_601018↑o
```

回到gdb中，单步步过“ ► 0x400579 <main+19>    mov    edi, 0x400644”，然后输入si以单步步入到puts@plt <puts@plt>中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608877930119-79ab356a-b4da-44f4-aeae-6a38605eb1d9.png)

根据IDA中所显示的地址看一下此时puts got表中的内容：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608878189846-254cede3-a7c1-4d03-a58e-f0746b54fbec.png)

可以看到，got表中并没有存放puts的真实地址，从上面的汇编代码可以看到，程序将要跳转到0x601018执行这个地址中的内容，而0x601018存放的地址是0x400436：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608879555421-e0ab9aa8-6cb9-4dc0-80de-004281513add.png)

因此程序会执行0x400436的内容：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608879765846-795d5136-3165-4f9a-af2a-a166a3e5f598.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608879790282-6dd8a366-e5c1-431f-a334-7e21ed191e00.png)

si单步步入到<_dl_runtime_resolve_xsavec>：如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608878622400-3d3638a7-640d-452b-8b61-de0ffbbb4ec7.png)

然后输入finish直接跳出这个函数：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608878690985-6fb75a9c-ec33-44d5-9a9b-623cb875a9a8.png)

再来看一下此时的got表：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608878738802-58a7570d-5549-4a2d-84c9-a6eefe2a5223.png)

可以看到，got表中现在已经存放有puts函数的真实地址。我们单步步入到下一个puts：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608878935684-3a858443-e7a1-40d6-80e4-127e0c114996.png)

> *RIP  0x400430 (puts@plt) ◂— jmp    qword ptr [rip + 0x200be2]
>

可以看到下一步就可以直接执行0x601018中puts的真实地址了：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1608880234868-cc3c11ee-7817-451b-8b6b-b9b757b43ce0.png)

由此我们可以看到，使用ret2libc3的方式对栈进行leak时，可以根据got表中存放的真实地址来泄露libc基地址：

libc_base=leak_function_addr_in_stack-libc.symbols['function']



