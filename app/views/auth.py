from flask import Blueprint,render_template,request,session,redirect,url_for
from app.db import DatabaseManager

# Blueprintオブジェクト作成
auth_bp = Blueprint('auth',__name__,url_prefix='/auth')


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
    print(sql)
    print(user)
    db.disconnect()

    #認証失敗
    if user is None:
        return render_template(
            'auth/login.html',
            error='メールアドレスまたはパスワードが違います'
        )
    
    #sessionに保存
    session["user_id"] = user["user_id"]
    session["user_name"] = user["user_name"]

    # ログイン成功
    return redirect(url_for("main.main_form"))
# -----------------------------------------------------
# 新規登録画面表示　（エンドポイント：' ')  担当者名：
# -----------------------------------------------------
@auth_bp.route('/register')
def register():
    return render_template('auth/register_user.html')
