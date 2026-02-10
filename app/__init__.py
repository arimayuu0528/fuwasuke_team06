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
        # ログインページと静的ファイルはチェックしない　無限ループ回避用
        if request.endpoint in (
            'auth.login_form',
            'auth.login_process',
            'auth.register',
            'index',
            'static'
        ):
            return


        # ログインしていなければログイン画面へ
        if not session.get('user_id'):
            return redirect(url_for('auth.login_form'))

        # 今日の気分が未登録なら登録画面へ
        db = DatabaseManager()
        db.connect()
        #今日の日付を取得
        today = date.today()

        # 今日の気分が登録されているかチェックするSQL
        sql = """
        SELECT *
        FROM t_today_moods
        WHERE user_id = %s
        AND DATE(mood_date) = %s
        """

        # ログイン中のユーザーが今日の気分を登録しているか取得
        mood = db.fetch_one(sql, (session['user_id'], today))
        db.disconnect()

        #今日の気分が未登録の場合
        if not mood and request.endpoint != 'mood.register_mood':
            return redirect(url_for('mood.register_mood'))
        

        # 登録済み → home へ
        # if request.endpoint != 'mood.home':
        #     return render_template('main/home.html')


    return app   
