from urllib import parse
import requests
import json
from datetime import datetime


class UserTweets():

    def __init__(self):
        self.url = "https://twitter.com/i/api/graphql/ltnTUBKlkqoAuuV9JnJFyg/UserTweets?variables=%7B%22userId%22%3A%22{}%22%2C%22count%22%3A40%2C%22{}includePromotedContent%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withSuperFollowsUserFields%22%3Atrue%2C%22withDownvotePerspective%22%3Afalse%2C%22withReactionsMetadata%22%3Afalse%2C%22withReactionsPerspective%22%3Afalse%2C%22withSuperFollowsTweetFields%22%3Atrue%2C%22withVoice%22%3Atrue%2C%22withV2Timeline%22%3Atrue%2C%22__fs_dont_mention_me_view_api_enabled%22%3Afalse%2C%22__fs_interactive_text_enabled%22%3Atrue%2C%22__fs_responsive_web_uc_gql_enabled%22%3Afalse%7D"
        self.url_token = 'https://api.twitter.com/1.1/guest/activate.json'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'x-guest-token': '',
            'x-twitter-client-language': 'zh-cn',
            'x-twitter-active-user': 'yes',
            'x-csrf-token': 'b4b7466770287523c3dd07a1918bda30773bedecc7f6f28d2cfcaba14a2c7cf383181fc0ec80abe687b06121ae9bfa1b886c2b42f726bc4d6c11caaf1ccf69f9ed5d5709cdf634aec8c155ee27471f65',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Referer': 'https://twitter.com/',
            'Connection': 'keep-alive',
        }
        self.tokens = self.getToken_one()
        self.guest_token = self.get_token()

    def getToken_one(self):
        token = ""
        request = requests.get("https://abs.twimg.com/responsive-web/client-web/main.70645c85.js")
        text_block = request.text
        action_refresh_section = text_block[text_block.index('a="ACTION_REFRESH"'):]
        sections = action_refresh_section.split(',')
        for section in sections:
            if section[0:2]=='s=':
                token = parse.unquote(section[3:-1])
                break
        return(token)


    def get_token(self):
        request = requests.post("https://api.twitter.com/1.1/guest/activate.json", headers={"Authorization":'Bearer ' +self.tokens})
        token = request.json()['guest_token']
        return token

    def update_headers_info(self):
        self.headers.update({"Authorization":'Bearer '+ self.tokens,"x-guest-token":self.guest_token})


    def get_user_rest_id(self, screen_name):
        headers = {"Authorization": 'Bearer ' + self.tokens, "x-guest-token": self.guest_token}
        url = """https://twitter.com/i/api/graphql/7mjxD3-C6BxitPMVQ6w0-Q/UserByScreenName?variables=%7B%22screen_name%22%3A%22""" + screen_name + """%22%2C%22withSafetyModeUserFields%22%3Atrue%2C%22withSuperFollowsUserFields%22%3Atrue%7D"""
        request = requests.get(url, headers=headers)
        return (request.json()['data']["user"]["result"]["rest_id"])


    def deal_user_instructions(self, rest_id):
        try:
            self.update_headers_info()
            cursor = ''
            while True:
                if cursor:
                    cursor_info = """cursor%22%3A%22"""+parse.quote(cursor)+"""%22%2C%22"""
                else:
                    cursor_info = cursor
                res = requests.get(self.url.format(rest_id, cursor_info), headers=self.headers)
                # res = requests.get(self.url, headers=self.headers)
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
                        retweet = content["content"]["itemContent"]["tweet_results"]["result"]["legacy"]
                        if "retweeted_status_result" in retweet:
                            legacy = retweet["retweeted_status_result"]["result"]["legacy"]

                        else:
                            legacy = retweet
                        reply_count, retweet_count, favorite_count = legacy["reply_count"], legacy["retweet_count"], legacy["favorite_count"]
                        publish_time, full_text = datetime.strptime(legacy.get("created_at", ""),"%a %b %d %H:%M:%S +0000 %Y"), legacy['full_text']
                        print("--full_text--", full_text)
                        entities = legacy.get("extended_entities", {}).get("media", {})
                        video_url, media_url = "", ""

                        if entities:
                            media = entities[0]
                            media_url, variants = media.get("media_url_https", ""), media.get("video_info", {}).get(
                                "variants", [])
                            # 视频
                            if variants:
                                number = 0
                                for data in variants:
                                    if "bitrate" in data:
                                        bitrate = data["bitrate"]
                                        if bitrate > number:
                                            number = bitrate
                                            video_url = data["url"]
                    else:
                        continue
                # for s in entries:
                #     print("--s--", s)
                next = timeline.get('timeline', {}).get('instructions', [])
                if len(next) > 1:
                    cursor = next[-1].get('entries', [{}])[-1].get('content', {}).get('value', '')
                else:
                    cursor = next[0].get('entries', [{}])[-1].get('content', {}).get('value', '')
                print("--cursor--", cursor)
                if not cursor:
                    cursor = ''
        except Exception as e:
            print(e)


if __name__ == '__main__':
    screen_name = "SecondLiveReal"
    rest_id = ""
    user = UserTweets()
    # rest_id = user.get_user_rest_id(screen_name)
    # print("--rest_id--", rest_id)
    # user.deal_user_instructions(rest_id)
    user.deal_user_instructions(rest_id)
