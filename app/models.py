from datetime import datetime, timedelta
from dateutil import parser
from hashlib import md5
from time import time
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import DeclarativeMeta
from operator import itemgetter
import jwt
import redis
import rq
import json
import os
import base64
from app import db, login
from app.search import add_to_index, remove_from_index, query_index


class AuditMixin(object):
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), index=True)
    modified_at = db.Column(
        db.DateTime(timezone=True), default=func.now(), onupdate=func.now(), index=True
    )

class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, schema, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        result = schema(many=True).dump(resources.items)
        data = {
            schema.Meta.type_: result,
            "_meta": {
                "page": page,
                "per_page": per_page,
                "total_pages": resources.pages,
                "total_items": resources.total,
            },
            "_links": {
                "self": url_for(endpoint, page=page, per_page=per_page, **kwargs),
                "next": url_for(endpoint, page=page + 1, per_page=per_page, **kwargs)
                if resources.has_next
                else None,
                "prev": url_for(endpoint, page=page - 1, per_page=per_page, **kwargs)
                if resources.has_prev
                else None,
            },
        }
        return data


class Follow(AuditMixin, PaginatedAPIMixin, db.Model):
    __tablename__ = "follows"

    follower_id = db.Column(
        "follower_id", db.Integer, db.ForeignKey("user.id"), primary_key=True
    )
    followed_id = db.Column(
        "followed_id", db.Integer, db.ForeignKey("user.id"), primary_key=True
    )

    def __repr__(self):
        return "<User {} -follows-> User {}>".format(self.follower_id, self.followed_id)

    def from_dict(self, data):
        for field in ["follower_id", "followed_id"]:
            if field in data:
                setattr(self, field, data[field])
        for field in ["created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.now())

    def to_dict(self):
        data = {
            "follower_id": self.follower_id,
            "follower": self.follower,
            "followed_id": self.followed_id,
            "followed": self.followed,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }
        return data


class Likes(AuditMixin, PaginatedAPIMixin, db.Model):
    __tablename__ = "likes"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)

    def __repr__(self):
        return "<User {} -likes-> Post {}>".format(self.user_id, self.post_id)

    def from_dict(self, data):
        for field in ["user_id", "post_id"]:
            if field in data:
                setattr(self, field, data[field])
        for field in ["created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.now())

    def to_dict(self):
        data = {
            "user_id": self.user_id,
            "user": self.user,
            "post_id": self.post_id,
            "post": self.post,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }
        return data


class User(UserMixin, SearchableMixin, PaginatedAPIMixin, AuditMixin, db.Model):
    __searchable__ = ["username", "about_me", "name"]

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    name = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.email and self.email in current_app.config["ADMINS"]:
            self.is_admin = True

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        ).decode("utf-8")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except:
            return
        return User.query.get(id)

    def from_dict(self, data, new_user=False):
        if "id" in data:
            setattr(self, "id", data["id"])
        for field in ["username", "name", "email", "about_me"]:
            if field in data:
                setattr(self, field, data[field])
        for field in ["last_seen", "created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.now())
        if new_user:
            if "password" in data:
                self.set_password(data["password"])
            if "email" in data and data["email"] in current_app.config["ADMINS"]:
                setattr(self, "is_admin", True)

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode("utf-8")
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.username = "Guest"

    def is_admin(self):
        return False

    def __repr__(self):
        return "<anonymous user>"


login.anonymous_user = Anonymous


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Comments(AuditMixin, PaginatedAPIMixin, db.Model):
    __tablename__ = "comments"
    parent_id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)

    def __repr__(self):
        return "<Post {} is a comment on Post {}".format(
            self.comment_id, self.parent_id
        )

    def from_dict(self, data):
        for field in ["parent_id", "comment_id"]:
            if field in data:
                setattr(self, field, data[field])
        for field in ["created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.now())

    def to_dict(self):
        data = {
            "parent_id": self.parent_id,
            "comment_id": self.comment_id,
            "comment": self.comment,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }
        return data


class Reposts(AuditMixin, PaginatedAPIMixin, db.Model):
    __tablename__ = "reposts"
    root_id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)
    repost_id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)

    def __repr__(self):
        return "<Post {} reposts Post {}".format(self.repost_id, self.root_id)

    def from_dict(self, data):
        for field in ["root_id", "repost_id"]:
            if field in data:
                setattr(self, field, data[field])
        for field in ["created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.now())

    def to_dict(self):
        data = {
            "root_id": self.root_id,
            "root": self.root,
            "repost_id": self.repost_id,
            "repost": self.repost,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }
        return data


class Post(SearchableMixin, AuditMixin, PaginatedAPIMixin, db.Model):
    __searchable__ = ["body"]

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    media_url = db.Column(db.String(1000), nullable=True)
    media_class = db.Column(db.String(6), nullable=True)
    media_type = db.Column(db.String(30), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    language = db.Column(db.String(5))
    is_comment = db.Column(db.Boolean, default=False)
    is_repost = db.Column(db.Boolean, default=False)
    likes = db.relationship(
        "Likes",
        foreign_keys=[Likes.post_id],
        backref=db.backref("post", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    comments = db.relationship(
        "Comments",
        foreign_keys=[Comments.parent_id],
        backref=db.backref("parent", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    parent = db.relationship(
        "Comments",
        foreign_keys=[Comments.comment_id],
        backref=db.backref("comment", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    reposts = db.relationship(
        "Reposts",
        foreign_keys=[Reposts.root_id],
        backref=db.backref("root", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    root = db.relationship(
        "Reposts",
        foreign_keys=[Reposts.repost_id],
        backref=db.backref("repost", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return "<Post {}>".format(self.body)

    def comment_on_post(self, comment):
        # comment must be a Post instance
        c = Comments(parent=self, comment=comment)
        db.session.add(c)

    def has_comments(self):
        return self.comments.count() > 0

    def repost_post(self, repost):
        # repost must be a Post instance
        r = Reposts(root=self, repost=repost)
        db.session.add(r)

    def has_root(self):
        return self.root.count() > 0

    def from_dict(self, data):
        if "id" in data:
            setattr(self, "id", data["id"])
        for field in [
            "body",
            "media_url",
            "media_class",
            "media_type",
            "language",
            "is_comment",
            "is_repost",
        ]:
            if field in data:
                setattr(self, field, data[field])
        for field in ["created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.now())
