> 文章参考自：[https://cloud.tencent.com/developer/article/1744139](https://cloud.tencent.com/developer/article/1744139)
>
> Cardinal官方网站：[https://cardinal.ink/](https://cardinal.ink/)
>

# 平台简介
Cardinal是由 Vidar-Team开发的AWD 比赛平台，使用 Go 编写。Cardinal可以作为 CTF 线下比赛平台，亦可用于团队内部 AWD 模拟练习。

# 开始搭建
## 配置Cardinal
首先来到cardinal的github：[https://github.com/vidar-team/Cardinal](https://github.com/vidar-team/Cardinal)

当然你可以下载源码自己编译，这里直接选择使用已经release版本：

[https://github.com/vidar-team/Cardinal/releases/tag/v0.7.3](https://github.com/vidar-team/Cardinal/releases/tag/v0.7.3)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625739983237-1925304f-2b35-42fa-8ca9-0a48cbb3c45e.png)

由于我准备在kali上搭建环境，因此这里选“[Cardinal_v0.7.3_linux_amd64.tar.gz](https://github.com/vidar-team/Cardinal/releases/download/v0.7.3/Cardinal_v0.7.3_linux_amd64.tar.gz)”

> kali-vmware下载地址（下载解压即用）：[https://www.kali.org/get-kali/#kali-virtual-machines](https://www.kali.org/get-kali/#kali-virtual-machines)
>
> kali账号密码均为kali
>

打开kali虚拟机，由于awd的比赛都需要docker，所以先在kali中安装docker：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625742303690-3c971306-dfc4-496e-8086-d9bafd4cb352.png)

---

> 另外提一嘴，cardinal平台是有docker版本的，可以使用docker来搭建，这篇文章就不采用这种方式了
>

docker配置文件如下：

Dockerfile：

```dockerfile
FROM lsiobase/alpine:3.11
ARG Title
ARG Language
ARG BeginTime
ARG EndTime
ARG Duration
ARG Port
ARG FlagPrefix
ARG FlagSuffix
ARG CheckDownScore
ARG AttackScore
WORKDIR /Cardinal
ENV TZ="Asia/Shanghai"
ENV PUID=19999
ENV PGID=19999
COPY ./Cardinal /Cardinal
RUN chmod +x /Cardinal/Cardinal && \
    mkdir /Cardinal/conf && \
    echo -e "[base] #基础配置\n\
        SystemLanguage=\"${Language}\"\n\
        BeginTime=\"${BeginTime}\"\n\
        RestTime=[\n\
        # [\"2020-02-16T17:00:00+08:00\",\"2020-02-16T18:00:00+08:00\"],\n\
        ]\n\
        EndTime=\"${EndTime}\"\n\
        Duration=${Duration}\n\
        SeparateFrontend=false\n\
        Salt=\"$(cat /proc/sys/kernel/random/uuid)\"\n\
        Port=\":${Port}\"\n\
        CheckDownScore=${CheckDownScore}\n\
        AttackScore=${AttackScore}\n\
        \n\
        [mysql]\n\
        DBHost=\"db\"\n\
        DBUsername=\"root\"\n\
        DBPassword=\"Cardinal\"\n\
        DBName=\"Cardinal\"\
    " > /Cardinal/conf/Cardinal.toml
EXPOSE 19999
CMD ["/Cardinal/Cardinal"]
```

docker-compose文件如下：

```powershell
version: "3.8"
services:
  cardinal:
    build:
      context: ./
      args:
        - Language=zh-CN  #比赛语言 zh-CN/en-US 可选
        - BeginTime=2020-02-17T12:00:00-05:00 #比赛开始时间，参考该格式修改
        - EndTime=2020-02-18T12:00:00-05:00   #比赛结束时间，参考该格式修改
        - Duration=2    #每轮持续时间，单位分钟
        - Port=19999    #端口
        - CheckDownScore=50   #CheckDown扣分
        - AttackScore=50      #攻陷得分
    environment:
      CARDINAL_DOCKER: 1
    ports:
      - "19999:19999"       #端口映射，默认监听至19999
    logging:
      options:
        max-size: "200k"
        max-file: "10"
    restart: always
    depends_on:
      - db
  db:
    image: mysql:8.0.21
    volumes:
      - ./Cardinal_database:/var/lib/mysql
    logging:
      options:
        max-size: "200k"
        max-file: "10"
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: Cardinal
      MYSQL_DATABASE: Cardinal
      MYSQL_USER: Cardinal
      MYSQL_PASSWORD: Cardinal
    command: mysqld --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

配置文件按照自己的需求改，然后将这两个文件放在同一文件夹下sudo docker-compose up -d --build即可

---

言归正传，kali中也并没有自带有docker-compose，需要我们自己安装：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625743201487-2d66d857-66c7-423a-9b27-df899fb75df4.png)

安装完成之后下载并解压文章之前提到的Cardinal_v0.7.3_linux_amd64.tar.gz：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625744005186-4ed256ab-0d2d-441d-91e9-09062c446c95.png)

然后其中kali自带的mysql服务并创建cradinal数据库：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625744169963-17f59612-c399-4558-9a09-1a222ad36c19.png)

> mysql账号密码均为root
>

然后运行可执行文件Cardinal按照提示进行配置：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625744767444-92e4ee27-1baf-4b2e-a596-4587923e8816.png)

如上图所示，在运行Cardinal文件之前首先修改数据库密码，否则会报错：

```powershell
#使用root权限进入数据库进行修改：
set password for username @localhost = password(newpwd); #修改格式
set password for root @localhost = password('kali');
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625744918673-063cc66b-7174-41a9-bdcb-15ce5cdc500d.png)

重新运行文件即可进入：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625745128425-10eddc77-da0f-4af7-9711-a5fcae70b468.png)

> 上图的“请输入管理员账号”和“请输入管理员密码”的意思是让你输入你想要设置的管理员账号密码
>

配置完成之后即可访问

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625745515377-b7a53800-4bf6-4f80-80de-0bb685a08b16.png)

## 配置靶机
> 参看资料：[https://github.com/glzjin/20190511_awd_docker](https://github.com/glzjin/20190511_awd_docker)
>

所需要的文件如下：

### 修改Dockerfile文件
原文章Dockerfile：

```dockerfile
FROM phusion/baseimage

RUN sed -i "s/http:\/\/archive.ubuntu.com/http:\/\/mirrors.aliyun.com/g" /etc/apt/sources.list
RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get install -y lib32z1 xinetd build-essential

RUN rm -f /etc/service/sshd/down && /etc/my_init.d/00_regen_ssh_host_keys.sh > /dev/null 2>&1
RUN sed -ri 's/^#?PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config

RUN groupadd glzjin && \
    useradd -g glzjin glzjin -m && \
    password=$(openssl passwd -1 -salt 'abcdefg' '123456') && \
    sed -i 's/^glzjin:!/glzjin:'$password'/g' /etc/shadow

COPY ./flag.txt /flag.txt
COPY ./calculator /home/glzjin/calculator
COPY ./ctf.xinetd /etc/xinetd.d/ctf

RUN chown glzjin:glzjin /home/glzjin/calculator && chmod 777 /home/glzjin/calculator

RUN echo 'ctf - nproc 1500' >>/etc/security/limits.conf

CMD exec /bin/bash -c "/etc/init.d/ssh start; /etc/init.d/xinetd start; trap : TERM INT; sleep infinity & wait"

EXPOSE 8888
EXPOSE 22
```

为了方便之后的操作，我们将这个配置文件修改一下：

```dockerfile
#Dockerfile

#导入docker镜像phusion/baseimage
FROM phusion/baseimage:18.04-1.0.0

#修改docker中apt源为aliyun
RUN sed -i "s/http:\/\/archive.ubuntu.com/http:\/\/mirrors.aliyun.com/g" /etc/apt/sources.list

#执行命令"apt-get update"和"apt-get -y dist-upgrade"以更新源和升级包
RUN apt-get update && apt-get -y dist-upgrade

#安装32位程序所需要的依赖
RUN apt-get install -y lib32z1 xinetd build-essential

#删除文件
RUN rm -f /etc/service/sshd/down && /etc/my_init.d/00_regen_ssh_host_keys.sh > /dev/null 2>&1

#修改ssh配置文件以允许使用root权限登录
RUN sed -ri 's/^#?PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config

#创建新用户组ctf
RUN groupadd ctf && \
    #新建用户ctf，此用户所属的用户组为ctf
    #-m：自动建立用户的登入目录
    useradd -g ctf ctf -m && \
    #设置ssh登录密码为ctf
    #使用-salt参数可以防止rainbow table（彩虹表）攻击
    password=$(openssl passwd -1 -salt 'abcdefg' 'ctf') && \
    #设置ctf用户登录密码为ctf
    sed -i 's/^ctf:!/ctf:'$password'/g' /etc/shadow

#拷贝flag.txt到根目录，没什么用，有用的是之后的flag文件
COPY ./flag.txt /flag.txt
#拷贝pwn文件到home中
COPY ./pwn /home/ctf/pwn
#拷贝守护进程文件到linux的xinetd.d文件夹中
COPY ./ctf.xinetd /etc/xinetd.d/ctf
#赋予可执行文件用户组和读写权限
RUN chown ctf:ctf /home/ctf/pwn && chmod 777 /home/ctf/pwn

#限制ctf用户创建的进程数
RUN echo 'ctf - nproc 1500' >>/etc/security/limits.conf

#启动ssh服务；
#启动自定义的xinetd（守护进程）服务；
#使用trap捕获SIGTERM（终止信号）和SIGINT（中断信号）
#总结：保持镜像一直运行，保证容器不被停掉
CMD exec /bin/bash -c "/etc/init.d/ssh start; /etc/init.d/xinetd start; trap : TERM INT; sleep infinity & wait"

#向外暴露（映射）8888端口和22端口
#其中8888端口用来访问pwn题目，22端口用来访问ssh
EXPOSE 8888
EXPOSE 22
```

### 修改守护进程文件
原文件如下：

```plain
service ctf
{
    disable = no
    socket_type = stream
    protocol    = tcp
    wait        = no
    user        = root
    type        = UNLISTED
    port        = 8888
    bind        = 0.0.0.0
    server      = /usr/sbin/chroot
    server_args = --userspec=1000:1000 / timeout 50 /home/glzjin/calculator
    banner_fail = /etc/banner_fail

    # safety options
    per_source	  = 10 # the maximum instances of this service per source IP address
    rlimit_cpu	  = 60 # the maximum number of CPU seconds that the service may use
    rlimit_as     = 1024M # the Address Space resource limit for the service
    #access_times = 2:00-9:00 12:00-24:00

    #Instances   = 20 #process limit
    #per_source  = 5 #link ip limit

    #log warning die
    log_on_success  = PID HOST EXIT DURATION
    log_on_failure  = HOST ATTEMPT
    log_type =FILE /var/log/myservice.log 8388608 15728640

}
```

修改为：

```plain
service ctf
{
    #不禁用此服务
    disable = no

    #服务的数据包类型为stream
    socket_type = stream

    #链接使用的协议为tcp
    protocol    = tcp

    #为每个请求创建一个进程（多线程服务）
    wait        = no

    #运行此服务进程的用户为root
    user        = root

    #没有在标准系统文件如/etc/rpc或/etc/service中的服务为unlisted
    type        = UNLISTED
    
    #链接的端口为8888
    port        = 8888

    #将bind配置为0.0.0.0进行监听
    bind        = 0.0.0.0

    #启动的server为/usr/sbin/chroot
    server      = /usr/sbin/chroot

    #server的参数：以普通用户来访问pwn文件
    server_args = --userspec=1000:1000 / timeout 50 /home/ctf/pwn

    #当客户端链接失败时反馈给客户端的信息
    banner_fail = /etc/banner_fail

    # safety options
    #一些安全选项

    #per_source表示每一个IP地址上最多可以建立的实例数目
    per_source	  = 10 # the maximum instances of this service per source IP address

    #服务最多可占用的CPU秒数
    rlimit_cpu	  = 60 # the maximum number of CPU seconds that the service may use

    #限制服务对内存的占用
    rlimit_as     = 1024M # the Address Space resource limit for the service
    #access_times = 2:00-9:00 12:00-24:00 #允许访问的时间段

    #可同时运行的最大进程数
    #Instances   = 20 #process limit
    #per_source  = 5 #link ip limit

    #log warning die
    #登记链接成功时的信息：记录下PID 客户机ip地址 进程终止的状态 会话持续期
    log_on_success  = PID HOST EXIT DURATION

    #登记链接失败时的信息：客户机ip地址 失败的事实
    log_on_failure  = HOST ATTEMPT

    #设置的日志文件FILE的临界值为8MB，到达此值时，syslog文件会出现告警，到达15MB，系统会停止所有使用这个日志系统的服务。
    log_type =FILE /var/log/myservice.log 8388608 15728640

}
```

### 修改docker-compose.yml文件
```yaml
version: "3"
services:
    
    pwn1:
        build: ./pwn1 #注意目录要对应
        ports: #端口号注意要和Dockerfile和ctf.xinetd对应
            - "18888:8888" #向外映射的pwn端口
            - "18889:22"   #向外映射的ssh端口
        restart:
                always
    #pwn2:
    #    build: ./pwn2 
    #    ports:
    #        - "18890:80"
    #        - "18891:22"
```

### 拉取镜像
接下来我们将修改后的文件这样摆放（将这些文件放在任意目录下，这里我将文件夹命名为：docker-pwn）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625808419233-654abed2-0f9f-46e4-b521-379ab91359bf.png)

然后切换到docker-pwn目录下，执行sudo docker-compose up -d --build，耐心等待，执行结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625808540425-6434b7c7-6b48-4e0f-ada1-f733c80c0fe5.png)

### 测试
nc 虚拟机ip 18888看一下是否可以正常连接到题目：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625810844564-0a0561ba-3730-4bc9-bbab-e22bdf2ac3ba.png)

测试ssh是否可以正常登入：

普通用户ctf（密码：ctf）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625812101174-12bd0649-ec3f-472b-96ed-593f1b6c3515.png)

为了以root身份登入ssh，我们需要先在docker中设置一下密码即可正常登入：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625812148985-24e3ae9d-6843-4582-9e60-c48759761fca.png)

> 如果想要配置多个pwn靶机可以重复上面的步骤并配置docker-compose.yml即可，注意不要让端口号冲突
>

## 联动靶机和Cardinal
运行Cardinal，访问虚拟机ip+端口号19999（记得启动mysql服务）并输入账号密码以登入后台：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625811168934-2b890e2d-4cd6-4e43-b4a0-1b4e24dd0fac.png)

登入后首先访问“题目管理”界面：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625812343401-15097cf2-f56b-408b-9851-7bab17a5578d.png)

点击“添加新的Challenge”：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625812395464-6c54d009-8907-42ef-a2e0-0eccb764ad2a.png)

添加完成之后点击“队伍管理”添加新队伍：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625812548774-ee85735f-4126-4958-81e4-bc4168897b5f.png)

记得保存好密码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625812602335-38e23d54-1800-4d31-95f9-cc382ee41f78.png)

之后点击“添加新靶机”

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625811506092-7a9ad443-8068-4d7c-974b-84a19fea2b9c.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625812807856-3616ebb8-202c-4a57-80db-2c52c1298133.png)

注意，这里添加的一定要是root的ssh，否则无法更新flag。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625812856020-445de3c9-437b-414c-bbd3-7b5ca27ab09a.png)

然后我们到“flag管理”生成flag：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625812960060-646f241c-79e3-4179-97e3-07d375db745c.png)

awd的flag都是动态的，除非getshell，否则选手是不可能提前知道flag的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625813075261-b82500f9-2494-41a6-bd5d-b387a96c058d.png)

最后我们到“靶机管理”处点击“更新所有flag”就会在目录下生成flag文件

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625813114664-d9931e44-bc45-4561-a0ff-408eb51ffed8.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625813185211-4a8df367-40e1-4520-88a7-1b94ac7399c5.png)

### 测试
用户端：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625813691630-e756abdb-c2d0-4c51-8496-6bd8b9dba555.png)

另外想要开放题目时可以再设置一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625813755702-ddafb9af-fdb4-432d-b33b-53b1539b2405.png)

也可以设置队伍靶机相互可见：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625813850499-1817c71d-4805-4c0c-9871-21490fd085b2.png)

最终效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625813819047-aa392087-d640-4304-b24a-89611d9baa21.png)

现在越来越多的AWD比赛不给root而给普通的ctf权限，至于具体给什么权限自己是情况而定。

# 写在最后
当然这个平台还可以连接大屏以实现攻击时酷炫的效果，这里就不多说了，感兴趣的话可以参见：

[https://cardinal.ink/asteroid/](https://cardinal.ink/asteroid/)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1625813549647-15c1349f-af49-419d-80e7-4bff6606afaf.png)











