from flask import jsonify, request, url_for, abort
from app import db
from app.models import Follow, User
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import FollowSchema


@bp.route("/follows", methods=["GET"])
@token_auth.login_required
def get_follows():
    """
    ---
    get:
      summary: get follows
      description: retrieve all follows
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: FollowSchema
        '401':
          description: Not authenticated
      tags:
        - Follows
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Follow.to_collection_dict(
        Follow.query,
        page,
        per_page,
        FollowSchema,
        "api.get_follows",
    )
    return jsonify(data)


@bp.route("/follows", methods=["POST"])
@token_auth.login_required
def create_follows():
    """
    ---
    post:
      summary: Create a follow
      description: create new follows for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: FollowInputSchema
      responses:
        '201':
          description: call successful
          content:
            application/json:
              schema: FollowSchema
        '401':
          description: Not authenticated
      tags:
        - Follows
    """
    data = request.get_json() or {}
    if "followed_id" not in data:
        return bad_request("must include followed_id fields")
    if "follower_id" in data and token_auth.current_user().id != int(
        data["follower_id"]
    ):
        abort(403)
    if "follower_id" not in data:
        data["follower_id"] = token_auth.current_user().id
    if User.query.filter_by(id=data["followed_id"]).first() is None:
        return bad_request("User with followed_id does not exist")
    if (
        Follows.query.filter_by(follower_id=data["follower_id"])
        .filter_by(followed_id=data["followed_id"])
        .first()
        is not None
    ):
        return bad_request("Follow already exists")
    follow = Follow()
    follow.from_dict(data)
    db.session.add(follow)
    db.session.commit()
    response = jsonify(FollowSchema().dump(follow))
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_follows")
    return response


@bp.route("/follows", methods=["PUT"])
@token_auth.login_required
def update_follows():
    """
    ---
    put:
      summary: Modify a follow
      description: modify follows for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: FollowInputSchema
      responses:
        '200':
          description: resource updated successful
          content:
            application/json:
              schema: FollowSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Follows
    """
    data = request.get_json() or {}
    if "followed_id" not in data:
        return bad_request("must include followed_id fields")
    if "follower_id" in data and token_auth.current_user().id != int(
        data["follower_id"]
    ):
        abort(403)
    if "follower_id" not in data:
        data["follower_id"] = token_auth.current_user().id
    if User.query.filter_by(id=data["followed_id"]).first() is None:
        return bad_request("User with followed_id does not exist")
    follow = (
        Follow.query.filter_by(followed_id=data["followed_id"])
        .filter_by(follower_id=data["follower_id"])
        .first_or_404()
    )
    follow.from_dict(data)
    db.session.commit()
    response = jsonify(FollowSchema().dump(follow))
    response.status_code = 200
    return response


@bp.route("/follows/<int:followed_id>", methods=["DELETE"])
@token_auth.login_required
def delete_follows(followed_id):
    """
    ---
    delete:
      summary: Delete a follow
      description: delete follows for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: followed_id
          schema:
            type: integer
          required: true
          description: Numeric ID of the followed to be deleted
      responses:
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Follows
    """
    follow = (
        Follow.query.filter_by(followed_id=followed_id)
        .filter_by(follower_id=token_auth.current_user().id)
        .first_or_404()
    )
    db.session.delete(follow)
    db.session.commit()
    return "", 204
