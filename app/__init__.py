from flask import Flask

def create_app():
    app = Flask(__name__)

    # ここでBlueprintを登録する（追加するたびここに1行増やす）-------------------------------------
    from .blueprints.product import product_bp
    from .blueprints.item import item_bp

    app.register_blueprint(product_bp)
    app.register_blueprint(item_bp)
    # -----------------------------------------------------------------------------------------
    @app.get("/")
    def health():
        return {"ok": True}

    return app
