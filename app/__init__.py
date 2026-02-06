# ==========================================================
# Filename      : app/__init__.py
# Descriptions  : Application Factory
# ==========================================================
from flask import Flask, render_template,session,request,redirect,url_for
from datetime import date
from app.db import DatabaseManager

def create_app():
    app = Flask(__name__, instance_relative_config=True)
 
    # 1) 共有デフォルト（Git管理）
    app.config.from_object("app.config.Config")
 
    # 2) ローカル秘密（Git管理しない）※あれば上書き
    app.config.from_pyfile("config.py", silent=True)
 
  
   


    # --- Blueprintの登録 ---
    # viewsパッケージからproductsとauthのBlueprintをインポート
    from .views import auth,schedule,task,mood,main

    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(schedule.schedule_bp)
    app.register_blueprint(task.task_bp)
    app.register_blueprint(mood.mood_bp)
    app.register_blueprint(main.main_bp)
    

    # --- トップページのルートをここで定義 ---
    @app.route('/')
    def index():
        return render_template('auth/login.html')
    


    @app.before_request
    def check_user():
        # ログインページと静的ファイルはチェックしない
        if request.endpoint in ('auth.login', 'index', 'static'):
            return

        # ログインしていなければログイン画面へ
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))

        # 今日の気分が未登録なら登録画面へ
        db = DatabaseManager()
        today = date.today()

        sql = "SELECT * FROM t_today_moods WHERE user_id = %s AND mood_date = %s"
        mood = db.query(sql, (session['user_id'], today), fetch_one=True)

        if not mood and request.endpoint != 'mood.register_mood':
            return redirect(url_for('mood.register_mood'))
        

    return app   
