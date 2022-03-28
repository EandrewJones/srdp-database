from flask import jsonify, request, url_for
from marshmallow import ValidationError
from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.api_spec import (
    NonviolentTacticsSchema,
    NonviolentTacticsInputSchema,
)
from app.models import NonviolentTactics


@bp.route("/nonviolent_tactics/<int:id>", methods=["GET"])
@token_auth.login_required
def get_nonviolent_tactic(id):
    """
    ---
    get:
      summary: Get nonviolent tactic by id
      description: retrieve nonviolent tactic by id
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: Numeric primary key id of the non-violent action entry to retreieve
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: NonviolentTacticsSchema
        '401':
          description: Not authenticated
      tags:
        - NonviolentTactics
    """
    nonviolent_tactic = NonviolentTactics.query.get_or_404(id)
    response = jsonify(NonviolentTacticsSchema().dump(nonviolent_tactic))
    response.status_code = 200
    response.headers["Location"] = url_for(
        "api.get_nonviolent_tactic", id=nonviolent_tactic.id
    )
    return response


@bp.route("/nonviolent_tactics", methods=["GET"])
@token_auth.login_required
def get_nonviolent_tactics():
    """
    ---
    get:
      summary: get nonviolent actions
      description: retrieve all nonviolent actions
      security:
        - BasicAuth: []
        - BearerAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: NonviolentTacticsSchema
        '401':
          description: Not authenticated
      tags:
        - NonviolentTactics
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = NonviolentTactics.to_collection_dict(
        NonviolentTactics.query,
        page,
        per_page,
        NonviolentTacticsSchema,
        "api.get_nonviolent_tactics",
    )
    return jsonify(data)


@bp.route("/nonviolent_tactics", methods=["POST"])
@token_auth.login_required
def create_nonviolent_tactics():
    """
    ---
    post:
      summary: Create one or more nonviolent tactics
      description: create new nonviolent tactics by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema: NonviolentTacticsInputSchema
      responses:
        '201':
          description: call successful
          content:
            application/json:
              schema: NonviolentTactics
        '401':
          description: Not authenticated
      tags:
        - NonviolentTactics
    """
    data = request.get_json() or {}
    # If single entry, regular add
    if isinstance(data, dict):
        if "id" in data and NonviolentTactics.query.filter_by(id=data["id"]).first():
            return bad_request(
                f"id {data['id']} already taken; please use a different id."
            )
        nonviolent_tactic = NonviolentTactics()
        nonviolent_tactic.from_dict(data)
        db.session.add(nonviolent_tactic)
        db.session.commit()
        response = jsonify(NonviolentTacticsSchema().dump(nonviolent_tactic))
        response.status_code = 201
    # If multiple entries, bulk save
    if isinstance(data, list):
        nonviolent_tactics = []
        for entry in data:
            if (
                "id" in entry
                and NonviolentTactics.query.filter_by(id=entry["id"]).first()
            ):
                return bad_request(
                    f"id {data['id']} already taken; please use a different id."
                )
            nonviolent_tactic = NonviolentTactics()
            nonviolent_tactic.from_dict(entry)
            nonviolent_tactics.append(nonviolent_tactic)
        db.session.add_all(nonviolent_tactics)
        db.session.commit()
        response = jsonify(NonviolentTacticsSchema(many=True).dump(nonviolent_tactics))
        response.status_code = 201
        response.headers["Location"] = url_for("api.get_nonviolent_tactics")
    return response


@bp.route("/nonviolent_tactics/<int:id>", methods=["PUT"])
@token_auth.login_required
def update_nonviolent_tactic(id):
    """
    ---
    put:
      summary: Modify a nonviolent tactic entry
      description: modify a nonviolent tactic by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: primary key id of nonviolent tactic to update
      requestBody:
        required: true
        content:
          application/json:
            schema: NonviolentTacticsInputSchema
      responses:
        '200':
          description: resource updated successful
          content:
            application/json:
              schema: NonviolentTacticsSchema
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - NonviolentTactics
    """
    nonviolent_tactic = NonviolentTactics.query.get_or_404(id)
    data = request.get_json() or {}
    nonviolent_tactic.from_dict(data)
    db.session.commit()
    response = jsonify(NonviolentTacticsSchema().dump(nonviolent_tactic))
    response.status_code = 200
    response.headers["Location"] = url_for(
        "api.get_nonviolent_tactic", id=nonviolent_tactic.id
    )
    return response


@bp.route("nonviolent_tactics/<int:id>", methods=["DELETE"])
@token_auth.login_required
def delete_nonviolent_tactic(id):
    """
    ---
    delete:
      summary: Delete a nonviolent tactic entry
      description: delete nonviolent tactic by authorized user
      security:
        - BasicAuth: []
        - BearerAuth: []
      parameters:
        - in: path
          name: id
          schema:
            type: integer
          required: true
          description: primary key id o of the nonviolent tactic entry to be deleted
      responses:
        '401':
          description: Not authenticated
        '204':
          description: no content
      tags:
        - NonviolentTactics
    """
    nonviolent_tactic = NonviolentTactics.query.get_or_404(id)
    db.session.delete(nonviolent_tactic)
    db.session.commit()
    return "", 204
