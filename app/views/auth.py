from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
auth_bp = Blueprint('auth',__name__,url_prefix='/auth')


# -----------------------------------------------------
# ○○画面処理　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@auth_bp.route("/login")
def login_form():
    # エンドポイント名、関数名は各自変更してください。
    pass