from bs4 import BeautifulSoup
# 调用requests库获取的网页
import requests
import chardet
url = 'http://www.tipdm.com'
ua = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) Chrome/65.0.3325.181'}
# 初始化HTML
rqg = requests.get(url)
html = rqg.content.decode('utf-8') #（以 utf-8 指定的编码格式解码字符串）
soup = BeautifulSoup(html, "lxml")    # 生成BeautifulSoup对象 或用 html.parser解析器
print("输出格式化的BeautifulSoup对象:", soup.prettify())
