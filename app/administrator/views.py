from flask import url_for, redirect, request, current_app
from flask_admin import AdminIndexView, expose
from flask_login import current_user
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.fileadmin.s3 import S3FileAdmin
from app.models import User, Follow, Likes, Post, Reposts, Comments
from app import db, admin
from config import Config
import os.path as op


# Restricted Views
class RestrictedModelView(ModelView):
    """Restricted Model Views in Admin Panel."""

    page_size = 50
    create_model = True
    edit_modal = True

    def is_accessible(self):
        return current_user.is_admin and current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login", next=request.url))


class RestrictedAdminView(AdminIndexView):
    """Restricted Admin Panel."""

    @expose("/")
    def index(self):
        return self.render(
            "admin/index.html",
            title=f"Admin Panel - {current_app.config['COVER_NAME']}",
        )

    def is_accessible(self):
        return current_user.is_admin and current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login", next=request.url))


# Model Views
class PostView(RestrictedModelView):
    column_list = (
        "id",
        "created_at",
        "modified_at",
        "body",
        "media_url",
        "media_class",
        "media_type",
        "language",
        "is_repost",
        "is_comment",
        "author.username",
    )
    column_searchable_list = ("id", "author.username", "body")
    column_sortable_list = column_list
    column_filters = column_list


class RepostsView(RestrictedModelView):
    column_list = (
        "created_at",
        "modified_at",
        "root.id",
        "root.body",
        "repost.id",
        "repost.body",
    )
    column_searchable_list = ("root.id", "repost.id", "root.body", "repost.body")
    column_sortable_list = column_list
    column_filters = column_list


class CommentsView(RestrictedModelView):
    column_list = (
        "created_at",
        "modified_at",
        "parent.id",
        "parent.body",
        "comment.id",
        "comment.body",
    )
    column_searchable_list = ("parent.id", "comment.id", "parent.body", "comment.body")
    column_sortable_list = column_list
    column_filters = column_list


class UserView(RestrictedModelView):
    column_list = (
        "id",
        "created_at",
        "modified_at",
        "username",
        "name",
        "email",
        "about_me",
        "last_seen",
        "is_admin",
    )
    column_searchable_list = ("id", "username", "name", "email", "about_me")
    column_sortable_list = column_list
    column_filters = column_list


class FollowView(RestrictedModelView):
    column_list = (
        "created_at",
        "modified_at",
        "follower.id",
        "follower.username",
        "follower.name",
        "followed.id",
        "followed.username",
        "followed.name",
    )
    column_searchable_list = (
        "follower.id",
        "follower.username",
        "follower.name",
        "followed.id",
        "followed.username",
        "followed.name",
    )
    column_sortable_list = column_list
    column_filters = column_list


class LikesView(RestrictedModelView):
    column_list = (
        "created_at",
        "modified_at",
        "user.id",
        "user.username",
        "user.name",
        "post.id",
        "post.body",
    )
    column_searchable_list = (
        "user.id",
        "user.username",
        "user.name",
        "post.id",
        "post.body",
    )
    column_sortable_list = column_list
    column_filters = column_list


# File Views
class RestrictedFileAdmin(FileAdmin):
    def is_accessible(self):
        return current_user.is_admin and current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login", next=request.url))


class RestrictedS3FileAdmin(S3FileAdmin):
    def is_accessible(self):
        return current_user.is_admin and current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login", next=request.url))


# Add admin model views
admin.add_view(LikesView(Likes, db.session, endpoint="likes", category="Users"))
admin.add_view(FollowView(Follow, db.session, category="Users"))
admin.add_view(UserView(User, db.session, category="Users"))
admin.add_view(CommentsView(Comments, db.session, category="Posts"))
admin.add_view(PostView(Post, db.session, category="Posts"))
admin.add_view(RepostsView(Reposts, db.session, category="Posts"))


# Add admin file views
path = op.abspath(op.join(op.dirname(__file__), "..", "static"))
admin.add_view(
    RestrictedFileAdmin(
        path, "/static/", name="Static Files", category="File Management"
    )
)
admin.add_view(
    RestrictedS3FileAdmin(
        Config.S3_BUCKET,
        "us-east-1",
        Config.S3_ACCESS_KEY,
        Config.S3_SECRET_ACCESS_KEY,
        name="S3 Bucket",
        category="File Management",
    )
)
