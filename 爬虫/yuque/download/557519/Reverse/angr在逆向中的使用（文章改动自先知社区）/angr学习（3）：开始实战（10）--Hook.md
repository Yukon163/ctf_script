<font style="color:#333333;">在逆向中，使用Hook来解决问题非常的常见</font><font style="color:#333333;">，</font>其实Hook也十分的简单，而且可以将复杂的问题简单化。

首先，什么是hook？简单点来说，如下图所示：

Hook，可以中文译为“挂钩”或者“钩子”，逆向开发中改变程序运行的一种技术。

在逆向开发中是指改变程序运行流程的技术，通过Hook可以让自己的代码运行在别人的程序中。需要了解其Hook原理，这样就能够对恶意代码攻击进行有效的防护。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592791767463-3dafce2a-c4fb-4932-afbe-08fb0c282e9f.png)

使用之前使用过的例子：defcamp_r100/r100

程序流程很简单，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592791930599-f28495e5-3cf3-4f54-9458-2323438cb6f8.png)

因为我们要学习的是hook，因此不使用原来angr的方法进行解题，首先先来看一下代码：

```python
import angr

project = angr.Project("r100", auto_load_libs=False)

@project.hook(0x400844)
def print_flag(state):
    print("FLAG SHOULD BE:", state.posix.dumps(0))
    project.terminate_execution()

project.execute()
```

官方文档的介绍如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592792039467-246838f1-bb8e-4c75-9c36-eac9ba618a6f.png)

我们**<font style="color:#F5222D;">可以通过</font>**`**<font style="color:#F5222D;">@proj.hook(proj.entry)</font>**`**<font style="color:#F5222D;">的方式来Hook任意一个地址。</font>**

例子中使用了`project.execute()`方法，此方法并不常用，它往往和`project.terminate_execution()`结合起来使用，并且通常用在hook时，如下图所示

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592792383530-2249d6c9-714a-451b-84f1-0024f0d33821.png)

**<font style="color:#F5222D;">因此代码大概的执行流程如下：</font>**

1. **<font style="color:#F5222D;">初始化proj</font>**
2. **<font style="color:#F5222D;">hook指定地址的函数</font>**
3. **<font style="color:#F5222D;">调用</font>**`**<font style="color:#F5222D;">project.execute()</font>**`
4. **<font style="color:#F5222D;">当遇到</font>**`**<font style="color:#F5222D;">project.terminate_execution()</font>**`**<font style="color:#F5222D;">符号执行结束</font>**

此时angr会执行到`0x400844`并打印出flag的结果。

```python
import angr

project = angr.Project("r100", auto_load_libs=False)

@project.hook(0x400844)
def print_flag(state):
    print("FLAG SHOULD BE:", state.posix.dumps(0))
    project.terminate_execution()

project.execute()
```

其中`0x400844`的内容如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592792526942-097b59c0-3257-4c13-8127-9a07866dac8a.png)

执行angr日志如下：

```bash
ubuntu@ubuntu:~/Desktop/angr$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/angr$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/angr$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/angr$ python 1.py
FLAG SHOULD BE: b'Code_Talkers\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xb5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xb5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf1\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xb5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\xf5\x00'
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

flag{Code_Talkers}

