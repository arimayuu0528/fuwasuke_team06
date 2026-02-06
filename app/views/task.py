from flask import Blueprint,render_template,request
from app.db import DatabaseManager

# Blueprintオブジェクト作成
task_bp = Blueprint('task',__name__,url_prefix='/task')


# -----------------------------------------------------
# ○○画面処理　（エンドポイント：' ')  担当者名：有馬、向山
# -----------------------------------------------------

# -----------------------------------------------------
# タスク(ホーム)
# -----------------------------------------------------

@task_bp.route("/task")
def task_form():
    rec=request.form
    
    # エンドポイント名、関数名は各自変更してください。
    pass

# -----------------------------------------------------
# タスク一覧
# -----------------------------------------------------

@task_bp.route("/task_list")
def task_list():
    pass

# -----------------------------------------------------
# タスク作成
# -----------------------------------------------------

@task_bp.route("/task_create")
def task_create():
    pass

# -----------------------------------------------------
# タスク提案
# -----------------------------------------------------

@task_bp.route("/task_suggestion")
def task_suggestion():
    
    return render_template('suggestion_task.html')