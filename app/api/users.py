from flask import jsonify, request, url_for, abort
from app import db
from app.models import User
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import UserSchema


@bp.route("/users/<int:id>", methods=["GET"])
@token_auth.login_required
def get_user(id):
    """
    ---
    get:
      summary: Get single user
      description: retrieve a user by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the user to get
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: UserSchema
        '401':
          description: Not authenticated
      tags:
        - User
    """
    if token_auth.current_user().id == id or token_auth.current_user().is_admin:
        user = User.query.get_or_404(id)
        return UserSchema().dump(user)
    else:
        return bad_request("Only admins can view users.")


@bp.route("/users", methods=["GET"])
@token_auth.login_required
def get_users():
    """
    ---
    get:
      summary: Get users
      description: retrieve all users
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: UserSchema
        '401':
          description: Not authenticated
      tags:
        - User
    """
    if not token_auth.current_user().is_admin:
        return bad_request("Only admins can view users.")
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    users = User.query
    data = User.to_collection_dict(users, page, per_page, UserSchema, "api.get_users")
    return jsonify(data)


@bp.route("/users", methods=["POST"])
def create_user():
    """
    ---
    post:
      summary: Create a user
      description: create new users
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: UserInputSchema
      responses:
        '201':
          description: call successful
          content:
            application/json:
              schema: UserSchema
        '401':
          description: Not authenticated
      tags:
        - User
    """
    # if not token_auth.current_user.is_admin:
    #     return bad_request(
    #         "Only admins can create new users. Please authenticate as admin."
    #     )
    data = request.get_json() or {}
    if (
        "username" not in data
        or "email" not in data
        or "password" not in data
        or "name" not in data
    ):
        return bad_request("must include username, name, email and password fields")
    if User.query.filter_by(username=data["username"]).first():
        return bad_request("please use a different username")
    if User.query.filter_by(email=data["email"]).first():
        return bad_request("please use a different email address")
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(UserSchema().dump(user))
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_user", id=user.id)
    return response


@bp.route("/users/<int:id>", methods=["PUT"])
@token_auth.login_required
def update_user(id):
    """
    ---
    put:
      summary: Modify a user
      description: modify user info for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the user to be modified.
      requestBody:
        required: true
        content:
          application/json:
            schema: UserInputSchema
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: UserSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - User
    """
    # TODO: allow admins to put
    if token_auth.current_user().id == id or token_auth.current_user().is_admin:
        user = User.query.get_or_404(id)
        data = request.get_json() or {}
        if (
            "username" in data
            and data["username"] != user.username
            and User.query.filter_by(username=data["username"]).first()
        ):
            return bad_request("please use a different username")
        if (
            "email" in data
            and data["email"] != user.email
            and User.query.filter_by(email=data["email"]).first()
        ):
            return bad_request("please use a different email address")
        user.from_dict(data, new_user=False)
        db.session.commit()
        response = jsonify(UserSchema().dump(user))
        response.status_code = 200
        response.headers["Location"] = url_for("api.get_user", id=user.id)
        return response
    else:
        abort(403)


@bp.route("/users/<int:id>", methods=["DELETE"])
@token_auth.login_required
def delete_user(id):
    """
    ---
    delete:
      summary: Delete a user
      description: delete user for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the post to be deleted
      responses:
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - User
    """
    if token_auth.current_user().id == id or token_auth.current_user().is_admin:
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        return "", 204
    else:
        abort(403)
