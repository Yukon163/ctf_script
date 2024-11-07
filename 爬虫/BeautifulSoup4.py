from bs4 import BeautifulSoup

html = '''<meta charset='UTF-8'>
<html>
<head>
    <title>ID和Class的定义</title>
    <style type='text/css'>
    <!--
        #divdemo{background-color:#90EE90 ;border:0.2cm groove orange;} 
       #divdemo1{background-color:#66EE90 ;border:0.6cm groove green;}
        .m1 {font-size:20px; color:#FF0000;}
        p.p2{font-size:26px; color:#FF0066;}
        .red {font-size:20px; color:red;}
        .green {font-size:20px; color:green;}
        .blue {font-size:20px; color:blue;}
    -->
    </style>
</head>
<body>
    <div id='divdemo'>
        <p>此段文字以默认方式显示</p>
        <p class='m1'>此段文字以16像素大小，红色字体显示</p>
        <p class='p2'>此段文字以26像素大小，玫红色字体显示</p>
        <p class='p2'>此段文字以26像素大小，玫红色字体显示1</p>
        <p class='p2'>此段文字以26像素大小，玫红色字体显示2</p>
        <a href=http://www.ahu.edu.cn  class='m1'  title='安徽大学'>安徽大学</a>

    </div>
    <div  id='divdemo1'> 
        <p class='red'>数据分析</p>
        <h2 class='green'>数据可视化</h2>
        <h3 class='blue'>机器学习</h3>
       <h3 class='red'>机器不学习</h3>
       <p   class='blue'>Python程序设计</p>
   </div>


</body></html>
'''

soup = BeautifulSoup(html, 'html.parser')

from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'html.parser')
# 1、用属性找到第一个div
tg = soup.div
# 2、用属性找第一个div下面的第一个p文本
tg1 = soup.div.p.text
# 3、用find方法找查找
tg2 = soup.find('div')  # 第一个div
tg3 = soup.find('div', id='divdemo1')  # 指定id
print(tg3.find('p', class_='blue'))  # 在tg3下继续查找子项
print(tg3.find('h3', class_='red'))  # 在tg3下继续查找子项
# 以上两个操作说明，find 不论是否带属性查找，都是只能找到符合条件的第一个
# 4、用find_all方法找查找
# 1) #查找所有div 结果为可迭代对象
tg = soup.find_all('div')
# 2)指定id
tg2 = soup.find_all('div', id='divdemo1')  # 集合
for i in tg2:  # 迭代出每个元素的文本
    print(i.text)
# 3）指定class_ 
tg3 = soup.find_all('p', class_='blue')  # 指定类别查找

# 4)  tg2为结果集，长度为1，索引好0的文本就是期中子项中的所有内容
tg2 = soup.find_all('div', id='divdemo1')
print(tg2[0].text)

# 5）查找链接a的地址属性

taget = soup.a  # 指定第一个a
print(taget['href'])
taget = soup.find('a')  # 查找第一个a

print(taget['href'])

Taget = soup.find_all('a')  # 查找所有的a，结果为列表，需要迭代才能输出地址

# 6)如何用find查找子项

taget = soup.find('div')  # 第一个div
t1 = taget.findChild('p')  # 期中子项
print(t1)
t2 = t1.find_next('p')  # 子项的下一个子项
print(t2)
t3 = t2.find_all_previous('p')  # 子项的上所有个
print(t3)
