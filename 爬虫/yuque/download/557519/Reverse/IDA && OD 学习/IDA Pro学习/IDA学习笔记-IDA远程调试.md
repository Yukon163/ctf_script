> 2019NCTF-debug（IDA远程调试）
>

配置报错解决方法：

<font style="color:#F5222D;">Linux执行可执行文件提示No such file or directory的解决方法：</font>

[https://blog.csdn.net/sun927/article/details/46593129](https://blog.csdn.net/sun927/article/details/46593129)

<font style="color:#F5222D;">Incompatible debugging server:address size is 4 bytes, expected 4 </font><font style="color:#000000;">的</font>解决方法：

<font style="color:#333333;">你的android_server 是32位的 </font>

<font style="color:#333333;">而你启动的 ida 是64位的 </font>

<font style="color:#333333;">换成32位的ida 就OK</font>



材料：linux虚拟机、debug文件一个、IDA7.0

首先我们需要启动ubuntu（linux），然后在Windows环境下找到IDA的安装目录：

例如，我的是：D:\Program Files (x86)\IDA_Pro_v7.0\dbgsrv

将dbgsrv目录完整的拷贝到ubuntu中（我拷贝到ubuntu的桌面上）

我的是：/home/ubuntu/Desktop/

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575177643324-715ff99e-b168-4e0b-8fdb-dedbe5995ec8.png)



接下来我们需要确定debug处理器的位数，在debug目录下右键打开终端，输入file debug：

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575177780067-ae6449ff-d174-451b-bcfd-ae5164238885.png)

ELF 64-bit，说明它是64位可执行文件

然后我们在Windows环境下的IDA里配置，打开64为的IDA：将debug载入到IDA中

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575178719200-14573b5d-f73e-499e-9611-2ea1c3a7a57c.png)

在菜单栏上选中：调试器->选择调试器

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575178746190-d954d946-063f-4521-b326-b35a48888a3f.png)

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575178788904-76e3cdc9-da64-48f4-8525-b2f8ce6cdf2d.png)

选中Remote Linux debugger，点击确定

再次单击菜单栏中的调试器->进程选项

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575178836200-eaaddb1c-b310-437c-9d2d-0563f1024d76.png)

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575179253969-4bdf556c-a3cb-4035-b3df-c7c17a49e5e2.png)

应用程序、输入文件、目录、主机名、端口都是虚拟机的参数（其他空白就好）

主机名就是IP地址，那linux的IP地址怎么看？

在linux中终端中输入ip addr

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575179108783-05ead593-1dc3-4d3e-998a-6ea64f4436bf.png)

其中：红色划线部分为虚拟机的IP地址，如下图

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575179133737-478e1b5a-f4a7-463f-a62f-8f04a9970886.png)

接下来，我们开始调试：

首先输入在dbgsrv中打开终端：输入chmod a+x linux_server64（因为虚拟机的系统是64位的）给所有用户增加权限；

> 注意给debug elf权限：chmod a+x debug
>

接着：输入：./linux_server64（linux为64位，无法执行32位的程序，会提示<font style="color:#F5222D;">No such file or directory</font>，需要安装32的库），启动远程调试服务

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575180472762-e1329311-5752-41f0-b84d-04bb30580b4c.png)

在IDA里打开![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575180462136-d3411172-d7da-4429-b0f0-de953b1d099e.png)

启动！

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575180546489-32f31901-1259-453f-a3e4-0fc51772938f.png)

单击“是”，IDA界面如下

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575180568132-2480e5c9-10ea-4c57-84bc-a99b8a5bdd5b.png)

linux终端界面如下：

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575180596510-efb728f1-ce0d-4b8b-b16b-7d6e4ca070be.png)

题目提示：远程调试即可得到flag

在IDA进行文本搜索：NCTF

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575180739986-0982d0cf-fab4-4d7c-9865-01e5aa5392bc.png)![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575180746753-00212290-f489-430b-ad7f-56c68cb9763b.png)

确定，搜索真的好慢。。。耐心。。。。

NCTF{just_debug_it_2333}

