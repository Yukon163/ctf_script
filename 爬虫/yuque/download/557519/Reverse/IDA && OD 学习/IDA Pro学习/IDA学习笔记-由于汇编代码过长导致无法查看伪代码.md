> 参考资料：[https://www.jianshu.com/p/e5d422a3df23](https://www.jianshu.com/p/e5d422a3df23)
>

Decompilation failure:

F888: too big function

Please refer to the manual to find appropriate actions

![](https://cdn.nlark.com/yuque/0/2020/webp/574026/1588658460533-e5c4c512-712d-4ca9-9183-19c7d7b4b0a8.webp)

## 解决方案
修改配置文件`IDA 7.0\cfg\hexrays.cfg`



```plain
MAX_FUNCSIZE            = 64        // Functions over 64K are not decompiled
// 修改为：
MAX_FUNCSIZE            = 1024        // Functions over 64K are not decompiled
```



