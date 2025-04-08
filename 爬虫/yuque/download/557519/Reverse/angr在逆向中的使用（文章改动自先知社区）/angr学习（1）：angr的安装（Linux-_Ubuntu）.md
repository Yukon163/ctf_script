**<font style="color:#F5222D;">总结：这玩意儿真难安装。。。(有可能需要挂飞机，反正我挂了）</font>**

针对python版本：python3（python 3.8.2）

材料：**全新**的ubuntu 20.04（全程联网安装）

文件名称：ubuntu-20.04-desktop-amd64.iso

镜像下载地址：[http://releases.ubuntu.com/20.04/ubuntu-20.04-desktop-amd64.iso](http://releases.ubuntu.com/20.04/ubuntu-20.04-desktop-amd64.iso)

链接：[https://pan.baidu.com/s/1S178E9AUo_HlKdaa-k04nw](https://pan.baidu.com/s/1S178E9AUo_HlKdaa-k04nw)

提取码：diyc

复制这段内容后打开百度网盘手机App，操作更方便哦

说明： python virtual enviroment是一个python环境管理工具，该工具能够在真实的系统中创建一个虚拟的python环境，以防止软件安装过程中对真实环境的影响，同时也能方便解决python中不同版本不兼容的问题。具体请到百度搜索virtualenvwrapper和virtualenv，其中virtualenvwrapper是对virtualenv的封装。在angr中使用的是virtualenvwrapper。由于angr的库修改自python库，因此直接安装angr会**破坏**原来的库文件，so，不推荐直接安装。

参考资料：[https://blog.csdn.net/z2664836046/article/details/97683626](https://blog.csdn.net/z2664836046/article/details/97683626)

> **<font style="color:#F5222D;">命令语句解读如下（文章内容如下）：</font>**
>
> 1.安装依赖（基本开发环境）：
>
> sudo apt-get install python-dev libffi-dev build-essential virtualenvwrapper
>
> 2.virtualenvwrapper初始化：
>
> 首先设置一个环境变量WORKON_HOME
>
> export WORKON_HOME=$HOME/Python-workhome
>
> 这里的$HOME/Python-workhome就是准备放置虚拟环境的地址
>
> 启动virtualenvwrapper.sh脚本
>
> source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
>
> 注意：可以使用whereis virtualenvwrapper.sh命令查看脚本的位置
>
> 3.在python3的环境下安装angr：
>
> mkvirtualenv --python=$(which python3) angr && pip install angr
>
> 4.安装好后在其他的命令在一个新的终端窗口直接运行workon，并没有创建的angr虚拟环境，需要执行下面两条命令才可以：
>
> export WORKON_HOME=$HOME/Python-workhome
>
> source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
>
> 可以写一个shell脚本包含两条命令，以后直接运行shell脚本即可。
>



> virtualenvwrapper操作命令：
>
> 创建环境
>
> mkvirtualenv env1  
>
> 环境创建之后，会自动进入该目录，并激活该环境。
>
> 切换或进入环境
>
> workon env1
>
> 列出已有环境
>
> workon
>
> 退出环境
>
> deactivate
>
> 删除环境
>
> rmvirtualenv
>



> CFG可视化：angr-utils能够实现CFG（以及其他流图）的可视化，安装过程：
>
> workon angr
>
> git clone [https://github.com/axt/bingraphvis](https://github.com/axt/bingraphvis)
>
> pip install -e ./bingraphvis
>
> git clone [https://github.com/axt/angr-utils](https://github.com/axt/angr-utils)
>
> pip install -e ./angr-utils
>





日志信息如下：

接下来的命令一条一条执行，首先我们先看一下ubuntu自带的python版本：

```bash
ubuntu@ubuntu:~/Desktop$ python
Command 'python' not found, did you mean:
 command 'python3' from deb python3
 command 'python' from deb python-is-python3
```

Ubuntu竟然没有自带python，接着执行命令：

```bash
ubuntu@ubuntu:~/Desktop$ sudo apt-get install python-dev libffi-dev build-essential virtualenvwrapper
[sudo] password for ubuntu:  
Reading package lists... Done
Building dependency tree        
Reading state information... Done
Note, selecting 'python-dev-is-python2' instead of 'python-dev'
The following additional packages will be installed:
 binutils binutils-common binutils-x86-64-linux-gnu dpkg-dev fakeroot g++
 g++-9 gcc gcc-9 libalgorithm-diff-perl libalgorithm-diff-xs-perl
 libalgorithm-merge-perl libasan5 libatomic1 libbinutils libc-dev-bin
 libc6-dev libcrypt-dev libctf-nobfd0 libctf0 libexpat1-dev libfakeroot
 libgcc-9-dev libitm1 liblsan0 libpython2-dev libpython2-stdlib libpython2.7
 libpython2.7-dev libpython2.7-minimal libpython2.7-stdlib libquadmath0
 libstdc++-9-dev libtsan0 libubsan1 linux-libc-dev make manpages-dev
 python-is-python2 python-pip-whl python2 python2-dev python2-minimal
 python2.7 python2.7-dev python2.7-minimal python3-appdirs python3-distlib
 python3-distutils python3-filelock python3-importlib-metadata
 python3-more-itertools python3-pbr python3-setuptools python3-stevedore
 python3-virtualenv python3-virtualenv-clone python3-virtualenvwrapper
 python3-zipp virtualenv
Suggested packages:
 binutils-doc debian-keyring g++-multilib g++-9-multilib gcc-9-doc
 gcc-multilib autoconf automake libtool flex bison gcc-doc gcc-9-multilib
 gcc-9-locales glibc-doc libstdc++-9-doc make-doc python2-doc python-tk
 python2.7-doc binfmt-support python-setuptools-doc virtualenvwrapper-doc
The following NEW packages will be installed:
 binutils binutils-common binutils-x86-64-linux-gnu build-essential dpkg-dev
 fakeroot g++ g++-9 gcc gcc-9 libalgorithm-diff-perl
 libalgorithm-diff-xs-perl libalgorithm-merge-perl libasan5 libatomic1
 libbinutils libc-dev-bin libc6-dev libcrypt-dev libctf-nobfd0 libctf0
 libexpat1-dev libfakeroot libffi-dev libgcc-9-dev libitm1 liblsan0
 libpython2-dev libpython2-stdlib libpython2.7 libpython2.7-dev
 libpython2.7-minimal libpython2.7-stdlib libquadmath0 libstdc++-9-dev
 libtsan0 libubsan1 linux-libc-dev make manpages-dev python-dev-is-python2
 python-is-python2 python-pip-whl python2 python2-dev python2-minimal
 python2.7 python2.7-dev python2.7-minimal python3-appdirs python3-distlib
 python3-distutils python3-filelock python3-importlib-metadata
 python3-more-itertools python3-pbr python3-setuptools python3-stevedore
 python3-virtualenv python3-virtualenv-clone python3-virtualenvwrapper
 python3-zipp virtualenv virtualenvwrapper
0 upgraded, 64 newly installed, 0 to remove and 78 not upgraded.
Need to get 41.8 MB of archives.
After this operation, 185 MB of additional disk space will be used.
Do you want to continue? [Y/n] Y
Get:1 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 libpython2.7-minimal amd64 2.7.18~rc1-2 [335 kB]
Get:2 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python2.7-minimal amd64 2.7.18~rc1-2 [1,302 kB]                                                                                            
Get:3 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python2-minimal amd64 2.7.17-2ubuntu4 [27.5 kB]                                                                                            
Get:4 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 libpython2.7-stdlib amd64 2.7.18~rc1-2 [1,880 kB]                                                                                          
Get:5 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python2.7 amd64 2.7.18~rc1-2 [248 kB]                                                                                                      
Get:6 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 libpython2-stdlib amd64 2.7.17-2ubuntu4 [7,072 B]                                                                                          
Get:7 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python2 amd64 2.7.17-2ubuntu4 [26.5 kB]                                                                                                    
Get:8 http://us.archive.ubuntu.com/ubuntu focal/main amd64 binutils-common amd64 2.34-6ubuntu1 [207 kB]                                                                                                    
Get:9 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libbinutils amd64 2.34-6ubuntu1 [474 kB]                                                                                                        
Get:10 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libctf-nobfd0 amd64 2.34-6ubuntu1 [47.0 kB]                                                                                                    
Get:11 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libctf0 amd64 2.34-6ubuntu1 [46.6 kB]                                                                                                          
Get:12 http://us.archive.ubuntu.com/ubuntu focal/main amd64 binutils-x86-64-linux-gnu amd64 2.34-6ubuntu1 [1,614 kB]                                                                                      
Get:13 http://us.archive.ubuntu.com/ubuntu focal/main amd64 binutils amd64 2.34-6ubuntu1 [3,376 B]                                                                                                        
Get:14 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libc-dev-bin amd64 2.31-0ubuntu9 [71.8 kB]                                                                                                    
Get:15 http://us.archive.ubuntu.com/ubuntu focal-updates/main amd64 linux-libc-dev amd64 5.4.0-29.33 [1,098 kB]                                                                                            
Get:16 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libcrypt-dev amd64 1:4.4.10-10ubuntu4 [104 kB]                                                                                                
Get:17 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libc6-dev amd64 2.31-0ubuntu9 [2,520 kB]                                                                                                      
Get:18 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libitm1 amd64 10-20200411-0ubuntu1 [26.3 kB]                                                                                                  
Get:19 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libatomic1 amd64 10-20200411-0ubuntu1 [9,284 B]                                                                                                
Get:20 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libasan5 amd64 9.3.0-10ubuntu2 [395 kB]                                                                                                        
Get:21 http://us.archive.ubuntu.com/ubuntu focal/main amd64 liblsan0 amd64 10-20200411-0ubuntu1 [144 kB]                                                                                                  
Get:22 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libtsan0 amd64 10-20200411-0ubuntu1 [319 kB]                                                                                                  
Get:23 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libubsan1 amd64 10-20200411-0ubuntu1 [136 kB]                                                                                                  
Get:24 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libquadmath0 amd64 10-20200411-0ubuntu1 [146 kB]                                                                                              
Get:25 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libgcc-9-dev amd64 9.3.0-10ubuntu2 [2,359 kB]                                                                                                  
Get:26 http://us.archive.ubuntu.com/ubuntu focal/main amd64 gcc-9 amd64 9.3.0-10ubuntu2 [8,234 kB]                                                                                                        
Get:27 http://us.archive.ubuntu.com/ubuntu focal/main amd64 gcc amd64 4:9.3.0-1ubuntu2 [5,208 B]                                                                                                          
Get:28 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libstdc++-9-dev amd64 9.3.0-10ubuntu2 [1,711 kB]                                                                                              
Get:29 http://us.archive.ubuntu.com/ubuntu focal/main amd64 g++-9 amd64 9.3.0-10ubuntu2 [8,404 kB]                                                                                                        
Get:30 http://us.archive.ubuntu.com/ubuntu focal/main amd64 g++ amd64 4:9.3.0-1ubuntu2 [1,604 B]                                                                                                          
Get:31 http://us.archive.ubuntu.com/ubuntu focal/main amd64 make amd64 4.2.1-1.2 [162 kB]                                                                                                                  
Get:32 http://us.archive.ubuntu.com/ubuntu focal/main amd64 dpkg-dev all 1.19.7ubuntu3 [679 kB]                                                                                                            
Get:33 http://us.archive.ubuntu.com/ubuntu focal/main amd64 build-essential amd64 12.8ubuntu1 [4,624 B]                                                                                                    
Get:34 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libfakeroot amd64 1.24-1 [25.7 kB]                                                                                                            
Get:35 http://us.archive.ubuntu.com/ubuntu focal/main amd64 fakeroot amd64 1.24-1 [62.6 kB]                                                                                                                
Get:36 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libalgorithm-diff-perl all 1.19.03-2 [46.6 kB]                                                                                                
Get:37 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libalgorithm-diff-xs-perl amd64 0.04-6 [11.3 kB]                                                                                              
Get:38 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libalgorithm-merge-perl all 0.08-3 [12.0 kB]                                                                                                  
Get:39 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libexpat1-dev amd64 2.2.9-1build1 [116 kB]                                                                                                    
Get:40 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 libpython2.7 amd64 2.7.18~rc1-2 [1,036 kB]                                                                                                
Get:41 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 libpython2.7-dev amd64 2.7.18~rc1-2 [2,473 kB]                                                                                            
Get:42 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 libpython2-dev amd64 2.7.17-2ubuntu4 [7,140 B]                                                                                            
Get:43 http://us.archive.ubuntu.com/ubuntu focal/main amd64 manpages-dev all 5.05-1 [2,266 kB]                                                                                                            
Get:44 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python-is-python2 all 2.7.17-4 [2,496 B]                                                                                                  
Get:45 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python2.7-dev amd64 2.7.18~rc1-2 [287 kB]                                                                                                  
Get:46 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python2-dev amd64 2.7.17-2ubuntu4 [1,268 B]                                                                                                
Get:47 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python-dev-is-python2 all 2.7.17-4 [1,396 B]                                                                                              
Get:48 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python-pip-whl all 20.0.2-5ubuntu1 [1,799 kB]                                                                                              
Get:49 http://us.archive.ubuntu.com/ubuntu focal/main amd64 python3-appdirs all 1.4.3-2.1 [10.8 kB]                                                                                                        
Get:50 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python3-distlib all 0.3.0-1 [116 kB]                                                                                                      
Get:51 http://us.archive.ubuntu.com/ubuntu focal/main amd64 python3-distutils all 3.8.2-1ubuntu1 [140 kB]                                                                                                  
Get:52 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python3-filelock all 3.0.12-2 [7,948 B]                                                                                                    
Get:53 http://us.archive.ubuntu.com/ubuntu focal/main amd64 python3-more-itertools all 4.2.0-1build1 [39.4 kB]                                                                                            
Get:54 http://us.archive.ubuntu.com/ubuntu focal/main amd64 python3-zipp all 1.0.0-1 [5,312 B]                                                                                                            
Get:55 http://us.archive.ubuntu.com/ubuntu focal/main amd64 python3-importlib-metadata all 1.5.0-1 [9,992 B]                                                                                              
Get:56 http://us.archive.ubuntu.com/ubuntu focal/main amd64 python3-setuptools all 45.2.0-1 [330 kB]                                                                                                      
Get:57 http://us.archive.ubuntu.com/ubuntu focal/main amd64 python3-pbr all 5.4.5-0ubuntu1 [64.0 kB]                                                                                                      
Get:58 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python3-virtualenv all 20.0.17-1 [63.4 kB]                                                                                                
Get:59 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python3-virtualenv-clone all 0.3.0-2 [8,696 B]                                                                                            
Get:60 http://us.archive.ubuntu.com/ubuntu focal/main amd64 python3-stevedore all 1:1.32.0-0ubuntu2 [18.4 kB]                                                                                              
Get:61 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python3-virtualenvwrapper all 4.8.4-4 [13.0 kB]                                                                                            
Get:62 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 virtualenv all 20.0.17-1 [2,132 B]                                                                                                        
Get:63 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 virtualenvwrapper all 4.8.4-4 [19.4 kB]                                                                                                    
Get:64 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libffi-dev amd64 3.3-4 [57.0 kB]                                                                                                              
Fetched 41.8 MB in 14min 42s (47.4 kB/s)                                                                                                                                                                  
Extracting templates from packages: 100%
Selecting previously unselected package libpython2.7-minimal:amd64.
(Reading database ... 178979 files and directories currently installed.)
Preparing to unpack .../0-libpython2.7-minimal_2.7.18~rc1-2_amd64.deb ...
Unpacking libpython2.7-minimal:amd64 (2.7.18~rc1-2) ...
Selecting previously unselected package python2.7-minimal.
Preparing to unpack .../1-python2.7-minimal_2.7.18~rc1-2_amd64.deb ...
Unpacking python2.7-minimal (2.7.18~rc1-2) ...
Selecting previously unselected package python2-minimal.
Preparing to unpack .../2-python2-minimal_2.7.17-2ubuntu4_amd64.deb ...
Unpacking python2-minimal (2.7.17-2ubuntu4) ...
Selecting previously unselected package libpython2.7-stdlib:amd64.
Preparing to unpack .../3-libpython2.7-stdlib_2.7.18~rc1-2_amd64.deb ...
Unpacking libpython2.7-stdlib:amd64 (2.7.18~rc1-2) ...
Selecting previously unselected package python2.7.
Preparing to unpack .../4-python2.7_2.7.18~rc1-2_amd64.deb ...
Unpacking python2.7 (2.7.18~rc1-2) ...
Selecting previously unselected package libpython2-stdlib:amd64.
Preparing to unpack .../5-libpython2-stdlib_2.7.17-2ubuntu4_amd64.deb ...
Unpacking libpython2-stdlib:amd64 (2.7.17-2ubuntu4) ...
Setting up libpython2.7-minimal:amd64 (2.7.18~rc1-2) ...
Setting up python2.7-minimal (2.7.18~rc1-2) ...
Linking and byte-compiling packages for runtime python2.7...
Setting up python2-minimal (2.7.17-2ubuntu4) ...
Selecting previously unselected package python2.
(Reading database ... 179726 files and directories currently installed.)
Preparing to unpack .../00-python2_2.7.17-2ubuntu4_amd64.deb ...
Unpacking python2 (2.7.17-2ubuntu4) ...
Selecting previously unselected package binutils-common:amd64.
Preparing to unpack .../01-binutils-common_2.34-6ubuntu1_amd64.deb ...
Unpacking binutils-common:amd64 (2.34-6ubuntu1) ...
Selecting previously unselected package libbinutils:amd64.
Preparing to unpack .../02-libbinutils_2.34-6ubuntu1_amd64.deb ...
Unpacking libbinutils:amd64 (2.34-6ubuntu1) ...
Selecting previously unselected package libctf-nobfd0:amd64.
Preparing to unpack .../03-libctf-nobfd0_2.34-6ubuntu1_amd64.deb ...
Unpacking libctf-nobfd0:amd64 (2.34-6ubuntu1) ...
Selecting previously unselected package libctf0:amd64.
Preparing to unpack .../04-libctf0_2.34-6ubuntu1_amd64.deb ...
Unpacking libctf0:amd64 (2.34-6ubuntu1) ...
Selecting previously unselected package binutils-x86-64-linux-gnu.
Preparing to unpack .../05-binutils-x86-64-linux-gnu_2.34-6ubuntu1_amd64.deb ...
Unpacking binutils-x86-64-linux-gnu (2.34-6ubuntu1) ...
Selecting previously unselected package binutils.
Preparing to unpack .../06-binutils_2.34-6ubuntu1_amd64.deb ...
Unpacking binutils (2.34-6ubuntu1) ...
Selecting previously unselected package libc-dev-bin.
Preparing to unpack .../07-libc-dev-bin_2.31-0ubuntu9_amd64.deb ...
Unpacking libc-dev-bin (2.31-0ubuntu9) ...
Selecting previously unselected package linux-libc-dev:amd64.
Preparing to unpack .../08-linux-libc-dev_5.4.0-29.33_amd64.deb ...
Unpacking linux-libc-dev:amd64 (5.4.0-29.33) ...
Selecting previously unselected package libcrypt-dev:amd64.
Preparing to unpack .../09-libcrypt-dev_1%3a4.4.10-10ubuntu4_amd64.deb ...
Unpacking libcrypt-dev:amd64 (1:4.4.10-10ubuntu4) ...
Selecting previously unselected package libc6-dev:amd64.
Preparing to unpack .../10-libc6-dev_2.31-0ubuntu9_amd64.deb ...
Unpacking libc6-dev:amd64 (2.31-0ubuntu9) ...
Selecting previously unselected package libitm1:amd64.
Preparing to unpack .../11-libitm1_10-20200411-0ubuntu1_amd64.deb ...
Unpacking libitm1:amd64 (10-20200411-0ubuntu1) ...
Selecting previously unselected package libatomic1:amd64.
Preparing to unpack .../12-libatomic1_10-20200411-0ubuntu1_amd64.deb ...
Unpacking libatomic1:amd64 (10-20200411-0ubuntu1) ...
Selecting previously unselected package libasan5:amd64.
Preparing to unpack .../13-libasan5_9.3.0-10ubuntu2_amd64.deb ...
Unpacking libasan5:amd64 (9.3.0-10ubuntu2) ...
Selecting previously unselected package liblsan0:amd64.
Preparing to unpack .../14-liblsan0_10-20200411-0ubuntu1_amd64.deb ...
Unpacking liblsan0:amd64 (10-20200411-0ubuntu1) ...
Selecting previously unselected package libtsan0:amd64.
Preparing to unpack .../15-libtsan0_10-20200411-0ubuntu1_amd64.deb ...
Unpacking libtsan0:amd64 (10-20200411-0ubuntu1) ...
Selecting previously unselected package libubsan1:amd64.
Preparing to unpack .../16-libubsan1_10-20200411-0ubuntu1_amd64.deb ...
Unpacking libubsan1:amd64 (10-20200411-0ubuntu1) ...
Selecting previously unselected package libquadmath0:amd64.
Preparing to unpack .../17-libquadmath0_10-20200411-0ubuntu1_amd64.deb ...
Unpacking libquadmath0:amd64 (10-20200411-0ubuntu1) ...
Selecting previously unselected package libgcc-9-dev:amd64.
Preparing to unpack .../18-libgcc-9-dev_9.3.0-10ubuntu2_amd64.deb ...
Unpacking libgcc-9-dev:amd64 (9.3.0-10ubuntu2) ...
Selecting previously unselected package gcc-9.
Preparing to unpack .../19-gcc-9_9.3.0-10ubuntu2_amd64.deb ...
Unpacking gcc-9 (9.3.0-10ubuntu2) ...
Selecting previously unselected package gcc.
Preparing to unpack .../20-gcc_4%3a9.3.0-1ubuntu2_amd64.deb ...
Unpacking gcc (4:9.3.0-1ubuntu2) ...
Selecting previously unselected package libstdc++-9-dev:amd64.
Preparing to unpack .../21-libstdc++-9-dev_9.3.0-10ubuntu2_amd64.deb ...
Unpacking libstdc++-9-dev:amd64 (9.3.0-10ubuntu2) ...
Selecting previously unselected package g++-9.
Preparing to unpack .../22-g++-9_9.3.0-10ubuntu2_amd64.deb ...
Unpacking g++-9 (9.3.0-10ubuntu2) ...
Selecting previously unselected package g++.
Preparing to unpack .../23-g++_4%3a9.3.0-1ubuntu2_amd64.deb ...
Unpacking g++ (4:9.3.0-1ubuntu2) ...
Selecting previously unselected package make.
Preparing to unpack .../24-make_4.2.1-1.2_amd64.deb ...
Unpacking make (4.2.1-1.2) ...
Selecting previously unselected package dpkg-dev.
Preparing to unpack .../25-dpkg-dev_1.19.7ubuntu3_all.deb ...
Unpacking dpkg-dev (1.19.7ubuntu3) ...
Selecting previously unselected package build-essential.
Preparing to unpack .../26-build-essential_12.8ubuntu1_amd64.deb ...
Unpacking build-essential (12.8ubuntu1) ...
Selecting previously unselected package libfakeroot:amd64.
Preparing to unpack .../27-libfakeroot_1.24-1_amd64.deb ...
Unpacking libfakeroot:amd64 (1.24-1) ...
Selecting previously unselected package fakeroot.
Preparing to unpack .../28-fakeroot_1.24-1_amd64.deb ...
Unpacking fakeroot (1.24-1) ...
Selecting previously unselected package libalgorithm-diff-perl.
Preparing to unpack .../29-libalgorithm-diff-perl_1.19.03-2_all.deb ...
Unpacking libalgorithm-diff-perl (1.19.03-2) ...
Selecting previously unselected package libalgorithm-diff-xs-perl.
Preparing to unpack .../30-libalgorithm-diff-xs-perl_0.04-6_amd64.deb ...
Unpacking libalgorithm-diff-xs-perl (0.04-6) ...
Selecting previously unselected package libalgorithm-merge-perl.
Preparing to unpack .../31-libalgorithm-merge-perl_0.08-3_all.deb ...
Unpacking libalgorithm-merge-perl (0.08-3) ...
Selecting previously unselected package libexpat1-dev:amd64.
Preparing to unpack .../32-libexpat1-dev_2.2.9-1build1_amd64.deb ...
Unpacking libexpat1-dev:amd64 (2.2.9-1build1) ...
Selecting previously unselected package libpython2.7:amd64.
Preparing to unpack .../33-libpython2.7_2.7.18~rc1-2_amd64.deb ...
Unpacking libpython2.7:amd64 (2.7.18~rc1-2) ...
Selecting previously unselected package libpython2.7-dev:amd64.
Preparing to unpack .../34-libpython2.7-dev_2.7.18~rc1-2_amd64.deb ...
Unpacking libpython2.7-dev:amd64 (2.7.18~rc1-2) ...
Selecting previously unselected package libpython2-dev:amd64.
Preparing to unpack .../35-libpython2-dev_2.7.17-2ubuntu4_amd64.deb ...
Unpacking libpython2-dev:amd64 (2.7.17-2ubuntu4) ...
Selecting previously unselected package manpages-dev.
Preparing to unpack .../36-manpages-dev_5.05-1_all.deb ...
Unpacking manpages-dev (5.05-1) ...
Selecting previously unselected package python-is-python2.
Preparing to unpack .../37-python-is-python2_2.7.17-4_all.deb ...
Unpacking python-is-python2 (2.7.17-4) ...
Selecting previously unselected package python2.7-dev.
Preparing to unpack .../38-python2.7-dev_2.7.18~rc1-2_amd64.deb ...
Unpacking python2.7-dev (2.7.18~rc1-2) ...
Selecting previously unselected package python2-dev.
Preparing to unpack .../39-python2-dev_2.7.17-2ubuntu4_amd64.deb ...
Unpacking python2-dev (2.7.17-2ubuntu4) ...
Selecting previously unselected package python-dev-is-python2.
Preparing to unpack .../40-python-dev-is-python2_2.7.17-4_all.deb ...
Unpacking python-dev-is-python2 (2.7.17-4) ...
Selecting previously unselected package python-pip-whl.
Preparing to unpack .../41-python-pip-whl_20.0.2-5ubuntu1_all.deb ...
Unpacking python-pip-whl (20.0.2-5ubuntu1) ...
Selecting previously unselected package python3-appdirs.
Preparing to unpack .../42-python3-appdirs_1.4.3-2.1_all.deb ...
Unpacking python3-appdirs (1.4.3-2.1) ...
Selecting previously unselected package python3-distlib.
Preparing to unpack .../43-python3-distlib_0.3.0-1_all.deb ...
Unpacking python3-distlib (0.3.0-1) ...
Selecting previously unselected package python3-distutils.
Preparing to unpack .../44-python3-distutils_3.8.2-1ubuntu1_all.deb ...
Unpacking python3-distutils (3.8.2-1ubuntu1) ...
Selecting previously unselected package python3-filelock.
Preparing to unpack .../45-python3-filelock_3.0.12-2_all.deb ...
Unpacking python3-filelock (3.0.12-2) ...
Selecting previously unselected package python3-more-itertools.
Preparing to unpack .../46-python3-more-itertools_4.2.0-1build1_all.deb ...
Unpacking python3-more-itertools (4.2.0-1build1) ...
Selecting previously unselected package python3-zipp.
Preparing to unpack .../47-python3-zipp_1.0.0-1_all.deb ...
Unpacking python3-zipp (1.0.0-1) ...
Selecting previously unselected package python3-importlib-metadata.
Preparing to unpack .../48-python3-importlib-metadata_1.5.0-1_all.deb ...
Unpacking python3-importlib-metadata (1.5.0-1) ...
Selecting previously unselected package python3-setuptools.
Preparing to unpack .../49-python3-setuptools_45.2.0-1_all.deb ...
Unpacking python3-setuptools (45.2.0-1) ...
Selecting previously unselected package python3-pbr.
Preparing to unpack .../50-python3-pbr_5.4.5-0ubuntu1_all.deb ...
Unpacking python3-pbr (5.4.5-0ubuntu1) ...
Selecting previously unselected package python3-virtualenv.
Preparing to unpack .../51-python3-virtualenv_20.0.17-1_all.deb ...
Unpacking python3-virtualenv (20.0.17-1) ...
Selecting previously unselected package python3-virtualenv-clone.
Preparing to unpack .../52-python3-virtualenv-clone_0.3.0-2_all.deb ...
Unpacking python3-virtualenv-clone (0.3.0-2) ...
Selecting previously unselected package python3-stevedore.
Preparing to unpack .../53-python3-stevedore_1%3a1.32.0-0ubuntu2_all.deb ...
Unpacking python3-stevedore (1:1.32.0-0ubuntu2) ...
Selecting previously unselected package python3-virtualenvwrapper.
Preparing to unpack .../54-python3-virtualenvwrapper_4.8.4-4_all.deb ...
Unpacking python3-virtualenvwrapper (4.8.4-4) ...
Selecting previously unselected package virtualenv.
Preparing to unpack .../55-virtualenv_20.0.17-1_all.deb ...
Unpacking virtualenv (20.0.17-1) ...
Selecting previously unselected package virtualenvwrapper.
Preparing to unpack .../56-virtualenvwrapper_4.8.4-4_all.deb ...
Unpacking virtualenvwrapper (4.8.4-4) ...
Selecting previously unselected package libffi-dev:amd64.
Preparing to unpack .../57-libffi-dev_3.3-4_amd64.deb ...
Unpacking libffi-dev:amd64 (3.3-4) ...
Setting up python3-distutils (3.8.2-1ubuntu1) ...
Setting up python3-more-itertools (4.2.0-1build1) ...
Setting up manpages-dev (5.05-1) ...
Setting up python3-filelock (3.0.12-2) ...
Setting up python3-setuptools (45.2.0-1) ...
Setting up python3-pbr (5.4.5-0ubuntu1) ...
update-alternatives: using /usr/bin/python3-pbr to provide /usr/bin/pbr (pbr) in auto mode
Setting up libalgorithm-diff-perl (1.19.03-2) ...
Setting up binutils-common:amd64 (2.34-6ubuntu1) ...
Setting up linux-libc-dev:amd64 (5.4.0-29.33) ...
Setting up libctf-nobfd0:amd64 (2.34-6ubuntu1) ...
Setting up python3-virtualenv-clone (0.3.0-2) ...
Setting up python3-distlib (0.3.0-1) ...
Setting up python3-zipp (1.0.0-1) ...
Setting up libffi-dev:amd64 (3.3-4) ...
Setting up libfakeroot:amd64 (1.24-1) ...
Setting up libpython2.7-stdlib:amd64 (2.7.18~rc1-2) ...
Setting up fakeroot (1.24-1) ...
update-alternatives: using /usr/bin/fakeroot-sysv to provide /usr/bin/fakeroot (fakeroot) in auto mode
Setting up libasan5:amd64 (9.3.0-10ubuntu2) ...
Setting up make (4.2.1-1.2) ...
Setting up libquadmath0:amd64 (10-20200411-0ubuntu1) ...
Setting up libatomic1:amd64 (10-20200411-0ubuntu1) ...
Setting up libubsan1:amd64 (10-20200411-0ubuntu1) ...
Setting up libcrypt-dev:amd64 (1:4.4.10-10ubuntu4) ...
Setting up python3-stevedore (1:1.32.0-0ubuntu2) ...
Setting up python-pip-whl (20.0.2-5ubuntu1) ...
Setting up libbinutils:amd64 (2.34-6ubuntu1) ...
Setting up libc-dev-bin (2.31-0ubuntu9) ...
Setting up python3-appdirs (1.4.3-2.1) ...
Setting up libalgorithm-diff-xs-perl (0.04-6) ...
Setting up liblsan0:amd64 (10-20200411-0ubuntu1) ...
Setting up libitm1:amd64 (10-20200411-0ubuntu1) ...
Setting up libalgorithm-merge-perl (0.08-3) ...
Setting up libtsan0:amd64 (10-20200411-0ubuntu1) ...
Setting up libctf0:amd64 (2.34-6ubuntu1) ...
Setting up libpython2.7:amd64 (2.7.18~rc1-2) ...
Setting up python3-importlib-metadata (1.5.0-1) ...
Setting up python2.7 (2.7.18~rc1-2) ...
Setting up libpython2-stdlib:amd64 (2.7.17-2ubuntu4) ...
Setting up python3-virtualenv (20.0.17-1) ...
Setting up python2 (2.7.17-2ubuntu4) ...
Setting up libgcc-9-dev:amd64 (9.3.0-10ubuntu2) ...
Setting up virtualenv (20.0.17-1) ...
Setting up libc6-dev:amd64 (2.31-0ubuntu9) ...
Setting up python-is-python2 (2.7.17-4) ...
Setting up binutils-x86-64-linux-gnu (2.34-6ubuntu1) ...
Setting up libstdc++-9-dev:amd64 (9.3.0-10ubuntu2) ...
Setting up python3-virtualenvwrapper (4.8.4-4) ...
Setting up virtualenvwrapper (4.8.4-4) ...
Setting up binutils (2.34-6ubuntu1) ...
Setting up dpkg-dev (1.19.7ubuntu3) ...
Setting up libexpat1-dev:amd64 (2.2.9-1build1) ...
Setting up gcc-9 (9.3.0-10ubuntu2) ...
Setting up libpython2.7-dev:amd64 (2.7.18~rc1-2) ...
Setting up gcc (4:9.3.0-1ubuntu2) ...
Setting up g++-9 (9.3.0-10ubuntu2) ...
Setting up g++ (4:9.3.0-1ubuntu2) ...
update-alternatives: using /usr/bin/g++ to provide /usr/bin/c++ (c++) in auto mode
Setting up build-essential (12.8ubuntu1) ...
Setting up libpython2-dev:amd64 (2.7.17-2ubuntu4) ...
Setting up python2.7-dev (2.7.18~rc1-2) ...
Setting up python2-dev (2.7.17-2ubuntu4) ...
Setting up python-dev-is-python2 (2.7.17-4) ...
Processing triggers for desktop-file-utils (0.24-1ubuntu2) ...
Processing triggers for mime-support (3.64ubuntu1) ...
Processing triggers for gnome-menus (3.36.0-1ubuntu1) ...
Processing triggers for libc-bin (2.31-0ubuntu9) ...
Processing triggers for man-db (2.9.1-1) ...
Processing triggers for install-info (6.7.0.dfsg.2-5) ...
```

我们再来看一下python的版本：

```bash
ubuntu@ubuntu:~/Desktop$ python
Python 2.7.18rc1 (default, Apr  7 2020, 12:05:55)  
[GCC 9.3.0] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>>
ubuntu@ubuntu:~/Desktop$ python3
Python 3.8.2 (default, Mar 13 2020, 10:14:16) 
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> 
```

可以看到python2、python3都安装了上去，下面我们设置一个环境变量WORKON_HOME，这里的$HOME/Python-workhome就是准备放置虚拟环境的地址

```bash
export WORKON_HOME=$HOME/Python-workhome
```

启动virtualenvwrapper.sh脚本：（注意：可以使用whereis virtualenvwrapper.sh命令查看脚本的位置）

```bash
ubuntu@ubuntu:~/Desktop$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/premkproject
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/postmkproject
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/initialize
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/premkvirtualenv
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/postmkvirtualenv
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/prermvirtualenv
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/postrmvirtualenv
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/predeactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/postdeactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/preactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/postactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/get_env_details
ubuntu@ubuntu:~/Desktop$
```

接下来继续执行命令：

```bash
ubuntu@ubuntu:~/Desktop$ mkvirtualenv --python=$(which python3) angr && pip install angr
created virtual environment CPython3.8.2.final.0-64 in 740ms
  creator CPython3Posix(dest=/home/ubuntu/Python-workhome/angr, clear=False, global=False)
  seeder FromAppData(download=False, contextlib2=latest, distlib=latest, chardet=latest, ipaddr=latest, setuptools=latest, packaging=latest, pyparsing=latest, webencodings=latest, urllib3=latest, colorama=latest, six=latest, CacheControl=latest, html5lib=latest, wheel=latest, pkg_resources=latest, pep517=latest, msgpack=latest, idna=latest, lockfile=latest, pytoml=latest, pip=latest, distro=latest, retrying=latest, certifi=latest, requests=latest, progress=latest, appdirs=latest, via=copy, app_data_dir=/home/ubuntu/.local/share/virtualenv/seed-app-data/v1.0.1.debian)
  activators BashActivator,CShellActivator,FishActivator,PowerShellActivator,PythonActivator,XonshActivator
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/angr/bin/predeactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/angr/bin/postdeactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/angr/bin/preactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/angr/bin/postactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/Python-workhome/angr/bin/get_env_details
Collecting angr
  Downloading angr-8.20.1.7-py3-none-manylinux1_x86_64.whl (1.2 MB)
     |████████████████████████████████| 1.2 MB 996 kB/s 
Collecting ailment==8.20.1.7
  Downloading ailment-8.20.1.7.tar.gz (10 kB)
Collecting dpkt
  Downloading dpkt-1.9.2-py3-none-any.whl (145 kB)
     |████████████████████████████████| 145 kB 2.3 MB/s 
Collecting GitPython
  Downloading GitPython-3.1.2-py3-none-any.whl (451 kB)
     |████████████████████████████████| 451 kB 2.5 MB/s 
Collecting mulpyplexer
  Downloading mulpyplexer-0.08.tar.gz (2.1 kB)
Collecting psutil
  Downloading psutil-5.7.0.tar.gz (449 kB)
     |████████████████████████████████| 449 kB 2.3 MB/s 
Collecting itanium-demangler
  Downloading itanium_demangler-1.0.tar.gz (6.9 kB)
Collecting pycparser>=2.18
  Downloading pycparser-2.20-py2.py3-none-any.whl (112 kB)
     |████████████████████████████████| 112 kB 2.4 MB/s 
Collecting rpyc
  Downloading rpyc-4.1.5-py3-none-any.whl (68 kB)
     |████████████████████████████████| 68 kB 1.6 MB/s 
Collecting cffi>=1.7.0
  Downloading cffi-1.14.0-cp38-cp38-manylinux1_x86_64.whl (409 kB)
     |████████████████████████████████| 409 kB 4.1 MB/s 
Collecting unicorn
  Downloading unicorn-1.0.1-py2.py3-none-manylinux1_x86_64.whl (18.2 MB)
     |████████████████████████████████| 18.2 MB 133 kB/s 
Collecting protobuf
  Downloading protobuf-3.11.3-cp38-cp38-manylinux1_x86_64.whl (1.3 MB)
     |████████████████████████████████| 1.3 MB 167 kB/s 
Collecting progressbar2
  Downloading progressbar2-3.51.3-py2.py3-none-any.whl (51 kB)
     |████████████████████████████████| 51 kB 48 kB/s 
Collecting cachetools
  Downloading cachetools-4.1.0-py3-none-any.whl (10 kB)
Collecting claripy==8.20.1.7
  Downloading claripy-8.20.1.7.tar.gz (121 kB)
     |████████████████████████████████| 121 kB 306 kB/s 
Collecting pyvex==8.20.1.7
  Downloading pyvex-8.20.1.7-py3-none-manylinux1_x86_64.whl (2.7 MB)
     |████████████████████████████████| 2.7 MB 225 kB/s 
Collecting capstone>=3.0.5rc2
  Downloading capstone-4.0.2-py2.py3-none-manylinux1_x86_64.whl (2.1 MB)
     |████████████████████████████████| 2.1 MB 131 kB/s 
Collecting cle==8.20.1.7
  Downloading cle-8.20.1.7.tar.gz (94 kB)
     |████████████████████████████████| 94 kB 216 kB/s 
Collecting sortedcontainers
  Downloading sortedcontainers-2.1.0-py2.py3-none-any.whl (28 kB)
Collecting archinfo==8.20.1.7
  Downloading archinfo-8.20.1.7.tar.gz (43 kB)
     |████████████████████████████████| 43 kB 77 kB/s 
Collecting networkx>=2.0
  Downloading networkx-2.4-py3-none-any.whl (1.6 MB)
     |████████████████████████████████| 1.6 MB 488 kB/s 
Collecting gitdb<5,>=4.0.1
  Downloading gitdb-4.0.5-py3-none-any.whl (63 kB)
     |████████████████████████████████| 63 kB 353 kB/s 
Collecting plumbum
  Downloading plumbum-1.6.9-py2.py3-none-any.whl (115 kB)
     |████████████████████████████████| 115 kB 496 kB/s 
Requirement already satisfied: six>=1.9 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from protobuf->angr) (1.14.0)
Requirement already satisfied: setuptools in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from protobuf->angr) (44.0.0)
Collecting python-utils>=2.3.0
  Downloading python_utils-2.4.0-py2.py3-none-any.whl (12 kB)
Collecting decorator
  Downloading decorator-4.4.2-py2.py3-none-any.whl (9.2 kB)
Collecting future
  Downloading future-0.18.2.tar.gz (829 kB)
     |████████████████████████████████| 829 kB 438 kB/s 
Collecting pysmt
  Downloading PySMT-0.9.0-py2.py3-none-any.whl (317 kB)
     |████████████████████████████████| 317 kB 491 kB/s 
Collecting z3-solver>=4.8.5.0
  Downloading z3_solver-4.8.8.0-py2.py3-none-manylinux1_x86_64.whl (29.6 MB)
     |████████████████████████████████| 29.6 MB 239 kB/s 
Collecting bitstring
  Downloading bitstring-3.1.7.tar.gz (195 kB)
     |████████████████████████████████| 195 kB 226 kB/s 
Collecting minidump==0.0.10
  Downloading minidump-0.0.10-py3-none-any.whl (45 kB)
     |████████████████████████████████| 45 kB 235 kB/s 
Collecting pefile
  Downloading pefile-2019.4.18.tar.gz (62 kB)
     |████████████████████████████████| 62 kB 54 kB/s 
Collecting pyelftools>=0.25
  Downloading pyelftools-0.26-py2.py3-none-any.whl (136 kB)
     |████████████████████████████████| 136 kB 141 kB/s 
Collecting smmap<4,>=3.0.1
  Downloading smmap-3.0.4-py2.py3-none-any.whl (25 kB)
Building wheels for collected packages: ailment, mulpyplexer, psutil, itanium-demangler, claripy, cle, archinfo, future, bitstring, pefile
  Building wheel for ailment (setup.py) ... done
  Created wheel for ailment: filename=ailment-8.20.1.7-py3-none-any.whl size=13864 sha256=86a02282de19c7517e24743ad50e27a251c2710fbe985fd2c591ac0beec88726
  Stored in directory: /home/ubuntu/.cache/pip/wheels/35/fb/a3/be5de9b4da08e78614aaea2a55a45bd2971cce41371aefb970
  Building wheel for mulpyplexer (setup.py) ... done
  Created wheel for mulpyplexer: filename=mulpyplexer-0.8-py3-none-any.whl size=2892 sha256=54bb264411da7d93d434e2494de153aef6178d9a76123af8350daea70e343f04
  Stored in directory: /home/ubuntu/.cache/pip/wheels/85/4f/24/e67b7ffb5aac4b9b244ed93f2117aa3e0beceee19b9bd59115
  Building wheel for psutil (setup.py) ... error
  ERROR: Command errored out with exit status 1:
   command: /home/ubuntu/Python-workhome/angr/bin/python -u -c 'import sys, setuptools, tokenize; sys.argv[0] = '"'"'/tmp/pip-install-x0_gyoxj/psutil/setup.py'"'"'; __file__='"'"'/tmp/pip-install-x0_gyoxj/psutil/setup.py'"'"';f=getattr(tokenize, '"'"'open'"'"', open)(__file__);code=f.read().replace('"'"'\r\n'"'"', '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' bdist_wheel -d /tmp/pip-wheel-eo4vh7dk
       cwd: /tmp/pip-install-x0_gyoxj/psutil/
  Complete output (44 lines):
  running bdist_wheel
  running build
  running build_py
  creating build
  creating build/lib.linux-x86_64-3.8
  creating build/lib.linux-x86_64-3.8/psutil
  copying psutil/__init__.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_common.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_pswindows.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_psosx.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_psbsd.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_pslinux.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_psaix.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_compat.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_psposix.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_pssunos.py -> build/lib.linux-x86_64-3.8/psutil
  creating build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/runner.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/__init__.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_misc.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_memory_leaks.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/__main__.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_contracts.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_system.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_unicode.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_process.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_aix.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_sunos.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_posix.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_windows.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_osx.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_bsd.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_linux.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_connections.py -> build/lib.linux-x86_64-3.8/psutil/tests
  running build_ext
  building 'psutil._psutil_linux' extension
  creating build/temp.linux-x86_64-3.8
  creating build/temp.linux-x86_64-3.8/psutil
  x86_64-linux-gnu-gcc -pthread -Wno-unused-result -Wsign-compare -DNDEBUG -g -fwrapv -O2 -Wall -g -fstack-protector-strong -Wformat -Werror=format-security -g -fwrapv -O2 -g -fstack-protector-strong -Wformat -Werror=format-security -Wdate-time -D_FORTIFY_SOURCE=2 -fPIC -DPSUTIL_POSIX=1 -DPSUTIL_SIZEOF_PID_T=4 -DPSUTIL_VERSION=570 -DPSUTIL_LINUX=1 -I/home/ubuntu/Python-workhome/angr/include -I/usr/include/python3.8 -c psutil/_psutil_common.c -o build/temp.linux-x86_64-3.8/psutil/_psutil_common.o
  psutil/_psutil_common.c:9:10: fatal error: Python.h: No such file or directory
      9 | #include <Python.h>
        |          ^~~~~~~~~~
  compilation terminated.
  error: command 'x86_64-linux-gnu-gcc' failed with exit status 1
  ----------------------------------------
  ERROR: Failed building wheel for psutil
  Running setup.py clean for psutil
  Building wheel for itanium-demangler (setup.py) ... done
  Created wheel for itanium-demangler: filename=itanium_demangler-1.0-py3-none-any.whl size=7289 sha256=139dfeb904675c78aa476f36b4dd1451abe10ad93efac61559d7f0b90151cec6
  Stored in directory: /home/ubuntu/.cache/pip/wheels/ef/d0/d8/c959f310715c5dd85267e00bbc28189f946d5a05c8bf82ce98
  Building wheel for claripy (setup.py) ... done
  Created wheel for claripy: filename=claripy-8.20.1.7-py3-none-any.whl size=150562 sha256=ffa73a9559f73e30fed0304c6a8c325cf03ea7355cd65376ba2682b637372123
  Stored in directory: /home/ubuntu/.cache/pip/wheels/e2/f1/dd/f23b82f8e13b820340d6b511ae41ef516de0c839e1bf417443
  Building wheel for cle (setup.py) ... done
  Created wheel for cle: filename=cle-8.20.1.7-py3-none-any.whl size=122379 sha256=cabc6da9087805d6e21579300bbb16aa4bc11cce050a33aba8ae66f0996981a6
  Stored in directory: /home/ubuntu/.cache/pip/wheels/49/e9/d2/063945e7f0d9973d7e5513ccc2367a502db97f819f0f3d5e1a
  Building wheel for archinfo (setup.py) ... done
  Created wheel for archinfo: filename=archinfo-8.20.1.7-py3-none-any.whl size=53317 sha256=1770a47ba5cc69b92ec1040a7e2aab42ee3f3c1f91802c14a5496e50e967de5c
  Stored in directory: /home/ubuntu/.cache/pip/wheels/bc/6e/f9/2ab66c7550a8106298e285405a4c88d33e377a04a7e25382e7
  Building wheel for future (setup.py) ... done
  Created wheel for future: filename=future-0.18.2-py3-none-any.whl size=491058 sha256=8b770d74cf2fe7522eea65bc3896aca02d1533f74ffb164ddd51c64956c695e0
  Stored in directory: /home/ubuntu/.cache/pip/wheels/8e/70/28/3d6ccd6e315f65f245da085482a2e1c7d14b90b30f239e2cf4
  Building wheel for bitstring (setup.py) ... done
  Created wheel for bitstring: filename=bitstring-3.1.7-py3-none-any.whl size=37946 sha256=d268a057c35ce6fd381ad47b2b0d2ac9ce962a72af962797149eefae427ca35f
  Stored in directory: /home/ubuntu/.cache/pip/wheels/6c/2f/25/52effb6e8c69461de76989c5996e836583fa7bbbc7cd539af1
  Building wheel for pefile (setup.py) ... done
  Created wheel for pefile: filename=pefile-2019.4.18-py3-none-any.whl size=60822 sha256=206281246e2df98278b0fbdc7d4cc82e06196497899934ee82c0dba9f8107e4f
  Stored in directory: /home/ubuntu/.cache/pip/wheels/42/52/d5/9550bbfb9eeceaf0f19db1cf651cc8ba41d3bcf8b4d20e4279
Successfully built ailment mulpyplexer itanium-demangler claripy cle archinfo future bitstring pefile
Failed to build psutil
Installing collected packages: ailment, dpkt, smmap, gitdb, GitPython, mulpyplexer, psutil, itanium-demangler, pycparser, plumbum, rpyc, cffi, unicorn, protobuf, python-utils, progressbar2, cachetools, decorator, future, pysmt, z3-solver, claripy, bitstring, archinfo, pyvex, capstone, minidump, pefile, pyelftools, sortedcontainers, cle, networkx, angr
    Running setup.py install for psutil ... error
    ERROR: Command errored out with exit status 1:
     command: /home/ubuntu/Python-workhome/angr/bin/python -u -c 'import sys, setuptools, tokenize; sys.argv[0] = '"'"'/tmp/pip-install-x0_gyoxj/psutil/setup.py'"'"'; __file__='"'"'/tmp/pip-install-x0_gyoxj/psutil/setup.py'"'"';f=getattr(tokenize, '"'"'open'"'"', open)(__file__);code=f.read().replace('"'"'\r\n'"'"', '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' install --record /tmp/pip-record-a8b2m4_f/install-record.txt --single-version-externally-managed --compile --install-headers /home/ubuntu/Python-workhome/angr/include/site/python3.8/psutil
         cwd: /tmp/pip-install-x0_gyoxj/psutil/
    Complete output (44 lines):
    running install
    running build
    running build_py
    creating build
    creating build/lib.linux-x86_64-3.8
    creating build/lib.linux-x86_64-3.8/psutil
    copying psutil/__init__.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_common.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_pswindows.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_psosx.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_psbsd.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_pslinux.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_psaix.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_compat.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_psposix.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_pssunos.py -> build/lib.linux-x86_64-3.8/psutil
    creating build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/runner.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/__init__.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_misc.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_memory_leaks.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/__main__.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_contracts.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_system.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_unicode.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_process.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_aix.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_sunos.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_posix.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_windows.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_osx.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_bsd.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_linux.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_connections.py -> build/lib.linux-x86_64-3.8/psutil/tests
    running build_ext
    building 'psutil._psutil_linux' extension
    creating build/temp.linux-x86_64-3.8
    creating build/temp.linux-x86_64-3.8/psutil
    x86_64-linux-gnu-gcc -pthread -Wno-unused-result -Wsign-compare -DNDEBUG -g -fwrapv -O2 -Wall -g -fstack-protector-strong -Wformat -Werror=format-security -g -fwrapv -O2 -g -fstack-protector-strong -Wformat -Werror=format-security -Wdate-time -D_FORTIFY_SOURCE=2 -fPIC -DPSUTIL_POSIX=1 -DPSUTIL_SIZEOF_PID_T=4 -DPSUTIL_VERSION=570 -DPSUTIL_LINUX=1 -I/home/ubuntu/Python-workhome/angr/include -I/usr/include/python3.8 -c psutil/_psutil_common.c -o build/temp.linux-x86_64-3.8/psutil/_psutil_common.o
    psutil/_psutil_common.c:9:10: fatal error: Python.h: No such file or directory
        9 | #include <Python.h>
          |          ^~~~~~~~~~
    compilation terminated.
    error: command 'x86_64-linux-gnu-gcc' failed with exit status 1
    ----------------------------------------
ERROR: Command errored out with exit status 1: /home/ubuntu/Python-workhome/angr/bin/python -u -c 'import sys, setuptools, tokenize; sys.argv[0] = '"'"'/tmp/pip-install-x0_gyoxj/psutil/setup.py'"'"'; __file__='"'"'/tmp/pip-install-x0_gyoxj/psutil/setup.py'"'"';f=getattr(tokenize, '"'"'open'"'"', open)(__file__);code=f.read().replace('"'"'\r\n'"'"', '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' install --record /tmp/pip-record-a8b2m4_f/install-record.txt --single-version-externally-managed --compile --install-headers /home/ubuntu/Python-workhome/angr/include/site/python3.8/psutil Check the logs for full command output.
(angr)
```

再试一次，依然报错：

```bash
ubuntu@ubuntu:~/Desktop$ mkvirtualenv --python=$(which python3) angr && pip install angr
created virtual environment CPython3.8.2.final.0-64 in 829ms
  creator CPython3Posix(dest=/home/ubuntu/Python-workhome/angr, clear=False, global=False)
  seeder FromAppData(download=False, contextlib2=latest, distlib=latest, chardet=latest, ipaddr=latest, setuptools=latest, packaging=latest, pyparsing=latest, webencodings=latest, urllib3=latest, colorama=latest, six=latest, CacheControl=latest, html5lib=latest, wheel=latest, pkg_resources=latest, pep517=latest, msgpack=latest, idna=latest, lockfile=latest, pytoml=latest, pip=latest, distro=latest, retrying=latest, certifi=latest, requests=latest, progress=latest, appdirs=latest, via=copy, app_data_dir=/home/ubuntu/.local/share/virtualenv/seed-app-data/v1.0.1.debian)
  activators BashActivator,CShellActivator,FishActivator,PowerShellActivator,PythonActivator,XonshActivator
Collecting angr
  Using cached angr-8.20.1.7-py3-none-manylinux1_x86_64.whl (1.2 MB)
Requirement already satisfied: GitPython in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (3.1.2)
Requirement already satisfied: ailment==8.20.1.7 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (8.20.1.7)
Requirement already satisfied: dpkt in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (1.9.2)
Collecting sortedcontainers
  Using cached sortedcontainers-2.1.0-py2.py3-none-any.whl (28 kB)
Processing /home/ubuntu/.cache/pip/wheels/49/e9/d2/063945e7f0d9973d7e5513ccc2367a502db97f819f0f3d5e1a/cle-8.20.1.7-py3-none-any.whl
Collecting cffi>=1.7.0
  Using cached cffi-1.14.0-cp38-cp38-manylinux1_x86_64.whl (409 kB)
Processing /home/ubuntu/.cache/pip/wheels/bc/6e/f9/2ab66c7550a8106298e285405a4c88d33e377a04a7e25382e7/archinfo-8.20.1.7-py3-none-any.whl
Collecting networkx>=2.0
  Using cached networkx-2.4-py3-none-any.whl (1.6 MB)
Collecting rpyc
  Using cached rpyc-4.1.5-py3-none-any.whl (68 kB)
Collecting progressbar2
  Using cached progressbar2-3.51.3-py2.py3-none-any.whl (51 kB)
Collecting unicorn
  Using cached unicorn-1.0.1-py2.py3-none-manylinux1_x86_64.whl (18.2 MB)
Collecting cachetools
  Using cached cachetools-4.1.0-py3-none-any.whl (10 kB)
Collecting protobuf
  Using cached protobuf-3.11.3-cp38-cp38-manylinux1_x86_64.whl (1.3 MB)
Collecting pyvex==8.20.1.7
  Using cached pyvex-8.20.1.7-py3-none-manylinux1_x86_64.whl (2.7 MB)
Collecting pycparser>=2.18
  Using cached pycparser-2.20-py2.py3-none-any.whl (112 kB)
Processing /home/ubuntu/.cache/pip/wheels/e2/f1/dd/f23b82f8e13b820340d6b511ae41ef516de0c839e1bf417443/claripy-8.20.1.7-py3-none-any.whl
Collecting psutil
  Using cached psutil-5.7.0.tar.gz (449 kB)
Collecting capstone>=3.0.5rc2
  Using cached capstone-4.0.2-py2.py3-none-manylinux1_x86_64.whl (2.1 MB)
Processing /home/ubuntu/.cache/pip/wheels/ef/d0/d8/c959f310715c5dd85267e00bbc28189f946d5a05c8bf82ce98/itanium_demangler-1.0-py3-none-any.whl
Requirement already satisfied: mulpyplexer in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (0.8)
Requirement already satisfied: gitdb<5,>=4.0.1 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from GitPython->angr) (4.0.5)
Processing /home/ubuntu/.cache/pip/wheels/42/52/d5/9550bbfb9eeceaf0f19db1cf651cc8ba41d3bcf8b4d20e4279/pefile-2019.4.18-py3-none-any.whl
Collecting pyelftools>=0.25
  Using cached pyelftools-0.26-py2.py3-none-any.whl (136 kB)
Collecting minidump==0.0.10
  Using cached minidump-0.0.10-py3-none-any.whl (45 kB)
Collecting decorator>=4.3.0
  Using cached decorator-4.4.2-py2.py3-none-any.whl (9.2 kB)
Collecting plumbum
  Using cached plumbum-1.6.9-py2.py3-none-any.whl (115 kB)
Requirement already satisfied: six in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from progressbar2->angr) (1.14.0)
Collecting python-utils>=2.3.0
  Using cached python_utils-2.4.0-py2.py3-none-any.whl (12 kB)
Requirement already satisfied: setuptools in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from protobuf->angr) (44.0.0)
Processing /home/ubuntu/.cache/pip/wheels/6c/2f/25/52effb6e8c69461de76989c5996e836583fa7bbbc7cd539af1/bitstring-3.1.7-py3-none-any.whl
Processing /home/ubuntu/.cache/pip/wheels/8e/70/28/3d6ccd6e315f65f245da085482a2e1c7d14b90b30f239e2cf4/future-0.18.2-py3-none-any.whl
Collecting pysmt
  Using cached PySMT-0.9.0-py2.py3-none-any.whl (317 kB)
Collecting z3-solver>=4.8.5.0
  Using cached z3_solver-4.8.8.0-py2.py3-none-manylinux1_x86_64.whl (29.6 MB)
Requirement already satisfied: smmap<4,>=3.0.1 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from gitdb<5,>=4.0.1->GitPython->angr) (3.0.4)
Building wheels for collected packages: psutil
  Building wheel for psutil (setup.py) ... error
  ERROR: Command errored out with exit status 1:
   command: /home/ubuntu/Python-workhome/angr/bin/python -u -c 'import sys, setuptools, tokenize; sys.argv[0] = '"'"'/tmp/pip-install-3qenw5gp/psutil/setup.py'"'"'; __file__='"'"'/tmp/pip-install-3qenw5gp/psutil/setup.py'"'"';f=getattr(tokenize, '"'"'open'"'"', open)(__file__);code=f.read().replace('"'"'\r\n'"'"', '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' bdist_wheel -d /tmp/pip-wheel-_5ycqc6b
       cwd: /tmp/pip-install-3qenw5gp/psutil/
  Complete output (44 lines):
  running bdist_wheel
  running build
  running build_py
  creating build
  creating build/lib.linux-x86_64-3.8
  creating build/lib.linux-x86_64-3.8/psutil
  copying psutil/__init__.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_common.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_pswindows.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_psosx.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_psbsd.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_pslinux.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_psaix.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_compat.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_psposix.py -> build/lib.linux-x86_64-3.8/psutil
  copying psutil/_pssunos.py -> build/lib.linux-x86_64-3.8/psutil
  creating build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/runner.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/__init__.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_misc.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_memory_leaks.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/__main__.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_contracts.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_system.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_unicode.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_process.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_aix.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_sunos.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_posix.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_windows.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_osx.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_bsd.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_linux.py -> build/lib.linux-x86_64-3.8/psutil/tests
  copying psutil/tests/test_connections.py -> build/lib.linux-x86_64-3.8/psutil/tests
  running build_ext
  building 'psutil._psutil_linux' extension
  creating build/temp.linux-x86_64-3.8
  creating build/temp.linux-x86_64-3.8/psutil
  x86_64-linux-gnu-gcc -pthread -Wno-unused-result -Wsign-compare -DNDEBUG -g -fwrapv -O2 -Wall -g -fstack-protector-strong -Wformat -Werror=format-security -g -fwrapv -O2 -g -fstack-protector-strong -Wformat -Werror=format-security -Wdate-time -D_FORTIFY_SOURCE=2 -fPIC -DPSUTIL_POSIX=1 -DPSUTIL_SIZEOF_PID_T=4 -DPSUTIL_VERSION=570 -DPSUTIL_LINUX=1 -I/home/ubuntu/Python-workhome/angr/include -I/usr/include/python3.8 -c psutil/_psutil_common.c -o build/temp.linux-x86_64-3.8/psutil/_psutil_common.o
  psutil/_psutil_common.c:9:10: fatal error: Python.h: No such file or directory
      9 | #include <Python.h>
        |          ^~~~~~~~~~
  compilation terminated.
  error: command 'x86_64-linux-gnu-gcc' failed with exit status 1
  ----------------------------------------
  ERROR: Failed building wheel for psutil
  Running setup.py clean for psutil
Failed to build psutil
Installing collected packages: sortedcontainers, future, pefile, bitstring, pycparser, cffi, archinfo, pyvex, pyelftools, minidump, cle, decorator, networkx, plumbum, rpyc, python-utils, progressbar2, unicorn, cachetools, protobuf, pysmt, z3-solver, claripy, psutil, capstone, itanium-demangler, angr
    Running setup.py install for psutil ... error
    ERROR: Command errored out with exit status 1:
     command: /home/ubuntu/Python-workhome/angr/bin/python -u -c 'import sys, setuptools, tokenize; sys.argv[0] = '"'"'/tmp/pip-install-3qenw5gp/psutil/setup.py'"'"'; __file__='"'"'/tmp/pip-install-3qenw5gp/psutil/setup.py'"'"';f=getattr(tokenize, '"'"'open'"'"', open)(__file__);code=f.read().replace('"'"'\r\n'"'"', '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' install --record /tmp/pip-record-b1ebflo9/install-record.txt --single-version-externally-managed --compile --install-headers /home/ubuntu/Python-workhome/angr/include/site/python3.8/psutil
         cwd: /tmp/pip-install-3qenw5gp/psutil/
    Complete output (44 lines):
    running install
    running build
    running build_py
    creating build
    creating build/lib.linux-x86_64-3.8
    creating build/lib.linux-x86_64-3.8/psutil
    copying psutil/__init__.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_common.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_pswindows.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_psosx.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_psbsd.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_pslinux.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_psaix.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_compat.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_psposix.py -> build/lib.linux-x86_64-3.8/psutil
    copying psutil/_pssunos.py -> build/lib.linux-x86_64-3.8/psutil
    creating build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/runner.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/__init__.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_misc.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_memory_leaks.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/__main__.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_contracts.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_system.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_unicode.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_process.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_aix.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_sunos.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_posix.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_windows.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_osx.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_bsd.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_linux.py -> build/lib.linux-x86_64-3.8/psutil/tests
    copying psutil/tests/test_connections.py -> build/lib.linux-x86_64-3.8/psutil/tests
    running build_ext
    building 'psutil._psutil_linux' extension
    creating build/temp.linux-x86_64-3.8
    creating build/temp.linux-x86_64-3.8/psutil
    x86_64-linux-gnu-gcc -pthread -Wno-unused-result -Wsign-compare -DNDEBUG -g -fwrapv -O2 -Wall -g -fstack-protector-strong -Wformat -Werror=format-security -g -fwrapv -O2 -g -fstack-protector-strong -Wformat -Werror=format-security -Wdate-time -D_FORTIFY_SOURCE=2 -fPIC -DPSUTIL_POSIX=1 -DPSUTIL_SIZEOF_PID_T=4 -DPSUTIL_VERSION=570 -DPSUTIL_LINUX=1 -I/home/ubuntu/Python-workhome/angr/include -I/usr/include/python3.8 -c psutil/_psutil_common.c -o build/temp.linux-x86_64-3.8/psutil/_psutil_common.o
    psutil/_psutil_common.c:9:10: fatal error: Python.h: No such file or directory
        9 | #include <Python.h>
          |          ^~~~~~~~~~
    compilation terminated.
    error: command 'x86_64-linux-gnu-gcc' failed with exit status 1
    ----------------------------------------
ERROR: Command errored out with exit status 1: /home/ubuntu/Python-workhome/angr/bin/python -u -c 'import sys, setuptools, tokenize; sys.argv[0] = '"'"'/tmp/pip-install-3qenw5gp/psutil/setup.py'"'"'; __file__='"'"'/tmp/pip-install-3qenw5gp/psutil/setup.py'"'"';f=getattr(tokenize, '"'"'open'"'"', open)(__file__);code=f.read().replace('"'"'\r\n'"'"', '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' install --record /tmp/pip-record-b1ebflo9/install-record.txt --single-version-externally-managed --compile --install-headers /home/ubuntu/Python-workhome/angr/include/site/python3.8/psutil Check the logs for full command output.
(angr)
```

此时**<font style="color:#F5222D;">新开启一个终端窗口</font>**，发现实际环境中pip未安装：

```bash
ubuntu@ubuntu:~/Desktop$ pip

Command 'pip' not found, but there are 18 similar ones.

ubuntu@ubuntu:~/Desktop$ pip3

Command 'pip3' not found, but can be installed with:

sudo apt install python3-pip

```

在此终端中进入虚拟环境：

```bash
ubuntu@ubuntu:~/Desktop$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/premkproject
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/postmkproject
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/initialize
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/premkvirtualenv
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/postmkvirtualenv
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/prermvirtualenv
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/postrmvirtualenv
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/predeactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/postdeactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/preactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/postactivate
virtualenvwrapper.user_scripts creating /home/ubuntu/.virtualenvs/get_env_details
```

分别执行命令：

```bash
export WORKON_HOME=$HOME/Python-workhome
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
```



紧接着：

```bash
ubuntu@ubuntu:~/Desktop$ sudo apt install python3-pip
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following additional packages will be installed:
  libpython3-dev libpython3.8 libpython3.8-dev libpython3.8-minimal
  libpython3.8-stdlib python3-dev python3-wheel python3.8 python3.8-dev
  python3.8-minimal zlib1g-dev
Suggested packages:
  python3.8-venv python3.8-doc binfmt-support
The following NEW packages will be installed:
  libpython3-dev libpython3.8-dev python3-dev python3-pip python3-wheel
  python3.8-dev zlib1g-dev
The following packages will be upgraded:
  libpython3.8 libpython3.8-minimal libpython3.8-stdlib python3.8
  python3.8-minimal
5 upgraded, 7 newly installed, 0 to remove and 73 not upgraded.
Need to get 4,871 kB/11.1 MB of archives.
After this operation, 22.3 MB of additional disk space will be used.
Do you want to continue? [Y/n] Y
Get:1 http://us.archive.ubuntu.com/ubuntu focal-updates/main amd64 libpython3.8-dev amd64 3.8.2-1ubuntu1.1 [3,938 kB]
Get:2 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libpython3-dev amd64 3.8.2-0ubuntu2 [7,236 B]
Get:3 http://us.archive.ubuntu.com/ubuntu focal/main amd64 zlib1g-dev amd64 1:1.2.11.dfsg-2ubuntu1 [156 kB]
Get:4 http://us.archive.ubuntu.com/ubuntu focal-updates/main amd64 python3.8-dev amd64 3.8.2-1ubuntu1.1 [515 kB]
Get:5 http://us.archive.ubuntu.com/ubuntu focal/main amd64 python3-dev amd64 3.8.2-0ubuntu2 [1,212 B]
Get:6 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python3-wheel all 0.34.2-1 [23.8 kB]
Get:7 http://us.archive.ubuntu.com/ubuntu focal/universe amd64 python3-pip all 20.0.2-5ubuntu1 [230 kB]
Fetched 4,871 kB in 23s (210 kB/s)                                             
(Reading database ... 185966 files and directories currently installed.)
Preparing to unpack .../00-python3.8_3.8.2-1ubuntu1.1_amd64.deb ...
Unpacking python3.8 (3.8.2-1ubuntu1.1) over (3.8.2-1ubuntu1) ...
Preparing to unpack .../01-libpython3.8_3.8.2-1ubuntu1.1_amd64.deb ...
Unpacking libpython3.8:amd64 (3.8.2-1ubuntu1.1) over (3.8.2-1ubuntu1) ...
Preparing to unpack .../02-libpython3.8-stdlib_3.8.2-1ubuntu1.1_amd64.deb ...
Unpacking libpython3.8-stdlib:amd64 (3.8.2-1ubuntu1.1) over (3.8.2-1ubuntu1) ...
Preparing to unpack .../03-python3.8-minimal_3.8.2-1ubuntu1.1_amd64.deb ...
Unpacking python3.8-minimal (3.8.2-1ubuntu1.1) over (3.8.2-1ubuntu1) ...
Preparing to unpack .../04-libpython3.8-minimal_3.8.2-1ubuntu1.1_amd64.deb ...
Unpacking libpython3.8-minimal:amd64 (3.8.2-1ubuntu1.1) over (3.8.2-1ubuntu1) ..
.
Selecting previously unselected package libpython3.8-dev:amd64.
Preparing to unpack .../05-libpython3.8-dev_3.8.2-1ubuntu1.1_amd64.deb ...
Unpacking libpython3.8-dev:amd64 (3.8.2-1ubuntu1.1) ...
Selecting previously unselected package libpython3-dev:amd64.
Preparing to unpack .../06-libpython3-dev_3.8.2-0ubuntu2_amd64.deb ...
Unpacking libpython3-dev:amd64 (3.8.2-0ubuntu2) ...
Selecting previously unselected package zlib1g-dev:amd64.
Preparing to unpack .../07-zlib1g-dev_1%3a1.2.11.dfsg-2ubuntu1_amd64.deb ...
Unpacking zlib1g-dev:amd64 (1:1.2.11.dfsg-2ubuntu1) ...
Selecting previously unselected package python3.8-dev.
Preparing to unpack .../08-python3.8-dev_3.8.2-1ubuntu1.1_amd64.deb ...
Unpacking python3.8-dev (3.8.2-1ubuntu1.1) ...
Selecting previously unselected package python3-dev.
Preparing to unpack .../09-python3-dev_3.8.2-0ubuntu2_amd64.deb ...
Unpacking python3-dev (3.8.2-0ubuntu2) ...
Selecting previously unselected package python3-wheel.
Preparing to unpack .../10-python3-wheel_0.34.2-1_all.deb ...
Unpacking python3-wheel (0.34.2-1) ...
Selecting previously unselected package python3-pip.
Preparing to unpack .../11-python3-pip_20.0.2-5ubuntu1_all.deb ...
Unpacking python3-pip (20.0.2-5ubuntu1) ...
Setting up libpython3.8-minimal:amd64 (3.8.2-1ubuntu1.1) ...
Setting up python3-wheel (0.34.2-1) ...
Setting up python3-pip (20.0.2-5ubuntu1) ...
Setting up zlib1g-dev:amd64 (1:1.2.11.dfsg-2ubuntu1) ...
Setting up python3.8-minimal (3.8.2-1ubuntu1.1) ...
Setting up libpython3.8-stdlib:amd64 (3.8.2-1ubuntu1.1) ...
Setting up python3.8 (3.8.2-1ubuntu1.1) ...
Setting up libpython3.8:amd64 (3.8.2-1ubuntu1.1) ...
Setting up libpython3.8-dev:amd64 (3.8.2-1ubuntu1.1) ...
Setting up python3.8-dev (3.8.2-1ubuntu1.1) ...
Setting up libpython3-dev:amd64 (3.8.2-0ubuntu2) ...
Setting up python3-dev (3.8.2-0ubuntu2) ...
Processing triggers for mime-support (3.64ubuntu1) ...
Processing triggers for gnome-menus (3.36.0-1ubuntu1) ...
Processing triggers for libc-bin (2.31-0ubuntu9) ...
Processing triggers for man-db (2.9.1-1) ...
Processing triggers for desktop-file-utils (0.24-1ubuntu2) ...
```

最后：

```bash
ubuntu@ubuntu:~/Desktop$ mkvirtualenv --python=$(which python3) angr && pip install angr
created virtual environment CPython3.8.2.final.0-64 in 235ms
  creator CPython3Posix(dest=/home/ubuntu/Python-workhome/angr, clear=False, global=False)
  seeder FromAppData(download=False, contextlib2=latest, distlib=latest, chardet=latest, ipaddr=latest, setuptools=latest, packaging=latest, pyparsing=latest, webencodings=latest, urllib3=latest, colorama=latest, six=latest, CacheControl=latest, html5lib=latest, wheel=latest, pkg_resources=latest, pep517=latest, msgpack=latest, idna=latest, lockfile=latest, pytoml=latest, pip=latest, distro=latest, retrying=latest, certifi=latest, requests=latest, progress=latest, appdirs=latest, via=copy, app_data_dir=/home/ubuntu/.local/share/virtualenv/seed-app-data/v1.0.1.debian)
  activators BashActivator,CShellActivator,FishActivator,PowerShellActivator,PythonActivator,XonshActivator
Collecting angr
  Using cached angr-8.20.1.7-py3-none-manylinux1_x86_64.whl (1.2 MB)
Requirement already satisfied: rpyc in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (4.1.5)
Requirement already satisfied: archinfo==8.20.1.7 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (8.20.1.7)
Collecting psutil
  Using cached psutil-5.7.0.tar.gz (449 kB)
Requirement already satisfied: capstone>=3.0.5rc2 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (4.0.2)
Requirement already satisfied: GitPython in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (3.1.2)
Requirement already satisfied: pycparser>=2.18 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (2.20)
Requirement already satisfied: pyvex==8.20.1.7 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (8.20.1.7)
Requirement already satisfied: sortedcontainers in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (2.1.0)
Requirement already satisfied: ailment==8.20.1.7 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (8.20.1.7)
Processing /home/ubuntu/.cache/pip/wheels/ef/d0/d8/c959f310715c5dd85267e00bbc28189f946d5a05c8bf82ce98/itanium_demangler-1.0-py3-none-any.whl
Requirement already satisfied: networkx>=2.0 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (2.4)
Processing /home/ubuntu/.cache/pip/wheels/85/4f/24/e67b7ffb5aac4b9b244ed93f2117aa3e0beceee19b9bd59115/mulpyplexer-0.8-py3-none-any.whl
Requirement already satisfied: protobuf in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (3.11.3)
Requirement already satisfied: cffi>=1.7.0 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (1.14.0)
Requirement already satisfied: cle==8.20.1.7 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (8.20.1.7)
Requirement already satisfied: cachetools in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (4.1.0)
Requirement already satisfied: progressbar2 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (3.51.3)
Requirement already satisfied: unicorn in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (1.0.1)
Requirement already satisfied: claripy==8.20.1.7 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (8.20.1.7)
Requirement already satisfied: dpkt in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from angr) (1.9.2)
Requirement already satisfied: plumbum in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from rpyc->angr) (1.6.9)
Requirement already satisfied: gitdb<5,>=4.0.1 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from GitPython->angr) (4.0.5)
Requirement already satisfied: bitstring in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from pyvex==8.20.1.7->angr) (3.1.7)
Requirement already satisfied: future in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from pyvex==8.20.1.7->angr) (0.18.2)
Requirement already satisfied: decorator>=4.3.0 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from networkx>=2.0->angr) (4.4.2)
Requirement already satisfied: six>=1.9 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from protobuf->angr) (1.14.0)
Requirement already satisfied: setuptools in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from protobuf->angr) (44.0.0)
Requirement already satisfied: pyelftools>=0.25 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from cle==8.20.1.7->angr) (0.26)
Requirement already satisfied: minidump==0.0.10 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from cle==8.20.1.7->angr) (0.0.10)
Requirement already satisfied: pefile in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from cle==8.20.1.7->angr) (2019.4.18)
Requirement already satisfied: python-utils>=2.3.0 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from progressbar2->angr) (2.4.0)
Requirement already satisfied: z3-solver>=4.8.5.0 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from claripy==8.20.1.7->angr) (4.8.8.0)
Requirement already satisfied: pysmt in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from claripy==8.20.1.7->angr) (0.9.0)
Requirement already satisfied: smmap<4,>=3.0.1 in /home/ubuntu/Python-workhome/angr/lib/python3.8/site-packages (from gitdb<5,>=4.0.1->GitPython->angr) (3.0.4)
Building wheels for collected packages: psutil
  Building wheel for psutil (setup.py) ... done
  Created wheel for psutil: filename=psutil-5.7.0-cp38-cp38-linux_x86_64.whl size=285825 sha256=003436de5046cfdf5658f64ec1441bf3ce93d6f0c530c350b09b30d7d6670c40
  Stored in directory: /home/ubuntu/.cache/pip/wheels/90/c9/b6/04665702b01dbd9ee92a05e834b627948ed01cdd482e6a78e1
Successfully built psutil
Installing collected packages: psutil, itanium-demangler, mulpyplexer, angr
Successfully installed angr-8.20.1.7 itanium-demangler-1.0 mulpyplexer-0.8 psutil-5.7.0
(angr)
```

测试一下：

```bash
ubuntu@ubuntu:~/Desktop$ python
Python 3.8.2 (default, Apr 27 2020, 15:53:34) 
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import angr
>>> 
```

未报错，成功！

**配置好之后使用angr的方法：**

```bash
ubuntu@ubuntu:~/Desktop$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop$ workon
angr
ubuntu@ubuntu:~/Desktop$ workon angr
(angr) ubuntu@ubuntu:~/Desktop$ python3
Python 3.8.2 (default, Apr 27 2020, 15:53:34) 
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import angr
>>> 
[1]+  Stopped                 python3
(angr) ubuntu@ubuntu:~/Desktop$ python2
Python 2.7.18rc1 (default, Apr  7 2020, 12:05:55) 
[GCC 9.3.0] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import angr
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: No module named angr
>>> 
[2]+  Stopped                 python2
(angr) ubuntu@ubuntu:~/Desktop$ 
```

