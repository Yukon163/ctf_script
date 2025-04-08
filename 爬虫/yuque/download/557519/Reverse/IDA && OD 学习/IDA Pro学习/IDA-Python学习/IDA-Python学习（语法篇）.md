> 文章改动自：[https://www.52pojie.cn/thread-1117330-1-1.html](https://www.52pojie.cn/thread-1117330-1-1.html)
>
> 参考资料：[https://wizardforcel.gitbooks.io/grey-hat-python/41.html](https://wizardforcel.gitbooks.io/grey-hat-python/41.html)
>
> 链接：[https://pan.baidu.com/s/1U7CPET4jgn_ByoM1mllREg](https://pan.baidu.com/s/1U7CPET4jgn_ByoM1mllREg)
>
> 提取码：qu5p
>

IDA-python是一种在IDA交互式反编译器中所运行的脚本，它可以对IDA所呈现的数据和汇编指令进行操作，并且简化我们逆向分析的流程，加快我们的分析进度、IDA-python本质上是基于python语言，它相比python多了一些函数库，这些函数库能帮助我们对IDA显示出来的内容进行操作，接下来简单的介绍一下IDA-python的语法。

在这里我们编写了一个简单的demo方便演示，源码如下：

```c
#include<iostream>
#include<Windows.h>
using namespace std;

void correct(){
  cout<<"correct!";
}
void wrong(){
  cout<<"wrong!";
}
int main(){
    char name[10] = "";
    cout<<"plz input your name:"<<endl;
    cin>>name;
    if (!strcmp(name, "Cyberangel")){
        correct();
    }
    else{
        wrong();
    }
    system("pause");
    return 0;
}
```

将编译好的可执行文件拖入IDA中，接下来我们开始讲解语法。

# 脚本运行
IDA-python的脚本运行分为两种方式，一种是导入已经写好的脚本文件，另一种是在IDA中编写脚本命令：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593397261456-a5bf64d1-dbc7-4d17-b42d-29e1007d8dfb.png)

脚本文件：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593397420959-fff3df91-ffa6-427c-8700-477f88b4bef4.png)

脚本命令：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593397447129-4a80de13-3e4a-498b-b7b2-10ddcc29997f.png)

注意，这里有IDC（C语言）、IDA-python（python）脚本之分，选择python即可。

# 地址获取
<font style="color:#444444;">列举几个常用的显示反汇编窗口中特殊地址的函数，</font>**<font style="color:#F5222D;">在输出地址时，为了更形象得显示地址，常常使用hex()函数来把地址的返回值转成十六进制形式，</font>**<font style="color:#444444;">获取的地址可以为汇编代码遍历提供了开始地址。</font>

> 在 IDA 中二进制文件被分成了不同的段，这些段根据功能分成了不同的类型（ CODE, DATA, BSS, STACK, CONST,XTRN）。
>

```python
def hex(str) #把字符串转换成十六进制
def MinEA() #获取反汇编窗口中代码段的最小地址
def MaxEA() #获取反汇编窗口中代码段的最大地址
def ScreenEA() #获取光标所在位置
def SegEnd(str) #获取程序中某段的结束地址
```

示例1：

```python
print hex(MinEA()) #打印16进制形式的代码段最小地址
print hex(MaxEA()) #打印16进制形式的代码段最大地址
print hex(ScreenEA()) #获取光标所在位置
for seg in Segments():  
    #如果为代码段，则调用SegEnd(seg)
    if SegName(seg) == '.text':
        print hex(SegEnd(seg))
```

> 留意一下这里的Segment()和SegName()就好
>
> 顺便再补充几个：
>
> `FirstSeg()：`访问程序中的第一个段。
>
> `NextSeg():`<font style="background-color:transparent;">访问下一个段，如果没有就返回 BADADDR。</font>
>
> `SegByName( string SegmentName ):`<font style="background-color:transparent;">通过段名字返回段基址，举个例子，如果调用.text 作为参数，就会返回程序中代码段的开始位置。</font>
>
> `SegStart( long Address ):`<font style="background-color:transparent;">通过段内的某个地址，获得段头的地址。</font>
>

> `SegName( long Address ):`<font style="background-color:transparent;">通过段内的某个地址，获得段名。</font>
>

> `Segments():`<font style="background-color:transparent;">返回目标程序中的所有段的开始地址。</font>
>

打印结果：

```python
0x401000L
0x40b000L
0x401594L
0x403000L
```

# 数值获取
<font style="color:#444444;">在使用idapython脚本时，经常需要获取反汇编窗口中某些地址处的数值，这些数值是以十六进制的形式存在的，得到这些数值后就可以查找某些字符串或者指令或者数据的十六进制形式(长整型)，获取数值的值常用的有4个，它们传入的参数都为地址，返回的是数值(字符串形式)</font>

```python
def Byte(addr) #以字节为单位获取地址处的值
def Word(addr) #以字为单位获取地址处的值
def Dword(addr) #以双字为单位获取地址处的值
def Qword(addr) #以四字为单位获取地址处的值
def isLoaded(addr) #判断地址处的数值是否有效
```

示例2：

```python
print isLoaded(0x404026)
print Byte(0x404026)
print Word(0x404026)
print Dword(0x404026)
print Qword(0x404026)
```

```python
True
67
31043
1700952387
7453001577299867971
```

> **<font style="color:#F5222D;">打印形式以十进制输出</font>**
>

# 操作码获取
使用IDA-python脚本获取地址处的操作数及操作码，可以帮助我们对某些给定的指令加以注释，或者根据操作数来判断程序的关键操作并可以给出显眼的注释。

```python
def GetDisasm(addr) #输出某地址处的反汇编字符串(包括注释)
def GetOpnd(addr，n) #获取某地址处的操作数(第一个参数是地址，第二个是操作数索引)
def GetFlags(addr) # 获取与地址对应的整数
def GetMnem(addr) #输出某地址处的指令
def GetOpType(addr,n) #输出指定操作数的类型
def GetOperandValue(addr,n) #输出跟指定操作数相关的数据值
```

示例3：

```python
print GetDisasm(0x4015A1) 
print GetOpnd(0x4015A1,1) 
print hex(GetFlags(0x4015A1)) 
print GetMnem(0x4015A1) 
print GetOpType(0x4015A1,1) 
print GetOperandValue(0x4015A1,1)
```

输出结果：

```python
mov     qword ptr [rbp+Str1], 0
0
0x40b10748
mov
5
0
```

# 搜索操作
IDA-python脚本跟其它的脚本一样具有搜索功能，它可以在指定的地址处进行搜索，搜索的方向可以是上，也可以是下，搜索的方向是由flag来确定的。搜索功能可以帮助我们找到特定的字符串或者指令，搜索失败时返回-1.

```python
def FindBinary(ea,flag,str) #对某字符串进行搜索，找到后返回字符串地址
def FindCode(ea,flag)  #从当前地址查找第一个指令并返回指令地址
def FindData(addr,flag) #从当前地址查找第一个数据项并返回数据地址
 
flag取值有：
SEARCH_DOWN 向下搜索
SEARCH_UP 向上搜索
SEARCH_NEXT 获取下一个找到的对象。
SEARCH_CASE 指定大小写敏感
SEARCH_UNICODE 搜索 Unicode 字符串。
```

```python
print hex(FindBinary(MinEA(),SEARCH_DOWN,'Cyberangel'))
print hex(FindCode(MinEA(),SEARCH_DOWN))  
print hex(FindData(MinEA(),SEARCH_DOWN))
```

> def MinEA() #获取反汇编窗口中代码段的最小地址
>

```python
0x404026L
0x401010L
0x401dbcL
```

# 数据判断操作
我们获取指令或者操作码，有时需要判断获取的值是否符合相应的数据类型，如果符合则进一步进行操作，否则进行下一步操作。**<font style="color:#F5222D;">以下函数的返回值类型为bool型，传入的参数类型为字符串类型。</font>**

```python
def isCode(f)#判断是否为代码
def isData(f) #判断是否为数据
def isTail(f) #判断标记地址是否为尾部
def isUnknown(f) #判断标记地址是否为未知
def isHead(f) #判断标记地址是否为头部
```

```python
print isCode(GetFlags(0x401114))
print isData(GetFlags(0x401114)) 
print isTail(0x401134) 
print isUnknown(0x401214) 
print isHead(0x401114)
```

> def GetFlags(addr) # 获取与地址对应的整数
>

输出：

```python
True
False
False
False
False
```

# 修改操作部分
该部分函数为修改IDA数据库中数值的函数，数值的修改之后，当再次打开IDA（之前保存了数据库），数据不会复原，数据的修改函数以修改单位进行区分，以下为数据的修改函数。这些函数可以帮助我们修改获取去除某些指令或者字符串。

```python
def PatchByte(addr,val) #以字节为单位修改
def PatchWord(addr,val) #以字为单位修改
def PatchDword(addr,val) ##以双字为单位修改
```

```python
PatchByte(0x4015E8,0x12)
PatchWord(0x4015EF,0x12456978)
PatchDword(0x4015F2,0x00000000)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593400919090-168914c2-4073-421b-9eb2-793a29216a29.png)

# 交互部分
当运行脚本时，需要跟用户进行交互，让用户来选择接下来要进行的内容，这些交互可以让用户做选择，输入字符串或者跳转到想要查看的地址等，这些函数使得操作更人性化，甚至这些交互函数也可以作为程序的调式工具，输出中间结果等。

```python
def AskYN(n,str) #弹出对话框，让用户来选择是或者否
def Jump(addr) #跳转到相应的地址
def AskStr(str,str) #显示一个输入框，让用户输入字符串
def Message(str) #在输出出口输出一句字符串
```

```python
AskYN(1,'is it?')
Jump(0x404026)
AskStr('hello!','please enter!')
Message('hello!')
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593401220216-4c51a80e-b96b-49f9-9a46-9dddeea7e1fa.png)   ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593401220641-c6bb40a3-9869-4a72-af74-253ae6f3ef4e.png)

# 函数操作部分
在代码段中，含有很多的函数，通过跟函数操作相关的函数可以获取代码段中的所有函数、函数中的参数、函数名及函数中调用了哪些函数。这些函数可以帮助我们分析重要的函数，从而加快对程序的分析。

```python
def Functions(start,end)#获取某地址区间所有函数
def GetFunctionName(addr)#获取函数名字
def NextFunction(addr) #获取下一个函数地址
def XrefsTo(Addr, flags)#获取调用某地址处函数的函数
```

```python
for seg in Segments():  
    #如果为代码段
    if SegName(seg) == '.text':
        for function_ea in Functions(seg,SegEnd(seg)):
            FunctionName=GetFunctionName(function_ea)
            print FunctionName
            nextFunc=NextFunction(function_ea)
            print nextFunc
```

```python
__mingw_invalidParameterHandler
4198416
pre_c_init
4198704
pre_cpp_init
4198784
__tmainCRTStartup
4199600
WinMainCRTStartup
4199648
mainCRTStartup
4199696
atexit
4199728
__gcc_register_frame
4199744
__gcc_deregister_frame
4199760
_Z7correctv
4199794
_Z5wrongv
4199828
main
4199966
__tcf_0
4199993
_Z41__static_initialization_and_destruction_0ii
4200053
_GLOBAL__sub_I__Z7correctv
4200096
_ZStrsIcSt11char_traitsIcEERSt13basic_istreamIT_T0_ES6_PS3_
4200104
_ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
4200112
_ZSt4endlIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_
4200120
_ZNSt8ios_base4InitD1Ev
4200128
_ZNSt8ios_base4InitC1Ev
4200136
_ZNSolsEPFRSoS_E
4200144
__do_global_dtors
4200208
__do_global_ctors
4200320
__main
4200352
my_lconv_init
4200368
_setargv
4200384
__security_init_cookie
4200608
__report_gsfailure
4200864
__dyn_tls_dtor
4200912
__dyn_tls_init
4201040
__tlregdtor
4201056
__mingw_raise_matherr
4201136
__mingw_setusermatherr
4201152
_matherr
4201408
fpreset
4201424
_decode_pointer
4201440
_encode_pointer
4201456
__write_memory.part.0
4201920
_pei386_runtime_relocator
4202624
__mingw_SEH_error_handler
4203040
__mingw_init_ehandler
4203776
__mingwthr_run_key_dtors.part.0
4203888
___w64_mingwthr_add_key_dtor
4204016
___w64_mingwthr_remove_key_dtor
4204176
__mingw_TLScallback
4204400
_ValidateImageBase.part.0
4204432
_ValidateImageBase
4204464
_FindPESection
4204544
_FindPESectionByName
4204688
__mingw_GetSectionForAddress
4204816
__mingw_GetSectionCount
4204880
_FindPESectionExec
4204992
_GetPEImageBase
4205056
_IsNonwritableInCurrentImage
4205216
__mingw_enum_import_library_names
4205392
___chkstk_ms
4205456
vfprintf
4205464
system
4205472
strncmp
4205480
strlen
4205488
strcmp
4205496
signal
4205504
memcpy
4205512
malloc
4205520
fwrite
4205528
free
4205536
fprintf
4205544
exit
4205552
calloc
4205560
abort
4205568
_onexit
4205576
_initterm
4205584
_cexit
4205592
_amsg_exit
4205600
__setusermatherr
4205608
__set_app_type
4205616
__lconv_init
4205624
__getmainargs
4205632
__C_specific_handler
4205648
__acrt_iob_func
4205680
_get_invalid_parameter_handler
4205696
_set_invalid_parameter_handler
4205712
__p__acmdln
4205728
__p__fmode
4205744
__iob_func
4205760
VirtualQuery
4205768
VirtualProtect
4205776
UnhandledExceptionFilter
4205784
TlsGetValue
4205792
TerminateProcess
4205800
Sleep
4205808
SetUnhandledExceptionFilter
4205816
RtlVirtualUnwind
4205824
RtlLookupFunctionEntry
4205832
RtlCaptureContext
4205840
RtlAddFunctionTable
4205848
QueryPerformanceCounter
4205856
LeaveCriticalSection
4205864
InitializeCriticalSection
4205872
GetTickCount
4205880
GetSystemTimeAsFileTime
4205888
GetStartupInfoA
4205896
GetLastError
4205904
GetCurrentThreadId
4205912
GetCurrentProcessId
4205920
GetCurrentProcess
4205928
EnterCriticalSection
4205936
DeleteCriticalSection
4205952
.text_52
4206064
register_frame_ctor
18446744073709551615
```

> 再补充几个：
>

> `Chunks( long FunctionAddress )`
>

> 返回一个列表，包含了函数片段。每个列表项都是一个元组（chunk start, chunk end）
>

> `LocByName( string FunctionName )：`<font style="background-color:transparent;">通过函数名返回函数的地址。</font>
>

> `GetFuncOffset( long Address )：`<font style="background-color:transparent;">通过任意一个地址，然后得到这个地址所属的函数名，以及给定地址和函数的相对位移。 然后把这些信息组成字符串以"名字+位移"的形式返回。</font>
>

# 交叉引用
找出代码和数据的交叉引用，在分析文件的执行流程时很重要，尤其是当我们分析感兴趣的代码块的时候，盲目的查找无意义字符会让你有一种想死的冲动，这也是为什么 IDA 依然会成为逆向工程的王者的原因。IDAPython 提供了一大堆函数用于各种交叉引用。最常用的就是下面几种。

```python
CodeRefsTo( long Address, bool Flow )
#返回一个列表，告诉我们 Address 处代码被什么地方引用了，Flow 告诉 IDAPython 是否要 跟踪这些代码。
CodeRefsFrom( long Address, bool Flow )
#返回一个列表，告诉我们 Address 地址上的代码引用何处的代码。
DataRefsTo( long Address )
#返回一个列表，告诉我们 Address 处数据被什么地方引用了。常用于跟踪全局变量。
#DataRefsFrom( long Address )
返回一个列表，告诉我们 Address 地址上的代码引用何处的数据。
```

# Debugger Hooks
Debugger Hook 是 IDAPython 提供的另一个非常酷的功能，用于 Hook 住 IDA 内部的调试器，同时处理各种调试事件。虽然 IDA 一般不用于调试任务，但是当需要动态调试的时候，调用 IDA 内部调试器还是比外部的会方便很多。之后我们会用 debugger hooks 创建一 个代码覆盖率统计工具。使用 debugger hook 之前，先要创建一个hook 类然后在类里头定义各种不同的处理函数。

```python
class DbgHook(DBG_Hooks):
    # Event handler for when the process starts
    def dbg_process_start(self, pid, tid, ea, name, base, size) 
        return
    # Event handler for process exit
    def dbg_process_exit(self, pid, tid, ea, code): 
        return
    # Event handler for when a shared library gets loaded def 
    dbg_library_load(self, pid, tid, ea, name, base, size):
        return
    # Breakpoint handler
    def dbg_bpt(self, tid, ea): 
        return
```

这个类包含了我们在创建调试脚本时，会经常用到的几个调试事件处理函数。安装 hook 的方式如下:

```python
debugger = DbgHook() 
debugger.hook()
```

现在运行调试器，hook 会捕捉所有的调试事件，这样就能非常精确的控制 IDA 调试器。 下面的函数在调试的时候非常有用:

```python
AddBpt( long Address )#在指定的地点设置软件断点。
GetBptQty()#返回当前设置的断点数量。
GetRegValue( string Register )#通过寄存器名获得寄存器值。
SetRegValue( long Value, string Register )#设定寄存器的值。
```

# 其他
```python
GetInputFileMD5()
#返回 IDA 加载的二进制文件的 MD5 值，通过这个值能够判断一个文件的不同版本是否有改变。
```

