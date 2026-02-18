from flask import Blueprint,render_template,session,redirect,url_for,request
from app.db import DatabaseManager

from flask import render_template
from datetime import datetime, date, timedelta
import jpholiday

import mysql.connector

# Blueprintオブジェクト作成
main_bp = Blueprint('main',__name__,url_prefix='/main')





# -----------------------------------------------------
# ホーム画面処理　（エンドポイント：'/home')  担当者名：
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

    # データ取得
    instance_rows = db.fetch_all("SELECT i.schedule_date, m.title, i.start_time FROM t_fixed_schedule_instances i JOIN t_fixed_schedule_masters m ON i.master_id = m.master_id WHERE i.is_cancelled = 0")
    master_rows = db.fetch_all("SELECT title, repeat_type, day_of_week, start_time FROM t_fixed_schedule_masters")
    min_date_result = db.fetch_one("SELECT MIN(schedule_date) as start_from FROM t_fixed_schedule_instances")
    db.disconnect()

    today = date.today()
    start_date = min_date_result['start_from'] if min_date_result and min_date_result['start_from'] else today - timedelta(days=365)
    if isinstance(start_date, datetime): start_date = start_date.date()
    end_date = today + timedelta(days=365)

    events_dict = {}
    

    instance_lookup = {}
    
    for row in instance_rows:
        date_key = row['schedule_date'].strftime('%Y-%m-%d')
        time_obj = row['start_time']
        time_str = time_obj.strftime('%H:%M:%S') if hasattr(time_obj, 'strftime') else str(time_obj).zfill(8)
        
        if date_key not in events_dict:
            events_dict[date_key] = []
            instance_lookup[date_key] = set()
            
        events_dict[date_key].append({'title': row['title'], 'time': time_str})
        instance_lookup[date_key].add(row['title'])


    weekday_map = {0:'月',1:'火',2:'水',3:'木',4:'金',5:'土',6:'日'}

    for m in master_rows:
        time_obj = m['start_time']
        time_str = time_obj.strftime('%H:%M:%S') if hasattr(time_obj, 'strftime') else str(time_obj).zfill(8)
        m_title = m['title']
        m_repeat = m['repeat_type']
        m_dow = m['day_of_week'] or ""

        curr = start_date
        while curr <= end_date:
            date_key = curr.strftime('%Y-%m-%d')
            
            if not (date_key in instance_lookup and m_title in instance_lookup[date_key]):
                should_add = False
                if m_repeat == '毎日':
                    if not m_dow or weekday_map[curr.weekday()] in m_dow:
                        should_add = True
                elif m_repeat == '毎週':
                    if m_dow and weekday_map[curr.weekday()] in m_dow:
                        should_add = True
                
                if should_add:
                    if date_key not in events_dict:
                        events_dict[date_key] = []
                    events_dict[date_key].append({'title': m_title, 'time': time_str})
            
            curr += timedelta(days=1)

    # ソート処理
    sorted_events_dict = {}
    for d_key, ev_list in events_dict.items():
        ev_list.sort(key=lambda x: x['time'])
        sorted_events_dict[d_key] = [e['title'] for e in ev_list]

    # 祝日計算
    holidays_dict = {}
    curr_h = start_date
    while curr_h <= end_date:
        name = jpholiday.is_holiday_name(curr_h)
        if name:
            holidays_dict[curr_h.strftime('%Y-%m-%d')] = name
        curr_h += timedelta(days=1)

    return render_template('main/calendar.html',
                            holidays_json=holidays_dict,
                            current_year=today.year,
                            current_month=today.month,
                            events_json=sorted_events_dict)


# -----------------------------------------------------
# レポート画面表示処理　（エンドポイント：'/report')  担当者名：日髙
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