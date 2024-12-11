# middleware.py

from flask import jsonify, request, redirect, make_response, session
from functools import wraps
import requests
import os
from jose import jwt, jwk
from jose.utils import base64url_decode
import time

# Middleware configuration
AUTH_SERVICE_BASE_URL = os.getenv('AUTH_SERVICE_BASE_URL')
COGNITO_DOMAIN = os.getenv('COGNITO_DOMAIN')
COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
COGNITO_CLIENT_SECRET = os.getenv('COGNITO_CLIENT_SECRET')
COGNITO_REGION = os.getenv('COGNITO_REGION')
COGNITO_REDIRECT_URI = os.getenv('COGNITO_REDIRECT_URI')

USER_POOL_ID = os.getenv('USER_POOL_ID')
TOKEN_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/oauth2/token"
JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"


def validate_jwt_token(token):
    try:
        jwks_response = requests.get(JWKS_URL).json()
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        try:
            key = next(k for k in jwks_response["keys"] if k["kid"] == kid)
        except StopIteration:
            print(f"No matching 'kid' found. JWT Header 'kid': {kid}")
            print(f"Available 'kids': {[k['kid'] for k in jwks_response['keys']]}")
            return False, None
        public_key = jwk.construct(key)

        # Verify the token
        message, encoded_signature = token.rsplit(".", 1)
        decoded_signature = base64url_decode(encoded_signature.encode())
        if not public_key.verify(message.encode(), decoded_signature):
            return False, None

        claims = jwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
        )
        if claims.get("exp", 0) < int(time.time()):
            return False, None

        return True, claims
    except Exception as e:
        print(f"Token validation error: {e}")
        return False, None


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")

        if access_token:
            valid, claims = validate_jwt_token(access_token)
            if valid:
                # attach user info to the request
                request.user_info = {
                    "user_id": claims.get("sub"),
                    "email": claims.get("email"),
                    "photo_url": claims.get("picture"),
                }
                return f(*args, **kwargs)

        if refresh_token:
            try:
                token_payload = {
                    "grant_type": "refresh_token",
                    "client_id": COGNITO_CLIENT_ID,
                    "client_secret": COGNITO_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                }
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                response = requests.post(TOKEN_URL, data=token_payload, headers=headers)
                print("Cognito Response:", response.json())
                new_tokens = response.json()

                if "error" in new_tokens:
                    raise Exception(new_tokens["error_description"])

                res = make_response(f(*args, **kwargs))
                res.set_cookie("access_token", new_tokens.get('access_token'))
                # res.set_cookie("refresh_token", new_tokens.get('refresh_token'))
                res.set_cookie("id_token", new_tokens.get('id_token'))
                valid, claims = validate_jwt_token(new_tokens.get('access_token'))
                if valid:
                    print("automatic token refresh done")
                    return res
            except Exception as e:
                print(f"Token refresh error: {e}")

        return jsonify({"error": "not authorized"}), 401

    return decorated_function

