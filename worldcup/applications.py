import sys, os
sys.path.append(os.pardir)
import re
import requests
import json
from config import *
from utils import *
from db.deal_mysql_info import *
import threading
import schedule


class WorldCup():

    def __init__(self):
        self.team_excel = read_team_excel()

    def deal_parse_data(self, data):
        datetime_now = str_to_datetime(datetime.datetime.now().strftime("%Y-%m-%d %X"))
        status, bet_status, win_open, score_open, total_open = 0, 2, 0, 0, 0
        big_open, pool_total, event_type = 0, 0, 1

        left, right = data['leftLogo'], data['rightLogo']
        score_home = (0 if left['score'] == '-' else int(left['score']))
        score_away = (0 if right['score'] == '-' else int(right['score']))
        start_time = str_to_datetime(data['startTime'])
        end_date = start_time + datetime.timedelta(hours=3)
        home_team_name, away_team_name = country_info[left['name']], country_info[right['name']]
        left_info = query_team_info(home_team_name)[0]
        home_team_id, group_name = left_info.get('id', 0), left_info.get('group_name', "")
        right_info = query_team_info(away_team_name)[0]
        away_team_id = right_info.get('id', 0)
        home_team_logo, away_team_logo = static_flag.format(home_team_name), static_flag.format(away_team_name)
        home_team_nft_image = static_nft_flag.format(home_team_id)
        away_team_nft_image = static_nft_flag.format(away_team_id)

        winner = (1 if score_home > score_away else 2 if score_home < score_away else 0)
        total = score_home + score_away
        end_time = ( datetime_now if data['matchStatusText'] == "已结束" else end_date)
        end_status = ( "end" if data['matchStatusText'] == "已结束" else "start")

        event_update = {'home_team_id': home_team_id, 'away_team_id': away_team_id,
                      'score_home': score_home, 'score_away': score_away, 'total': total,
                      'winner': winner,'end_time': end_time, 'end_status': end_status}
        event_list = [
            start_time, group_name, home_team_id, away_team_id, home_team_name, away_team_name, status, bet_status,
            win_open, score_open, total_open, big_open, end_time, winner, score_home, score_away, pool_total, total,
            event_type, home_team_logo, away_team_logo, home_team_nft_image, away_team_nft_image
        ]
        return event_update, event_list

    def deal_team_info(self, team_info):
        datetime_now = str_to_datetime(datetime.datetime.now().strftime("%Y-%m-%d %X"))
        team_name = country_info[team_info["name"]]
        team_id, points = team_info["team_id"], team_info["points"]
        team_logo = static_flag.format(team_name)
        team_NFT_image = static_nft_flag.format(team_id)
        win, lose, draw,team_deposit_count = team_info["win"], team_info["lose"], team_info["draw"], 0
        total_match, group_name = team_info["total_match"], team_info["group_name"]
        total_score, total_lose = team_info["total_score"], team_info["total_lose"]
        team_update = [total_score, total_lose, points, total_match, win, lose,draw, team_id]
        team_list = [
            team_id, team_name, team_logo, team_NFT_image, total_score, total_lose, points, total_match, win, lose,
            draw,datetime_now, datetime_now, group_name, team_deposit_count
        ]
        # print("------team_update-------:", team_update)
        insert_team_info(team_update,team_list)


    def deal_player_info(self, result):
        player_logo = ""
        datetime_now = str_to_datetime(datetime.datetime.now().strftime("%Y-%m-%d %X"))
        player_id, player_name = result["player_id"], result["player_name"]
        team_id, score = result["team_id"], result["score"]
        file_path = get_file_path("player")
        file_list = os.listdir(file_path)
        for file_name in file_list:
            soccer_id = file_name.split(".")[0]
            if soccer_id == player_id:
                player_logo = static_player.format(file_name)
                break
            else:
                continue
        player_list = [player_id, player_name, player_logo, score, team_id, datetime_now, datetime_now]
        # print("------player_list-------:", player_list)
        insert_player_info(player_list)


    def deal_ranking_data(self, ranking):
        ranking_data, ranking_title = ranking["tabList"], ranking["title"]
        group_list, match_ups = ranking_data[0]["data"], ranking_data[1]["matchUps"]
        for data in group_list:
            team_list, group_name = data["list"], data["title"].replace("组", "")
            for info in team_list:
                record_list, link = info["record"], info["link"]
                team_name = record_list[0]["name"]
                # team_id, na_tab_info = info["teamId"], info["naTabInfo"]
                for excel in self.team_excel:
                    if team_name == excel['team_name']:
                        team_id, goals = excel['team_id'], record_list[2].split("/")
                        win, draw, lose = goals[0], goals[1], goals[2]
                        in_out_info = record_list[3].split("/")
                        total_score, total_lose = in_out_info[0], in_out_info[1]
                        record_info = {
                            "team_id": team_id, "group_name": group_name, "total_match": record_list[1],
                            "win": win, "draw": draw, "lose": lose, "points": record_list[4],
                            "total_score": total_score,"total_lose": total_lose
                        }
                        record_info.update(record_list[0])
                        self.deal_team_info(record_info)
                        break
                    else:
                        continue

    def deal_event_data(self):
        try:
            urls = get_urls(days_list)
            for url in urls:
                resp = requests.get(url=url, headers=headers)
                for event in resp.json()['data'][0]['list']:
                    left_name = event['leftLogo']['name']
                    right_name = event['rightLogo']['name']
                    if left_name.isalpha() and right_name.isalpha():
                        event_data, event_list = self.deal_parse_data(event)
                        insert_event_info(event_data, event_list)
                    else:
                        continue
                time.sleep(3)
        except Exception as e:
            print("event_data error: {}".format(e))


    def read_player_excel(self):
        file_excel = "excel"
        xls_path = get_excel_path(file_excel,player_xls)
        sheet = pd.read_excel(xls_path)
        for data in sheet.values:
            excel_info, score = {}, 0
            player_id = str(data[0]).strip()
            country_id = str(data[2]).strip()
            player_name = str(data[3]).strip()
            for excel in self.team_excel:
                if country_id == excel['country_id']:
                    team_id = excel['team_id']
                    excel_info.update({'player_id': player_id, 'player_name': player_name, 'score': score, 'team_id': team_id})
                    self.deal_player_info(excel_info)
                    break
                else:
                    continue

    def get_world_cup_info(self):
        # https://tiyu.baidu.com/api/realtime?&pn=10&word=%E4%B8%96%E7%95%8C%E6%9D%AF   #新闻
        print("world_cup--:{}".format(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')))
        response = requests.get(url=url, headers=headers)
        html = response.text
        result = re.search(r'opts.contentData =(.*)', html).group(1).rstrip(";")
        json_info = json.loads(result)["data"]["tabsList"]
        schedule, ranking, foot_ball = json_info[0], json_info[1], json_info[2]
        self.deal_ranking_data(ranking)
        self.deal_event_data()
        # self.read_player_excel()

    def job_task(self):
        threading.Thread(target=self.get_world_cup_info).start()


    def start_scheduler(self):
        schedule.every(3).minutes.do(self.job_task)

        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':
    # nohup python3 -u applications.py >world_cup.log 2>&1 &
    w_cup = WorldCup()
    w_cup.start_scheduler()

