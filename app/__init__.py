# ==========================================================
# Filename      : app/__init__.py
# Descriptions  : Application Factory
# ==========================================================
from flask import Flask, render_template,session,request,redirect,url_for
from datetime import date, timedelta
from werkzeug.routing import BuildError
from app.db import DatabaseManager
 
def create_app():
    app = Flask(__name__, instance_relative_config=True)
 
    # 1) 共有デフォルト（Git管理）
    app.config.from_object("app.config.Config")
 
    # 2) ローカル秘密（Git管理しない）※あれば上書き
    app.config.from_pyfile("config.py", silent=True)
 
# --- 修正箇所：設定を config 辞書に直接入れる ---
    # Secret Keyが設定されていないとセッションは保存されません
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = "your-very-secret-key-12345"
   
    # 30日間の有効期限を設定
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
    # --------------------------------------------
 
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
   
    # @app.before_request
    # def check_user():
    @app.before_request
    def check_user():
        endpoint = request.endpoint
 
        if endpoint is None:
            return
 
        # static は無条件許可
        if endpoint.startswith("static"):
            return
 
        # ログイン不要（許可）エンドポイント
        if endpoint in (
            'auth.login_form',
            'auth.login_process',
            'auth.register',
            'auth.register_process',
            # 'mood.register_mood_form',
            'mood.register_mood_process',
            'mood.register',
            'index',
        ):
            return
 
        # 未ログイン
        if not session.get('user_id'):
            return redirect(url_for('auth.login_form'))
 
        user_id = session['user_id']
 
        db = DatabaseManager()
        db.connect()
 
        today = date.today()
 
        # ===== 気分チェック =====
        mood_sql = """
            SELECT 1
            FROM t_today_moods
            WHERE user_id=%s
            AND mood_date >= CURDATE()
            AND mood_date < CURDATE() + INTERVAL 1 DAY
            LIMIT 1
        """
        mood = db.fetch_one(mood_sql, (user_id,))
 
        # 未登録 → 気分登録画面へ
        if not mood:
            db.disconnect()
            if endpoint not in (
                "mood.register_mood_form",
                "mood.register_mood_process",
            ):
                return redirect(url_for("mood.register_mood_form"))
            return
 
        # ===== タスク提案チェック =====
        task_sql = """
            SELECT task_suggestion_id
            FROM t_task_suggestions
            WHERE user_id=%s
            AND suggestion_date=%s
            LIMIT 1
        """
        task = db.fetch_one(task_sql, (user_id, today))
 
        db.disconnect()
 
        
 
        # すべてOK → homeへ（特定エンドポイントから来た場合の保険）
        if endpoint in (
            "mood.register_mood_form",
            "task.task_form",
            # "index",
        ):
            return redirect(url_for("main.home"))
 
        # mood -> main.home のときだけ行き先を分岐
        if endpoint == "main.home":
            ref = request.referrer or ""
            if "/mood" in ref:
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
 
                if row2 is None:
                    cnt, sid = 0, None
                elif isinstance(row2, dict):
                    cnt = int(row2.get("cnt", 0))
                    sid = row2.get("sid")
                else:
                    cnt = int(row2[0]) if len(row2) > 0 and row2[0] is not None else 0
                    sid = row2[1] if len(row2) > 1 else None
 
                if cnt >= 2:
                    return redirect(url_for("task.task_suggestion"))
 
                if cnt == 1 and sid is not None:
                    sid = int(sid)
                    session["selected_task_suggestion_id"] = sid
                    session["current_task_suggestion_id"] = sid
                    return
 
                return redirect(url_for("task.task_suggestion"))
                # 未選択（3件など）→ タスク提案へ ※3案がある状態（複数案）ならタスク提案画面に送る
                if cnt >= 2:
                    return redirect(url_for("task.task_suggestion"))
 
                # 選択済み（1件）→ main.home を表示（redirectしない）※# 1件だけなら既に選択済みとみなす
                if cnt == 1 and sid is not None:
                    sid = int(sid) # 提案IDをintに揃える
                    session["selected_task_suggestion_id"] = sid # 選択済み提案IDとしてセッションに保存
                    session["current_task_suggestion_id"] = sid  # 現在の提案IDとしてもセッションに保存
                    return  # Noneを返して main.home を表示
               
                    # # ◇ task/taskに飛ばしたい場合:
                    # return redirect(url_for("task.task_form"))
 
 
                # 0件は異常なので提案へ（保険）※今日の提案が0件は想定外＝タスク提案作成へ送る
                return redirect(url_for("task.task_suggestion"))
 
    return app  
 
 