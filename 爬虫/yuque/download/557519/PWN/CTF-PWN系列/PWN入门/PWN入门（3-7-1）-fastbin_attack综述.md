> + 2024-08-17更新：本文在2020年编写时拷贝自CTF-Wiki，现已重新调整与完善文章内容并重新纠正原有错误。本文使用环境如下：
>
> ![](https://cdn.nlark.com/yuque/0/2024/png/574026/1723872226413-5cdfeff3-6acb-4340-bb2a-4c8e65047dd9.png)
>

## 介绍
fastbin attack 是指所有基于 fastbin 机制的漏洞利用方法。这类利用的前提是：

+ 存在堆溢出、use-after-free 等能控制 chunk 内容的漏洞
+ 漏洞发生于 fastbin 类型的 chunk 中

如果细分的话，可以做如下的分类：

+ Fastbin Double Free
+ House of Spirit
+ Alloc to Stack
+ Arbitrary Alloc

其中：

+ **<font style="color:#F5222D;">Fastbin Double Free 和 House of Spirit：这两个利用手法侧重于释放“正常由用户创建的chunk”和“由攻击者伪造的 chunk”，然后再次申请 chunk 进行攻击</font>**。
+ **<font style="color:#F5222D;">Alloc to Stack 和 Arbitrary Alloc：侧重于利用堆溢出等方式修改chunk的fd指针，即直接申请指定位置的chunk 进行攻击。</font>**

## 原理
**<font style="color:#DF2A3F;">若一个chunk被释放之后进入fastbin，那么</font>****<font style="color:#F5222D;">其相邻下一个堆块的 prev_inuse 标志位不会被清空。</font>**

> + PREV_INUSE（简写为P，位于chunk size字段的最低位）：
>
> 记录前一个 chunk 块是否处于分配状态。一般来说，**堆中第一个被分配的内存块的 size 字段的 P 位都会被设置为 1，**以便于防止访问前面的非法内存。当一个 chunk size 的 P 位为 0 时，我们能通过 prev_size 字段来获取上一个 chunk 的大小以及地址。这也方便进行空闲 chunk 之间的合并。
>

比如我们现在有如下C语言代码：

```c
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    void *chunk1,*chunk2,*chunk3;
    chunk1=malloc(0x30);	// 实际上申请得到的chunk size 为 0x41
    chunk2=malloc(0x30);
    chunk3=malloc(0x30);

	// free
    free(chunk1);
    free(chunk2);
    free(chunk3);
    return 0;
}
```

<font style="color:rgba(0, 0, 0, 0.87);">释放前：</font>

```c
pwndbg> x/30gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000041 <=== chunk1		# 0x41使用二进制可以表示为0b 0100 0001
0x602010:	0x0000000000000000	0x0000000000000000					# 最低位表示 PREV_INUSE
0x602020:	0x0000000000000000	0x0000000000000000
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000041 <=== chunk2
0x602050:	0x0000000000000000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
0x602080:	0x0000000000000000	0x0000000000000041 <=== chunk3
0x602090:	0x0000000000000000	0x0000000000000000
0x6020a0:	0x0000000000000000	0x0000000000000000
0x6020b0:	0x0000000000000000	0x0000000000000000
0x6020c0:	0x0000000000000000	0x0000000000020f41 <=== top chunk
0x6020d0:	0x0000000000000000	0x0000000000000000
0x6020e0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

执行三次free后可以看到chunk3 -> chunk2 -> chunk1构成了一个单链表：

```c
pwndbg> x/30gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000041 <=== chunk1
0x602010:	0x0000000000000000	0x0000000000000000
0x602020:	0x0000000000000000	0x0000000000000000
0x602030:	0x0000000000000000	0x0000000000000000
0x602040:	0x0000000000000000	0x0000000000000041 <=== chunk2
0x602050:	0x0000000000602000	0x0000000000000000
0x602060:	0x0000000000000000	0x0000000000000000
0x602070:	0x0000000000000000	0x0000000000000000
0x602080:	0x0000000000000000	0x0000000000000041 <=== chunk3
0x602090:	0x0000000000602040	0x0000000000000000
0x6020a0:	0x0000000000000000	0x0000000000000000
0x6020b0:	0x0000000000000000	0x0000000000000000
0x6020c0:	0x0000000000000000	0x0000000000020f41 <=== top chunk
0x6020d0:	0x0000000000000000	0x0000000000000000
0x6020e0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

额外的，main_arena 会记录着“最后进入fastbin的free chunk起始地址”，比如刚刚经过我们的释放就有：

```c
pwndbg> x/16gx &main_arena 
0x7ffff7dd1b20 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b30 <main_arena+16>:	0x0000000000000000	0x0000000000602080
                                                    # 指向最后被free的chunk -- chunk3
                                                    # chunk3 -> chunk2 -> chunk1
0x7ffff7dd1b40 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b50 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b60 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dd1b70 <main_arena+80>:	0x0000000000000000	0x00000000006020c0
                                                    # top chunk
0x7ffff7dd1b80 <main_arena+96>:	0x0000000000000000	0x00007ffff7dd1b78
0x7ffff7dd1b90 <main_arena+112>:	0x00007ffff7dd1b78	0x00007ffff7dd1b88
pwndbg> 
```

<font style="color:rgba(0, 0, 0, 0.87);">我们可以使用如下方式来表示这一点：</font>

```c
fastbins:
main_arena[size = 0x20] -> NULL
main_arena[size = 0x30] -> NULL
main_arena[size = 0x40] -> chunk3 -> chunk2 -> chunk1 -> NULL
main_arena[size = 0x50] -> NULL
main_arena[size = 0x60] -> NULL
main_arena[size = 0x70] -> NULL
main_arena[size = 0x80] -> NULL
```

