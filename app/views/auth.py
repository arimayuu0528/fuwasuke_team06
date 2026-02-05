from flask import Blueprint,render_template,request
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
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    # 未入力チェック
    if not email or not password:
        return render_template(
            "auth/login.html",
            error="メールアドレスとパスワードを入力してください"
        )

    db = DatabaseManager()
    user = db.get_user_by_email(email)

    # ユーザーが存在しない or パスワード不一致
    if not user or user["password"] != password:
        return render_template(
            "auth/login.html",
            error="メールアドレスまたはパスワードが違います"
        )

    # ログイン成功
    return render_template("mood/register_mood.html")