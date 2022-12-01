import sys, os
sys.path.append(os.pardir)

import random
from datetime import datetime, timedelta
import requests
import json
import time
import os
import dingding
from apscheduler.schedulers.background import BackgroundScheduler
from lib.call_mysql import call_query_mysql, call_insert_mysql
from lib.qiniu_upload import Qiniu


class LookSRare():

    def __init__(self):
        # https://looksrare.org/collections/0x34d85c9CDeB23FA97cb08333b511ac86E1C4E258
        self.url = "https://api.looksrare.org"
        self.headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        }
        self.nft_other = "t_other_nft"
        self.nft_activity = "t_other_nft_activity"
        self.nft_assert = "t_other_nft_asset"
        self.nft_properties = "t_other_nft_properties"
        self.nft_statistics = "t_other_nft_statistics"

    def api_request(self, endpoint, query_params):
        # print("{}--{}".format(endpoint, query_params))
        api_ulr = self.url + endpoint
        res = requests.get(url=api_ulr, headers=self.headers, params=query_params)
        response = json.loads(res.text)
        return response


    def collections(self, address):
        endpoint = f"/api/v1/collections"
        query_params = {"address": address}
        return self.api_request(endpoint, query_params)


    def collections_stats(self, address):
        endpoint = f"/api/v1/collections/stats"
        query_params = {"address": address}
        return self.api_request(endpoint, query_params)


    def properties(self, collection, tokenId):
        endpoint = f"/api/v1/tokens"
        query_params = {"collection": collection, "tokenId": tokenId}
        return self.api_request(endpoint, query_params)


    def events(self, collection, tokenId, types="SALE", limit=5):
        # activities, like Listing, Transfer,Sale,offer
        pagination = json.dumps({"first": limit})
        #  ["LIST", "OFFER", "SALE", "TRANSFER", "MINT"]
        endpoint = f"/api/v1/events"
        query_params = {"collection": collection, "tokenId": tokenId, "type": types, "pagination": pagination}
        return self.api_request(endpoint, query_params)


    def get_orders(self, collection, limit, sort):
        # items
        # https://api.looksrare.org/api/v1/orders?
        # isOrderAsk=true&collection=0x34d85c9CDeB23FA97cb08333b511ac86E1C4E258&status%5B%5D=VALID&pagination%5Bfirst%5D=5&sort=PRICE_ASC
        endpoint = f"/api/v1/orders"
        status = json.dumps(["VALID"])
        pagination = json.dumps({"first": limit})
        query_params = {"isOrderAsk": "true", "collection": collection, "status": status, "pagination": pagination, "sort": sort}
        return self.api_request(endpoint, query_params)


    def formatUTCtime(self, timestamp):
        utc_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        utc_date = datetime.strptime(timestamp, utc_format) + timedelta(hours=8)
        return utc_date

    def datetime_to_str(self, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)


    def deal_str_float(self, data):
        if data:
            result = float(data) / 1000000000000000000
            number = round(result, 3)
        else:
            number = 0
        return number


    def deal_query_nft(self):
        # current 分页
        json_info = {"table": self.nft_other, "current": 1}
        game_list = call_query_mysql(json_info)
        for game in game_list["records"]:
            nft_id, game_id = game.get("id", 0), game.get("gameId", 0)
            address = game.get("collectionAddress", "")
            if address:
                print("--address--:", address)
                self.get_nft_looksrare(nft_id, game_id, address)
                time.sleep(2)


    def deal_other_nft(self, table, nft_info):
        msg = call_insert_mysql(table, nft_info)
        if msg["msg"] != "ok":
            print("error--{}".format(msg))
        else:
            return msg["data"]


    def get_nft_looksrare(self, nft_id, game_id, address):
        try:
            time_list = ["24h", "7d"]
            stats = self.collections_stats(address)["data"]
            items, owners = stats.get("totalSupply", 0), stats.get("countOwners", 0)
            total_volume = self.deal_str_float(stats.get("volumeAll", 0))
            floor_price = self.deal_str_float(stats.get("floorPrice", 0))
            one_day_change, seven_day_change = stats.get("floorChange24h", 0), stats.get("floorChange7d", 0)
            time.sleep(random.randint(2, 4))
            res = self.collections(address)["data"]
            name, description = res.get("name", ""), res.get("description", "")
            #  LAND   ERC721
            symbol, nft_type = res.get("symbol", ""), res.get("type", "")
            nft_info = {
                "id": nft_id, "nft_name": name, "items": items, "owners": owners,
                "floorPrice": floor_price, "totalVolume": total_volume
            }
            self.deal_other_nft(self.nft_other, nft_info)

            for time_state in time_list:
                volume, sales, average_price = 0, 0, 0
                if time_state == "24h":
                    volume = self.deal_str_float((stats["volume24h"] if stats["volume24h"] else 0))
                    sales = (stats["count24h"] if stats["count24h"] else 0)
                    average_price = self.deal_str_float((stats["average24h"] if stats["average24h"] else 0))
                elif time_state == "7d":
                    volume = self.deal_str_float((stats["volume7d"] if stats["volume7d"] else 0))
                    sales = (stats["count7d"] if stats["count7d"] else 0)
                    average_price = self.deal_str_float((stats["average7d"] if stats["average7d"] else 0))

                nft_stats = {
                    "nftId": nft_id, "gameId": game_id, "volume": volume, "sales": sales, "averagePrice": average_price,
                    "oneDayChange": one_day_change, "sevenDayChange": seven_day_change, "floorPrice": floor_price,
                    "numOwners": owners, "totalSupply": items, "platform": "looksrare", "time_state": time_state
                }
                self.deal_other_nft(self.nft_statistics, nft_stats)
                time.sleep(random.randint(3, 6))

            # items
            time.sleep(random.randint(3, 6))
            order_list = look.get_orders(address, 10, "PRICE_ASC")["data"]
            for order in order_list:
                # chain_name = "Ethereum"
                chain_id = 1
                tokenId, price = order.get("tokenId", ""), self.deal_str_float(order.get("price", 0))
                startTime, endTime = order.get("startTime", 0), order.get("endTime", 0)
                prop = look.properties(collection=address, tokenId=tokenId)["data"]
                collection = prop.get("collection", {})
                permalink = "{}/collections/{}/{}".format(self.url, address,tokenId)
                attributes_list = prop.get("attributes", [])
                details_name, coll_address = prop.get("name", ""), prop.get("collectionAddress", "")
                schema_name, owner_address = collection.get("type", ""), collection.get("owner", "")
                old_id, image = prop.get("id", 0), prop.get("imageURI", "")
                # 七牛云
                image_url = Qiniu.get_upload_img_url(image)
                payment_symbol, platform = "ETH", "looksrare"

                asset_info = {
                    "nftId": nft_id, "gameId": game_id, "chainId": chain_id, "currentPrice": price,
                    "createdDate": startTime, "saleTime": endTime,
                    "detailsName": details_name, "contractAddress": coll_address, "tokenId": tokenId,
                    "tokenStandard": schema_name,"platform": platform, "payment_symbol": payment_symbol, "permalink": permalink,
                    "imageUrl": image_url,"ownerAddress": owner_address, "oldId": old_id, "description": description,
                }

                asset_id = self.deal_other_nft(self.nft_assert, asset_info)
                time.sleep(random.randint(3, 6))

                # properties
                for attr in attributes_list:
                    trait_type, value = attr.get("traitType", ""), attr.get("value", "")
                    trait_count = int(attr.get("count", "0"))
                    percent = round(trait_count / items * 100)
                    traits_info = {
                        "assetId": asset_id, "traitType": trait_type, "value": value, "percent": percent,
                        "traitCount": trait_count, "items": items
                    }
                    self.deal_other_nft(self.nft_properties, traits_info)

                # item activity
                activity_list, limit = ["LIST", "OFFER", "SALE", "TRANSFER", "MINT"], 10
                for types in activity_list:
                    events = look.events(collection=address, tokenId=tokenId, types=types, limit=limit)["data"]
                    # print("--events--:", events)
                    if events:
                        activity = events[0]
                        order_info = activity.get("order", {})
                        collection = activity.get("collection", {})
                        asset_address, asset_schema = collection.get("address", ""), collection.get("type", "")
                        order_hash = activity.get("hash", "")
                        if order_info:
                            create_time, sale_time = order_info.get("startTime", 0), order_info.get("endTime", 0)
                            current_price = self.deal_str_float(order_info["price"])
                            _from = order_info.get("signer", "")
                        else:
                            create_time = self.datetime_to_str(self.formatUTCtime(activity.get("createdAt", "")))
                            sale_time = create_time
                            current_price = 0
                            _from, _to = activity.get("from", ""), activity.get("to", "")

                        event_info = {
                            "assetId": asset_id, "currentPrice": current_price, "saleTime": sale_time,
                            "createdDate": create_time,"assetAddress": asset_address, "assetSchema": asset_schema,
                            "makerAddress": _from,"orderHash": order_hash,"activityType": types
                        }
                        self.deal_other_nft(self.nft_activity, event_info)
                        time.sleep(random.randint(3, 6))
                    else:
                        continue
        except Exception as e:
            print("looks_rare error: {}".format(e))
            dingding.ding(__file__)


    def start_scheduler(self):
        scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        # 每天04:00执行
        scheduler.add_job(self.deal_query_nft, 'cron', hour=4)
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
        try:
            scheduler.start()
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()


if __name__ == '__main__':
    look = LookSRare()
    look.start_scheduler()






