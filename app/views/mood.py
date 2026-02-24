from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from app.db import DatabaseManager

# Blueprint
mood_bp = Blueprint('mood', __name__, url_prefix='/mood')


@mood_bp.route("/", methods=["GET", "POST"])
def register():

    db = DatabaseManager()
    db.connect()

    # 今日すでに登録済みか確認
    check_sql = """
        SELECT 1
        FROM t_today_moods
        WHERE user_id = %s
        AND DATE(mood_date) = CURDATE()
        LIMIT 1
    """
    exists = db.fetch_one(check_sql, (session["user_id"],))

    # ✅ 登録済みならホームへ
    if exists:
        db.disconnect()
        return redirect(url_for("main.home"))

    if request.method == "POST":
        mood_value = request.form.get("mood")

        mood_point_dict = {
            "genki": 5,
            "futu": 3,
            "warui": 1
        }
        mood_point = mood_point_dict.get(mood_value, 3)

        now = datetime.now()

        insert_sql = """
            INSERT INTO t_today_moods (user_id, mood_date, mood, mood_point)
            VALUES (%s, %s, %s, %s)
        """

        db.execute_query(insert_sql, (
            session["user_id"],
            now,
            mood_value,
            mood_point
        ))

        db.disconnect()

        return redirect(url_for("main.home"))

    db.disconnect()
    return render_template("mood/register_mood.html")