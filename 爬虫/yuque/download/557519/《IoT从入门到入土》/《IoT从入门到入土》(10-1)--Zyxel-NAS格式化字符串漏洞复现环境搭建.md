> + Ubuntu虚拟机网络链接方式为“桥接”。
> + 本文首发于IOTsec-Zone
>

# 1、前言
之前在IoTsec-Zone社区的安全情报中看到了一个NAS的CVE（`CVE-2022-34747`），其漏洞类型是一直没有遇到过的格式化字符串漏洞，本篇文章我们先搭建一下环境。

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669864571935-12f57057-ff3b-44de-b50f-b381243484af.png)

# 2、基本分析
访问Zyxel的`Security-Advisories`知道影响范围包含了型号NAS326、NAS540、NAS542：

> + [https://www.zyxel.com/global/en/support/security-advisories/zyxel-security-advisory-for-format-string-vulnerability-in-nas](https://www.zyxel.com/global/en/support/security-advisories/zyxel-security-advisory-for-format-string-vulnerability-in-nas)
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669077120616-45dfd385-6e77-4221-b85c-3c1c707f0651.png)

该漏洞已经在该型号的最新版本固件`V5.21(AAZF.12)C0`中修复，查看最新版本的Release Note有如下这么两句轻描淡写的话：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669076951018-1dc22a2d-b7f7-4e7d-ac90-c086e05e3ebb.png)

对于NAS326来说，受影响的版本为`V5.21(AAZF.11)C0`以及之前，所以下载相应的包含漏洞的固件就好。这里我选择下载`V5.21(AAZF.10)C0`与最新版本`V5.21(AAZF.12)C0`（`V5.21(AAZF.11)C0`官网已经不让下载了）：

+ [https://download.zyxel.com/NAS326/firmware/NAS326_V5.21(AAZF.10)C0.zip](https://download.zyxel.com/NAS326/firmware/NAS326_V5.21(AAZF.10)C0.zip)【V5.21(AAZF.10)C0】
+ [https://download.zyxel.com/NAS326/firmware/NAS326_V5.21(AAZF.12)C0.zip](https://download.zyxel.com/NAS326/firmware/NAS326_V5.21(AAZF.12)C0.zip)【V5.21(AAZF.12)C0】

对两个固件分别解压后使用`BeyondCompare`进行diff，如下图所示；噗，果然如更新日志说的那样，可执行文件`nsuagent`确实被删除了。

> + `BeyondCompare`：[https://www.scootersoftware.com/download.php](https://www.scootersoftware.com/download.php)
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669078021949-82c1d9ca-db21-428f-a717-418d5543fbfd.png)

那么漏洞基本可以确定是出现在`nsuagent`上了，不然官方没有理由移除这个文件。既然是格式化字符串漏洞，那么我们可以使用IDA的LazyIDA插件辅助我们具体定位：

> + `LazyIDA`：[https://github.com/L4ys/LazyIDA](https://github.com/L4ys/LazyIDA)
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669078780846-039421fb-0233-4745-98d7-a51e88565584.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669078812186-092fce7a-49e1-41bd-ad70-a91770e1fc5b.png)

双击点进去查看第一个`fprintf`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669078841967-24a0c7b5-6c54-4258-b0f2-30a18a11a959.png)

根据`fprintf`函数声明：`int fprintf(FILE *stream, const char *format, ...)`，那没跑了，如果`fprintf`的第二个参数s可以被控制，则可造成格式化字符串漏洞。**这里需要注意，前面的**`**vnsprintf**`**并不存在格式化字符串漏洞，因为其格式化字符串为固定的，如：**`"username: %s, password: %s\n"`**。**

> + 不一定要用LazyIDA，也可以使用VulFi定位漏洞点：
>
> ![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669079197936-125eb4ac-d51f-4772-ab7d-9e89dd3552c7.png)
>

# 3、环境搭建
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669079482289-217a2394-44fc-46fe-a3a8-f0fb4e2870ed.png)

如果仔细看的话会发现，这两个文件系统包含的固件内容均不完整且恰好互补，所以想要顺利的模拟成功就需要手动将两个解压后的两个文件夹合并（合并后的文件夹我命名为了rootfs）。目标文件`nsuagent`为ARM架构，我仍然选择使用qemu-system模式进行模拟，命令如下：

```bash
# Ubuntu虚拟机--------------------------------------------------------------------------------
$ tar czf rootfs.tar.gz ./rootfs
$ sudo tunctl -t tap0
$ sudo ifconfig tap0 192.168.5.2/24
$ sudo qemu-system-arm -M vexpress-a9 -kernel vmlinuz-3.2.0-4-vexpress \
  -initrd initrd.img-3.2.0-4-vexpress \
  -drive if=sd,file=debian_wheezy_armhf_standard.qcow2 \
  -append "root=/dev/mmcblk0p2" -smp 2,cores=2 \
  -net nic -net tap,ifname=tap0,script=no,downscript=no -nographic
# qemu----------------------------------------------------------------------------------------
$ ifconfig eth0 192.168.5.1/24
# Ubuntu虚拟机--------------------------------------------------------------------------------
$ scp ./rootfs.tar.gz root@192.168.5.1:/root/
# qemu----------------------------------------------------------------------------------------
$ tar -zxvf ./rootfs.tar.gz
$ cd ./rootfs
$ chmod -R 777 ./*
$ cd ../
$ mount -o bind /dev ./rootfs/dev && mount -t proc /proc ./rootfs/proc
$ chroot ./rootfs sh
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669164920258-cdd47a77-6627-4a01-b282-f9d053db4e22.png)

尝试直接运行`/usr/sbin/nsuagent`会出现报`/usr/lib/libz.so.1: file too short`的错误，如下图所示

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669000575111-b2159795-e5a0-4b71-8c00-83cb68c14014.png)

查看该动态链接库：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669080456261-008c97f2-94c8-407e-b24a-c9e135a110ed.png)

寄！软链接在binwalk解压的时候好像出现了问题，其实它应该软链接到`libz.so.1.2.8`:

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669080528021-b8161a3e-d969-405f-8f10-6329ac979058.png)

得，根据报错手动修复吧...

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669080756604-49ff0871-beec-4f77-bedf-6572978499dc.png)

所有需要修复的软链接如下：

```bash
$ rm ./libz.so.1
$ ln -s ./libz.so.1.2.8 ./libz.so.1
$ ls -al ./libz.so.1
lrwxrwxrwx 1 cyberangel cyberangel 15 11月 22 09:32 ./libz.so.1 -> ./libz.so.1.2.8
$ rm ./libsmbclient.so.0
$ ln -s ./libsmbclient.so.0.2.1 ./libsmbclient.so.0
$ rm ./libpam.so.0
$ ln -s ./libpam.so.0.83.1 ./libpam.so.0
$ rm ./libpthread.so.0           
$ ln -s ./libpthread-2.20-2014.11.so ./libpthread.so.0
$ rm ./libsamba-util.so.0
$ ln -s ./libsamba-util.so.0.0.1 ./libsamba-util.so.0
$ rm ./libtalloc.so.2
$ ln -s ./libtalloc.so.2.0.8 ./libtalloc.so.2
$ rm ./libndr.so.0
$ ln -s ./libndr.so.0.0.2 ./libndr.so.0
$ rm ./libndr-standard.so.0
$ ln -s ./libndr-standard.so.0.0.1 ./libndr-standard.so.0
$ rm ./libtevent.so.0
$ ln -s ./libtevent.so.0.9.18 ./libtevent.so.0
$ rm ./libwbclient.so.0
$ ln -s ./libwbclient.so.0.11 ./libwbclient.so.0
$ rm ./libsamba-credentials.so.0
$ ln -s ./libsamba-credentials.so.0.0.1 ./libsamba-credentials.so.0
$ rm ./libgensec.so.0
$ ln -s ./libgensec.so.0.0.1 ./libgensec.so.0
$ rm ./libsamba-hostconfig.so.0
$ ln -s ./libsamba-hostconfig.so.0.0.1 ./libsamba-hostconfig.so.0
$ rm ./libndr-nbt.so.0
$ ln -s ./libndr-nbt.so.0.0.1 ./libndr-nbt.so.0
$ rm ./libtevent-util.so.0
$ ln -s ./libtevent-util.so.0.0.1 ./ibtevent-util.so.0
$ rm ./ibtevent-util.so.0 
$ ln -s ./libtevent-util.so.0.0.1 ./libtevent-util.so.0
$ rm ./libcom_err.so.2
$ ln -s ./libcom_err.so.2.1 ./libcom_err.so.2
$ rm ./libdcerpc-binding.so.0
$ ln -s ./libdcerpc-binding.so.0.0.1 ./libdcerpc-binding.so.0
$ rm ./libtdb.so.1
$ ln -s ./libtdb.so.1.2.12 ./libtdb.so.1
$ rm ./libnsl.so.1
$ ln -s ./libnsl-2.20-2014.11.so ./libnsl.so.1
$ rm ./liblber-2.4.so.2
$ ln -s ./liblber-2.4.so.2.10.3 ./liblber-2.4.so.2
$ rm ./libldap-2.4.so.2
$ ln -s ./libldap-2.4.so.2.10.3 ./libldap-2.4.so.2
$ rm ./libkrb5-samba4.so.26
$ ln -s ./libkrb5-samba4.so.26.0.0 ./libkrb5-samba4.so.26
$ rm ./libgssapi-samba4.so.2
$ ln -s ./libgssapi-samba4.so.2.0.0 ./libgssapi-samba4.so.2
$ rm ./libldb.so.1
$ ln -s ./libldb.so.1.1.16 ./libldb.so.1
$ rm ./libasn1-samba4.so.8
$ ln -s ./libasn1-samba4.so.8.0.0 ./libasn1-samba4.so.8
$ rm ./libsamdb.so.0
$ ln -s ./libsamdb.so.0.0.1 ./libsamdb.so.0
$ rm ./libntdb.so.0
$ ln -s ./libntdb.so.0.9 ./libntdb.so.0
$ rm ./libattr.so.1
$ ln -s ./libattr.so.1.1.0 ./libattr.so.1
$ rm ./libresolv.so.2
$ ln -s ./libresolv-2.20-2014.11.so ./libresolv.so.2
$ rm ./libheimbase-samba4.so.1
$ ln -s ./libheimbase-samba4.so.1.0.0 ./libheimbase-samba4.so.1 
$ rm ./libroken-samba4.so.19
$ ln -s ./libroken-samba4.so.19.0.1 ./libroken-samba4.so.19
$ rm ./libhx509-samba4.so.5
$ ln -s ./libhx509-samba4.so.5.0.0 ./libhx509-samba4.so.5
$ rm ./libhcrypto-samba4.so.5
$ ln -s ./libhcrypto-samba4.so.5.0.1 ./libhcrypto-samba4.so.5
$ rm ./libwind-samba4.so.0
$ ln -s ./libwind-samba4.so.0.0.0 ./libwind-samba4.so.0
$ rm ./libndr-krb5pac.so.0
$ ln -s ./libndr-krb5pac.so.0.0.1 ./libndr-krb5pac.so.0
$ rm ./libgnutls.so.28
$ ln -s ./libgnutls.so.28.41.4 ./libgnutls.so.28
$ rm ./libgcrypt.so.20
$ ln -s ./libgcrypt.so.20.0.3 ./libgcrypt.so.20
$ rm ./libpcre.so.1
$ ln -s ./libpcre.so.1.2.4 ./libpcre.so.1
$ rm ./libnettle.so.4
$ ln -s ./libnettle.so.4.7 ./libnettle.so.4
$ rm ./libhogweed.so.2
$ ln -s ./libhogweed.so.2.5 ./libhogweed.so.2
$ rm ./libgmp.so.10
$ ln -s ./libgmp.so.10.2.0 ./libgmp.so.10
$ rm ./libpcreposix.so.0
$ ln -s ./libpcreposix.so.0.0.3 ./libpcreposix.so.0
$ rm ./libgpg-error.so.0
$ ln -s ./libgpg-error.so.0.10.0 ./libgpg-error.so.0
```

再次尝试运行：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669164643154-9accb6f2-216a-451e-9944-9af1ea1e3be6.png)

emmm，程序没有任何输出。IDA逆向后发现main函数调用了daemon，导致程序启动后转入了后台运行，故我们无法查看它的状态：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669009716215-3ab34d70-41ef-4e26-861c-d518970e8fc7.png)

解决方式也很简单，nop掉main的`daemon`函数就可以了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669009867218-ab7ceed3-b740-4a4a-a4e0-d7e4e31d6dc2.png)

保存导出后替换原来的`nsuagent`文件，再次启动却发现还是会报错：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669165111794-4b28b433-a158-45db-a355-178b59f72d23.png)

如上图所示，`nsuagent`在执行的过程中会调用脚本文件`/bin/nsa400getconfig.sh`，交叉引用后可以得到调用链：`main -> sub_19A80 -> sub_17550`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669087413130-1dc01d9a-7aae-42d2-9301-042bdf443c87.png)

popen执行脚本后会将结果返回给v4，然后调用fread函数将结果读取到ptr中，之后程序可能会根据这个返回内容进行处理与判断。所以这个脚本关系着环境搭建的成功与否，下面我们将注意力集中到这个脚本（代码如下面代码框所示），仔细观察会发现程序的所有报错基本上都是由它引起的：

```bash
#!/bin/sh

IFCONFIG="busybox ifconfig"
ROUTE="busybox route"
AWK="/bin/awk"
CUT="/bin/cut"
GREP="/bin/grep"
CAT="/bin/cat"
HOSTNAME="/bin/hostname"
FIRMWARE_INFO_PATH=`cat /etc/settings/firmware_info_path`"/mnt/info/fwversion"
WebPort=`${CAT} /etc/service_conf/httpd_zld.conf | grep Listen | cut -d " " -f2 | sed -n '1p'`

BOND_NAME="bond0"

ETH1_NAME="egiga0"
IP1=""
MASK1=""
GATEWAY1=""
DHCP1=""

ETH2_NAME="egiga1"
IP2=""
MASK2=""
GATEWAY2=""
DHCP2=""

Bond0_linked=`cat /sys/class/net/bond0/carrier`
if [ "${Bond0_linked}" == "1" ]; then 
	BondingON="yes"
else
	BondingON="no"
fi

if [ "${BondingON}" == "yes" ]; then #Bonding on
	IP1=`${IFCONFIG} bond0 | ${GREP} "inet addr" | ${CUT} -d: -f2 | ${CUT} -d" " -f1`
	MASK1=`${IFCONFIG} bond0 | ${GREP} "inet addr" | ${CUT} -d: -f4`
	GATEWAY1=`${ROUTE} -n | ${GREP} bond0 | ${AWK} '$1 == "0.0.0.0" {print $2}'`
	DHCP1=`ps | ${GREP} dhcp | ${GREP} bond0`
	METRIC1=5;
	if [ "${DHCP1}" == "" ]; then
		DHCP1="static"
	else
		DHCP1="dhcp"
	fi

	BondingMode=`${CAT} /sys/class/net/bond0 | ${GREP} "active-backup"`

	if [ "${BondingMode}" == "" ]; then
		BondingMode=`${CAT} /sys/class/net/bond0 | ${GREP} "balancing"`
		if [ "${BondingMode}" == "" ]; then
			BondingMode="link-aggregation"
		else
			BondingMode="adaptive-load-balancing"
		fi
	else
		BondingMode="active-backup"
	fi
else
	#checks if egiga0 is up and linked
	egiga0_link=`${CAT} /sys/class/net/${ETH1_NAME}/carrier`
	if [ ${egiga0_link} -eq 1 ]; then
		IP1=`${IFCONFIG} ${ETH1_NAME} | ${GREP} "inet addr" | ${CUT} -d: -f2 | ${CUT} -d" " -f1`
		MASK1=`${IFCONFIG} ${ETH1_NAME} | ${GREP} "inet addr" | ${CUT} -d: -f4`
		GATEWAY1=`${ROUTE} -n| ${GREP} ${ETH1_NAME} | ${AWK} '$1 == "0.0.0.0" {print $2}'`
		#METRIC1=`${ROUTE} -n | ${GREP} ${ETH1_NAME} | ${AWK} '$1 == "0.0.0.0" {print $5}'`
	else
		IP1="0.0.0.0"
		MASK1="0.0.0.0"
		GATEWAY1="0.0.0.0"
		METRIC1=20
	fi
	DHCP1=`ps | ${GREP} dhcpcd_request | ${GREP} ${ETH1_NAME}`
	if [ "${DHCP1}" == "" ]; then
		DHCP1="static"
	else
		DHCP1="dhcp"
	fi

	#checks if egiga1 is up and linked
	if [ -e "/sys/class/net/${ETH2_NAME}" ]; then
		egiga1_link=`${CAT} /sys/class/net/${ETH2_NAME}/carrier`
		if [ ${egiga1_link} -eq 1 ]; then
			IP2=`${IFCONFIG} ${ETH2_NAME} | ${GREP} "inet addr" | ${CUT} -d: -f2 | ${CUT} -d" " -f1`
			MASK2=`${IFCONFIG} ${ETH2_NAME} | ${GREP} "inet addr" | ${CUT} -d: -f4`
			GATEWAY2=`${ROUTE} -n| ${GREP} ${ETH2_NAME} | ${AWK} '$1 == "0.0.0.0" {print $2}'`
			#METRIC2=`${ROUTE} -n | ${GREP} ${ETH2_NAME}| ${AWK} '$1 == "0.0.0.0" {print $5}'`
		else
			IP2="0.0.0.0"
			MASK2="0.0.0.0"
			GATEWAY2="0.0.0.0"
			METRIC2=22
		fi
		DHCP2=`ps | ${GREP} dhcpcd_request | ${GREP} ${ETH2_NAME}`
		if [ "${DHCP2}" == "" ]; then
			DHCP2="static"
		else
			DHCP2="dhcp"
		fi
	fi
fi

#The firmare later that 5.10 doesn't rely on the metric value to determine which interface is the default value. But the NSU Client have to be compatible with the older models and firmware, the gateway of which is indicated by the metric value.
default_gateway=`/usr/bin/python -c "from lib import config_api; pyconf = config_api.ConfigOperator(); print pyconf.get_conf_value('network.interface', 'default_gateway')"`
if [ "${default_gateway}" == "${ETH2_NAME}" ]; then
	METRIC1=7
	METRIC2=5
else
	METRIC1=5
	METRIC2=7
fi


Hostname=`${HOSTNAME}`
Modelname=`${CAT} /etc/modelname`

FwVersion=`${CAT} ${FIRMWARE_INFO_PATH}`


DNS_FETCH=`/usr/bin/python -c "from lib import config_api; pyconf = config_api.ConfigOperator(); print pyconf.get_conf_value('network.interface.nameserver', 'fetch')"`
if [ "${DNS_FETCH}" == "manually" ]; then
	AutoDNS="no"
else
	AutoDNS="yes"
fi

PRIDNS=`${CAT} /etc/resolv.conf | ${AWK} '/nameserver/ {print $2}' | sed -n '1p'`
SECDNS=`${CAT} /etc/resolv.conf | ${AWK} '/nameserver/ {print $2}' | sed -n '2p'`

MAC1=`${IFCONFIG} ${ETH1_NAME} | ${GREP} HWaddr | tr -s ' ' | ${CUT} -d ' '  -f5`
if [ -e "/sys/class/net/${ETH2_NAME}" ]; then
	MAC2=`${IFCONFIG} ${ETH2_NAME} | ${GREP} HWaddr | tr -s ' ' | ${CUT} -d ' '  -f5`
fi

NasID=${MAC1}


PPPoE_Enable=`ps | grep pppoe | grep -v "grep"`
if [ "${PPPoE_Enable}" == "" ]; then
	PPPoE_Enable="no"
else
	PPPoE_Enable="yes"
fi

if [ ${PPPoE_Enable} == "yes" ]; then
	PPPoE_IP=`${IFCONFIG} ppp0 | ${GREP} "inet addr" | ${CUT} -d: -f2 | ${CUT} -d" " -f1`
	PPPoE_MASK=`${IFCONFIG} ppp0 | ${GREP} "Mask" | ${CUT} -d: -f4`
	PPPoE_DNS=`${CAT} /etc/ppp/resolv.conf | ${AWK} '/nameserver/ {print $2}' | sed -n '1p'`
	PPPoE_UserID=`/usr/bin/python -c "from lib import config_api; pyconf = config_api.ConfigOperator(); print pyconf.get_conf_value('network.interface.ppp0', 'account')"`
	PPPoE_PassWd=`/usr/bin/python -c "from lib import config_api; pyconf = config_api.ConfigOperator(); print pyconf.get_conf_value('network.interface.ppp0', 'password')"`
fi

TIME_ZONE=`python -c "from models import date_time_main_model; print date_time_main_model.getTimeZone_for_nsu()"`

if [ "${IP1}" == "" ]; then
	IP1="0.0.0.0"
fi

if [ "${MASK1}" == "" ]; then
	MASK1="0.0.0.0"
fi

if [ "${GATEWAY1}" == "" ]; then
	GATEWAY1="0.0.0.0"
fi

if [ -e "/sys/class/net/${ETH2_NAME}" ]; then
	[ "${IP2}" == "" ] && IP2="0.0.0.0"
	[ "${MASK2}" == "" ] && MASK2="0.0.0.0"
	[ "${GATEWAY2}" == "" ] && GATEWAY2="0.0.0.0"
fi

if [ "${PPPoE_IP}" == "" ]; then
	PPPoE_IP="0.0.0.0"
fi

if [ "${PPPoE_MASK}" == "" ]; then
	PPPoE_MASK="0.0.0.0"
fi

if [ "${PPPoE_DNS}" == "" ]; then
	PPPoE_DNS="0.0.0.0"
fi

echo "IP type1: ${DHCP1}"
echo "IP address1: ${IP1}"
echo "netmask1: ${MASK1}"
echo "gateway1: ${GATEWAY1}"
echo "MAC address1: ${MAC1}"
echo "metric1: ${METRIC1}"

if [ "${BondingON}" == "no" ]; then
	if [ -e "/sys/class/net/${ETH2_NAME}" ]; then
		echo "IP type2: ${DHCP2}"
		echo "IP address2: ${IP2}"
		echo "netmask2: ${MASK2}"
		echo "gateway2: ${GATEWAY2}"
		echo "MAC address2: ${MAC2}"
		echo "metric2: ${METRIC2}"
	fi
fi

echo "hostname: ${Hostname}"
echo "autoDNS: ${AutoDNS}"
echo "name-server-1: ${PRIDNS}"
echo "name-server-2: ${SECDNS}"
echo "model name: ${Modelname}"
echo "fwversion: ${FwVersion}"
echo "WebGUIPort: ${WebPort}"
echo "NAS_ID: ${NasID}"
echo "Bonding Driver Setting:"
echo "  activate: ${BondingON}"
echo "  mode: ${BondingMode}"
echo "PPPoE_Enable: ${PPPoE_Enable}"
echo "PPPoE_IP: ${PPPoE_IP}"
echo "PPPoE_Mask: ${PPPoE_MASK}"
echo "PPPoE_DNS: ${PPPoE_DNS}"
echo "PPPoE_UserID: ${PPPoE_UserID}"
echo "PPPoE_PassWd: ${PPPoE_PassWd}"
echo "Time_Zone: ${TIME_ZONE}"

# get the total and used size for all volume
USED_TOTAL_SIZE=`python -c "from models import storage_main; print storage_main.MainGetAllVolSizUsed_Total()"`

# total volume size (in KB)
TOTAL_SIZE=`echo ${USED_TOTAL_SIZE} | awk -F"/" '{print $2}'`
echo "totalVolSize: ${TOTAL_SIZE}"

# total used volume size (in KB)
TOTAL_USED=`echo ${USED_TOTAL_SIZE} | awk -F"/" '{print $1}'`
echo "totalUsedSize: ${TOTAL_USED}"

# FTP port ("" means no FTP is listening now)
echo "ftpPort: `cat /var/zyxel/pure-ftpd.arg | cut -d "S" -f2 | cut -d" " -f2`"


shotID=0
hdAmount=0
sdx_array="`ls -d /sys/block/sd? | awk -F "/" '{print $4}'`"

for sdx in ${sdx_array}
do
	[ "`/sbin/intern_disk_chker -c ${sdx}`" != "yes" ] && continue

	hdAmount=$((${hdAmount}+1))
	DISK_SIZE_SECTOR=`cat /sys/block/${sdx}/size`
	DISK_SIZE_K=$((${DISK_SIZE_SECTOR}/2))

	shotID=`cat "/tmp/intern_disk.map" | grep ${sdx} | cut -c 5`
	echo "DISK${shotID}_SIZE: ${DISK_SIZE_K}"
done

# HD amount
echo "hdAmount: ${hdAmount}"

# md status
cd /i-data/sysvol
if [ "$?" != "0" ]; then
	echo "raidType:"
else
	# NOTE:
	#       this raid type is fake now! just used to determine if raid
	#       available now
	echo "raidType: JBOD"
fi

# revision
echo "revision: `cat /firmware/mnt/info/revision`"

# customer
echo "customer: ZyXEL"

# installed packages
#/usr/bin/ipkg-cl -f /etc/zyxel/pkg_conf/zypkg_conf/zy-pkg.conf -t /i-data/.system/zy-pkgs/tmp list | grep -A4 "^pkgName" > /tmp/all.lst
#PKGS="`cat /tmp/all.lst | grep -v "version:" | grep -v "description:" | grep -v "URL:"|grep -B2 -E "(Built-in)|(Enable)" | grep "pkgName" | awk -F' ' '{print $2}'`"
#echo "pkgInstalled: `echo "${PKGS}" | tr '\n' ';'`"

#because the v5.2 move the admin page to desktop, remove the shortcut for NSU
echo "pkgInstalled: "

exit 0

```

单独执行`/bin/nsa400getconfig.sh`，有如下日志：

```bash
/ # /bin/nsa400getconfig.sh
cat: can't open '/sys/class/net/bond0/carrier': No such file or directory
cat: can't open '/sys/class/net/egiga0/carrier': No such file or directory
sh: 1: unknown operand
cat: can't open '/firmware/mnt/info/fwversion': No such file or directory
ifconfig: egiga0: error fetching interface information: Device not found
IP type1: static
IP address1: 0.0.0.0
netmask1: 0.0.0.0
gateway1: 0.0.0.0
MAC address1: 
metric1: 5
hostname: debian-armhf
autoDNS: yes
name-server-1: 192.168.1.1
name-server-2: 
model name: NAS326
fwversion: 
WebGUIPort: 80
NAS_ID: 
Bonding Driver Setting:
  activate: no
  mode: 
PPPoE_Enable: no
PPPoE_IP: 0.0.0.0
PPPoE_Mask: 0.0.0.0
PPPoE_DNS: 0.0.0.0
PPPoE_UserID: 
PPPoE_PassWd: 
Time_Zone: 
totalVolSize: 
totalUsedSize: 
cat: can't open '/var/zyxel/pure-ftpd.arg': No such file or directory
ftpPort: 
ls: /sys/block/sd?: No such file or directory
hdAmount: 0
/bin/nsa400getconfig.sh: cd: line 255: can't cd to /i-data/sysvol
raidType:
cat: can't open '/firmware/mnt/info/revision': No such file or directory
revision: 
customer: ZyXEL
pkgInstalled: 
/ # 
```

看来报错还真的不少，我们一个一个来解决吧。前两个有关于网卡的报错都和`sys`有关：

+ `cat: can't open '/sys/class/net/bond0/carrier': No such file or directory`，这里暂时先忽略。
+ `cat: can't open '/sys/class/net/egiga0/carrier': No such file or directory`

我们退出shell去挂载一下：`mount -vt sysfs sysfs ./rootfs/sys`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669166442464-c7669e17-567a-4d74-8b78-a633fb5aad7c.png)

因为我们的qemu网卡是`eth0`，所以将脚本中的`ETH1_NAME="egiga0"`更改为`ETH1_NAME="eth0"`，再次执行就可以正常的获取网卡信息了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669166611933-b6b8c086-920f-4fac-8905-3d816d11e6f3.png)

针对其他报错的处理方式不再详细说明，我都写在下面了：

+ `cat: can't open '/firmware/mnt/info/fwversion': No such file or directory`：
    - `mkdir -p /firmware/mnt/info/`
    - 随便写一个就好：`echo "NAS326" > /firmware/mnt/info/fwversion`
+ `can't open '/var/zyxel/pure-ftpd.arg': No such file or directory`：
    - 通常来说ftp的端口默认为21：`echo 21 > /var/zyxel/pure-ftpd.arg`
+ `can't cd to /i-data/sysvol`：
    - `mkdir -p /i-data/sysvol`
+ `can't open '/firmware/mnt/info/revision': No such file or directory`：
    - 随便写一个就好：`echo 0 > /firmware/mnt/info/revision`
+ `ls: /sys/block/sd?: No such file or directory`：看名字可能与NAS的存储有关，这里暂不处理。

再次启动`nsuagent`，端口为50127的UDP：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669168464674-84b67a8e-559b-413f-a81e-d438b2f19a6f.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669168566615-c99476dc-1816-4edd-abc7-c980e6af1851.png)

emmm，看起来像是成功了，但是我觉得还没有模拟完全？提出这个问题的原因是我注意到脚本中还调用了python（`/usr/bin/python -c [...]`），可是python起不来啊：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669169441829-e533eb31-898f-4db7-8a08-4ff134d6024b.png)

使用strace跟踪一下系统调用看看？

> + 适用于arm的strace-static：[https://github.com/andrew-d/static-binaries/blob/master/binaries/linux/arm/strace](https://github.com/andrew-d/static-binaries/blob/master/binaries/linux/arm/strace)
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669169527654-e1dd798a-17a6-4b90-9fc6-927f036fd19f.png)

`Exec format error`，我去，我才反应过来是软链接的问题：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669169598272-01fb01ec-721d-42f5-bff8-4a488da67eea.png)

将python与python2这两个软连接修复完成之后，还需要修复如下软链接：

+ `ln -s /usr/lib/libutil-2.20-2014.11.so /usr/lib/libutil.so.1`
+ `ln -s /usr/lib/libsqlite3.so.0.8.6 /usr/lib/libsqlite3.so.0`

再次执行`nsa400getconfig.sh`，仍需我们进一步处理报错：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669169885622-b6eb35d4-eb0b-4522-92ce-1e09016665c6.png)

看来是python代码出错了，根据`nsa400getconfig.sh`的内容确定一下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669170410398-0c7241ef-e5d9-474a-a7a3-1a4a64f810c1.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669170459503-39d754ec-c84b-48be-b81a-e26977f86983.png)

对于此固件来说，所有的python脚本均以编译后的pyc文件形式存在，要想查看它的代码只需要使用`uncompyle6`进行反编译即可（`pip install uncompyle6`）。对`uncompyle6 date_time_main_model.pyc`反编译后的结果如下：

```python
# uncompyle6 version 3.8.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.17 (default, Jul  1 2022, 15:56:32) 
# [GCC 7.5.0]
# Warning: this version of Python has problems handling the Python 3 byte type in constants properly.

# Embedded file name: /home/release-build/NAS326/521AAZF10B2/sysapps/web_framework/build/models/date_time_main_model.py.pre
# Compiled at: 2021-04-01 10:00:23
"""This model offers all relative functions about date_time.
"""
from lib import config_api, tools
import shlex, re, subprocess, os, time
from re import sub as re_sub
from time import sleep
import datetime
from datetime import date
from calendar import Calendar
from time import gmtime, strftime
from models.system_main_model import write_pyconf
pyconf = config_api.ConfigOperator()
DATE_TIME_PYCONF_PATH = 'system.date_time'
GET_TIME = 'date +%T'
GET_DATE = 'date +%x'
GET_TIME_S = 'date +%s'
PATH_DATE = '/bin/date'
NTPDATE_AGENT = '/usr/sbin/ntpdate_agent'
UPDATE_SCHEDULE_JOB = '/usr/bin/restart_scheduler.sh > /dev/null 2>&1 &'
YEAR_LIMIT = 2038
SYS_TO_RTC = '/sbin/rtcAccess systortc'
PATH_AUTO_DST = '/usr/sbin/dst.sh'
DST_FILE_PATH = '/i-data/.system/zoneinfo/'
ZONE_RULE_FILE = '/var/zyxel/myzone_rule'
PATH_ZIC = '/usr/sbin/zic'
ZONE_FORMAT_FILE = '/etc/MyZone'
LOCALTIME_TIME_PATH = '/etc/localtime'
MONTH_LIST = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
TIMEZONE_DICT = {'-12:00': 'Eniwetok,Kwajalein', '-11:00': 'Midway Island,Samoa', '-10:00': 'Hawaii', '-09:00': 'Alaska', '-08:00': 'Pacific Time (US & Canada)', '-07:00': 'Mountain Time (US & Canada)', '-06:00': 'Central America', 
   '-05:00': 'Indiana(East)', '-04:30': 'Caracas', '-04:00': 'Atlantic Time (Canada)', '-03:30': 'Newfoundland', '-03:00': 'Brasilia', '-02:00': 'Mid-Atlantic', '-01:00': 'Azores', 
   '+00:00': 'Casablanca', '+01:00': 'Central,West Africa', '+02:00': 'Amman', '+03:00': 'Baghdad', '+03:30': 'Tehran', '+04:00': 'Moscow,Saint Petersburg,Volgograd', '+04:30': 'Kabul', 
   '+05:00': 'Ekaterinburg', '+05:30': 'Chennai,Kolkata,Mumbai,New Delhi', '+05:45': 'Kathmandu', '+06:00': 'Yekaterinburg', '+06:30': 'Yangon (Rangoon)', '+07:00': 'Omsk', '+08:00': 'Taipei', 
   '+09:00': 'Irkutsk', '+09:30': 'Adelaide', '+10:00': 'Brisbane', '+11:00': 'Vladivostok', '+12:00': 'Magadan', '+13:00': "Nuku'alofa"}

def get_date_time_pyconf(key):
    return pyconf.get_conf_value(DATE_TIME_PYCONF_PATH, key)


def get_time():
    psPopen = subprocess.Popen(GET_TIME, shell=True, close_fds=True, stdin=None, stdout=subprocess.PIPE, stderr=None)
    time = psPopen.stdout.read().strip('\r\n')
    return {'current_time': time}


def get_date():
    psPopen = subprocess.Popen(GET_DATE, shell=True, close_fds=True, stdin=None, stdout=subprocess.PIPE, stderr=None)
    date = psPopen.stdout.read().strip('\r\n')
    date = re.split('/', date)
    year = date[2]
    mon = date[0]
    day = date[1]
    date = '20%s-%s-%s' % (year, mon, day)
    return {'current_date': date}


def set_date_time(date, time):
    date = re.split('/', date)
    year = date[2]
    mon = date[0]
    day = date[1]
    if int(year) >= YEAR_LIMIT:
        return 'year error'
    date = '%s%s0000%s' % (mon, day, year)
    cmd = '%s %s' % (PATH_DATE, date)
    cmd_set = shlex.split(cmd)
    tools.execRoot(cmd_set)
    cmd = '%s %s' % (PATH_DATE, time)
    cmd_set = shlex.split(cmd)
    tools.execRoot(cmd_set)
    cmd = '%s' % SYS_TO_RTC
    cmd_set = shlex.split(cmd)
    tools.execRoot(cmd_set)
    return 'Success'


def get_ntpstatus():
    active = get_date_time_pyconf('NTP_active')
    server = get_date_time_pyconf('NTP_server')
    last_update_time = get_date_time_pyconf('NTP_last_update_time')
    NTP_result = {'NTP_active': active, 'NTP_server': server, 'NTP_last_update_time': last_update_time}
    return {'ntp_status': NTP_result}


def set_ntpserver(ntpserver):
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'NTP_server', ntpserver)
    return 'Success'


def ntpsync(ntpserver):
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'timeServerActive', 'true')
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'timeServerAddr', ntpserver)
    cmd = '%s %s &' % (NTPDATE_AGENT, ntpserver)
    cmd_set = shlex.split(cmd)
    tools.execRoot(cmd_set)
    cmd = '%s' % SYS_TO_RTC
    cmd_set = shlex.split(cmd)
    tools.execRoot(cmd_set)
    return 'Success'


def disablentp():
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'NTP_active', 'no')
    return 'Success'


def migrate_clock_saving_interval(clock_interval):
    startMon = re.search('begin (\\w+)', clock_interval)
    begin_tmp = 'begin ' + startMon.group(1)
    startOrd = re.search(begin_tmp + ' (\\w+)', clock_interval)
    begin_tmp = begin_tmp + ' ' + startOrd.group(1)
    startWeek = re.search(begin_tmp + ' (\\w+)', clock_interval)
    begin_tmp = begin_tmp + ' ' + startWeek.group(1)
    startHour = re.search(begin_tmp + ' (\\w+)', clock_interval)
    begin_tmp = begin_tmp + ' ' + startHour.group(1)
    startMin = re.search(begin_tmp + ':(\\w+)', clock_interval)
    startMon = startMon.group(1)
    startMon = startMon[0].upper() + startMon[1:]
    startWeek = startWeek.group(1)
    startWeek = startWeek[0].upper() + startWeek[1:]
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startMon', startMon)
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startOrd', startOrd.group(1))
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startWeek', startWeek)
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startHour', startHour.group(1))
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startMin', startMin.group(1))
    endMon = re.search('end (\\w+)', clock_interval)
    begin_tmp = 'end ' + endMon.group(1)
    endOrd = re.search(begin_tmp + ' (\\w+)', clock_interval)
    begin_tmp = begin_tmp + ' ' + endOrd.group(1)
    endWeek = re.search(begin_tmp + ' (\\w+)', clock_interval)
    begin_tmp = begin_tmp + ' ' + endWeek.group(1)
    endHour = re.search(begin_tmp + ' (\\w+)', clock_interval)
    begin_tmp = begin_tmp + ' ' + endHour.group(1)
    endMin = re.search(begin_tmp + ':(\\w+)', clock_interval)
    begin_tmp = begin_tmp + ':' + endMin.group(1) + ' '
    offset = re.split(begin_tmp, clock_interval)
    endMon = endMon.group(1)
    endMon = endMon[0].upper() + endMon[1:]
    endWeek = endWeek.group(1)
    endWeek = endWeek[0].upper() + endWeek[1:]
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endMon', endMon)
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endOrd', endOrd.group(1))
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endWeek', endWeek)
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endHour', endHour.group(1))
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endMin', endMin.group(1))
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'offset', offset[1].strip('\r\n'))
    return 'Success'


def parse_date_time_conf(zysh_conf):
    is_ntp_active = 0
    zyconf_ntp_server = ''
    zyconf_auto_daylight_active = ''
    zyconf_clock_saving_interval = ''
    zyconf_clock_time_zone = ''
    try:
        with open(zysh_conf, 'r') as (r_file):
            for line in r_file:
                if 'ntp server' in line:
                    zyconf_ntp_server = line
                    name = line.strip('ntp ')
                    name = name.strip('server ')
                    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'timeServerAddr', name.strip('\r\n'))
                if 'clock time-zone' in line:
                    zyconf_clock_time_zone = line
                if 'clock saving-interval' in line:
                    zyconf_clock_saving_interval = line
                    if migrate_clock_saving_interval(zyconf_clock_saving_interval) != 'Success':
                        print 'migrate_clock_saving_interval error'
                if 'clock daylight-saving' in line:
                    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'daylightSaving', 'true')
                if 'daylight_saving start' in line:
                    zyconf_auto_daylight_active = line
                    area_path = re.search('daylight_saving start "(\\w+)', zyconf_auto_daylight_active)
                    city_path = re.search('in "(\\w+)', zyconf_auto_daylight_active)
                    if area_path:
                        daylight_path = area_path.group(1) + '/' + city_path.group(1)
                        DST_check_path = DST_FILE_PATH + daylight_path
                        if not os.path.exists(DST_check_path):
                            daylight_path = area_path.group(1)
                        pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'autoDaylightType', daylight_path)
                        pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'daylightSaving', 'true')
                        pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'autoDaylightStatus', 'true')
                    if zyconf_clock_time_zone:
                        time_zone = re.split('clock time-zone ', zyconf_clock_time_zone)
                        time_zone = time_zone[1]
                        time_zone = time_zone[:3] + ':' + time_zone[3:]
                        if city_path.group(1).strip('\r\n') == 'NULL':
                            city = TIMEZONE_DICT[time_zone.strip('\r\n')]
                        else:
                            city = city_path.group(1).strip('\r\n')
                        timezoneCountry = '%s/%s' % (time_zone.strip('\r\n'), city)
                        pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'timezoneCountry', timezoneCountry)
                    break

            with open(zysh_conf, 'r') as (r_file):
                conf = r_file.read()
                if zyconf_ntp_server:
                    zyconf_ntp_server = '!\r\n' + zyconf_ntp_server
                    conf = re_sub(zyconf_ntp_server, '', conf)
                conf = re_sub('clock time-zone \\W\\d\\d\\d\\d', '', conf)
                conf = re_sub('clock daylight-saving', '', conf)
                if zyconf_auto_daylight_active:
                    zyconf_auto_daylight_active = '!\r\n' + zyconf_auto_daylight_active
                    conf = re_sub(zyconf_auto_daylight_active, '', conf)
                conf = re_sub(zyconf_clock_saving_interval, '', conf)
            with open(zysh_conf, 'w') as (w_file):
                w_file.write(conf)
    except IOError:
        pass

    try:
        with open(zysh_conf, 'r') as (r_file):
            for line in r_file:
                if 'ntp' in line:
                    is_ntp_active = 1
                    break

        if is_ntp_active == 0:
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'NTP_active', 'no')
        if is_ntp_active == 1:
            with open(zysh_conf, 'r') as (r_file):
                conf = r_file.read()
                conf = re_sub('!\r\nntp', '', conf)
            with open(zysh_conf, 'w') as (w_file):
                w_file.write(conf)
    except IOError:
        pass


def getDateTimeStatus():
    psPopen = subprocess.Popen(PATH_DATE, shell=True, close_fds=True, stdin=None, stdout=subprocess.PIPE, stderr=None)
    time = psPopen.stdout.read().strip('\r\n')
    today = re.split(' ', str(time))
    psPopen = subprocess.Popen(GET_TIME, shell=True, close_fds=True, stdin=None, stdout=subprocess.PIPE, stderr=None)
    time = psPopen.stdout.read().strip('\r\n')
    if today[2]:
        current_time = '%s %s, %s %s' % (today[1], today[2], date.today().year, time)
    else:
        current_time = '%s %s, %s %s' % (today[1], today[3], date.today().year, time)
    timeServerActive = get_date_time_pyconf('timeServerActive')
    timeServerAddr = get_date_time_pyconf('timeServerAddr')
    timezoneCountry = get_date_time_pyconf('timezoneCountry')
    daylightSaving = get_date_time_pyconf('daylightSaving')
    autoDaylightStatus = get_date_time_pyconf('autoDaylightStatus')
    autoDaylightType = get_date_time_pyconf('autoDaylightType')
    startMon = get_date_time_pyconf('startMon')
    startOrd = get_date_time_pyconf('startOrd')
    startWeek = get_date_time_pyconf('startWeek')
    startHour = get_date_time_pyconf('startHour')
    startMin = get_date_time_pyconf('startMin')
    endMon = get_date_time_pyconf('endMon')
    endOrd = get_date_time_pyconf('endOrd')
    endWeek = get_date_time_pyconf('endWeek')
    endHour = get_date_time_pyconf('endHour')
    offset = get_date_time_pyconf('offset')
    endMin = get_date_time_pyconf('endMin')
    date_time_result = {'currentTime': current_time, 'timeServerActive': timeServerActive, 'timeServerAddr': timeServerAddr, 'timezoneCountry': timezoneCountry, 
       'daylightSaving': daylightSaving, 'autoDaylightStatus': autoDaylightStatus, 'autoDaylightType': autoDaylightType, 
       'startMon': startMon, 'startOrd': startOrd, 'startWeek': startWeek, 'startHour': startHour, 'startMin': startMin, 
       'endMon': endMon, 'endOrd': endOrd, 'endWeek': endWeek, 'endHour': endHour, 'endMin': endMin, 'offset': offset}
    return date_time_result


def setTime(time_s):
    today = re.split(' ', str(time_s))
    time = today[4]
    if MONTH_LIST.index(today[1]) + 1 < 10:
        set_date = '0%s' % (MONTH_LIST.index(today[1]) + 1)
    else:
        set_date = '%s' % (MONTH_LIST.index(today[1]) + 1)
    date = '%s/%s/%s' % (set_date, today[2], today[3])
    ret = set_date_time(date, time)
    return ret


def sync_time():
    timezoneCountry = get_date_time_pyconf('timezoneCountry')
    zone = re.split(':', timezoneCountry)
    hour = zone[0]
    if os.path.exists(ZONE_RULE_FILE) == False:
        cmd = '%s %s' % ('/bin/touch', ZONE_RULE_FILE)
        cmd_set = shlex.split(cmd)
        tools.execRoot(cmd_set)
        cmd = '%s 777 %s' % ('/bin/chmod', ZONE_RULE_FILE)
        cmd_set = shlex.split(cmd)
        tools.execRoot(cmd_set)
    else:
        cmd = '%s 777 %s' % ('/bin/chmod', ZONE_RULE_FILE)
        cmd_set = shlex.split(cmd)
        tools.execRoot(cmd_set)
    if get_date_time_pyconf('daylightSaving') == 'true' and get_date_time_pyconf('autoDaylightStatus') == 'false':
        try:
            with open(ZONE_RULE_FILE, 'w') as (w_file):
                conf = '#Rule\tNAME\tFROM\tTO\tTYPE\tIN\tON\tAT\tSAVE\tLETTER/S\n'
                w_file.write(conf)
                for years in range(4):
                    start_date = manual_get_start_date(years)
                    start_time = re.split('-', str(start_date))
                    year = int(start_time[0])
                    get_day = start_time[2]
                    get_day = re.split(' ', str(get_day))
                    day = int(get_day[0])
                    check_int = float(get_date_time_pyconf('offset'))
                    if len(get_date_time_pyconf('offset')) == 3:
                        conf = 'Rule\tMyRule\t%s\tonly\t-\t%s\t%s\t%s:%s\t%s:30\t        D\n' % (year, get_date_time_pyconf('startMon'), day, get_date_time_pyconf('startHour'), get_date_time_pyconf('startMin'), int(check_int))
                    else:
                        conf = 'Rule\tMyRule\t%s\tonly\t-\t%s\t%s\t%s:%s\t%s:0\t        D\n' % (year, get_date_time_pyconf('startMon'), day, get_date_time_pyconf('startHour'), get_date_time_pyconf('startMin'), int(check_int))
                    w_file.write(conf)
                    end_date = manual_get_end_date(years)
                    end_time = re.split('-', str(end_date))
                    year = int(end_time[0])
                    get_day = end_time[2]
                    get_day = re.split(' ', str(get_day))
                    day = int(get_day[0])
                    conf = 'Rule\tMyRule\t%s\tonly\t-\t%s\t%s\t%s:%s\t0\t        -\n\n' % (year, get_date_time_pyconf('endMon'), day, get_date_time_pyconf('endHour'), get_date_time_pyconf('endMin'))
                    w_file.write(conf)

                conf = '# Zone  NAME\tGMTOFF\tRULES/SAVE\tFORMAT  [UNTIL]\n'
                w_file.write(conf)
                conf = 'Zone    MyZone\t%s:00\tMyRule\t%s\n' % (hour, '%sGMT')
                w_file.write(conf)
        except IOError:
            print 'open %s fail' % ZONE_RULE_FILE

    else:
        try:
            with open(ZONE_RULE_FILE, 'w') as (w_file):
                conf = '#Rule\tNAME\tFROM\tTO\tTYPE\tIN\tON\tAT\tSAVE\tLETTER/S\n'
                w_file.write(conf)
                conf = 'Rule\tMyRule\t%s\tonly\t-\tJun\t1\t00:00\t0\t- \n\n' % date.today().year
                w_file.write(conf)
                conf = '# Zone  NAME\tGMTOFF\tRULES/SAVE\tFORMAT  [UNTIL]\n'
                w_file.write(conf)
                conf = 'Zone    MyZone\t%s:00\tMyRule\t%s\n' % (hour, '%sGMT')
                w_file.write(conf)
        except IOError:
            print 'open %s fail' % ZONE_RULE_FILE

    cmd = '%s -d /etc %s' % (PATH_ZIC, ZONE_RULE_FILE)
    cmd_set = shlex.split(cmd)
    tools.execRoot(cmd_set)
    cmd = '/bin/ln -s -f %s %s' % (ZONE_FORMAT_FILE, LOCALTIME_TIME_PATH)
    cmd_set = shlex.split(cmd)
    tools.execRoot(cmd_set)
    return 'Success'


def auto_daylight_run(status, country):
    if status == 'disable':
        cmd = PATH_AUTO_DST + ' disable'
        psPopen = subprocess.Popen(cmd, shell=True, close_fds=True, stdin=None, stdout=subprocess.PIPE, stderr=None)
    else:
        cmd = '%s enable %s' % (PATH_AUTO_DST, country)
        cmd_set = shlex.split(cmd)
        tools.execRoot(cmd_set)
    return 'Success'


def manual_get_start_date(year):
    start_mon = MONTH_LIST.index(get_date_time_pyconf('startMon')) + 1
    start_year = date.today().year + year
    start_time = '1 %s %s' % (get_date_time_pyconf('startMon'), start_year)
    d = time.strptime(start_time, '%d %b %Y')
    weeks = strftime('%U', d)
    start_time = '%s %s %s' % (start_year, weeks, get_date_time_pyconf('startWeek'))
    mytime = datetime.datetime.strptime(start_time, '%Y %W %a')
    this_mon = re.split('-', str(mytime))
    if start_mon > int(this_mon[1]):
        weeks = int(weeks) + 1
    if start_mon == 1:
        start_time = '%s %s %s' % (start_year, '0', 'Mon')
        mytime = datetime.datetime.strptime(start_time, '%Y %W %a')
        mytime = re.split(' ', str(mytime))
        check_week = '%s-01-01' % start_year
        if check_week == mytime[0]:
            weeks = int(weeks) + 1
    if get_date_time_pyconf('startOrd') == 'last':
        check_time = '%s %s %s' % (start_year, int(weeks) + 4, get_date_time_pyconf('startWeek'))
        mytime = datetime.datetime.strptime(check_time, '%Y %W %a')
        check_mon = re.split('-', str(mytime))
        if int(check_mon[1]) == int(this_mon[1]):
            weeks = int(weeks) + 4
        else:
            weeks = int(weeks) + 3
    else:
        weeks = int(weeks) + (int(get_date_time_pyconf('startOrd')) - 1)
    start_time = '%s %s %s' % (start_year, weeks, get_date_time_pyconf('startWeek'))
    mytime = datetime.datetime.strptime(start_time, '%Y %W %a')
    if get_date_time_pyconf('startOrd') == 'last':
        weeks = int(weeks) + 1
        start_time = '%s %s %s' % (start_year, weeks, get_date_time_pyconf('startWeek'))
        check_time = datetime.datetime.strptime(start_time, '%Y %W %a')
        check_mon = re.split('-', str(check_time))
        if int(check_mon[1]) == start_mon:
            mytime = check_time
    return mytime


def manual_get_end_date(year):
    start_mon = MONTH_LIST.index(get_date_time_pyconf('startMon')) + 1
    end_mon = MONTH_LIST.index(get_date_time_pyconf('endMon')) + 1
    if start_mon > end_mon:
        end_year = date.today().year + year + 1
    else:
        end_year = date.today().year + year
    end_time = '1 %s %s' % (get_date_time_pyconf('endMon'), end_year)
    d = time.strptime(end_time, '%d %b %Y')
    weeks = strftime('%U', d)
    end_time = '%s %s %s' % (end_year, weeks, get_date_time_pyconf('endWeek'))
    mytime = datetime.datetime.strptime(end_time, '%Y %W %a')
    this_mon = re.split('-', str(mytime))
    if end_mon > int(this_mon[1]):
        weeks = int(weeks) + 1
    if end_mon == 1:
        end_time = '%s %s %s' % (end_year, '0', 'Mon')
        mytime = datetime.datetime.strptime(end_time, '%Y %W %a')
        mytime = re.split(' ', str(mytime))
        check_week = '%s-01-01' % end_year
        if check_week == mytime[0]:
            weeks = int(weeks) + 1
    if get_date_time_pyconf('endOrd') == 'last':
        check_time = '%s %s %s' % (end_year, int(weeks) + 4, get_date_time_pyconf('endWeek'))
        mytime = datetime.datetime.strptime(check_time, '%Y %W %a')
        check_mon = re.split('-', str(mytime))
        if int(check_mon[1]) == int(this_mon[1]):
            weeks = int(weeks) + 4
        else:
            weeks = int(weeks) + 3
    else:
        weeks = int(weeks) + (int(get_date_time_pyconf('endOrd')) - 1)
    end_time = '%s %s %s' % (end_year, weeks, get_date_time_pyconf('endWeek'))
    mytime = datetime.datetime.strptime(end_time, '%Y %W %a')
    if get_date_time_pyconf('endOrd') == 'last':
        weeks = int(weeks) + 1
        end_time = '%s %s %s' % (end_year, weeks, get_date_time_pyconf('endWeek'))
        check_time = datetime.datetime.strptime(end_time, '%Y %W %a')
        check_mon = re.split('-', str(check_time))
        if int(check_mon[1]) == end_mon:
            mytime = check_time
    return mytime


def sync_date_time_status():
    timeServerActive = get_date_time_pyconf('timeServerActive')
    timeServerAddr = get_date_time_pyconf('timeServerAddr')
    daylightSaving = get_date_time_pyconf('daylightSaving')
    autoDaylightStatus = get_date_time_pyconf('autoDaylightStatus')
    autoDaylightType = get_date_time_pyconf('autoDaylightType')
    if timeServerActive == 'true':
        ntpsync(timeServerAddr)
    sync_time()
    if autoDaylightStatus == 'true' and daylightSaving == 'true':
        auto_daylight_run('enable', autoDaylightType)
    subprocess.Popen(UPDATE_SCHEDULE_JOB, shell=True, close_fds=True, stdin=None, stdout=subprocess.PIPE, stderr=None)
    return


def setTimeZone_for_nsu(city, tzData, tzValue):
    city_str_nsu2gui_map = {'Mexico City,Mounterry,Guadalajara': 'Mexico City,Monterrey,Guadalajara', 
       'Indiana (East)': 'Indiana(East)', 
       'Harare,Pitori': 'Harare,Pretoria', 
       'Islamabad,Karachi': 'Islamabad, Karachi'}
    if city_str_nsu2gui_map.has_key(city):
        city = city_str_nsu2gui_map[city]
    timezoneCountry = '%s:%s/%s' % (tzValue[:3], tzValue[3:], city)
    autoDaylightType = tzData
    setTimeZone(timezoneCountry, autoDaylightType, False)


def getTimeZone_for_nsu():
    city_str_gui2nsu_map = {'Mexico City,Monterrey,Guadalajara': 'Mexico City,Mounterry,Guadalajara', 
       'Indiana(East)': 'Indiana (East)', 
       'Harare,Pretoria': 'Harare,Pitori', 
       'Islamabad, Karachi': 'Islamabad,Karachi'}
    city = get_date_time_pyconf('timezoneCountry').split('/', 1)[(-1)]
    if city_str_gui2nsu_map.has_key(city):
        city = city_str_gui2nsu_map[city]
    return city


def setTimeZone(timezoneCountry, autoDaylightType, save_pyconf=True):
    if autoDaylightType == '':
        autoDaylightStatus = 'false'
        daylightSaving = 'false'
    else:
        autoDaylightStatus = 'true'
        daylightSaving = 'true'
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'timezoneCountry', timezoneCountry)
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'daylightSaving', daylightSaving)
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'autoDaylightType', autoDaylightType)
    pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'autoDaylightStatus', autoDaylightStatus)
    sync_date_time_status()
    if save_pyconf:
        write_pyconf()


def setDateTimeStatus(arguments):
    try:
        pre_daylightSaving = get_date_time_pyconf('daylightSaving')
        pre_autoDaylightStatus = get_date_time_pyconf('autoDaylightStatus')
        pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'timezoneCountry', arguments['timezoneCountry'])
        pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'daylightSaving', arguments['daylightSaving'])
        pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'autoDaylightType', arguments['autoDaylightType'])
        pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'autoDaylightStatus', arguments['autoDaylightStatus'])
        if arguments['timeServerActive'] == 'true':
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'timeServerActive', arguments['timeServerActive'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'timeServerAddr', arguments['timeServerAddr'])
            ret = ntpsync(arguments['timeServerAddr'])
        else:
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'timeServerActive', arguments['timeServerActive'])
            ret = setTime(arguments['manuallyTime'])
        if arguments['daylightSaving'] == 'true' and arguments['autoDaylightStatus'] == 'false':
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startMon', arguments['startMon'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startOrd', arguments['startOrd'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startWeek', arguments['startWeek'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startHour', arguments['startHour'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'startMin', arguments['startMin'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endMon', arguments['endMon'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endOrd', arguments['endOrd'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endWeek', arguments['endWeek'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endHour', arguments['endHour'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'endMin', arguments['endMin'])
            pyconf.modify_conf_value(DATE_TIME_PYCONF_PATH, 'offset', arguments['offset'])
        ret = sync_time()
        if arguments['daylightSaving'] == 'true':
            if arguments['autoDaylightStatus'] == 'true':
                ret = auto_daylight_run('enable', arguments['autoDaylightType'])
            elif pre_daylightSaving == 'true' and pre_autoDaylightStatus == 'true':
                ret = auto_daylight_run('disable', 'Nope')
        elif pre_daylightSaving == 'true' and pre_autoDaylightStatus == 'false':
            ret = auto_daylight_run('disable', 'Nope')
        subprocess.Popen(UPDATE_SCHEDULE_JOB, shell=True, close_fds=True, stdin=None, stdout=subprocess.PIPE, stderr=None)
    except Exception as e:
        tools.pylog(str(e))
        print 'except:%s' % e

    return ret
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669182922581-657f801b-afec-42f7-a79a-90a36adbb2a8.png)

如上图所示，来到报错函数`getTimeZone_for_nsu`，进一步追踪`get_date_time_pyconf`：

```python
def get_date_time_pyconf(key):
    return pyconf.get_conf_value(DATE_TIME_PYCONF_PATH, key)	# DATE_TIME_PYCONF_PATH = 'system.date_time'
```

另外，在此py文件的开头还需要我们注意一点，对象`pyconf`由`config_api.ConfigOperator`定义：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669182991183-3cd884f6-8efc-4b3f-9936-c81126071c6d.png)

即，初始化类时加载的文件为`config_api.pyc`，反编译它：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669170894754-5ba989a3-ccc6-4522-891a-d7cf35ea8148.png)

很明显，类`ConfigOperator`调用了文件`/var/web_framework/py_conf`，但在解包的rootfs中并未找到`py_conf`，而找到了两个md5值相同的`py_conf_delaut`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669171168838-5f2e197d-4b4e-44a8-8976-745ffbe864bf.png)

我们很容易寻找到`py_conf_delaut`与`py_conf`之间的关系，后者都是由前者复制过来的：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669171329600-507d38a2-8139-4b0b-a524-96785ebd5ec6.png)

所以随便选一个文件就行，在qemu中执行如下命令：

+ `cp -a /usr/local/apache/web_framework/data/config/py_conf_default /etc/zyxel/py_conf`
+ `cp -a /etc/zyxel/py_conf /var/web_framework/`

再执行一下脚本：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669171580224-594c57a1-d9a7-414f-82b7-236a1e47e445.png)

看起来没有任何多余的报错了，挺好。kill掉原来的nsuagent进程，重新启动：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669171665948-94ea746d-66cd-4a84-88cc-e93547f5a5bf.png)

好了，回过头再来仔细看Bug fix的两句话：

+ `[Vulnerability] Format string vulnerability`
+ `Remove nsuagent and do not support NAS starter utility（utility：工具）`

看来移除`nsuagent`后就不支持`NAS starter utility`这个工具了。为了方便调试，我们在Windows安装`NSU_2.01_1018.msi`后，将安装目录下的所有文件压缩传到Ubuntu，Crossover运行之：

> + `NAS starter utility`下载地址：[https://zyxel-nas-starter-utility.software.informer.com/download/](https://zyxel-nas-starter-utility.software.informer.com/download/)
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669168958660-1dc0abdf-d2de-4294-bbeb-51b649679d0b.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669171792048-acbc0ea6-a697-438a-890a-0fcda9888f82.png)

emmm，为什么这个软件没有`发现（discovery）`出我们的设备呢，如上图所示；并且注意到qemu中运行的`nsuagent`开始报错了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669171830158-78459b7a-bca8-4659-a081-4bdba17ada1a.png)

这说明软件与nsuagent是有通信流量的，识别不出来有可能还是网卡的问题，还是来到IDA的`nsuagent`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669172105691-93b426f9-0bb5-4058-8acb-9a2f2a9dc56b.png)

都是硬编码的`egiga`，并没有我们的`eth`，所以可能需要将网卡名称改一下：

```bash
$ ifconfig eth0 down
$ ip link set eth0 name egiga0
$ ifconfig egiga0 up
```

修改前后的效果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669172197411-23c7067f-4c88-4b04-a0bc-adecc90ec598.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669172285689-0fd2d821-65c7-439d-9da4-aef6c993ee8e.png)

挺好，网络仍然是正常的：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669172343682-b6e2d8b4-c37f-4ba1-b0a6-eecf9834d835.png)

最后将脚本改回来：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669172423485-0de62831-4fe6-4a44-a316-19ead14a8bc0.png)

再次尝试启动`nsuagent`，稍等片刻之后就会出现我们的设备：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669172473550-bf9563ba-5279-48f1-95a3-c3450598312e.png)

此时启动wireshark抓取tap0的流量：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669172707281-27a50cf5-21d9-46ba-b1ee-f3bccdbf6036.png)

在软件中进入NAS管理界面，注意状态一定要是`Unreachable`，而不是`Down`，如果是后者请重启软件或等待几秒钟；点击`Show the directory of the NAS`，随便输入账号密码后点击登录：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669172997404-47259d6c-482b-4e02-b0f7-f291a7faab8b.png)

登录时的流量包如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669173102654-2eba4a97-ad01-49c2-adc6-9e9fd2740107.png)

搭建完成！

# 4、附件及其说明
> 附件链接： [https://pan.baidu.com/s/1niU-71inmTf-Z3TCndEPwg](https://pan.baidu.com/s/1niU-71inmTf-Z3TCndEPwg) 提取码: j7vq
>

```bash
cyberangel@cyberangel:~/Desktop/$ tree -L 1 ./Zyxel_ENV
./Zyxel_ENV
├── 521AAZF10C0.bin								# 含有漏洞的固件
├── _521AAZF10C0.bin.extracted		# 漏洞固件解包
├── diff													# 漏洞固件解包与最新固件解包的diff
├── images												# 我打包好的qemu镜像
├── LazyIDA-master.zip
├── NAS326_V5.21(AAZF.10)C0.zip
├── NAS326_V5.21(AAZF.12)C0.zip
├── nsa320_2.01.zip								# NAS管理软件.msi.zip
├── nsuagent_patch								# patch掉daemon的nsuagent
├── nsuagent_vuln									# 未经修改的nsuagent
├── rootfs												# 合并后的文件系统						
├── rootfs_bk.tar.gz							# 未修复软链接的完整文件系统						
├── strace
├── ZyXEL													# NAS管理软件
├── Zyxel_wireshark.pcapng				# 流量包
└── ZyXEL													# NAS管理软件zip

5 directories, 11 files

cyberangel@cyberangel:~/Desktop/$ 
```

