import time
import re
import json
from playwright.sync_api import sync_playwright
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from selenium import webdriver
import os
from lib.call_mysql import call_insert_mysql, call_delete_mysql

class Nftgo():

	def __init__(self):
		self.whales_list = "https://api.nftgo.io/api/v1/whales/data/list/whaleBought?by=WhaleNum&asc=-1&timeRank={}&action={}"
		self.chart_tracking = "https://api.nftgo.io/api/v1/whales/data/chart/tracking?timeRank={}"
		self.ranking_whales = "https://api.nftgo.io/api/v1/ranking/whalesv2?by=value&asc=-1&hasContract=-1&fields=value,valuePercent,nftNum,buyVolume,buyVolumePercent,sellVolume,sellVolumePercent,lastTrade,mostCollections,estValue,estURP,estValuePercent,estURPPercent,activities,collections,profit,profitPercent,pnl,pnlPercent&offset={}&limit={}"
		self.whales_activity = "https://nftgo.io/api/v1/whales-activity?action={}&cid=all&to={}&scroll=0&limit=15&isListed=-1"
		self.list_topSales = "https://api.nftgo.io/api/v1/whales/data/list/topSales?action={}&by=PriceEth&asc=-1&timeRank={}&excludeWashTrading=-1"
		self.list_topBuyer = "https://api.nftgo.io/api/v1/whales/data/list/topBuyer?by=VolumeEth&asc=-1&timeRank={}"
		self.list_topSeller = "https://api.nftgo.io/api/v1/whales/data/list/topSeller?by=VolumeEth&asc=-1&timeRank={}"
		self.list_whaleMintColl = "https://api.nftgo.io/api/v1/whales/data/list/whaleMintColl?by=WhaleNum&asc=-1&isListed=-1&timeRank={}"
		self.list_mintWhale = "https://api.nftgo.io/api/v1/whales/data/list/mintWhale?by=MintNum&asc=-1&timeRank={}"

	def formatUTCtime(self, timestamp):
		utc_format = "%Y-%m-%dT%H:%M:%S.%fZ"
		utc_date = datetime.strptime(timestamp, utc_format) + timedelta(hours=8)
		return utc_date

	def datetime_to_str(self, dt, fmt=None):
		if fmt is None:
			fmt = '%Y-%m-%d %X'
		return dt.strftime(fmt)

	def get_today_timestamp(self):
		now = datetime.now()
		zeroToday = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,microseconds=now.microsecond)
		lastToday = zeroToday + timedelta(hours=23, minutes=59, seconds=59)
		timestamp = int(str(int(time.mktime(lastToday.timetuple()))) + "999")
		return timestamp


	def insert_whale_info(self, table_name, whale_info):
		msg = call_insert_mysql(table_name, whale_info)
		if msg["msg"] != "ok":
			print("--11--:", table_name, whale_info)

	def delete_whale_info(self, table_name):
		msg = call_delete_mysql(table_name)
		if msg["msg"] != "ok":
			print("--11--:", table_name)

	def api_whales_list(self, action,time_rank):
		# buy sell  "1h" "24h" "7d" "30d"
		# truncate table t_whale_most_involved;
		# SELECT coll_contracts,coll_name,whale_num,sale_num,whale_volume,volume,volume_change,floor_price_token_price,floor_price_change,order_avg_price,order_avg_price_change,market_cap,market_cap_change,action FROM t_whale_most_involved where action='sell';
		table_name = "t_whale_most_involved"
		url = self.whales_list.format(time_rank, action)
		result = self.get_request_nftgo(url)
		for data in result:
			collTags, floor = data.get("collTags", {}), data.get("floorPrice", {})
			coll, whaleNum, saleNum = data.get("coll", {}),int(data.get("whaleNum", 0)),int(data.get("saleNum", 0))
			from_time = data.get("fromTime", 0)
			whaleVolume = (float(data["whaleVolume"]) if data.get("whaleVolume", 0) else 0)
			total_volume = (float(data["volume{}".format(time_rank)]) if data.get("volume{}".format(time_rank), 0) else 0)
			volumeChange = (float(data["volume{}Change{}".format(time_rank,time_rank)]) if data.get("volume{}Change{}".format(time_rank,time_rank), 0) else 0)
			blockchain, contract = collTags.get("blockchain", ""), collTags.get("contract", "")

			floor_price = (float(floor["tokenPrice"]) if floor and floor.get("tokenPrice", 0) else 0)
			floor_price_change = (float(data["floorPriceChange{}".format(time_rank)]) if data.get("floorPriceChange{}".format(time_rank), 0) else 0)
			avg_price = (float(data["orderAvgPriceETH{}".format(time_rank)]) if data.get("orderAvgPriceETH{}".format(time_rank), 0) else 0)
			avg_price_change = (float(data["orderAvgPrice{}Change{}".format(time_rank,time_rank)]) if data.get("orderAvgPrice{}Change{}".format(time_rank,time_rank), 0) else 0)
			marketCap = (float(data["marketCap"]) if data.get("marketCap", 0) else 0)
			marketCapChange = (float(data["marketCapChange{}".format(time_rank)]) if data.get("marketCapChange{}".format(time_rank), 0) else 0)
			cid, name, logo, createTime = coll.get("_id", ""), coll.get("name", ""), coll.get("logo", ""), coll.get("createTime", "")
			create_time = self.datetime_to_str(self.formatUTCtime(createTime))
			most_involved = {
				"collName": name, "whaleNum":whaleNum, "saleNum":saleNum, "collId":cid, "collLogo": logo,"whaleVolume": whaleVolume,"volume": total_volume,
				"volumeChange": volumeChange,"collBlockchain": blockchain,"collContracts": contract, "floorPriceTokenPrice": floor_price,"floorPriceChange": floor_price_change,
				"orderAvgPrice": avg_price,"orderAvgPriceChange": avg_price_change,"marketCap": marketCap,"marketCapChange": marketCapChange,
				"createTime": create_time,"action": action, "timeState": time_rank, "fromTime": from_time
			}
			# print("--most_involved--:", most_involved)
			self.insert_whale_info(table_name, most_involved)



	def whales_chart_tracking(self, timeRank):
		# 保留数据
		url = self.chart_tracking.format(timeRank)
		result = self.get_request_nftgo(url)
		for data in result:
			active_Whale, burn = data.get("activeFilterWhaleChart", {}), data.get("burn", {})
			buy, mint, sell = data.get("buyChart", {}), data.get("mintChart", {}), data.get("sellChart", {})
			active_meta, active_values = active_Whale.get("meta", {}), active_Whale.get("values", {})
			burn_meta, burn_values = burn.get("meta", {}), burn.get("values", {})
			buy_meta, buy_values = buy.get("meta", {}), buy.get("values", {})
			mint_meta, mint_values = mint.get("meta", {}), mint.get("values", {})
			sell_meta, sell_values = mint.get("meta", {}), mint.get("values", {})

			active_meta_delta, active_meta_name, active_meta_value = active_meta.get("delta", 0), active_meta.get(
				"name", ""), active_meta.get("value", 0)
			active_values_x, active_values_y = active_values.get("x", []), active_values.get("y", [])

			burn_meta_delta, burn_meta_name, burn_meta_value = burn_meta.get("delta", 0), burn_meta.get(
				"name", ""), burn_meta.get("value", 0)
			burn_values_x, burn_values_y = burn_values.get("x", []), burn_values.get("y", [])

			buy_meta_delta, buy_meta_name, buy_meta_value = buy_meta.get("delta", 0), buy_meta.get(
				"name", ""), buy_meta.get("value", 0)
			buy_values_x, buy_values_y = buy_values.get("x", []), buy_values.get("y", [])

			mint_meta_delta, mint_meta_name, mint_meta_value = mint_meta.get("delta", 0), mint_meta.get(
				"name", ""), mint_meta.get("value", 0)
			mint_values_x, mint_values_y = mint_values.get("x", []), mint_values.get("y", [])

			sell_meta_delta, sell_meta_name, sell_meta_value = sell_meta.get("delta", 0), sell_meta.get(
				"name", ""), sell_meta.get("value", 0)
			sell_values_x, sell_values_y = sell_values.get("x", []), sell_values.get("y", [])
			whale_trends = {
				"active_meta_delta":active_meta_delta,"active_meta_name":active_meta_name,"active_meta_value":active_meta_value,
				"active_values_x": active_values_x,"active_values_y":active_values_y,"burn_meta_delta":burn_meta_delta,"burn_meta_name": burn_meta_name,
				"burn_meta_value":burn_meta_value,"burn_values_x":burn_values_x,"burn_values_y":burn_values_y,"buy_meta_delta": buy_meta_delta,
				"buy_meta_name": buy_meta_name,"buy_meta_value": buy_meta_value,"buy_values_x": buy_values_x,"buy_values_y": buy_values_y,
				"mint_meta_delta": mint_meta_delta,"mint_meta_name": mint_meta_name,"mint_meta_value": mint_meta_value,"mint_values_x": mint_values_x,
				"mint_values_y": mint_values_y,"sell_meta_delta": sell_meta_delta,"sell_meta_name": sell_meta_name,"sell_meta_value": sell_meta_value,
				"sell_values_x": sell_values_x,"sell_values_y": sell_values_y
			}
			print("--whale_trends--:", whale_trends)
		return result


	def whales_ranking_whales(self, offset, limit):
		# truncate table t_whale_all;
		# select whale_addr,whale_holding_value,est_value,pnl,buy_volume,sell_volume,collections,nft_num, activities,last_trade_timestamp  from t_whale_all;
		table_name = "t_whale_all"
		url = self.ranking_whales.format(offset, limit)
		result = self.get_request_nftgo(url)
		offset_len = len(result["list"])
		for data in result["list"]:
			tags, most_collections,last_trade = data.get("tags", {}), data.get("mostCollections", []), data.get("lastTrade",{})
			blockchain,address = tags.get("blockchain", ""), tags.get("addr", "")
			holding_value = (float(tags["whaleHoldingValue"]) if tags.get("whaleHoldingValue", 0) else 0)
			whale_ranking = (float(tags["whaleRanking"]) if tags.get("whaleRanking", 0) else 0)
			est_value = (float(data["estValue"]) if data.get("estValue", 0) else 0)
			pnl = (float(data["pnl"]) if data.get("pnl", 0) else 0)
			buy_volume = (float(data["buyVolume"]) if data.get("buyVolume", 0) else 0)
			sell_volume = (float(data["sellVolume"]) if data.get("sellVolume", 0) else 0)
			collections, nftNum, activities =  data.get("collections", 0), data.get("nftNum", 0), data.get("activities", 0)
			timestamp = (float(last_trade["timestamp"]) if last_trade and "timestamp" in last_trade else 0)
			coll_name, coll_logo, hasRarity = "", "", True
			if most_collections:
				most = most_collections[0]
				coll_name, coll_logo = most.get("name", ""), most.get("logo", "")
				hasRarity = most.get("hasRarity", True)

			whale_all = {
				"whaleAddr": address, "whaleBlockchain": blockchain,"whaleHoldingValue": holding_value,
				"whaleRanking": whale_ranking, "collHasRarity": hasRarity,"collName": coll_name,"collLogo": coll_logo, "estValue": est_value,
				"pnl": pnl, "buyVolume": buy_volume, "sellVolume": sell_volume, "collections": collections,
				"nftNum": nftNum,"activities": activities,"lastTradeTimestamp": timestamp
			}
			self.insert_whale_info(table_name, whale_all)
		return offset_len


	def api_whales_activity(self, action, to):
		# truncate table t_whale_activity;
		# select tx_from,from_whale_holding_value,from_whale_ranking,action,nft_name,tx_to,token_unit_price,usd_unit_price,gas_fee,coll_name from t_whale_activity;
		table_name = "t_whale_activity"
		url = self.whales_activity.format(action, to)
		result = self.get_request_nftgo(url)
		for data in result:
			coll, coll_tags = data.get("coll", {}), data.get("collTags", {})
			nft,object_tag = data.get("nft", {}), data.get("objectAddrTag", {})
			subject_info, subject_tag = data.get("subjectInfo", {}), data.get("subjectAddrTag", {})
			coll_name, coll_logo = coll.get("name", ""), coll.get("logo", "")
			nft_name = (nft["name"] if nft and "name" in nft else data["contractName"])
			nft_image, nft_blockchain, nft_token_id = nft.get("image", ""), nft.get("blockchain", ""), nft.get("tokenId", "")
			obj_tag_addr, obj_tag_alias = object_tag.get("addr", ""), object_tag.get("alias", "")
			sub_tag_addr, sub_tag_alias = subject_tag.get("addr", ""), subject_tag.get("alias", "")
			sub_tag_whale_holding, sub_tag_whale_ranking = subject_tag.get("whaleHoldingValue", 0), subject_tag.get("whaleRanking", 0)
			time = subject_info.get("time", 0)
			tx_url, gasFee = data.get("txUrl", ""), data.get("gasFee", 0)
			tokenUnitPrice, usdUnitPrice = data.get("tokenUnitPrice", 0), data.get("usdUnitPrice", 0)
			action_name = data.get("action", "")

			if subject_tag and sub_tag_alias:
				from_name = sub_tag_alias
			else:
				from_name = sub_tag_addr

			if object_tag and obj_tag_alias:
				to_name = obj_tag_alias
			else:
				to_name = obj_tag_addr

			whale_activity = {
				"fromAlias": from_name,"fromAddr": sub_tag_addr,"fromWhaleHoldingValue": sub_tag_whale_holding,"fromWhaleRanking": sub_tag_whale_ranking,
				"action": action_name,"nftName": nft_name,"nftBlockchain": nft_blockchain,"nftTokenId": nft_token_id,
				"toAddr": obj_tag_addr, "toAlias": to_name,"tokenUnitPrice": tokenUnitPrice,"usdUnitPrice": usdUnitPrice,
				"gasFee": gasFee,"coll_name": coll_name, "coll_logo": coll_logo,"txUrl": tx_url, "time": time,"nftImage": nft_image,
			}
			# print(whale_activity)
			self.insert_whale_info(table_name, whale_activity)


	def whales_list_topSales(self, action,time_rank):
		table_name = "t_whale_bought"
		# truncate table t_whale_bought;
		# select coll_name,price,token_price,token_price_change,change_percent,seller_addr,buyer_addr,time,action from t_whale_bought where action='buy';
		url = self.list_topSales.format(action,time_rank)
		result = self.get_request_nftgo(url)
		for data in result:
			nft, coll, buyer_tags = data.get("nft", {}), data.get("coll", {}), data.get("buyerTags", {})
			seller_tags =  data.get("sellerTags", {})
			nft_name, nft_image = nft.get("name", ""),nft.get("image", "")
			blockchain, coll_logo = coll.get("blockchain", ""), coll.get("logo", "")
			price = (float(data["price"]) if data.get("price", 0) else 0)
			token_price = (float(data["tokenPrice"]) if data.get("tokenPrice", 0) else 0)
			token_price_before = (float(data["tokenPriceBefore"]) if data.get("tokenPriceBefore", 0) else 0)
			token_price_change = (float(data["tokenPriceChange"]) if data.get("tokenPriceChange", 0) else 0)
			price_before = (float(data["priceBefore"]) if data.get("priceBefore", 0) else 0)
			changePrice = (float(data["changePrice"]) if data.get("changePrice", 0) else 0)

			change_percent = (float(data["changePercent"]) if data.get("changePercent", 0) else 0)
			buyer_address,buyer_alias, buyer_holding, buyer_ranking = buyer_tags.get("addr", ""), buyer_tags.get("alias", ""), float(buyer_tags.get("whaleHoldingValue", 0)), float(buyer_tags.get("whaleRanking", 0))
			seller_address, seller_ens, seller_holding, seller_ranking = seller_tags.get("addr", ""), seller_tags.get("ensName",""), float(seller_tags.get("whaleHoldingValue", 0)), float(seller_tags.get("whaleRanking", 0))
			create_time, txUrl = data.get("time", 0), data.get("txUrl", "")
			whales_bought = {
				"nftName": nft_name, "nftImage": nft_image, "collLogo": coll_logo, "collBlockchain": blockchain, "price": price, "tokenPrice": token_price,
				"tokenPriceBefore": token_price_before,"tokenPriceChange": token_price_change,"buyerAlias": buyer_alias,
				"priceBefore": price_before, "changePrice":changePrice,"changePercent":change_percent,"buyerAddr": buyer_address,"sellerAddr": seller_address,
				"sellerEnsName": seller_ens, "sellerWhaleHoldingValue": seller_holding,"sellerWhaleRanking": seller_ranking,"time": create_time,
				"action": action, "timeState": time_rank, "txUrl": txUrl
				}
			# print("--whales_bought--:", whales_bought)
			self.insert_whale_info(table_name, whales_bought)



	def whales_list_topBuyer(self, time_rank):
		# truncate table t_whale_top_buyer;
		# select addr,whale_whale_ranking,whale_whale_holding_value,volume,coll_num,sale_num from t_whale_top_buyer;
		table_name = "t_whale_top_buyer"
		url = self.list_topBuyer.format(time_rank)
		result = self.get_request_nftgo(url)
		for data in result:
			tags, volume = data.get("tags", ""), data.get("volume", 0)
			coll_num, sale_num = data.get("collNum", 0), data.get("saleNum", 0)
			address, blockchain = tags.get("addr", ""), tags.get("blockchain", "")
			whale_ranking,whale_value = tags.get("whaleRanking", 0), tags.get("whaleHoldingValue", 0)
			top_buyer = {
				"addr": address, "whaleWhaleHoldingValue":whale_value, "whaleWhaleRanking": whale_ranking, "whaleBlockchain": blockchain,
				"collNum": coll_num, "saleNum": sale_num, "volume": volume,"timeState": time_rank
				}

			self.insert_whale_info(table_name, top_buyer)


	def whales_list_topSeller(self, time_rank):
		# truncate table t_whale_top_seller;
		# select addr,whale_whale_ranking,whale_whale_holding_value,volume,coll_num,sale_num from t_whale_top_seller;
		table_name = "t_whale_top_seller"
		url = self.list_topSeller.format(time_rank)
		result = self.get_request_nftgo(url)
		for data in result:
			tags, volume = data.get("tags", ""), data.get("volume", 0)
			coll_num, sale_num = data.get("collNum", 0), data.get("saleNum", 0)
			address, blockchain = tags.get("addr", ""), tags.get("blockchain", "")
			whale_ranking,whale_value = tags.get("whaleRanking", 0), tags.get("whaleHoldingValue", 0)
			top_seller = {
				"addr": address, "whaleWhaleHoldingValue":whale_value, "whaleWhaleRanking": whale_ranking, "whaleBlockchain": blockchain,
				"collNum": coll_num, "saleNum": sale_num, "volume": volume,"timeState": time_rank
				}
			self.insert_whale_info(table_name, top_seller)



	def whales_list_whaleMintColl(self, time_rank):
		# truncate table t_whale_most_minted;
		# select coll_name,coll_logo,whale_num,whale_mint_num,whale_mint_volume,minter_num,total_gas_fee,first_mint_time,time_state from t_whale_most_minted where time_state='24h';
		table_name = "t_whale_most_minted"
		url = self.list_whaleMintColl.format(time_rank)
		result = self.get_request_nftgo(url)
		for data in result:
			coll, coll_tags = data.get("coll", {}), data.get("collTags", {})
			mint_num, whale_num = data.get("whaleMintNum", 0), data.get("whaleNum", 0)
			mint_volume, minter_num = data.get("whaleMintVolume", 0),data.get("minterNum", 0)
			fomo, totalGasFee = data.get("fomo", 0), data.get("totalGasFee", 0)
			blockchain, contract = coll_tags.get("blockchain", ""), coll_tags.get("contract", "")
			name = ( coll["name"] if coll and "name" in coll and coll["name"] else data["contractName"])
			logo = (coll["logo"] if coll and  "logo" in coll else "")
			firstMintTime, from_time = data.get("firstMintTime", 0), data.get("fromTime", 0)
			most_minted = {
				"collName": name, "whaleMintVolume":mint_volume, "minterNum":minter_num,"whaleMintNum":mint_num,"whaleNum":whale_num,
				"fomo": fomo,"totalGasFee": totalGasFee,"collBlockchain": blockchain,"collContracts": contract,"firstMintTime": firstMintTime,
				"collLogo": logo,"timeState": time_rank, "fromTime": from_time
				}
			self.insert_whale_info(table_name, most_minted)


	def whales_list_mintWhale(self, time_rank):
		# truncate table t_whale_top_minter;
		# select whale_addr,whale_holding_value,whale_ranking,mint_num,coll_num,mint_volume,total_gas_fee,time_state from t_whale_top_minter where time_state='24h';
		table_name = "t_whale_top_minter"
		url = self.list_mintWhale.format(time_rank)
		result = self.get_request_nftgo(url)
		for data in result:
			tags = data.get("tags", {})
			address, blockchain = tags.get("addr", ""), tags.get("blockchain", "")
			holding_value = (float(tags["whaleHoldingValue"]) if tags.get("whaleHoldingValue", 0) else 0)
			whale_ranking = (float(tags["whaleRanking"]) if tags.get("whaleRanking", 0) else 0)
			mintNum, collNum = data.get("mintNum", 0), data.get("collNum", 0)
			mintVolume, totalGasFee = data.get("mintVolume", 0), data.get("totalGasFee", 0)
			last_mint_time, from_time = data.get("lastMintTime", 0), data.get("fromTime", 0)
			top_minter = {
				"whaleAddr": address, "whaleBlockchain": blockchain, "whaleHoldingValue": holding_value, "whaleRanking": whale_ranking,
				"mintNum": mintNum,"collNum": collNum, "mintVolume": mintVolume, "totalGasFee": totalGasFee,"timeState": time_rank,
				"lastMintTime": last_mint_time,"fromTime": from_time
			}
			self.insert_whale_info(table_name, top_minter)

	def get_request_nftgo(self, url):
		playwright = sync_playwright().start()
		browser = playwright.chromium.launch(headless=False)
		page = browser.new_page()
		page.goto(url)
		page.wait_for_load_state("networkidle")
		html = page.content()
		result = re.search(r'pre-wrap;">({.*})</pre>', html).group(1)
		response = json.loads(result)
		browser.close()
		playwright.stop()
		return response["data"]


	def timer_hours_task(self):
		action_list = ["buy", "sell"]
		# Most Whales Involved
		for action in action_list:
			self.api_whales_list(action, "1h")
		# Whales Bought
		for action in action_list:
			self.whales_list_topSales(action, "1h")
		# Top Buyers
		self.whales_list_topBuyer("1h")
		# Top Sellers
		self.whales_list_topSeller("1h")
		# Most Whale Minted
		self.whales_list_whaleMintColl("1h")
		# Top Whale Minters
		self.whales_list_mintWhale("1h")


	def timer_day_task(self):
		# 当天时间戳 2022-05-12 23:59:59
		today_stamp = self.get_today_timestamp()
		action_list, Whale_Activities = ["buy", "sell"], ["all"]
		Most_Whales_Involved, whales_Bough = ["24h", "7d"], ["24h", "7d"]
		Top_Buyers, Top_Sellers = ["24h", "7d"], ["24h", "7d"]
		Most_Whale_Minted, Top_Whale_Minters = ["24h", "7d"], ["24h", "7d"]

		# Most Whales Involved
		for time_rank in Most_Whales_Involved:
			for action in action_list:
				self.api_whales_list(action,time_rank)
		# Whales Bought
		for bough in whales_Bough:
			for action in action_list:
				self.whales_list_topSales(action,bough)
		# Top Buyers
		for top_buy in Top_Buyers:
			self.whales_list_topBuyer(top_buy)
		# Top Sellers
		for top_sell in Top_Sellers:
			self.whales_list_topSeller(top_sell)
		# Most Whale Minted
		for most_minted in Most_Whale_Minted:
			self.whales_list_whaleMintColl(most_minted)
		# Top Whale Minters
		for top_minters in Top_Whale_Minters:
			self.whales_list_mintWhale(top_minters)
		# Whale Activities
		for activity in Whale_Activities:
			self.api_whales_activity(activity, today_stamp)
		# All_Whales
		offset, limit, length = 0, 40, 40
		while True:
			print("--length--:", length, offset)
			if length >= 40:
				offset_len = self.whales_ranking_whales(offset, limit)
				offset = offset + limit
				length = offset_len
			else:
				break


	def start_scheduler(self):
		scheduler = BackgroundScheduler()
		# 每1小时执行一次
		scheduler.add_job(self.timer_hours_task, 'interval', hours=1)
		# 每天执行一次
		scheduler.add_job(self.timer_day_task, 'interval', days=1)
		scheduler.start()
		print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
		try:
			while True:
				time.sleep(2)
		except (KeyboardInterrupt, SystemExit):
			scheduler.shutdown()


if __name__ == '__main__':
	nft = Nftgo()
	nft.start_scheduler()