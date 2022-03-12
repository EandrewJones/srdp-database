from flask import jsonify, request, url_for
from marshmallow import ValidationError
from app import db
from app.api import bp
from app.api.groups import get_group
from app.api.violent_tactics import get_violent_tactics
from app.api.nonviolent_tactics import get_nonviolent_tactics
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import (
    OrganizationSchema,
    OrganizationInputSchema,
)
from app.models import Organizations


@bp.route("/organizations", method=["GET"])
@token_auth.login_required
def get_orgs():
    """
    ---
    get:
      summary: get organizations
      description: retrieve all organizations
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: OrganizationSchema
        '401':
          description: Not authenticated
      tags:
        - Organizations
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Organizations.to_collection_dict(
        Organizations.query, page, per_page, OrganizationSchema, "api.get_orgs"
    )
    return jsonify(data)


@bp.route("/organizations?facId=<int:facId>", method=["GET"])
@token_auth.login_required
def get_organization(facId):
    """
    ---
    get:
      summary: Get single organization
      description: retrieve an organization by facId
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: facId
          schema:
            type: integer
          required: true
          description: Numeric facId of the organization to retrieve
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: OrganizationSchema
        '401':
          description: Not authenticated
      tags:
        - Organizations
    """
    group = Organizations.query.filter_by(facId=facId).first_or_404()
    return OrganizationSchema().dump(group)


@bp.route("/organizations/group?facId=<int:facId>", method=["GET"])
@token_auth.login_required
def get_org_group(facId):
    """
    ---
    get:
      summary: Get organization's parent ethnolinguistic group
      description: retrieve ethnolingustic group for which an organization makes claims
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: facId
          schema:
            type: integer
          required: true
          description: Numeric facId of the organization to fetch group for
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: GroupSchema
        '401':
          description: Not authenticated
      tags:
        - Organizations
    """
    organization = Organizations.query.filter_by(facId=facId).first_or_404()
    return get_group(kgcId=organization.kgcId)


@bp.route("/organizations/violentTactics?<int:facId>", methods=["GET"])
@token_auth.login_required
def get_org_violent_tactics(facId):
    """
    ---
    get:
      summary: Get organization's violent tactics
      description: retrieve collection of organization' violent tactics
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: facId
          schema:
            type: integer
          required: true
          description: Numeric facId of the organization to fetch violent tactics for
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: ViolentTacticsSchema
        '401':
          description: Not authenticated
      tags:
        - Organizations
    """
    return get_violent_tactics(facId=facId)


@bp.route("/organizations/nonviolentTactics?facId=<int:facId>", methods=["GET"])
@token_auth.login_required
def get_org_nonviolent_tactics(facId):
    """
    ---
    get:
      summary: Get organization's non-violent tactics
      description: retrieve collection of organization' non-violent tactics
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: facId
          schema:
            type: integer
          required: true
          description: Numeric facId of the organization to fetch non-violent tactics for
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: NonviolentTacticsSchema
        '401':
          description: Not authenticated
      tags:
        - Organizations
    """
    return get_nonviolent_tactics(facId=facId)


@bp.route("/organizations", methods=["POST"])
@token_auth.login_required
def create_orgs():
    """
    ---
    post:
      summary: Create one or more organizations
      description: create new organizations for authorized user
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
              schema: OrganizationSchema
        '401':
          description: Not authenticated
      tags:
        - Organizations
    """
    data = request.get_json() or {}
    if "body" not in data:
        return bad_request("must include body field")
    # If single entry, regular add
    if isinstance(data, dict):
        if "id" in data and Organizations.query.filter_by(facId=data["facId"]).first():
            return bad_request(
                f"facId {data['facId']} already taken; please use a different id."
            )
        try:
            organization = OrganizationInputSchema().load(data)
        except ValidationError as err:
            print(err.messages)
            print(err.valid_data)
        db.session.add(organization)
        response = jsonify(OrganizationSchema().dump(organization))
        response.status_code = 201
        response.headers["Location"] = url_for("api.get_org", facId=organization.facId)
    # If multiple entries, bulk save
    if isinstance(data, list):
        for entry in data:
            if (
                "facId" in entry
                and Organizations.query.filter_by(facId=entry["facId"]).first()
            ):
                return bad_request(
                    f"facId {data['facId']} already taken; please use a different facId."
                )
        try:
            organizations = OrganizationInputSchema(many=True).load(data)
        except ValidationError as err:
            print(err.messages)
            print(err.valid_data)
        db.session.bulk_save_objects(organizations)
        db.session.commit()
        response = jsonify(OrganizationSchema(many=True).dump(organizations))
        response.status_code = 201
        response.headers["Location"] = url_for("api.get_orgs")  # Might cause problems
    return response


@bp.route("/organizations?facId=<int:facId>", methods=["PUT"])
@token_auth.login_required
def update_org(facId):
    """
    put:
      summary: Modify an organization
      description: modify an organization by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: facId
          schema:
            type: integer
          required: true
          description: facId of the organization to update
      requestBody:
        required: true
        content:
          application/json:
            schema: OrganizationInputSchema
      responses:
        '200':
          description: resource updated successful
          content:
            application/json:
              schema: OrganizationSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - Organizations
    """
    organization = Organizations.query.filter_by(facId=facId).first_or_404()
    data = request.get_json() or {}
    if "body" not in data:
        return bad_request("must include body field")
    organization.from_dict(data)
    db.session.commit()
    response = jsonify(OrganizationSchema().dump(organization))
    response.status_code = 200
    response.headers["Location"] = url_for("api.get_org", facId=organization.facId)
    return response


@bp.route("organizations?facId=<int:facId>", methods=["DELETE"])
@token_auth.login_required
def delete_org(facId):
    """
    delete:
      summary: Delete an organization
      description: delete organization by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: facId
          schema:
            type: integer
          required: true
          description: facId of the organization to be deleted
      responses:
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags
        - Organizations
    """
    organization = Organizations.query.filter_by(facId=facId).first_or_404()
    db.session.delete(organization)
    db.session.commit()
    return "", 204
