from flask import Blueprint,render_template,request,session,redirect,url_for
from app.db import DatabaseManager
from datetime import timedelta

# Blueprintオブジェクト作成
auth_bp = Blueprint('auth',__name__,url_prefix='/auth')

# Blueprint内でセッション有効期限を設定（30日）
@auth_bp.before_app_request
def make_session_permanent():
    session.permanent = True

# -----------------------------------------------------
# ログイン画面表示　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@auth_bp.route("/login", methods=["GET"])
def login_form():
    return render_template("auth/login.html")
# -----------------------------------------------------
# ログイン処理　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login_process():
    email = request.form.get("email")
    password = request.form.get("password")

    # 未入力チェック
    if not email or not password:
        return render_template(
            "auth/login.html",
            error="メールアドレスとパスワードを入力してください"
        )

    db = DatabaseManager()
    db.connect()

    sql = """
        SELECT user_id, email, user_name
        FROM t_users
        WHERE email = %s AND password = %s
    """
    user = db.fetch_one(sql, (email, password))
    db.disconnect()

    #認証失敗
    if user is None:
        return render_template(
            'auth/login.html',
            error='メールアドレスまたはパスワードが違います'
        )
    
    #sessionに保存、30日間保持
    session.permanent = True
    session["user_id"] = user["user_id"]
    session["user_name"] = user["user_name"]

    # ログイン成功
    return redirect(url_for("mood.register"))
# -----------------------------------------------------
# 新規登録画面表示　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@auth_bp.route("/register", methods=["GET"])
def register():
    return render_template("auth/register_user.html")
# -----------------------------------------------------
# 新規登録処理　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@auth_bp.route("/register", methods=["POST"])
def register_process():
    email = request.form.get("email")
    password = request.form.get("password")
    user_name = request.form.get("user_name")
    wakeup_time = request.form.get("wakeup_time")
    sleep_time = request.form.get("sleep_time")

    db = DatabaseManager()
    db.connect()

    # メールアドレス重複チェック
    sql = "SELECT user_id FROM t_users WHERE email = %s"
    existing = db.fetch_one(sql, (email,))

    if existing:
        db.disconnect()
        return render_template(
            "auth/register_user.html",
            error="このメールアドレスはすでに登録されています"
        )

    # ユーザー登録
    sql = """
        INSERT INTO t_users (email, password, user_name, wakeup_time, sleep_time)
        VALUES (%s, %s, %s, %s, %s)
    """
    db.execute_query(sql, (email, password, user_name, wakeup_time, sleep_time))
    db.disconnect()

    # session保存
    session["user_name"] = user_name

    return redirect(url_for("auth.login_form"))
# -----------------------------------------------------
# ログアウト処理　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_form"))
