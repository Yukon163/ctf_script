> 主要参考资料：[https://bbing.com.cn/202106/fopen-deep/](https://bbing.com.cn/202106/fopen-deep/)
>

[FILE结构体及漏洞利用方法](https://fish-o0o.github.io/2019/12/29/FILE%E7%BB%93%E6%9E%84%E4%BD%93%E5%8F%8A%E6%BC%8F%E6%B4%9E%E5%88%A9%E7%94%A8%E6%96%B9%E6%B3%95/#fopen)

使用docker一件配置环境：

> sudo docker pull ccr.ccs.tencentyun.com/cyberangel_pub/yuque:_io_file_v1
>

附件：

> 链接: [https://pan.baidu.com/s/1cxj8veYkJhD_dh1fSzLwxQ](https://pan.baidu.com/s/1cxj8veYkJhD_dh1fSzLwxQ) 提取码: hon3
>

# 环境准备
本篇文章中使用到的Linux和libc详细信息如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637475452704-7594748b-9838-40ff-b7d5-531435109af2.png)

在文章的开头需要将将Linux的环境准备一下，现将Linux的apt源进行编辑：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637474842469-9f381ecd-5cf0-4c85-92dc-13819e055317.png)

如上图所示，将/etc/apt目录下的sources.list中的所有以deb和deb-src开头的注释符全部删除，保存文件后执行如下命令：

```powershell
apt update 						 # 更新源
apt install libc6-dbg  # 安装glibc符号表
apt source libc6-dev   # 找到一个可写目录，下载源码
```

下载好的源码会自动解压到当前目录下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637475510586-edfeb2cf-e55f-4454-9b4f-36671fc2bda9.png)

本篇文章我们边调试源码边理解IO FILE的结构和文件打开函数fopen的执行流程。现所需要调试的可执行文件源码如下：

```c
//编译命令：gcc -g test1.c -o test
#include<stdio.h>
int main(){
	char data[50]={0};
	printf("Cyberangel\n");
	FILE *fp=fopen("flag.txt","rb");
	fread(data,1,50,fp);
	printf("%s\n",data);
	return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637475807785-50358eb0-c371-432f-a904-043efaa57b7c.png)

> 记得在可执行文件所在的目录下创建flag.txt。
>

# 复习结构体
> 参考资料：[http://c.biancheng.net/](http://c.biancheng.net/)
>

由于在文章的后续会出现大量的结构体，所以在调试源码之前要复习结构体的具体概念。

## 结构体的定义
在C语言中可以使用数组来存放类型相同的数据，但是对于类型不同的数据就要使用结构体这种数据类型来进行存放，结构体定义的形式为：

```c
struct 结构体名称{
    结构体成员1;
    结构体成员2;
    ...
};
```

比如说，现在要定义一个结构体存放“书📚”的信息：

```c
struct Books{
    char  title[50];    # 书的名称
    char  author[50];	# 书的作者
    int   book_id;		# 书的序号
};
```

其中"Books"为结构体的名称，在这个结构体中包含了3个成员：title、author和book_id。注意定义成员时不能在结构体内部对它们进行赋值，下面这种方式是错误的：

```c
struct Books{
    char  title[50] = "Pwn from 0 to 0";    # 书的名称
    char  author[50] = "Cyberangel";		# 书的作者
    int   book_id = 0xdeadbeef;				# 书的序号
};
```

既然结构体是一种数据类型，那么可以使用它来定义一些变量：

```c
struct Books book1,book2;   //定义时关键字struct不能少
```

这里定义了两个变量类型为Books的book1和book2结构体变量，每个变量中都包含了3个结构体成员。变量的定义还可以使用如下方式进行：

```c
struct Books{
    char  title[50];    
    char  author[50];
    int   book_id;
} book1,book2;
```

也就是在定义结构体的过程中直接定义**结构体变量**；假如说在后续的代码中只需要定义两个结构体变量，那么可以在定义结构体时可以不写结构体名称：

```c
struct {
    char  title[50];    
    char  author[50];
    int   book_id;
} book1,book2;
```

虽然这样书写很简单，但是在之后不能再使用该结构体定义新的结构体变量，因为没有结构体名称。

## 结构体成员的赋值
在C语言的数组中可以使用[index]来获取对应的元素，同样的在结构体中可以使用"结构体变量.成员名称"来获取单个成员：

```c
struct {
    char  title[50];    
    char  author[50];
    int   book_id;
} book1;

strcpy(book1.title, "Pwn from 0 to 0");  # book1.title = "Pwn from 0 to 0"
strcpy(book1.author, "Cyberangel");      # book1.author = "Cyberangel"
book1.book_id = 0xdeadbeef;              # book1.book_id = 0xdeadbeef
```

虽然不能在结构体内部进行直接赋值，但是可以使用如下方法对各个成员进行同时赋值：

```c
struct {
    char  title[50];    
    char  author[50];
    int   book_id;
} book1 = {"Pwn from 0 to 0","Cyberangel",0xdeadbeef};
```

另外，结构体说白了就是一种数据类型，它并不占内存空间，但是其中的结构体成员是实实在在的变量，所以需要使用到内存空间，这一点会在稍后的对例子的调试中进行展现。

## 结构体指针
结构体指针是对“指向结构体的指针”的缩写，当一个指针指向结构体时，我们就将这个指针称为结构体指针，其一般的定义形式为：

```c
struct {
    char  title[50];    
    char  author[50];
    int   book_id;
} book1 = {"Pwn from 0 to 0","Cyberangel",0xdeadbeef};

struct *p = &book1; 
// struct *p = NULL;
// p = &book1;
```

同样的，也可以在定义结构体的同时定义结构体指针：

```c
struct {
    char  title[50];    
    char  author[50];
    int   book_id;
} book1 = {"Pwn from 0 to 0","Cyberangel",0xdeadbeef} , *p = &book1;
```

数组和结构体还是有一些差别的，在访问结构体时必须使用&取地址符获取其地址，这是因为结构体是数据类型的集合，稍后会在IDA中进行查看。但是数组就不一样了，其每个元素本身就是一个地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637572169825-c68a0048-ec9b-4962-98da-482fcc66e878.png)

关于数组的知识可以访问如下链接，这里就不再说明：

[PWN杂记（1-2）-《gcc中关于C语言char类型的这件事（1）》](https://www.yuque.com/cyberangel/rg9gdm/bichu8)

## 获取结构体成员
除了可以通过结构体变量来访问结构体的成员，还可以使用结构体指针来进行访问：

```c
struct {
    char  title[50];    
    char  author[50];
    int   book_id;
} book1 = {"Pwn from 0 to 0","Cyberangel",0xdeadbeef} , *p = &book1;

//第一种方式
printf("%s",(*p).title);
printf("%s",(*p).author);
printf("%d",(*p).book_id);
//第二种方式
printf("%s",p->title);
printf("%s",p->author);
printf("%d",p->book_id);
```

在第一种写法中"."的优先级高于"*"，所以小括号可不能少。第二种写法中使用"->"来访问结构体是"->"在C语言中的唯一用法。但是假如结构体成员非常多，使用结构体变量进行传参则会耗费很多的内存资源，所以最好的方法就是使用结构体指针来进行传递，因为后者只是传入了一个指针，速度很快。这一点会在稍后的调试中可以看到。

## 结构体指针作为函数参数
```c
#include<stdio.h>
#include <string.h>

struct Books{
    char  title[50];    
    char  author[50];
    int   book_id;
};

void PrintINFO1(struct Books book){
    printf( "Book 1 title : %s\n", book.title);
    printf( "Book 1 author : %s\n", book.author);
    printf( "Book 1 book_id : %x\n", book.book_id); //程序是之前编译的，此处的"%d"变为"%x",但是不影响内存布局，下同。
    printf("#######################################\n");
}

void PrintINFO2(struct Books *book){
   printf( "Book title : %s\n", book->title);
   printf( "Book author : %s\n", book->author);
   printf( "Book book_id : %x\n", book->book_id);  //这里也不影响
}

int main(){
    struct Books book1;
    strcpy(book1.title, "Pwn from 0 to 0");
    strcpy(book1.author, "Cyberangel"); 
    book1.book_id = 0xdeadbeef;
    PrintINFO1(book1);
    PrintINFO2(&book1);
    return 0;
}
```

> 编译命令：gcc -g struct1.cpp -o struct1
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637574122618-217c12e4-7c33-49c1-a416-a8158b68e33d.png)

直接在IDA中来到main函数，在函数的开头根据book1结构体变量的地址（即&book1）进行写入寻址：

> IDA已经自动为该程序恢复对应的结构体。
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637626524719-b753128c-f6e2-49ad-af4b-fcb5fd72f94d.png)

下一步是将之前赋值好的内容（所有的结构体成员）压入到stack中，为紧接着的call _Z10PrintINFO15Books做铺垫。这里并没有使用寄存器传参而是使用栈：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637626728161-b1d404c0-41d8-4c0f-a625-888539a0fb04.png)

可以看到在使用结构体变量进行传参时会将所有的结构体成员压入到stack中，这会导致浪费十分多的内存资源。再在printf中根据栈中的结构体成员的偏移进行寻址打印（也可以说根据rbp寻址）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637626883013-78f9811d-1be6-462a-97ea-3e959d1b1e24.png)

但是如果使用结构体指针传参的话就没有那么多事情了，只是向函数中传入一个指针罢了，这样速度很快：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637626994007-b1e4c4a0-68bd-4734-a939-e4f893d9287f.png)

PrintINFO2的所有汇编指令如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637627016815-c0f17923-d30b-4293-bdf0-3957e664dda3.png)

**<font style="color:#F5222D;">所以我们可以说结构体变量代表的是整个集合本身，作为函数参数时会传递所有的结构体变量，而不会像数组一样被编译器转换成一个指针传入。如果结构体成员较多，尤其是成员为数组时，传送的时间和空间开销会很大，影响程序的运行效率。所以最好的办法就是使用结构体指针，这时由实参传向形参的只是一个地址，非常快速。</font>**

# IO的概述
在开始调试之前我们先简单的说一下Linux中IO的大致内容。程序的输入输出是通过文件流进行实现的，在程序加载完毕之后默认有三个文件流打开，分别是：_IO_2_1_stderr_、_IO_2_1_stdout_、_IO_2_1_stdin_。这三个文件流的本质是一个结构体，它们之间使用结构体成员_chain进行连接，最终形成了IO链表_IO_list_all。当我们在程序中每打开一个新的文件会自动生成一个文件流，glibc会将新生成的文件流使用头插法连入到_IO_list_all链表中:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637808411173-933b1258-f26a-4166-a9f7-7608f7a4ba1d.png)

然后会根据fopen的参数对结构体的成员进行赋值，这个过程比较复杂需要我们慢慢的调试，函数执行完毕之后会返回指向新建文件流的fp文件指针，根据这个指针在后续可以对文件进行操作。

# 开始调试
先引入我们所需要的源码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637476841677-b0baee4b-91db-48f7-b0b3-15a7407c815d.png)

然后调试到经过_dl_runtime_resolve_xsavec函数解析过后的_IO_new_fopen。

## _IO_new_fopen
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637477018491-b7770b36-6e93-44af-bf26-da0362bffc43.png)

该函数的两个参数分别是字符串指针filename和mode，分别代表着要open的文件名称和open方式，这两个参数都存在于只读的rodata段：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637477133721-70146706-53cb-46ba-b574-c679cc928e44.png)

## _IO_new_fopen->__fopen_internal
进入__fopen_internal函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637477264928-0ec74fc9-7f17-4c72-9f5d-e03bad5ec731.png)

在后续的文章中会出现许多结构体，这也就是前面我们要复习结构体知识的原因。结构体与结构体之间的关系可以使用下面的思维导图来表示：

[IO_struct.xmind](https://www.yuque.com/attachments/yuque/0/2021/xmind/574026/1637930228903-bd25fb45-a524-4733-b3b6-0942be283b95.xmind)

这里还是简单的说一下吧，结构体locked_FILE由三部分组成：

+ **<font style="color:#F5222D;">文件流_IO_FILE_plus结构体</font>**，它包含着IO中许多重要的参数。
+ _IO_lock_t代表着该文件流中的“锁”，能够保证在多核多线程环境中，在某一个时间点上只能有一个线程进入临界区代码，从而保证临界区中IO文件流的一致性【操作系统--锁】。
+ _IO_wide_data结构体为读取宽字节数据而生，它的结构与_IO_FILE_plus相似。【web--宽字节注入】

> 在接下来结构体的定义中指针都是char*类型的，应对ASCII字符没有一点问题。但是应对更复杂的编码就会出现问题，比如说中文，它在ASCII的环境下是会发生乱码的情况，这个时候该怎么办？问题稍后解答。
>

locked_FILE的源代码如下：

```c
  struct locked_FILE
  {
    struct _IO_FILE_plus fp;
#ifdef _IO_MTSAFE_IO   //_IO_MTSAFE_IO已经定义
    _IO_lock_t lock;
#endif
    struct _IO_wide_data wd;
  } *new_f = (struct locked_FILE *) malloc (sizeof (struct locked_FILE));  //malloc
```

并且在此结构体中成员结构体都是使用结构体变量进行定义的而非指针，根据前面的内容**<font style="color:#F5222D;">结构体变量代表的是整个结构体本身</font>**，所以实际上在内存中locked_FILE结构体的表现形式为这3个结构体全部展开：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637822596800-ff3be843-e84d-42fb-a03b-9687eda39488.png)

> new_f->fp的vtable变量被定义为_IO_jump_t结构体指针，所以在内存中并未展开。
>

这里会申请一个大小为locked_FILE的chunk，然后让new_f指针指向这个chunk的user_data，如果返回的new_f == NULL则意味着文件读取失败：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637478239066-95170623-21e4-4d2f-afc4-ba23f9b3fdf5.png)

```c
  if (new_f == NULL)  
    return NULL;	//返回后代表着文件指针为NULL，也就是平时所说的读取文件失败。
----------------------------------------------------------------------------------------
FILE *fp=fopen("flag.txt","rb");
fread(data,1,50,fp); 				//若fp == NULL则不会出现段错误，详情见下一篇的fread
printf("%s\n",data);
```

另外要说明的是在内存中展开的_IO_FILE是被扩充之后的形式，其中的一部分属于_IO_FILE_complete结构体：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637823070768-4826f91c-c736-4b8d-a86e-a5d2eeb93fa8.png)

扩充的具体原因需要注意_IO_FILE的宏定义作用范围，原因我注释到了下面的代码框中可自行查看：

```c
//glibc-2.23/libio/libio.h
struct _IO_FILE {
  int _flags;		/* High-order word is _IO_MAGIC; rest is flags. */
#define _IO_file_flags _flags
	......
  char* _IO_read_ptr;	/* Current read pointer */
    ......（成员省略）
  char *_IO_save_end; /* Pointer to end of non-current get area. */
    ......（成员省略）
	......
  _IO_lock_t *_lock;			//_IO_USE_OLD_IO_FILE实际上并没有定义，所以紧邻着_IO_USE_OLD_IO_FILE
    							//下面的代码全部失效。
#ifdef _IO_USE_OLD_IO_FILE------------------------------------------------------
};																				| # 失效
																				| # 失效
struct _IO_FILE_complete														| # 失效
{																				| # 失效
  struct _IO_FILE _file;														| # 失效
#endif--------------------------------------------------------------------------
	//上面的代码包括开头的"};"失效，其结构体定义被扩展到最后一行。
#if defined _G_IO_IO_FILE_VERSION && _G_IO_IO_FILE_VERSION == 0x20001
  _IO_off64_t _offset;
# if defined _LIBC || defined _GLIBCPP_USE_WCHAR_T
  /* Wide character stream stuff.  */
  struct _IO_codecvt *_codecvt;
  struct _IO_wide_data *_wide_data;
  struct _IO_FILE *_freeres_list;
  void *_freeres_buf;
# else
  void *__pad1;
  void *__pad2;
  void *__pad3;
  void *__pad4;
# endif
  size_t __pad5;
  int _mode;
  /* Make sure we don't get into trouble again.  */
  char _unused2[15 * sizeof (int) - 4 * sizeof (void *) - sizeof (size_t)];
#endif
}; //扩展到此处
```

接下来看一下_IO_FILE_plus结构体，其定义如下：

```c
struct _IO_FILE_plus
{
  _IO_FILE file;
  const struct _IO_jump_t *vtable;
};
```

> 源代码中关于_IO_FILE_plus的注释：
>
> We always allocate an extra word following an _IO_FILE. This contains a pointer to the function jump table used. This is for compatibility with C++ streambuf; the word can be used to smash to a pointer to a virtual function table. 
>

_IO_FILE包含了许多重要成员的结构体，为了与C++进行兼容还定义了额外的_IO_jump_t类型的vtable指针：

```c
struct _IO_jump_t
{
    JUMP_FIELD(size_t, __dummy);  // #define JUMP_FIELD(TYPE, NAME) TYPE NAME
    JUMP_FIELD(size_t, __dummy2);
    ......(省略结构体成员)
#if 0
    get_column;
    set_column;
#endif
};
```

locked_FILE还包括为了线程的安全性所定义的_IO_lock_t结构体：

```c
# glibc-2.23/sysdeps/nptl/stdio-lock.h
typedef struct { int lock; int cnt; void *owner; } _IO_lock_t;
```

最后一个locked_FILE结构体成员被定义为与_IO_FILE比较相似的_IO_wide_data结构体：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637633549074-c09017b8-7ca1-4e6f-b5e7-16a509e4d5a5.png)

现在回答之前的问题，为了兼容更广泛的编码格式在IO中glibc提供了宽字节流也就是上面的_IO_wide_data结构体，它的结构体成员虽然比较少，但是每个wchar_t【4字节】成员大小要比char类型大的多。在此结构体中包含了成员`struct _IO_codecvt _codecvt;`，其中的_IO_codecvt是针对字符编码转换的函数表，这里不对其进行说明。

> wchar_t百度百科：[https://baike.baidu.com/item/wchar_t/8562830](https://baike.baidu.com/item/wchar_t/8562830)】
>

继续向下看__fopen_internal的源代码：

```c
#ifdef _IO_MTSAFE_IO
  new_f->fp.file._lock = &new_f->lock;
#endif
```

根据C语言的运算符优先级："->"大于"&，所以&new_f->lock可以看做是&(new_f->lock)。这就很明显了，&new_f->lock是获取已展开结构体locked_FILE的lock成员变量地址，然后对_IO_FILE的_lock成员进行赋值，这样我们就能通过_IO_FILE_plus结构体直接访问_IO_lock_t的内存：

```c
  struct locked_FILE
  {
    struct _IO_FILE_plus fp;
#ifdef _IO_MTSAFE_IO
    _IO_lock_t lock;   # 结构体变量（在内存中已经展开）
#endif
    struct _IO_wide_data wd;
  } *new_f = (struct locked_FILE *) malloc (sizeof (struct locked_FILE));
-------------------------------------------------------------------------------------
struct _IO_FILE {
    ......
  _IO_lock_t *_lock;   # 结构体指针（对其进行赋值）
    ......
};
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637634501022-18add592-66ad-4500-bb4b-0f0b1ab89acf.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637634698746-54af6289-9bc0-42d7-bb8f-98e75420b1ed.png)

> 总结：上面的步骤创建了存放在堆中的新_IO_FILE_plus文件流（malloc）。
>

## _IO_new_fopen->__fopen_internal->_IO_no_init
现在进入_IO_no_init函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637635898205-cb91d9d4-6b2d-4a20-83b7-aa0c15f8bd42.png)

```c
_IO_no_init (&new_f->fp.file, 0, 0, &new_f->wd, &_IO_wfile_jumps);  //call _IO_no_init
_IO_no_init (_IO_FILE *fp, int flags, int orientation, struct _IO_wide_data *wd, const struct _IO_jump_t *jmp)

fp=fp@entry=0x602420, 
flags=flags@entry=0,             
orientation=orientation@entry=0, 
wd=wd@entry=0x602510, 
jmp=0x7ffff7dd0260 <_IO_wfile_jumps>
```

该函数的结构体传参方式为指针传参，其中的flags和orientation参数的值会根据宏定义的判定进行固定，这里我们无需理会：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637824868141-c457afcc-3219-4b8a-b80e-eb046ba61270.png)

需要看的是传入的_IO_jump_t结构体指针jmp，其结构体的定义如下：

```c
struct _IO_jump_t
{
    JUMP_FIELD(size_t, __dummy);     // #define JUMP_FIELD(TYPE, NAME) TYPE NAME
    ......
    JUMP_FIELD(_IO_read_t, __read);
    ......
#if 0
    get_column;
    set_column;
#endif
};
```

还记得之前_IO_FILE_plus的vtable指针吗，它也是_IO_jump_t类型：

```c
struct _IO_FILE_plus
{
  _IO_FILE file;
  const struct _IO_jump_t *vtable; //vtable的类型是_IO_jump_t
};
```

与你想的没错，vtable正是C++虚函数的虚表指针，而_IO_jump_t则是与其对应的虚函数表（以下简称虚表）。实际上这里使用到了面向对象的思想，但是这张虚表是如何定义的？我们来仔细说说：

宏定义JUMP_FIELD并不复杂，拿其中read为例该宏可以展开为`_IO_read_t __read`。根据结构体中成员的定义，_IO_read_t和__read分别是该成员的类型和名称，但_IO_read_t是如何定义的？

```c
typedef _IO_ssize_t (*_IO_read_t) (_IO_FILE *, void *, _IO_ssize_t);
```

> 所有的typedef关键字用法出门右转：[http://c.biancheng.net/view/2040.html](http://c.biancheng.net/view/2040.html)
>

需要理解一下typedef关键字，一个简单的例子如下：

```c
#include<stdio.h>
typedef void*(*Function)(int,int); //函数指针

void *pwn(int ip ,int port){
    printf("Cyberangel\n");
    printf("%d,%d\n",ip,port); //实际上ip不为int,主要我想省事...
    return NULL;
}

int main(){
    Function function = pwn; 
    function(192,22);
    return 0;
}
```

大致流程就是首先定义pwn函数，然后使用typedef函数为这个函数定义了一个**别名**function，当执行代码function(192,22)时即会调用pwn(192,22)。

回到上面的_IO_read_t，我们对该宏进行完全展开：

```c
_IO_ssize_t *Function_Name(_IO_FILE* parameter1, void* parameter2,_IO_ssize_t parameter2){
    //函数体
    //...
}
```

> 该宏定义其实还可以继续简化，自己可以尝试着根据定义去找一下：
>
> `typedef (long int) (*_IO_read_t)(_IO_FILE *, void *, (long int))`
>

JUMP_FIELD会对每一个成员进行定义，在_IO_wfile_jumps中会对它们进行赋值。这里只看JUMP_INIT，其他的宏定义可以自行去源码中查看：

```c
const struct _IO_jump_t _IO_wfile_jumps =
{
  JUMP_INIT_DUMMY,
  ......
  JUMP_INIT(read, _IO_file_read),   #define JUMP_INIT(NAME, VALUE) VALUE
  ......							#宏定义只返回了一个VALUE
};
libc_hidden_data_def (_IO_wfile_jumps)
    
//JUMP_INIT宏定义中的第一个参数read宏定义在glibc-2.23/libio/fileops.c中：
	# define read(FD, Buf, NBytes) __read (FD, Buf, NBytes)
```

JUMP_INIT会返回VALUE，也就是_IO_file_read函数在内存中的起始地址：

```c
_IO_ssize_t
_IO_file_read (_IO_FILE *fp, void *buf, _IO_ssize_t size)
{
  return (__builtin_expect (fp->_flags2 & _IO_FLAGS2_NOTCANCEL, 0)
	  ? read_not_cancel (fp->_fileno, buf, size)
	  : read (fp->_fileno, buf, size));
}
libc_hidden_def (_IO_file_read)
```

> **虚表在程序加载进内存之前就已经初始化，因为虚表所在的内存空间为libc。**
>

虚函数表的最终初始化结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637732325497-0b9974b1-beae-4e4c-be34-f7d3eeb9a7a2.png)

> _IO_FILE的虚函数调用流程由于在此篇文章中没有体现所以先按下不表，之后的文章我们再进行说明。（挖坑...
>

## _IO_new_fopen->__fopen_internal->_IO_no_init->_IO_old_init
> 其本身的函数名称_IO_no_init可以直译为"当前的文件流没有初始化"，所以在这个函数中要初始化结构体中所有的成员。同样的之前new_f指针可以理解为“新建的【new】file【文件】（IO结构体指针）”。
>

下面这张图是_IO_no_init和_IO_old_init分别初始化的结构体成员：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637732705962-7fc478cd-c8f3-44b3-90ae-d750215f688b.png)

左侧的_IO_old_init函数主要初始化的是_IO_FILE结构体，右侧则初始化_IO_wide_data结构体。

> 传入__IO_no_init函数时使用的是&(new_f->fp.file)，所以这里_IO_no_init和_IO_old_init的形参fp表示_IO_FILE结构体指针。要注意和之前的_IO_FILE_plus的结构体变量fp进行区分：`struct _IO_FILE_plus fp`。
>

_IO_old_init函数会对_IO_FILE结构体的所有成员置为NULL：

```c
#ifdef _IO_MTSAFE_IO
  if (fp->_lock != NULL) 		//*_lock == &_IO_lock_t
    _IO_lock_init (*fp->_lock); //对_IO_lock_t的3个成员置0
#endif
-----------------------------------------------------------
pwndbg> p *fp->_lock
$42 = {
  lock = 0, 
  cnt = 0, 
  owner = 0x0
}
pwndbg> 
```

> 仍然要注意这里访问_lock的方式为通过_IO_FILE的_lock指针来访问_IO_lock_t结构体，而不是通过locked_FILE的结构体变量直接去访问。
>
> #ifdef _IO_MTSAFE_IO
>
>   new_f->fp.file._lock = &new_f->lock;
>
> #endif
>

## _IO_new_fopen->__fopen_internal->_IO_no_init
和_IO_old_init的作用相同，该函数初始化了应对宽字节的_IO_wide_data：

```c
void
_IO_no_init (_IO_FILE *fp, int flags, int orientation,
	     struct _IO_wide_data *wd, const struct _IO_jump_t *jmp)
{
  _IO_old_init (fp, flags);
  fp->_mode = orientation;
#if defined _LIBC || defined _GLIBCPP_USE_WCHAR_T
  if (orientation >= 0)   //进入if语句
    {
      fp->_wide_data = wd;   				//这里对fp的_wide_data进行赋值，地址为_IO_wide_data结构体地址
      fp->_wide_data->_IO_buf_base = NULL;  //所以接下来可以使用fp->_wide_data的方式访问_IO_wide_data结构体
      fp->_wide_data->_IO_buf_end = NULL;
      fp->_wide_data->_IO_read_base = NULL;
      fp->_wide_data->_IO_read_ptr = NULL;
      fp->_wide_data->_IO_read_end = NULL;
      fp->_wide_data->_IO_write_base = NULL;
      fp->_wide_data->_IO_write_ptr = NULL;
      fp->_wide_data->_IO_write_end = NULL;
      fp->_wide_data->_IO_save_base = NULL;
      fp->_wide_data->_IO_backup_base = NULL;
      fp->_wide_data->_IO_save_end = NULL;

      fp->_wide_data->_wide_vtable = jmp;
    }
  else
    /* Cause predictable crash when a wide function is called on a byte
       stream.  */
    fp->_wide_data = (struct _IO_wide_data *) -1L;
#endif
  fp->_freeres_list = NULL;
}
```

到此处各个成员的值如下图所示(_IO_wide_data结构体过长不再展示)：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637734047465-8a483204-2582-4f1d-bfa0-ddb6503fc5cf.png)

## _IO_new_fopen->__fopen_internal
在之前的篇幅中并没有介绍_IO_FILE的重要成员_flags，实际上这个成员意义非凡，它会标记所在的文件流读写属性。它的第一次赋值在刚刚过去的_IO_old_init函数中，其由_IO_MAGIC（0xFBAD的魔术头）和flags进行与运算得到：

```c
void
_IO_old_init (_IO_FILE *fp, int flags)
{
  fp->_flags = _IO_MAGIC|flags;  // #define _IO_MAGIC 0xFBAD0000 /* Magic number */
  ......
}

/* Magic numbers and bits for the _flags field. The magic numbers use the high-order bits of _flags; 
the remaining bits are available for variable flags.
Note: The magic numbers must all be negative if stdio emulation is desired. */
```

> <font style="color:#F5222D;">不要将_flags和flags这两个东西混为一谈。</font>
>

参数flags在传入函数_IO_no_init前就已经进行设定：

```c
调用链：
    _IO_no_init (&new_f->fp.file, 0, 0, &new_f->wd, &_IO_wfile_jumps);
    _IO_no_init (_IO_FILE *fp, int flags, int orientation, struct _IO_wide_data *wd, const struct _IO_jump_t *jmp)

flag的值是多少取决于宏定义：
    #if defined _LIBC || defined _GLIBCPP_USE_WCHAR_T
    _IO_no_init (&new_f->fp.file, 0, 0, &new_f->wd, &_IO_wfile_jumps);  //flag默认为0
    #else
    _IO_no_init (&new_f->fp.file, 1, 0, NULL, NULL);  //flag默认为1
    #endif
```

在正常情况下程序执行到此处_flags的值为0xFBAD0000，它的值会在之后执行的流程中发生变化，值的更改离不开如下宏定义：

```c
#define _IO_MAGIC 0xFBAD0000 /* Magic number */
#define _OLD_STDIO_MAGIC 0xFABC0000 /* Emulate old stdio. */
#define _IO_MAGIC_MASK 0xFFFF0000
#define _IO_USER_BUF 1 /* User owns buffer; don't delete it on close. */
#define _IO_UNBUFFERED 2
#define _IO_NO_READS 4 /* Reading not allowed */
#define _IO_NO_WRITES 8 /* Writing not allowd */
#define _IO_EOF_SEEN 0x10
#define _IO_ERR_SEEN 0x20
#define _IO_DELETE_DONT_CLOSE 0x40 /* Don't call close(_fileno) on cleanup. */
#define _IO_LINKED 0x80 /* Set if linked (using _chain) to streambuf::_list_all.*/
#define _IO_IN_BACKUP 0x100
#define _IO_LINE_BUF 0x200
#define _IO_TIED_PUT_GET 0x400 /* Set if put and get pointer logicly tied. */
#define _IO_CURRENTLY_PUTTING 0x800
#define _IO_IS_APPENDING 0x1000
#define _IO_IS_FILEBUF 0x2000
#define _IO_BAD_SEEN 0x4000
#define _IO_USER_LOCK 0x8000
```

他们的具体含义碰到再说，继续读源码：

```c
_IO_JUMPS (&new_f->fp) = &_IO_file_jumps;  #_IO_JUMPS宏定义：#define _IO_JUMPS(THIS) (THIS)->vtable
_IO_file_init (&new_f->fp);
```

&new_f->fp等价于&(new_f->fp)，将上面的宏定义展开可得到：&(new_f->fp->vtable)，所以这条代码是设置新文件流的虚表指针。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637744172117-4ba3ba43-bec3-45bf-b82c-ed6351b98192.png)

> + 别乱了，_IO_FILE_plus的虚表指针vtable到现在才进行设置，之前只是说明了虚表的初始化过程。
> + 虚表全称虚函数表。
>

## _IO_new_fopen->__fopen_internal->_IO_file_init
_IO_file_init函数会将新建的文件流连入到IO链表中，我们来看看其中具体的实现过程：

```c
void
_IO_new_file_init (struct _IO_FILE_plus *fp)         //指针为_IO_FILE_plus
{
  /* POSIX.1 allows another file handle to be used to change the position
     of our file descriptor.  Hence we actually don't know the actual
     position before we do the first fseek (and until a following fflush). */
  fp->file._offset = _IO_pos_BAD;                    // _IO_pos_BAD == ((long int)(-1))
  fp->file._IO_file_flags |= CLOSED_FILEBUF_FLAGS;   //_IO_file_flags宏定义：_flags

  _IO_link_in (fp);
  fp->file._fileno = -1;
}
libc_hidden_ver (_IO_new_file_init, _IO_file_init)
```

上述代码会对_flags和_offset重新进行设置，先来看第一个_IO_pos_BAD定义：

```c
/* _IO_pos_BAD is an _IO_off64_t value indicating error, unknown, or EOF. */
#ifndef _IO_pos_BAD
# define _IO_pos_BAD ((_IO_off64_t) -1)
#endif
```

根据注释可以知道_IO_pos_BAD是一个值为_IO_off64_t - 1（long int）的宏定义，它表示操作文件时遇到了错误、未知或异常，设置后_offset == -1。

> 当前文件流就处于未初始化完毕的未知状态。
>

然后看CLOSED_FILEBUF_FLAGS宏定义：

```c
#define CLOSED_FILEBUF_FLAGS \
  (_IO_IS_FILEBUF+_IO_NO_READS+_IO_NO_WRITES+_IO_TIED_PUT_GET)
```

它由_IO_IS_FILEBUF、_IO_NO_READS、_IO_NO_WRITES和_IO_TIED_PUT_GET这四个宏定义组成，都可以在_flags的宏定义中找到：

```c
#define _IO_MAGIC 0xFBAD0000 /* Magic number */
......
define _IO_NO_READS 4 /* Reading not allowed */
define _IO_NO_WRITES 8 /* Writing not allowd */
......
define _IO_TIED_PUT_GET 0x400 /* Set if put and get pointer logicly tied. */
#define _IO_CURRENTLY_PUTTING 0x800
#define _IO_IS_APPENDING 0x1000
define _IO_IS_FILEBUF 0x2000
#define _IO_BAD_SEEN 0x4000
#define _IO_USER_LOCK 0x8000
```

+ _IO_NO_READS：不允许对当前的文件流进行读取操作
+ _IO_NO_WRITES：不允许对当前的文件流进行写入操作
+ _IO_TIED_PUT_GET：表示与put和get进行了逻辑绑定（没理解...
+ _IO_IS_FILEBUF：文件流标志符【不是文件描述符】

所以CLOSED_FILEBUF_FLAGS表示当前的新建文件流文件缓冲区已经关闭。设置后的_flags为0xFBAD240C。下面来到_IO_link_in函数。

## _IO_new_fopen->__fopen_internal->_IO_file_init->_IO_link_in
_IO_link_in函数主要是将新生成的文件流连入到_IO_list_all链表，其源码如下：

```c
void
_IO_link_in (struct _IO_FILE_plus *fp)
{
  if ((fp->file._flags & _IO_LINKED) == 0) 
    {
      fp->file._flags |= _IO_LINKED;
#ifdef _IO_MTSAFE_IO
      _IO_cleanup_region_start_noarg (flush_cleanup);
      _IO_lock_lock (list_all_lock);
      run_fp = (_IO_FILE *) fp;
      _IO_flockfile ((_IO_FILE *) fp);
#endif
      fp->file._chain = (_IO_FILE *) _IO_list_all;
      _IO_list_all = fp;
      ++_IO_list_all_stamp;
#ifdef _IO_MTSAFE_IO
      _IO_funlockfile ((_IO_FILE *) fp);
      run_fp = NULL;
      _IO_lock_unlock (list_all_lock);
      _IO_cleanup_region_end (0);
#endif
    }
}
libc_hidden_def (_IO_link_in)
```

第一步判断_flags是否设置_IO_LINKED标志位，该宏定义表示文件流连入了_IO_list_all链表与否（这个链表在之前的"IO概述"中提到过）：

```c
define _IO_LINKED 0x80 /* Set if linked (using _chain) to streambuf::_list_all.*/
```

该文件流是全新创建的，需要连入到链表中，现在我们进入if：

```c
  if ((fp->file._flags & _IO_LINKED) == 0)   
    { //进入if语句后即代表着_IO_list_all链表开始连入，所以我们将_IO_FILE的_flags成员进行设置。
      //_IO_LINKED设置后之后不会再重复连入
      fp->file._flags |= _IO_LINKED;  //或运算后fp->file._flags == 0xfbad248c
#ifdef _IO_MTSAFE_IO   //该宏已经定义
    ......
#endif
    }
```

为了防止在多线程下的数据混乱，我们需要对IO加锁🔐，涉及到之前的_IO_lock_t结构体：

```c
#ifdef _IO_MTSAFE_IO
      _IO_cleanup_region_start_noarg (flush_cleanup); # 该函数不重要
      _IO_lock_lock (list_all_lock);   #对链表上锁，保证线程的安全
      run_fp = (_IO_FILE *) fp;
      _IO_flockfile ((_IO_FILE *) fp); #同样对链表进行上锁
#endif
```

到这里先暂停一下，和之前的虚表情况相同，在动态链接时程序加载到内存前_IO_list_all就已经初始化，该链表的定义如下：

```c
#  define DEF_STDFILE(NAME, FD, CHAIN, FLAGS) \
  struct _IO_FILE_plus NAME \
    = {FILEBUF_LITERAL(CHAIN, FLAGS, FD, NULL), \
       &_IO_file_jumps};
# endif
#endif

DEF_STDFILE(_IO_2_1_stdin_, 0, 0, _IO_NO_WRITES);
DEF_STDFILE(_IO_2_1_stdout_, 1, &_IO_2_1_stdin_, _IO_NO_READS);
DEF_STDFILE(_IO_2_1_stderr_, 2, &_IO_2_1_stdout_, _IO_NO_READS+_IO_UNBUFFERED);

struct _IO_FILE_plus *_IO_list_all = &_IO_2_1_stderr_;
libc_hidden_data_def (_IO_list_all)
```

上面的宏定义没有必要深究，用一张图进行表示现在的_IO_list_all即可：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637893192814-6dea8aff-a0fc-4280-aa8c-32b4d514ce04.png)





![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637756353140-75de6640-2d44-4f31-b0cd-478ec823e72d.png)

> _IO_2_1_stderr_、_IO_2_1_stdout_、_IO_2_1_stdin_的地址分别为0x7ffff7dd2540、0x7ffff7dd2620、0x7ffff7dd18e0
>

_IO_list_all是_IO_FILE_plus类型的结构体**<font style="color:#F5222D;">指针</font>**，它指向了一串_IO_FILE_plus结构体，这些结构体的集合组成了管理程序中所有FILE结构体（文件流）的单链表，也就是图中的_IO_2_1_stderr_、_IO_2_1_stdout_、_IO_2_1_stdin_。有一点值得进行说明，那就是上面的三个文件流共用一个一个虚表。以_IO_2_1_stdout_为例介绍_IO_FILE_plus前几个成员的具体含义：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637888429272-9fb88b8a-872e-4496-b4fb-036c7d3191b1.png)

```c
    _IO_read_ptr = 0x602010,        	# 输入缓冲区的当前地址	/* Current read pointer */
    _IO_read_end = 0x602010, 			# 输入缓冲区的结束地址	/* End of get area. */
    _IO_read_base = 0x602010, 			# 输入缓冲区的起始地址	/* Start of putback+get area. */
    _IO_write_base = 0x602010, 			# 输出缓冲区的起始地址	/* Start of put area. */
    _IO_write_ptr = 0x602010, 			# 输出缓冲区的当前地址	/* Current put pointer. */
    _IO_write_end = 0x602010, 			# 输出缓冲区的结束地址	/* End of put area. */
    _IO_buf_base = 0x602010, 			# 输入输出缓冲区的起始地址 /* Start of reserve area. */
    _IO_buf_end = 0x602410, 			# 输入输出缓冲区的结束地址 /* End of reserve area. */
     /* The following fields are used to support backing up and undo. */ 
     // 下面的标志是用来支持缓冲区的备份和回滚操作
    _IO_save_base = 0x0, 				# 备份缓冲区的起始地址
    _IO_backup_base = 0x0, 				# 备份缓冲区的第一个有效字符的指针
    _IO_save_end = 0x0, 				# 备份缓冲区的起始地址
    _markers = 0x0,						
    _chain = 0x7ffff7dd18e0, 			# 下一个文件流的地址
    _fileno = 0x1, 						# 文件描述符
    _flags2 = 0x0, 						# 标志符
    _old_offset = 0xffffffffffffffff, 
    _cur_column = 0x0, 					# 表示文件流中文件的行数
    _vtable_offset = 0x0, 				# 虚表指针偏移
    _shortbuf = {0x0}, 
    _lock = 0x7ffff7dd3780, 			# 锁结构体
    _offset = 0xffffffffffffffff,		# 文件描述符的偏移 
    _codecvt = 0x0, 
    _wide_data = 0x7ffff7dd17a0, 		# 宽字节流指针
    _freeres_list = 0x0, 
    _freeres_buf = 0x0, 
    __pad5 = 0x0, 
    _mode = 0xffffffff, 				
    _unused2 = {0x0 <repeats 20 times>}
```

> 上面成员的含义注释有可能不正确，因为是我根据变量名和注释进行理解的，如果不正确望指出，感谢~
>

其中地址0x602010、0x602410属于堆区的地址：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637893472146-0925dde8-9ddd-426b-b02c-6714ef229396.png)

我们来看一下_IO_2_1_stdout_具体的内容：

```c
pwndbg> heap
Allocated chunk | PREV_INUSE	# _IO_2_1_stdout_的缓冲区（文件流在libc中）
Addr: 0x602000
Size: 0x411

Allocated chunk | PREV_INUSE	# 新建的文件流(结构体locked_FILE而非缓冲区)
Addr: 0x602410					# new_f==(struct locked_FILE *) 0x602420
Size: 0x231

Top chunk | PREV_INUSE			# top_chunk
Addr: 0x602640
Size: 0x209c1

pwndbg> 
```

```c
pwndbg> x/16gx 0x602000   # _IO_2_1_stdout_
0x602000:       0x0000000000000000      0x0000000000000411 #缓冲区
0x602010:       0x676e617265627943      0x00000000000a6c65
    			# g n a r e b y C		#			  l e
......
pwndbg> 
```

> 将此处的内存与之前的成员_IO_buf_base、_IO_buf_end等进行对照就很容易理解他们的含义了。
>

**<font style="color:#F5222D;">还要补充一点，标准输入输出错误这三者的文件流的内存都在libc中，而我们新申请的文件流则处于heap中，这一点要注意区分。</font>**

来到这个函数的主要功能--将新建的文件流（_IO_FILE_plus结构体）连入到我们的链表中：

```c
fp->file._chain = (_IO_FILE *) _IO_list_all; //由于这里使用了头插法进行连入，所以指针_IO_list_all总是指向最新打开的文件流
_IO_list_all = fp;						
++_IO_list_all_stamp;  //++后_IO_list_all_stamp == 1
//_IO_list_all_stamp表示对_IO_list_all链表的修改次数
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637756822388-67a60ca9-e7e6-4d25-8d6b-c97a3f0edb7f.png)

最后对IO解锁后返回：

```c
#ifdef _IO_MTSAFE_IO
      _IO_funlockfile ((_IO_FILE *) fp);
      run_fp = NULL;
      _IO_lock_unlock (list_all_lock);
      _IO_cleanup_region_end (0);
#endif
```

## _IO_new_fopen->__fopen_internal->_IO_file_init
```c
fp->file._fileno = -1
```

这里的_fileno其实就是平常所说的文件描述符，在上图中可以知道已经初始化完成的标准输入stdin、标准输出stdout、标准错误输出stderr的文件描述符分别为0、1、2。文件描述符的定义时非负整数的索引值，但是在这里先将_fileno设置为-1，表示当前此文件流还没有完全初始化，是一个非法的值。

> 请容许我这么形象的比喻：一个Linux进程可以打开成百上千个文件，为了表示和区分已经打开的文件，Linux 会给每个文件分配一个编号（一个 ID），这个编号就是一个整数，被称为文件描述符（File Descriptor）。
>

## _IO_new_fopen->__fopen_internal
返回到__fopen_internal：

```c
#if  !_IO_UNIFIED_JUMPTABLES    //_IO_UNIFIED_JUMPTABLES == 1
  new_f->fp.vtable = NULL;      //不执行
#endif
  if (_IO_file_fopen ((_IO_FILE *) new_f, filename, mode, is32) != NULL)  //执行if
    return __fopen_maybe_mmap (&new_f->fp.file);
```

## _IO_new_fopen->__fopen_internal->_IO_file_fopen
_IO_file_fopen函数是打开文件的核心函数，我们来看一下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637757842004-8f63b114-5bde-442d-bc24-c4867681b0cf.png)

这个函数太长了需要分段切割查看，先来看传入的参数吧：

```c
_IO_FILE *
_IO_new_file_fopen (_IO_FILE *fp, const char *filename, const char *mode,
		    int is32not64)
{
    ......
}

● _IO_FILE *fp == 0x602420 ◂— 0xfbad248c
● const char *filename == 0x400752 ◂— insb   byte ptr [rdi], dx /* 'flag.txt' */
● const char *mode == 0x40074f ◂— jb     0x4007b3 /* 'rb' */
● int is32not64 == 0x1
```

注意这里传入的fp是指向_IO_FILE结构体而非_IO_FILE_plus，这是因为在传入参数时发生了强制类型转换(_IO_FILE *) new_f：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637799426417-4f83ee99-865e-4353-ab7f-1f6255d5005b.png)

如下所示，此函数的开头先定义了一些变量，老规矩我们边调试边理解其含义。

```c
  int oflags = 0, omode;
  int read_write;
  int oprot = 0666;
  int i;
  _IO_FILE *result;
#ifdef _LIBC     //_LIBC已被定义
  const char *cs;
  const char *last_recognized;
#endif
```

## _IO_new_fopen->__fopen_internal->_IO_file_fopen->_IO_file_is_open
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637934974805-52e370e5-ca3e-407b-95cf-d77678b4580d.png)

```c
#define _IO_file_is_open(__fp) ((__fp)->_fileno != -1)
```

_IO_file_is_open是一个宏函数，它检查结构体中的_fileno即文件表示符是否为-1，即检查IO链表_IO_list_all中是否有新增加的文件流（因为使用的是头插法所以可以直接检查），如果没有则会直接返回到上层的_IO_file_fopen函数。

## _IO_new_fopen->__fopen_internal->_IO_file_fopen
```c
  switch (*mode)
    {
    case 'r':
      omode = O_RDONLY;
      read_write = _IO_NO_WRITES;
      break;
    case 'w':
      omode = O_WRONLY;
      oflags = O_CREAT|O_TRUNC;
      read_write = _IO_NO_READS;
      break;
    case 'a':
      omode = O_WRONLY;
      oflags = O_CREAT|O_APPEND;
      read_write = _IO_NO_READS|_IO_IS_APPENDING;
      break;
    default:
      __set_errno (EINVAL);
      return NULL;
    }
```

mode是打开文件方式"rb"的指针，由于mode是char *类型，所以*mode == 'r'：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637800506484-5e508a4f-938c-4145-b675-d1d8aaec839d.png)

**参数oflags表示文件修改的方式--新建文档 or 对文档的内容进行追加**。进入到case 'r'语句中：

```c
    case 'r':
      omode = O_RDONLY;           //宏定义 #define O_RDONLY 00
      read_write = _IO_NO_WRITES; //宏定义 #define _IO_NO_WRITES 8 /* Writing not allowd */
      break;
```

**omode代表着文件的读写属性**--只读 or 只写 or 只读写，在此处omode为只读O_RDONLY。另一个参数**read_write表示文件的读写方式**，由于这里的omode为只读所以此处的读写方式为不允许写（_IO_NO_WRITES）。mode、omode、oflags、read_write之间的关系可以使用下表总结：

| mode | omode | oflags | read_write |
| --- | --- | --- | --- |
| r | O_RDONLY（只读） | NULL（无） | _IO_NO_WRITES（不允许写） |
| w | O_WRONLY（只写） | O_CREAT |  O_TRUNC（新建 | 覆盖） | _IO_NO_READS（不允许读） |
| a | O_WRONLY（只写） | O_CREAT | O_APPEND（新建 | 追加） | _IO_NO_READS|_IO_IS_APPENDING（不允许读但可以追加） |


> 所以根据两个switch case的先后顺序，mode的参数不能随便乱写，比如不能将wb写为bw。
>

接下来会继续遍历mode，每次遍历会将对应的所需要的变量赋值，关键的代码我都进行了注释，自己可以看看：

```c
#ifdef _LIBC 
  last_recognized = mode;  			  //mode文件打开方式的指针--处于.rodata段
#endif 
  for (i = 1; i < 7; ++i)			  //最多遍历7次
    {
      switch (*++mode)
	{
	case '\0':						  //遇到'\0'直接跳出循环		
	  break;
	case '+':
	  omode = O_RDWR; 				  //表示文件打开方式为追加打开  #define O_RDWR 02
	  read_write &= _IO_IS_APPENDING; //#define _IO_IS_APPENDING 0x1000,进行与运算，表示文件的读写方式为追加
#ifdef _LIBC
	  last_recognized = mode;		  
#endif
	  continue;
	case 'x':
	  oflags |= O_EXCL;
#ifdef _LIBC
	  last_recognized = mode;
#endif
	  continue;
	case 'b': 						  //以二进制文件方式打开
#ifdef _LIBC
	  last_recognized = mode;         
#endif
	  continue;
	case 'm':
	  fp->_flags2 |= _IO_FLAGS2_MMAP;
	  continue;
	case 'c':
	  fp->_flags2 |= _IO_FLAGS2_NOTCANCEL;
	  continue;
	case 'e':
#ifdef O_CLOEXEC
	  oflags |= O_CLOEXEC;
#endif
	  fp->_flags2 |= _IO_FLAGS2_CLOEXEC;
	  continue;
	default:
	  /* Ignore.  */
	  continue;
	}
      break;
    }
```

> 没有注释的都是不常见的这里就先不管了。'b'参数只是对last_recognized进行赋值，并没有体现“以二进制打开文件”的特征，这一点可能会在之后的文章中进行展现。
>

可以将上面的switch case整理为如下表格：

| mode | omode | oflags | read_write | _flags2 |
| --- | --- | --- | --- | --- |
| '\0' | 不变 | 不变 | 不变 | 不变 |
| '+' | O_RDWR<br/>（可读可写） | 不变 | &= _IO_IS_APPENDING<br/>（可追加） | 不变 |
| 'x' | 不变 | |= O_EXCL | 不变 | 不变 |
| 'b' | 不变 | 不变 | 不变 | 不变 |
| 'm' | 不变 | 不变 | 不变 | |= _IO_FLAGS2_MMAP |
| 'c' | 不变 | 不变 | 不变 | |= _IO_FLAGS2_NOTCANCEL |
| 'e' | 不变 | |= O_CLOEXEC | 不变 | |= _IO_FLAGS2_CLOEXEC |


上面的内容可以对应到我们学C语言时最基本的文件打开方式：

> 转自菜鸟教程：[https://www.runoob.com/cprogramming/c-file-io.html](https://www.runoob.com/cprogramming/c-file-io.html)
>

| <font style="color:rgb(255, 255, 255);">模式</font> | <font style="color:rgb(255, 255, 255);">描述</font> |
| --- | --- |
| <font style="color:rgb(51, 51, 51);">r</font> | <font style="color:rgb(51, 51, 51);">打开一个已有的文本文件，允许读取文件。</font> |
| <font style="color:rgb(51, 51, 51);">w</font> | <font style="color:rgb(51, 51, 51);">打开一个文本文件，允许写入文件。如果文件不存在，则会创建一个新文件。在这里，您的程序会从文件的开头写入内容。如果文件存在，则该会被截断为零长度，重新写入。</font> |
| <font style="color:rgb(51, 51, 51);">a</font> | <font style="color:rgb(51, 51, 51);">打开一个文本文件，以追加模式写入文件。如果文件不存在，则会创建一个新文件。在这里，您的程序会在已有的文件内容中追加内容。</font> |
| <font style="color:rgb(51, 51, 51);">r+</font> | <font style="color:rgb(51, 51, 51);">打开一个文本文件，允许读写文件。</font> |
| <font style="color:rgb(51, 51, 51);">w+</font> | <font style="color:rgb(51, 51, 51);">打开一个文本文件，允许读写文件。如果文件已存在，则文件会被截断为零长度，如果文件不存在，则会创建一个新文件。</font> |
| <font style="color:rgb(51, 51, 51);">a+</font> | <font style="color:rgb(51, 51, 51);">打开一个文本文件，允许读写文件。如果文件不存在，则会创建一个新文件。读取会从文件的开头开始，写入则只能是追加模式。</font> |


> 如果处理的是二进制文件，则需使用下面的访问模式来取代上面的访问模式："rb", "wb", "ab", "rb+", "r+b", "wb+", "w+b", "ab+", "a+b"
>

_flags2字段隐含了一些关于文件的属性，这里含义表现的很模糊，下面只扔一个宏定义吧：

```c
// glibc-2.23/libio/libio.h
#define _IO_FLAGS2_MMAP 1
#define _IO_FLAGS2_NOTCANCEL 2
#ifdef _LIBC
# define _IO_FLAGS2_FORTIFY 4
#endif
#define _IO_FLAGS2_USER_WBUF 8
#ifdef _LIBC
# define _IO_FLAGS2_SCANF_STD 16
# define _IO_FLAGS2_NOCLOSE 32
# define _IO_FLAGS2_CLOEXEC 64
#endif
```

## _IO_new_fopen->__fopen_internal->_IO_file_fopen->_IO_file_open
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637801299414-cffe8b5a-b454-4a29-9dbb-a1eda8f983d5.png)

```c
result = _IO_file_open (fp, filename, omode|oflags, oprot, read_write, is32not64);
------------------------------------------------------------------------------------

_IO_FILE *
_IO_file_open (_IO_FILE *fp, const char *filename, int posix_mode, int prot,
	       int read_write, int is32not64)
{
    // *fp：结构体_IO_FILE
    // *filename文件名称
    // posix_mode：omode和oflags的与运算
    // prot文件的权限，默认为0666
    // read_write文件读写的方式
    // is32not64 == 1
	......
}
libc_hidden_def (_IO_file_open)
```

先来看第一段代码：

```c
  int fdesc;
#ifdef _LIBC  //宏_LIBC已经定义
  if (__glibc_unlikely (fp->_flags2 & _IO_FLAGS2_NOTCANCEL))  // fp->_flags2 == 0
      														  // #define _IO_FLAGS2_NOTCANCEL 2
    fdesc = open_not_cancel (filename,
			     posix_mode | (is32not64 ? 0 : O_LARGEFILE), prot);
  else
    fdesc = open (filename, posix_mode | (is32not64 ? 0 : O_LARGEFILE), prot);  // 进入else分支
#else
  fdesc = open (filename, posix_mode, prot);
#endif
```

在该函数的开头首先先判断该文件流的_flags2是否设置了_IO_FLAGS2_NOTCANCEL属性，即在之前的mode中是否使用了'c'模式，有则会执行open_not_cancel函数，没有则会执行open。这里会进入else分支，该函数的本质是调用了syscall：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637802547561-8b713ce9-5f55-4549-8487-17aa8e571602.png)

函数返回后fdesc == 3，这是Linux内核为文件流新分配的文件描述符。然后调用_IO_mask_flags根据之前通过switch case得到的read_write属性对_flags进行重新设置。若读写方式为a(追加)，则会将文件末尾作为文件的指针。

```c
  if (fdesc < 0)  //若fdesc < 0 则表示文件打开失败，系统调用出现问题
    return NULL;
  fp->_fileno = fdesc;  // 设置文件描述符
  _IO_mask_flags (fp, read_write,_IO_NO_READS+_IO_NO_WRITES+_IO_IS_APPENDING); //设置_flags
        '''
        #define _IO_mask_flags(fp, f, mask) \
               ((fp)->_flags = ((fp)->_flags & ~(mask)) | ((f) & (mask))) 
        '''
  /* For append mode, send the file offset to the end of the file.  Don't
     update the offset cache though, since the file handle is not active.  */
  if ((read_write & (_IO_IS_APPENDING | _IO_NO_READS)) //针对append模式
      == (_IO_IS_APPENDING | _IO_NO_READS))
    {
      _IO_off64_t new_pos = _IO_SYSSEEK (fp, 0, _IO_seek_end);  //文件指针new_pos移动到文件尾
      if (new_pos == _IO_pos_BAD && errno != ESPIPE)
	{
	  close_not_cancel (fdesc);
	  return NULL;
	}
    }
  _IO_link_in ((struct _IO_FILE_plus *) fp);
  return fp;
```

> fp->_fileno == 3；fp->_flags ==0xfbad2488
>

## _IO_new_fopen->__fopen_internal->_IO_file_fopen->_IO_file_open->_IO_link_in
最后会调用_IO_link_in函数确保该结构体已链入_IO_list_all链表(因为在_IO_link_in函数中会有对_IO_LINKED的check，所以并不是重复链入)，至此_IO_file_open函数执行完毕。

```c
void
_IO_link_in (struct _IO_FILE_plus *fp)
{
  if ((fp->file._flags & _IO_LINKED) == 0)   //判断是否在_IO_list_all中
    {
      fp->file._flags |= _IO_LINKED;
#ifdef _IO_MTSAFE_IO
      _IO_cleanup_region_start_noarg (flush_cleanup);
      _IO_lock_lock (list_all_lock);
      run_fp = (_IO_FILE *) fp;
      _IO_flockfile ((_IO_FILE *) fp);
#endif
      fp->file._chain = (_IO_FILE *) _IO_list_all;
      _IO_list_all = fp;
      ++_IO_list_all_stamp;
#ifdef _IO_MTSAFE_IO
      _IO_funlockfile ((_IO_FILE *) fp);
      run_fp = NULL;
      _IO_lock_unlock (list_all_lock);
      _IO_cleanup_region_end (0);
#endif
    }
}
```

## _IO_new_fopen->__fopen_internal->_IO_file_fopen
该函数剩下的代码如下，其中的大部分是对宽字节结构体进行设置，这里就不再研究了：

```c
  if (result != NULL)
    {
#ifndef __ASSUME_O_CLOEXEC
      if ((fp->_flags2 & _IO_FLAGS2_CLOEXEC) != 0 && __have_o_cloexec <= 0)
	{
	  int fd = _IO_fileno (fp);
	  if (__have_o_cloexec == 0)
	    {
	      int flags = __fcntl (fd, F_GETFD);
	      __have_o_cloexec = (flags & FD_CLOEXEC) == 0 ? -1 : 1;
	    }
	  if (__have_o_cloexec < 0)
	    __fcntl (fd, F_SETFD, FD_CLOEXEC);
	}
#endif

      /* Test whether the mode string specifies the conversion.  */
      cs = strstr (last_recognized + 1, ",ccs=");
      if (cs != NULL)
	{
	  /* Yep.  Load the appropriate conversions and set the orientation
	     to wide.  */
	  struct gconv_fcts fcts;
	  struct _IO_codecvt *cc;
	  char *endp = __strchrnul (cs + 5, ',');
	  char *ccs = malloc (endp - (cs + 5) + 3);

	  if (ccs == NULL)
	    {
	      int malloc_err = errno;  /* Whatever malloc failed with.  */
	      (void) _IO_file_close_it (fp);
	      __set_errno (malloc_err);
	      return NULL;
	    }

	  *((char *) __mempcpy (ccs, cs + 5, endp - (cs + 5))) = '\0';
	  strip (ccs, ccs);

	  if (__wcsmbs_named_conv (&fcts, ccs[2] == '\0'
				   ? upstr (ccs, cs + 5) : ccs) != 0)
	    {
	      /* Something went wrong, we cannot load the conversion modules.
		 This means we cannot proceed since the user explicitly asked
		 for these.  */
	      (void) _IO_file_close_it (fp);
	      free (ccs);
	      __set_errno (EINVAL);
	      return NULL;
	    }

	  free (ccs);

	  assert (fcts.towc_nsteps == 1);
	  assert (fcts.tomb_nsteps == 1);

	  fp->_wide_data->_IO_read_ptr = fp->_wide_data->_IO_read_end;
	  fp->_wide_data->_IO_write_ptr = fp->_wide_data->_IO_write_base;

	  /* Clear the state.  We start all over again.  */
	  memset (&fp->_wide_data->_IO_state, '\0', sizeof (__mbstate_t));
	  memset (&fp->_wide_data->_IO_last_state, '\0', sizeof (__mbstate_t));

	  cc = fp->_codecvt = &fp->_wide_data->_codecvt;

	  /* The functions are always the same.  */
	  *cc = __libio_codecvt;

	  cc->__cd_in.__cd.__nsteps = fcts.towc_nsteps;
	  cc->__cd_in.__cd.__steps = fcts.towc;

	  cc->__cd_in.__cd.__data[0].__invocation_counter = 0;
	  cc->__cd_in.__cd.__data[0].__internal_use = 1;
	  cc->__cd_in.__cd.__data[0].__flags = __GCONV_IS_LAST;
	  cc->__cd_in.__cd.__data[0].__statep = &result->_wide_data->_IO_state;

	  cc->__cd_out.__cd.__nsteps = fcts.tomb_nsteps;
	  cc->__cd_out.__cd.__steps = fcts.tomb;

	  cc->__cd_out.__cd.__data[0].__invocation_counter = 0;
	  cc->__cd_out.__cd.__data[0].__internal_use = 1;
	  cc->__cd_out.__cd.__data[0].__flags
	    = __GCONV_IS_LAST | __GCONV_TRANSLIT;
	  cc->__cd_out.__cd.__data[0].__statep =
	    &result->_wide_data->_IO_state;

	  /* From now on use the wide character callback functions.  */
	  _IO_JUMPS_FILE_plus (fp) = fp->_wide_data->_wide_vtable;

	  /* Set the mode now.  */
	  result->_mode = 1;
	}
    }
  return result;
```

## _IO_new_fopen->__fopen_internal
返回到__fopen_internal函数：

```c
  if (_IO_file_fopen ((_IO_FILE *) new_f, filename, mode, is32) != NULL)
    return __fopen_maybe_mmap (&new_f->fp.file);  //进入

  _IO_un_link (&new_f->fp);   
  free (new_f);    //WARNING:UAF
  return NULL;   
```

> new_f未置NULL，存在UAF。
>

如果无法进入if语句的__fopen_maybe_mmap即刚刚的_IO_file_fopen函数返回的result为NULL，则表示文件打开失败，此时会释放开头的结构体指针new_f，反之则进入下面的__fopen_maybe_mmap函数：

```c
_IO_FILE *
__fopen_maybe_mmap (_IO_FILE *fp)
{
#ifdef _G_HAVE_MMAP
  if ((fp->_flags2 & _IO_FLAGS2_MMAP) && (fp->_flags & _IO_NO_WRITES)) 
    {  // 检查是否设置了_flags2的_IO_FLAGS2_MMAP和_flags的_IO_NO_WRITES
      /* Since this is read-only, we might be able to mmap the contents
	 directly.  We delay the decision until the first read attempt by
	 giving it a jump table containing functions that choose mmap or
	 vanilla file operations and reset the jump table accordingly.  */

      if (fp->_mode <= 0)   //_mode表示是否使用宽字节流
	_IO_JUMPS_FILE_plus (fp) = &_IO_file_jumps_maybe_mmap;  //重新设置_IO_FILE_plus的虚表指针
      else
	_IO_JUMPS_FILE_plus (fp) = &_IO_wfile_jumps_maybe_mmap; //重新设置_IO_FILE_plus的虚表指针
      fp->_wide_data->_wide_vtable = &_IO_wfile_jumps_maybe_mmap;  //设置宽字节流的虚表
    }
#endif
  return fp;  //fp是最终的结果，直接返回到main函数。
}
```

# 总结
恭喜你能看到这里，之前的篇幅完成了对fopen函数源码的分析，大致概括下来就3个操作：

1. 为文件流申请空间；
2. 初始化FILE结构体及虚表，将文件流链入_IO_list_all链表中；
3. 打开文件流，包括读取文件属性以及利用系统调用打开文件。

还有，除了在打开文件时日常用到的r、w、a、b、+之外还有x、m、c、e这4个参数，而且参数的先后也有所要求不能随意的颠倒顺序。

