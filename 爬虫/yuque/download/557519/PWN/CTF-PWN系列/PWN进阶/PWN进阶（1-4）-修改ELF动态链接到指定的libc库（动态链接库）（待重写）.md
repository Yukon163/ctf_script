> 参考资料：[https://bbs.pediy.com/thread-254868.htm](https://bbs.pediy.com/thread-254868.htm)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/173-jE_Dka_05kpJqtsbG-g](https://pan.baidu.com/s/173-jE_Dka_05kpJqtsbG-g)  密码: mufe
>
> --来自百度网盘超级会员V3的分享
>

# 引入
再做pwn题时，会遇到很多的libc版本，经常见到的有libc-2.23.so和libc-2.27.so。现在的pwn题基本上都是运行在LTS版本的，这些版本是长期的维护支持版，具有较强的稳定性，因此受到出题人的喜爱：

> [https://cn.ubuntu.com/download](https://cn.ubuntu.com/download)
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611130006042-6129f5d6-a197-44e8-910d-b0eb22988955.png)

不同版本的libc，其机制又不同，比如2.27版本的libc其引入了tcachebin机制，而2.23并没有此机制。因此如果靶机环境是2.27，那么你用2.23做题就无法得到正确payload。这个时候就需要修改程序的libc。 

接下来先介绍一下Linux中常用的动态链接库：

# Linux动态链接库
现在看一个普通程序运行时需要加载的运行库：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611130296266-12c72939-0693-4e91-9306-1ab44ca4d4e8.png)

## linux-vdso.so.1
> 较旧的版本名称为：linux-gate.so.1
>

VDSO的全称为Virtual Dynamically-linked Shared Object（虚拟动态链接共享对象），从它的名字就可以看出来

这是一个很有意思的东西；首先它是虚拟的，并不是实实在在的一个文件，其次每个ELF在动态链接加载时会使用这个库（共享）。

> VDSO将内核态的调用映射到用户态的地址空间中，使得调用开销更小, 路径更好。开销更小比较容易理解, 那么路径更好指的是什么呢? 拿x86下的系统调用举例, 传统的int 0x80有点慢, Intel和AMD分别实现了sysenter, sysexit和syscall, sysret, 即所谓的快速系统调用指令, 使用它们更快, 但是也带来了兼容性的问题. 于是Linux实现了vsyscall, 程序统一调用vsyscall, 具体的选择由内核来决定. 而vsyscall的实现就在VDSO中。
>

## libc.so.6
> 64位路径：/lib/x86_64-linux-gnu/libc.so.6
>
> 32位路径：/lib/i386-linux-gnu/libc.so.6
>

libc.so.6是程序运行时库glibc的软链接（可以简单的理解为Windows操作系统上的快捷方式），它其实是链接到同目录下的libc文件，比如：libc-2.23.so、libc-2.27.so等。系统几乎所有程序都依赖这个库。程序启动和运行时，是根据libc.so.6软链接找到glibc库，删除libc.so.6将导致系统的几乎所有程序不能工作。

当然对于pwn手来说这个东西是咱们的老朋友了，pwn掉题目时都要绕过它的机制来获取用户态的shell权限从而得到flag。简单来说就是绕过程序发生堆栈溢出时libc对其的检查机制。libc-2.??.so，其中??的版本越高，说明libc检查机制越多，越难绕过（新加入的tcache除外）。

> 当然，这东西也是C语言编写的，作为pwn手都要研究研究其源码。
>

## ld-linux-x86-64.so.2
> 32位版本名称及路径：/lib/ld-linux.so.2
>
> 64位版本名称及路径：/lib64/ld-linux-x86-64.so.2
>
> ld-linux-x86-64.so.2（ld-linux.so.X），其中X为一个数字，在不同的平台上名字也会不同。
>

ld-linux-x86-64.so.X是linux的动态加载器(dynamic loader)，当操作系统加载动态链接的应用程序时，它必须找到并加载它执行该应用程序所依赖的动态库。 在linux系统上，这份工作由ld-linux-x86-64.so.X处理。 你可以对一个应用程序或动态库使用ldd命令查看他依赖哪些库。当应用程序被加载到内存时，OS将控制权传递给ld-linux-x86-64.so.X，而不是应用程序的正常入口点。ld-linux-x86-64.so.X搜索并加载未解析的库，然后将控制权传递给应用程序的起始点。

**<font style="color:#F5222D;">当然，这个文件也是一个软链接：</font>**

**<font style="color:#F5222D;">/lib64/ld-linux-x86-64.so.2链接到</font>****<font style="color:#F5222D;">/lib/x86_64-linux-gnu/ld-2.27.so</font>**

# 直接修改LD_PERLOAD
libc和程序是通过动态连接器连接在一起的，其详细信息的信息写在程序的LD_RERLOAD中因此我们可以直接修改LD_PERLOAD为目标libc。但是，随意的修改LD_RERLOAD可能会使程序崩溃：

```python
段错误 (核心已转储)
```

因此修改动态链接库libc时，同样也需要修改ld-linux-x86-64.so.2。

当然也可以在编写pwn的exp文件时（pwntools），使用

```python
p=process(['/path/to/ld.so','./pwn'],env={'LD_PERLOAD':'/path/to/libc.so.6'})
替代原来的：
p=process("/path/to/libc.so.6")、p=process("/path/to/libc-2.??.so")
```

但是这种方式修改后gdb调试时，是没有libc相应调试信息的。 这里我们推荐另外一种方式，下载glibc-all-in-one并编译所需版本的glibc，利用patchelf工具修改程序的链接器和glibc。

# 使用patchelf修改
Linux环境

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611136258463-c29f4b42-92df-4874-a10f-ea88d1706cca.png)

## glibc-all-in-one的下载和使用
> github：[https://github.com/matrix1001/glibc-all-in-one](https://github.com/matrix1001/glibc-all-in-one)
>

```bash
git clone https://github.com/matrix1001/glibc-all-in-one.git 
cd glibc-all-in-one
```

> check supported packages. remember to run update_list at first.
>

根据github上的提示，先执行update_list：

```powershell
ubuntu@ubuntu:~/Desktop/glibc-all-in-one$ ./update_list 
[+] Common list has been save to "list"
[+] Old-release list has been save to "old_list"
ubuntu@ubuntu:~/Desktop/glibc-all-in-one$ cat list 
2.23-0ubuntu11.2_amd64
2.23-0ubuntu11.2_i386
2.23-0ubuntu3_amd64
2.23-0ubuntu3_i386
2.27-3ubuntu1.2_amd64
2.27-3ubuntu1.2_i386
2.27-3ubuntu1.4_amd64
2.27-3ubuntu1.4_i386
2.27-3ubuntu1_amd64
2.27-3ubuntu1_i386
2.31-0ubuntu9.1_amd64
2.31-0ubuntu9.1_i386
2.31-0ubuntu9.2_amd64
2.31-0ubuntu9.2_i386
2.31-0ubuntu9_amd64
2.31-0ubuntu9_i386
2.32-0ubuntu3.1_amd64
2.32-0ubuntu3.1_i386
2.32-0ubuntu3_amd64
2.32-0ubuntu3_i386
2.32-0ubuntu6_amd64
2.32-0ubuntu6_i386
ubuntu@ubuntu:~/Desktop/glibc-all-in-one$ cat old_list 
2.21-0ubuntu4.3_amd64
2.21-0ubuntu4.3_i386
2.21-0ubuntu4_amd64
2.21-0ubuntu4_i386
2.24-3ubuntu1_amd64
2.24-3ubuntu1_i386
2.24-3ubuntu2.2_amd64
2.24-3ubuntu2.2_i386
2.24-9ubuntu2.2_amd64
2.24-9ubuntu2.2_i386
2.24-9ubuntu2_amd64
2.24-9ubuntu2_i386
2.26-0ubuntu2.1_amd64
2.26-0ubuntu2.1_i386
2.26-0ubuntu2_amd64
2.26-0ubuntu2_i386
2.28-0ubuntu1_amd64
2.28-0ubuntu1_i386
2.29-0ubuntu2_amd64
2.29-0ubuntu2_i386
2.30-0ubuntu2.2_amd64
2.30-0ubuntu2.2_i386
2.30-0ubuntu2_amd64
2.30-0ubuntu2_i386
ubuntu@ubuntu:~/Desktop/glibc-all-in-one$ 
```

> Note: use download for packages in the list; use download_old for packages in the old_list.
>

注意，使用download下载list中的包，使用download_old下载old_list中的包。

> needed glibc not in my list ?
>
> you can download the debs on your own, then use `extract`
>

没有在list文件中没有发现所需要的glibc版本？你可以自己下载debs文件，然后解压缩：

```powershell
./extract ~/libc6_2.26-0ubuntu2_i386.deb /tmp/test
./extract ~/libc6-dbg_2.26-0ubuntu2_i386.deb /tmp/test_dbg
```

当然如果你所需的glibc版本只有源码，可以使用此工具进行编译：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611137584141-831fe16d-ccd5-46fe-ba0f-1cd04f7664c1.png)

> 不翻译了，主要是懒
>

## 下载所需的glibc
由于我的环境是有tcachebin机制的glibc-2.27，为凸显实验结果，这里选择下载没有tcachebin机制的glibc-2.23，这里我选择2.23-0ubuntu11.2_amd64。

执行命令：

```powershell
ubuntu@ubuntu:~/Desktop/glibc-all-in-one$ ./download 2.23-0ubuntu11.2_amd64
Getting 2.23-0ubuntu11.2_amd64
  -> Location: https://mirror.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc/libc6_2.23-0ubuntu11.2_amd64.deb
  -> Downloading libc binary package
  -> Extracting libc binary package
  -> Package saved to libs/2.23-0ubuntu11.2_amd64
  -> Location: https://mirror.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc/libc6-dbg_2.23-0ubuntu11.2_amd64.deb
  -> Downloading libc debug package
  -> Extracting libc debug package
  -> Package saved to libs/2.23-0ubuntu11.2_amd64/.debug
ubuntu@ubuntu:~/Desktop/glibc-all-in-one$ 
```

> 我已经换源为清华源。如果原来的源无法链接或下载太慢，建议挂梯子或换源。
>

此时在目录下会生成libs文件夹，里面就是所需的glibc：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611138060529-e72bae18-2f97-4a38-9be3-ff317e1385f6.png)

# patchelf下载和安装使用
> github：[https://github.com/NixOS/patchelf](https://github.com/NixOS/patchelf)
>

下载并编译安装工具：

```powershell
git clone https://github.com/NixOS/patchelf.git
cd patchelf
./bootstrap.sh
./configure
make
make check
sudo make install
```

这里只介绍修改elf动态链接库的办法，工具还有其他的用法，这里不再介绍，感兴趣的可以去github看readme.md

# 开始修改
为了方便演示，先写一个demo并编译它：

```c
#include<stdio.h>
#include<stdlib.h>
int main(){
	sleep(0);
	void *p[10]={0};
	for(int i = 0 ;i<10;i++){
		p[i]=malloc(0x10);
	}
	sleep(0);
	for(int j = 0;j<10;j++){
		free(p[j]);
		p[j]=NULL;
	}
	sleep(0);
	return 0;
}
```

> gcc -g -fno-stack-protector -z execstack -no-pie -z norelro glibc_test.c -o glibc_test
>
> ubuntu@ubuntu:~/Desktop/glibc_test$ checksec --file=glibc_test
>
> [*] '/home/ubuntu/Desktop/glibc_test/glibc_test'
>
>     Arch:     amd64-64-little
>
>     RELRO:    No RELRO
>
>     Stack:    No canary found
>
>     NX:       NX disabled
>
>     PIE:      No PIE (0x400000)
>
>     RWX:      Has RWX segments
>
> sleep(0);的作用为“方便下断点”
>

gdb程序，对代码的第14行下断点，开始运行程序：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611140710842-4507f401-51cc-473c-b538-81ed642ab15d.png)

可以看到tcachebin上已经被填满，开始对原程序进行patch

> 备份一个名为glibc_test_backup的副本
>

看一下程序的加载库：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611140905204-d2fb00ae-f97e-47ba-a785-1ee61567f14c.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611142044505-e45988a5-59f7-4538-aa25-1cacaee8d84c.png)

linux-vdso.so.1是一个虚拟文件，因此我们不需要去修改它，主要修改后两个文件。

由于安装了patchelf，所以可以在任意的目录去调用它：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611141119485-058b399f-ddb4-4a4b-89dc-93c4d77ddf43.png)

将刚刚下载的libc-2.23.so和ld-2.23.so移到glibc_test待patch的文件夹下：

> 这里下载的ld-linux-x86-64.so.2是链接到本文件夹下的ld-2.23.so
>

首先patch程序链接到ld-2.23.so：

```c
patchelf --set-interpreter ./ld-2.23.so ./glibc_test
```

然后将程序链接到libc-2.23.so：

```c
patchelf --replace-needed libc.so.6 ./libc-2.23.so ./glibc_test
```

ldd看一下效果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611143439762-ef221430-e932-42b2-98f6-3be3e85f34cf.png)

gdb看一下效果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611144132931-c4ed1cdb-da7a-4dec-a186-bb7113a3918f.png)

没有在堆区中没有发现tcache<font style="color:#333333;">_perthread_struct，说明修改成功</font>

当然，和pwndbg强制加载libc一样，**<font style="color:#F5222D;">修改之后的程序无法查看heap和bin</font>**，但是我们可以从内存看出程序已经被修改成功。**<font style="color:#F5222D;">修改之后的程序不能缺少任何一个加载库，并且库都得在修改时的目录下面</font>**：

> 或者是将本机上的两个库文件移动到ELF文件夹下同样也可以执行。
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611143738614-3b540e1b-902f-434c-b30b-718961bc344a.png)

> 上图是缺少两个库文件的状况。
>

# 在 gdb 中加载 debug 文件/符号表（补充）
难道真的没有办法在修改elf的库文件之后在pwndbg中使用heap和bin命令吗？

其实使用heap和bin命令实际上依赖的是libc的符号表文件，来看一下之前的一张图：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611196742571-69a97e32-1091-4a69-a100-66003216df04.png)

### <font style="background-color:#FEFEFE;">通过 gdb 命令 set debug-file-directory directories</font>
```powershell
pwndbg> bin
bins: This command only works with libc debug symbols.
They can probably be installed via the package manager of your choice.
See also: https://sourceware.org/gdb/onlinedocs/gdb/Separate-Debug-Files.html

E.g. on Ubuntu/Debian you might need to do the following steps (for 64-bit and 32-bit binaries):
sudo apt-get install libc6-dbg
sudo dpkg --add-architecture i386
sudo apt-get install libc-dbg:i386
```

从上面的提示可以看到bin/heap命令都是依赖符号库。下面的内容又提示了可以使用：

sudo apt-get install libc6-dbg

这个命令来解决，但是由于我们将程序的库文件已经修改，执行上面的命令之后其实是安装了本机的libc的符号文件，对调试这个程序没有帮助。

可以到[https://mirrors.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc/](https://mirrors.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc/)下载对应的glibc符号文件。

比如：使用glibc-all-in-one下载的是libc6_2.23-0ubuntu11.2_amd64.deb，那么就去网站上下载libc6-dbg_2.23-0ubuntu11.2_amd64.deb文件，下载完成之后解压，在使用pwndbg调试时导入即可：

```powershell
set debug-file-directory $directories
```

> $directories是解压之后的目录。
>

导入之后输入r重新调试程序即可看到效果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611197618248-1cf9eb11-2b53-455f-b563-0266ce5edc52.png)

### <font style="background-color:#FEFEFE;">将 debug 文件放入 ".debug" 文件夹</font>
<font style="background-color:#FEFEFE;">在放置 libc 的目录下新建 ".debug"文件夹（修改之后自动隐藏），将 debug 文件放入其中即可。</font>

> <font style="background-color:#FEFEFE;">2021.04.08补充：</font>
>
> 当时写文章的时候没有写清楚，这里的debug文件指的是我们使用glib-all-in-one
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611198428850-9b879895-15ab-4a1e-9719-c36c6370aa49.png)



![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611198488498-520f2d46-3d77-463c-b52b-9e52f36202cc.png)





