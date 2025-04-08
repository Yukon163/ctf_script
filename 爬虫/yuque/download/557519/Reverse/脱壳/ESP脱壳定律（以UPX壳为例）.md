参考资料：

[https://bbs.ichunqiu.com/forum.php?mod=viewthread&tid=15978&extra=&highlight=esp&page=1](https://bbs.ichunqiu.com/forum.php?mod=viewthread&tid=15978&extra=&highlight=esp&page=1)

<font style="color:#F5222D;">（</font><font style="color:#F5222D;">由于在输液时写文章，故部分语言借助如上链接，望理解</font><font style="color:#F5222D;">）</font>

为了方便，我们找到在吾爱破解工具包中找到单文件工具并使用加壳工具对其加壳。

使用的单文件工具如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585614864724-b92c8470-df65-4392-95c6-b4f295891d4d.png)

首先在加壳之前查一下壳：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585615278915-644783cc-9040-466e-afaa-bf247040642e.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585615379856-240c67cf-59ae-465b-803e-48a305e42602.png)

没有壳，接下来手动对其加一个UPX壳，同样使用吾爱破解工具包中的加壳工具

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585615569572-bf7c7bff-f17c-4a2c-8a20-aa4b1a6849ee.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585615622875-46e247c5-34eb-4e9f-9977-a0ea2c6561f2.png)

再检测一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585615706763-4fc0ef10-c7aa-448d-ba23-7bb6f33170f4.png)

加壳成功，接下来使用ESP脱壳定律进行脱壳。



---



ESP脱壳定律原理：“堆栈平衡”原理

在开始讨论ESP定律之前，先给复习一下一些简单的汇编知识。

**1.call**

这个命令是访问子程序的一个汇编基本指令。也许你说，这个我早就知道了！别急请继续看完。call真正的意义是什么呢？我们可以这样来理解：

1.向堆栈中压入下一行程序的地址；

2.JMP到call的子程序地址处。

例如：

00401029.E8           call 004A3508

0040102E.5A           pop edx

在执行了00401029以后，程序会将0040102E压入堆栈，然后JMP到004A3508地址处！

**2.RETN**

与call对应的就是RETN了。对于RETN我们可以这样来理解：

1.将当前的ESP中指向的地址出栈；

2.JMP到这个地址。

这个就完成了一次调用子程序的过程。在这里关键的地方是：如果我们要返回父程序，则当我们在堆栈中进行堆栈的操作的时候，一定要保证在RETN这条指令之前，ESP指向的是我们压入栈中的地址。这也就是著名的“堆栈平衡”原理！（[https://blog.csdn.net/D_R_L_T/article/details/74625872?depth_1-utm_source=distribute.pc_relevant.none-task&utm_source=distribute.pc_relevant.none-task](https://blog.csdn.net/D_R_L_T/article/details/74625872?depth_1-utm_source=distribute.pc_relevant.none-task&utm_source=distribute.pc_relevant.none-task)）

<font style="color:#4D4D4D;"></font>

<font style="color:#4D4D4D;">ESP定律的适用范围：几乎全部的压缩壳，部分加密壳。只要是在JMP到OEP后的壳，理论上我们都可以使用。但是在何时下断点避开校验，何时下断OD才能断下来，这还需要多多总结和多多积累。</font>



---

将加壳后的程序载入到OD中后，点击否

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585616350171-e2180134-45c5-4a84-9b05-b20320554e7e.png)

OD界面如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585616419334-6a908a0b-0e47-4848-9914-3be606ccff8f.png)

按下F8开始单步执行

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585616519579-9feacf79-bf24-45e6-ae6e-bab14207384c.png)

当有且只有ESP和EIP为红色时，我们可以用ESP定律了（也可以直接在下面的Command窗口中输入dd 0019FF54后回车）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585616666855-96d19ea8-8b5b-40bf-be12-b7f6b47fdff2.png)

此时有：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585616722361-34c75e91-36ef-490d-8620-6d7abe464a8f.png)

下硬件断点：（这个操作也可以在command窗口输入 HR 0019FF54回车后完成，然后我们按F9运行程序，此时程序会暂停在我们设置的断点位置）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585616791219-98b6f983-f87a-4511-b0c2-ccb9ce4211bd.png)

这两种方法最终的效果都会在数据窗口中跟随到0012FFA4这个地址，然后我们可以右键那一段地址任意HEX设置断点→硬件访问→word型，按下F9执行，EIP停在：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585616909254-3ffc1942-5d44-4dd9-a34e-8201964ce27a.png)

然后我们F8单步走，到了jnz位置后不要再按F8了（这是向上跳转的），我们用鼠标点击她的下一行然后按F4，让程序转到跳转下面继续运行（sub esp,-0x80），到达jmp后我们必须跳过去，因为接下来就有可能是程序的OEP领空。

> OEP：程序的入口点，软件加壳就是隐藏了OEP（或者用了假的OEP）
>

这里就是易语言/VC程序的OEP：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585617388007-a4b578e7-d56c-4ad5-92e5-b8ac313a1d06.png)

然后我们就可以脱壳了，脱壳前我们先把断点清理掉，以免出错【调试→硬件断点→删除】

此时程序真正的OEP为：0040438E

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585617443964-b8a50dc5-c042-4f16-8640-fdcd58f45c26.png)

打开吾爱破解工具包的![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585617665211-72ec7adb-d5b1-485a-bce8-71bae0137e8b.png)

运行相同的进程：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585617827236-e1786b02-a945-4c90-8525-0175c80aefe8.png)

在“Scylla”中“附加活动进程”：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585617940997-5112c552-bb6f-4eaf-b0e1-5e882b1494aa.png)

在IAT信息框中的OEP更改为真正的OEP：0040438E，然后自动查找IAT并获取输入表（出现下图点击否）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585618106572-06e56309-81dc-4397-8580-6af369795c41.png)

最终如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585618159393-d5ca14a5-3cd3-4ec6-b4eb-e4698f699e87.png)

然后转储到文件，保存为：UPX Unpacker_dump.exe

最后修复转储后的文件，选择UPX Unpacker_dump.exe，自动保存为UPX Unpacker_dump_SCY.exe

打开UPX Unpacker_dump_SCY.exe，正常运行

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585617827236-e1786b02-a945-4c90-8525-0175c80aefe8.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585618661600-e88e4a6a-5d6e-4f38-aac6-df395d8cd9b8.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585619004238-4ea459f7-d6d9-40c2-8286-0e0e267660af.png)

**注：EP段提示UPX0是因为没有优化区段**



---



**附：**

程序校验值:

文件：	吾爱破解工具包\Tools\Unpackers\UPX Unpacker.exe（加UPX壳前）

大小：	155, 648 字节

修改时间：2015-07-19 14:43:53

MD5：	E0BD593F0D6D53755123E09E78D13E59

SHA1：	D9E75DAD01D31A2A875E05254012F56CDC61AFC5

CRC32：E3BE1942



文件：	C:\Users\Windows 10\Desktop\UPX Unpacker.exe（加UPX壳后）

大小：	52, 224 字节

修改时间：2015-07-19 14:43:53

MD5：	69B3722D1049AC1DA7B8322BD90851E6

SHA1：	E81F81D953692E6231F49FB83FA50C89F36D28A9

CRC32：EACCC927



文件：	C:\Users\Windows 10\Desktop\UPX Unpacker_dump.exe

大小：	171, 008 字节

修改时间：2020-03-31 09:29:57

MD5：	3C7E50FAB84915D800CE6F2E5A68D3F4

SHA1：	A1BF30DA1C45376E108CE63DC1F2A98F9851A1A9

CRC32：3BE1A9B1



文件：	C:\Users\Windows 10\Desktop\UPX Unpacker_dump_SCY.exe

大小：	172, 544 字节

修改时间：2020-03-31 09:31:10

MD5：	ED22315E459B1AA806FB1C7C920DB74B

SHA1：	4DE20DB95EB6C17D6F464D5729C8F829218DAABC

CRC32：5FC14E9A



**部分语言OEP：**

> **<font style="color:#F5222D;">delphi:</font>**
>
>  55            PUSH EBP
>
>  8BEC          MOV EBP,ESP
>
>  83C4 F0       ADD ESP,-10
>
>  B8 A86F4B00   MOV EAX,PE.004B6FA8
>
> **<font style="color:#F5222D;">vc++</font>**
>
>   55            PUSH EBP
>
>   8BEC          MOV EBP,ESP
>
>   83EC 44       SUB ESP,44
>
>   56            PUSH ESI
>

> **<font style="color:#F5222D;">vc6.0</font>**
>

>  55                 push ebp
>

>  8BEC               mov ebp,esp
>

>  6A FF              push -1
>

> vc7.0
>

>  6A 70              push 70
>

>  68 50110001        push hh.01001150
>

>  E8 1D020000        call hh.010017B0
>

>  33DB               xor ebx,ebx
>

> **<font style="color:#F5222D;">vb:</font>**
>

> 00401166  - FF25 6C104000   JMP DWORD PTR DS:[<&MSVBVM60.#100>]      ; MSVBVM60.ThunRTMain
>

> 0040116C >  68 147C4000     PUSH PACKME.00407C14
>

> 00401171    E8 F0FFFFFF     CALL <JMP.&MSVBVM60.#100>
>

> 00401176    0000            ADD BYTE PTR DS:[EAX],AL
>

> 00401178    0000            ADD BYTE PTR DS:[EAX],AL
>

> 0040117A    0000            ADD BYTE PTR DS:[EAX],AL
>

> 0040117C    3000            XOR BYTE PTR DS:[EAX],AL
>

> **<font style="color:#F5222D;">bc++</font>**
>

> 0040163C > $ /EB 10         JMP SHORT BCLOCK.0040164E
>

> 0040163E     |66            DB 66                                    ;  CHAR 'f'
>

> 0040163F     |62            DB 62                                    ;  CHAR 'b'
>

> 00401640     |3A            DB 3A                                    ;  CHAR ':'
>

> 00401641     |43            DB 43                                    ;  CHAR 'C'
>

> 00401642     |2B            DB 2B                                    ;  CHAR '+'
>

> 00401643     |2B            DB 2B                                    ;  CHAR '+'
>

> 00401644     |48            DB 48                                    ;  CHAR 'H'
>

> 00401645     |4F            DB 4F                                    ;  CHAR 'O'
>

> 00401646     |4F            DB 4F                                    ;  CHAR 'O'
>

> 00401647     |4B            DB 4B                                    ;  CHAR 'K'
>

> 00401648     |90            NOP
>

> 00401649     |E9            DB E9
>

> 0040164A   . |98E04E00      DD OFFSET BCLOCK.___CPPdebugHook
>

> 0040164E   > \A1 8BE04E00   MOV EAX,DWORD PTR DS:[4EE08B]
>

> 00401653   .  C1E0 02       SHL EAX,2
>

> 00401656   .  A3 8FE04E00   MOV DWORD PTR DS:[4EE08F],EAX
>

> 0040165B   .  52            PUSH EDX
>

> 0040165C   .  6A 00         PUSH 0                                   ; /pModule = NULL
>

> 0040165E   .  E8 DFBC0E00   CALL <JMP.&KERNEL32.GetModuleHandleA>    ; \GetModuleHandleA
>

> 00401663   .  8BD0          MOV EDX,EAX
>

> **<font style="color:#F5222D;">dasm:</font>**
>

> 00401000 >/$  6A 00         PUSH 0                                   ; /pModule = NULL
>

> 00401002  |.  E8 C50A0000   CALL <JMP.&KERNEL32.GetModuleHandleA>    ; \GetModuleHandleA
>

> 00401007  |.  A3 0C354000   MOV DWORD PTR DS:[40350C],EAX
>

> 0040100C  |.  E8 B50A0000   CALL <JMP.&KERNEL32.GetCommandLineA>     ; [GetCommandLineA
>

> 00401011  |.  A3 10354000   MOV DWORD PTR DS:[403510],EAX
>

> 00401016  |.  6A 0A         PUSH 0A                                  ; /Arg4 = 0000000A
>

> 00401018  |.  FF35 10354000 PUSH DWORD PTR DS:[403510]               ; |Arg3 = 00000000
>

> 0040101E  |.  6A 00         PUSH 0                                   ; |Arg2 = 00000000
>

> 00401020  |.  FF35 0C354000 PUSH DWORD PTR DS:[40350C]               ; |Arg1 = 00000000
>

本节出现的名词解释

> EP段：EntryPoint,入口点
>

> OD：
>

> HR 访问时进行硬件中断
>

> DD 转存在堆栈格式
>

> EIP：寄存器的一种，EIP寄存器里存储的是CPU下次要执行的指令的地址
>

> ESP：寄存器的一种，寄存器里存储的是是栈的栈底指针，通常叫栈基址
>

