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
    #     return   # ← これで完全スルー（開発用）



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


        # セッションにuser_idが無い＝未ログイン
        if not session.get('user_id'):
            # 未ログインはログイン画面へ強制送還
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

        if mood and endpoint in (
            "mood.register_mood_form",
            "mood.register_mood_process",
            "mood.register"
        ):
            return redirect(url_for("index"))


        # 今日の気分が無い（未登録）の場合:
        if not mood:
            # 気分登録フォームへ誘導
            try:
                return redirect(url_for("mood.register_mood_form"))
            except BuildError:
                return redirect(url_for('mood.register'))  # ← 修正



        # =============================
        # ★追加：mood→main.home のときだけ行き先を分岐
        #  - 今日の提案が3件（未選択）なら → タスク提案へ
        #  - 今日の提案が1件（選択済み）なら → main.home を表示（何もしない）
        # =============================
        if endpoint == "main.home": # 今から行こうとしているのが main.home の場合:
            ref = request.referrer or "" # 直前ページURL
            if "/mood" in ref:      # mood系ページから来た（＝気分登録直後）と判断できる場合だけ
                # 初期化
                cnt = 0             # 今日の提案が何件あるか
                sid = None          # 今日の提案IDを入れる

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
                if row2 is None: # 何も返らない（0件・異常）場合:
                    cnt, sid = 0, None       # 0件扱いにする
                elif isinstance(row2, dict): # dict形式（例：{"cnt": 3, "sid": 10}）の場合:
                    cnt = int(row2.get("cnt", 0)) # cntを取り出してint化（無ければ0）
                    sid = row2.get("sid")    # sidを取り出す（Noneの可能性あり）
                else:
                    # 1要素目をcntとして読む
                    cnt = int(row2[0]) if len(row2) > 0 and row2[0] is not None else 0
                    # 2要素目をsidとして読む（無ければNone）
                    sid = row2[1] if len(row2) > 1 else None

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
