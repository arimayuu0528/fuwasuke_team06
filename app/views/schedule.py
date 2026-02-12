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
    # カテゴリーのリストを定義
    categories = ['セルフケア', '仕事', '勉強', '趣味', '運動', '家事']

    if request.method == 'POST':
        title = request.form['title']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        active_days = request.form.get('active_days', "")
        category = request.form['category']
        memo = request.form['memo']

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
            user_id,title,duration_min,start_time,end_time,
            repeat_type,day_of_week,location,tag,memo
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        params = (
            user_id,title,duration_min,start_time,end_time,
            "weekly",active_days,"",category,memo
        )

        # 👇 直接実行してcommit
        db.cursor.execute(sql, params)
        db.connection.commit()

        print("保存完了")

        db.disconnect()

        return redirect(url_for('schedule.schedule_list'))

    # GETの場合、カテゴリーを渡す
    return render_template("schedule/register_schedule.html", categories=categories)




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

    db.disconnect()

    return render_template("schedule/schedule_list.html", tasks=tasks)

# -----------------------------------------------------
# 固定タスク削除
# URL：/schedule/delete/<id>
# -----------------------------------------------------
@schedule_bp.route("/delete/<int:master_id>", methods=["POST"])
def delete_schedule(master_id):
    db = DatabaseManager()
    db.connect()

    sql_child = "DELETE FROM t_fixed_schedule_instances WHERE master_id = %s"
    db.cursor.execute(sql_child, (master_id,))

    sql_parent = "DELETE FROM t_fixed_schedule_masters WHERE master_id = %s"
    db.cursor.execute(sql_parent, (master_id,))

    db.connection.commit()
    db.disconnect()

    return redirect(url_for("schedule.schedule_list"))