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
        endpoint = request.endpoint

        if endpoint is None:
            return

        if endpoint in (
            'auth.login_form',
            'auth.login_process',
            'auth.register',
            'mood.register',   # ← 修正
            'index',
            'static'
        ):
            return

        if not session.get('user_id'):
            return redirect(url_for('auth.login_form'))

        db = DatabaseManager()
        db.connect()

        today = date.today()
        sql = """
        SELECT 1
        FROM t_today_moods
        WHERE user_id = %s
        AND DATE(mood_date) = %s
        """
        mood = db.fetch_one(sql, (session['user_id'], today))
        db.disconnect()

        if not mood:
            return redirect(url_for('mood.register'))  # ← 修正

    return app   
