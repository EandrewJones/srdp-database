"""OpenAPI v3 Specification"""

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from marshmallow import Schema, fields
from flask import url_for
from config import Config
from app import ma
from app.models import Follow, Likes, User, Comments, Reposts, Post


# Create an APISpec
spec = APISpec(
    title=Config.COVER_NAME,
    version="0.1.0",
    openapi_version="3.0.3",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
    info=dict(
        description=f"An API for social media data I/O on the {Config.COVER_NAME} platform.\
            \n\nWhen passing new data to the model, the order of creation must be `Users` >\
            (`Follows` | `Posts`) > (`Likes` | `Comments` | `Reposts`), where the pipe '|' \
            indicates order indifference at the step. Users must be token-authorized to \
            POST, PUT, or DELETE their own content. All paths are token protected except\
            for `User` creation.\
            \n\nAny model may be GET retrieved by any user so long as they are token-authorized.\
            User tokens change every 30 minutes and can be retrieved with curl:\
            \n\n\t\tcurl --user <username>:<password> -X POST http://<host_name>/api/tokens\
            \n\nor with HTTPie:\
            \n\n\t\thttp -a <username>:<password> POST http://<host_name>/api/tokens."
    ),
)

# security schema
http_basic_scheme = {"type": "http", "scheme": "basic"}
http_bearer_scheme = {"type": "http", "scheme": "bearer"}
spec.components.security_scheme("BasicAuth", http_basic_scheme)
spec.components.security_scheme("BearerAuth", http_bearer_scheme)

# Define Schemas
class FollowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "follows"
        model = Follow
        include_fk = True

    # Links
    _links = ma.Hyperlinks(
        {
            "follower": ma.URLFor("api.get_user", values=dict(id="<follower_id>")),
            "followed": ma.URLFor("api.get_user", values=dict(id="<followed_id>")),
        }
    )


class FollowInputSchema(Schema):
    # Required fields
    follower_id = fields.Int(description="Follower's id.", required=True)
    followed_id = fields.Int(description="Followed's id", required=True)

    # Optional fields
    created_at = fields.DateTime(description="Time of follow.")
    modified_at = fields.DateTime(description="Time of most recent modification.")


class LikesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "likes"
        model = Likes
        include_fk = True

    # Links
    _links = ma.Hyperlinks(
        {
            "user": ma.URLFor("api.get_user", values=dict(id="<user_id>")),
            "post": ma.URLFor("api.get_post", values=dict(id="<post_id>")),
        }
    )


class LikesInputSchema(Schema):
    # Required fields
    user_id = fields.Int(description="Liking user's id.", required=True)
    post_id = fields.Int(description="Liked post id.", required=True)

    # Optional Fields
    created_at = fields.DateTime(description="Time of like.")
    modified_at = fields.DateTime(description="Time of most recent modification.")


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "users"
        model = User
        include_fk = True
        fields = (
            "username",
            "name",
            "about_me",
            "email",
            "id",
            "last_seen",
            "created_at",
            "modified_at",
            "_links",
        )

    # Links
    _links = ma.Hyperlinks(
        {
            "self": ma.URLFor("api.get_user", values=dict(id="<id>")),
            "collection": ma.URLFor("api.get_users"),
            "posts": ma.URLFor("api.get_user_posts", values=dict(id="<id>")),
            "followers": ma.URLFor("api.get_followers", values=dict(id="<id>")),
            "followed": ma.URLFor("api.get_followed", values=dict(id="<id>")),
            "liked_posts": ma.URLFor("api.get_liked_posts", values=dict(id="<id>")),
            "followed_posts": ma.URLFor(
                "api.get_followed_posts", values=dict(id="<id>")
            ),
        }
    )


class UserInputSchema(Schema):
    # required fields
    username = fields.String(description="User's profile name.", required=True)
    email = fields.String(description="User's email.", required=True)
    password = fields.String(description="User's password.", required=True)
    name = fields.String(description="User's name.", required=True)

    # optional fields
    about_me = fields.String(description="User's short description.")
    last_seen = fields.DateTime(description="User's last log on time.")


class CommentsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "comments"
        model = Comments
        include_fk = True

    # Links
    _links = ma.Hyperlinks(
        {
            "parent": ma.URLFor("api.get_post", values=dict(id="<parent_id>")),
            "comment": ma.URLFor("api.get_post", values=dict(id="<comment_id>")),
        }
    )


class CommentsInputSchema(Schema):
    # Required fields
    parent_id = fields.Int(description="Parent post's id.", required=True)
    comment_id = fields.Int(description="Comment post's id.", required=True)

    # Optional fields
    created_at = fields.DateTime(description="Time of comment.")
    modified_at = fields.DateTime(description="Time of most recent modification.")


class RepostsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "reposts"
        model = Reposts
        include_fk = True

    # Links
    _links = ma.Hyperlinks(
        {
            "root": ma.URLFor("api.get_post", values=dict(id="<root_id>")),
            "repost": ma.URLFor("api.get_post", values=dict(id="<repost_id>")),
        }
    )


class RepostsInputSchema(Schema):
    # Required fields
    root_id = fields.Int(description="Root post's id.", required=True)
    repost_id = fields.Int(description="Repost post's id.", required=True)

    # Optional fields
    created_at = fields.DateTime(description="Time of repost.")
    modified_at = fields.DateTime(description="Time of most recent modification.")


class PostSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "posts"
        model = Post
        include_fk = True

    # Relationships
    author = ma.Nested(UserSchema)
    comments = ma.Nested(CommentsSchema(many=True))
    reposts = ma.Nested(RepostsSchema(many=True))

    # Links
    _links = ma.Hyperlinks(
        {
            "self": ma.URLFor("api.get_post", values=dict(id="<id>")),
            "collection": ma.URLFor("api.get_posts"),
        }
    )


class PostInputSchema(Schema):
    # Required inputs
    body = fields.String(description="Post body.", required=True)

    # Optional inputs
    id = fields.Int(description="Post id.")
    user_id = fields.Int(description="Author id.")
    created_at = fields.DateTime(description="Time posted.")
    modified_at = fields.DateTime(description="Time of most recent modification.")
    media_url = fields.URL(description="Link to s3-hosted media.")
    media_class = fields.String(description="Media 'bucket' in s3.")
    media_type = fields.String(
        description="Media type. One of ['audio', 'videos', 'photos']."
    )
    language = fields.String(description="Post language.")
    is_repost = fields.Boolean(description="Whether post is a repost.")
    is_comment = fields.Boolean(description="Whether post is a comment.")


# register schemas with spec
names = [
    "Follows",
    "FollowsInput",
    "Likes",
    "LikesInput",
    "User",
    "UserInput",
    "Comments",
    "CommentsInput",
    "Reposts",
    "RepostsInput",
    "Post",
    "PostInput",
]
schemas = [
    FollowSchema,
    FollowInputSchema,
    LikesSchema,
    LikesInputSchema,
    UserSchema,
    UserInputSchema,
    CommentsSchema,
    CommentsInputSchema,
    RepostsSchema,
    RepostsInputSchema,
    PostSchema,
    PostInputSchema,
]
for name, schema in zip(names, schemas):
    spec.components.schema(name, schema=schema)


# add swagger tags for endpoint annotation
tags = [
    {"name": name, "description": f"routes for {name} model I/O"}
    for name in names
    if not name.endswith("Input")
]
for tag in tags:
    print(f"Adding tag: {tag['name']}")
    spec.tag(tag)
