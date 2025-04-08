> **<font style="color:#13C2C2;">感谢@Taqini师傅</font>**
>
> 参考文章：
>
> [http://taqini.space/2020/04/29/about-execve](http://taqini.space/2020/04/29/about-execve)
>
> [http://www.pwn4fun.com/pwn/onegadget-xuanxue-getshell.html](http://www.pwn4fun.com/pwn/onegadget-xuanxue-getshell.html)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1GCVAZ-W39RJk4eUw7LdFUQ](https://pan.baidu.com/s/1GCVAZ-W39RJk4eUw7LdFUQ)  密码: 3der
>
> --来自百度网盘超级会员V3的分享
>

# 前言
gadget可以译为小片段的意思，但在pwn中gadget的作用是利用ELF或libc.so中的汇编代码来调整栈帧或寄存器的值，从而达到ROP攻击：getshell、执行自定义参数函数（read、write等）。而one_gadget也是由一些小片段组成的，但是组成的是execve("/bin/sh",argv,envp)，利用此函数可以达到getshell的目的；所以将凭借一己之力getshell的gadget称为one_gadget。

# execve-函数原型
one_gadget本质上调用的是execve("/bin/sh",argv,envp)，先来看一下它的函数原型：

```c
#include <unistd.h>
int execve (const char *filename, char *const argv [], char *const envp[]);
```

execve函数中有3个参数，简单看一下参数的类型：

+ const char *filename

第一个参数是const char *类型的，这意味着在内存中filename必须是一个合法的指针（字符串常量）。

+ char *const argv []和char *const envp[]

这两个参数都是char *const类型的数组，同样也要求必须是一个合法的指针（字符串数组常量）。

> 关于char类型，可以看：
>
> [https://www.yuque.com/cyberangel/rg9gdm/bichu8](https://www.yuque.com/cyberangel/rg9gdm/bichu8)
>

# execve-man手册
为了深入研究execve函数，有必要研究一下它的man手册：

> [https://man7.org/linux/man-pages/man2/execve.2.html](https://man7.org/linux/man-pages/man2/execve.2.html)
>
> 或在Linux的终端上执行：man execve
>
> **<font style="color:#F5222D;">这里只摘了与本文有关系的段落，不涉及Linux底层调用。</font>**
>

execve() executes the program referred to by pathname. This causes the program that is currently being run by the calling process to be replaced with a new program, with newly initialized stack, heap, and (initialized and uninitialized) data segments.

> execve执行pathname所指向的程序，这将导致新程序会代替当前所运行的程序（包含新初始化的堆栈和初始化的和未初始化的数据段）
>

pathname must be either a binary executable, or a script starting with a line of the form:

#!interpreter [optional-arg]

> <font style="background-color:#FADB14;">pathname</font>**<font style="color:#F5222D;background-color:#FADB14;">必须</font>**<font style="background-color:#FADB14;">指向一个可执行文件或以“</font><font style="background-color:#FADB14;">#!interpreter [optional-arg]</font><font style="background-color:#FADB14;">”开头的脚本文件</font>
>

argv is an array of pointers to strings passed to the new program as its command-line arguments.  By convention, the first of these strings (i.e., argv[0]) should contain the filename associated with the file being executed.  The argv array must be terminated by a NULL pointer.  (Thus, in the new program, argv[argc] will be NULL.)

> 参数argv是一个指向字符串的指针数组，它作为命令行的参数传递给新程序。**<font style="color:#F5222D;background-color:#FADB14;">按照惯例</font>**，这些字符串的第一个参数（即argv[0]）应该包含与正在执行的文件相关联的文件名。<font style="background-color:#FADB14;">argv数组必须以空指针结束。</font>（因此在新程序中，argv[argc]为空）。
>

envp is an array of pointers to strings, conventionally of the form key=value, which are passed as the environment of the new program.  The envp array must be terminated by a NULL pointer.

> envp是指向字符串的指针数组，**<font style="color:#F5222D;background-color:#FADB14;">通常</font>**是key=value的形式，它将作为环境传递给新程序。<font style="background-color:#FADB14;">envp必须以空指针结束</font>
>

execve() does not return on success, and the text, initialized data, uninitialized data (bss), and stack of the calling process are overwritten according to the contents of the newly loaded program.

> <font style="background-color:#FADB14;">成功调用execve()不会返回任何值</font>，代码段、初始化的数据段、未初始化的bss段，和调用程序的栈将根据新加载的程序的内容覆盖。
>

Interpreter scripts

An interpreter script is a text file that has execute permission enabled and whose first line is of the form:#!interpreter [optional-arg]

> 解释器脚本
>
> 解释器脚本是一个文本文件，（要让它成功的被执行）<font style="background-color:#FADB14;">必须赋予其可执行权限</font>，并且文件的第一行的格式为#!interpreter [optional-arg]
>

The interpreter must be a valid pathname for an executable file.If the pathname argument of execve() specifies an interpreter script, then interpreter will be invoked with the following arguments:interpreter [optional-arg] pathname arg...where pathname is the absolute pathname of the file specified as the first argument of execve(), and arg...  is the series of words pointed to by the argv argument of execve(), starting at argv[1].  Note that there is no way to get the argv[0] that was passed to the execve() call.

> 解释器必须是包含有效路径名（pathname）可执行文件。如果execve()的pathname参数指定了解释器脚本，那么将使用以下参数调用解释器:interpreter [optional-arg] pathname arg...（解释器 [可选参数] 路径名 参数）
>
> <font style="background-color:#FADB14;">其中pathname是作为execve()的第一个参数指定的文件</font>**<font style="color:#F5222D;background-color:#FADB14;">绝对</font>**<font style="background-color:#FADB14;">路径名，</font>从argv[1]开始，arg…是由execve()的argv参数指向的一系列words组成。注意，无法获取到传递给execve()的argv[0]。
>

For portable use, optional-arg should either be absent, or be specified as a single word (i.e., it should not contain white space); see NOTES below.Since Linux 2.6.28, the kernel permits the interpreter of a script to itself be a script.  This permission is recursive, up to a limit of four recursions, so that the interpreter may be a script which is interpreted by a script, and so on.

> 为了方便使用，optional-arg应该指定为空或单个单词(不包含空格);详情请参阅下面的注意事项。从Linux 2.6.28开始，<font style="background-color:#FADB14;">内核允许脚本的解释器本身就是脚本</font><font style="background-color:#FADB14;">。这个权限是递归的，最多只能有四次递归</font>，因此解释器可以是由脚本解释的脚本，以此类推。
>

Limits on size of arguments and environment 

Most UNIX implementations impose some limit on the total size ofthe command-line argument (argv) and environment (envp) strings that may be passed to a new program.  

> 限制参数和环境的大小
>
> <font style="background-color:#FADB14;">大多数UNIX对传递给新程序的命令行参数(argv)和环境字符串(envp)的总大小施加了一些限制。</font>（限制太复杂，不在此介绍）。
>

RETURN VALUE

       On success, execve() does not return, on error -1 is returned,and errno is set appropriately.

> 如果调用成功，execve()不会返回，**<font style="color:#F5222D;background-color:#FADB14;">否则返回-1，并且为errno赋值。</font>**
>
> errno详见：
>
> [https://manpages.debian.org/unstable/manpages-zh/execve.2.zh_CN.html](https://manpages.debian.org/unstable/manpages-zh/execve.2.zh_CN.html) #中文
>
> [https://man7.org/linux/man-pages/man2/execve.2.html](https://man7.org/linux/man-pages/man2/execve.2.html) #英文
>

# execve-分析
man文档中描述filename用到的是must，must代表必须，这意味着pathname必须符合要求才可以让execve正常执行：

> pathname **<font style="color:#F5222D;">must</font>** be either a binary executable, or a script starting...
>

而对于另外两个参数argv和envp则描述的是：by convention和conventionally

> **<font style="color:#F5222D;">By convention</font>**, the first of these strings
>
> envp is an array of pointers to strings, **<font style="color:#F5222D;">conventionally</font>** of the form key=value...
>

这两个词都有按照惯例的意思，反过来说也可以不按照惯例，进一步将，execve对这两个参数的限制并没有那么严格。在man文档所说的是“按照惯例argv[0]是被执行程序的程序名”，但也可以不是；“按照惯例环境变量应该是key=value的格式”，但也可以不是。写个代码来测试一下：

> man文档中已经说明这两个参数必须以空指针结尾
>
> 让argv[0]中的指针指向0xdeadbeef，让envp[0]中的指针指向0xdeadbeef，最终执行：
>
> execve("/bin/sh","deadbeef","deadbeef")
>

```c
#include<stdio.h>
#include<unistd.h>

int main(){
	const char *filename="/bin/sh";
	char *const argv []={"0xdeadbeef",NULL};
	char *const envp[]={"0xdeadbeef",0};
	execve(filename,argv,envp);
	return 0;
}
```

> gcc -g test.c -o test
>

编译之后，执行效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611900788739-e36f85ee-93db-488a-9e18-9e8b35cc99f6.png)

gdb调试，下断点直接来到execve处，查看内存：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611901206333-cf4a16bb-4ec6-4d25-9e64-a6cb17683aea.png)

```c
pwndbg> x/8gx 0x7fffffffdd70
0x7fffffffdd70:	0x000000000040069c	0x0000000000000000 #argv参数
				#指向“deadbeef”      #以NULL结尾
0x7fffffffdd80:	0x000000000040069c	0x0000000000000000 #envp参数
				#指向“deadbeef”      #以NULL结尾
0x7fffffffdd90:	0x00007fffffffde80	0x7dbad91c7800cd00
0x7fffffffdda0:	0x0000000000400610	0x00007ffff7a2d840
pwndbg> x/4gx 0x40069c
0x40069c:	0x6562646165647830	0x3b031b0100006665 #deadbeef字符串
    		# e b d a e d x 0                 f e 
0x4006ac:	0x0000000500000034	0x00000080fffffda8
pwndbg> x/4gx 0x400694
0x400694:	0x0068732f6e69622f	0x6562646165647830
    		#“/bin/sh”
0x4006a4:	0x3b031b0100006665	0x0000000500000034
pwndbg> 
```

> 在此处，NULL和0的效果是相同的
>

从内存中可以看到0x7fffffffdd70处存放的是指针，这也暗含了其类型char *const argv[]，envp也是这样。

**总结：不按照惯例去设置argv（参数）和envp（环境变量）也是可以的。**

# execve-一个小总结
> int execve (const char *filename, char *const argv [], char *const envp[]);
>

+ execve()功能：执行pathname指定的程序（创建新进程）
+ pathname：二进制程序或可执行脚本的路径名，其数据类型是const char *pathname（字符串常量）
+ argv：传给新程序的参数列表，数据类型是char *const argv[]（字符串数组常量）
+ envp 是新程序的环境变量列表，通常是key=value的形式，数据类型：char *const envp[] 字符串数组常量
+ argv 和 envp 数组的末尾必须是一个空指针（NULL pointer）

# PWN-one_gadget-分析
pwn中的one_gadget虽然强大，但在利用时仍然逃不了限制：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611903776593-bf42b21d-bf67-43de-807d-0c1ee7856cd0.png)

为了方便对照前面的内容，我们以第二个one_gadget来举例：

```c
0x4527a execve("/bin/sh", rsp+0x30, environ)
constraints:
  [rsp+0x30] == NULL
```

> **0x4527a表示在libc文件中的偏移**
>

```c
pwndbg> vmmap
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
          0x400000           0x401000 r-xp     1000 0      /home/ubuntu/Desktop/one_gadget_test/test
          0x600000           0x601000 r--p     1000 0      /home/ubuntu/Desktop/one_gadget_test/test
          0x601000           0x602000 rw-p     1000 1000   /home/ubuntu/Desktop/one_gadget_test/test
    0x7ffff7a0d000     0x7ffff7bcd000 r-xp   1c0000 0      /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7bcd000     0x7ffff7dcd000 ---p   200000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dcd000     0x7ffff7dd1000 r--p     4000 1c0000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd1000     0x7ffff7dd3000 rw-p     2000 1c4000 /lib/x86_64-linux-gnu/libc-2.23.so
    0x7ffff7dd3000     0x7ffff7dd7000 rw-p     4000 0      
    0x7ffff7dd7000     0x7ffff7dfd000 r-xp    26000 0      /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7fd8000     0x7ffff7fdb000 rw-p     3000 0      
    0x7ffff7ff7000     0x7ffff7ffa000 r--p     3000 0      [vvar]
    0x7ffff7ffa000     0x7ffff7ffc000 r-xp     2000 0      [vdso]
    0x7ffff7ffc000     0x7ffff7ffd000 r--p     1000 25000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffd000     0x7ffff7ffe000 rw-p     1000 26000  /lib/x86_64-linux-gnu/ld-2.23.so
    0x7ffff7ffe000     0x7ffff7fff000 rw-p     1000 0      
    0x7ffffffde000     0x7ffffffff000 rw-p    21000 0      [stack]
0xffffffffff600000 0xffffffffff601000 r-xp     1000 0      [vsyscall]
pwndbg> x/10i 0x7ffff7a0d000+0x4527a
   0x7ffff7a5227a <do_system+1098>:	mov    rax,QWORD PTR [rip+0x37ec37]        # 0x7ffff7dd0eb8
   0x7ffff7a52281 <do_system+1105>:	lea    rdi,[rip+0x147b8f]        # 0x7ffff7b99e17
   0x7ffff7a52288 <do_system+1112>:	lea    rsi,[rsp+0x30]
   0x7ffff7a5228d <do_system+1117>:	mov    DWORD PTR [rip+0x381209],0x0        # 0x7ffff7dd34a0 <lock>
   0x7ffff7a52297 <do_system+1127>:	mov    DWORD PTR [rip+0x381203],0x0        # 0x7ffff7dd34a4 <sa_refcntr>
   0x7ffff7a522a1 <do_system+1137>:	mov    rdx,QWORD PTR [rax]
   0x7ffff7a522a4 <do_system+1140>:	call   0x7ffff7ad97f0 <execve>
   0x7ffff7a522a9 <do_system+1145>:	mov    edi,0x7f
   0x7ffff7a522ae <do_system+1150>:	call   0x7ffff7ad9790 <__GI__exit>
   0x7ffff7a522b3:	nop    DWORD PTR [rax]
pwndbg> 
```

当然，也可以使用IDA来看：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611905084880-bde5c6c1-8f66-4362-9467-864d89f227e2.png)

execve("/bin/sh", rsp+0x30, environ)

这个execve的首个参数为"/bin/sh"（rdi）；第三个参数为environ（环境变量），这也是固定的，那么影响getshell的因素就只有第二个参数了即argv（rsi）了。

one_gadget工具静态分析得到的限制条件中说到的[rsp+0x30]==NULL只是一种情况，即argv数组为空，但是按照execve文档中的定义，只要argv是指针数组且末尾为NULL即可，因此在实际的one gadget利用中，要具体情况具体分析，在one gadget执行时，找到限制条件对应的内存的布局，凡是满足指针数组格式的都应该被考虑在内。

就这个one_gadget而言，限制条件是[rsp+0x30] == NULL，但是根据文章前面所说：rsp+0x30对应的内存区域满足如下结构就可以（是个合法指针）：

```c
rsp+0x30 - ptr0 -> argv[0]
rsp+0x38 - ptr1 -> argv[1]
rsp+0x40 - ptr2 -> argv[2]
......
rsp+0x?? - NULL -> ^
```

> **可以对照一下前面的内存**
>

这里虽然只显示了4个one gadget，但实际上libc中并不是只有这4个one gadget。

one_gadget命令默认显示的是限制条件比较宽泛的one gadget，通过-l参数指定搜索级别，显示更多的one gadget。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611909282952-a3b6665e-20bd-4ff0-9fb5-dbf09862f5f0.png)![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611909328570-362c034f-aaca-40c1-9cb4-e95b5ed7878f.png)

# 一些测试
## 0、envp合法性和指针的合法性
为了证明以上内容正确，我们做个测试

> 下面代码均以gcc -g test?.c -o test? 编译执行。
>

先来测试envp合法性问题：

```c
#include <stdio.h>
#include <stdlib.h>

int main(){
    char* sh = "/bin/sh";
    char* envp[] = {'aaaaa',NULL};
    char* argv[] = {"aaaaaaaa",NULL};

    execve(sh,argv,envp);
    
    return 0;

}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611908636463-8f889468-f06a-44d0-959d-279f7ac16829.png)

envp不合法，无法getshell。

> **<font style="color:#F5222D;">请注意：</font>**char* envp[] = {0,NULL};中的envp[0]是一个合法的指针
>
> char* envp[] = {"0",NULL};也是合法的
>
> char* envp[] = {123456789,NULL};不合法
>
> char* envp[] = {"123456789",NULL};合法
>
> **<font style="color:#F5222D;">因此指针的合法性不是看指针指向地址是否合法，而是看envp[]中的内容是否属于（const） </font>****<font style="color:#F5222D;">char* envp，</font>**
>
> **<font style="color:#F5222D;">argv和envp同理。</font>**
>

## 1、char* argv[] = {"aaaaaaaa",NULL};
```c
#include <stdio.h>
#include <stdlib.h>

int main(){
    char* sh = "/bin/sh";
    char* envp[] = {0,NULL};
    char* argv[] = {"aaaaaaaa",NULL};

    execve(sh,argv,envp);
    
    return 0;

}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611906535852-e7f93061-6f1f-4f94-a661-76ea11323d28.png)

可以getshell

## 2、char* argv[] = {NULL,'aabbbbb','aaaaaaaa'};
```c
#include <stdio.h>
#include <stdlib.h>

int main(){
    char* sh = "/bin/sh";
    char* envp[] = {0,NULL};
    char* argv[] = {NULL,'aabbbbb','aaaaaaaa'};

    execve(sh,argv,envp);
    
    return 0;

}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611907542207-d846e246-bb18-4db3-b560-67f1d030729a.png)

因为数组碰到NULL就结束，所以仍然满足条件。

##  3、char* argv[] = {'aabbbbb','aaaaaaaa',NULL};
```c
#include <stdio.h>
#include <stdlib.h>

int main(){
    char* sh = "/bin/sh";
    char* envp[] = {0,NULL};
    char* argv[] = {'aabbbbb','aaaaaaaa',NULL};

    execve(sh,argv,envp);
    
    return 0;

}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611908099127-5dac8240-0b00-41c9-baaf-58378301cc38.png)

argv[0]和argv[1]不是个合法指针（单引号），无法getshell

## 4、char* argv[] = {"aaaaaaaa",'aaaaa',NULL};
假设第一个合法，第二个不合法：

```c
#include <stdio.h>
#include <stdlib.h>

int main(){
    char* sh = "/bin/sh";
    char* envp[] = {0,NULL};
    char* argv[] = {"aaaaaaaa",'aaaaa',NULL};

    execve(sh,argv,envp);
    
    return 0;

}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611908287037-d55e2272-20a6-4b68-b0c2-2d4af7e5450e.png)

无法getshell。

## 5、char* argv[] = {"aaaaaaaa","bbb",NULL};
```c
#include <stdio.h>
#include <stdlib.h>

int main(){
    char* sh = "/bin/sh";
    char* envp[] = {0,NULL};
    char* argv[] = {"aaaaaaaa","bbb",NULL};

    execve(sh,argv,envp);
    
    return 0;

}
```

argv中的指针均合法，可以getshell。

# 总结
只要argv和envp最终是合法的指针数组，那么one_gadget就能成功。

> Taqini师傅：
>
> 对程序进行分析是要动静结合的，而one_gadget命令归根结底只是个静态分析工具，他提供的信息可能并不全面。在实际分析程序的过程中，你可能会发现有些不满足限制条件的one gadget居然也能成功getshell。这并不是玄学，请不要为此困惑，只不过是one_gadget命令还不够强大罢了2333
>
> 总而言之，静态分析出的限制条件只是提供了一个参考，并不意味着，不满足条件就攻击不成。
>

对one_gadget这个工具原理感兴趣的可以看：

> [https://xz.aliyun.com/t/2720](https://xz.aliyun.com/t/2720)
>

