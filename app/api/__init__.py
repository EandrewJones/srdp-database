from flask import Blueprint
from config import Config
from flask_swagger_ui import get_swaggerui_blueprint
from app.models import User
from app import db

SWAGGER_URL = "/api/docs"
API_URL = "/api/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": Config.COVER_NAME}
)

bp = Blueprint("api", __name__, cli_group=None)

# Create admin command
@bp.cli.command("create-admin")
def create_admin():
    uname = Config.ADMIN_USERNAME
    email = Config.ADMIN_EMAIL
    pword = Config.ADMIN_PASSWORD
    # Check if admin user already exists
    admin_exists = User.query.filter_by(username=uname).first() is not None
    if admin_exists:
        print(f"Default admin <username: {uname}, email: {email}> already exists.")
        return

    # Create default admin
    admin = User(
        username=uname,
        email=email,
    )
    admin.set_password(password=pword)
    db.session.add(admin)
    db.session.commit()
    print(f"Admin <username: {uname}, email: {email}> successfully created.")


from app.api import (
    users,
    errors,
    tokens,
    groups,
    organizations,
    violent_tactics,
    nonviolent_tactics,
)
