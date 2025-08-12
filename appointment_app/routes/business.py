from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import mysql.connector
from database import get_db_cursor
from functools import wraps
from typing import List, Dict, Any, Optional

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

@bp.route('/working-hours', methods=['POST'])
@validate_business_id
def get_working_hours():
    """
    Get working hours for a business
    
    Request body: {
        "business_id": 1  # ID of the business
    }
    
    Returns: List of working hours for each day of the week with day names
    """
    data = request.get_json() or {}
    business_id = data.get('business_id')
    
    if not business_id:
        return jsonify({"error": "business_id is required in the request body"}), 400
    
    try:
        with get_db_cursor(dictionary=True) as cursor:
            # Get working hours from the database
            cursor.execute("""
                SELECT 
                    business_hours_id,
                    day_of_week,
                    open_time,
                    close_time,
                    is_closed
                FROM business_hours
                WHERE business_id = %s
                ORDER BY day_of_week
            """, (business_id,))
            
            hours = cursor.fetchall()
            
            # If no hours found, return empty list for all days
            if not hours:
                return jsonify({
                    "business_id": business_id,
                    "working_hours": []
                })
            
            # Convert to list with day names
            working_hours = []
            for day in hours:
                day_info = {
                    "business_hours_id": day['business_hours_id'],
                    "day_of_week": DAY_NAMES[day['day_of_week']],
                    "day_number": day['day_of_week'],
                    "open_time": str(day['open_time']) if day['open_time'] else None,
                    "close_time": str(day['close_time']) if day['close_time'] else None,
                    "is_closed": bool(day['is_closed'])
                }
                working_hours.append(day_info)
            
            return jsonify({
                "business_id": business_id,
                "working_hours": working_hours
            }), 200
        
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    
    return jsonify({"error": "Method not allowed"}), 405

@bp.route('/phones', methods=['POST'])
@validate_business_id
def list_business_phones():
    """
    List all phone numbers for a business
    
    Request body: {
        "business_id": 1  # ID of the business
    }
    
    Returns: List of phone numbers associated with the business
    """
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or 'business_id' not in data:
                return jsonify({"error": "Missing required field: business_id"}), 400
            
            business_id = data['business_id']
            
            # Get database connection and cursor
            with get_db_cursor(dictionary=True) as cursor:
                # Check if business exists
                cursor.execute("SELECT 1 FROM business WHERE business_id = %s", (business_id,))
                if not cursor.fetchone():
                    return jsonify({"error": f"Business with ID {business_id} not found"}), 404
                
                # Query business phones with language_code and language details
                query = """
                    SELECT 
                        bp.business_phone_id,
                        bp.business_id,
                        bp.phone_sid,
                        bp.friendly_name,
                        bp.business_phone,
                        bp.language_code,
                        bp.is_primary,
                        bp.created_at,
                        bp.updated_at,
                        l.language_name
                    FROM business_phone bp
                    LEFT JOIN language l ON bp.language_code = l.language_code
                    WHERE bp.business_id = %s
                    ORDER BY bp.is_primary DESC, bp.created_at ASC
                """
                
                cursor.execute(query, (business_id,))
                phones = cursor.fetchall()
            
            # Convert datetime objects to string for JSON serialization
            for phone in phones:
                phone['created_at'] = phone['created_at'].isoformat() if phone['created_at'] else None
                phone['updated_at'] = phone['updated_at'].isoformat() if phone['updated_at'] else None
            
            return jsonify({
                "business_id": business_id,
                "phones": phones
            }), 200
            
        except mysql.connector.Error as err:
            return jsonify({"error": f"Database error: {err}"}), 500
        except Exception as e:
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    
    return jsonify({"error": "Method not allowed"}), 405
