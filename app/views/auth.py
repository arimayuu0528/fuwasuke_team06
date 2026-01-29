from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
auth_bp = Blueprint('auth',__name__,url_prefix='/auth')