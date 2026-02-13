from flask import Blueprint,render_template
from app.db import DatabaseManager

from flask import render_template
from datetime import datetime, date, timedelta
import jpholiday

# Blueprintオブジェクト作成
main_bp = Blueprint('main',__name__,url_prefix='/main')





# -----------------------------------------------------
# ホーム画面処理　（エンドポイント：'/home')  担当者名：日髙
# -----------------------------------------------------
@main_bp.route("/home")
def home():
    # return render_template('main/home.html')
  
    current_user_id = 1
    today = date.today()
    
    rec = []
    percent = 0
    remain_count = 0
    
    db = DatabaseManager()
    db.connect()
    
    try:
        # 1. プロパティからカーソルを直接取得（withは使わない）
        cursor = db.cursor 
        
        # 2. 今日のタスク提案(Header)を取得
        sql_suggestion = """
            SELECT task_suggestion_id 
            FROM t_task_suggestions 
            WHERE user_id = %s AND suggestion_date = %s
            LIMIT 1
        """
        cursor.execute(sql_suggestion, (current_user_id, today))
        suggestion = cursor.fetchone()

        if suggestion:
            # 3. 提案詳細(Detail)とタスク名を結合して取得
            sql_details = """
                SELECT 
                    t.task_name, 
                    d.plan_min,
                    d.actual_work_min
                FROM t_task_suggestion_detail d
                JOIN t_tasks t ON d.task_id = t.task_id
                WHERE d.task_suggestion_id = %s
            """
            cursor.execute(sql_details, (suggestion['task_suggestion_id'],))
            details = cursor.fetchall()

            for row in details:
                # actual_work_minがあれば完了(done)とみなす
                is_done = True if row['actual_work_min'] and row['actual_work_min'] > 0 else False
                rec.append({
                    "name": row['task_name'],
                    "time": f"{row['plan_min']}分",
                    "done": is_done
                })
        
        # カーソルを閉じる
        cursor.close()

        # 4. 達成度と残り数の計算
        total_tasks = len(rec)
        if total_tasks > 0:
            completed_tasks = len([t for t in rec if t["done"]])
            percent = int((completed_tasks / total_tasks) * 100)
            remain_count = total_tasks - completed_tasks

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # クラスの設計に合わせて disconnect または close を呼ぶ
        if hasattr(db, 'disconnect'):
            db.disconnect()
        elif hasattr(db, 'close'):
            db.close()

    return render_template(
        'task/task_home.html', 
        rec=rec, 
        percent=percent, 
        remain_count=remain_count
    )

# -----------------------------------------------------
# タスク・固定予定登録画面遷移ボタン処理　（エンドポイント：'/add_event')  担当者名：日髙
# -----------------------------------------------------
@main_bp.route("/add_event")
def add_event():
    return render_template('task/register_task.html')


# -----------------------------------------------------
# カレンダー表示画面処理　（エンドポイント：'/calendar')  担当者名：日髙
# -----------------------------------------------------
@main_bp.route("/calendar")
def main_form():
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
@main_bp.route('/report')
def report():
    return render_template('mood/mood_graph.html')


# -----------------------------------------------------
# マイページ画面表示処理　（エンドポイント：'/mypage')  担当者名：日髙
# -----------------------------------------------------
# main.py の末尾付近に追加、または既存のmypageがあれば修正

@main_bp.route("/mypage")
def mypage():
    db = DatabaseManager()
    db.connect()
    
    # 本来はセッションからユーザーIDを取得しますが、一旦 ID=1 のユーザーを取得
    user_id = 1 
    user = db.fetch_one("SELECT user_name, email FROM t_users WHERE user_id = %s", (user_id,))
    
    db.disconnect()

    # もしユーザーが見つからない場合のデフォルト値
    if not user:
        user = {'user_name': 'ゲストユーザー', 'email': '-'}

    return render_template('main/mypage.html', user=user)