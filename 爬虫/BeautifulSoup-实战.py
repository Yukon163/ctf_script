import requests
from bs4 import BeautifulSoup

url = 'http://www.tipdm.com'
ua = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) Chrome/65.0.3325.181'}

rqg = requests.get(url, headers=ua)
# rqg.encoding = chardet.detect(rqg.content)['encoding']
html_code = rqg.content.decode('utf-8')
soup = BeautifulSoup(html_code, 'html-parser')

with open("input_file_addr", 'rb') as input_file:
    with open("output_file_addr", 'wb') as output_file:
        output_file.write(input_file.read()[::-1])