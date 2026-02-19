from flask import Blueprint,render_template,session,redirect,url_for,request
from app.db import DatabaseManager

from flask import render_template
from datetime import datetime, date, timedelta
import jpholiday

import mysql.connector

# Blueprintオブジェクト作成
main_bp = Blueprint('main',__name__,url_prefix='/main')





# -----------------------------------------------------
# ホーム画面処理　（エンドポイント：'/home')  担当者名：向山
# -----------------------------------------------------
@main_bp.route("/home")
def home():
    current_user_id = 1
    
    # データ確認用に日付を固定（サンプルデータに合わせる）
    today = date(2026, 1, 26)  

    rec = []
    percent = 0
    remain_count = 0

    db = DatabaseManager()
    db.connect()

    try:
        cursor = db.cursor

        # ==========================
        # 1. 今日の曜日
        # ==========================
        week_labels = ["日","月","火","水","木","金","土"]
        today_week = week_labels[today.weekday()]

        # ==========================
        # 2. 固定予定（曜日判定＋キャンセル反映）
        # ==========================
        sql_fixed = """
            SELECT m.master_id, m.title, m.start_time, m.end_time,
                   i.is_cancelled
            FROM t_fixed_schedule_masters m
            LEFT JOIN t_fixed_schedule_instances i
              ON m.master_id = i.master_id AND i.schedule_date = %s
            WHERE m.user_id = %s
              AND (m.repeat_type='毎日' OR m.day_of_week LIKE CONCAT('%%', %s, '%%'))
            ORDER BY m.start_time
        """
        cursor.execute(sql_fixed, (today, current_user_id, today_week))
        fixed_schedules = cursor.fetchall()

        for item in fixed_schedules:
            # インスタンスでキャンセルされていればスキップ
            if item.get('is_cancelled'):
                continue
            s_time = item['start_time'].strftime('%H:%M') if hasattr(item['start_time'], 'strftime') else str(item['start_time'])
            e_time = item['end_time'].strftime('%H:%M') if hasattr(item['end_time'], 'strftime') else str(item['end_time'])
            rec.append({
                "name": item['title'],
                "time": f"{s_time} - {e_time}",
                "done": False,
                "is_fixed": True
            })

        # ==========================
        # 3. 今日の提案タスク
        # ==========================
        sql_suggestion = """
            SELECT task_suggestion_id 
            FROM t_task_suggestions 
            WHERE user_id = %s AND suggestion_date = %s
            LIMIT 1
        """
        cursor.execute(sql_suggestion, (current_user_id, today))
        suggestion = cursor.fetchone()

        if suggestion:
            sql_details = """
                SELECT t.task_name, d.plan_min, d.actual_work_min
                FROM t_task_suggestion_detail d
                JOIN t_tasks t ON d.task_id = t.task_id
                WHERE d.task_suggestion_id = %s
            """
            cursor.execute(sql_details, (suggestion['task_suggestion_id'],))
            details = cursor.fetchall()

            for row in details:
                is_done = True if row.get('actual_work_min') and row['actual_work_min'] > 0 else False
                rec.append({
                    "name": row['task_name'],
                    "time": f"{row['plan_min']}分",
                    "done": is_done,
                    "is_fixed": False
                })

        cursor.close()

        # ==========================
        # 4. 達成度と残り数（提案タスクのみ）
        # ==========================
        proposal_tasks = [t for t in rec if not t["is_fixed"]]
        total_tasks = len(proposal_tasks)
        if total_tasks > 0:
            completed_tasks = len([t for t in proposal_tasks if t["done"]])
            percent = int((completed_tasks / total_tasks) * 100)
            remain_count = total_tasks - completed_tasks

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

    return render_template(
        'task/task_home.html', 
        rec=rec, 
        percent=percent, 
        remain_count=remain_count
    )



# -----------------------------------------------------
# タスク・固定予定登録画面遷移ボタン処理　（エンドポイント：'/add_event')  担当者名：日髙
# -----------------------------------------------------
# @main_bp.route("/add_event")
# def add_event():
#     return render_template('schedule/register_schedule.html')


# -----------------------------------------------------
# カレンダー表示画面処理　（エンドポイント：'/calendar')  担当者名：日髙
# -----------------------------------------------------
@main_bp.route("/calendar")
def main_form():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login_form'))
    
    db = DatabaseManager()
    db.connect()

    sql_masters = """
        SELECT title, start_time, end_time, location, tag, memo, day_of_week, DATE(created_at) as created_date
        FROM t_fixed_schedule_masters
        WHERE user_id = %s AND is_cancelled = 0
    """
    masters = db.fetch_all(sql_masters, (user_id,)) or []

    print(masters)
    db.disconnect()

    # 2. 表示範囲の設定
    today = date.today()
    start_date = (today - timedelta(days=365)).replace(day=1)
    end_date = (today + timedelta(days=365)).replace(day=1) - timedelta(days=31)
    end_date = end_date.replace(day=1) - timedelta(days=1)

    events_json = {}
    holidays_json = {}
    
    # 曜日の漢字マップ（Pythonの0=月〜6=日を漢字に変換）
    weekday_map = ["月", "火", "水", "木", "金", "土", "日"]

    curr = start_date
    while curr <= end_date:
        date_str = curr.strftime('%Y-%m-%d')
        
        # 祝日判定
        holiday_name = jpholiday.is_holiday_name(curr)
        if holiday_name:
            holidays_json[date_str] = holiday_name

        # 今日の曜日を漢字にする
        current_kanji = weekday_map[curr.weekday()]

        # その日の予定を格納する「空のリスト」を作成（上書き防止）
        day_events = []

        for m in masters:
            # 作成日がNULLの場合の安全策（作成日以降の判定）
            m_created = m.get('created_date') or date(2000, 1, 1)
            
            # 条件：作成日以降、かつ、マスタの曜日文字列に今日の漢字が含まれているか
            if curr >= m_created and current_kanji in m['day_of_week']:
                def format_timedelta(td):
                    if td is None:
                        return ""
                    if isinstance(td, timedelta):
                        total_seconds = int(td.total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        return f"{hours:02}:{minutes:02}"
                    if hasattr(td, 'strftime'):
                        return td.strftime('%H:%M')
                    return str(td)
                
                s_time = format_timedelta(m['start_time'])
                e_time = format_timedelta(m['end_time'])
                day_events.append({
                    "title":m['title'],
                    "start_time":s_time,
                    "end_time":e_time,
                    "location":m['location'] or "",
                    "tag":m['tag'] or "",
                    "memo":m['memo'] or ""
                })
            

        # 予定リストに中身があれば、日付をキーにして保存
        if day_events:
            events_json[date_str] = day_events
        
        curr += timedelta(days=1)

    # 3. テンプレートへ渡す
    return render_template(
        'main/calendar.html',
        events_json=events_json,
        holidays_json=holidays_json,
        current_year=today.year,
        current_month=today.month
    )



# -----------------------------------------------------
# レポート画面表示処理　（エンドポイント：'/report')  担当者名：大井
# -----------------------------------------------------


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="huwasuke_db"
    )


@main_bp.route("/mood_graph/<int:user_id>")
def mood_graph(user_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 直近7日分を取得
    query = """
        SELECT DATE(mood_date) as d, mood_point
        FROM t_today_moods
        WHERE user_id = %s
        AND mood_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        ORDER BY d
    """

    cursor.execute(query, (user_id,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    # DB結果を辞書化
    mood_dict = {}
    for row in results:
        mood_dict[row["d"]] = row["mood_point"]

    # 直近7日をすべて生成（欠け日も埋める）
    today = datetime.today().date()
    dates = []
    values = []

    for i in range(6, -1, -1):  # 7日前〜今日
        day = today - timedelta(days=i)
        dates.append(day.strftime("%m-%d"))
        values.append(mood_dict.get(day, None))  # 無い日は None

    return render_template(
        "mood/mood_graph.html",
        dates=dates,
        values=values
    )



# -----------------------------------------------------
# マイページ画面表示処理　（エンドポイント：'/mypage')  担当者名：日髙
# -----------------------------------------------------
# main.py の末尾付近に追加、または既存のmypageがあれば修正

@main_bp.route("/mypage", methods=["GET","POST"])
def mypage():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('auth.login_form'))

    db = DatabaseManager()
    db.connect()

    if request.method == "POST":
        wakeup_time = request.form.get("wakeup_time")
        sleep_time = request.form.get("sleep_time")

        update_sql = "UPDATE t_users SET wakeup_time = %s, sleep_time = %s WHERE user_id = %s"
        db.execute_query(update_sql,(wakeup_time,sleep_time,user_id))
        return redirect(url_for('main.mypage'))
    
    user = db.fetch_one("SELECT user_name, email, wakeup_time, sleep_time FROM t_users WHERE user_id = %s" , (user_id,))

    if user:
        if user.get('wakeup_time'):
            total_seconds = int(user['wakeup_time'].total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            user['wakeup_time'] = f"{hours:02}:{minutes:02}"

        if user.get('sleep_time'):
            total_seconds = int(user['sleep_time'].total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            user['sleep_time'] = f"{hours:02}:{minutes:02}"

    today = date.today()
    sql_mood = """
        SELECT mood
        FROM t_today_moods
        WHERE user_id = %s AND DATE(mood_date) = %s
        ORDER BY mood_date DESC LIMIT 1
    """
    mood_data = db.fetch_one(sql_mood,(user_id,today))
    
    db.disconnect()

    

    mood_map = {
        "genk" : "元気",
        "futu" : "普通",
        "waru" : "悪い"
    }

    display_mood = "未登録"
    if mood_data:
        display_mood = mood_map.get(mood_data['mood'],mood_data['mood'])

    print(display_mood)


    return render_template('main/mypage.html', user=user,today_mood=display_mood)