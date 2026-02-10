from flask import Blueprint, render_template, url_for
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

@mood_bp.route("/")
def register():
    url = url_for("register")
    return render_template("register_mood.html", url)
    

