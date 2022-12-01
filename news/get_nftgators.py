import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import calendar
from liunx.call_mysql import call_insert_mysql
from liunx.qiniu_upload import Qiniu
# from ubuntu.gamefi.liunx.qiniu_upload import Qiniu

class Nftgators():
    def __init__(self):
        self.now_time = self.datetime_to_str(datetime.datetime.now())
        self.url = "https://www.nftgators.com/blockchain-games/"
        self.news_table = "t_news"

    def datetime_to_str(self, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)

    def deal_time(self, time_list):
        year, day = time_list[2], time_list[1]
        month = list(calendar.month_name).index(time_list[0])
        ymd = datetime.datetime(int(year), int(month), int(day)).strftime("%Y-%m-%d")
        time_str = f"{ymd} 00:00:00"
        return time_str

    def get_nft_gators(self):
        browse, hot = 0, 0

        # driver = webdriver.Chrome()

        option = Options()
        option.add_argument("--headless")
        driver = webdriver.Chrome(options=option)


        driver.get(self.url)
        btn_water_xpath = "//button[@class='cs-load-more']"
        # 等待响应完成
        while True:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.XPATH, btn_water_xpath)))
            more_xpath = "//div[@id='primary']/div[2]/div[2]/button"
            btn_water = driver.find_elements_by_xpath(more_xpath)
            # print("--btn_water--", btn_water)
            if len(btn_water) > 0:
                btn_water[0].send_keys("Load More")
                time.sleep(2)
            else:
                break

        soup = BeautifulSoup(driver.page_source, 'lxml')
        root_in = soup.select('div[class="cs-header__inner cs-header__inner-desktop"]>div>div>a')[0].get("href")
        source = root_in.split("//")[1].split(".")[1]
        logo_url = soup.select('div[class="cs-header__inner cs-header__inner-desktop"]>div>div>a>img')[0].get("src")

        article_list = soup.select('div[class="cs-posts-area cs-posts-area-posts"]>div>div>article')
        print(len(article_list))
        for div in article_list:
            image = div.select('img')[0].get("src")
            # 七牛云
            image_url = Qiniu.get_upload_img_url(image)
            title = div.select('h2[class="cs-entry__title"]>a')[0].get_text().strip()
            content = div.select('div[class="cs-entry__excerpt"]')[0].get_text().strip()
            time_list = div.select('div[class="cs-meta-date"]')[0].get_text().replace(",", "").split(" ")
            create_time = self.deal_time(time_list)
            # 判断数据库是否存在
            game_info = {
                "title": title, "createTime": create_time, "updateTime": self.now_time, "contentText": content,
                "rootIn": source, "browse_volume": browse, "hot_volume": hot, "logoUrl": image_url
            }
            print("--game_info--", game_info)
            # self.deal_news_info(game_info)

        driver.quit()


    def deal_news_info(self, news):
        title = news["title"]
        msg = call_insert_mysql(self.news_table, news)
        if msg["msg"] != "ok":
            print("----11:", title)



if __name__ == '__main__':
    nf = Nftgators()
    nf.get_nft_gators()
