from flask import Blueprint, request, jsonify
from appointment_app.database import get_db_cursor
import mysql.connector

# Create blueprint
bp = Blueprint('premium_numbers', __name__)

def format_premium_number(row, columns):
    """Helper function to format premium number data"""
    number = {}
    for i, value in enumerate(row):
        col_name = columns[i]
        # Convert datetime objects to ISO format strings
        if hasattr(value, 'isoformat'):
            number[col_name] = value.isoformat()
        else:
            number[col_name] = value
    return number

@bp.route('/premium-numbers', methods=['GET'])
def list_premium_numbers():
    """
    List all available premium numbers (where taken = false)
    
    Returns: List of available premium numbers with their details
    """
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT _id, phone_number, phone_sid, price, taken, 
                       created_at, updated_at
                FROM premium_numbers
                WHERE taken = FALSE
                ORDER BY price ASC
            """)
            
            numbers = cursor.fetchall()
            
            # Format datetime fields to ISO format strings
            for number in numbers:
                for key, value in number.items():
                    if hasattr(value, 'isoformat'):
                        number[key] = value.isoformat()
            
            return jsonify({
                "success": True,
                "count": len(numbers),
                "data": numbers
            })
            
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": str(err)}), 500

@bp.route('/premium-numbers/reserve', methods=['POST'])
def reserve_premium_number():
    """
    Reserve a premium number and add it to business_phone
    
    Request body:
    {
        "phone_number": "+1234567890",  # The phone number to reserve
        "business_id": 123,            # ID of the business to assign the number to
        "friendly_name": "Main Line"   # User-friendly name for the phone number
    }
    
    Returns: Success message with the reserved number and business_phone details
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['phone_number', 'business_id']
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    
    if missing_fields:
        return jsonify({
            "success": False, 
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    phone_number = data['phone_number']
    business_id = data['business_id']
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # Start transaction
            cursor.execute("START TRANSACTION")
            
            # First check if the number exists and is available
            cursor.execute("""
                SELECT * FROM premium_numbers 
                WHERE phone_number = %s
                FOR UPDATE
            """, (phone_number,))
            
            number = cursor.fetchone()
            
            if not number:
                cursor.execute("ROLLBACK")
                return jsonify({
                    "success": False,
                    "message": f"Premium number {phone_number} not found"
                }), 404
                
            if number['taken']:
                cursor.execute("ROLLBACK")
                return jsonify({
                    "success": False,
                    "message": f"Premium number {phone_number} is already taken"
                }), 400
                
            # Check if business exists
            cursor.execute("""
                SELECT business_id FROM business WHERE business_id = %s
            """, (business_id,))
            
            if not cursor.fetchone():
                cursor.execute("ROLLBACK")
                return jsonify({
                    "success": False,
                    "message": f"Business with ID {business_id} not found"
                }), 404
            
            # Reserve the number
            cursor.execute("""
                UPDATE premium_numbers 
                SET taken = TRUE, 
                    updated_at = NOW()
                WHERE phone_number = %s
            """, (phone_number,))
            
            if cursor.rowcount == 0:
                cursor.execute("ROLLBACK")
                return jsonify({
                    "success": False,
                    "message": "Failed to reserve the premium number"
                }), 500
                
            # Add to business_phone table with explicit collation
            cursor.execute("""
                INSERT INTO business_phone 
                (business_id, phone_sid, business_phone, is_primary, created_at, updated_at)
                VALUES (%s, %s, %s COLLATE utf8mb4_unicode_ci, 0, NOW(), NOW())
            """, (
                business_id,
                number['phone_sid'],
                phone_number
            ))
            
            if cursor.rowcount == 0:
                cursor.execute("ROLLBACK")
                return jsonify({
                    "success": False,
                    "message": "Failed to add phone number to business"
                }), 500
                
            # Get the updated number details with explicit collation
            cursor.execute("""
                SELECT pn._id, pn.phone_number, pn.phone_sid, pn.price, pn.taken, 
                       pn.created_at, pn.updated_at,
                       bp.business_phone_id, bp.business_id, bp.friendly_name as business_friendly_name,
                       bp.is_primary, bp.created_at as assigned_at
                FROM premium_numbers pn
                LEFT JOIN business_phone bp ON pn.phone_number = bp.business_phone COLLATE utf8mb4_unicode_ci
                WHERE pn.phone_number = %s
            """, (phone_number,))
            
            result = cursor.fetchone()
            
            # Commit transaction
            cursor.execute("COMMIT")
            
            return jsonify({
                "success": True,
                "message": "Premium number reserved and added to business successfully",
                "data": dict(result) if result else None
            })
            
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": str(err)}), 500

@bp.route('/premium-numbers/release', methods=['POST'])
def release_premium_number():
    """
    Release a premium number by setting taken = false
    
    Request body:
    {
        "phone_number": "+1234567890"  # The phone number to release
    }
    
    Returns: Success message with the released number details
    """
    data = request.get_json()
    
    if not data or 'phone_number' not in data:
        return jsonify({"success": False, "message": "Phone number is required"}), 400
    
    phone_number = data['phone_number']
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # First check if the number exists and is taken
            cursor.execute("""
                SELECT * FROM premium_numbers 
                WHERE phone_number = %s
                FOR UPDATE
            """, (phone_number,))
            
            number = cursor.fetchone()
            
            if not number:
                return jsonify({
                    "success": False,
                    "message": f"Premium number {phone_number} not found"
                }), 404
                
            if not number['taken']:
                return jsonify({
                    "success": False,
                    "message": f"Premium number {phone_number} is not currently taken"
                }), 400
            
            # Release the number
            cursor.execute("""
                UPDATE premium_numbers 
                SET taken = FALSE, 
                    updated_at = NOW()
                WHERE phone_number = %s
            """, (phone_number,))
            
            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "message": "Failed to release the premium number"
                }), 500
            
            # Get the updated number details
            cursor.execute("""
                SELECT _id, phone_number, phone_sid, price, taken, created_at, updated_at
                FROM premium_numbers
                WHERE phone_number = %s
            """, (phone_number,))
            
            updated_number = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            
            return jsonify({
                "success": True,
                "message": "Premium number released successfully",
                "data": format_premium_number(updated_number, columns)
            })
            
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": str(err)}), 500
