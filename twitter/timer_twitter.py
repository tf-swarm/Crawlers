from urllib import parse
import requests
import json
from datetime import datetime
from lib.call_mysql import call_insert_mysql,call_query_mysql
from lib.qiniu_upload import Qiniu
# from ubuntu.gamefi.liunx.qiniu_upload import Qiniu


class Twitter():
    def __init__(self):
        self.now_time = self.datetime_to_str(datetime.now())
        self.user_table = "t_influencers"
        self.article_table = "t_influencers_article"
        self.tokens = self.getToken_one()
        self.guest_token = self.getToken_two(self.tokens)
        self.user_url = """https://api.twitter.com/graphql/4S2ihIKfF3xhp-ENxvUAfQ/UserByScreenName?variables=%7B%22screen_name%22%3A%22{}%22%2C%22withHighlightedLabel%22%3Atrue%7D"""
        self.tweets_url = "https://twitter.com/i/api/graphql/ltnTUBKlkqoAuuV9JnJFyg/UserTweets?variables=%7B%22userId%22%3A%22{}%22%2C%22count%22%3A40%2C%22{}includePromotedContent%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withSuperFollowsUserFields%22%3Atrue%2C%22withDownvotePerspective%22%3Afalse%2C%22withReactionsMetadata%22%3Afalse%2C%22withReactionsPerspective%22%3Afalse%2C%22withSuperFollowsTweetFields%22%3Atrue%2C%22withVoice%22%3Atrue%2C%22withV2Timeline%22%3Atrue%2C%22__fs_dont_mention_me_view_api_enabled%22%3Afalse%2C%22__fs_interactive_text_enabled%22%3Atrue%2C%22__fs_responsive_web_uc_gql_enabled%22%3Afalse%7D"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'x-twitter-client-language': 'zh-cn',
            'x-twitter-active-user': 'yes',
            'x-csrf-token': 'b4b7466770287523c3dd07a1918bda30773bedecc7f6f28d2cfcaba14a2c7cf383181fc0ec80abe687b06121ae9bfa1b886c2b42f726bc4d6c11caaf1ccf69f9ed5d5709cdf634aec8c155ee27471f65',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Referer': 'https://twitter.com/',
            'Connection': 'keep-alive',
        }


    def getToken_one(self):
        token = ""
        request = requests.get("https://abs.twimg.com/responsive-web/client-web/main.ac08d185.js")
        text_block = request.text
        action_refresh_section = text_block[text_block.index('a="ACTION_REFRESH"'):]
        sections = action_refresh_section.split(',')
        for section in sections:
            if section[0:2]=='s=':
                token = parse.unquote(section[3:-1])
                break
        return(token)


    def getToken_two(self, tokens):
        url = "https://api.twitter.com/1.1/guest/activate.json"
        headers = {"Authorization":'Bearer '+tokens}
        request = requests.post(url=url, headers=headers)
        token = request.json()['guest_token']
        return(token)

    def datetime_to_str(self, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)

    def update_headers_info(self):
        self.headers.update({"Authorization":'Bearer '+ self.tokens,"x-guest-token":self.guest_token})

    def deal_user_info(self):
        """查询数据"""
        json_info = {"table": self.user_table}
        game_list = call_query_mysql(json_info)
        for data in game_list:
            g_id, source_url = data.get("id", 0), data.get("sourceUrl", "")
            if len(source_url.split("/")) > 3:
                screen_name = source_url.split("/")[3]
                self.get_twitter_user_data(g_id, screen_name)


    def get_twitter_user_data(self, g_id, screen_name):
        """用户数据"""
        try:
            headers = {"Authorization": 'Bearer ' + self.tokens, "x-guest-token": self.guest_token}
            res = requests.get(self.user_url.format(screen_name), headers=headers)
            result = json.loads(res.text)['data']
            if "user" in result:
                legacy = result["user"]["legacy"]
                rest_id = result["user"]["rest_id"]
                created_at = datetime.strptime(legacy.get("created_at", ""), "%a %b %d %H:%M:%S +0000 %Y")
                register_time = self.datetime_to_str(created_at)
                # 头像
                user_image = legacy.get("profile_image_url_https", "")
                # 七牛云处理
                logo_url = Qiniu.get_upload_img_url(user_image)
                # 关注          跟随者
                friends_count, followers_count = legacy.get("friends_count", 0), legacy.get("followers_count", 0)
                search_info = {
                    "id": g_id, "settledTime": register_time, "updateTime": self.now_time, "logo": logo_url,
                    "followNum": friends_count, "beFollowedNum": followers_count, "sourceType": "twitter"
                }
                print("{}--{}".format(screen_name, datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
                call_insert_mysql(self.user_table, search_info)
                self.deal_user_instructions(g_id, rest_id)
        except Exception as e:
            print("twitter_user {}".format(e))



    def deal_user_instructions(self, g_id, rest_id):
        """用户推文"""
        try:
            self.update_headers_info()
            cursor = ''
            for tw in range(1): # 0 1
                if cursor:
                    cursor_info = """cursor%22%3A%22"""+parse.quote(cursor)+"""%22%2C%22"""
                else:
                    cursor_info = cursor
                res = requests.get(self.tweets_url.format(rest_id, cursor_info), headers=self.headers)
                result = json.loads(res.text)
                timeline = result['data']['user']['result']['timeline_v2']
                instructions = timeline['timeline']["instructions"]
                num = 0
                for index,data in enumerate(instructions):
                    if "entries" in data:
                        if len(data["entries"]) > 3:
                            num = index
                        else:
                            continue
                    else:
                        continue
                entries = instructions[num]["entries"]
                if len(entries) < 3:
                    break

                for s, content in enumerate(entries):
                    if "itemContent" in content["content"]:
                        video_url, pic_url = "", ""
                        retweet = content["content"]["itemContent"]["tweet_results"]["result"]["legacy"]
                        if "retweeted_status_result" in retweet:
                            legacy = retweet["retweeted_status_result"]["result"]["legacy"]
                        else:
                            legacy = retweet
                        # 转推
                        retweet_count = int(legacy["retweet_count"]) + int(legacy["quote_count"])
                        reply_count, favorite_count = legacy["reply_count"], legacy["favorite_count"]
                        created_at, full_text = datetime.strptime(legacy.get("created_at", ""),"%a %b %d %H:%M:%S +0000 %Y"), legacy['full_text']
                        publish_time = self.datetime_to_str(created_at)
                        conversation_id = legacy["id_str"] # rest_id
                        # print("--conversation_id--", conversation_id, legacy)
                        entities = legacy.get("extended_entities", {}).get("media", {})
                        if entities:
                            media = entities[0]
                            media_url, variants = media.get("media_url_https", ""), media.get("video_info", {}).get("variants", [])
                            # 七牛云处理
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
                        article_info = {
                            "influencersId": g_id, "content": full_text, "pic": pic_url, "video": video_url,
                            "createTime": publish_time, "updateTime": self.now_time, "likeNum": favorite_count,
                            "reply": reply_count, "retweet": retweet_count, "conversationId": conversation_id,
                        }
                        # self.deal_article_info(article_info)
                    else:
                        continue
                next = timeline.get('timeline', {}).get('instructions', [])
                if len(next) > 1:
                    cursor = next[-1].get('entries', [{}])[-1].get('content', {}).get('value', '')
                else:
                    cursor = next[0].get('entries', [{}])[-1].get('content', {}).get('value', '')
                if not cursor:
                    cursor = ''
        except Exception as e:
            print(e)


    def deal_article_info(self, search_info):
        conversation_id = search_info["conversationId"]
        msg = call_insert_mysql(self.article_table, search_info)
        if msg["msg"] != "ok":
            print("--11--:", conversation_id)


if __name__ == '__main__':
    tw = Twitter()
    g_id, screen_name = 745, "elonmusk" #"HeroGalaxyNFT"  elonmusk
    tw.get_twitter_user_data(g_id, screen_name)


