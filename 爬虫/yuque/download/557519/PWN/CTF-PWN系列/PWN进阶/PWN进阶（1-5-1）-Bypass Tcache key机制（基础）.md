> 参考资料：
>
> [https://www.anquanke.com/post/id/219292](https://www.anquanke.com/post/id/219292)
>
> [https://xz.aliyun.com/t/7292](https://xz.aliyun.com/t/7292)
>
> [https://www.anquanke.com/post/id/194960](https://www.anquanke.com/post/id/194960) #glibc-2.29新增的保护机制学习总结
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1AnmF44GJlOGYMcFd8466tw](https://pan.baidu.com/s/1AnmF44GJlOGYMcFd8466tw)  密码: h30i
>
> --来自百度网盘超级会员V3的分享
>

# 前言
万万没想到，Tcache的key机制竟然会出现在libc 2.27上，这个是在做2021的*CTF遇到的，之前没有遇到过，也没有碰过，就顺手记录一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611127959640-05c7c55b-efdb-46a3-be2d-551ac17f11ed.png)

本来以为Tcache的Key机制只会在libc-2.29及以上版本出现，但是从星盟的WP中可以得知，由于ubuntu的2.27-3ubuntu1.3的更新，导致在libc-2.27版本上出现了Key机制。

# key的出现原因
在之前的旧版本，填满tcachebin非常简单粗暴，如果程序不清空指针，可以由头到尾free同一个chunk，直接把tcachebin填满，但在libc-2.27.so（libc-2.29.so）更新之后这个方法不再适用。下面看一下关于tcachebin的源码，看看这个新指针起到如何的作用。

# 源码审计
看一下更新之后的libc-2.27.so的源码，主要改动如下：

## 1.Tcache结构体定义变更
> 下面所说的key和e->key是一个东西
>

### 原始定义
```c
/* We overlay this structure on the user-data portion of a chunk when
   the chunk is stored in the per-thread cache.  */
typedef struct tcache_entry
{
  struct tcache_entry *next;
} tcache_entry;
```

### 新定义
```c
/* We overlay this structure on the user-data portion of a chunk when
   the chunk is stored in the per-thread cache.  */
typedef struct tcache_entry
{
  struct tcache_entry *next;
  /* This field exists to detect double frees.  */
  struct tcache_perthread_struct *key; /* 新增指针 */
} tcache_entry;
```

从上面对key指针注释可以看到，它的存在可以防止tcachebin中double free，并且这个指针放在bk的位置

### 意义
在tcache_entry结构体中增加8个字节（64位）的tcache_perthread_struct *key，这个key指针放在每个chunk 的bk指针的位置，为之后double free的检测奠定基础。

## 2.加入对tcache数量限制
### 原始定义
无

### 新定义
```c
#define MAX_TCACHE_COUNT 127    /* Maximum value of counts[] entries.  */
```

新加入了MAX_TCACHE_COUNT的宏定义，所有tcachebin的数目加起来最大数量为127。

### 意义
限制tcachebin中的chunk数量

## 3.tcache_put加入了新步骤
### 原始定义
```c
/* Caller must ensure that we know tc_idx is valid and there's room
   for more chunks.  */
static __always_inline void tcache_put (mchunkptr chunk, size_t tc_idx)
{
  tcache_entry *e = (tcache_entry *) chunk2mem (chunk);
  assert (tc_idx < TCACHE_MAX_BINS);
  e->next = tcache->entries[tc_idx];
  tcache->entries[tc_idx] = e;
  ++(tcache->counts[tc_idx]);
}
```

### 新定义
```c
/* Caller must ensure that we know tc_idx is valid and there's room
   for more chunks.  */
static __always_inline void tcache_put (mchunkptr chunk, size_t tc_idx)
{
  tcache_entry *e = (tcache_entry *) chunk2mem (chunk);
  assert (tc_idx < TCACHE_MAX_BINS);

  /* Mark this chunk as "in the tcache" so the test in _int_free will
     detect a double free.  */
  e->key = tcache; //写入tcache_perthread_struct地址

  e->next = tcache->entries[tc_idx];
  tcache->entries[tc_idx] = e;
  ++(tcache->counts[tc_idx]);
}
```

### 意义
在将chunk放入tcachebin中时，会将e->key写入到tcache_perthread_struct地址处。

## 4.tcache_get加入了新步骤
### 原始定义
```c
/* Caller must ensure that we know tc_idx is valid and there's
   available chunks to remove.  */
static __always_inline void *
tcache_get (size_t tc_idx)
{
  tcache_entry *e = tcache->entries[tc_idx];
  assert (tc_idx < TCACHE_MAX_BINS);
  assert (tcache->entries[tc_idx] > 0);
  tcache->entries[tc_idx] = e->next;
  --(tcache->counts[tc_idx]);
  return (void *) e;
}
```

### 新定义
```c
/* Caller must ensure that we know tc_idx is valid and there's
   available chunks to remove.  */
static __always_inline void *
tcache_get (size_t tc_idx)
{
  tcache_entry *e = tcache->entries[tc_idx];
  assert (tc_idx < TCACHE_MAX_BINS);
  assert (tcache->entries[tc_idx] > 0);
  tcache->entries[tc_idx] = e->next;
  --(tcache->counts[tc_idx]);
  e->key = NULL; //清空e->key
  return (void *) e;
}
```

### 意义
将chunk从Tcache中移除时，会清空<font style="color:#DD1144;background-color:rgba(0, 0, 0, 0.04);">e->key</font>。

## 5.int_free中加入了新检查
### 原始定义
```c
#if USE_TCACHE
  {
    size_t tc_idx = csize2tidx (size);

    if (tcache
    && tc_idx < mp_.tcache_bins
    && tcache->counts[tc_idx] < mp_.tcache_count)
      {
    tcache_put (p, tc_idx);
    return;
      }
  }
#endif
```

### 新定义
```c
#if USE_TCACHE
  {
    size_t tc_idx = csize2tidx (size);
    if (tcache != NULL && tc_idx < mp_.tcache_bins)
      {
        /* Check to see if it's already in the tcache.  */
        tcache_entry *e = (tcache_entry *) chunk2mem (p);

        /* This test succeeds on double free.  However, we don't 100%
           trust it (it also matches random payload data at a 1 in
           2^<size_t> chance), so verify it's not an unlikely
           coincidence before aborting.  */
        if (__glibc_unlikely (e->key == tcache))
          {//e->key检查是否为tcache_perthread_struct地址
            tcache_entry *tmp;
            LIBC_PROBE (memory_tcache_double_free, 2, e, tc_idx);
            for (tmp = tcache->entries[tc_idx]; tmp; tmp = tmp->next)
              if (tmp == e)// 检查tcache中是否有一样的chunk
                malloc_printerr ("free(): double free detected in tcache 2");
                /* If we get here, it was a coincidence.  We've wasted a
                   few cycles, but don't abort.  */
          }

        if (tcache->counts[tc_idx] < mp_.tcache_count)
          {
            tcache_put (p, tc_idx);
            return;
          }
      }
  }
#endif
```

这里有两个需要绕过的地方：

+ e->key检查是否为tcache_perthread_struct地址
+ 检查tcache中是否有一样的chunk

这里注意，绕过检查一即可绕过检查二（注意看if语句的位置）

### 意义
调用int_free时，将会检查整个Tcache链表，如果发现将要释放的chunk已存在于链表中将会报错

**<font style="color:#F5222D;">free(): double free detected in tcache 2。</font>**

## 7.do_set_tcache_count发生了变更
### 原始定义
```c
static inline int __always_inline do_set_tcache_count (size_t value)
{
  LIBC_PROBE (memory_tunable_tcache_count, 2, value, mp_.tcache_count);
  mp_.tcache_count = value;
  return 1;
}
```

### 新定义
```c
static inline int __always_inline do_set_tcache_count (size_t value)
{
  if (value <= MAX_TCACHE_COUNT)
    {
      LIBC_PROBE (memory_tunable_tcache_count, 2, value, mp_.tcache_count);
      mp_.tcache_count = value;
    }
  return 1;
}
```

### 意义
限制tcache_count的数目必须小于MAX_TCACHE_COUNT(即127)，防止发生溢出。

---

# 内存中的新旧版tcachebin
为了方便理解，接下来看一下内存中的key

我们下载新版2.27编译好的libc库：libc6_2.27-3ubuntu1.4_amd64.deb

> 为了不让之后在本机调试做题时遇见麻烦（因为我本机libc-2.27.so没有key机制，幸好没更新，如果更新的话，之后做题会遇到很大的麻烦），下载完成之后在Linux中不要双击安装，而是将其解压出来。
>
> 可以到此处下载。
>
> [https://mirrors.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc/](https://mirrors.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc/)
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611309067075-8cbd194a-f439-4f3f-933e-aaaf1897a790.png)

编写如下源码：

```c
#include<stdio.h>
#include<stdlib.h>
int main(){
	sleep(0);
	void *p[10]={0};
	for(int i = 0 ;i<10;i++){
		p[i]=malloc(0x10);
	}
	sleep(0);
	for(int j = 0;j<10;j++){
		free(p[j]);
		p[j]=NULL;
	}
	sleep(0);
	return 0;
}
```

> sleep是为了方便下断点.
>

这里编译出两份：

> 编译命令：
>
> gcc -g -fno-stack-protector -z execstack -no-pie -z norelro glibc_test.c -o old_glibc_test
>
> gcc -g -fno-stack-protector -z execstack -no-pie -z norelro glibc_test.c -o new_glibc_test
>

然后将编译出来的new_glibc_test对其修改动态链接库链接到刚才新下载的libc文件，对两份文件同时进行调试，观察效果。

以上提到内容的教程均可在如下链接获取：

[PWN进阶（1-4）-修改ELF动态链接到指定的libc库（动态链接库）（待重写）](https://www.yuque.com/cyberangel/rg9gdm/vk7hfg)

修改效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611310054056-679756e9-afcd-4541-adce-1ed8a1b9acd9.png)

开始对其一起进行gdb动态调试，**<font style="color:#F5222D;">注意new_glibc_test文件在调试过程中附加符号库</font>**:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611312955009-11bb1f06-8567-4e9e-99d6-9ff14207c597.png)

对代码的第12行下断点，然后运行程序，此时程序进行了第一次free：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611314627650-1a28d823-afe7-4421-97de-5eb0ec6d4828.png)

看一下此时的bin情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611314751298-0d44a21f-cb20-432c-82ee-84200f674b08.png)

内存状况：(相同部分如代码框所示)

```c
pwndbg> x/120gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251 #tcache_perthread_struct
0x601010:	0x0000000000000001	0x0000000000000000
......
0x601050:	0x0000000000601260	0x0000000000000000
......
0x601240:	0x0000000000000000	0x0000000000000000
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611315415152-6860d14f-95ab-4bb1-a505-186a398e8263.png)

> 从红箭头的指向可以看出，现在被free的chunk加入了key指针。
>

继续运行程序，执行第二次free：

```c
pwndbg> x/120gx 0x601000
0x601000:	0x0000000000000000	0x0000000000000251
0x601010:	0x0000000000000002	0x0000000000000000
......
0x601050:	0x0000000000601280	0x0000000000000000
......
0x601240:	0x0000000000000000	0x0000000000000000
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611315800815-c64a311d-dcd3-405a-818b-332129d1c918.png)

看一下new_libc_test的其中一部分内存：

```c
0x601250:	0x0000000000000000	0x0000000000000021
0x601260:	0x0000000000000000	0x0000000000601010 #写入tcache_perthread_struct
0x601270:	0x0000000000000000	0x0000000000000021
0x601280:	0x0000000000601260	0x0000000000601010 #写入tcache_perthread_struct
    		#指向前一个被free堆块的data
0x601290:	0x0000000000000000	0x0000000000000021
0x6012a0:	0x0000000000000000	0x0000000000000000
0x6012b0:	0x0000000000000000	0x0000000000000021
```

多次输入c，让程序free完：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1611316451454-7dc0c81e-f501-4c51-bdca-c98f648b5698.png)

# 小总结
> PS：要结合上面的源码来看
>

+ 当一个属于tcache大小的chunk被free掉时，会调用tcache_put，e->key处会写入tcache_perthread_struct的地址，也就是heap开头的位置。而当程序从tcache取出chunk时，会将e->key重新清空。
+ _int_free中tcache部分对double free的**<font style="color:#F5222D;">检测方法</font>**：首先_int_free会**<font style="color:#F5222D;">检查chunk的key是否为tcache_perthread_struct地址</font>**，然后会遍历tcache，检查此chunk是否已经在tcache中，如有则触发malloc_printerr报错free(): double free detected in tcache 2。

> 上面所说的e->key和key是一个东西
>

+ 简单总结一下，key字符下tcachebin触发double free报错的条件为：

```c
e-key == &tcache_perthread_struct && chunk in tcachebin[chunk_idx]
```

新增保护主要还是用到`e->key`这个属性，因此绕过想绕过检测进行double free，这里也是入手点。

# 绕过key机制
绕过思路有以下两个：

1. 如果有UAF漏洞或堆溢出，可以修改`e->key`为空，或者其他非`tcache_perthread_struct`的地址。这样可以直接绕过`_int_free`里面第一个if判断。不过如果UAF或堆溢出能直接修改chunk的fd的话，根本就不需要用到double free了。
2. 利用堆溢出，修改chunk的size，最差的情况至少要做到off by null。留意到`_int_free`里面判断当前chunk是否已存在tcache的地方，**<font style="color:#F5222D;">它是根据chunk的大小去查指定的tcache链，由于我们修改了chunk的size，查找tcache链时并不会找到该chunk，满足free的条件</font>**。**<font style="color:#F5222D;">虽然double free的chunk不在同一个tcache链中，不过不影响我们使用tcache poisoning（修改next指针）进行攻击。</font>**

