from urllib.request import urlopen
from bs4 import BeautifulSoup

url = urlopen('https://cointelegraph.com/news/polygon-powers-india-police-complaint-portal-battling-corruption')
soup = BeautifulSoup(url, 'html.parser')   # parser 解析

# 获取文章标题
title = soup.find('article', class_="post__article").find('h1')
print("标题:{}".format(title.string))

# 获取文章正文
content_list = soup.find('div', class_="post-content").contents

print("内容：")
for label in content_list:
    if(label.name == "p"):
        print(label.getText())
        print()
