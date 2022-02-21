from flask import jsonify, request, url_for, abort
from app import db
from app.models import Likes, Post
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import LikesSchema


@bp.route("/likes", methods=["GET"])
@token_auth.login_required
def get_all_likes():
    """
    ---
    get:
      summary: get likes
      description: retrieve all likes
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: LikesSchema
        '401':
          description: Not authenticated
      tags:
        - Likes
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Likes.to_collection_dict(
        Likes.query, page, per_page, LikesSchema, "api.get_all_likes"
    )
    return jsonify(data)


@bp.route("/likes", methods=["POST"])
@token_auth.login_required
def create_likes():
    """
    ---
    post:
      summary: Create a like
      description: create new likes for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: LikesInputSchema
      responses:
        '201':
          description: call successful
          content:
            application/json:
              schema: LikesSchema
        '401':
          description: Not authenticated
      tags:
        - Likes
    """
    data = request.get_json() or {}
    if "post_id" not in data:
        return bad_request("must include post_id fields")
    if "user_id" in data and token_auth.current_user().id != int(data["user_id"]):
        abort(403)
    if "user_id" not in data:
        data["user_id"] = token_auth.current_user().id
    if Post.query.filter_by(id=data["post_id"]).first() is None:
        return bad_request("Post with post_id does not exist")
    if (
        Post.query.filter_by(id=data["post_id"]).first().author.id
        == token_auth.current_user().id
    ):
        return bad_request("User cannot like their own post")
    if (
        Likes.query.filter_by(user_id=data["user_id"])
        .filter_by(post_id=data["post_id"])
        .first()
        is not None
    ):
        return bad_request("Like already exists")
    like = Likes()
    like.from_dict(data)
    db.session.add(like)
    db.session.commit()
    response = jsonify(LikesSchema().dump(like))
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_all_likes")
    return response


@bp.route("/likes", methods=["PUT"])
@token_auth.login_required
def update_likes():
    """
    ---
    put:
      summary: Modify a like
      description: modify likes for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: LikesInputSchema
      responses:
        '200':
          description: resource updated successful
          content:
            application/json:
              schema: LikesSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Likes
    """
    data = request.get_json() or {}
    if "post_id" not in data:
        return bad_request("must include post_id fields")
    if "user_id" in data and token_auth.current_user().id != int(data["user_id"]):
        abort(403)
    if "user_id" not in data:
        data["user_id"] = token_auth.current_user().id
    if Post.query.filter_by(id=data["post_id"]).first() is None:
        return bad_request("Post with post_id does not exist")
    like = (
        Likes.query.filter_by(post_id=data["post_id"])
        .filter_by(user_id=data["user_id"])
        .first_or_404()
    )
    like.from_dict(data)
    db.session.commit()
    response = jsonify(LikesSchema().dump(like))
    response.status_code = 200
    return response


@bp.route("/likes/<int:post_id>", methods=["DELETE"])
@token_auth.login_required
def delete_likes(post_id):
    """
    ---
    delete:
      summary: Delete a like
      description: delete likes for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: post_id
          schema:
            type: integer
          required: true
          description: Numeric ID of the like to be deleted
      responses:
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Likes
    """
    like = (
        Likes.query.filter_by(post_id=post_id)
        .filter_by(user_id=token_auth.current_user().id)
        .first_or_404()
    )
    db.session.delete(like)
    db.session.commit()
    return "", 204
