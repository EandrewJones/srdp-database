from flask import jsonify, request, url_for
from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import GroupSchema, OrganizationSchema
from app.models import Groups, Organizations, Organizations


@bp.route("/groups", methods=["GET"])
@token_auth.login_required
def get_groups():
    """
    ---
    get:
      summary: get groups
      description: retrieve all groups
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: GroupSchema
        '401':
          description: Not authenticated
      tags:
        - Groups
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Groups.to_collection_dict(
        Groups.query, page, per_page, GroupSchema, "api.get_groups"
    )
    return jsonify(data)


@bp.route("/groups/<int:kgcId>", methods=["GET"])
@token_auth.login_required
def get_group(kgcId):
    """
    ---
    get:
      summary: Get single group
      description: retrieve a group by kgcId
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: kgcId
          schema:
            type: integer
          required: true
          description: Numeric kgcId of the group to retrieve
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: GroupSchema
        '401':
          description: Not authenticated
      tags:
        - Groups
    """
    group = Groups.query.filter_by(kgcId=kgcId).first_or_404()
    return GroupSchema().dump(group)


@bp.route("/groups/<int:kgcId>/organizations", methods=["GET"])
@token_auth.login_required
def get_group_organizations(kgcId):
    """
    ---
    get:
      summary: Get group organizations
      description: retrieve a all organizations within an ethnolingustic group
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: kgcId
          schema:
            type: integer
          required: true
          description: Numeric kgcId of the group to get organizations for
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: GroupSchema
        '401':
          description: Not authenticated
      tags:
        - Groups
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    organizations = Organizations.query.filter_by(kgcId=kgcId)
    data = Organizations.to_collection_dict(
        organizations,
        page,
        per_page,
        OrganizationSchema,
        "api.get_group_organizations",
        kgcId=kgcId,
    )
    return jsonify(data)


@bp.route("/groups", methods=["POST"])
@token_auth.login_required
def create_groups():
    """
    ---
    post:
      summary: Create a group
      description: create new posts for authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: GroupInputSchema
      responses:
        '201':
          description: call successful
          content:
            application/json:
              schema: GroupSchema
        '401':
          description: Not authenticated
      tags:
        - Groups
    """
    data = request.get_json() or {}
    # If single entry, regular add
    if isinstance(data, dict):
        if "kgcId" not in data:
            return bad_request("must include kgcId field")
        if (
            "kgcId" in data
            and Organizations.query.filter_by(kgcId=data["kgcId"]).first()
        ):
            return bad_request(
                f"kgcId {data['kgcId']} already taken; please use a different id."
            )

        group = Groups()
        group.from_dict(data)
        db.session.add(group)
        db.session.commit()
        response = jsonify(GroupSchema().dump(group))
        response.status_code = 201
        response.headers["Location"] = url_for("api.get_group", kgcId=group.kgcId)
    # If multiple entries, bulk save
    if isinstance(data, list):
        groups = []
        for entry in data:
            if "kgcId" not in entry:
                return bad_request("must include kgcId field")
            if (
                "kgcId" in entry
                and Organizations.query.filter_by(kgcId=entry["kgcId"]).first()
            ):
                return bad_request(
                    f"kgcId {data['kgcId']} already taken; please use a different kgcId."
                )
            group = Groups()
            group.from_dict(entry)
            groups.append(group)
        db.session.add_all(groups)
        db.session.commit()
        response = jsonify(GroupSchema(many=True).dump(groups))
        response.status_code = 201
        response.headers["Location"] = url_for("api.get_groups")  # Might cause problems
    return response


@bp.route("/groups/<int:kgcId>", methods=["PUT"])
@token_auth.login_required
def update_group(kgcId):
    """
    ---
    put:
      summary: Modify a group
      description: modify group by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: kgcId
          schema:
            type: integer
          required: true
          description: kgcId of the group to update
      requestBody:
        required: true
        content:
          application/json:
            schema: GroupInputSchema
      responses:
        '200':
          description: resource updated successful
          content:
            application/json:
              schema: GroupSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Groups
    """
    group = Groups.query.filter_by(kgcId=kgcId).first_or_404()
    data = request.get_json() or {}
    group.from_dict(data)
    db.session.commit()
    response = jsonify(GroupSchema().dump(group))
    response.status_code = 200
    response.headers["Location"] = url_for("api.get_group", kgcId=group.kgcId)
    return response


@bp.route("groups/<int:kgcId>", methods=["DELETE"])
@token_auth.login_required
def delete_group(kgcId):
    """
    ---
    delete:
      summary: Delete a group
      description: delete group by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: kgcId
          schema:
            type: integer
          required: true
          description: kgcId of the group to be deleted
      responses:
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Groups
    """
    group = Groups.query.filter_by(kgcId=kgcId).first_or_404()
    db.session.delete(group)
    db.session.commit()
    return "", 204
