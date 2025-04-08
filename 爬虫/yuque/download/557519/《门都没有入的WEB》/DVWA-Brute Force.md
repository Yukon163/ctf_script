这里选择使用Burp Suite自带的浏览器进行抓包。

# 准备
来到DVWA的`Vulnerability: Brute Force`，在调整DVWA安全等级后，注意cookie中是否存在两个security字段，如果存在请删掉其中一个这样才能使得调整的安全等级起效。

# Low
先查看源码，对源码的详细注释见下：

```php
<?php

if( isset( $_GET[ 'Login' ] ) ) { //检测Login变量是否已设置（这里是由get方式进行传参设置）并且非NULL
    // Get username
    $user = $_GET[ 'username' ];  //获取get的user

    // Get password
    $pass = $_GET[ 'password' ];  //获取get的password 
    $pass = md5( $pass );         //对password进行md5加密

    // Check the database
    $query  = "SELECT * FROM `users` WHERE user = '$user' AND password = '$pass';";  //对数据库进行查询的语句
    $result = mysqli_query($GLOBALS["___mysqli_ston"],  $query ) or die( '<pre>' . ((is_object($GLOBALS["___mysqli_ston"])) ? mysqli_error($GLOBALS["___mysqli_ston"]) : (($___mysqli_res = mysqli_connect_error()) ? $___mysqli_res : false)) . '</pre>' );
	/*
    	可以对result进行展开:
    	$result = 
        mysqli_query($GLOBALS["___mysqli_ston"],  $query)    //mysqli_query数据库查询语句
        	or 
        die( '<pre>' . (								     //die相当于exit + 输出
               (is_object($GLOBALS["___mysqli_ston"]))       
                ? 
                mysqli_error($GLOBALS["___mysqli_ston"])     
                : 
                (($___mysqli_res = mysqli_connect_error()) ? $___mysqli_res : false)   
                    //mysqli_connect_error检测数据库是否连接成功
             ) . '</pre>' );
         上面的代码可以不用管细节，其大概逻辑就是执行mysql查询语句结果赋值给$result变量
    */
    if( $result && mysqli_num_rows( $result ) == 1 ) { // mysqli_num_rows返回$result变量中行的数量
        // Get users details
        $row    = mysqli_fetch_assoc( $result );       //mysqli_fetch_assoc将$result合并为数组并返回其中指针所指向的元素（最初为第一个元素），返回后指针将后移到之后的一个元素。
      																								 //这里的数组类似于python中的字典（键=>值），
        $avatar = $row["avatar"];                      //获取数组中avatar的值

        // Login successful
        echo "<p>Welcome to the password protected area {$user}</p>";    //登录成功
        echo "<img src=\"{$avatar}\" />";
    }
    else {
        // Login failed
        echo "<pre><br />Username and/or password incorrect.</pre>";     //登录失败
    }

    ((is_null($___mysqli_res = mysqli_close($GLOBALS["___mysqli_ston"]))) ? false : $___mysqli_res);  //关闭与数据库的链接
}

?>
```

由于登录的账号与密码均为弱口令，所以我们可以对其进行爆破，使用burp进行抓包后发送到intruder：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640864034631-92f63e52-79d4-4bfd-8ce8-cbfd5e97b714.png)

来到intruder，由于这里账号密码均不知道，所以需要同时对账号密码进行爆破，选择attack type为Cluster bomb并清空burp为我们选择的payload变量：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640864287151-22c79d5f-e946-4d2d-9b06-96147c4c30e0.png)

然后选择我们需要的变量：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640864316155-dc7195c7-49d1-45c2-a369-2e1491ec2ef0.png)

接下来对爆破字典进行设置，这里自定义几个就可以了，首先对第一个变量进行设置：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640864609817-df3d2766-ce9e-4c55-b7ca-963bc76faebe.png)

然后对第二个变量进行设置：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640864498736-a2ab4446-6559-4326-aad0-45d3c2e23d03.png)

然后点击此页面上的Start attack，由于失败和成功的相应包不同，所以可以根据其长度来判断爆破成功与否，很简单，只要找到长度不同的那个就是正确的账号密码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640864777487-4bd266ab-37c1-49aa-888c-c1becbe21023.png)

账号密码为admin、password，如上图所示。多提一句，low等级的两个数据框存在SQL注入，可以通过此种方式获取账号密码的md5值：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640865332182-7da53ba4-dd63-4555-a4f5-6da6372869ab.png)

# medium
我们将DVWA的安全等级调整到medium，注意看一下调整后的cookie是否正确：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640864993418-89a24467-0f17-4fa1-907a-fef30af212c2.png)

仍然的，先看一下源码：

```php
<?php

if( isset( $_GET[ 'Login' ] ) ) {
    // Sanitise username input
    $user = $_GET[ 'username' ];
    $user = ((isset($GLOBALS["___mysqli_ston"]) && is_object($GLOBALS["___mysqli_ston"])) ? mysqli_real_escape_string($GLOBALS["___mysqli_ston"],  $user ) : ((trigger_error("[MySQLConverterToo] Fix the mysql_escape_string() call! This code does not work.", E_USER_ERROR)) ? "" : ""));

    // Sanitise password input
    $pass = $_GET[ 'password' ];
    $pass = ((isset($GLOBALS["___mysqli_ston"]) && is_object($GLOBALS["___mysqli_ston"])) ? mysqli_real_escape_string($GLOBALS["___mysqli_ston"],  $pass ) : ((trigger_error("[MySQLConverterToo] Fix the mysql_escape_string() call! This code does not work.", E_USER_ERROR)) ? "" : ""));
    $pass = md5( $pass );

    // Check the database
    $query  = "SELECT * FROM `users` WHERE user = '$user' AND password = '$pass';";
    $result = mysqli_query($GLOBALS["___mysqli_ston"],  $query ) or die( '<pre>' . ((is_object($GLOBALS["___mysqli_ston"])) ? mysqli_error($GLOBALS["___mysqli_ston"]) : (($___mysqli_res = mysqli_connect_error()) ? $___mysqli_res : false)) . '</pre>' );

    if( $result && mysqli_num_rows( $result ) == 1 ) {
        // Get users details
        $row    = mysqli_fetch_assoc( $result );
        $avatar = $row["avatar"];

        // Login successful
        echo "<p>Welcome to the password protected area {$user}</p>";
        echo "<img src=\"{$avatar}\" />";
    }
    else {
        // Login failed
        sleep( 2 );
        echo "<pre><br />Username and/or password incorrect.</pre>";
    }

    ((is_null($___mysqli_res = mysqli_close($GLOBALS["___mysqli_ston"]))) ? false : $___mysqli_res);
}

?>
```

相较于low等级，这里添加了`mysqli_real_escape_string`函数来过滤一些特殊字符，减少了SQL注入的可能性，但是这里似乎可以使用字符编码进行绕过（这里先不说）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640865738511-353edc5c-b0dc-4646-b94e-96eaef9dc77d.png)

虽然这里过滤了字符，但是并没有从根源上阻止爆破（`sleep( 2 )`不算，只是延长了爆破时间而已），爆破过程和之前的相同。

# High
现在来到高等级，这个等级就很有意思了：

```php
<?php

if( isset( $_GET[ 'Login' ] ) ) {
    // Check Anti-CSRF token
    checkToken( $_REQUEST[ 'user_token' ], $_SESSION[ 'session_token' ], 'index.php' );    //校验本地的token是否和服务器中的token值相同
  																																												 //如果不相同则发生302重定向

    // Sanitise username input
    $user = $_GET[ 'username' ];
    $user = stripslashes( $user );
    $user = ((isset($GLOBALS["___mysqli_ston"]) && is_object($GLOBALS["___mysqli_ston"])) ? mysqli_real_escape_string($GLOBALS["___mysqli_ston"],  $user ) : ((trigger_error("[MySQLConverterToo] Fix the mysql_escape_string() call! This code does not work.", E_USER_ERROR)) ? "" : ""));

    // Sanitise password input
    $pass = $_GET[ 'password' ];
    $pass = stripslashes( $pass );
    $pass = ((isset($GLOBALS["___mysqli_ston"]) && is_object($GLOBALS["___mysqli_ston"])) ? mysqli_real_escape_string($GLOBALS["___mysqli_ston"],  $pass ) : ((trigger_error("[MySQLConverterToo] Fix the mysql_escape_string() call! This code does not work.", E_USER_ERROR)) ? "" : ""));
    $pass = md5( $pass );

    // Check database
    $query  = "SELECT * FROM `users` WHERE user = '$user' AND password = '$pass';";
    $result = mysqli_query($GLOBALS["___mysqli_ston"],  $query ) or die( '<pre>' . ((is_object($GLOBALS["___mysqli_ston"])) ? mysqli_error($GLOBALS["___mysqli_ston"]) : (($___mysqli_res = mysqli_connect_error()) ? $___mysqli_res : false)) . '</pre>' );

    if( $result && mysqli_num_rows( $result ) == 1 ) {   //登陆成功
        // Get users details
        $row    = mysqli_fetch_assoc( $result );
        $avatar = $row["avatar"];

        // Login successful
        echo "<p>Welcome to the password protected area {$user}</p>";
        echo "<img src=\"{$avatar}\" />";
    }
    else {																							 //登录失败
        // Login failed
        sleep( rand( 0, 3 ) );
        echo "<pre><br />Username and/or password incorrect.</pre>";
    }

    ((is_null($___mysqli_res = mysqli_close($GLOBALS["___mysqli_ston"]))) ? false : $___mysqli_res);
}

// Generate Anti-CSRF token
generateSessionToken(); 																//每次执行后会重新生成token

?>
```

校验token值的源码如下：

```php
    checkToken( $_REQUEST[ 'user_token' ], $_SESSION[ 'session_token' ], 'index.php' );    //校验本地的token是否和服务器中的token值相同
------------------------------------------------------------------------------------------------------------------------------------------------
  //https://github.com/digininja/DVWA/blob/3bbc5a233509caa1a56fa7d6d6097776783f3678/dvwa/includes/dvwaPage.inc.php#L562
// Token functions --
function checkToken( $user_token, $session_token, $returnURL ) {  # Validate the given (CSRF) token
	if( $user_token !== $session_token || !isset( $session_token ) ) {
		dvwaMessagePush( 'CSRF token is incorrect' );    //将CSRF token is incorrect显示到前端
		dvwaRedirect( $returnURL );                      //进行资源重定向
	}
}
```

同时我们在本地中发现了token值的存放地点，它其实是一个框但只不过隐藏掉了：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640919281749-07bb7209-87c8-4c32-aef4-a4d2dc652765.png)

因为是前端，我们可以将其属性修改为text来显示出来：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640919325629-71b91bc5-9aec-4bcc-859c-54679ef0c66a.png)

当每次提交账号密码后，无论正确与否服务器始终会返回一个新的token并对其进行设置，我们现在将其进行修改：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640919528855-29900582-9705-4904-be67-6240edb1dcec.png)

点击登录，查看网络资源情况：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640919620175-d7a8667b-f545-42e8-a9c5-07cd2b16a845.png)

重定向意味着我们我们不能再使用之前的方式进行爆破，因为发送请求之后如果token不正确服务器返回的并不是网站的页面而是返回302 found，收到302后浏览器再跳转到对应的页面，这点可以在burp中得到印证：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640919825290-f4cd9f72-4d1e-4410-a280-3bb95151934b.png)

相应的，要实现302跳转就要向浏览器发送请求，我们来看一下，首先修改token为不正确的值：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640920142067-2aed2298-3c11-447c-b9dd-afa572092609.png)

然后发送请求，浏览器收到服务器的302重定向：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640920241844-a4a59de9-0d36-4e4e-a790-e9460605e64c.png)

收到302后浏览器会再次发送请求到达目标网站：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640920328182-2d8e990f-d8c8-4d97-879c-7bd812f42dbd.png)

就是因为这个302重定向导致我们无法使用之前的方法进行爆破，我们应该怎么办？之前我们提到过，浏览器向服务器发送请求后**每次**都会返回一个新的token到本地（一个text类型的框），所以我们可以利用这一点来来获取正确的token，具体操作方法如下：

先抓取到对应的请求包，然后发送到intruder中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640921987462-2cb6b2d6-3618-4139-a2b2-e3a7d0bc2aac.png)

调整模式为pitchfork，设置对应的变量。接下来设置payload，username和password的payload和之前设置方法相同，这里主要看第三个payload的设置方法（3表示对第三个payload变量进行设置而不是一下子设置三个）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640921230687-e01f7dc9-1c67-4c1c-9971-84744263368a.png)

设置payload类型为Recursive grep，然后点击Options，之后设置总是重定向：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640922740730-da4cfa14-3043-4f06-8ea4-b54e01c9938c.png)

找到Grep - Extract：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640921395158-f34f1a52-ebbf-4ebd-b565-af173d80e8d0.png)

点击Add添加我们的token，如下图所示：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640921717491-7322c255-a7ca-43aa-a46c-c627ec30ea67.png)

记下token的值：`f578db391cc8b773306634c25e37e15b`，点击确定后返回，会出现：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640921798160-d23f4fb8-a7cc-4865-99a8-57d80c28feb3.png)

返回Payloads设置，为我们的token附初始值：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640921901802-630532bd-3907-4e08-a43c-79d7dcbc2bf6.png)

最后设置Resource Pool为单线程，因为Recursive grep只能支持单线程，否则会报错，顺带着设置一下延迟：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640941471349-16d193b8-df56-4bb0-a76d-d0ea754cffce.png)

点击Start Attack开始爆破，结果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640941372995-bd863ba4-78a7-47f7-828f-7e64d6305a1c.png)

账号密码：admin、password。

# impossible
impossible在high的基础上添加了对爆破的限制，爆破是不太可能的了：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1640942896263-07fc5165-eb94-4056-a0fa-bfde6112c0d3.png)

## 总结
感兴趣的可以对high等级写个python脚本进行爆破，这里就不详说了。





