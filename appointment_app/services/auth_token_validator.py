import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
import os
import time
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
def verify_bearer_token(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, "Missing or invalid Authorization header"

    token = auth_header.split(" ")[1]  # Extract actual token
    try:
        # Decode and verify signature + expiration
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],   # Or ["RS256"] if using public/private keys
            options={"require": ["exp"]}  # Make sure exp is present
        )
        return payload, None  # Valid token
    except ExpiredSignatureError:
        return None, "Token has expired"
    except InvalidTokenError as e:
        return None, f"Invalid token: {str(e)}"


def generate_jwt_token(user, validity=86400): # -8640000
    """Generate JWT token for user"""
    payload = {
        'user_id': user['id'],
        'email': user['email'],
        'business_id': user['business_id'],
        'role': user['role'],
        'exp': int(time.time()) + validity,  # expires in 24 hours
        'iat': int(time.time())
    }
    token =  jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def generate_clover_jwt_token(business_id, validity=86400): # -8640000
    """Generate JWT token for user"""
    payload = {
        'provider': 'clover',
        'business_id': business_id,
        'exp': int(time.time()) + validity,  # expires in 24 hours
        'iat': int(time.time())
    }
    token =  jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token
