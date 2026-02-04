from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
main_bp = Blueprint('main',__name__,url_prefix='/main')