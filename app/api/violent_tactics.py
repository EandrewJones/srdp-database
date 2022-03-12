from flask import jsonify, request, url_for, abort
from marshmallow import ValidationError
from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import ViolentTacticsSchema, ViolentTacticsInputSchema
from app.models import ViolentTactics


@bp.route("/violent_tactics?id=<int:id>", methods=["GET"])
@token_auth.login_required
def get_violent_tactic(id):
    """
    get:
      summary: Get violent tactic by id
      description: retrieve violent tactic by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric primary key id of the violent action entry to retreieve
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: ViolentTacticsSchema
        '401':
          description: Not authenticated
      tags:
        - ViolentTactics
    """
    violent_tactic = ViolentTactics.query.get_or_404(id)
    return ViolentTacticsSchema.dump(violent_tactic)


@bp.route("/violent_tactics", method=["GET"])
@token_auth.login_required
def get_violent_tactics():
    """
    ---
    get:
      summary: get violent actions
      description: retrieve all violent actions
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: ViolentTacticsSchema
        '401':
          description: Not authenticated
      tags:
        - violent_tactics
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = ViolentTactics.to_collection_dict(
        ViolentTactics.query, page, per_page, ViolentTacticsSchema, "api.get_orgs"
    )
    return jsonify(data)


@bp.route("/violent_tactics?facId=<int:facId>", method=["GET"])
@token_auth.login_required
def get_org_violent_tactics(facId):
    """
    ---
    get:
      summary: Get violent tactics filtered by facId
      description: retrieve violent tactics by facId
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: facId
          schema:
            type: integer
          required: true
          description: Numeric facId of the organization to retrieve violent tactics for
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: ViolentTacticsSchema
        '401':
          description: Not authenticated
      tags:
        - ViolentTactics
    """
    violent_tactics = ViolentTactics.query.filter_by(facId=facId).all()
    return ViolentTacticsSchema(many=True).dump(violent_tactics)


@bp.route("/violent_tactics", methods=["POST"])
@token_auth.login_required
def create_violent_tactics():
    """
    ---
    post:
      summary: Create one or more violent tactics
      description: create new violent tactics by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: ViolentTacticsInputSchema
      responses:
        '201':
          description: call successful
          content:
            application/json:
              schema: ViolentTactics
        '401':
          description: Not authenticated
      tags:
        - ViolentTactics
    """
    data = request.get_json() or {}
    if "body" not in data:
        return bad_request("must include body field")
    # If single entry, regular add
    if isinstance(data, dict):
        if "id" in data and ViolentTactics.query.filter_by(id=data["id"]).first():
            return bad_request(
                f"id {data['id']} already taken; please use a different id."
            )
        try:
            violent_tactic = ViolentTacticsInputSchema().load(data)
        except ValidationError as err:
            print(err.messages)
            print(err.valid_data)
        db.session.add(violent_tactic)
        response = jsonify(ViolentTacticsSchema().dump(violent_tactic))
        response.status_code = 201
    # If multiple entries, bulk save
    if isinstance(data, list):
        for entry in data:
            if "id" in entry and ViolentTactics.query.filter_by(id=entry["id"]).first():
                return bad_request(
                    f"id {data['id']} already taken; please use a different id."
                )
        try:
            violent_tactics = ViolentTacticsInputSchema(many=True).load(data)
        except ValidationError as err:
            print(err.messages)
            print(err.valid_data)
        db.session.bulk_save_objects(violent_tactics)
        db.session.commit()
        response = jsonify(ViolentTacticsSchema(many=True).dump(violent_tactics))
        response.status_code = 201
        response.headers["Location"] = url_for(
            "api.get_violent_tactics"
        )  # Might cause problems
    return response


@bp.route("/violent_tactics?id=<int:id>", methods=["PUT"])
@token_auth.login_required
def update_violent_tactic(id):
    """
    put:
      summary: Modify a violent tactic entry
      description: modify a violent tactic by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: primary key id of violent tactic to update
      requestBody:
        required: true
        content:
          application/json:
            schema: ViolentTacticsInputSchema
      responses:
        '200':
          description: resource updated successful
          content:
            application/json:
              schema: ViolentTacticsSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - ViolentTactics
    """
    violent_tactic = ViolentTactics.query.get_or_404(id)
    data = request.get_json() or {}
    if "body" not in data:
        return bad_request("must include body field")
    violent_tactic.from_dict(data)
    db.session.commit()
    response = jsonify(ViolentTacticsSchema().dump(violent_tactic))
    response.status_code = 200
    response.headers["Location"] = url_for(
        "api.get_violent_tactic", facId=violent_tactic.id
    )
    return response


@bp.route("violent_tactics?id=<int:id>", methods=["DELETE"])
@token_auth.login_required
def delete_violent_tactic(id):
    """
    delete:
      summary: Delete a violent tactic entry
      description: delete violent tactic by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: primary key id o of the violent tactic entry to be deleted
      responses:
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags
        - ViolentTactics
    """
    violent_tactic = ViolentTactics.query.get_or_404(id)
    db.session.delete(violent_tactic)
    db.session.commit()
    return "", 204
