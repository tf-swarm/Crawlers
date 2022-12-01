import requests
import json
import feedparser
from lxml import etree
from datetime import datetime, timedelta
from lib.call_mysql import call_query_mysql, call_insert_mysql
from lib.qiniu_upload import Qiniu
# from ubuntu.gamefi.liunx.qiniu_upload import Qiniu

class Medium():

    def __init__(self):
        # url = "https://www.toptal.com/developers/feed2json/convert?url={}".format("https://medium.com/feed/@SecondLiveReal")
        # url = 'https://api.rss2json.com/v1/api.json?rss_url=https://medium.com/feed/@SecondLiveReal'
        self.table_name = "t_game_list"
        self.table_strategy = "t_game_strategy"


    def deal_query_info(self):
        json_info = {"table": self.table_name}
        games = call_query_mysql(json_info)
        for data in games:
            g_id, chainId, medium_link = data.get("id", 0), data.get("chainId", ""), data.get("mediuLink", "")
            if medium_link and  medium_link.find("@") != -1:
                user_name = medium_link[medium_link.find("@"):]
                print("{}--:{}".format(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), user_name))
                self.get_feedparser_json(g_id, user_name)
            else:
                continue


    def deal_medium_info(self, medium):
        title = medium["title"]
        msg = call_insert_mysql(self.table_strategy, medium)
        if msg["msg"] != "ok":
            print("----11:", title)

    def formatGMTime(self,timestamp):
        gmt_format = '%a, %d %b %Y %H:%M:%S GMT'
        gmt_date = datetime.strptime(timestamp, gmt_format) + timedelta(hours=8)
        return gmt_date

    def datetime_to_str(self, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)


    def get_feedparser_json(self ,game_id, user_name):
        rss_url = "https://medium.com/feed/{}".format(user_name)
        result = feedparser.parse(rss_url)
        print("--feed--:", game_id, user_name, len(result["entries"]))
        for entry in result["entries"]:
            # 标题
            title = entry.get("title", "")
            # 缩略图  https://miro.medium.com/max/1024/0*35qAY2SUg0KQObd-.png
            tree = etree.HTML(entry["summary"])
            image = tree.xpath('//img//@src')[0].replace("cdn-images-1", "miro")
            # 七牛云
            image_url = Qiniu.get_upload_img_url(image)
            # 发布时间
            published_time = self.datetime_to_str(self.formatGMTime(entry.get("published", "")))
            # 链接
            link = entry.get("link", "")
            # 类别
            if "tags" in entry:
                tags = [x["term"] for x in entry["tags"]]
            else:
                tags = []
            # 作者
            author = entry.get("author", "")
            # 内容
            content = entry.get("summary", "").replace("cdn-images-1", "miro")

            medium_info = {
                "gameId": game_id, "title": title, "thumbnail": image_url, "published_time": published_time,
                 "categories": tags, "author": author, "content": content
            }
            # print("--medium--:", medium_info)
            self.deal_medium_info(medium_info)


if __name__ == '__main__':
    med = Medium()
    med.deal_query_info()
    # med.get_single_text()

