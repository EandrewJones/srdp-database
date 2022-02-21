from flask import jsonify, request, url_for, abort
from app import db
from app.models import Reposts, Post
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import RepostsSchema


@bp.route("/reposts", methods=["GET"])
@token_auth.login_required
def get_all_reposts():
    """
    ---
    get:
      summary: Get reposts
      description: retrieve all reposts
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: RepostsSchema
        '401':
          description: Not authenticated
      tags:
        - Reposts
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Reposts.to_collection_dict(
        Reposts.query, page, per_page, RepostsSchema, "api.get_all_reposts"
    )
    return jsonify(data)


@bp.route("/reposts", methods=["POST"])
@token_auth.login_required
def create_reposts():
    """
    ---
    post:
      summary: Create a repost
      description: create new reposts for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: RepostsInputSchema
      responses:
        '201':
          description: call successful
          content:
            application/json:
              schema: RepostsSchema
        '401':
          description: Not authenticated
      tags:
        - Reposts
    """
    data = request.get_json() or {}
    if "root_id" not in data or "repost_id" not in data:
        return bad_request("must include root_id and repost_id fields")
    if (
        Post.query.filter_by(id=data["root_id"]).first is None
        or Post.query.filter_by(id=data["repost_id"]).first is None
    ):
        return bad_request(
            "Cannot create relationship. Root and repost posts must exist."
        )
    if (
        Reposts.query.filter_by(root_id=data["root_id"])
        .filter_by(repost_id=data["repost_id"])
        .first()
        is not None
    ):
        return bad_request("Repost already exists")
    repost_post = Post.query.filter_by(id=data["repost_id"]).first()
    if repost_post.author.id != token_auth.current_user().id:
        abort(403)

    # Change repost status
    repost_post.is_repost = True

    # Create link
    repost = Reposts()
    repost.from_dict(data)
    db.session.add(repost)
    db.session.commit()

    # Create response
    response = jsonify(RepostsSchema().dump(repoost))
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_all_reposts")
    return response


@bp.route("/reposts", methods=["PUT"])
@token_auth.login_required
def update_reposts():
    """
    ---
    put:
      summary: Modify a repost
      description: modify repost for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: RepostsInputSchema
      responses:
        '200':
          description: resource updated successful
          content:
            application/json:
              schema: RepostsSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Reposts
    """
    data = request.get_json() or {}
    if "root_id" not in data or "repost_id" not in data:
        return bad_request("must include root_id and repost_id fields")
    repost = (
        Reposts.query.filter_by(root_id=data["root_id"])
        .filter_by(repost_id=data["repost_id"])
        .first_or_404()
    )
    repost_post = Post.query.filter_by(id=data["repost_id"]).first()
    if repost_post.author.id != token_auth.current_user().id:
        abort(403)
    repost.from_dict(data)
    db.session.commit()
    response = jsonify(RepostsSchema().dump(repost))
    response.status_code = 200
    return response


@bp.route("/reposts/<int:root_id>/<int:repost_id>", methods=["DELETE"])
@token_auth.login_required
def delete_reposts(root_id, repost_id):
    """
    ---
    delete:
      summary: Delete a repost
      description: delete reposts for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: root_id
          schema:
            type: integer
          required: true
          description: Numeric ID of the root post
        - in: path
          name: repost_id
          schema:
            type: integer
          required: true
          description: Numeric ID of the repost post
      responses:
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Reposts
    """

    repost = (
        Reposts.query.filter_by(root_id=root_id)
        .filter_by(repost_id=repost_id)
        .first_or_404()
    )
    repost_post = Post.query.filter_by(id=repost_id).first()
    if repost_post.author.id != token_auth.current_user().id:
        abort(403)
    db.session.delete(repost)
    db.session.commit()
    return "", 204
