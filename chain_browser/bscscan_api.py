import requests
import json
import time
import datetime

class Bscscan():

    def __init__(self):
        self.api_key = "xxxxx" # 申请的api_key
        self.api_url = "https://api.bscscan.com/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
        }

    def get_http_request(self, url):
        res = requests.get(url=url, headers=self.headers, timeout=60)
        response = json.loads(res.text)
        if not response["result"]:
            print("--response--:", response)
        return response["result"]

    def timestamp_to_str(self, ts, fmt=None):
        t = time.localtime(ts)
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return time.strftime(fmt, t)

    def str_to_timestamp(self, s, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        t = datetime.datetime.strptime(s, fmt).timetuple()
        return int(time.mktime(t))


    def get_erc20_token_transfer_events_by_address(self, contract_address):
        try:
            offset, page = 100, 1
            total_num, total_quantity = 0, 0
            transfer_list = []
            now_stamp = self.str_to_timestamp(str(datetime.date.today()) + " 00:00:00")
            for index in range(1, 100):
                url = "{}api?module=account&action=tokentx&contractaddress={}&page={}&offset={}&sort=desc&apikey={}".format(
                    self.api_url, contract_address, page, offset, self.api_key)
                res_list = self.get_http_request(url)
                for transfer in res_list:
                    time_stamp = int(transfer["timeStamp"])
                    txn_hash, time_date = transfer["hash"], self.timestamp_to_str(time_stamp)
                    _from, _to = transfer["from"], transfer["to"]
                    quantity = float(transfer["value"]) / 1000000000000000000
                    print("--transfer--:", time_stamp, now_stamp)
                    if time_stamp >= now_stamp:
                        total_num = total_num + 1
                        total_quantity = total_quantity + quantity
                        transaction = {"txn_hash": txn_hash, "age": time_date, "from": _from, "to": _to,"quantity": quantity}
                        transfer_list.append(transaction)
                    else:
                        break
                time.sleep(5)
                page = page + 1
            print("--events--:", page, total_num, round(total_quantity, 2))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    bsc = Bscscan()
    address = "0x3203c9e46ca618c8c1ce5dc67e7e9d75f5da2377"
    bsc.get_erc20_token_transfer_events_by_address(address)
