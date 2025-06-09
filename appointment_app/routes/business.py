from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from database import get_db_cursor

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
        JOIN business b ON bg.business_id = b.id
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
