# coding:utf-8

import requests
import parsel
import time
import datetime
from datetime import datetime
from liunx.call_mysql import call_insert_mysql
import re
from liunx.qiniu_upload import Qiniu
# from ubuntu.gamefi.liunx.qiniu_upload import Qiniu

class Egamers():

    def __init__(self):
        self.now_time = self.datetime_to_str(datetime.now())
        self.news_table = "t_news"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        }

    def datetime_to_str(self, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)

    def get_requests_info(self, url):
        result = requests.get(url=url, headers=self.headers)
        response = parsel.Selector(result.text)
        return response

    def deal_news_team(self, html_data):
        browse, hot = 0, 0
        try:
            # 来源
            root_in = "eGamers.io"
            logo_url = html_data.xpath('.//*[@id="tdi_19"]/div/div[2]/div/div[1]/div/a/span[1]/img/@data-lazy-src').extract_first()
            article_list = html_data.xpath('//div[@class="td_block_inner tdb-block-inner td-fix-index"]/div')
            # print("{}--:".format(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
            print("--news--", len(article_list), datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S'))
            for div in article_list:
                image = div.xpath('./div/div[1]/div[1]/a/span/@data-img-url').extract_first()
                # 七牛云
                image_url = Qiniu.get_upload_img_url(image)
                title = div.xpath('./div/div[2]/h3/a/text()').extract_first()
                time_str = div.xpath('./div/div[2]/div/span/span[2]/time/@datetime').extract_first()
                create_time = time_str.replace("T", " ").replace(".000Z", "").split("+")[0]
                nft_url = div.xpath('./div/div[1]/div[1]/a/@href').extract_first()
                category = self.get_requests_info(nft_url)
                content = category.xpath('//div[@class="tdb-block-inner td-fix-index"]/p[1]').extract_first()
                content_text = re.compile(r'<[^>]+>', re.S).sub('', content)
                game_info = {
                    "title": title, "createTime": create_time, "updateTime": self.now_time, "contentText": content_text,
                    "rootIn": root_in, "browse_volume": browse,"hot_volume": hot,"logoUrl": image_url
                }
                print("--game_info--", game_info)
                # 判断数据库是否存在
                # msg = self.deal_news_info(game_info)
        except Exception as e:
            print("{}".format(e))

    def deal_news_info(self, news):
        title = news["title"]
        msg = call_insert_mysql(self.news_table, news)
        if msg["msg"] != "ok":
            print("----11:", title)


    def get_egamers_news_team(self):
        for i in range(1, 2):
            url = "https://egamers.io/category/blockchain-games/page/{}/".format(i)
            result = self.get_requests_info(url)
            self.deal_news_team(result)
            break


if __name__ == '__main__':
    eg = Egamers()
    eg.get_egamers_news_team()
    # url = "https://egamers.io/splinterlands-accomplishes-2-32m-daily-rentals-successfully/"
    # eg.get_requests_info(url)