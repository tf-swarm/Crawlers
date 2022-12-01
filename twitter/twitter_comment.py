import sys

sys.path.append('..')
import requests
from urllib import parse
import json
import time
from datetime import datetime
from liunx.call_mysql import call_query_mysql, call_insert_mysql
from liunx.qiniu_upload import Qiniu
# from ubuntu.gamefi.liunx.qiniu_upload import Qiniu


class SearchTwitter():

    def __init__(self):
        self.url = "https://twitter.com/i/api/2/search/adaptive.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&include_ext_has_nft_avatar=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_quote_count=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&include_ext_media_availability=true&include_ext_sensitive_media_warning=true&include_ext_trusted_friends_metadata=true&send_error_codes=true&simple_quoted_tweet=true&q={}&count=20&query_source=typed_query&cursor={}&pc=1&spelling_corrections=1&ext=mediaStats%2ChighlightedLabel%2ChasNftAvatar%2CvoiceInfo%2Cenrichments%2CsuperFollowMetadata"
        self.game_table = "t_game_list"
        self.comment_table = "t_game_comment"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'x-guest-token': '',
            'x-twitter-client-language': 'zh-cn',
            'x-twitter-active-user': 'yes',
            'x-csrf-token': '25ea9d09196a6ba850201d47d7e75733',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Referer': 'https://twitter.com/',
            'Connection': 'keep-alive',
        }

    def getToken_one(self):
        token = ""
        request = requests.get("https://abs.twimg.com/responsive-web/client-web/main.52d59a45.js")
        text_block = request.text
        action_refresh_section = text_block[text_block.index('a="ACTION_REFRESH"'):]
        sections = action_refresh_section.split(',')
        for section in sections:
            if section[0:2]=='s=':
                token = parse.unquote(section[3:-1])
                break
        return(token)


    def get_token(self):
        tokens = self.getToken_one()
        request = requests.post("https://api.twitter.com/1.1/guest/activate.json", headers={"Authorization":'Bearer ' +tokens})
        token = request.json()['guest_token']
        self.headers.update({"Authorization":'Bearer '+ tokens,"x-guest-token":token})


    def formate_time_stamp(self, time_):
        return int(time.mktime(time.strptime(time_, "%Y-%m-%d")))

    def stamp_formate_time(self, time_):
        return time.strftime("%Y-%m-%d", time.localtime(int(time_)))

    def datetime_to_str(self, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)

    def deal_query_info(self):
        """查询数据"""
        deal_list = []
        json_info = {"table": self.game_table}
        game_list = call_query_mysql(json_info)
        for data in game_list:
            g_id, names = data.get("id", 0), data.get("gameName", "")
            if names not in deal_list:
                deal_list.append(names)
                self.deal_global_info(g_id, names, 1)
            else:
                continue


    def deal_global_info(self, game_id, search_name, page=None):
        tweet_list, num = [], 0
        now_time = self.datetime_to_str(datetime.now())
        self.get_token()
        try:
            cursor = ''
            while True:
                if num > 500:
                    self.get_token()
                    num = 0
                num += 1
                res = requests.get(url=self.url.format(parse.quote(search_name), parse.quote(cursor)), headers=self.headers)
                root = json.loads(res.text)
                tweets = root['globalObjects']['tweets']
                users = root['globalObjects']['users']
                if page:
                    if num > page:
                        break

                if not tweets and not users:
                    break
                # print("{}--{}--{}--:".format(game_id, len(tweets), datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
                for tw in tweets.values():
                    # conversation_id_str
                    # 回复          喜欢
                    reply_count, favorite_count = tw["reply_count"], tw["favorite_count"]
                    # 转推
                    retweet_count = int(tw["retweet_count"]) + int(tw["quote_count"])
                    publish_time, full_text, user_id = self.datetime_to_str(datetime.strptime(tw.get("created_at", ""), "%a %b %d %H:%M:%S +0000 %Y")), tw['full_text'], tw['user_id_str']
                    conversation_id = tw["id_str"]
                    entities = tw.get("extended_entities", {}).get("media", {})
                    video_url, pic_url, background_url, logo_url = "", "", "", ""

                    if entities:
                        media = entities[0]
                        media_url, variants = media.get("media_url_https", ""), media.get("video_info", {}).get("variants", [])
                        if media_url:
                            pic_url = Qiniu.get_upload_img_url(media_url)
                        # 视频
                        if variants:
                            number = 0
                            for data in variants:
                                if "bitrate" in data:
                                    bitrate = data["bitrate"]
                                    if bitrate > number:
                                        number = bitrate
                                        video_url = data["url"]

                    legacy = users[user_id]
                    register_time = self.datetime_to_str(datetime.strptime(legacy.get("created_at", ""), "%a %b %d %H:%M:%S +0000 %Y"))
                    # 简介        头像
                    description, user_image = legacy.get("description", ""), legacy.get("profile_image_url_https","")
                    # 七牛云处理
                    if user_image:
                        logo_url = Qiniu.get_upload_img_url(user_image)
                    name, screen = legacy.get("name", ""), legacy.get("screen_name", "")
                    # 关注          跟随者            收藏
                    friends_count, followers_count, favourites_count = legacy.get("friends_count", 0), legacy.get("followers_count", 0), legacy.get("favourites_count", 0)

                    # Telegram, Discord = legacy.get("Telegram", ""), legacy.get("Discord", "")
                    # profile_banner_url
                    official_url, banner_url, location = legacy.get("url", ""), legacy.get("profile_banner_url", ""), legacy.get("location", "")
                    if banner_url:
                        background_url = Qiniu.get_upload_img_url(banner_url)
                    # print("--legacy--", type(register_time), type(publish_time), type(now_time))
                    search_info = {
                        "gameId": game_id, "userName": screen, "userLogo": logo_url, "userIntro": description, "userTime": register_time,
                        "userConcernNum": friends_count, "userFollowNum": followers_count, "user_collect_num": favourites_count, "website": official_url,
                        "background": background_url, "content": full_text, "pic": pic_url, "video": video_url, "createTime": publish_time, "updateTime": now_time,
                        "reply": reply_count, "likeNum": favorite_count, "retweet": retweet_count, "conversationId": conversation_id
                    }
                    self.deal_legacy_info(search_info)

                next = root.get('timeline', {}).get('instructions', [])
                if len(next) > 1:
                    content = next[-1].get('replaceEntry', {}).get('entry', {})
                else:
                    content = next[0].get('addEntries', {}).get('entries', [{}])[-1]
                cursor = content.get('content', {}).get('operation',{}).get('cursor',{}).get('value', '')
                if not cursor:
                    cursor = ''
        except Exception as e:
            print(e)


    def deal_legacy_info(self, search_info):
        msg = call_insert_mysql(self.comment_table, search_info)
        if msg["msg"] != "ok":
            print("--insert--:", search_info["conversationId"])


if __name__ == '__main__':
    t = SearchTwitter()
    t.deal_query_info()
