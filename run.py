# ==========================================================
# Filename      : run.py 02/24
# Descriptions  : アプリケーション起動ファイル
# ==========================================================
# appパッケージからcreate_app関数をインポート
from app import create_app

# create_app関数を呼び出してアプリケーションインスタンスを作成
app = create_app()

if __name__ == '__main__':
    # アプリケーションをデバッグモードで実行
    app.run(host='0.0.0.0', port=5000, debug=True)