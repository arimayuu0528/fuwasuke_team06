# 0224
from flask import Blueprint,render_template,request,session,redirect,url_for
from datetime import date,datetime
from datetime import time as dt_time, timedelta
from app.db import DatabaseManager

import traceback

# Blueprintオブジェクト作成
task_bp = Blueprint('task',__name__,url_prefix='/task')

# -----------------------------------------------------
# タスク(ホーム)：担当者名 向山 
# -----------------------------------------------------

@task_bp.route("/task", methods=["GET","POST"])
def task_form():
    # ----------------------------
    # GET（リダイレクト先として使う）
    # ----------------------------
    if request.method == "GET":
        # 優先：開始済み → 選択済み → クエリ＜どの提案IDを表示するかの優先順位ルール＞
        suggestion_id = ( # 表示対象の task_suggestion_id を1つに決める（最初に見つかったものを採用)
            session.get("current_task_suggestion_id")           # 今「開始中」の提案ID（セッションに保存されている想定）
            or session.get("selected_task_suggestion_id")       #「選択済み」 の提案ID（セッションに保存されている想定）
            or request.args.get("task_suggestion_id", type=int) # URLの ?task_suggestion_id= をintに変換して取得
        ) # ここまでで suggestion_id が決まる（取得できない場合：None）

        # 提案IDが取得できなかった場合:
        if suggestion_id is None: 
            # 提案を作成/選択する画面へ戻す
            return redirect(url_for("task.task_suggestion"))

        # DB操作クラスをインスタンス化
        db = DatabaseManager()
        # DBへ接続
        db.connect()

        # 例外処理
        try:
            # 提案IDの詳細（タスク一覧 等）をDBから取得
            details = fetch_suggestion_details(db, int(suggestion_id))
            # 取得した提案IDの詳細からtask_nameだけを抽出
            task_names = [row.get("task_name") for row in details if row.get("task_name")]
            # ★追加：task_home.html(JS) 用の rec を作る
            rec = []
            for row in details:
                task_id = row.get("task_id")       # s_detail.* に含まれる想定 :contentReference[oaicite:4]{index=4}
                task_name = row.get("task_name")   # JOINして取れてる :contentReference[oaicite:5]{index=5}
                plan_min = row.get("plan_min")     # s_detail.* に含まれる想定 :contentReference[oaicite:6]{index=6}

                if not task_id or not task_name:
                    continue

                rec.append({
                "id": int(task_id),
                "name": task_name,
                "time": f"{int(plan_min)}分" if plan_min is not None else "",
                "is_fixed": False,
                "repeat_type": "",
                "day_of_week": "",
                "done": False,
                })
            return render_template(
                "task/task_home.html",                  # 表示するHTML
                task_suggestion_id=int(suggestion_id),  # 提案ID（型をintで統一）
                task_names=task_names,                  # タスク名のリスト
                rec=rec,
            )
        finally: # try内で成功/失敗しても必ず通る
            db.disconnect() # DB接続を必ず切断する
    # ----------------------------
    # POST（formから受け取って表示）
    # ----------------------------
    # POST（formから受け取って表示）
    task_suggestion_id = request.form.get("task_suggestion_id", type=int)
    if task_suggestion_id is None:
        task_suggestion_id = session.get("current_task_suggestion_id") or session.get("selected_task_suggestion_id")  # :contentReference[oaicite:10]{index=10}

    if task_suggestion_id is None:
        return redirect(url_for("task.task_suggestion"))

    db = DatabaseManager()
    db.connect()
    try:
        details = fetch_suggestion_details(db, int(task_suggestion_id))  # :contentReference[oaicite:11]{index=11}

        task_names = [row.get("task_name") for row in details if row.get("task_name")]

        rec = []
        for row in details:
            task_id = row.get("task_id")
            task_name = row.get("task_name")
            plan_min = row.get("plan_min")
            if not task_id or not task_name:
                continue
            rec = []
            for i, name in enumerate(task_names):
                rec.append({
                    "id": i + 1,
                    "name": name,
                    "time": "",
                    "is_fixed": False,
                    "repeat_type": "",
                    "day_of_week": "",
                    "done": False,
                })

        return render_template(
            "task/task_home.html",
            task_suggestion_id=int(task_suggestion_id),
            task_names=task_names,
            rec=rec,   # ★必須 :contentReference[oaicite:12]{index=12}
        )
    finally:
        db.disconnect()


# -----------------------------------------------------
# タスク一覧：担当者名 向山
# URL：/task/task_list
# -----------------------------------------------------
@task_bp.route("/task_list")
def task_list():

    # ログインチェック
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('auth.login'))

    today = date.today()

    db = DatabaseManager()
    db.connect()

    sql = """
    SELECT
        t.task_id,
        t.task_name,
        t.motivation_id,
        m.motivation_name,
        t.deadline,
        t.duration_min,
        t.remaining_min,
        t.created_date,
        t.category_name
    FROM t_tasks t
    LEFT JOIN t_motivations m ON t.motivation_id = m.motivation_id
    WHERE t.user_id = %s
    ORDER BY t.deadline, t.task_name
    """

    db.cursor.execute(sql, (user_id,))
    rows = db.cursor.fetchall()

    tasks = []
    for row in rows:
        tasks.append({
            'id':              row['task_id'],
            'title':           row['task_name'],
            'motivation_id':   row['motivation_id'],
            'motivation_name': row['motivation_name'],
            'due_date':        row['deadline'].strftime('%Y/%m/%d') if row['deadline'] else '',
            'duration_min':    row['duration_min'],
            'remaining_min':   row['remaining_min'],
            'created_date':    row['created_date'],
            'category_name':   row['category_name'],
            # 締切が今日以前なら「今日中」バッジ
            'is_today': row['deadline'] is not None and row['deadline'] <= today,
        })

    db.disconnect()

    return render_template('task/task_list.html', tasks=tasks)


# -----------------------------------------------------
# タスク削除
# URL：/task/delete/◯◯
# -----------------------------------------------------
@task_bp.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):

    user_id = session.get("user_id")  # ← ここを変更
    if not user_id:
        return redirect(url_for('auth.login'))  # 未ログインならログインページへ

    db = DatabaseManager()
    db.connect()

    sql = """
    DELETE FROM t_tasks
    WHERE task_id = %s AND user_id = %s
    """

    db.cursor.execute(sql, (task_id, user_id))
    db.connection.commit()
    db.disconnect()

    return redirect(url_for('task.task_list'))

# -----------------------------------------------------
# タスク作成：担当者名 向山
# -----------------------------------------------------

@task_bp.route("/task_create", methods=["GET", "POST"])
def task_create():
    # GET：タスク登録フォームを表示
    if request.method == "GET":
        return render_template("task/task_register.html", task=None)

    # POST：フォームのデータを受け取ってDBに登録
    user_id = get_current_user_id()

    task_name             = request.form.get("title", "").strip()
    category_name         = request.form.get("category", "").strip()
    duration_min          = request.form.get("duration", type=int)
    deadline              = request.form.get("date", "").strip()
    motivation_id         = request.form.get("motivation", type=int) or 1
    notification_enabled  = request.form.get("notification_enabled", type=int) or 1
    notification_min      = request.form.get("notification_min", type=int) or 5

    errors = []
    if not task_name:
        errors.append("タスク名を入力してください")
    if duration_min is None or duration_min <= 0:
        errors.append("予定時間を選択してください")
    if not deadline:
        errors.append("日付を入力してください")

    if errors:
        return render_template(
            "task/task_register.html",
            errors=errors,
            task={
                "title":                task_name,
                "category":             category_name,
                "duration":             duration_min,
                "date":                 deadline,
                "motivation":           motivation_id,
                "notification_enabled": notification_enabled,
                "notification_min":     notification_min,
            },
        )

    db = DatabaseManager()
    db.connect()

    try:
        sql = """
            INSERT INTO t_tasks
                (user_id, task_name, motivation_id, deadline,
                 duration_min, remaining_min, created_date, category_name)
            VALUES
                (%s, %s, %s, %s, %s, %s, CURDATE(), %s)
        """
        db.cursor.execute(sql, (
            user_id,
            task_name,
            motivation_id,
            deadline      or None,
            duration_min,
            duration_min,
            category_name or None,
        ))
        db.connection.commit()

    except Exception as e:
        db.connection.rollback()
        raise e

    finally:
        db.disconnect()

    return redirect(url_for("task.task_list"))

# -------------------------------------------------------------------------------------------------------------------
# タスク提案：担当者名 有馬
# -------------------------------------------------------------------------------------------------------------------
# *** 関数 **********************************************************************************************************
# -------------------------------------------------------------------------------------------------------------------
# 整数 value を [min_value,max_value]の範囲に収めて返す関数
# -------------------------------------------------------------------------------------------------------------------
def clamp_int(value: int, min_value: int, max_value: int) -> int: # 【定義】： 戻り値 int
    if value < min_value: # もし value が 下限(min_value) より 小さい場合：
        return min_value  # 下限(min_value) を返す
    if value > max_value: # もし value が 下限(max_value) より 大きい場合：
        return max_value  # 上限(max_value) を返す
    return value # どちらでもなければ範囲内の為 value をそのまま返す
# -------------------------------------------------------------------------------------------------------------------
# 時刻(time_obj)を ｢分(int)｣に変換して返す関数
# -------------------------------------------------------------------------------------------------------------------
def time_to_minutes(time_obj):
    # Noneの場合：
    if time_obj is None:
        return 0 #  0 分として扱う（安全）

    if isinstance(time_obj, timedelta): # timedelta(経過時間)の場合：
        # 秒 → 分 に直して返す
        return int(time_obj.total_seconds() // 60) # 例) timedelta(seconds=28800) → 480分


    if isinstance(time_obj, dt_time):   # datetime.time(時刻)の場合：
        return time_obj.hour * 60 + time_obj.minute # 分にする 例) 07:30 → 7*60+30 → 450分

    if isinstance(time_obj, str):       # 文字列の場合
        parts = time_obj.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return hour * 60 + minute

    # それ以外の型が来たら原因が分かるように落とす
    raise TypeError(f"time_to_minutes: unsupported type: {type(time_obj)} value={time_obj!r}")
# -------------------------------------------------------------------------------------------------------------------
# 今、アクセスしている人の user_id を取得して int(整数) で返す関数
# -------------------------------------------------------------------------------------------------------------------
def get_current_user_id() -> int:     # 【定義】： 戻り値 int
    user_id_in_session = session.get("user_id") # セッション(ログイン情報) から user_id を取り出す (無ければ None)
    if user_id_in_session is not None:          # セッションに user_id が入っている(=ログイン済み)場合：
        return int(user_id_in_session)          # intに変換して返す ※文字列等の可能性

    user_id_in_query = request.args.get("user_id", type=int) # URLの ?user_id=　 をintとして取得 (変換できない/無ければ None)
    if user_id_in_query is not None:            # クエリに user_id が入っている場合：
        return int(user_id_in_query)            # intに変換して返す
    # ---------------------------------------------------------------------------------------------------------------
    return 1                          # 【開発用：仮IDを1とする】セッションもクエリもない場合
# -------------------------------------------------------------------------------------------------------------------
# 今日の気分( mood / mood_point ) をDBから1件取得して 無ければデフォルト(普通,2)を返す関数
# -------------------------------------------------------------------------------------------------------------------
def fetch_today_mood(db: DatabaseManager, user_id: int) -> tuple[str, int]: #【定義】： 戻り値 str , int
    today = date.today()              # 今日の日付(例：2026-02-07)を作成

    # ---------------------------------------------------------------------------------------------------------------
    # 気分の文字列(mood),気分点(mood_point) を 今日の気分テーブル(t_today_moods)から取得
    #【WHERE(条件)】指定ユーザー & 今日の日付
    #【ORDER BY(並び順)】  最新の記録
    #【LIMIT(1件だけ取得)】
    sql = """                 
        SELECT mood, mood_point
        FROM t_today_moods
        WHERE user_id = %s AND DATE(mood_date) = %s
        ORDER BY mood_date DESC
        LIMIT 1;
    """
    # ----------------------------------------------------------------------------------------------------------------
    # SQL文を実行し、1件だけ辞書形式で取得
    row = db.fetch_one(sql, (user_id, today))
    if row is not None:  # データが取得できた場合：
        return row["mood"], int(row["mood_point"]) # 気分文字列(mood) , 気分点(mood_point) を返す
    return "普通", 2     # データが無い場合には デフォルト(普通,2)を返す
# -------------------------------------------------------------------------------------------------------------------
# ｢起床～就寝の活動時間(分) - 今日の固定予定(分)｣ を行い、今日使える作業時間(分) を返す関数
# -------------------------------------------------------------------------------------------------------------------
def calc_available_minutes(db: DatabaseManager, user_id: int) -> int: # 【定義】： 戻り値 int
    today = date.today() # 今日の日付(例：2026-02-07)を作成

    # ---------------------------------------------------------------------------------------------------------------
    # 起床時刻(wakeup_time),就寝時刻(sleep_time) を ユーザーテーブル(t_users)から取得
    user_sql = "SELECT wakeup_time, sleep_time FROM t_users WHERE user_id=%s;"
    # ---------------------------------------------------------------------------------------------------------------
    # SQLを実行し、1件だけ辞書形式で取得
    user_row = db.fetch_one(user_sql, (user_id,))
    if user_row is None: # データが無い場合：
        return 60        # 最低60分を返す ※どんな日でもタスク提案ロジックが動くようにする

    wake_minutes = time_to_minutes(user_row["wakeup_time"]) # 関数time_to_minutesで起床時間を｢分｣に変換
    sleep_minutes = time_to_minutes(user_row["sleep_time"]) # 関数time_to_minutesで就寝時間を｢分｣に変換
    active_minutes = sleep_minutes - wake_minutes           # 活動時間＝就寝時間(分)-起床時間(分)
    # ---------------------------------------------------------------------------------------------------------------
    # 開始時刻(start_time),終了時刻(end_time) を取得
    fixed_sql = """
        SELECT ins.start_time, ins.end_time
        FROM t_fixed_schedule_instances ins
        JOIN t_fixed_schedule_masters mas ON ins.master_id = mas.master_id
        WHERE mas.user_id = %s
          AND ins.schedule_date = %s
          AND ins.is_cancelled = 0;
    """
    # ----------------------------------------------------------------------------------------------------------------
    # 固定予定を一覧で取得 (なければ空リストが返る)
    fixed_rows = db.fetch_all(fixed_sql, (user_id, today)) or []
    # 固定予定の合計分数を格納する fixed_minutes_sum を0で初期化
    fixed_minutes_sum = 0
    for row in fixed_rows: # 固定予定リストをループ
        start_m = time_to_minutes(row["start_time"])  # 関数time_to_minutes で開始時刻を｢分｣に変換
        end_m = time_to_minutes(row["end_time"])      # 関数time_to_minutes で終了時刻を｢分｣に変換
        fixed_minutes_sum += max(0, end_m - start_m)  # 固定予定の合計分数に ｢終了時刻-開始時刻｣を加算 ※万が一、終了時刻が開始時刻よりも早い時間だった場合にマイナスにさせないため0未満であれば0を返す

    free_minutes = active_minutes - fixed_minutes_sum # 今日使える作業時間(分)＝｢起床～就寝の活動時間(分) - 今日の固定予定(分)｣
    return max(60, free_minutes)                      # 60未満であれば60を返す ※どんな日でもタスク提案ロジックが動くように最低60分確保
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 今日のタスク提案がDBにあるか確認してあれば取得し、返す関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def fetch_today_suggestion(db: DatabaseManager, user_id: int): # 【定義】
    today = date.today() # 今日の日付(例：2026-02-07)を作成
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # タスク提案(ヘッダ)テーブル t_task_suggestions から全カラム取得 
    #【WHERE(条件)】指定ユーザー&今日の日付
    #【ORDER BY(並び順)】最新の記録
    #【LIMIT(1件だけ取得)】
    sql = """
        SELECT *
        FROM t_task_suggestions
        WHERE user_id = %s AND suggestion_date = %s
        ORDER BY task_suggestion_id DESC
        LIMIT 1;
    """
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    return db.fetch_one(sql, (user_id, today)) # SQL文を実行して結果を返す
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 今日のタスク提案を複数取得する関数 
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def fetch_today_suggestions(db: DatabaseManager, user_id: int):
    today = date.today()
    sql = """
        SELECT *
        FROM t_task_suggestions
        WHERE user_id = %s AND suggestion_date = %s
        ORDER BY task_suggestion_id DESC;
    """
    return db.fetch_all(sql, (user_id, today)) or []
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# タスク提案詳細をDBから取得し、返す関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def fetch_suggestion_details(db: DatabaseManager, suggestion_id: int): #【定義】
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # t_task_suggestion_detail の列全て,
    # t_tasks.task_name,
    # t_tasks.category_name,
    # t_tasks.deadline,
    # t_tasks.remaining_min, ※ 2つのテーブルで｢提案時点｣と｢現在｣を混同しないように別名を付ける
    # ta.motivation_id を取得
    sql = """
        SELECT
            s_detail.*,
            ta.task_name,
            ta.category_name,
            ta.deadline,
            ta.remaining_min AS current_remaining_min,
            ta.motivation_id
        FROM t_task_suggestion_detail s_detail
        JOIN t_tasks ta ON s_detail.task_id = ta.task_id
        WHERE s_detail.task_suggestion_id = %s
        AND ta.is_completed = FALSE
        ORDER BY s_detail.priority_score DESC, s_detail.plan_min DESC;
    """
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # 一覧を取得する(無ければ空リストを返す) 
    return db.fetch_all(sql, (suggestion_id,)) or []
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 係数 ＝ 直近7日間の "実績のタスク難易度" ÷ "気分合計" を作成する関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def calc_coefficient(db: DatabaseManager, user_id: int, today: date) -> float: #【定義】： 戻り値 float
    start_day = today - timedelta(days=7) # 集計開始日：今日から7日前 (直近7日間のはじまり)
    end_day = today - timedelta(days=1)   # 集計終了日：昨日(今日は除外)
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # SUM(mood_point)：気分点を合計
    # COALESCE(  ,0)：合計がNULLになるケース(0件)では気分点0にする
    #【WHERE(条件)】user_id,start_day,end_dayが入る
    mood_sql = """
        SELECT COALESCE(SUM(mood_point), 0) AS mood_sum
        FROM t_task_suggestions
        WHERE user_id=%s AND suggestion_date BETWEEN %s AND %s;
    """
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    mood_row = db.fetch_one(mood_sql, (user_id, start_day, end_day))    # SQLを実行して気分点を取得
    mood_sum = int(mood_row["mood_sum"]) if mood_row is not None else 0 # 合計をintに変換(取得できなければ0)
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # 実績タスクレベル合計を作成するために直近7日間のタスク提案詳細を集める
    # ｢実績割合 × タスクレベル｣ を計算する材料
    detail_sql = """
        SELECT
            s_detail.plan_min,
            s_detail.actual_work_min,
            s_detail.remaining_min_at_suggest,
            ta.motivation_id
        FROM t_task_suggestions sug
        JOIN t_task_suggestion_detail s_detail ON sug.task_suggestion_id = s_detail.task_suggestion_id
        JOIN t_tasks ta ON s_detail.task_id = ta.task_id
        WHERE sug.user_id=%s
          AND sug.suggestion_date BETWEEN %s AND %s;
    """
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # 一覧取得(無ければ空リストが返る)
    detail_rows = db.fetch_all(detail_sql, (user_id, start_day, end_day)) or []
    # 実績タスクレベル合計を格納するための変数を0で初期化
    actual_level_sum = 0.0
    for row in detail_rows: # detailを1件ずつループする
        # タスク提案時点の｢所要時間(残り分数)｣が無い or 0 未満の場合 
        if row["remaining_min_at_suggest"]  is None or int(row["remaining_min_at_suggest"]) <= 0:
            continue        # 次のループに進む
        # 理解しやすいようにtask_levelに格納しておく　※変数名
        task_level = float(row["motivation_id"])
        # 実績分(done_min)に格納
        done_min = row["actual_work_min"]
        if done_min is None: # 実績が未入力の場合：
            done_min = row["plan_min"] # 提案した分数(plan_min)を実績とする
        # 実績分(done_min)をfloat型に揃えておく
        done_min = float(done_min or 0)
        # 実績割合(ratio)を作成：ratio = やった時間/所要時間　※所要時間をやった時間が上回った際は最大1.0に収める
        ratio = min(1.0, done_min / float(row["remaining_min_at_suggest"]))
        # 実績タスクレベル合計に ｢タスクレベル × 実績割合｣ を加算する
        actual_level_sum += task_level * ratio
    # 気分点合計が0だと割れない(初日)ので
    if mood_sum <= 0:
        return 1.0 # 初期係数＝1.0 で返す

    # 係数 ＝ 実績タスクレベル合計 ÷ 気分点合計
    coefficient = actual_level_sum / float(mood_sum)
    # 最小値 0.1 最大値5.0までに収める
    coefficient = max(0.1, min(5.0, coefficient)) 
    # float型に揃えて返す
    return float(coefficient)
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ユーザーからの評価(1~3)を倍率に変換する関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def evaluation_to_multiplier(evaluation: int | None) -> float: #【定義】： 戻り値 float
    if evaluation is None: # 評価なしの場合：
        return 1.0         # 倍率1.0を返す
    elif evaluation == 1:  # 評価1の場合：
        return 0.8         # 倍率0.8を返す
    elif evaluation == 2:  # 評価2の場合：
        return 1.0         # 倍率1.0を返す
    elif evaluation == 3:  # 評価3の場合：
        return 1.2         # 倍率1.2を返す
    else:                  # 想定外の値の場合：
        return 1.0         # 倍率1.0を返す
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 今日の"目標タスクレベル"を決める関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def calc_target_task_level(mood_point: int, eval_mul: float, coefficient: float) -> int: #【定義】： 戻り値 int
    # 目標タスクレベル ＝ 係数(coefficient) × 評価倍率(eval_mul) × 気分点(mood_point)
    raw = round(float(coefficient) * float(eval_mul) * float(mood_point))
    # rawを整数(int)に変換して関数clamp_intで1~6の範囲に収めて返す
    return clamp_int(int(raw), 1, 6) # 最低値1 最大値6にすることで提案できなくなる&提案が莫大な量になる事を防ぐ
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 期限までの残り日数(days_left)から締め切り補正倍率を返す関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def calc_deadline_multiplier(days_left: int | None) -> float: #【定義】： 戻り値 float 
    if days_left is None:    # days_leftが無い場合：
        return 1.0 # 期限補正無し
    if days_left < 0:        # days_leftが0未満(期限切れ)の場合：
        return 1.5  # 期限補正 1.5 - かなり強く優先する
    if days_left == 0:       # days_leftが0(期限-今日)の場合：
        return 1.4  # 期限補正 1.4 - 強く優先する
    if 1 <= days_left <= 2:  # days_leftが0(期限まで1~2日)の場合：
        return 1.3  # 期限補正 1.3 - やや強く優先する
    if 3 <= days_left <= 7:  # days_leftが0(期限まで3~7日)の場合：
        return 1.2  # 期限補正 1.2 - やや優先する
    if 8 <= days_left <= 14: # days_leftが0(期限まで8~14日)の場合：
        return 1.1  # 期限補正 1.1 - 少し優先する
    return 1.0      # それ以外(15日以上)は期限補正無し
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 実施タスクレベル＝タスクレベル × (やる分数 ÷ 所要時間)を返す関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def calc_exec_task_level(task_level: int, plan_min: int, required_min: int) -> float: #【定義】： 戻り値 float 
    # 所要時間が0未満の場合
    if required_min <= 0:
        return 0.0 # 0.0を計算不能として返す
    # 実施割合 ＝ ｢今日提案した分数(plan_min) ÷ 所要時間(required_min)｣
    ratio = min(1.0, float(plan_min) / float(required_min)) # ※入力した分数が提案した分数を上回った場合には1.0を上限とする
    # 実施タスクレベル＝タスクレベル × (実施割合)
    return float(task_level) * ratio
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# タスク1件に対して｢今日はこのタスクを何分やるか？｣の提案を行う分数を返す関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def pick_plan_minutes(task_level: int, mood_point: int, remaining_min: int, minutes_left: int) -> int: #【定義】： 戻り値 int
    # task_level（1〜3）から「基本の提案分数」を決める
    if task_level == 1:   # task_levelが1の場合：
        base_minutes = 20 # 基本提案分数 20分
    elif task_level == 2: # task_levelが2の場合：
        base_minutes = 30 # 基本提案分数 30分
    elif task_level == 3: # task_levelが3の場合：
        base_minutes = 60 # 基本提案分数 60分
    else:                 # 想定外の値の場合：
        base_minutes = 30 # 基本提案分数 30分

    # mood_point（1〜3）から「気分による倍率」を決める
    if mood_point == 1:     # 気分点が1の場合
        mood_factor = 0.9   # 倍率0.9
    elif mood_point == 2:   # 気分点が1の場合
        mood_factor = 1.0   # 倍率1.0
    elif mood_point == 3:   # 気分点が1の場合
        mood_factor = 1.15  # 倍率1.15
    else:                   # 想定外の値の場合：
        mood_factor = 1.0   # 倍率1.0

    # 提案分数＝基本提案分数 × 気分倍率
    raw_minutes = base_minutes * mood_factor

    # 提案分数を「5分単位」に丸める（例：33分→35分）
    chunk = int(round(raw_minutes / 5) * 5)

    # ただし最低でも10分は提案する（短すぎる提案を防ぐ）
    chunk = max(10, chunk)

    # 提案分数が「タスク残り時間 remaining_min」「今日の残り作業予算 minutes_left」を超えないように制限し、
    # さらに0未満にならないようにして返す
    return max(0, min(chunk, remaining_min, minutes_left))
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 今日の提案に対して｢どのタスクを何分やるか｣の詳細を作成してDBに保存する関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def build_and_insert_suggestion_details(
    db: DatabaseManager,
    suggestion_id: int,
    user_id: int,
    mood_point: int,
    target_level: int,
    avoid_task_ids: set[int] | None = None,
    diversity_penalty: float = 0.0,
) -> list[int]:
    today = date.today() # 今日の日付(例：2026-02-07)を作成
    free_minutes = calc_available_minutes(db, user_id) # 今日使える作業分数(関数calc_available_minutesを利用)
    minutes_left = int(free_minutes) # 今日残り作業予算

    # 追加：前案で使ったタスクを「避けやすく」するための設定
    avoid_task_ids = set(avoid_task_ids or [])
    diversity_penalty = max(0.0, min(0.95, float(diversity_penalty or 0.0)))

    # ------------------------------------------------------------------------------------------------------------
    # remaining_min > 0　(完了しているタスクを候補から外す)
    task_sql = """
        SELECT
            task_id,
            deadline,
            remaining_min,
            created_date,
            motivation_id AS task_level
        FROM t_tasks
        WHERE user_id = %s AND remaining_min > 0
        ORDER BY created_date ASC;
    """
    # -------------------------------------------------------------------------------------------------------------
    # 候補タスク一覧(無ければ空リストが返る)
    task_rows = db.fetch_all(task_sql, (user_id,)) or []

    candidates = [] # タスク候補を格納するリストを初期化
    for task in task_rows: # タスク1件ずつループ
        deadline = task["deadline"] # 期限
        if deadline is None: # 期限が未設定(None)の場合：
            days_left = None # 残り日数は None
        else:                # 期限が存在する場合：
            days_left = (deadline - today).days # 期限 - 今日　で残り日数を .days で整数にする
        deadline_mul = calc_deadline_multiplier(days_left) # 締め切り補正倍率(関数calc_deadline_multiplierを利用)

        task_id = int(task["task_id"])                   # ★追加（task_idを先に取り出す）
        task_level = int(task["task_level"])             # motivation_idが入る
        base_priority = float(task_level) * float(deadline_mul) # タスクレベル × 締め切り補正倍率

        # ★追加：前案で使ったタスクは優先点を下げて「別案」を出しやすくする
        if diversity_penalty > 0.0 and task_id in avoid_task_ids:
            base_priority *= (1.0 - diversity_penalty)

        # タスク提案候補をまとめて保存
        candidates.append(
            {
                "task_id": task_id,                           # タスクID
                "task_level": task_level,                     # タスクレベル
                "remaining_min": int(task["remaining_min"]),  # 今の残り分数
                "days_left": days_left,                       # 期限までの残り日数
                "deadline_mul": float(deadline_mul),          # 締め切り補正倍率
                "base_priority": float(base_priority),        # 暫定の提案での優先点
            }
        )

    # 暫定の提案での優先点が高い順に並び替え
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            if candidates[i]["base_priority"] < candidates[j]["base_priority"]:
                # iの方が低いなら入れ替え
                candidates[i], candidates[j] = candidates[j], candidates[i]

    picked = []             # 提案詳細を格納するリストを初期化
    sum_exec_level = 0.0    # 実施タスクレベル合計を格納する変数を初期化

    for item in candidates:     # 優先度順にループ
        if minutes_left <= 0:   # 今日の残り予算が無い場合：
            break               # break = 提案しない
        if sum_exec_level >= float(target_level) and len(picked) >= 1: # 提案した実施タスクレベルの合計(sum_exec_level)がtarget_levelに達した場合 ※最低1件は出す
            break               # break = 提案を打ち切り

        plan_min = pick_plan_minutes(
            item["task_level"],     # タスクレベル
            mood_point,             # 気分点
            item["remaining_min"],  # タスク残り分数
            minutes_left,           # 今日残り作業予算
        )

        # 0分になったらスキップ
        if int(plan_min) <= 0:
            continue

        required_min = int(item["remaining_min"])   # 提案時点の残り分数
        exec_level = calc_exec_task_level(item["task_level"], plan_min, required_min) # 実施タスクレベル
        priority_score = float(exec_level) * float(item["deadline_mul"])              # 優先点

        picked.append( # 採用したタスク詳細を追加
            {
                "task_id": item["task_id"],
                "plan_min": int(plan_min),
                "remaining_min_at_suggest": int(item["remaining_min"]),
                "days_left": item["days_left"],
                "deadline_multiplier": float(item["deadline_mul"]),
                "exec_task_level": float(exec_level),
                "priority_score": float(priority_score),
            }
        )

        minutes_left -= int(plan_min)       # 今日の残り予算を減算
        sum_exec_level += float(exec_level) # 目標達成までの合計を加算

    # 1件もタスクを採用できない場合
    if not picked:
        return []  # ★変更：空リストで返す

    # 暫定の提案での優先点が高い順に並び替え（※元コード通り残す）
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            if candidates[i]["base_priority"] < candidates[j]["base_priority"]:
                # iの方が低いなら入れ替え
                candidates[i], candidates[j] = candidates[j], candidates[i]

    # ---------------------------------------------------------------------------------------------------------------------------------------------------
    # insert_sqlに格納
    insert_sql = """
        INSERT INTO t_task_suggestion_detail
        (task_suggestion_id, task_id, plan_min,
         remaining_min_at_suggest, days_left,
         deadline_multiplier, exec_task_level, priority_score)
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    for row in picked:          # 採用したタスク提案詳細をタスク1件ずつ
        db.cursor.execute(      # タスク提案詳細テーブルに保存
            insert_sql,
            (
                suggestion_id,
                row["task_id"],
                row["plan_min"],
                row["remaining_min_at_suggest"],
                row["days_left"],
                row["deadline_multiplier"],
                row["exec_task_level"],
                row["priority_score"],
            ),
        )

    # ★追加：この案で採用した task_id を返す（次の案で“避ける”ため）
    return [row["task_id"] for row in picked]
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 〇分 → 〇時間〇分 に変換
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def minutes_to_hm(minutes: int) -> str:
    # None や空を安全に 0 として扱う
    minutes = int(minutes or 0)

    h = minutes // 60
    m = minutes % 60

    # 表示ルールは好みで調整OK
    if h == 0:
        return f"{m}分"
    return f"{h}時間{m}分"          # 例: 125 → "2時間5分"
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 期限タグ判定関数
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# deadline:DBからくる｢期限｣ 
# today: date 今日の日付(date型)
# -> str | None: 戻り値は "期限切れ"/"今日中"(文字列) もしくは None
def get_deadline_tag(deadline, today: date) -> str | None:
    # 万が一 期限が設定されていない場合:
    if deadline is None:
        # 弾く
        return None

    # deadline の型が date/datetime/str のどれで来ても date に揃える ※取得方法によって型が変わる可能性があるため
    if isinstance(deadline, datetime):  # deadline が datetime の場合:
        deadline_date = deadline.date() # datetime から 日付部分だけを取り出して date にする
    elif isinstance(deadline, date):    # deadline が date の場合:
        deadline_date = deadline        # date ならそのまま使うので代入のみ
    elif isinstance(deadline, str):     # dealine が str の場合: 
        # "YYYY-MM-DD" / "YYYY-MM-DD HH:MM:SS" どっちも対応
        try: # 安全にtryで囲む
             # ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
             # deadline[:10] 先頭10文字(YYYY-MM-DD)だけ切り出す
             # datetime.strptime(    ,"%Y-%m-%d") 文字列 → datetimeに変換
             # .date() datetime → dateに変換(時刻部分は不要)
            deadline_date = datetime.strptime(deadline[:10], "%Y-%m-%d").date()
        # 変換失敗(空文字/違う形式)の場合:
        except Exception:
            # 弾く
            return None
    # 想定外の型の場合:
    else:
        # 弾く
        return None
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # ＜日数差の計算＞
    # deadline_date - today は timedelta（期間）になるので .days で日数だけ取り出し
    # 期限が昨日 ＝ -1  /  期限が今日 ＝ 0  /  期限が明日 ＝1
    days_left = (deadline_date - today).days
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # ＜期限判定＞
    if days_left < 0:     # 期限切れ
        return "期限切れ"
    if days_left == 0:    # 今日中
        return "今日中"
    return None           # それ以外
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# *****************************************************************************************************************************************************************************************************
@task_bp.route("/task_suggestion", methods=["GET", "POST"])
def task_suggestion():  # 「今日のタスク提案」を表示 / 3案作成 / 選択 / 評価更新 する処理（3案提案版）
    user_id = get_current_user_id()  # ログイン中ユーザーID
    today = date.today()             # 今日の日付

    db = DatabaseManager()           # DB操作クラス
    db.connect()                     # DB接続

    # 例外処理 ----------------------------------------------------------------------------------------------------------------------------
    try:
        # --------------------------------------------------------------------------------------------------------------------------------
        # 今日の提案（ヘッダ）を全部取得する（3案を出すため）
        # --------------------------------------------------------------------------------------------------------------------------------
        def fetch_today_suggestions_all() -> list[dict]: #【定義】戻り値：辞書型(dict)のリスト(list)
            # ----------------------------------------------------------------------------------------------------------------------------
            # SQL実行
            # ＜取得する列＞
            # task_suggestion_id (タスク提案ID),
            # user_id (そのタスク提案がどのユーザーのものか),
            # suggestion_date (提案の日付),
            # mood(その日の気分),
            # mood_point(気分点1~3)
            # evaluation(評価1~3)
            # evaluation_multiplier(評価倍率 0.8/1.0/1.2)
            # target_task_level(目標タスクレベル)
            db.cursor.execute(
                """
                SELECT
                    task_suggestion_id,
                    user_id,
                    suggestion_date,
                    mood,
                    mood_point,
                    coef_value,
                    evaluation,
                    evaluation_multiplier,
                    target_task_level
                FROM t_task_suggestions
                WHERE user_id=%s AND suggestion_date=%s
                ORDER BY task_suggestion_id ASC;
                """,
                (user_id, today),
            )
            # -----------------------------------------------------------------------------------------------------------------------------
            # 結果を全件取得
            rows = db.cursor.fetchall()
            # 返す(0件なら空リストが返る)
            return rows or []

        # --------------------------------------------------------------------------------------------------------------------------------
        # 指定IDの提案（ヘッダ）を1件取得する（評価更新などで使う）
        # --------------------------------------------------------------------------------------------------------------------------------
        def fetch_suggestion_by_id(task_suggestion_id: int) -> dict | None: #【定義】戻り値：1件見つかれば辞書型(dict) / 見つからなければNone
            # ----------------------------------------------------------------------------------------------------------------------------
            # SQL実行
            # ＜取得する列＞
            # task_suggestion_id (タスク提案ID),
            # user_id (そのタスク提案がどのユーザーのものか),
            # suggestion_date (提案の日付),
            # mood(その日の気分),
            # mood_point(気分点1~3)
            # evaluation(評価1~3)
            # evaluation_multiplier(評価倍率 0.8/1.0/1.2)
            # target_task_level(目標タスクレベル)
            db.cursor.execute(
                """
                SELECT
                    task_suggestion_id,
                    user_id,
                    suggestion_date,
                    mood,
                    mood_point,
                    coef_value,
                    evaluation,
                    evaluation_multiplier,
                    target_task_level
                FROM t_task_suggestions
                WHERE task_suggestion_id=%s AND user_id=%s;
                """,
                (task_suggestion_id, user_id),
            )
            # ----------------------------------------------------------------------------------------------------------------------------
            # 1件だけ取得して返す
            return db.cursor.fetchone()
        # --------------------------------------------------------------------------------------------------------------------------------
        # 指定IDの提案（詳細 + ヘッダ）を削除する（ユーザーに選ばれなかった2案を消す用）
        # --------------------------------------------------------------------------------------------------------------------------------
        # 指定 task_suggestion_id(タスク提案ID) の ｢提案データ一式｣ を削除する
        def delete_suggestion(task_suggestion_id: int) -> None: #【定義】戻り値：無し
            # 「タスク提案詳細テーブル」から削除SQL実行
            db.cursor.execute(
                "DELETE FROM t_task_suggestion_detail WHERE task_suggestion_id=%s;",
                (task_suggestion_id,),
            )
            # ｢タスク提案(ヘッダ)テーブル｣から削除SQL実行
            db.cursor.execute(
                "DELETE FROM t_task_suggestions WHERE task_suggestion_id=%s;",
                (task_suggestion_id,),
            )
        # --------------------------------------------------------------------------------------------------------------------------------
        # 目標タスクレベル(base)から「3案ぶんのレベル」を作る（重複しないように調整）
        # --------------------------------------------------------------------------------------------------------------------------------
        # base_level(基準となる目標タスクレベル)から3つのレベルのタスク案を作成する
        def make_three_levels(base_level: int) -> list[int]: #【関数】int型のみのlist
            # まずは最初の候補を 「baseの前後 ±1 と base自身」の3つにする
            candidates = [base_level - 1, base_level, base_level + 1]

            # 最終的に返す "重複なしのレベル" を入れるリストを用意 
            levels: list[int] = []
            # candidates の中身(3個) を1個ずつループ
            for lv in candidates:
                lv = max(1, min(6, int(lv))) # lv を必ず 1~6 の範囲に収める(int:整数型)
                if lv not in levels:  # 重複チェック
                    levels.append(lv) # levelsに追加

            # base±1 だけで3つ揃わないケースに備え、次は base±2 から外側を探すための距離(step) を2でスタート
            step = 2
            # levels が 3つ未満の間 & step<=6 まで　※step<=6 は探し続けて無限ループにならないように設定
            while len(levels) < 3 and step <= 6:
                # baseから step文 離れた ""左右2つ(マイナス側→プラス側)""を順に試す
                for lv in (base_level - step, base_level + step):
                    lv = max(1, min(6, int(lv))) # lv を必ず 1~6 の範囲に収める(int:整数型)
                    if lv not in levels:    # 重複チェック
                        levels.append(lv)   # levelsに追加
                    if len(levels) >= 3:    # 3つ揃った場合：
                        break               # ループを抜ける
                # 次の探索距離にいくために1加算
                step += 1

            # 最後に「必ず3つ」にする　※保険
            while len(levels) < 3:
                # lv を必ず 1~6 の範囲に収める(int:整数型)
                lv = max(1, min(6, len(levels) + 1))
                if lv not in levels:  # 重複チェック
                    levels.append(lv) # levelsに追加

            return levels[:3] # 最終的に先頭3つだけ返して list[int]の3タスクにする

        # --------------------------------------------------------------------------------------------------------------------------------
        # 提案詳細の合計分数（plan_min）を計算して「◯時間◯分」文字列にする
        # --------------------------------------------------------------------------------------------------------------------------------
        # details は「提案詳細の行（dict）のリスト」想定　戻り値： str（例："2時間10分"）
        def calc_total_plan_text(details: list[dict]) -> str:
            # 合計分数を格納する変数を0で初期化
            total_plan_min = 0
            # 各タスク詳細を1つずつ取り出してループ
            for row in details:
                # row（辞書）から "plan_min" を取り出す　"plan_min" が無ければ 0
                plan_min = row.get("plan_min", 0)
                
                if plan_min is None: # Noneの場合：
                    # 0とする
                    plan_min = 0 
                # plan_min をintに変換してから加算
                total_plan_min += int(plan_min)
            # 〇分 → 〇時間〇分 に変換(関数minutes_to_hmを使用)
            return minutes_to_hm(total_plan_min)
        # --------------------------------------------------------------------------------------------------------------------------------
        # 詳細に deadline_tag を付ける（期限切れ / 今日中）
        # --------------------------------------------------------------------------------------------------------------------------------
        def attach_deadline_tags(details: list[dict]) -> None: #【定義】戻り値：None
            # タスク提案詳細の各タスクを1つずつループ
            for row in details:
                # row.get("deadline")で期限日を取り出して各タグを付与(関数get_deadline_tagを使用)
                row["deadline_tag"] = get_deadline_tag(row.get("deadline"), today)

        # --------------------------------------------------------------------------------------------------------------------------------
        # 今日のタスク提案が「0件」の場合、タスク提案 3案をDBに作る
        # --------------------------------------------------------------------------------------------------------------------------------
        # 今日の日付の タスク提案(ヘッダ)を全て取得して 変数suggestions_today に代入
        suggestions_today = fetch_today_suggestions_all()

        # 取得した｢今日のタスク提案｣が0件(まだ提案が未作成)の場合: 
        if len(suggestions_today) == 0:
            # 今日の気分（文字列, 気分点）を取得（例: "ふつう", 2）
            mood_text, mood_point = fetch_today_mood(db, user_id)

            # 係数を計算
            coefficient = calc_coefficient(db, user_id, today)

            # 初回は評価なしなので評価倍率は 1.0
            eval_mul = 1.0

            # 基準の目標タスクレベル
            base_target_level = calc_target_task_level(mood_point, eval_mul, coefficient)

            # 3案分の目標タスクレベル（重複しないように作成）
            levels = make_three_levels(base_target_level)

            # 表示ラベル（レベルが小さい順＝ 軽め → ふつう → 多め）
            levels_sorted = sorted(levels)
            label_by_level = {
                levels_sorted[0]: "軽め案",
                levels_sorted[1]: "ふつう案",
                levels_sorted[2]: "多め案",
            }

            used_task_ids: set[int] = set()

            # 3案をDBにINSERTして、詳細も作る
            for i, target_level in enumerate(levels_sorted):
                # 2案目以降は、直前案と同じタスクに寄りすぎないよう優先点を下げる
                diversity_penalty = 0.0 if i == 0 else (0.35 if i == 1 else 0.55)

                db.cursor.execute(
                    """
                    INSERT INTO t_task_suggestions
                    (user_id, suggestion_date, mood, mood_point, coef_value, evaluation, evaluation_multiplier, target_task_level)
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (user_id, today, mood_text, mood_point, coefficient, None, eval_mul, target_level),
                )
                new_suggestion_id = db.cursor.lastrowid  # 直前INSERTのID

                # 詳細（どのタスクを何分やるか）を作成して保存
                picked_ids = build_and_insert_suggestion_details(
                    db=db,
                    suggestion_id=new_suggestion_id,
                    user_id=user_id,
                    mood_point=mood_point,
                    target_level=target_level,
                    avoid_task_ids=used_task_ids,
                    diversity_penalty=diversity_penalty,
                )
                used_task_ids.update(picked_ids)

            # 3案作成をDBに確定
            db.connection.commit()

            # 作り直したので、改めて今日の提案一覧を取得
            suggestions_today = fetch_today_suggestions_all()

        # --------------------------------------------------------------------------------------------------------------------------------
        # POST：3案の「選択」 or 「評価更新」 or 「開始」
        # --------------------------------------------------------------------------------------------------------------------------------
        if request.method == "POST":
            # -- 今日の提案ID一覧（検証に使用）
            today_ids = [row["task_suggestion_id"] for row in suggestions_today]

            # タスク提案 3案のうち「どれを採用するか」選択
            # formから｢ユーザーが選択した提案ID｣をintで受け取る(無ければNone)
            picked_id = (request.form.get("selected_suggestion_id", type=int)
                         or request.form.get("task_suggestion_id",type=int))
            # 値があり、｢今日のタスク提案IDのどれか｣に含まれている場合:
            if picked_id is not None and picked_id in today_ids: 
                # 選ばれたIDをセッションに保存
                session["selected_task_suggestion_id"] = picked_id

                # 選ばれなかった2案を削除
                for sid in today_ids:           # 今日のタスク提案IDを1つずつループ
                    if sid != picked_id:        # 採用したタスク提案ID以外の場合
                        delete_suggestion(sid)  # 不採用のタスク提案をDBから削除

                # 削除を確定
                db.connection.commit()

                # ★追加：開始中IDが残っているとそっちが優先されるのでクリア
                session.pop("current_task_suggestion_id", None)
                # 選んだ1案だけ表示する画面へ戻す
                return redirect(url_for("task.task_form"))

            # -- 評価更新
            # form から評価値(1~3)をintで受け取る(無ければNone)
            evaluation = request.form.get("evaluation", type=int)

            # 評価対象ID（HTML側で hidden など：name="task_suggestion_id" を付ける想定）
            eval_target_id = request.form.get("task_suggestion_id", type=int)

            # 既に採用されたタスク提案ID(ユーザーが選択済み)があればセッションから取得(無ければNone)
            selected_id = session.get("selected_task_suggestion_id")
            # 評価対象IDがNoneの場合
            if eval_target_id is None:
                # セッションの選択済みタスク提案IDが｢今日のタスク提案ID一覧｣に含まれている場合:
                if selected_id in today_ids:
                    # 選択済みタスク提案IDを評価対象とする
                    eval_target_id = selected_id
                # 今日のタスク提案が既に1件(ユーザーによって選択済み)の場合:
                elif len(today_ids) == 1:
                    # その1件を評価対象とする
                    eval_target_id = today_ids[0]
                    # 1件しかないので「選択済み」としてセッションも揃える
                    session["selected_task_suggestion_id"] = eval_target_id
                # 未選択で複数案が残っているなど、評価対象が決め打てないケースの場合:
                else:
                    # 未選択で複数案があるなら、一旦「先頭案」を評価対象とする ※保険
                    eval_target_id = today_ids[0]

            # 評価(evaluation)が来ている時だけ「評価更新」実行
            if evaluation is not None:
                # 評価対象のタスク提案(ヘッダ)をDBから1件取得
                target_suggestion = fetch_suggestion_by_id(int(eval_target_id))
                # 対象がNone(見つからない)場合:
                if target_suggestion is None:
                    # 画面に戻す
                    return redirect(url_for("task.task_suggestion"))

                # DBの気分点があれば使い、無ければ2(ふつう想定)にする
                mood_point = int(target_suggestion.get("mood_point", 2))
                # DBの係数があれば使い、無ければ1.0にする
                coefficient = float(target_suggestion.get("coef_value", 1.0))

                # 評価(1〜3) → 評価倍率に変換
                eval_mul = evaluation_to_multiplier(evaluation)

                # 目標タスクレベル＝ 気分点 × 評価倍率 × 係数
                target_level = calc_target_task_level(mood_point, eval_mul, coefficient)

                # ヘッダを更新（評価・倍率・目標レベル）
                db.cursor.execute(
                    """
                    UPDATE t_task_suggestions
                    SET evaluation=%s,
                        evaluation_multiplier=%s,
                        target_task_level=%s
                    WHERE task_suggestion_id=%s;
                    """,
                    (evaluation, eval_mul, target_level, int(eval_target_id)),
                )

                # 既存の詳細を全削除（作り直すため）
                db.cursor.execute(
                    "DELETE FROM t_task_suggestion_detail WHERE task_suggestion_id=%s;",
                    (int(eval_target_id),),
                )

                # 新しい目標レベルで詳細を再作成
                build_and_insert_suggestion_details(
                    db=db,
                    suggestion_id=int(eval_target_id),
                    user_id=user_id,
                    mood_point=mood_point,
                    target_level=target_level,
                )

                # DB確定
                db.connection.commit()

                # 再表示
                return redirect(url_for("task.task_suggestion"))

            # 「開始したいタスク提案ID」をintで受け取る（無ければNone）
            start_target_id = request.form.get("start_suggestion_id", type=int)

             # 開始対象のタスク提案IDがformから渡ってこなかった場合:
            if start_target_id is None:
                # start_target_id が無い場合は選択済み → なければ先頭
                selected_id = session.get("selected_task_suggestion_id")  # セッションの「選択済みタスク提案ID」を取る
                # 選択済みタスク提案IDが今日の提案に含まれているなら
                if selected_id in today_ids:
                    start_target_id = selected_id  # その選択済みIDを開始対象にする
                # 選択済みが無い/不正などの場合
                else:
                    start_target_id = today_ids[0] # 先頭の提案を開始対象にする ※保険

            # セッションに「今開始したタスク提案ID」を記録
            session["current_task_suggestion_id"] = int(start_target_id) # 「今このタスク提案を実行中」という状態をセッションに保存

            # 画面再表示
            return redirect(url_for("task.task_suggestion"))

        # --------------------------------------------------------------------------------------------------------------------------------
        # GET：表示（未選択なら3案まとめて、選択済みなら1案だけ）
        # --------------------------------------------------------------------------------------------------------------------------------
        # 今日の提案を「目標タスクレベル順」に並べる（ライト→ふつう→がっつり の順に表示する）
        suggestions_sorted = sorted(  # suggestions_today を「表示したい順」に並べ替えた新しいリストを作る
            suggestions_today,        # 並べ替え対象：今日のタスク提案（ヘッダ）一覧
            # 並べ替えキー：目標タスクレベル ※タスク提案ID（同点のときの安定順）
            key=lambda r: (int(r.get("target_task_level", 0)), int(r.get("task_suggestion_id", 0))),
        )

        # 3案ラベルを作成
        labels = ["軽め案", "ふつう案", "多め案"]
        # 「提案ID → ラベル文字列」を入れる辞書を用意
        label_by_id: dict[int, str] = {}
        # 並べ替え済みの提案を、番号(i)付きで順に取り出す
        for i, s in enumerate(suggestions_sorted):
             # 0〜2なら labels ※3件以上なら「案4」などにする
            label_by_id[int(s["task_suggestion_id"])] = labels[i] if i < len(labels) else f"案{i+1}"

        # 選択済みタスク提案ID（未選択なら None）
        # セッションから「選択済みの提案ID」を取得（無ければ None）
        selected_id = session.get("selected_task_suggestion_id")

        # 選択済みIDが今日の一覧に無いなら無効化（削除済み等の対策）
        today_ids = [row["task_suggestion_id"] for row in suggestions_today]
        if selected_id not in today_ids: # selected_id が今日の提案ID一覧に無い（削除済み/不正/古い）場合:
            selected_id = None # 選択状態を「未選択」に戻す
        # ★追加：今日の提案が複数残っているなら「未選択」扱いに戻す（= 3案表示する）
        if len(today_ids) >= 2:
            session.pop("selected_task_suggestion_id", None)
            selected_id = None 

        # 表示用：各案の「ヘッダ + 詳細 + 合計時間」をまとめる
        # テンプレに渡す「表示用まとまり（案ごと）」を入れるリスト
        suggestion_bundles: list[dict] = [] 
         # 並べ替え済みの提案を順に処理する
        for s in suggestions_sorted:
            sid = int(s["task_suggestion_id"]) # タスク提案IDを int にして扱う（型を揃える）

            # 選択済みなら「その1案だけ」表示（未選択なら全部表示）
            # 選択済みで、かつ「今見ている案」が選択案ではない場合:
            if selected_id is not None and sid != int(selected_id):
                continue # この案は表示しない（次の案へ）

            # このタスク提案IDの「詳細（タスク一覧）」をDBから取得
            details = fetch_suggestion_details(db, sid)
            if not details:
                continue
            attach_deadline_tags(details)                # deadline_tag を付与
            # details の plan_min 合計から「◯時間◯分」文字列を作る
            total_plan_text = calc_total_plan_text(details)

            # テンプレ表示に必要な情報を「タスク提案1案分」をまとめて追加
            suggestion_bundles.append(
                {
                    "label": label_by_id.get(sid, "案"), # その案に付けるラベル（無ければ "案"）
                    "suggestion": s,                     # ヘッダ
                    "suggestion_list": details,          # 詳細一覧
                    "total_plan_text": total_plan_text,  # 合計時間の表示用文字列
                }
            )

        # 後方互換：テンプレが「1案前提」でも動くように、先頭案を単体変数でも渡す
        # 先頭案のヘッダ（無ければ None）
        single_suggestion = suggestion_bundles[0]["suggestion"] if suggestion_bundles else None
        # 先頭案の詳細一覧（無ければ空）
        single_list = suggestion_bundles[0]["suggestion_list"] if suggestion_bundles else []
        # 先頭案の合計時間（無ければ 0分表記）
        single_total = suggestion_bundles[0]["total_plan_text"] if suggestion_bundles else minutes_to_hm(0)

        return render_template(
            "task/task_suggestion.html",
            # 3案提案用（テンプレ側でループ表示）
            suggestion_bundles=suggestion_bundles, # 3案（または1案）の表示用リスト
            selected_suggestion_id=selected_id,    # 現在選択済みのタスク提案ID（未選択なら None
            # 1案前提テンプレでも動くように（既存キー）
            suggestion=single_suggestion,   # 後方互換：1案表示用のヘッダ
            suggestion_list=single_list,    # 後方互換：1案表示用の詳細
            total_plan_text=single_total,   # 後方互換：1案表示用の合計時間文字列
        )

    # エラー時：DBを安全に戻す -------------------------------------------------------------------------------------------------------------
    except Exception as e:
        if db.connection is not None: # DB接続が存在する（途中までDB操作している)場合:
            db.connection.rollback()  # 途中までの変更を取り消す

        traceback.print_exc()           # どの行で落ちたかをコンソールに詳しく出力（デバッグ用）
        return f"タスク提案エラー: {e}"  # ブラウザにエラーメッセージを返す

    # 最後に必ず実行 ----------------------------------------------------------------------------------------------------------------------
    finally: # 成功しても失敗しても、最後に必ず通る
        db.disconnect()  # DB切断