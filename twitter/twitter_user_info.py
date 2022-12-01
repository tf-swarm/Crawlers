import requests
from urllib import parse
import json
from datetime import datetime
from liunx.qiniu_upload import Qiniu

class UserByScreenName():

    def __init__(self):
        self.token_one = self.getToken_one()
        self.token_two = self.getToken_two(self.token_one)

    def datetime_to_str(self, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)

    def getToken_one(self):
        token = ""
        request = requests.get("https://abs.twimg.com/responsive-web/client-web/main.a8574df5.js")
        text_block = request.text
        action_refresh_section = text_block[text_block.index('i="ACTION_REFRESH"'):]
        sections = action_refresh_section.split(',')
        for section in sections:
            if section[0:2]=='a=':
                token = parse.unquote(section[3:-1])
                break
        return(token)


    def getToken_two(self, tokens):
        request = requests.post("https://api.twitter.com/1.1/guest/activate.json", headers={"Authorization":'Bearer '+tokens})
        token = request.json()['guest_token']
        return (token)


    def getUserRestID(self, screen_name, token_one, token_two):
        variables = {'variables':json.dumps({'screen_name':screen_name,'withHighlitedLabel':True})}
        headers = {"Authorization":'Bearer '+ token_one,"x-guest-token":token_two}
        url = """https://api.twitter.com/graphql/4S2ihIKfF3xhp-ENxvUAfQ/UserByScreenName?variables=%7B%22screen_name%22%3A%22"""+screen_name+"""%22%2C%22withHighlightedLabel%22%3Atrue%7D"""
        request = requests.get(url, headers=headers)
        return(request.json()['data'])


    def getTweets(self, screen_name):
        # "https://pbs.twimg.com/profile_images/1454807122210816000/aGorBtwv_200x200.jpg"
        # "https://pbs.twimg.com/profile_images/1454807122210816000/aGorBtwv_normal.jpg"
        user_info = {}
        result = self.getUserRestID(screen_name, self.token_one, self.token_two)
        legacy = result["user"]["legacy"]
        created_at = datetime.strptime(legacy.get("created_at", ""), "%a %b %d %H:%M:%S +0000 %Y")
        register_time = self.datetime_to_str(created_at)

        # print("--create_time--", create_time)
        description, profile_image = legacy.get("description", ""), legacy.get("profile_image_url_https", "")
        # 七牛云处理
        image_url = profile_image.replace("_normal", "_200x200")
        # logo_url = Qiniu.get_upload_img_url(image_url)

        # print("--description--", description, profile_image)
        name, screen = legacy.get("name", ""), legacy.get("screen_name", "") # @WemixNetwork
        # print("--name--", name, screen)
        friends_count, followers_count, favourites_count = legacy.get("friends_count", 0),legacy.get("followers_count", 0),legacy.get("favourites_count", 0)
        # print("--count--", friends_count, followers_count)
        Telegram, Discord = legacy.get("Telegram", ""), legacy.get("Discord", "")
        # print("--Discord--", Telegram, Discord)
        url, banner_url, location = legacy.get("url", ""),legacy.get("profile_banner_url", ""),legacy.get("location", "")

        rest_id = result["user"].get("rest_id", "")

        # for key, value in legacy.items():
        #     print("--user--", key, value )]

        user_info.update({
            "rest_id": rest_id, "name": name, "create_time": register_time, "description": description, "logo_url": image_url,
            "following": friends_count, "followers": followers_count, "telegram": Telegram, "discord": Discord,
            "website_url": url, "background_url": banner_url, "location": location
        })
        return user_info


twitter_user = UserByScreenName()