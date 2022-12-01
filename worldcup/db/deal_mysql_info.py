from WorldCup2022.db.connect_mysql import CUD_data,read_data
import time


def datetime_to_timestamp(ts):
    return int(time.mktime(ts.timetuple()))

def query_event_info(home_team_id, away_team_id):
    sql = "select id, total, end_time from t_event where home_team_id = %s and away_team_id = %s"
    data = [home_team_id, away_team_id]
    event_list = read_data(sql=sql, data=data)
    return event_list

def query_team_id(team_id):
    sql = "select group_name,update_time from t_team where id = %s"
    data = [team_id]
    team_list = read_data(sql=sql, data=data)
    return team_list

def query_team_info(team_name):
    sql = "select id, group_name from t_team where team_name = %s"
    data = [team_name]
    team_list = read_data(sql=sql, data=data)
    return team_list

def query_player_id(player_id):
    sql = "select id,player_name from t_player where id = %s"
    data = [player_id]
    player_list = read_data(sql=sql, data=data)
    return player_list


def insert_event_info(event_info, event_list):
    home_team_id, away_team_id = event_info["home_team_id"], event_info["away_team_id"]
    score_home, score_away =  event_info["score_home"], event_info["score_away"]
    winner,end_time,total = event_info["winner"],event_info["end_time"],event_info["total"]
    end_status = event_info["end_status"]
    query_list = query_event_info(home_team_id, away_team_id)
    if not query_list:
        sql = 'insert into t_event(start_time,group_name,home_team_id,away_team_id,home_team_name,away_team_name,status,bet_status,win_open,score_open, total_open, big_open, end_time, winner, score_home, score_away,pool_total,total,event_type,home_team_logo,away_team_logo,home_team_nft_image,away_team_nft_image) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        data = event_list
        CUD_data(sql, data)
    else:
        event_id, old_total, old_time = query_list[0].get("id"), int(query_list[0].get("total")), query_list[0].get("end_time")
        end_date, old_date = datetime_to_timestamp(end_time), datetime_to_timestamp(old_time)
        if old_total == 0 and end_date < old_date:
            print("--old_total--:", end_time, old_time)
            sql = 'update t_event set end_time = %s, winner = %s, score_home = %s, score_away = %s, total = %s where id = %s'
            data = [end_time, winner, score_home, score_away, total, event_id]
            CUD_data(sql, data)
        else:
            if end_status != "end":
                print("--end_status--:", end_status, [winner, score_home, score_away, total, event_id])
                # select end_time,total,winner, score_home, score_away from t_event;
                sql = 'update t_event set winner = %s, score_home = %s, score_away = %s, total = %s where id = %s'
                data = [winner, score_home, score_away, total, event_id]
                CUD_data(sql, data)


def insert_team_info(team_update,team_list):
    # 判断是否更新
    team_id = team_list[0]
    # total_score  total_lose points total_match win lose draw
    query_team_list = query_team_id(team_id)
    if not query_team_list:
        sql = 'insert into t_team(id,team_name,team_logo,team_NFT_image,total_score,total_lose,points,total_match,win,lose,draw,create_time,update_time,group_name,team_deposit_count) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        data = team_list
        CUD_data(sql, data)
    else:
        # print("--team_update--:", team_update)
        sql = 'update t_team set total_score = %s, total_lose = %s, points = %s, total_match = %s, win = %s, lose = %s, draw = %s  where id = %s'
        data = team_update
        CUD_data(sql, data)


def insert_player_info(player_list):
    player_id = player_list[0]
    query_list = query_player_id(player_id)
    if not query_list:
        sql = 'insert into t_player(id,player_name,player_logo,score,team_id,create_time,update_time) values (%s,%s,%s,%s,%s,%s,%s)'
        data = player_list
        CUD_data(sql, data)
    # else:
    #     player_id = player_list[0].get("id")
    #     sql = 'update t_player set player_logo = %s, update_time = %s where id = %s'
    #     data = [player_logo, datetime_now, player_id]
    #     CUD_data(sql, data)