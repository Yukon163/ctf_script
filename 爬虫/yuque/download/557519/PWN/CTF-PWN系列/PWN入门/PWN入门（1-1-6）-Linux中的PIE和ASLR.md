> 文章来源于：[https://blog.csdn.net/counsellor/article/details/81543197](https://blog.csdn.net/counsellor/article/details/81543197)
>
> [https://www.cnblogs.com/rec0rd/p/7646857.html](https://www.cnblogs.com/rec0rd/p/7646857.html)
>

# 0x00 背景知识
ASLR(Address Space Layout Randomization)在2005年被引入到Linux的内核 kernel 2.6.12 中，当然早在2004年就以patch的形式被引入。**<font style="color:#F5222D;">随着内存地址的随机化，使得响应的应用变得随机。这意味着同一应用多次执行所使用内存空间完全不同，也意味着简单的缓冲区溢出攻击无法达到目的。</font>**

GDB从版本7开始，第一次在Ubuntu 9.10（Karmic）上，被调试的程序可以被关闭ASLR（通过标记位ADDR_NO_RANDOMIZE ）。

此处有坑，笔者有一个Ubuntu 9.10的虚拟机，用了下面将要介绍的全部姿势，死活关闭不了ASLR，后来换成Ubuntu 10.04就没问题了，说明Ubuntu 9.10的版本控制ASLR的方法还不成熟，需要重源码层面确认是否可以关闭开启，真是坑到家了。

# 0x01 查看ASLR设置
查看当前操作系统的ASLR配置情况，两种命令任你选择

```bash
$ cat /proc/sys/kernel/randomize_va_space
2
$ sysctl -a --pattern randomize
kernel.randomize_va_space = 2
```

# 0x02 配置选项
0 = 关闭

1 = 半随机。共享库、栈、mmap() 以及 VDSO 将被随机化。（留坑，PIE会影响heap的随机化。。）

2 = 全随机。除了1中所述，还有heap。

后面会详细介绍ASLR的组成，不关心的同学可以简单理解为ASLR不是一个笼统的概念，而是要按模块单独实现的。当然，在攻防对抗的角度上，应为不是所有组件都会随机，所以我们就可以按图索骥，写出通用的shellcode调用系统库。

# 0x03 查看地址空间随机效果
使用ldd命令就可以观察到程序所依赖动态加载模块的地址空间，如下下图所示，被括号包裹。在shell中，运行两次相同的ldd命令，即可对比出前后地址的不同之处，当然，ASLR开启时才会变化：

ASLR开启时，动态库的加载地址不同

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597395340137-0938518d-ea22-4384-8090-fdebb072dd85.png)

ASLR关闭时，动态库的加载地址相同

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1597395394600-40a32b2d-eb22-4bde-b610-4db8f1788886.png)

# 0x04 关闭ASLR
**方法一： 手动修改randomize_va_space文件**

诚如上面介绍的randomize_va_space文件的枚举值含义，设置的值不同，linux内核加载程序的地址空间的策略就会不同。比较简单明了。这里0代表关闭ASLR。

```bash
# echo 0 > /proc/sys/kernel/randomize_va_space
1
```

> 注意，这里是先进root权限，后执行。不要问为什么sudo echo 0 > /proc/sys/kernel/randomize_va_space为什么会报错
>

**方法二： 使用sysctl控制ASLR**

```bash
$ sysctl -w kernel.randomize_va_space=0
```

这是一种临时改变随机策略的方法，重启之后将恢复默认。如果需要永久保存配置，需要在配置文件 /etc/sysctl.conf 中增加这个选项。

**方法三： 使用setarch控制单个程序的随机化**

如果你想历史关闭单个程序的ASLR，使用setarch是很好的选择。setarch命令如其名，改变程序的运行架构环境，并可以自定义环境flag。

```bash
setarch `uname -m` -R ./your_program
1
```

-R参数代表关闭地址空间随机化（开启ADDR_NO_RANDOMIZE)

**方法四： 在GDB场景下，使用set disable-randomization off**

在调试特定程序时，可以通过set disable-randomization命令开启或者关闭地址空间随机化。默认是关闭随机化的，也就是on状态。

当然，这里开启，关闭和查看的方法看起来就比较正规了。

```bash
关闭ASLR：
set disable-randomization on
开启ASLR：
set disable-randomization off
查看ASLR状态：
show disable-randomization
```

# 0x05 ASLR与PIE的区别
首先，ASLR的是操作系统的功能选项，作用于executable（ELF）装入内存运行时，因而只能随机化stack、heap、libraries的基址；而PIE（Position Independent Executables）是编译器（gcc，..）功能选项（-fPIE），作用于excutable编译过程，可将其理解为特殊的PIC（so专用，Position Independent Code），加了PIE选项编译出来的ELF用file命令查看会显示其为so，其随机化了ELF装载内存的基址（代码段、plt、got、data等共同的基址）。

　　其次，ASLR早于PIE出现，所以有return-to-plt、got hijack、stack-pivot(bypass stack ransomize)等绕过ASLR的技术；而在ASLR+PIE之后，这些bypass技术就都失效了，只能借助其他的信息泄露漏洞泄露基址（常用libc基址）。

　　最后，ASLR有0/1/2三种级别，其中0表示ASLR未开启，1表示随机化stack、libraries，2还会随机化heap。

> 注：只有在开启 ASLR 之后，PIE 才会生效。
>

