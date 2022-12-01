import requests
import json

insert_url = ""
query_url = ""


headers = {
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
        }

def call_query_mysql(query_games): # mysql2022
    currency_list = []
    table = query_games["table"]
    try:
        data = json.dumps(query_games)
        res = requests.post(url= query_url, headers=headers, data=data, timeout=20)
        result = json.loads(res.text)
        if result["msg"] == "ok":
            currency_list = result["data"]
        return currency_list
    except Exception as e:
        print("query {} error:{}".format(table, e))
        return currency_list


def call_insert_mysql(table, game_info):
    result = {}
    try:
        json_info = json.dumps(game_info)
        req_info = {"table": table, "data": json_info}
        games = json.dumps(req_info)
        res = requests.post(url=insert_url, headers=headers ,data=games, timeout=20)
        result = json.loads(res.text)
        return result
    except Exception as e:
        print("insert or update {} error:{}".format(table, e))
        return result


def call_delete_mysql(table):
    result = {}
    try:
        req_info = {"table": table}
        games = json.dumps(req_info)
        res = requests.post(url=insert_url, headers=headers ,data=games, timeout=20)
        result = json.loads(res.text)
        return result
    except Exception as e:
        print("delete {} error:{}".format(table, e))
        return result