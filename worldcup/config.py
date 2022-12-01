
# MySQL配置
MYSQL_HOST = '192.168.1.168'
MYSQL_USER = 'root'
MYSQL_PASSWORD = '123456789'
MYSQL_DB = 'world_cup'


team_xls = "team_nft.xlsx"
player_xls = "player_nft.xlsx"
static_flag = "/static/flag/{}.png"
static_nft_flag = "/static/nft_flag/{}.jpg"
static_player = "/static/player/{}"


url = "https://tiyu.baidu.com/match/%E4%B8%96%E7%95%8C%E6%9D%AF/tab/%E6%8E%92%E5%90%8D"
base_url = 'https://tiyu.baidu.com/api/match/%E4%B8%96%E7%95%8C%E6%9D%AF/live/date/2022-{}/direction/after?from=self'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
}

country_info = {
    '卡塔尔': 'Qatar', '厄瓜多尔': 'Ecuador', '塞内加尔': 'Senegal', '荷兰': 'Netherlands', '英格兰': 'England',
    '伊朗': 'Iran', '美国': 'USA', '威尔士': 'Wales', '阿根廷': 'Argentina', '沙特阿拉伯': 'SaudiArabia', '墨西哥': 'Mexico',
    '波兰': 'Poland', '法国': 'France', '丹麦': 'Denmark', '突尼斯': 'Tunisia', '澳大利亚': 'Australia', '西班牙': 'Spain',
    '德国': 'Germany', '日本': 'Japan', '哥斯达黎加': 'Costa Rica', '比利时': 'Belgium', '加拿大': 'Canada', '摩洛哥': 'Morocco',
    '克罗地亚': 'Croatia', '巴西': 'Brazil', '塞尔维亚': 'Serbia', '瑞士': 'Switzerland', '喀麦隆': 'Cameroon', '葡萄牙': 'Portugal',
    '加纳': 'Ghana', '乌拉圭': 'Uruguay', '韩国': 'Korea Republic',
}

days_list = [
    '11-20', '11-21', '11-22', '11-23', '11-24', '11-25', '11-26', '11-27',
    '11-28', '11-29', '11-30', '12-01', '12-02', '12-03', '12-04', '12-05',
    '12-06', '12-08', '12-09', '12-10', '12-13', '12-14', '12-16', '12-17'
]