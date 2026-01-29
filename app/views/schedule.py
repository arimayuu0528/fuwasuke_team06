from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
schedule_bp = Blueprint('schedule',__name__,url_prefix='/schedule')