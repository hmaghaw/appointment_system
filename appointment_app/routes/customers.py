from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional, List
from appointment_app.database import get_db_cursor
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import re
from ..services.auth_token_validator import verify_bearer_token

bp = Blueprint('customers', __name__, url_prefix='/api/customers')

def get_customers_by_business(business_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all customers for a specific business
    
    Args:
        business_id: The ID of the business to get customers for
        
    Returns:
        List of customer dictionaries with their details
    """
    print(f"[get_customers_by_business] Fetching customers for business_id: {business_id}")
    
    if not isinstance(business_id, int) or business_id <= 0:
        print(f"[get_customers_by_business] Invalid business_id: {business_id}")
        return []
        
    try:
        with get_db_cursor(dictionary=True) as cursor:
            # First verify the business exists
            cursor.execute("SELECT 1 FROM business WHERE business_id = %s", (business_id,))
            if not cursor.fetchone():
                print(f"[get_customers_by_business] Business with ID {business_id} not found")
                return []
                
            query = """
                SELECT 
                    customer_id,
                    business_id,
                    customer_phone,
                    first_name,
                    last_name,
                    email,
                    language,
                    notes,
                    is_active,
                    created_at,
                    updated_at
                FROM customer
                WHERE business_id = %s
                ORDER BY first_name, last_name, customer_id
            """
            print(f"[get_customers_by_business] Executing query: {query} with business_id: {business_id}")
            cursor.execute(query, (business_id,))
            customers = cursor.fetchall()
            print(f"[get_customers_by_business] Fetched {len(customers)} customers")
            
            # Convert datetime objects to ISO format for JSON serialization
            for customer in customers:
                for key, value in customer.items():
                    if isinstance(value, datetime):
                        customer[key] = value.isoformat()
            
            return customers
            
    except Error as e:
        error_msg = f"[get_customers_by_business] Database error: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"[get_customers_by_business] Unexpected error: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

def get_customer_by_id(customer_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve customer information by customer_id
    
    Args:
        customer_id: The ID of the customer to retrieve
        
    Returns:
        Dictionary containing customer information if found, None otherwise or on error
    """
    if not isinstance(customer_id, int) or customer_id <= 0:
        return None
        
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT * FROM customer 
                WHERE customer_id = %s
            """, (customer_id,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error fetching customer: {e}")
        return None

@bp.route('/info', methods=['POST'])
def get_customer():
    """
    Get customer information by ID
    
    Request body should contain:
    {
        "customer_id": 1  // ID of the customer to retrieve
    }
    
    Returns:
        JSON with customer data if found, or error message
    """
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json()
    
    if not data or 'customer_id' not in data:
        return jsonify({"error": "Missing customer_id in request body"}), 400
        
    try:
        customer_id = int(data['customer_id'])
    except (ValueError, TypeError):
        return jsonify({"error": "customer_id must be an integer"}), 400
    
    customer = get_customer_by_id(customer_id)
    
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
        
    return jsonify({
        "success": True,
        "customer": customer
    })

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
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

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
    - customer_id: ID of the customer to update

    Request body may contain any of these fields to update:
    - first_name
    - last_name
    - email
    - customer_phone (must be unique per business)
    - notes
    - is_active
    - language: ISO 639-1 language code (e.g., 'en', 'ar', 'fr')

    Returns:
        JSON with success status, message, and updated customer data on success.
    """
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json()

    if not data or 'customer_id' not in data:
        return jsonify({"success": False, "message": "Customer ID is required"}), 400

    customer_id = data['customer_id']
    update_fields = []
    params = {'customer_id': customer_id}

    updatable_fields = ['first_name', 'last_name', 'email', 'customer_phone', 'notes', 'is_active', 'language']
    for field in updatable_fields:
        if field in data:
            update_fields.append(f"{field} = %({field})s")
            params[field] = data[field]

    if not update_fields:
        return jsonify({"success": False, "message": "No valid fields to update"}), 400

    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           SELECT *
                           FROM customer
                           WHERE customer_id = %(customer_id)s
                               FOR UPDATE
                           """, {'customer_id': customer_id})

            customer = cursor.fetchone()
            if not customer:
                return jsonify({"success": False, "message": "Customer not found"}), 404

            # Check for unique phone per business if updated
            if 'customer_phone' in data and data['customer_phone'] != customer['customer_phone']:
                cursor.execute("""
                               SELECT customer_id
                               FROM customer
                               WHERE business_id = %(business_id)s
                                 AND customer_phone = %(customer_phone)s
                                 AND customer_id != %(customer_id)s
                               """, {
                                   'business_id': customer['business_id'],
                                   'customer_phone': data['customer_phone'],
                                   'customer_id': customer_id
                               })
                if cursor.fetchone():
                    return jsonify({"success": False,
                                    "message": "A customer with this phone number already exists for this business"}), 409

            update_query = f"""
                UPDATE customer 
                SET {', '.join(update_fields)}, updated_at = NOW()
                WHERE customer_id = %(customer_id)s
            """

            cursor.execute(update_query, params)

            if cursor.rowcount == 0:
                return jsonify({"success": False, "message": "Failed to update customer"}), 500

            cursor.execute("""
                           SELECT *
                           FROM customer
                           WHERE customer_id = %s
                           """, (customer_id,))

            updated_customer = cursor.fetchone()
            if not updated_customer:
                return jsonify({"success": False, "message": "Failed to retrieve updated customer"}), 500

            return jsonify({
                "success": True,
                "message": "Customer updated successfully",
                "customer": updated_customer
            }), 200

    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": str(err)}), 400



@bp.route('/list', methods=['POST'])
def list_customers():
    """
    List all customers for a specific business
    
    Request body should contain:
    {
        "business_id": 111  // Required: ID of the business
    }
    
    Returns:
        JSON object containing:
        - customers: List of customer objects
        - total: Total number of customers for the business
    """
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json()
    
    if not data or 'business_id' not in data:
        return jsonify({"error": "business_id is required"}), 400
        
    try:
        business_id = int(data['business_id'])
        
        # Get all customers for the business
        customers = get_customers_by_business(business_id)
        
        # Get total count
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM customer WHERE business_id = %s", (business_id,))
            total = cursor.fetchone()['total']
        
        return jsonify({
            "customers": customers or [],
            "total": total
        })
        
    except ValueError:
        return jsonify({"error": "Invalid business_id, limit, or offset format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

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
                SELECT customer_id, first_name, last_name, email, language 
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
                    "first_name": "Guest",
                    "last_name": "",
                    "email": "",
                    "language": ""  # Default language for new customers
                }), 201
            else:
                # Return existing customer info
                return jsonify({
                    "customer_id": customer['customer_id'],
                    "first_name": customer['first_name'] or "Guest",
                    "last_name": customer['last_name'] or "",
                    "email": customer['email'] or "",
                    "language": customer.get('language', '')  # Return the customer's language, default to '' if not set
                }), 200
                
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@bp.route('', methods=['DELETE'])
def delete_customer():
    """
    Delete a customer by ID
    
    Request body should contain:
    {
        "customer_id": 24  // Required: ID of the customer to delete
    }
    
    Returns:
        JSON object with success status and message
        {
            "success": true/false,
            "message": "Customer deleted successfully" or error message
        }
    """
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json()
    
    if not data or 'customer_id' not in data:
        return jsonify({
            "success": False,
            "message": "customer_id is required in the request body"
        }), 400
    
    try:
        customer_id = int(data['customer_id'])
        if customer_id <= 0:
            raise ValueError("customer_id must be a positive integer")
            
        with get_db_cursor(commit=True) as cursor:
            # First check if customer exists
            cursor.execute(
                "SELECT customer_id FROM customer WHERE customer_id = %s",
                (customer_id,)
            )
            if not cursor.fetchone():
                return jsonify({
                    "success": False,
                    "message": f"Customer with ID {customer_id} not found"
                }), 404
            
            # Delete the customer
            cursor.execute(
                "DELETE FROM customer WHERE customer_id = %s",
                (customer_id,)
            )
            
            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "message": "No customer was deleted"
                }), 404
            
            return jsonify({
                "success": True,
                "message": f"Customer with ID {customer_id} has been deleted"
            }), 200
            
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"Invalid customer_id: {str(e)}"
        }), 400
    except mysql.connector.Error as e:
        # Handle foreign key constraint violations or other DB errors
        error_msg = str(e).lower()
        if "foreign key constraint" in error_msg:
            return jsonify({
                "success": False,
                "message": "Cannot delete customer because they have associated records (e.g., appointments). Please delete those first."
            }), 400
        return jsonify({
            "success": False,
            "message": f"Database error: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500
