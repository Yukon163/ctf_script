from bs4 import BeautifulSoup

html = """<html >
<head>
    <meta charset="UTF-8">
    <title>我的第一个页面</title>
</head>
<body>
    <h1>这里是文章的标题。</h1>
    <p>这里是文章的段落1。</p>
   <p>这里是文章的段落2。</p>
  <p>这里是文章的段落3。</p>
<a href=http://www.ahu.edu.cn  title=“安徽大学”>安徽大学</a>  
<a href=http://www.ustc.edu.cn  title=“中国科技大学”>中国科技大学</a>
</body>
</html> 
"""
soup = BeautifulSoup(html, 'lxml')
# tag = soup.a
# print("soup的name:", soup.name)  # 获取soup的name
# print("a标签的name:", soup.a.name)  # 获取a标签的name
# print("tag的name:", tag.name)  # 获取tag的name
# print("tag的内容:", tag)  # 标签全部内容
# print("tag的文本:", tag.text)  # 标签标题
# print("tag的属性:", tag.attrs['title'])  # 属性为字典
# print("tag的链接：", tag.attrs['href'])

a_tags = soup.find_all('a')
# my-class_a_tags = soup.find_all('a', class_='my-class')  # 查找所有 class 属性为 'my-class' 的 <a> 标签
# soup.find_all('div', recursive=False)  # 仅查找直接子标签，不递归查找子孙标签
# soup.find_all('p', string='这里是文章的段落1。')  # 查找所有文本内容为 '这里是文章的段落1。' 的 <p> 标签
# soup.find_all('a', limit=3)  # 仅返回前三个符合条件的 <a> 标签
# paragraphs_with_class = soup.find_all('p', class_='paragraph-class')

if len(a_tags) >= 2:
    for i in range(len(a_tags)):
        second_a_tag = a_tags[i]
        print(f"<a{i}> tag's content:", second_a_tag)
        print(f"<a{i}> tag's title attribute:", second_a_tag.attrs['title'])
        print(f"<a{i}> tag's href attribute:", second_a_tag.attrs['href'])
else:
    print("No second <a> tag found.")

tag = soup.title
print("Tag对象中包含的字符串:", tag.string)  # 获取Tag对象中包含的字符串
print("tag.string的类型:", type(tag.string))  # 查看类型

t = soup.head
t1 = soup.p  # 定位文档对象中的标签
t2 = soup.title
t3 = soup.a
print(t)
print(t.meta["charset"], t.title.text)
print(t1, t1.text)
print(t2, t2.text)
print(t3, t3.text)


