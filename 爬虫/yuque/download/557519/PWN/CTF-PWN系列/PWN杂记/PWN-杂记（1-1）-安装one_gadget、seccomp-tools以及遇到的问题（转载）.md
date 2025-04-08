> 转载自：[https://www.yuque.com/chenguangzhongdeyimoxiao/xx6p74/pn5v60](https://www.yuque.com/chenguangzhongdeyimoxiao/xx6p74/pn5v60)
>

**<font style="color:#F5222D;">这篇文章可以解决在Ubuntu 16.04 one_gadget安装完成之后运行时报错的问题，十分感谢这篇文章，感谢：</font>**

**<font style="color:#F5222D;">@Shura_phoenix 师傅：</font>**[https://www.yuque.com/chenguangzhongdeyimoxiao](https://www.yuque.com/chenguangzhongdeyimoxiao)



**最近做到了很多seccomp沙盒的题目，seccomp-tools对我们做题很有帮助，于是准备安装。**

****

# ubuntu安装命令
```python
sudo apt install gcc ruby-dev
sudo gem install seccomp-tools
```

照理来说是直接会成功的，而我却出现了很奇怪的问题，而且在网上找了很久也没有跟我类似的问题，最终自己还是解决了，记录一下过程~

# ERROR
首先报错如下，找了很久，大概错误我估计是因为**ruby版本的关系**

**可以先查看以下ruby版本**

```python
ruby --version
```

![](https://cdn.nlark.com/yuque/0/2020/png/408029/1596530991466-62b12002-69c1-4d09-b59a-6523b5eb52ac.png)

# 解决办法1
我的版本**之前是2.3**，我用尽了所有所有方法都不行，后面准备**升级到高版本**

```python
git clone https://github.com/postmodern/ruby-install
#然后执行以下命令，按理是可以直接升级到高版本的
ruby-install --latest
```

或者直接：

```python
ruby-install --latest ruby
```

以上方式我是不可以的，如果按照以上方式是不行的，请继续往下看

---

# 最终解决办法
首先**<font style="color:#4D4D4D;">添加 PPA 源：</font>**

```python
sudo add-apt-repository ppa:brightbox/ruby-ng
sudo apt-get update
```

然后删除旧的版本ruby

```python
sudo apt-get purge --auto-remove ruby
```

<font style="color:#4D4D4D;">然后</font>**<font style="color:#4D4D4D;">安装新版本(2.6）</font>**<font style="color:#4D4D4D;">：</font>

```python
sudo apt-get install ruby2.6 ruby2.6-dev
```

到此为止ruby应该是已经安装成功了

我们再次安装seccomp-tools

```python
sudo gem install seccomp-tools
```

我是已经安装成功了

![](https://cdn.nlark.com/yuque/0/2020/png/408029/1596533001957-22c77d4c-fb73-4fd3-908f-a4e23f8a3fd2.png)

使用一下工具，没有什么问题

![](https://cdn.nlark.com/yuque/0/2020/png/408029/1596530956802-c4d0cc2a-d7bd-40e0-a598-f4cd9b741f62.png)

！！！但是，**one_gadget用不了了**

![](https://cdn.nlark.com/yuque/0/2020/png/408029/1596532875544-dc033ed0-e1e4-4a1a-b13e-5638be95f0cc.png)

**ok,我们重装一下one_gadget！**

```python
sudo gem install one_gadget
```

![](https://cdn.nlark.com/yuque/0/2020/png/408029/1596532786565-a5a541af-ccf9-4410-9a04-30ceb39f77a4.png)

找一道题试一下，**可以用了！！！**

![](https://cdn.nlark.com/yuque/0/2020/png/408029/1596533071908-64d83f78-a185-4407-8833-adb08de32bf1.png)

**谢天谢地！！！**

---

**据说还可以rvm安装reby，但是看了下，挺麻烦的，就不试了**

