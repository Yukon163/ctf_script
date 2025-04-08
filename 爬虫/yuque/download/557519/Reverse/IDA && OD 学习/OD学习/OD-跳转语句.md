资料来源：[https://www.cnblogs.com/nxiao/articles/6354387.html](https://www.cnblogs.com/nxiao/articles/6354387.html)

一、机械码,又称机器码.

ultraedit打开,编辑exe文件时你会看到

许许多多的由0,1,2,3,4,5,6,7,8,9,A,B,C,D,E,F组成的数码,这些数码 就是机器码.

修改程序时必须通过修改机器码来修改exe文件.

二、需要熟练掌握的全部汇编知识(只有这么多)

不大容易理解,可先强行背住,混个脸儿熟,以后慢慢的就理解了

cmp a,b 比较a与b

mov a,b 把b的值送给a

ret 返回主程序

nop 无作用,英文“no operation”的简写，意思是“do nothing”(机器码90)***机器码的含义参看上面

(解释:ultraedit打开编辑exe文件时你看到90,等同于汇编语句nop)

call 调用子程序

je 或jz 若相等则跳(机器码74 或0F84)

jne或jnz 若不相等则跳(机器码75或0F85)

jmp 无条件跳(机器码EB)

jb 若小于则跳

ja 若大于则跳

jg 若大于则跳

jge 若大于等于则跳

jl 若小于则跳

jle 若小于等于则跳

pop 出栈

push 压栈

三、常见修改(机器码)

74=>75 74=>90 74=>EB

75=>74 75=>90 75=>EB

jnz->nop

75->90(相应的机器码修改)

jnz -> jmp

75 -> EB(相应的机器码修改)

jnz -> jz

75->74 (正常) 0F 85 -> 0F 84(特殊情况下,有时,相应的机器码修改)

四、两种不同情况的不同修改方法

1.修改为jmp

je(jne,jz,jnz) =>jmp相应的机器码EB （出错信息向上找到的第一个跳转）jmp的作用是绝对跳，无条件跳，从而跳过下面的出错信息

xxxxxxxxxxxx 出错信息，例如：注册码不对，sorry,未注册版不能...，"Function Not Avaible in Demo" 或 "Command Not Avaible" 或 "Can't save in Shareware/Demo"等 （我们希望把它跳过，不让它出现） xxxxxxxxxxxx 正确路线所在

2.修改为nop

je(jne,jz,jnz) =>nop相应的机器码90 （正确信息向上找到的第一个跳转） nop的作用是抹掉这个跳转，使这个跳转无效，失去作用，从而使程序顺利来到紧跟其后的正确信息处 xxxxxxxxxxxx 正确信息，例如：注册成功，谢谢您的支持等（我们希望它不被跳过，让它出现，程序一定要顺利来到这里）

xxxxxxxxxxxx 出错信息（我们希望不要跳到这里，不让它出现）

五、爆破无敌口诀 背会此口诀，天下无敌，以后慢慢琢磨，仔细体会，收益多多。如此好的口诀，不要错过

一条（跳）就死，九筒（90）就胡   (对应上面的2.修改为nop）

一条（跳）就胡，一饼（EB）伺候   (对应上面的1.修改为jmp）

妻死（74）便妻无（75）

爸死（84）便爸无（85）

