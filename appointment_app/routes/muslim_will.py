from flask import Blueprint, request, jsonify
from appointment_app.database import get_db_cursor
from appointment_app.services.auth_token_validator import verify_bearer_token
from mysql.connector import Error

bp = Blueprint('muslim_will', __name__, url_prefix='/api/muslimwill')

@bp.route('/get_customer_status', methods=['POST'])
def get_customer_status():
    """
    Get customer status from muslim_will_customer_status table
    
    Request body should contain:
    {
        "customer_phone": "+16478724666"
    }
    
    Returns:
        JSON with customer status data if found, or error message
    """
    # payload, error = verify_bearer_token(request)
    # if error:
    #     return jsonify({"error": error}), 401

    data = request.get_json()
    
    if not data or 'customer_phone' not in data:
        return jsonify({"error": "Missing customer_phone in request body"}), 400
        
    customer_phone = str(data['customer_phone']).strip()
    if not customer_phone:
        return jsonify({"error": "customer_phone cannot be empty"}), 400
    
    try:
        with get_db_cursor(dictionary=True) as cursor:

            # Get customer status from muslim_will_customer_status table
            cursor.execute("""
                SELECT id, customer_phone, current_status, next_step, timestamp
                FROM muslim_will_customer_status
                WHERE customer_phone = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (customer_phone,))
            
            status_record = cursor.fetchone()
            
            if not status_record:
                return jsonify({
                    "success": True,
                    "message": "No status record found for this customer",
                }), 200
            
            # Convert timestamp to ISO format if it's a datetime object
            if 'timestamp' in status_record and status_record['timestamp']:
                from datetime import datetime
                if isinstance(status_record['timestamp'], datetime):
                    status_record['timestamp'] = status_record['timestamp'].isoformat()
            
            return jsonify({
                "success": True,
                "customer_status": {
                    "current_status":status_record['current_status'],
                    "next_step":status_record['next_step'],
                }
            }), 200
            
    except Error as e:
        error_msg = f"Database error: {str(e)}"
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        return jsonify({"error": error_msg}), 500
