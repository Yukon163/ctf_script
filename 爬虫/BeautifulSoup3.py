from bs4 import BeautifulSoup

html = """<html><head><title>ID和类的定义</title>
    <style type="text/css">
    <!-- #divdemo{background-color:#90EE90 ;border:0.2cm groove orange;}
           #data{background-color:#66EE90 ;border:0.6cm groove green;}
        .p1 {font-size:16px; color:#FF0000;}
        p.p2{font-size:26px; color:#FF0066;}
    -->
    </style> </head><body>
    <div id="divdemo">	
        <p>此段文字以默认方式显示</p>
        <p class="p1">此段文字以16像素大小，红色字体显示</p>
        <p class="p2">此段文字以26像素大小，玫红色字体显示</p>
       <p class="p2">此段文字以26像素大小，玫红色字体显示1</p>
        <p class="p2">此段文字以26像素大小，玫红色字体显示2</p>
        <a href=http://www.ahu.edu.cn  class=“p1"  title=“安徽大学”>安徽大学</a>
        <a href=http://www.ahu.edu.cn   title=“安徽大学”>安徽大学</a>
        <!--此语句测试上面的CSS的.p1属性-->
</div>
<div  id=“data”> 数据分许 </div>   <!--测试**kwargs参数-->
</body></html> 
"""
soup = BeautifulSoup(html, 'html.parser')

tag = soup.find_all('p', class_="p2")  # 三个class_=p2
print("CSS类名匹配获取的节点:", tag)  # 获得的是所有节点的列表
print("CSS类名匹配获取的节点内容:", tag[0].text)  # 列表第一个项的文本
for k in tag:
    print(k.text)  # 获得是列表，可以遍历列表得到其中文本

tag1 = soup.find_all('p', class_='p2',
                     string=['此段文字以26像素大小，玫红色字体显示1', '此段文字以26像素大小，玫红色字体显示2'])
# 在搜索的节点中用string过滤指定文本，文本可以是列表
print(type(tag1))  # 结果为列表
print(tag1[0].text)  # 都是列表的[0]项，但与上面的内容就不同了
tag2 = soup.find_all('div', id="divdemo")
print(tag2)
# 最后的参数key指定任意属性
soup=BeautifulSoup(html,'html.parser')

taget=soup.find("div")  #第一个div
t1=taget.findChild('p') #期中子项
print(t1)
t2=t1.find_next('p')  #子项的下一个子项
print(t2)
t3=t2.find_previous()  #子项的上一个
print(t3)
