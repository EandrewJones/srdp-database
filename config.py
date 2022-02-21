import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):

    # Website Cover Name, Logo, and Background
    COVER_NAME = os.environ.get("COVER_NAME") or "CogSec SMS"
    LOGO = os.environ.get("LOGO") or "logo-1.png"
    BG = os.environ.get("BG") or "background-space1.jpeg"

    # Experiment Variables
    EXP_LENGTH_DAYS = int(os.environ.get("EXPERIMENT_LENGTH_DAYS")) or 7
    ALLOW_EMBEDS = os.environ.get("ALLOW_LINK_EMBEDS") == "True"

    # Cookies
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"

    # CORS
    CORS_HEADERS = "Content-Type"

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email Logging Parameters
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    ADMINS = os.environ.get("ADMIN")

    # App language and admin parameters
    LANGUAGES = ["en", "es"]
    MS_TRANSLATOR_KEY = os.environ.get("MS_TRANSLATOR_KEY")

    # Search bar
    ES_URL = os.environ.get("ES_URL")
    POSTS_PER_PAGE = 25

    # ELK
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")
    LOGSTASH_URL = os.environ.get("LOGSTASH_URL")

    # UserALE logging
    USERALE_OBSERVE_TARGET = os.environ.get("USERALE_OBSERVE_TARGET")
    USERALE_MUTATION_TARGET = os.environ.get("USERALE_MUTATION_TARGET")
    USERALE_LOG_THRESHOLD = os.environ.get("USERALE_LOG_THRESHOLD")
    USERALE_LOG_TYPE = os.environ.get("USERALE_LOG_TYPE")
    USERALE_EVENT_TYPE = os.environ.get("USERALE_EVENT_TYPE")

    # Redis
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://"

    # Amazon S3 Server
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "mp4", "mov", "m4a", "mp3"]
    IMG_EXTENSIONS = ["png", "jpg", "jpeg"]

    BUCKETS = {
        "audio": ["m4a", "mp3"],
        "videos": ["mp4", "mov"],
        "photos": ["png", "jpg", "jpeg", "gif"],
    }
    S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
    S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY")
    S3_BUCKET = os.environ.get("S3_BUCKET")
