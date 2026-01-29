from flask import Blueprint,render_template
from app.db import DatabaseManager

# Blueprintオブジェクト作成
task_bp = Blueprint('task',__name__,url_prefix='/task')