这里以`tumctf2016_zwiebel`作为例子进行说明。

[https://github.com/angr/angr-doc/tree/master/examples/tumctf2016_zwiebel](https://github.com/angr/angr-doc/tree/master/examples/tumctf2016_zwiebel)

首先看官方文档的说明。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592793477496-7c740358-2eb1-47a1-a049-9395c93cf2f7.png)

`**<font style="color:#F5222D;">hook_symbol</font>**`**<font style="color:#F5222D;">函数可以根据所给出的符号名，在二进制文件中找寻对应的地址，并且hook该地址。</font>**

我们使用IDA载入题目，来到main函数的伪代码：

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  void (__fastcall *v3)(void *, void *); // rax
  void (__fastcall *v4)(void *, void *); // r14
  void (__fastcall *v5)(void *, void *); // rdi

  printf("Input key: ", argv, envp);
  fflush(stdout);
  fgets(flag, 144, stdin);
  v3 = (void (__fastcall *)(void *, void *))mmap(0LL, 0x24C8DuLL, 7, 34, -1, 0LL);
  v4 = v3;
  v5 = v3;
  memcpy(v3, &shc, 0x24C8DuLL);
  v4(v5, &shc);
  return 0;
}
```

**<font style="color:#F5222D;">这是一个smc的题目，对于angr来说为了能在符号执行时进行自解密，需要添加support_selfmodifying_code=True参数</font>**

**<font style="color:#F5222D;">  
</font>**![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592794007615-50849baf-1af0-4368-9289-f1f8042f2da1.png)

> 所谓SMC，意思就是动态修改程序，一般用于带壳破解或者程序解码，
>

<font style="color:#333333;">很明显，我们无法使用</font>`sm.explore(find=xxx,avoid=xxx)`<font style="color:#333333;">的方式来使用angr，同时注意到程序中出现了</font>`**<font style="color:#F5222D;">ptrace</font>**`**<font style="color:#F5222D;">想必一定有反调试</font>**<font style="color:#333333;">，让我们通过hook的方法来绕过反调试。</font>

```plain
p.hook_symbol('ptrace', angr.SIM_PROCEDURES['stubs']['ReturnUnconstrained'](return_value=0))
```

**<font style="color:#F5222D;">因为</font>**`**<font style="color:#F5222D;">angr</font>**`**<font style="color:#F5222D;">实现了大量的符号化函数，以此来替代程序中对库函数的外部调用，其中</font>**`**<font style="color:#F5222D;">angr.SIM_PROCEDURES</font>**`**<font style="color:#F5222D;">是</font>**`**<font style="color:#F5222D;">angr</font>**`**<font style="color:#F5222D;">对符号化函数的字典调用，我们可以采用</font>**`**<font style="color:#F5222D;">angr.SIM_PROCEDURES['模块名']['库函数名']()</font>**`**<font style="color:#F5222D;">进行</font>**`**<font style="color:#F5222D;">hook</font>**`

而后便可以通过`simulation_manager`进行执行了。

```plain
state = p.factory.full_init_state(cadd_options=angr.options.unicorn)
sm = p.factory.simulation_manager(state)
```

这里只能采用类似step的方法进行解决，效率很低,例子中提供的代码是这样的。

```python
while sm.active:
        # in order to save memory, we only keep the recent 20 deadended or
        # errored states
        #print(len(sm.active))
        sm.run(n=20)
        if 'deadended' in sm.stashes and sm.deadended:
            sm.stashes['deadended'] = sm.deadended[-20:]
        if sm.errored:
            sm.errored = sm.errored[-20:]
    assert sm.deadended
    flag = sm.deadended[-1].posix.dumps(0).split(b"\n")[0]
    import ipdb; ipdb.set_trace()
    return flag
```

我觉得有点多此一举了，他这段代码的目的就是执行完`sm.run()`此时正确的输入应该保存在最后一个`deadended`节点的`posix.dumps(0)`当中，最后跑了两个小时。

完整脚本如下：

```python
import angr

def main():

    # Uncomment the following two lines if you want to have logging output from
    # SimulationManager
    # import logging
    # logging.getLogger('angr.manager').setLevel(logging.DEBUG)

    p = angr.Project("zwiebel", support_selfmodifying_code=True) 
    # 这非常重要，这个二进制文件会解包它的代码
    
    p.hook_symbol('ptrace', angr.SIM_PROCEDURES['stubs']['ReturnUnconstrained'](return_value=0))

    # unicorn工具支持执行程序，特别是代码解压缩，速度更快
     
    state = p.factory.full_init_state(add_options=angr.options.unicorn)
    sm = p.factory.simulation_manager(state)

    while sm.active:
        # 为了节省内存, 我们只能保存20 deadended or errored states
        #print(len(sm.active))
        sm.run(n=20)
        if 'deadended' in sm.stashes and sm.deadended:
            sm.stashes['deadended'] = sm.deadended[-20:]
        if sm.errored:
            sm.errored = sm.errored[-20:]

    assert sm.deadended
    flag = sm.deadended[-1].posix.dumps(0).split(b"\n")[0]
    import ipdb; ipdb.set_trace()
    return flag

def test():
    flag = main()
    assert flag.startswith(b'hxp{1_h0p3_y0u_d1dnt_p33l_th3_0ni0n_by_h4nd}')

if __name__ == "__main__":
    print(main())

# Here is the output (after 2 hours and 31 minutes on my machine running Pypy):
# 
# ipdb> print(sm)
# <PathGroup with 20 errored, 21 deadended>
# ipdb> print(sm.deadended[-1])
# <Path with 160170 runs (at 0x20001e0)>
# ipdb> print(sm.deadended[-1].state.posix.dumps(0))
# hxp{1_h0p3_y0u_d1dnt_p33l_th3_0ni0n_by_h4nd}
# :)
```



