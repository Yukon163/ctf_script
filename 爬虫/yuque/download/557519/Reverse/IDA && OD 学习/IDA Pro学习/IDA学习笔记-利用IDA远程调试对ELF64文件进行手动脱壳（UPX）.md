又是“~~**快乐**~~输液”的一天......

---

材料：2020HGame中reverse的unpack_00b2bb661b

将ELF文件放入到三个查壳器中，要么提示无壳要么报错

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586216616175-69320d8c-cf1c-4c98-9006-9f3376505310.png)

既然这样，我们将程序运行看看能得到什么吧，为了方便，将文件“unpack_00b2bb661b”重命名为“1”，尝试运行一下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586217210362-a391ee13-e05f-45a2-bef2-16e275332cf6.png)

> 注意给elf文件以权限：chmod a+x 文件名，否则会出现“Permission denied”的错误
>

将文件载入到IDA中：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586217349227-c01a69f0-997b-4bf8-9210-b68840686c21.png)

只有这几个函数，有可能加了壳

> 2020HGame中的题目中提示道：
>
> ![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586217572828-9d49546c-b9a7-4928-934e-886181d2ae3f.png)
>

**查不出来是什么壳是由于出题人更改了ELF文件头**

接下来我们使用IDA的远程调试进行手动脱壳：

首先将Windows的IDA安装目录下的dbgsrv文件夹全部拷贝到linux（ubuntu）中，然后让ELF文件“1”放入到相同文件夹下，如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586217817067-1f839a36-b618-45ef-9a7b-4c6d130b1fae.png)

接下来我们需要确定debug处理器的位数，在debug目录下右键打开终端，输入file 1：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586218039044-2608688f-9e5a-4e52-a958-60d1ab3b9b05.png)

> ELF 64-bit，说明它是64位可执行文件
>

然后我们在Windows环境下的IDA里配置，打开64为的IDA：将debug载入到IDA中

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586218343068-9776c572-1bd1-4b3a-9890-22bbba94bd73.png)

在菜单栏上选中：调试器->选择调试器

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586218344434-5010b411-4269-4905-91bd-2bf76dc8ca5a.png)

选中Remote Linux debugger，点击确定

再次单击菜单栏中的调试器->进程选项

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575178836200-eaaddb1c-b310-437c-9d2d-0563f1024d76.png)

应用程序、输入文件、目录、主机名、端口都是虚拟机的参数（其他空白就好）

主机名就是IP地址，那linux的IP地址怎么看？

在linux中终端中输入ip addr

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586218460294-ad40ff81-4b9d-4c81-a39a-ef215e91d486.png)

最终所需填写参数如下图所示：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586218525045-972f59d5-8846-4fdc-aa94-ed8945e49543.png)

接下来，我们开始调试：

首先输入在dbgsrv中打开终端：

> 注意给elf权限：chmod a+x linux_server64
>
>   chmod a+x 1
>

接着：输入：./linux_server64（linux为64位，无法执行32位的程序，会提示<font style="color:#F5222D;">No such file or directory</font>，需要安装32的库），启动远程调试服务

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586218694656-8a78f582-050d-486e-880a-b905e56db699.png)

在IDA里打开![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575180462136-d3411172-d7da-4429-b0f0-de953b1d099e.png)

启动！

![](https://cdn.nlark.com/yuque/0/2019/png/574026/1575180546489-32f31901-1259-453f-a3e4-0fc51772938f.png)

单击“是”，IDA界面如下

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586218725790-a423b9fc-2cb2-42e0-9dab-de2c490ec124.png)

这时候我们会发现单步步入和单步步过是灰的，无法执行

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586218799164-750c4ddf-1520-4f06-b1aa-804c5c440a97.png)

先中断调试：Ctrl+F2（调试器->终止进程），然后“菜单栏->窗口->重置桌面”，来到：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586219023782-f22384cb-d535-46b2-bb4e-a6719de27896.png)

单击函数窗口中的start函数，来到视图窗口

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586219083888-25c4cbbf-73d2-4cdc-bcdb-1db74011608a.png)

选中视图窗口中的public start，右键->添加断点

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586219165213-a93bdb31-0c73-443c-a6ee-b2a90934c6ae.png)

再次尝试进行调试

调试器->启动进程，在接下来弹出的窗口中选择“是”，此时单步步入和单步步过可用，接下来开始手动脱“类UPX壳”，界面如下：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586219328185-7ddf7403-2359-458a-8e12-aecde9e672e0.png)

参考资料：[https://www.52pojie.cn/thread-1048649-1-1.html](https://www.52pojie.cn/thread-1048649-1-1.html)

开始单步调试：

> <font style="color:#444444;">单步调试遵循两个原则：</font>
>
> <font style="color:#444444;">1.除非F8跑飞，否则不用F7。</font>
>
> <font style="color:#444444;">2.循环直接跳过。</font>
>

上来直接按F8会直接跑飞的（别问我是怎么知道的），因此只能单步步入F7

> 若程序跑飞，只能重新调试喽
>

有：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586219635858-f238a848-997f-4c14-ae0e-7c77dfccaa1a.png)

一直单步来到LOAD:000000000044F3EF call    sub_44F36D，此时若单步步过，程序会直接跑飞，因此我们单步步入：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586219763569-67113860-94bd-4c47-a087-9183d06007d2.png)

接下来继续F8（注意别让程序跑飞了），稍后来到：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586219843260-6302b4e7-a344-4830-bc3e-d969bd18e2b0.png)

按下F7单步步入：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586219875072-62cfc5a6-ef3d-4f81-a8d3-0399287ad36a.png)

调试器窗口向下滑动，会看到三个循环

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586219961181-86a702ef-1e4d-4634-90b0-b7f2b0dce456.png)

光标单击debug001:000000000084F489 lea     r15, [rdi-8]，按下F4运行到光标处，然后继续调试，直到：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586220082045-457944b5-b183-43ab-a659-79241872534a.png)

在这里观察寄存器中R15的值：00007FFE1EE3DC00

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586220145669-8fe99162-17fd-4149-9201-b5c3eb04490a.png)

在堆栈窗口中的空白处右键:

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586220250058-2b08b9f6-9233-4088-83fd-db0ea4ca5868.png)

有：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586220290993-15fc9020-6b6e-4d5c-851f-9e07b21bc232.png)

然后继续单步步过，然后会弹出窗口：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586220575466-cf24c896-7d18-4efc-9309-9c31a0831d12.png)

单击是，来到：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586220625535-9198f9f5-95bb-4f45-bc57-207280a4b66b.png)

继续F8

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586221061774-7757ed5f-a9d5-462a-bc82-ec1e77d9f265.png)

> 注：ELF文件的入口点为：0x400890
>

F8步过rern后，单击是：![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586221146015-2abce2dd-855b-4be6-aacb-8d13bea15077.png)

发现来到了我们刚才所说的入口点（OEP）

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586221180051-a588120c-93a5-4cb3-8d8c-a1686c15d4b7.png)

如上图光标所指向的地方就是OEP，开始dump内存，IDC脚本如下：



```c
#include <idc.idc>
#define PT_LOAD 1
#define PT_DYNAMIC 2
static main(void)
{
    auto ImageBase, StartImg, EndImg;
    auto e_phoff;
    auto e_phnum, p_offset;
    auto i, dumpfile;
    ImageBase = 0x400000;
    StartImg = 0x400000;
    EndImg = 0x0;
    if (Dword(ImageBase) == 0x7f454c46 || Dword(ImageBase) == 0x464c457f)
    {
        if (dumpfile = fopen("C:\Users\Windows 10\Desktop\unpack_00b2bb661b", "wb")) //此处填写Windows环境下的ELF文件路径
        {
            e_phoff = ImageBase + Qword(ImageBase + 0x20);
            Message("e_phoff = 0x%x\n", e_phoff);
            e_phnum = Word(ImageBase + 0x38);
            Message("e_phnum = 0x%x\n", e_phnum);
            for (i = 0; i < e_phnum; i++)
            {
                if (Dword(e_phoff) == PT_LOAD || Dword(e_phoff) == PT_DYNAMIC)
                {
                    p_offset = Qword(e_phoff + 0x8);
                    StartImg = Qword(e_phoff + 0x10);
                    EndImg = StartImg + Qword(e_phoff + 0x28);
                    Message("start = 0x%x, end = 0x%x, offset = 0x%x\n", StartImg, EndImg, p_offset);
                    dump(dumpfile, StartImg, EndImg, p_offset);
                    Message("dump segment %d ok.\n", i);
                }
                e_phoff = e_phoff + 0x38;
            }
            fseek(dumpfile, 0x3c, 0);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fseek(dumpfile, 0x28, 0);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fputc(0x00, dumpfile);
            fclose(dumpfile);
        }
        else
            Message("dump err.");
    }
}
static dump(dumpfile, startimg, endimg, offset)
{
    auto i;
    auto size;
    size = endimg - startimg;
    fseek(dumpfile, offset, 0);
    for (i = 0; i < size; i = i + 1)
    {
        fputc(Byte(startimg + i), dumpfile);
    }
}
```

在IDA中：菜单栏->文件->脚本命令，粘贴代码，然后运行：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586222247130-4911a4be-b54c-4b67-b884-c77e0c6e4379.png)

稍等片刻，会在同路径生成：UsersWindows 10Desktopunpack_00b2bb661b（文件名可能不相同）

关闭调试。

将脱壳后的文件拖入IDA中

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586222507197-be2ee305-2340-479d-b874-0616bb303559.png)

成功脱壳，Shift+F12搜索字符串，找到Wrong input，交叉引用来到：

![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586222668615-e32a39a7-0bdc-451e-a84c-32e67d85923f.png)

然后写一个解密代码：

```c
#include <stdio.h>
int main()
{
    unsigned char str[] = {0x68, 0x68, 0x63, 0x70, 0x69, 0x80, 0x5B, 0x75, 0x78, 0x49, 0x6D, 0x76, 0x75, 0x7B, 0x75, 0x6E, 0x41, 0x84, 0x71, 0x65, 0x44,
                           0x82, 0x4A, 0x85, 0x8C, 0x82, 0x7D, 0x7A, 0x82, 0x4D, 0x90, 0x7E, 0x92, 0x54, 0x98, 0x88, 0x96, 0x98, 0x57, 0x95, 0x8F, 0xA6, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    //必须有unsigned（无符号型，否则会报错）
    int i;
    for (i = 0; i <= 41; i++)
    {
        printf("%c", str[i] - i);
    }
    return 0;
}
```





![](https://cdn.nlark.com/yuque/0/2020/png/574026/1586223923345-41b86132-c5e5-4459-8fad-ecd1d977b165.png)

flag：hgame{Unp@cking_1s_R0m4ntic_f0r_r3vers1ng}

