import secrets
secret_key = secrets.token_urlsafe(64)
print(f"JWT_SECRET_KEY={secret_key}")