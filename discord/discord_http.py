import requests
import urllib.request
import json
import datetime
import time

class DiscordHttp():

    def __init__(self):
        now_stamp = self.str_to_timestamp(str(datetime.date.today()) + " 00:00:00")

    def str_to_timestamp(self, s, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        t = datetime.datetime.strptime(s, fmt).timetuple()
        return int(time.mktime(t))

    def get_ip(self):
        IPA = urllib.request.urlopen('https://checkip.amazonaws.com').read().decode('utf8')
        print(f"ready at {IPA}")
        return IPA

    def get_channel_message(self):
        now_stamp = self.str_to_timestamp(str(datetime.date.today()) + " 00:00:00")
        channel_id = '608495101374758944'
        all_messages, limit = [], 100
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "authorization": "ODQ5NTIxMjQ0MTk4MTQxOTg3.GcHiPk.MWmA3931BoyQyPFylKpE86jPPNoso6ocGjFAwo"
        }
        url = "https://discord.com/api/v9/channels/{}/messages?limit={}".format(channel_id, limit)
        res = requests.get(url=url, headers=headers)
        json_info = json.loads(res.text)
        for discord in json_info:
            discord_id = discord.get("id", "")
            content = discord.get("content", "")
            timestamp = discord.get("timestamp", "")
            print("--discord--:", discord_id, timestamp)
        # all_messages.extend(json_info)
        # while len(r.json()) == LIMIT:
        #     last_message_id = r.json()[-1].get('id')
        #     r = requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages?limit={LIMIT}&before={last_message_id}',headers=HEADERS)
        #     all_messages.extend(r.json())
        #     print(f'len(r.json()) is {len(r.json())} and last_message_id is {last_message_id} and len(all_messages) is {len(all_messages)}')



if __name__ == '__main__':
    disc = DiscordHttp()
    disc.get_channel_message()


