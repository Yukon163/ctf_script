> 附件：链接: [https://pan.baidu.com/s/17CySOLmxS_0VO2nQZRbwIA](https://pan.baidu.com/s/17CySOLmxS_0VO2nQZRbwIA) 提取码: i4nz
>
> 本文首发于IOTsec-Zone
>

# 准备工作
因为互联网上似乎没有模拟华硕路由器的公开资料，我手边恰好有型号为`RT-ACRH17`的路由器，所以在本篇文章我们将尝试模拟该型号路由器的http服务。实体机的存在可能为之后的固件模拟流程提供比较大的便利：

![](https://cdn.nlark.com/yuque/0/2022/jpeg/574026/1666924149511-77f0d92a-60f4-42b3-adbc-a79d8e113649.jpeg?x-oss-process=image/auto-orient,1)

该型号路由器在国内生产，所以可到华硕官网（[https://www.asus.com.cn/networking-iot-servers/wifi-routers/asus-wifi-routers/rt-acrh17/helpdesk_download/](https://www.asus.com.cn/networking-iot-servers/wifi-routers/asus-wifi-routers/rt-acrh17/helpdesk_download/)）下载固件。本篇文章的目标固件版本为`3.0.0.4.382.52517`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666925151546-4888f31a-7027-481e-8bc8-caad7454bc09.png)

> + `RT-ACRH17_3.0.0.4_382_52517-gb4d36a6.trx`：`d8a63fccabb78394c5202873969161be（MD5）` 
> + `FW_RT_ACRH17_300438252517.zip`：`591992882df36580b128cdbbefaa29d1（MD5）`   
>

使用binwalk解压`.trx`固件（`binwalk -Me RT-ACRH17_3.0.0.4_382_52517-gb4d36a6.trx`）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666925184630-3425b538-d674-4973-b674-b807a82e7345.png)

可知，使用的指令集为ARM，32位小端序（LSB），更详细的busybox信息如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666925306456-e8281662-df5f-49ae-a52d-2835eaf56f68.png)

我打算使用QEMU-system进行模拟，需要准备的文件如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666925539782-e00e7462-f884-4650-9b7e-18056e969ede.png)

```shell
#!/bin/bash

# 3.2.0
wget https://people.debian.org/~aurel32/qemu/armhf/debian_wheezy_armhf_standard.qcow2
wget https://people.debian.org/~aurel32/qemu/armhf/initrd.img-3.2.0-4-vexpress
wget https://people.debian.org/~aurel32/qemu/armhf/vmlinuz-3.2.0-4-vexpress
```

首先设置虚拟机网卡：

```shell
$ sudo tunctl -t tap0
$ sudo ifconfig tap0 192.168.50.2/24
	# 设置IP为50.2的原因为华硕路由器默认的后台为192.168.50.1，为了方便我就这样设置了，没有额外含义。
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666926331545-02b8d70a-0549-4a16-84f8-083ff25c9abd.png)

使用qemu启动模拟环境，命令如下：

```shell
$ sudo qemu-system-arm -M vexpress-a9 -kernel vmlinuz-3.2.0-4-vexpress \
     -initrd initrd.img-3.2.0-4-vexpress \
     -drive if=sd,file=debian_wheezy_armhf_standard.qcow2 \
     -append "root=/dev/mmcblk0p2" -smp 2,cores=2 \
     -net nic -net tap,ifname=tap0,script=no,downscript=no -nographic
```

启动过程请耐心等待，默认的账号密码均为`root`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666926267008-25986808-7b66-47cb-920d-7241734eddff.png)

> Tips：建议在启动完成之后拍一个虚拟机快照，这样我们就能任何时刻都能以极短的时间恢复到此处。
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666926759237-5332b8a6-1a2a-42a2-986b-b225a09f19e9.png)

配置qemu的网络：`ifconfig eth0 192.168.50.1/24`。尝试在外部能否连接上qemu：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666926971231-8ad7b111-4105-41f2-89f9-762dbbc09d8c.png)

对之前解压的文件系统进行压缩，利用ssh上传至qemu：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666927498198-427e8af2-ccab-4aee-8039-777169c8fdbe.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666927320264-806aee21-c868-4071-b8ba-d8434615db85.png)

来到qemu，解压缩文件系统：`tar -zxvf squashfs-root.tar.gz`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666927707846-17d1d2b5-c5e3-4c1f-bfd0-76a5940caa3a.png)

效果如下图所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666927748881-bdf34ce1-f51d-4849-8418-a567e7af1276.png)

准备工作完成，下面开始模拟。

# 固件模拟
### 01、开始模拟！
在qemu内部挂载文件系统，然后chroot：

```shell
$ cd ../
$ mount -o bind /dev ./squashfs-root/dev && mount -t proc /proc ./squashfs-root/proc
$ chroot ./squashfs-root sh
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666932440101-2bbab2a8-398a-4f8a-b5fa-3ae9a3788ee5.png)

看见那些报错的软链接了吗？这里先手动创建这些文件夹吧：

```shell
$ cd tmp
$ mkdir -p ./etc ./home ./mnt ./opt ./home/root ./var
```

效果如下图所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666932712663-200a2540-5e31-4164-9da8-f819f1f67a54.png)

通过搜索文件系统，会发现有两个与http服务有关的可执行文件，分别是`./usr/sbin/httpds`和`./usr/sbin/httpd`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666932874497-c134c80f-4df0-49f6-ad4a-293107680c40.png)

但启动时调用的是httpd而非httpsd，这一点可以从下面的真机环境中看出来。

### 02、收集真机环境信息
> + **<font style="color:#E8323C;background-color:#FADB14;">实体路由器后台的账号密码已经被设置为</font>**`**<font style="color:#E8323C;background-color:#FADB14;">qiangwang</font>**`**<font style="color:#E8323C;background-color:#FADB14;">、</font>**`**<font style="color:#E8323C;background-color:#FADB14;">2022qwb</font>**`**<font style="color:#E8323C;background-color:#FADB14;">，不再是原来的默认账号密码</font>**`**<font style="color:#E8323C;background-color:#FADB14;">admin、admin</font>**`**<font style="color:#E8323C;background-color:#FADB14;">；我们之后的hook是基于该路由器的nvram实现的。</font>**
>

为了方便之后固件模拟，我打算在真机中收集一些有用的信息。华硕路由器路由器很方便，它自带ssh和telnet服务，直接连接上去就行了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666934318705-d6fad4ee-1001-42c3-bba0-e050daff2b9a.png)

连接后可以很轻松的获取实机的nvram：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666934937061-81b1ee1e-ebea-445b-8d27-26e7ec3f7dfc.png)

> 真机上的nvram：[nvram.txt]()
>

然后收集内核启动信息：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666935219460-e508a021-3aba-4fdd-a095-86e356c8ce6e.png)

> 真机上的内核启动信息：[start.log]()
>

再收集一下进程信息：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666935366629-3dfb589b-13bd-4960-90dc-db80d7eac106.png)

```plain
  PID USER       VSZ STAT COMMAND
    1 qiangwan  4164 S    /sbin/init
    2 qiangwan     0 SW   [kthreadd]
    3 qiangwan     0 SW   [ksoftirqd/0]
    5 qiangwan     0 SW<  [kworker/0:0H]
    6 qiangwan     0 SW   [kworker/u8:0]
    7 qiangwan     0 SW   [rcu_preempt]
    8 qiangwan     0 SW   [rcu_sched]
    9 qiangwan     0 SW   [rcu_bh]
   10 qiangwan     0 SW   [migration/0]
   11 qiangwan     0 SW   [watchdog/0]
   12 qiangwan     0 SW   [watchdog/1]
   13 qiangwan     0 SW   [migration/1]
   14 qiangwan     0 SW   [ksoftirqd/1]
   15 qiangwan     0 SW   [kworker/1:0]
   16 qiangwan     0 SW<  [kworker/1:0H]
   17 qiangwan     0 SW   [watchdog/2]
   18 qiangwan     0 SW   [migration/2]
   19 qiangwan     0 SW   [ksoftirqd/2]
   21 qiangwan     0 SW<  [kworker/2:0H]
   22 qiangwan     0 SW   [watchdog/3]
   23 qiangwan     0 SW   [migration/3]
   24 qiangwan     0 SW   [ksoftirqd/3]
   26 qiangwan     0 SW<  [kworker/3:0H]
   27 qiangwan     0 SW<  [khelper]
   28 qiangwan     0 SW   [kdevtmpfs]
   29 qiangwan     0 SW<  [writeback]
   30 qiangwan     0 SW<  [bioset]
   31 qiangwan     0 SW<  [crypto]
   32 qiangwan     0 SW<  [kblockd]
   33 qiangwan     0 SW   [kworker/1:1]
   34 qiangwan     0 SW   [kswapd0]
   35 qiangwan     0 SW   [fsnotify_mark]
   50 qiangwan     0 SW   [spi0]
   51 qiangwan     0 SW   [kworker/u8:1]
   64 qiangwan     0 SW   [kworker/0:1]
   65 qiangwan     0 SW<  [ipv6_addrconf]
   66 qiangwan     0 SW   [kworker/3:1]
   67 qiangwan     0 SW<  [deferwq]
   68 qiangwan     0 SW   [ubi_bgt0d]
   69 qiangwan     0 SW   [kworker/2:1]
   89 qiangwan   636 S    hotplug2 --persistent --no-coldplug
  259 qiangwan     0 SW<  [alloc_task_wque]
  289 qiangwan     0 SW<  [alloc_task_wque]
  351 qiangwan  4136 S    console
  353 qiangwan     0 SW   [ubifs_bgt0_5]
  367 qiangwan     0 SW   [khubd]
  448 qiangwan  1440 S    /sbin/syslogd -m 0 -S -O /jffs/syslog.log -s 256 -l 6
  450 qiangwan  1440 S    /sbin/klogd -c 5
  492 qiangwan  4148 S    /sbin/wanduck
  493 qiangwan  4376 S    asd
  494 qiangwan  2288 S    protect_srv
  507 qiangwan  1440 S    telnetd -b 192.168.50.1
  545 qiangwan  1020 S    dropbear -p 22 -a
  546 qiangwan  4144 S    wpsaide
  549 nobody     996 S    dnsmasq --log-async
  554 qiangwan  2116 S    avahi-daemon: running [RT-ACRH17-00EC.local]
  562 qiangwan  1452 S    crond
  563 qiangwan  4172 S    httpd -i br0
  564 qiangwan  1096 S    /usr/sbin/infosvr br0
  566 qiangwan  1092 S    sysstate
  567 qiangwan  8472 S    ahs
  568 qiangwan  4144 S    watchdog
  570 qiangwan  2668 S    rstats
  583 qiangwan  1104 S    lld2d br0
  590 qiangwan  4600 S    networkmap --bootwait
  593 qiangwan  8680 S    mastiff
  598 qiangwan     0 SW   [kworker/3:2]
  744 qiangwan  4144 S    usbled
  754 qiangwan     0 SW   [kworker/2:2]
  755 qiangwan  2044 S    hostapd -d -B /etc/Wireless/conf/hostapd_ath0.conf -P /var/run/hostapd_ath0.pid -e /var/run/entropy_ath0.
  811 qiangwan     0 SW   [kworker/0:2]
  830 qiangwan  4144 S    ntp
  831 qiangwan  2048 S    hostapd -d -B /etc/Wireless/conf/hostapd_ath1.conf -P /var/run/hostapd_ath1.pid -e /var/run/entropy_ath1.
  894 qiangwan   932 S    miniupnpd -f /etc/upnp/config
  925 qiangwan  4144 S    disk_monitor
  928 qiangwan  1456 S    /sbin/udhcpc -i eth0 -p /var/run/udhcpc0.pid -s /tmp/udhcpc -O33 -O249
 3582 qiangwan  1044 S    dropbear -p 22 -a
 3603 qiangwan  1456 S    -sh
 3649 qiangwan  1444 R    ps -w
```

> + 路由器只启动了httpd：`httpd -i br0`，没有启动httpsd。
>

最后从路由器后台导出日志：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666936719931-86090ea0-ec7b-4ee0-a7c3-3a46bd149d23.png)

> 真机后台日志：[syslog.txt]()
>

收集完成之后我们继续模拟。

### 03、继续模拟
尝试直接执行`httpd`可执行文件，会出现如下错误：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666936594527-3e816f4f-5464-40ba-a81b-f7205c5a085c.png)

前面的一些`/dev/nvram`错误先不用管，将注意力集中在后面的证书报错。在真机的日志`syslog.txt`中搜索`certificate（证书）`，可得到下面的结果：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666937073906-ccba4fe4-428a-47cc-9f1a-a4adace8c72b.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666937093057-259cab0f-f4f4-4eee-9f8f-e87dc020fdd2.png)

在文件系统中分别搜索字符串`Save SSL certificate`和`Succeed to init SSL`，均定位到了`httpd`文件：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666937294020-4e1fe738-2476-454b-8166-7eb398fbbbea.png)

`httpd`拖入IDA，搜索上面任意一个字符串，交叉引用到函数`sub_100A8`：

```c
int __fastcall sub_100A8(int a1)
{
  int v2; // r5
  int v3; // r6
  int i; // r10
  int v5; // r0
  int v6; // r0
  int v7; // r8
  int v8; // r5
  char v10[32]; // [sp+8h] [bp-68h] BYREF
  char *v11; // [sp+28h] [bp-48h] BYREF
  const char *v12; // [sp+2Ch] [bp-44h]
  const char *v13; // [sp+30h] [bp-40h]
  const char *v14; // [sp+34h] [bp-3Ch]
  const char *v15; // [sp+38h] [bp-38h]
  const char *v16; // [sp+3Ch] [bp-34h]
  const char *v17; // [sp+40h] [bp-30h]
  int v18; // [sp+44h] [bp-2Ch]
  __int64 v19; // [sp+48h] [bp-28h] BYREF

  v2 = 1;
  v3 = file_lock("httpd");
  do
  {
    if ( v3 < 0 )
      sleep(v2 * v2);
    else
      v2 = 5;
    ++v2;
  }
  while ( v2 <= 4 );
  if ( sub_D308("https_crt_gen", "1") )
    ((void (*)(void))sub_10074)();
  for ( i = 1; ; i = 0 )
  {
    v7 = sub_D308("https_crt_save", "1");
    v5 = f_exists("/etc/cert.pem");
    if ( v5 )
    {
      v5 = f_exists("/etc/key.pem");
      if ( v5 )
        goto LABEL_11;
    }
    if ( !v7 )
      goto LABEL_10;
    logmessage_normal("httpd", "Save SSL certificate...%d", a1);
    v11 = "tar";
    v12 = "-xzf";
    v13 = "/jffs/cert.tgz";
    v14 = "-C";
    v15 = "/";
    v16 = "etc/cert.pem";
    v17 = "etc/key.pem";
    v18 = 0;
    if ( eval(&v11, 0, 0, 0) )
    {
      v8 = 0;
    }
    else
    {
      v8 = 1;
      system("cat /etc/key.pem /etc/cert.pem > /etc/server.pem");
      system("cp /etc/cert.pem /etc/cert.crt");
    }
    v5 = sub_D308("https_intermediate_crt_save", "1");
    if ( v5 )
    {
      v11 = "tar";
      v12 = "-xzf";
      v13 = "/jffs/cert.tgz";
      v14 = "-C";
      v15 = "/";
      v16 = "etc/intermediate_cert.pem";
      v17 = 0;
      v5 = eval(&v11, 0, 0, 0);
    }
    if ( !v8 )
    {
LABEL_10:
      sub_10074(v5);
      logmessage_normal("httpd", "Generating SSL certificate...%d", a1);
      f_read("/dev/urandom", &v19, 8);
      snprintf(v10, 0x20u, "%llu", v19 & 0x7FFFFFFFFFFFFFFFLL);
      v11 = "gencert.sh";
      v12 = v10;
      v13 = 0;
      v5 = eval(&v11, 0, 0, 0);
LABEL_11:
      if ( !v7 )
        goto LABEL_12;
    }
    sub_10034(v5);
LABEL_12:
    if ( mssl_init("/etc/cert.pem", "/etc/key.pem") )
      break;
    v6 = logmessage_normal("httpd", "Failed to initialize SSL, generating new key/cert...%d", a1);
    sub_10074(v6);
    if ( !i )
    {
      logmessage_normal("httpd", "Unable to start in SSL mode, exiting! %d", a1);
      file_unlock(v3);
      exit(1);
    }
  }
  logmessage_normal("httpd", "Succeed to init SSL certificate...%d", a1);
  return file_unlock(v3);
}
```

虽然我并没有仔细看这个函数的代码逻辑，但当中的一段代码还是引起了我的注意：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666938175037-e8f82fa1-3d21-4353-94c5-9b422e35aae2.png)

二话不说，我直接在qemu中执行`gencert.sh`脚本，出现如下错误：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666939468336-37f40ef7-fa96-4380-894d-a438385647e5.png)

```shell
#!/bin/sh
SECS=1262278080

cd /etc

NVCN=`nvram get https_crt_cn`
if [ "$NVCN" == "" ]; then
NVCN="router.asus.com"
fi

cp -L openssl.cnf openssl.config

I=0
for CN in $NVCN; do
echo "$I.commonName=CN" >> openssl.config
echo "$I.commonName_value=$CN" >> openssl.config
I=$(($I + 1))
done

# create the key and certificate request
#openssl req -new -out /tmp/cert.csr -config openssl.config -keyout /tmp/privkey.pem -newkey rsa:1024 -passout pass:password
# remove the passphrase from the key
#openssl rsa -in /tmp/privkey.pem -out key.pem -passin pass:password
# convert the certificate request into a signed certificate
#openssl x509 -in /tmp/cert.csr -out cert.pem -req -signkey key.pem -setstartsecs $SECS -days 3653 -set_serial $1

# create the key and certificate request
OPENSSL_CONF=/etc/openssl.config openssl req -new -out /tmp/cert.csr -keyout /tmp/privkey.pem -newkey rsa:2048 -passout pass:password
# remove the passphrase from the key
#OPENSSL_CONF=/etc/openssl.cnf openssl rsa -in /tmp/privkey.pem -out key.pem -passin pass:password
# convert the certificate request into a signed certificate
#OPENSSL_CONF=/etc/openssl.cnf RANDFILE=/dev/urandom openssl x509 -in /tmp/cert.csr -out cert.pem -req -signkey key.pem -days 3653 -sha256

# 2020/01/03 import the self-certificate
OPENSSL_CONF=/etc/openssl.config openssl rsa -in /tmp/privkey.pem -out key.pem -passin pass:password
OPENSSL_CONF=/etc/openssl.config RANDFILE=/dev/urandom openssl req -x509 -new -nodes -in /tmp/cert.csr -key key.pem -days 3653 -sha256 -out cert.pem

#	openssl x509 -in /etc/cert.pem -text -noout

# server.pem for WebDav SSL
cat key.pem cert.pem > server.pem

# cfg_pub.pem for cfg server
IS_SUPPORT_CFG_SYNC=`nvram get rc_support|grep -i cfg_sync`
if [ "$IS_SUPPORT_CFG_SYNC" != "" ]; then
openssl rsa -in key.pem -outform PEM -pubout -out cfg_pub.pem
fi

# 2020/01/03 import the self-certificate
cp cert.pem cert.crt

rm -f /tmp/cert.csr /tmp/privkey.pem openssl.config

```

提示没有`cert.pem`文件，大致的看一下该脚本逻辑就会发现，报错源头似乎还是和`nvram`有关：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666939902817-68be3ebc-f93e-424e-abf2-ace1dc75f282.png)

可是，在真机中`https_crt_cn`的值本身就为空，那就不是nvram的问题了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666940823166-60c8670c-0bfa-430d-a6c7-8e111e6a1516.png)

再次仔细查看上面的报错，发现`openssl.cnf`文件不存在，但事实上该文件在文件系统中是存在的，在`./rom/etc/openssl.cnf`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666940975378-08ed215f-8348-4a73-9e96-cefb56a8b3f2.png)

究其原因，在系统启动时会自动调用`./sbin/rc`文件，该可执行文件执行时会将`/rom/etc`目录下的文件软链接到`/etc`中：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666942945047-56597062-ecda-412a-a11c-1dcb2a8ce5e5.png)

![在实机上查看](https://cdn.nlark.com/yuque/0/2022/png/574026/1666943282458-f6149656-c3c2-4742-a8e8-211466291d18.png)

看来软链接创建的还是有问题，为了图省事我就直接复制文件了 -- 在qemu中执行`cp -R /rom/etc/* /etc/`以让`/rom/etc`的所有文件复制到`/etc`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666944044112-3f54f5c2-bafe-4231-80bc-340f654dbcab.png)

再次重新执行`gencert.sh`脚本就可以了

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666944103019-9c1a0987-6bb4-4bd2-84a5-5e8b1b86b3da.png)

再次尝试执行`httpd`，有如下错误：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666944273981-2004fc5c-2f09-497a-a154-e1cb5867388b.png)

很简单，创建`/var/run/`目录就行（`mkdir -p /var/run/`），再次执行`httpd`，稍等片刻之后会出现如下信息：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666944452385-1b1e482c-5cb8-45a1-96f5-4ca12083f561.png)

emmm...，看起来似乎是成功了，使用curl访问华硕路由器主页`Main_Login.asp`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666945105061-baaffccf-69b5-4305-88ef-057edfca148b.png)

？**为什么一访问就404，而且看终端上显示的内容似乎表明这请求连接并没有关闭 -- 光标一直在闪烁？？?**`CTRL+C`之后尝试执行`curl http://192.168.50.1/`呢？

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666946379015-d011b3b1-fead-4a9a-b191-1b24ee9cd8cd.png)

直接不返回了，一看qemu，直接段错误了可还行，如下图所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666946420466-12aef8cd-e4f6-4c06-a145-c039a513cc40.png)

### 04-1、解决httpd的404问题！
> + **<font style="color:#E8323C;">感谢@Wankko Ree师傅的提示！</font>**
>

无法访问网页是不是因为没有在www目录下启动？在根目录重新启动httpd并执行`curl http://192.168.50.1/www/Main_Login.asp`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666946865209-a1956729-38de-475f-a1b0-495655cd9a6a.png)

...，果然是httpd启动目录的问题，并且似乎连接仍然没有断开：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1666947852992-60fe0d2e-e835-4812-9879-a386a2464d26.png)

如上图所示，还要注意返回的asp文件存在`<#2433#>`的占位符；正常情况下返回的是经httpd解析（替换）后的语言包：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667008235511-1a85c53a-62ec-4212-9655-50b509683b8e.png)

如果你使用浏览器访问该URL会发生502：

![更正：链接“未”断开](https://cdn.nlark.com/yuque/0/2022/png/574026/1667007836048-ce205e42-715b-4b01-bf2a-3e9e03205dd6.png)

这些都是什么奇奇怪怪的问题。反正无论如何都是访问不了了呗。我们在www目录重新启动httpd，再次执行`curl http://192.168.50.1/Main_Login.asp`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667008533334-d2c287eb-ab16-48d8-9c5e-3a7b1db64a42.png)

由于语言包也在www目录下，所以这样启动httpd之后就可以正常的解析语言包了；但还是当使用浏览器访问时程序就崩溃了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667009336011-3249ce62-f2a8-48a8-a340-19ddaf2cfe4e.png)

### 04-2、解决段错误问题
本来我想用IDA去调试出段错误的原因，但是由于qemu在Linux虚拟机的内部，我Windows的IDA并不能直接连接到qemu的gdbserver；若使用rinetd转发，虽然nc测试连通性没有问题、gdbserver也显示connected，但IDA就是死活连不上去。我仔细想了想，现在只剩下了两条路可走：

1. 我只有Windows上的IDA Pro 7.7，而Windows程序是无法运行在Linux的；但可以使用`Crossover`在Linux上直接运行Windows版IDA，然后连接调试。
2. 对nvram进行hook，然后具体情况具体分析，看还会不会出现段错误。

当然，第二种肯定是最简单的，那就选第二种吧。之前我们在真机中已经提取了nvram的所有值，因此可以很方便的利用`firmadyne libnvram`对`httpd`进行hook【不使用`nvram-faker`的原因在于它缺少了对`nvram_unset`函数的hook支持：`can't resolve symbol 'nvram_unset'`；虽然似乎并不影响程序的正常执行，但是为了保险起见我决定不采用它】。

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667010763634-e28ba86f-b126-4b05-9644-92a3628027b4.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667010809350-a9736a98-0617-4172-a8d3-40a7b13485e3.png)

因为路由器为arm架构，采用的也是uClibc，所以具体的hook方法我不再细说，烦请参考之前的我写的文章：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667011535648-948771ac-df4f-4b6a-9897-dc11446a5ff3.png)

[《IoT从入门到入土》(5)--模拟固件下的patch与hook（1）](https://www.yuque.com/cyberangel/yal5fc/gg3r9m)

只需要将《模拟固件下的patch与hook》一文的`config.h`替换为如下内容然后编译即可，可别忘了之前曾出现的问题：

![《IoT从入门到入土》(5)--模拟固件下的patch与hook（1）](https://cdn.nlark.com/yuque/0/2022/png/574026/1667012674984-e6abdff1-f207-4f30-8cee-8797d8b312db.png)

```c
#ifndef INCLUDE_CONFIG_H
#define INCLUDE_CONFIG_H

// Determines whether debugging information should be printed to stderr.
#define DEBUG               1
// Determines the size of the internal buffer, used for manipulating and storing key values, etc.
#define BUFFER_SIZE         256
// Determines the size of the "emulated" NVRAM, used by nvram_get_nvramspace().
#define NVRAM_SIZE          2048
// Determines the maximum size of the user-supplied output buffer when a length is not supplied.
#define USER_BUFFER_SIZE    64
// Determines the unique separator character (as string) used for the list implementation. Do not use "\0".
#define LIST_SEP            "\xff"
// Special argument used to change the semantics of the nvram_list_exist() function.
#define LIST_MAGIC          0xdeadbeef
// Identifier value used to generate IPC key in ftok()
#define IPC_KEY             'A'
// Timeout for the semaphore
#define IPC_TIMEOUT         1000
// Mount point of the base NVRAM implementation.
#define MOUNT_POINT         "/firmadyne/libnvram/"
// Location of NVRAM override values that are copied into the base NVRAM implementation.
#define OVERRIDE_POINT      "/firmadyne/libnvram.override/"

// Define the semantics for success and failure error codes.
#define E_FAILURE  0
#define E_SUCCESS  1

// Default paths for NVRAM default values.
#define NVRAM_DEFAULTS_PATH \
    /* "DIR-505L_FIRMWARE_1.01.ZIP" (10497) */ \
    PATH("/var/etc/nvram.default") \
    /* "DIR-615_REVE_FIRMWARE_5.11.ZIP" (9753) */ \
    PATH("/etc/nvram.default") \
    /* "DGL-5500_REVA_FIRMWARE_1.12B05.ZIP" (9469) */ \
    PATH("/etc/nvram.conf") \
    PATH("/etc/nvram.deft") \
    PATH("/etc/nvram.update") \
    TABLE(Nvrams) \
    PATH("/etc/wlan/nvram_params") \
    PATH("/etc/system_nvram_defaults")

// Default values for NVRAM.
#define NVRAM_DEFAULTS \
    ENTRY("ehci_ports", nvram_set,"1-1 3-1")\
    ENTRY("wl_radius_port", nvram_set,"1812")\
    ENTRY("PM_type", nvram_set,"0")\
    ENTRY("wl0_expire", nvram_set,"0")\
    ENTRY("wl0_lrc", nvram_set,"2")\
    ENTRY("wl0.1_radius_port", nvram_set,"1812")\
    ENTRY("printer_ifname", nvram_set,"usb")\
    ENTRY("qos_reset", nvram_set,"0")\
    ENTRY("filter_lw_time2_x", nvram_set,"00002359")\
    ENTRY("wl1_wme", nvram_set,"auto")\
    ENTRY("vpn_client5_errno", nvram_set,"")\
    ENTRY("curr_CTL", nvram_set,"CN")\
    ENTRY("wl_mode_x", nvram_set,"0")\
    ENTRY("wan_unit", nvram_set,"0")\
    ENTRY("qos_irates", nvram_set,"100,100,100,100,100,0,0,0,0,0")\
    ENTRY("vts_upnplist", nvram_set,"")\
    ENTRY("Ate_power_on_off_ver", nvram_set,"2.4")\
    ENTRY("wl0.2_ap_isolate", nvram_set,"0")\
    ENTRY("printer_model_t", nvram_set,"")\
    ENTRY("dhcp1_gateway_x", nvram_set,"")\
    ENTRY("dr_enable_x", nvram_set,"1")\
    ENTRY("ddns_regular_check", nvram_set,"0")\
    ENTRY("pushnotify_diskmonitor", nvram_set,"1")\
    ENTRY("ipv6_fw_enable", nvram_set,"0")\
    ENTRY("wl1_hwaddr", nvram_set,"04:D4:C4:D4:00:EC")\
    ENTRY("wl1_bw_ul", nvram_set,"")\
    ENTRY("wl1.2_bw_enabled", nvram_set,"0")\
    ENTRY("wan0_pppoe_hostuniq", nvram_set,"")\
    ENTRY("wan0_primary", nvram_set,"1")\
    ENTRY("dhcp1_enable_x", nvram_set,"0")\
    ENTRY("wl0_frameburst", nvram_set,"off")\
    ENTRY("misc_ping_x", nvram_set,"0")\
    ENTRY("smbd_enable", nvram_set,"1")\
    ENTRY("ipv6_6rd_ip4size", nvram_set,"0")\
    ENTRY("wl0_txbf", nvram_set,"1")\
    ENTRY("wl_assoc_retry_max", nvram_set,"3")\
    ENTRY("wan_ppp_phy", nvram_set,"1")\
    ENTRY("log_ipaddr", nvram_set,"")\
    ENTRY("pptpd_mtu", nvram_set,"1450")\
    ENTRY("wan0_ipaddr", nvram_set,"0.0.0.0")\
    ENTRY("vpn_serverx_eas", nvram_set,"1, ")\
    ENTRY("vpn_server_local", nvram_set,"10.8.0.1")\
    ENTRY("vpn_client_tlsremote", nvram_set,"0")\
    ENTRY("wl1_mimo_preamble", nvram_set,"mm")\
    ENTRY("wl1.1_unit", nvram_set,"1.1")\
    ENTRY("wan0_proto", nvram_set,"dhcp")\
    ENTRY("fw_pt_h323", nvram_set,"1")\
    ENTRY("btn_ez_mode", nvram_set,"0")\
    ENTRY("VPNServer_enable", nvram_set,"0")\
    ENTRY("vpn_client_bridge", nvram_set,"1")\
    ENTRY("wl_wdsapply_x", nvram_set,"0")\
    ENTRY("wan_dhcpenable_x", nvram_set,"1")\
    ENTRY("qos_rst", nvram_set,"off")\
    ENTRY("wl0.2_macmode", nvram_set,"disabled")\
    ENTRY("apps_state_upgrade", nvram_set,"")\
    ENTRY("led_lan4_gpio", nvram_set,"12337")\
    ENTRY("wl_nctrlsb", nvram_set,"lower")\
    ENTRY("vpn_client_poll", nvram_set,"0")\
    ENTRY("ipv6_tun_v4end", nvram_set,"0.0.0.0")\
    ENTRY("wl1_HT_STBC", nvram_set,"1")\
    ENTRY("wl1.3_wpa_gtk_rekey", nvram_set,"3600")\
    ENTRY("PM_state", nvram_set,"")\
    ENTRY("ASUS_EULA", nvram_set,"0")\
    ENTRY("dms_dir_manual", nvram_set,"0")\
    ENTRY("apps_swap_enable", nvram_set,"0")\
    ENTRY("aae_disable_force", nvram_set,"0")\
    ENTRY("wl0.3_bss_enabled", nvram_set,"0")\
    ENTRY("wl1.3_akm", nvram_set,"")\
    ENTRY("et0macaddr", nvram_set,"04:D4:C4:D4:00:E8")\
    ENTRY("wifi_psk", nvram_set,"")\
    ENTRY("qca_sfe", nvram_set,"1")\
    ENTRY("vpn_crt_server_key", nvram_set,"")\
    ENTRY("vpn_client_reneg", nvram_set,"-1")\
    ENTRY("wl1_HT_GI", nvram_set,"1")\
    ENTRY("wl0.3_key", nvram_set,"1")\
    ENTRY("wps_enable", nvram_set,"1")\
    ENTRY("ubifs_on", nvram_set,"1")\
    ENTRY("dms_enable", nvram_set,"1")\
    ENTRY("wl1.2_wme", nvram_set,"auto")\
    ENTRY("webdav_acc_lock", nvram_set,"0")\
    ENTRY("wl0.2_radius_port", nvram_set,"1812")\
    ENTRY("dhcp1_dns1_x", nvram_set,"")\
    ENTRY("wan_pppoe_passwd", nvram_set,"")\
    ENTRY("wl0_akm", nvram_set,"")\
    ENTRY("wan0_6rd_prefix", nvram_set,"")\
    ENTRY("vpn_client3_state", nvram_set,"")\
    ENTRY("wan_clientid_type", nvram_set,"0")\
    ENTRY("log_port", nvram_set,"514")\
    ENTRY("vpn_client_username", nvram_set,"")\
    ENTRY("custom_clientlist", nvram_set,"")\
    ENTRY("wl0.2_mode", nvram_set,"ap")\
    ENTRY("wan0_dns", nvram_set,"")\
    ENTRY("ddns_hostname_x_old", nvram_set,"")\
    ENTRY("wl_bw_enabled", nvram_set,"0")\
    ENTRY("wps_modelname", nvram_set,"Wi-Fi Protected Setup Router")\
    ENTRY("fw_dos_x", nvram_set,"0")\
    ENTRY("wl0_phrase_x", nvram_set,"")\
    ENTRY("wl1.2_bw_dl", nvram_set,"")\
    ENTRY("wl1.3_auth", nvram_set,"0")\
    ENTRY("lan_state_t", nvram_set,"2")\
    ENTRY("keyword_enable_x", nvram_set,"0")\
    ENTRY("webdav_last_login_info", nvram_set,"")\
    ENTRY("https_crt_gen", nvram_set,"0")\
    ENTRY("pptpd_sr_rulelist", nvram_set,"")\
    ENTRY("vpn_serverx_clientlist", nvram_set,"")\
    ENTRY("fb_total_size", nvram_set,"0")\
    ENTRY("wl1.3_wep_x", nvram_set,"0")\
    ENTRY("wl0_country_code", nvram_set,"CN")\
    ENTRY("btn_rst_gpio", nvram_set,"4114")\
    ENTRY("wl0_mumimo", nvram_set,"1")\
    ENTRY("apps_state_autorun", nvram_set,"")\
    ENTRY("emf_rtport_entry", nvram_set,"")\
    ENTRY("dhcp_dns1_x", nvram_set,"")\
    ENTRY("apps_local_space", nvram_set,"/rom")\
    ENTRY("Ate_version", nvram_set,"1.0")\
    ENTRY("vlan_pvid_list", nvram_set,"")\
    ENTRY("wl1_phrase_x", nvram_set,"")\
    ENTRY("usb_path3_diskmon_freq_time", nvram_set,"")\
    ENTRY("rstats_new", nvram_set,"0")\
    ENTRY("wl_mssid", nvram_set,"1")\
    ENTRY("wan_auth_x", nvram_set,"")\
    ENTRY("pptpd_dns1", nvram_set,"")\
    ENTRY("wl1_frag", nvram_set,"2346")\
    ENTRY("wan0_ppp_echo_interval", nvram_set,"6")\
    ENTRY("sysstate_msqid_to_d", nvram_set,"0")\
    ENTRY("webs_update_ts", nvram_set,"0")\
    ENTRY("led_lan2_gpio", nvram_set,"12331")\
    ENTRY("wan_nat_x", nvram_set,"1")\
    ENTRY("autofw_rulelist", nvram_set,"")\
    ENTRY("pptpd_dns2", nvram_set,"")\
    ENTRY("pptpd_clientlist", nvram_set,"")\
    ENTRY("wl0.2_wpa_psk", nvram_set,"")\
    ENTRY("wl_nmode_x", nvram_set,"0")\
    ENTRY("wl0.1_bw_dl", nvram_set,"")\
    ENTRY("HwVer", nvram_set,"")\
    ENTRY("wl_maclist_x", nvram_set,"")\
    ENTRY("lan_dnsenable_x", nvram_set,"0")\
    ENTRY("fb_transid", nvram_set,"123456789ABCDEF0")\
    ENTRY("wl0.2_wep_x", nvram_set,"0")\
    ENTRY("wan0_clientid", nvram_set,"")\
    ENTRY("url_mode_x", nvram_set,"0")\
    ENTRY("wl1.2_net_reauth", nvram_set,"36000")\
    ENTRY("wan0_ppp_echo_failure", nvram_set,"10")\
    ENTRY("restore_defaults", nvram_set,"0")\
    ENTRY("acs_ch13", nvram_set,"0")\
    ENTRY("wl0.3_radio", nvram_set,"1")\
    ENTRY("reboot_schedule", nvram_set,"00000000000")\
    ENTRY("diskformat_file_system", nvram_set,"tfat")\
    ENTRY("ipv6_get_dns", nvram_set,"")\
    ENTRY("wl1_wpa_gtk_rekey", nvram_set,"3600")\
    ENTRY("wl1.1_akm", nvram_set,"")\
    ENTRY("wan0_ifname", nvram_set,"eth0")\
    ENTRY("wl0.1_key", nvram_set,"1")\
    ENTRY("wl0.3_radius_key", nvram_set,"")\
    ENTRY("wl0.3_radius_port", nvram_set,"1812")\
    ENTRY("success_start_service", nvram_set,"1")\
    ENTRY("ohci_ports", nvram_set,"1-1 4-1")\
    ENTRY("wl0_atf", nvram_set,"0")\
    ENTRY("wl0.3_lanaccess", nvram_set,"off")\
    ENTRY("wl1.1_auth", nvram_set,"0")\
    ENTRY("wl1.2_bw_ul", nvram_set,"")\
    ENTRY("lan_auxstate_t", nvram_set,"0")\
    ENTRY("wl_atf_sta", nvram_set,"")\
    ENTRY("wan_pppoe_service", nvram_set,"")\
    ENTRY("filter_lw_time_x", nvram_set,"00002359")\
    ENTRY("vpn_server_plan", nvram_set,"1")\
    ENTRY("vpn_client_retry", nvram_set,"30")\
    ENTRY("wl0_nctrlsb", nvram_set,"1")\
    ENTRY("wl1_maclist_x", nvram_set,"")\
    ENTRY("wl_wme_apsd", nvram_set,"on")\
    ENTRY("keyword_sched", nvram_set,"000000")\
    ENTRY("cloud_sync", nvram_set,"")\
    ENTRY("usb_path3_diskmon_freq", nvram_set,"0")\
    ENTRY("env_path", nvram_set,"")\
    ENTRY("wl0.3_auth_mode", nvram_set,"none")\
    ENTRY("wl_radius_ipaddr", nvram_set,"")\
    ENTRY("PM_LETTER_PATH", nvram_set,"")\
    ENTRY("dev_fail_reboot", nvram_set,"3")\
    ENTRY("wl0.2_ssid", nvram_set,"ASUS_E8_2G_Guest2")\
    ENTRY("wl1.1_radius_ipaddr", nvram_set,"")\
    ENTRY("lan_gateway", nvram_set,"0.0.0.0")\
    ENTRY("usb_ohci", nvram_set,"1")\
    ENTRY("enable_webdav_lock", nvram_set,"0")\
    ENTRY("wl_lrc", nvram_set,"2")\
    ENTRY("wl1_crypto", nvram_set,"aes")\
    ENTRY("wl0_ifname", nvram_set,"ath0")\
    ENTRY("usb_storage", nvram_set,"1")\
    ENTRY("apps_state_switch", nvram_set,"")\
    ENTRY("lan_unit", nvram_set,"-1")\
    ENTRY("lan_domain", nvram_set,"")\
    ENTRY("temp_lang", nvram_set,"")\
    ENTRY("sshd_authkeys", nvram_set,"")\
    ENTRY("vpn_client_if", nvram_set,"tun")\
    ENTRY("vpn_client1_errno", nvram_set,"")\
    ENTRY("swpjverno", nvram_set,"")\
    ENTRY("ct_max", nvram_set,"300000")\
    ENTRY("lan_netmask_rt", nvram_set,"255.255.255.0")\
    ENTRY("ipv6_ipaddr", nvram_set,"")\
    ENTRY("wl0.1_bw_ul", nvram_set,"")\
    ENTRY("wl1.1_macmode", nvram_set,"disabled")\
    ENTRY("wan0_6rd_router", nvram_set,"")\
    ENTRY("w_Setting", nvram_set,"1")\
    ENTRY("webs_notif_flag", nvram_set,"")\
    ENTRY("wl_auth_mode_x", nvram_set,"psk2")\
    ENTRY("lan1_ipaddr", nvram_set,"192.168.2.1")\
    ENTRY("wl0.1_auth_mode_x", nvram_set,"open")\
    ENTRY("wl1.1_radius_key", nvram_set,"")\
    ENTRY("diskmon_freq_time", nvram_set,"")\
    ENTRY("ipv6_state_t", nvram_set,"0")\
    ENTRY("pptpd_broadcast", nvram_set,"0")\
    ENTRY("wan0_mroute", nvram_set,"")\
    ENTRY("wan_pppoe_mru", nvram_set,"1492")\
    ENTRY("fw_pt_l2tp", nvram_set,"1")\
    ENTRY("vpn_crt_server_ca", nvram_set,"")\
    ENTRY("wl1_expire", nvram_set,"0")\
    ENTRY("wl0.2_key1", nvram_set,"")\
    ENTRY("lan_route", nvram_set,"")\
    ENTRY("wl1_wdslist", nvram_set,"")\
    ENTRY("wl0.2_key2", nvram_set,"")\
    ENTRY("wl1.3_preauth", nvram_set,"")\
    ENTRY("fw_pt_sip", nvram_set,"1")\
    ENTRY("wl0_rast_sens_level", nvram_set,"1")\
    ENTRY("wl1_channel", nvram_set,"0")\
    ENTRY("wl0.2_key3", nvram_set,"")\
    ENTRY("wan_gateway", nvram_set,"0.0.0.0")\
    ENTRY("wl0_mode", nvram_set,"ap")\
    ENTRY("wl0_nmode_x", nvram_set,"0")\
    ENTRY("wl0.2_key4", nvram_set,"")\
    ENTRY("wl1.1_infra", nvram_set,"1")\
    ENTRY("wl1.3_lanaccess", nvram_set,"off")\
    ENTRY("ftp_ports", nvram_set,"")\
    ENTRY("wl_txbf", nvram_set,"1")\
    ENTRY("dhcp_start", nvram_set,"192.168.50.2")\
    ENTRY("wan_ppp_echo_failure", nvram_set,"10")\
    ENTRY("dms_friendly_name", nvram_set,"RT-ACRH17-00E8")\
    ENTRY("vpn_server_unit", nvram_set,"1")\
    ENTRY("ipv6_prefix", nvram_set,"")\
    ENTRY("wl0_user_rssi", nvram_set,"0")\
    ENTRY("wl_txpower", nvram_set,"100")\
    ENTRY("webdav_lock_interval", nvram_set,"2")\
    ENTRY("https_crt_cn", nvram_set,"")\
    ENTRY("ipv6_ifdev", nvram_set,"ppp")\
    ENTRY("wl1.3_auth_mode", nvram_set,"none")\
    ENTRY("lan1_route", nvram_set,"")\
    ENTRY("pptpd_enable", nvram_set,"0")\
    ENTRY("vpn_server_nm", nvram_set,"255.255.255.0")\
    ENTRY("vpn_client_digest", nvram_set,"SHA1")\
    ENTRY("PM_SMTP_AUTH_PASS", nvram_set,"")\
    ENTRY("wl0_ap_isolate", nvram_set,"0")\
    ENTRY("dhcp_end", nvram_set,"192.168.50.254")\
    ENTRY("vpn_client_addr", nvram_set,"")\
    ENTRY("vpn_crt_client_key", nvram_set,"")\
    ENTRY("ipv6_service", nvram_set,"disabled")\
    ENTRY("gvlan_rulelist", nvram_set,"")\
    ENTRY("aae_support", nvram_set,"1")\
    ENTRY("wl_akm", nvram_set,"")\
    ENTRY("VPNClient_rule", nvram_set,"")\
    ENTRY("PM_USE_TLS", nvram_set,"true")\
    ENTRY("wl1_subunit", nvram_set,"-1")\
    ENTRY("wl0.2_bw_enabled", nvram_set,"0")\
    ENTRY("dhcp_lease", nvram_set,"86400")\
    ENTRY("wan_vendorid", nvram_set,"")\
    ENTRY("restrict_rulelist", nvram_set,"")\
    ENTRY("wl0_wme_no_ack", nvram_set,"off")\
    ENTRY("wl1.1_wpa_psk", nvram_set,"")\
    ENTRY("vpn_server1_errno", nvram_set,"")\
    ENTRY("app_access", nvram_set,"0")\
    ENTRY("location_code", nvram_set,"CN")\
    ENTRY("usb_fat_opt", nvram_set,"")\
    ENTRY("usb_fs_ntfs", nvram_set,"1")\
    ENTRY("wl0_atf_sta", nvram_set,"")\
    ENTRY("wl1_rts", nvram_set,"2347")\
    ENTRY("wan0_pppoe_relay", nvram_set,"0")\
    ENTRY("usb_fatfs_mod", nvram_set,"open")\
    ENTRY("smbd_user", nvram_set,"nas")\
    ENTRY("ttl_inc_enable", nvram_set,"0")\
    ENTRY("wl1_radio_time_x", nvram_set,"00002359")\
    ENTRY("yadns_enable_x", nvram_set,"0")\
    ENTRY("qos_rulelist", nvram_set,"<Web Surf>>80>tcp>0~512>0<HTTPS>>443>tcp>0~512>0<File Transfer>>80>tcp>512~>3<File Transfer>>443>tcp>512~>3")\
    ENTRY("qos_sticky", nvram_set,"1")\
    ENTRY("MULTIFILTER_URL_ENABLE", nvram_set,"")\
    ENTRY("filter_lwlist", nvram_set,"")\
    ENTRY("wl0.2_auth_mode_x", nvram_set,"open")\
    ENTRY("wl0.2_wpa_gtk_rekey", nvram_set,"3600")\
    ENTRY("reload_svc_radio", nvram_set,"1")\
    ENTRY("webs_last_info", nvram_set,"")\
    ENTRY("ipv6_tun_addrlen", nvram_set,"64")\
    ENTRY("wl1.3_ap_isolate", nvram_set,"0")\
    ENTRY("wan0_xipaddr", nvram_set,"0.0.0.0")\
    ENTRY("sshd_hostkey", nvram_set,"AAAAB3NzaC1yc2EAAAADAQABAAABAQCWFfmqRFZzJS2Q0IDAiJB8iN7UtOdhjjGZUDvaydyebwnR3Wc9XQDttm9YxodXSLg7xStq1Ucj+n0N1ZgYdbz/UMvLO5nY8PTwV2g0+CM10jKxkPvjCNwcXjKg+Xrk1Nus8RfeTvz+mvl5FyXLVslvxflyZMYRNGTnnDgZBD5Ji7N4nwaLek6aAAvu33jmWdRPuTAHD+oAhdEnv7ypRm5Eq34GOKpyI6njftt7jo241CD1hVAcD8sPhN8ENw8EIToZxVahd4R1d3f76c1zkr6TtVYKdGubx0CpHR95kVAfGbnzXlbus4Z/DK2DFRsIarybQ0sFt1ZXAJgrVFtspFEhAAABAAL2qX6wwWB+DKCYNl+e3rP/z58VeJ9k83Kkmn71JxCfjosE3zjPZyEafee7yVC6Vk1zVOpzzkceB0W8eMesXPxRXgnL+itmBB8iCbQojWju1uqJy2h57H84prEmJfSiZZlMTClrB7y3BourHuddRgZZi1W0etL8hOzMGVE4o8p30l+V+dEKLws+xUy9Wn+CvnqiFj8MvTospijeMC4b/8ZxM52L6U091cBzP66TIwQLQ24dooJCPzFamCy4HW/m1luKtpakuHTHNySHHo+Vwkctudgh8ZJNQz60nz7f+yuoOCPyByok0UidwPb2MGT234OJ2ZOqxWosQe97tVoUl9EAAACBAPAI9UD0L8XMVhNc/IGMTDvUB8XpfAPgy1wVY1tuz52PE4T2cTBVYVx0YfDet/NW4TKkqI513/6Vpj8b1AffqGBg2yzuwBpr4lKF+4uIJGvIOIc5sQjQLamfuxIwvaR1wbEM6BAu4eC6Lteh7PUZxXsDXIl/ysKQfZ9PeZccqeWxAAAAgQCgEXc4wpP5K6sTKcMrAul7YKO5/FiCLUEl8ziNIu/PIEBi2YtxIWSrhLNf4nKCdZPUtXgTPJInIoi/98KPQZjiWgfMedeNvtHVOx/VJhXJOAT1H3dLJ+s70fS//ydEna55wKGnHmIy7nCYLUPSqpPNZmwXzyy+UbkE50AmBMpOcQ")\
    ENTRY("et1macaddr", nvram_set,"04:D4:C4:D4:00:EC")\
    ENTRY("wl0_HT_TxStream", nvram_set,"2")\
    ENTRY("wl0_nband", nvram_set,"2")\
    ENTRY("filter_lw_date_x", nvram_set,"1111111")\
    ENTRY("enable_webdav", nvram_set,"0")\
    ENTRY("share_link_param", nvram_set,"")\
    ENTRY("apps_dev", nvram_set,"")\
    ENTRY("apps_state_update", nvram_set,"")\
    ENTRY("ipv6_gateway", nvram_set,"")\
    ENTRY("apps_depend_action", nvram_set,"")\
    ENTRY("rc_service_pid", nvram_set,"")\
    ENTRY("ntp_server0", nvram_set,"pool.ntp.org")\
    ENTRY("dms_dir", nvram_set,"/mnt")\
    ENTRY("wl0_pmk_cache", nvram_set,"60")\
    ENTRY("force_change", nvram_set,"1")\
    ENTRY("AllLED", nvram_set,"1")\
    ENTRY("ntp_server1", nvram_set,"time.nist.gov")\
    ENTRY("filter_lw_icmp_x", nvram_set,"")\
    ENTRY("pptpd_server", nvram_set,"")\
    ENTRY("vpn_client_rg", nvram_set,"0")\
    ENTRY("fb_attach_cfgfile", nvram_set,"")\
    ENTRY("lan_netmask", nvram_set,"255.255.255.0")\
    ENTRY("reboot_schedule_enable", nvram_set,"0")\
    ENTRY("computer_name", nvram_set,"RT-ACRH17-00E8")\
    ENTRY("st_samba_workgroup", nvram_set,"WORKGROUP")\
    ENTRY("fb_attach_syslog", nvram_set,"")\
    ENTRY("ipv6_prefix_length", nvram_set,"64")\
    ENTRY("wl0.1_crypto", nvram_set,"aes")\
    ENTRY("wl1.2_mode", nvram_set,"ap")\
    ENTRY("rc_support", nvram_set,"mssid 2.4G 5G update usbX1 qcawifi switchctrl manual_stb 11AC pwrctrl noitunes nodm reboot_schedule ipv6 ipv6pt PARENTAL2 loclist pptpd openvpnd utf8_ssid frs_feedback email media appnet findasus atf diskutility HTTPS ssh vpnc optimize_xbox wps_multiband user_low_rssi tcode usericon cfg_wps_btn stainfo noiptv")\
    ENTRY("wl_nband", nvram_set,"1")\
    ENTRY("wan_gateway_x", nvram_set,"0.0.0.0")\
    ENTRY("vpn_client_comp", nvram_set,"-1")\
    ENTRY("PM_hour", nvram_set,"0")\
    ENTRY("lan1_hwnames", nvram_set,"")\
    ENTRY("http_username", nvram_set,"qiangwang")\
    ENTRY("vpnc_dnsenable_x", nvram_set,"1")\
    ENTRY("vpn_server_reneg", nvram_set,"-1")\
    ENTRY("wl0_ssid", nvram_set,"Chunqiu_2G")\
    ENTRY("wl0_dtim", nvram_set,"1")\
    ENTRY("wl1_key", nvram_set,"1")\
    ENTRY("wl1_mumimo", nvram_set,"1")\
    ENTRY("st_samba_force_mode", nvram_set,"4")\
    ENTRY("rstats_offset", nvram_set,"1")\
    ENTRY("vpn_server_firewall", nvram_set,"auto")\
    ENTRY("vpn_server_digest", nvram_set,"SHA1")\
    ENTRY("wl0_bw_dl", nvram_set,"")\
    ENTRY("wan0_6rd_prefixlen", nvram_set,"")\
    ENTRY("wl1_mrate_x", nvram_set,"0")\
    ENTRY("wl1_wep_x", nvram_set,"0")\
    ENTRY("wl1.1_crypto", nvram_set,"aes")\
    ENTRY("wan0_pppoe_ifname", nvram_set,"")\
    ENTRY("nat_state", nvram_set,"1")\
    ENTRY("wl_bw", nvram_set,"1")\
    ENTRY("wl_atf", nvram_set,"0")\
    ENTRY("wan_phytype", nvram_set,"")\
    ENTRY("keyword_rulelist", nvram_set,"")\
    ENTRY("wl0_vifnames", nvram_set,"wl0.1 wl0.2 wl0.3")\
    ENTRY("http_lanport", nvram_set,"80")\
    ENTRY("wl_bw_dl", nvram_set,"")\
    ENTRY("wl_plcphdr", nvram_set,"long")\
    ENTRY("PM_day", nvram_set,"0")\
    ENTRY("wl0_txpower", nvram_set,"100")\
    ENTRY("wl0.1_expire", nvram_set,"0")\
    ENTRY("autodet_auxstate", nvram_set,"0")\
    ENTRY("switch_wan1prio", nvram_set,"0")\
    ENTRY("wl_macmode", nvram_set,"disabled")\
    ENTRY("wl_mimo_preamble", nvram_set,"mm")\
    ENTRY("lan_dns2_x", nvram_set,"")\
    ENTRY("lan1_wins", nvram_set,"")\
    ENTRY("wl0.3_auth_mode_x", nvram_set,"open")\
    ENTRY("wl1.1_bss_enabled", nvram_set,"0")\
    ENTRY("wl1_vifnames", nvram_set,"wl1.1 wl1.2 wl1.3")\
    ENTRY("wan_hwname", nvram_set,"")\
    ENTRY("ipv6_dnsenable", nvram_set,"1")\
    ENTRY("wl1_HT_TxStream", nvram_set,"4")\
    ENTRY("wl_implicitxbf", nvram_set,"0")\
    ENTRY("lan_lease", nvram_set,"86400")\
    ENTRY("wl0_key1", nvram_set,"")\
    ENTRY("wl1_sched", nvram_set,"000000")\
    ENTRY("wl1.1_expire", nvram_set,"0")\
    ENTRY("wl0_key2", nvram_set,"")\
    ENTRY("wan0_hostname", nvram_set,"")\
    ENTRY("wan0_proto_t", nvram_set,"dhcp")\
    ENTRY("HwId", nvram_set,"")\
    ENTRY("wl2_vifnames", nvram_set,"")\
    ENTRY("wl0_key3", nvram_set,"")\
    ENTRY("wl0.1_preauth", nvram_set,"")\
    ENTRY("wl0.2_net_reauth", nvram_set,"36000")\
    ENTRY("vpn_client4_errno", nvram_set,"")\
    ENTRY("switch_wan2tagid", nvram_set,"")\
    ENTRY("log_size", nvram_set,"256")\
    ENTRY("mfp_ip_monopoly", nvram_set,"")\
    ENTRY("wl0_key4", nvram_set,"")\
    ENTRY("wl1_radius_key", nvram_set,"")\
    ENTRY("dms_dbcwd", nvram_set,"")\
    ENTRY("wl_lanaccess", nvram_set,"off")\
    ENTRY("webdav_aidisk", nvram_set,"0")\
    ENTRY("PM_MAIL_TARGET", nvram_set,"")\
    ENTRY("wl0_guest_num", nvram_set,"10")\
    ENTRY("wl0.3_macmode", nvram_set,"disabled")\
    ENTRY("wl1.2_key", nvram_set,"1")\
    ENTRY("freeze_duck", nvram_set,"0")\
    ENTRY("wl3_vifnames", nvram_set,"")\
    ENTRY("lan1_lease", nvram_set,"86400")\
    ENTRY("wan_hwaddr_x", nvram_set,"")\
    ENTRY("ddns_username_x", nvram_set,"")\
    ENTRY("ipv6_6rd_prefix", nvram_set,"")\
    ENTRY("wl0_bw_ul", nvram_set,"")\
    ENTRY("led_usb_gpio", nvram_set,"255")\
    ENTRY("wl_auth_mode", nvram_set,"none")\
    ENTRY("wl0_vifs", nvram_set,"")\
    ENTRY("wl1.2_ssid", nvram_set,"ASUS_E8_5G_Guest2")\
    ENTRY("btn_wps_gpio", nvram_set,"4107")\
    ENTRY("wl1_ifname", nvram_set,"ath1")\
    ENTRY("qos_orules", nvram_set,"")\
    ENTRY("wl1_bcn", nvram_set,"100")\
    ENTRY("usb_path2_diskmon_freq", nvram_set,"0")\
    ENTRY("sshd_pass", nvram_set,"1")\
    ENTRY("wl1_radio_date_x", nvram_set,"1111111")\
    ENTRY("wan_ppp_echo", nvram_set,"0")\
    ENTRY("misc_lpr_x", nvram_set,"0")\
    ENTRY("vpnc_heartbeat_x", nvram_set,"")\
    ENTRY("vpn_crt_server_dh", nvram_set,"")\
    ENTRY("wl_bw_ul", nvram_set,"")\
    ENTRY("udpxy_clients", nvram_set,"10")\
    ENTRY("wl1_lanaccess", nvram_set,"off")\
    ENTRY("wan0_dhcpenable_x", nvram_set,"1")\
    ENTRY("wl_wpa_psk", nvram_set,"742649264")\
    ENTRY("mr_enable_x", nvram_set,"0")\
    ENTRY("wan_pppoe_relay", nvram_set,"0")\
    ENTRY("sp_battle_ips", nvram_set,"")\
    ENTRY("http_passwd", nvram_set,"2022qwb")\
    ENTRY("ipv6_sbstate_t", nvram_set,"0")\
    ENTRY("ddns_last_wan_unit", nvram_set,"-1")\
    ENTRY("led_2g_gpio", nvram_set,"12340")\
    ENTRY("webdav_proxy", nvram_set,"0")\
    ENTRY("apps_swap_file", nvram_set,".swap")\
    ENTRY("ipv6_debug", nvram_set,"0")\
    ENTRY("wl1_auth_mode", nvram_set,"none")\
    ENTRY("lan_stp", nvram_set,"1")\
    ENTRY("wan_enable", nvram_set,"1")\
    ENTRY("usb_automount", nvram_set,"1")\
    ENTRY("Ate_total_fail", nvram_set,"10")\
    ENTRY("wl1.2_bss_enabled", nvram_set,"0")\
    ENTRY("odmpid", nvram_set,"RT-ACRH17")\
    ENTRY("script_usbhotplug", nvram_set,"")\
    ENTRY("st_webdav_mode", nvram_set,"2")\
    ENTRY("ipv6_tun_peer", nvram_set,"")\
    ENTRY("wl0_HT_GI", nvram_set,"1")\
    ENTRY("wl0.2_unit", nvram_set,"0.2")\
    ENTRY("wl0.3_akm", nvram_set,"")\
    ENTRY("wl0.3_radius_ipaddr", nvram_set,"")\
    ENTRY("wl_mode", nvram_set,"ap")\
    ENTRY("ct_timeout", nvram_set,"600 30")\
    ENTRY("ddns_transfer", nvram_set,"")\
    ENTRY("fw_lw_enable_x", nvram_set,"0")\
    ENTRY("usb_fs_ext3", nvram_set,"1")\
    ENTRY("ftp_lang", nvram_set,"EN")\
    ENTRY("wl0.1_radius_key", nvram_set,"")\
    ENTRY("wl1.2_key1", nvram_set,"")\
    ENTRY("switch_wan0tagid", nvram_set,"")\
    ENTRY("wl0.2_wme", nvram_set,"auto")\
    ENTRY("wl1.1_radius_port", nvram_set,"1812")\
    ENTRY("wl1.2_key2", nvram_set,"")\
    ENTRY("wan0_pppoe_passwd", nvram_set,"")\
    ENTRY("apps_new_arm", nvram_set,"1")\
    ENTRY("wl_turbo_qam_brcm_intop", nvram_set,"1")\
    ENTRY("qos_ibw", nvram_set,"")\
    ENTRY("wollist", nvram_set,"")\
    ENTRY("wl0_radio_time2_x", nvram_set,"00002359")\
    ENTRY("wl0_wdsapply_x", nvram_set,"0")\
    ENTRY("wl1.2_key3", nvram_set,"")\
    ENTRY("atcover_sip", nvram_set,"0")\
    ENTRY("wl_atf_mode", nvram_set,"0")\
    ENTRY("fw_pt_rtsp", nvram_set,"1")\
    ENTRY("btn_rst", nvram_set,"0")\
    ENTRY("wl0_closed", nvram_set,"0")\
    ENTRY("wl0_plcphdr", nvram_set,"long")\
    ENTRY("wl1_optimizexbox", nvram_set,"0")\
    ENTRY("wl0.3_wpa_psk", nvram_set,"")\
    ENTRY("wl1.2_key4", nvram_set,"")\
    ENTRY("vpn_client2_state", nvram_set,"")\
    ENTRY("wl_wpa_gtk_rekey", nvram_set,"3600")\
    ENTRY("wl_HT_GI", nvram_set,"1")\
    ENTRY("wl0_macmode", nvram_set,"disabled")\
    ENTRY("wl0_assoc_retry_max", nvram_set,"3")\
    ENTRY("wl0_turbo_qam", nvram_set,"1")\
    ENTRY("wl0.3_infra", nvram_set,"1")\
    ENTRY("wl1.1_bw_dl", nvram_set,"")\
    ENTRY("wl1.1_wpa_gtk_rekey", nvram_set,"3600")\
    ENTRY("sshd_ecdsakey", nvram_set,"AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBC4t70mdIPBaPGTUyN+bsTrYToVa0YDXLY/M5kOWjkerKIcvK/7FcsrNWdKXq1XdZowGx8YQFAohodn78qvy0IwAAAAhAJ6ZLPnByP3/VPir9L4pDjEAcwvjMr3tLjVfVItwuMyg")\
    ENTRY("dms_sas", nvram_set,"0")\
    ENTRY("wl1.2_wep_x", nvram_set,"0")\
    ENTRY("wan0_ppp_phy", nvram_set,"1")\
    ENTRY("wan0_xgateway", nvram_set,"0.0.0.0")\
    ENTRY("led_usb3_gpio", nvram_set,"255")\
    ENTRY("vpnc_proto", nvram_set,"disable")\
    ENTRY("wl1.3_radio", nvram_set,"1")\
    ENTRY("dns_delay_round", nvram_set,"2")\
    ENTRY("vpn_client_tlscrypt", nvram_set,"0")\
    ENTRY("smbd_cpage", nvram_set,"936")\
    ENTRY("diskmon_force_stop", nvram_set,"0")\
    ENTRY("vpnc_sbstate_t", nvram_set,"0")\
    ENTRY("upnp_ssdp_interval", nvram_set,"60")\
    ENTRY("qos_type", nvram_set,"0")\
    ENTRY("enable_samba", nvram_set,"1")\
    ENTRY("wl0_bw_enabled", nvram_set,"0")\
    ENTRY("time_zone_dst", nvram_set,"0")\
    ENTRY("Ate_dev_check", nvram_set,"0")\
    ENTRY("smbd_nlsmod", nvram_set,"nls_cp936")\
    ENTRY("upnp_clean", nvram_set,"1")\
    ENTRY("ipv6_6rd_router", nvram_set,"0.0.0.0")\
    ENTRY("wl1_nctrlsb", nvram_set,"lower")\
    ENTRY("wl0.1_wep_x", nvram_set,"0")\
    ENTRY("wl0.1_lanaccess", nvram_set,"off")\
    ENTRY("lan_hwaddr", nvram_set,"04:D4:C4:D4:00:EC")\
    ENTRY("lan_ipaddr_rt", nvram_set,"192.168.50.1")\
    ENTRY("share_link_host", nvram_set,"")\
    ENTRY("dms_dir_type_x", nvram_set,"")\
    ENTRY("vpn_server_ccd_excl", nvram_set,"0")\
    ENTRY("wl1.3_bss_enabled", nvram_set,"0")\
    ENTRY("wan0_auth_x", nvram_set,"")\
    ENTRY("wan_dns", nvram_set,"")\
    ENTRY("wan_pppoe_options_x", nvram_set,"")\
    ENTRY("apps_ipkg_server", nvram_set,"http://nw-dlcdnet.asus.com/asusware/arm/stable")\
    ENTRY("PM_SMTP_AUTH", nvram_set,"LOGIN")\
    ENTRY("wl0_radio_time_x", nvram_set,"00002359")\
    ENTRY("wl0.1_auth_mode", nvram_set,"none")\
    ENTRY("wl0.2_radio", nvram_set,"1")\
    ENTRY("dms_dbdir", nvram_set,"/tmp/mnt/Smile-Pro/.minidlna")\
    ENTRY("vpn_server_dhcp", nvram_set,"1")\
    ENTRY("PM_SMTP_AUTH_USER", nvram_set,"")\
    ENTRY("yadns_rulelist", nvram_set,"")\
    ENTRY("apps_wget_timeout", nvram_set,"30")\
    ENTRY("wl0_mode_x", nvram_set,"0")\
    ENTRY("wl0.1_akm", nvram_set,"")\
    ENTRY("wl0.3_ap_isolate", nvram_set,"0")\
    ENTRY("wl1.2_radius_port", nvram_set,"1812")\
    ENTRY("wan0_pppoe_ac", nvram_set,"")\
    ENTRY("innerver", nvram_set,"3.0.0.4.382_52517-gb4d36a6")\
    ENTRY("wl_ssid", nvram_set,"Chunqiu_5G")\
    ENTRY("wl_dtim", nvram_set,"1")\
    ENTRY("wan_dns2_x", nvram_set,"")\
    ENTRY("vpn_client_adns", nvram_set,"0")\
    ENTRY("ipv6_prefix_s", nvram_set,"")\
    ENTRY("wl1.1_bw_ul", nvram_set,"")\
    ENTRY("wl1.2_macmode", nvram_set,"disabled")\
    ENTRY("wl1.3_bw_enabled", nvram_set,"0")\
    ENTRY("vpn_server2_state", nvram_set,"")\
    ENTRY("lan_wps_oob", nvram_set,"disabled")\
    ENTRY("restwifi_qis", nvram_set,"1")\
    ENTRY("wan_pppoe_mtu", nvram_set,"1492")\
    ENTRY("usb_ext_opt", nvram_set,"")\
    ENTRY("wl0_wpa_psk", nvram_set,"742649264")\
    ENTRY("wl1_frameburst", nvram_set,"off")\
    ENTRY("wl0.1_ifname", nvram_set,"")\
    ENTRY("wl0.2_crypto", nvram_set,"aes")\
    ENTRY("nvramver", nvram_set,"1")\
    ENTRY("x_Setting", nvram_set,"1")\
    ENTRY("vpn_clientx_eas", nvram_set,"")\
    ENTRY("apps_depend_action_target", nvram_set,"")\
    ENTRY("led_logo_gpio", nvram_set,"255")\
    ENTRY("wl_atf_ssid", nvram_set,"")\
    ENTRY("vpn_server_port", nvram_set,"")\
    ENTRY("printer_status_t", nvram_set,"")\
    ENTRY("iptv_port_settings", nvram_set,"12")\
    ENTRY("wan_vpndhcp", nvram_set,"1")\
    ENTRY("upnp_clean_interval", nvram_set,"600")\
    ENTRY("wl1.1_ifname", nvram_set,"")\
    ENTRY("wl1.2_crypto", nvram_set,"aes")\
    ENTRY("usb_printer", nvram_set,"1")\
    ENTRY("wl0.2_auth", nvram_set,"0")\
    ENTRY("fb_email_dbg", nvram_set,"")\
    ENTRY("wl0_mbss", nvram_set,"")\
    ENTRY("wl1_bw", nvram_set,"1")\
    ENTRY("wan_netmask_x", nvram_set,"0.0.0.0")\
    ENTRY("pptpd_wins1", nvram_set,"")\
    ENTRY("Ate_power_on_off_enable", nvram_set,"0")\
    ENTRY("printer_user_t", nvram_set,"")\
    ENTRY("wl_key1", nvram_set,"")\
    ENTRY("lan_wps_reg", nvram_set,"enabled")\
    ENTRY("wan_proto", nvram_set,"dhcp")\
    ENTRY("rstats_stime", nvram_set,"1")\
    ENTRY("pptpd_wins2", nvram_set,"")\
    ENTRY("vpn_server_r1", nvram_set,"192.168.1.50")\
    ENTRY("wl1_nmode_x", nvram_set,"0")\
    ENTRY("wl0.2_expire", nvram_set,"0")\
    ENTRY("wl1.1_ap_isolate", nvram_set,"0")\
    ENTRY("wl_key2", nvram_set,"")\
    ENTRY("wan_gw_mac", nvram_set,"")\
    ENTRY("usb_usb2", nvram_set,"1")\
    ENTRY("st_max_user", nvram_set,"5")\
    ENTRY("vpn_server_r2", nvram_set,"192.168.1.55")\
    ENTRY("Ate_continue_fail", nvram_set,"3")\
    ENTRY("wl1.1_lanaccess", nvram_set,"off")\
    ENTRY("webs_state_update", nvram_set,"")\
    ENTRY("wl0_unit", nvram_set,"0")\
    ENTRY("wl_key3", nvram_set,"")\
    ENTRY("usb_usb3", nvram_set,"0")\
    ENTRY("wan0_pppoe_mru", nvram_set,"1492")\
    ENTRY("ddns_ipaddr", nvram_set,"")\
    ENTRY("time_zone_x", nvram_set,"GMT-8")\
    ENTRY("wl_country_code", nvram_set,"CN")\
    ENTRY("secret_code", nvram_set,"10830222")\
    ENTRY("wl_key4", nvram_set,"")\
    ENTRY("vpn_client_cn", nvram_set,"")\
    ENTRY("wl1.1_auth_mode", nvram_set,"none")\
    ENTRY("wl1.2_expire", nvram_set,"0")\
    ENTRY("wan0_state_t", nvram_set,"4")\
    ENTRY("buildno", nvram_set,"382")\
    ENTRY("wl_hwaddr", nvram_set,"04:D4:C4:D4:00:EC")\
    ENTRY("subnet_rulelist", nvram_set,"")\
    ENTRY("ddns_cache", nvram_set,"")\
    ENTRY("ddns_regular_period", nvram_set,"60")\
    ENTRY("asus_mfg", nvram_set,"0")\
    ENTRY("ipv6_dhcp_end", nvram_set,"")\
    ENTRY("wl1.2_wpa_psk", nvram_set,"")\
    ENTRY("wl1.3_radius_port", nvram_set,"1812")\
    ENTRY("wan_ipaddr_x", nvram_set,"0.0.0.0")\
    ENTRY("ddns_enable_x", nvram_set,"0")\
    ENTRY("MULTIFILTER_ALL", nvram_set,"0")\
    ENTRY("rstats_exclude", nvram_set,"")\
    ENTRY("vpn_server_verb", nvram_set,"3")\
    ENTRY("wl0_bss_enabled", nvram_set,"1")\
    ENTRY("wl1_atf_sta", nvram_set,"")\
    ENTRY("led_wan_gpio", nvram_set,"8253")\
    ENTRY("usb_ntfs_opt", nvram_set,"")\
    ENTRY("enable_cloudsync", nvram_set,"0")\
    ENTRY("ipv6_autoconf_type", nvram_set,"0")\
    ENTRY("wl1_lrc", nvram_set,"2")\
    ENTRY("wan0_xnetmask", nvram_set,"0.0.0.0")\
    ENTRY("led_5g_gpio", nvram_set,"12342")\
    ENTRY("lan1_stp", nvram_set,"1")\
    ENTRY("PM_MAIL_SUBJECT", nvram_set,"")\
    ENTRY("ddns_update_by_wdog", nvram_set,"")\
    ENTRY("wanports_mask", nvram_set,"32")\
    ENTRY("vpn_server_hmac", nvram_set,"-1")\
    ENTRY("fb_feedbackcount", nvram_set,"0")\
    ENTRY("wl1.2_radius_ipaddr", nvram_set,"")\
    ENTRY("apps_state_stop", nvram_set,"")\
    ENTRY("wan_pppoe_idletime", nvram_set,"0")\
    ENTRY("wan_ppp_echo_interval", nvram_set,"6")\
    ENTRY("qos_syn", nvram_set,"on")\
    ENTRY("autodet_state", nvram_set,"")\
    ENTRY("wps_band_x", nvram_set,"0")\
    ENTRY("vpn_crt_server_ca_key", nvram_set,"")\
    ENTRY("enable_samba_tuxera", nvram_set,"0")\
    ENTRY("webs_state_odm", nvram_set,"0")\
    ENTRY("productid", nvram_set,"RT-AC82U")\
    ENTRY("local_domain", nvram_set,"router.asus.com")\
    ENTRY("usb_irq_thresh", nvram_set,"0")\
    ENTRY("wl0_radio_date_x", nvram_set,"1111111")\
    ENTRY("lan1_gateway", nvram_set,"192.168.2.1")\
    ENTRY("usb_path1_diskmon_freq", nvram_set,"0")\
    ENTRY("rstats_data", nvram_set,"")\
    ENTRY("vpn_client_crypt", nvram_set,"tls")\
    ENTRY("PM_title", nvram_set,"")\
    ENTRY("wl1.3_net_reauth", nvram_set,"36000")\
    ENTRY("vpn_client5_state", nvram_set,"")\
    ENTRY("mr_altnet_x", nvram_set,"")\
    ENTRY("PM_target", nvram_set,"")\
    ENTRY("wl1_txbf", nvram_set,"1")\
    ENTRY("HwBom", nvram_set,"")\
    ENTRY("vpn_server_rgw", nvram_set,"0")\
    ENTRY("vpn_client_cipher", nvram_set,"default")\
    ENTRY("wl0_timesched", nvram_set,"0")\
    ENTRY("wl1.1_auth_mode_x", nvram_set,"open")\
    ENTRY("qos_ack", nvram_set,"on")\
    ENTRY("qos_burst0", nvram_set,"")\
    ENTRY("diskmon_freq", nvram_set,"0")\
    ENTRY("wl1.2_unit", nvram_set,"1.2")\
    ENTRY("3rd-party", nvram_set,"")\
    ENTRY("qos_burst1", nvram_set,"")\
    ENTRY("PM_LETTER_CONTENT", nvram_set,"")\
    ENTRY("fb_serviceno", nvram_set,"")\
    ENTRY("log_level", nvram_set,"6")\
    ENTRY("telnetd_enable", nvram_set,"1")\
    ENTRY("vpn_loglevel", nvram_set,"3")\
    ENTRY("wl0_bw", nvram_set,"1")\
    ENTRY("wan0_gateway", nvram_set,"0.0.0.0")\
    ENTRY("vpn_server_igncrt", nvram_set,"0")\
    ENTRY("fb_attach_wlanlog", nvram_set,"")\
    ENTRY("wl0_igs", nvram_set,"0")\
    ENTRY("wl1_closed", nvram_set,"0")\
    ENTRY("apps_state_remove", nvram_set,"")\
    ENTRY("extendno_org", nvram_set,"52517-gb4d36a6")\
    ENTRY("wps_mfstring", nvram_set,"ASUSTeK Computer Inc.")\
    ENTRY("wan_hwaddr", nvram_set,"04:D4:C4:D4:00:E8")\
    ENTRY("MULTIFILTER_MACFILTER_DAYTIME", nvram_set,"")\
    ENTRY("fb_comment", nvram_set,"")\
    ENTRY("wl1_bss_enabled", nvram_set,"1")\
    ENTRY("wl1.3_wme", nvram_set,"auto")\
    ENTRY("ntp_ready", nvram_set,"0")\
    ENTRY("sr_enable_x", nvram_set,"0")\
    ENTRY("misc_http_x", nvram_set,"0")\
    ENTRY("wl_user_rssi", nvram_set,"0")\
    ENTRY("wan0_gateway_x", nvram_set,"0.0.0.0")\
    ENTRY("lan_ifnames", nvram_set,"eth1 ath0 ath1")\
    ENTRY("wl_phrase_x", nvram_set,"")\
    ENTRY("enable_webdav_captcha", nvram_set,"0")\
    ENTRY("wl1_akm", nvram_set,"")\
    ENTRY("wl1_txpower", nvram_set,"100")\
    ENTRY("wl0.3_bw_dl", nvram_set,"")\
    ENTRY("lan_dns", nvram_set,"")\
    ENTRY("lan_dns1_x", nvram_set,"")\
    ENTRY("udpxy_enable_x", nvram_set,"0")\
    ENTRY("fb_email", nvram_set,"")\
    ENTRY("fb_pdesc", nvram_set,"")\
    ENTRY("wl0_optimizexbox", nvram_set,"0")\
    ENTRY("switch_stb_x", nvram_set,"0")\
    ENTRY("PM_SMTP_PORT", nvram_set,"")\
    ENTRY("wl0_wme", nvram_set,"auto")\
    ENTRY("wl0_radius_port", nvram_set,"1812")\
    ENTRY("wl0_wep_x", nvram_set,"0")\
    ENTRY("mr_qleave_x", nvram_set,"0")\
    ENTRY("upnp_port", nvram_set,"0")\
    ENTRY("usb_hfs_opt", nvram_set,"")\
    ENTRY("rstats_path", nvram_set,"")\
    ENTRY("vpn_server_ccd_val", nvram_set,"")\
    ENTRY("wl0.3_mode", nvram_set,"ap")\
    ENTRY("aae_enable", nvram_set,"2")\
    ENTRY("webs_state_info", nvram_set,"")\
    ENTRY("restart_fwl", nvram_set,"0")\
    ENTRY("ddns_wildcard_x", nvram_set,"0")\
    ENTRY("sshd_port", nvram_set,"22")\
    ENTRY("upnp_min_port_int", nvram_set,"1024")\
    ENTRY("ipv6_rtr_addr", nvram_set,"")\
    ENTRY("ipv6_prefix_length_s", nvram_set,"64")\
    ENTRY("wl0_radius_ipaddr", nvram_set,"")\
    ENTRY("wl1_radio", nvram_set,"1")\
    ENTRY("wl0.2_preauth", nvram_set,"")\
    ENTRY("wl1.2_radius_key", nvram_set,"")\
    ENTRY("ipv6_dhcp_pd", nvram_set,"1")\
    ENTRY("wl1_user_rssi", nvram_set,"0")\
    ENTRY("ddns_server_x_old", nvram_set,"")\
    ENTRY("vpn_client_useronly", nvram_set,"0")\
    ENTRY("Ate_total_fail_check", nvram_set,"0")\
    ENTRY("vlan_enable", nvram_set,"0")\
    ENTRY("wl_wep_x", nvram_set,"0")\
    ENTRY("qos_method", nvram_set,"0")\
    ENTRY("vpn_server_if", nvram_set,"tun")\
    ENTRY("vpn_server_cipher", nvram_set,"AES-128-CBC")\
    ENTRY("wl0.3_wpa_gtk_rekey", nvram_set,"3600")\
    ENTRY("wl1.2_auth_mode_x", nvram_set,"open")\
    ENTRY("wan_pppoe_username", nvram_set,"")\
    ENTRY("vpn_client_unit", nvram_set,"1")\
    ENTRY("wl0_sched", nvram_set,"000000")\
    ENTRY("wan0_expires", nvram_set,"31")\
    ENTRY("led_wps_gpio", nvram_set,"4136")\
    ENTRY("led_lan3_gpio", nvram_set,"12330")\
    ENTRY("st_ftp_force_mode", nvram_set,"2")\
    ENTRY("PM_restart", nvram_set,"0")\
    ENTRY("PM_mon", nvram_set,"0")\
    ENTRY("wl1_mode_x", nvram_set,"0")\
    ENTRY("wan0_upnp_enable", nvram_set,"1")\
    ENTRY("upgrade_fw_status", nvram_set,"0")\
    ENTRY("wan_ifnames", nvram_set,"eth0")\
    ENTRY("smbd_custom", nvram_set,"")\
    ENTRY("st_ftp_mode", nvram_set,"2")\
    ENTRY("fb_email_provider", nvram_set,"")\
    ENTRY("wl1_turbo_qam_brcm_intop", nvram_set,"1")\
    ENTRY("wan0_sbstate_t", nvram_set,"3")\
    ENTRY("vpn_client3_errno", nvram_set,"")\
    ENTRY("rcno", nvram_set,"2")\
    ENTRY("wl_rateset", nvram_set,"default")\
    ENTRY("wl_crypto", nvram_set,"aes")\
    ENTRY("wl_pmk_cache", nvram_set,"60")\
    ENTRY("wan0_hwname", nvram_set,"")\
    ENTRY("dms_rebuild", nvram_set,"0")\
    ENTRY("wl1_ap_isolate", nvram_set,"0")\
    ENTRY("wl0.2_ifname", nvram_set,"")\
    ENTRY("wl0.3_bw_ul", nvram_set,"")\
    ENTRY("wl0.3_crypto", nvram_set,"aes")\
    ENTRY("wl1.2_akm", nvram_set,"")\
    ENTRY("ddns_hostname_old", nvram_set,"")\
    ENTRY("wl_sched", nvram_set,"000000")\
    ENTRY("usb_fs_fat", nvram_set,"1")\
    ENTRY("ipv6_6rd_prefixlen", nvram_set,"32")\
    ENTRY("wl0.2_key", nvram_set,"1")\
    ENTRY("btn_ez", nvram_set,"0")\
    ENTRY("vpn_crt_server_client_crt", nvram_set,"")\
    ENTRY("ipv6_tun_mtu", nvram_set,"0")\
    ENTRY("wl1_atf", nvram_set,"0")\
    ENTRY("wl0.3_bw_enabled", nvram_set,"0")\
    ENTRY("wl1.1_wme", nvram_set,"auto")\
    ENTRY("old_resolve", nvram_set,"1")\
    ENTRY("wl_mbss", nvram_set,"")\
    ENTRY("fw_pt_pppoerelay", nvram_set,"0")\
    ENTRY("Ate_boot_fail", nvram_set,"0")\
    ENTRY("wl1_wme_no_ack", nvram_set,"off")\
    ENTRY("wl0.1_bridge", nvram_set,"")\
    ENTRY("wl0.1_mode", nvram_set,"ap")\
    ENTRY("wl1.2_ifname", nvram_set,"")\
    ENTRY("wl1.3_crypto", nvram_set,"aes")\
    ENTRY("wan0_phytype", nvram_set,"")\
    ENTRY("wlready", nvram_set,"1")\
    ENTRY("wl_ifnames", nvram_set,"ath0 ath1")\
    ENTRY("wl_radius_key", nvram_set,"")\
    ENTRY("lan_proto", nvram_set,"static")\
    ENTRY("lan_ipaddr", nvram_set,"192.168.50.1")\
    ENTRY("dhcp1_staticlist", nvram_set,"")\
    ENTRY("wl1_radius_port", nvram_set,"1812")\
    ENTRY("wl1_pmk_cache", nvram_set,"60")\
    ENTRY("wl1.2_auth", nvram_set,"0")\
    ENTRY("apps_mounted_path", nvram_set,"")\
    ENTRY("led_lan_gpio", nvram_set,"255")\
    ENTRY("lan1_netmask", nvram_set,"255.255.255.0")\
    ENTRY("url_enable_x", nvram_set,"0")\
    ENTRY("wl_unit", nvram_set,"1")\
    ENTRY("wl_expire", nvram_set,"0")\
    ENTRY("wan_pptp_options_x", nvram_set,"")\
    ENTRY("vpnc_pppoe_username", nvram_set,"")\
    ENTRY("wl1_plcphdr", nvram_set,"long")\
    ENTRY("wl0.3_ssid", nvram_set,"ASUS_E8_2G_Guest3")\
    ENTRY("wl1.1_bridge", nvram_set,"")\
    ENTRY("wan0_route", nvram_set,"")\
    ENTRY("webs_state_url", nvram_set,"")\
    ENTRY("acs_band1", nvram_set,"0")\
    ENTRY("wl1_macmode", nvram_set,"disabled")\
    ENTRY("wl0.3_expire", nvram_set,"0")\
    ENTRY("wl1.3_infra", nvram_set,"1")\
    ENTRY("wl_nmode_protection", nvram_set,"auto")\
    ENTRY("wps_sta_pin", nvram_set,"00000000")\
    ENTRY("ct_tcp_timeout", nvram_set,"0 432000 120 60 120 120 10 60 30 0")\
    ENTRY("lan1_proto", nvram_set,"0")\
    ENTRY("http_clientlist", nvram_set,"")\
    ENTRY("wl0_frag", nvram_set,"2346")\
    ENTRY("btn_radio_gpio", nvram_set,"255")\
    ENTRY("led_lan1_gpio", nvram_set,"12333")\
    ENTRY("acs_band3", nvram_set,"0")\
    ENTRY("usb_path1_diskmon_freq_time", nvram_set,"")\
    ENTRY("Ate_boot_check", nvram_set,"0")\
    ENTRY("wl0.1_closed", nvram_set,"0")\
    ENTRY("wl1.3_auth_mode_x", nvram_set,"open")\
    ENTRY("wan0_netmask", nvram_set,"0.0.0.0")\
    ENTRY("wl0.1_ap_isolate", nvram_set,"0")\
    ENTRY("wl1.3_expire", nvram_set,"0")\
    ENTRY("wan1_ppp_phy", nvram_set,"1")\
    ENTRY("preferred_lang", nvram_set,"CN")\
    ENTRY("wps_multiband", nvram_set,"1")\
    ENTRY("wl1.1_bw_enabled", nvram_set,"0")\
    ENTRY("wan0_enable", nvram_set,"1")\
    ENTRY("rcno_org", nvram_set,"2")\
    ENTRY("dhcp_gateway_x", nvram_set,"")\
    ENTRY("vpn_client_proto", nvram_set,"udp")\
    ENTRY("wl1.1_closed", nvram_set,"0")\
    ENTRY("vpn_client1_state", nvram_set,"")\
    ENTRY("pwr_usb_gpio", nvram_set,"255")\
    ENTRY("w_apply", nvram_set,"1")\
    ENTRY("wan_clientid", nvram_set,"")\
    ENTRY("PM_SMTP_SERVER", nvram_set,"")\
    ENTRY("Ate_rc_check", nvram_set,"0")\
    ENTRY("wl0.2_infra", nvram_set,"1")\
    ENTRY("wan0_wins", nvram_set,"")\
    ENTRY("wl_guest_num", nvram_set,"10")\
    ENTRY("pptpd_clients", nvram_set,"192.168.10.2-11")\
    ENTRY("vpnc_connect_row", nvram_set,"")\
    ENTRY("vpn_client_firewall", nvram_set,"auto")\
    ENTRY("vpn_client_rgw", nvram_set,"0")\
    ENTRY("wl0.3_key1", nvram_set,"")\
    ENTRY("wl1.1_wep_x", nvram_set,"0")\
    ENTRY("wl_txq_thresh", nvram_set,"1024")\
    ENTRY("MULTIFILTER_TMP", nvram_set,"")\
    ENTRY("usb_uhci", nvram_set,"0")\
    ENTRY("sshd_enable", nvram_set,"1")\
    ENTRY("wl0.1_radius_ipaddr", nvram_set,"")\
    ENTRY("wl0.3_key2", nvram_set,"")\
    ENTRY("lan_sbstate_t", nvram_set,"0")\
    ENTRY("wl0.3_key3", nvram_set,"")\
    ENTRY("wl1.2_radio", nvram_set,"1")\
    ENTRY("led_all_gpio", nvram_set,"255")\
    ENTRY("wl_igs", nvram_set,"0")\
    ENTRY("vpnc_pptp_options_x", nvram_set,"")\
    ENTRY("vpn_crt_server_crl", nvram_set,"")\
    ENTRY("ttl_spoof_enable", nvram_set,"0")\
    ENTRY("wl1_mode", nvram_set,"ap")\
    ENTRY("wl0.3_key4", nvram_set,"")\
    ENTRY("wl1.1_preauth", nvram_set,"")\
    ENTRY("init_wl_re", nvram_set,"0")\
    ENTRY("have_fan_gpio", nvram_set,"255")\
    ENTRY("webdav_http_port", nvram_set,"8082")\
    ENTRY("enable_acc_restriction", nvram_set,"0")\
    ENTRY("fb_ptype", nvram_set,"")\
    ENTRY("wl0_rateset", nvram_set,"default")\
    ENTRY("wl0.1_ssid", nvram_set,"ASUS_E8_2G_Guest")\
    ENTRY("usb_fs_hfs", nvram_set,"1")\
    ENTRY("vpn_debug", nvram_set,"0")\
    ENTRY("vpn_server_poll", nvram_set,"0")\
    ENTRY("wl1_guest_num", nvram_set,"10")\
    ENTRY("wl1_rast_sens_level", nvram_set,"1")\
    ENTRY("wan0_vendorid", nvram_set,"")\
    ENTRY("wan0_6rd_ip4size", nvram_set,"")\
    ENTRY("autodet_proceeding", nvram_set,"0")\
    ENTRY("wan_dns1_x", nvram_set,"")\
    ENTRY("enable_ftp", nvram_set,"1")\
    ENTRY("fb_attach_modemlog", nvram_set,"")\
    ENTRY("wl0_wme_apsd", nvram_set,"on")\
    ENTRY("wl1_wpa_psk", nvram_set,"742649264")\
    ENTRY("wl1.3_macmode", nvram_set,"disabled")\
    ENTRY("vpn_client_password", nvram_set,"")\
    ENTRY("wl_wme", nvram_set,"auto")\
    ENTRY("pptpd_mppe", nvram_set,"13")\
    ENTRY("webs_state_flag", nvram_set,"0")\
    ENTRY("led_wan_red_gpio", nvram_set,"68")\
    ENTRY("fw_pt_pptp", nvram_set,"1")\
    ENTRY("dms_tivo", nvram_set,"0")\
    ENTRY("Ate_dev_fail", nvram_set,"0")\
    ENTRY("wl1_wme_apsd", nvram_set,"on")\
    ENTRY("wl0.1_radio", nvram_set,"1")\
    ENTRY("wl0.3_net_reauth", nvram_set,"36000")\
    ENTRY("lan_ifname", nvram_set,"eth0")\
    ENTRY("wan_pppoe_hostuniq", nvram_set,"")\
    ENTRY("shell_timeout", nvram_set,"0")\
    ENTRY("wl0_turbo_qam_brcm_intop", nvram_set,"1")\
    ENTRY("diskmon_status", nvram_set,"0")\
    ENTRY("boardflags", nvram_set,"0x100")\
    ENTRY("wl_mumimo", nvram_set,"1")\
    ENTRY("wan_upnp_enable", nvram_set,"1")\
    ENTRY("rstats_bak", nvram_set,"0")\
    ENTRY("vpn_crt_server_crt", nvram_set,"")\
    ENTRY("wl0_mimo_preamble", nvram_set,"mm")\
    ENTRY("wan0_nat_x", nvram_set,"1")\
    ENTRY("ddns_return_code_chk", nvram_set,"")\
    ENTRY("acc_num", nvram_set,"1")\
    ENTRY("smbd_cset", nvram_set,"utf8")\
    ENTRY("vpn_server_crypt", nvram_set,"tls")\
    ENTRY("PM_freq", nvram_set,"0")\
    ENTRY("wan0_pppoe_mtu", nvram_set,"1492")\
    ENTRY("time_zone_dstoff", nvram_set,"M3.2.0/2,M10.2.0/2")\
    ENTRY("qos_icmp", nvram_set,"on")\
    ENTRY("yadns_mode", nvram_set,"0")\
    ENTRY("wl0_auth_mode_x", nvram_set,"psk2")\
    ENTRY("wl1_radio_time2_x", nvram_set,"00002359")\
    ENTRY("wl0.1_key1", nvram_set,"")\
    ENTRY("vpn_server1_state", nvram_set,"")\
    ENTRY("wl0.1_key2", nvram_set,"")\
    ENTRY("et_txq_thresh", nvram_set,"3300")\
    ENTRY("apps_state_action", nvram_set,"")\
    ENTRY("https_crt_save", nvram_set,"1")\
    ENTRY("sw_mode", nvram_set,"1")\
    ENTRY("wl_turbo_qam", nvram_set,"1")\
    ENTRY("wl_HT_STBC", nvram_set,"1")\
    ENTRY("diskmon_part", nvram_set,"")\
    ENTRY("ipv6_tun_addr", nvram_set,"")\
    ENTRY("wl0.1_key3", nvram_set,"")\
    ENTRY("wl1.2_wpa_gtk_rekey", nvram_set,"3600")\
    ENTRY("buildinfo", nvram_set,"Wed May 12 01:03:10 UTC 2021 barton@b4d36a6")\
    ENTRY("lan1_domain", nvram_set,"")\
    ENTRY("share_link_result", nvram_set,"")\
    ENTRY("wl0.1_key4", nvram_set,"")\
    ENTRY("wan0_dns2_x", nvram_set,"")\
    ENTRY("dhcpd_lmax", nvram_set,"253")\
    ENTRY("Ate_check_delay", nvram_set,"0")\
    ENTRY("invoke_later", nvram_set,"0")\
    ENTRY("wl_frameburst", nvram_set,"off")\
    ENTRY("misc_httpsport_x", nvram_set,"8443")\
    ENTRY("wl1.3_mode", nvram_set,"ap")\
    ENTRY("apps_state_enable", nvram_set,"")\
    ENTRY("sr_rulelist", nvram_set,"")\
    ENTRY("wl0_nmode_protection", nvram_set,"auto")\
    ENTRY("wl1.1_net_reauth", nvram_set,"36000")\
    ENTRY("wan0_netmask_x", nvram_set,"0.0.0.0")\
    ENTRY("mfp_ip_requeue", nvram_set,"")\
    ENTRY("wl1_ssid", nvram_set,"Chunqiu_5G")\
    ENTRY("asus_device_list", nvram_set,"<3>RT-ACRH17>192.168.50.1>04:D4:C4:D4:00:EC>0>Chunqiu_2G>255.255.255.0>1")\
    ENTRY("wl1_dtim", nvram_set,"1")\
    ENTRY("wl1_turbo_qam", nvram_set,"1")\
    ENTRY("wl1.3_wpa_psk", nvram_set,"")\
    ENTRY("webs_update_trigger", nvram_set,"")\
    ENTRY("qos_enable", nvram_set,"0")\
    ENTRY("upnp_max_port_int", nvram_set,"65535")\
    ENTRY("fan_gpio", nvram_set,"255")\
    ENTRY("wl_vifnames", nvram_set,"wl1.1 wl1.2 wl1.3")\
    ENTRY("wps_enable_x", nvram_set,"1")\
    ENTRY("wan_ipaddr", nvram_set,"0.0.0.0")\
    ENTRY("ipv6_tun_ttl", nvram_set,"255")\
    ENTRY("ipv6_dns1", nvram_set,"")\
    ENTRY("Ate_fw_fail", nvram_set,"10")\
    ENTRY("wl0.2_radius_key", nvram_set,"")\
    ENTRY("reboot_time", nvram_set,"100")\
    ENTRY("ahs_is_JSON_updated", nvram_set,"0")\
    ENTRY("acc_list", nvram_set,"qiangwang>2022qwb")\
    ENTRY("dmz_ip", nvram_set,"")\
    ENTRY("http_client", nvram_set,"0")\
    ENTRY("ipv6_dns2", nvram_set,"")\
    ENTRY("label_mac", nvram_set,"04:D4:C4:D4:00:E8")\
    ENTRY("dns_probe_host", nvram_set,"dns.msftncsi.com")\
    ENTRY("acc_webdavproxy", nvram_set,"admin>1")\
    ENTRY("http_autologout", nvram_set,"30")\
    ENTRY("pushnotify_httplogin", nvram_set,"1")\
    ENTRY("ipv6_dns3", nvram_set,"")\
    ENTRY("disiosdet", nvram_set,"1")\
    ENTRY("wl1_wdsapply_x", nvram_set,"0")\
    ENTRY("switch_wan2prio", nvram_set,"0")\
    ENTRY("http_id", nvram_set,"TIDe855a6487043d70a")\
    ENTRY("wl0_rts", nvram_set,"2347")\
    ENTRY("dhcp_staticlist", nvram_set,"")\
    ENTRY("smbd_wins", nvram_set,"1")\
    ENTRY("diskmon_policy", nvram_set,"disk")\
    ENTRY("diskmon_usbport", nvram_set,"")\
    ENTRY("vpnc_pppoe_options_x", nvram_set,"")\
    ENTRY("PM_MY_EMAIL", nvram_set,"")\
    ENTRY("wan0_gw_mac", nvram_set,"")\
    ENTRY("wl_ifname", nvram_set,"ath1")\
    ENTRY("wan_wins", nvram_set,"")\
    ENTRY("upnp_clean_threshold", nvram_set,"20")\
    ENTRY("wan0_pppoe_options_x", nvram_set,"")\
    ENTRY("http_enable", nvram_set,"0")\
    ENTRY("vpnc_state_t", nvram_set,"0")\
    ENTRY("ipv6_get_domain", nvram_set,"")\
    ENTRY("wl1_auth_mode_x", nvram_set,"psk2")\
    ENTRY("wl0.2_lanaccess", nvram_set,"off")\
    ENTRY("wl0.3_ifname", nvram_set,"")\
    ENTRY("link_internet", nvram_set,"1")\
    ENTRY("apps_depend_do", nvram_set,"")\
    ENTRY("vpn_crt_client_ca", nvram_set,"")\
    ENTRY("wl0_maclist_x", nvram_set,"")\
    ENTRY("wl1_key1", nvram_set,"")\
    ENTRY("wl1_nmode_protection", nvram_set,"auto")\
    ENTRY("wan0_clientid_type", nvram_set,"0")\
    ENTRY("https_lanport", nvram_set,"8443")\
    ENTRY("sshd_port_x", nvram_set,"22")\
    ENTRY("wl1_key2", nvram_set,"")\
    ENTRY("wl0.2_auth_mode", nvram_set,"none")\
    ENTRY("wan0_hwaddr_x", nvram_set,"")\
    ENTRY("wan0_vpndhcp", nvram_set,"1")\
    ENTRY("wanduck_start_detect", nvram_set,"1")\
    ENTRY("wl_gmode_protection", nvram_set,"auto")\
    ENTRY("apps_swap_threshold", nvram_set,"")\
    ENTRY("vpnc_clientlist", nvram_set,"")\
    ENTRY("Ate_reboot_count", nvram_set,"100")\
    ENTRY("wl1_key3", nvram_set,"")\
    ENTRY("wl0.2_bridge", nvram_set,"")\
    ENTRY("wl1.1_mode", nvram_set,"ap")\
    ENTRY("wl1.3_ifname", nvram_set,"")\
    ENTRY("wl1.3_key", nvram_set,"1")\
    ENTRY("lan1_wps_oob", nvram_set,"enabled")\
    ENTRY("wl_radio_time_x", nvram_set,"00002359")\
    ENTRY("fb_country", nvram_set,"")\
    ENTRY("ipv6_prefix_len_wan", nvram_set,"64")\
    ENTRY("wl0_wpa_gtk_rekey", nvram_set,"3600")\
    ENTRY("wl1_bw_enabled", nvram_set,"0")\
    ENTRY("wl1_key4", nvram_set,"")\
    ENTRY("vpn_client_userauth", nvram_set,"0")\
    ENTRY("wl_frag", nvram_set,"2346")\
    ENTRY("diskremove_bad_device", nvram_set,"1")\
    ENTRY("vpn_client_nm", nvram_set,"255.255.255.0")\
    ENTRY("wl1.2_bridge", nvram_set,"")\
    ENTRY("wan0_dnsenable_x", nvram_set,"1")\
    ENTRY("wan0_desc", nvram_set,"")\
    ENTRY("dhcp_static_x", nvram_set,"0")\
    ENTRY("vpn_crt_client_static", nvram_set,"")\
    ENTRY("ipv6_radvd", nvram_set,"1")\
    ENTRY("wl0_key", nvram_set,"1")\
    ENTRY("wl0.1_macmode", nvram_set,"disabled")\
    ENTRY("wl1.3_ssid", nvram_set,"ASUS_E8_5G_Guest3")\
    ENTRY("wl1_vifs", nvram_set,"")\
    ENTRY("wan0_ppp_echo", nvram_set,"0")\
    ENTRY("vpn_client4_state", nvram_set,"")\
    ENTRY("qos_obw", nvram_set,"")\
    ENTRY("MULTIFILTER_DEVICENAME", nvram_set,"")\
    ENTRY("wl0_HT_STBC", nvram_set,"1")\
    ENTRY("apps_state_error", nvram_set,"")\
    ENTRY("emf_entry", nvram_set,"")\
    ENTRY("url_rulelist", nvram_set,"")\
    ENTRY("daapd_enable", nvram_set,"0")\
    ENTRY("pptpd_mru", nvram_set,"1450")\
    ENTRY("PM_MAIL_FILE", nvram_set,"")\
    ENTRY("wl1.3_bw_dl", nvram_set,"")\
    ENTRY("rc_service", nvram_set,"")\
    ENTRY("webs_state_error", nvram_set,"")\
    ENTRY("filter_lw_default_x", nvram_set,"ACCEPT")\
    ENTRY("st_samba_mode", nvram_set,"4")\
    ENTRY("wl0.2_closed", nvram_set,"0")\
    ENTRY("wan1_ppp_echo", nvram_set,"0")\
    ENTRY("DCode", nvram_set,"")\
    ENTRY("territory_code", nvram_set,"CN/01")\
    ENTRY("console_loglevel", nvram_set,"5")\
    ENTRY("upnp_min_port_ext", nvram_set,"1")\
    ENTRY("ipv6_dhcp_start", nvram_set,"")\
    ENTRY("ct_hashsize", nvram_set,"3929")\
    ENTRY("blver", nvram_set,"RT-AC82U-01-00-01-01")\
    ENTRY("fb_state", nvram_set,"")\
    ENTRY("lan1_wps_reg", nvram_set,"enabled")\
    ENTRY("time_zone", nvram_set,"CST-8")\
    ENTRY("apps_state_autofix", nvram_set,"1")\
    ENTRY("vpn_server_sn", nvram_set,"10.8.0.0")\
    ENTRY("vpn_server_pdns", nvram_set,"0")\
    ENTRY("vpn_client_port", nvram_set,"1194")\
    ENTRY("vpn_crt_client_crl", nvram_set,"")\
    ENTRY("switch_wantag", nvram_set,"none")\
    ENTRY("qos_default", nvram_set,"3")\
    ENTRY("wl1.2_closed", nvram_set,"0")\
    ENTRY("usb_ntfs_mod", nvram_set,"open")\
    ENTRY("switch_wan0prio", nvram_set,"0")\
    ENTRY("vts_enable_x", nvram_set,"0")\
    ENTRY("rstats_sshut", nvram_set,"1")\
    ENTRY("vpn_upload_unit", nvram_set,"")\
    ENTRY("vpn_upload_type", nvram_set,"")\
    ENTRY("wl0.3_preauth", nvram_set,"")\
    ENTRY("fw_enable_x", nvram_set,"0")\
    ENTRY("pptpd_chap", nvram_set,"0")\
    ENTRY("wl0.1_bw_enabled", nvram_set,"0")\
    ENTRY("wl0.3_unit", nvram_set,"0.3")\
    ENTRY("wl0.3_wme", nvram_set,"auto")\
    ENTRY("wl1.2_lanaccess", nvram_set,"off")\
    ENTRY("wl0.2_bw_dl", nvram_set,"")\
    ENTRY("wl1.3_key1", nvram_set,"")\
    ENTRY("wan0_pppoe_idletime", nvram_set,"0")\
    ENTRY("wan0_pppoe_service", nvram_set,"")\
    ENTRY("networkmap_fullscan", nvram_set,"2")\
    ENTRY("restart_wifi", nvram_set,"0")\
    ENTRY("extendno", nvram_set,"52517-gb4d36a6")\
    ENTRY("switch_wan1tagid", nvram_set,"")\
    ENTRY("wl0_implicitxbf", nvram_set,"0")\
    ENTRY("wl0.3_wep_x", nvram_set,"0")\
    ENTRY("wl1.2_auth_mode", nvram_set,"none")\
    ENTRY("wl1.3_key2", nvram_set,"")\
    ENTRY("wan0_auxstate_t", nvram_set,"1")\
    ENTRY("wl1.3_key3", nvram_set,"")\
    ENTRY("wl1.3_radius_ipaddr", nvram_set,"")\
    ENTRY("wan0_hwaddr", nvram_set,"04:D4:C4:D4:00:E8")\
    ENTRY("wan_hostname", nvram_set,"")\
    ENTRY("apps_ipkg_old", nvram_set,"0")\
    ENTRY("wl1.3_key4", nvram_set,"")\
    ENTRY("lanports_mask", nvram_set,"30")\
    ENTRY("dhcp1_start", nvram_set,"192.168.2.2")\
    ENTRY("MULTIFILTER_ENABLE", nvram_set,"")\
    ENTRY("VPNServer_mode", nvram_set,"pptpd")\
    ENTRY("vpn_server_proto", nvram_set,"udp")\
    ENTRY("vpn_crt_client_crt", nvram_set,"")\
    ENTRY("wl0_radio", nvram_set,"1")\
    ENTRY("wl1.1_ssid", nvram_set,"ASUS_E8_5G_Guest")\
    ENTRY("wl1.1_key", nvram_set,"1")\
    ENTRY("wl1.2_ap_isolate", nvram_set,"0")\
    ENTRY("wl_wdslist", nvram_set,"")\
    ENTRY("webdav_https_port", nvram_set,"443")\
    ENTRY("fb_browserInfo", nvram_set,"")\
    ENTRY("wl0.1_wpa_psk", nvram_set,"")\
    ENTRY("wl_channel", nvram_set,"0")\
    ENTRY("vpn_crt_server_static", nvram_set,"")\
    ENTRY("vpn_client_local", nvram_set,"10.8.0.2")\
    ENTRY("wl1.3_bw_ul", nvram_set,"")\
    ENTRY("wl0_bcn", nvram_set,"100")\
    ENTRY("wl1_assoc_retry_max", nvram_set,"3")\
    ENTRY("wl_timesched", nvram_set,"0")\
    ENTRY("vpn_client_verb", nvram_set,"3")\
    ENTRY("ipv6_dhcp_lifetime", nvram_set,"86400")\
    ENTRY("Ate_reboot_delay", nvram_set,"20")\
    ENTRY("wan0_heartbeat_x", nvram_set,"")\
    ENTRY("webs_state_level", nvram_set,"0")\
    ENTRY("wl_radio", nvram_set,"1")\
    ENTRY("dhcp1_lease", nvram_set,"86400")\
    ENTRY("vpn_server_tls_keysize", nvram_set,"0")\
    ENTRY("wl0_hwaddr", nvram_set,"04:D4:C4:D4:00:E8")\
    ENTRY("wps_wer_mode", nvram_set,"allow")\
    ENTRY("usb_path2_diskmon_freq_time", nvram_set,"")\
    ENTRY("wl_rast_sens_level", nvram_set,"1")\
    ENTRY("wl_subunit", nvram_set,"-1")\
    ENTRY("jumbo_frame_enable", nvram_set,"0")\
    ENTRY("dhcp1_static_x", nvram_set,"0")\
    ENTRY("qos_orates", nvram_set,"80-100,10-100,5-100,3-100,2-95,0-0,0-0,0-0,0-0,0-0")\
    ENTRY("vpn_server_ccd", nvram_set,"0")\
    ENTRY("vpn_client_hmac", nvram_set,"-1")\
    ENTRY("svc_ready", nvram_set,"0")\
    ENTRY("buildno_org", nvram_set,"382")\
    ENTRY("emf_enable", nvram_set,"0")\
    ENTRY("redirect_dname", nvram_set,"1")\
    ENTRY("r_Setting", nvram_set,"0")\
    ENTRY("vpn_serverx_dns", nvram_set,"")\
    ENTRY("vpn_server_comp", nvram_set,"adaptive")\
    ENTRY("wl0.1_unit", nvram_set,"0.1")\
    ENTRY("vpn_client2_errno", nvram_set,"")\
    ENTRY("usbctrlver", nvram_set,"1")\
    ENTRY("wl_radio_date_x", nvram_set,"1111111")\
    ENTRY("script_usbmount", nvram_set,"")\
    ENTRY("diskformat_label", nvram_set,"")\
    ENTRY("httpd_die_reboot", nvram_set,"")\
    ENTRY("rstats_enable", nvram_set,"1")\
    ENTRY("custom_usericon_del", nvram_set,"")\
    ENTRY("wl0_gmode_protection", nvram_set,"auto")\
    ENTRY("wl0.2_bw_ul", nvram_set,"")\
    ENTRY("wl1.1_key1", nvram_set,"")\
    ENTRY("wl1_timesched", nvram_set,"0")\
    ENTRY("wl0.1_wpa_gtk_rekey", nvram_set,"3600")\
    ENTRY("wl0.2_akm", nvram_set,"")\
    ENTRY("wl1.1_key2", nvram_set,"")\
    ENTRY("ddns_return_code", nvram_set,"")\
    ENTRY("rstats_colors", nvram_set,"")\
    ENTRY("pptpd_ms_network", nvram_set,"1")\
    ENTRY("PM_MY_NAME", nvram_set,"")\
    ENTRY("wl1.1_key3", nvram_set,"")\
    ENTRY("wl_rts", nvram_set,"2347")\
    ENTRY("ddns_passwd_x", nvram_set,"")\
    ENTRY("dms_stdlna", nvram_set,"0")\
    ENTRY("ipv6_6rd_dhcp", nvram_set,"1")\
    ENTRY("wl1_implicitxbf", nvram_set,"0")\
    ENTRY("wl0.1_wme", nvram_set,"auto")\
    ENTRY("wl1.1_key4", nvram_set,"")\
    ENTRY("apps_download_file", nvram_set,"")\
    ENTRY("webs_state_upgrade", nvram_set,"")\
    ENTRY("usb_hfs_mod", nvram_set,"open")\
    ENTRY("record_lanaddr", nvram_set,"")\
    ENTRY("guard_mode", nvram_set,"0")\
    ENTRY("wl0_HT_RxStream", nvram_set,"2")\
    ENTRY("wl_ap_isolate", nvram_set,"0")\
    ENTRY("lan_wins", nvram_set,"")\
    ENTRY("wan_desc", nvram_set,"")\
    ENTRY("rast_idlrt", nvram_set,"20")\
    ENTRY("wps_modelnum", nvram_set,"RT-ACRH17")\
    ENTRY("lan_hwnames", nvram_set,"")\
    ENTRY("nat_redirect_enable", nvram_set,"1")\
    ENTRY("wl0_atf_mode", nvram_set,"0")\
    ENTRY("wl1_radius_ipaddr", nvram_set,"")\
    ENTRY("wl1_country_code", nvram_set,"CN")\
    ENTRY("wl_wme_no_ack", nvram_set,"off")\
    ENTRY("dhcp1_end", nvram_set,"192.168.2.254")\
    ENTRY("wan_dnsenable_x", nvram_set,"1")\
    ENTRY("wl1.2_infra", nvram_set,"1")\
    ENTRY("wl1_atf_mode", nvram_set,"0")\
    ENTRY("wl0.1_net_reauth", nvram_set,"36000")\
    ENTRY("wl0.3_auth", nvram_set,"0")\
    ENTRY("wan0_unit", nvram_set,"0")\
    ENTRY("wan0_pppoe_username", nvram_set,"")\
    ENTRY("wl0_radius_key", nvram_set,"")\
    ENTRY("wl1_gmode_protection", nvram_set,"auto")\
    ENTRY("wl_optimizexbox", nvram_set,"0")\
    ENTRY("autofw_enable_x", nvram_set,"0")\
    ENTRY("wl1_mbss", nvram_set,"")\
    ENTRY("led_pwr_gpio", nvram_set,"4136")\
    ENTRY("wl_key", nvram_set,"1")\
    ENTRY("wl_mrate_x", nvram_set,"0")\
    ENTRY("ipv6_relay", nvram_set,"192.88.99.1")\
    ENTRY("wl0_wdslist", nvram_set,"")\
    ENTRY("wl1_rateset", nvram_set,"default")\
    ENTRY("wl1.2_preauth", nvram_set,"")\
    ENTRY("vpn_server2_errno", nvram_set,"")\
    ENTRY("dhcpc_mode", nvram_set,"1")\
    ENTRY("ddns_hostname_x", nvram_set,"")\
    ENTRY("daapd_friendly_name", nvram_set,"RT-ACRH17-00E8")\
    ENTRY("vpnc_auto_conn", nvram_set,"")\
    ENTRY("vpn_client_custom", nvram_set,"")\
    ENTRY("wl0_channel", nvram_set,"0")\
    ENTRY("wl1_unit", nvram_set,"1")\
    ENTRY("wps_device_name", nvram_set,"RT-ACRH17")\
    ENTRY("usb_enable", nvram_set,"1")\
    ENTRY("web_redirect", nvram_set,"3")\
    ENTRY("wl0.1_infra", nvram_set,"1")\
    ENTRY("wan0_ipaddr_x", nvram_set,"0.0.0.0")\
    ENTRY("sshd_dsskey", nvram_set,"AAAAB3NzaC1kc3MAAACBAPnQ3kDhmbgkycbH34IsnqgDxCnRl1lNPBj1V3uuUM3N2zO1aQAjHgYSwGNu4f7jCNSP8EgjL6r+TgzrNNb57lXxmbCNo84nmIXp4yPA1s14i2iuhdT2l7V8HQeeB+TYyLBsZN+unX9IJ5t9u21t2sKm5GOFCQwjKx/QwxYsE3tlAAAAFQCyjBQ8hEBbk4FmPTDjmkL2Gtsc6QAAAIBgc/s4wpz7cPfXUaByL0iD+f/yL4kZd/81p30cAVHVS2XwNYxTHzwtZiYa9HfkNW3FAjrHBTcwIjh9o4OVgjkOtsKVKvJ2I5EWLYCi+qUS9XVjE7n+iNDJ68cDHXXQUBcUOU+iHp2p2N32iw2ycpDpbys/xxnf4OkBJzOzDZtvaAAAAIEA8aBlvnczRXR7CML93EfjulsTzFkDFwHa6VPcojJj3Nv9hjJsUdbdrrcEqF1EpucGkd6XPtJsWfuDYeuFbkDF7Zlu5U10NDmMYRX3QEykJrIvJVKdC/Z2WUMLLzpz8+RBtsAlMkon5LFyVFMHuVbtfERWDCrOvd5O11FdPsj8BCIAAAAUFyEC+eVjnpRfUlqHtzCoboUe4k4")\
    ENTRY("vpn_upload_state", nvram_set,"")\
    ENTRY("dns_probe_content", nvram_set,"131.107.255.255 112.4.20.71 fd3e:4f5a:5b81::1")\
    ENTRY("wl0.1_bss_enabled", nvram_set,"0")\
    ENTRY("wl_bss_enabled", nvram_set,"1")\
    ENTRY("upnp_enable", nvram_set,"1")\
    ENTRY("PM_enable", nvram_set,"0")\
    ENTRY("link_wan", nvram_set,"0")\
    ENTRY("wl_radio_time2_x", nvram_set,"00002359")\
    ENTRY("fw_log_x", nvram_set,"none")\
    ENTRY("script_usbumount", nvram_set,"")\
    ENTRY("vpn_client_remote", nvram_set,"10.8.0.1")\
    ENTRY("ipv6_accept_defrtr", nvram_set,"1")\
    ENTRY("wl0.3_bridge", nvram_set,"")\
    ENTRY("wl1.1_radio", nvram_set,"1")\
    ENTRY("wl1.3_radius_key", nvram_set,"")\
    ENTRY("apps_install_folder", nvram_set,"asusware.arm")\
    ENTRY("wl1_nband", nvram_set,"1")\
    ENTRY("wan_pppoe_ac", nvram_set,"")\
    ENTRY("qos_fin", nvram_set,"off")\
    ENTRY("game_vts_rulelist", nvram_set,"")\
    ENTRY("wl0_subunit", nvram_set,"-1")\
    ENTRY("pwr_usb_gpio2", nvram_set,"255")\
    ENTRY("wl1_HT_RxStream", nvram_set,"4")\
    ENTRY("emf_uffp_entry", nvram_set,"")\
    ENTRY("dhcp_enable_x", nvram_set,"1")\
    ENTRY("vpn_server_c2c", nvram_set,"0")\
    ENTRY("wan0_pptp_options_x", nvram_set,"")\
    ENTRY("apps_state_install", nvram_set,"")\
    ENTRY("wl1.3_bridge", nvram_set,"")\
    ENTRY("ddns_status", nvram_set,"")\
    ENTRY("lan1_hwaddr", nvram_set,"")\
    ENTRY("dhcp1_wins_x", nvram_set,"")\
    ENTRY("misc_httpport_x", nvram_set,"8080")\
    ENTRY("vpnc_pppoe_passwd", nvram_set,"")\
    ENTRY("vpn_client_nat", nvram_set,"1")\
    ENTRY("lfp_disable", nvram_set,"0")\
    ENTRY("wl0.1_auth", nvram_set,"0")\
    ENTRY("qos_bw_rulelist", nvram_set,"")\
    ENTRY("fw_pt_ipsec", nvram_set,"1")\
    ENTRY("apps_swap_size", nvram_set,"33000")\
    ENTRY("asus_mfg_flash", nvram_set,"")\
    ENTRY("vpn_crt_server_client_key", nvram_set,"")\
    ENTRY("wl0_lanaccess", nvram_set,"off")\
    ENTRY("wl0_atf_ssid", nvram_set,"")\
    ENTRY("wl_closed", nvram_set,"0")\
    ENTRY("vpnc_pptp_options_x_list", nvram_set,"")\
    ENTRY("wl0_auth_mode", nvram_set,"none")\
    ENTRY("webdav_lock_times", nvram_set,"3")\
    ENTRY("wl0.3_closed", nvram_set,"0")\
    ENTRY("wan_heartbeat_x", nvram_set,"")\
    ENTRY("wl1_bw_dl", nvram_set,"")\
    ENTRY("wl1_atf_ssid", nvram_set,"")\
    ENTRY("wan0_dns1_x", nvram_set,"")\
    ENTRY("aae_retry_cnt", nvram_set,"0")\
    ENTRY("wl1_txbf_en", nvram_set,"0")\
    ENTRY("boardnum", nvram_set,"04:d4:c4:d4:00:ec")\
    ENTRY("dhcp_wins_x", nvram_set,"")\
    ENTRY("vpn_client_gw", nvram_set,"")\
    ENTRY("fb_split_files", nvram_set,"1")\
    ENTRY("wl0_crypto", nvram_set,"aes")\
    ENTRY("MULTIFILTER_MAC", nvram_set,"")\
    ENTRY("MULTIFILTER_URL", nvram_set,"")\
    ENTRY("upnp_max_port_ext", nvram_set,"65535")\
    ENTRY("ipv6_rtr_addr_s", nvram_set,"")\
    ENTRY("wl1.3_closed", nvram_set,"0")\
    ENTRY("firmver", nvram_set,"3.0.0.4")\
    ENTRY("wl_bcn", nvram_set,"100")\
    ENTRY("url_sched", nvram_set,"000000")\
    ENTRY("dms_port", nvram_set,"8200")\
    ENTRY("vpn_server_custom", nvram_set,"")\
    ENTRY("acs_dfs", nvram_set,"1")\
    ENTRY("upnp_secure", nvram_set,"1")\
    ENTRY("upnp_mnp", nvram_set,"1")\
    ENTRY("vts_ftpport", nvram_set,"2021")\
    ENTRY("VPNClient_enable", nvram_set,"0")\
    ENTRY("wl1.3_unit", nvram_set,"1.3")\
    ENTRY("btn_ez_radiotoggle", nvram_set,"0")\
    ENTRY("custom_usericon", nvram_set,"")\
    ENTRY("vlan_rulelist", nvram_set,"")\
    ENTRY("wl1_igs", nvram_set,"0")\
    ENTRY("wl0.2_bss_enabled", nvram_set,"0")\
    ENTRY("dms_state", nvram_set,"")\
    ENTRY("apps_download_percent", nvram_set,"")\
    ENTRY("uuid", nvram_set,"4b95b287-679f-471a-9643-97eec95811b5")\
    ENTRY("ddns_server_x", nvram_set,"")\
    ENTRY("dms_dir_x", nvram_set,"")\
    ENTRY("firmware_path", nvram_set,"")\
    ENTRY("vpn_server_remote", nvram_set,"10.8.0.2")\
    ENTRY("wl0.2_radius_ipaddr", nvram_set,"")\
    ENTRY("ct_udp_timeout", nvram_set,"30 180")\
    ENTRY("vts_rulelist", nvram_set,"")\
    ENTRY("ipv6_fw_rulelist", nvram_set,"")\
    ENTRY("wl0_mrate_x", nvram_set,"0")\

#endif
```

编译命令如下：

1. `cd /home/cyberangel/Desktop/`
2. `export LD_LIBRARY_PATH="$PWD/hndtools-arm-linux-2.6.36-uclibc-4.5.3/lib"`
3. `./hndtools-arm-linux-2.6.36-uclibc-4.5.3/bin/arm-uclibc-gcc -c -O2 -fPIC -Wall /home/cyberangel/Desktop/ASUS-RT-ACRH17/libnvram-master/nvram.c -o /home/cyberangel/Desktop/ASUS-RT-ACRH17/libnvram-master/firmadyne_nvram.o`
4. `./hndtools-arm-linux-2.6.36-uclibc-4.5.3/bin/arm-uclibc-gcc -shared -nostdlib /home/cyberangel/Desktop/ASUS-RT-ACRH17/libnvram-master/firmadyne_nvram.o -o /home/cyberangel/Desktop/ASUS-RT-ACRH17/libnvram-master/firmadyne_libnvram.so`

将编译好的动态链接库文件`firmadyne_libnvram.so`上传qemu，这里图省事我直接将原来的`/usr/lib/libnvram.so`备份后替换为`firmadyne_libnvram.so`，最后需要手动创建文件夹`/firmadyne/libnvram`（`mkdir -p /firmadyne/libnvram`）。

www目录下启动httpd后访问`http://192.168.50.1/Main_Login.asp`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667036360076-5c8c7112-fa5a-46e5-8f91-f8aeae100175.png)

输入正确的账号密码：`qiangwang`、`2022qwb`并登录：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667039641954-12b7054a-6819-4be3-8afe-e79624856982.png)

看来模拟还是有些问题，但值得高兴的是hook之后段错误问题就不存在了，网页也能够正常的在浏览器中访问，至于为什么curl的连接不断开我就不细细的追究了。

### 04-3、解决无法登录的问题
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667040031881-ad0b533c-f946-4636-b38b-f7e94db14781.png)

唉？不对啊，我们的账号密码明明是这个。如上图所示，`http_username`代表后台的账号，而`http_passwd`则是后台的密码，但为什么登录不上去呢？难道还是nvram的问题？为了方便抓包（主要是我懒得配Ubuntu的抓包环境了），我使用rinetd将qemu的http服务转发到虚拟机（192.168.2.242）的8080端口：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667180428472-6b3a3db4-8c02-4aa7-8398-61c1f718a4e7.png)

这样我们就能够在虚拟机外部进行访问了：

> 注：由于Parallels Desktop的问题，之后篇幅中出现的Linux虚拟机IP可能会不同，请谅解。
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667180653313-e0f6645a-2719-4627-8103-470a210a1a92.png)

随意输入密码，在尝试登录5次之后，路由器会将自身锁定：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667181695815-05263f8f-9551-4259-b9bc-e9b8143b1697.png)

`login.cgi`的请求会携带经过base64编码后的认证信息`login_authorization`（`qiangwang:2022qwb`）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667182545266-7174d635-e002-4c82-8231-36a509f6d647.png)

根据封禁提示`You have entered an incorrect username or password`搜索此字符串：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667182997259-07d14df6-4532-4c98-a6fd-76b211cda7f4.png)

转到`./www/Main_Login.asp`，有这么一段代码：

```javascript
var login_info = tryParseJSON('<% login_error_info(); %>');
// ...
var flag = login_info.error_status;
// ...
else if(flag == 7){
document.getElementById("error_status_field").innerHTML ="You have entered an incorrect username or password 5 times. Please try again after "+"<span id='rtime'></span>"+" seconds.";
document.getElementById("error_status_field").className = "error_hint error_hint1";
disable_input(1);
disable_button(1);
rtime_obj=document.getElementById("rtime");
countdownfunc();
countdownid = window.setInterval(countdownfunc,1000);
}
```

看来当路由器返回`flag == 7`时就代表着路由器将自己封禁。进一步追踪，则有：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667181345324-aaf772e0-5c82-4506-ad9f-1efb474dab1c.png)

看来所谓的`login.cgi`是“虚拟”出的，本质还是`httpd`，在IDA中搜索这串字符串，交叉引用来到：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667183754266-a8169952-639e-4158-a5b6-649c71096809.png)

IDA并未识别出此函数，如下图所示：![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667183775711-d0ac5f02-cd96-48a8-af8f-49fad7d9b8cc.png)

在键盘上按下p键将该代码块声明为函数，大致看了一下，可以确定`sub_29188`是登录逻辑：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667184203594-fbed69aa-b02a-409e-a8b7-d2ba1cebf149.png)

`dword_55AF4`应该就是之前提到的flag，因为该全局变量的值牵扯到“lock_time”：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667184360329-c8b6aa75-3292-4798-a891-38a290ddc451.png)

账号密码的验证主逻辑仍然存在于这个函数，伪代码如下：

```c
      if ( !v17 && sub_12424("http_username", v56) && compare_passwd_in_shadow((int)v56, (int)v23) )
      {
        v44 = *v13;
        if ( f_exists("/tmp/HTTPD_DEBUG") > 0 || (v45 = nvram_get_int("HTTPD_DBG"), v45 > 0) )
          v45 = sub_DB88("/jffs/HTTPD_DEBUG.log", "[%s:(%d)]: authpass!\n", "login_cgi", 14780);
        *v13 = v44;
        if ( v4 )
        {
          if ( v4 == 2 && !nvram_get_int("app_access") )
            nvram_set("app_access", "1");
        }
```

具体的值我们还是调试一下吧，具体Crossover的安装步骤我就不细说了。

> ubuntu安装包下载地址：[https://cpv2.mairuan.com/crossoverchina.com/trial/Linux/crossover-22.deb](https://cpv2.mairuan.com/crossoverchina.com/trial/Linux/crossover-22.deb)
>

最终效果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667186950257-47db8efd-46da-49e2-a72a-3bb497392300.png)

使用的gdbserver为[https://github.com/therealsaumil/static-arm-bins/blob/master/gdbserver-armel-static-8.0.1](https://github.com/therealsaumil/static-arm-bins/blob/master/gdbserver-armel-static-8.0.1)：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667191094720-457a0490-359e-45cd-b5df-7423366ee2b9.png)

这里直接attach上正在运行的httpd进程就可以了，映射端口为1234（`./gdbserver-armel-static-8.0.1 --attach :1234 3476`）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667191160116-f8c0f5af-951d-4d66-8a47-d0adb541a861.png)

配置IDA的gdbclient：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667191227911-451f67fa-a7d5-4f8c-b812-2456a520de58.png)

开始gdb，点击登录按钮后会自动断到：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667191438262-23d94a71-4b5d-4cfd-8e9c-c4ddf374040d.png)

if逻辑中有两个函数，首先来看第一个函数sub_12424，此时v52的值为`qiangwang`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667191949023-80324baa-3ee1-40e2-8461-2a52a803536b.png)

> + <font style="color:rgb(138, 143, 141);">v13 == 0</font>
>

进入该函数，则有：

```c
bool __fastcall sub_12424(int a1, const char *a2)
// 传入参数：http_username与qiangwang
{
  const char *v3; // r0

  v3 = (const char *)nvram_get();		// *v3 == "qiangwang"
  return v3 && strcmp(v3, a2) == 0;
  // return TruE
}
```

看来这个函数是没有什么问题的，那么问题就出在另外一个函数`compare_passwd_in_shadow`了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667192705374-3f20ad60-1bd0-4674-a957-e0672ce94839.png)

这个函数的符号在编译时并没有删掉，从函数名称可知它与文件`/etc/shadow`有关。`compare_passwd_in_shadow`定义在`/usr/lib/libpasswd.so`这个动态链接库中：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667272077746-8c9accf1-0411-46ce-af41-3ce379772406.png)

`/etc/passwd`和`/etc/shadow`在实体路由器的内容分别如下：

```bash
qiangwang@RT-ACRH17:/tmp/etc# cat passwd
qiangwang:x:0:0:qiangwang:/root:/bin/sh
nas:x:100:100:nas:/dev/null:/dev/null
nobody:x:65534:65534:nobody:/dev/null:/dev/null
# ---------------------------------------------------------------
qiangwang@RT-ACRH17:/tmp/etc# cat shadow
qiangwang:$1$khQvtTDa$.nfOv8HW4hJQfES8v0ufn.:0:0:99999:7:0:0:
nas:*:0:0:99999:7:0:0:
nobody:*:0:0:99999:7:0:0:
qiangwang@RT-ACRH17:/tmp/etc#
```

此时我们的qemu不存在这两个文件（chroot后），是不是因为这两个文件不存在导致的无法登录呢？直接上传：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667193088186-0dbf6bdf-d808-40f7-9db4-3dd05bfb7156.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667193134494-7091a999-e25e-464d-b1e4-5de4a28244d8.png)

拍摄快照，断开IDA远程调试，重新启动httpd后尝试登录：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667198884933-8e036e7b-eb4b-442a-bcc2-86d87de9219e.png)

哦<font style="color:rgb(51, 51, 51);">↗</font>，看来没有问题了。提示我们修改密码，这里我就都修改为`cyberangel`吧：  
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667198996636-b4c8b655-8f2d-4a6f-aa9a-3ed2c7695493.png)

耐心等待，却发现仍然要求我们修改密码？？？直接死循环了？？？

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667199018373-0f5ac2bb-2a3c-4453-8e6e-3867723186a0.png)

分别查看：`/etc/passwd`、`/etc/shadow`、`/firmadyne/libnvram/http_passwd`、`/firmadyne/libnvram/httpd_username`的值：

```bash
/ # cat /etc/passwd 
qiangwang:x:0:0:qiangwang:/root:/bin/sh
nas:x:100:100:nas:/dev/null:/dev/null
nobody:x:65534:65534:nobody:/dev/null:/dev/null
#------------------------------------------------------------------
/ # cat /etc/shadow 
qiangwang:$1$khQvtTDa$.nfOv8HW4hJQfES8v0ufn.:0:0:99999:7:0:0:
nas:*:0:0:99999:7:0:0:
nobody:*:0:0:99999:7:0:0:
#------------------------------------------------------------------
/ # cat /firmadyne/libnvram/http_passwd 
cyberangel/ # cat /firmadyne/libnvram/http_username
cyberangel/ # 
```

可以看到`http_passwd`与`httpd_username`均变成了`cyberangel`，那这究竟发生了什么情况？

### 04-4、修复无限提示修改密码的问题
macOS上访问`[http://192.168.2.250:8080/Main_Login.asp](http://192.168.50.1/Main_Login.asp)`，输入原来的密码发现提示密码错误：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667202328654-8d4755f3-2899-4f9f-a8ab-e6d7889c34af.png)

输入修改后的密码也提示错误。再次gdb调试：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667203460684-4ad66408-1bce-4f33-b810-8d1daf7090bc.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667203477871-88fd82b7-bf92-401f-b3ec-b1031b29e2f9.png)

`v52 == v19 == "cyberangel"`，可此时的passwd和shadow并没有`cyberangel`，看来登录不上去的原因是shadow没有被修改成功。会不会是权限的问题呢？将shadow与passwd chmod 777之后，恢复快照，再次尝试：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667203667724-6d893fa0-5fc1-4a97-8055-c65bb7f5ac9d.png)

结果还是提示账号密码不正确，看来不是权限的原因，而是密码修改时出现了问题 -- 系统没有修改shadow与passwd，只修改了`http_username`和`http_passwd`。解决这个问题的方法有两种：

1. 寻找passwd和shadow没有被修改的原因。
2. 修复反复提示修改密码的bug。

这里我就选择第二种方式吧，**恢复之前的快照**，此时有：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667262661683-628ad4ba-60fa-495c-a146-d3bcf433c546.png)

再试来到修改密码的界面并使用burp抓取流量包：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667204761023-a3cb8e78-4600-4df1-bc51-c1bbd3345d5a.png)

字符串`<meta http-equiv="refresh" content="0; url=Main_Password.asp">`在http也能够找到，具体函数还是`sub_29188`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667205189422-66357ce0-615c-41cb-a196-d481fe16a008.png)

核心伪代码如下：

```c
          if ( !sub_28FFC(v50) || (v54 = ATE_FACTORY_MODE_STR(), sub_12424(v54, "1")) )
          {
            if ( !strncmp(v1, "cloud_sync.asp", 0xEu) )
            {
              fprintf(a1, "<meta http-equiv=\"refresh\" content=\"0; url=%s?flag=%s\">\r\n", v1, dest);
            }
            else if ( !strcmp(v1, "cfg_onboarding.cgi") )
            {
              fprintf(
                a1,
                "<meta http-equiv=\"refresh\" content=\"0; url=cfg_onboarding.cgi?flag=AMesh&id=%s\">\r\n",
                dest);
            }
            else if ( !sub_38418(v1, 1) && sub_3851C(v1) )
            {
              fprintf(a1, "<meta http-equiv=\"refresh\" content=\"0; url=%s\">\r\n", v1);
            }
            else
            {
              fprintf(a1, "<meta http-equiv=\"refresh\" content=\"0; url=%s\">\r\n", "index.asp");
            }
          }
          else
          {
            fputs("<meta http-equiv=\"refresh\" content=\"0; url=Main_Password.asp\">\r\n", a1);// 目标字符串
          }
```

IDA对上面的第一行代码下断点，调试来到此处：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667262829220-c8ef5fa9-349a-45fd-9558-8ad4601fced4.png)

汇编窗口单步走，来到调用sub_28FFC的地方：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667262900697-aa1013eb-0c68-4059-a931-15f78b3c6e97.png)

IDA对`sub_28FFC`的反编译并不准确，它没有参数v46。如下有：

```c
bool sub_28FFC()
{
  int v0; // r0
  const char *v1; // r4
  const char *v2; // r0

  v0 = nvram_get("http_passwd");
  v1 = "";
  if ( v0 )
    v1 = (const char *)v0;
  v2 = (const char *)nvram_default_get("http_passwd");
  return strcmp(v2, v1) == 0;		// v2 == v1 == "2022qwb"
  // return 1
}
```

这个函数返回TruE，但若想进入该if语句，就得让if的其中一个条件为真才行，现在前者已经为假，只能期待着后面的条件为真喽：

```c
if ( !sub_28FFC(v46) || (v50 = ATE_FACTORY_MODE_STR(), sub_12424(v50, "1")) ){
    // ...
}
```

直接单步过`ATE_FACTORY_MODE_STR`，看看他会返回什么：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667263720372-789ded23-9b40-4f6a-a807-33d04515cbc9.png)

返回的是字符串`ATEMODE`，进入`sub_12424`：

```c
bool __fastcall sub_12424(int a1, const char *a2)	// *a1 == "ATEMODE"   *a2 == "1"
{
  const char *v3; // r0

  v3 = (const char *)nvram_get(a1);		// nvram_get("ATEMODE")
  return v3 && strcmp(v3, a2) == 0;
}
```

 大致看一眼就是到，要想返回TruE，则：

+ v3必须要有值
+ v3和a2的值相同

综上：nvram的ATEMODE值必须为"1"；即，需要使用echo在libnvram目录下写值（若想要永久生效，则需要重新编译libnvram）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667264831436-f92c2721-68fd-40dd-a672-d7bf9ce9cb2c.png)

成功进入：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667264898386-9d2b2a41-c9de-4659-a525-da5255337fa5.png)

此时访问就没问题了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667264990181-12c7b43a-e35f-4cc0-bf5b-0f17e0679aab.png)

其他页面也都是正常的：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667265586901-0b5bf673-a983-4cca-b38a-8131f6b3d298.png)

# 反思
你会发现我们使用的`libnvram`的`get_default_nvram`定义和反编译出来的不一样：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667266322932-dd6ac058-d3b4-44bb-8742-c205709bed7f.png)

而我们的nvram定义有两个参数：

```c
char *nvram_default_get(const char *key, const char *val) {		// 两个参数
    char *ret = nvram_get(key);

    PRINT_MSG("%s = %s || %s\n", key, ret, val);

    if (ret) {
        return ret;
    }

    if (val && nvram_set(key, val)) {
        return nvram_get(key);
    }

    return NULL;
}
```

因为在前面我们将原有的`libnvram.so`进行了替换，所以我打算调试看一下，回到验证逻辑处：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667262829220-c8ef5fa9-349a-45fd-9558-8ad4601fced4.png)

进入`sub_28FFC`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667267181044-2ec49683-2431-4a07-b610-1bc037ea694f.png)

单步步入`nvram_default_get`，为了确保IDA显示的参数的正确性，对下图第5行的76F15148（nvram_get）下断点，有：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667267567581-93543b99-cb4e-4eda-921f-71deb509cd7e.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667267881431-5439932a-40db-4ba1-86d6-ab4a8448c1b6.png)

我们自己的libnvram源码和伪代码均在下面的代码框中，执行完第20行的`nvram_get(key)`后返回的是字符串`2022qwb`，这会导致`nvram_default_get`在第24行直接返回

```c
int __fastcall sub_76F15190(int a1, int a2)	// *a1 == "http_passwd"  *a2 == NULL
{
  int v4; // r4

  v4 = 76F15148(a1);				// char *ret = nvram_get(key);
  ((void (__fastcall *)(int, void *, void *, int, int, int))unk_76EFC760)(
    stderr,
    &unk_76F1C4A8,
    &unk_76F15D64,
    a1,
    v4,
    a2);  							// PRINT_MSG("%s = %s || %s\n", key, ret, val);
  if ( !v4 && a2 && ((int (__fastcall *)(int, int))unk_76EFC784)(a1, a2) )	// if (val && nvram_set(key, val)) {
    return 76F15148(a1);			// return nvram_get(key);
  else
    return v4;						// return ret;
}
// -------------------------------------------------------------------------------------
char *nvram_default_get(const char *key, const char *val) {					// *a1 == "http_passwd"  *a2 == NULL
    char *ret = nvram_get(key);

    PRINT_MSG("%s = %s || %s\n", key, ret, val);

    if (ret) {			// *ret == "2022qwb"
        return ret;		// 函数返回
    }

    if (val && nvram_set(key, val)) {
        return nvram_get(key);
    }

    return NULL;
}
```

在结合之前说的，要想sub_28FFC返回False，则意味着v0（nvram_get）和v2（nvram_default_get）值不能相同：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667267181044-2ec49683-2431-4a07-b610-1bc037ea694f.png)

根据我们的hook逻辑，nvram_get和nvram_default_get值返回永远是相同的，这就是为什么前面会出现一直让你“反复设置密码的原因”，因为此时你的密码与默认后台管理密码相同。文章的最后我们来看原版是怎么做的，首先是`nvram_get`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667283309329-572b16d5-dd3c-45b4-833b-8b7bcac13317.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667282582148-dc4be142-2ae3-4b6d-a352-efc59f0a934a.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667282593085-1e116c25-c83d-42f6-b082-9c16f841beb7.png)

函数`nvram_default_get`则定义在`libshared.so`中，大致逻辑就是有一个大数组`router_defaults`存放着许多路由器的默认值，传入函数参数“键”会返回相应的默认值：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667282841183-21ab4a32-ef43-4421-bb19-02fe0bf82b56.png)

如上图所示，华硕路由器的后台默认账号密码均为admin。**<font style="color:#E8323C;">我们hook时犯下的错误就显而易见了 -- </font>**`**<font style="color:#E8323C;">nvram_default_get</font>**`**<font style="color:#E8323C;">与</font>**`**<font style="color:#E8323C;">nvram_get</font>**`**<font style="color:#E8323C;">混为一谈：</font>**

+ **<font style="color:#E8323C;">非hook：</font>**
    - `**<font style="color:#E8323C;">nvram_default_get</font>**`**<font style="color:#E8323C;">从</font>**`**<font style="color:#E8323C;">libshared.so</font>**`**<font style="color:#E8323C;">的大数组</font>**`**<font style="color:#E8323C;">router_defaults</font>**`**<font style="color:#E8323C;">获取默认值。</font>**
    - `**<font style="color:#E8323C;">nvram_get</font>**`**<font style="color:#E8323C;">通过</font>**`**<font style="color:#E8323C;">libnvram.so</font>**`**<font style="color:#E8323C;">从</font>**`**<font style="color:#E8323C;">/dev/nvram（/bin/nvram）</font>**`**<font style="color:#E8323C;">获取用户的值。</font>**
+ **<font style="color:#E8323C;">hook：</font>**
    - `**<font style="color:#E8323C;">nvram_default_get</font>**`**<font style="color:#E8323C;">、</font>**`**<font style="color:#E8323C;">nvram_get</font>**`**<font style="color:#E8323C;">均从修改的</font>**`**<font style="color:#E8323C;">libnvram.so</font>**`**<font style="color:#E8323C;">获取值，导致获取的值一模一样。</font>**

最后的最后：

> + 本篇文章中并没有去研究修改后台密码的二进制逻辑，大家如果感兴趣的话可以根据本篇文章进行研究：
>
> ![](https://cdn.nlark.com/yuque/0/2022/png/574026/1667283891279-fabbda9f-625e-4499-8d3b-8b1be54a53a8.png)
>

