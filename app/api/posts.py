from flask import jsonify, request, url_for, abort
from app import db
from app.models import Post
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import PostSchema, LikesSchema


@bp.route("/posts/<int:id>", methods=["GET"])
@token_auth.login_required
def get_post(id):
    """
    ---
    get:
      summary: Get single post
      description: retrieve a post by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the post to get
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: PostSchema
        '401':
          description: Not authenticated
      tags:
        - Post
    """
    post = Post.query.get_or_404(id)
    return PostSchema().dump(post)


@bp.route("/posts", methods=["GET"])
@token_auth.login_required
def get_posts():
    """
    ---
    get:
      summary: get posts
      description: retrieve all posts
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: PostSchema
        '401':
          description: Not authenticated
      tags:
        - Post
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    posts = Post.query
    data = Post.to_collection_dict(
        posts,
        page,
        per_page,
        PostSchema,
        "api.get_posts",
    )
    return jsonify(data)


@bp.route("/posts/<int:id>/comments", methods=["GET"])
@token_auth.login_required
def get_comments(id):
    """
    ---
    get:
      summary: Get post comments
      description: retrieve a post's comments by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the post to get comments for
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: PostSchema
        '401':
          description: Not authenticated
      tags:
        - Post
    """
    post = Post.query.get_or_404(id)
    comment_ids = [c.comment_id for c in post.comments]
    comments = Post.query.filter(Post.id.in_(comment_ids))
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Post.to_collection_dict(
        comments, page, per_page, PostSchema, "api.get_comments", id=id
    )
    return jsonify(data)


@bp.route("/posts/<int:id>/reposts", methods=["GET"])
@token_auth.login_required
def get_reposts(id):
    """
    ---
    get:
      summary: Get post's reposts
      description: retrieve a post's reposts by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the post to get reposts for
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: PostSchema
        '401':
          description: Not authenticated
      tags:
        - Post
    """
    post = Post.query.get_or_404(id)
    repost_ids = [r.repost_id for r in post.reposts]
    reposts = Post.query.filter(Post.id.in_(repost_ids))
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Post.to_collection_dict(
        reposts, page, per_page, PostSchema, "api.get_reposts", id=id
    )
    return jsonify(data)


@bp.route("/posts/<int:id>/likes", methods=["GET"])
@token_auth.login_required
def get_likes(id):
    """
    ---
    get:
      summary: Get post's likes
      description: retrieve a post's likes by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the post to get likes for
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: LikesSchema
        '401':
          description: Not authenticated
      tags:
        - Post
    """
    post = Post.query.get_or_404(id)
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Post.to_collection_dict(
        post.likes, page, per_page, LikesSchema, "api.get_likes", id=id
    )
    return jsonify(data)


@bp.route("/posts", methods=["POST"])
@token_auth.login_required
def create_post():
    """
    ---
    post:
      summary: Create a post
      description: create new posts for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: PostInputSchema
      responses:
        '201':
          description: call successful
          content:
            application/json:
              schema: PostSchema
        '401':
          description: Not authenticated
      tags:
        - Post
    """
    data = request.get_json() or {}
    if "body" not in data:
        return bad_request("must include body field")
    if "id" in data and Post.query.filter_by(id=data["id"]).first():
        return bad_request("post id already taken; please use a different id")
    if "user_id" in data and data["user_id"] != token_auth.current_user.id:
        return bad_request(
            "Authenticated user does not match user_id; please fix user_id field or remove from request"
        )
    # TODO: figure out how to upload to s3 if file included in post request
    post = Post(author=token_auth.current_user())  # post author always set to current
    post.from_dict(data)
    db.session.add(post)
    db.session.commit()
    response = jsonify(PostSchema().dump(post))
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_post", id=post.id)
    return response


@bp.route("/posts/<int:id>", methods=["PUT"])
@token_auth.login_required
def update_post(id):
    """
    ---
    put:
      summary: Modify a post
      description: modify posts for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the post to get likes for
      requestBody:
        required: true
        content:
          application/json:
            schema: PostInputSchema
      responses:
        '200':
          description: resource updated successful
          content:
            application/json:
              schema: PostSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Post
    """
    post = Post.query.get_or_404(id)
    if token_auth.current_user().id != post.user_id:
        abort(403)
    data = request.get_json() or {}
    if "id" in data:
        return bad_request("ID must only be specified in request url.")
    post.from_dict(data)
    db.session.commit()
    response = jsonify(PostSchema().dump(post))
    response.status_code = 200
    response.headers["Location"] = url_for("api.get_post", id=post.id)
    return response


@bp.route("/posts/<int:id>", methods=["DELETE"])
@token_auth.login_required
def delete_post(id):
    """
    ---
    delete:
      summary: Delete a post
      description: delete posts for authorized user
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
        - Post
    """
    post = Post.query.get_or_404(id)
    if token_auth.current_user().id != post.user_id:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return "", 204
