都知道服务器的端口开的越多服务器越危险，所以在本篇文章中我们不采用开放安全组端口的方式向外暴露端口进行ssh登录docker的操作，而是利用服务器ssh默认向外开放的22端口作为跳板向内连接docker（不开放安全组端口）。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632795712249-20766901-38c3-48ad-a6fd-d5a4226e6285.png)

> 如上图所示，在采用这种方法之前，我的服务器上存在着许多向外暴露的docker端口（10001-10009），也就是说其他电脑可以直接连接我的端口，所以通过安全组放行的端口登录docker很危险，端口越多越危险。
>
> ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632809372078-dcbdd806-2b78-425a-8325-964bc23d290f.png)
>

# 在本机上下载vscode的ssh插件
> 本机指的是自己的电脑
>

在vscode中下载插件Remote Development：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632796396282-f983b43e-307a-4c4c-896e-ffee0c4ae79f.png)

安装之后在vscode的侧边栏会出现一个小电脑图标：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632796542016-664c8f44-1221-43c6-91a2-b8de06f917fb.png)

# 配置服务器的免密登录
点击"小电脑图标"，打开远程资源管理器：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632796651710-3df229e1-b56c-4d5b-9de2-8e1ebbf03b9f.png)

然后点击旁边的![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632796674628-6fd00135-9a8c-49d1-9912-5b59e9082e66.png)图标，打开第一个配置文件：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632796711683-1bd75c0f-2b37-405c-bd08-f999c71c4874.png)

第一次配置时打开这个文件是默认有一个例子在里面，由于我不是第一次配置，这里就不展示了:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632796996624-5a1d91ef-85f5-4c26-ac64-314b612b4c06.png)

首先我们在这个文件中写入服务器的信息：

```c
Host Cyberangel-Cloud_Server   #这个可以自己起名字
    HostName 42.192.???.???    #自己服务器的地址
    User ubuntu				   #服务器的用户名
    port 22					   #服务器向外暴露的ssh端口
```

填写完毕后会在ssh的侧边栏出现自己填写的服务器：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632797415263-af3b7e6a-433e-4687-871c-dc7e1770463f.png)

没有的话可以点击![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632796674628-6fd00135-9a8c-49d1-9912-5b59e9082e66.png)旁边的刷新按钮![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632797495568-1848281a-f7ca-41b5-89e7-e9e38f1ef764.png)；右击上图第一个红箭头所指的地方，连接服务器：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632797594376-d7edb91a-0fee-4558-a276-b36f5e58f117.png)

输入密码连接服务器后看一下有关ssh的配置文件夹：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632796028688-eb1dbfad-f564-432f-b546-9bfd808182c8.png)

> 打开终端方法，Windows同：
>
> ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632797833716-b6dcc57e-eb04-47cf-8b2e-3a6707f06481.png)
>

服务器上已经默认安装好了ssh，文件authorized_keys为空或不存在则表示还没有配置免密登录（即登录时要求输入密码）。之后我们打开本机的命令行开始生成ssh的私钥和公钥(一路回车即可)：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632798766157-624f87cd-0fde-4f47-bf24-ddc1df730fc6.png)

然后将公钥上传到服务器上：

```c
ssh-copy-id #刚才在vscode中填写的服务器Host
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632798898829-687d57a7-302f-4425-96aa-f660762e81f1.png)

再在ssh的配置文件中添加一行：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632799090067-50ee6443-5664-4fe0-a522-7db2d4b12443.png)

尝试一下免密登录：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632799216589-7163bc3d-586a-4d4f-a962-b4b3cbfcf55d.png)

> 也可以执行：ssh ubuntu@42.192.???.??? -p 22进行登录
>

无需输入密码即可登录成功，输入logout以退出服务器。

# 配置docker的免密登录
在服务器上随便pull一个自己需要的docker（文章中采用Ubuntu），然后在run docker时配置命令如下：

```c
ubuntu@VM-0-3-ubuntu:~$ sudo docker images
REPOSITORY                TAG       IMAGE ID       CREATED         SIZE
......
ubuntu                    xenial    38b3fa4640d4   2 months ago    135MB
......
ubuntu@VM-0-3-ubuntu:~$ 
#################################################################################
sudo docker run -it -p 10001:22 --privileged --name=pwn_16.04 ubuntu:xenial /bin/bash
#sudo:以管理员身份运行此命令
#docker run -it:创建docker，以交互模式运行
#-p 10001:22 ：10001:docker向外映射的端口，22:docker内部的ssh默认的22端口
#--privileged：在docker中拥有“真”root权限（在某些情况下具有重要作用）
#--name=pwn_16.04：要创建docker的名称为pwn_16.04
#ubuntu:xenial：拉取的docker镜像REPOSITORY和TAG
#/bin/bash：创建docker后运行docker的命令
```

> docker有关命令和问题请自行搜索，这里只说明ssh的配置；-p 10001:22中的10001可以换成其他的端口号
>

run之后会自动进入docker内部：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632799591338-48c2aeff-cd59-490f-8b31-5f8912573526.png)

在docker中执行“apt update && apt install openssh-server”安装ssh服务，安装完成之后对ssh服务进行配置：

```c
root@eb0c116ec9cc:/# vim /etc/ssh/sshd_config
#注意是sshd_config而不是ssh_config
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632799975803-119ddfc8-5177-4c1b-b0ae-fdb3945e2a47.png)

> 将PermitRootLogin选项取消注释，然后将其配置更改为yes；其他选项默认不动。
>

保存退出，在docker中输入passwd root修改root用户的密码，最后重启docker的ssh服务：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632800197635-0c06afc4-97f7-4337-9027-ad301b3bc434.png)

接下来我们需要在本机中增加ssh的配置选项：

```c
Host Cyberangel-Cloud_Server
    HostName 42.192.149.124
    User ubuntu
    port 22
    IdentityFile "~/.ssh/id_rsa"
 
Host Cyberangel-Cloud_docker_16     #任意起名字
    HostName localhost              #必须写localhost
    User root						#通过ssh登录docker中的root
    Port 10001						#docker对外开放的端口
    ProxyCommand ssh ubuntu@Cyberangel-Cloud_Server -W %h:%p  
#和“Host Cyberangel-Cloud_Server”相照应
#ubuntu@Cyberangel-Cloud_Server分别对应Cyberangel-Cloud_Server中的Host和User
```

然后在本机的终端中连接Cyberangel-Cloud_docker_16：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632807131522-1f1bb2d1-8902-408e-8280-7f7aab8ff38e.png)

输入密码即可登录，登出后执行“ssh-copy-id Cyberangel-Cloud_docker_16”以配置免密登录:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632807249353-4fb8e3d9-1719-4e92-aee6-2632337beea2.png)

再次尝试登录docker：ssh Cyberangel-Cloud_docker_16:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632807285363-3ca49f87-bc5d-401c-ba74-83bf4b86d4e2.png)

无需输入密码即可远程登录docker。

# vscode免密登录docker
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1632807432902-8178fa01-ac81-45d9-9a9f-d326eb04f288.png)

+ 直接连接:本机->服务器10001端口->连接docker
+ 间接连接:本机->服务器22端口->docker 10001端口->连接docker

> 有问题请在下面评论区留言，我会第一时间回复。
>

