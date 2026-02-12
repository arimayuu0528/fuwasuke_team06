# ==========================================================
# Filename      : app/__init__.py
# Descriptions  : Application Factory
# ==========================================================
from flask import Flask, render_template,session,request,redirect,url_for
from datetime import date
from werkzeug.routing import BuildError
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

        # ★追加
        if endpoint.startswith("static"):
            return
        if endpoint in (
            'auth.login_form',
            'auth.login_process',
            'auth.register',

            # ★追加
            "mood.register_mood_form",
            "mood.register_mood_process",

            'mood.register',   # ← 修正
            'schedule_list',

            'auth.register_process', 

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
        LIMIT 1
        """
        mood = db.fetch_one(sql, (session['user_id'], today))
        db.disconnect()


        if not mood:
            # ★追加
            try:
                return redirect(url_for("mood.register_mood_form"))
            except BuildError:
                return redirect(url_for('mood.register'))  # ← 修正


        # =============================
        # ★追加：mood→main.home のときだけ行き先を分岐
        #  - 今日の提案が3件（未選択）なら → タスク提案へ
        #  - 今日の提案が1件（選択済み）なら → main.home を表示（何もしない）
        # =============================
        if endpoint == "main.home":
            ref = request.referrer or ""
            if "/mood" in ref:
                # 初期化
                cnt = 0
                sid = None

                db2 = DatabaseManager()
                db2.connect()
                sql2 = """
                    SELECT COUNT(*) AS cnt, MAX(task_suggestion_id) AS sid
                    FROM t_task_suggestions
                    WHERE user_id = %s AND suggestion_date = %s
                """
                row2 = db2.fetch_one(sql2, (session["user_id"], today))
                db2.disconnect()

                # dict/tuple両対応で必ずcnt/sidに代入
                if row2 is None:
                    cnt, sid = 0, None
                elif isinstance(row2, dict):
                    cnt = int(row2.get("cnt", 0))
                    sid = row2.get("sid")
                else:
                    cnt = int(row2[0]) if len(row2) > 0 and row2[0] is not None else 0
                    sid = row2[1] if len(row2) > 1 else None

                # 未選択（3件など）→ タスク提案へ
                if cnt >= 2:
                    return redirect(url_for("task.task_suggestion"))

                # 選択済み（1件）→ main.home を表示（redirectしない）
                if cnt == 1 and sid is not None:
                    sid = int(sid)
                    session["selected_task_suggestion_id"] = sid
                    session["current_task_suggestion_id"] = sid
                    return  # Noneを返して main.home を表示
                
                    # # ◇ task/taskに飛ばしたい場合:
                    # return redirect(url_for("task.task_form"))


                # 0件は異常なので提案へ（保険）
                return redirect(url_for("task.task_suggestion"))

    return app   
