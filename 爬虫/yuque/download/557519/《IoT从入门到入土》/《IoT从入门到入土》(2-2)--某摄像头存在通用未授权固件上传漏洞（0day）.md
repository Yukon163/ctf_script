> <font style="color:rgba(0, 0, 0, 0.66);">本文首发于IOTsec-Zone</font>
>

将摄像头与互联网进行连接初始化之后，使用nmap扫描摄像头的开放端口：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657672039492-933436a0-e39c-4e66-a9ea-a01b35959df1.png)

可以看到摄像头开放了五个端口，这里关注到80端口，在浏览器中输入`http://192.168.2.116:80`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657861788650-16796846-5251-4d46-8052-891d3a970eb8.png)

发现会302重定向到`http://192.168.2.116/home.htm`，最终跳转到`http://192.168.2.116/apcam/adm/MyTest.asp`：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657861811862-7c148764-176a-4985-b056-731f9b2a408b.png)

而这个网站什么都没有。因为有官方的手机App，所以在不逆向的前提下可以通过抓包分析手机与云服务的通信状态，其中有一个关于固件升级的包：

```json
//---------------------------------------------------------------固件升级
POST /xx/xx/query_device_upgrade_task HTTP/1.1
Host: www.xxx.com
Content-Type: application/json; charset=utf-8
Content-Length: 278
Accept-Encoding: gzip, deflate
User-Agent: okhttp/3.12.8
Connection: close

{
    "header": {
        "device_list": [
            "xxx"
        ],
        "seqno": "xxx",
        "user_id": "xxx",
        "package_name": "xxx",
        "language": "zh_CN",
        "client_version": "x.x.x.x",
        "token": "xxx",
        "phone_model": "xxx"
    }
}

//---------------------------------------------------------------响应包
HTTP/1.1 200 OK
Date: Mon, 04 Jul 2022 00:57:26 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 463
Connection: close
Set-Cookie: xxx=xxx; path=/
Set-Cookie: xxx=xxx; path=/
Server: elb

{
    "error_code": "0",
    "error_msg": "success",
    "body_info": {
        "upgrade_task": [
            {
                "device_id": "xxx",
                "is_force": "N",
                "main_version": {
                    "device_version": "xx.xx.xx.xx",
                    "version_type": 0,
                    "url": "http://xxx.img",
                    "md5sum": "xxx",
                    "remark": "1.优化固件功能，提高用户体验。",
                    "is_support_sdcard_prealloc": 1,
                    "last_app_version": ""
                },
                "sub_versions": [],
                "switchto_sdcard_prealloc": "Y"
            }
        ]
    }
}
```

即，当摄像头存在固件升级时可以获取固件的URL，将固件下载后因为发现固件过小，所以可以知道是"增量包"而不是"全量包"，在ubuntu中尝试使用`firmware_mod_kit`的`./extract-firmware.sh`进行解压：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657691537034-dcc49658-2346-44b8-8182-6ae403327e4d.png)

摄像头使用的架构为MIPS 32位小端序：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657674903969-2b370bd9-9eac-4318-89b7-2a3068e9f21b.png)

来到固件目录，使用grep命令尝试搜索关键字：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657691709046-5d9e5d06-776f-4420-bdd1-cd960395f632.png)

goahead中的`http://"+location.hostname+"/xxxx/xxx/upload_firmware.asp`引人注目，在浏览器中访问：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657691727968-05d1741c-bc32-43bc-b2a5-d766d4a26722.png)

发现未授权固件上传漏洞。查看增量包中的两个shell脚本，修改其中的startapp：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657675107910-86219354-9362-430a-a121-127b72a6e84f.png)

发现内置的telnetd接口，取消其注释，使用`firmware_mod_kit`的`build-firmware.sh`重新打包：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657675284775-c578372d-a257-41ce-9160-4723281fe8d1.png)

为了避免一些不必要的问题，我们将打包后的固件重命名为原升级包的名称：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657691813221-2a783b28-125a-4d84-a2d0-0d2c9d7b11c4.png)

使用`upload_firmware.asp`上传：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657693833755-1945f8b8-e7da-488a-9c6c-f96f9872feac.png)

再次使用nmap扫描端口：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657675631182-636a0889-ef77-4353-b6e6-c3c2f7427c71.png)

开放了telnet的23端口，尝试连接：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657691860711-68f833d9-17c5-4814-b09e-4eec578eed54.png)

嘶，需要密码，回到配置文件，修改为`telnetd -l /bin/sh &`

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657675968564-016d7195-c237-4a25-9e35-35f503785297.png)

保存修改后重新打包上传：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657691907916-69ad2c58-4677-49eb-9523-32bfa0408fa9.png)

重新尝试telnet登录：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657676208782-c92ffc4e-ccd6-4136-a60a-120abbb86748.png)

拿到root shell，可以使用的命令如下：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657676330798-91de2020-b39b-424f-af5a-4d0dbf074dcb.png)

命令还不少，有base64、wget等。web目录在：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657692058886-1d90ae4c-0f7d-4861-8a28-4a3880cf895d.png)

这能访问的asp页面不少啊，其中就包括前面使用的`upload_firmware.asp`。关于telnetd：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657677566325-8f6d860b-9210-4320-a693-448517d15eeb.png)

`telnetd -l /bin/sh &`：`telnetd -l /bin/sh`表示直接启动shell，`&`表示telnet后台运行。并且因为摄像头有云服务，所以它也是通外网的：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657678690580-81f89a8d-44a4-48ee-a6c7-6a7a70131490.png)

因为这个摄像头有base64命令，所以可以通过它来上传或下载文件，比如现在我要下载`goahead`，对文件进行base64编码：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657692180600-1f1ae700-5fef-4109-9a33-b221fa84249f.png)

将编码保存到txt中，然后`base64 --decode`即可：

![](https://cdn.nlark.com/yuque/0/2022/png/574026/1657687169428-aa200540-7035-43ae-955f-7b0bada429e3.png)

总结：

1. 通过流量分析软件/固件的行为，或许是一个很便捷的方法。
2. 厂商不注重对某些网页的鉴权，甚至可以导致任意刷写修改过后的固件。
3. 通过取消注释启动脚本中的telnet服务，即可建立主机与摄像头的telnet链接。
4. 对文件进行base编码即可达到下载传输文件的目的。

