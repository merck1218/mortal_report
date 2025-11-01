import urllib.request, json, datetime, sys
from app.services import get_db_connection, reports, statistics
from app import config

def new_order_function(json):
    # 変数宣言
    url = json.get('url')
    dst_path = config.Config.DST_PATH

    # JSONファイルダウンロード関数呼び出し
    mortal_json_path = download_json_function(url,dst_path)

    # gameidの取得関数呼び出し
    gameid = create_gameid_function()

    # 統計情報関数呼び出し
    statistic = create_statistics_function(mortal_json_path)

    # レポート関数呼び出し
    report = create_reports_function(json)

    # 結果保存
    statistics.new_statistics_function(gameid, statistic)
    reports.new_reports_function(gameid, report)

    # 結果返却
    message = {"status": "success"}
    return message


def download_json_function(url,path):
    # URL判定 + ダウンロード
    if ("mjai.ekyu.moe" in url):
        json_filename = url.split("/")[6]
        json_url = "https://mjai.ekyu.moe/report/" + json_filename
        urllib.request.urlretrieve(json_url, path + "/" + json_filename)
        return path + "/" + json_filename
    elif ("review.bigcoach.work" in url):
        json_filename = url.split("/")[4] + ".json"
        json_url = "https://review.bigcoach.work/output/" + json_filename
        urllib.request.urlretrieve(json_url, path + "/" + json_filename)
        return path + "/" + json_filename
    else:
        sys.exit("Unsupported URL")


def create_gameid_function():
    # SQL文生成
    today = datetime.date.today()
    date = today.strftime("%Y%m%d")
    sql_text = f"SELECT max(game_id) FROM reports WHERE game_id::TEXT LIKE '{date}%' HAVING max(game_id) IS NOT NULL;"

    # SQL実行処理
    conn = get_db_connection.get_connection()
    cur = conn.cursor()
    cur.execute(sql_text)
    rows = cur.fetchall()
    cur.close
    conn.close

    # ゲームID生成
    gameid = int(rows[0][0]) + 1 if rows != [] else int(date + "001")
    return gameid


def create_statistics_function(json_path):
    # プレイヤーの開始位置関数
    def player_number_function():
        # プレイヤーID取得
        actor_id = json_load['review']['kyokus'][0]['entries'][0]['actual']['actor']
        
        # 結果返却
        return actor_id
    
    # プレイヤーのポイント、順位関数
    def player_point_function():
        # プレイヤー情報読み込み
        player_data = json_load['mjai_log']
        player_data_dictionary = {}
        game_default_point = 0
        game_total_point = 0
        difference_point = 0

        # プレイヤーごとにループ処理
        for player in range(4):
            # 初期点数
            default_point_data = [item for item in player_data if item['type'] == 'start_kyoku' and item['bakaze'] == 'E' and item['kyoku'] == 1 and item['honba'] == 0]
            default_point = [item['scores'] for item in default_point_data][0][player]

            # リーチ数のカウント
            reach_count = 0
            reach_data = [item for item in player_data if item['type'] == 'reach_accepted' and item['actor'] == player]
            reach_count = len(reach_data)

            # 獲得したポイント
            get_point = 0
            get_point_data = [item for item in player_data if item['type'] == 'hora' or item['type'] == 'ryukyoku']
            get_point_data_delta = [item['deltas'][player] for item in get_point_data]
            get_point = sum(get_point_data_delta)

            # 総得点
            total_point = default_point + get_point -(reach_count * 1000)
            game_default_point += default_point
            game_total_point += total_point

            # 辞書登録
            player_data_dictionary[player] = total_point
        
        # オーラス供託処理
        if game_total_point != game_default_point:
            difference_point = game_default_point - game_total_point

        # 順位処理
        sorted_players = sorted(player_data_dictionary.items(), key=lambda x: x[1], reverse=True)
        for rank, (player, points) in enumerate(sorted_players, start=1):
            if rank == 1:
                points += difference_point
            player_data_dictionary[player] = (points, rank)
        
        # 結果返却
        return player_data_dictionary
    
    # 悪手関数
    def bad_choice_function():
        # SQL実行処理
        conn = get_db_connection.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE item = 'dealin_shanten_border'")
        rows = cur.fetchall()
        cur.close
        conn.close

        # 悪手基準
        dealin_shanten_border = int(rows[0][0]) * 0.01
        
        # 悪手データ読み込み
        bad_choice_data = json_load['review']['kyokus']
        bad_choice_entries_data = [item['entries'] for item in bad_choice_data]
        bad_choice_dictionary = {}
        bad_choice_count = 0
        bad_choice_data_length = len(bad_choice_data)

        # 悪手データループ
        for kyoku in range(bad_choice_data_length):
            kyoku_num = [item['kyoku'] for item in bad_choice_data][kyoku]
            honba_num = [item['honba'] for item in bad_choice_data][kyoku]
            kyoku_data = bad_choice_entries_data[kyoku]
            kyoku_list = []

            # 不一致データ
            not_equal_actuals = [item['actual'] for item in kyoku_data if item['is_equal'] == False]
            not_equal_details = [item['details'] for item in kyoku_data if item['is_equal'] == False]
            not_equal_length = len(not_equal_actuals)

            # 不一致データループ
            for i in range(not_equal_length):
                not_equal_actual = not_equal_actuals[i]
                not_equal_detail = not_equal_details[i]
                prob_data = [item['prob'] for item in not_equal_detail if item['action'] == not_equal_actual and item['prob'] <= dealin_shanten_border]

                if prob_data != []:
                    kyoku_list.append(prob_data[0])
            
            bad_choice_dictionary[(kyoku_num, honba_num)] = kyoku_list
            bad_choice_count += len(kyoku_list)
        
        return bad_choice_count
    
    # 放銃時平均シャンテン数関数
    def dealin_avg_shanetn_function(my_id):
        # 放銃データ読み込み
        dealin_data = json_load['review']['kyokus']
        dealin_dictionary = {}
        dealin_count = 0
        dealin_shanten = 0
        dealin_data_length = len(dealin_data)

        # 放銃データループ
        for kyoku in range(dealin_data_length):
            # 局データ
            kyoku_data = [item['entries'] for item in dealin_data][kyoku]
            kyoku_data_length = len(kyoku_data)
            kyoku_num = [item['kyoku'] for item in dealin_data][kyoku]
            honba_num = [item['honba'] for item in dealin_data][kyoku]

            # 終了ステータス
            end_status_data = [item['end_status'] for item in dealin_data][kyoku]
            actor = [item['actor'] for item in end_status_data if item['type'] == 'hora']
            target = [item['target'] for item in end_status_data if item['type'] == 'hora']

            if actor != []:
                actor = actor[0]
            
            if target != []:
                target = target[0]

            # 放銃チェック
            if actor != my_id and target == my_id:
                dealin_shanten += [item['shanten'] for item in kyoku_data][kyoku_data_length -1]
                dealin_count += 1
            
        return dealin_count, dealin_shanten


    # 基本処理
    json_open = open(json_path)
    json_load = json.load(json_open)

    # 標準情報
    rating = json_load['review']['rating']
    total_reviewed = json_load['review']['total_reviewed']
    total_matches = json_load['review']['total_matches']
    match_rate = total_matches / total_reviewed

    # プレイヤー情報
    my_id = player_number_function()
    shimocha_id = my_id + 1 if my_id < 3 else my_id - 3
    toimen_id = my_id + 2 if my_id < 2 else my_id -2
    kamicha_id = my_id +3 if my_id <1 else my_id -1 
    
    player_info = player_point_function()
    my_point = player_info[my_id][0]
    my_rank = player_info[my_id][1]
    shimocha_point = player_info[shimocha_id][0]
    shimocha_rank = player_info[shimocha_id][1]
    toimen_point = player_info[toimen_id][0]
    toimen_rank = player_info[toimen_id][1]
    kamicha_point = player_info[kamicha_id][0]
    kamicha_rank = player_info[kamicha_id][1]

    # 悪手情報
    total_bad = bad_choice_function()
    bad_rate = total_bad / total_matches

    # 放銃時平均シャンテン数
    dealin_data = dealin_avg_shanetn_function(my_id)
    dealin_count = dealin_data[0]
    dealin_shanten = dealin_data[1]

    # 結果返却
    statistics = [my_point, my_rank, shimocha_point, shimocha_rank, toimen_point, toimen_rank, kamicha_point, kamicha_rank, rating, total_reviewed, total_matches, total_bad, match_rate, bad_rate, dealin_count, dealin_shanten]
    return statistics


def create_reports_function(json_path):
    # JSONファイル名切り出し
    url = json_path.get('url')
    if ("mjai.ekyu.moe" in url):
        json_filename = url.split("/")[6]
    elif ("review.bigcoach.work" in url):
        json_filename = url.split("/")[4] + ".json"
    else:
        pass
  
    # レポートURL生成
    server = config.Config.SERVER_HOST
    report_url = f"http://{server}/killerducky/?data=/report/{json_filename}"

    # MAKA評価
    maka = json_path.get('maka')

    # 対局日程
    game_date = json_path.get('date')

    # 結果返却
    result = [game_date, maka, report_url]
    return result