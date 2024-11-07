import requests

url = "https://www.ptpress.com.cn/"

rqg = requests.get(url)
print("结果类型：", type(rqg))
print("状态码：", rqg.status_code)
print("响应头:", rqg.headers)
print("编码：", rqg.encoding)
print("网页内容", rqg.text)
print("", rqg)
print("", rqg)