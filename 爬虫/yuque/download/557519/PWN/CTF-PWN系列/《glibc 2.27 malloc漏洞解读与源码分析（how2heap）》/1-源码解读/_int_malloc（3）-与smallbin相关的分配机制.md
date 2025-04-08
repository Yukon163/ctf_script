# 关键词
+ smallbin分配内存
+ smallbin chunk移入tcachebin中
+ 单线程

# 快速回顾
假如说在上一小节中你继续向后调试的话会发现放入unsortedbin中的free chunk之后会移动到smallbin中，但是如果想要完全研究smallbin的分配过程，那个例子并不合适，因为它只会执行到部分代码，如下所示：

```c
if (in_smallbin_range (nb)) //判断要申请的chunk是否在smallbin的范围内
    {	//在此范围内
      idx = smallbin_index (nb);   //执行
      bin = bin_at (av, idx); 	   //执行

      if ((victim = last (bin)) != bin)  //进入
        {
          bck = victim->bk;			//执行
	  if (__glibc_unlikely (bck->fd != victim))
	    malloc_printerr ("malloc(): smallbin double linked list corrupted");
          set_inuse_bit_at_offset (victim, nb);
          bin->bk = bck;			//执行
          bck->fd = bin;			//执行

          if (av != &main_arena)	//不进入
	    set_non_main_arena (victim);
          check_malloced_chunk (av, victim, nb);	//执行
#if USE_TCACHE
	  /* While we're here, if we see other chunks of the same size,
	     stash them in the tcache.  */
       //翻译：当程序执行到此处时，如果在相同大小的bin中仍然有相同size的smallbin chunk
       //我们将把这些chunk放入到tcache中
	  size_t tc_idx = csize2tidx (nb);
	  if (tcache && tc_idx < mp_.tcache_bins)	//进入
	    {
	      mchunkptr tc_victim;

	      /* While bin not empty and tcache not full, copy chunks over.  */
          //smallbin不为空且tcache对应的链上未满，对smallbin chunk拷贝到tcache中
	      while (tcache->counts[tc_idx] < mp_.tcache_count	//无法进入！！！
		     && (tc_victim = last (bin)) != bin)
		{
		  if (tc_victim != 0)
		    { 
		      bck = tc_victim->bk;
		      set_inuse_bit_at_offset (tc_victim, nb);
		      if (av != &main_arena)
			set_non_main_arena (tc_victim);
		      bin->bk = bck;
		      bck->fd = bin;

		      tcache_put (tc_victim, tc_idx); //我们想让代码执行到此处！！！
	            }
		}
	    }
#endif
          void *p = chunk2mem (victim);		//执行
          alloc_perturb (p, bytes);		//执行
          return p;		//执行
        }
    }
```

整合到unsortedbin结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615969795505-6447eeb4-f39f-410f-bc91-a595297b51e2.png)

接下来的代码会将放入unsortedbin的chunk移入到smallbin或largebin中，这里是移入到了smallbin中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615969857533-5e372666-b2b1-41e8-82af-c6f60f91d652.png)

这里我们先不管移入smallbin的详细代码，当进行下一次malloc时，调试一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615970386513-ab54fe47-629c-41da-b624-295751c7b89a.png)

如上图所示，无法进入到此源码：

```c
	      while (tcache->counts[tc_idx] < mp_.tcache_count	//无法进入！！！
		     && (tc_victim = last (bin)) != bin)
		{
		  if (tc_victim != 0)
		    { 
		      bck = tc_victim->bk;
		      set_inuse_bit_at_offset (tc_victim, nb);
		      if (av != &main_arena)
			set_non_main_arena (tc_victim);
		      bin->bk = bck;
		      bck->fd = bin;

		      tcache_put (tc_victim, tc_idx); //我们想让代码执行到此处！！！
	            }
		}
```

上述代码是将smallbin的free chunk移入到tcachebin中，为了直观的了解代码，我们得重新写一个例子，有一些条件需要我们做到：

+ 要申请的chunk在smallbin的大小范围内
+ 申请时对应的smallbin链表不能为空
+ 在向smallbin申请chunk之后，smallbin中仍然有相同大小的free chunk
+ 此时对应大小的tcache链中未满

# 程序源码
```c
//例子改动于：how2heap:Tcache Stashing Unlink Attack
#include <stdio.h>
#include <stdlib.h>

int main(){
    unsigned long stack_var[0x10] = {0};
    unsigned long *chunk_lis[0x10] = {0};
    unsigned long *p,*pp;

    for(int i = 0;i < 9;i++){
        chunk_lis[i] = (unsigned long*)malloc(0x90);  //首先申请9个大小为0x90的chunk
    }

    for(int i = 3;i < 9;i++){
        free(chunk_lis[i]);     //释放6个chunk，这些会到tcache中
        chunk_lis[i]=NULL;
    }
    
    free(chunk_lis[1]);     //放到tcache:chunk1
    free(chunk_lis[0]);     //放到unsortedbin:chunk0
    free(chunk_lis[2]);     //放到unsortedbin:chunk2
    
    malloc(0xa0);           //申请一个0xa0的chunk，chunk0和chunk2都会被整理到smallbin中
    
    malloc(0x90);           //从tcache中申请两个0x90的chunk
    malloc(0x90);

    //现在calloc申请一个0x90大小的 chunk，他会把一个 smallbin 里的 chunk0 返回给我们，
    //另一个 smallbin 的 chunk2 将会与 tcache 相连.
    pp = calloc(1,0x90);    //calloc不会从tcachebin中申请chunk
    p = malloc(0x90);  
    return 0;
}
```

> 编译命令：gcc -g in_smallbin_range.c -o in_smallbin_range
>

# 开始调试
> 调试之前请先关闭系统的ALSR
>

注意现在我们的目标是上述in_smallbin_range源码，因此在调试的时请忽视其他代码。

现在直接对程序代码第25行下断点，然后看一下结果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615972259769-c90750ee-9b89-4272-8318-df606624e758.png)

图上很清楚，smallbin中有两个大小为0xa0的free chunk，为了让smallbin chunk移入到tcachebin中，现在需要对tcache进行free chunk申请：

```c
    malloc(0x90);           //从tcache中申请两个0x90的chunk
    malloc(0x90);
```

单步步过这两个malloc之后结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615972724286-2c89f4b4-5042-4bf3-bb7f-691b6d652072.png)

单步步入calloc：

```c
    pp = calloc(1,0x90);    
```

在这里要注意calloc不会向tcachebin申请chunk，可以将calloc认为是未加入tcache机制的malloc。

这是为什么呢？我们来对比一下__libc_calloc和__libc_malloc的源码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615974725825-c516a580-9761-41aa-8500-34de1842664f.png)

calloc和malloc的本质都是调用_int_malloc进行分配内存，而在调用此函数之前：

calloc会先调用__libc_calloc；malloc会先调用__libc_malloc

我们在__libc_calloc并未发现向tcachebin中申请内存的代码，也就是说申请tcache是在调用_int_malloc之前申请的。

知道这些后我们回过头来继续调试，进入_int_malloc函数，再经过一些判断之后会来到：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615976510280-0b330130-19c2-47e9-9b04-32ade06cf00b.png)

要申请的大小nb为160（0xa0）小于0x3ff，会进入到if中：

```c
      idx = smallbin_index (nb);  //获取nb在smallbin的index
      bin = bin_at (av, idx);	  //获取index在main_arena中的地址
```

结果如下

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615976832361-588d93cc-828a-45c9-b64d-90f57c436ee4.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615977049621-3e077f3e-85cd-49df-b14f-8ef58d83ce93.png)

然后进入下一个if语句的判断：

```c
      if ((victim = last (bin)) != bin)
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615977224171-41e5de0c-413a-46ec-83bb-4c424e8c3a79.png)

其中last函数的定义如下

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615977268192-f3f8e9fc-e0e9-4e01-9c72-67a62d7088d0.png)

我们可以这样理解：将传入的参数指针bin当作一个chunk，然后获取其的bk指针返回给victim：

```c
0x7ffff7dcdd30 <main_arena+240>:	0x00007ffff7dcdd20	0x00007ffff7dcdd20 #chunk
0x7ffff7dcdd40 <main_arena+256>:	0x0000555555756390	0x0000555555756250
    								#fd					#bk
0x7ffff7dcdd50 <main_arena+272>:	0x00007ffff7dcdd40	0x00007ffff7dcdd40
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615977809945-6f5ddf7b-65fa-4549-a854-4568a57ca03e.png)

> **<font style="color:#F5222D;">smallbin采用的是FIFO(先入先出)算法：将新释放的chunk添加到链表的头部，分配操作从链表的尾部中获取</font>**
>

放到这个程序来说，现在将要申请“最先进入”smallbin的free chunk（0x0000555555756250）。

```c
      if ((victim = last (bin)) != bin)
          //获取smallbin中最先进入的chunk的地址
          //换句话说这条语句的意思是判断smallbin中是否有空闲的smallbin chunk
```

对应大小的smallbin链表并不为空，进入if语句后执行如下代码：

```c
          bck = victim->bk;
```

```c
pwndbg> p victim->bk
$15 = (struct malloc_chunk *) 0x555555756390
pwndbg> x/16gx  victim
0x555555756250:	0x0000000000000000	0x00000000000000a1
0x555555756260:	0x00007ffff7dcdd30	0x0000555555756390
0x555555756270:	0x0000000000000000	0x0000000000000000
0x555555756280:	0x0000000000000000	0x0000000000000000
0x555555756290:	0x0000000000000000	0x0000000000000000
0x5555557562a0:	0x0000000000000000	0x0000000000000000
0x5555557562b0:	0x0000000000000000	0x0000000000000000
0x5555557562c0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

这条语句的作用是获取victim的bk指针，也就是获得倒数第二个smallbin chunk的地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615978439871-bc4fcf20-ff7a-41b5-9908-af490086d36d.png)

然后检查双向链表的完整性：

```c
	  if (__glibc_unlikely (bck->fd != victim))
	    malloc_printerr ("malloc(): smallbin double linked list corrupted");
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615978526634-8c258a88-37db-42a3-b41c-34b4159dc68d.png)

接下来执行：

```c
          set_inuse_bit_at_offset (victim, nb);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615978636467-0cb6cb2b-7853-46a6-ba46-472e617d1430.png)

这个语句的作用是设置next chunk的mchunk_prev_size域，直接来看一下效果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615978884504-67dea06f-99b0-4350-a648-2dd875f2d263.png)

```c
          bin->bk = bck;
```

执行此语句后main_arena情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615979275952-fcf07490-5a14-4273-bcbb-8115e18fc895.png)

```c
          bck->fd = bin;
```

效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615979418793-4783ec98-0c2a-46ea-a476-1e128991e507.png)

victim堆块已经从smallbin中摘除，现在smallbin链中已经剩下一个free chunk：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615985700656-1fb842fe-c297-4086-9009-a65d44c94986.png)

接下来又是一个if：

```c
          if (av != &main_arena)
	    set_non_main_arena (victim);
          check_malloced_chunk (av, victim, nb);  //检查
```

set_non_main_arena函数定义如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615986146096-9162f86e-db20-40db-8fcf-4e615a2f4196.png)

其作用是对某一个chunk进行标志位NON_MAIN_ARENA设置，这个标志位用来标记chunk不是由main_arena（主分配区）申请的。

接下来就到了我们的重点--将剩余的smallbin free chunk放入tcachebin中：

> 从smallbin中取出的victim chunk用于返回。
>

```c
#if USE_TCACHE
	  /* While we're here, if we see other chunks of the same size,
	     stash them in the tcache.  */
	  size_t tc_idx = csize2tidx (nb);
	  if (tcache && tc_idx < mp_.tcache_bins)
	    {
	      mchunkptr tc_victim;

	      /* While bin not empty and tcache not full, copy chunks over.  */
	      while (tcache->counts[tc_idx] < mp_.tcache_count
		     && (tc_victim = last (bin)) != bin)
		{
		  if (tc_victim != 0)
		    {
		      bck = tc_victim->bk;
		      set_inuse_bit_at_offset (tc_victim, nb);
		      if (av != &main_arena)
			set_non_main_arena (tc_victim);
		      bin->bk = bck;
		      bck->fd = bin;

		      tcache_put (tc_victim, tc_idx);
	            }
		}
	    }
#endif
```

老样子，通过nb来获取chunk在tcachebin中的index：

```c
size_t tc_idx = csize2tidx (nb);  //tc_idx==8
```

```c
	  if (tcache && tc_idx < mp_.tcache_bins) //tcache实际上指的是tcache_perthread_struct
```

然后判断tcache是否初始化并且通过判断victim的idx从而判断victim的大小是否在tcachebin的范围内：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615987296475-e7e4023e-06a9-46e4-81f1-42927383ca0b.png)

和之前“fastbin free chunk脱链”过程差不多，但是略有区别。

```c
	      /* While bin not empty and tcache not full, copy chunks over.  */
	      while (tcache->counts[tc_idx] < mp_.tcache_count //mp_.tcache_count==7
		     && (tc_victim = last (bin)) != bin)
//执行后：tc_victim==0x555555756390 bin==0x7ffff7dcdd30
```

+ tcache->counts[tc_idx] < mp_.tcache_count：检查对应大小的tcachebin链上是否已满
+ tc_victim = last (bin)) != bin：检查smallbin是否为空

如果tc_victim==bin说明smallbin已空，会跳出while循环。现在继续向下调试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615989394707-289e5a75-459a-4b28-a689-cdf162eb8a7b.png)

```c
if (tc_victim != 0) //判断指针tc_victim是否为NULL
    //换句话说判断除victim之外在相同大小的链表上是否还有其他的small chunk
```

判断后开始对smallbin中的tc_victim free chunk进行解链：

```c
bck = tc_victim->bk;
```

> 执行前：
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616026255181-f7245abd-a4b6-4b53-aca3-4e604a4e61f5.png)

> 执行后：
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616026311909-2cf5471b-8542-48c0-8e0d-185a5463bdc1.png)

```c
set_inuse_bit_at_offset (tc_victim, nb); //设置tc_victim下一个chunk的mchunk_prev_size域
```

因为我们要将tc_victim放入到tcachebin中，因此需要设置tc_victim的mchunk_size域。执行前后效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616051988449-8e21c633-97b9-4a59-9993-939ec25c2e6e.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616026782582-c6864a0e-49ad-41dd-ae95-d4a20d1bb4dc.png)

```c
		      if (av != &main_arena)  //判断av是否为main_arena（主分配区）
			set_non_main_arena (tc_victim);		//设置tc_victim的NON_MAIN_ARENA
		      bin->bk = bck;  //解链过程1
		      bck->fd = bin;  //解链过程2
```

> 我不知道之前说过没有，这里在强调一下：指针av在单线程的情况下始终指向main_arena
>

首先来看一下执行解链过程1后的情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616027048837-a2cfe6f0-b20a-4b0d-a84b-240fc795c3f2.png)

> 上图中的corrupted是损坏的意思。
>

下图是执行解链过程2后的情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616027086880-462f5ac3-21ff-4a0f-bf9c-9e94eabd1e23.png)

现在tc_victim已经被解链，接下来就是要链入到tcache中：

```c
		      tcache_put (tc_victim, tc_idx);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616027266561-b0a6ba3b-0c06-4fde-9082-671d07e33c39.png)

```c
static __always_inline void
tcache_put (mchunkptr chunk, size_t tc_idx)
{
  tcache_entry *e = (tcache_entry *) chunk2mem (chunk);  //获取chunk的chunk data起始地址
  assert (tc_idx < TCACHE_MAX_BINS);   //判断tc_idx是否在tcache范围内

  /* Mark this chunk as "in the tcache" so the test in _int_free will
     detect a double free.  */
  e->key = tcache;	//设置chunk的key标志位

  e->next = tcache->entries[tc_idx];  //设置next标志位
  tcache->entries[tc_idx] = e;	//设置tcache_perthread_struct的entries
  ++(tcache->counts[tc_idx]);	//设置tcache_perthread_struct的counts
}
```

这里的过程就不再说了（之前说过，不明白的可以下载文章最后的PPT），最终结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616027817583-e2d3f9ce-42fe-49e4-9589-8384b4bda26d.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616027854457-f92bb4bc-76b3-4438-9c1b-25c0dad866dc.png)

然后再次检查：

```c
	      /* While bin not empty and tcache not full, copy chunks over.  */
	      while (tcache->counts[tc_idx] < mp_.tcache_count  //检查对应大小的tcachebin链上是否已满
		     && (tc_victim = last (bin)) != bin) //检查对应大小的smallbin链是否为空
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1616028173119-e1867300-eb8b-418a-92f0-4415f0829073.png)不符合条件，退出循环，最终将申请到的victim chunk返回给用户。

[in_smallbin_range.pptx](https://www.yuque.com/attachments/yuque/0/2021/pptx/574026/1617701702891-146ba1ca-8d95-4c76-a906-61e6ff6be211.pptx)

