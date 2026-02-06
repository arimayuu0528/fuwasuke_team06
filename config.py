# ==========================================================
# Filename      : config.py
# Descriptions  : 設定ファイル
# ==========================================================
import os

class Config:
    # Flaskのセッション機能や特定の拡張機能で暗号化キーとして使用される
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret_key_py24'

    # DB接続情報を追加
    DB_HOST = 'localhost'
    DB_USER = 'team06'
    DB_PASSWORD = 'team06fuwasuke'
    DB_DATABASE = 'huwasuke_db'
