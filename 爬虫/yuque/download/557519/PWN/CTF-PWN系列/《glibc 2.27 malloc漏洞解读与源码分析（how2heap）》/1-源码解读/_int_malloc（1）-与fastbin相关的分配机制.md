# 文章关键词
+ 从fastbin中申请堆块（对fastbin chunk的解链过程）
+ 将fastbin free chunk移入对应的tcachebin链表中
+ tcache_put

> **<font style="color:#F5222D;">这里我们只研究单线程中的malloc，之后文章都是一样。</font>**
>

# 源码浏览
首先来看一下我们在这一小节中需要研究的_int_malloc源码：

```c
/*
   ------------------------------ malloc ------------------------------
 */

static void *
_int_malloc (mstate av, size_t bytes)
{
  INTERNAL_SIZE_T nb;               /* normalized request size */
  unsigned int idx;                 /* associated bin index */
  mbinptr bin;                      /* associated bin */

  mchunkptr victim;                 /* inspected/selected chunk */
  INTERNAL_SIZE_T size;             /* its size */
  int victim_index;                 /* its bin index */

  mchunkptr remainder;              /* remainder from a split */
  unsigned long remainder_size;     /* its size */

  unsigned int block;               /* bit map traverser */
  unsigned int bit;                 /* bit map traverser */
  unsigned int map;                 /* current word of binmap */

  mchunkptr fwd;                    /* misc temp for linking */
  mchunkptr bck;                    /* misc temp for linking */

#if USE_TCACHE
  size_t tcache_unsorted_count;	    /* count of unsorted chunks processed */
#endif

  /*
     Convert request size to internal form by adding SIZE_SZ bytes
     overhead plus possibly more to obtain necessary alignment and/or
     to obtain a size of at least MINSIZE, the smallest allocatable
     size. Also, checked_request2size traps (returning 0) request sizes
     that are so large that they wrap around zero when padded and
     aligned.
   */

  checked_request2size (bytes, nb);

  /* There are no usable arenas.  Fall back to sysmalloc to get a chunk from
     mmap.  */
  if (__glibc_unlikely (av == NULL))
    {
      void *p = sysmalloc (nb, av);
      if (p != NULL)
	alloc_perturb (p, bytes);
      return p;
    }

  /*
     If the size qualifies as a fastbin, first check corresponding bin.
     This code is safe to execute even if av is not yet initialized, so we
     can try it without checking, which saves some time on this fast path.
   */

#define REMOVE_FB(fb, victim, pp)			\
  do							\
    {							\
      victim = pp;					\
      if (victim == NULL)				\
	break;						\
    }							\
  while ((pp = catomic_compare_and_exchange_val_acq (fb, victim->fd, victim)) \
	 != victim);					\

  if ((unsigned long) (nb) <= (unsigned long) (get_max_fast ()))
    {
      idx = fastbin_index (nb);
      mfastbinptr *fb = &fastbin (av, idx);
      mchunkptr pp;
      victim = *fb;

      if (victim != NULL)
	{
	  if (SINGLE_THREAD_P)
	    *fb = victim->fd;
	  else
	    REMOVE_FB (fb, pp, victim);
	  if (__glibc_likely (victim != NULL))
	    {
	      size_t victim_idx = fastbin_index (chunksize (victim));
	      if (__builtin_expect (victim_idx != idx, 0))
		malloc_printerr ("malloc(): memory corruption (fast)");
	      check_remalloced_chunk (av, victim, nb);
#if USE_TCACHE
	      /* While we're here, if we see other chunks of the same size,
		 stash them in the tcache.  */
	      size_t tc_idx = csize2tidx (nb);
	      if (tcache && tc_idx < mp_.tcache_bins)
		{
		  mchunkptr tc_victim;

		  /* While bin not empty and tcache not full, copy chunks.  */
		  while (tcache->counts[tc_idx] < mp_.tcache_count
			 && (tc_victim = *fb) != NULL)
		    {
		      if (SINGLE_THREAD_P)
			*fb = tc_victim->fd;
		      else
			{
			  REMOVE_FB (fb, pp, tc_victim);
			  if (__glibc_unlikely (tc_victim == NULL))
			    break;
			}
		      tcache_put (tc_victim, tc_idx);
		    }
		}
#endif
	      void *p = chunk2mem (victim);
	      alloc_perturb (p, bytes);
	      return p;
	    }
	}
    }

```

要想弄清楚上述的所有代码，我们需要让某个tcachebin为空但是对应大小的fastbin中还有free chunk，接下来我们开始调试这些代码。

# 环境准备
首先先说明一点，假如说使用如下方式获取源码，在后续调试代码时可能会出现一些问题。比如说无法进入_int_malloc函数内部进行调试，在调试时源码到处乱跳（有时候还会执行到注释😭）等。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615515638125-abea0de1-ec94-400b-bcf4-60d2d34355be.png)

一开始我认为是glibc在编译时使用-O2（编译优化）的缘故，假如说不使用-O2编译的话会发生一些问题：

```c
mkdir build
cd build
CFLAGS="-g -O0" ../configure --disable-sanity-checks #使用-O0（不优化）进行编译
make -j24 2>&1 | tee build_glibc.log #生成编译时的编译命令并储存到文件中。
```

结果就是在编译时会发生报错，可以找到报错的代码：/glibc源码目录/include/libc-symbols.h

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615516193410-9d64fcfe-7bf4-42ec-9579-c7742227ae82.png)

> 一些文件在编译时必须开启优化编译
>

使用-O1进行编译或把此宏定义注释掉再次进行编译都还是不可以；这说明glibc源码只能使用-O2进行编译（当然其他命令也可能编译成功，只是我不知道罢了）。

在网上进行搜索后又找到了一种方法，这种源码的获得方式不会出现之前的奇怪问题。

> 这里使用ubuntu-Linux
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615517088652-e970e266-123e-413f-8e3a-15e93ec0c769.png)

首先备份一下源防止出现问题：

```bash
ubuntu@ubuntu:~/Desktop/malloc$ sudo cp /etc/apt/sources.list ./source_backup.list
ubuntu@ubuntu:~/Desktop/malloc$ ls
demo  demo.c  fastbin_demo  fastbin_demo.c  source_backup.list  test  test.c
ubuntu@ubuntu:~/Desktop/malloc$ cat source_backup.list 
```

                         



然后我们将/etc/apt/sources.list文件中以deb-src开头的注释符删掉：

> sudo vim /etc/apt/sources.list<font style="background-color:transparent;">        </font><font style="background-color:transparent;">                                       </font>
>
> 修改完保存即可，紧接着执行sudo apt update（更新源），待命令执行完毕后，获取源码：
>

```bash
mkdir glibc
cd glibc
sudo apt source libc6-dev #获取源码
#执行完成之后会出现警告：
#W: Download is performed unsandboxed as root as file 'glibc_2.27-3ubuntu1.4.dsc' couldn't be accessed by user '_apt'. - pkgAcquire::Run (13: Permission denied)
#忽略就行了
```

> 压缩包glibc_2.27.orig.tar.xz存放着我们所要调试的代码。
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615518286006-1db65c20-f738-4d40-b20f-e053da74da44.png)

# 程序源码
看一下需要准备的程序，其源码如下：

```c
#include<stdio.h>
#include<stdlib.h>
int main(){
	void *p[10]={0}; #用来存放malloc返回的指针
	for(int i = 0 ;i<10;i++){
		p[i]=malloc(0x10);	#初始化heap，申请10个chunk
	}
	for(int i = 0 ;i <10;i++){
		free(p[i]);			#填满tcachebin，填充fastbin
		p[i]=NULL;
	}
	for(int m = 0; m<7;m++){
		p[m]=malloc(0x10);  #向tcachebin申请7个chunk，清空tcachebin
	}
	malloc(0x10); #malloc时会将fastbin中的剩余移到tcachebin中，执行文章开头的源码。
	malloc(0x10);
	return 0;
}
```

> 编译命令：gcc -g fastbin_demo.c -o fastbin_demo
>

# 开始调试glibc源码
## 从fastbin中申请堆块
在开始调试glibc源码之前，我们需要关闭Linux的ALSR：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615532043627-4ec685d3-7b59-438e-82c9-a401484da313.png)

程序编译完成后引入malloc源码：

```bash
ubuntu@ubuntu:~/Desktop/malloc$ gdb fastbin_demo 
GNU gdb (Ubuntu 8.1.1-0ubuntu1) 8.1.1
......
pwndbg> dir /home/ubuntu/Desktop/malloc/glibc/glibc-2.27/malloc
Source directories searched: /home/ubuntu/Desktop/malloc/glibc/glibc-2.27/malloc:$cdir:$cwd
pwndbg> 
```

对代码的第14行下断点，在终端中输入r以开始调试，结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615532379501-207350a9-8754-4be8-8834-8b678e08e55c.png)

由于在free堆块之后会优先进入tcachebin中，所以程序的12-15行的作用是清空对应大小tcachebin链表的free chunk。

> 在申请时chunk时，tcache优先级最高
>

接下来单步步入第15行的malloc：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615532613370-bad383cf-12d9-4866-ad60-6c59394c82f6.png)

然后一直单步直到我们要研究的_int_malloc函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615532712787-2727cebf-d53a-4c34-b6c7-f94c1ee244d4.png)

进入这个函数后我们仔细研究这个函数，首先关注的是传入_int_malloc函数中的两个参数：mstate av、size_t bytes：

```c
pwndbg> p av
$1 = (mstate) 0x7ffff7dcdc40 <main_arena>
pwndbg> p *av
$2 = {
  mutex = 0, 
  flags = 0, 
  have_fastchunks = 1, 
  fastbinsY = {0x555555756370, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}, 
  top = 0x555555756390, 
  last_remainder = 0x0, 
  bins = {0x7ffff7dcdca0 <main_arena+96>, 0x7ffff7dcdca0 <main_arena+96>, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0d0 <main_arena+1168>, 0x7ffff7dce0d0 <main_arena+1168>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2d0 <main_arena+1680>, 0x7ffff7dce2d0 <main_arena+1680>...}, 
  binmap = {0, 0, 0, 0}, 
  next = 0x7ffff7dcdc40 <main_arena>, 
  next_free = 0x0, 
  attached_threads = 1, 
  system_mem = 135168, 
  max_system_mem = 135168
}
pwndbg> p bytes
$3 = 16
pwndbg> 
```

bytes是我们在写用C写程序时代码中的malloc(size)中的size，而av是指向main_arena的指针；

> main_arena可以译为主分配区
>

继续向下研究代码：

```c
checked_request2size (bytes, nb); 
```

执行完成之后来看一下结果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615533361817-475ce26d-5b8e-4ceb-98d5-923db521d7ef.png)

> bytes==16 (0x10)；nb==32 (0x20)
>

从执行结果可以知道checked_request2size的作用是将我们输入的malloc(size)中的size转化为chunk中size。

> checked_request2size牵扯到最小堆块申请大小和堆块对齐，我们不在这里研究它。
>

```c
  /* There are no usable arenas.  Fall back to sysmalloc to get a chunk from
     mmap.  */	//av指针指向main_arena
  if (__glibc_unlikely (av == NULL)) //若没有可用的main_arena
    {		//调用sysmalloc从mmap获得堆空间
      void *p = sysmalloc (nb, av);
      if (p != NULL)
	alloc_perturb (p, bytes);
      return p;
    }
```

这段代码的注释已经标的很清楚，不再说；继续向下：

```c
  if ((unsigned long) (nb) <= (unsigned long) (get_max_fast ()))
```

这里调用了函数get_max_fast来获取global_max_fast的值，这个值代表着放入fastbin的free chunk最大大小，在默认情况下global_max_fast的值为0x80：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615534104216-2c3c5a64-b93b-41f1-a9ad-9ea393a438a5.png)

fastbin的头节点存放在在main_arena中：

```c
pwndbg> x/16gx &main_arena
0x7ffff7dcdc40 <main_arena>:	0x0000000000000000	0x0000000000000001
0x7ffff7dcdc50 <main_arena+16>:	0x0000555555756370	0x0000000000000000
    							#here～
0x7ffff7dcdc60 <main_arena+32>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdc70 <main_arena+48>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdc80 <main_arena+64>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdc90 <main_arena+80>:	0x0000000000000000	0x0000000000000000
0x7ffff7dcdca0 <main_arena+96>:	0x0000555555756390	0x0000000000000000
0x7ffff7dcdcb0 <main_arena+112>:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
pwndbg> 
```

由于nb==0x20小于global_max_fast的值（申请的堆块大小在fastbin的范围内），因此执行if语句的内容：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615534577810-b95dec20-1ecc-452e-989f-e6a99fd660f6.png)

首先：

```c
      idx = fastbin_index (nb); 
```

这条语句获得了nb在fastbin中所对应的索引（在英文中也叫index；idx是index的缩写），这个索引决定着要向哪一个fastbin链表进行申请。

> fastbin的index是从0开始的，如上图所示。
>

```c
      mfastbinptr *fb = &fastbin (av, idx); 
---------------------------------------------------------------
mfastbinptr和fastbin(ar_ptr, idx)的定义如下：
typedef struct malloc_chunk *mfastbinptr;
#define fastbin(ar_ptr, idx) ((ar_ptr)->fastbinsY[idx])
......
```

fb是mfastbinptr（malloc_chunk）类型的指针，直接来看一下这行代码的执行结果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615535408495-1e74a433-c7ab-47ae-809a-edf68677747b.png)

```c
pwndbg> x/16gx &main_arena
0x7ffff7dcdc40 <main_arena>:	0x0000000000000000	0x0000000000000001
0x7ffff7dcdc50 <main_arena+16>:	0x0000555555756370	0x0000000000000000
    							#index0(0x20)		#index1(0x30)
0x7ffff7dcdc60 <main_arena+32>:	0x0000000000000000	0x0000000000000000
    							#index2(0x40)		#index3(0x50)
0x7ffff7dcdc70 <main_arena+48>:	0x0000000000000000	0x0000000000000000
    							#index4(0x60)		#index5(0x70)
0x7ffff7dcdc80 <main_arena+64>:	0x0000000000000000	0x0000000000000000
    							#index6(0x80)		#未启用		
0x7ffff7dcdc90 <main_arena+80>:	0x0000000000000000	0x0000000000000000
    							#未启用    		  #未启用
0x7ffff7dcdca0 <main_arena+96>:	0x0000555555756390	0x0000000000000000
    							#top_chunk			#last_remainder
0x7ffff7dcdcb0 <main_arena+112>:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
pwndbg> 
```

很明显，上述语句的含义是获取fastbinY[idx]中第一条链表所在的地址。

> + fb：是一个指针，这个指针指向main_arena+16
> + *fb：是一个值，代表着地址main_arena+16中存放的值
>

继续调试：

```c
      mchunkptr pp;
      victim = *fb;	
```

我们先忽略定义的pp变量，当victim被*fb赋值之后，victim的含义就显而易见了。在英语中victim是受害者；牺牲品的意思；在这里我们可以将victim引申为“将要malloc的堆块”。

> victim是malloc_chunk类型的指针
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615538095390-68781f9e-fe54-4d96-914b-b1c54a7f7c9e.png)

```c
      if (victim != NULL) 
	{ //现在fastbinY[idx]链表中有空闲的free chunk，进入if语句
```

```c
	  if (SINGLE_THREAD_P)  //此程序为单线程，进入if语句
	    *fb = victim->fd;	
	  else	
	    REMOVE_FB (fb, pp, victim); //当程序为多线程时
```

> 附：
>
> 查看当前进程（fastbin_demo）是否为多线程：
>
> ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615539240848-11645918-1203-493d-b9bc-eac6cd9f78ff.png)
>

接下来程序就会执行 *fb = victim->fd;，执行结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615539523633-093434c2-227d-44e4-9c0e-895b0dafaca0.png)

victim的fd指针的地址为0x555555756350，因此在执行此语句之后指针fb同样指向0x555555756350；

> 在执行此语句之前*fb的值为0x555555756370，现在*fb为0x555555756350。
>

由于*fb代表了fastbinY[idx]中最后插入此链表的free chunk，现在*fb发生了改变意味着victim已经从fastbinY[idx]链表中，pwndbg中的bin命令可以印证这一点：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615540044155-a4a21012-3ae3-4201-9f15-f5be42253969.png)

好了，victim已经从链表中取出，接下来会对victim进行安全性检查：

```c
	  if (__glibc_likely (victim != NULL))  //检测取下来的指针victim是否为NULL。
	    { //victim有效
	      size_t victim_idx = fastbin_index (chunksize (victim));
          //利用chunksize函数获取victim的size（忽略PREV_INUSE、IS_MMAPPED、NON_MAIN_ARENA三个标志位）
          //然后获取对应fastbinY的index
	      if (__builtin_expect (victim_idx != idx, 0)) //安全性检查，避免chunk的size被改写
		malloc_printerr ("malloc(): memory corruption (fast)"); //触发异常
	      check_remalloced_chunk (av, victim, nb); //细致的检查，在编译glibc时声明开启debug支持
```

Q：为什么要对chunk的size进行检查？

A：攻击者可以利用堆溢出等手段更改处于free状态的victim大小，在malloc时假若条件允许会将victim取出，如果此时的victim size已经被更改，当malloc时候会导致堆块的重叠和异常。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615541094784-f4ca5026-2949-41c5-a1a3-421d47b907cd.png)

但是要注意，此种情况要和fastbin的Chunk Extend and Overlapping这种攻击方式区别开，前者是在堆块free的时候修改size，后者是在堆块malloc时候修改：

```c
#include<stdio.h> //fastbin Chunk Extend and Overlapping
#include<stdlib.h> 
int main(void)
{
    void *ptr,*ptr1;

    ptr=malloc(0x10);//分配第一个0x10的chunk
    malloc(0x10);//分配第二个0x10的chunk

    *(long long *)((long long)ptr-0x8)=0x41;// 修改第一个块的size域(在malloc时)

    free(ptr);
    ptr1=malloc(0x30);// 实现 extend，控制了第二个块的内容
    return 0;
} //来自CTF-wiki
```

victim的脱链过程图解如下：

[fastbin.pptx](https://www.yuque.com/attachments/yuque/0/2021/pptx/574026/1615618605146-f71ad456-3cbd-4d8e-94b7-a5fe8f4ff9e3.pptx)

> 建议将PPT下载再进行查看
>

# 整理fastbin chunk到tcachebin
## free chunk从fastbin脱链
下面继续调试，只不过现在我们的目标换成了tcachebin：

```c
#if USE_TCACHE //如果开启了tcache机制
	      /* While we're here, if we see other chunks of the same size,
		 stash them in the tcache.  */ 
          //如果这个链表中还有其他的free chunk，为了提高速度，我们将其放到tcachebin中
	      size_t tc_idx = csize2tidx (nb); //将nb转化为tcache对应的index
```

上面的代码和fastbin的类似，都是将nb计算转化为tcachebin中对应的index：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615609891074-e65ac12c-6172-46d8-94f2-7c217a936cc7.png)

```c
	      if (tcache && tc_idx < mp_.tcache_bins) //tcache的含义之后会说
		{	 //若tcache已经初始化并且chunk对应的index在tcachebin的范围内
		  mchunkptr tc_victim;
```

接下来的if语句中的内容是重中之重：

```c
		  /* While bin not empty and tcache not full, copy chunks.  */
		  while (tcache->counts[tc_idx] < mp_.tcache_count
			 && (tc_victim = *fb) != NULL)
		    {
```

+ fastbinY[idx]对应大小的tcachebin链未满
+ fastbinY[idx]中仍有空闲的chunk

若程序满足上述条件会进入while循环开始解链，当程序执行到if (SINGLE_THREAD_P) 时我们来看一下结果：                             

> 注意将mp_.tcache_count和mp_.tcache_bins区分开。
>
> + mp_.tcache_count表示每条tcachebin链表中最多容纳free chunk数目
> + mp_.tcache_bins表示tcachebin中不同大小的链表总个数
>

解链过程和之前fastbin free chunk的完全相同：*fb = tc_victim->fd; 

效果如下：![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615612421620-10d2d280-cc5d-4f70-ba59-c27bacd6ee15.png)

## free chunk链入tcachebin
本质是调用tcache_put函数，源码如下：

```c
/* Caller must ensure that we know tc_idx is valid and there's room
   for more chunks.  */
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

在tcache_put函数中，传入函数的chunk代表着将要链入tcachebin的chunk，tc_idx是其对应的tcache index。

```c
  tcache_entry *e = (tcache_entry *) chunk2mem (chunk);
  assert (tc_idx < TCACHE_MAX_BINS);
```

当我们将free chunk 从fastbin中取出之后，使用chunk2mem将chunk的起始地址转化为chunk_data的地址，并让指针e指向该地址，然后判断tcachebin是否已满。

---

```c
p  /* Mark this chunk as "in the tcache" so the test in _int_free will
     detect a double free.  */ //
  e->key = tcache; //对移入tcache的chunk写入key指针，防止double free
//此key指针指向tcache_perthread_struct的data
```

> 代码中的tcache指向tcache_perthread_struct的起始地址+0x10
>

效果如下：

```c
#写入之前
pwndbg> x/16gx 0x555555756330
0x555555756330:	0x0000000000000000	0x0000000000000021 #malloc
0x555555756340:	0x0000000000000000	0x0000000000000000
0x555555756350:	0x0000000000000000	0x0000000000000021 #tc_victim
0x555555756360:	0x0000555555756330	0x0000000000000000
0x555555756370:	0x0000000000000000	0x0000000000000021 #fastbin
0x555555756380:	0x0000555555756350	0x0000000000000000
0x555555756390:	0x0000000000000000	0x0000000000020c71
0x5555557563a0:	0x0000000000000000	0x0000000000000000
pwndbg> 
#写入之后
pwndbg> x/16gx 0x555555756330
0x555555756330:	0x0000000000000000	0x0000000000000021 #malloc
0x555555756340:	0x0000000000000000	0x0000000000000000
0x555555756350:	0x0000000000000000	0x0000000000000021 #tc_victim
0x555555756360:	0x0000555555756330	0x0000555555756010
    								#here～
0x555555756370:	0x0000000000000000	0x0000000000000021 #fastbin
0x555555756380:	0x0000555555756350	0x0000000000000000
0x555555756390:	0x0000000000000000	0x0000000000020c71
0x5555557563a0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

---

```c
  e->next = tcache->entries[tc_idx];
```

上述代码的作用是向chunk的next位中写入tcache_perthread_struct的entries：

> entries始终为最后插入某个tcachebin的free chunk的userdata的起始地址（即tc_victim+0x10），因为原来此链表中没有free chunk，因此next指针为NULL。
>

```c
pwndbg> x/16gx 0x555555756330
0x555555756330:	0x0000000000000000	0x0000000000000021 #malloc
0x555555756340:	0x0000000000000000	0x0000000000000000
0x555555756350:	0x0000000000000000	0x0000000000000021 #tcachebin
0x555555756360:	0x0000000000000000	0x0000555555756010
    			#here～
0x555555756370:	0x0000000000000000	0x0000000000000021 #fastbin
0x555555756380:	0x0000555555756350	0x0000000000000000
0x555555756390:	0x0000000000000000	0x0000000000020c71
0x5555557563a0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

现在free chunk已经被链入tcachebin中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615615286733-574ba54c-730f-46f2-9c8c-20dafff1a1cc.png)

最后执行如下代码：

```c
  tcache->entries[tc_idx] = e; //设置entries
  ++(tcache->counts[tc_idx]); //counts数量++
------------------------------------------------------------------
执行前：
pwndbg> x/76gx 0x555555756000
0x555555756000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
......（省略内存均为0）
0x555555756250:	0x0000000000000000	0x0000000000000021
pwndbg> 
------------------------------------------------------------------
执行后：
pwndbg> x/76gx 0x555555756000
0x555555756000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x555555756010:	0x0000000000000001	0x0000000000000000
    			#tcache->counts[tc_idx]
0x555555756020:	0x0000000000000000	0x0000000000000000
0x555555756030:	0x0000000000000000	0x0000000000000000
0x555555756040:	0x0000000000000000	0x0000000000000000
0x555555756050:	0x0000555555756360	0x0000000000000000
    			#tcache->entries[tc_idx]
......
0x555555756250:	0x0000000000000000	0x0000000000000021
pwndbg>
```

若fastbin中还有free chunk且tcachebin有空位会继续移入：

```c
/*
   ------------------------------ malloc ------------------------------
 */

static void *
_int_malloc (mstate av, size_t bytes)
{
......
  if ((unsigned long) (nb) <= (unsigned long) (get_max_fast ()))
    {
	......(从fastbin中申请chunk)
#if USE_TCACHE
	      /* While we're here, if we see other chunks of the same size,
		 stash them in the tcache.  */
	      size_t tc_idx = csize2tidx (nb);
	      if (tcache && tc_idx < mp_.tcache_bins)
		{
		  mchunkptr tc_victim;

		  /* While bin not empty and tcache not full, copy chunks.  */
		  while (tcache->counts[tc_idx] < mp_.tcache_count
			 && (tc_victim = *fb) != NULL)  
		    {
              
				......（freechunk从fastbin中脱链）
		      tcache_put (tc_victim, tc_idx); //移入tcachebin中
		    }
		}
#endif  //当tcachebin已满时
	      void *p = chunk2mem (victim);  //将fastbin中申请的chunk置为malloc状态
	      alloc_perturb (p, bytes);
	      return p;  //返回从chunk的指针
	    }
	}
    }
```

在while循环终止后会返回victim。

另外，fastbin的chunk被放入tcachebin后chunk顺序会颠倒，比如：

+ fastbin：chunk1、chunk2、chunk3
+ tcachebin：NULL

整理之后：

+ fastbin：NULL
+ tcachebin：chunk3、chunk2、chunk1

