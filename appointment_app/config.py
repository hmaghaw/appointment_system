import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Main database configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'port': 3306
    }
    
    # Call history database configuration (separate instance on port 3307)
    CALL_HISTORY_DB_CONFIG = {
        'host': os.getenv('CALL_DB_HOST', 'localhost'),
        'user': os.getenv('CALL_DB_USER', 'call_user'),
        'password': os.getenv('CALL_DB_PASSWORD', 'call_password'),
        'database': os.getenv('CALL_DB_NAME', 'call_history'),
        'port': int(os.getenv('CALL_DB_PORT', 3307))
    }
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
