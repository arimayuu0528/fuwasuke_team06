# ==========================================================
# Filename      : app/__init__.py
# Descriptions  : Application Factory
# ==========================================================
from flask import Flask, render_template,session

def create_app():
    # Flaskアプリケーションのインスタンスを作成
    # __name__をappパッケージのパスに設定
    app = Flask(__name__)
    
    # config.pyから設定を読み込む
    app.config.from_object('config.Config')

    # --- Blueprintの登録 ---
    # viewsパッケージからproductsとauthのBlueprintをインポート
    # （）
    from .views import item,product,auth,schedule,task
    app.register_blueprint(item.item_bp)
    app.register_blueprint(product.product_bp)
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(schedule.schedule_bp)
    app.register_blueprint(task.task_bp)
    







    # --- トップページのルートをここで定義 ---
    @app.route('/')
    def index():
        return render_template('index.html')
    return app