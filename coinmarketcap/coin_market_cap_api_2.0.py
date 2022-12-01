from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import time
import random
import requests
import re
from datetime import datetime, timedelta
from influencers.twitter_user_info import twitter_user
from bs4 import BeautifulSoup


class APITimer(object):

    def __init__(self):
        self.__t = time.time()

    def reset(self):
        self.__t = time.time()

    @property
    def elapsed(self):
        return time.time() - self.__t


class CoinMarketCapAPIError(Exception):

    def __init__(self, r):
        super(CoinMarketCapAPIError, self).__init__(repr(r))
        self.rep = r


class Response(object):

    def __init__(self, resp, timer):
        self.__payload = json.loads(resp.text)
        self.__timer = timer
        self._message = self.__payload.get('message', None)
        self._error = self.__payload.get('error', None)
        self._statusCode = self.__payload.get('statusCode', None)
        if self._message and self._error and self._statusCode:
            self.status = {
                'error_code': self._statusCode,
                'error_message': self._message,
            }
        else:
            self.status = self.__payload.get('status', {})

        self.data = self.__payload.get('data', {})
        self.timestamp = self.status.get('timestamp', None)
        self.error_code = self.status.get('error_code', None)
        self.error_message = self.status.get('error_message', None)
        self.error = True if self.error_code and self.error_message else False
        self.ok = False if self.error else True
        self.elapsed = self.status.get('elapsed', None)
        self.credit_count = self.status.get('credit_count', None)
        self.__time_snap = timer.elapsed


class GameMarket():

    def __init__(self):
        self.base_url = 'https://pro-api.coinmarketcap.com/v1'
        self.headers = {
            "Content-type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        }


    def formatUTCtime(self, timestamp):
        utc_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        utc_date = datetime.strptime(timestamp, utc_format) + timedelta(hours=8)
        return utc_date

    def datetime_to_str(self, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)


    def api_coin_market_cap(self, url, **kwargs):
        api_key = self.get_api_key()
        timer = APITimer()
        api_url = '{}{}'.format(self.base_url, url)
        self.headers.update({"X-CMC_PRO_API_KEY": api_key})
        session = Session()
        session.headers.update(self.headers)
        try:
            response = session.get(api_url, params=kwargs)
            rep = Response(response, timer)
            if rep.error:
                raise CoinMarketCapAPIError(rep)
            return rep
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
            raise e


    def get_api_key(self):
        new_list = []
        key_list = [] # 申请的api_key列表
        while True:
            api_key = random.sample(key_list, 1)[0]
            url = 'https://pro-api.coinmarketcap.com/v1/key/info'
            self.headers.update({"X-CMC_PRO_API_KEY": api_key})
            session = Session()
            session.headers.update(self.headers)
            try:
                response = session.get(url)
                result = json.loads(response.text)["data"]
                credits_left = result["usage"]["current_day"]["credits_left"]
                if credits_left > 0:
                    print("credits_left--:", credits_left)
                    break
                else:
                    if len(new_list) != len(key_list):
                        if api_key not in new_list:
                            new_list.append(api_key)
                        else:
                            continue
                    else:
                        raise "NO API KEY"
            except (ConnectionError, Timeout, TooManyRedirects) as e:
                print(e)
        return api_key

    def get_market_pairs(self, slug):
        # 交易所数据
        market_list, exchange_list = [], []
        url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/market-pairs/latest"
        params = {"slug": slug, "start": 1, "limit": 50, "category": "spot", "sort": "cmc_rank_advanced"}
        res = requests.get(url=url, headers=self.headers, params=params)
        response = json.loads(res.text)
        market = response["data"]
        for exchange in market["marketPairs"]:
            exchange_id = exchange["exchangeId"]
            exchange_name = exchange["exchangeName"]
            if exchange_name not in exchange_list:
                logo_url = "https://s2.coinmarketcap.com/static/img/exchanges/64x64/{}.png".format(exchange_id)
                market_info = {"name": exchange_name, "logo_url": logo_url}
                market_list.append(market_info)
                exchange_list.append(exchange_name)
            else:
                continue
        # print("--market_list--:", len(market_list), market_list)
        return market_list

    def get_wallets_info(self, slug):
        wallet_list = []
        url = "https://coinmarketcap.com/currencies/{}/wallets/".format(slug)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        }
        res = requests.get(url=url, headers=headers)
        pattern = re.compile('.*"wallets":(.*?)]')  # }],"isAudited"
        result = pattern.findall(res.text, re.S)
        if result:
            response = json.loads(f'{result[0]}]')
            for wallet in response:
                id, name, url = wallet["id"], wallet["name"], wallet["url"]
                logo_url = "https://s2.coinmarketcap.com/static/img/wallets/128x128/{}.png".format(id)
                wallet_info = {"name": name, "url": url, "logo_url": logo_url}
                wallet_list.append(wallet_info)
        return wallet_list

    def get_twitter_info(self, screen_name):
        # screen_name = "Stepnofficial"  # AxieInfinity  SecondLiveReal
        result = twitter_user.getTweets(screen_name)
        twitter_info = {
            "logo_url": result["logo_url"], "twitter_banner": result["background_url"],
            "followers": result["followers"], "following": result["following"]
            }
        return  twitter_info

    def get_binance_api(self, symbol):
        url = "https://api3.binance.com/api/v3/ticker/24hr"
        params = {"symbol": "{}USDT".format(symbol)}  # , "interval": "1h","limit": 24
        res = requests.get(url=url, params=params, headers=self.headers)
        ticker = json.loads(res.text)
        ticker_info = {
            "price_low_24h": ticker["lowPrice"], "price_high_24h": ticker["highPrice"],
            "quote_volume_24h": ticker["quoteVolume"]
            }
        return ticker_info

    def get_game_introduction(self, slug):
        """简介"""
        url = "https://coinmarketcap.com/currencies/{}/".format(slug)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        }
        res = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(res.text, 'lxml')
        # .get_text()
        content = soup.select('div[class="sc-16r8icm-0 kjciSH contentClosed hasShadow"]')[0]
        # print(content)
        return content


    def cryptocurrency_quotes_latest(self, **kwargs):
        """
        价格
        https://coinmarketcap.com/api/documentation/v1/#operation/getV1CryptocurrencyQuotesLatest
        """
        coin_cap = {}
        result = self.api_coin_market_cap('/cryptocurrency/quotes/latest', **kwargs)

        for keys, game in result.data.items():
            quotes = game["quote"]["USD"]
            last_time = self.datetime_to_str(self.formatUTCtime(quotes["last_updated"]))
            symbol_price = (quotes["price"] if quotes.get("price", 0) else 0)
            volume_24h = (quotes["volume_24h"] if quotes.get("volume_24h", 0) else 0)
            volume_change_24h = (quotes["volume_change_24h"] if quotes.get("volume_change_24h", 0) else 0)
            percent_change_24h = (quotes["percent_change_24h"] if quotes.get("percent_change_24h", 0) else 0)
            percent_change_7d = (quotes["percent_change_7d"] if quotes.get("percent_change_7d", 0) else 0)
            percent_change_30d = (quotes["percent_change_30d"] if quotes.get("percent_change_30d", 0) else 0)
            market_cap = (quotes["market_cap"] if quotes.get("market_cap", 0) else 0)
            fully_diluted_market_cap = (quotes["fully_diluted_market_cap"] if quotes.get("fully_diluted_market_cap", 0) else 0)
            circulating_supply = (quotes["circulating_supply"] if quotes.get("circulating_supply", 0) else 0)
            max_supply = (quotes["max_supply"] if quotes.get("max_supply", 0) else 0)
            total_supply = (quotes["total_supply"] if quotes.get("total_supply", 0) else 0)
            coin_cap.update({
                "symbol_price": symbol_price, "volume_24h": volume_24h, "volume_change_24h": volume_change_24h,
                "percent_change_24h": percent_change_24h, "percent_change_7d": percent_change_7d,
                "percent_change_30d": percent_change_30d,
                "market_cap": market_cap, "fully_diluted_market_cap": fully_diluted_market_cap,
                "circulating_supply": circulating_supply,
                "max_supply": max_supply, "total_supply": total_supply, "last_time": last_time
            })
        return coin_cap

    def cryptocurrency_info(self, **kwargs):
        """
        官网
        https://coinmarketcap.com/api/documentation/v1/#operation/getV1CryptocurrencyInfo
        """
        coin_cap = {}
        result = self.api_coin_market_cap('/cryptocurrency/info', **kwargs)
        #  ETH: 1, BSC: 56, heco: 128, Polygon: 137, oec: 66, Ronin: 2020, Fantom: 250, Avalanche: 43114, Solana: 245022926
        for keys, game in result.data.items():
            urls_info = game["urls"]
            medium_url = (urls_info["message_board"][0] if urls_info.get("message_board", []) else "")
            # print("medium---:{}".format(medium_url))
            website_url = (urls_info["website"][0] if urls_info.get("website", []) else "")
            technical_doc = (urls_info["technical_doc"][0] if urls_info.get("technical_doc", []) else "")
            twitter_url = (urls_info["twitter"][0] if urls_info.get("twitter", []) else "")
            discord_url = (urls_info["chat"][0] if urls_info.get("chat", []) else "")
            reddit_url = (urls_info["reddit"][0] if urls_info.get("reddit", []) else "")
            facebook_url = (urls_info["facebook"][0] if urls_info.get("facebook", []) else "")
            contract_list, tag_names = json.dumps(game["contract_address"]), json.dumps(game["tag-names"])
            release_time = self.datetime_to_str(self.formatUTCtime(game["date_added"]))
            twitter_name = game.get("twitter_username", "")  # 推特名称
            platform = game["platform"]
            if platform:
                chain_name, chain_symbol, token_address = platform["name"], platform["symbol"], platform["token_address"]
                chain_id = (1 if chain_name == "Ethereum" else 56 if chain_name == "BNB" else 137 if chain_name == "Polygon" else 2020 if chain_name == "Ronin" else 128 if chain_name == "Huobi Token" else 250 if chain_name == "Fantom" else 43114 if chain_name == "Avalanche" else 245022926 if chain_name == "Solana" else 66 if chain_name == "OKC Token" else 0)
            else:
                chain_id, chain_name, token_address = 0, "", ""

            coin_cap.update({
                "chain_id": chain_id, "chain_name": chain_name, "token_address": token_address,
                "name": game["name"], "slug": game["slug"], "symbol": game["symbol"], "medium_url": medium_url,
                "symbol_url": game["logo"], "release_time": release_time, "website_url": website_url,
                "description": game["description"], "technical_doc": technical_doc, "twitter_url": twitter_url,
                "discord_url": discord_url, "reddit_url": reddit_url, "facebook_url": facebook_url,
                "contract_address": contract_list, "tags": tag_names, "twitter_name": twitter_name
            })
        return coin_cap


    def game_market_info(self, slug):
        print("start--:{}".format(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
        market_info = {}
        arguments = {'slug': slug}
        # type   grade  discription1  discription_pic1
        # logo_url followers  following  twitter_banner  market_list   wallets_list  price_low_24h  price_high_24h  quote_volume_24h

        # https://axieinfinity.medium.com
        # https://medium.com/@SecondLiveReal

        official_info = self.cryptocurrency_info(**arguments)  # 官网
        slug, screen_name,symbol = official_info["slug"], official_info["twitter_name"], official_info["symbol"]
        price_info = self.cryptocurrency_quotes_latest(**arguments)  # 价格
        price, market_cap = price_info["symbol_price"], price_info["market_cap"]
        market_list = self.get_market_pairs(slug) # 交易所：名称和logo
        wallets_list = self.get_wallets_info(slug)
        twitter_info = self.get_twitter_info(screen_name)
        market_info.update(official_info)
        market_info.update(price_info)
        if price > 0 and market_cap > 0:
            ticker_info = self.get_binance_api(symbol)
        else:
            ticker_info = {"price_low_24h": 0, "price_high_24h": 0,"quote_volume_24h": 0}
        market_info.update({"market_list": json.dumps(market_list), "wallets_list": json.dumps(wallets_list)})
        market_info.update(twitter_info)
        market_info.update(ticker_info)
        print("end--:{}".format(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
        return market_info

# https://api-gravity.coinmarketcap.com/gravity/v3/gravity/trending-posts/18069?over-view=false&last-score=38291.8882&q=1653875973
# https://api.coinmarketcap.com/content/v3/news/aggregated?coins=6783&page=1&size=4


if __name__ == '__main__':
    slug= "axie-infinity"
    game = GameMarket()
    market_info = game.game_market_info(slug)
    for key, value in market_info.items():
        print("{}----:{}".format(key, value))

