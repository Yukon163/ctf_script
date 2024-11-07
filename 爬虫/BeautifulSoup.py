from bs4 import *

from bs4 import BeautifulSoup
html='''
<div class="panel">
    <div class="panel-heading">
        <h4>Hello</h4>
    </div>
    <div class="panel-body">
        <ul class="list" id="list-1">
            <li class="element">Foo</li>
            <li class="element">Bar</li>
            <li class="element">Jay</li>
        </ul>
        <ul class="list list-small" id="list-2">
            <li class="element1">Foo-1</li>
            <li class="element1">Bar</li>
        </ul>
    </div>
</div>'''
soup = BeautifulSoup(html, 'lxml')
trage=soup.ul  #定位文档对象中的标签
print(trage) #
print(trage.name) #第一个标签ul名字
print(trage.attrs) #第一个标签属性的字典
print(type(trage.attrs))  #属性的类型
# 读取字典用[key]
print(trage.attrs["id"])
print(trage.li) #找到第一 ，用text可以得到标签整体列表内容
print(trage.li.text)  #具体标题内容
