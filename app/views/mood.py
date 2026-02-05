from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
mood_bp = Blueprint('mood',__name__,url_prefix='/mood')


# -----------------------------------------------------
# ○○画面処理　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@mood_bp.route("/mood")
def mood_form():
    # エンドポイント名、関数名は各自変更してください。
    pass