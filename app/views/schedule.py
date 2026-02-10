from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import DatabaseManager
from datetime import datetime

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')


# -----------------------------------------------------
# 固定タスク登録画面・登録処理
# URL：/schedule/schedule
# -----------------------------------------------------
@schedule_bp.route('/schedule', methods=['GET', 'POST'])
def schedule_form():
    if request.method == 'POST':
        title = request.form['title']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        active_days = request.form['active_days']
        category = request.form['category']
        memo = request.form['memo']

        # 仮ユーザーID（ログイン後は session['user_id']）
        user_id = 1

        # duration_min 計算
        fmt = "%H:%M"
        duration_min = (
            datetime.strptime(end_time, fmt)
            - datetime.strptime(start_time, fmt)
        ).seconds // 60

        db = DatabaseManager()
        db.connect()

        sql = """
        INSERT INTO t_fixed_schedule_masters
        (
            user_id,
            title,
            duration_min,
            start_time,
            end_time,
            repeat_type,
            day_of_week,
            location,
            tag,
            memo
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        params = (
            user_id,
            title,
            duration_min,
            start_time,
            end_time,
            "weekly",
            active_days,
            "",
            category,
            memo
        )

        db.execute_query(sql, params)
        db.disconnect()

        return redirect(url_for('schedule.schedule_list'))



# -----------------------------------------------------
# 固定タスク一覧
# URL：/schedule/list
# -----------------------------------------------------
@schedule_bp.route("/list")
def schedule_list():
    db = DatabaseManager()
    db.connect()

    sql = """
    SELECT
        master_id,
        title,
        start_time,
        end_time,
        day_of_week,
        tag,
        memo
    FROM t_fixed_schedule_masters
    ORDER BY start_time
    """

    rows = db.fetch_all(sql)

    if not rows:
        rows = []

    tasks = []
    for row in rows:
        tasks.append({
            "id": row["master_id"],
            "title": row["title"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "category": row["tag"],
            "comment": row["memo"],
            "active_days": list(row["day_of_week"]) if row["day_of_week"] else []
        })
        rows = db.fetch_all("SELECT * FROM t_fixed_schedule_masters")

    print("DEBUG rows:", rows)


    db.disconnect()
    return render_template("schedule/schedule_list.html", tasks=tasks)
