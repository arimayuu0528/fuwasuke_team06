# from flask import Blueprint,render_template,request,session,redirect,url_for,flash
# from datetime import date, datetime  # 今日の日付や日時計算に使う
# from app.db import DatabaseManager

# # Blueprintオブジェクト作成
# task_bp = Blueprint('task',__name__,url_prefix='/task')


# # -----------------------------------------------------
# # タスク(ホーム)：担当者名 向山
# # -----------------------------------------------------

# @task_bp.route("/task")
# def task_form():
#     rec=request.form
    
#     # エンドポイント名、関数名は各自変更してください。
#     pass

# # -----------------------------------------------------
# # タスク一覧：担当者名 向山
# # -----------------------------------------------------

# @task_bp.route("/task_list")
# def task_list():
#     pass

# # -----------------------------------------------------
# # タスク作成：担当者名 向山
# # -----------------------------------------------------

# @task_bp.route("/task_create")
# def task_create():
#     pass

# # -----------------------------------------------------------------------------------
# # タスク提案：担当者名 有馬
# # -----------------------------------------------------------------------------------
# # ***********************************************************************************
# #  関数
# # ***********************************************************************************
# # -----------------------------------------------------------------------------------
# # 値を範囲内に押し込む [目標タスクレベル]
# # -----------------------------------------------------------------------------------
# def clamp_int(value: int, min_value: int, max_value: int) -> int:
#     """数値を[min_value, max_value]に収めて返す"""  # 閾値で丸める関数
#     return max(min_value, min(max_value, value))  # 最小/最大の範囲に収める

# # -----------------------------------------------------------------------------------
# # 時刻を 分 に戻す
# # -----------------------------------------------------------------------------------
# def time_to_minutes(t) -> int:
#     """datetime.time -> 分に変換"""  # time型を分に変換する
#     return t.hour * 60 + t.minute  # 例：07:30 -> 450
# # -----------------------------------------------------------------------------------
# # 今のユーザーIDを決める
# # -----------------------------------------------------------------------------------
# def get_current_user_id() -> int:
#     """
#     user_id を取得する（保険付き）
#     1) session["user_id"] があればそれ
#     2) 開発用に ?user_id=1 のクエリも許可
#     3) それも無ければ 1 を返す（開発用）
#     """  # ログイン未完成でも動くようにする
#     session_user_id = session.get("user_id")  # セッションから user_id を取得
#     if session_user_id:                       # セッションに user_id があるなら
#         return int(session_user_id)           # int化して返す

#     query_user_id = request.args.get("user_id", type=int)  # URLクエリから user_id を取得
#     if query_user_id:                                      # クエリに user_id があるなら
#         return int(query_user_id)                          # int化して返す

#     return 1  # 最後の保険：開発用に user_id=1 を返す

# # ---------------------------------------------------------------------------------------------
# # 【DB取得】「今日の気分点（mood_point）」をDBから取得 無ければデフォルトを返す
# # ---------------------------------------------------------------------------------------------
# def fetch_today_mood(conn, user_id: int) -> tuple[str, int]:
#     """
#     今日の最新の気分（t_today_moods）を1件取る
#     無ければ 普通(2) を返す
#     """  # 今日の気分をDBから取る
#     today = date.today()  # 今日の日付を作る

#     sql = """  # 今日の気分（最新1件）を取るSQL
#         SELECT mood, mood_point
#         FROM t_today_moods
#         WHERE user_id = %s AND DATE(mood_date) = %s
#         ORDER BY mood_date DESC
#         LIMIT 1;
#     """

#     cursor = conn.cursor(dictionary=True)  # dict形式で取れるカーソル
#     cursor.execute(sql, (user_id, today))  # SQLを実行
#     mood_row = cursor.fetchone()  # 1件取得
#     cursor.close()  # カーソルを閉じる

#     if mood_row:  # 取得できた場合
#         return mood_row["mood"], int(mood_row["mood_point"])  # moodとmood_pointを返す

#     return "普通", 2  # 無い場合はデフォルト（普通=2）
# # ----------------------------------------------------------------------------------------------
# # 
# # ----------------------------------------------------------------------------------------------
# def calc_available_minutes(conn, user_id: int) -> int:
#     """
#     今日使える時間（分）を計算する
#     活動可能時間 = (sleep_time - wakeup_time)
#     固定予定合計 = Σ(end_time - start_time) ※キャンセル除外
#     使える時間 = 活動可能時間 - 固定予定合計
#     最低60分は確保する
#     """  # 今日の作業可能分数を返す
#     today = date.today()  # 今日の日付

#     cursor = conn.cursor(dictionary=True)  # dictカーソルを作る

#     cursor.execute(  # ユーザーの起床/就寝を取る
#         "SELECT wakeup_time, sleep_time FROM t_users WHERE user_id=%s;",
#         (user_id,),
#     )
#     user_row = cursor.fetchone()  # 1件取得
#     if not user_row:  # ユーザーが取れないなら
#         cursor.close()  # カーソルを閉じる
#         return 60  # 最低60分を返す
#         wake_minutes = time_to_minutes(user_row["wakeup_time"])  # 起床時刻を分に
#     sleep_minutes = time_to_minutes(user_row["sleep_time"])  # 就寝時刻を分に
#     active_minutes = sleep_minutes - wake_minutes  # 活動可能時間（分）

#     sql_fixed = """  # 今日の固定予定（インスタンス）を取るSQL
#         SELECT i.start_time, i.end_time
#         FROM t_fixed_schedule_instances i
#         JOIN t_fixed_schedule_masters m ON i.master_id = m.master_id
#         WHERE m.user_id = %s
#           AND i.schedule_date = %s
#           AND i.is_cancelled = 0;
#     """

#     cursor.execute(sql_fixed, (user_id, today))  # 固定予定のSQL実行
#     fixed_rows = cursor.fetchall()  # 固定予定を全件取得
#     cursor.close()  # カーソルを閉じる

#     fixed_minutes_sum = 0  # 固定予定の合計分数
#     for r in fixed_rows:  # 固定予定を1件ずつ処理
#         start_m = time_to_minutes(r["start_time"])  # 開始を分に
#         end_m = time_to_minutes(r["end_time"])  # 終了を分に
#         fixed_minutes_sum += max(0, end_m - start_m)  # マイナス対策しつつ加算

#     available = active_minutes - fixed_minutes_sum  # 使える時間（分）= 活動可能 - 固定予定
#     return max(60, available)  # 最低60分を保証して返す
# # ----------------------------------------------------------------------------------------------------
# # 
# # ----------------------------------------------------------------------------------------------------
# def fetch_today_suggestion(conn, user_id: int):
#     """今日の提案ヘッダ（t_task_suggestions）があれば1件返す（無ければNone）"""  # 既に提案があるか確認
#     today = date.today()  # 今日の日付

#     sql = """  # 今日の提案ヘッダを取るSQL
#         SELECT *
#         FROM t_task_suggestions
#         WHERE user_id = %s AND suggestion_date = %s
#         LIMIT 1;
#     """

#     cursor = conn.cursor(dictionary=True)  # dictカーソル
#     cursor.execute(sql, (user_id, today))  # SQL実行
#     suggestion_row = cursor.fetchone()  # 1件取得
#     cursor.close()  # 閉じる

#     return suggestion_row  # dict or None を返す
# # ------------------------------------------------------------------------------------------------------
# # 
# # ------------------------------------------------------------------------------------------------------

# def fetch_suggestion_details(conn, suggestion_id: int):
#     """提案詳細（detail）＋タスク情報（tasks）をJOINして一覧で返す"""  # 画面表示用にまとめて取る
#     sql = """  # detail と tasks を結合して表示に必要な情報を取得
#         SELECT
#             d.*,
#             t.task_name,
#             t.category_name,
#             t.deadline,
#             t.remaining_min AS current_remaining_min,
#             COALESCE(t.task_level, t.motivation_id) AS task_level
#         FROM t_task_suggestion_detail d
#         JOIN t_tasks t ON d.task_id = t.task_id
#         WHERE d.task_suggestion_id = %s
#         ORDER BY d.priority_score DESC, d.plan_min DESC;
#     """

#     cursor = conn.cursor(dictionary=True)  # dictカーソル
#     cursor.execute(sql, (suggestion_id,))  # SQL実行
#     detail_rows = cursor.fetchall()  # 全件取得
#     cursor.close()  # 閉じる

#     return detail_rows  # 一覧を返す
# # ------------------------------------------------------------------------------------------------------
# @task_bp.route("/task_suggestion")
# def task_suggestion():
    
#     return render_template('suggestion_task.html')