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
                    bp.business_phone
                FROM business b
                JOIN business_phone bp ON b.business_id = bp.business_id
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

@bp.route('/services', methods=['POST'])
@validate_business_id
def list_services():
    """
    List services for a business with optional language translation and active/inactive filtering
    
    Request body: {
        "business_id": 1,  # ID of the business
        "language": "en",  # Optional: Language code (defaults to 'en')
        "all": false       # Optional: If true, returns both active and inactive services
    }
    
    Returns: List of services for the business with translated content if available
    """
    data = request.get_json() or {}
    business_id = data['business_id']
    language = data.get('language', 'en')
    show_all = data.get('all', False)
    
    try:
        # Use a new connection to avoid unread results
        with get_db_cursor(commit=False) as cursor:
            # First, get the services with translations
            query = """
                SELECT 
                    s.service_id,
                    s.business_id,
                    COALESCE(st.name, s.name) as name,
                    COALESCE(st.description, s.description) as description,
                    s.duration_minutes,
                    s.price,
                    s.buffer_before_minutes,
                    s.buffer_after_minutes,
                    s.is_active,
                    s.created_at,
                    s.updated_at
                FROM service s
                LEFT JOIN (
                    SELECT service_id, name, description 
                    FROM service_translation 
                    WHERE language_code = %s
                ) st ON s.service_id = st.service_id
                WHERE s.business_id = %s
            """
            
            # Add active filter if not showing all services
            if not show_all:
                query += " AND s.is_active = TRUE"
                
            # Add ordering
            query += " ORDER BY name"
            
            # Execute the query with parameters
            cursor.execute(query, (language, business_id))
            
            # Fetch all rows at once to avoid unread results
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            
            services = []
            for row in rows:
                # Convert row to dictionary
                service = {}
                for i, value in enumerate(row):
                    col_name = columns[i]
                    value = row[col_name]
                    
                    # Handle None values
                    if value is None:
                        service[col_name] = None
                        continue
                        
                    # Convert bytes to string if needed
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except UnicodeDecodeError:
                            value = str(value, 'latin-1')
                    # Convert decimal to float for JSON serialization
                    elif col_name == 'price':
                        try:
                            value = float(value)
                        except (TypeError, ValueError):
                            value = None
                    # Convert datetime/timedelta to ISO format
                    elif isinstance(value, (datetime, timedelta)):
                        value = value.isoformat()
                    
                    service[col_name] = value
                
                # Ensure is_active is a boolean
                if 'is_active' in service:
                    service['is_active'] = bool(service['is_active'])
                
                services.append(service)
            
            return jsonify({
                "business_id": business_id,
                "services": services,
                "count": len(services)
            })
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/services', methods=['DELETE'])
def delete_service():
    """
    Permanently delete a service by ID (hard delete)
    
    Request body: {
        "service_id": 1    # ID of the service to delete
    }
    
    Returns: Success message or error
    """
    data = request.get_json() or {}
    service_id = data.get('service_id')
    
    if not service_id:
        return jsonify({"error": "service_id is required"}), 400
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # First check if the service exists
            cursor.execute(
                "SELECT service_id FROM service WHERE service_id = %s",
                (service_id,)
            )
            if not cursor.fetchone():
                return jsonify({"error": "Service not found"}), 404
            
            # Perform hard delete
            cursor.execute(
                "DELETE FROM service WHERE service_id = %s",
                (service_id,)
            )
            
            # Verify the service was deleted
            cursor.execute(
                "SELECT service_id FROM service WHERE service_id = %s",
                (service_id,)
            )
            if not cursor.fetchone():
                return jsonify({
                    "status": "success",
                    "message": f"Service {service_id} has been permanently deleted",
                    "service_id": service_id
                })
            else:
                return jsonify({
                    "error": "Failed to delete service",
                    "details": "The service record was not deleted as expected"
                }), 500
                
    except mysql.connector.Error as err:
        error_msg = f"Database error: {str(err)}"
        print(error_msg)  # Log the error for debugging
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)  # Log the error for debugging
        return jsonify({"error": error_msg}), 500

@bp.route('/services/upsert', methods=['POST'])
@validate_business_id
def upsert_service():
    """
    Create or update a service
    
    Request body: {
        "service_id": 1,              # Required for update, omit for create
        "business_id": 123,           # Required, validated by decorator
        "name": "Haircut",            # Required
        "description": "Basic haircut service",
        "duration_minutes": 30,       # Required
        "price": 25.00,
        "buffer_before_minutes": 5,
        "buffer_after_minutes": 5,
        "is_active": true             # Optional, defaults to true
    }
    
    Returns: The created/updated service
    """
    data = request.get_json() or {}
    business_id = data.get('business_id')
    service_id = data.get('service_id')
    
    # Validate required fields
    required_fields = ['name', 'duration_minutes']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    # Prepare service data
    service_data = {
        'business_id': business_id,
        'name': data['name'],
        'description': data.get('description', ''),
        'duration_minutes': data['duration_minutes'],
        'price': data.get('price'),
        'buffer_before_minutes': data.get('buffer_before_minutes', 0),
        'buffer_after_minutes': data.get('buffer_after_minutes', 0),
        'is_active': data.get('is_active', True) if service_id is None else data.get('is_active', True)
    }
    
    try:
        with get_db_cursor(commit=True) as cursor:
            if service_id:
                # Update existing service
                # First verify the service belongs to the business
                cursor.execute(
                    "SELECT service_id FROM service WHERE service_id = %s AND business_id = %s",
                    (service_id, business_id)
                )
                if not cursor.fetchone():
                    return jsonify({"error": "Service not found or access denied"}), 404
                
                # Update the service
                set_clause = ", ".join([f"{k} = %s" for k in service_data.keys()])
                values = list(service_data.values()) + [service_id]
                
                # Create parameter placeholders for the SET clause
                set_params = ", ".join([f"{k} = %s" for k in service_data.keys()])
                
                # Build the query with parameter placeholders
                query = f"""
                    UPDATE service 
                    SET {set_params}, updated_at = CURRENT_TIMESTAMP
                    WHERE service_id = %s
                """
                
                # Execute with all parameters in the correct order
                cursor.execute(query, values)
                
                action = "updated"
            else:
                # Create new service
                columns = ", ".join(service_data.keys())
                placeholders = ", ".join(["%s"] * len(service_data))
                
                cursor.execute(
                    f"""
                    INSERT INTO service ({columns})
                    VALUES ({placeholders})
                    """,
                    list(service_data.values())
                )
                service_id = cursor.lastrowid
                action = "created"
            
            # Get the created/updated service
            cursor.execute(
                """
                SELECT 
                    service_id, name, description, duration_minutes, 
                    price, buffer_before_minutes, buffer_after_minutes, is_active
                FROM service 
                WHERE service_id = %s
                """,
                (service_id,)
            )

            # Get the column names from the cursor
            column_names = cursor.column_names

            # Fetch one row of results
            row_data = cursor.fetchone()

            # Create an empty dictionary to store the result
            service = {}

            # Pair each column name with its corresponding value and add to the dictionary
            for i, column_name in enumerate(column_names):
                service[column_name] =row_data[column_name]
            
            # Convert decimal to float for JSON serialization
            if 'price' in service and service['price'] is not None:
                service['price'] = float(service['price'])
            
            return jsonify({
                "status": "success",
                "message": f"Service {action} successfully",
                "service": service
            })
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/working-hours', methods=['POST'])
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
                
                # Query business phones
                query = """
                    SELECT 
                        business_phone_id,
                        business_id,
                        phone_sid,
                        friendly_name,
                        business_phone,
                        is_primary,
                        created_at,
                        updated_at
                    FROM business_phone
                    WHERE business_id = %s
                    ORDER BY is_primary DESC, created_at ASC
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
