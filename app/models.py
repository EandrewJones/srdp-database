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


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return (
            cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)),
            total,
        )

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            "add": list(session.new),
            "update": list(session.dirty),
            "delete": list(session.deleted),
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes["add"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes["update"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes["delete"]:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    # helper method to refresh an index with all the data from the relational side
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, "before_commit", SearchableMixin.before_commit)
db.event.listen(db.session, "after_commit", SearchableMixin.after_commit)


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
    profile_pic = db.Column(db.String(1000), nullable=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship("Post", backref="author", lazy="dynamic")
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)
    liked_posts = db.relationship(
        "Likes",
        foreign_keys=[Likes.user_id],
        backref=db.backref("user", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    followed = db.relationship(
        "Follow",
        foreign_keys=[Follow.follower_id],
        backref=db.backref("follower", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    followers = db.relationship(
        "Follow",
        foreign_keys=[Follow.followed_id],
        backref=db.backref("followed", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    messages_sent = db.relationship(
        "Message", foreign_keys="Message.sender_id", backref="author", lazy="dynamic"
    )
    messages_received = db.relationship(
        "Message",
        foreign_keys="Message.recipient_id",
        backref="recipient",
        lazy="dynamic",
    )
    last_message_read_time = db.Column(db.DateTime)
    last_updates_read_time = db.Column(db.DateTime)
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")
    tasks = db.relationship("Task", backref="user", lazy="dynamic")

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.follow(self)
        if self.email and self.email in current_app.config["ADMINS"]:
            self.is_admin = True

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
            digest, size
        )

    def like_post(self, post):
        if not self.has_liked(post):
            l = Likes(user=self, post=post)
            db.session.add(l)

    def unlike_post(self, post):
        l = self.liked_posts.filter_by(post_id=post.id).first()
        if l:
            db.session.delete(l)

    def has_liked(self, post):
        if post.id is None:
            return None
        return self.liked_posts.filter_by(post_id=post.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.user_id).filter(
            Follow.follower_id == self.id
        )

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

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return (
            Message.query.filter_by(recipient=self)
            .filter(Message.timestamp > last_read_time)
            .count()
        )

    def new_comments(self):
        last_updates_read_time = self.last_updates_read_time or datetime(1900, 1, 1)
        user_post_ids = [post.id for post in Post.query.filter_by(author=self).all()]
        return Comments.query.filter(Comments.parent_id.in_(user_post_ids)).filter(
            Comments.modified_at > last_updates_read_time
        )

    def new_likes(self):
        last_updates_read_time = self.last_updates_read_time or datetime(1900, 1, 1)
        user_post_ids = [post.id for post in Post.query.filter_by(author=self).all()]
        return (
            Likes.query.filter(Likes.post_id.in_(user_post_ids))
            .filter(Likes.modified_at > last_updates_read_time)
            .filter(Likes.user_id != self.id)
        )

    def new_reposts(self):
        last_updates_read_time = self.last_updates_read_time or datetime(1900, 1, 1)
        user_post_ids = [post.id for post in Post.query.filter_by(author=self).all()]
        return Reposts.query.filter(Reposts.root_id.in_(user_post_ids)).filter(
            Reposts.modified_at > last_updates_read_time
        )

    def new_follows(self):
        last_updates_read_time = self.last_updates_read_time or datetime(1900, 1, 1)
        return (
            Follow.query.filter_by(followed=self)
            .filter(Follow.modified_at > last_updates_read_time)
            .filter(Follow.follower_id != self.id)
        )

    def updates(self, offset=0, per_page=25):
        # Convert new updates to list of dictionaries
        new_follows = [nf.to_dict() for nf in self.new_follows()]
        new_follows = [{**item, "type": "follow"} for item in new_follows]
        new_likes = [nl.to_dict() for nl in self.new_likes()]
        new_likes = [{**item, "type": "like"} for item in new_likes]
        new_comments = [nc.to_dict() for nc in self.new_comments()]
        new_comments = [{**item, "type": "comment"} for item in new_comments]
        new_reposts = [nr.to_dict() for nr in self.new_reposts()]
        new_reposts = [{**item, "type": "repost"} for item in new_reposts]

        # Concatenate lists and sort
        updates = new_follows + new_likes + new_comments + new_reposts
        sorted_updates = sorted(updates, key=itemgetter("created_at"), reverse=True)
        total = len(sorted_updates)
        return sorted_updates[offset : offset + per_page], total

    def updates_count(self):
        return (
            self.new_follows().count()
            + self.new_likes().count()
            + self.new_comments().count()
            + self.new_reposts().count()
        )

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue(
            "app.tasks." + name, self.id, *args, **kwargs
        )
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self, complete=False).first()

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


class Message(db.Model, PaginatedAPIMixin):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return "<Message {}>".format(self.body)


class Notification(db.Model, PaginatedAPIMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get("progress", 0) if job is not None else 100
