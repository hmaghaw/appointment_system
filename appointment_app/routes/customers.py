from flask import Blueprint, request, jsonify
from database import get_db_cursor
import mysql.connector
from datetime import datetime

bp = Blueprint('customers', __name__, url_prefix='/api/customers')

def validate_customer_data(data):
    """Validate customer data and return error message if invalid"""
    required_fields = ['business_id', 'first_name', 'last_name', 'phone_number']
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            return f"{field} is required"
    return None

@bp.route('', methods=['POST'])
def create_customer():
    """
    Create a new customer
    
    Request body should contain:
    - business_id: ID of the business the customer belongs to (required)
    - first_name: Customer's first name (required)
    - last_name: Customer's last name (required)
    - phone_number: Customer's phone number (required, unique per business)
    - email: Customer's email (optional)
    - notes: Additional notes (optional)
    
    Returns:
        The created customer object with ID or error message
    """
    data = request.get_json()
    
    # Validate required fields
    if error := validate_customer_data(data):
        return jsonify({"error": error}), 400
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if business exists
            cursor.execute("SELECT id FROM business WHERE id = %s", (data['business_id'],))
            if not cursor.fetchone():
                return jsonify({"error": "Business not found"}), 404
            
            # Check if phone number already exists for this business
            cursor.execute("""
                SELECT id FROM customer 
                WHERE business_id = %s AND phone_number = %s
            """, (data['business_id'], data['phone_number']))
            
            if cursor.fetchone():
                return jsonify({"error": "A customer with this phone number already exists for this business"}), 409
            
            # Insert new customer
            cursor.execute("""
                INSERT INTO customer (
                    business_id, first_name, last_name, email, 
                    phone_number, notes, created_at, updated_at
                ) VALUES (
                    %(business_id)s, %(first_name)s, %(last_name)s, %(email)s, 
                    %(phone_number)s, %(notes)s, NOW(), NOW()
                )
            """, {
                'business_id': data['business_id'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data.get('email'),
                'phone_number': data['phone_number'],
                'notes': data.get('notes')
            })
            
            # Get the created customer
            customer_id = cursor.lastrowid
            cursor.execute("SELECT * FROM customer WHERE id = %s", (customer_id,))
            customer = cursor.fetchone()
            
            return jsonify(customer), 201
            
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

@bp.route('', methods=['PUT'])
def update_customer():
    """
    Update an existing customer
    
    Request body must contain:
    - id: ID of the customer to update
    
    Request body may contain any of these fields to update:
    - first_name: Customer's first name
    - last_name: Customer's last name
    - email: Customer's email
    - phone_number: Customer's phone number (must be unique per business)
    - notes: Additional notes
    - is_active: Boolean indicating if customer is active
    
    Returns:
        The updated customer object or error message
    """
    data = request.get_json()
    
    if not data or 'id' not in data:
        return jsonify({"error": "Customer ID is required"}), 400
        
    customer_id = data['id']
    update_fields = []
    params = {'customer_id': customer_id}
    
    # Check which fields to update
    updatable_fields = ['first_name', 'last_name', 'email', 'phone_number', 'notes', 'is_active']
    for field in updatable_fields:
        if field in data:
            update_fields.append(f"{field} = %({field})s")
            params[field] = data[field]
    
    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if customer exists and get current data
            cursor.execute("""
                SELECT * FROM customer 
                WHERE id = %(customer_id)s
                FOR UPDATE
            """, {'customer_id': customer_id})
            
            customer = cursor.fetchone()
            if not customer:
                return jsonify({"error": "Customer not found"}), 404
            
            # If phone number is being updated, check for duplicates
            if 'phone_number' in data and data['phone_number'] != customer['phone_number']:
                cursor.execute("""
                    SELECT id FROM customer 
                    WHERE business_id = %(business_id)s 
                    AND phone_number = %(phone_number)s
                    AND id != %(customer_id)s
                """, {
                    'business_id': customer['business_id'],
                    'phone_number': data['phone_number'],
                    'customer_id': customer_id
                })
                
                if cursor.fetchone():
                    return jsonify({"error": "A customer with this phone number already exists for this business"}), 409
            
            # Update customer
            update_query = f"""
                UPDATE customer 
                SET {', '.join(update_fields)}, updated_at = NOW()
                WHERE id = %(customer_id)s
            """
            
            cursor.execute(update_query, params)
            
            # Fetch the updated customer
            cursor.execute("""
                SELECT * FROM customer 
                WHERE id = %s
            """, (customer_id,))
            
            updated_customer = cursor.fetchone()
            if not updated_customer:
                return jsonify({"error": "Failed to retrieve updated customer"}), 500
                
            return jsonify(updated_customer), 200
            
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
