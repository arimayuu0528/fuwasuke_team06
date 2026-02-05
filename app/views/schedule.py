from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
schedule_bp = Blueprint('schedule',__name__,url_prefix='/schedule')


# -----------------------------------------------------
# ○○画面処理　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@schedule_bp.route("/schedule")
def schedule_form():
    # エンドポイント名、関数名は各自変更してください。
    pass