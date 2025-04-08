## 文件保护
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1613979515261-f2e95315-4444-49fd-b77b-bbf6177c178e.png)

## 解题思路
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1613979565846-21167479-d377-4aac-ad76-3216c7af248b.png)

IDA分析：read时候没有发生溢出，但是由于dest栈空间限制，拼接之后会发生溢出，但是查看栈空间之后无法得到任何有效信息。

## 知识链接
上网搜了一下，发现Linux的命令行是可以单行执行多个命令的：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1613979755261-63b0e390-fc34-467c-8253-5e381775e3d8.png)

或者是

## ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1613979795307-20a81988-6800-45a4-8be8-59800df4b332.png)
因此我们可以使用这个特性来getshell

## exp
![](https://cdn.nlark.com/yuque/0/2021/png/574026/1613980049761-b1923087-2a52-41f1-8ce0-37e47ba59ff3.png)

## flag
flag{e8ef6d27-255a-4421-bb96-24347e235ce3}

