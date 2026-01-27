import mysql.connector
from flask import current_app #current_appをインポート


class DatabaseManager:
    # current_appからDBの設定を読み込む
    def __init__(self):
        self.host = current_app.config['DB_HOST']
        self.user = current_app.config['DB_USER']
        self.passwd = current_app.config['DB_PASSWORD']
        self.db = current_app.config['DB_DATABASE']
        self.connection = None
        self.cursor = None

    # DBの接続メソッド
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host = self.host,
                user = self.user,
                passwd = self.passwd,
                db = self.db
            )
            self.cursor = self.connection.cursor(dictionary=True)
            print("データベースに接続しました。")
        except mysql.connector.Error as err:
            print(f"接続エラー：{err}")


    # DBの切断メソッド
    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()


    # データ取得メソッド(fetch_all)
    def fetch_all(self,sql,params=None):
        if self.cursor is None:
            return None
        try:
            self.cursor.execute(sql,params)
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"クエリエラー：{err}")
            return None
        

    # データ取得メソッド(fetch_one)
    def fetch_one(self,sql,params=None):
        if self.cursor is None:
            return None
        try:
            self.cursor.execute(sql,params)
            return self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"クエリエラー：{err}")
            return None
        

    # データ操作メソッド(INSERT,UPDATE,DELETE用)
    def execute_query(self,sql,params=None):
        if self.cursor is None:
            return False
        try:
            self.cursor.execute(sql,params)
            self.connection.commit()
            print("クエリを実行し、コミットしました。")
            return True
        except mysql.connector.Error as err:
            print(f"クエリエラー：{err}")
            self.connection.rollback()
            return False
