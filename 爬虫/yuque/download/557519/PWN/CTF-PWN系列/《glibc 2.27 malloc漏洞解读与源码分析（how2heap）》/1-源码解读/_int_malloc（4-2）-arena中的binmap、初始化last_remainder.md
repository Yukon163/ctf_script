> 接上一小节的内容我们继续调试。这一小节和下一小节的PPT解析在下一篇文章中，可以去那里下载。
>
> 由于个人精力有限,PPT的内容仅供参考,一切以文章内容为准!
>

# 开始调试
## 第三次while循环
在上一小节的末尾中iters并不大于MAX_ITERS，因此不会跳出循环而是执行下一次的循环。

```c
 while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av)) //判断unsortedbin是否为空
        {
     		......
 		}
```

现在unsortedbin链表中已经为空，不再会进入while循环，而是直接执行while循环之后的代码：

```c
#if USE_TCACHE
      /* If all the small chunks we found ended up cached, return one now.  */
      if (return_cached)  //现在return_cached==0
	{
	  return tcache_get (tc_idx);
	}
#endif
```

这个宏的意思是当执行while循环处理完unsortedbin中的free chunk之后，在此过程中如果之前有将free chunk放入tcachebin中，则会取出tcache chunk返回。在我们调试的这个程序中不会进入此if，继续向下执行：

```c
      /*
         If a large request, scan through the chunks of current bin in
         sorted order to find smallest that fits.  Use the skip list for this.
       */

      if (!in_smallbin_range (nb)) //nb==160==0xa0
        {	//nb是large chunk（大于0x3f0的chunk）
          ......
        }
```

这里判断nb是否在largebin的范围内，nb太小这里不会进入if语句，我们继续向下调试，来到：

```c
      /*
         Search for a chunk by scanning bins, starting with next largest
         bin. This search is strictly by best-fit; i.e., the smallest
         (with ties going to approximately the least recently used) chunk
         that fits is selected.

         The bitmap avoids needing to check that most blocks are nonempty.
         The particular case of skipping all bins during warm-up phases
         when no chunks have been returned yet is faster than it might look.
       */

      ++idx;   //执行后idx==11  //index可能由smallbin或largebin进行初始化
      bin = bin_at (av, idx);  //获取对应的main_arena指针
      block = idx2block (idx); 
      map = av->binmap[block];
      bit = idx2bit (idx);
```

> 下面的加密内容是一些疑问，不用看。。。。。。
>

[此处为语雀卡片，点击链接查看](https://www.yuque.com/cyberangel/rg9gdm/gwmpy5#U389Q)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616403642438-66329f1a-fc9a-4f2d-8cf4-fe58649bf91c.png)

> 现在的变量的值如上图所示
>

上面的代码牵扯到了binmap，再说之前来简单的说一下bin的一些宏定义：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616417038178-9a437fcc-cad5-4dce-b7c3-3440a7b6a644.png)

NBINS定义了bins的总个数：包括unsortedbin、smallbin、largebin<font style="color:#F5222D;">（</font>**<font style="color:#F5222D;">不包含tcachebin、fastbin）</font>**；bins指针数组在malloc_state中的定义如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616419205672-0f885696-634d-4245-a5ce-82d7aed52a38.png)

另外宏定义NSMALLBINS定义了smallbin的个数为64，我们可以根据源码可以分别计算出unsortedbin、smallbin、largebin中链表的数目：

| bins的分类 | 对应链表的个数 | 对应的bin数组 |
| --- | --- | --- |
| unsortedbin | 1 | bin[1] |
| smallbin | 62 | bin[2]~bin[63] |
| largebin | 63 | bin[64]~bin[126] |


> 注意：这里的数组是bin而不是bins，千万不要将bins和bin搞混；bin数组实际上并不存在，这是我们自己为了表达简单而创造的一个变量，在这里定义一条链表对应一个bin数组
>

这里可能有一些疑惑，我们来解答一下

Q：NBINS等于128，那bin数组不是应该为bin[0]~bin[127]吗？但是我在上述表格中没有发现bin[0]和bin[127]。

A：bin[0]和bin[127]实际上是没有启用(不存在)的，另外在注释中实际上提到过bin[0]：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616459176244-1e148444-24d4-4b48-b686-ea4038417149.png)

Q：NBINS的个数为128个，对应到源码中bins[NBINS*2-2]==bins[254]，bin和bins在内存中存在的形式是什么，应该怎样区分？

为了回答这一点，我们这儿给一个例子来说明：

```c
#include<stdio.h>
#include<stdlib.h>
int main(){
	malloc(0x10);
	return 0;
}
```

> 编译命令：gcc -g main_arena.c -o main_arena
>

引入源码之后进入malloc进行调试进入malloc函数之后对malloc_init_state下断点运行后单步到for循环：

> malloc_init_state在堆块初始化时进行调用。
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616471646974-41f2333d-3aa3-4fe9-a223-cb3f8d9c6cf9.png)

现在heap段还没有初始化，为了方便理解我们将此时汇编代码dump下来：

```c
pwndbg> disassemble 
Dump of assembler code for function ptmalloc_init:
   0x00007ffff7a734b0 <+0>:	push   rbx
   0x00007ffff7a734b1 <+1>:	sub    rsp,0x50
	......（省略与for循环无关的汇编代码）
｜-> 0x00007ffff7a73550 <+160>:	movdqa xmm0,xmm2   //for循环开始
｜   0x00007ffff7a73554 <+164>:	add    rax,0x40    //增加rax的值；增加前rax==0x7ffff7dcdc40
	......（省略一些不重要的代码）
｜   0x00007ffff7a735a5 <+245>:	movaps XMMWORD PTR [rax-0x40],xmm8 //写入到main_arena
｜   0x00007ffff7a735aa <+250>:	movaps XMMWORD PTR [rax-0x30],xmm1 //写入到main_arena
｜   0x00007ffff7a735ae <+254>:	movdqa xmm1,xmm0
｜   0x00007ffff7a735b2 <+258>:	punpcklqdq xmm1,xmm0
｜   0x00007ffff7a735b6 <+262>:	punpckhqdq xmm0,xmm0
｜   0x00007ffff7a735ba <+266>:	movaps XMMWORD PTR [rax-0x20],xmm1 //写入到main_arena
｜   0x00007ffff7a735be <+270>:	movaps XMMWORD PTR [rax-0x10],xmm0 //写入到main_arena
｜   0x00007ffff7a735c2 <+274>:	cmp    rax,rdx  //结束循环的条件：rax==rdx //rax==0x7ffff7dcdcb0 (main_arena+112)  rdx==0x7ffff7dce470 (main_arena+2096)
｜__ 0x00007ffff7a735c5 <+277>:	jne    0x7ffff7a73550 <ptmalloc_init+160>    //循环跳转
   ......(for循环之外的汇编)
End of assembler dump.
pwndbg> 
```

> 上面的一些汇编语言虽然牵扯到intel的SSE2指令集，但是我们完全可以忽略他们。
>
> 类似于xmm1这种的东西是寄存器。
>

虽然源代码中for循环的循环条件为i < NBINS(128)，但是在编译完成之后循环直到rax==0x7ffff7dce470(main_arena+2096)，虽然代码变了，但是本质是未发生改变的。汇编中的代码会循环31次，每次循环写入4次main_arena，一共写入了31*4==128次。我们摘取一个写入到main_arena的语句：

```c
在第一次循环中：
 ► 0x7ffff7a735a5 <ptmalloc_init.part+245>    movaps xmmword ptr [rax - 0x40], xmm8 <0x7ffff7dcdcb0>
```

此时xmm8的寄存器值取下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616482910928-fc20266e-d89b-4297-a9c9-a13d4b332616.png)

我们选取其中的 v2_int64 = {140737351834784, 140737351834784}，我们将其转为16进制：![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616483203406-a105a9e9-9df4-4c25-aa41-5ed9c7cc0584.png)

> ~~无意间秀了一下布洛妮娅和明日香的终端~~
>

movaps之后的main_arena如下：![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616483513153-224f4bfe-9329-4266-8b93-cd86ff7fd07e.png)

汇编循环之后的结果：

```c
pwndbg> x/300gx &main_arena 
0x7ffff7dcdc40 <main_arena>:	0x0000000000000000	0x0000000000000000
......(省略内容均为空)
0x7ffff7dcdca0 <main_arena+96>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdcb0 <main_arena+112>:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......(省略内容不重要内容)
0x7ffff7dce450 <main_arena+2064>:	0x00007ffff7dce440	0x00007ffff7dce440 #这是一行
0x7ffff7dce460 <main_arena+2080>:	0x00007ffff7dce450	0x00007ffff7dce450 #汇编循环赋值到此处结束
0x7ffff7dce470 <main_arena+2096>:	0x0000000000000000	0x0000000000000000 
0x7ffff7dce480 <main_arena+2112>:	0x0000000000000000	0x0000000000000000
0x7ffff7dce490 <main_arena+2128>:	0x0000000000000000	0x0000000000000000
0x7ffff7dce4a0 <main_arena+2144>:	0x0000000000000000	0x0000000000000000
0x7ffff7dce4b0 <main_arena+2160>:	0x00007ffff7dcdc40	0x0000000000000000
......(省略内容不重要内容)
0x7ffff7dce590 <_nl_global_locale+48>:	0x0000000000000000	0x00007ffff7dcb080
pwndbg> 

```

在汇编循环结束之后会继续对main_arena进行赋值：

```c
pwndbg> disassemble 
Dump of assembler code for function ptmalloc_init:
   0x00007ffff7a734b0 <+0>:	push   rbx
   0x00007ffff7a734b1 <+1>:	sub    rsp,0x50
	......
   0x00007ffff7a73550 <+160>:	movdqa xmm0,xmm2  //汇编循环开始
	......
   0x00007ffff7a735c5 <+277>:	jne    0x7ffff7a73550 <ptmalloc_init+160>  //汇编循环结束
	......
   0x00007ffff7a735fe <+334>:	movaps XMMWORD PTR [rip+0x35ae6b],xmm0        # 0x7ffff7dce470 <main_arena+2096>   //再次对main_arena进行赋值
   0x00007ffff7a73605 <+341>:	movq   xmm0,QWORD PTR [rsp+0x8]
   0x00007ffff7a7360b <+347>:	mov    QWORD PTR [rsp+0x8],rax
   0x00007ffff7a73610 <+352>:	punpcklqdq xmm0,xmm0
   0x00007ffff7a73614 <+356>:	lea    rax,[rcx-0x7c0]
   0x00007ffff7a7361b <+363>:	movaps XMMWORD PTR [rip+0x35ae5e],xmm0        # 0x7ffff7dce480 <main_arena+2112>   //再次对main_arena进行赋值
   0x00007ffff7a73622 <+370>:	movq   xmm0,QWORD PTR [rsp+0x8]
   0x00007ffff7a73628 <+376>:	punpcklqdq xmm0,xmm0
   0x00007ffff7a7362c <+380>:	movaps XMMWORD PTR [rip+0x35ae5d],xmm0        # 0x7ffff7dce490 <main_arena+2128>   //再次对main_arena进行赋值
   0x00007ffff7a73633 <+387>:	mov    DWORD PTR [rip+0x35a60b],0x0        # 0x7ffff7dcdc48 <main_arena+8>
=> 0x00007ffff7a7363d <+397>:	lea    rdx,[rip+0xfffffffffffff7ec]        # 0x7ffff7a72e30 <_dl_tunable_set_mallopt_check>
   0x00007ffff7a73644 <+404>:	mov    QWORD PTR [rip+0x35a655],rax        # 0x7ffff7dcdca0 <main_arena+96>
	......
   0x00007ffff7a73779 <+713>:	jmp    0x7ffff7a734ee <ptmalloc_init+62>
   0x00007ffff7a7377e <+718>:	call   0x7ffff7b16b10 <__stack_chk_fail>
End of assembler dump.
pwndbg> 
```

3次赋值之后：

```c
pwndbg> x/300gx &main_arena 
0x7ffff7dcdc40 <main_arena>:	0x0000000000000000	0x0000000000000000
......(省略内容均为空)
0x7ffff7dcdca0 <main_arena+96>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdcb0 <main_arena+112>:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......(省略内容不重要内容)
0x7ffff7dce450 <main_arena+2064>:	0x00007ffff7dce440	0x00007ffff7dce440 #这是一行
0x7ffff7dce460 <main_arena+2080>:	0x00007ffff7dce450	0x00007ffff7dce450 #汇编循环赋值到此处结束
0x7ffff7dce470 <main_arena+2096>:	0x00007ffff7dce460	0x00007ffff7dce460 #第一次赋值
0x7ffff7dce480 <main_arena+2112>:	0x00007ffff7dce470	0x00007ffff7dce470 #第二次赋值
0x7ffff7dce490 <main_arena+2128>:	0x00007ffff7dce480	0x00007ffff7dce480 #第三次赋值
0x7ffff7dce4a0 <main_arena+2144>:	0x0000000000000000	0x0000000000000000
0x7ffff7dce4b0 <main_arena+2160>:	0x00007ffff7dcdc40	0x0000000000000000
......(省略内容不重要内容)
0x7ffff7dce590 <_nl_global_locale+48>:	0x0000000000000000	0x00007ffff7dcb080
pwndbg> 

```

```c
	for (i = 1; i < NBINS; ++i)  //NBINS==128，for会循环127次
    {
      bin = bin_at (av, i);    //i==1,av==&main_arena
      bin->fd = bin->bk = bin;
    }
```

到这里应该看的很清楚了，这里稍稍的总结一下：

+ 一共需要向main_arena写入127行
+ 在源代码中循环一次（指for循环）会赋值一行，会循环127次；
+ 在编译优化后的汇编语句中循环一次赋值4行main_arena，一共循环31次，循环之后会对main_arena继续赋值，一共127次

> 可以看出在编译时的编译优化“-O2”命令看起来还是有用的，大大提高了代码执行的效率。
>

源码在赋值的时候使用bin_at(av,i)进行寻址，而bin_at的宏定义如下：

```c
#define bin_at(m, i) \
  (mbinptr) (((char *) &((m)->bins[((i) - 1) * 2]))	- offsetof (struct malloc_chunk, fd))  
```

因为在定义指针数组时bins定义为mchunkptr bins[NBINS * 2 - 2];（mchunkptr bins[254]）,所以宏定义bin_at可以看作是：

```c
#define bin_at(m, 1) \
  (mbinptr) (((char *) &((m)->bins[((1) - 1) * 2]))	- offsetof (struct malloc_chunk, fd))  ==  (mbinptr) (((char *) &((m)->bins[0])) - offsetof (struct malloc_chunk, fd))   
------------------------------------------------------------------------------------------------------
#define bin_at(m, 2) \
  (mbinptr) (((char *) &((m)->bins[((2) - 1) * 2]))	- offsetof (struct malloc_chunk, fd))  ==  (mbinptr) (((char *) &((m)->bins[2])) - offsetof (struct malloc_chunk, fd))   
------------------------------------------------------------------------------------------------------
#define bin_at(m, 127) \
  (mbinptr) (((char *) &((m)->bins[((127) - 1) * 2]))	- offsetof (struct malloc_chunk, fd))  ==  (mbinptr) (((char *) &((m)->bins[252])) - offsetof (struct malloc_chunk, fd))   
```

之前我们说过，我们“创造”出来的数组bin的范围是bin[0]~bin[127]（实际上有效范围是bin[1]~bin[126]），所以在内存的main_arena中表现形式为：

```c
pwndbg> x/300gx &main_arena
0x7ffff7dcdc40 <main_arena>:	0x0000000000000000	0x0000000000000000
......
0x7ffff7dcdca0 <main_arena+96>:	0x0000000000000000	0x0000000000000000	   #这一行代表bin[0](无效)
0x7ffff7dcdcb0 <main_arena+112>:	0x00007ffff7dcdca0	0x00007ffff7dcdca0 #......
    								#bins[0]			#bins[1]
0x7ffff7dcdcc0 <main_arena+128>:	0x00007ffff7dcdcb0	0x00007ffff7dcdcb0 #......
0x7ffff7dcdcd0 <main_arena+144>:	0x00007ffff7dcdcc0	0x00007ffff7dcdcc0 #......
0x7ffff7dcdce0 <main_arena+160>:	0x00007ffff7dcdcd0	0x00007ffff7dcdcd0 #......
......
0x7ffff7dce480 <main_arena+2112>:	0x00007ffff7dce470	0x00007ffff7dce470 #这一行代表bin[126]
0x7ffff7dce490 <main_arena+2128>:	0x00007ffff7dce480	0x00007ffff7dce480 #这一行代表bin[127](无效)
    								#bins[252]			#bins[253] //bins共254个
0x7ffff7dce4a0 <main_arena+2144>:	0x0000000000000000	0x0000000000000000
```

好了，现在第二个问题也回答完了。接下来继续研究源码。当程序走到这一步时，说明：

+ tcachebin中没有合适的free chunk
+ fastbin中没有合适的free chunk
+ smallbin中没有合适的free chunk
+ unsortedbin中找不到合适的块（不存在或者循环达到限制）
+ largebin中没有合适的块

这该怎么办呢？所有的bin中都没有合适的free chunk，不可能向top_chunk申请切割分配堆块吧，如果这样内存碎片化的程度大大增加。虽然没有大小“恰好合适”的free chunk，但是这时我们可以考虑放宽对于分配到的chunk的要求，仅仅要求其大小大于nb，同时又尽可能的小而不必恰好与之相等，因此可以**<font style="color:#F5222D;">遍历每一个bin</font>**，从中找出符合要求的chunk并对其进行切割后将余下的部分放入last remainder。接下来的代码就是实现我所说的：

```c
      ++idx;   //执行后idx==11
      bin = bin_at (av, idx);  //获取对应的main_arena指针
      block = idx2block (idx); //block==0
      map = av->binmap[block]; //map==0
      bit = idx2bit (idx);	//bit==2048
```

上面牵扯到的函数宏定义如下：

```c
/* Conservatively use 32 bits per map word, even if on 64bit system */
#define BINMAPSHIFT      5
#define BITSPERMAP       (1U << BINMAPSHIFT)
#define BINMAPSIZE       (NBINS / BITSPERMAP)

#define idx2block(i)     ((i) >> BINMAPSHIFT)
#define idx2bit(i)       ((1U << ((i) & ((1U << BINMAPSHIFT) - 1))))

#define mark_bin(m, i)    ((m)->binmap[idx2block (i)] |= idx2bit (i))
#define unmark_bin(m, i)  ((m)->binmap[idx2block (i)] &= ~(idx2bit (i)))
#define get_binmap(m, i)  ((m)->binmap[idx2block (i)] & idx2bit (i))
```

首先执行了idx++，idx是要申请堆块的大小nb在largebin的index，然后执行 bin = bin_at (av, idx)，这两步的目的是为了移动到下一个largebin链表。

> 因为当前的链表并不能满足，所以需要来查找比当前链表更大的largebin链表。
>

这里简单的介绍一下binmap：binmap是arena（分配区）中的一个成员，它用来标识相应的链表中是否存在free chunk，利用binmap可以加快查找chunk的速度。 这段代码用来查询比nb大的链表中是否存在可用的chunk。

> block为该idx对应链表binmap的位置，map为binmap[block]数组对应的值
>

现在的binmap状况如下所示：

```c
pwndbg> p av->binmap
$63 = {0, 0, 17, 0}
pwndbg> 
------------------------------------------------------------------------------------------------------
#binmap（注意小端序）
0x7ffff7dce4a0 <main_arena+2144>:	00000000000000000000000000000000 #binmap[0] 4byte==32bit
0x7ffff7dce4a4 <main_arena+2148>:   00000000000000000000000000000000 #binmap[1] 4byte==32bit
0x7ffff7dce4a8 <main_arena+2152>:   00000000000000000000000000010001 #binmap[2] 4byte==32bit  //十进制17，二进制10001
0x7ffff7dce4a8 <main_arena+2156>:   00000000000000000000000000000000 #binmap[3] 4byte==32bit
```

> 注意binmap的查看形式为二进制，每个binmap可以表示32个链表的状态，即1bit表示1条链；若此bit==1表示此链上有free chunk，反之则没有。
>

我们来仔细研究一下binmap的结构，binmap一共有128个bit，这里可以猜测128bit正好对应了前面所说的128个bin数组。我们来验证一下，首先导出此时的main_arena：

```c
0x7ffff7dcdca0 <main_arena+96>:	0x0000555555757130	0x0000000000000000     #bin[0]
0x7ffff7dcdcb0 <main_arena+112>:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......（省略了一些不重要的内容）
0x7ffff7dce090 <main_arena+1104>:	0x00007ffff7dce080	0x00007ffff7dce080
0x7ffff7dce0a0 <main_arena+1120>:	0x0000555555756250	0x0000555555756250 #bin[64]
0x7ffff7dce0b0 <main_arena+1136>:	0x00007ffff7dce0a0	0x00007ffff7dce0a0
0x7ffff7dce0c0 <main_arena+1152>:	0x00007ffff7dce0b0	0x00007ffff7dce0b0
0x7ffff7dce0d0 <main_arena+1168>:	0x00007ffff7dce0c0	0x00007ffff7dce0c0
0x7ffff7dce0e0 <main_arena+1184>:	0x00005555557566b0	0x00005555557566b0 #bin[68]
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
......（省略了一些不重要的内容）
0x7ffff7dce490 <main_arena+2128>:	0x00007ffff7dce480	0x00007ffff7dce480 #bin[127]
```

对照一下binmap（binmap在_int_malloc中定义为一个数组）：

```c
pwndbg> p av->binmap
$63 = {0, 0, 17, 0}
pwndbg> 
------------------------------------------------------------------------------------------------------
#binmap（注意小端序）                       
0x7ffff7dce4a0 <main_arena+2144>:	00000000000000000000000000000000 #binmap[0] 4byte==32bit
0x7ffff7dce4a4 <main_arena+2148>:   00000000000000000000000000000000 #binmap[1] 4byte==32bit
0x7ffff7dce4a8 <main_arena+2152>:   00000000000000000000000000010001 #binmap[2] 4byte==32bit  
                                                               ｜  ｜   //十进制17，二进制10001（原来的binmap是为{0, 0, 1, 0}）
                                                               ｜  ｜
                                                               ｜  ｜
                       ————————————————————————————————————————     ————————————————————————————————————————
                      ｜                                                                                    ｜
                      ｜                                                                                    ｜ 
         这一位为1，代表着对应的链表不为空                                                         这一位为1，代表着对应的链表不为空 
         对应着bin[68]                                                                        对应着bin[64] 
0x7ffff7dce4a8 <main_arena+2156>:   00000000000000000000000000000000 #binmap[3] 4byte==32bit
```

> 从上面可以得到一个结论：binmap和内存数据在此Linux版本（ubuntu）中都是使用小端序进行存储和读取。
>

开始进行下面的for循环：

```c
for (;; ) //无条件进入for，相当于while(1)
        {
          /* Skip rest of block if there are no more set bits in this block.  */
    	  // 如果bit>map，则表示该map中没有比当前所需要chunk大的空闲块
          // 如果bit为0，那么说明，上面idx2bit带入的参数idx==0。
          if (bit > map || bit == 0)  //bit==2048，map==0
            { 
              do
                { //进入内层的do...while循环
                  if (++block >= BINMAPSIZE) /* out of bins */  //计算可以得到宏BINMAPSIZE==4，注意:这里的block先++再比较
                    goto use_top;
                }
              while ((map = av->binmap[block]) == 0); //循环一次之后：block==1，av->binmap[1]

              bin = bin_at (av, (block << BINMAPSHIFT));
              bit = 1;
            }
			......（省略代码）
        }
```

首先我们要解决一个疑问，这里的bit值为什么在经过idx2bit计算后为2048，我们来看一下2048的二进制：

> 2048==00000000000000000000100000000000（这里以main_arena内存类似的形式呈现）
>

现在的map是为0的，也就是说当前binmap上没有空闲的chunk，因此在这里需要使用do...while循环遍历寻找：

>      0==00000000000000000000000000000000
>

总结：先确定bit的值，之后和map进行比较确定当前的block上是否有更大的空闲chunk，如果有则直接跳过if语句；如果此block上没有符合条件的free chunk，则遍历其他的block直到确定。

> idx2bit宏取第i位为1，剩下的置0，例如idx2bit(2)会生成“00000000000000000000000000000100”
>

```c
第一次循环后：
pwndbg> p block
$83 = 1
pwndbg> p av->binmap[block]
$84 = 0
pwndbg> 
----------------------------------------------------------------
第二次循环后：
pwndbg> p block
$87 = 2
pwndbg> p av->binmap[block]
$88 = 17
pwndbg> 
```

在第二次循环结束之后，在判断条件中会将av->binmap[block]赋值给map，此时map==17!=0，因此会结束此循环，这意味着发现了可以满足大小的chunk：

```c
pwndbg> p av->binmap
$63 = {0, 0, 17, 0}
pwndbg> 
------------------------------------------------------------------------------------------------------
#binmap（注意小端序）
0x7ffff7dce4a0 <main_arena+2144>:	00000000000000000000000000000000 #binmap[0] 4byte==32bit  //block==0(smallbin、unsortedbin)
0x7ffff7dce4a4 <main_arena+2148>:   00000000000000000000000000000000 #binmap[1] 4byte==32bit  //block==1(smallbin)
0x7ffff7dce4a8 <main_arena+2152>:   00000000000000000000000000010001 #binmap[2] 4byte==32bit  //block==2(largebin)
                                                               ｜  ｜
                                                               ｜  ｜
                                                               ｜  ｜
                       ————————————————————————————————————————     ————————————————————————————————————————
                      ｜                                                                                    ｜
                      ｜                                                                                    ｜ 
         这一位为1，代表着对应的链表不为空                                                         这一位为1，代表着对应的链表不为空 
         对应着bin[68]                                                                        对应着bin[64] 
0x7ffff7dce4a8 <main_arena+2156>:   00000000000000000000000000000000 #binmap[3] 4byte==32bit  //block==3(largebin)
```

在终止循环之后，会执行：

```c
              bin = bin_at (av, (block << BINMAPSHIFT));  //block==2，block<<BINMAPSHIFT==64
              bit = 1;
```

block << BINMAPSHIFT的结果正好对应链表不为空的bin[64]，这里获取链对应的指针bin，结果为

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616578267672-7a29bcb0-a5af-4fde-ab83-56e6bc1010bf.png)

```c
0x7ffff7dcdca0 <main_arena+96>:	0x0000555555757130	0x0000000000000000     #bin[0]
0x7ffff7dcdcb0 <main_arena+112>:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
......（省略了一些不重要的内容）
0x7ffff7dce090 <main_arena+1104>:	0x00007ffff7dce080	0x00007ffff7dce080 <--------bin指针指向此处
0x7ffff7dce0a0 <main_arena+1120>:	0x0000555555756250	0x0000555555756250 #bin[64]
0x7ffff7dce0b0 <main_arena+1136>:	0x00007ffff7dce0a0	0x00007ffff7dce0a0
0x7ffff7dce0c0 <main_arena+1152>:	0x00007ffff7dce0b0	0x00007ffff7dce0b0
0x7ffff7dce0d0 <main_arena+1168>:	0x00007ffff7dce0c0	0x00007ffff7dce0c0
0x7ffff7dce0e0 <main_arena+1184>:	0x00005555557566b0	0x00005555557566b0 #bin[68]
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
......（省略了一些不重要的内容）
0x7ffff7dce490 <main_arena+2128>:	0x00007ffff7dce480	0x00007ffff7dce480 #bin[127]
```

然后将bit置为1，继续执行下列代码：

```c
          /* Advance to bin with set bit. There must be one. */
          while ((bit & map) == 0)  //bit & map == 1 & 17 == 1
            {
              bin = next_bin (bin);
              bit <<= 1;
              assert (bit != 0);
            }
```

上述代码的意思很清楚，现在我们已经知道了block==2有满足的free chunk，但是不知道具体是哪条链上有free chunk，由于现在bin链上的第一个就是free chunk，因此会跳出循环。现在来举个例子：假如现在binmap的情况为{0, 0, 10, 0}：

```c
pwndbg> p av->binmap
$63 = {0, 0, 10, 0} //10对应的二进制为1010
pwndbg> 
------------------------------------------------------------------------------------------------------
#binmap（注意小端序）
0x7ffff7dce4a0 <main_arena+2144>:   00000000000000000000000000000000 #binmap[0] 4byte==32bit  //block==0(smallbin、unsortedbin)
0x7ffff7dce4a4 <main_arena+2148>:   00000000000000000000000000000000 #binmap[1] 4byte==32bit  //block==1(smallbin)
0x7ffff7dce4a8 <main_arena+2152>:   00000000000000000000000000001010 #binmap[2] 4byte==32bit  //block==2(largebin)
                                                                ｜ ｜
                                                                ｜ ｜
                                                                ｜ ｜
                       ————————————————————————————————————————     ————————————————————————————————————————
                      ｜                                                                                    ｜
                      ｜                                                                                    ｜ 
         这一位为1，代表着对应的链表不为空                                                         这一位为1，代表着对应的链表不为空 
         对应着bin[68]                                                                        对应着bin[64] 
0x7ffff7dce4a8 <main_arena+2156>:   00000000000000000000000000000000 #binmap[3] 4byte==32bit  //block==3(largebin)
```

已经知道block==2上有可用的free chunk，然后执行下列代码：

```c
          /* Advance to bin with set bit. There must be one. */
          while ((bit & map) == 0)  //bit & map == 1 & 10 == 0
            {//满足条件进入循环（意味着block2上的第一条链没有可用的free chunk）
              bin = next_bin (bin); //bin指针向下移动
              bit <<= 1;            //bit=bit<<1，现在bit==2
              assert (bit != 0);    //assert(false)触发断言
            }
------------------------------------------------------------------------------------------------------
第二次循环：
          /* Advance to bin with set bit. There must be one. */
          while ((bit & map) == 0)  //bit & map == 2 & 10 == 2 说明对应的链表上有可用的chunk，终止循环
            {
              bin = next_bin (bin); 
              bit <<= 1; 
              assert (bit != 0); 
            }
```

回过头来继续分析代码：

```c
          /* Inspect the bin. It is likely to be non-empty */
          victim = last (bin); //获取链表上的最后一个chunk

          /*  If a false alarm (empty bin), clear the bit. */
          if (victim == bin)  //检查这个bin，因为它有可能是空的（我们之前说过，当一个bin为空时，它对应的binmap项并不会立即被clear（置0）） 
            {   //链表为NULL
 				......
            }
          else
            {	//不为NULL
              ......
            }
```

为什么要执行这段代码，我们看一下注释就知道：当一个bin为空时，它对应的binmap项并不会立即被clear。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616581193947-cdc72c56-4b07-41c0-aaea-a74d513d72cc.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616581394212-a2d278e6-84d5-4a62-a226-5503da278ed3.png)

现在对应的链表不为空，因此会进入else语句，首先来看第一部分：

```c
			{
              size = chunksize (victim);  //获取victim（0x555555756250）的size ,size==1072==0x430，nb==0xa0

              /*  We know the first chunk in this bin is big enough to use. */
              assert ((unsigned long) (size) >= (unsigned long) (nb));  //取出来的chunk的大小一定大于nb

              remainder_size = size - nb;  //计算切割后的chunk大小，remainder_size==912==0x390

              /* unlink */
              unlink (av, victim, bck, fwd); //对victim进行unlink，将chunk从largebin的链表中取出
	
				......(代码略)
            }
---------------------------------------------------------------------------------------------------
#此时的内存（在unlink之前）：
largebins
0x400: 0x555555756250 —▸ 0x7ffff7dce090 (main_arena+1104) ◂— 0x555555756250 /* 'PbuUUU' */
0x500: 0x5555557566b0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
pwndbg> x/140gx 0x555555756250
0x555555756250:	0x0000000000000000	0x0000000000000431 #victim
0x555555756260:	0x00007ffff7dce090	0x00007ffff7dce090
0x555555756270:	0x0000555555756250	0x0000555555756250
......（省略均为空）
0x555555756680:	0x0000000000000430	0x0000000000000030
0x555555756690:	0x0000000000000000	0x0000000000000000
0x5555557566a0:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x7ffff7dce090
0x7ffff7dce090 <main_arena+1104>:	0x00007ffff7dce080	0x00007ffff7dce080
0x7ffff7dce0a0 <main_arena+1120>:	0x0000555555756250	0x0000555555756250
0x7ffff7dce0b0 <main_arena+1136>:	0x00007ffff7dce0a0	0x00007ffff7dce0a0
0x7ffff7dce0c0 <main_arena+1152>:	0x00007ffff7dce0b0	0x00007ffff7dce0b0
0x7ffff7dce0d0 <main_arena+1168>:	0x00007ffff7dce0c0	0x00007ffff7dce0c0
0x7ffff7dce0e0 <main_arena+1184>:	0x00005555557566b0	0x00005555557566b0
0x7ffff7dce0f0 <main_arena+1200>:	0x00007ffff7dce0e0	0x00007ffff7dce0e0
0x7ffff7dce100 <main_arena+1216>:	0x00007ffff7dce0f0	0x00007ffff7dce0f0
pwndbg> 
```

现在对largebin的victim进行unlink，unlink源码如下：

```c
/* Take a chunk off a bin list */
#define unlink(AV, P, BK, FD) {                                            \
    if (__builtin_expect (chunksize(P) != prev_size (next_chunk(P)), 0))      \
      malloc_printerr ("corrupted size vs. prev_size");			      \
    FD = P->fd;								      \
    BK = P->bk;								      \
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))		      \
      malloc_printerr ("corrupted double-linked list");			      \
    else {								      \
        FD->bk = BK;							      \
        BK->fd = FD;							      \
        if (!in_smallbin_range (chunksize_nomask (P))			      \
            && __builtin_expect (P->fd_nextsize != NULL, 0)) {		      \
	    if (__builtin_expect (P->fd_nextsize->bk_nextsize != P, 0)	      \
		|| __builtin_expect (P->bk_nextsize->fd_nextsize != P, 0))    \
	      malloc_printerr ("corrupted double-linked list (not small)");   \
            if (FD->fd_nextsize == NULL) {				      \
                if (P->fd_nextsize == P)				      \
                  FD->fd_nextsize = FD->bk_nextsize = FD;		      \
                else {							      \
                    FD->fd_nextsize = P->fd_nextsize;			      \
                    FD->bk_nextsize = P->bk_nextsize;			      \
                    P->fd_nextsize->bk_nextsize = FD;			      \
                    P->bk_nextsize->fd_nextsize = FD;			      \
                  }							      \
              } else {							      \
                P->fd_nextsize->bk_nextsize = P->bk_nextsize;		      \
                P->bk_nextsize->fd_nextsize = P->fd_nextsize;		      \
              }								      \
          }								      \
      }									      \
}
```

传入unlink的参数分别为：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616588057543-02ee1b8e-d7db-4879-be91-55fd7d4c5309.png)

> 由于bck和fwd未初始化，因此显示optimized out(已优化)，在调用unlink时不会跳转到对应的代码，因此只能根据汇编来猜测对应的内容
>

经过检查之后，现在对bck和fwd指针进行初始化：

```c
    FD = P->fd;								      s
    BK = P->bk;
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616588431257-88fd28a3-767d-4a67-addf-613b3496c056.png)

对其进行初始化之后会进入如下的else语句：

```c
        FD->bk = BK;							      \
        BK->fd = FD;	
```

这两句话的作用是将victim从main_arena中断链，然后又是一些安全性检查：

```c
        if (!in_smallbin_range (chunksize_nomask (P))		//判断victim是否在smallbin范围内（包括三个标志位的大小）
            && __builtin_expect (P->fd_nextsize != NULL, 0)) {		     //安全性检查
	    if (__builtin_expect (P->fd_nextsize->bk_nextsize != P, 0)	     //安全性检查
		|| __builtin_expect (P->bk_nextsize->fd_nextsize != P, 0))       //安全性检查
	      malloc_printerr ("corrupted double-linked list (not small)");  
```

接下来的代码就是largebin解链的核心步骤：

```c
            if (FD->fd_nextsize == NULL) {				      \
                if (P->fd_nextsize == P)				      \
                  FD->fd_nextsize = FD->bk_nextsize = FD;		      \
                else {							      \
                    FD->fd_nextsize = P->fd_nextsize;			      \
                    FD->bk_nextsize = P->bk_nextsize;			      \
                    P->fd_nextsize->bk_nextsize = FD;			      \
                    P->bk_nextsize->fd_nextsize = FD;			      \
                  }							      \
              } else {							      \
                P->fd_nextsize->bk_nextsize = P->bk_nextsize;		      \
                P->bk_nextsize->fd_nextsize = P->fd_nextsize;		      \
              }	
```

首先判断victim的fd_nextsize是否为NULL：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616589075121-39f010e4-7e96-41a8-8633-60effafcc6b3.png)

不为NULL，会执行else语句设置victim的fd_nextsize和bk_nextsize指针：

```c
              } else {							      \
                P->fd_nextsize->bk_nextsize = P->bk_nextsize;		      \
                P->bk_nextsize->fd_nextsize = P->fd_nextsize;		      \
              }	
```

现在victim已经解链完成。然后又是一段if...else： 

```c
              /* Exhaust */
              if (remainder_size < MINSIZE) //remainder_szie==0x390；MINSIZE==0x1f
                {
                  	......
                }
              /* Split */
              else
                {
					......
                }
---------------------------------------------------------------------------------------------------
MINSIZE的宏定义如下：
/* The smallest size we can malloc is an aligned minimal chunk */

#define MINSIZE  \
  (unsigned long)(((MIN_CHUNK_SIZE+MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK))
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616590982539-6efb3126-35a4-440e-bfef-5812423b8a6f.png)

现在进入else语句，对victim进行切割并设置last_remainder，切割余下的不慎将会链入到unsortedbin中：

```c
 /* Split */
              else
                {
                  remainder = chunk_at_offset (victim, nb);   //获取应该分割的地方（地址）：remainder==(mchunkptr) 0x5555557562f0
                  /* We cannot assume the unsorted list is empty and therefore
                     have to perform a complete insert here.  */  //由于现在我们不能确定此时的unsortedbin是否为空，因此在这里需要进行一次完整的插入操作
                  bck = unsorted_chunks (av); 	//获取unsortedbinbin在main_arena的指针
                  fwd = bck->fd; //bck==fwd==(mchunkptr) 0x7ffff7dcdca0 <main_arena+96>
		  if (__glibc_unlikely (fwd->bk != bck)) //安全性检查
		    malloc_printerr ("malloc(): corrupted unsorted chunks2");
                  remainder->bk = bck;  //将对victim切割后剩下的remainder链入到unsortedbin
                  remainder->fd = fwd;
                  bck->fd = remainder;
                  fwd->bk = remainder;
```

链入unsortedbin效果如下：

```c
pwndbg> x/20gx &main_arena
......(NULL)
0x7ffff7dcdca0 <main_arena+96>:	0x0000555555757130	0x0000000000000000
0x7ffff7dcdcb0 <main_arena+112>:	0x00005555557562f0	0x00005555557562f0
0x7ffff7dcdcc0 <main_arena+128>:	0x00007ffff7dcdcb0	0x00007ffff7dcdcb0
0x7ffff7dcdcd0 <main_arena+144>:	0x00007ffff7dcdcc0	0x00007ffff7dcdcc0
pwndbg> bin
tcachebins
empty
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all: 0x5555557562f0 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— 0x5555557562f0
smallbins
empty
largebins
0x500: 0x5555557566b0 —▸ 0x7ffff7dce0d0 (main_arena+1168) ◂— 0x5555557566b0
pwndbg> x/140gx victim
0x555555756250:	0x0000000000000000	0x0000000000000431
0x555555756260:	0x00007ffff7dce090	0x00007ffff7dce090
0x555555756270:	0x0000555555756250	0x0000555555756250
0x555555756280:	0x0000000000000000	0x0000000000000000
0x555555756290:	0x0000000000000000	0x0000000000000000
0x5555557562a0:	0x0000000000000000	0x0000000000000000
0x5555557562b0:	0x0000000000000000	0x0000000000000000
0x5555557562c0:	0x0000000000000000	0x0000000000000000
0x5555557562d0:	0x0000000000000000	0x0000000000000000
0x5555557562e0:	0x0000000000000000	0x0000000000000000
0x5555557562f0:	0x0000000000000000	0x0000000000000000
0x555555756300:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
0x555555756310:	0x0000000000000000	0x0000000000000000
......（省略内容均为空）
0x555555756680:	0x0000000000000430	0x0000000000000030
0x555555756690:	0x0000000000000000	0x0000000000000000
0x5555557566a0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

最终设置：

```c
                  /* advertise as last remainder */
                  if (in_smallbin_range (nb))  //在smallbin范围内
                    av->last_remainder = remainder;	//设置last_remainder
				  if (!in_smallbin_range (remainder_size))  //remainder_size==0x390
                    { //remainder_size不在smallbin范围内
                      remainder->fd_nextsize = NULL;
                      remainder->bk_nextsize = NULL;
                    }
                  set_head (victim, nb | PREV_INUSE |
                            (av != &main_arena ? NON_MAIN_ARENA : 0));  //在smallbin范围内
                  set_head (remainder, remainder_size | PREV_INUSE);
                  set_foot (remainder, remainder_size);
```

效果如下：

```c
pwndbg> x/140gx 0x555555756250
0x555555756250:	0x0000000000000000	0x00000000000000a1 #victim     #第一个set_head
0x555555756260:	0x00007ffff7dce090	0x00007ffff7dce090
0x555555756270:	0x0000555555756250	0x0000555555756250
......
0x5555557562f0:	0x0000000000000000	0x0000000000000391 #remainder  #第二个set_head
0x555555756300:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
0x555555756310:	0x0000000000000000	0x0000000000000000
......
0x555555756680:	0x0000000000000390	0x0000000000000030
    			#set_foot
0x555555756690:	0x0000000000000000	0x0000000000000000
0x5555557566a0:	0x0000000000000000	0x0000000000000000
pwndbg> p *av
$97 = {
  mutex = 0, 
  flags = 0, 
  have_fastchunks = 0, 
  fastbinsY = {0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}, 
  top = 0x555555757130, 
  last_remainder = 0x5555557562f0,   //last_remainder已设置
  bins = {0x5555557562f0, 0x5555557562f0, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0c0 <main_arena+1152>, 0x5555557566b0, 0x5555557566b0, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2d0 <main_arena+1680>, 0x7ffff7dce2d0 <main_arena+1680>...}, 
  binmap = {0, 0, 17, 0}, 
  next = 0x7ffff7dcdc40 <main_arena>, 
  next_free = 0x0, 
  attached_threads = 1, 
  system_mem = 135168, 
  max_system_mem = 135168
}
pwndbg> 
```

> 注意：binmap此时未发生变化！！！未被清空对应的bit！！！！对应了之前我们所说的。
>

然后返回victim即可：

```c
              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim);
              alloc_perturb (p, bytes);
              return p;
```



