from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
main_bp = Blueprint('main',__name__,url_prefix='/main')


# -----------------------------------------------------
# ○○画面処理　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@main_bp.route("/main")
def main_form():
    # エンドポイント名、関数名は各自変更してください。
    pass