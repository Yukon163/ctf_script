import requests

url = "http://www.tipdm.com"

hd = {"User-Agent":'Mozilla/5.0 (Windows NT 6.1; Win64; x64) Chrome/65.0.3325.181'}

rqg = requests.get(url, headers=hd, timeout=2)
print("状态码：", rqg.status_code)
print("编码：", rqg.encoding)
print("响应头:", rqg.headers)
print("网页内容", rqg.text)