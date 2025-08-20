# This code is to create a test Bearer Token that expires in 10 years
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret")
    from auth_token_validator import generate_jwt_token
    user={
        "id":999,
        "email":"hanyelgaml@ideationmax.com",
        "business_id":999,
        "role":"admin"
    }
    token = generate_jwt_token(user, validity=315360000)
    print(token)
