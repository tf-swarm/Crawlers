import time
import hmac
import urllib.parse
import hashlib
import base64
import requests
import json
import datetime


def ding(file):
    dd_secret = 'xxxx' #需要开启机器人加签 此处为加签的secret
    dd_token = 'xx' #自定义机器人的 token

    timestamp = str(round(time.time() * 1000))
    secret = dd_secret  # 钉钉secret

    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    # https://oapi.dingtalk.com/robot/send?access_token=70cf02d367
    url = 'https://oapi.dingtalk.com/robot/send?access_token=' + dd_token + '&timestamp=' + timestamp + '&sign=' + sign
    # print(url)
    dd_txt = '-要发送的内容\n' \
             f'{file} 运行失败  {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}'
    data = {
        "msgtype": "text",
        "text": {"content": dd_txt}
    }
    headers = {'Content-Type': 'application/json'}
    res = requests.post(url=url, data=json.dumps(data), headers=headers)





