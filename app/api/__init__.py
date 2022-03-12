from flask import Blueprint
from config import Config
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = "/api/docs"
API_URL = "/api/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": Config.COVER_NAME}
)

bp = Blueprint("api", __name__)

from app.api import (
    users,
    errors,
    tokens,
    groups,
    organizations,
    violent_tactics,
    nonviolent_tactics,
)
