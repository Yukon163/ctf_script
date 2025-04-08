ELF是32位的，64位的虚拟机无法直接运行，需要安装32的库文件，执行命令：

```bash
ubuntu@ubuntu:~/Desktop/angr$ sudo apt-get install lib32z1
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following additional packages will be installed:
  libc6-i386
The following NEW packages will be installed:
  lib32z1 libc6-i386
0 upgraded, 2 newly installed, 0 to remove and 73 not upgraded.
Need to get 2,780 kB of archives.
After this operation, 14.9 MB of additional disk space will be used.
Do you want to continue? [Y/n] Y
Get:1 http://us.archive.ubuntu.com/ubuntu focal/main amd64 libc6-i386 amd64 2.31-0ubuntu9 [2,723 kB]
Get:2 http://us.archive.ubuntu.com/ubuntu focal/main amd64 lib32z1 amd64 1:1.2.11.dfsg-2ubuntu1 [56.6 kB]                                           
Fetched 2,780 kB in 15s (191 kB/s)                                                                                                                  
Selecting previously unselected package libc6-i386.
(Reading database ... 187508 files and directories currently installed.)
Preparing to unpack .../libc6-i386_2.31-0ubuntu9_amd64.deb ...
Unpacking libc6-i386 (2.31-0ubuntu9) ...
Selecting previously unselected package lib32z1.
Preparing to unpack .../lib32z1_1%3a1.2.11.dfsg-2ubuntu1_amd64.deb ...
Unpacking lib32z1 (1:1.2.11.dfsg-2ubuntu1) ...
Setting up libc6-i386 (2.31-0ubuntu9) ...
Setting up lib32z1 (1:1.2.11.dfsg-2ubuntu1) ...
Processing triggers for libc-bin (2.31-0ubuntu9) ...
```

这样就可以了

