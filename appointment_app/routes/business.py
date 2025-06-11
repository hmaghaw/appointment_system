from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import mysql.connector
from database import get_db_cursor
from functools import wraps

bp = Blueprint('business', __name__, url_prefix='/api/business')

@bp.route('/greeting', methods=['POST'])
def get_business_greeting():
    """
    Get greeting for a specific business
    
    Request body: {
        "business_id": 123  # ID of the business
    }
    """
    data = request.get_json() or {}
    business_id = data.get('business_id')
    
    if not business_id:
        return jsonify({"error": "business_id is required in the request body"}), 400
    query = """
        SELECT bg.*, b.name as business_name
        FROM business_greetings bg
        JOIN business b ON bg.business_id = b.business_id
        WHERE bg.business_id = %s AND bg.is_active = TRUE
        ORDER BY bg.created_at DESC
        LIMIT 1
    """
    
    with get_db_cursor() as cursor:
        cursor.execute(query, (business_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "No active greeting found for this business"}), 404
        
        # Convert row to dictionary
        columns = [col[0] for col in cursor.description]
        greeting = {}
        for i, value in enumerate(result):
            col_name = columns[i]
            if isinstance(value, (datetime, timedelta)):
                greeting[col_name] = value.isoformat()
            else:
                greeting[col_name] = result[col_name]
    
    return jsonify(greeting)

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
    List all active services for a business
    
    Request body: {
        "business_id": 1  # ID of the business
    }
    
    Returns: List of active services for the business
    """
    data = request.get_json()
    business_id = data['business_id']
    
    try:
        with get_db_cursor() as cursor:
            # Get all active services for the business
            cursor.execute("""
                SELECT 
                    service_id,
                    name,
                    description,
                    duration_minutes,
                    CAST(price AS FLOAT) as price,
                    buffer_before_minutes,
                    buffer_after_minutes,
                    created_at,
                    updated_at
                FROM service
                WHERE business_id = %s AND is_active = TRUE
                ORDER BY name
            """, (business_id,))
            
            services = []
            columns = [col[0] for col in cursor.description]
            
            for row in cursor.fetchall():
                service = {}
                for i, value in enumerate(row):
                    col_name = columns[i]
                    if isinstance(value, (datetime, timedelta)):
                        service[col_name] = value.isoformat()
                    else:
                        service[col_name] = row[col_name]
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
