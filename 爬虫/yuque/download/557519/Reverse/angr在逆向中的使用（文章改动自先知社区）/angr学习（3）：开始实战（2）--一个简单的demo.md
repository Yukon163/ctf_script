在上一节我们使用自己编写的程序来进行angr的学习，接下来继续实战，看一看使用angr解题到底有多么简单

示例程序：[https://github.com/angr/angr-doc/tree/master/examples/defcamp_r100](https://github.com/angr/angr-doc/tree/master/examples/defcamp_r100)

开启虚拟环境：

```bash
ubuntu@ubuntu:~/Desktop/angr$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/angr$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/angr$ workon
angr
ubuntu@ubuntu:~/Desktop/angr$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/angr$
```

看一下文件属性：

```bash
(angr) ubuntu@ubuntu:~/Desktop/angr$ file r100
r100: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 2.6.24, BuildID[sha1]=0f464824cc8ee321ef9a80a799c70b1b6aec8168, stripped
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

顺便再看一下文件保护：

```bash
(angr) ubuntu@ubuntu:~/Desktop/angr$ checksec --file=r100
RELRO           STACK CANARY      NX            PIE             RPATH      RUNPATH	Symbols		FORTIFY	Fortified	Fortifiable  FILE
Partial RELRO   Canary found      NX enabled    No PIE          No RPATH   No RUNPATH   No Symbols      Yes	0		2	r100
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

没有开启PIE，这为我们编写angr脚本提供了方便

将文件载入IDA中,我们看一下文件的执行流程:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592451850881-064f5693-5336-4634-8bb2-2e5e4670e7da.png)

执行流程很简单：首先输入未知的内容，在使用函数sub_4006FD进行处理判断，最终执行到结果(Nice!或Incorrect password)，在汇编中**<font style="color:#F5222D;">记下两个地址</font>**(一定要是跳转之后的地址,对于上图来说是jnz之后的地址)，如下图所示:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592452392687-5e2ac77e-ea47-4f9f-a030-7f22d45cfbec.png)

按F5可以看下伪代码:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592452114970-0e5fe16b-7310-4d21-ab56-da2d2affd070.png)

进入函数sub_4006FD,如下图所示

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592452468073-d37f8e45-96fc-4c2c-9e6c-bc950f88e382.png)

在上图中可以看出这里程序在for循环中对输入的a1进行了求解变换，但是这些对angr都不重要，无论中间过程如何变幻，甚至上了虚拟机保护，我们只知道程序执行的正确(Nice)路径就可以了.

> **<font style="color:#F5222D;">angr是看重程序执行路径的符号执行工具</font>**
>

开始写angr脚本：（和上一节的脚本几乎一模一样,可以参照前一节的内容）

```python
import angr #导入angr

proj = angr.Project('./r100') #加载二进制文件
state = proj.factory.entry_state() #创建状态，默认就是程序的入口地址，也可以指定一个地址作为入口地址
sm = proj.factory.simulation_manager(state) #创建模拟器用来模拟程序执行
res=sm.explore(find=0x400844, avoid=0x400855)#使用explore执行模拟器，find和avoid用来作为约束条件。
if len(res.found) >0:
	print (sm.found[0].posix.dumps(0))#打印found的第一个结果
```

> res=sm.explore(find=0x400844, avoid=0x400855)就是上面提到过的两个地址
>

保存为solve.py，执行代码：

```bash
(angr) ubuntu@ubuntu:~/Desktop/angr$ python solve.py
b'Code_Talkers\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xb5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xb5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xd5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf1\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\x00'
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

flag：Code_Talkers

普通的解法：

```c
#include<stdio.h>
int main(){
    char v3[]={"DufhbmfpG`imosewUglpt"};
    char flag[]="";
    for(int i = 0; i <= 11; ++i ){
        printf("%c",(v3[(i % 3)*7+2 * (i / 3)]-1));
    }
    return 0;
}
```

其中注意一下printf("%c",(v3[(i % 3)*7+2 * (i / 3)]-1));就可以了

