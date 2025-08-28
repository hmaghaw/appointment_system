from flask import Blueprint, jsonify, request, abort
from datetime import datetime, timedelta
import mysql.connector
from appointment_app.database import get_db_cursor
from functools import wraps
from typing import List, Dict, Any, Optional, Tuple
from appointment_app.services.auth_token_validator import verify_bearer_token

# Map day numbers to day names
DAY_NAMES = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
}

bp = Blueprint('business', __name__, url_prefix='/api/business')

@bp.route('/messages', methods=['POST'])
def handle_business_messages():
    """
    Handle business messages
    
    For listing messages, send:
    {
        "business_id": 123
    }
    
    For creating a new message, send:
    {
        "business_id": 123,
        "message": "Welcome to our business!",
        "type": "greeting",
        "is_active": true
    }
    """
    # Verify bearer token
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401
        
    data = request.get_json() or {}
    
    # If message and type are provided, it's a create request
    if 'message' in data and 'type' in data:
        return create_business_message()
    # Otherwise, it's a list request
    elif 'business_id' in data:
        return get_business_messages()
    else:
        return jsonify({"error": "Invalid request. Either provide business_id for listing or required fields for creation"}), 400

def get_business_messages():
    data = request.get_json() or {}
    business_id = data.get('business_id')
    
    if not business_id:
        return jsonify({"error": "business_id is required in the request body"}), 400
    
    query = """
        SELECT 
            bm.business_message_id,
            bm.business_id,
            bm.type,
            bm.message,
            bm.is_active,
            bm.created_at,
            bm.updated_at,
            b.name as business_name
        FROM business_messages bm
        JOIN business b ON bm.business_id = b.business_id
        WHERE bm.business_id = %s AND bm.is_active = TRUE
        ORDER BY bm.created_at DESC
    """
    
    with get_db_cursor() as cursor:
        cursor.execute(query, (business_id,))
        results = cursor.fetchall()
        
        if not results:
            return jsonify({"messages": [], "count": 0})
        
        # Convert rows to list of dictionaries
        columns = [col[0] for col in cursor.description]
        messages = []
        
        for row in results:
            message = {}
            for i, value in enumerate(row):
                col_name = columns[i]
                if isinstance(value, (datetime, timedelta)):
                    message[col_name] = value.isoformat()
                else:
                    message[col_name] = row[col_name]
            messages.append(message)
    
    return jsonify({
        "messages": messages,
        "count": len(messages)
    })

def create_business_message():
    data = request.get_json() or {}
    business_id = data.get('business_id')
    message = data.get('message')
    message_type = data.get('type', 'greeting')
    is_active = data.get('is_active', True)
    
    if not all([business_id, message]):
        return jsonify({"error": "business_id and message are required"}), 400
    
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO business_messages 
                (business_id, message, type, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (business_id, message, message_type, is_active))
            
            # Get the created message
            message_id = cursor.lastrowid
            cursor.execute("""
                SELECT bm.*, b.name as business_name
                FROM business_messages bm
                JOIN business b ON bm.business_id = b.business_id
                WHERE bm.business_message_id = %s
            """, (message_id,))
            
            result = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            new_message = {}
            for i, value in enumerate(result):
                col_name = columns[i]
                if isinstance(value, (datetime, timedelta)):
                    new_message[col_name] = value.isoformat()
                else:
                    new_message[col_name] = result[col_name]
            
            return jsonify(new_message), 201
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/by-phone', methods=['POST'])
def get_business_by_phone():
    """
    Get business information by phone number
    
    Request body: {
        "phone": "+1234567890"  # Phone number to search for
    }
    
    Returns: Business information if found, error otherwise
    """
    # Verify bearer token
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401
        
    data = request.get_json() or {}
    phone = data.get('business_phone')
    
    if not phone:
        return jsonify({"error": "Phone number is required in the request body"}), 400
    
    try:
        with get_db_cursor() as cursor:
            # Search for business by phone number
            cursor.execute("""
                SELECT
                    b.business_id,
                    b.name,
                    b.timezone,
                    b.status,
                    b.created_at,
                    b.updated_at,
                    bp.business_phone,
                    bp.language_code,
                    l.language_name
                FROM business b
                JOIN business_phone bp ON b.business_id = bp.business_id
                LEFT JOIN language l ON bp.language_code = l.language_code
                WHERE bp.business_phone = %s
                LIMIT 1
            """, (phone.strip(),))
            
            business = cursor.fetchone()
            
            if not business:
                return jsonify({"error": "No business found with the provided phone number"}), 404
            
            # Convert row to dictionary
            columns = [col[0] for col in cursor.description]
            business_dict = {}
            for i, value in enumerate(business):
                col_name = columns[i]
                if isinstance(value, (datetime, timedelta)):
                    business_dict[col_name] = value.isoformat()
                else:
                    business_dict[col_name] = business[col_name]
            
            return jsonify(business_dict)
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def validate_business_id(f):
    """Decorator to validate business_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json() or {}
        business_id = data.get('business_id')
        if not business_id:
            return jsonify({"error": "business_id is required in the request body"}), 400
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/get', methods=['POST'])
@validate_business_id
def get_business():
    """
    Get business information by ID
    
    Request body: {
        "business_id": 1  # ID of the business
    }
    
    Returns: Business information if found, 404 if not found
    """
    try:
        # Verify bearer token
        payload, error = verify_bearer_token(request)
        if error:
            return jsonify({"error": error}), 401
            
        data = request.get_json() or {}
        business_id = data.get('business_id')
        
        if not business_id:
            return jsonify({"error": "business_id is required in the request body"}), 400
            
        with get_db_cursor(dictionary=True) as cursor:
            # Get business information
            cursor.execute("""
                SELECT *
                FROM business
                WHERE business_id = %s
            """, (business_id,))
            
            business = cursor.fetchone()
            
            if not business:
                return jsonify({"error": "Business not found"}), 404
                
            # Convert datetime objects to ISO format strings
            for field in ['created_at', 'updated_at']:
                if field in business and business[field]:
                    if isinstance(business[field], datetime):
                        business[field] = business[field].isoformat()
                    
            return jsonify(business)
        
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@bp.route('', methods=['PUT'])
def update_business():
    """
    Update business settings
    
    Request body: {
        "business_id": 31,  # ID of the business to update
        "is_auto_recharge": 1,  # Optional: 0 or 1
        "recharge_threshold": 10,  # Optional: Threshold in cents
        "recharge_amount": 20  # Optional: Recharge amount in cents
    }
    
    Returns: Updated business information
    """
    try:
        # Verify bearer token
        payload, error = verify_bearer_token(request)
        if error:
            return jsonify({"error": error}), 401
            
        data = request.get_json() or {}
        business_id = data.get('business_id')
        
        if not business_id:
            return jsonify({"error": "business_id is required"}), 400
            
        # Define allowed fields that can be updated
        allowed_fields = {
            'is_auto_recharge': int,
            'recharge_threshold': int,
            'recharge_amount': int
        }
        
        # Filter and validate update fields
        update_fields = {}
        for field, field_type in allowed_fields.items():
            if field in data:
                try:
                    update_fields[field] = field_type(data[field])
                except (ValueError, TypeError):
                    return jsonify({"error": f"Invalid value for {field}"}), 400
        
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
            
        with get_db_cursor(dictionary=True, commit=True) as cursor:
            # Build the update query
            set_clause = ", ".join([f"{field} = %s" for field in update_fields])
            values = list(update_fields.values())
            values.append(business_id)
            
            query = f"""
                UPDATE business
                SET {set_clause}
                WHERE business_id = %s
            """
            
            cursor.execute(query, tuple(values))
            
            # Get the updated business record
            cursor.execute("""
                SELECT *
                FROM business
                WHERE business_id = %s
            """, (business_id,))
            
            updated_business = cursor.fetchone()
            
            if not updated_business:
                return jsonify({"error": "Business not found"}), 404
                
            # Convert datetime objects to ISO format strings
            for field in ['created_at', 'updated_at']:
                if field in updated_business and updated_business[field]:
                    if isinstance(updated_business[field], datetime):
                        updated_business[field] = updated_business[field].isoformat()
            
            return jsonify(updated_business)
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@bp.route('/phones', methods=['POST'])
def list_business_phones():
    """
    List all phone numbers for a business
    
    Request body: {
        "business_id": 1  # ID of the business
    }
    
    Returns: List of phone numbers associated with the business
    """
    try:
        # Verify bearer token
        payload, error = verify_bearer_token(request)
        if error:
            return jsonify({"error": error}), 401
            
        data = request.get_json() or {}
        business_id = data.get('business_id')
        
        if not business_id:
            return jsonify({"error": "business_id is required"}), 400
            
        with get_db_cursor(dictionary=True) as cursor:
            # Get business phones
            query = """
                SELECT 
                    bp.business_phone_id,
                    bp.business_phone,
                    bp.language_code,
                    l.language_name,
                    bp.is_primary,
                    bp.created_at,
                    bp.updated_at
                FROM business_phone bp
                LEFT JOIN language l ON bp.language_code = l.language_code
                WHERE bp.business_id = %s
                ORDER BY 
                    bp.is_primary DESC,
                    bp.business_phone
            """
            
            cursor.execute(query, (business_id,))
            phones = cursor.fetchall()
        
        # Convert datetime objects to string for JSON serialization
        for phone in phones:
            for field in ['created_at', 'updated_at']:
                if field in phone and phone[field]:
                    if isinstance(phone[field], datetime):
                        phone[field] = phone[field].isoformat()
        
        return jsonify({
            "business_id": business_id,
            "phones": phones
        }), 200
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/phone/language', methods=['PUT'])
def update_phone_language():
    """
    Update the language code for a business phone
    
    Request body: {
        "business_phone_id": 123,  # ID of the phone to update
        "language_code": "en"      # New language code (e.g., 'en', 'es', 'fr')
    }
    
    Returns: Updated phone information or error message
    """
    try:
        # Verify bearer token
        payload, error = verify_bearer_token(request)
        if error:
            return jsonify({"error": error}), 401
            
        data = request.get_json() or {}
        business_phone_id = data.get('business_phone_id')
        language_code = data.get('language_code')
        
        if not all([business_phone_id, language_code]):
            return jsonify({
                "success": False,
                "error": "Both business_phone_id and language_code are required"
            }), 400
            
        # First, verify the language code is valid
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT language_code FROM language WHERE language_code = %s", (language_code,))
            if not cursor.fetchone():
                # If exact match not found, try case-insensitive search
                cursor.execute("SELECT language_code FROM language WHERE LOWER(language_code) = LOWER(%s)", (language_code,))
                lang = cursor.fetchone()
                if not lang:
                    # Get list of available languages for the error message
                    cursor.execute("SELECT language_code, language_name FROM language")
                    available_langs = cursor.fetchall()
                    return jsonify({
                        "success": False,
                        "error": f"Invalid language code: {language_code}",
                        "available_languages": available_langs
                    }), 400
                language_code = lang['language_code']  # Use the correct case from DB
            
        with get_db_cursor(dictionary=True, commit=True) as cursor:
            # Check if the phone exists
            cursor.execute(
                "SELECT * FROM business_phone WHERE business_phone_id = %s",
                (business_phone_id,)
            )
            phone = cursor.fetchone()
            
            if not phone:
                return jsonify({
                    "success": False,
                    "error": "Phone not found"
                }), 404
            
            # Update the language code
            cursor.execute(
                """
                UPDATE business_phone 
                SET language_code = %s,
                    updated_at = NOW()
                WHERE business_phone_id = %s
                """,
                (language_code, business_phone_id)
            )
            
            # Commit the transaction to ensure the update is saved
            
            # Get the updated record
            cursor.execute(
                """
                SELECT 
                    bp.business_id,
                    bp.business_phone_id,
                    bp.language_code
                FROM business_phone bp
                WHERE bp.business_phone_id = %s
                """,
                (business_phone_id,)
            )
            updated_phone = cursor.fetchone()
            
            if not updated_phone:
                return jsonify({
                    "success": False,
                    "error": "Failed to fetch updated phone information"
                }), 500
            
            # Get the language name
            cursor.execute(
                "SELECT language_name FROM language WHERE language_code = %s",
                (language_code,)
            )
            language_result = cursor.fetchone()
            language_name = language_result['language_name'] if language_result else "Unknown"
            
            # Prepare response data
            response_data = {
                "business_id": updated_phone['business_id'],
                "business_phone_id": updated_phone['business_phone_id'],
                "language_code": updated_phone['language_code'],
                "language_name": language_name
            }
            
            return jsonify({
                "success": True,
                "message": "Phone language updated successfully",
                "phone": response_data
            }), 200
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
