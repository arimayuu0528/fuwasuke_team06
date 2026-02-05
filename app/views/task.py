from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
task_bp = Blueprint('task',__name__,url_prefix='/task')


# -----------------------------------------------------
# ○○画面処理　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@task_bp.route("/task")
def task_form():
    # エンドポイント名、関数名は各自変更してください。
    pass