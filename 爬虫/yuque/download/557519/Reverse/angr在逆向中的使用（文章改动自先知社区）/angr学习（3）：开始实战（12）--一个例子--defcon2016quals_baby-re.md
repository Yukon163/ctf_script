例题下载地址：[https://github.com/angr/angr-doc/tree/master/examples/defcon2016quals_baby-re](https://github.com/angr/angr-doc/tree/master/examples/defcon2016quals_baby-re)

这道题作为例子可能会更好一点。

这题其实不用hook也能顺利的解出，只是我们需要对结果进行处理一下，才能得到我们想要的flag。

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592815889409-ff4f09b7-c483-484c-8d76-ff5815c7ef52.png)

首先将文件下载下来，载入到IDA中

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  unsigned int v4; // [rsp+0h] [rbp-60h]
  unsigned int v5; // [rsp+4h] [rbp-5Ch]
  unsigned int v6; // [rsp+8h] [rbp-58h]
  unsigned int v7; // [rsp+Ch] [rbp-54h]
  unsigned int v8; // [rsp+10h] [rbp-50h]
  unsigned int v9; // [rsp+14h] [rbp-4Ch]
  unsigned int v10; // [rsp+18h] [rbp-48h]
  unsigned int v11; // [rsp+1Ch] [rbp-44h]
  unsigned int v12; // [rsp+20h] [rbp-40h]
  unsigned int v13; // [rsp+24h] [rbp-3Ch]
  unsigned int v14; // [rsp+28h] [rbp-38h]
  unsigned int v15; // [rsp+2Ch] [rbp-34h]
  unsigned int v16; // [rsp+30h] [rbp-30h]
  unsigned __int64 v17; // [rsp+38h] [rbp-28h]

  v17 = __readfsqword(0x28u);
  printf("Var[0]: ", argv, envp);
  fflush(_bss_start);
  __isoc99_scanf("%d", &v4);
  printf("Var[1]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v5);
  printf("Var[2]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v6);
  printf("Var[3]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v7);
  printf("Var[4]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v8);
  printf("Var[5]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v9);
  printf("Var[6]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v10);
  printf("Var[7]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v11);
  printf("Var[8]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v12);
  printf("Var[9]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v13);
  printf("Var[10]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v14);
  printf("Var[11]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v15);
  printf("Var[12]: ");
  fflush(_bss_start);
  __isoc99_scanf("%d", &v16);
  if ( (unsigned __int8)CheckSolution(&v4) )
    printf("The flag is: %c%c%c%c%c%c%c%c%c%c%c%c%c\n", v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16);
  else
    puts("Wrong");
  return 0;
}
```

在这里可以看到，和之前见到过的都不一样，这里多次调用了__isoc99_scanf函数写入到stream（之后会清空缓冲区），然后调用CheckSolution函数进行验证。

<font style="color:#333333;">其实之前我们遇到过类似的题目，不过那时我们采取的方法是：跳过输入部分，直接对内存进行存储，从而进行输入，这里当然也能这么做，只需对</font>`[rbp+var_60]`<font style="color:#333333;">内存进行操作即可</font>

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592816296712-21ef762c-1a35-44e1-933d-4f2fbb05e539.png)

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1592816365961-1903c389-e59f-4066-bb2a-b20ac58211a1.png)

```python
import angr
import claripy

# 最简单的方法，不过需要对结果进行变化
def main():
    proj = angr.Project('./baby-re', auto_load_libs=False)
    state = proj.factory.entry_state(add_options={angr.options.LAZY_SOLVES})
    sm = proj.factory.simulation_manager(state)
    sm.explore(find=0x4028E9, avoid=0x402941)
    found=sm.found[0]
    print(found.posix.dumps(0))

# 跳过程序自身的输入，通过内存控制输入
def main2():
    proj = angr.Project('./baby-re', auto_load_libs=False)
    flag_chars = [claripy.BVS('flag_%d' % i, 32) for i in range(13)]

    state = proj.factory.blank_state(addr=0x4028E0,add_options={angr.options.LAZY_SOLVES})
    for i in range(13):
        state.memory.store(state.regs.rbp-0x60+i*4,flag_chars[i])
    state.regs.rdi = state.regs.rbp-0x60
    sm = proj.factory.simulation_manager(state)
    sm.explore(find=0x4028E9, avoid=0x402941)
    found=sm.found[0]
    for i in range(0,13):
    	print(found.solver.eval(flag_chars[i],cast_to=bytes))
    
if __name__ == '__main__':
    main()
    main2()
```

日志信息如下

```bash
(angr) ubuntu@ubuntu:~/Desktop/angr$ python 1.py
b'0000000077000000009700000001160000000104000000003200000001050000000115000000003200000001040000000097000000011400000001000000000033'
WARNING | 2020-06-22 02:20:03,550 | angr.state_plugins.symbolic_memory | The program is accessing memory or registers with an unspecified value. This could indicate unwanted behavior.
WARNING | 2020-06-22 02:20:03,550 | angr.state_plugins.symbolic_memory | angr will cope with this by generating an unconstrained symbolic variable and continuing. You can resolve this by:
WARNING | 2020-06-22 02:20:03,550 | angr.state_plugins.symbolic_memory | 1) setting a value to the initial state
WARNING | 2020-06-22 02:20:03,550 | angr.state_plugins.symbolic_memory | 2) adding the state option ZERO_FILL_UNCONSTRAINED_{MEMORY,REGISTERS}, to make unknown regions hold null
WARNING | 2020-06-22 02:20:03,550 | angr.state_plugins.symbolic_memory | 3) adding the state option SYMBOL_FILL_UNCONSTRAINED_{MEMORY_REGISTERS}, to suppress these messages.
WARNING | 2020-06-22 02:20:03,550 | angr.state_plugins.symbolic_memory | Filling register rbp with 8 unconstrained bytes referenced from 0x4028e0 (main+0x2f9 in baby-re (0x4028e0))
b'M\x00\x00\x00'
b'a\x00\x00\x00'
b't\x00\x00\x00'
b'h\x00\x00\x00'
b' \x00\x00\x00'
b'i\x00\x00\x00'
b's\x00\x00\x00'
b' \x00\x00\x00'
b'h\x00\x00\x00'
b'a\x00\x00\x00'
b'r\x00\x00\x00'
b'd\x00\x00\x00'
b'!\x00\x00\x00'
```

当然这里都不重要，重要的是我们要使用hook的方法来解题：

我们可以通过这样的方式进行Hook

`proj.hook_symbol('__isoc99_scanf', my_scanf(), replace=True)`

我们用自己的`my_scanf()`来代替`__isoc99_scanf`，我们在保持scanf功能不变的情况下，将我们的符号变量存储进去。

```python
class my_scanf(angr.SimProcedure):
        def run(self, fmt, ptr): # pylint: disable=arguments-differ,unused-argument
            self.state.mem[ptr].dword = flag_chars[self.state.globals['scanf_count']]
            self.state.globals['scanf_count'] += 1
```

这样程序每次调用`scanf`时，其实就是在执行`my_scanf，`就会将`flag_chars[i]`存储到`self.state.mem[ptr]`当中，这其中`ptr`参数，其实就是本身`scanf`函数传递进来的`rdi`也就是`[rbp+var_60]+i*4`,为了控制下标，我们设置了一个全局符号变量`scanf_count。`

如此一来，只要angr执行到我们想要到达的分支，那么我们就可以通过`solver.eval()`的方式将其打印出来。



代码如下：

```python
import angr
import claripy
def main():
    proj = angr.Project('./baby-re', auto_load_libs=False)
    # let's provide the exact variables received through the scanf so we don't have to worry about parsing stdin into a bunch of ints.
    flag_chars = [claripy.BVS('flag_%d' % i, 32) for i in range(13)]
    class my_scanf(angr.SimProcedure):
        def run(self, fmt, ptr): # pylint: disable=arguments-differ,unused-argument
            self.state.mem[ptr].dword = flag_chars[self.state.globals['scanf_count']]
            self.state.globals['scanf_count'] += 1
    proj.hook_symbol('__isoc99_scanf', my_scanf(), replace=True)
    sm = proj.factory.simulation_manager()
    sm.one_active.options.add(angr.options.LAZY_SOLVES)
    sm.one_active.globals['scanf_count'] = 0
    # search for just before the printf("%c%c...")
    # If we get to 0x402941, "Wrong" is going to be printed out, so definitely avoid that.
    sm.explore(find=0x4028E9, avoid=0x402941)
    # evaluate each of the flag chars against the constraints on the found state to construct the flag
    flag = ''.join(chr(sm.one_found.solver.eval(c)) for c in flag_chars)
    return flag
def test():
    assert main() == 'Math is hard!'
if __name__ == '__main__':
    print(main())
```

