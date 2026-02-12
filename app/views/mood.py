from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
from app.db import DatabaseManager
# Blueprintオブジェクト作成
mood_bp = Blueprint('mood',__name__,url_prefix='/mood')


# -----------------------------------------------------
# ○○画面処理　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
# @mood_bp.route("/register_mood")
# def register_mood():
#     return render_template("register_mood.html")




# @mood_bp.route("/home")
# def home():
#     return render_template("main/home.html")

@mood_bp.route("/", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        mood_value = request.form.get("mood")

        mood_point_dict = {
            "genki": 5,
            "futu": 3,
            "warui": 1
        }
        mood_point = mood_point_dict.get(mood_value, 3)

        db = DatabaseManager()
        db.connect()

        now = datetime.now()

        sql = """
        INSERT INTO t_today_moods (user_id, mood_date, mood, mood_point)
        VALUES (%s, %s, %s, %s)
        """

        db.execute_query(sql, (session["user_id"], now, mood_value, mood_point))

        db.disconnect()

        return redirect(url_for("main.home"))
        # # ◇「ログイン → 気分入力 → task/task」にしたい場合:
        # return redirect(url_for("task.task_form"))

    return render_template("mood/register_mood.html")


    

