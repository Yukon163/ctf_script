# 调试
## 第二次内循环
接上一小节，我们来看unlink源码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615856276536-cbc1218c-f30b-4a8c-98a1-74e1063c99c0.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615856297166-4a659aaa-39d6-4a3d-8106-f085856e89ba.png)

先来看一下传入unlink的四个参数：

+ av：指针，指向main_arena（AV）
+ nextchunk：指针，指向p chunk的下一个chunk（P）
+ bck：已定义但其值未初始化（BK）
+ fwd：已定义但其值未初始化（FD）

函数上来就是一个安全性的检查：

```c
    if (__builtin_expect (chunksize(P) != prev_size (next_chunk(P)), 0))      \
      malloc_printerr ("corrupted size vs. prev_size");
```

chunksize获取了**<font style="color:#F5222D;">除了三个标志位之外的大小</font>**，next_chunk函数定义如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615856674970-bdae8fff-718c-4b59-a000-79bba1eacfda.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615857127602-5dc1d7f4-1b35-4340-bc1b-5a63a5ecb771.png)

由于现在nextchunk（P）已经在双向链表中（unsortedbin），所以有两个地方记录其大小，所以检查一下其大小是否一致(size检查)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615856949539-34e38a35-937f-4e3f-bdfc-93cd2b591a0e.png)

```c
pwndbg> x/16gx  0x555555756400
0x555555756400:	0x0000000000000000	0x0000000000000031 //chunksize(P)->结果为0x30
0x555555756410:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
0x555555756420:	0x0000000000000000	0x0000000000000000
0x555555756430:	0x0000000000000030	0x0000000000000040
    			//next_chunk(p)检查此处->结果为0x30
0x555555756440:	0x0000000000000000	0x0000000000000000
0x555555756450:	0x0000000000000000	0x0000000000000000
0x555555756460:	0x0000000000000000	0x0000000000000000
0x555555756470:	0x0000000000000000	0x0000000000020b91
pwndbg> 
```

两处检查的值相等，因此不会触发异常，如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615857369720-e768376b-9fee-4af2-b5db-4a7f646204d6.png)

> RSI是prev_size (next_chunk(P))的检查结果、R9是chunksize(P)的检查结果
>

```c
    FD = P->fd;								      \
    BK = P->bk;								      \
```

现在开始初始化FD，BK（bck、fwd）指针，结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615863113389-a25c9068-2752-48be-a4eb-df262c3e94fa.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615863170628-50ae5837-095d-4da5-affd-bf89d102ae40.png)

> 这两个指针都指向main_arena+96
>

然后又是一个安全性检查：

```c
    if (__builtin_expect (FD->bk != P || BK->fd != P, 0))   //检查双向链表的完整性
      malloc_printerr ("corrupted double-linked list");	
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615863297004-9d8f8dac-3ba3-450c-b462-0077d2b5473a.png)

这里是检查unsortedbin双向链表的完整性，这里当然没有任何问题，之后会进入else语句：

```c
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
      }	
```

首先来看第一步：

```c
        FD->bk = BK;							      \
        BK->fd = FD;
//执行之前：BK==bck==0x7ffff7dcdca0；FD==fwd==0x7ffff7dcdca0
```

执行之后，这两步是设置来main_arena+112的指针：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615864430911-f3bec205-b212-4daf-9745-195556063b38.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615864501262-09045abb-7d1a-4737-9989-69b6b1eee543.png)

换句话说就是将第一次循环中插入unsortedbin中的free chunk取出，然后又又又是一个检查：

```c
        if (!in_smallbin_range (chunksize_nomask (P))			      \
            && __builtin_expect (P->fd_nextsize != NULL, 0)) {		      \
```

chunksize_nomask定义在malloc.c的开头：![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615864753860-22933e0f-b0da-43fc-997b-ddea63d50756.png)

这个函数和chunksize函数类似，只是在计算某个chunk时包含了3个标志位的大小，然后判断待放入unsortedbin的chunk是否在largebin的范围内：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615865144908-af93fb1a-757c-4b79-a149-6e85f25499bf.png)

传入的p chunk过小，因此不在smallbin的范围内，会结束unlink过程：

```c
        if (!in_smallbin_range (chunksize_nomask (P))	//False		      
            && __builtin_expect (P->fd_nextsize != NULL, 0)) {	//False
```

然后会回到malloc_consolidate函数：

```c
	  first_unsorted = unsorted_bin->fd;
	  unsorted_bin->fd = p;
	  first_unsorted->bk = p;

	  if (!in_smallbin_range (size)) { //不进入
	    p->fd_nextsize = NULL;
	    p->bk_nextsize = NULL;
	  }

	  set_head(p, size | PREV_INUSE); //size是两个堆块的大小！！！
	  p->bk = unsorted_bin;
	  p->fd = first_unsorted;
	  set_foot(p, size);
```

这个函数和第一次循环相同，不说了。最终效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615866370968-84f5f4ab-9e90-43cb-8018-aede8afd8060.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615866474983-68342f8b-db30-4c7a-b69e-cc333b164445.png)

稍微总结一下，在整理除了第一个free chunk 堆块（这个堆块和第一个堆块相邻）时，先将unsortedbin中的free chunk进行unlink，然后再和待插入的chunk合并一起放入unsortedbin中。

在进行了三次内循环之后，最终所有的fastbin chunk都进入了unsortedbin，他们都被整合成了一个堆块：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615866861102-a6a99c67-a771-4643-ae8b-3ea2d078e522.png)

malloc_consolidate过程结束，但是注意：原有堆块的fd、bk指针并未清空。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615866975266-4ba07faa-bd51-4a4e-aae0-9a5694a872cc.png)

来一个总结：

```c
  if (in_smallbin_range (nb))
    {
      ......
    }

  /*
	......
   */

  else
    {
      idx = largebin_index (nb);
      if (atomic_load_relaxed (&av->have_fastchunks))
        malloc_consolidate (av);   //进入malloc_consolidate
    }
----------------------------------------------------------------------------------------------------
static void malloc_consolidate(mstate av)
{
  ......

  atomic_store_relaxed (&av->have_fastchunks, false);

  unsorted_bin = unsorted_chunks(av);

  ......

  maxfb = &fastbin (av, NFASTBINS - 1);
  fb = &fastbin (av, 0);
  do {
    p = atomic_exchange_acq (fb, NULL);
    if (p != 0) {
      do {
		......内循环（将fastbinY[idx]中的每一个free chunk放入unsortedbin）
      } while ( (p = nextp) != 0);  //外循环，遍历每一个fastbin链

    }
  } while (fb++ != maxfb);
}
```

整个流程图如下，建议下载阅读：

> 由于个人精力有限，PPT的内容仅供参考，一切以文章内容为准！
>

[unsortedbin unlink.pptx](https://www.yuque.com/attachments/yuque/0/2021/pptx/574026/1617676153778-8122f9bd-6d3b-4b0b-b399-03a0aa451f90.pptx)

