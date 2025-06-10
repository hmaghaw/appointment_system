from flask import Blueprint, request, jsonify
from database import get_db_cursor
import mysql.connector
from datetime import datetime
import re

bp = Blueprint('customers', __name__, url_prefix='/api/customers')

def validate_customer_data(data):
    """Validate customer data and return error message if invalid"""
    required_fields = ['business_id', 'first_name', 'last_name', 'customer_phone']
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
    - customer_phone: Customer's phone number (required, unique per business)
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
            cursor.execute("SELECT business_id FROM business WHERE business_id = %s", (data['business_id'],))
            if not cursor.fetchone():
                return jsonify({"error": "Business not found"}), 404
            
            # Check if phone number already exists for this business
            cursor.execute("""
                SELECT customer_id FROM customer 
                WHERE business_id = %s AND customer_phone = %s
            """, (data['business_id'], data['customer_phone']))
            
            if cursor.fetchone():
                return jsonify({"error": "A customer with this customer_phone already exists for this business"}), 409
            
            # Insert new customer
            cursor.execute("""
                INSERT INTO customer (
                    business_id, first_name, last_name, email, 
                    customer_phone, notes, created_at, updated_at
                ) VALUES (
                    %(business_id)s, %(first_name)s, %(last_name)s, %(email)s, 
                    %(customer_phone)s, %(notes)s, NOW(), NOW()
                )
            """, {
                'business_id': data['business_id'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data.get('email'),
                'customer_phone': data['customer_phone'],
                'notes': data.get('notes')
            })
            
            # Get the created customer
            customer_id = cursor.lastrowid
            cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
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
    - customer_phone: Customer's phone number (must be unique per business)
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
    updatable_fields = ['first_name', 'last_name', 'email', 'customer_phone', 'notes', 'is_active']
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
                WHERE customer_id = %(customer_id)s
                FOR UPDATE
            """, {'customer_id': customer_id})
            
            customer = cursor.fetchone()
            if not customer:
                return jsonify({"error": "Customer not found"}), 404
            
            # If phone number is being updated, check for duplicates
            if 'customer_phone' in data and data['customer_phone'] != customer['customer_phone']:
                cursor.execute("""
                    SELECT customer_id FROM customer 
                    WHERE business_id = %(business_id)s 
                    AND customer_phone = %(customer_phone)s
                    AND customer_id != %(customer_id)s
                """, {
                    'business_id': customer['business_id'],
                    'customer_phone': data['customer_phone'],
                    'customer_id': customer_id
                })
                
                if cursor.fetchone():
                    return jsonify({"error": "A customer with this customer_phone already exists for this business"}), 409
            
            # Update customer
            update_query = f"""
                UPDATE customer 
                SET {', '.join(update_fields)}, updated_at = NOW()
                WHERE customer_id = %(customer_id)s
            """
            
            cursor.execute(update_query, params)
            
            # Fetch the updated customer
            cursor.execute("""
                SELECT * FROM customer 
                WHERE customer_id = %s
            """, (customer_id,))
            
            updated_customer = cursor.fetchone()
            if not updated_customer:
                return jsonify({"error": "Failed to retrieve updated customer"}), 500
                
            return jsonify(updated_customer), 200
            
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

@bp.route('/upsert', methods=['POST'])
def upsert_customer():
    """
    Find or create a customer by phone number
    
    Request body should contain:
    - customer_phone: Customer's phone number (required)
    - business_phone: Business's phone number (required)
    - first_name: Customer's first name (optional, will be set to 'Guest' if not provided)
    - last_name: Customer's last name (optional, will be set to empty if not provided)
    - email: Customer's email (optional, will be set to empty if not provided)
    
    Returns:
        A JSON object with customer_id, name, and email
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'customer_phone' not in data or 'business_phone' not in data:
        return jsonify({"error": "customer_phone and business_phone are required"}), 400
    
    # Use phone numbers exactly as provided
    customer_phone = str(data['customer_phone']).strip()
    business_phone = str(data['business_phone']).strip()
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # First, try to find the business by phone
            cursor.execute("""
                SELECT b.business_id 
                FROM business b
                JOIN business_phone bp ON b.business_id = bp.business_id
                WHERE bp.business_phone = %s
            """, (business_phone,))
            business = cursor.fetchone()
            
            if not business:
                return jsonify({"error": "Business not found with the provided phone number"}), 404
            
            business_id = business['business_id']
            
            # Try to find the customer by phone and business
            cursor.execute("""
                SELECT customer_id, first_name, last_name, email 
                FROM customer 
                WHERE business_id = %s AND customer_phone = %s
            """, (business_id, customer_phone))
            
            customer = cursor.fetchone()
            
            if not customer:
                # Create new customer with just the phone number if not found
                cursor.execute("""
                    INSERT INTO customer (
                        business_id, customer_phone, first_name, last_name, email,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, 'Guest', '', '', NOW(), NOW()
                    )
                """, (business_id, customer_phone))
                
                customer_id = cursor.lastrowid
                
                # Return the newly created customer info with default values
                return jsonify({
                    "customer_id": customer_id,
                    "name": "Guest",
                    "email": ""
                }), 201
            else:
                # Return existing customer info
                full_name = f"{customer['first_name'] or ''} {customer['last_name'] or ''}".strip()
                return jsonify({
                    "customer_id": customer['customer_id'],
                    "name": full_name if full_name else "Guest",
                    "email": customer['email'] or ""
                }), 200
                
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
