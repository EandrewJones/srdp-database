from flask import Blueprint

bp = Blueprint("admin_bp", __name__)

from app.administrator import views
