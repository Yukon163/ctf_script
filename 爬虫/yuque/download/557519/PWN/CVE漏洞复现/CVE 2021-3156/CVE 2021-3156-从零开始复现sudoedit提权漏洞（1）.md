> 附件：
>
> 链接: [https://pan.baidu.com/s/1Feluk-f9T4kUPCvSLuA-sQ](https://pan.baidu.com/s/1Feluk-f9T4kUPCvSLuA-sQ)  密码: td5f
>
> --来自百度网盘超级会员V3的分享
>
> 附件中的虚拟机密码和root权限均为ubuntu
>
> 虚拟机环境已经搭建好，可以直接下载使用。
>

# 前言
作者第一次研究并复现高危漏洞，也参考了不少资料，花了十分大的精力，但是难免有分析错误的地方，欢迎在评论区留言指正。

# 简介
2021年01月26日，sudo发布安全通告，修复了一个类Unix操作系统中sudo命令基于堆的缓冲区溢出漏洞（CVE-2021-3156，该漏洞被命名为“Baron Samedit”），任何本地用户（普通用户和系统用户，sudoer和非sudoers）都可以利用此漏洞，而无需进行身份验证，攻击者不需要知道用户的密码。成功利用此漏洞提权获得root权限。

# 影响版本
- sudo:sudo: 1.8.2 - 1.8.31p2

- sudo:sudo: 1.9.0 - 1.9.5p1

# 漏洞检测
可以使用如下方法进行对漏洞进行检测：

以非root用户登录系统，并使用命令sudoedit -s /

- 如果响应一个以sudoedit:开头的报错，那么表明存在漏洞。

- 如果响应一个以usage:开头的报错，那么表明不存在漏洞或漏洞补丁已经生效。

# 漏洞成因
sudoers.c源文件中的set_cmnd()函数在拷贝参数时，由于错误处理'\'（未进行转义），造成堆写越界的问题，攻击者可通过控制参数和环境变量向特定堆地址之后的内存中写入任意长度的数据，其中包括'\0'。

# 复现准备
> 本次复现所需要的虚拟机镜像和其他资料将会在附件中提供
>

下载附件中所需要的虚拟机镜像，然后进行安装。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612496411820-534876d8-cb8c-4f86-aab6-980c28a23c1d.png)

> 为了加快安装速度和避免网络系统更新的影响，请在安装系统时关闭虚拟机网络
>

在安装过程中，学习一下复现漏洞的前置知识。

# 前置知识
## 用户、用户组
Linux是多用户的操作系统，每个用户之间可以有相同或不同的权限，他们的权限都来自root用户的授权。为了使授权更加的简便，Linux引入了用户组的概念。简而言之，用户组将权限相同的用户划分为一个小组，在这个小组中每个人都有相同的权限；但是不同用户之间的权限可能存在差异，比如A用户需要read权限，而B用户需要read权限之外还需要write权限，因此Linux中的用户和用户组并不是简单的一对一关系，它可以存在4种对应关系：

> [http://c.biancheng.net/view/3038.html](http://c.biancheng.net/view/3038.html)
>

+ 一对一：一个用户可以存在一个组中，是组中的唯一成员；
+ 一对多：一个用户可以存在多个用户组中，此用户具有这多个组的共同权限；
+ 多对一：多个用户可以存在一个组中，这些用户具有和组相同的权限；
+ 多对多：多个用户可以存在多个组中，也就是以上 3 种关系的扩展。

<font style="color:#444444;">用户和组之间的关系可以如下图片来表示：</font>

![](https://cdn.nlark.com/yuque/0/2021/gif/574026/1612506252731-81cd35cb-23f0-4110-8fb2-f5a3df54b5b9.gif)

## RUID、EUID、SUID、RGID、EGID、SGID
我们需要了解一下这几个东西，因为这玩意儿会牵扯到之后的Linux提权。

> UID：User ID 用户ID，GID：Group ID 组ID
>

### 真实用户ID
真实用户ID（Real UID,即RUID）与真实用户组ID（Real GID，即RGID）用于标识我是谁，也就是登录用户的UID和GID，加入系统以Cyberangel登录，在Linux运行的所有的命令的实际用户ID都是Cyberangel的UID，实际用户组ID都是Cyberangel的GID（可以用id命令查看）。 

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612505241769-24d4bdeb-9ae6-41cc-81a0-fc9701aeacf8.png)

### 有效用户ID
有效用户ID（Effective UID，即EUID）与有效用户组ID（Effective Group ID，即EGID）**<font style="color:#F5222D;">在创建与访问文件的时候发挥作用，</font>**通过进程的有效用户ID和有效用户组ID来决定进程对系统资源的访问权限，具体来说，创建文件时，系统内核将**根据创建文件的进程的EUID与EGID设定文件的所有者/组属性**，而在访问文件时，内核亦根**据访问进程的EUID与EGID决定其能否访问文件**。**<font style="color:#F5222D;">一般情况下</font>**，有效用户ID（EUID）等于实际用户ID（RUID）。

### 暂存用户ID
暂存用户ID（Saved UID，即SUID）是针对文件而言的，用于表示对外权限的开放。**<font style="color:#F5222D;">SUID属性只能运用在可执行文件上，当用户执行该执行文件时，会临时拥有该执行文件所有者的权限，</font>****<font style="color:#F5222D;">本权限仅在执行该二进制可执行文件的过程中有效</font>****<font style="color:#F5222D;">（这一点对Linux系统安全极为重要，后面将会举一个例子）</font>**

如果可执行文件所有者权限的第三位是一个小写的“s”就表明该执行文件拥有SUID属性。如果在浏览文件时，发现所有者权限的第三位是一个大写的“S”则表明该文件的SUID属性无效，比如将SUID属性给一个没有执行权限的文件。下面是passwd可执行文件的权限情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612508342999-43cd5b5c-ecdf-476f-afdd-f164b4fd289f.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612508511569-2c61faaf-e6de-41db-b746-a7cdb5b0149f.png)

> 当然文件类型还有其他的：
>
> p表示命名管道文件     d表示目录文件     <font style="background-color:transparent;">l表示符号连接文件 </font>
>
> -表示普通文件     <font style="background-color:transparent;">s表示socket文件     c表示字符设备文件     b表示块设备文件</font>
>
> <font style="background-color:transparent;"></font>
>
> r表示可读；w表示可写；x表示可执行；没有权限的位置用-表示
>

当s标志出现在用户组的 x 权限时称为 SGID。SGID 的特点与 SUID 相同，我们通过 /usr/bin/mlocate 程序来演示其用法，其权限如下图所示：

> [https://www.cnblogs.com/sparkdev/p/9651622.html](https://www.cnblogs.com/sparkdev/p/9651622.html)
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612509162328-5ea6b0bf-6f33-4fa9-8e77-63a05b8b2d53.png)

> mlocate 程序通过查询数据库文件 /var/lib/mlocate/mlocate.db 实现快速的文件查找。
>

很明显，它被设置了 SGID 权限，下面是数据库文件 /var/lib/mlocate/mlocate.db 的权限信息：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612509579415-85b27c5f-f763-457d-b3e3-154a1216aecd.png)

当普通用户tester执行mlocate命令时，tester就会获得用户组mlocate的执行权限，又由于用户组mlocate对 mlocate.db具有读权限，所以tester就可以读取mlocate.db 了。这个过程如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612509799477-478f231b-eeb3-4a02-81f0-4466e34e756f.png)

除二进制程序外，SGID 也可以用在目录上。当一个目录设置了 SGID 权限后，它具有如下功能：

+ 用户若对此目录具有 r 和 x 权限，该用户能够进入该目录
+ 用户在此目录下的有效用户组将变成该目录的用户组
+ 若用户在此目录下拥有 w 权限，则用户所创建的新文件的用户组与该目录的用户组相同

> 注意：
>
> 当对文件的SUID位设置后，则有效用户ID等于文件的所有者的UID，而不是实际用户ID（RUID）；同样，如果设置了文件的SGID位，则有效用户组ID（EUID）等于文件所有者的GID，而不是实际用户组ID（RUID）。
>

## sudo(su)权限提升
一般情况下，在安装或卸载一些软件时会报出“permission denied”，其意义为“权限被拒绝”，因此我们需要将普通用户权限提升至管理员权限才能正常安装或卸载。

普通用户“Cyberangel”中，在桌面上右击打开终端，查看环境变量：

> 只摘取了一些与“用户、组、ID”相关的环境变量
>

```bash
cyberangel@ubuntu:~$ env
USERNAME=cyberangel
USER=cyberangel					#当前登录的用户
PWD=/home/cyberangel    #表示终端中的当前路径
HOME=/home/cyberangel		#当前用户主目录
SHELL=/bin/bash 				#当前用户的Shell种类
LOGNAME=cyberangel			#是指当前用户的登录名
cyberangel@ubuntu:~$ whoami    #显示的是当前用户下的用户名
cyberangel
cyberangel@ubuntu:~$ who       #显示当前真正登录系统中的用户（不会显示那些用su命令切换用户的登录者）
cyberangel :1           2021-02-01 21:58 (:1)
cyberangel@ubuntu:~$ id
uid=1000(cyberangel) gid=1000(cyberangel) groups=1000(cyberangel),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),116(lpadmin),126(sambashare)
cyberangel@ubuntu:~$ 
```

> who 显示的是实际用户的用户名，即用户登陆的时候的用户ID，此命令相当于who -m。whoami显示的是有效用户ID（操作用户）.
>

### su root（su）
> su：superuser_<u></u>_
>

su name的含义是切换用户到name账户，如果后面不加账户时系统默认为切换到root账户，密码也为root密码，登陆后**<font style="color:#F5222D;">没有时间限制</font>**。但是在ubuntu中默认禁用root登陆，所以需要先设置一下密码才可登陆（执行sudo passwd root，然后给其设定自己的密码即可）。

切换之后一些重要的环境变量如下：

```bash
cyberangel@ubuntu:~$ su root
Password: 
root@ubuntu:/home/cyberangel# env
USERNAME=cyberangel 
USER=root                #变更为root
PWD=/home/cyberangel
HOME=/root							 #变更为root
SHELL=/bin/bash
LOGNAME=root						 #变更为root
root@ubuntu:/home/cyberangel# whoami          #变更为root 
root
root@ubuntu:/home/cyberangel# who
cyberangel :1           2021-02-01 21:58 (:1)
root@ubuntu:/home/cyberangel# id
uid=0(root) gid=0(root) groups=0(root)        #变更为root
root@ubuntu:/home/cyberangel# 
```

和前面对比可以知道，在使用su root变更为root用户之后，home目录将变更为/root，用户id和组全部变为root，但是当前所在的目录并没有变化。

> 当然su root和su都表示与root建立一个链接，通过root执行命令，
>

### sudo -i
sudo -i表示以root身份登陆，设置这条命令是为了频繁的执行某些只有超级用户才能执行的命令而不用每次输入密码。提示输入密码时该密码为当前账户的密码（当然root权限是不是谁都能登陆的，要求执行该命令的用户必须在sudoers中才可以）。**<font style="color:#F5222D;">提权之后没有时间限制</font>**。想退回普通账户时可以执行“exit”或“logout” （su root同理）。

```bash
cyberangel@ubuntu:~$ sudo -i
Password: 
root@ubuntu:~# env
USERNAME=root							#变更为root
USER=root    							#变更为root
PWD=/root    							#变更为root
HOME=/root   							#变更为root
SHELL=/bin/bash
LOGNAME=root   		   			#变更为root
root@ubuntu:~# whoami
root
root@ubuntu:~# who
cyberangel :1           2021-02-01 21:58 (:1)
root@ubuntu:~# id
uid=0(root) gid=0(root) groups=0(root)       			 #变更为root
root@ubuntu:~# 
```

从上面可以看出，包括PWD之内的所有环境变量都变为了root。

### sudo su
```bash
cyberangel@ubuntu:~$ sudo su
Password: 
root@ubuntu:/home/cyberangel# env
USERNAME=root										#变更为root
USER=root												#变更为root
PWD=/home/cyberangel
HOME=/root											#变更为root
SHELL=/bin/bash
LOGNAME=root										#变更为root
root@ubuntu:/home/cyberangel# whoami
root
root@ubuntu:/home/cyberangel# who
cyberangel :1           2021-02-01 21:58 (:1)
root@ubuntu:/home/cyberangel# id
uid=0(root) gid=0(root) groups=0(root)
root@ubuntu:/home/cyberangel# 
```

sudo su表示运行sudo命令给su命令提权，运行su命令。 要求执行该命令的用户**<font style="color:#F5222D;">必须在sudoers中才可以完成提权。</font>**与之前的sudo -i不同的是，在完成提权之后pwd不会改变为/root。

# 环境配置
看到这里，系统应该安装完成了，将附件中的linux.iso下载下来，并在虚拟机中挂载镜像，以安装vmtools。

解压iso中的tar.gz到Deskop，然后安装：

```bash
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

cyberangel@ubuntu:~/Desktop/VMwareTools-10.3.22-15902021/vmtools-distrib$ sudo ./vmware-install.pl 
[sudo] password for cyberangel: #输入安装时设置的密码
open-vm-tools packages are available from the OS vendor and VMware recommends 
using open-vm-tools packages. See http://kb.vmware.com/kb/2073803 for more 
information.
Do you still want to proceed with this installation? [no] y #输入y
......（一路回车）
#安装完成之后在终端中输入reboot重启系统。
```

重启之后，打开网络先校准下时间，然后安装几个常用的工具，在终端执行依次下列命令：

> sudo apt update #更新源
>
> sudo apt install vim #安装编辑器vim
>
> sudo apt install git #安装git clone
>
> sudo apt install gcc #安装gcc
>
> sudo apt install cmake #安装cmake
>

```bash
#安装pwndbg   #pwndbg我习惯了，当然也可以安装其他的gdb调试器
cd Desktop
git clone https://github.com/pwndbg/pwndbg
cd pwndbg
sudo ./setup.sh #为cyberangel用户安装pwndbg
```

然后试一下：

```bash
cyberangel@ubuntu:~/Desktop/pwndbg$ gdb
......（内容略）
pwndbg: loaded 187 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
pwndbg> 
```

然后提权为root用户安装：

```bash
cyberangel@ubuntu:~/Desktop/pwndbg$ sudo su
root@ubuntu:/home/cyberangel/Desktop/pwndbg# ./setup.sh 
......（内容略）
root@ubuntu:/home/cyberangel/Desktop/pwndbg# gdb
......（内容略）
pwndbg: loaded 187 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
pwndbg> 
```

回到普通用户，看一下sudo版本：

```bash
cyberangel@ubuntu:~/Desktop/pwndbg$ sudo -V
Sudo version 1.8.21p2
Sudoers policy plugin version 1.8.21p2
Sudoers file grammar version 46
Sudoers I/O plugin version 1.8.21p2
cyberangel@ubuntu:~/Desktop/pwndbg$ 
```

# 简单的sudo提权demo
安装完成后看一个由于SUID而引起的提权的demo，源码如下：

```c
#include<stdlib.h>
#include<unistd.h>
#include<stdio.h>
int main(){
    system("id");
    system("whoami");
    printf("##################################################");
    setgid(0);
    system("id");
    system("whoami");
    printf("##################################################");
    setuid(0);
    system("id");
    system("whoami");
    printf("##################################################");
    system("/bin/sh");
    return 0;
}
```

> 对其进行编译：gcc -g demo.c -o demo
>

编译之后尝试运行一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612590788715-d12f0752-2074-419a-a1ce-0f4a222e1f4a.png)

看来并没有提升到root权限，假如说对其进行设置SUID标志位呢？

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612518161821-2d9b5141-6709-4e38-b852-40474389a1e2.png)

```bash
cyberangel@ubuntu:~/Desktop/sudo_demo$ sudo chown root:root demo #更改可执行文件的用户和组

We trust you have received the usual lecture from the local System
Administrator. It usually boils down to these three things:

    #1) Respect the privacy of others.
    #2) Think before you type.
    #3) With great power comes great responsibility.

Password: 
cyberangel@ubuntu:~/Desktop/sudo_demo$sudo chmod u+s demo #赋予SUID标志位
```

更改时会出现警告信息，忽略它，完成后查看文件权限：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612590869382-f1294690-d9ef-439f-936b-844d7ebfeb72.png)

现在文件属于root用户和组，执行后无需输入密码就可提权到root权限：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612590938730-9a7264fe-2ff1-4865-a172-2bd8194afc6c.png)

由环境变量可知，效果和su root是相同的。值得注意的是代码中的setgid(0)和setuid(0)，这两个函数的原型如下：

> [https://blog.csdn.net/qq_41453285/article/details/103074879](https://blog.csdn.net/qq_41453285/article/details/103074879)
>

```c
#include <unistd.h>
int setuid(uid_t uid);
int setgid(gid_ gid);
```

从man文档中可以了解到这两个函数是用来更改“用户ID和组ID的（UID和GID）”，若成功返回0；失败返回-1。

**<font style="color:#F5222D;">需要注意的是实际的用户ID只能由root权限更改，另外，更改ID的规则如下：</font>**

> 下面我们以更改用户ID为例（关于用户ID我们所说明的一切也适用于组ID）：
>
> ①若进程具有超级用户特权，则setuid函数将实际用户ID、有效用户ID、保存的设置用户ID设置为uid
>
> ②若进程没有超级用户特权，则uid等于实际用户ID或保存的设置用户ID，则setuid只将有效用户ID设置为uid。不更改实际用户ID和保存的设置用户ID
>
> ③如果上面两个条件都不满足，则errno设置为EPERM，并返回-1
>

**_POSIX_SAVED_IDS常量：如果没有定义_POSIX_SAVED_IDS常量，则上面那些设置规则都无效**

可以在编译时测试该常量，或者在运行时通过sysconf函数来判断是否定义该常量，这里就不再详细展开了，感兴趣的可以去问度娘。

**<font style="color:#3399EA;">再来补充一下前面的内容</font>**（关于用户ID的说明也适用于组ID）：

+ **<font style="color:#86CA5E;">实际用户ID：</font>**
    - **<font style="color:#F5222D;">只有</font>****超级用户进程**可以更改实际用户ID
    - 通常，实际用户ID是在用户登录时，**由login程序设置的**。而且绝不会改变它。因为login是一个超级用户进程，当它调用setuid时，设置所有3个用户ID
+ **<font style="color:#86CA5E;">有效用户ID：</font>**
    - **仅当对程序文件设置了设置用户ID位时**，exec函数才设置有效用户ID；**如果设置用户ID位没有设置**，exec函数不会改变有效用户ID，而谁维持其现有值
    - **任何时候都可以调用setuid**，将有效用户ID设置为实际用户ID或保存的设置用户ID
    - 自然地，不能将有效用户ID设置为任意随机值
+ **<font style="color:#86CA5E;">保存的设置用户ID：</font>**
    - 保存的设置用户ID是**由exec复制有效用户ID而得到的**
    - 如果设置了文件的设置用户ID位，则在exec根据文件的用户ID设置了进程的有效用户ID以后，**这个副本就被保存起来了**

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612582920135-dfc2a463-5fa9-43b7-8d25-176a208a72da.png)

回头看一下写的提权程序：

首先这个可执行文件的其他用户权限是r-x，这意味着这个文件普通用户cyberangel也可以执行；当程序开始执行时，由于程序的拥有者的UID和GID均为root，因此在执行setuid和setgid后就可以拥有root权限，详细执行步骤如下图所示：

> **<font style="color:#F5222D;">由于文件有SUID标志位，当用户执行时，会临时拥有该执行文件所有者（root）的权限。</font>**
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612590938730-9a7264fe-2ff1-4865-a172-2bd8194afc6c.png)

看完这个demo之后，接下来开始分析提权漏洞CVE 2021-3156

# CVE 2021-3156
## 准备工作
先看一下测试使用的poc：

> sudoedit -s '\' aabbccddeeffgghhiiggkkllmmnn
>

执行一下，看能否引发溢出：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612591934140-21db0da2-9519-4c22-914f-7d11e3b2ff1d.png)

成功溢出，但是由于原来的sudo没有debug环境，因此去[https://www.sudo.ws/download.html](https://www.sudo.ws/download.html)下载对应的sudo安装包：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612517028318-f5f678ae-6eaa-4f00-beaa-e16a64671191.png)

然后解压，debug安装：

```bash
tar xf sudo-1.8.21p2.tar.gz
cd sudo-1.8.21p2.tar.gz/
mkdir build
cd build/
../configure --enable-env-debug #启用debug环境
make -j
sudo make install
```

安装完成之后，开始进行调试：

> 调试之前先进入root用户，并关闭系统地址随机化：
>
> _echo 0 > /proc/sys/kernel/randomize_va_space（重启之后需重新执行此命令）_
>

---

调试的命令为gdb --args sudoedit -s '\' aabbccddeeffgghhiiggkkllmmnn

> 注意，调试的poc要能溢出触发raise，否则无法完成后面的调试步骤
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612592552865-0c7566f1-cfc2-4420-b1c7-9f2449f43452.png)

引入源码并切换目录：

> dir /home/cyberangel/Desktop/sudo-1.8.21p2/plugins/sudoers
>
> cd /home/cyberangel/Desktop/sudo-1.8.21p2/plugins/sudoers
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612595151089-b26ddf1c-ebcf-4df6-9160-581a08e0b0e8.png)

<font style="background-color:transparent;">由于sudo的代码是动态加载的，因此在对代码下断点之前先运行程序触发异常，输入r：</font>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612592907286-34f9a873-80a1-424a-a2f2-c9ff2869cd10.png)

<font style="background-color:transparent;">现在触发了异常，就可以对代码下断点了。</font>

## sudoedit及环境变量简介
首先来看一下sudoedit这个命令：

平常在修改文件时我用的最多的就是vim，sudoedit和vim的功能大致类似，但是和vim又有些许的不同，sudoedit这个命令是等价于sudo -e的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612593919496-92a490ae-9787-463c-b84b-473d8b6d3247.png)

以下是这个命令编辑文件的基本用法：

```bash
sudoedit /path/to/file1 /path/to/file2 ...
# 或是：
sudo -e /path/to/file1 /path/to/file2 ...
#sudoedit可以同时编辑多个文件
```

> <font style="background-color:transparent;">感兴趣的可以上网搜搜sudoedit和vim的区别，这里不在多说。</font>
>

sudo有许多的命令选项，其中溢出的问题就发生在-s身上：

| -s [command] | 如果设置了shell环境变量，则"-s"选项运行由shell环境变量指定的shell，或者运行密码数据库中指定的shell。如果指定了命令，则通过shell的"-c"选项将命令传递给shell执行。如果没有指定命令，则执行交互式shell。 |
| :--- | :--- |


这里牵扯到Linux的环境变量，之前说过可以使用env命令进行打印。

这里再补充一下，可以使用“env -i NAME1=VALUE1 NAME2=VALUE2 <command-line>”指定环境变量执行命令行<command-line>，例如：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612594506114-335711e6-cb73-4715-94bf-1f373b1673a5.png)

> 环境变量的格式不一定为NAME1=VALUE1，但是在bash中格式必须为这个，否则会报错：
>
> ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612594689007-ce235687-50be-488e-8187-ab8c42acb872.png)
>
> 这个问题可以看：[https://www.yuque.com/cyberangel/rg9gdm/gbyagk](https://www.yuque.com/cyberangel/rg9gdm/gbyagk)
>

## 漏洞函数分析
引发溢出的函数在“/sudo-1.8.21p2/build/plugins/sudoers/sudoers.c”中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612595357319-43484a12-55cc-4730-86fa-a353f5a80535.png)

溢出关键代码如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612595449534-750613e5-dda5-4587-9898-6774a001b838.png)

由于不了解sudo代码，所以决定直接动态调试以查看变量的含义，触发异常后引入源码对sudoers.c的第852行下断点：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612595739777-6f9fa2e4-c279-4011-ad01-56911f93da90.png)

输入r以断下程序：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612595781449-9979b1b1-8446-4db4-9814-4e1c1dd4ebea.png)

看一下if语句中这三个变量分别是什么：

```c
if (ISSET(sudo_mode, MODE_SHELL|MODE_LOGIN_SHELL)) {
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612596039236-98ab1be6-5f6a-4485-89a4-8edb0d22a7b3.png)

内存中并没有MODE_SHELL和MODE_LOGIN_SHELL的信息，只能知道sudo_mode的值是"\002"，到这里无法获得任何信息，那就看一下函数的调用栈：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612596338953-fb5254c9-c1dc-484f-bb2c-8aa6cfe9f78d.png)

从中可以知道，main函数在/sudo-1.8.21p2/src/sudo.c中，来看一下它。

### main（/src/sudo.c）
sudo.c中我们可以找到sudo_mode的信息，但是仍然不知道其含义。

```c
81 :static int sudo_mode; #定义sudo_mode变量
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612596641339-9e76c64a-a593-4b45-bcc4-c1f3020e04ac.png)

### parse_args.c（/src/parse_args.c）
sudo_mode是函数parse_args的返回值，这个函数定义在：

/sudo-1.8.21p2/src/parse_args.c中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612597389782-f0d9eb03-332d-4f0d-91ff-fed7a4f3911e.png)

大致看了一下，这个函数主要定义了一些sudo的选项，同时根据输入的命令和参数去设置一些标志位，由于我们执行的命令为sudoedit -s，所以执行完这段代码后mode=MODE_EDIT，flag=MODE_SHELL：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612598187358-cbd485ef-6c7c-4cb0-917c-52824d6aa4c0.png)

其中MODE_EDIT和MODE_SHELL是宏定义，在sudo.h中可以找到：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612598092614-a9c35671-8216-4ddf-aafc-c9e15b6438af.png)

**<font style="color:#F5222D;">因此要执行到漏洞代码，MODE_SHELL必须已设置，也就是poc中必须要有参数-s才有可能发生溢出。</font>**

parse_args的返回值定义在这里：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612598487396-648a0d32-b6e1-4815-a764-3ccf8db21e8a.png)

从上面看出parse_args的返回值是由debug_return_int函数决定的，其中的参数为mode=MODE_EDIT，flag=MODE_SHELL；debug_return_int函数就不再看了，因为我们只是根据parse_args的返回值sudo

_mode来反推这几个宏定义的含义，不需要彻底的了解其原理。

**<font style="color:#F5222D;">总结：</font>****<font style="color:#F5222D;">sudo_mode是由</font>****<font style="color:#F5222D;">MODE_EDIT和</font>****<font style="color:#F5222D;">MODE_SHELL决定的，具有唯一性。</font>**

### sudoers.c（set_cmnd）
回头继续看sudoers.c中的static int set_cmnd(void)：

```c
	/* set user_args */
	if (NewArgc > 1) {
	    char *to, *from, **av;
	    size_t size, n;

	    /* Alloc and build up user_args. */
	    for (size = 0, av = NewArgv + 1; *av; av++)
		size += strlen(*av) + 1;
	    if (size == 0 || (user_args = malloc(size)) == NULL) {
		sudo_warnx(U_("%s: %s"), __func__, U_("unable to allocate memory"));
		debug_return_int(-1);
	    }
	    if (ISSET(sudo_mode, MODE_SHELL|MODE_LOGIN_SHELL)) {
		/*
		 * When running a command via a shell, the sudo front-end
		 * escapes potential meta chars.  We unescape non-spaces
		 * for sudoers matching and logging purposes.
		 */
		for (to = user_args, av = NewArgv + 1; (from = *av); av++) {
		    while (*from) {
			if (from[0] == '\\' && !isspace((unsigned char)from[1]))
			    from++;
			*to++ = *from++;
		    }
		    *to++ = ' ';
		}
		*--to = '\0';
	    } else {
		for (to = user_args, av = NewArgv + 1; *av; av++) {
		    n = strlcpy(to, *av, size - (to - user_args));
		    if (n >= size - (to - user_args)) {
			sudo_warnx(U_("internal error, %s overflow"), __func__);
			debug_return_int(-1);
		    }
		    to += n;
		    *to++ = ' ';
		}
		*--to = '\0';
	    }
	}
```

将断点下载第842行，重新调试来看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612601974034-d8ff87ee-5b77-44cc-9064-179ea593ec31.png)

从代码的注释可以知道，这个第一个for循环和接下来的if语句是用来设置user_args的值，对第849行下断点，继续调试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612602310635-24292065-3920-4e67-888a-0cda8decfc69.png)

看一下此时的值：

```c
pwndbg> x/gx &NewArgc
0x7ffff61b4dd0 <NewArgc>:	0x0000000000000003
pwndbg> x/6gx &NewArgv
0x7ffff61b4cc8 <NewArgv>:	0x000055555578e258	0x0000000000020002
0x7ffff61b4cd8:	0x0000000000000000	0x000055555577f0f8
0x7ffff61b4ce8 <sudo_user+8>:	0x000055555577f0f8	0x0000000000000000
pwndbg> x/16gx &size
Address requested for identifier "size" which is in register $r14
pwndbg>
#寄存器r14的值：0x1f==31
```

其中变量NewArgc和NewArgv是全局变量：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612603101744-8be0af20-5e06-463d-9690-6274d9b81731.png)

两个全局变量是由sudoers_policy_main函数赋值的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612610596581-b9071821-903c-4f77-8b7a-99c99671114e.png)

从上面的代码可以看出NewArgv实际上是个数组：

```c
pwndbg> x/s NewArgv[0]
0x55555556e09c:	"sudoedit"
pwndbg> x/s NewArgv[1]
0x7fffffffe767:	"\\"
pwndbg> x/s NewArgv[2]
0x7fffffffe769:	"aabbccddeeffgghhiiggkkllmmnn"
pwndbg> x/s NewArgv[3]
0x0:	<error: Cannot access memory at address 0x0>
pwndbg> x/4gx NewArgv
0x55555578e258:	0x000055555556e09c	0x00007fffffffe767
    			#NewArgv[0]			#NewArgv[1]
0x55555578e268:	0x00007fffffffe769	0x0000000000000000
    			#NewArgv[3]			#NULL
pwndbg> 
```

回到代码中的for循环：

```c
	    /* Alloc and build up user_args. */
	    for (size = 0, av = NewArgv + 1; *av; av++)
		size += strlen(*av) + 1;
```

这是先计算NewArgv[1]、 NewArgv[2]的两个参数的长度2+28+1=31，然后执行if语句中的user_args=malloc(size)，因此user_args分配的内存大小为 31 字节。

漏洞的关键点出现了：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612605690346-48d5b9b8-dc0c-4d22-ab62-4f0cf276d044.png)

为方便理解，直接对867行下断点，看一下溢出之后的内容：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612606628383-d66edaba-b81a-4bef-a3f3-a1b35a6e9221.png)

```c
pwndbg> x/16gx 0x555555786580-0x10
0x555555786570:	0x0000000000000000	0x0000000000000031
0x555555786580:	0x6463636262616100	0x6867676666656564
0x555555786590:	0x6c6b6b6767696968	0x6161206e6e6d6d6c
0x5555557865a0:	0x6565646463636262	0x6969686867676666
0x5555557865b0:	0x6d6d6c6c6b6b6767	0x00007ffff7206e6e #to
0x5555557865c0:	0x0000000000000000	0x0000000000000000
0x5555557865d0:	0x7420656c69662073	0x656c62616e65206f
0x5555557865e0:	0x7369687420230a20	0x6f6974636e756620
pwndbg> 
```

根据结果这下就好理解了：

**<font style="color:#F5222D;">这几行代码是将</font>**_**<u><font style="color:#F5222D;">aabbccddeeffgghhiiggkkllmmnn</font></u>**_**<font style="color:#F5222D;">拷贝到之前malloc(0x31)中，</font>****<font style="color:#F5222D;">但是仔细观察内存会发现拷贝时出现了错误：</font>**

```c
pwndbg> x/16gx 0x555555786580-0x10
0x555555786570:	0x0000000000000000	0x0000000000000031 #malloc_chunk
0x555555786580:	0x6463636262616100	0x6867676666656564
                ##d c c b b a a       h g g f f e e d			
0x555555786590:	0x6c6b6b6767696968	0x6161206e6e6d6d6c #()表示空格
                ##l k k g g i i h     a a ()n n m m l 
0x5555557865a0:	0x6565646463636262	0x6969686867676666 #next_chunk（unsortedbin）
                ##e e d d c c b b     i i h h g g f f 
0x5555557865b0:	0x6d6d6c6c6b6b6767	0x00007ffff7206e6e 
                ##m m l l k k g g               ()n n  
0x5555557865c0:	0x0000000000000000	0x0000000000000000
0x5555557865d0:	0x7420656c69662073	0x656c62616e65206f
0x5555557865e0:	0x7369687420230a20	0x6f6974636e756620
pwndbg> 
```

由于复制错误导致了堆溢出，next_chunk的size和fd及bk指针被覆盖：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612609779202-b62910de-501f-4832-80c8-eb6041671eb0.png)

执行的命令：gdb --args sudoedit -s '\' aabbccddeeffgghhiiggkkllmmnn

本意要写入：aabbccddeeffgghhiiggkkllmmnn

实际上写入：aabbccddeeffgghhiiggkkllmmnn()aabbccddeeffggiiggkkllmmnn()

```c
		for (to = user_args, av = NewArgv + 1; (from = *av); av++) {
		    while (*from) {
			if (from[0] == '\\' && !isspace((unsigned char)from[1]))   
			    from++;
			*to++ = *from++;
		    }
		    *to++ = ' ';
		}
```

仔细分析一下这个代码，首先在进入循环之前将malloc的地址给了to，现在to=malloc(0x31)，然后将NewArgv + 1赋值到av中，现在av=NewArgv[1]；进入循环后，在处理NewArgv[1]=='\'时，from[0] 为 \ ，from[1] 为 \x00 ，会通过这个判断让 from++ ，然后后面会再次from++，这就导致了堆溢出。

不明白？调试一下：

> 以下的内存地址和上面的略有区别，因为我重新调试了，好像关了ALSR地址仍会变。
>

```c
##########################################################################
第一次for循环：
		#NewArgv[1]= "\+\x00",NewArgv[2]= "aabbccddeeffgghhiiggkkllmmnn",（步骤1）
		for (to = user_args, av = NewArgv + 1; (from = *av); av++) {
            #进入for循环av =NewArgv[1]（步骤2）
            #from = *av（*av：\+\x00）（步骤3）
		    while (*from) { 
            #进入while循环（步骤4）
			if (from[0] == '\\' && !isspace((unsigned char)from[1]))
                ##若from[0]为\并且from[1]是NULL结束字符（不为空格），则进入此if语句（步骤5）
                #判断结果：真（步骤6）
			    from++;  #执行from++后此时指向NULL结束字符（步骤7）
			*to++ = *from++;
            #下一行from++指向下个字符串开头，若该字符串存在，则继续这个while循环
		    }
----------------------------------------------------------------------------
进入for循环后：
pwndbg> x/gx to
0x555555786530:	0x00007ffff79b5ca0
pwndbg> p *av
$20 = 0x7fffffffe78d "\\"
pwndbg> x/gx av
0x55555578e210:	0x00007fffffffe78d
pwndbg> x/gx NewArgv
0x55555578e208:	0x000055555556e09c
pwndbg> x/gx from
0x7fffffffe78d:	0x636362626161005c
pwndbg> p from[1]
$16 = 0 '\000'
pwndbg> p from[0]
$17 = 92 '\\'
pwndbg> p *to
$7 = -96 '\240'
pwndbg> 

*from不为空，进入while循环，判断if语句，此时from[0]=='\\',from[1]==NULL;
满足条件，进入if语句，执行from++，得到from==aabbccddeeffgghhiiggkkllmmnn
此时的from[1]==97（'a'），紧接着执行*to++ = *from++;，结果如下：
*to==92 '\\'，*from==97 'a'。
由于while循环的终止条件是*av==NULL，从上面的经验得知，
while语句将会在复制完aabbccddeeffgghhiiggkkllmmnn字符串之后终止
##########################################################################
while循环结束，执行*to++ = ' ';之后，内存状况如下：
pwndbg> x/16gx 0x555555786530-0x10
0x555555786520:	0x0000000000000000	0x0000000000000031
0x555555786530:	0x6463636262616100	0x6867676666656564
                ##d c c b b a a       h g g f f e e d	
0x555555786540:	0x6c6b6b6767696968	0x0000206e6e6d6d6c #()表示空格
                ##l k k g g i i h    	  ()n n m m l 
0x555555786550:	0x2065766f62612065	0x0000000000000d91 #现在没有溢出
0x555555786560:	0x00007ffff79b5ca0	0x00007ffff79b5ca0
0x555555786570:	0x0000000000000000	0x0000000000000000
0x555555786580:	0x7420656c69662073	0x656c62616e65206f
0x555555786590:	0x7369687420230a20	0x6f6974636e756620


pwndbg> x/8gx to
0x55555578654e:	0x766f626120650000	0x000000000d912065
0x55555578655e:	0x7ffff79b5ca00000	0x7ffff79b5ca00000
0x55555578656e:	0x0000000000000000	0x0000000000000000
0x55555578657e:	0x656c696620730000	0x62616e65206f7420
pwndbg> x/8gx av
0x55555578e218:	0x00007fffffffe78f	0x0000000000000000
0x55555578e228:	0x0000000000000021	0x54552e53555f6e65
0x55555578e238:	0x0000000000382d46	0x0000000000000000
0x55555578e248:	0x0000000000008dc1	0x0000000000000000
pwndbg> x/8gx NewArgv
0x55555578e208:	0x000055555556e09c	0x00007fffffffe78d
0x55555578e218:	0x00007fffffffe78f	0x0000000000000000
0x55555578e228:	0x0000000000000021	0x54552e53555f6e65
0x55555578e238:	0x0000000000382d46	0x0000000000000000
pwndbg> x/8gx from
value has been optimized out
pwndbg> p *to
$14 = 0 '\000'
pwndbg> p *from
value has been optimized out
pwndbg> p *av
$15 = 0x7fffffffe78f "aabbccddeeffgghhiiggkkllmmnn"
pwndbg> 

##########################################################################
现在，我们输入的所有的字符串都已经复制完成到堆中,由于*av!=NULL,
因此进入第二次for循环继续复制（重复第一次for循环）：
pwndbg> x/s NewArgv[1]
0x7fffffffe78d:	"\\"
pwndbg> x/s NewArgv[2]
0x7fffffffe78f:	"aabbccddeeffgghhiiggkkllmmnn"
pwndbg>
		for (to = user_args, av = NewArgv + 1; (from = *av); av++) {
        	#进入之后：av==NewArgv[2]
		    while (*from) {
			if (from[0] == '\\' && !isspace((unsigned char)from[1]))
			    from++;
			*to++ = *from++;
		    }
		    *to++ = ' '; 
		}
---------------------------------------------------------------------------- 
稍微总结一下，在第一次进入if语句时：
NewArgv[1]= "\+空格",NewArgv[2]= "aabbccddeeffgghhiiggkkllmmnn"
所以在处理NewArgv[1]时,from[0]=='\',from[1]==\x00 ，
会通过if判断让 from++ ，然后后面会再次from++(*to++ = *from++;);
之后from就指向了NewArgv[1]字符串\x00后面一个字符的位置即'a'：
pwndbg> x/gx *NewArgv
0x55555556e09c:	0x746964656f647573 #NewArgv[0]
				#"sudoedit"			
pwndbg> x/s NewArgv[1]
0x7fffffffe78d:	"\\"
pwndbg> x/s NewArgv[2]
0x7fffffffe78f:	"aabbccddeeffgghhiiggkkllmmnn"
pwndbg> x/16gx 0x7fffffffe78d-0x10
0x7fffffffe77d:	0x6f6475732f6e6962	0x00732d0074696465
0x7fffffffe78d:	0x636362626161005c	0x6767666665656464 NewArgv[1]+NewArgv[2]
                ##d c c b b a a \      h g g f f e e d
0x7fffffffe79d:	0x6b6b676769696868	0x4c006e6e6d6d6c6c
                ##l k k g g i i h    	  ()n n m m l 
......(others)
pwndbg>  
可以看到NewArgv[1](0x5c 0x00)后面紧跟着的是NewArgv[2](0x61 0x61 ...)，
所以在第二次for循环中，from执行的就是NewArgv[2]的开头。
从而会再次进入for循环把NewArgv[2]拷贝到user_args导致堆溢出。
注意：只会循环复制两次，因为第三次for循环时*av==NewArgv[2]==NULL，导致：
from = *av赋值异常，从而终止循环。
---------------------------------------------------------------------------- 
标准的空白字符包括：
' '     (0x20)    space (SPC) 空格符
'\t'    (0x09)    horizontal tab (TAB) 水平制表符    
'\n'    (0x0a)    newline (LF) 换行符
'\v'    (0x0b)    vertical tab (VT) 垂直制表符
'\f'    (0x0c)    feed (FF) 换页符
'\r'    (0x0d)    carriage return (CR) 回车符
函数原型：int isspace(int c);
返回值：如果 c 是一个空白字符，则该函数返回非零值（true），否则返回 0（false）。
```

> **<font style="color:#F5222D;">另外一点：C语言中的\具有转义含义，因此\\才代表'\'</font>**
>

溢出之后的结果如下：

```c
pwndbg> x/16gx 0x555555786520
0x555555786520:	0x0000000000000000	0x0000000000000031 #overflow_chunk
0x555555786530:	0x6463636262616100	0x6867676666656564
0x555555786540:	0x6c6b6b6767696968	0x6161206e6e6d6d6c
0x555555786550:	0x6565646463636262	0x6969686867676666 #unsortedbin
0x555555786560:	0x6d6d6c6c6b6b6767	0x00007ffff7206e6e
0x555555786570:	0x0000000000000000	0x0000000000000000
0x555555786580:	0x7420656c69662073	0x656c62616e65206f
0x555555786590:	0x7369687420230a20	0x6f6974636e756620
```

当下次malloc申请unsortedbin会触发异常使得程序崩溃：

```bash
pwndbg> c
Continuing.
malloc(): memory corruption

Program received signal SIGABRT, Aborted.
```

下一小节将会分析恶意so加载和poc的源代码。

