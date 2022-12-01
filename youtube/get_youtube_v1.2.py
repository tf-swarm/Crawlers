import time
import json
import requests
import os
import re
import random
from datetime import datetime, timedelta
from lib.qiniu_upload import Qiniu
from lib.call_mysql import call_query_mysql, call_insert_mysql
from lib.dingding import ding

from apscheduler.schedulers.blocking import BlockingScheduler


class YouTuBe():

    def __init__(self):
        self.day_time = datetime.now().strftime('%Y-%m-%d')
        self.now_time = self.datetime_to_str(datetime.now())
        self.game_table = "t_game_list"
        self.video_table = "t_game_video_crawler"
        self.api_uri = "https://www.googleapis.com/youtube/v3/"
        self.api_info = {}
        self.api_key_list= [] # Google 申请api_key


    def http_request(self, url, api_key):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            }
            response = requests.get(url=url, headers=headers)
            json_info = json.loads(response.text)
            # 验证 api_key
            if api_key not in self.api_info:
                self.api_info[api_key] = 1
            else:
                self.api_info[api_key] = self.api_info[api_key] + 1
            return json_info
        except Exception as e:
            print("http_request {}".format(e))

    def formatUTCtime(self, stamp_str):
        utc_format = "%Y-%m-%dT%H:%M:%SZ"
        utc_date = datetime.strptime(stamp_str, utc_format) + timedelta(hours=8)
        return utc_date

    def datetime_to_str(self, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)

    def random_api_key(self):
        api_key = random.choice(self.api_key_list)
        if api_key in self.api_info:
            if len(self.api_key_list) > 1:
                if int(self.api_info[api_key]) >= 1000:
                    self.api_key_list.remove(api_key)
                    api_key = random.choice(self.api_key_list)
            else:
                raise Exception("api key []")

        return api_key

    def deal_PT_time(self, duration):
        try:
            duration_str = ""
            if "H" in duration and "M" in duration and "S" in duration:
                hour_list = re.compile('[\d]+H').findall(duration)
                hour = re.compile('[\d]+').findall(hour_list[0])
                minute_list = re.compile('[\d]+M').findall(duration)
                minute = re.compile('[\d]+').findall(minute_list[0])
                second_list = re.compile('[\d]+S').findall(duration)
                second = re.compile('[\d]+').findall(second_list[0])
                duration_str = "{}:{}:{}".format(hour[0], minute[0], second[0])

            elif "H" in duration and "M" in duration and "S" not in duration:
                hour_list = re.compile('[\d]+H').findall(duration)
                hour = re.compile('[\d]+').findall(hour_list[0])
                minute_list = re.compile('[\d]+M').findall(duration)
                minute = re.compile('[\d]+').findall(minute_list[0])
                duration_str = "{}:{}:00".format(hour[0], minute[0])

            elif "H" in duration and "M" not in duration and "S" in duration:
                hour_list = re.compile('[\d]+H').findall(duration)
                hour = re.compile('[\d]+').findall(hour_list[0])
                second_list = re.compile('[\d]+S').findall(duration)
                second = re.compile('[\d]+').findall(second_list[0])
                duration_str = "{}:00:{}".format(hour[0], second[0])

            elif "H" not in duration and "M" in duration and "S" in duration:
                minute_list = re.compile('[\d]+M').findall(duration)
                minute = re.compile('[\d]+').findall(minute_list[0])
                second_list = re.compile('[\d]+S').findall(duration)
                second = re.compile('[\d]+').findall(second_list[0])
                duration_str = "{}:{}".format(minute[0], second[0])

            elif "H" not in duration and "M" not in duration and "S" in duration:
                second_list = re.compile('[\d]+S').findall(duration)
                second = re.compile('[\d]+').findall(second_list[0])
                duration_str = "0:{}".format(second[0])

            elif "H" not in duration and "M" in duration and "S" not in duration:
                minute_list = re.compile('[\d]+M').findall(duration)
                minute = re.compile('[\d]+').findall(minute_list[0])
                duration_str = "{}:00".format(minute[0])

            elif "H" in duration and "M" not in duration and "S" not in duration:
                hour_list = re.compile('[\d]+H').findall(duration)
                hour = re.compile('[\d]+').findall(hour_list[0])
                duration_str = "{}:00:00".format(hour[0])

            return duration_str
        except Exception as e:
            print("{}_error: {}".format(duration, e))


    def deal_game_video(self, video_info):
        msg = call_insert_mysql(self.video_table, video_info)
        if msg["msg"] != "ok":
            print("--msg--:", video_info)


    def deal_youtube_info(self):
        """查询数据"""
        repeat_list = []
        json_info = {"table": self.game_table}
        game_list = call_query_mysql(json_info)
        for data in game_list:
            game_id, chain_id, game_name = data.get("id", 0), data.get("chainId", ""), data.get("gameName", "")
            if game_name not in repeat_list:
                repeat_list.append(game_name)
                print("{}--:{}".format(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), game_name))
                self.get_search_info(game_id, chain_id, game_name)
            else:
                continue


    def get_search_info(self, game_id, chain_id, name):
        #  PT3H33M6S   PT14M32S    PT46S
        try:
            max_results = 10
            api_key = self.random_api_key()
            after, before = "{}T00:00:00Z".format(self.day_time), "{}T23:59:00Z".format(self.day_time)
            search_url = "{}search?key={}&maxResults={}&part=id&type=video&q={}&publishedAfter={}&publishedBefore={}".format(self.api_uri, api_key, max_results, name, after, before)
            result = self.http_request(search_url, api_key)
            for items in result["items"]:
                video_id = items["id"]["videoId"]
                # https://www.youtube.com/watch?v=3OSUpTaiJM8
                # https://www.youtube.com/embed/3OSUpTaiJM8
                video = "https://www.youtube.com/embed/{}".format(video_id)
                video_api_key = self.random_api_key()
                video_info_url = "{}videos?id={}&part=snippet,contentDetails,statistics,topicDetails&key={}".format(self.api_uri, video_id, video_api_key)
                video_info = self.http_request(video_info_url, video_api_key)
                for item in video_info["items"]:
                    snippet, content_details = item["snippet"], item["contentDetails"]
                    statistics, thumbnails = item["statistics"], snippet["thumbnails"]
                    image = thumbnails.get("high", {}).get("url", "")
                    # 七牛云
                    image_url = Qiniu.get_upload_img_url(image)

                    publish_time = self.datetime_to_str(self.formatUTCtime(snippet.get("publishedAt", "")))
                    # 标题   频道ID
                    title, channel_id = snippet.get("title", ""), snippet.get("channelId", "")
                    # 描述      频道标题
                    description, channel_title = snippet.get("description", ""), snippet.get("channelTitle", "")
                    # 视频所属类别ID
                    category_id = snippet.get("categoryId", "")
                    # 视频时长
                    duration = self.deal_PT_time(content_details.get("duration", ""))
                    # 2d/3d
                    dimension = content_details.get("dimension", "")
                    # 清晰度/分辨率hd/sd
                    definition = content_details.get("definition", "")
                    # 观看      点赞
                    view_count, like_count = statistics.get("viewCount", ""), statistics.get("likeCount", "")
                    # 喜爱   评论
                    favorite_count, comment_count = statistics.get("favoriteCount", ""), statistics.get("commentCount", "")
                    # 点踩
                    dislike_count = statistics.get("dislikeCount", "")
                    print("{}_{}--:{}".format(game_id, name, datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
                    watch_info = {
                        "gameId": game_id, "chainId": chain_id, "gameName": name, "createTime": publish_time,
                        "introduction": title, "viewNum": view_count, "pic": image_url, "video": video,"duration": duration,
                        "updateTime": self.now_time, "likeNum": like_count, "unlikeNum": dislike_count
                    }
                    # print("--watch--:", watch_info)
                    self.deal_game_video(watch_info)
        except Exception as e:
            print("search_error: {}".format(e))
            ding(__file__)


def start_scheduler():
    you = YouTuBe()
    you.deal_youtube_info()


if __name__ == '__main__':
    # start_scheduler()
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    # 每天4点20分执行一次
    scheduler.add_job(start_scheduler, 'cron', hour=4, minute=20)
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
        scheduler.start()
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()










