import sys, os
sys.path.append(os.pardir)

from game_NFT.opensea.opensea_api import OpenseaAPI
import os
import json
import time
# import dingding
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from lib.call_mysql import call_query_mysql, call_insert_mysql
from lib.qiniu_upload import Qiniu



class OpenSea():

    def __init__(self):
        # https://github.com/FastestMolasses/PyOpenSea
        self.api = OpenseaAPI()
        self.nft_other = "t_other_nft"
        self.nft_activity = "t_other_nft_activity"
        self.nft_assert = "t_other_nft_asset"
        self.nft_properties = "t_other_nft_properties"
        self.nft_statistics = "t_other_nft_statistics"


    def format_Ttime(self, timestamp):
        utc_format = "%Y-%m-%dT%H:%M:%S.%f"
        utc_date = datetime.strptime(timestamp, utc_format) + timedelta(hours=8)
        return str(utc_date).split(".")[0]

    def timestamp_to_str(self, ts, fmt=None):
        t = time.localtime(ts)
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return time.strftime(fmt, t)


    def deal_assets_price(self, contract_address, token_id, Weth_token, eth_token):
        listings, offers = {}, {}
        result = self.api.listings(asset_contract_address=contract_address, token_id=token_id)
        asset_list = result["seaport_listings"]
        if len(asset_list) > 0:
            asset_one = asset_list[0]
            # print("--asset_one--:", contract_address, token_id)
            listing_time = int(asset_one["expiration_time"])  # + 8*60*60 listing_time
            sale_time = self.timestamp_to_str(listing_time)
            address = asset_one["maker"]["address"]
            current_price = int(asset_one["current_price"]) /1000000000000000000

            payment_symbol, symbol_price, usd_price = "ETH", 0, 0
            if eth_token:
                payment_symbol = eth_token["symbol"]
                symbol_price = round(float(eth_token["usd_price"]), 2)
                usd_price = float(symbol_price) * float(current_price)

            # payment_symbol  current_price  usd_price  symbol_price  sale_time
            listings.update({
                "currentPrice": current_price,"saleTime": sale_time,"paymentSymbol": payment_symbol,
                "symbolPrice": symbol_price, "usdPrice": usd_price
                })


        offers_info = self.api.offers(asset_contract_address=contract_address, token_id=token_id)
        offers_list = offers_info["seaport_offers"]
        if len(offers_list) > 0:
            asset_two = offers_list[0]
            # print("--asset_two--:", contract_address, token_id)
            expiration_time = int(asset_two["expiration_time"])  # + 8*60*60  expiration_time
            sale_time = self.timestamp_to_str(expiration_time)
            address = asset_two["maker"]["address"]
            current_price = int(asset_two["current_price"]) /1000000000000000000

            payment_symbol, symbol_price, usd_price = "WETH", 0, 0
            if Weth_token:
                payment_symbol = Weth_token["symbol"]
                symbol_price = float(Weth_token["usd_price"])
                usd_price = float(symbol_price) * float(current_price)

            offers.update({
                "currentPrice": current_price,"saleTime": sale_time,"paymentSymbol": payment_symbol,
                "symbolPrice": symbol_price, "usdPrice": usd_price
            })

        asset_info = {}
        if listings and not offers:
            asset_info = listings
        elif not listings and offers:
            asset_info = offers
        elif listings and offers:
            list_price, offers_price = listings["currentPrice"], offers["currentPrice"]
            if list_price > offers_price:
                asset_info = listings
            else:
                asset_info = offers
        return asset_info


    def get_properties_info(self, asset_id, traits_list, total_supply):
        for data in traits_list:
            trait_type, value = data["trait_type"], data["value"]
            trait_count = data["trait_count"]
            percent = round(trait_count / total_supply * 100)
            traits_info = {
                "assetId": asset_id,"traitType": trait_type, "value": value,
                "percent": percent, "traitCount": trait_count,"items": total_supply
            }
            time.sleep(1)
            # print("--traits_info--:{}".format(traits_info))
            self.deal_other_nft(self.nft_properties, traits_info)

    def get_asset_listings(self, asset_id, seaport_listings, eth_token):
        """NFT清单"""
        for data in seaport_listings:
            listing_time = int(data["listing_time"])  # + 8*60*60
            sale_time = self.timestamp_to_str(listing_time)
            address, order_hash = data["maker"]["address"], data["order_hash"]

            current_price = int(data["current_price"]) /1000000000000000000
            create_time = self.format_Ttime(data["created_date"])
            payment_symbol, eth_usd_price, usd_price = "ETH", 0, 0
            if eth_token:
                payment_symbol = eth_token["symbol"]
                eth_usd_price = float(eth_token["usd_price"])
                usd_price = float(eth_usd_price) * float(current_price)

            listings = {"assetId": asset_id,"currentPrice": current_price, "saleTime": sale_time, "makerAddress": address,
                        "paymentSymbol": payment_symbol, "ethUsdPrice": eth_usd_price, "usdPrice": usd_price,
                        "orderHash": order_hash, "activityType": "listings","createdDate": create_time
                        }
            time.sleep(1)
            self.deal_other_nft(self.nft_activity, listings)

    def get_asset_offers(self, asset_id, seaport_offers, floor_price, Weth_token):
        for data in seaport_offers:
            create_time = self.format_Ttime(data["created_date"])
            expiration_time = int(data["listing_time"])  # + 8*60*60
            sale_time = self.timestamp_to_str(expiration_time)
            address = data["maker"]["address"]  # From
            order_hash = data["order_hash"]
            current_price = int(data["current_price"]) /1000000000000000000
            floor_difference = round(((current_price - floor_price) / floor_price) * 100)

            payment_symbol, eth_usd_price, usd_price = "ETH", 0, 0
            if Weth_token:
                payment_symbol = Weth_token["symbol"]
                eth_usd_price = float(Weth_token["usd_price"])
                usd_price = float(eth_usd_price) * float(current_price)

            offers = {
                "assetId": asset_id, "currentPrice": current_price, "floorDifference": floor_difference,
                "paymentSymbol": payment_symbol, "ethUsdPrice": eth_usd_price, "usdPrice": usd_price,
                "saleTime": sale_time,"makerAddress": address,"orderHash": order_hash,"activityType": "offers",
                "createdDate": create_time
            }
            time.sleep(1)
            self.deal_other_nft(self.nft_activity, offers)



    def deal_other_nft(self, table, nft_info):
        msg = call_insert_mysql(table, nft_info)
        if msg["msg"] != "ok":
            print("error--{}".format(msg))
        else:
            return msg["data"]


    def deal_query_nft(self):
        json_info = {"table": self.nft_other, "current": 1}
        game_list = call_query_mysql(json_info)
        for game in game_list["records"]:
            nft_id, game_id = game.get("id", 0), game.get("gameId", 0)
            slug = game.get("slug", "")
            print("--slug--:", nft_id, game_id, slug)
            self.get_nft_opensea(nft_id, game_id, slug)
            time.sleep(5)


    def get_nft_opensea(self, nft_id, game_id, slug):
        open_sea = self.api.collection(slug)
        if "collection" in open_sea:
            time_list = ["24h", "7d", "30d"]
            coll, stats = open_sea["collection"], open_sea["collection"]["stats"]
            items, owners = (stats["count"] if stats["count"] else 0), (stats["num_owners"] if stats["num_owners"] else 0)
            floor_price, total_volume = (stats["floor_price"] if stats["floor_price"] else 0), ( stats["total_volume"] if stats["total_volume"] else 0)
            description = (coll["description"] if coll["description"] else "")
            name, slugs = (coll["name"] if coll["name"] else ""), (coll["slug"] if coll["slug"] else "")

            one_day_change = (stats["one_day_change"] if stats["one_day_change"] else 0)
            seven_day_change = (stats["seven_day_change"] if stats["seven_day_change"] else 0)

            # one_day_volume、one_day_change、seven_day_volume、seven_day_change、floor_price、num_owners、total_supply,platform

            nft_info = {
                "id": nft_id, "nftName": name, "slug": slugs, "description": description, "items": items, "owners": owners,
                "floorPrice": floor_price, "totalVolume": total_volume
                }
            self.deal_other_nft(self.nft_other, nft_info)

            for time_state in time_list:
                if time_state == "24h":
                    volume = (stats["one_day_volume"] if stats["one_day_volume"] else 0)
                    sales = (stats["one_day_sales"] if stats["one_day_sales"] else 0)
                    average_price = (stats["one_day_average_price"] if stats["one_day_average_price"] else 0)
                elif time_state == "7d":
                    volume = (stats["seven_day_volume"] if stats["seven_day_volume"] else 0)
                    sales = (stats["seven_day_sales"] if stats["seven_day_sales"] else 0)
                    average_price = (stats["seven_day_average_price"] if stats["seven_day_average_price"] else 0)
                else:
                    volume = (stats["thirty_day_volume"] if stats["thirty_day_volume"] else 0)
                    sales = (stats["thirty_day_sales"] if stats["thirty_day_sales"] else 0)
                    average_price = (stats["thirty_day_average_price"] if stats["thirty_day_average_price"] else 0)

                nft_stats = {
                    "nftId": nft_id, "gameId": game_id, "volume": volume, "sales": sales, "averagePrice": average_price,
                    "oneDayChange": one_day_change, "sevenDayChange": seven_day_change, "floorPrice": floor_price,
                    "numOwners": owners, "totalSupply": items, "platform": "opensea", "time_state": time_state
                }
                self.deal_other_nft(self.nft_statistics, nft_stats)

            self.get_items_list(nft_id, game_id, slug)


    def get_items_list(self, nft_id, game_id, slug):
        try:
            res_info = self.api.collection(slug)["collection"]
            eth_token, Weth_token = {}, {}
            payment_list = res_info["payment_tokens"]
            total_supply = res_info["stats"]["total_supply"]
            floor_price = res_info["stats"]["floor_price"]
            for tokens in payment_list:
                token_name, symbol = tokens.get("name", ""), tokens.get("symbol", "")
                usd_price = tokens.get("usd_price", 0)
                if symbol == "ETH":
                    eth_token.update({"name": token_name, "symbol": symbol, "usd_price": usd_price})
                elif symbol == "WETH":
                    Weth_token.update({"name": token_name, "symbol": symbol, "usd_price": usd_price})
                else:
                    continue

            result = self.api.assets(collection=slug, order_direction="asc")
            _next = result["next"]  # 翻页
            for asset in result["assets"]:
                owner_name, owner_img, owner_address, chain_name = "", "", "", "Ethereum"
                traits_list = asset["traits"]
                asset_contract, permalink = asset["asset_contract"], asset["permalink"]
                open_sea = permalink.split("/")
                chain_id, address, token = 1, open_sea[5], open_sea[6]
                image, token_id, old_id = asset["image_url"], asset["token_id"], asset["id"]
                time.sleep(1)
                # 七牛云
                # print("--image--:", address, token, image)
                image_url = Qiniu.get_upload_img_url(image)
                name = (asset["name"] if asset["name"] else "#{}".format(token_id))
                description = (asset["description"] if asset["description"] else "")
                contract_address, schema_name = asset_contract["address"], asset_contract["schema_name"]
                creator_fees, created_date = asset_contract["dev_seller_fee_basis_points"], asset_contract["created_date"]
                create_time = self.format_Ttime(created_date)

                if "owner" in asset:
                    owner, owner_address = asset["owner"], asset["owner"]["address"]
                    if not owner["user"]:
                        owner_name = owner_address[2:8].upper()
                    else:
                        user_name = owner["user"]["username"]
                        if user_name:
                            owner_name = user_name

                asset_info = {
                    "nftId": nft_id, "gameId": game_id, "detailsName": name, "contractAddress": contract_address,
                    "tokenId": token_id, "tokenStandard": schema_name, "creatorFees": creator_fees, "platform": "opensea",
                    "permalink": permalink, "imageUrl": image_url, "ownerName": owner_name, "chainId": chain_id,
                    "createdDate": create_time, "ownerAddress": owner_address, "oldId": old_id, "description": description,
                }
                time.sleep(3)
                assets_price = self.deal_assets_price(address, token, Weth_token, eth_token)
                asset_info.update(assets_price)
                # nft asset
                time.sleep(2)
                asset_id = self.deal_other_nft(self.nft_assert, asset_info)
                # properties

                self.get_properties_info(asset_id, traits_list, total_supply)
                # item activity
                time.sleep(2)
                res_listings = self.api.listings(address, token)
                if res_listings:
                    seaport_listings = res_listings.get("seaport_listings", [])
                    self.get_asset_listings(asset_id, seaport_listings, eth_token)

                time.sleep(2)
                res_offers = self.api.offers(address, token)
                if res_offers:
                    seaport_offers = res_offers.get("seaport_offers", [])
                    self.get_asset_offers(asset_id, seaport_offers, floor_price, Weth_token)
        except Exception as e:
            print("{}_items_list: {}".format(slug, e))
            dingding.ding(__file__)


    def start_scheduler(self):
        scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        # 每天01:00执行
        # scheduler.add_job(self.deal_query_nft, 'interval', days=1)
        scheduler.add_job(self.deal_query_nft, 'cron', hour=1)
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
        try:
            scheduler.start()
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()


if __name__ == '__main__':
    open = OpenSea()
    # open.start_scheduler()





