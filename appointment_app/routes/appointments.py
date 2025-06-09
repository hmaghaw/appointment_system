from flask import Blueprint, request, jsonify
from database import get_db_cursor
import mysql.connector
from datetime import datetime, timedelta
from services.appointment_service import validate_appointment

# Create blueprint
bp = Blueprint('appointments', __name__)

def parse_datetime(dt_str):
    """Parse datetime string from various formats"""
    formats = [
        '%Y-%m-%dT%H:%M:%S',  # ISO format
        '%Y-%m-%d %H:%M:%S',  # SQL format
        '%Y-%m-%dT%H:%M',     # ISO without seconds
        '%Y-%m-%d %H:%M'      # SQL without seconds
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Time data '{dt_str}' does not match any supported format")

@bp.route('/api/appointments', methods=['GET'])
def get_appointments():
    """List all appointments"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT id, business_id, business_customer_id, service_id, 
                   start_time, end_time, status, created_at, updated_at
            FROM appointment
            ORDER BY start_time DESC
        """)
        appointments = cursor.fetchall()
        return jsonify(appointments)

@bp.route('/api/appointments', methods=['POST'])
def create_appointment():
    """
    Create a new appointment
    
    Request body should contain:
    - business_id: ID of the business
    - business_customer_id: ID of the customer at this business
    - service_id: ID of the service being booked
    - start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['business_id', 'business_customer_id', 'service_id', 'start_time']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Parse and validate times
        start_time = parse_datetime(data['start_time'])
        
        # Get service duration
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT duration_minutes FROM service 
                WHERE id = %s AND business_id = %s
            """, (data['service_id'], data['business_id']))
            service = cursor.fetchone()
            
            if not service:
                return jsonify({"error": "Service not found"}), 404
                
            # Calculate end time based on service duration
            end_time = start_time + timedelta(minutes=service['duration_minutes'])
            
        # Validate the appointment
        is_valid, error = validate_appointment(
            business_id=data['business_id'],
            service_id=data['service_id'],
            start_time=start_time,
            end_time=end_time
        )
        
        if not is_valid:
            return jsonify({"error": error}), 400
        
        # Create the appointment
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO appointment 
                (business_id, business_customer_id, service_id, start_time, end_time, status)
                VALUES (%(business_id)s, %(business_customer_id)s, %(service_id)s, 
                        %(start_time)s, %(end_time)s, 'scheduled')
            """, {
                'business_id': data['business_id'],
                'business_customer_id': data['business_customer_id'],
                'service_id': data['service_id'],
                'start_time': start_time,
                'end_time': end_time
            })
            
            appointment_id = cursor.lastrowid
            
            # Fetch the created appointment
            cursor.execute("""
                SELECT * FROM appointment WHERE id = %s
            """, (appointment_id,))
            appointment = cursor.fetchone()
            return jsonify(appointment), 201
            
    except ValueError as e:
        return jsonify({"error": f"Invalid date/time format: {str(e)}"}), 400
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
