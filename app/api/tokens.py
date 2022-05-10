from flask import jsonify
from app import db
from app.api import bp
from app.api.auth import basic_auth, token_auth
from app.api_spec import TokenSchema

@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    """
    ---
    post:
      summary: Retrieve an authentication token
      description: Pass BasicAuth credentials to endpoint to receive an authentication token for further requests.
      security:
        - BasicAuth: []
      responses:
        '200':
          description: call successful
          content:
            application/json:
              schema: TokenSchema
        '401':
          description: Not authenticated
      tags:
        - Token
    """
    token = basic_auth.current_user().get_token()
    # expiration = basic_auth.current_user().get_token_expiration()
    payload = TokenSchema.load({'token': token, 'expiration': 0})
    db.session.commit()
    return TokenSchema().dump(payload)


@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204
