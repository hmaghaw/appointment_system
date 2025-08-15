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
    Reserve a premium number by setting taken = true
    
    Request body:
    {
        "phone_number": "+1234567890"  # The phone number to reserve
    }
    
    Returns: Success message with the reserved number details
    """
    data = request.get_json()
    
    if not data or 'phone_number' not in data:
        return jsonify({"success": False, "message": "Phone number is required"}), 400
    
    phone_number = data['phone_number']
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # First check if the number exists and is available
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
                
            if number['taken']:
                return jsonify({
                    "success": False,
                    "message": f"Premium number {phone_number} is already taken"
                }), 400
            
            # Reserve the number
            cursor.execute("""
                UPDATE premium_numbers 
                SET taken = TRUE, 
                    updated_at = NOW()
                WHERE phone_number = %s
            """, (phone_number,))
            
            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "message": "Failed to reserve the premium number"
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
                "message": "Premium number reserved successfully",
                "data": format_premium_number(updated_number, columns)
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
