from urllib import parse
import requests
import json
import yaml
import os
import parsel


class Following():

    def __init__(self):
        self.following_url = "https://twitter.com/i/api/graphql/f1mvfzNVYp5HAU_WKkPzKA/Following?variables=%7B%22userId%22%3A%22{}%22%2C%22count%22%3A20%2C%22{}includePromotedContent%22%3Afalse%2C%22withSuperFollowsUserFields%22%3Atrue%2C%22withDownvotePerspective%22%3Afalse%2C%22withReactionsMetadata%22%3Afalse%2C%22withReactionsPerspective%22%3Afalse%2C%22withSuperFollowsTweetFields%22%3Atrue%7D&features=%7B%22dont_mention_me_view_api_enabled%22%3Atrue%2C%22interactive_text_enabled%22%3Atrue%2C%22responsive_web_uc_gql_enabled%22%3Afalse%2C%22vibe_tweet_context_enabled%22%3Afalse%2C%22responsive_web_edit_tweet_api_enabled%22%3Afalse%2C%22standardized_nudges_misinfo%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D"
        self.followers_url = "https://twitter.com/i/api/graphql/_z6sGSDDIPpaqe2yabcioQ/Followers?variables=%7B%22userId%22%3A%22{}%22%2C%22count%22%3A20%2C%22{}includePromotedContent%22%3Afalse%2C%22withSuperFollowsUserFields%22%3Atrue%2C%22withDownvotePerspective%22%3Afalse%2C%22withReactionsMetadata%22%3Afalse%2C%22withReactionsPerspective%22%3Afalse%2C%22withSuperFollowsTweetFields%22%3Atrue%7D&features=%7B%22dont_mention_me_view_api_enabled%22%3Atrue%2C%22interactive_text_enabled%22%3Atrue%2C%22responsive_web_uc_gql_enabled%22%3Afalse%2C%22vibe_tweet_context_enabled%22%3Afalse%2C%22responsive_web_edit_tweet_api_enabled%22%3Afalse%2C%22standardized_nudges_misinfo%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D"
        self.headers = self.get_header_yml()
        self.agent_header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        }

    def get_header_yml(self):
        path = "{}\\{}".format(os.getcwd(), "config.yml")
        file = open(path, 'r', encoding="utf-8")
        file_data = file.read()
        file.close()
        # 指定Loader
        data = yaml.load(file_data, Loader=yaml.FullLoader)
        return data

    def guest_token(self):
        guest_url = "https://api.twitter.com/1.1/guest/activate.json"
        request = requests.post(url=guest_url, headers=self.headers)
        guest_token = request.json()['guest_token']
        return (guest_token)


    def get_user_rest_id(self, screen_name):
        guest_token = self.guest_token()
        guest_header = {"x-guest-token": guest_token}
        guest_header.update(self.headers)
        url = """https://twitter.com/i/api/graphql/mCbpQvZAw6zu_4PvuAUVVQ/UserByScreenName?variables=%7B%22screen_name%22%3A%22""" + screen_name + """%22%2C%22withSafetyModeUserFields%22%3Atrue%2C%22withSuperFollowsUserFields%22%3Atrue%7D"""
        response = requests.get(url, headers=guest_header)
        result = response.json()['data']["user"]["result"]
        return result["rest_id"]


    def get_following_entries(self, screen_name):
        rest_id = self.get_user_rest_id(screen_name)
        cursor, number = '', 0
        while True:
            if number < 2:
                if cursor:
                    cursor_info = """cursor%22%3A%22""" + parse.quote(cursor) + """%22%2C%22"""
                else:
                    cursor_info = cursor
                res = requests.get(self.following_url.format(rest_id, cursor_info), headers=self.headers)
                result = json.loads(res.text)
                timeline = result["data"]["user"]["result"]["timeline"]
                instructions = timeline['timeline']["instructions"]
                num = 0
                for index, data in enumerate(instructions):
                    if "entries" in data:
                        if len(data["entries"]) > 3:
                            num = index

                entries = instructions[num]["entries"]
                if len(entries) < 3:
                    break
                print("len------------: {}".format(len(entries)))
                for entry in entries:
                    if "itemContent" in entry["content"]:
                        user_results = entry["content"]["itemContent"]["user_results"]
                        legacy = user_results["result"]["legacy"]
                        name, screen_name = legacy["name"], legacy["screen_name"]
                        description = legacy["description"]
                        print("{}--{}--{}".format(name, screen_name, description))
                    else:
                        continue
                cursor = entries[len(entries) - 2]["content"]["value"]
                number = number + 1
            else:
                break

    def get_followers_entries(self, screen_name):
        rest_id = self.get_user_rest_id(screen_name)
        cursor, number = '', 0
        while True:
            if number < 2:
                if cursor:
                    cursor_info = """cursor%22%3A%22""" + parse.quote(cursor) + """%22%2C%22"""
                else:
                    cursor_info = cursor
                res = requests.get(self.followers_url.format(rest_id, cursor_info), headers=self.headers)
                result = json.loads(res.text)
                timeline = result["data"]["user"]["result"]["timeline"]
                instructions = timeline['timeline']["instructions"]
                num = 0
                for index, data in enumerate(instructions):
                    if "entries" in data:
                        if len(data["entries"]) > 3:
                            num = index
                entries = instructions[num]["entries"]
                if len(entries) < 3:
                    break
                print("len------------: {}".format(len(entries)))
                for entry in entries:
                    if "itemContent" in entry["content"]:
                        user_results = entry["content"]["itemContent"]["user_results"]
                        legacy = user_results["result"]["legacy"]
                        name, screen_name = legacy["name"], legacy["screen_name"]
                        description = legacy["description"]
                        print("{}--{}--{}".format(name, screen_name, description))
                    else:
                        continue
                cursor = entries[len(entries)-2]["content"]["value"]
                number = number + 1
            else:
                break

    def get_discord_info(self, discord_name):
        url = "https://discord.com/api/v9/invites/{}?with_counts=true&with_expiration=true".format(discord_name)
        self.agent_header.update({"Authorization": "ODQ5NTIxMjQ0MTk4MTQxOTg3.YaHPXg.7cgEH69QB7NyHSJpde9B81BJKM8"})
        res = requests.get(url=url, headers=self.agent_header)
        result = json.loads(res.text)
        code = result["code"]
        # 在线人数  总成员
        member_count, presence_count = result["approximate_presence_count"], result["approximate_member_count"]
        # print("--result--:", code, member_count, presence_count)
        return member_count, presence_count


    def get_telegram_info(self, telegram_name):
        url = "https://t.me/{}".format(telegram_name)
        # url = "https://t.me/SecondLiveCommunity"
        res = requests.get(url=url, headers=self.agent_header)
        result = res.text
        html_xml = parsel.Selector(result)
        page_extra = html_xml.xpath('.//div[@class="tgme_page_extra"]/text()').extract_first()
        members, online = 0, 0
        if page_extra.find('members') != -1 and page_extra.find('online') != -1:
            extra_list = page_extra.split(",")
            one, two = extra_list[0], extra_list[1]
            members = one[:one.find('members')].replace(" ", "")
            online = two[:two.find('online')].replace(" ", "")
        elif page_extra.find('subscribers') != -1:
            members = page_extra[:page_extra.find('subscribers')].replace(" ", "")
        # print("--page_extra--:", members, online)
        return members, online


if __name__ == '__main__':
    screen_name = "elonmusk"
    fol = Following()
    fol.get_following_entries(screen_name)


