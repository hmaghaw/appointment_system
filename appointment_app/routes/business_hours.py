from flask import Blueprint, request, jsonify
from database import get_db_cursor
import mysql.connector
from datetime import datetime, time, timedelta
from flask import jsonify, request, Blueprint

DAY_NAMES = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
}
bp = Blueprint('business_hours', __name__)

def validate_business_hours(data):
    """Validate business hours data"""
    required_fields = ['business_id', 'day_of_week']
    if not all(field in data for field in required_fields):
        return False, "Missing required fields"
    
    day_of_week = data.get('day_of_week')
    if not isinstance(day_of_week, int) or day_of_week < 0 or day_of_week > 6:
        return False, "day_of_week must be an integer between 0 (Monday) and 6 (Sunday)"
    
    is_closed = data.get('is_closed', False)
    if not is_closed:
        if 'open_time' not in data or 'close_time' not in data:
            return False, "open_time and close_time are required when is_closed is False"
        
        try:
            if data['open_time'] and not isinstance(datetime.strptime(data['open_time'], '%H:%M:%S'), datetime.time):
                return False, "open_time must be in format HH:MM:SS"
            if data['close_time'] and not isinstance(datetime.strptime(data['close_time'], '%H:%M:%S'), datetime.time):
                return False, "close_time must be in format HH:MM:SS"
        except ValueError:
            return False, "Invalid time format. Use HH:MM:SS"
    
    return True, ""


@bp.route('/business-hours/get', methods=['POST'])
def get_business_hours():
    """
    Get all business hours for a business
    
    Request body:
    {
        "business_id": 1
    }
    
    Returns:
    {
        "success": true,
        "data": [
            {
                "business_hours_id": 1,
                "business_id": 1,
                "day_of_week": 0,
                "open_time": "09:00:00",
                "close_time": "17:00:00",
                "is_closed": false
            },
            ...
        ]
    }
    """
    data = request.get_json()
    
    if not data or 'business_id' not in data:
        return jsonify({"success": False, "error": "business_id is required in the request body"}), 400
    
    try:
        business_id = int(data['business_id'])  # Ensure business_id is an integer
        with get_db_cursor(dictionary=True) as cursor:  # Use dictionary cursor for easier handling
            query = """
                SELECT 
                    business_hours_id,
                    day_of_week,
                    TIME_FORMAT(open_time, '%H:%i') as open_time,
                    TIME_FORMAT(close_time, '%H:%i') as close_time,
                    is_closed
                FROM business_hours 
                WHERE business_id = %s
                ORDER BY day_of_week
            """
            cursor.execute(query, (business_id,))
            
            # Since we're using dictionary cursor, we can directly fetch all rows
            business_hours = []
            for row in cursor.fetchall():
                # Create a new dict with serializable values
                row['day_of_week']=DAY_NAMES[row['day_of_week']]
                hour_data = {}
                for key, value in row.items():
                    if value is None:
                        hour_data[key] = None
                    elif hasattr(value, 'isoformat'):
                        hour_data[key] = value.isoformat()
                    else:
                        hour_data[key] = value
                
                business_hours.append(hour_data)
            
            return jsonify({
                "business_id": business_id,
                "success": True, 
                "data": business_hours
            })
            
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {str(err)}"}), 500

@bp.route('/business-hours/update', methods=['POST'])
def update_business_hours():
    """
    Update existing business hours

    Request body:
    {
        "business_hours_id": 1,   # Required
        "open_time": "10:00:00",  # Optional
        "close_time": "18:00:00", # Optional
        "is_closed": false        # Optional
    }

    Rules:
    - If is_closed = true → open_time and close_time are set to NULL.
    - If is_closed = false → open_time and close_time must be provided or inferred from DB.
    - If is_closed is not provided, open_time/close_time can still be updated independently.
    """
    data = request.get_json()

    if not data or 'business_hours_id' not in data:
        return jsonify({"success": False, "error": "business_hours_id is required"}), 400

    business_hours_id = data['business_hours_id']

    try:
        with get_db_cursor(commit=True, dictionary=True) as cursor:
            # Fetch existing record
            cursor.execute("SELECT * FROM business_hours WHERE business_hours_id = %s", (business_hours_id,))
            existing = cursor.fetchone()
            if not existing:
                return jsonify({"success": False, "error": "Business hours not found"}), 404

            update_fields = []
            params = []

            if 'is_closed' in data:
                is_closed = data['is_closed']
                update_fields.append("is_closed = %s")
                params.append(is_closed)

                if is_closed:
                    update_fields.append("open_time = NULL")
                    update_fields.append("close_time = NULL")
                else:
                    open_time = data.get('open_time', existing['open_time'])
                    close_time = data.get('close_time', existing['close_time'])

                    if not open_time or not close_time:
                        return jsonify({
                            "success": False,
                            "error": "open_time and close_time are required when is_closed is false"
                        }), 400

                    update_fields.append("open_time = %s")
                    update_fields.append("close_time = %s")
                    params.extend([open_time, close_time])
            else:
                # Update only provided open_time/close_time if is_closed is not specified
                if 'open_time' in data:
                    update_fields.append("open_time = %s")
                    params.append(data['open_time'])
                if 'close_time' in data:
                    update_fields.append("close_time = %s")
                    params.append(data['close_time'])

            if not update_fields:
                return jsonify({"success": False, "error": "No updatable fields provided"}), 400

            params.append(business_hours_id)
            query = f"""
                UPDATE business_hours
                SET {', '.join(update_fields)}
                WHERE business_hours_id = %s
            """
            cursor.execute(query, tuple(params))

            # Return updated record
            cursor.execute("SELECT * FROM business_hours WHERE business_hours_id = %s", (business_hours_id,))
            updated = cursor.fetchone()

            updated_serialized = {k: serialize_value(v) for k, v in updated.items()}

            return jsonify({"success": True, "data": updated_serialized})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {str(err)}"}), 500
#
# @bp.route('/business-hours/create-weekly', methods=['POST'])
# def create_weekly_business_hours():
#     """
#     Create a full week's default business hours for a given business_id.
#
#     Request body:
#     {
#         "business_id": 1   # Required
#     }
#
#     Rules:
#     - Monday–Friday → open_time = "09:00:00", close_time = "17:00:00", is_closed = false
#     - Saturday & Sunday → open_time = NULL, close_time = NULL, is_closed = true
#     - Inserts 7 rows into business_hours (one per day)
#     """
#
#     data = request.get_json()
#     if not data or 'business_id' not in data:
#         return jsonify({"success": False, "error": "business_id is required"}), 400
#
#     business_id = data['business_id']
#
#     try:
#         default_hours = [
#             {"day_of_week": 0, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Monday
#             {"day_of_week": 1, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Tuesday
#             {"day_of_week": 2, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Wednesday
#             {"day_of_week": 3, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Thursday
#             {"day_of_week": 4, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": False},  # Friday
#             {"day_of_week": 5, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": True},
#             # Saturday (closed)
#             {"day_of_week": 6, "open_time": "09:00:00", "close_time": "17:00:00", "is_closed": True}  # Sunday (closed)
#         ]
#         with get_db_cursor(commit=True, dictionary=True) as cursor:
#             inserted = []
#             for entry in default_hours:
#                 cursor.execute("""
#                                INSERT INTO business_hours (business_id, day_of_week, open_time, close_time, is_closed)
#                                VALUES (%s, %s, %s, %s, %s)
#                                """, (
#                                    business_id,
#                                    entry["day_of_week"],
#                                    entry["open_time"] if not entry["is_closed"] else None,
#                                    entry["close_time"] if not entry["is_closed"] else None,
#                                    entry["is_closed"]
#                                ))
#
#                 inserted.append({
#                     "business_id": business_id,
#                     "day_of_week": entry["day_of_week"],
#                     "open_time": entry["open_time"] if not entry["is_closed"] else None,
#                     "close_time": entry["close_time"] if not entry["is_closed"] else None,
#                     "is_closed": entry["is_closed"]
#                 })
#
#             return jsonify({"success": True, "data": inserted}), 201
#
#     except mysql.connector.Error as err:
#         return jsonify({"success": False, "error": f"Database error: {str(err)}"}), 500

def serialize_value(v):
    if isinstance(v, (datetime, time, timedelta)):
        return str(v)
    return v
