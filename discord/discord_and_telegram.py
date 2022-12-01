import requests
import json
import parsel


def get_discord_info(discord_name):
    agent_header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    }
    url = "https://discord.com/api/v9/invites/{}?with_counts=true&with_expiration=true".format(discord_name)
    agent_header.update({"Authorization": "ODQ5NTIxMjQ0MTk4MTQxOTg3.YaHPXg.7cgEH69QB7NyHSJpde9B81BJKM8"})
    res = requests.get(url=url, headers=agent_header)
    result = json.loads(res.text)
    code = result["code"]
    # 在线人数  总成员
    member_count, presence_count = result["approximate_presence_count"], result["approximate_member_count"]
    # print("--result--:", code, member_count, presence_count)
    return member_count, presence_count


def get_telegram_info(telegram_name):
    agent_header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    }
    url = "https://t.me/{}".format(telegram_name)
    # url = "https://t.me/SecondLiveCommunity"
    res = requests.get(url=url, headers=agent_header)
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