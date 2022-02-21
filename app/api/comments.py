from flask import jsonify, request, url_for, abort
from app import db
from app.models import Comments, Post
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import CommentsSchema


@bp.route("/comments", methods=["GET"])
@token_auth.login_required
def get_all_comments():
    """
    ---
    get:
      summary: get comments
      description: retrieve all comments
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: CommentsSchema
        '401':
          description: Not authenticated
      tags:
        - Comments
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Comments.to_collection_dict(
        Comments.query, page, per_page, CommentsSchema, "api.get_all_comments"
    )
    return jsonify(data)


@bp.route("/comments", methods=["POST"])
@token_auth.login_required
def create_comments():
    """
    ---
    post:
      summary: Create a comment
      description: create new comments for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: CommentsInputSchema
      responses:
        '201':
          description: call successful
          content:
            application/json:
              schema: CommentsSchema
        '401':
          description: Not authenticated
      tags:
        - Comments
    """
    data = request.get_json() or {}
    if "parent_id" not in data or "comment_id" not in data:
        return bad_request("must include parent_id and comment_id fields")
    if (
        Post.query.filter_by(id=data["parent_id"]).first is None
        or Post.query.filter_by(id=data["comment_id"]).first is None
    ):
        return bad_request(
            "Cannot create relationship. Parent and comment post must exist."
        )
    if (
        Comments()
        .query.filter_by(comment_id=data["comment_id"])
        .filter_by(parent_id=data["parent_id"])
        .first()
        is not None
    ):
        return bad_request("Comment already exists")
    comment_post = Post.query.filter_by(id=data["comment_id"]).first()
    if comment_post.author.id != token_auth.current_user().id:
        abort(403)

    # Change comment status
    comment_post.is_comment = True

    # Create link
    comment = Comments()
    comment.from_dict(data)
    db.session.add(comment)
    db.session.commit()

    # Create response
    response = jsonify(CommentsSchema().dump(comment))
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_all_comments")
    return response


@bp.route("/comments", methods=["PUT"])
@token_auth.login_required
def update_comments():
    """
    ---
    put:
      summary: Modify a comment
      description: modify comments for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: CommentsInputSchema
      responses:
        '200':
          description: resource updated successful
          content:
            application/json:
              schema: CommentsSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Comments
    """
    data = request.get_json() or {}
    if "parent_id" not in data or "comment_id" not in data:
        return bad_request("must include parent_id and comment_id fields")
    comment = (
        Comments.query.filter_by(parent_id=data["parent_id"])
        .filter_by(comment_id=data["comment_id"])
        .first_or_404()
    )
    comment_post = Post.query.filter_by(id=data["comment_id"]).first()
    if comment_post.author.id != token_auth.current_user().id:
        abort(403)
    comment.from_dict(data)
    db.session.commit()
    response = jsonify(CommentsSchema().dump(comment))
    response.status_code = 200
    return response


@bp.route("/comments/<int:parent_id>/<int:comment_id>", methods=["DELETE"])
@token_auth.login_required
def delete_comments(parent_id, comment_id):
    """
    ---
    delete:
      summary: Delete a comment
      description: delete comments for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: parent_id
          schema:
            type: integer
          required: true
          description: Numeric ID of the parent post
        - in: path
          name: comment_id
          schema:
            type: integer
          required: true
          description: Numeric ID of the comment post
      responses:
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Comments
    """
    comment = (
        Comments.query.filter_by(parent_id=parent_id)
        .filter_by(comment_id=comment_id)
        .first_or_404()
    )
    comment_post = Post.query.filter_by(id=comment_id).first()
    if comment_post.author.id != token_auth.current_user().id:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    return "", 204
