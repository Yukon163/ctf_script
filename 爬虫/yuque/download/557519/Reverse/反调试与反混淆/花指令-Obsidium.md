> 2015NCTF-2015_nctf_re
>

还得输一星期的液，要废了...

论右手打字的憋屈感...

---

参考资料：[https://www.cnblogs.com/ZRBYYXDM/articles/5192953.html](https://www.cnblogs.com/ZRBYYXDM/articles/5192953.html)

首先介绍一下花指令的概念：

花指令是一些专门用来迷惑反汇编软件的代码数据，而对于cpu来说，依旧还是会执行正确的代码。通过插入无效数据，干扰反汇编软件对PE文件的分析，导致其显示出很多无用的信息。

接下来我们开始实战：

任务目标：拆解Nag窗口 & 找出密钥

首先查壳：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585878723625-f0d4d7f6-09af-4f63-9cf6-41b89c21954d.png)

没有壳，为了调试方便，在Windows XP虚拟机环境下运行该程序，结果无限（255次）弹出如下窗口：

（任务管理器结束此进程）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585879089619-7adaa7f5-e01d-41fe-b98c-ce0576315a17.png)（不搞，滚！）

在IDA里就可以看出（搜索字符串“小兄弟”然后交叉引用）：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585879393475-726bb2c7-c8b9-4104-b8c0-c1aa889278c3.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585879452649-27322a98-5bb9-44ad-b4be-74a46c7d4c03.png)

接下来我们拆解Nag窗口：

用OD载入该程序，对MessageBoxA下断

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585879726048-4c3ccc14-e916-4b5d-be0f-59e24717c54e.png)

F9运行后中断：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585879802574-b12445fe-c394-47fc-b841-30769dd5a3f8.png)

按F8单步走，当步过call user32.MessageBoxExA后，此时的堆栈窗口如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1585881538345-8385ba47-21fa-43a1-8f1a-aa9d7d686b5c.png)

并且弹出窗口：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586048327081-6a136c52-647b-4341-88ef-5c28bce0d9d9.png)

单击窗口中的确定后，我们继续在OD中步过，来到：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586048610366-5f3ab0a2-8847-4f35-96be-99da9f7a93d2.png)

继续：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586048694841-9ae9a422-e6a3-463c-b433-cfb8a6edbc7b.png)

继续：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586048763939-ce02b9a4-48ef-449b-b7b3-ba41008fc19a.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586048801720-06f26312-4819-4dca-9df8-c17d2b62d3e1.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586048849275-1f155a66-098e-4f5f-aca0-a61ec5e0519a.png)

结果我们又回到了：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586048927130-77bcf9b6-f014-4a3a-bccc-3e938652a8f5.png)

在上述循环，我们发现关键语句：地址的00401311 jnz short 00401300

这条语句关乎着是否弹出窗口，我们再次单步来到地址的00401311 jnz short 00401300

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586049302416-a9048dcb-d46d-4c64-90e4-5c958db93f9e.png)

要使其不跳转，修改jnz short 00401300为：je short 00401300

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586049419605-993e6a4a-7098-48ca-9879-20b292737e01.png)

然后保存exe：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586049584701-41c54b2f-0848-4bf1-8c24-4fff73555003.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586049624284-4bc29006-8b4d-4569-8e6c-c4c04a7dc679.png)

保存为2.exe，关闭OD

打开2.exe，弹出一次窗口后，有：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586049848670-a7289ad1-1559-4ef5-8dfa-ab39d5379ccb.png)

用OD载入修改后的2.exe，由于有上述窗口，我们对GetDlgItemTextA下断：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586050087804-30fe8ac7-303b-4b70-8a22-4449777bb5ff.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586050082316-808d3fec-7425-485a-b303-6d5e5952023a.png)

按F9执行，在弹出的窗口中点击确定：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586048327081-6a136c52-647b-4341-88ef-5c28bce0d9d9.png)

然后出现：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586049848670-a7289ad1-1559-4ef5-8dfa-ab39d5379ccb.png)

随便输入内容：“123456789”，单击确定，OD中有：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586050595027-eb2eb159-f49e-4a0b-9c36-ddf8e21265ad.png)

多次F8单步执行回到程序领空

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586050756199-f9d41331-516b-4099-a08c-c3c80614139d.png)

（为了方便，在地址0040141F处下断）如图所示，程序后面出现了一大段无用数据，继续运行，发现程序跟入了无用数据中，但寄存器的值却在不停的变换，说明该处指令被混淆过。

由于吾爱破解的OD中没有去除“Obsidium”花指令的插件，我们记下地址0040141F，打开吾爱破解工具包中的

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586051172412-993651f3-beb7-4cd1-8663-bf61c5a9891e.png)

将程序载入，使程序的EIP来到地址0040141F（期间需要一些操作）：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586051369554-9151c6d9-4dab-42e0-9cb7-57cac0c298cc.png)

选择40141F-401431处指令，右键->去除花指令->Obsidium即可去除花指令

> 注意：请在去除花指令之前让EIP指向地址401433处，否则可能会出现调试异常！
>

此时的寄存器窗口：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586051688604-8706cbbd-60aa-4868-adee-ff12da798a58.png)

接下来我们慢慢的分析：（此时EIP指向：00401433）（十六进制：123456789ABCDEF）

00401431      C3            retn

00401432      C45B 5A       les     ebx, fword ptr [ebx+5A]

00401435      59            pop     ecx

00401436      51            push    ecx

00401437      52            push    edx

00401438      53            push    ebx

00401439      33DB          xor     ebx, ebx

0040143B      74 01         **je      short 0040143E**

<font style="color:#F5222D;">0040143D      E8 5B5A5980   call    80996E9D（未执行，可nop）</font>

00401442      306E 51       xor     byte ptr [esi+51], ch

00401445      52            push    edx

00401446      53            push    ebx

00401447      33DB          xor     ebx, ebx

00401449      74 01         **je      short 0040144C**

<font style="color:#F5222D;">0040144B    - E9 5B5A5980   jmp     80996EAB（未执行，可nop）</font>

00401450      70 01         jo      short 00401453

00401452      6251 52       bound   edx, qword ptr [ecx+52]

...（省略一部分指令）

没有执行的地方可以确定是垃圾数据，<font style="color:#303030;">用n</font>op填充（“剩余的用nop填充”不要打钩）

从地址00401441处就开始对我们输入的数据进行异或，可以跟随一下数据窗口

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586079373198-baae62a9-fba4-4848-9bb4-2526b5d224a3.png)

<font style="color:#800080;">00401441</font>      <font style="color:#800080;">8030</font> 6E       <font style="color:#0000FF;">xor</font>     byte ptr [eax], 6E               <font style="color:#008000;">;</font><font style="color:#008000;">  第一个字符与6E异或</font>

<font style="color:#800080;">00401444</font>      <font style="color:#800080;">51</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ecx</font>

<font style="color:#800080;">00401445</font>      <font style="color:#800080;">52</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    edx</font>

<font style="color:#800080;">00401446</font>      <font style="color:#800080;">53</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ebx</font>

<font style="color:#800080;">00401447</font>      33DB          <font style="color:#0000FF;">xor</font>     ebx, ebx                         <font style="color:#008000;">;</font><font style="color:#008000;">  清空ebx</font>

<font style="color:#800080;">00401449</font>      <font style="color:#800080;">74</font> <font style="color:#800080;">01</font>         <font style="color:#0000FF;">je</font>      short <font style="color:#800080;">0040144C</font>                   <font style="color:#008000;">;</font><font style="color:#008000;">  跳入144C，144B没有被执行</font>

<font style="color:#800080;">0040144B</font>      <font style="color:#800080;">90</font>            <font style="color:#0000FF;">nop</font>

<font style="color:#800080;">0040144C</font>      5B            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ebx</font>

<font style="color:#800080;">0040144D</font>      5A            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     edx</font>

<font style="color:#800080;">0040144E</font>      <font style="color:#800080;">59</font>            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ecx</font>

<font style="color:#800080;">0040144F</font>      <font style="color:#800080;">8070</font> <font style="color:#800080;">01</font> <font style="color:#800080;">62</font>    <font style="color:#0000FF;">xor</font>     byte ptr [eax+<font style="color:#800080;">1</font>], <font style="color:#800080;">62</font>             <font style="color:#008000;">;</font><font style="color:#008000;">  第二个字符与62异或</font>

<font style="color:#800080;">00401453</font>      <font style="color:#800080;">51</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ecx</font>

<font style="color:#800080;">00401454</font>      <font style="color:#800080;">52</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    edx</font>

<font style="color:#800080;">00401455</font>      <font style="color:#800080;">53</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ebx</font>

<font style="color:#800080;">00401456</font>      33DB          <font style="color:#0000FF;">xor</font>     ebx, ebx                         <font style="color:#008000;">;</font><font style="color:#008000;">  清空ebx</font>

<font style="color:#800080;">00401458</font>      <font style="color:#800080;">74</font> <font style="color:#800080;">01</font>         <font style="color:#0000FF;">je</font>      short <font style="color:#800080;">0040145B</font>                   <font style="color:#008000;">;</font><font style="color:#008000;">  跳入145B，145A没有被执行</font>

<font style="color:#800080;">0040145A</font>      <font style="color:#800080;">90</font>            <font style="color:#0000FF;">nop</font>

<font style="color:#800080;">0040145B</font>      5B            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ebx</font>

<font style="color:#800080;">0040145C</font>      5A            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     edx</font>

<font style="color:#800080;">0040145D</font>      <font style="color:#800080;">59</font>            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ecx</font>

<font style="color:#800080;">0040145E</font>      <font style="color:#800080;">8070</font> <font style="color:#800080;">02</font> <font style="color:#800080;">76</font>    <font style="color:#0000FF;">xor</font>     byte ptr [eax+<font style="color:#800080;">2</font>], <font style="color:#800080;">76</font>             <font style="color:#008000;">;</font><font style="color:#008000;">  第三个字符与76异或</font>

<font style="color:#800080;">00401462</font>      <font style="color:#800080;">51</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ecx</font>

<font style="color:#800080;">00401463</font>      <font style="color:#800080;">52</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    edx</font>

<font style="color:#800080;">00401464</font>      <font style="color:#800080;">53</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ebx</font>

<font style="color:#800080;">00401465</font>      33DB          <font style="color:#0000FF;">xor</font>     ebx, ebx                         <font style="color:#008000;">;</font><font style="color:#008000;">  清空ebx</font>

<font style="color:#800080;">00401467</font>      <font style="color:#800080;">74</font> <font style="color:#800080;">01</font>         <font style="color:#0000FF;">je</font>      short <font style="color:#800080;">0040146A</font>                   <font style="color:#008000;">;</font><font style="color:#008000;">  跳入146A，1469没有被执行</font>

<font style="color:#800080;">00401469</font>      <font style="color:#800080;">90</font>            <font style="color:#0000FF;">nop</font>

<font style="color:#800080;">0040146A</font>      5B            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ebx</font>

<font style="color:#800080;">0040146B</font>      5A            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     edx</font>

<font style="color:#800080;">0040146C</font>      <font style="color:#800080;">59</font>            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ecx</font>

<font style="color:#800080;">0040146D</font>      <font style="color:#800080;">8070</font> <font style="color:#800080;">03</font> <font style="color:#800080;">65</font>    <font style="color:#0000FF;">xor</font>     byte ptr [eax+<font style="color:#800080;">3</font>], <font style="color:#800080;">65</font>             <font style="color:#008000;">;</font><font style="color:#008000;">  第四个字符与65异或</font>

<font style="color:#800080;">00401471</font>      <font style="color:#800080;">51</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ecx</font>

<font style="color:#800080;">00401472</font>      <font style="color:#800080;">52</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    edx</font>

<font style="color:#800080;">00401473</font>      <font style="color:#800080;">53</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ebx</font>

<font style="color:#800080;">00401474</font>      33DB          <font style="color:#0000FF;">xor</font>     ebx, ebx                         <font style="color:#008000;">;</font><font style="color:#008000;">  清空ebx</font>

<font style="color:#800080;">00401476</font>      <font style="color:#800080;">74</font> <font style="color:#800080;">01</font>         <font style="color:#0000FF;">je</font>      short <font style="color:#800080;">00401479</font>                   <font style="color:#008000;">;</font><font style="color:#008000;">  跳入1479，1478没有被执行</font>

<font style="color:#800080;">00401478</font>      <font style="color:#800080;">90</font>            <font style="color:#0000FF;">nop</font>

<font style="color:#800080;">00401479</font>      5B            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ebx</font>

<font style="color:#800080;">0040147A</font>      5A            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     edx</font>

<font style="color:#800080;">0040147B</font>      <font style="color:#800080;">59</font>            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ecx</font>

<font style="color:#800080;">0040147C</font>      <font style="color:#800080;">8070</font> <font style="color:#800080;">04</font> 7F    <font style="color:#0000FF;">xor</font>     byte ptr [eax+<font style="color:#800080;">4</font>], 7F             <font style="color:#008000;">;</font><font style="color:#008000;">  第五个字符与7F异或</font>

<font style="color:#800080;">00401480</font>      <font style="color:#800080;">51</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ecx</font>

<font style="color:#800080;">00401481</font>      <font style="color:#800080;">52</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    edx</font>

<font style="color:#800080;">00401482</font>      <font style="color:#800080;">53</font>            <font style="color:#0000FF;">push</font><font style="color:#000000;">    ebx</font>

<font style="color:#800080;">00401483</font>      33DB          <font style="color:#0000FF;">xor</font>     ebx, ebx                         <font style="color:#008000;">;</font><font style="color:#008000;">  清空ebx</font>

<font style="color:#800080;">00401485</font>      <font style="color:#800080;">74</font> <font style="color:#800080;">01</font>         <font style="color:#0000FF;">je</font>      short <font style="color:#800080;">00401488</font>                   <font style="color:#008000;">;</font><font style="color:#008000;">  跳入1488，1487没有被执行</font>

<font style="color:#800080;">00401487</font>      <font style="color:#800080;">90</font>            <font style="color:#0000FF;">nop</font>

<font style="color:#800080;">00401488</font>      5B            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ebx</font>

<font style="color:#800080;">00401489</font>      5A            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     edx</font>

<font style="color:#800080;">0040148A</font>      <font style="color:#800080;">59</font>            <font style="color:#0000FF;">pop</font><font style="color:#000000;">     ecx</font>

<font style="color:#800080;">0040148B</font>      <font style="color:#800080;">8070</font> <font style="color:#800080;">05</font> <font style="color:#800080;">49</font>    <font style="color:#0000FF;">xor</font>     byte ptr [eax+<font style="color:#800080;">5</font>], <font style="color:#800080;">49</font>             <font style="color:#008000;">;</font><font style="color:#008000;">  第六个字符与49异或</font>

    <font style="color:#008000;">;</font><font style="color:#008000;">省略一部分异或指令</font>

数据进行异或后，数据窗口如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586079582357-c10926dc-b409-4e45-922d-9b9e571e2bf3.png)

异或运算完成后，来到判断算法：

0040156C      8B0D 3C524400 mov     ecx, dword ptr [44523C]<font style="color:#52C41A;"> //取出异或后的字符串</font>

00401572      0FB611        movzx   edx, byte ptr [ecx]<font style="color:#52C41A;">//判断首字符</font>

00401575      85D2          test    edx, edx/<font style="color:#52C41A;">/非零则跳转出错</font>

00401577      75 4A         jnz     short 004015C3<font style="color:#52C41A;">//退出</font>

00401579      C645 FF 00    mov     byte ptr [ebp-1], 0<font style="color:#52C41A;">//计数器置零</font>

0040157D      EB 08         jmp     short 00401587

0040157F      8A45 FF       mov     al, byte ptr [ebp-1]

00401582      04 01         add     al, 1

00401584      8845 FF       mov     byte ptr [ebp-1], al

00401587      0FB64D FF     movzx   ecx, byte ptr [ebp-1]

0040158B      83F9 14       cmp     ecx, 14<font style="color:#52C41A;">//计数器为0x14？</font>

0040158E      7D 33         jge     short 004015C3<font style="color:#52C41A;">//是则结束</font>

00401590      0FB655 FF     movzx   edx, byte ptr [ebp-1]

00401594      0FB645 FF     movzx   eax, byte ptr [ebp-1]

00401598      8B0D 3C524400 mov     ecx, dword ptr [44523C]<font style="color:#52C41A;">//异或后字符地址存入ecx</font>

0040159E      0FB60401      movzx   eax, byte ptr [ecx+eax]

004015A2      3BD0          cmp     edx, eax<font style="color:#52C41A;">//迭代字串的第n个字符是否等于n？</font>

004015A4      75 19         jnz     short 004015BF <font style="color:#52C41A;">//否则直接结束比较</font>

004015A6      0FB64D FF     movzx   ecx, byte ptr [ebp-1]

004015AA      83F9 13       cmp     ecx, 13<font style="color:#52C41A;">//计数器为0x13？</font>

004015AD      75 0E         jnz     short 004015BD <font style="color:#52C41A;"> //否则跳转 继续循环</font>

004015AF      6A 00         push    0

004015B1      6A 00         push    0

004015B3      68 84894300   push    00438984

004015B8      E8 49480000   call    00405E06

004015BD      90            nop

004015BE      90            nop

004015BF      90            nop

004015C0      90            nop

004015C1    ^ EB BC         jmp     short 0040157F

004015C3      5B            pop     ebx

004015C4      8BE5          mov     esp, ebp

004015C6      5D            pop     ebp

004015C7      C3            retn

该处将我们输入的字符串和一串固定的密钥进行异或，结果字串值应为0,1,2,3,4.......

写一段C代码实现逆算法：

<font style="color:#c586c0;">#include</font><font style="color:#569cd6;"> <iostream></font>

<font style="color:#c586c0;">using</font><font style="color:#d4d4d4;"> </font><font style="color:#569cd6;">namespace</font><font style="color:#d4d4d4;"> </font><font style="color:#4ec9b0;">std;</font>

<font style="color:#569cd6;">int</font><font style="color:#d4d4d4;"> </font><font style="color:#dcdcaa;">main(){</font>

<font style="color:#d4d4d4;">    </font><font style="color:#569cd6;">char</font><font style="color:#d4d4d4;"> ch = </font><font style="color:#b5cea8;">0x7F</font><font style="color:#d4d4d4;">;</font>

<font style="color:#d4d4d4;">    string str = </font><font style="color:#ce9178;">"nbve";</font>

<font style="color:#d4d4d4;">    str += ch;</font>

<font style="color:#d4d4d4;">    str +=</font><font style="color:#ce9178;">"I6KWyoex>QDy #n"</font><font style="color:#d4d4d4;">;</font><font style="color:#6a9955;">                        //拼接用来异或的字串</font>

<font style="color:#52C41A;">//str相当于：</font><font style="color:#52C41A;">"nbve</font><font style="color:#52C41A;">0x7F</font><font style="color:#52C41A;">I6KWyoex>QDy #n</font><font style="color:#52C41A;">";</font>

<font style="color:#d4d4d4;">    </font><font style="color:#4ec9b0;">string</font><font style="color:#d4d4d4;">::iterator iter = </font><font style="color:#9cdcfe;">str</font><font style="color:#d4d4d4;">.</font><font style="color:#dcdcaa;">begin</font><font style="color:#d4d4d4;">();</font>

<font style="color:#d4d4d4;">    </font><font style="color:#c586c0;">for</font><font style="color:#d4d4d4;"> ( </font><font style="color:#569cd6;">int</font><font style="color:#d4d4d4;"> i = </font><font style="color:#b5cea8;">0</font><font style="color:#d4d4d4;"> ; iter != </font><font style="color:#9cdcfe;">str</font><font style="color:#d4d4d4;">.</font><font style="color:#dcdcaa;">end</font><font style="color:#d4d4d4;">() ; iter++,i++ ){</font>

<font style="color:#d4d4d4;">        *iter ^= i;</font>

<font style="color:#d4d4d4;">    }</font>

<font style="color:#d4d4d4;">    cout << str << endl;</font>

<font style="color:#d4d4d4;">    </font><font style="color:#c586c0;">return</font><font style="color:#d4d4d4;"> </font><font style="color:#b5cea8;">0</font><font style="color:#d4d4d4;">;</font>

<font style="color:#d4d4d4;">}</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586079824884-d345870a-67a4-420e-bdc1-9b25e8664e38.png)

flag：nctf{L0L_pent3_Ki11}

