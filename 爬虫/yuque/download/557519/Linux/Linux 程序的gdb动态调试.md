peda是gdb的一个插件，安装后大大提升gdb在分析逆向/溢出程序时的用户体验。

安装方法：



```bash
git clone https://github.com/longld/peda.git ~/peda
echo "source ~/peda/peda.py" >> ~/.gdbinit
```

<font style="color:#000000;">其实就是下载完成后, 将 source ~/peda/peda.py 写入 ~/.gdbinit</font>

安装好后，开始进行调试，gdb 调试文件名，如下：

```bash
root@kali:~/桌面/CTF# gdb T0p_Gear_unupx
GNU gdb (Debian 8.2.1-2) 8.2.1
Copyright (C) 2018 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

For help, type "help".
Type "apropos word" to search for commands related to "word"...
Reading symbols from T0p_Gear_unupx...(no debugging symbols found)...done.
gdb-peda$ 
```

输入start，回车，调试程序会自动中断在入口点，介绍一下常用的命令：

| <font style="color:#262626;">break *0x400100 (b main)</font> | <font style="color:#262626;">在 0x400100 处下断点</font> |
| --- | --- |
| <font style="color:#262626;">tb</font> | <font style="color:#262626;">一次性断点</font> |
| <font style="color:#262626;">info b</font> | <font style="color:#262626;">查看断点信息</font> |
| delete [number] | <font style="color:#262626;">删除断点</font> |
| <font style="color:#262626;">watch *(int *)0x08044530</font> | <font style="color:#262626;">在内存0x0804453处的数据改变时stop</font> |
| <font style="color:#262626;">x /4xg $ebp</font> | <font style="color:#262626;">查看ebp开始的4个8字节内容（b：单字节，h：双字节，w：四字节，g：八字节；x：十六进制，s：字符串输出，i：反汇编，c：单字符）</font> |
| <font style="color:#262626;">p $eax</font> | <font style="color:#262626;">输出eax的内容</font> |
| <font style="color:#262626;">set $eax=4</font> | <font style="color:#262626;">修改变量值</font> |
| <font style="color:#262626;">c</font> | <font style="color:#262626;">继续运行</font> |
| <font style="color:#262626;">r（run）</font> | <font style="color:#262626;">重新开始运行</font> |
| <font style="color:#262626;">ni</font> | <font style="color:#262626;">单步步过</font> |
| <font style="color:#262626;">si</font> | <font style="color:#262626;">单步步入</font> |
| <font style="color:#262626;">fini</font> | <font style="color:#262626;">运行至函数刚结束处</font> |
| <font style="color:#262626;">return expression</font> | <font style="color:#262626;">将函数返回值指定为expression</font> |
| <font style="color:#262626;">bt</font> | <font style="color:#262626;">查看当前栈帧</font> |
| <font style="color:#262626;">info f</font> | <font style="color:#262626;">查看当前栈帧</font> |
| <font style="color:#262626;">context</font> | <font style="color:#262626;">查看运行上下文</font> |
| <font style="color:#262626;">stack</font> | <font style="color:#262626;">查看当前堆栈</font> |
| <font style="color:#262626;">call func</font> | <font style="color:#262626;">强制函数调用</font> |
| <font style="color:#262626;">ropgagdet</font> | <font style="color:#262626;">找common rop</font> |
| <font style="color:#262626;">vmmap</font> | 查看虚拟地址分布<br/> |
| <font style="color:#262626;">shellcode</font> | <font style="color:#262626;">搜索，生成shellcode</font> |
| <font style="color:#262626;">ptype struct link_map</font> | <font style="color:#262626;">查看link_map定义</font> |
| <font style="color:#262626;">p &((struct link_map*)0)->l_info</font> | <font style="color:#262626;">查看l_info成员偏移</font> |


可以使用这道题来练练手：

[https://www.yuque.com/cyberangel/vqcmca/ch05sw](https://www.yuque.com/cyberangel/vqcmca/ch05sw)

