> 文章思路来自：[https://blog.csdn.net/yan_star/article/details/88937283](https://blog.csdn.net/yan_star/article/details/88937283)
>
> 示例附件下载：链接：[https://pan.baidu.com/s/1zNtWgbL8Wo-bRCyaGCOtkQ](https://pan.baidu.com/s/1zNtWgbL8Wo-bRCyaGCOtkQ)
>

> 提取码：pevi 
>

缓冲区溢出的简单介绍：

缓冲区溢出：简单的说，缓冲区溢出就是超长的数据向小缓冲区复制，导致数据超出了小缓冲区，导致缓冲区其他的数据遭到破坏，这就是缓冲区溢出。而**<font style="color:#F5222D;">栈溢出是缓冲区溢出的一种</font>**，也是最常见的。只不过栈溢出发生在栈，堆溢出发生在堆，其实都是一样的。

栈的简单介绍：

栈：栈是一种计算机系统中的数据结构，它按照先进后出的原则存储数据，先进入的数据被压入栈底，最后的数据在栈顶，需要读数据的时候从栈顶开始弹出数据（最后一个数据被第一个读出来），是一种特殊的线性表。栈的操作常用的有进栈（PUSH），出栈（POP），还有常用的标识栈顶和栈底。

可以把栈想象成一摞扑克牌一样，一张一张叠加起来。（如下图的a1，a2，……，an）。

进栈（PUSH）：将一个数据放入栈里叫进栈（PUSH），相当于在扑克牌的在最上面放了一张新的扑克牌。

出栈（POP）：将一个数据从栈里取出叫出栈（POP），相当于在扑克牌的在最上面拿走了一张扑克牌。

栈顶：常用寄存器ESP，ESP是栈指针寄存器，其内存放着一个指针，该指针永远指向系统栈最上面一个栈帧的栈顶。

栈底：常用寄存器EBP，EBP是基址指针寄存器，其内存放着一个指针，该指针永远指向系统栈最上面一个栈帧的底部。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596098418455-59b5b1eb-02c0-4296-b8ef-c53eb1600e40.png)

接下来编写一个简单的程序来介绍一下栈溢出：

> 程序使用VS code进行编译
>

源代码如下：

```cpp
#include<stdio.h>
#include<string.h>

#define PASSWORD "12345"

int test(char *password){
    int ret_num;
    char buffer[8];
    ret_num=strcmp(password,PASSWORD);//相同返回0
    strcpy(buffer,password);
    return ret_num;
}
int main(){
    int flag=0;
    char password[88];
    while (1){
        printf("plz input your password:\n");
        scanf("%s",password);
        flag=test(password);
        if(flag){
            printf("incorrect password!\n\n");
        }
        else{
             printf("Success!You are right!\n");
        }
    }
    return 0;
}
```

程序的逻辑很简单，首先在代码开始定义了一个全局变量（#define PASSWORD "12345"），如果用户输入的密码和“12345”相等，则打印出“Success!You are right!”，否则输出“incorrect password!”

值得注意的是，程序缓冲区的溢出点在“strcpy(buffer,password);”，在test函数中，开辟了8个字节的数组空间，然后再将用户输入的数据复制到这个数组空间中，这就为栈溢出创造了条件，看下结果：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596098893021-d9b79209-518c-47df-b96f-33036f6e1255.png)

发现了一个有趣的结果，密码12345是正确的密码，这是我们自己定义的，但是当我输入“qqqqqqqq”时，显示的也是正确的结果，下面用xdbg64和IDA进行进一步的分析。

先来看看xdbg64：

在程序中搜索字符串“plz input your password:”：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596099051194-a0e51b8d-ff47-49c0-a42e-26da74207f3d.png)

双击进入“plz input your password:”，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596099088559-9c0dc691-edd5-4b3b-b9b9-ad7fa2acbc79.png)

在scanf函数后下F2断点

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596099128421-9812da1d-e749-42b0-997c-dc4bcdafbdd9.png)

下面的call 1.401550应该是我们要调用的test函数，为了验证这个想法，看看IDA中的汇编

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596099261878-2b0c3930-9d04-42a7-a2cf-964e6b1aab72.png)

call 1.401550的确调用的是test函数，看一下IDA中main函数的伪代码

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596099438226-e0e086f6-9246-47d0-bc25-168a406796f7.png)

其中v4就是源代码中的变量flag（用来接收test函数的返回值），双击进入test函数：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596099531051-7b0dc6b4-253c-434f-a0f0-eed47dac8124.png)

由于在前面知道输入“qqqqqqqq”（其实“12345678”也可以）会导致栈溢出，回过头来看一下test函数的源代码：

```cpp
int test(char *password){
    int ret_num;
    char buffer[8];
    ret_num=strcmp(password,PASSWORD);//相同返回0
    strcpy(buffer,password);
    return ret_num;
}
```

可以看到v3就是原变量ret_num，Dest就是原来的buffer，双击任意一个变量，来到IDA的栈界面：

> v3就是var_4
>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596101142490-e5f7821a-3fb8-474e-a6d8-1e3618aa143e.png)

可以看到Dest（buffer）的空间为0C-04=8个字节，当strcpy为8个字节时，程序会导致栈溢出覆盖掉返回值ret_num。具体点来说就是我们输入的“qqqqqqqq”为8个字节，但是都知道在C语言中字符串后面还有“字符串截断符0x00”，这个截断符00将var_4由原来的01覆盖为00，这样就输出了最终的“Success!You are right!”

回过头来看xdbg64：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596101896389-87e4f7ec-c362-4279-beb1-50b6818de8bd.png)

单步步入401550函数（即test函数）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596102172265-8cd3752e-648b-4a03-ad15-d9e3b5503a16.png)

从上面的图可以知道strcmp的返回值是由eax寄存器进行接收的，单步步过strcpy函数,eax的值为1，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596102342351-56bada63-8280-4ecc-9952-3a30fa78e7c3.png)

接下来的mov dword ptr ss:[rbp-4],eax，是将返回值赋值到ss:[rbp-4]中，右键在数据窗口中进行跟随以方便观察其变化：

单步步过mov dword ptr ss:[rbp-4],eax前

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596102622739-3d258fbf-0d39-437e-8837-cbc9d18f3b1e.png)

单步步过mov dword ptr ss:[rbp-4],eax后

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596102651297-78773603-3824-460a-92fd-c4c0b3736822.png)

RIP来到：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596102829186-73cdfd52-b059-4d3f-9337-785d4c2ba9cb.png)

看一下此时的栈窗口和数据窗口

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596102909134-c7546e00-e59e-4ef2-9a8d-b33fe24bbb71.png)![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596102910485-2528bee0-b7b1-49bd-bf85-5298df629833.png)

单步步过：

先来看数据窗口：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596102964503-1d9c9812-8e8c-46e8-90c1-20c9531aed99.png)

返回值已经变为00

再来看栈窗口

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1596103158335-0f5dd3a2-30c9-4ae0-8a87-4e46c48cacbb.png)

已发生栈溢出，这样就输出了success

> 注意，如果密码当初是定义为1234567，当我们输入01234567的时候是不行的，虽说0123457也是8位数，但是01234567小于1234567，返回值是-1，在内存里将按照补码存负数，那么字符串截断后符0x00淹没后，变成0x00FFFFFF，还是非0，这样密码则错误！
>

