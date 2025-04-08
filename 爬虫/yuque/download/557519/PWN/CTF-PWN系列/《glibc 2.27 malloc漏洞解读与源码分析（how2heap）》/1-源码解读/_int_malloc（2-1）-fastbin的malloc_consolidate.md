# 关键词
+ malloc_consolidate
+ fastbin合并到unsortedbin
+ unsortedbin结构

# 源码浏览
这篇文章将要研究malloc_consolidate代码：

```c
  /*
     If a small request, check regular bin.  Since these "smallbins"
     hold one size each, no searching within bins is necessary.
     (For a large request, we need to wait until unsorted chunks are
     processed to find best fit. But for small ones, fits are exact
     anyway, so we can check now, which is faster.)
   */

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
  mfastbinptr*    fb;                 /* current fastbin being consolidated */
  mfastbinptr*    maxfb;              /* last fastbin (for loop control) */
  mchunkptr       p;                  /* current chunk being consolidated */
  mchunkptr       nextp;              /* next chunk to consolidate */
  mchunkptr       unsorted_bin;       /* bin header */
  mchunkptr       first_unsorted;     /* chunk to link to */

  /* These have same use as in free() */
  mchunkptr       nextchunk;
  INTERNAL_SIZE_T size;
  INTERNAL_SIZE_T nextsize;
  INTERNAL_SIZE_T prevsize;
  int             nextinuse;
  mchunkptr       bck;
  mchunkptr       fwd;

  atomic_store_relaxed (&av->have_fastchunks, false);

  unsorted_bin = unsorted_chunks(av);

  /*
    Remove each chunk from fast bin and consolidate it, placing it
    then in unsorted bin. Among other reasons for doing this,
    placing in unsorted bin avoids needing to calculate actual bins
    until malloc is sure that chunks aren't immediately going to be
    reused anyway.
  */

  maxfb = &fastbin (av, NFASTBINS - 1);
  fb = &fastbin (av, 0);
  do {
    p = atomic_exchange_acq (fb, NULL);
    if (p != 0) {
      do {
	{
	  unsigned int idx = fastbin_index (chunksize (p));
	  if ((&fastbin (av, idx)) != fb)
	    malloc_printerr ("malloc_consolidate(): invalid chunk size");
	}

	check_inuse_chunk(av, p);
	nextp = p->fd;

	/* Slightly streamlined version of consolidation code in free() */
	size = chunksize (p);
	nextchunk = chunk_at_offset(p, size);
	nextsize = chunksize(nextchunk);

	if (!prev_inuse(p)) {
	  prevsize = prev_size (p);
	  size += prevsize;
	  p = chunk_at_offset(p, -((long) prevsize));
	  unlink(av, p, bck, fwd);
	}

	if (nextchunk != av->top) {
	  nextinuse = inuse_bit_at_offset(nextchunk, nextsize);

	  if (!nextinuse) {
	    size += nextsize;
	    unlink(av, nextchunk, bck, fwd);
	  } else
	    clear_inuse_bit_at_offset(nextchunk, 0);

	  first_unsorted = unsorted_bin->fd;
	  unsorted_bin->fd = p;
	  first_unsorted->bk = p;

	  if (!in_smallbin_range (size)) {
	    p->fd_nextsize = NULL;
	    p->bk_nextsize = NULL;
	  }

	  set_head(p, size | PREV_INUSE);
	  p->bk = unsorted_bin;
	  p->fd = first_unsorted;
	  set_foot(p, size);
	}

	else {
	  size += nextsize;
	  set_head(p, size | PREV_INUSE);
	  av->top = p;
	}

      } while ( (p = nextp) != 0);

    }
  } while (fb++ != maxfb);
}
```

# 例子展示
```c
#include<string.h>
#include<stdio.h>
#include<stdlib.h>
int main(){
    void *p[10]={0};
    for(int i = 0 ; i<10;i++){
	    p[i]=malloc(0x20);		 //申请10个大小为0x20的堆块
    }
    void *ptr,*ptr1,*ptr2;
    ptr = malloc(0x30);          //avoid merge with top chunk（防止如上的chunk接触到top_chunk，避免释放的时候并入top_chunk）
    
    for(int m = 0 ;m <10 ;m++){
	    free(p[m]);		         //free掉刚刚申请的10个chunk，7个填满tcachebin，3个放入fastbin中
	    p[m]=NULL;
    }

    ptr1 = malloc(0x400);		//申请一个largechunk(大小大于0x3F0)，fastbin chunk将会合入到unsortedbin然后放入到smallbin中
    ptr2= malloc(0x80);			//申请smallbin中的chunk
    return 0;
}
```

> 编译命令：gcc -g smallbin.c -o smallbin
>

假如说你没有看懂上面代码的注释写的是什么，没关系，编译完成之后对其开始调试。

# 调试
## 第一次内循环
```powershell
注意：在调试之前首先要关闭地址随机化
ubuntu@ubuntu:~/Desktop/malloc$ sudo su
root@ubuntu:/home/ubuntu/Desktop/malloc# echo 0 > /proc/sys/kernel/randomize_va_space
root@ubuntu:/home/ubuntu/Desktop/malloc# exit
exit
ubuntu@ubuntu:~/Desktop/malloc$
```

开头展示了malloc_consolidate的源码，当tcachebin、fastbin、smallbin均无法满足nb时，就会进入到else分支中调用malloc_consolidate函数对fastbin中所有的free chunk进行整理合并放入unsortedbin；之后malloc会将unsortedbin中所有free chunk放入到smallbin或largebin，这个操作会牵扯到另一部分glibc源码，这里先不用管。在按照前一篇文章的方式引入malloc源码之后，对代码17行下断点，运行：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615723209433-840c1a0e-7dfe-4b2e-a48e-9be94dfb8422.png)

现在tcachebin的0x30这条链已经被填满并且fastbin中已经有了3个free chunk，heap情况如下：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x555555756000
Size: 0x251

Free chunk (tcache) | PREV_INUSE
Addr: 0x555555756250
Size: 0x31
fd: 0x00

Free chunk (tcache) | PREV_INUSE
Addr: 0x555555756280
Size: 0x31
fd: 0x555555756260

Free chunk (tcache) | PREV_INUSE
Addr: 0x5555557562b0
Size: 0x31
fd: 0x555555756290

Free chunk (tcache) | PREV_INUSE
Addr: 0x5555557562e0
Size: 0x31
fd: 0x5555557562c0

Free chunk (tcache) | PREV_INUSE
Addr: 0x555555756310
Size: 0x31
fd: 0x5555557562f0

Free chunk (tcache) | PREV_INUSE
Addr: 0x555555756340
Size: 0x31
fd: 0x555555756320

Free chunk (tcache) | PREV_INUSE
Addr: 0x555555756370
Size: 0x31
fd: 0x555555756350

Free chunk (fastbins) | PREV_INUSE
Addr: 0x5555557563a0
Size: 0x31
fd: 0x00

Free chunk (fastbins) | PREV_INUSE
Addr: 0x5555557563d0
Size: 0x31
fd: 0x5555557563a0

Free chunk (fastbins) | PREV_INUSE
Addr: 0x555555756400
Size: 0x31
fd: 0x5555557563d0

Allocated chunk | PREV_INUSE
Addr: 0x555555756430
Size: 0x41

Top chunk | PREV_INUSE
Addr: 0x555555756470
Size: 0x20b91

pwndbg> 
```

> 这里的3个fastbin free chunk是相邻的
>

单步步入代码17行的malloc，由于要申请的chunk大小（nb）tcache、fast、smallbin均无法满足，因此会跳转到largebin分支：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615723462693-f66ff72a-cce5-43e7-8497-baeb60546b40.png)

```c
  else
    {
      idx = largebin_index (nb);
      if (atomic_load_relaxed (&av->have_fastchunks))   //判断fastbin中是否有free chunk
        malloc_consolidate (av);
    } 
//av->have_fastchunks的含义之前说过
```

源码如上所示，glibc首先算出要申请堆块的largebin idx（确定是largebin的哪一条链），然后进入if语句中的malloc_consolidate：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615724105856-d3b76403-d0c2-4a2f-82d8-959f760c355d.png)

> nb==1040==0x410
>

接下来开始调试malloc_consolidate的源码：

```c
static void malloc_consolidate(mstate av)
{
  mfastbinptr*    fb;                 /* current fastbin being consolidated */
  mfastbinptr*    maxfb;              /* last fastbin (for loop control) */
  mchunkptr       p;                  /* current chunk being consolidated */
  mchunkptr       nextp;              /* next chunk to consolidate */
  mchunkptr       unsorted_bin;       /* bin header */
  mchunkptr       first_unsorted;     /* chunk to link to */

  /* These have same use as in free() */
  mchunkptr       nextchunk;
  INTERNAL_SIZE_T size;
  INTERNAL_SIZE_T nextsize;
  INTERNAL_SIZE_T prevsize;
  int             nextinuse;
  mchunkptr       bck;
  mchunkptr       fwd;

  atomic_store_relaxed (&av->have_fastchunks, false);

  unsorted_bin = unsorted_chunks(av);

  /*
    Remove each chunk from fast bin and consolidate it, placing it
    then in unsorted bin. Among other reasons for doing this,
    placing in unsorted bin avoids needing to calculate actual bins
    until malloc is sure that chunks aren't immediately going to be
    reused anyway.
  */

  maxfb = &fastbin (av, NFASTBINS - 1);
  fb = &fastbin (av, 0);
  do {
    p = atomic_exchange_acq (fb, NULL);
    if (p != 0) {
      do {
	{
	  unsigned int idx = fastbin_index (chunksize (p));
	  if ((&fastbin (av, idx)) != fb)
	    malloc_printerr ("malloc_consolidate(): invalid chunk size");
	}

	check_inuse_chunk(av, p);
	nextp = p->fd;

	/* Slightly streamlined version of consolidation code in free() */
	size = chunksize (p);
	nextchunk = chunk_at_offset(p, size);
	nextsize = chunksize(nextchunk);

	if (!prev_inuse(p)) {
	  prevsize = prev_size (p);
	  size += prevsize;
	  p = chunk_at_offset(p, -((long) prevsize));
	  unlink(av, p, bck, fwd);
	}

	if (nextchunk != av->top) {
	  nextinuse = inuse_bit_at_offset(nextchunk, nextsize);

	  if (!nextinuse) {
	    size += nextsize;
	    unlink(av, nextchunk, bck, fwd);
	  } else
	    clear_inuse_bit_at_offset(nextchunk, 0);

	  first_unsorted = unsorted_bin->fd;
	  unsorted_bin->fd = p;
	  first_unsorted->bk = p;

	  if (!in_smallbin_range (size)) {
	    p->fd_nextsize = NULL;
	    p->bk_nextsize = NULL;
	  }

	  set_head(p, size | PREV_INUSE);
	  p->bk = unsorted_bin;
	  p->fd = first_unsorted;
	  set_foot(p, size);
	}

	else {
	  size += nextsize;
	  set_head(p, size | PREV_INUSE);
	  av->top = p;
	}

      } while ( (p = nextp) != 0);

    }
  } while (fb++ != maxfb);
}
```

在这个函数中传入的参数只有av一个，在之前说过av是指向main_arena的；继续调试到malloc_consolidate源码的第21行：

```c
  unsorted_bin = unsorted_chunks(av);
```

当执行了这行代码之后，结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615725173744-00d0e9fb-d540-4d96-8321-b596beac1d46.png)

很明显，这行代码是获取unsortedbin在main_arena的地址（这样说可能不太准确，能理解意思吧？）

```c
maxfb = &fastbin (av, NFASTBINS - 1); //maxfb指针指向&fastbinY[9]
fb = &fastbin (av, 0);	//fb指针指向&fastbinY[0]
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615725847623-bf66909f-d9d6-4cf4-b71e-304d2e8a0908.png)

程序无条件进入do while循环：

```c
  do {
    p = atomic_exchange_acq (fb, NULL);//将NULL存入*fb，并返回旧的*fb
	if (p != 0) {
      do {
	{
       ...... 
    }
      }
  } while (fb++ != maxfb);  //循环终止的条件，待会儿仔细说
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615726576114-00438eb9-1d46-4f0c-ac14-8ec9f31c80f0.png)

如上图所示，由于现在的指针p==NULL，因此不会进入if语句从而执行fb++，判断之后进入下一次循环：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615727729956-42b7db8a-949f-4f95-baab-5b15452da85f.png)

fb++之后*fb为fastbinY[1]链表上的最后被free的chunk的地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615728339977-7c81f261-194f-449e-8e8b-6ec422a81a05.png)

进入第二次do while循环，结果如下图所示：

```c
    p = atomic_exchange_acq (fb, NULL);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615729024538-388bea51-4331-473b-abad-cde48f0e80c7.png)![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615774977321-124b02c0-3c26-4c4e-8677-f32491e604d9.png)

> 由于main_arena中的指针已经被置NULL，因此在fastbin中已经不再显示，如上图所示。
>

和第一次一样，将NULL拷贝到*fb，备份让p指针指向原*fb的值，之后会进入if中的do while循环：

```c
    if (p != 0) {
      do {
	{
	  unsigned int idx = fastbin_index (chunksize (p));
	  if ((&fastbin (av, idx)) != fb)
	    malloc_printerr ("malloc_consolidate(): invalid chunk size");
	}

	check_inuse_chunk(av, p);
	nextp = p->fd;

	/* Slightly streamlined version of consolidation code in free() */
	size = chunksize (p);
	nextchunk = chunk_at_offset(p, size);
	nextsize = chunksize(nextchunk);

	if (!prev_inuse(p)) {
	  prevsize = prev_size (p);
	  size += prevsize;
	  p = chunk_at_offset(p, -((long) prevsize));
	  unlink(av, p, bck, fwd);
	}

	if (nextchunk != av->top) {
	  nextinuse = inuse_bit_at_offset(nextchunk, nextsize);

	  if (!nextinuse) {
	    size += nextsize;
	    unlink(av, nextchunk, bck, fwd);
	  } else
	    clear_inuse_bit_at_offset(nextchunk, 0);

	  first_unsorted = unsorted_bin->fd;
	  unsorted_bin->fd = p;
	  first_unsorted->bk = p;

	  if (!in_smallbin_range (size)) {
	    p->fd_nextsize = NULL;
	    p->bk_nextsize = NULL;
	  }

	  set_head(p, size | PREV_INUSE);
	  p->bk = unsorted_bin;
	  p->fd = first_unsorted;
	  set_foot(p, size);
	}

	else {
	  size += nextsize;
	  set_head(p, size | PREV_INUSE);
	  av->top = p;
	}

      } while ( (p = nextp) != 0);

    }
```

上面的代码看的头疼，继续调试吧，这样理解更到位：

```c
	{
	  unsigned int idx = fastbin_index (chunksize (p));
	  if ((&fastbin (av, idx)) != fb)
	    malloc_printerr ("malloc_consolidate(): invalid chunk size");
	}
```

和前一篇的文章中的代码相同，首先判断fastbin中的chunk大小是否发生了伪造，这里不再多说，继续：

```c
	check_inuse_chunk(av, p);
```

check_inuse_chunk(av,p)相当于do_check_inuse_chunk(av,p)，

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615730425134-3a354722-a8e7-43de-a308-bfecde8bae81.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615730511982-4e86e652-f5a7-4f9b-8e61-844faac56d3c.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615730565137-a9919a84-df29-4232-830b-3f6210f37229.png)

> 当PREV_INUSE为1时代表**<font style="color:#F5222D;">前一个</font>**chunk正处于malloc状态，free则为0
>

此函数目的是通过**<font style="color:#F5222D;">获取相邻</font>****<font style="color:#F5222D;">下一个</font>**chunk的PREV_INUSE标识位去检查p**<font style="color:#F5222D;">是否真正处于free状态，</font>**若为inuse(p)==0会触发assert断言。

此处没有触发assert，因此inuse(p)的值为1，由于宏定义PREV_INUSE==0x1，因此(((char *) (p))+ chunksize (p)))->mchunk_size)一定是0x41、0x31等类似的值，这里有两种情况：

+ p chunk未被free，
+ tcachebin、fastbin及其相邻的下一个chunk的**<font style="color:#F5222D;">PREV_INUSE位总是为1</font>**

```c
nextp = p->fd;
```

在这条语句（nextp = p->fd）中，由于p指向fastbinY[idx]链中最后一个被free的chunk（0x555555756400），因此fd指针是指向倒数第二个的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615774836022-7c960d72-9224-48f2-b3e1-26d09d099f16.png)

因此执行完成之后nextp的值如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615774547114-1b4e6b67-781f-4258-b82b-e4a232d9b2b1.png)

继续向下看：

```c
	size = chunksize (p); //得到除去A、M、P标志位之后的size域
	nextchunk = chunk_at_offset(p, size); //将位于p+size处的内存区域视为一个malloc_chunk，并将对应的指针返回
	nextsize = chunksize(nextchunk); //同上
```

调试结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615775744128-b2902d88-9477-4024-88ce-ca8457d16bd8.png)

这几条语句的作用获得了与p chunk紧邻的下一个chunk的信息：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615775939834-9bb60976-16fa-4b2f-9fe2-a9f354943579.png)

现在nextchunk指向0x555555756430。

```c
	if (!prev_inuse(p)) { //获取p chunk的PREV_INUSE位的值，当检测到此值为0时（前一个chunk处于free时（fastbin、tcachebin除外）），对其进行unlink
	  prevsize = prev_size (p);
	  size += prevsize;
	  p = chunk_at_offset(p, -((long) prevsize));
	  unlink(av, p, bck, fwd);  //进行unlink
	}
```

prev_inuse宏定义定义如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615777131210-917e82f4-c435-493d-9434-37e841f170f0.png)

因此，程序不会进入if语句而是进入下一个if语句的判断：

```c
if (nextchunk != av->top) {
		......
	else {
		......
	}
```

我们知道av是指向main_arena的：

```c
pwndbg> p av 
$41 = (mstate) 0x7ffff7dcdc40 <main_arena>
pwndbg> p *av 
$42 = {
  mutex = 0, 
  flags = 0, 
  have_fastchunks = 0, 
  fastbinsY = {0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}, 
  top = 0x555555756470, 
  last_remainder = 0x0, 
  bins = {0x7ffff7dcdca0 <main_arena+96>, 0x7ffff7dcdca0 <main_arena+96>, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcb0 <main_arena+112>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcc0 <main_arena+128>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdcd0 <main_arena+144>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdce0 <main_arena+160>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdcf0 <main_arena+176>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd00 <main_arena+192>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd10 <main_arena+208>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd20 <main_arena+224>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd30 <main_arena+240>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd40 <main_arena+256>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd50 <main_arena+272>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd60 <main_arena+288>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd70 <main_arena+304>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd80 <main_arena+320>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdd90 <main_arena+336>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcdda0 <main_arena+352>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddb0 <main_arena+368>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddc0 <main_arena+384>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcddd0 <main_arena+400>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcdde0 <main_arena+416>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcddf0 <main_arena+432>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde00 <main_arena+448>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde10 <main_arena+464>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde20 <main_arena+480>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde30 <main_arena+496>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde40 <main_arena+512>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde50 <main_arena+528>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde60 <main_arena+544>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde70 <main_arena+560>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde80 <main_arena+576>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcde90 <main_arena+592>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdea0 <main_arena+608>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdeb0 <main_arena+624>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcdec0 <main_arena+640>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcded0 <main_arena+656>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdee0 <main_arena+672>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdef0 <main_arena+688>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf00 <main_arena+704>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf10 <main_arena+720>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf20 <main_arena+736>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf30 <main_arena+752>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf40 <main_arena+768>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf50 <main_arena+784>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf60 <main_arena+800>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf70 <main_arena+816>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf80 <main_arena+832>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdf90 <main_arena+848>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfa0 <main_arena+864>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfb0 <main_arena+880>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfc0 <main_arena+896>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfd0 <main_arena+912>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdfe0 <main_arena+928>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dcdff0 <main_arena+944>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce000 <main_arena+960>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce010 <main_arena+976>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce020 <main_arena+992>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce030 <main_arena+1008>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce040 <main_arena+1024>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce050 <main_arena+1040>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce060 <main_arena+1056>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce070 <main_arena+1072>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce080 <main_arena+1088>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce090 <main_arena+1104>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0a0 <main_arena+1120>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0b0 <main_arena+1136>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0c0 <main_arena+1152>, 0x7ffff7dce0d0 <main_arena+1168>, 0x7ffff7dce0d0 <main_arena+1168>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0e0 <main_arena+1184>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce0f0 <main_arena+1200>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce100 <main_arena+1216>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce110 <main_arena+1232>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce120 <main_arena+1248>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce130 <main_arena+1264>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce140 <main_arena+1280>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce150 <main_arena+1296>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce160 <main_arena+1312>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce170 <main_arena+1328>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce180 <main_arena+1344>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce190 <main_arena+1360>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1a0 <main_arena+1376>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1b0 <main_arena+1392>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1c0 <main_arena+1408>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1d0 <main_arena+1424>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1e0 <main_arena+1440>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce1f0 <main_arena+1456>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce200 <main_arena+1472>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce210 <main_arena+1488>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce220 <main_arena+1504>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce230 <main_arena+1520>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce240 <main_arena+1536>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce250 <main_arena+1552>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce260 <main_arena+1568>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce270 <main_arena+1584>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce280 <main_arena+1600>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce290 <main_arena+1616>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2a0 <main_arena+1632>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2b0 <main_arena+1648>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2c0 <main_arena+1664>, 0x7ffff7dce2d0 <main_arena+1680>, 0x7ffff7dce2d0 <main_arena+1680>...}, 
  binmap = {0, 0, 0, 0}, 
  next = 0x7ffff7dcdc40 <main_arena>, 
  next_free = 0x0, 
  attached_threads = 1, 
  system_mem = 135168, 
  max_system_mem = 135168
}
pwndbg> 
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615778270978-295c7717-ca54-4e88-8fe2-b954112594b9.png)

```c
	if (nextchunk != av->top) {  //判断p chunk的下一个chunk是否为top_chunk
		......   //不是
	else {
		......	 //是
	}
```

很显然，p的下一个chunk不是top_chunk，因此进入if语句：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615778896771-4705320d-a9f9-4ba6-92c2-553bdc4794f4.png)

之后调用宏函数inuse_bit_at_offset：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615794058763-35b16134-db65-481f-b133-a2b72f8735ab.png)

PREV_INUSE的作用之前说过，那么此函数的作用是获取p chunk状态（malloc or free）；因为p chunk为处于fastbin中，函数返回值nextinuse为1；

程序会进入else分支：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615794460532-d56b25a8-e200-436e-bcb9-54e08fe0d1cf.png)

看一眼这个函数名称就知道它是用来清除next chunk的PREV_INUSE位的，如下图：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615794675875-e5c0deca-11be-43d8-96d8-97d36733a8f3.png)

```c
pwndbg> x/20gx 0x5555557563a0
0x5555557563a0:	0x0000000000000000	0x0000000000000031
0x5555557563b0:	0x0000000000000000	0x0000000000000000
0x5555557563c0:	0x0000000000000000	0x0000000000000000
0x5555557563d0:	0x0000000000000000	0x0000000000000031
0x5555557563e0:	0x00005555557563a0	0x0000000000000000
0x5555557563f0:	0x0000000000000000	0x0000000000000000
0x555555756400:	0x0000000000000000	0x0000000000000031
0x555555756410:	0x00005555557563d0	0x0000000000000000
0x555555756420:	0x0000000000000000	0x0000000000000000
0x555555756430:	0x0000000000000000	0x0000000000000040 #here
pwndbg> 

```

接下来会将p chunk链入unsortedbin中：

```c
	  first_unsorted = unsorted_bin->fd;  
	  unsorted_bin->fd = p;
	  first_unsorted->bk = p;

	  if (!in_smallbin_range (size)) {
	    p->fd_nextsize = NULL;
	    p->bk_nextsize = NULL;
	  }

	  set_head(p, size | PREV_INUSE);
	  p->bk = unsorted_bin;
	  p->fd = first_unsorted;
	  set_foot(p, size);
```

首先来看：

```c
	  first_unsorted = unsorted_bin->fd;  //获取对应的main_arena指针
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615795170192-4224c183-4cc5-414c-b25b-169cda2b32cd.png)

```c
	  unsorted_bin->fd = p;   //将p chunk链入unsortedbin：设置main_arena+112
	  first_unsorted->bk = p; //将p chunk链入unsortedbin：设置main_arena+120
```

> unsorted_bin->fd = p：
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615795342296-17e3cd8c-0a00-4c02-97ac-c2b00f67a1a4.png)

> first_unsorted->bk = p：
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615795424185-4e617202-6247-4a1b-8811-ea0ec87426f5.png)继续看如下代码：

```c
	  if (!in_smallbin_range (size)) {	//size是p chunk的大小，这里判断p chunk是否为large chunk
	    p->fd_nextsize = NULL;			//因为在unsortedbin中的largebin chunk没有fd_nextsize和bk_nextsize指针
	    p->bk_nextsize = NULL;
	  }
```

现在chunk的状态如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615796007245-2e64e9f3-89a2-4a4d-88fa-b14acf414f02.png)

```c
	  set_head(p, size | PREV_INUSE);   //设置p chunk的size为（size|PREV_INUSE）
	  p->bk = unsorted_bin;  //设置p的bk位
	  p->fd = first_unsorted;//设置p的fd位
		//设置完fd和bk位之后，p chunk才算是链入到了unsortedbin中
	  set_foot(p, size); //设置下一个chunk的mchunk_prev_size
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615797396224-4e454af1-194c-435f-a2e2-0534a5100423.png)

> 49==0x31
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615797518031-70367499-e56d-4315-a034-833db3c870e3.png)

> 设置这两个函数是为了方便对chunk的size（即：mchunk_size）和下一个chunk的mchunk_prev_size域进行设置
>

结果如下：

```c
pwndbg> x/20gx 0x5555557563a0
0x5555557563a0:	0x0000000000000000	0x0000000000000031
0x5555557563b0:	0x0000000000000000	0x0000000000000000
0x5555557563c0:	0x0000000000000000	0x0000000000000000
0x5555557563d0:	0x0000000000000000	0x0000000000000031 #nextp
									#set_head
0x5555557563e0:	0x00005555557563a0	0x0000000000000000
0x5555557563f0:	0x0000000000000000	0x0000000000000000
0x555555756400:	0x0000000000000000	0x0000000000000031 #p chunk //注意这个size为0x31而不是0x30
0x555555756410:	0x00007ffff7dcdca0	0x00007ffff7dcdca0 
0x555555756420:	0x0000000000000000	0x0000000000000000
0x555555756430:	0x0000000000000030	0x0000000000000040 #nextchunk
				#set_foot
pwndbg> 
```

<font style="background-color:transparent;">现在chunk已经完全放到了unsortedbin中：</font>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615798582012-b3e0116a-517d-4739-83cc-d44a87927e08.png)

<font style="background-color:transparent;">进入最终的一步：</font>

```c
while ( (p = nextp) != 0); 
//首先将nextp（在这里nextp是倒数第二个放入bin中的chunk）赋值给p，然后判断p是否为0 
//（直到遍历完当前fastbinY[idx]链表中所有free chunk）
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615801783273-f68eb552-ec5e-45f5-9673-c63a3286920e.png)

> 由于fastbin free已经被断链（*main_arena+24==NULL），所以gdb不再认为该chunk为free chunk
>

## <font style="background-color:transparent;">第二次内循环</font>
> tips：p是将要放入到unsortedbin的chunk，nextchunk是p的相邻下一个chunk，nextp是p的相邻上一个chunk
>

第二次的调试过程省略着写，现在要放入unsortedbin的chunk为0x5555557563d0：

```c
do {
	{
	  unsigned int idx = fastbin_index (chunksize (p));
	  if ((&fastbin (av, idx)) != fb)  //检查待加入unsortedbin的free chunk的大小
	    malloc_printerr ("malloc_consolidate(): invalid chunk size");
	}
    check_inuse_chunk(av, p); 
    		//通过检查next chunk的PREV_INUSE位来检查此chunk的free状态（只有tcachebin、fastbin和处于malloc状态的p chunk不会触发assert）
    	nextp = p->fd; //获取上一个相邻chunk的地址

	/* Slightly streamlined version of consolidation code in free() */
	size = chunksize (p);  //获取除去A、M、P标志位之后的size
	nextchunk = chunk_at_offset(p, size);  //获取下一个chunk的起始地址
	nextsize = chunksize(nextchunk); //获取除去A、M、P标志位之后的next chunk size
```

现在本地变量的值如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615807039880-be8d813f-5b29-40f4-975a-10da3b686695.png)

继续向下调试：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1617672447339-3f59c357-0d35-4209-9f01-3ea0f190f143.png)

```c
	if (!prev_inuse(p)) { //获取p chunk的PREV_INUSE，结果为1，不会进入if语句
	  prevsize = prev_size (p);
	  size += prevsize;
	  p = chunk_at_offset(p, -((long) prevsize));
	  unlink(av, p, bck, fwd);
	}

	if (nextchunk != av->top) { //下一个chunk不是top_chunk，进入if语句
	  nextinuse = inuse_bit_at_offset(nextchunk, nextsize);//获取nextchunk的状态
	  if (!nextinuse) {	//nextinuse==0，为真，进入if语句
	    size += nextsize;	
	    unlink(av, nextchunk, bck, fwd);
	  } else
	    clear_inuse_bit_at_offset(nextchunk, 0);
```

接下来是一个很重要的地方，因为牵扯到unlink：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615809726640-379331b7-af71-42da-afa9-758edc21a363.png)

首先执行这条语句：

```c
	  size += nextsize; //size、nextsize分别是p chunk和相邻下一个chunk的总大小（不计算A、M、P标志位）
 	  //请务必注意这一点
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615809844208-0fd55660-8621-4781-8b98-102b5d180d9a.png)

> 48==0x30
>

执行结果：size==96（0x60），然后执行unlink语句，unlink是一个宏函数，其定义如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615810089274-2fa634c6-075a-4793-bb05-e309ad417e21.png)

md，这么长，硬着头皮上吧。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1615809029507-e718749a-9531-4ccb-9b62-a5826da24a5d.png)

先来看一下传入unlink的四个参数：

+ av：指针，指向main_arena
+ nextchunk：指针，指向p chunk的下一个chunk
+ bck：已定义但其值未初始化
+ fwd：已定义但其值未初始化

> 语雀文章写长了之后会卡，下一篇文章见～
>

