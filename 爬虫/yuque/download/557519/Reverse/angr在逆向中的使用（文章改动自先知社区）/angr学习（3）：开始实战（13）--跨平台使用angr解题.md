# 前言
> 我们时常会遇到各种平台下的程序，有时我们为了搭一个动态调试的环境需要耗费不少的时间，更有甚者无功而返，那么这时不妨用angr试试，毕竟多一分尝试，多一分希望。
>

## 如何跨平台使用angr解题
通常来说，我们会在linux下安装angr框架，那么如果遇到不是linux的程序该怎么办呢？程序无法运行还能使用angr解决么！答案当然是可以。**<font style="color:#F5222D;">因为angr是符号执行框架，不是真正的在执行程序。</font>**我们只需要进行正确的条件设置就可以了。

### ARM程序
这里以 `android_arm_license_validation`为例

[https://github.com/angr/angr-doc/tree/master/examples/android_arm_license_validation](https://github.com/angr/angr-doc/tree/master/examples/android_arm_license_validation)

IDA载入，来到main函数：

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  const char **v4; // [sp+8h] [bp-24h]
  int v5; // [sp+14h] [bp-18h]
  char v6; // [sp+18h] [bp-14h]

  v4 = argv;
  if ( argc != 2 )
    sub_16A8();
  if ( strlen(argv[1]) != 16 )
    sub_16CC();
  puts("Entering base32_decode");
  sub_1340(0, v4[1], 16, &v6, &v5);
  printf("Outlen = %d\n", v5);
  puts("Entering check_license");
  sub_1760(&v6);
  return 0;
}
```

最关键的是设置合理的初始状态，从IDA的分析来看，最后的比较部分在`sub_1760`函数，

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593224943575-37f89e62-cf0d-4a91-9618-cbb1170d2aa4.png)

因此我们以此作为初始状态，同时看到该函数有一个`v6`参数，经过分析，可以知道该参数经过加密变换，最终用来校验的字符串，也就是说最后的校验过程我们可以不用了解，只需要使用angr将其爆破出来即可。

我们需要设置一个空的状态

`state = b.factory.blank_state(addr=0x401760)`

```bash
ubuntu@ubuntu:~/Desktop/angr$ export WORKON_HOME=$HOME/Python-workhome
ubuntu@ubuntu:~/Desktop/angr$ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
ubuntu@ubuntu:~/Desktop/angr$ workon angr
(angr) ubuntu@ubuntu:~/Desktop/angr$ ./validate
bash: ./validate: cannot execute binary file: Exec format error
(angr) ubuntu@ubuntu:~/Desktop/angr$ checksec --file=validate
RELRO           STACK CANARY      NX            PIE             RPATH      RUNPATH	Symbols		FORTIFY	Fortified	Fortifiable  FILE
Full RELRO      No canary found   NX enabled    PIE enabled     No RPATH   No RUNPATH   No Symbols      No	0		1	validate
(angr) ubuntu@ubuntu:~/Desktop/angr$ 
```

**<font style="color:#F5222D;">注意：此程序开启了PIE，加载到内存之后main函数的地址为</font>**`0x401760`

**<font style="color:#F5222D;">而后设置需要传入的参数，选取任意一个地址，用来存放变量。</font>**

```python
>>> concrete_addr = 0xfff00000
>>> code = claripy.BVS('code', 10*8)
>>> state.memory.store(concrete_addr, code, endness='Iend_BE')
```

> concrete：具体的（形容词）
>
> **<font style="color:#F5222D;">注意：此程序输入的地方并不在main函数，我们跳过了输入，所以要选取任意地址来存放输入的参数</font>**
>



![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321455-dea4deb1-915a-42b4-95d1-4bfd7b1510f6.png)

**<font style="color:#F5222D;">注意</font>**`**<font style="color:#F5222D;">ARM</font>**`**<font style="color:#F5222D;">程序是大端对齐。</font>**

为了正确的传入参数，我们需要了解`arm`程序传参方式。

---

`https://blog.csdn.net/celerychen2009/article/details/4761514  
`

`arm`程序传参方式：

**<font style="color:#F5222D;">r0,r1,r2,r3,在调用函数时，用来存放前4个函数参数和返回值，r4-r11,r14,在调用函数时必须保存这些寄存器到堆栈当中。</font>**如果函数的参数多于4个，则多余参数存放在堆栈当中，即sp,sp+4,sp+8,…依次类推。如果函数并没有用到那么多的寄存器，则没有必要把所有的寄存器入栈。如果函数要调用子函数，则r0,r1,r2,r3,r12,r14这些寄存器里面值将被改变，必须小心处理这些寄存器，一种可行的方法是，修改被调用子函数的入栈出栈代码

---

因此我们设置`r0`为输入的地址（也就是保存这个参数，因为有state.memory.store(concrete_addr, code, endness='Iend_BE'，将变量已经存入了concrete_addr)）：`state.regs.r0 = concrete_addr`



完整代码如下：

```python
#!/usr/bin/python

'''
Quick-and-dirty solution for the (un-obfuscated) Android License Check crackme from the Obfuscation Metrics Project.
The full how-to can be found in the 'Android' section of the OWASP Mobile Security Testing Guide:
https://github.com/OWASP/owasp-mstg/blob/master/Document/0x06a-Reverse-Engineering-and-Tampering-Android.md
'''

import angr
import claripy
import base64

def main():
    load_options = {}

    # Android NDK library path:
    # load_options['ld_path'] = ['/Users/berndt/Tools/android-ndk-r10e/platforms/android-21/arch-arm/usr/lib']

    b = angr.Project("./validate", load_options = load_options)

    # The key validation function starts at 0x401760, so that's where we create the initial state.
    # This speeds things up a lot because we're bypassing the Base32-encoder.

    state = b.factory.blank_state(addr=0x401760)

    concrete_addr = 0xffe00000
    code = claripy.BVS('code', 10*8)
    state.memory.store(concrete_addr, code, endness='Iend_BE')
    state.regs.r0 = concrete_addr

    sm = b.factory.simulation_manager(state)

    # 0x401840 = Product activation passed
    # 0x401854 = Incorrect serial

    sm.explore(find=0x401840, avoid=0x401854)
    found = sm.found[0]

    # Get the solution string from *(R11 - 0x20).

    solution = found.solver.eval(code, cast_to=bytes)
	print(solution)
    print(base64.b32encode(solution))
    

if __name__ == '__main__':
    main()
```

 print(base64.b32encode(solution))是因为程序对输入进行了base32加密

## windows dll
这里以`mma_howtouse`为例

[https://github.com/angr/angr-doc/tree/master/examples/mma_howtouse](https://github.com/angr/angr-doc/tree/master/examples/mma_howtouse)

程序是windows的dll，如果采用正常的方式解题，那么搭建动态调试的环境势必要花费一番功夫。

IDA载入，**<font style="color:#F5222D;">首先我们应该注意的是</font>**`**<font style="color:#F5222D;">dll</font>**`**<font style="color:#F5222D;">程序的基址是</font>**`**<font style="color:#F5222D;">0x10000000</font>**`**<font style="color:#F5222D;">，而不是</font>**`**<font style="color:#F5222D;">0x400000</font>**`**<font style="color:#F5222D;">。</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593227307861-96dd204d-a255-4960-b4d1-9461e842cf80.png)

**<font style="color:#F5222D;">通过导出表，我们可以定位到</font>**`**<font style="color:#F5222D;">fnhowtouse</font>**`**<font style="color:#F5222D;">函数，进行了</font>**`**<font style="color:#F5222D;">handler</font>**`**<font style="color:#F5222D;">的绑定，然后通过</font>**`**<font style="color:#F5222D;">(*(&v2 + a1))();</font>**`**<font style="color:#F5222D;">进行函数调用。</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593227352247-2886cc2f-35b7-492c-9975-39dc17e78252.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593227536066-cc0ef0bb-ad7d-4aef-91ea-5b45a78d52ec.png)

**<font style="color:#F5222D;">为了调用</font>**`**<font style="color:#F5222D;">fnhowtouse</font>**`**<font style="color:#F5222D;">函数,可以使用</font>**`**<font style="color:#F5222D;">callable</font>**`**<font style="color:#F5222D;">方法</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321479-022ce93f-f94c-477b-9c3c-605dfeb5c92d.png)

首先加载`howtouse.dll`

```plain
p = angr.Project('howtouse.dll', load_options={'main_opts': {'base_addr': 0x10000000}})
howtouse = p.factory.callable(0x10001130)
```

**<font style="color:#F5222D;">通过</font>**`**<font style="color:#F5222D;">callable</font>**`**<font style="color:#F5222D;">方法将</font>**`**<font style="color:#F5222D;">fnhowtouse</font>**`**<font style="color:#F5222D;">转化为python可以调用的函数</font>**

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321480-f9d209d1-632e-4cce-930c-6afcd414b8b2.png)

然后我们便可以通过`howtouse(i)`进行函数调用，而无需依赖环境。通过题目，我们可以知道`howtouse(i)`结果就是flag，因此我们可以通过

```plain
claripy.backends.concrete.convert(howtouse(i))
```

将结果转换为`BVV`类型，并通过`.value`将值取出。

因此代码可以如下进行组织：

```plain
getch = lambda i: chr(claripy.backends.concrete.convert(howtouse(i)).value)
    # Let's call this 45 times, and that's the result!
    return ''.join(getch(i) for i in range(45))
```

完整代码如下：

```python
#!/usr/bin/env python

#
# This binary, from the MMA CTF, was a simple reversing challenge. THe biggest
# challenge was actually *running* this library in Windows. Luckily, with angr,
# we can avoid having to do this!
#
# The approach here is to use angr as a concrete execution engine to call the
# `howtouse` function 45 times, as the array of function pointers in that
# function has 45 entries. The result turned out to be the flag.
#

import angr
import claripy

def main():
    # Load the binary. Base addresses are weird when loading binaries directly, so
    # we specify it explicitly.
    p = angr.Project('howtouse.dll', load_options={'main_opts': {'base_addr': 0x10000000}})

    # A "Callable" is angr's FFI-equivalent. It allows you to call binary functions
    # from Python. Here, we use it to call the `howtouse` function.
    howtouse = p.factory.callable(0x10001130)

    # In this binary, the result is a concrete char, so we don't need a symbolic
    # state or a solver to get its value.
    getch = lambda i: chr(claripy.backends.concrete.convert(howtouse(i)).value)

    # Let's call this 45 times, and that's the result!
    return ''.join(getch(i) for i in range(45))

def test():
    assert main() == 'MMA{fc7d90ca001fc8712497d88d9ee7efa9e9b32ed8}'

if __name__ == '__main__':
    print(main())


```

## windows驱动
这里以`flareon2015_10`为例

程序是windows驱动，2.5M还是蛮大的，IDA载入分析,来到sub_29C1A0。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321465-19f32ea0-9264-4c25-bff0-972f1662c93d.png)

What！这次又是个什么鬼图形，感觉出题人都要玩出花了。当然啦，angr最喜欢解决这种线性的题目了。

首先程序的入口。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593228483086-4b51f359-d3ed-42b0-b8d5-8528a8b2c6d1.png)

可以知道`sub_29cd20`是有用的函数

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321373-2b525e22-578e-4423-8308-b7fdf1f4bea6.png)

好吧。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321501-f762cd18-fb51-41ac-92bf-e35e0ed94e2d.png)

挨个查看一下，发现一个可疑的`case`

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321709-63ca911d-1676-48f1-b7a2-cda8d4084e21.png)

话说这程序导致我的IDA都有点不正常了。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321613-252e2c0e-bb86-4c93-af7d-18b591c1d1fa.png)

接下来查看`sub_2D2E0`函数

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321656-cc938c38-d93b-4d2e-8e06-450ea6580626.png)

真漂亮，还好不是在比赛的时候遇到这种题目。。

我仔细盘了一下代码。还真有趣。

看到`sub_13590`函数

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321753-7b17ce89-7962-4dbd-bec3-026d28df489f.png)

一百多行代码，F5之后就两行。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321742-a94c3df1-df76-47f2-bcc3-20aec1824fc3.png)

`sub_2D2E0`函数的前半部分都在为`0x29F210`地址的数据赋值

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321660-c4794c52-dd60-45b2-8f52-a403e6c4770d.png)

只有在最后几行，调用了`sub_110F0`函数，并传入了`byte_29F210`和`edx`，`ecx`作为参数

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321636-27203481-bbfb-4abe-896b-78e3f8611c15.png)

查一下`edx`对应`[ebp+var_3C]`的交叉引用，可以知道长度为40

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321656-8240e161-93e1-425e-b362-54636f597078.png)

查一下`edx`对应`[ebp+var_30]`的交叉引用可以知道`key`

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321608-a524366e-63fb-4f11-b923-5b3a9185da28.png)

具体查看`sub_110F0`函数，这回比较正常

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321641-9fb95f2b-672e-4adc-93c9-048f3c828ea1.png)

查看`sub_11010`函数

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1593223321747-5430c5fc-5dbb-455b-8cf9-eba800f1c686.png)

很明显是一个不太标准的`Tea`解密函数。

在查`sub_110F0`的交叉引用时，发现还有其他几个地方引用了该函数，不过我仔细查看了一下，这三个地方引用`sub_110F0`函数都是对相同的数据进行解密，只是数据存放的位置不同罢了。所以也就先不去关心了。

所以把数据`dump`下来，解密就可以了。

代码如下：

```plain
void decrypt (uint32_t* v, uint32_t* k) {
    uint32_t v0=v[0], v1=v[1], sum=0xC6EF3720, i;  /* set up */
    uint32_t delta=0x61C88647;          /* a key schedule constant */
    uint32_t k0=k[0], k1=k[1], k2=k[2], k3=k[3];   /* cache key */
    for (i=0; i<32; i++) {                         /* basic cycle start */
        v1 -= ((v0<<4) + k2) ^ (v0 + sum) ^ ((v0>>5) + k3);
        v0 -= ((v1<<4) + k0) ^ (v1 + sum) ^ ((v1>>5) + k1);
        sum += delta;
    }                                              /* end cycle */
    v[0]=v0; v[1]=v1;
}
int main()
{
    uint32_t k[4]={858927408,926299444,1111570744,1178944579};
    uint32_t v0[] = {0xfadc7f56,0xc49927aa};
    uint32_t v1[] = {0x92cf7c6c,0x1a476161};
    uint32_t v2[] = {0xfd63b919,0x20b6f20c};
    uint32_t v3[] = {0xfd5c2dc0,0x965471d9};
    uint32_t v4[] = {0xfff7434f,0x315d4cbb};
    // v为要加密的数据是两个32位无符号整数
    // k为加密解密密钥，为4个32位无符号整数，即密钥长度为128位
    setbuf(stdin,0);
    setbuf(stdout,0);
    setbuf(stderr,0);
    decrypt(v0,k);
    decrypt(v1,k);
    decrypt(v2,k);
    decrypt(v3,k);
    decrypt(v4,k);
    char *flag;
    sprintf(flag,"%x%x%x%x%x%x%x%x%x%x",v0[0],v0[1],v1[0],v1[1],v2[0],v2[1],v3[0],v3[1],v4[0],v4[1]);
    printf("%s",flag);
    return 0;
}
```

最后的结果需要转换一下。

再让我们看看如何使用angr的hook来完成解密工作。

大致思路，就是在程序调用解密函数前，将对应的数据存放到相应的位置即可。

因此我们的Hook函数可以这么写

```plain
def before_tea_decrypt(state):
    # Here we want to set the value of the byte array starting from 0x29f210
    # I got those bytes by using cross-reference in IDA
    all_bytes = bytes([0x56, 0x7f, 0xdc, 0xfa, 0xaa, 0x27, 0x99, 0xc4, 0x6c, 0x7c,
             0xfc, 0x92, 0x61, 0x61, 0x47, 0x1a, 0x19, 0xb9, 0x63, 0xfd,
             0xc, 0xf2, 0xb6, 0x20, 0xc0, 0x2d, 0x5c, 0xfd, 0xd9, 0x71,
             0x54, 0x96, 0x4f, 0x43, 0xf7, 0xff, 0xbb, 0x4c, 0x5d, 0x31])
    state.memory.store(ARRAY_ADDRESS, all_bytes)
```

这时hook的长度应该为0

`p.hook(0xadc31, before_tea_decrypt, length=0)`,有点类似于插桩

我们不会运行该程序，而是选取有用的部分运行。

我们只需要运行`2D2E0`函数即可。

这时需要用到`callable`方法：

它是将程序的二进制函数，变成像python本地的函数一样调用。

如下初始化

```plain
proc_big_68 = p.factory.callable(0x2D2E0, cc=p.factory.cc(func_ty=prototype), toc=None, concrete_only=True)
```

其中`prototype`是函数原型的申明

可以像这样声明：

`prototype = SimTypeFunction((SimTypeInt(False),), SimTypeInt(False))`

因此完整的`callable`调用如下

```plain
# Declare the prototype of the target function
    prototype = SimTypeFunction((SimTypeInt(False),), SimTypeInt(False))
    # Initialize the function instance
    proc_big_68 = p.factory.callable(BIG_PROC, cc=p.factory.cc(func_ty=prototype), toc=None, concrete_only=True)
    # Call the function and get the final state
    proc_big_68.perform_call(0)
    state = proc_big_68.result_state
```

最后我们可以通过`state.solver.eval(state.memory.load(ARRAY_ADDRESS, 40), cast_to=bytes)`获取flag

> 如果学会了，是不是非常简单呢
>

完整代码：

```python
import logging

import angr
from angr.sim_type import SimTypeFunction, SimTypeInt
from angr.procedures.stubs.UserHook import UserHook

# This is literally how I solved this challenge during the game. Now I know it's easier
# to just call tea_decrypt with those bytes (and the correct key), but I don't want to
# change this script anymore.

# You are strongly recommended to use pypy to run this script in order to get a better
# performance.

# I would like to thank my girlfriend for allowing me to work on FlareOn challenges
# during several nights we spent together.

ARRAY_ADDRESS = 0x29f210
BIG_PROC = 0x2d2e0

def before_tea_decrypt(state):
    # Here we want to set the value of the byte array starting from 0x29f210
    # I got those bytes by using cross-reference in IDA
    all_bytes = bytes([0x56, 0x7f, 0xdc, 0xfa, 0xaa, 0x27, 0x99, 0xc4, 0x6c, 0x7c,
             0xfc, 0x92, 0x61, 0x61, 0x47, 0x1a, 0x19, 0xb9, 0x63, 0xfd,
             0xc, 0xf2, 0xb6, 0x20, 0xc0, 0x2d, 0x5c, 0xfd, 0xd9, 0x71,
             0x54, 0x96, 0x4f, 0x43, 0xf7, 0xff, 0xbb, 0x4c, 0x5d, 0x31])
    state.memory.store(ARRAY_ADDRESS, all_bytes)

def main():
    p = angr.Project('challenge-7.sys', load_options={'auto_load_libs': False})

    # Set a zero-length hook, so our function got executed before calling the
    # function tea_decrypt(0x100f0), and then we can keep executing the original
    # code. Thanks to this awesome design by @rhelmot!
    p.hook(0xadc31, before_tea_decrypt, length=0)

    # Declare the prototype of the target function
    prototype = SimTypeFunction((SimTypeInt(False),), SimTypeInt(False))
    # Initialize the function instance
    proc_big_68 = p.factory.callable(BIG_PROC, cc=p.factory.cc(func_ty=prototype), toc=None, concrete_only=True)
    # Call the function and get the final state
    proc_big_68.perform_call(0)
    state = proc_big_68.result_state
    # Load the string from memory
    return state.solver.eval(state.memory.load(ARRAY_ADDRESS, 40), cast_to=bytes).strip(b'\0')

def test():
    assert main() == b"unconditional_conditions@flare-on.com"

if __name__ == "__main__":
    # Turn on logging so we know what's going on...
    # It's up to you to set up a logging handler beforehand
    logging.getLogger('angr.manager').setLevel(logging.DEBUG)
    print(main())
```

# 总结
对于跨平台的程序，最重要的了解该平台调用约定，需要对程序的运行有所了解。

