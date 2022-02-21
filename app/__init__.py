import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_admin import Admin
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from flask_cors import CORS
from elasticsearch import Elasticsearch
from redis import Redis
from micawber.providers import bootstrap_basic
from micawber.contrib.mcflask import add_oembed_filters
import rq
import json
import boto3
from config import Config

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = _l("Please log in to access this page.")
admin = Admin(template_mode="bootstrap4", name=Config.COVER_NAME)
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()
cors = CORS()
oembed_providers = bootstrap_basic()


def create_app(config_class=Config):
    # Instantiate app
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Set up extensions
    from app.administrator.views import RestrictedAdminView

    admin.init_app(app, index_view=RestrictedAdminView(), endpoint="admin")
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    cors.init_app(app)
    app.elasticsearch = (
        Elasticsearch([app.config["ES_URL"]]) if app.config["ES_URL"] else None
    )
    if app.elasticsearch:
        with open("search/config/index_template.json") as f:
            index_template = json.load(f)
        app.elasticsearch.indices.put_template(name="search", body=index_template)
    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue("cssms-tasks", connection=app.redis)
    app.s3 = boto3.client(
        "s3",
        aws_access_key_id=app.config["S3_ACCESS_KEY"],
        aws_secret_access_key=app.config["S3_SECRET_ACCESS_KEY"],
    )
    add_oembed_filters(app, oembed_providers)

    # Register Blueprints
    from app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    from app.api import swagger_ui_blueprint as swagger_bp
    from app.api import SWAGGER_URL

    app.register_blueprint(swagger_bp, url_prefix=SWAGGER_URL)

    from app.template_filters import bp as filter_bp

    app.register_blueprint(filter_bp)

    from app.administrator import bp as admin_bp

    app.register_blueprint(admin_bp)

    # Set up mail server and logging
    if not app.debug and not app.testing:
        if app.config["MAIL_SERVER"]:
            auth = None
            if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr="no-reply@" + app.config["MAIL_SERVER"],
                toaddrs=app.config["ADMINS"],
                subject="CogSec Social Media Simulator Failure",
                credentials=auth,
                secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if app.config["LOG_TO_STDOUT"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists("logs"):
                os.mkdir("logs")
            file_handler = RotatingFileHandler(
                "logs/cssms.log", maxBytes=10240, backupCount=10
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s "
                    "[in %(pathname)s:%(lineno)d]"
                )
            )
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("CogSec SMS startup")

    return app


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config["LANGUAGES"])


from app import models
