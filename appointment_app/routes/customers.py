from flask import Blueprint, request, jsonify
from database import get_db_cursor
import mysql.connector
from datetime import datetime

bp = Blueprint('customers', __name__, url_prefix='/api/customers')

@bp.route('', methods=['POST'])
def create_customer():
    """
    Create a new customer
    
    Request body should contain:
    - business_id: ID of the business the customer belongs to
    - first_name: Customer's first name
    - last_name: Customer's last name
    - email: Customer's email (optional)
    - phone_number: Customer's phone number (required and must be unique per business)
    - notes: Additional notes (optional)
    
    Returns:
        The created customer object with ID
    """
    data = request.get_json()
    
    # Required fields
    required_fields = ['business_id', 'first_name', 'last_name', 'phone_number']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if business exists
            cursor.execute("SELECT id FROM business WHERE id = %s", (data['business_id'],))
            if not cursor.fetchone():
                return jsonify({"error": "Business not found"}), 404
            
            # First, check if customer with this phone number already exists
            cursor.execute("""
                SELECT id FROM customer 
                WHERE phone_number = %s
            """, (data['phone_number'],))
            
            customer_result = cursor.fetchone()
            
            if customer_result:
                # Customer exists, get their ID
                customer_id = customer_result['id']
                # Update customer info
                cursor.execute("""
                    UPDATE customer 
                    SET first_name = %(first_name)s,
                        last_name = %(last_name)s,
                        email = %(email)s,
                        updated_at = NOW()
                    WHERE id = %(customer_id)s
                """, {
                    'customer_id': customer_id,
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data.get('email')
                })
            else:
                # Insert new customer
                cursor.execute("""
                    INSERT INTO customer (
                        first_name, last_name, email, phone_number, created_at, updated_at
                    ) VALUES (
                        %(first_name)s, %(last_name)s, %(email)s, %(phone_number)s, NOW(), NOW()
                    )
                """, {
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data.get('email'),
                    'phone_number': data['phone_number']
                })
                customer_id = cursor.lastrowid
            
            # Check if this customer is already associated with this business
            cursor.execute("""
                SELECT id FROM business_customer 
                WHERE business_id = %(business_id)s AND customer_id = %(customer_id)s
            """, {
                'business_id': data['business_id'],
                'customer_id': customer_id
            })
            
            business_customer = cursor.fetchone()
            
            if business_customer:
                # Update existing business customer
                cursor.execute("""
                    UPDATE business_customer 
                    SET first_name = %(first_name)s,
                        last_name = %(last_name)s,
                        email = %(email)s,
                        phone_number = %(phone_number)s,
                        notes = %(notes)s,
                        updated_at = NOW()
                    WHERE id = %(id)s
                """, {
                    'id': business_customer['id'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data.get('email'),
                    'phone_number': data['phone_number'],
                    'notes': data.get('notes')
                })
                business_customer_id = business_customer['id']
            else:
                # Create new business customer
                cursor.execute("""
                    INSERT INTO business_customer (
                        business_id, customer_id, first_name, last_name, 
                        email, phone_number, notes, created_at, updated_at
                    ) VALUES (
                        %(business_id)s, %(customer_id)s, %(first_name)s, %(last_name)s, 
                        %(email)s, %(phone_number)s, %(notes)s, NOW(), NOW()
                    )
                """, {
                    'business_id': data['business_id'],
                    'customer_id': customer_id,
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data.get('email'),
                    'phone_number': data['phone_number'],
                    'notes': data.get('notes')
                })
                business_customer_id = cursor.lastrowid
            
            # Get the created/updated business customer
            cursor.execute("""
                SELECT * FROM business_customer 
                WHERE id = %s
            """, (business_customer_id,))
            
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
        The updated customer object
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
            # Check if customer exists
            cursor.execute("""
                SELECT id FROM business_customer 
                WHERE id = %(customer_id)s
                FOR UPDATE
            """, {'customer_id': customer_id})
            
            if not cursor.fetchone():
                return jsonify({"error": "Customer not found"}), 404
            
            # Update customer
            update_query = f"""
                UPDATE business_customer 
                SET {', '.join(update_fields)}, updated_at = NOW()
                WHERE id = %(customer_id)s
            """
            
            cursor.execute(update_query, params)
            
            # Fetch the updated customer
            cursor.execute("""
                SELECT * FROM business_customer 
                WHERE id = %s
            """, (customer_id,))
            
            updated_customer = cursor.fetchone()
            if not updated_customer:
                return jsonify({"error": "Failed to retrieve updated customer"}), 500
                
            return jsonify(updated_customer), 200
            
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
