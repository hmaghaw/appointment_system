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
    Search for appointments with filtering and language-specific service names
    
    Request Body (JSON):
    {
        "business_id": int,           # Optional: Filter by business ID
        "customer_id": int,           # Optional: Filter by customer ID within the business
        "start_date": "YYYY-MM-DD",   # Optional: Filter appointments after this date
        "end_date": "YYYY-MM-DD",     # Optional: Filter appointments before this date
        "status": "string",           # Optional: Filter by appointment status
        "language": "string"          # Optional: Language code for service names (default: 'en')
    }
    """
    # Get parameters from request body
    data = request.get_json() or {}
    
    # Extract parameters with defaults
    business_id = data.get('business_id')
    customer_id = data.get('customer_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    language = data.get('language', 'en')  # Default to English
    
    # Build the base query with language support for service names
    query = """
        SELECT a.appointment_id, a.business_id, a.customer_id, a.service_id, 
               a.start_time, a.end_time, a.status, a.created_at, a.updated_at,
               COALESCE(st.name, s.name) as service_name,
               CAST(COALESCE(st.description, s.description) AS CHAR) as service_description,
               CONCAT(c.first_name, ' ', c.last_name) as customer_name
        FROM appointment a
        LEFT JOIN service s ON a.service_id = s.service_id AND a.business_id = s.business_id
        LEFT JOIN service_translation st ON s.service_id = st.service_id 
            AND st.language_code = %s
        LEFT JOIN customer c ON a.customer_id = c.customer_id
        WHERE 1=1
    """
    params = [language]  # Add language as the first parameter
    
    # Add filters based on query parameters
    if business_id is not None:
        query += " AND a.business_id = %s"
        params.append(business_id)
        
    if customer_id is not None:
        query += " AND a.customer_id = %s"
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
    - customer_id: ID of the customer at this business
    - service_id: ID of the service being booked
    - start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['business_id', 'customer_id', 'service_id', 'start_time']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Parse and validate times
        start_time = parse_datetime(data['start_time'])
        
        # Get service duration
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT duration_minutes FROM service 
                WHERE service_id = %s AND business_id = %s
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
                (business_id, customer_id, service_id, start_time, end_time, status)
                VALUES (%(business_id)s, %(customer_id)s, %(service_id)s, 
                        %(start_time)s, %(end_time)s, 'scheduled')
            """, {
                'business_id': data['business_id'],
                'customer_id': data['customer_id'],
                'service_id': data['service_id'],
                'start_time': start_time,
                'end_time': end_time
            })
            
            appointment_id = cursor.lastrowid
            
            # Fetch the created appointment
            cursor.execute("""
                SELECT * FROM appointment WHERE appointment_id = %s
            """, (appointment_id,))
            appointment = cursor.fetchone()
            return jsonify(appointment), 201
            
    except ValueError as e:
        return jsonify({"error": f"Invalid date/time format: {str(e)}"}), 400
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400


@bp.route('/api/appointments', methods=['PUT'])
def update_appointment():
    data = request.get_json()

    if not data or 'appointment_id' not in data:
        return jsonify({"success": False, "message": "Appointment ID is required in the request body"}), 400

    appointment_id = data['appointment_id']

    if 'date' not in data or 'time' not in data:
        return jsonify({"success": False, "message": "Both 'date' and 'time' are required"}), 400

    try:
        # Validate date format strictly: YYYY-MM-DD
        date_str = data['date']
        datetime.strptime(date_str, "%Y-%m-%d")

        # Validate time format strictly: HH:MM (24-hour)
        time_str = data['time']
        datetime.strptime(time_str, "%H:%M")

        # Combine date and time into datetime object
        start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                SELECT * FROM appointment 
                WHERE appointment_id = %s
                    FOR UPDATE
            """, (appointment_id,))
            appointment = cursor.fetchone()

            if not appointment:
                return jsonify({"success": False, "message": "Appointment not found"}), 404

            service_id = appointment['service_id']

            cursor.execute("""
                SELECT duration_minutes FROM service 
                WHERE service_id = %s AND business_id = %s
            """, (service_id, appointment['business_id']))
            service = cursor.fetchone()

            if not service:
                return jsonify({"success": False, "message": "Service not found"}), 404

            end_time = start_time + timedelta(minutes=service['duration_minutes'])

            is_valid, error = validate_appointment(
                business_id=appointment['business_id'],
                service_id=service_id,
                start_time=start_time,
                end_time=end_time,
                exclude_appointment_id=appointment_id
            )

            if not is_valid:
                return jsonify({"success": False, "message": error}), 400

            update_query = """
                UPDATE appointment 
                SET start_time = %(start_time)s,
                    end_time = %(end_time)s,
                    status = 'scheduled',
                    updated_at = NOW()
                WHERE appointment_id = %(appointment_id)s
            """

            cursor.execute(update_query, {
                'start_time': start_time,
                'end_time': end_time,
                'appointment_id': appointment_id
            })

            if cursor.rowcount == 0:
                return jsonify({"success": False, "message": "Failed to Update Appointment"}), 500

            return jsonify({"success": True, "message": "Appointment Updated Successfully"}), 200

    except ValueError as e:
        return jsonify({"success": False, "message": f"Invalid date/time format: {str(e)}"}), 400
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": str(err)}), 400

@bp.route('/api/appointments', methods=['DELETE'])
def cancel_appointment():
    data = request.get_json()

    if not data or 'appointment_id' not in data:
        return jsonify({"success": False, "message": "Appointment ID is required in the request body"}), 400

    appointment_id = data['appointment_id']

    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if appointment exists
            cursor.execute("""
                SELECT * FROM appointment 
                WHERE appointment_id = %s
                FOR UPDATE
            """, (appointment_id,))
            appointment = cursor.fetchone()

            if not appointment:
                return jsonify({"success": False, "message": "Appointment not found"}), 404

            # Update appointment status to 'canceled'
            update_query = """
                UPDATE appointment 
                SET status = 'canceled',
                    updated_at = NOW()
                WHERE appointment_id = %s
            """
            cursor.execute(update_query, (appointment_id,))

            if cursor.rowcount == 0:
                return jsonify({"success": False, "message": "Failed to cancel Appointment"}), 500

            return jsonify({"success": True, "message": "Appointment canceled successfully"}), 200

    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": str(err)}), 400

@bp.route('/api/appointments/business', methods=['POST'])
def list_business_appointments():
    """
    List all appointments for a business with detailed customer and service information
    
    Request Body (JSON):
    {
        "business_id": 123,           # Required: ID of the business
        "start_date": "2025-07-01",   # Optional: Filter appointments on or after this date (YYYY-MM-DD)
        "end_date": "2025-07-31",     # Optional: Filter appointments on or before this date
        "status": "confirmed"         # Optional: Filter by status (e.g., 'scheduled', 'confirmed', 'completed', 'cancelled'). If not provided, returns appointments of all statuses.
    }
    """
    data = request.get_json() or {}
    
    # Validate required fields
    if 'business_id' not in data:
        return jsonify({"error": "business_id is required"}), 400
    
    # Extract parameters
    business_id = data['business_id']
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    status = data.get('status')
    
    # Build the query with detailed customer and service information
    query = """
        SELECT 
            a.appointment_id, 
            a.business_id, 
            a.customer_id, 
            a.service_id, 
            a.start_time, 
            a.end_time, 
            a.status, 
            a.created_at, 
            a.updated_at,
            a.notes,
            COALESCE(st.name, s.name) as service_name,
            CAST(COALESCE(st.description, s.description) AS CHAR) as service_description,
            c.first_name as customer_first_name,
            c.last_name as customer_last_name,
            CONCAT(c.first_name, ' ', c.last_name) as customer_full_name,
            c.email as customer_email
        FROM appointment a
        LEFT JOIN service s ON a.service_id = s.service_id AND a.business_id = s.business_id
        LEFT JOIN service_translation st ON s.service_id = st.service_id 
            AND st.language_code = 'en'  # Default to English for service names
        LEFT JOIN customer c ON a.customer_id = c.customer_id
        WHERE a.business_id = %s
    """
    params = [business_id]
    
    # Add date filters
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
    
    # Add status filter if provided
    if status:
        query += " AND a.status = %s"
        params.append(status)
    
    # Sort by start time (oldest first)
    query += " ORDER BY a.start_time ASC"
    
    with get_db_cursor() as cursor:
        cursor.execute(query, tuple(params))
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
                    appointment[col_name] = row[col_name]
            appointments.append(appointment)
        
        return jsonify(appointments)
