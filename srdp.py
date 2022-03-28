from flask import jsonify
from app import create_app, db
from app.models import User, Groups, NonviolentTactics, ViolentTactics, Organizations
from app.api_spec import spec


app = create_app()


with app.test_request_context():
    # register all swagger documented functions here
    for fn_name in app.view_functions:
        if not fn_name.startswith("api."):
            continue
        print(f"Loading swagger docs for function: {fn_name}")
        view_fn = app.view_functions[fn_name]
        spec.path(view=view_fn)


@app.route("/api/swagger.json")
def create_swagger_json():
    return jsonify(spec.to_dict())


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Groups": Groups,
        "NonviolentTactics": NonviolentTactics,
        "ViolentTactics": ViolentTactics,
        "Organizations": Organizations,
    }
