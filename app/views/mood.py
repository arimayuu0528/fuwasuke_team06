from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
mood_bp = Blueprint('mood',__name__,url_prefix='/mood')