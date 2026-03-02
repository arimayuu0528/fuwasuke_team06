from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
from app.db import DatabaseManager

# Blueprint
mood_bp = Blueprint('mood', __name__, url_prefix='/mood')

# --------------------------------------------------------------------------
# DBに｢保存できる気分｣を固定
# --------------------------------------------------------------------------
# フォームで受け付ける気分の値を固定(バリデーション用)
ALLOWED_MOODS = ("元気", "普通", "悪い")

# --------------------------------------------------------------------------
# 想定の点数に固定（※画面には基本出さない。内部判定だけに使う）
# --------------------------------------------------------------------------
# 気分の文字列→内部点数(3/2/1)への対応表を定義
MOOD_POINT_MAP = {
    "元気": 3,  # 元気＝3
    "普通": 2,  # 普通＝2
    "悪い": 1,  # 悪い＝1
}

# --------------------------------------------------------------------------
# 週次の振り返り文を作る（文章/判定/キャラ画像）をまとめたdictを作る関数
# --------------------------------------------------------------------------
# - 点数は内部判定だけに使う（画面には点数を出さない）
# - 平均点を3等分した範囲で「絶好調/好調/しんどかった」を判定
# - 判定範囲に応じてキャラクター画像も切り替える
# - 今週(week=0)は、日曜日(end_date)になるまで「未確定」表示にする
# --------------------------------------------------------------------------
def _build_week_review(week: int, today, end_date, mood_points: list[int]) -> dict:
    # 「その週ごとのタイトル」作成
    heading = "今週の振り返り" if week == 0 else "前の週の振り返り"

    # 画像（static/image/〜 の想定。グラフで使用している画像を流用）
    IMG_GENKI = "image/gennki.png"
    IMG_FUTU  = "image/futu.png"
    IMG_WARUI = "image/warui.png"

    # ------------------------------------------------------------------------------------------------------------------
    # 今週は日曜まで振り返りを出さない
    # ------------------------------------------------------------------------------------------------------------------
    # week == 0 は 今週。
    # today < end_date（日曜より前）なら 週の集計が揃っていないので ready=False を返して、テンプレート側は「未確定表示」
    if week == 0 and today < end_date:
        return {
            "heading": heading, # 週ごとのタイトル
            "ready": False,     # まだ確定した週次レポートを表示しない
            "status": None,     # 判定結果無し状態：(絶好調/好調/不調：無し)
            "message": "今週の振り返りは日曜日表示予定。", # ユーザーに説明するための文章
            "reasons": ["週の集計が揃うと確定表示します。"], # ユーザーに説明するための文章
            "character_img": IMG_FUTU, # 集計中 :「普通」キャラ画像
            "character_alt": "集計中", # キャラ画像の代替テキスト(alt)
        }

    # ------------------------------------------------------------------------------------------------------------------
    # DBから取れた点数リスト mood_points が空なら、週次判定はせず「記録なし」扱い
    # ------------------------------------------------------------------------------------------------------------------
    if not mood_points:
        return {
            "heading": heading,         # 週ごとのタイトル
            "ready": True,              # 週次レポートを表示
            "status": "記録なし",        # 気分記録なし
            "message": "この週は気分の記録がありませんでした。", # ユーザーに説明するための文章
            "reasons": ["1日だけでも記録できると、週の傾向として振り返りが作れます。"], # ユーザーに説明するための文章
            "character_img": IMG_FUTU,  # 記録なし：「普通」キャラ画像
            "character_alt": "記録なし", # キャラ画像の代替テキスト(alt)
        }

    # -------------------------------------------------------------------------------------------------------------
    # 理由（点数は出さず、言葉で）
    # -------------------------------------------------------------------------------------------------------------
    total = len(mood_points) # ｢この週に、何日分の記録があったか｣
    # 
    good = 0    # 「元気(3点)」の日数カウンタ変数を0で初期化
    normal = 0  # 「普通(2点)」の日数カウンタ変数を0で初期化
    bad = 0     # 「悪い(1点)」の日数カウンタ変数を0で初期化

    for p in mood_points:  # mood_points（点数のリスト）を先頭から1つずつ取り出して p に入れる
        if p == 3:         # p が 3(元気)の場合:
            good += 1      # good を 1 加算 
        elif p == 2:       # p が 2(普通)の場合:
            normal += 1    # normal を 1 加算 
        elif p == 1:       # p が 1(悪い)の場合:
            bad += 1       # bad を 1 加算
        else:              # None や 0 の 想定外が入っていた場合
            pass           # 無視して次の要素へ進む
    
    # 画面に出す理由文のリスト
    reasons = [
        f"週に {total}日分の気分記録がありました。",
    ]
    # 「どれが多かったか」を文章にする
    if good >= normal and good >= bad:  # 気分＝元気 が 最多の場合:
        # 元気コメント
        reasons.append("気分が元気な日が一番多く、　　　　　　　　全体的に上向きな一週間でしたね！")
    elif bad >= good and bad >= normal: # 気分＝悪い が 最多の場合:
        # 悪いコメント
        reasons.append("気分が悪い日が目立っていて、　　　　　　　疲れが溜まりやすい一週間でした。")
    else:                               # 気分＝普通 が 最多の場合:
        # 普通コメント
        reasons.append("気分が普通の日が中心で、　　　　　　　　　安定して過ごせた週でした。")

    # -----------------------------------------------------------------------------------------------------------------------------
    # 判定ロジック：平均で3分割
    #   [1.00-1.66] 不調 / [1.67-2.33] 好調 / [2.34-3.00] 絶好調
    # -----------------------------------------------------------------------------------------------------------------------------
    # 平均 avg の 計算　
    avg = sum(mood_points) / total # 平均 = 週の点数の合計 / 記録日数

    if avg >= 2.34:
        status = "絶好調！な一週間" # 見出し用ラベル
        message = "週全体として気分が高めでした。　　　　良い流れを来週も続けられると最高！" # 説明文
        character_img = IMG_GENKI  # 絶好調：「元気」キャラ画像
        character_alt = "絶好調（元気）" # # キャラ画像の代替テキスト(alt)
    elif avg >= 1.67:
        status = "好調な一週間"     # 見出し用ラベル
        message = """大きく崩れずに過ごせた週でした。　　　　　調子が良い時、無理しすぎないのがコツ""" # 説明文
        character_img = IMG_FUTU   # 好調：「普通」キャラ画像
        character_alt = "好調（普通）"
    else:
        status = "不調な一週間でした..."  # 見出し用ラベル
        message = "特にしんどさが出やすい週でした。　　　　　回復を最優先にして、　　　　　　　　　　　来週は小さく整えていきましょう。" # 説明文
        character_img = IMG_WARUI  # 不調：「悪い」キャラ画像
        character_alt = "しんどい（悪い）"

    return {
        "heading": heading, # 週ごとのタイトル
        "ready": True,      # 週次レポートを表示
        "status": status,   # 見出し用ラベル
        "message": message, # ユーザーに説明するための文章
        "reasons": reasons, # 気分記録に基づく理由文
        # 画像切替用
        "character_img": character_img, # キャラ画像
        "character_alt": character_alt, # キャラ画像の代替テキスト(alt)
        # avgは必要なら保持（画面には出さない運用）
        "avg": round(avg, 2), # 平均値を小数第２位までに丸める
        "count": total,       # 記録日数
    }
# --------------------------------------------------------------------------
# sessionにuser_idが入っていなければログイン画面に飛ばす関数
# --------------------------------------------------------------------------
def _require_login_user_id() -> int:
    # sessionからuser_idを取得
    user_id = session.get("user_id")
    # user_idが無い場合:(セッション切れ/未ログイン)
    if user_id is None:
        # ログイン画面に飛ばす
        return redirect(url_for("auth.login"))
    # user_idをintにして返す
    return int(user_id)

# --------------------------------------------------------------------------
# 気分表示/登録
# --------------------------------------------------------------------------
@mood_bp.route("/", methods=["GET", "POST"])
def register():
    # sessionからuser_id取得(関数_require_login_user_idを利用)
    user_id = _require_login_user_id()
    db = DatabaseManager()  # DB操作クラスのインスタンスを作成
    db.connect()            # DBに接続

    # 今日既に気分が登録済みか確認
    check_sql = """
        SELECT today_moods_id
        FROM t_today_moods
        WHERE user_id = %s
        AND DATE(mood_date) = CURDATE()
        LIMIT 1
    """
    # SQL実行
    exists = db.fetch_one(check_sql, (session["user_id"],))

    # POSTの場合:(登録処理)
    if request.method == "POST":
        # フォーム値：元気/普通/悪いのどれかである前提
        mood = request.form.get("mood", "").strip()
        # バリデーション
        if mood not in ALLOWED_MOODS:  # 元気/普通/悪い でない場合:
            db.disconnect()  # DB接続を閉じる
            return render_template(
                "mood/register_mood.html",
                error="気分の値が不正です(正:元気/普通/悪い)"
            )

        # mood(元気/普通/悪い)から点数(3/2/1)を取得
        mood_point = MOOD_POINT_MAP[mood]
        now = datetime.now()

        # 既に今日の気分が登録されている場合:
        if exists:
            # 今日の分は上書き（UPDATE）
            update_sql = """
                UPDATE t_today_moods
                SET mood_date = %s,
                    mood = %s,
                    mood_point = %s
                WHERE today_moods_id = %s
                AND user_id = %s
            """
            db.execute_query(update_sql, (now, mood, mood_point, exists["today_moods_id"], user_id))
        else:
            # 初回登録(INSERT)
            insert_sql = """
                INSERT INTO t_today_moods (user_id, mood_date, mood, mood_point)
                VALUES (%s, %s, %s, %s)
            """
            db.execute_query(insert_sql, (user_id, now, mood, mood_point))

        # DB接続を閉じる
        db.disconnect()
        # ホーム画面へ遷移
        return redirect(url_for("main.home"))

    # DB接続を閉じる
    db.disconnect()
    # 気分入力画面へ遷移
    return render_template("mood/register_mood.html")

# -------------------------------------------------------------------------------
# 気分グラフの表示:週単位でページング
# -------------------------------------------------------------------------------
@mood_bp.route("/graph", methods=["GET"])
def graph(): # 週単位の気分グラフ画面を作成して返す関数
    # sessionからuser_id取得(関数_require_login_user_idを利用)
    user_id = _require_login_user_id()

    # 何週前を表示するか（0=今週）: URLクエリからweekを取得
    week = request.args.get("week", default=0, type=int) # ?week= の値をintで取得（無ければ0=今週）
    if week < 0: # もし負の値なら（例：-1）
        week = 0 # 0に丸める（今週扱いにする）

    # 「過去2週間だけ」（0〜1）の制限
    if week > 1: # もし 2以上が来たら（例：?week=10）
        week = 1 # 1に丸める（前週までに制限する）

    db = DatabaseManager() # DB操作用クラスのインスタンスを作る
    db.connect()           # DBに接続する

    # ------------------------------------------------------------
    # 週の範囲を作る
    # today.weekday(): 月0〜日6
    # monday: 今週の月曜日
    # week=0: 今週 / week=1: 前の週
    # ------------------------------------------------------------
    today = datetime.now().date() # 今日の日付（時刻は捨ててdateだけにする）
    monday = today - timedelta(days=today.weekday()) # 今日から「今週の月曜」まで戻した日付を作る
    start_date = monday - timedelta(days=7 * week)   # week=0なら今週月曜、week=1なら先週月曜…という開始日を作る
    end_date = start_date + timedelta(days=6)        # 開始日から6日進めて「日曜」を終端日として作る


    # 週の範囲内の気分データをDBから取るSQL
    sql = """
        SELECT DATE(mood_date) AS mood_day, mood_point
        FROM t_today_moods
        WHERE user_id = %s
        AND DATE(mood_date) BETWEEN %s AND %s
        ORDER BY mood_date;
    """
    # SQLを実行して結果（複数行）をリストで受け取る
    rows = db.fetch_all(sql, (user_id, start_date, end_date))

    # 日付 -> mood_point（同日複数なら最後が残る）
    mood_by_day = {} # 「日付」をキーにして点数を引ける辞書を用意する
    for r in rows:   # DB結果を1行ずつループで取り出す
        mood_by_day[r["mood_day"]] = r["mood_point"] # その日付の点数を辞書に入れる（同じ日が複数なら上書きされ最後が残る）

    # Chart.js用 7日分の配列（未入力日は None → JSでは null）
    dates = []  # グラフの横軸ラベル（日付文字列）を入れるリスト
    values = [] # グラフの値（点数 or None）を入れるリスト
    for i in range(7): # 月曜〜日曜の7日分を必ず作るために0〜6でループ
        d = start_date + timedelta(days=i)   # start_date（月曜）からi日進めた日付を作る
        dates.append(d.strftime("%Y-%m-%d")) # 日付を "YYYY-MM-DD" 形式の文字列にしてdatesへ追加
        values.append(mood_by_day.get(d, None)) # その日の点数が辞書にあれば点数、無ければNoneをvaluesへ追加する

    # None（未入力日）を除外して、記録がある点数だけのリストを作成
    week_points = [v for v in values if v is not None]
    # 点数リストから週の振り返り文・状態を作成(関数_build_week_reviewを利用)
    review = _build_week_review(week, today, end_date, week_points)

    db.disconnect() #  DB接続を閉じる

    return render_template(
        "mood/mood_graph.html",
        dates=dates,    # グラフ用：日付ラベル配列
        values=values,  # グラフ用：点数配列（未入力はNone→JS側でnull相当）
        week=week,      # どの週を表示しているか（ページングに利用）
        start_label=start_date.strftime("%m月%d日"), # 開始日
        end_label=end_date.strftime("%m月%d日"),     # 終了日
        can_prev=True,  # 「前へ（過去へ）」ボタンを出すか（ここでは常にTrue）
        can_next=(week > 0), # 「次へ（未来へ）」ボタン：今週(0)のときはFalse、前週(1)のときはTrue
        review=review,  # 週の振り返り（見出し・状態・理由文・キャラ画像等）
    )