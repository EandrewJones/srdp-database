from datetime import datetime, timedelta
from dateutil import parser
from hashlib import md5
from time import time
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func

# from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.dialects.mysql import TINYINT
from operator import itemgetter
import jwt
import json
import os
import base64
from app import db, login


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


class ViolentTactics(db.Model, AuditMixin, PaginatedAPIMixin):
    __tablename__ = "violence"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    facId = db.Column(
        "facId",
        db.Integer,
        db.ForeignKey("organizations.facId"),
        index=True,
    )
    year = db.Column(db.Integer)
    againstState = db.Column(db.Integer, nullable=False, default=0)
    againstStateFatal = db.Column(db.Integer, nullable=False, default=0)
    againstOrg = db.Column(db.Integer, nullable=False, default=0)
    againstOrgFatal = db.Column(db.Integer, nullable=False, default=0)
    againstIngroup = db.Column(db.Integer, nullable=False, default=0)
    againstIngroupFatal = db.Column(db.Integer, nullable=False, default=0)
    againstOutgroup = db.Column(db.Integer, nullable=False, default=0)
    againstOutgroupFatal = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Violent Tactics - org: {self.organization}, facId: {self.facId}, year: {self.year}>"

    def from_dict(self, data):
        for field in [
            "facId",
            "year",
            "againstState",
            "againstStateFatal",
            "againstOrg",
            "againstOrgFatal",
            "againstIngroup",
            "againstIngroupFatal",
            "againstOutgroup",
            "againstOutgroupFatal",
        ]:
            if field in data and field is not None:
                setattr(self, field, data[field])
        for field in ["created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.now())


class NonviolentTactics(db.Model, AuditMixin, PaginatedAPIMixin):
    __tablename__ = "nonviolence"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    facId = db.Column(
        "facId", db.Integer, db.ForeignKey("organizations.facId"), index=True
    )
    year = db.Column(db.Integer)
    economicNoncooperation = db.Column(db.Integer, nullable=False, default=0)
    protestDemonstration = db.Column(db.Integer, nullable=False, default=0)
    nonviolentIntervention = db.Column(db.Integer, nullable=False, default=0)
    socialNoncooperation = db.Column(db.Integer, nullable=False, default=0)
    institutionalAction = db.Column(db.Integer, nullable=False, default=0)
    politicalNoncooperation = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Nonviolent Tactics - org: {self.organization}, facId: {self.facId}, year: {self.year}>"

    def from_dict(self, data):
        for field in [
            "facId",
            "year",
            "economicNoncooperation",
            "protestDemonstration",
            "nonviolentIntervention",
            "socialNoncooperation",
            "institutionalAction",
            "politicalNoncooperation",
        ]:
            if field in data and field is not None:
                setattr(self, field, data[field])
        for field in ["created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.now())


class Groups(db.Model, AuditMixin, PaginatedAPIMixin):
    __tablename__ = "groups"

    kgcId = db.Column(db.Integer, primary_key=True)
    groupName = db.Column(db.String(255), index=True, nullable=False)
    country = db.Column(db.String(255), nullable=False)
    organizations = db.relationship("Organizations", backref="Group", lazy="dynamic")
    startYear = db.Column(db.Integer, nullable=True)
    endYear = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<Group: {self.groupName}, kgcId: {self.kgcId}>"

    def from_dict(self, data):
        for field in ["kgcId", "groupName", "country", "startYear", "endYear"]:
            if field in data and field is not None:
                setattr(self, field, data[field])
        for field in ["created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.current_timestamp())


class Organizations(db.Model, AuditMixin, PaginatedAPIMixin):
    __tablename__ = "organizations"

    facId = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    kgcId = db.Column(
        db.Integer, db.ForeignKey("groups.kgcId")
    )  # Might not be necessary if we can indirectly ref via the group backref
    facName = db.Column(db.String(767), nullable=False)
    startYear = db.Column(db.Integer, nullable=True)
    endYear = db.Column(db.Integer, nullable=True)
    nonviolentTactics = db.relationship(
        "NonviolentTactics",
        foreign_keys=[NonviolentTactics.facId],
        backref=db.backref("organization", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    violentTactics = db.relationship(
        "ViolentTactics",
        foreign_keys=[ViolentTactics.facId],
        backref=db.backref("organization", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Organization: {self.facName}, facId: {self.facId}>"

    def from_dict(self, data):
        for field in ["facId", "kgcId", "facName", "startYear", "endYear"]:
            if field in data and field is not None:
                setattr(self, field, data[field])
        for field in ["created_at", "modified_at"]:
            if field in data:
                dtime_obj = parser.parse(data[field])
                setattr(self, field, dtime_obj)
            else:
                setattr(self, field, func.now())


class User(UserMixin, PaginatedAPIMixin, AuditMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.email and self.email in current_app.config["ADMIN_EMAIL"]:
            self.is_admin = True

    def __repr__(self):
        return "User <id: {}, username: {}>".format(self.id, self.username)

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
            if field in data and field is not None:
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
            if "email" in data and data["email"] in current_app.config["ADMIN_EMAIL"]:
                setattr(self, "is_admin", True)

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode("utf-8")
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def get_token_expiration(self):
        return self.token_expiration

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
