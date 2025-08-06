#!/usr/bin/env python3
"""
Elite Wellness Spa Authentication API
Handles both email/password and Google OAuth authentication
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
import secrets
import requests
import os
import json
import mysql.connector
from mysql.connector import Error
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("User blueprint loaded.")  # You must call this
# Create Blueprint
bp = Blueprint('user', __name__, url_prefix='')

# Configure logging


# CORS is now configured in app.py

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'elite_wellness_spa'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True
}

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')


def get_db_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None


def execute_query(query, params=None, fetch=False):
    """Execute database query"""
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch:
            result = cursor.fetchall() if fetch == 'all' else cursor.fetchone()
        else:
            result = cursor.rowcount

        cursor.close()
        connection.close()
        return result
    except Error as e:
        logger.error(f"Query execution error: {e}")
        if connection:
            connection.close()
        return None


def generate_jwt_token(user):
    """Generate JWT token for user"""
    import os
    from flask import current_app
    
    # Get JWT secret key from environment variables or use a default (not recommended for production)
    secret_key = os.getenv('JWT_SECRET_KEY')
    if not secret_key:
        if current_app.config.get('TESTING'):
            secret_key = 'test-secret-key'  # Only for testing
        else:
            raise ValueError("JWT_SECRET_KEY is not set in environment variables")
    
    payload = {
        'user_id': user['id'],
        'email': user['email'],
        'business_id': user['business_id'],
        'role': user['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')


def format_user_response(user):
    """Format user data for API response"""
    return {
        'id': user['id'],
        'email': user['email'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'full_name': f"{user['first_name']} {user['last_name']}",
        'role': user['role'],
        'permissions': json.loads(user['permissions']) if user['permissions'] else [],
        'avatar_url': user['profile_picture_url'],
        'auth_provider': user['auth_provider']
    }


def get_business_info(business_id):
    """Get business information"""

    query = "SELECT * FROM business WHERE business_id = %s"
    business = execute_query(query, (business_id,), fetch='one')

    if business:
        return {
            'id': business['business_id'],
            'name': business['name'],
            'slogan': "Business Slogan",
            'timezone': business['timezone'],
            'status': business['status']
        }
    return None

def create_weekly_business_hours(business_id):
    default_hours = [
        {"day_of_week": 0, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Monday
        {"day_of_week": 1, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Tuesday
        {"day_of_week": 2, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Wednesday
        {"day_of_week": 3, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Thursday
        {"day_of_week": 4, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Friday
        {"day_of_week": 5, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": True},  # Saturday (closed)
        {"day_of_week": 6, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": True}  # Sunday (closed)
    ]

    try:
        # Insert default hours for each day
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        for day in default_hours:
            cursor.execute("""
                           INSERT INTO business_hours
                               (business_id, day_of_week, open_time, close_time, is_closed)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (
                               business_id,
                               day['day_of_week'],
                               day['open_time'],
                               day['close_time'],
                               False
                           ))
        conn.commit()
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {str(err)}"}), 500

@bp.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    """User registration endpoint"""
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()
        logger.info(f"Signup request received: {data}")

        if not data:
            logger.error("No JSON data received")
            return jsonify({
                'success': False,
                'error': 'no_data',
                'message': 'No data received'
            }), 400

        # Extract and validate signup data
        business_name = data.get('businessName')
        admin_name = data.get('adminName')
        email = data.get('email')
        password = data.get('password')
        admin_phone = data.get('adminPhone')

        logger.info(f"Parsed data - Email: {email}, Business: {business_name}, Admin: {admin_name}")

        # Validate required fields
        if not all([business_name, admin_name, email, password]):
            return jsonify({
                'success': False,
                'error': 'missing_fields',
                'message': 'All fields are required'
            }), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({
                'success': False,
                'error': 'invalid_email',
                'message': 'Invalid email format'
            }), 400

        # Validate password strength
        if len(password) < 8:
            return jsonify({
                'success': False,
                'error': 'weak_password',
                'message': 'Password must be at least 8 characters long'
            }), 400

        # Check if user already exists
        logger.info(f"Checking if user exists: {email}")
        existing_user = execute_query(
            "SELECT id FROM users WHERE email = %s",
            (email,),
            fetch='one'
        )

        if existing_user:
            logger.info(f"User already exists: {email}")
            return jsonify({
                'success': False,
                'error': 'user_exists',
                'message': 'An account with this email already exists'
            }), 409
            
        # Check if business name already exists
        logger.info(f"Checking if business exists: {business_name}")
        existing_business = execute_query(
            "SELECT business_id FROM business WHERE name = %s",
            (business_name,),
            fetch='one'
        )

        if existing_business:
            logger.info(f"Business already exists: {business_name}")
            return jsonify({
                'success': False,
                'error': 'business_exists',
                'message': 'A business with this name already exists'
            }), 409

        # Create new business record
        logger.info(f"Creating business: {business_name}")

        # First, insert the business record
        business_insert = """
                          INSERT INTO business (name, timezone, status)
                          VALUES (%s, %s, %s)
                          """
        try:
            # Get database connection and cursor
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Insert the business
            cursor.execute(
                "INSERT INTO business (name, timezone, status) VALUES (%s, %s, %s)",
                (business_name, 'UTC', 'active')
            )
            
            # Get the last inserted ID
            business_id = cursor.lastrowid
            
            if business_id is None or business_id == 0:
                raise Exception("No business ID returned from database")

            create_weekly_business_hours(business_id)
            # Commit the transaction
            conn.commit()
            
        except Exception as e:
            # Rollback in case of error
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Failed to create business: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'business_creation_failed',
                'message': 'Failed to create business record'
            }), 500
            
        finally:
            # Close cursor and connection
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
        logger.info(f"Business created successfully with ID: {business_id}")
        
        # Add admin phone to business_phone table if provided
        if admin_phone:
            phone_insert = """
                          INSERT INTO business_phone (business_id, business_phone, is_primary)
                          VALUES (%s, %s, TRUE)
                          """
            execute_query(phone_insert, (business_id, admin_phone))

        # Create new user account
        user_id = f"user_{secrets.token_hex(8)}"
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        # Parse admin name
        name_parts = admin_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user_insert = """
                      INSERT INTO users (
                          id, email, password_hash, first_name, last_name, 
                          role, business_id, auth_provider, permissions, 
                          phone, active, email_verified, created_at, updated_at
                      ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                      """

        permissions = json.dumps(['read', 'write', 'delete', 'manage_staff', 'manage_appointments', 'manage_business'])

        execute_query(user_insert, (
            user_id,
            email,
            password_hash,
            first_name,
            last_name,
            'admin',  # New signups are business admins
            business_id,
            'email',
            permissions,
            admin_phone,
            True,
            False,  # Email verification required
            datetime.datetime.utcnow(),
            datetime.datetime.utcnow()
        ))

        # Fetch the created user
        new_user = execute_query(
            "SELECT * FROM users WHERE id = %s",
            (user_id,),
            fetch='one'
        )

        if not new_user:
            return jsonify({
                'success': False,
                'error': 'user_creation_failed',
                'message': 'Failed to create user account'
            }), 500

        # Generate JWT token
        token = generate_jwt_token(new_user)

        # Get business info
        business = get_business_info(business_id)

        logger.info(f"User successfully created: {email}")

        return jsonify({
            'success': True,
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 86400,
            'admin': format_user_response(new_user),
            'business': business,
            'message': 'Account created successfully'
        }), 201

    except Exception as e:
        logger.error(f"Signup error: {e}")
        import traceback
        logger.error(f"Signup traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': f'Failed to create account: {str(e)}'
        }), 500

@bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    """Email/password authentication endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'missing_credentials',
                'message': 'Email and password are required'
            }), 400

        # Get user from database
        query = """
                SELECT * \
                FROM users
                WHERE email = %s \
                  AND active = 1 \
                """
        user = execute_query(query, (email,), fetch='one')

        if not user:
            return jsonify({
                'success': False,
                'error': 'invalid_credentials',
                'message': 'Invalid email or password'
            }), 401

        # Verify password for email auth
        if user['auth_provider'] in ['email', 'email,google'] and user['password_hash']:
            if not check_password_hash(user['password_hash'], password):
                return jsonify({
                    'success': False,
                    'error': 'invalid_credentials',
                    'message': 'Invalid email or password'
                }), 401
        else:
            return jsonify({
                'success': False,
                'error': 'social_login_required',
                'message': 'This account uses social login. Please use Google sign-in.'
            }), 401

        # Update last login
        update_query = "UPDATE users SET last_login = %s WHERE id = %s"
        execute_query(update_query, (datetime.datetime.utcnow(), user['id']))

        # Generate JWT token
        token = generate_jwt_token(user)

        # Get business info
        business = get_business_info(user['business_id'])

        return jsonify({
            'success': True,
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 86400,
            'admin': format_user_response(user),
            'business': business
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500


@bp.route('/social/callback', methods=['POST', 'OPTIONS'])
def social_callback():
    """Google OAuth callback endpoint"""
    # Handle CORS preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Domain,Accept,Origin')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response, 200

    try:
        data = request.get_json()
        logger.info(f"Social callback received: {data}")

        provider = data.get('provider')
        code = data.get('code')
        state = data.get('state')
        redirect_uri = data.get('redirect_uri')

        logger.info(f"Provider: {provider}, Code length: {len(code) if code else 0}")

        if provider != 'google':
            logger.error(f"Unsupported provider: {provider}")
            return jsonify({
                'success': False,
                'error': 'unsupported_provider',
                'message': 'Only Google OAuth is supported'
            }), 400

        if not code:
            logger.error("Missing authorization code")
            return jsonify({
                'success': False,
                'error': 'missing_code',
                'message': 'Authorization code is required'
            }), 400

        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            logger.error(
                f"Google OAuth credentials not configured - CLIENT_ID: {'SET' if GOOGLE_CLIENT_ID else 'MISSING'}, CLIENT_SECRET: {'SET' if GOOGLE_CLIENT_SECRET else 'MISSING'}")
            return jsonify({
                'success': False,
                'error': 'oauth_not_configured',
                'message': 'Google OAuth credentials not configured on server. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.'
            }), 500

        # Exchange code for Google access token
        logger.info(f"Attempting to exchange Google code for token...")
        google_user = exchange_google_code(code, redirect_uri)
        if not google_user:
            logger.error("Failed to exchange Google code")
            return jsonify({
                'success': False,
                'error': 'google_auth_failed',
                'message': 'Failed to authenticate with Google'
            }), 401

        logger.info(f"Google user data received: {google_user.get('email', 'no email')}")

        # Find or create user
        logger.info(f"Attempting to find or create user for email: {google_user.get('email')}")
        user = find_or_create_social_user(google_user, 'google')
        if not user:
            logger.error("User creation/lookup failed - check database connection and schema")
            return jsonify({
                'success': False,
                'error': 'user_creation_failed',
                'message': 'Failed to create user account - check server logs'
            }), 500

        logger.info(f"User found/created successfully: {user.get('email', 'no email')}")

        # Generate JWT token
        token = generate_jwt_token(user)

        # Get business info
        business = get_business_info(user['business_id'])

        return jsonify({
            'success': True,
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 86400,
            'admin': format_user_response(user),
            'business': business
        }), 200

    except Exception as e:
        logger.error(f"Social auth error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': f'Internal server error: {str(e)}'
        }), 500

def exchange_google_code(auth_code, redirect_uri):
    """Exchange Google authorization code for user information"""
    try:
        # Exchange code for tokens
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }

        token_response = requests.post(token_url, data=token_data)
        tokens = token_response.json()

        if 'access_token' not in tokens:
            logger.error(f"Google token exchange failed: {tokens}")
            return None

        # Get user info from Google
        user_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={tokens['access_token']}"
        user_response = requests.get(user_url)
        user_data = user_response.json()

        return {
            'id': user_data['id'],
            'email': user_data['email'],
            'first_name': user_data.get('given_name', ''),
            'last_name': user_data.get('family_name', ''),
            'picture': user_data.get('picture'),
            'verified_email': user_data.get('verified_email', False)
        }

    except Exception as e:
        logger.error(f"Google code exchange error: {e}")
        return None


def find_or_create_social_user(social_data, provider):
    """Find existing social user or create new one"""
    try:
        # Check if user exists by email
        query = "SELECT * FROM users WHERE email = %s"
        existing_user = execute_query(query, (social_data['email'],), fetch='one')

        if existing_user:
            # Update existing user with social login info
            if existing_user['auth_provider'] == 'email':
                # User previously used email/password, now adding social login
                update_query = """
                               UPDATE users \
                               SET social_id           = %s, \
                                   auth_provider       = 'email,google', \
                                   profile_picture_url = %s, \
                                   last_login          = %s
                               WHERE id = %s \
                               """
                execute_query(update_query, (
                    social_data['id'],
                    social_data['picture'],
                    datetime.datetime.utcnow(),
                    existing_user['id']
                ))
            else:
                # Update last login time
                update_query = "UPDATE users SET last_login = %s WHERE id = %s"
                execute_query(update_query, (datetime.datetime.utcnow(), existing_user['id']))

            # Return updated user
            return execute_query(query, (social_data['email'],), fetch='one')
        else:
            # Create new social user
            return create_social_user(social_data, provider)

    except Exception as e:
        logger.error(f"Find/create social user error: {e}")
        return None


def create_social_user(social_data, provider):
    """Create new user from social login data"""
    try:
        user_id = f"user_{secrets.token_hex(8)}"

        insert_query = """
                       INSERT INTO users (id, email, password_hash, first_name, last_name, role, business_id, \
                                          auth_provider, social_id, profile_picture_url, permissions, \
                                          active, email_verified, last_login, created_at) \
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                       """

        permissions = json.dumps(['read', 'write', 'manage_appointments'])

        execute_query(insert_query, (
            user_id,
            social_data['email'],
            None,  # No password for social users
            social_data['first_name'],
            social_data['last_name'],
            'admin',  # Default role for spa admins
            '1',  # Default business for Elite Wellness Spa
            provider,
            social_data['id'],
            social_data.get('picture'),
            permissions,
            True,
            social_data.get('verified_email', False),
            datetime.datetime.utcnow(),
            datetime.datetime.utcnow()
        ))

        # Return the created user
        query = "SELECT * FROM users WHERE id = %s"
        return execute_query(query, (user_id,), fetch='one')

    except Exception as e:
        logger.error(f"Create social user error: {e}")
        return None





@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200


@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'not_found',
        'message': 'Endpoint not found'
    }), 404


@bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'internal_error',
        'message': 'Internal server error'
    }), 500

