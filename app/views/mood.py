from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
from app.db import DatabaseManager

# Blueprint
mood_bp = Blueprint('mood', __name__, url_prefix='/mood')

# DBに｢保存できる気分｣を固定
ALLOWED_MOODS = ("元気", "普通", "悪い")

# 想定の点数に固定（※画面には基本出さない。内部判定だけに使う）
MOOD_POINT_MAP = {
    "元気": 3,  # 元気＝3
    "普通": 2,  # 普通＝2
    "悪い": 1,  # 悪い＝1
}

# --------------------------------------------------------------------------
# 週次の振り返り文を作る（点数を見せず、理由を言葉で出す）
# --------------------------------------------------------------------------
def _build_week_review(week: int, today, end_date, mood_points: list[int]) -> dict:
    """
    週次の振り返り情報を作る

    - 点数は内部判定だけに使う（画面には点数を出さない）
    - 平均点を3等分した範囲で「絶好調/好調/しんどかった」を判定
    - 判定範囲に応じてキャラクター画像も切り替える
    - 今週(week=0)は、日曜日(end_date)になるまで「未確定」表示にする
    """

    heading = "今週の振り返り" if week == 0 else "前の週の振り返り"

    # 画像（static/image/〜 の想定。グラフで使ってる画像を流用）
    IMG_GENKI = "image/gennki.png"
    IMG_FUTU  = "image/futu.png"
    IMG_WARUI = "image/warui.png"

    # ----------------------------
    # 今週は日曜まで振り返りを出さない
    # ----------------------------
    if week == 0 and today < end_date:
        return {
            "heading": heading,
            "ready": False,
            "status": None,
            "message": "今週(7日分)の振り返りは日曜日表示予定。",
            "reasons": ["週の集計が揃うと確定表示します。"],
            # 集計中は「普通」のキャラにしておく（必要なら別画像に変更OK）
            "character_img": IMG_FUTU,
            "character_alt": "集計中",
        }

    # ----------------------------
    # 記録なし
    # ----------------------------
    if not mood_points:
        return {
            "heading": heading,
            "ready": True,
            "status": "記録なし",
            "message": "この週は気分の記録がありませんでした。",
            "reasons": ["1日だけでも記録できると、週の傾向として振り返りが作れます。"],
            "character_img": IMG_FUTU,
            "character_alt": "記録なし",
        }

    # ----------------------------
    # 理由（点数は出さず、言葉で）
    # ----------------------------
    total = len(mood_points)
    good = sum(1 for p in mood_points if p == 3)    # 元気
    normal = sum(1 for p in mood_points if p == 2)  # 普通
    bad = sum(1 for p in mood_points if p == 1)     # 悪い

    reasons = [
        f"この週は {total}日分の気分記録がありました。",
    ]
    # 「どれが多かったか」を文章にする（数字をもっと隠したければ、ここも文章だけにできます）
    if good >= normal and good >= bad:
        reasons.append("気分が元気な日が一番多く、　　　　　　　　全体的に上向きな一週間でしたね！")
    elif bad >= good and bad >= normal:
        reasons.append("気分が悪い日が目立っていて、　　　　　　　疲れが溜まりやすい一週間でした。")
    else:
        reasons.append("気分が普通の日が中心で、　　　　　　　　　安定して過ごせた週でした。")

    # ----------------------------
    # 判定ロジック（内部のみ）：平均で3分割
    #   [1.00-1.66] しんどい / [1.67-2.33] 好調 / [2.34-3.00] 絶好調
    # ----------------------------
    avg = sum(mood_points) / total

    if avg >= 2.34:
        status = "絶好調！な一週間"
        message = "週全体として気分が高めでした。良い流れを来週も少しだけ続けられると最高です。"
        character_img = IMG_GENKI
        character_alt = "絶好調（元気）"
    elif avg >= 1.67:
        status = "好調な一週間"
        message = """大きく崩れずに過ごせた週でした。　　　　　調子が良い日に無理しすぎないのがコツ。"""
        character_img = IMG_FUTU
        character_alt = "好調（普通）"
    else:
        status = "不調な一週間でした..."
        message = "特にしんどさが出やすい週でした。　　　　　回復を最優先にして、　　　　　　　　　　　来週は小さく整えていきましょう。"
        character_img = IMG_WARUI
        character_alt = "しんどい（悪い）"

    return {
        "heading": heading,
        "ready": True,
        "status": status,
        "message": message,
        "reasons": reasons,
        # 画像切替用
        "character_img": character_img,
        "character_alt": character_alt,
        # avgは必要なら保持（画面には出さない運用）
        "avg": round(avg, 2),
        "count": total,
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
                WHERE id = %s
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

        db.disconnect()
        return redirect(url_for("main.home"))

    db.disconnect()
    return render_template("mood/register_mood.html")

# -------------------------------------------------------------------------------
# 気分グラフの表示:週単位でページング
# -------------------------------------------------------------------------------
@mood_bp.route("/graph", methods=["GET"])
def graph():
    user_id = _require_login_user_id()

    # 何週前を表示するか（0=今週）: URLクエリからweekを取得
    week = request.args.get("week", default=0, type=int)
    if week < 0:
        week = 0

    # 「過去2週間だけ」（0〜1）の制限
    if week > 1:
        week = 1

    db = DatabaseManager()
    db.connect()

    # ------------------------------------------------------------
    # 週の範囲を作る
    # today.weekday(): 月0〜日6
    # monday: 今週の月曜日
    # week=0: 今週 / week=1: 前の週
    # ------------------------------------------------------------
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    start_date = monday - timedelta(days=7 * week)
    end_date = start_date + timedelta(days=6)  # その週の日曜日

    # 指定期間のデータを取得
    sql = """
        SELECT DATE(mood_date) AS mood_day, mood_point
        FROM t_today_moods
        WHERE user_id = %s
        AND DATE(mood_date) BETWEEN %s AND %s
        ORDER BY mood_date;
    """
    rows = db.fetch_all(sql, (user_id, start_date, end_date))

    # 日付 -> mood_point（同日複数なら最後が残る）
    mood_by_day = {}
    for r in rows:
        mood_by_day[r["mood_day"]] = r["mood_point"]

    # Chart.js用 7日分の配列（未入力日は None → JSでは null）
    dates = []
    values = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        dates.append(d.strftime("%Y-%m-%d"))
        values.append(mood_by_day.get(d, None))

    week_points = [v for v in values if v is not None]
    review = _build_week_review(week, today, end_date, week_points)

    db.disconnect()

    return render_template(
        "mood/mood_graph.html",
        dates=dates,
        values=values,
        week=week,
        start_label=start_date.strftime("%m月%d日"),
        end_label=end_date.strftime("%m月%d日"),
        can_prev=True,
        can_next=(week > 0),
        review=review, 
    )