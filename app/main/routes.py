from flask import redirect, url_for
from app.main import bp


@bp.route("/", methods=["GET"])
@bp.route("/index", methods=["GET"])
def index():
    return redirect("/api/docs")
