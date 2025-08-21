#!/usr/bin/env python3
"""
Elite Wellness Spa Authentication API
Handles both email/password and Google OAuth authentication
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import secrets
import requests
import os
import json
import mysql.connector
from mysql.connector import Error
import logging
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from ..services.send_email_notification import send_email_notification
import time
from ..services.auth_token_validator import generate_jwt_token, verify_bearer_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("User blueprint loaded.")

# Create Blueprint
bp = Blueprint('user', __name__, url_prefix='')

# Password reset token expiration (24 hours)
RESET_TOKEN_EXPIRATION = 24 * 60 * 60  # 24 hours in seconds

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID')
GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET')
GMAIL_REFRESH_TOKEN = os.getenv('GMAIL_REFRESH_TOKEN')
GMAIL_USER = os.getenv('GMAIL_USER')
EMAIL_FROM = os.getenv('EMAIL_FROM', GMAIL_USER or 'noreply@elitewellnessspa.com')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://1b508cc8-944c-4d37-9ed6-0934fa85b53c-00-2jwasb0kbfe30.spock.replit.dev')

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


def format_user_response(user):
    """Format user data for API response"""
    return {
        'id': user['id'],
        'email': user['email'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'full_name': f"{user['first_name']} {user['last_name']}",
        'role': user['role'],
        'permissions': json.loads(user['permissions']) if user.get('permissions') else [],
        'avatar_url': user.get('profile_picture_url'),
        'auth_provider': user.get('auth_provider', 'email'),
        'email_verified': bool(user.get('email_verified')),
        'active': bool(user.get('active', False))
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
    inserted = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        for entry in default_hours:
            cursor.execute("""
                INSERT INTO business_hours (business_id, day_of_week, open_time, close_time, is_closed)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                business_id,
                entry["day_of_week"],
                entry["open_time"] if not entry["is_closed"] else None,
                entry["close_time"] if not entry["is_closed"] else None,
                entry["is_closed"]
            ))

            inserted.append({
                "business_id": business_id,
                "day_of_week": entry["day_of_week"],
                "open_time": entry["open_time"] if not entry["is_closed"] else None,
                "close_time": entry["close_time"] if not entry["is_closed"] else None,
                "is_closed": entry["is_closed"]
            })

        return inserted

    except mysql.connector.Error as err:
        raise RuntimeError(f"Database error: {str(err)}")

def send_verification_email(email, token, first_name, last_name):
    """Send an email with the verification link using the centralized email service"""
    verification_url = f"{FRONTEND_URL}/verify-email?token={token}"
    return send_email_notification(
        trigger_event="email_verification",
        to=email,
        first_name=first_name,
        verify_url=verification_url,
        expires_minutes=1440  # 24 hours
    )

def validate_reset_token(token):
    """Validate a password reset token and return the user if valid"""
    query = """
    SELECT user_id, expires_at, used 
    FROM password_reset_tokens 
    WHERE token = %s AND used = 0 AND expires_at > UTC_TIMESTAMP()
    LIMIT 1
    """
    result = execute_query(query, (token,), fetch=True)
    
    if not result:
        return None
    
    return result['user_id']  # Return user_id


def mark_token_used(token):
    """Mark a reset token as used"""
    query = """
    UPDATE password_reset_tokens 
    SET used = 1 
    WHERE token = %s
    """
    execute_query(query, (token,))


def send_password_reset_email(email, token):
    """Send a password reset email with the reset token using the centralized email service"""
    try:
        # Get user by email to include their name in the email
        query = "SELECT id, first_name, last_name, email_verified FROM users WHERE email = %s"
        result = execute_query(query, (email,), fetch=True)
        
        if not result:
            logger.warning(f"Attempted to send reset email to non-existent email: {email}")
            return True  # Don't reveal if email exists or not
            
        #user_id, first_name, last_name, email_verified = result[0]
        user_id= result['id']
        first_name= result['first_name']
        last_name= result['last_name']
        email_verified= result['email_verified']

        # Don't allow password reset for unverified emails
        if not email_verified:
            logger.warning(f"Attempted password reset for unverified email: {email}")
            return True  # Still return success to avoid email enumeration
            
        reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
        
        # Send the email using the centralized email service
        return send_email_notification(
            trigger_event="password_reset_request",
            to=email,
            first_name=first_name,
            reset_url=reset_url,
            ttl_minutes=1440  # 24 hours
        )
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}", exc_info=True)
        return False


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
        first_name = data.get('adminFirstName')
        last_name = data.get('adminLastName')
        email = data.get('email')
        password = data.get('password')
        admin_phone = data.get('adminPhone')

        logger.info(f"Parsed data - Email: {email}, Business: {business_name}, Admin: {first_name} {last_name}")

        # Validate required fields
        if not all([business_name, first_name, last_name, email, password]):
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

        # Create new user account (initially inactive)
        user_id = f"user_{secrets.token_hex(8)}"
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        permissions = json.dumps(['read', 'write', 'delete', 'manage_staff', 'manage_appointments', 'manage_business'])

        try:
            # Get a new connection and cursor for user creation
            user_conn = get_db_connection()
            user_cursor = user_conn.cursor(dictionary=True)
            
            # Insert the user (initially inactive)
            user_cursor.execute(
                """
                INSERT INTO users 
                (id, email, password_hash, first_name, last_name, role, business_id, 
                 auth_provider, active, email_verified, permissions, phone, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (user_id, email, password_hash, first_name, last_name, 'admin', 
                 business_id, 'email', False, False, permissions, admin_phone)
            )
            
            # Commit the transaction
            user_conn.commit()
            
            # Return success response with user data (user is inactive until email is verified)
            user = {
                'id': user_id,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'role': 'admin',
                'business_id': business_id,
                'auth_provider': 'email',
                'active': False,
                'email_verified': False,
                'permissions': json.loads(permissions)
            }
            
            # Generate and send verification email (this also sends a welcome email)
            verification_token =  generate_jwt_token(user)

            send_verification_email(email, verification_token, first_name, last_name)
            
            return jsonify({
                'success': True,
                'message': 'Registration successful! Please check your email to verify your account.',
                'user': user
            }), 200
            
        except Exception as e:
            if 'user_conn' in locals() and user_conn:
                user_conn.rollback()
            logger.error(f"Failed to create user: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'user_creation_failed',
                'message': 'Failed to create user account. Please try again.'
            }), 500
            
        finally:
            if 'user_cursor' in locals() and user_cursor:
                user_cursor.close()
            if 'user_conn' in locals() and user_conn:
                user_conn.close()

    except Exception as e:
        logger.error(f"Signup error: {e}")
        import traceback
        logger.error(f"Signup traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': f'Failed to create account: {str(e)}'
        }), 500

@bp.route('/resend_verify_email', methods=['POST', 'OPTIONS'])
def resend_verify_email():

    if request.method == 'OPTIONS':
        return '', 200
    data = request.get_json()
    email = data.get('email')

    query = """
            SELECT * \
            FROM users
            WHERE email = %s \
            """
    user = execute_query(query, (email,), fetch='one')

    # Generate and send verification email (this also sends a welcome email)
    verification_token = generate_jwt_token(user)

    send_verification_email(email, verification_token, user["first_name"], user["last_name"])

    return jsonify({
        'success': True,
        'message': 'Verification email resent! Please check your email to verify your account.',
        'user': user
    }), 200

@bp.route('/verify-email', methods=['GET'])
def verify_email():
    """Verify user's email using the verification token"""
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    user_id = payload['user_id']
    
    try:
        # Activate the user and mark email as verified
        execute_query(
            "UPDATE users SET active = TRUE, email_verified = TRUE WHERE id = %s",
            (user_id,)
        )
        
        # Get user data to generate JWT
        user = execute_query(
            "SELECT * FROM users WHERE id = %s",
            (user_id,),
            fetch='one'
        )
        
        if not user:
            raise Exception("User not found after verification")
            
        # Generate JWT token
        token = generate_jwt_token(user)
        business = get_business_info(user['business_id'])

        return jsonify({
            'success': True,
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 86400,
            'admin': format_user_response(user),
            'business': business,
            'message': 'Email verified successfully',
        })
        
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'verification_failed',
            'message': 'Failed to verify email. Please try again.'
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
                WHERE email = %s 
                """
        user = execute_query(query, (email,), fetch='one')
        if not user['email_verified']:
            return jsonify({
                'success': False,
                'error': 'email_not_verified',
                'message': 'Your email is not verified'
            }), 401

        if not user['active']:
            return jsonify({
                'success': False,
                'error': 'inactive_user',
                'message': 'Your user account is inactive. Please contact your administrator.'
            }), 401

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
        execute_query(update_query, (datetime.utcnow(), user['id']))

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

@bp.route('/request_password_reset', methods=['POST'])
def request_password_reset():
    """Request a password reset email"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'missing_email',
                'message': 'Email is required'
            }), 400
            
        # Check if user exists, password is correct, and email is verified
        user = execute_query(
            "SELECT * FROM users WHERE email = %s",
            (email,),
            fetch='one'
        )
        
        if user and not user.get('email_verified'):
            return jsonify({
                'success': False,
                'error': 'email_not_verified',
                'message': 'Please verify your email before logging in. Check your email for the verification link.'
            }), 403
            
        if user and not user.get('active'):
            return jsonify({
                'success': False,
                'error': 'account_inactive',
                'message': 'Your account is not active. Please contact support.'
            }), 403
        
        if not user:
            # Don't reveal if the email exists or not
            logger.info(f"Password reset requested for non-existent email: {email}")
            return jsonify({
                'success': True,
                'message': 'If an account with this email exists, a password reset link has been sent.'
            })
            
        # Generate and store reset token
        token = generate_jwt_token(user,1800) # Token Expires in 30 mins
        # Send password reset email
        email_sent = send_password_reset_email(user['email'], token)
        
        if not email_sent:
            logger.error(f"Failed to send password reset email to {email}")
            return jsonify({
                'success': False,
                'error': 'email_send_failed',
                'message': 'Failed to send password reset email. Please try again later.'
            }), 500
            
        return jsonify({
            'success': True,
            'message': 'If an account with this email exists, a password reset link has been sent.'
        })
        
    except Exception as e:
        logger.error(f"Error in request_password_reset: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'server_error',
            'message': 'An error occurred while processing your request.'
        }), 500


@bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset user password with a valid token"""
    try:
        # Verify bearer token
        payload, error = verify_bearer_token(request)
        if error:
            return jsonify({"error": error}), 401

        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')
        
        if not all([token, new_password]):
            return jsonify({
                'success': False,
                'error': 'missing_fields',
                'message': 'Token and new password are required'
            }), 400
            
        # Validate password strength
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'error': 'weak_password',
                'message': 'Password must be at least 8 characters long'
            }), 400
            
        # Validate token and get user ID
        user_id = validate_reset_token(token)
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'invalid_token',
                'message': 'Invalid or expired password reset token.'
            }), 400
            
        # Hash the new password
        password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Update user's password
        update_query = """
        UPDATE users 
        SET password_hash = %s, updated_at = UTC_TIMESTAMP()
        WHERE id = %s
        """
        execute_query(update_query, (password_hash, user_id))
        
        # Mark token as used
        mark_token_used(token)
        
        return jsonify({
            'success': True,
            'message': 'Your password has been successfully reset.'
        })
        
    except Exception as e:
        logger.error(f"Error in reset_password: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'server_error',
            'message': 'An error occurred while resetting your password.'
        }), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
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

