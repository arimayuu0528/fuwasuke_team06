# app/config.py
import os
from dotenv import load_dotenv

# .env 読み込み
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret_key_py24')

    DB_HOST='localhost'
    DB_USER='suke'
    DB_PASSWORD='suke06'
    DB_DATABASE='huwasuke_db'