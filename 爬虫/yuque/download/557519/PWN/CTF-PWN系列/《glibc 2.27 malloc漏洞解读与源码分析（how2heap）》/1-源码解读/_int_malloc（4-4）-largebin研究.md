这一小节我们来详细的了解下largebin的分配机制，和之前一样我们仍然使用一个例子来了解。这一篇文章相当于对之前内容的一个补充，强烈建议参考后面的PPT文件！！！

# 例子
> 例子来自：[https://xz.aliyun.com/t/6596](https://xz.aliyun.com/t/6596)
>

```c
#include<stdio.h>
#include<stdlib.h>

int main()
{
    unsigned long *pa, *pb, *p1, *p2, *p3, *p4, *p5, *p6, *p7, *p8, *p9, *p10, *p11, *p12, *p13, *p14;
    unsigned long *p;
    pa = malloc(0xb0);
    pb = malloc(0x20);
    p1 = malloc(0x400);
    p2 = malloc(0x20);
    p3 = malloc(0x410);
    p4 = malloc(0x20);
    p5 = malloc(0x420);
    p6 = malloc(0x20);
    p7 = malloc(0x420);
    p8 = malloc(0x20);
    p9 = malloc(0x430);
    p10 = malloc(0x20);
    p11 = malloc(0x430);
    p12 = malloc(0x20);
    p13 = malloc(0x430);
    p14 = malloc(0x20);
    free(pa);
    free(p1);
    free(p3);
    free(p5);
    free(p7);
    free(p9);
    free(p11);
    free(p13);
    p = malloc(0x20);
    p = malloc(0x80);

    return 0;
}
```

然后我们使用gcc来编译：gcc -g supplement.c -o supplement

# largebin结构解读
> 在调试之前首先关闭系统的地址随机化：echo 0 > /proc/sys/kernel/randomize_va_space
>

在malloc(0x20);之前是这样的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1617268096118-5246c594-0c4c-44a8-9868-010fe2448832.png)

在经过malloc中while循环整理后，unsortedbin中的会被移入到smallbin或largebin中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1617268131671-1d20d3e4-ffe9-49f0-bd22-d76a4834f43e.png)

此时我们先来看一下largebin中的0x400这条链：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1617268262109-693866da-d2b5-4ef4-a1ee-427a603c34de.png)

画个图来表示一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1617270744458-93ed4e71-74c6-4c17-b4a0-63edffd4c1f1.png)

可以看到，在大小不相同的large chunk之间会额外增加fd_nextsize和bk_nextsize这两个指针来进行链接，这也印证了nextsize的名字：“下一个大小“，并且从图中可以印证largebin中的free chunk是从大到小进行排序的。一般的，bk_nextsize指向前一个比它大的chunk，fd_nextsize指向下一个比它小的chunk(表头和表尾的chunk除外)。

> **<font style="color:#F5222D;">为了说明方便，我们将链表中最左边的堆块称之为“表尾”，将最右边的堆块称之为“表头”。</font>**
>
> 上图情况就是例外。表头在链表中指的是：0x555555756780，表尾指的是：0x555555756bd0
>

第二条链表0x440和第一条链表上的情况类似，但又有着些许的不同：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1617271137161-b4eaedba-f2ec-44b1-94a1-7cd7e2ddaa76.png)

同样画个图来表示一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1617330468725-9e3b0048-8d2b-451c-9d52-f9bdb5091389.png)

来看一下上面这张图，图上的三个chunk大小都是相同的，只有在0x555555757490 chunk中出现了fd_nextsize和bk_nextsize。这里先不管largebin的分配过程，来看一下第一个malloc之后的结果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1617331196575-7353f7ff-4604-45f6-bda8-718bca3a2d94.png)

很明显在申请内存时使用了0x555555756780这个free chunk，然后对其进行切割后将余下的chunk放入unsortedbin中。为了让之后的调试更有目的性，接下来我们看一下关于largebin的源码。

# 源码解读--largebin的插入和排序过程
```c
          /* place chunk in bin */

          if (in_smallbin_range (size)) //size来源于unsortedbin中victim的大小，现在已将victim从unsortedbin链表上脱下
            { //smallbin在之前说过，这里并不是我们的重点
              victim_index = smallbin_index (size);
              bck = bin_at (av, victim_index);
              fwd = bck->fd;
            }
          else //else语句才是我们的重点
            {
              victim_index = largebin_index (size); //为插入作准备
              bck = bin_at (av, victim_index); //不懂的可以看一下之前的文章中我画的图
              fwd = bck->fd;

              /* maintain large bins in sorted order */
              if (fwd != bck) //利用fwd和bck两个指针来判断largebin是否为空
                { //不等说明不为空
                  /* Or with inuse bit to speed comparisons */
                  size |= PREV_INUSE; 
                  /* if smaller than smallest, bypass loop below */
                  assert (chunk_main_arena (bck->bk)); //安全性检查，因为unsortedbin的NON_MAIN_ARENA位永远是0
                  if ((unsigned long) (size) //bck->bk存储着相应对应链表中最小的chunk。
		      < (unsigned long) chunksize_nomask (bck->bk)) 
                    { //如果说victim的大小小于链表中的最小堆块  ////PPT从此处开始
                      fwd = bck; //准备插入
                      bck = bck->bk; 

                      victim->fd_nextsize = fwd->fd; //设置victim的fd_nextsize
                      victim->bk_nextsize = fwd->fd->bk_nextsize;//设置victim的bk_nextsize
                      fwd->fd->bk_nextsize = victim->bk_nextsize->fd_nextsize = victim;//设置比他大的堆块的两个指针
                    }
                  else
                    { //如果说victim的大小大于或等于链表中的最小堆块
                      assert (chunk_main_arena (fwd)); //和之前一样，对fwd指向的堆块进行安全性检查
                      while ((unsigned long) size < chunksize_nomask (fwd))
                        { //反向遍历，直到遍历到victim的大小大于或等于
                          fwd = fwd->fd_nextsize; //最初fwd指向最大的chunk（表尾）
                          	//这里使用循环对fwd指针进行遍历
			  assert (chunk_main_arena (fwd));
                        }

                      if ((unsigned long) size //如果找到了一个和victim一样大的chunk
			  == (unsigned long) chunksize_nomask (fwd))
                        /* Always insert in the second position.  */
                        fwd = fwd->fd; //准备插入，此中情况下并不会修改原有堆块的nextsize指针
                      		//我们会将victim插入原有堆块的“右边👉”
                      else
                        {//如果找到的chunk和当前victim大小不相同
                          victim->fd_nextsize = fwd;
                          victim->bk_nextsize = fwd->bk_nextsize;
                          fwd->bk_nextsize = victim;
                          victim->bk_nextsize->fd_nextsize = victim;
                        }
                      bck = fwd->bk; //准备插入
                    }
                }
              else //largebin链表为空，直接将victim插入
                victim->fd_nextsize = victim->bk_nextsize = victim;
            }

          mark_bin (av, victim_index);
          victim->bk = bck; //将victim完全插入smallbin或largebin中
          victim->fd = fwd;
          fwd->bk = victim;
          bck->fd = victim;
```

# 源码解读--largebin的分配过程
申请largebin free chunk源码如下：

```c
      /*
         If a large request, scan through the chunks of current bin in
         sorted order to find smallest that fits.  Use the skip list for this.
       */

      if (!in_smallbin_range (nb)) 
        { //如果申请的nb在largebin范围内
          bin = bin_at (av, idx); //idx = largebin_index (nb); 
				//获取对应的index在main_arena中对应的链表bin
          /* skip scan if empty or largest chunk is too small */
          if ((victim = first (bin)) != bin  //first是获取largebin中的第一个free chunk（即表尾）
	      && (unsigned long) chunksize_nomask (victim) 
	        >= (unsigned long) (nb))
              //由于largebin从表尾到表头是从大到小排列的
            { //若bin链表不为空且victim可以满足nb的大小，也就是说如果链上的最大的chunk可以满足nb
              victim = victim->bk_nextsize; //我们反向遍历bin链表即从小到大开始遍历，现在victim是此链表中最小的chunk
              while (((unsigned long) (size = chunksize (victim)) < //size是victim的大小
                      (unsigned long) (nb))) //当victim的大小小于nb时
                  //这里我们的目的是找到一个>=nb的victim
                victim = victim->bk_nextsize; //bk_nextsize在一般情况下储存的是比victim大的chunk

              /* Avoid removing the first entry for a size so that the skip
                 list does not have to be rerouted.  */ //现在已经找到符合条件的victim
              if (victim != last (bin) //判断找到的victim是不是此链上的最后一个free chunk
		  && chunksize_nomask (victim)
		    == chunksize_nomask (victim->fd)) //判断此chunk是否与前一个的大小相同
                victim = victim->fd; //如果大小相同，我们就取之前的那个chunk，
              						 //这样可以避免调整fd_nextsize和bk_nextsize

              remainder_size = size - nb; //计算分配后剩余的大小
              unlink (av, victim, bck, fwd); //对victim进行unlink

              /* Exhaust */
              if (remainder_size < MINSIZE)  //判断分割后剩下的大小remainder_size是否可以成为一个独立的free chunk
                { //不可以
                  set_inuse_bit_at_offset (victim, size);
                  if (av != &main_arena)
		    set_non_main_arena (victim);
                }
              /* Split */
              else
                { //可以，下面的步骤前一篇文章基本上说过
                  remainder = chunk_at_offset (victim, nb);
                  /* We cannot assume the unsorted list is empty and therefore
                     have to perform a complete insert here.  */
                  bck = unsorted_chunks (av);
                  fwd = bck->fd;
		  if (__glibc_unlikely (fwd->bk != bck))
		    malloc_printerr ("malloc(): corrupted unsorted chunks");
                  remainder->bk = bck;
                  remainder->fd = fwd;
                  bck->fd = remainder;
                  fwd->bk = remainder;
                  if (!in_smallbin_range (remainder_size)) 
                    { //若分割后的大小仍为large chunk，需要将两个指针置为NULL
                      remainder->fd_nextsize = NULL;
                      remainder->bk_nextsize = NULL;
                    }
                  set_head (victim, nb | PREV_INUSE |
                            (av != &main_arena ? NON_MAIN_ARENA : 0));
                  set_head (remainder, remainder_size | PREV_INUSE);
                  set_foot (remainder, remainder_size);
                }
              check_malloced_chunk (av, victim, nb);
              void *p = chunk2mem (victim);
              alloc_perturb (p, bytes);
              return p; //返回victim堆块
            }
        }
```

# 源码解读--largebin的unlink
```c
/* Take a chunk off a bin list */
#define unlink(AV, P, BK, FD) {   //注意，在largebin链表中在unlink时寻找合适堆块的遍历是反向遍历
								  //即从小到大使用bk_nextsize进行遍历
    if (__builtin_expect (chunksize(P) != prev_size (next_chunk(P)), 0)) //安全性检查     
      malloc_printerr ("corrupted size vs. prev_size");			      
    FD = P->fd;		//获取victim的前后指针
    BK = P->bk;		//形式为：free chunk(bck) victim free chunk(fwd)						      
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))	//检查双向链表完整性     
      malloc_printerr ("corrupted double-linked list");			      
    else {								      
        FD->bk = BK;	//对bck的fd、fwd的bk进行设置						      
        BK->fd = FD;							      
        if (!in_smallbin_range (chunksize_nomask (P))			      
            && __builtin_expect (P->fd_nextsize != NULL, 0)) {	
            	//若victim属于large chunk且victim->fd_nextsize!=NULL
            	//也就是说如果victim属于large chunk且victim不是相同大小的第一个chunk
            	//我们不会对其进行unlink
	    if (__builtin_expect (P->fd_nextsize->bk_nextsize != P, 0) //largebin中对双向链表的完整性进行检查	      
		|| __builtin_expect (P->bk_nextsize->fd_nextsize != P, 0))    
	      malloc_printerr ("corrupted double-linked list (not small)");   
            if (FD->fd_nextsize == NULL) {	//如果我们获取到的chunk是相同大小的第一个chunk
                	//eg：chunk0(fd_nextsize、bk_nextsize) chunk1 （chunk0size==chunk1size）
                	//这里指chunk1
                if (P->fd_nextsize == P)	//如果在相同size大小的large chunk中只有victim一个			      
                  FD->fd_nextsize = FD->bk_nextsize = FD;		      
                else {	//如果除victim之外还有其他相同大小的chunk						      
                    FD->fd_nextsize = P->fd_nextsize;			      
                    FD->bk_nextsize = P->bk_nextsize;			      
                    P->fd_nextsize->bk_nextsize = FD;			      
                    P->bk_nextsize->fd_nextsize = FD;			      
                  }							      
              } else { //如果不是则对其victim进行脱链（即chunk0size>chunk1size）							      
                P->fd_nextsize->bk_nextsize = P->bk_nextsize;		      
                P->bk_nextsize->fd_nextsize = P->fd_nextsize;		      
              }								      
          }								      
      }									      
}
```

[supplement.pptx](https://www.yuque.com/attachments/yuque/0/2021/pptx/574026/1617871545536-5db1e919-ea2e-40d3-b9b5-507337364561.pptx)

