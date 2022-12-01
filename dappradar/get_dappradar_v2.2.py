import random
from playwright.sync_api import sync_playwright
import time
import requests
import json

class DappRadar():

    def __init__(self):
        self.cook_sec = self.get_cookie_info()


    def get_browser_category(self):
        playwright = sync_playwright().start()
        for index in range(1, 2):
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()
            url = "https://dappradar.com/rankings/category/games/{}".format(index)
            page.on('response', self.on_response)
            page.goto(url, timeout = 0)
            time.sleep(10)
            browser.close()
        playwright.stop()


    def on_response(self, response):
        if '/api/dapps' in response.url and response.status == 200:
            dap_list = response.json()["dapps"]
            for data in dap_list:
                deepLink = data.get("deepLink", "")
                if "https://dappradar.com/deeplink" in deepLink:
                    statistic_list, chart_list = ["day", "week", "month"], ["week", "month"]
                    game_name, slug = data.get("name", ""), data.get("slug", "")
                    protocols, category = data.get("protocols", []), data.get("category", "")
                    logo_url, statistic = data.get("logo", ""), data.get("statistic", {})
                    # 24小时
                    total_balance_in_fiat = statistic.get("totalBalanceInFiat", 0)
                    total_volume_in_fiat = statistic.get("totalVolumeInFiat", 0)
                    user_activity, changes = statistic.get("userActivity", 0), statistic.get("changes", {})
                    dau = changes.get("dau", {}).get("status", "")
                    print("----{}----".format(game_name))
                    if len(protocols) > 1:
                        multi_url = "/{}/{}/{}".format("multichain", category, slug)
                    else:
                        multi_url = "/{}/{}/{}".format(protocols[0], category, slug)
                    for stat_time in statistic_list:
                        time.sleep(random.randint(2, 5))
                        stat_url = multi_url + "/statistic/{}?currency=USD".format(stat_time)
                        currency = self.get_request_info(stat_url, self.cook_sec)
                        # USERS
                        users, users_change = currency.get("userActivity", 0), currency.get("userActivityChange", 0)
                        # TRANSACTIONS
                        transaction, transaction_change = currency.get("transactionCount", 0),  currency.get("transactionChange", 0)
                        # VOLUME
                        total_volume, total_volume_change = currency.get("totalVolumeInFiat", 0), currency.get("totalVolumeChangeInFiat", 0)
                        # BALANCE
                        total_balance, total_balance_change = currency.get("totalBalanceInFiat", 0),currency.get("totalBalanceChangeInFiat", 0)
                        # "usd"
                        balance, coin_name = currency.get("balance", 0), currency.get("coinName", "")
                        currency_info = {
                            "userActivity": users, "userActivityChange": users_change, "transactionCount": transaction,
                            "transactionChange": transaction_change,"totalVolumeInFiat": total_volume,
                            "totalVolumeChangeInFiat": total_volume_change, "totalBalanceInFiat":total_balance,
                            "totalBalanceChangeInFiat": total_balance_change, "balance": balance, "coinName": coin_name
                        }
                        print("--{}---{}:".format(stat_time, currency_info))

                    for chart_time in chart_list:
                        time.sleep(random.randint(2, 5))
                        chart_url = multi_url + "/chart/{}?currency=USD".format(chart_time)
                        charts = self.get_request_info(chart_url, self.cook_sec)
                        x_axis, series = charts.get("xaxis", []), charts.get("series", [])
                        chart_info = {"x_axis": x_axis, "series": series}
                        print("--{}---{}:".format(chart_time, chart_info))
                else:
                    continue
                break


    def get_request_info(self, url, cookie):
        result = {}
        cook_sec = "cook-sec-dr={}".format(cookie)
        try:
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                "Cookie": cook_sec,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            }
            href_url = "https://dappradar.com/v2/api/dapp{}".format(url)
            request = requests.get(href_url, headers=headers, timeout=10)
            result = json.loads(request.text)
            return result
        except Exception as e:
            print("request {} error {}".format(url, e))
            return result


    def get_cookie_info(self):
        cook_sec = ""
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        page.goto('https://dappradar.com/multichain/games/axie-infinity')
        try:
            cookies = context.cookies()
            page.wait_for_timeout(15000)
            for data in cookies:
                name = data["name"]
                # print("data--:", data)
                if name == "cook-sec-dr":
                    cook_sec = data["value"]
                else:
                    continue
            context.close()
            browser.close()
            playwright.stop()
            print("cook-sec-dr:", cook_sec)
            return cook_sec
        except Exception as e:
            print("Error in playwright {}.".format(e))
            context.close()
            browser.close()
            playwright.stop()



if __name__ == '__main__':
    dap = DappRadar()
    dap.get_browser_category()