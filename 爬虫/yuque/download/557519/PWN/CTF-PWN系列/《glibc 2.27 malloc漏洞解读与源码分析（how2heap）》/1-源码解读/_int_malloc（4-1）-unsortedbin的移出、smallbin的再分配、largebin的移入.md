# 前言
到这里，我们已经研究了一半的_int_malloc源码，但是后半部分的源码更重要也更复杂，所以还是按照之前的调试方法一步一步的进行调试，然后再画图进行分析理解。

# 关键词
unsortedbin的移出、smallbin的再分配、largebin的移入

# 研究对象
后半部分的_int_malloc源码中的while循环

# 一个例子
> 注意：以下例子只能覆盖到大部分源码，但仍有一些源码没有牵扯到，这部分源码会在之后的篇幅中进行讲解。
>

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(){ 
    void *p1 = malloc(0x420);
    void *q1 = malloc(0x20);
    void *p2 = malloc(0x500);
    void *q2 = malloc(0x20);
    void *p3 = malloc(0x500);
    void *q3 = malloc(0x20);
 
    free(p1);
    free(p2);
 
    void* p4 = malloc(0x90);
    free(p3);
 
    void *p5 = malloc(0x90);	
    void *p6 = malloc(0x1000);
    void *p7 = malloc(0x30);
    void *p8 = malloc(0x40);
    void *p9 = malloc(0x3f0);
    void *p10 = malloc(0x500);
    return 0;
}
```

> 编译命令：gcc -g largebin.c -o largebin
>

# 开始调试
## 第一次while循环
> 在调试之前请先关闭系统的地址随机化
>

首先对源码的第15行下断点，然后开始调试，看一下bin的状况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616226169485-5c9a2083-da31-4b92-9ad6-f508fc64b029.png)

这里不用管为什么会产生这样的堆布局，因为内存的释放是_int_free的事情，之后我们会单独的研究free源码。

在引入glibc源码之后单步步入第15行的malloc，然后来到_int_malloc函数中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616226502741-e812ea41-fe5b-40dc-8e65-0e83df645493.png)

由于此时的bin中tcachebin、fastbin和smallbin没有free chunk，因此最终会来到此处：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616226625058-76456d15-b608-4faa-b01f-574126ea1c6d.png)

这里是我们要开始调试的起始站，看一下开头的代码：

```c
#if USE_TCACHE
  INTERNAL_SIZE_T tcache_nb = 0;
  size_t tc_idx = csize2tidx (nb);        //nb==0xa0
  if (tcache && tc_idx < mp_.tcache_bins) //若tcache已经初始化并且nb在tcache的范围内
    tcache_nb = nb;                       //将nb赋值给tcache_nb
  int return_cached = 0; 
  tcache_unsorted_count = 0;              //后两个变量的含义我们稍后再说
#endif
```

上面的注释已经写的很明显了，继续单步调试会到很头疼的地方：

```c
  for (;; )
    {    
		......
    }
```

上面的for循环是一个超大循环，它的范围是从此处一直到_int_malloc源码结尾，看得出来这是一个很大的外层循环，其中在for循环的开头又套着一个while循环：

```c
int iters = 0;
      while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av))
        {  
          ......
#define MAX_ITERS       10000
          if (++iters >= MAX_ITERS)
            break;
        }
```

同样的，里层的while循环也是十分的大，但是代码量是外层for循环的一半左右，引人注意的是while循环中的判断条件：

```c
(victim = unsorted_chunks (av)->bk) != unsorted_chunks (av)
```

先来进入while循环再来看结果吧：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616228685997-2e1382c1-e2d9-4452-8206-390ecb82e465.png)

> unsorted_chunks (av)->bk的执行结果为victim
>

现在main_arena的状况如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616228804448-dd35bee3-f03d-4d10-9036-2468ca613c18.png)

为了进一步说明这个语句的意思，需要看一下汇编：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616229036692-3221f861-35e8-4679-95a1-c24ce0704c69.png)

第一个红箭头是victim的值（即unsorted_chunks (av)->bk的执行结果），第二个（R13寄存器）是unsorted_chunks (av)的结果，然后通过比较R13和RAX寄存器的值来实现跳转。

```c
pwndbg> x/20gx &main_arena
0x7ffff7dcdc40 <main_arena>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdc50 <main_arena+16>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdc60 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdc70 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdc80 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdc90 <main_arena+80>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdca0 <main_arena+96>:	0x0000555555757130	0x0000000000000000
    							#top_chunk
         <unsorted_chunks (av)>:	0x00005555557566b0	0x0000555555756250
    													#victim
0x7ffff7dcdcc0 <main_arena+128>:	0x00007ffff7dcdcb0	0x00007ffff7dcdcb0
0x7ffff7dcdcd0 <main_arena+144>:	0x00007ffff7dcdcc0	0x00007ffff7dcdcc0
pwndbg> 
```

+ unsorted_chunks (av)：取得unsortedbin在main_arena中的指针（结果为0x7ffff7dcdca0）
+ unsorted_chunks (av)->bk：可以这样理解，将0x7ffff7dcdca0当作堆块，获取它的bk指针的值

更进一步讲，while循环中判断的意思是：获取unsortedbin中是否有已经存在的free chunk，如果有则进入while循环。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616229968454-e11bab0f-eca0-485e-9793-3b60cf8f4d64.png)

> 注意：unsortedbin是FIFO（first in first out 先入先出）
>

继续调试：

```c
          bck = victim->bk;
```

很简单，这条语句是获得victim的bk指针：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616230106255-ba351cb0-3276-4d2d-a356-10d436bc2852.png)

注意：victim的bk指针是指向unsortedbin中另外一个free chunk的。

```c
          if (__builtin_expect (chunksize_nomask (victim) <= 2 * SIZE_SZ, 0)
              || __builtin_expect (chunksize_nomask (victim)
				   > av->system_mem, 0))
            malloc_printerr ("malloc(): memory corruption");
```

这个if语句有点复杂，可以分为两个部分：

+ __builtin_expect (chunksize_nomask (victim) <= 2 * SIZE_SZ, 0) 
+ __builtin_expect (chunksize_nomask (victim) > av->system_mem, 0)

先来看第二条语句的av->system_mem：

```c
pwndbg> p *av
$13 = {
  mutex = 0, 
  flags = 0, 
  have_fastchunks = 0, 
  fastbinsY = {0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}, 
  top = 0x555555757130, 
  last_remainder = 0x0, 
  bins = {0x5555557566b0, 0x555555756250, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0d0 <main_arena+1168>, 0x7ffff7dce0d0 <main_arena+1168>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2d0 <main_arena+1680>, 0x7ffff7dce2d0 <main_arena+1680>...}, 
  binmap = {0, 0, 0, 0}, 
  next = 0x7ffff7dcdc40 <main_arena>, 
  next_free = 0x0, 
  attached_threads = 1, 
  system_mem = 135168, 
  max_system_mem = 135168
}
pwndbg> 
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616230795686-bb66be69-8ad3-4131-8903-a1bf50641f5a.png)

ststem_mem在这里进行定义，其值有后续代码进行初始化（这里暂时忽略初始化的过程）。这个值的含义是“系统为该arena（这里指main_arena）分配的内存大小”，这个大小本质上是heap区的大小：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616231217944-0b1d4250-0fd8-4355-95f2-c58cefbecd28.png)

> 135168==0x21000
>

+ __builtin_expect (chunksize_nomask (victim) <= 2 * SIZE_SZ, 0) 

//victim的大小不能小于等于2 * SIZE_SZ（堆块不可能小于2*SIZE_SZ，除非被篡改）

+ __builtin_expect (chunksize_nomask (victim) > av->system_mem, 0)

//victim的大小不能超过现在堆区的大小。

两个条件必须同时满足才可以继续执行下面的代码：

```c
          size = chunksize (victim);  //chunksize获取某个chunk的大小（大小不包括3个标志位）
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616232722015-1be6c8ff-3338-443a-befa-e9b2e83c2eb6.png)

size是堆块victim的大小。

```c
          if (in_smallbin_range (nb) && 
              bck == unsorted_chunks (av) &&  
              victim == av->last_remainder &&  
              (unsigned long) (size) > (unsigned long) (nb + MINSIZE))
            {
```

又是一个判断，一个一个条件来看：

+ if (in_smallbin_range (nb)  //判断要申请的chunk大小是否在smallbin的范围内
+ bck == unsorted_chunks (av)  

//由于bck会指向unsortedbin中的另外一个free chunk，因此这条语句的含义是判断unsortedbin中是否只有一个chunk。

+ victim == av->last_remainder //判断victim是否是last_remainder
+ (unsigned long) (size) > (unsigned long) (nb + MINSIZE)  //判断victim的大小是否满足要申请堆块的大小。

> last_remainder的含义之后会说
>

```c
          if (in_smallbin_range (nb) &&  //True：在smallbin的范围内
              bck == unsorted_chunks (av) &&  //False：除了victim还有另外的堆块
              victim == av->last_remainder &&  //False：这里的victim不是last_remainder
              (unsigned long) (size) > (unsigned long) (nb + MINSIZE)) //True：此堆块可以满足要求
            {
```

因此程序不会进入此if语句，从而会执行接下来的：

```c
          /* remove from unsorted list */  
          unsorted_chunks (av)->bk = bck;  
          bck->fd = unsorted_chunks (av);
```

这两条语句的功能已经在注释中写出了：将某个free chunk从unsortedbin链表中移除。来看一下移除之后的bin情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616309009478-36bd3e8a-283f-4da9-941c-cc5bc2632c45.png)

> 这里可以看出unsortedbin是FIFO（先入先出）的特性。
>

现在0x555555756250堆块（victim）已经被从unsortedbin list中移除，接下来又是一个if分支：

```c
          /* Take now instead of binning if exact fit */

		if (size == nb) //size==1072,nb==160
            {
              set_inuse_bit_at_offset (victim, size);
				......
              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim);
              alloc_perturb (p, bytes);
              return p; //返回victim
            }
```

victim的大小与nb很明显不相同，但是现在我们要思考一下为什么要存在这一个机制：

我们可以在这个if语句中搜寻到一些线索，注意到if的末尾有一个return语句，这个语句是返回从bin中摘除下来的victim指针的；所以如果unsortedbin中victim大小和nb相同，malloc会直接返回此堆块，避免内存空间的碎片化。

由于此时的unsortedbin free chunk（victim）不符合nb不能直接返回，接下来会尝试将从unsortedbin中取下来的victim插入smallbin或largebin中（对内存碎片再次整理）：

```c
          /* place chunk in bin */
                       
          if (in_smallbin_range (size))   //size==0x430
            {
				......  //放入smallbin
            }
          else
            { 
              victim_index = largebin_index (size);
              ......	//放入largebin
            }
```

在这个程序的情况下，malloc会将victim将会放入largebin中：

```c
          else
            {  //不在smallbin范围内，准备放入largebin中
              victim_index = largebin_index (size);  //获取largebin index->victim_index==64
              bck = bin_at (av, victim_index);  
              fwd = bck->fd;
```

和之间放入其他chunk的步骤相同，首先获取victim_size在largebin中的index，然后执行下面两条语句，结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616311121134-e9a8a1a9-de2d-496e-855f-27cd16b48e2b.png)

可以这样理解这两条语句：

```c
pwndbg> x/16gx 0x7ffff7dce090-0x10
0x7ffff7dce080 <main_arena+1088>:	0x00007ffff7dce070	0x00007ffff7dce070
bck指针指向此处 <将此处当作一个堆块>:	  0x00007ffff7dce080  0x00007ffff7dce080
0x7ffff7dce0a0 <main_arena+1120>:	0x00007ffff7dce090	0x00007ffff7dce090
    								#bck->fd（fwd）	   #bk
0x7ffff7dce0b0 <main_arena+1136>:	0x00007ffff7dce0a0	0x00007ffff7dce0a0
0x7ffff7dce0c0 <main_arena+1152>:	0x00007ffff7dce0b0	0x00007ffff7dce0b0
0x7ffff7dce0d0 <main_arena+1168>:	0x00007ffff7dce0c0	0x00007ffff7dce0c0
0x7ffff7dce0e0 <main_arena+1184>:	0x00007ffff7dce0d0	0x00007ffff7dce0d0
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
pwndbg> 
```

bin_at函数获取了victim对应的largebin在main_arena指针，然后让bck指向此处；我们可以将0x7ffff7dce090开始当作一个chunk，那么这个chunk的fd指针就是bck->fd。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616311528543-e9e85f32-d3b3-4757-af75-5fd1a95bfe30.png)

下面代码是插入largebin的过程，在这个过程中要注意largebin和之前的bin都不太相同，除了多了fd_nextsize和bk_nextsize这两个指针外，还有largebin与其他bin的机制不相同，简单的来说：

+ largebin的每一条链上的大小不一定相同
+ largebin的每一条链表上的free chunk是从大到小（在pwndbg的largebin命令执行后从左向右看）进行排序的。

```c
              /* maintain large bins in sorted order */
			  //确保largebin的free chunk按照顺序放置
              if (fwd != bck) //判断放入之前largebin是否为空
                {	//largebin不为空，需要按照一定规则进行插入
                  ......
                }
              else  //largebin为空，直接插入对应大小的链表中
                victim->fd_nextsize = victim->bk_nextsize = victim; 
```

```c
pwndbg> x/140gx 0x555555756250
0x555555756250:	0x0000000000000000	0x0000000000000431 #victim
0x555555756260:	0x00007ffff7dcdca0	0x00005555557566b0 //这里的fd和bk指针不用管，因为victim已经与unsortedbin没关系了
    			#fd					#bk                //victim被取下后它的fd和bk并没有置NULL
0x555555756270:	0x0000000000000000	0x0000000000000000
......
0x555555756680:	0x0000000000000430	0x0000000000000030
......
pwndbg> 
```

由于对应大小的largebin链表为空，现在会执行else语句，将victim直接插入对应的largebin链表中：<font style="background-color:#FADB14;"></font>

```c
victim->fd_nextsize = victim->bk_nextsize = victim;   //设置victim堆块的fd_nextsize和bk_nextsize
```

为了更清楚的看到结果，在这里将此语句进行拆分，首先执行victim->bk_nextsize = victim：

```c
pwndbg> x/140gx 0x555555756250
0x555555756250:	0x0000000000000000	0x0000000000000431 #victim
0x555555756260:	0x00007ffff7dcdca0	0x00005555557566b0
    			#fd					#bk
0x555555756270:	0x0000000000000000	0x0000555555756250
    			#fd_nextsize		#bk_nextsize
......
0x555555756680:	0x0000000000000430	0x0000000000000030
......
pwndbg> 
```

然后执行：victim->fd_nextsize = victim->bk_nextsize

```c
pwndbg> x/140gx 0x555555756250
0x555555756250:	0x0000000000000000	0x0000000000000431 #victim
0x555555756260:	0x00007ffff7dcdca0	0x00005555557566b0
    			#fd					#bk
0x555555756270:	0x0000555555756250	0x0000555555756250
    			#fd_nextsize		#bk_nextsize
......
0x555555756680:	0x0000000000000430	0x0000000000000030
......
pwndbg> 
```

> 注意：地址0x555555756680所在的这一行中的数据0x430和0x30在victim进入unsortedbin时设置
>

```c
          mark_bin (av, victim_index);
```

mark_bin的定义如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616313252682-6c5cc14c-edec-4d5f-8444-8ec3478269d4.png)

这个定义似乎有点复杂，直接来看一下结果吧：

```c
pwndbg> p *av
$28 = {
  mutex = 0, 
  flags = 0, 
  have_fastchunks = 0, 
  fastbinsY = {0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}, 
  top = 0x555555757130, 
  last_remainder = 0x0, 
  bins = {0x5555557566b0, 0x5555557566b0, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0d0 <main_arena+1168>, 0x7ffff7dce0d0 <main_arena+1168>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2d0 <main_arena+1680>, 0x7ffff7dce2d0 <main_arena+1680>...}, 
  binmap = {0, 0, 0, 0},   //执行后binmap = {0, 0, 1, 0}, 
  next = 0x7ffff7dcdc40 <main_arena>, 
  next_free = 0x0, 
  attached_threads = 1, 
  system_mem = 135168, 
  max_system_mem = 135168
}
pwndbg> 
```

注意上面av中的binmap发生了变化，关于binmap的注释如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616313614249-af59200f-2555-4bc9-b1bd-831b4807ce41.png)

> 为了补偿由于bins的巨大数目（128个）所产生的时间开销，我们使用一种一级索引结构来进行对bin之间的搜索。这种结构被称为binmap，它是一种记录bins中的bin是否为空的位向量。如此一来，我们便可以在遍历bin时跳过空bin。当一个bin变成空bin时，binmap并不会立刻清空。当我们下一次调用malloc，对bin遍历时才会清空那些被注意到为空的bin所对应的位。
>

为了更清楚的理解binmap的工作流程，在这里先不研究，等待程序再次设置binmap时我们再进行研究。之前我们已经将victim的fd_nextsize和bk_nextsize这两个指针已经设置好，接下来程序会对victim的fd和bk指针进行设置，执行下列步骤：

```c
          victim->bk = bck;
          victim->fd = fwd;
```

执行之后的效果如下：

```c
pwndbg> x/140gx 0x555555756250
0x555555756250:	0x0000000000000000	0x0000000000000431
0x555555756260:	0x00007ffff7dcdca0	0x00007ffff7dce090
    								#victim->bk = bck;
0x555555756270:	0x0000555555756250	0x0000555555756250
......
0x555555756680:	0x0000000000000430	0x0000000000000030
0x555555756690:	0x0000000000000000	0x0000000000000000
0x5555557566a0:	0x0000000000000000	0x0000000000000000
pwndbg> x/140gx 0x555555756250
0x555555756250:	0x0000000000000000	0x0000000000000431
0x555555756260:	0x00007ffff7dce090	0x00007ffff7dce090
    			#victim->fd = fwd;	
0x555555756270:	0x0000555555756250	0x0000555555756250
......
0x555555756680:	0x0000000000000430	0x0000000000000030
0x555555756690:	0x0000000000000000	0x0000000000000000
0x5555557566a0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

victim的指针已经全部设置完成，接下来该设置main_arena的指针了：

```c
          fwd->bk = victim;
          bck->fd = victim;
```

结果如下代码框所示：

```c
pwndbg> x/16gx 0x7ffff7dce090-0x10
0x7ffff7dce080 <main_arena+1088>:	0x00007ffff7dce070	0x00007ffff7dce070
0x7ffff7dce090 <main_arena+1104>:	0x00007ffff7dce080	0x00007ffff7dce080
0x7ffff7dce0a0 <main_arena+1120>:	0x00007ffff7dce090	0x0000555555756250
    													#fwd->bk = victim
0x7ffff7dce0b0 <main_arena+1136>:	0x00007ffff7dce0a0	0x00007ffff7dce0a0
0x7ffff7dce0c0 <main_arena+1152>:	0x00007ffff7dce0b0	0x00007ffff7dce0b0
0x7ffff7dce0d0 <main_arena+1168>:	0x00007ffff7dce0c0	0x00007ffff7dce0c0
0x7ffff7dce0e0 <main_arena+1184>:	0x00007ffff7dce0d0	0x00007ffff7dce0d0
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
pwndbg> x/16gx 0x7ffff7dce090-0x10
0x7ffff7dce080 <main_arena+1088>:	0x00007ffff7dce070	0x00007ffff7dce070
0x7ffff7dce090 <main_arena+1104>:	0x00007ffff7dce080	0x00007ffff7dce080
0x7ffff7dce0a0 <main_arena+1120>:	0x0000555555756250	0x0000555555756250
    								#bck->fd = victim
0x7ffff7dce0b0 <main_arena+1136>:	0x00007ffff7dce0a0	0x00007ffff7dce0a0
0x7ffff7dce0c0 <main_arena+1152>:	0x00007ffff7dce0b0	0x00007ffff7dce0b0
0x7ffff7dce0d0 <main_arena+1168>:	0x00007ffff7dce0c0	0x00007ffff7dce0c0
0x7ffff7dce0e0 <main_arena+1184>:	0x00007ffff7dce0d0	0x00007ffff7dce0d0
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
pwndbg> 
```

对victim的四个指针和main_arena的指针设置完成之后victim才算是被放到了（链接到了）largebin中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616333293366-87ed5e78-8c3e-45a4-a4ac-f124084f5a3d.png)

接下来又是一段if语句：

```c
#if USE_TCACHE
      /* If we've processed as many chunks as we're allowed while
	 filling the cache, return one of the cached ones.  */
      ++tcache_unsorted_count;
      if (return_cached
	  && mp_.tcache_unsorted_limit > 0
	  && tcache_unsorted_count > mp_.tcache_unsorted_limit)
	{
	  return tcache_get (tc_idx);
	}
#endif
```

当然，进入这个if语句和之前的一段代码有关系，我们将这个代码单独摘出来说一下：

```c
	      if (tcache_nb //tcache_nb在之前赋值：tcache_nb==nb
		  && tcache->counts[tc_idx] < mp_.tcache_count) 
		{
		  tcache_put (victim, tc_idx);
		  return_cached = 1;  //注意：只有这里会对return_cached的值赋1
		  continue;    //跳出本次while循环，继续执行下一次的while循环
		}
	      else  
		{
#endif
              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim);
              alloc_perturb (p, bytes);
              return p;  //返回vicim
#if USE_TCACHE
		}
```

首先来看上面代码框的if语句，tcache_nb这个值是在进入for循环之前初始化的，当时初始化的条件是tcachebin已经初始化并且nb在tcachebin的范围中；在这里如果不想进入else分支执行代码除了要满足前面的条件之外还要要求对应的tcachebin链表未满，然后将victim放入tcachebin中并且让return_cached赋值为1；否则直接进入else分支直接返回victim；

**<font style="color:#F5222D;">简单的总结一下：在循环处理unsortedbin链上的某个chunk（这个chunk名叫victim），当victim_size和nb相同且条件都满足时，我们并不会直接返回(return)，而是将victim放到tcachebin中跳出本次循环继续处理其他unsorted free chunk。</font>****<font style="color:#F5222D;">因此我们大致可以知道：变量</font>****<font style="color:#F5222D;">return_cached代表着是从unsortedbin是否有free chunk移动到tcachebin中，其值只有1（有）或0（没有）。</font>****<font style="color:#F5222D;"></font>**

知道这些后我们还需要看这两个变量：mp_.tcache_unsorted_limit和tcache_unsorted_count；首先来看前者的定义：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616380918725-fd67676f-e06a-49a4-af53-d150c0fddd2c.png)

根据代码的上下文可以知道，当前面的条件都满足无法使程序直接return时，每遍历一次unsortedbin就会使tcache_unsorted_count++： **<font style="color:#F5222D;"></font>**

```c
#if USE_TCACHE
      /* If we've processed as many chunks as we're allowed while
	 filling the cache, return one of the cached ones.  */
      ++tcache_unsorted_count; //现在tcache_unsorted_count==1
      if (return_cached   //在现在调试的程序中，没有free chunk移动到从unsortedbintcachebin中，其真值为false
	  && mp_.tcache_unsorted_limit > 0  //---->tcache_unsorted_limit默认为0
	  && tcache_unsorted_count > mp_.tcache_unsorted_limit) //true
	{
	  return tcache_get (tc_idx);  //返回从tcache中得到堆块
	}
#endif
```

源码的注释中写有：在执行前面的代码之后如果我们有victim放入到了tcachebin中，会在这里直接返回一个放入tcache中的free chunk（这个chunk是victim）。mp_.tcache_unsorted_limit中的limit是限制的意思，进一步说：mp_.tcache_unsorted_limit这个参数的值会限制tcache从unsortedbin中获取chunk的数量，当取0时，不做限制，因此一般情况下，不会执行上述代码。

最后来到while循环的末尾：

```c
#define MAX_ITERS       10000
          if (++iters >= MAX_ITERS) //iters代表while循环的次数，当达到最大循环次数（10000次）时会跳出循环
            break;
```

最终，第一次循环的结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616382680546-3a45b86b-5813-443c-ae15-8657b19aa593.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616383719095-665923b6-371c-40d2-bc28-24f231667816.png)

## 第二次while循环
> 在以下的内容中之前提到过的代码会简略说明，没有提到的则会详细说明。
>

```c
      while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av)) 
          //获取unsortedbin中是否有free chunk，有则进入while循环。
```

现在的victim的状态如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616383386663-5f085dd7-f958-4697-a734-825afb9362c3.png)

现在还有一个unsortedbin中还有一个free chunk，进入while循环：

```c
		//若unsortedbin不为空（注意unsortedbin是first in first out） 
          bck = victim->bk;  //bck指向main_arena而不是unsortedbin chunk。
          if (__builtin_expect (chunksize_nomask (victim) <= 2 * SIZE_SZ, 0) //判断victim是否满足要求
              || __builtin_expect (chunksize_nomask (victim)  //victim不能过小，也不能过大
				   > av->system_mem, 0))
            malloc_printerr ("malloc(): memory corruption");
          size = chunksize (victim);   //victim size对齐
```

由于现在unsortedbin中只有一个free chunk，因此bck会指向main_arena而不是另一个unsortedbin chunk：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616383775060-7cf330bb-6920-4225-b653-2ce0f5b4f6ed.png)

> 由于在第一次while循环并没有返回，因此nb未改变。
>

```c
          if (in_smallbin_range (nb) &&       //判断nb是否在smallbin的范围内（True）
              bck == unsorted_chunks (av) &&  //这里判断unsortedbin中是否只有一个free chunk（True）
              victim == av->last_remainder && //判断victim是否是last_ramainder（False）
              (unsigned long) (size) > (unsigned long) (nb + MINSIZE))
            {
```

因为victim!=last_remainder所以不会进入if语句，现在将victim从unsortedbin链表中移除：

```c
          /* remove from unsorted list */
          unsorted_chunks (av)->bk = bck;
          bck->fd = unsorted_chunks (av);
```

移除完成之后，效果如下：![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616397722697-1cb1c1c1-d7a8-4c51-a0e1-c9af978f3fb5.png)

```c
          if (size == nb) //size==1296；nb==160
            {
				......
            }
```

无法进入上述if，程序将继续向下执行，再经过判断后这里会将victim链入到largebin中：

```c
          /* place chunk in bin */

          if (in_smallbin_range (size)) //size(victim)==1296
            {
             	......
            }
          else
            { //进入largebin
              victim_index = largebin_index (size); //获取victim在largebin中对应的index，victim_index==68
              bck = bin_at (av, victim_index);	//获取在main_arena中的指针赋值给bck
              fwd = bck->fd;	//获取bck->fd
   				...... 	
            }
```

执行else中的前三行效果如下：

```c
pwndbg> x/16gx 0x7ffff7dce090-0x10
0x7ffff7dce080 <main_arena+1088>:	0x00007ffff7dce070	0x00007ffff7dce070
0x7ffff7dce090 <main_arena+1104>:	0x00007ffff7dce080	0x00007ffff7dce080
0x7ffff7dce0a0 <main_arena+1120>:	0x0000555555756250	0x0000555555756250
0x7ffff7dce0b0 <main_arena+1136>:	0x00007ffff7dce0a0	0x00007ffff7dce0a0
0x7ffff7dce0c0 <main_arena+1152>:	0x00007ffff7dce0b0	0x00007ffff7dce0b0
0x7ffff7dce0d0 < bck所指向的地方 >:	0x00007ffff7dce0c0	0x00007ffff7dce0c0 //bck==0x7ffff7dce0d0
0x7ffff7dce0e0 <main_arena+1184>:	0x00007ffff7dce0d0	0x00007ffff7dce0d0
    								#bck->fd（fwd）
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
pwndbg> 
```

继续向下调试，由于victim对应的largebin链表为空，执行else分支：

```c
              /* maintain large bins in sorted order */
              if (fwd != bck) //判断victim在largebin中的链表是否为空
                {	//不为空
					......
                }
              else
                victim->fd_nextsize = victim->bk_nextsize = victim;  //设置victim的fd_nextsize和bk_nextsize
```

```c
//victim->fd_nextsize = victim->bk_nextsize = victim执行后
pwndbg> x/16gx 0x5555557566b0
0x5555557566b0:	0x0000000000000000	0x0000000000000511
0x5555557566c0:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
0x5555557566d0:	0x00005555557566b0	0x00005555557566b0
    			#fd_nextsize		#bk_nextsize
0x5555557566e0:	0x0000000000000000	0x0000000000000000
0x5555557566f0:	0x0000000000000000	0x0000000000000000
0x555555756700:	0x0000000000000000	0x0000000000000000
0x555555756710:	0x0000000000000000	0x0000000000000000
0x555555756720:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

然后设置victim的bk、fd和main_arena，将victim链入到largebin中：

```c
          mark_bin (av, victim_index);
          victim->bk = bck;
          victim->fd = fwd;
          fwd->bk = victim;
          bck->fd = victim;
```

 结果如下：

```c
pwndbg> p *av
$47 = {
  mutex = 0, 
  flags = 0, 
  have_fastchunks = 0, 
  fastbinsY = {0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}, 
  top = 0x555555757130, 
  last_remainder = 0x0, 
  bins = {0x7ffff7dcdca0 <main_arena+96>, 0x7ffff7dcdca0 <main_arena+96>, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce080 <main_arena+1088>, 0x555555756250, 0x555555756250, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0c0 <main_arena+1152>, 0x5555557566b0, 0x5555557566b0, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2d0 <main_arena+1680>, 0x7ffff7dce2d0 <main_arena+1680>...}, 
  binmap = {0, 0, 17, 0},  //binmap--mark_bin(av, victim_index)
  next = 0x7ffff7dcdc40 <main_arena>, 
  next_free = 0x0, 
  attached_threads = 1, 
  system_mem = 135168, 
  max_system_mem = 135168
}
pwndbg> 
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616400066107-0e630abc-f98c-4558-b07b-a3cd8d12a721.png)

现在到while循环的尾声：

```c
#if USE_TCACHE
      /* If we've processed as many chunks as we're allowed while
	 filling the cache, return one of the cached ones.  */
      ++tcache_unsorted_count;
      if (return_cached  //现在return_cached==0，无法进入if
	  && mp_.tcache_unsorted_limit > 0 //tcache_unsorted_limit==0
	  && tcache_unsorted_count > mp_.tcache_unsorted_limit)
	{
	  return tcache_get (tc_idx);
	}
#endif

#define MAX_ITERS       10000
          if (++iters >= MAX_ITERS) 
            break;
        }
```

现在所有unsortedbin都进入了smallbin或largebin，while循环即将结束。

> 下一篇文章接着说。
>



