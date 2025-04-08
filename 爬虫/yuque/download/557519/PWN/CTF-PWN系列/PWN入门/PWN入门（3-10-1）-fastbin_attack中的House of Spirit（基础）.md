> 参考资料：[https://www.anquanke.com/post/id/85357](https://www.anquanke.com/post/id/85357)
>

# 简介
首先，你先别被House of Spirit这个名字给弄晕了，不要将这个名字直译成中文。使用最简单的话来说这是一个组合型漏洞的利用，进一步来说是变量覆盖和堆管理机制的组合利用。

# 原理
House of Spirit的利用关键在于能够覆盖一个堆指针变量（也就是调用malloc之后堆块中malloc_data返回的地址），让其指向可以控制的区域。

# 利用思路
1. 伪造堆块
2. 覆盖堆指针指向上一步伪造的堆块
3. 释放堆块，将伪造的堆块放入fastbin的单链表里面（需要绕过检测）
4. 申请堆块，将刚才释放的堆块申请出来，最终可以使得向目标区域中写入数据，以达到控制内存的目的。

# 在free时需要绕过的检测
> 参考自：[https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/fastbin_attack-zh/#house-of-spirit](https://ctf-wiki.github.io/ctf-wiki/pwn/linux/glibc-heap/fastbin_attack-zh/#house-of-spirit)
>

接下来看一下free伪造的堆块时需要绕过的检测，以libc-2.23.so这个版本的源码进行讲解。

> 打开源码目录中的文件malloc.c
>

## 检测一
> + fake chunk 的 ISMMAP 位不能为 1，因为 free 时，如果是 mmap 的 chunk，会单独处理。
>

结合源码来看一下：

```c
#malloc.c
#代码第2952-2969行
   if (chunk_is_mmapped (p))                       /* release mmapped memory. */
    {/*首先M标志位不能为1才能绕过检测*/
      /* see if the dynamic brk/mmap threshold needs adjusting */
      if (!mp_.no_dyn_threshold
          && p->size > mp_.mmap_threshold
          && p->size <= DEFAULT_MMAP_THRESHOLD_MAX)
        {
          mp_.mmap_threshold = chunksize (p);
          mp_.trim_threshold = 2 * mp_.mmap_threshold;
          LIBC_PROBE (memory_mallopt_free_dyn_thresholds, 2,
                      mp_.mmap_threshold, mp_.trim_threshold);
        }
      munmap_chunk (p);
      return;
    }
    ar_ptr = arena_for_chunk (p);
    _int_free (ar_ptr, p, 0);
```

## 检测二
> + fake chunk 地址需要对齐， MALLOC_ALIGN_MASK
>

这个不再说。

## 检测三
> + fake chunk 的 size 大小需要满足对应的 fastbin 的需求，同时也得对齐。
>

```c
#malloc.c
#代码第3886行
if ((unsigned long)(size) <= (unsigned long)(get_max_fast ())
    //chunk的size大小要小于fastbin的回收范围
```

## 检测四
> + fake chunk 的 next chunk 的大小不能小于 `2 * SIZE_SZ`，同时也不能大于`av->system_mem` 。
>

```c
#malloc.c
#代码第3904-3914行
	 if (have_lock
	    || ({ assert (locked == 0);
		  mutex_lock(&av->mutex);
		  locked = 1;
		  chunk_at_offset (p, size)->size <= 2 * SIZE_SZ
		    || chunksize (chunk_at_offset (p, size)) >= av->system_mem;
	      }))
	  {
	    errstr = "free(): invalid next size (fast)";
	    goto errout;
	  }
```

## 检测五
> + fake chunk 对应的 fastbin 链表头部不能是该 fake chunk，即不能构成 double free 的情况。
>

这个不再说。

# 总结
总的来说，house of spirit的主要意思是我们想要控制的区域控制不了，但是它前面和后面都可以控制，所以伪造好数据将它放入fastbin中，后面将该内存区域当作堆块申请出来，致使该区域被当作普通的内存使用，从而使目标区域变成可控的。



