import os
import json
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    # Project info
    COVER_NAME = "Strategies of Resistance Data Project"

    # Hashing
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"

    # CORS
    CORS_HEADERS = "Content-Type"

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "srdp.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email Logging Parameters
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME") or "admin"
    ADMIN_EMAIL = json.loads(os.environ.get("ADMIN_EMAILS"))
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
