from flask import Blueprint, request, jsonify
from database import get_db_cursor
from datetime import datetime, time, timedelta
import mysql.connector
from services.availability_service import get_daily_availability, get_weekly_availability
from ..services.auth_token_validator import verify_bearer_token
# Create blueprint
bp = Blueprint('availability', __name__)

@bp.route('/api/availability', methods=['POST'])
def check_availability():
    """Check available time slots for a service"""
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json()
    
    # Validate required fields
    required_fields = ['business_phone', 'service_id', 'date']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    business_phone = data['business_phone']
    service_id = data['service_id']
    date_str = data['date']
    view = data.get('view', 'day')
    
    # Validate view parameter
    if view not in ['day', 'week']:
        return jsonify({"error": "Invalid view parameter. Must be 'day' or 'week'"}), 400
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    
    try:
        if view == 'day':
            return get_daily_availability(business_phone, service_id, target_date)
        elif view == 'week':
            return get_weekly_availability(business_phone, service_id, target_date)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
