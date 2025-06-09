import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_CONFIG = {
        #'host': os.getenv('DB_HOST', 'db'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'port': 3306
    }
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
