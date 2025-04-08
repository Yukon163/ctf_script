习题如下：

[BUUCTF-RoarCTF2019-polyre（控制平坦化、反虚假控制流脚本、CRC64）](https://www.yuque.com/cyberangel/vqcmca/ccy1c4)

> **目录是随后添加的,可能导致行文不畅,见谅**
>

---

> 链接：[https://pan.baidu.com/s/1fWaMKvT-Dn-aoStWlzzgQw](https://pan.baidu.com/s/1fWaMKvT-Dn-aoStWlzzgQw)
>
> 提取码：uj9s
>

**注：在此篇文章中并不会阐述ollvm混淆及反混淆的原理，****<font style="color:#F5222D;">只注重利用符号执行来去除这些反混淆</font>****<font style="color:#F5222D;">（针对控制流平坦化，虚假控制流）与去除混淆前后的对比</font>****，没有指令替换是因为我没有找到相关示例，先不学它。**

<font style="color:#585858;">简单来说，ollvm由3种不同的保护方式组成：控制流平坦化，虚假控制流和指令替换，这些保护方式可以累加，对于静态分析来说混淆后代码非常复杂。在这篇文章中，我们将展示如何逐一去除每种保护</font><font style="color:#585858;">。</font><font style="color:#585858;"></font>

<font style="color:#585858;">首先我们先启动虚拟机中的angr环境，执行代码：</font>

```bash
ubuntu@ubuntu:~/Desktop/ollvm$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/ollvm$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/ollvm$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/ollvm$ 
```

# 一、控制流平坦化（flat_control_flow）
## ①示例源码
接下来我们先看ollvm混淆当中的控制流平坦化（flat_control_flow），先看一下演示的源码：

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int check_password(char *passwd)
{
    int i, sum = 0;
    for (i = 0; ; i++)
    {
        if (!passwd[i])
        {
            break;
        }
        sum += passwd[i];
    }
    if (i == 4)
    {
        if (sum == 0x1a1 && passwd[3] > 'c' && passwd[3] < 'e' && passwd[0] == 'b')
        {
            if ((passwd[3] ^ 0xd) == passwd[1])
            {
                return 1;
            }   
            puts("Orz...");
        }
    }
    else
    {
        puts("len error");
    }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2)
    {
        puts("error");
        return 1;
    }
    if (check_password(argv[1]))
    {
        puts("Congratulation!");
    }
    else
    {
        puts("error");
    }
    return 0;
}
```

## ②混淆之后
代码可以仔细看也可以不看，这都无所谓，只知道我们利用angr环境进行混淆的去除就行了。

### main函数
将混淆后的示例文件(check_passwd_x8664_flat)载入IDA中，看一下main函数的流程图：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589703670531-a51d494e-0344-42cd-9c12-273c7032f390.png)

伪代码如下：

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  signed int v3; // eax
  int v4; // eax
  signed int v5; // ecx
  signed int v7; // [rsp+44h] [rbp-1Ch]
  int v8; // [rsp+58h] [rbp-8h]

  v8 = 0;
  v7 = 1633153878;
  do
  {
    while ( v7 > -1424773165 )
    {
      if ( v7 > -608328430 )
      {
        if ( v7 > 1948349962 )
        {
          if ( v7 == 1948349963 )
          {
            v8 = 1;
            v7 = -1883523171;
            puts("error");
          }
        }
        else if ( v7 > 1633153877 )
        {
          if ( v7 == 1633153878 )
          {
            v3 = 1228678806;
            envp = (const char **)(unsigned int)argc;
            if ( argc != 2 )
              v3 = 1948349963;
            v7 = v3;
          }
        }
        else
        {
          switch ( v7 )
          {
            case -608328429:
              v8 = 0;
              v7 = -1883523171;
              break;
            case -549365528:
              v7 = -608328429;
              puts("Congratulation!");
              break;
            case 1228678806:
              v4 = check_password(argv[1], argv, envp);
              v5 = -1424773164;
              envp = (const char **)3745601768LL;
              if ( v4 )
                v5 = -549365528;
              v7 = v5;
              break;
          }
        }
      }
      else if ( v7 == -1424773164 )
      {
        v7 = -608328429;
        puts("error");
      }
    }
  }
  while ( v7 != -1883523171 );
  return v8;
}
```

### check_password函数
再来看一下check_password函数的流程图

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589703848359-4e0dfa14-0503-4fb3-a8e7-d87688bc985f.png)

伪代码：

```c
__int64 __fastcall check_password(_BYTE *a1)
{
  signed int v1; // eax
  signed int v2; // eax
  signed int v3; // eax
  signed int v4; // eax
  signed int v5; // eax
  signed int v6; // eax
  signed int v7; // eax
  signed int v9; // [rsp+84h] [rbp-1Ch]
  int v10; // [rsp+88h] [rbp-18h]
  int v11; // [rsp+8Ch] [rbp-14h]
  unsigned int v12; // [rsp+9Ch] [rbp-4h]

  v10 = 0;
  v11 = 0;
  v9 = -955205777;
  do
  {
    while ( 1 )
    {
      while ( 1 )
      {
        while ( 1 )
        {
          while ( 1 )
          {
            while ( 1 )
            {
              while ( 1 )
              {
                while ( 1 )
                {
                  while ( 1 )
                  {
                    while ( 1 )
                    {
                      while ( v9 <= -1353076680 )
                      {
                        if ( v9 == -1875835489 )
                        {
                          ++v11;
                          v9 = -955205777;
                        }
                      }
                      if ( v9 > -1179578599 )
                        break;
                      if ( v9 == -1353076679 )
                        v9 = -839392482;
                    }
                    if ( v9 > -1004319330 )
                      break;
                    if ( v9 == -1179578598 )
                    {
                      v9 = -839392482;
                      puts("len error");
                    }
                  }
                  if ( v9 <= 757515321 )
                    break;
                  if ( v9 == 757515322 )
                    v9 = 64169026;
                }
                if ( v9 <= 636151742 )
                  break;
                if ( v9 == 636151743 )
                {
                  v3 = -1353076679;
                  if ( v10 == 417 )
                    v3 = 213586486;
                  v9 = v3;
                }
              }
              if ( v9 > -955205778 )
                break;
              if ( v9 == -1004319329 )
              {
                v12 = 1;
                v9 = -370272981;
              }
            }
            if ( v9 > -902957347 )
              break;
            if ( v9 == -955205777 )
            {
              v1 = 757515322;
              if ( a1[v11] )
                v1 = 40935283;
              v9 = v1;
            }
          }
          if ( v9 > -839392483 )
            break;
          if ( v9 == -902957346 )
          {
            v5 = -1353076679;
            if ( (char)a1[3] < 101 )
              v5 = 463203461;
            v9 = v5;
          }
        }
        if ( v9 > -370272982 )
          break;
        if ( v9 == -839392482 )
        {
          v12 = 0;
          v9 = -370272981;
        }
      }
      if ( v9 <= -137643622 )
        break;
      if ( v9 > 40935282 )
      {
        if ( v9 > 463203460 )
        {
          if ( v9 == 463203461 )
          {
            v6 = -1353076679;
            if ( *a1 == 98 )
              v6 = 428283389;
            v9 = v6;
          }
        }
        else if ( v9 > 428283388 )
        {
          if ( v9 == 428283389 )
          {
            v7 = -137643621;
            if ( ((char)a1[3] ^ 0xD) == (char)a1[1] )
              v7 = -1004319329;
            v9 = v7;
          }
        }
        else
        {
          switch ( v9 )
          {
            case 40935283:
              v10 += (char)a1[v11];
              v9 = -1875835489;
              break;
            case 64169026:
              v2 = -1179578598;
              if ( v11 == 4 )
                v2 = 636151743;
              v9 = v2;
              break;
            case 213586486:
              v4 = -1353076679;
              if ( (char)a1[3] > 99 )
                v4 = -902957346;
              v9 = v4;
              break;
          }
        }
      }
      else if ( v9 == -137643621 )
      {
        v9 = -1353076679;
        puts("Orz...");
      }
    }
  }
  while ( v9 != -370272981 );
  return v12;
}
```

emmm，混淆后的样子大概就是这鬼样

## ③混淆之前
再来看一下混淆前的流程图：

### main函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589703919494-79d83e88-b090-4e72-bb06-aa57dfe07d26.png)

伪代码：

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  int result; // eax

  if ( argc == 2 )
  {
    if ( (unsigned int)check_password(argv[1], argv, envp) )
      puts("Congratulation!");
    else
      puts("error");
    result = 0;
  }
  else
  {
    puts("error");
    result = 1;
  }
  return result;
}
```

### check_password函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589703954045-afd1891b-4f08-4932-98cf-da6076481141.png)

伪代码：

```c
signed __int64 __fastcall check_password(_BYTE *a1)
{
  int i; // [rsp+18h] [rbp-8h]
  int v3; // [rsp+1Ch] [rbp-4h]

  v3 = 0;
  for ( i = 0; a1[i]; ++i )
    v3 += (char)a1[i];
  if ( i == 4 )
  {
    if ( v3 == 417 && a1[3] > 99 && a1[3] <= 100 && *a1 == 98 )
    {
      if ( (a1[3] ^ 0xD) == a1[1] )
        return 1LL;
      puts("Orz...");
    }
  }
  else
  {
    puts("len error");
  }
  return 0LL;
}
```

差别真的不是一点点。。。

## ④去除混淆
### 去除混淆--main函数
接下来我们开始去除混淆，将反混淆的脚本下载下来后，我们先去除main函数的混淆，执行命令：

**(针对文件check_passwd_x8664_flat)**

```bash
(angr) ubuntu@ubuntu:~/Desktop/ollvm/flat_control_flow$ python3 deflat.py -f check_passwd_x8664_flat --addr 0x4009A0
*******************relevant blocks************************
prologue: 0x4009a0
main_dispatcher: 0x4009c3
pre_dispatcher: 0x400b82
retn: 0x400b79
relevant_blocks: ['0x400b48', '0x400ade', '0x400ac0', '0x400b66', '0x400b2a', '0x400b03']
*******************symbolic execution*********************
-------------------dse 0x400b48---------------------
-------------------dse 0x400ade---------------------
-------------------dse 0x400ac0---------------------
-------------------dse 0x400b66---------------------
-------------------dse 0x400b2a---------------------
-------------------dse 0x400b03---------------------
-------------------dse 0x4009a0---------------------
************************flow******************************
0x400b48:  ['0x400b66']
0x400ade:  ['0x400b79']
0x400ac0:  ['0x400ade', '0x400b03']
0x400b66:  ['0x400b79']
0x400b2a:  ['0x400b66']
0x400b03:  ['0x400b2a', '0x400b48']
0x4009a0:  ['0x400ac0']
0x400b79:  []
************************patch*****************************
Successful! The recovered file: check_passwd_x8664_flat_recovered
(angr) ubuntu@ubuntu:~/Desktop/ollvm/flat_control_flow$ 
```

> 0x4009A0是main函数起始的地址，可以在IDA中查看
>

反混淆后的文件将以check_passwd_x8664_flat_recovered保存，我们给他重命名一下为“check_passwd_x8664_flat_recovered_main”意思是我们只去除了main函数的混淆，载入到IDA里看一下：

流程图如下：（这么长是因为有许多的nop指令存在）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589704633865-fb4768ad-bea5-48b1-971c-b4c156e89274.png)

main函数的伪代码如下：

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  int v4; // [rsp+58h] [rbp-8h]

  if ( argc == 2 )
  {
    if ( (unsigned int)check_password(argv[1], argv, 2LL, 1948349963LL) )
      puts("Congratulation!");
    else
      puts("error");
    v4 = 0;
  }
  else
  {
    v4 = 1;
    puts("error");
  }
  return v4;
}
```

由于我们没有对check_password函数进行反混淆，因此它还是原来那种鬼样。。。

### 去除混淆--check_password函数
执行命令去除check_password函数的反混淆：

**(针对文件check_passwd_x8664_flat)**

```bash
(angr) ubuntu@ubuntu:~/Desktop/ollvm/flat_control_flow$ python3 deflat.py -f check_passwd_x8664_flat --addr 0x400530
*******************relevant blocks************************
prologue: 0x400530
main_dispatcher: 0x400554
pre_dispatcher: 0x40099b
retn: 0x40098f
relevant_blocks: ['0x400837', '0x40094f', '0x40080d', '0x40095b', '0x40086a', '0x40091b', '0x4007ec', '0x4008a9', '0x40097c', '0x4008cc', '0x40092e', '0x4008ee', '0x400819', '0x40084e', '0x400886']
*******************symbolic execution*********************
-------------------dse 0x400837---------------------
-------------------dse 0x40094f---------------------
-------------------dse 0x40080d---------------------
-------------------dse 0x40095b---------------------
-------------------dse 0x40086a---------------------
-------------------dse 0x40091b---------------------
-------------------dse 0x4007ec---------------------
-------------------dse 0x4008a9---------------------
-------------------dse 0x40097c---------------------
-------------------dse 0x4008cc---------------------
-------------------dse 0x40092e---------------------
-------------------dse 0x4008ee---------------------
-------------------dse 0x400819---------------------
-------------------dse 0x40084e---------------------
-------------------dse 0x400886---------------------
-------------------dse 0x400530---------------------
************************flow******************************
0x400837:  ['0x4007ec']
0x40094f:  ['0x40097c']
0x40080d:  ['0x40084e']
0x40095b:  ['0x40097c']
0x40086a:  ['0x400886', '0x40094f']
0x40091b:  ['0x40098f']
0x4007ec:  ['0x400819', '0x40080d']
0x4008a9:  ['0x4008cc', '0x40094f']
0x40097c:  ['0x40098f']
0x4008cc:  ['0x4008ee', '0x40094f']
0x40092e:  ['0x40094f']
0x4008ee:  ['0x40091b', '0x40092e']
0x400819:  ['0x400837']
0x40084e:  ['0x40086a', '0x40095b']
0x400886:  ['0x4008a9', '0x40094f']
0x400530:  ['0x4007ec']
0x40098f:  []
************************patch*****************************
Successful! The recovered file: check_passwd_x8664_flat_recovered
(angr) ubuntu@ubuntu:~/Desktop/ollvm/flat_control_flow$
```

> 0x400530是check_password函数起始的地址，可以在IDA中查看
>

将反混淆后的文件重命名为“check_passwd_x8664_flat_recovered_check_password”,载入IDA中，

流程图：（存在大量的nop）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589705665614-ad30c1b0-f12b-4797-8e7f-8f9f42d284ac.png)

伪代码：

```bash
__int64 __fastcall check_password(_BYTE *a1)
{
  int v2; // [rsp+88h] [rbp-18h]
  int i; // [rsp+8Ch] [rbp-14h]

  v2 = 0;
  for ( i = 0; a1[i]; ++i )
    v2 += (char)a1[i];
  if ( i != 4 )
  {
    puts("len error");
LABEL_14:
    return 0;
  }
  if ( v2 != 417 || (char)a1[3] <= 99 || (char)a1[3] >= 101 || *a1 != 98 )
    goto LABEL_14;
  if ( ((char)a1[3] ^ 0xD) != (char)a1[1] )
  {
    puts("Orz...");
    goto LABEL_14;
  }
  return 1;
}
```

这样，混淆就基本上取出来，可以对比一下前后的伪代码，2333~

---

# 二、虚假控制流（bogus_control_flow）
接下来看虚假控制流（bogus_control_flow）：

先切换一下路径：

```bash
ubuntu@ubuntu:~/Desktop/ollvm/flat_control_flow$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/ollvm/flat_control_flow$ cd ../
(angr) ubuntu@ubuntu:~/Desktop/ollvm$ cd bogus_control_flow
(angr) ubuntu@ubuntu:~/Desktop/ollvm/bogus_control_flow$ 
```

## ①示例源码
```c
#include <stdio.h>

unsigned int target_function(unsigned int n)
{
    unsigned int mod = n % 4;
    unsigned int result = 0 ;

    if (mod == 0){
        result = (n | 0xBAAAD0BF) * (2 ^ n);
    } else if (mod == 1){
        result = (n & 0xBAAAD0BF) * (3 + n);
    } else if (mod == 2){
        result = (n ^ 0xBAAAD0BF) * (4 | n);
    } else {
        result = (n + 0xBAAAD0BF) * (5 & n);
    }

    return result;
}

void main()
{
    unsigned int value = 0x12345;
    unsigned int result = target_function(value);
    printf("result: 0x%x\n", result);
}
```

## ②混淆之前
### main函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589708217196-b4c17381-e809-4827-a1af-bbf424f4f3f5.png)

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  int v3; // eax

  v3 = target_function(74565);
  return printf("result: 0x%x\n", v3);
}
```

### target_function函数:
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589708250556-74f0644b-9b57-4560-9a3f-7eafd2a2767b.png)

```c
int __cdecl target_function(int a1)
{
  int v3; // [esp+4h] [ebp-8h]

  v3 = a1 & 3;
  if ( !(a1 & 3) )
    return (a1 ^ 2) * (a1 | 0xBAAAD0BF);
  if ( v3 == 1 )
    return (a1 + 3) * (a1 & 0xBAAAD0BF);
  if ( v3 == 2 )
    return (a1 | 4) * (a1 ^ 0xBAAAD0BF);
  return (a1 & 5) * (a1 - 1163210561);
}
```

## ③混淆之后
将混淆之后的示例文件载入IDA中:

### main函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589706732822-94542f00-b6df-4aa9-be4d-398885c6b845.png)

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  int v3; // eax
  int *v4; // edx
  int result; // eax
  int v6; // eax
  int *v7; // edx
  int v8; // [esp-10h] [ebp-28h]
  int v9; // [esp-Ch] [ebp-24h]
  int v10; // [esp+0h] [ebp-18h]
  int *v11; // [esp+4h] [ebp-14h]
  int v12; // [esp+8h] [ebp-10h]
  int *v13; // [esp+Ch] [ebp-Ch]

  if ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 )
    goto LABEL_3;
  while ( 1 )
  {
    v13 = &v8;
    v3 = target_function(74565);
    v4 = v13;
    *v13 = v3;
    v9 = *v4;
    result = printf("result: 0x%x\n", v9);
    v12 = result;
    if ( y < 10 || (((_BYTE)x - 1) * (_BYTE)x & 1) == 0 )
      break;
LABEL_3:
    v11 = &v8;
    v6 = target_function(74565);
    v7 = v11;
    *v11 = v6;
    v9 = *v7;
    v10 = printf("result: 0x%x\n", v9);
  }
  return result;
}
```

### target_function函数
![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589706782774-6cd97609-5855-4588-a5a8-61a2dc7b95f3.png)

```c
int __cdecl target_function(int a1)
{
  bool v1; // bl
  int v3; // [esp+0h] [ebp-28h]
  bool v4; // [esp+6h] [ebp-22h]
  bool v5; // [esp+7h] [ebp-21h]
  int *v6; // [esp+8h] [ebp-20h]
  int *v7; // [esp+Ch] [ebp-1Ch]
  bool v8; // [esp+13h] [ebp-15h]
  int *v9; // [esp+14h] [ebp-14h]
  int v10; // [esp+18h] [ebp-10h]

  v10 = a1;
  if ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 )
    goto LABEL_23;
  while ( 1 )
  {
    v3 = v10;
    *(&v3 - 4) = v10 & 3;
    *(&v3 - 4) = 0;
    v1 = *(&v3 - 4) == 0;
    v9 = &v3;
    v8 = v1;
    v7 = &v3 - 4;
    v6 = &v3 - 4;
    if ( y < 10 || (((_BYTE)x - 1) * (_BYTE)x & 1) == 0 )
      break;
LABEL_23:
    v3 = v10;
    *(&v3 - 4) = v10 & 3;
    *(&v3 - 4) = 0;
  }
  if ( v8 )
  {
    if ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 )
      goto LABEL_24;
    while ( 1 )
    {
      *v6 = (*v9 ^ 2) * (*v9 | 0xBAAAD0BF);
      if ( y < 10 || (((_BYTE)x - 1) * (_BYTE)x & 1) == 0 )
        break;
LABEL_24:
      *v6 = (*v9 ^ 2) * (*v9 | 0xBAAAD0BF);
    }
  }
  else
  {
    do
      v5 = *v7 == 1;
    while ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 );
    if ( v5 )
    {
      if ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 )
        goto LABEL_26;
      while ( 1 )
      {
        *v6 = (*v9 + 3) * (*v9 & 0xBAAAD0BF);
        if ( y < 10 || (((_BYTE)x - 1) * (_BYTE)x & 1) == 0 )
          break;
LABEL_26:
        *v6 = (*v9 + 3) * (*v9 & 0xBAAAD0BF);
      }
    }
    else
    {
      do
        v4 = *v7 == 2;
      while ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 );
      if ( v4 )
      {
        if ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 )
          goto LABEL_28;
        while ( 1 )
        {
          *v6 = (*v9 | 4) * (*v9 ^ 0xBAAAD0BF);
          if ( y < 10 || (((_BYTE)x - 1) * (_BYTE)x & 1) == 0 )
            break;
LABEL_28:
          *v6 = (*v9 | 4) * (*v9 ^ 0xBAAAD0BF);
        }
      }
      else
      {
        if ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 )
          goto LABEL_29;
        while ( 1 )
        {
          *v6 = (*v9 & 5) * (*v9 - 1163210561);
          if ( y < 10 || (((_BYTE)x - 1) * (_BYTE)x & 1) == 0 )
            break;
LABEL_29:
          *v6 = (*v9 & 5) * (*v9 - 1163210561);
        }
      }
      while ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 )
        ;
    }
    while ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 )
      ;
  }
  do
    v3 = *v6;
  while ( y >= 10 && (((_BYTE)x - 1) * (_BYTE)x & 1) != 0 );
  return v3;
}
```

## ④去除混淆
### main函数
开始进行反混淆,首先针对main函数:

**(针对文件:target_x86_bogus)**

```bash
(angr) ubuntu@ubuntu:~/Desktop/ollvm/bogus_control_flow$ python3 debogus.py -f target_x86_bogus --addr 0x08048AB0
*******************symbolic execution*********************
WARNING | 2020-05-17 02:18:42,423 | angr.engines.successors | Exit state has over 256 possible solutions. Likely unconstrained; skipping. <BV32 mem_7ffefffc_12_32{UNINITIALIZED}>
executed blocks:  ['0x9000000', '0x8048686', '0x8048991', '0x8048592', '0x8048914', '0x8048b18', '0x80484ab', '0x804862c', '0x804842e', '0x8048ab0', '0x80482b0', '0x80484b6', '0x8048b37', '0x8048950', '0x8048955', '0x8048556', '0x80489d8', '0x80488d8', '0x80483e0', '0x80485e0', '0x80485f0', '0x8048af4', '0x8048b7c']
************************patch******************************
Successful! The recovered file: target_x86_bogus_recovered
(angr) ubuntu@ubuntu:~/Desktop/ollvm/bogus_control_flow$ 
```

将生成的文件重命名为"target_x86_bogus_recovered_main",载入IDA:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589707256926-70f658ce-1d69-4771-93e6-215489eaf3d9.png)

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  int v3; // eax
  int *v4; // edx
  int v6; // [esp+0h] [ebp-18h]
  int *v7; // [esp+Ch] [ebp-Ch]

  *(&v6 - 4) = 74565;
  v6 = *(&v6 - 4);
  v7 = &v6 - 4;
  v3 = target_function(v6);
  v4 = v7;
  *v7 = v3;
  return printf("result: 0x%x\n", *v4);
}
```

### target_function函数
接下来处理target_function函数:

**(针对文件:target_x86_bogus)**

```bash
(angr) ubuntu@ubuntu:~/Desktop/ollvm/bogus_control_flow$ python3 debogus.py -f target_x86_bogus --addr 0x80483e0
*******************symbolic execution*********************
WARNING | 2020-05-17 02:30:40,194 | angr.engines.successors | Exit state has over 256 possible solutions. Likely unconstrained; skipping. <BV32 mem_7ffefffc_12_32{UNINITIALIZED}>
WARNING | 2020-05-17 02:30:40,541 | angr.engines.successors | Exit state has over 256 possible solutions. Likely unconstrained; skipping. <BV32 mem_7ffefffc_13_32{UNINITIALIZED}>
WARNING | 2020-05-17 02:30:40,834 | angr.engines.successors | Exit state has over 256 possible solutions. Likely unconstrained; skipping. <BV32 mem_7ffefffc_14_32{UNINITIALIZED}>
WARNING | 2020-05-17 02:30:41,023 | angr.engines.successors | Exit state has over 256 possible solutions. Likely unconstrained; skipping. <BV32 mem_7ffefffc_15_32{UNINITIALIZED}>
executed blocks:  ['0x8048686', '0x804868b', '0x8048991', '0x8048592', '0x8048914', '0x8048715', '0x8048897', '0x8048720', '0x8048725', '0x80484ab', '0x804862c', '0x804842e', '0x80484b6', '0x80484bb', '0x80487bb', '0x80487c0', '0x80486c7', '0x8048950', '0x8048551', '0x80488d3', '0x8048955', '0x8048556', '0x8048856', '0x80489d8', '0x80488d8', '0x804885b', '0x80483e0', '0x80485e0', '0x8048761', '0x80485eb', '0x80485f0', '0x80484f7', '0x80487fc']
************************patch******************************
Successful! The recovered file: target_x86_bogus_recovered
(angr) ubuntu@ubuntu:~/Desktop/ollvm/bogus_control_flow$ 
```

将处理后的文件重命名为:target_x86_bogus_recovered_target_function

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1589708045459-30390e50-282d-4c42-8922-db823884b444.png)

```c
unsigned int __cdecl target_function(int a1)
{
  bool v1; // bl
  int v3; // [esp+0h] [ebp-28h]
  bool v4; // [esp+6h] [ebp-22h]
  bool v5; // [esp+7h] [ebp-21h]
  int *v6; // [esp+8h] [ebp-20h]
  int *v7; // [esp+Ch] [ebp-1Ch]
  bool v8; // [esp+13h] [ebp-15h]
  int *v9; // [esp+14h] [ebp-14h]
  int v10; // [esp+18h] [ebp-10h]

  v10 = a1;
  *(&v3 - 4) = a1;
  *(&v3 - 4) &= 3u;
  *(&v3 - 4) = 0;
  v1 = *(&v3 - 4) == 0;
  v9 = &v3 - 4;
  v8 = v1;
  v7 = &v3 - 4;
  v6 = &v3 - 4;
  if ( v1 )
    return (*v9 ^ 2) * (*v9 | 0xBAAAD0BF);
  v5 = *v7 == 1;
  if ( v5 )
    return (*v9 + 3) * (*v9 & 0xBAAAD0BF);
  v4 = *v7 == 2;
  if ( v4 )
    *v6 = (*v9 | 4) * (*v9 ^ 0xBAAAD0BF);
  else
    *v6 = (*v9 & 5) * (*v9 - 1163210561);
  return *v6;
}
```

# 三<font style="color:#333333;">、</font>参考文档
[https://www.freebuf.com/articles/terminal/130142.html](https://www.freebuf.com/articles/terminal/130142.html)

[https://github.com/cq674350529/deflat](https://github.com/cq674350529/deflat)

PS:(我也不知道在哪搞的)

[基于符号执行的反混淆方法研究.pdf](https://www.yuque.com/attachments/yuque/0/2020/pdf/574026/1589705833722-8afdd136-0535-4e6f-a1ef-987bc254d630.pdf)

