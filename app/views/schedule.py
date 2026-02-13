from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import DatabaseManager
from datetime import datetime

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')


# -----------------------------------------------------
# 固定タスク登録画面・登録処理
# URL：/schedule/
# -----------------------------------------------------
@schedule_bp.route('/', methods=['GET', 'POST'])
def schedule_form():

    tags = ['仕事', '休憩', '健康', '趣味']

    if request.method == 'POST':
        title = request.form['title']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        day_of_week = request.form.get('day_of_week', "")
        repeat_type = request.form.get('repeat_type', '毎日')
        location = request.form.get('location', '')
        tag = request.form['tag']
        memo = request.form.get('memo', '')

        user_id = 1

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
            user_id, title, duration_min, start_time, end_time,
            repeat_type, day_of_week, location, tag, memo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            user_id, title, duration_min, start_time, end_time,
            repeat_type, day_of_week, location, tag, memo
        )

        db.cursor.execute(sql, params)
        db.connection.commit()
        db.disconnect()

        return redirect(url_for('schedule.schedule_list'))

    return render_template("schedule/register_schedule.html", tags=tags)


# -----------------------------------------------------
# 固定タスク一覧
# URL：/schedule/list
# -----------------------------------------------------
@schedule_bp.route('/list')
def schedule_list():

    user_id = 1

    db = DatabaseManager()
    db.connect()

    sql = """
    SELECT 
        master_id,
        title,
        duration_min,
        start_time,
        end_time,
        repeat_type,
        day_of_week,
        location,
        tag,
        memo
    FROM t_fixed_schedule_masters
    WHERE user_id = %s
    ORDER BY start_time, title
    """


    db.cursor.execute(sql, (user_id,))
    rows = db.cursor.fetchall()

    tasks = []
    for row in rows:
        task = {
            'id': row['master_id'],
            'title': row['title'],
            'duration_min': row['duration_min'],
            'start_time': row['start_time'],
            'end_time': row['end_time'],
            'repeat_type': row['repeat_type'],
            'day_of_week': row['day_of_week'],
            'location': row['location'],
            'tag': row['tag'],
            'memo': row['memo'],
            'active_days': row['day_of_week'] if row['day_of_week'] else ''
        }

        tasks.append(task)

    db.disconnect()

    return render_template('schedule/schedule_list.html', tasks=tasks)


# -----------------------------------------------------
# 削除
# URL：/schedule/delete/◯◯
# -----------------------------------------------------
@schedule_bp.route('/delete/<int:task_id>', methods=['POST'])
def delete_schedule(task_id):

    user_id = 1

    db = DatabaseManager()
    db.connect()

    sql = """
    DELETE FROM t_fixed_schedule_masters
    WHERE master_id = %s AND user_id = %s
    """


    db.cursor.execute(sql, (task_id, user_id))
    db.connection.commit()
    db.disconnect()

    return redirect(url_for('schedule.schedule_list'))
