参考资料：[https://blog.csdn.net/Dakshesh/article/details/102588364](https://blog.csdn.net/Dakshesh/article/details/102588364)

**首先copy别人的东西：**

**系统经典语录：  
****1、命令操作完没有任何消息信息, 就是最好的消息  
****2、系统一切从根开始  
****3、系统中数据一切皆文件**

****

**一、linux的关机命令：**

1、shutdown命令可以将系统安全的关机：

①【-r】重启计算机

②【-h】关机后关闭电源

③【-c】cancel current process 取消目前正在执行的关机程序

④【-time】设定关机（shutdown）前的时间

shutdown -h now 立刻关机

<font style="color:#F5222D;">shutdown -h 时刻 在某个时刻关机？？？？？</font>

shutdown -r now 立刻重启

shutdown -h 10 十分钟后关机 

2、顺带提一下**halt**也可以单独使用，也可以达到关机的效果，halt命令时间上调用的是shutdown -h，halt执行时，杀死应用进程，执行<font style="color:#F5222D;">sync</font>系统调用，内核停止，可能导致linux系统的死机，需要重启

3、**poweroff**会发送一个<font style="color:#F5222D;">ACPI</font>信号来通知系统关机

4、**<font style="color:#F5222D;">init</font>**<font style="color:#F5222D;">进程</font>一共分为7个级别，0和6代表关机和重启



**二、linux重启命令：**<font style="color:#F5222D;">只有这一个吗？</font>

reboot执行重启命令

三、linux查询<font style="color:#F5222D;">当前</font>所在位置路径：pwd

四、linux切换目录：cd

五、linux创建目录文件；mkdir

参数：-p递归创建

六、linux以树形结构展示目录结构：tree

参数：-l：指定层数

          -d：只显示目录

七、linux查看命令：ls

参数：-l：长格式显示

          -a：显示所有文件

          -d：显示目录

八：linux复制命令：cp

参数：-r 递归

    -i是否确认覆盖

    -a 相当于dpr -p 保持文件或目录树形

九：linux删除命令：rm

参数：-r 递归

    -f强制

两个一起用可以删掉世界（极其危险的命令）

十、linux更改命令别名：alias 删除命令别名：unalias

十一、linux移动命令：mv

参数：-t 把所用源参数移动到目录中

在相同路径目录下中使用相当于改名，在不同路径中相当于移动

十二、linux打印命令：echo

参数：-h不换行 -e支持转义 \t代表top \n代表回车

十三；linux创建文件或更新文件时间戳：touch

十四：linux查看文件内容：cat

参数：-n 显示行号

十五：linux输出头部/尾部部分文件：head/tail

参数： -n 行数

十六：linux替换或删除字符：

注意：只是把文件内容输出出来，而不是改变文件内容

十七：linux查找文件里符合条件的字符串：grep

十八：linux查看文件类型：file

十九：linux：查找命令所在路径：which

二十：linux查找目录下文件：find

参数：-name 按文件名查找

   -type 按文件类型查找（后面接文件类型参数，例如：目录d、文件 f）

   -exec 对搜索结果进行处理 

   -mtime 按修改时间进行查找

二十一：查看当前用户/添加普通用户：whoami/useradd

二十二：查看文件属性：stat

二十三：显示系统时间和日期：date

二十四：查看文件系统：df

二十五：压缩命令：

| 参数 | 用途 |
| :---: | :---: |
| - z | 压缩 |
| - c | 创建 |
| - v | 输出打包过程 |
| - f | 文件 |
| - t | 查看文件 |
| - C | 指定解压路径 |
| - x | 解压 |
| - h | 跟随软连接 |
| - exclude | 排除不打包文件 |
| - X | 从文件中排除不打包的文件 |


二十六：查看服务是否开启：telnet

telnet命令通常用来远程登录，但也可以确定远程服务的状态，比如确定远程服务器的某个端口是否能访问。

二十七：查看硬件信息：

| 命令 | 用途 |
| :---: | :---: |
| lscpu | 查看cpu使用情况 |
| free | 查看内存使用情况 |
| w | 查看负载使用情况 |
| top | 查看负载使用情况 |
| uptime | 查看负载使用情况 |


二十八：删除执行中的程序：kill

强行杀死进程（危险命令）

二十九：显示目录或文件的大小：du

参数：- h 人类能看懂的形式显示出来

注：显示指定的目录或文件所占用的磁盘空间

