from flask import Blueprint,render_template,request,session,redirect,url_for,flash
from datetime import date, datetime  # 今日の日付や日時計算に使う
from app.db import DatabaseManager

# Blueprintオブジェクト作成
task_bp = Blueprint('task',__name__,url_prefix='/task')


# -----------------------------------------------------
# タスク(ホーム)：担当者名 向山
# -----------------------------------------------------

@task_bp.route("/task")
def task_form():
    rec=request.form
    return render_template('task_home.html')
    # エンドポイント名、関数名は各自変更してください。
    pass

# -----------------------------------------------------
# タスク一覧：担当者名 向山
# -----------------------------------------------------

@task_bp.route("/task_list")
def task_list():
    pass

# -----------------------------------------------------
# タスク作成：担当者名 向山
# -----------------------------------------------------

@task_bp.route("/task_create")
def task_create():
    pass

# --------------------------------------------------------
# タスク提案：担当者名 有馬
# --------------------------------------------------------
@task_bp.route("/task_suggestion")
def task_suggestion():
    
    return render_template('task_suggestion.html')