UPack（Ultimate PE压缩器）是一款PE文件的运行时压缩器，其**特点是用一种非常独特的方式对PE头进行变形。**UPack会引起诸多现有PE分析程序错误，因此各制作者（公司）不得不重新修改、调整程序。也就是说，UPack使用了一些划时代的技术方法，详细分析UPack可以把对PE头的认识提升到一个新层次。本章将完全颠覆大家之前对PE头的了解，在学习更多知识的同时，进一步感受代码逆向分析的乐趣与激情。

# 18.1 UPack说明
UPack是一个名叫dwing的中国人编写的PE压缩器。

网址：http://wex.cn/dwing/mycomp.htm

Upack0.39Final：http://wex.cn/dwing/download/upack039.7z

UPack的制作者对PE头有深刻认识，由其对 Windows OS PE装载器的详细分析就可以推测出来。许多PE压缩器中, UPack都以对PE头的独特变形技法而闻名。初次查看 UPack压缩的文件PE头时,经常会产生“这是什么啊？这能运行吗？”等疑问,其独特的变形技术可窥一斑。

UPack刚出现时,其对PE头的独特处理使各种PE实用程序(调试器、PEⅤ lewer等)无法正常运行(经常非正常退出)这种特征使许多恶意代码制作者使用UPack压缩自己的恶意代码并发布。由于这样的恶意代码非常多,现在大部分杀毒软件干脆将所有UPack压缩的文件全部识别为恶意文件并删除(还有几个类似的在恶意代码中常用的压缩器)。

理解下面所有内容后再亲自制作PE Viewer或PE压缩器/Crypter，这样就能成为PE文件头的专家了，以后无论PE头如何变形都能轻松分析。

提示------------------------------------------------------------------------------------------------------------------

详细分析UPack前要先关闭系统中运行的杀毒软件的实时监控功能（大部分杀毒软件会将UPack识别为病毒并删除），分析完成后再打开。

-----------------------------------------------------------------------------------------------------------------------

# 18.2使用UPack 压缩notepad.exe
提示------------------------------------------------------------------------------------------------------------------

使用Windows XP SP3中的notepad.exe程序。

-----------------------------------------------------------------------------------------------------------------------

下面使用UPack 0.39 Final版本压缩notepad.exe。首先将upack.exe与notepad.exe复制到合适的文件中（参考图18-1)，然后在命令行窗口输入命令压缩文件（压缩命令带有几个参数，但这里使用默认（default）参数即可），如图18-2所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581386713946-5b442d86-39a4-4e91-a23a-91f1f2270175.png)图18-1notepad.exe&Upack.exe文件

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581386852362-8055c936-190f-43c5-81fc-b65bb4c7092a.png)

图18-2用UPack压缩notepad.exe

UPack会直接压缩源文件本身，且不会另外备份。因此，压缩重要文件前一定要先备份。

运行时压缩完成后，文件名将变为notepad_upack.exe。接下来使用PEView查看，如图18-3所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581387044395-bbedcb71-243f-4d63-ad55-0d0d5c6cf149.png)

图18-3 notepad_upack.exe

这里使用的是PEView的最新版本（0.9.8），但是仍然无法正常读取PE文件头（没有IMAGE_OPTIONAL_HEADER、IMAGE_SECTION_HEADER等的信息）。而在旧版PEView中，程序干脆会非正常终止退出。

# 18.3使用Stud_PE工具
由于最强大的PE Viewer工具PE View无法正常运行，下面再向各位介绍一款类似的PE实用工具Stud PE。

网址：http://www.cgsoftlabs.roStud_PE:http://www.cgsoftlabs.ro/zip/Stud_PE.zip最新版本为2.4.0.1，更新说明中有一条针对UPack的说明，如图18-4所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581387293329-799b534b-eed6-45ac-a9b3-33fda6ab5fbe.png)

更新说明中指出，针对Upack的RVA2RAW功能已得到修改（UPack到处制造麻烦）。图18-5是Stud_PE的运行界面。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581387413509-bb862d15-80a8-44b4-9ff6-e0630ab060c9.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581387424212-55f9cf13-4c14-407c-924e-7d3128f4a2d9.png)

图18-5 Stud_PE的运行界面。

Stud_PE的界面结构要比PEView略复杂一些，但它拥有其他工具无法比拟的众多独特优点（也能很好地显示UPack）。分析UPack文件的PE头时将对Stud PE进行更加详细的说明。

# 18.4比较PE文件头
先使用Hex Editor打开2个文件（notepad.exe、notepad_upack.exe)，再比较其PE头部分。

## 18.4.1原notepad.exe的PE文件头
图18-6是个典型的PE文件头，其中数据按照IMAGE_DOS_HEADER、DOS Stub、IMAGE_NT_ HEADERS、IMAGE_SECTION_HEADER顺序排列。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581387633276-92331042-80fc-4a2f-94db-81bf875887a8.png)

图18-6 notepad.exe的PE文件头

## 18.4.2 notepad_upack.exe 运行时压缩的PE文件头
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581387698457-33e50b62-837e-4316-9b87-d86c43483eb6.png)

图18-7 notepad_upx.exe的PE头

如图18-7所示，notepad_upx.exe的PE头看上去有些奇怪。MZ与PE签名贴得太近了，并且没有DOS存根，出现了大量字符串，中间好像还夹杂着代码。总之，整个文件不对劲的地方太多了。

下面详细分析UPack中使用的这种独特的PE文件头结构。

# 18.5分析UPack的PE文件头
## 18.5.1重叠文件头
**重叠文件头也是其他压缩器经常使用的技法，借助该方法可以把MZ文件头（IMAGE DOSHEADER）与PE文件头（IMAGE NT HEADERS)巧妙重叠在一起，并可有效节约文件头空间。**当然这会额外增加文件头的复杂性，给分析带来很大困难（很难再使用PE相关工具）。

下面使用Stud_PE看一下MZ文件头部分。请按Headers选项卡的Basic HEADERS tree view inhexeditor按钮，如图18-8所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581387962145-f1eb6f84-3412-463c-9fef-512ea8a1a397.png)

图18-8 重写文件头

MZ文件头（IMAGE_DOS_HEADER)中有以下2个重要成员。

(offset 0)e_magic：Magic number=4D5A('MZ')

(offset 3C)e_lfanew：File address of new exe header

提示------------------------------------------------------------------------------------------------------------------

还记得e_magic和e_lfanew吗？

**e_magic**：一个WORD类型，值是一个常数0x4D5A，用文本编辑器查看该值位‘MZ’，可执行文件必须都是'MZ'开头。

**e_lfanew**：为32位可执行文件扩展的域，用来表示DOS头之后的NT头相对文件起始地址的偏移（换一种说法就是指示NT头的偏移，根据不同文件拥有可变值）

所有PE文件在开始部分（e_magic）都有DOS签名（“MZ”）。e_lfanew值指向NT头所在位置（NT头的名称为IMAGE_NT_HEADERS，

-----------------------------------------------------------------------------------------------------------------------

其余成员都不怎么重要（对程序运行没有任何意义）。

问题在于，根据PE文件格式规范，IMAGE_NT_HEADERS的起始位置是“可变的”。换言之，**IMAGE_NT_HEADERS的起始位置由e_lfanew的值决定。**一般在一个正常程序中，e_lfanew拥有如下所示的值（不同的构建环境会有不同）。

e_lfanew=MZ文件头大小（40）+DOS存根大小（可变：VC++下为A0）=E0

UPack中e_lfanew的值为10，这并不违反PE规范，只是钻了规范本身的空子罢了。像这样就可以把MZ文件头与PE文件头重叠在一起。

## 18.5.2 IMAGE_FILE_HEADER.SizeOfOptionalHeader
修改IMAGE_FILE_HEADER.SizeOfOptionalHeader的值，可以向文件头插入解码代码。

SizeOfOptionallHeader表示PE文件头中紧接在IMAGE_FILE HEADER下的IMAGE OPTIONAL HEADER结构体的长度（E0）。UPack将该值更改为148，如图18-9所示（图中框选的部分）。

提示------------------------------------------------------------------------------------------------------------------

IMAGE_NT_HEADER结构体的最后一个成员为IMAGE_OPTIONAL_HEADER32**结构体**。SizeOfOptionalHeader成员用来指出IMAGE_OPTIONAL_HEADER32结构体的长度。**IMAGE_OPTIONAL_HEADER32结构体由C语言编写而成，故其大小已经确定。**但是Windows的PE装载器需要查看IMAGE_FILE_HEADER的SizeOfOptionalHeader值，从而识别出IMAGE_OPTIONAL_HEADER32结构体的大小。

-----------------------------------------------------------------------------------------------------------------------

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581388593553-314406f4-a81c-4d80-ad84-e23189d98af7.png)

图18-9 SizeOfOptionalHeader

此处会产生一个疑问。由字面意思可知，IMAGE_OPTIONAL_HEADER是结构体，PE32文件格式中其大小已经被确定为E0。

**<font style="color:#F5222D;">既然如此，PE文件格式的设计者们为何还要另外输入IMAGE_OPTIONAL</font>****<font style="color:#F5222D;">_</font>****<font style="color:#F5222D;">HEADER结构体的大小呢?</font>**原来的设计意图是，根据PE文件形态分别更换并插入其他IMAGE_OPTIONAL_HEADER形态的结构体。**简言之，由于IMAGE****_****OPTIONAL****_****HEADER的种类很多，所以需要另外输入结构体的大小**（比如：64位PE32+的IMAGE_OPTIONAL_HEADER结构体的大小为F0）。

**SizeOfOptionalHeader的另一层含义是确定节区头（IMAGE_SECTION_HEADER）的起始偏移。**

仅从PE文件头来看，紧接着IMAGE_OPTIONAL_HEADER的好像是IMAGE_SECTION_HEADER。但实际上（更准确地说），**<font style="color:#F5222D;">从IMAGE</font>****<font style="color:#F5222D;">_</font>****<font style="color:#F5222D;">OPTIONAL</font>****<font style="color:#F5222D;">_</font>****<font style="color:#F5222D;">HEADER的起始偏移加上SizeOfOptionalHeader值后的位置开始才是IMAGE</font>****<font style="color:#F5222D;">_</font>****<font style="color:#F5222D;">SECTION</font>****<font style="color:#F5222D;">_</font>****<font style="color:#F5222D;">HEADER</font>**。

**UPack把SizeOfOptionalHeader的值设置为148，比正常值（E0或F0）要更大一些。**所以IMAGE_SECTION_HEADER是从偏移170开始的（IMAGE_OPTIONAL_HEADER的起始偏移（28）+SizeOfOptionalHeader(148)=170)。

**UPack的意图是什么？为什么要改变这个值（SizeOfOptionalHeader)呢？**

UPack的基本特征就是把PE文件头变形，像扭曲的麻花（第13章提到过）一样，向文件头适当插入解码需要的代码。增大SizeOfOptionalHeader的值后，就在IMAGE_OPTIONAL_HEADER与IMAGE_SECTION_HEADER之间添加了额外空间。**UPack就向这个区域添加解码代码，这是一种超越PE文件头常规理解的巧妙方法。**

下面查看一下该区域。IMAGE_OPTIONAL_HEADER结束的位置为D7，IMAGE_ SECTION_HEADER的起始位置为170。使用Hex Editor查看中间的区域，如图18-10所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581389217546-daeb4cf1-7f86-404d-9ad3-a3410b404ac3.png)

图18-10 解码代码

使用调试器查看反汇编代码，如图18-11所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581389425192-61cb2838-8657-4289-802e-122389468ca1.png)

图18-11并不是PE文件头中的信息，而是UPack中使用的代码。若PE相关实用工具将其识别为PE文件头信息，就会引发错误，导致程序无法正常运行。

## 18.5.3 IMAGE_OPTIONAL_HEADER.NumberOfRvaAndSizes
提示------------------------------------------------------------------------------------------------------------------

**#8.NumberOfRvaAndSizes**

NumberOfRvaAndSizes 用来指定DataDirectory（IMAGE_OPTIONAL_HEADER32结构体的最后一个成员）数组的个数。虽然结构体定义中明确指出了数组个数为IMAGE_NUMBEROF_DIRECTORY_ENTRIES(16)，但是PE装载器通过查看NumberOfRvaAndSizes值来识别数组大小，换言之，数组大小也可能不是16。

-----------------------------------------------------------------------------------------------------------------------

**从IMAGE_OPTIONAL_HEADER结构体中可以看到，其NumberOfRvaAndSizes的值也发生了改变，这样做的目的也是为了向文件头插入自身代码。**

**<font style="color:#F5222D;">NumberOfRvaAndSizes值用来指出紧接在后面的IMAGE</font>****<font style="color:#F5222D;">_</font>****<font style="color:#F5222D;">DATA</font>****<font style="color:#F5222D;">_</font>****<font style="color:#F5222D;">DIRECTORY结构体数组的元素个数</font>****<font style="color:#F5222D;">。正常文件中IMAGE_DATA_DIRECTORY数组元素的个数为10，但在UPack中将其更改为了A个</font>**（参考图18-12中的框选区域）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581389864383-9873f18c-b825-425f-aa4c-07925de4ff78.png)

图18-12 NumberOfRvaAndSizes

IMAGE_DATA_DIRECTORY结构体数组元素的个数已经被确定为10，但PE规范将NumberOfRvaAndSizes值作为数组元素的个数（类似于前面讲解过的SizeOfOptionalHeader)。**<font style="color:#F5222D;">所以UPack中IMAGE_DATA_DIRECTORY结构体数组的后6个元素被忽略。</font>****<font style="color:#F5222D;">    </font>**

表18-1中已经对IMAGE_DATA_DIRECTORY结构体数组的各项进行了说明。其中粗斜体的项如果更改不正确，就会引发运行错误。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581390044795-7226ac50-83fa-43c2-a32a-bca0586be821.png)

**UPack将IMAGE****_****OPTIONAL****_****HEADER.NumberOfRvaAndSizes的值更改为A，从LOAD****_****CONFIG项（文件偏移D8以后）开始不再使用。UPack就在这块被忽视的IMAGE****_****DATA****_****DIRECTORY区域中覆写自己的代码。UPack真是精打细算，充分利用了文件头的每一个字节。**

   接下来使用Hex Editor查看IMAGE_DATA_DIRECTORY结构体数组区域，如图18-13所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581390351501-29251c2d-5e93-4bbf-9e5a-6ce5bbb5d2b4.png)

图18-13中淡色显示的部分是正常文件的IMAGE_DATA_DIRECTORY结构体数组区域，其下深色显示的是UPack忽视的部分（D8~107区域=LOAD_CONFIG Directory之后）。使用调试器查看被忽视的区域，将看到UPack自身的解码代码，如图18-11所示。

   另外，NumberOfRvaAndSizes的值改变后，在OllyDbg中打开该文件就会弹出如图18-14所示的错误消息框。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581390601268-5d47e8c5-840d-4951-8b9b-65791efd5c76.png)

OllyDbg检查PE文件时会检查NumberOfRvaAndSizes的值是否为10，这个错误信息并不重要，可以忽略。使用其他插件也可完全删除，仅供参考。

## 18.5.4 IMAGE_SECTION_HEADER
IMAGE_SECTION_HEADER结构体中，**<font style="color:#F5222D;">Upack会把自身数据记录到程序运行不需要的项目</font>**。这与UPack向PE文件头中不使用的区域覆写自身代码与数据的方法是一样的（PE文件头中未使用的区域比想象的要多）。

在前面的学习中，我们已经知道节区数是3个（code(代码）、data（数据）、resource（资源)），IMAGE_SECTION_HEADER结构体数组的起始位置为170。（**UPack把SizeOfOptionalHeader的值设置为148，比正常值（E0或F0）要更大一些。**所以IMAGE_SECTION_HEADER是从偏移170开始的（IMAGE_OPTIONAL_HEADER的起始偏移（28）+SizeOfOptionalHeader(148)=170)）。下面使用Hex Editor查看IMAGE_SECTION_HEADER结构体（偏移170~1E7的区域），如图18-15所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581391063322-b6de7f87-11f1-47a4-8056-92cf6926f93b.png)

图18-15 IMAGE_SECTION_HEADER

图18-15显示的即是IMAGE_SECTION_HEADER结构体，为便于查看，将其中数据整理如下（使用的是我亲自制作的PE Viewer）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581391206337-0c649100-fe61-44e9-892a-7e92501edecb.png)

代码18-1框选的结构体成员对程序运行没有任何意义。比如文件偏移1B0地址处的offset torelocations值为0100739D，它为原notepad.exe的EP值。此外，节区头中还隐藏着一些秘密（马上就会讲到）。

## 18.5.5重叠节区
**<font style="color:#F5222D;">UPack的主要特征之一就是可以随意重叠PE节区与文件头</font>**（刚刚学过PE文件头基础知识的朋友可能会对这种技法感到惊慌失措）。

通过Stud_PE提供的简略视图查看UPack的IMAGE_SECTION_HEADER。请选择Stu_PE的“Section”选项卡，如图18-16所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581391518826-3ad7cca1-697e-40c3-bb95-a896883a180b.png)

图18-16 Stud_ED的Section（**节区**）选项卡

从图18-16中可以看到，其中某些部分看上去比较奇怪。首先是第一个与第三个节区的文件起始偏移（RawOffset）值都为10。偏移10是文件头区域，UPack中该位置起即为节区部分。

然后让人感到奇怪的部分是，第一个节区与第三个节区的文件起始偏移与在文件中的大小（RawSize)是完全一致的。但是，节区内存的起始RVA（VirtualOffset）项与内存大小（VirtualSize)值是彼此不同的。根据PE规范，这样做不会有什么问题（更准确地说，PE规范并未明确指出这样做是不行的）。

综合以上两点可知，UPack会对PE文件头、第一个节区、第三个节区进行重叠。仅从数字上很难真正理解其中的含义，为了帮助各位更好地掌握，图18-17描述了UPack重叠的情形。

图18-17左侧描述的是文件中的节区信息，右侧描述的是内存中的节区信息。

根据节区头（IMAGE_SECTION_HEADER)中定义的值，PE装载器会将文件偏移0~1FF的区域分别映射到3个不同的内存位置（文件头、第一个节区、第三个节区）。**<font style="color:#F5222D;">也就是说，用相同的文件映像可以分别创建出处于不同位置的、大小不同的内存映像，请各位注意。</font>**

文件的头（第一/第三个节区）区域的大小为200，其实这是非常小的。**相反，第二个节区（2ndSection)尺寸（AE28）非常大，占据了文件的大部分区域，原文件（notepad.exe)即压缩于此。**

另外一个需要注意的部分是内存中的第一个节区区域，它的内存尺寸为14000，与原文件（notepad.exe)的Size ofImage具有相同的值。也就是说，**<font style="color:#F5222D;">压缩在第二个节区中的文件映像会被原样解压缩到第一个节区（notepad的内存映像）。另外，原notepad.exe拥有3个节区，它们被解压到一个节区。</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581391976926-8ed21f0d-359d-4f20-9e04-bacc67feb153.png)

解压缩后的第一个节区如图18-18所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581392036160-03974092-622d-4f1c-92a3-aa69c4fd2082.png)

**<font style="color:#F5222D;">重新归纳整理一下，压缩的notepad在内存的第二个节区，解压缩的同时被记录到第一个节区。</font>**

**<font style="color:#F5222D;">重要的是，notepad.exe（原文件）的内存映像会被整体解压，所以程序能够正常运行（地址变得准确而一致）。</font>**

## 18.5.6 RVA to RAW
各种PE实用程序对Upack束手无策的原因就是无法正确进行RVA→RAW的变换。UPack的制作者通过多种测试（或对PE装载器的逆向分析）发现了Windows PE装载器的Bug（或者异常处理），并将其应用到UPack。

PE实用程序第一次遇到应用了这种技法的文件时，大部分会出现“错误的内存引用，非正常终止”（后来许多实用程序对此进行了修复）。

首先复习一下RVA→RAW变换的常规方法。

> **<font style="color:#000000;">RAW-PointerToRawData=RVA-VirtualAddress=Imagebase</font>**
>
> **<font style="color:#F5222D;">RAW=RVA-VirtualAddress（是使用RVA形式表示的值）+PointerToRawData</font>**
>
> **VirtualAddress、PointerToRawData是从RVA所在的节区头中获取的值，它们都是已知值（known value)。**
>

根据上述公式，算一下EP的文件偏移量（RAW）。UPack的EP是RVA 1018（参考图18-19）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581393986061-8f7b53cb-4edc-450f-ad0c-03ea37f34137.png)

图18-19AddressOfEntryPoint

根据代码18-1、图18-17、图18-18，RVA1018位于第一个节区（1st Section)，将其代入公式换算如下。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581394096479-2c313bc6-7100-40a5-b889-f62c983b3a0f.png)

使用Hex Editor打开RAW28区域查看，如图18-20所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581394184378-d0dac0df-e56c-441a-8798-8af978188dcb.png)

图18-20 RAW28区域

RAW28不是代码区域，而是(ordinal:010B）“LoadLibraryA”字符串区域。现在UPack的这种把戏欺骗了我们（实际上，OllyDbg的早期版本并不能找出UPack的EP）。秘密就在于第一个节区的Pointer ToRawData值10。

一般而言，指向节区开始的文件偏移的Pointer ToRawData值应该是FileAlignment的整数倍。

UPack的FileAlignment为200，故PointerToRawData值应为0、200、400、600等值。**PE装载器发现第一个节区的PointerToRawData（10）不是FileAlignment（200)的整数倍时，它会强制将其识别为整数倍（该情况下为0）。**这使UPack文件能够正常运行，但是许多PE相关实用程序都会发生错误。

正常的RVA→RAW变换如下。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581394304280-435e9e46-1e26-424d-a829-d50d5b189d6f.png)

现在各位应该能够对UPack文件进行正常的RVA→RAW换算了。

## 18.5.7导入表（IMAGE_IMPORT_DESCRIPTOR array)
UPack的导入表（Import Table）组织结构相当独特（暗藏玄机）。

下面使用Hex Editor查看IMAGE_IMPORT_DESCRIPTOR结构体。首先要从Directory Table中获取**IDT（IMAGE IMPORT_DESCRIPTOR结构体数组）的地址**，如图18-22所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581394458993-586b5b1b-8ca8-486c-9183-1b9e9b870680.png)

图18-22导入表地址

图18-22右侧框选的8个字节大小的data就是指向导入表的IMAGE_DATA_DIRECTORY结构体。**前面4个字节为导入表的地址（RVA），后面4个字节是导入表的大小（Size）**。从图中可以看到导入表的RVA为271EE。

使用Hex Editor查看之前，需要先进行RVA→RAW变换。首先确定该RVA值属于哪个节区，内存地址271EE在内存中是第三个节区（参考图18-23）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581394553963-459fd101-d511-47e0-a077-6e8a14563b6f.png)

图18-23第三个节区区域

进行RVA→RAW变换，如下所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581394611516-a7bbb30e-ee3d-4d0b-aa26-70fa9339e7a8.png)

使用Hex Editor查看文件偏移1EE中的数据，如图18-24所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581394872055-3e35c728-4f3d-4c6f-8372-61da9be48e61.png)

图18-24 文件偏移1EE

该处就是使用UPack节区隐藏玄机的地方。

首先看一下代码18-2中IMAGE_IMPORT_DESCRIPTOR结构体的定义，再继续分析（结构体的大小为14字节）。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581394756170-dc2d9dd0-bcf2-413e-be81-5648a4474a61.png)

根据PE规范<font style="color:#000000;">，</font>**<font style="color:#F5222D;">导入表是由一系列IMAGE_IMPORT_DESCRIPTOR结构体组成的数组</font>****<font style="color:#F5222D;">，最后以一个内容为NULL的结构体结束。</font>**

图18-24中所选区域就是IMAGE_IMPORT_DESCRIPTOR结构体数组（导入表）。偏移1EE～201为第一个结构体，其后既不是第二个结构体，也不是（表示导入表结束的）NULL结构体。

乍一看这种做法分明是违反PE规范的。但是请注意图18-24中偏移200上方的粗线。该线条表示文件中第三个节区的结束（参考图18-23）。故运行时偏移在200以下的部分不会映射到第三个节区内存。下而看一下图18-25。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581394939298-c96d9cd6-fcff-4959-9c24-cf2bf1f2a0da.png)

第三个节区加载到内存时，文件偏移0~1FF的区域映射到内存的27000-271FF区域，而（第三个节区其余的内存区域）27200~28000区域全部填充为NULL。使用调试器查看相同区域，如图18-26所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581395072126-dd3d8d8e-ccc2-4bee-be7d-950702310468.png)

准确地说，只映射到010271FF，从01027200开始全部填充为NULL值。

再次返回PE规范的导入表条件，01027202地址以后出现NULL结构体，这并不算违反PE规范。而这正是UPack使用节区的玄机。从文件看导入表好像是损坏了，但其实它已在内存中准确表现出来。

 大部分PE实用程序从文件中读导入表时都会被这个玄机迷惑，查找错误的地址，继而引起内存引用错误，导致程序非正常终止（一句话——这个玄机还真是妙）。

## 18.5.8导入地址表
UPack都输入了哪些DLL中的哪些API呢?下面通过分析IAT查看。把代码18-2的IMAGE_IMPORT_DESCRIPTOR结构体与图18-24进行映射后，得到下表18-2。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581395250113-d1f8e6ea-4514-40ff-8864-14c5cb431058.png)

首先Name的RVA值为2，它属于Header区域（因为第一个节区是从RVA1000开始的）。

Header区域中RVA与RAW值是一样的，故使用Hex Editor查看文件中偏移（RAW)为2的区域，如图18-27所示。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581395307162-e222a3b6-d6e2-4af1-aa40-492ba66a4e4e.png)

    图18-27文件偏移2

在偏移为2的区域中可以看到字符串KERNEL32.DLL。该位置原本是DOS头部分（IMAGE_DOSHEADER），属于不使用的区域，UPack将Import DLL名称写入该处。空白区域一点儿都没浪费（好节俭的UPack)。得到DLL名称后，再看一下从中导入了哪些API函数。

一般而言，跟踪OriginalFirstThunk（INT)能够发现API名称字符串，但是像UPack这样，OriginalFirstThunk（INT）为0时，跟踪FirstThunk（IAT）也无妨（只要INT、IAT其中一个有API名称字符串即可）。由图18-23可知，IAT的值为11E8，属于第一个节区，故RVA→RAW换算如下。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581395399294-516e0140-3bc6-4ccd-895e-9d39ef40f27c.png)

IAT的文件偏移1E8显示在图18-28中。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581395478740-15da92ad-217c-478a-9bc9-24cd80687e2e.png)

图18-28 文件偏移1E8

图18-28中框选的部分就是IAT域，同时也作为INT来使用。也就是说，该处是Name Pointer（RVA）数组，其结束是NULL。此外还可以看到导入了2个API，分别为RVA28与BE。

RVA位置上存在着导入函数的[ordinal+名称字符串]，如图18-29所示。由于都是header区域，所以RVA与RAW值是一样的。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1581395556069-458a4072-6c10-490b-9d74-d644ad4fe6ca.png)

从图18-29中可以看到导人的2个API函数，分别为LoadLibraryA与GetProcAddress，它们在形成原文件的IAT时非常方便，所以普通压缩器也常常导入使用。

# 18.6小结
本章详细讲解了UPack的独特PE文件头相关知识。学习PE文件格式时虽然未涉及各结构体的所有成员，但分析UPack压缩的可执行文件的PE文件头（PE文件头变形得很厉害），会进一步加深大家对PE文件格式的了解。这些内容虽然对初学者有些难，但是如果多努力去理解并掌握这些内容，以后无论遇到什么样的PE文件头都能轻松分析。

# Q&A
Q.UPack压缩器是病毒文件吗？

A.UPack压缩器本身不是恶意程序。但是许多恶意代码制作者用UPack来压缩自己的恶意代码，使文件变得畸形，所以许多杀毒软件将UPack压缩的文件全部识别为病毒文件并删除。







