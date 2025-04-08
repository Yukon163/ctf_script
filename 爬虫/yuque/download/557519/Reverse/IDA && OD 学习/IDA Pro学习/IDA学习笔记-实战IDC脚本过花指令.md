> 参考资料：[https://blog.csdn.net/hgy413/article/details/50594320](https://blog.csdn.net/hgy413/article/details/50594320)
>
> [https://blog.csdn.net/weixin_44352049/article/details/85850733](https://blog.csdn.net/weixin_44352049/article/details/85850733)
>

参考示例下载地址：

> 链接：[https://pan.baidu.com/s/1U3-9o6exuuo3OqrdKCK-hQ](https://pan.baidu.com/s/1U3-9o6exuuo3OqrdKCK-hQ)
>
> 提取码：ac5j
>

将软件下载之后，首先查壳：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588559916120-6bd18db7-c3c3-4351-ab71-dc78d873800e.png)

在图中我们可以看到这个示例有MSLRH壳和UPX两种壳（其实示例本身就是MSLRH加壳工具）。不脱壳，我们将其载入到IDA中，在IDA中可以看出：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588560159589-a55f157b-43c4-4ce8-9928-cbbf7f3cb9d7.png)

有很多未知部分（黑色），数据部分（灰色），而且没有常规函数和库函数，可以印证这一定是加壳了。

将示例载入到OD中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588560397200-179cf241-6e80-4385-bfac-9fb8061f0262.png)

上来就是一个pushad，加壳了，没毛病。将界面向下滑动，可以发现有很多花指令（灰色指令），如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588561038074-15963bc9-d80f-4069-a3ae-6b271d5ceabb.png)

> 可以利用ESP脱壳定律进行脱壳
>

现在就可以关掉OD了，因为我们学习的是IDA。

载入IDA之后，我们来到start函数，在图表视图中我们可以看到pusha（IDA写法，OD中为pushad）指令：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588561354403-78c0baab-afbb-4037-b275-7b5b3ffef377.png)

首先调整IDA，让其将地址和机器指令显示出来：菜单栏->选项->常规，设置如下图，单击确定。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588561476256-4a2f5d0d-8d3b-4bce-a166-954a514b048c.png)

> Q:为什么操作码字节数为6？
>
> A:习惯了OD的显示方法
>

<font style="color:#4D4D4D;">鼠标放到有效分析的最后一行（如下图）</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588561706451-a95befae-4dfb-449c-9494-cc0bb328c94f.png)

<font style="color:#4D4D4D;">按下</font>space<font style="color:#4D4D4D;">，切换到文本视图模式，来到：</font>

> 为了方便分析，请先按之前的步骤将机器指令显示出来
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588561754800-69aa81a1-025c-4d06-b4bd-e2af79792cf7.png)

<font style="color:#4D4D4D;">我们先来看上图中箭头所指向的地方：</font>

```plain
call sub_456109 //调用函数
start	endp	;sp-analysis failed //sp分析失败
```

> Q:为什么会出现sp-analysis failed？
>
> A:由于ida检测到，IDA有栈跟踪的功能，它在函数内部遇到ret(retn)指令时会做判断：栈指针的值在函数的开头/结尾是否一致，如果不一致就会在函数的结尾标注"sp-analysis failed"。一般编程中，不同的函数调用约定(如stdcall&_cdcel call)可能会出现这种情况；另外，为了实现代码保护而加入代码混淆(特指用push/push+ret实现函数调用)技术也会出现这种情况
>

上图中有<font style="color:#F5222D;">红色</font>的地方：

```plain
sub_456109↓p //此处注释意为【分析交叉引用有冲突】,一般是深红色导航带上面一条指令
```

> 后面将补充交叉引用的简介。
>

定位到seg005:004560FF的call sub_456DEF处，在IDA左侧的函数窗口中进入，如下图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588562817515-b91cb057-534a-4ab0-91f5-8bae286eeebb.png)

call的调用特点不是push ebp和mov ebp,esp吗？这里IDA被花指令干扰了，因此错误的分析成为call sub_456DEF，返回到我们刚才分析的地方：eg005:004560FF的call sub_456DEF

按下D键，将其转换为数据，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588563671744-23819ad5-030e-40a9-81a8-faa658e29d65.png)

| 机器码 | 汇编语言 |
| :---: | :---: |
| 9A | CALL immed32 |
| E8 | CALL immed16 |
| E9 | JMP immed16 |
| EB | JMP immed8 |


<font style="color:#F5222D;">因为E8机器码在汇编中会被翻译为</font>`<font style="color:#F5222D;">call</font>`<font style="color:#F5222D;">，但是后面的</font>`<font style="color:#F5222D;">EB OC 00 00</font>`<font style="color:#F5222D;">会被翻译成</font>`<font style="color:#F5222D;">call</font>`<font style="color:#F5222D;">的地址，但是这个地址并不存在，</font>**<font style="color:#F5222D;">因此会报错</font>**<font style="color:#F5222D;">。</font><font style="color:#4D4D4D;">那么就很清楚了，这里不是</font>`call`<font style="color:#4D4D4D;">而是</font>`jmp`<font style="color:#4D4D4D;">到一个地址。光标定位到下一行</font>`EB`<font style="color:#4D4D4D;">，按</font>C<font style="color:#4D4D4D;">，将数据转换为代码，如下图：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588564269212-a9b9f2aa-d65b-40a9-9c2d-0e6d48c467d2.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588564292869-167ebe05-2c52-40c1-bdc9-e088ab0483eb.png)

<font style="color:#4D4D4D;">至此，一处花搞定。那什么叫做花指令呢？就是在本来正常的顺序下，让其不停跳转，中间一些永远不会执行到的地方，加上一些其他字符，使反编译器无法正常分析（或分析错误），就达到了在一定程度上保护程序的功效。还有一处花指令，就是紧接着下面的</font>call near ptr byte_4560FF

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588564405482-c4163a01-d9de-46d1-ae5a-e6d62bc222af.png)

<font style="color:#4D4D4D;">简单分析一下，先让其变为数据，结果分析发现一整段都是花：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588564889735-2478e071-9311-4bd8-b81a-b2fee44bc0c4.png)

<font style="color:#4D4D4D;">一堆花加在一起，是为花指令。这个例子中，有以下几种情形(分析出来类型，方便接下来用脚本去除所有的花指令)</font>

<font style="color:#4D4D4D;">示例一：</font>

```plain
	call label1
	db 0E8h
label2:
	jmp label3
	db 0
	db 0
	db 0E8h
	db 0F6h
	db 0FFh
	db OFFh
	db OFFh
label1: 
	:call label2
label3:
	add esp,8
```

<font style="color:#4D4D4D;">示例二：</font>

```plain
	jz label1
	jnz label1
	db 0EBh
	db2
label1:
	jmp label2
	db 81h
label2:
```

<font style="color:#4D4D4D;">示例三：</font>

```plain
	push eax
	call label1
	db 29h
	db 5Ah
label1:
	POP eax
	imul eax,3
	call label2
	db 29h
	db5Ah
label2:
	add esp,4
	pop eax
```

<font style="color:#4D4D4D;">示例四：</font>

```plain
	jmp label1
	db 68h
label1: 
	jmp label2
	db 0CDh,20h
label2:
	jmp label3
	db 0E8h
label3:
```

去除花指令的原理：

第一步：识别哪些是有用的数据，哪些是垃圾数据。

第二步：把垃圾数据用**nop(0x90h)**填充。

接下来我们模仿前面的步骤将花指令一一去除

第一处修改（之前详细介绍的内容）：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588565544860-9dd79b4e-aced-4563-bf57-5be4fb4ef26f.png)

第二处修改（第一处修改的地方略微向下滑动）：

修改之前：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588565697252-f57ee9eb-1dbf-45c8-96a3-80c2f3913c5a.png)

修改之后：（直接按下D就完成了修改）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588565779207-5819d142-8c69-4c2b-9b78-42ed9afaefe3.png)

第三处修改（第二处修改的地方略微向下滑动）：

修改之前：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588565949232-57ca2c1b-a90c-4fe7-bc83-00cf216303b8.png)

修改之后：（和第一处修改步骤相同）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588566011694-d7659c87-511f-4452-a987-80e5acaf3b40.png)

接下来我们看看第一二三处可以nop掉的地方：

第一处：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588564889735-2478e071-9311-4bd8-b81a-b2fee44bc0c4.png)

由上面的图可以知道可以nop掉的区域为：（灰色部分）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588568628789-8ad44653-b218-45ce-bd72-bafdb941bd96.png)

按下D转变为数据：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588568706537-abc6f38e-d479-47a2-9c26-f29cce7959fa.png)

对中间的jmp语句按D得到：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588568922933-d7c98f45-0be6-4055-8d84-adf12701da34.png)

灰色部分为花,同理,可以nop掉下列两处的语句

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588569238565-fbc77987-1e94-4209-b5a7-344112587280.png)

---

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588569238589-dd585e89-72cc-44a5-ad00-c6a6f875b819.png)

> 注：红色是标签，蓝色箭头是跳转流程，绿色是有用的代码
>

<font style="color:#4D4D4D;">按下D，依然整理一下：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588569320199-95845302-206f-4a4a-9a8a-34082e6e637f.png)

---

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588569320211-896dcd32-ae25-4a64-8eb0-b18afd5c2c18.png)

代码整理如下：

```plain
==================1=======================
E8                byte_4560FA     db 0E8h
0A                                db  0Ah
00                                db    0
00                                db    0
00                                db    0
E8                                db 0E8h
EB                byte_456100     db 0EBh
0C                                db  0Ch
00                                db    0
00                                db    0
E8                                db 0E8h
F6                                db 0F6h
FF                                db 0FFh
FF                                db 0FFh
FF                                db 0FFh
```

```plain
==================2=======================
74                                db 74h
04                                db    4
75                                db 75h
02                                db    2
EB                                db 0EBh
02                                db    2
EB                                db 0EBh
01                                db    1
81                                db 81h
50                byte_45613A     db 50h
E8                                db 0E8h
02                                db    2
00                                db    0
00                                db    0
00                                db    0
29                                db 29h
5A                                db 5Ah
58                                db 58h
6B                                db 6Bh
C0                                db 0C0h
03                                db    3
E8                                db 0E8h
02                                db    2
00                                db    0
00                                db    0
00                                db    0
29                                db 29h
5A                                db 5Ah
83                                db 83h
C4                                db 0C4h
04                                db    4
```

```plain
==================3=======================
EB                                db 0EBh
01                                db    1
68                                db 68h
EB                                db 0EBh
02                                db    2
CD                byte_4561A6     db 0CDh
20                                db  20h
EB                                db 0EBh
01                                db    1
E8                                db 0E8h

EB                                db 0EBh
01                                db    1
68                                db 68h
EB                                db 0EBh
02                                db    2
CD                byte_4561A6     db 20CDh
EB                                db 0EBh
01                                db    1
E8                                db 0E8h
```

接下来我们介绍IDC：

IDC的语言与C语言其实差不多，但还是有一定的出入，其文件扩展名为.idc。

当然，为了使用脚本更加的简单，并不需要将所有的花去除，接下来介绍几个关键点：

**FindBinary****（搜索数组）**：从一个给定的地址搜索一个指定的数据项

例如：eg=FindBinary(MinEA(),SEARCH_DOMN I SEARCH_CASE,"FF E4");

> 注：下文中的传入参数0X03一般都是写的这个（教程上是这么说的）
>

**MinEA**：给定的地址

**PatchByte()、PatchWord()、PatchDword()**：打补丁

去花的脚本如下：

```c
#include <idc.idc>
static main() 
{
	PatchJunkCode();//调用函数
}
static PatchJunkCode() 
{
    auto x,FBin,ProcRange;
	FBin = "E8 0A 00 00 00 E8 EB 0C 00 00 E8 F6 FF FF FF";
// 目 标 = "E8 0A 00 00 00 90 EB 0C 90 90 90 90 90 90 90";
	//花指令1的特征码
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		x = x + 5; //返回的x是第一个E8的地址，
		      //加上5是第二个E8的地址
		PatchByte (x,0x90);//nop掉
		x = x + 3; //00
		PatchByte (x,0x90);
		x++;  //00 E8
		PatchWord (x,0x9090);
		x =x + 2 ; //F6 FF FF FF
		PatchDword (x,0x90909090);
	}
//以下同理，就不再进行分析了
	FBin = "74 04 75 02 EB 02 EB 01 81";
// 目 标 = "74 04 75 02 90 90 EB 01 90";
	// 花指令2的特征码
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		x = x + 4; //EB 02
		PatchWord (x,0x9090);
		x = x + 4; //81
		PatchByte (x,0x90);
	}

	FBin = "50 E8 02 00 00 00 29 5A 58 6B C0 03 E8 02 00 00 00 29 5A 83 C4 04";
// 目 标 = "50 E8 02 00 00 00 90 90 58 6B C0 03 E8 02 00 00 00 90 90 83 C4 04";
	// 花指令3的特征码
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		x = x + 6;//29 5A
		PatchWord (x,0x9090);
		x = x + 11; //29 5A
		PatchWord (x,0x9090);
	}
	// 花指令4的特征码
	FBin = "EB 01 68 EB 02 CD 20 EB 01 E8";
// 目 标 = "EB 01 90 EB 02 90 90 EB 01 90";
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		x = x+2; //68
		PatchByte (x,0x90);
		x = x+3;  //CD 20
		PatchWord (x,0x9090);
		x = x+4;  //E8
		PatchByte (x,0x90);
	}
}
```

效果如下：

<font style="color:#4D4D4D;">去花之前：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588580989994-4f679188-38ac-4386-936b-518213520609.png)

<font style="color:#4D4D4D;">去花之后</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588580998404-3bbd228d-4fa8-47eb-b16f-5de9081c63c2.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588581010136-4839ba46-f5b9-4001-927f-3272bcda6dab.png)

但是存在这一些问题：

1. 有些显示是90，有些显示是nop，不美观
2. nop太多，不便于分析nop太多，不便于分析

改进：

1. 使用MakeUnknown把刚才修改的地方隐藏
2. 调用IDA的内置函数AnalyzeArea，从最小地址到最大地址重新分析

结果如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1588581165051-5c0f8333-8aa6-4c23-aff6-555bb2513b4a.png)

注：在不同的程序中，花的类型不一定相同，这也是OD去花插件的弊端，因为花随时可以更新，但是插件不一定能及时更新，因此使用还需要参考哲学思想：

> 具体问题具体分析
>

最终成品代码如下：

```c
#include <idc.idc>
static main() 
{
	auto x,FBin,ProcRange;

	HideJunkCode();

	PatchJunkCode();

	AnalyzeArea (MinEA(),MaxEA());
}


static PatchJunkCode() 
{
    auto x,FBin,ProcRange;

	FBin = "E8 0A 00 00 00 E8 EB 0C 00 00 E8 F6 FF FF FF";
	//花指令1的特征码
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		x=x+5; //E8
		PatchByte (x,0x90);
		x = x + 3; //00
		PatchByte (x,0x90);
		x++;  //00 E8
		PatchWord (x,0x9090);
		x =x +2 ; //F6 FF FF FF
		PatchDword (x,0x90909090);
	}

	FBin = "74 04 75 02 EB 02 EB 01 81";
	// 花指令2的特征码
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		x = x + 4; //EB 02
		PatchWord (x,0x9090);
		x = x + 4; //81
		PatchByte (x,0x90);
	}

	FBin = "50 E8 02 00 00 00 29 5A 58 6B C0 03 E8 02 00 00 00 29 5A 83 C4 04";
	// 花指令3的特征码
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		x = x + 6;//29 5A
		PatchWord (x,0x9090);
		x = x + 11; //29 5A
		PatchWord (x,0x9090);
	}

	FBin = "EB 01 68 EB 02 CD 20 EB 01 E8";
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		x = x+2; //68
		PatchByte (x,0x90);
		x = x+3;  //CD 20
		PatchWord (x,0x9090);
		x = x+4;  //E8
		PatchByte (x,0x90);
	}
}


static HideJunkCode()
{
	auto x,y,FBin;

	FBin = "E8 0A 00 00 00 E8 EB 0C 00 00 E8 F6 FF FF FF";
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		MakeUnknown (x,0x17,1);
		//x起始地址,y结束地址
		y = x + 0x17;
		HideArea (x,y,atoa(x),atoa(x),atoa(y),-1);
	}

	FBin = "74 04 75 02 EB 02 EB 01 81";
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		MakeUnknown (x,0x09,1);
		//x起始地址,y结束地址
		y = x + 0x09;
		HideArea (x,y,atoa(x),atoa(x),atoa(y),-1);
	}

	FBin = "50 E8 02 00 00 00 29 5A 58 6B C0 03 E8 02 00 00 00 29 5A 83 C4 04";
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		MakeUnknown (x,0x17,1);
		//x起始地址,y结束地址
		y = x + 0x17;
		HideArea (x,y,atoa(x),atoa(x),atoa(y),-1);
	}

	FBin = "EB 01 68 EB 02 CD 20 EB 01 E8";
	for (x = FindBinary(MinEA(),0x03,FBin);x != BADADDR;x = FindBinary(x,0x03,FBin))
	{
		MakeUnknown (x,0x09,1);
		//x起始地址,y结束地址
		y = x + 0x9;
		HideArea (x,y,atoa(x),atoa(x),atoa(y),-1);
	}

}
```

