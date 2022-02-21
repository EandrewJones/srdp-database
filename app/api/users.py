from flask import jsonify, request, url_for, abort
from app import db
from app.models import User, Post
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import UserSchema, PostSchema


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
    user = User.query.get_or_404(id)
    return UserSchema().dump(user)


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
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    users = User.query
    data = User.to_collection_dict(users, page, per_page, UserSchema, "api.get_users")
    return jsonify(data)


@bp.route("/users/<int:id>/followers", methods=["GET"])
@token_auth.login_required
def get_followers(id):
    """
    ---
    get:
      summary: Get a user's followers
      description: retrieve a user's followers by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the user to get followers for
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
    user = User.query.get_or_404(id)
    follower_ids = [f.follower_id for f in user.followers]
    followers = User.query.filter(User.id.in_(follower_ids))
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = User.to_collection_dict(
        followers, page, per_page, UserSchema, "api.get_followers", id=id
    )
    return jsonify(data)


@bp.route("/users/<int:id>/followed", methods=["GET"])
@token_auth.login_required
def get_followed(id):
    """
    ---
    get:
      summary: Get users a user follows
      description: retrieve users a user has followed by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the user to retrieve their followed users
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
    user = User.query.get_or_404(id)
    followed_ids = [f.followed_id for f in user.followed]
    followed = User.query.filter(User.id.in_(followed_ids))
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = User.to_collection_dict(
        followed, page, per_page, UserSchema, "api.get_followed", id=id
    )
    return jsonify(data)


@bp.route("/users/<int:id>/posts", methods=["GET"])
@bp.route("/users/<int:id>/posts/<string:order>", methods=["GET"])
@token_auth.login_required
def get_user_posts(id, order="oldest"):
    """
    ---
    get:
      summary: Get a user's posts
      description: retrieve all posts of a user by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the user whose posts will be retrieved
        - in: path
          name: order
          schema:
            type: string
            default: oldest
          required: false
          description: Chronological sorting of posts. Must be either "newest" (newest-oldest) or "oldest" (oldest-newest).
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: PostSchema
        '401':
          description: Not authenticated
      tags:
        - User
    """
    user = User.query.get_or_404(id)
    posts = user.posts
    if order == "newest":
        posts = user.posts.order_by(Post.created_at.desc())
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = User.to_collection_dict(
        posts, page, per_page, PostSchema, "api.get_user_posts", id=id
    )
    return jsonify(data)


@bp.route("/users/<int:id>/liked_posts", methods=["GET"])
@bp.route("/users/<int:id>/liked_posts/<string:order>", methods=["GET"])
@token_auth.login_required
def get_liked_posts(id, order="oldest"):
    """
    ---
    get:
      summary: Get user's liked posts
      description: retrieve all post liked by a user by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the user whose liked posts will be retrieved.
        - in: path
          name: order
          schema:
            type: string
            default: oldest
          required: false
          description: Chronological sorting of posts. Must be either "newest" (newest-oldest) or "oldest" (oldest-newest).
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: PostSchema
        '401':
          description: Not authenticated
      tags:
        - User
    """
    user = User.query.get_or_404(id)
    post_ids = [p.post_id for p in user.liked_posts]
    liked_posts = Post.query.filter(Post.id.in_(post_ids))
    if order == "newest":
        liked_posts = liked_posts.order_by(Post.created_at.desc())
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = User.to_collection_dict(
        liked_posts, page, per_page, PostSchema, "api.get_liked_posts", id=id
    )
    return jsonify(data)


@bp.route("/users/<int:id>/followed_posts", methods=["GET"])
@bp.route("/users/<int:id>/followed_posts/<string:order>", methods=["GET"])
@token_auth.login_required
def get_followed_posts(id, order="oldest"):
    """
    ---
    get:
      summary: Get followed users' posts for given user
      description: retrieve follower users' posts for given user by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric ID of the user whose followed users' posts will be retrieved.
        - in: path
          name: order
          schema:
            type: string
            default: oldest
          required: false
          description: Chronological sorting of posts. Must be either "newest" (newest-oldest) or "oldest" (oldest-newest).
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: PostSchema
        '401':
          description: Not authenticated
      tags:
        - User
    """
    if order not in ["oldest", "newest"]:
        return bad_request("order must be oldest or newest")
    user = User.query.get_or_404(id)
    followed_posts = user.followed_posts
    if order == "newest":
        followed_posts = followed_posts.order_by(Post.created_at.desc())
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = User.to_collection_dict(
        followed_posts, page, per_page, PostSchema, "api.get_followed_posts", id=id
    )
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
              schema: PostSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - User
    """
    if token_auth.current_user().id != id:
        abort(403)
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
    if token_auth.current_user().id != id:
        abort(403)
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return "", 204
