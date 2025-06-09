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

@bp.route('/api/appointments/search', methods=['POST'])
def search_appointments():
    """
    Search for appointments with filtering
    
    Request Body (JSON):
    {
        "business_id": int,           # Optional: Filter by business ID
        "business_customer_id": int,  # Optional: Filter by customer ID within the business
        "start_date": "YYYY-MM-DD",   # Optional: Filter appointments after this date
        "end_date": "YYYY-MM-DD",     # Optional: Filter appointments before this date
        "status": "string"            # Optional: Filter by appointment status
    }
    """
    # Get parameters from request body
    data = request.get_json() or {}
    
    # Extract parameters with defaults
    business_id = data.get('business_id')
    customer_id = data.get('business_customer_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    
    # Build the base query
    query = """
        SELECT a.id, a.business_id, a.business_customer_id, a.service_id, 
               a.start_time, a.end_time, a.status, a.created_at, a.updated_at,
               s.name as service_name,
               CONCAT(c.first_name, ' ', c.last_name) as customer_name
        FROM appointment a
        LEFT JOIN service s ON a.service_id = s.id AND a.business_id = s.business_id
        LEFT JOIN business_customer bc ON a.business_customer_id = bc.id AND a.business_id = bc.business_id
        LEFT JOIN customer c ON bc.customer_id = c.id
        WHERE 1=1
    """
    params = []
    
    # Add filters based on query parameters
    if business_id is not None:
        query += " AND a.business_id = %s"
        params.append(business_id)
        
    if customer_id is not None:
        query += " AND a.business_customer_id = %s"
        params.append(customer_id)
        
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query += " AND a.start_time >= %s"
            params.append(start_dt)
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
            
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query += " AND a.start_time < %s"
            params.append(end_dt)
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400
            
    if status:
        query += " AND a.status = %s"
        params.append(status)
    
    # Add sorting
    query += " ORDER BY a.start_time DESC"
    
    with get_db_cursor() as cursor:
        cursor.execute(query, tuple(params) if params else ())
        columns = [col[0] for col in cursor.description]
        appointments = []
        
        for row in cursor.fetchall():
            appointment = {}
            for i, value in enumerate(row):
                col_name = columns[i]
                if value is None:
                    appointment[col_name] = None
                    continue
                    
                if isinstance(value, (datetime, timedelta)):
                    if isinstance(value, timedelta):
                        # Convert timedelta to string (HH:MM:SS)
                        hours, remainder = divmod(value.seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        appointment[col_name] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        appointment[col_name] = value.isoformat()
                else:
                    appointment[col_name] = row[value]
            appointments.append(appointment)
        
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
