from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import mysql.connector
from database import get_db_cursor
from functools import wraps
import logging
from typing import List, Dict, Any, Optional
from .create_service_endpoint import create_service_blueprint

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from appointment_app.services.ai_translate import Translate
    TRANSLATOR = Translate()
    logger.info("Translation service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize translation service: {str(e)}")
    TRANSLATOR = None

# Create a new Blueprint for service-related routes
bp = Blueprint('service', __name__)

# Register the create service endpoint
create_service_blueprint(bp)

def validate_business_id(f):
    """Decorator to validate business_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json() or {}
        business_id = data.get('business_id')
        if not business_id:
            return jsonify({"error": "business_id is required in the request body"}), 400
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/list', methods=['POST'])
@validate_business_id
def list_services():
    """
    List services for a business with optional language translation and active/inactive filtering
    
    Request body: {
        "business_id": 1,  # ID of the business
        "language": "en",  # Optional: Language code (defaults to 'en')
        "all": false       # Optional: If true, returns both active and inactive services
    }
    
    Returns: List of services for the business with translated content if available
    """
    data = request.get_json() or {}
    business_id = data['business_id']
    language = data.get('language', 'en')
    show_all = data.get('all', False)
    
    try:
        # Use a new connection to avoid unread results
        with get_db_cursor(commit=False) as cursor:
            # First, get the services with translations
            query = """
                SELECT 
                    s.service_id,
                    s.business_id,
                    COALESCE(st.name, s.name) as name,
                    COALESCE(st.description, s.description) as description,
                    s.duration_minutes,
                    s.price,
                    s.buffer_before_minutes,
                    s.buffer_after_minutes,
                    s.is_active,
                    s.created_at,
                    s.updated_at,
                    st.translation_id
                FROM service s
                LEFT JOIN (
                    SELECT service_id, translation_id, name, description 
                    FROM service_translation 
                    WHERE language_code = %s
                ) st ON s.service_id = st.service_id
                WHERE s.business_id = %s
            """
            
            # Add active filter if not showing all services
            if not show_all:
                query += " AND s.is_active = TRUE"
                
            # Add ordering
            query += " ORDER BY name"
            
            # Execute the query with parameters
            cursor.execute(query, (language, business_id))
            
            # Fetch all rows at once to avoid unread results
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            
            services = []
            for row in rows:
                # Convert row to dictionary
                service = {}
                for i, value in enumerate(row):
                    col_name = columns[i]
                    value = row[col_name]
                    
                    # Handle None values
                    if value is None:
                        service[col_name] = None
                        continue
                        
                    # Convert bytes to string if needed
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except UnicodeDecodeError:
                            value = str(value, 'latin-1')
                    # Convert decimal to float for JSON serialization
                    elif col_name == 'price':
                        try:
                            value = float(value)
                        except (TypeError, ValueError):
                            value = None
                    # Convert datetime/timedelta to ISO format
                    elif isinstance(value, (datetime, timedelta)):
                        value = value.isoformat()
                    
                    service[col_name] = value
                
                # Ensure is_active is a boolean
                if 'is_active' in service:
                    service['is_active'] = bool(service['is_active'])
                
                services.append(service)
            
            return jsonify({
                "business_id": business_id,
                "services": services,
                "count": len(services)
            })
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/translation', methods=['PUT'])
def update_service_translation():
    """
    Update a service translation by translation_id.

    Request body: {
        "translation_id": 54,         # Required: ID of the translation to update
        "name": "Updated Name",       # Optional: New name for the service in this language
        "description": "New desc"     # Optional: New description for the service in this language
    }

    Returns: Success message or error
    """
    data = request.get_json() or {}
    translation_id = data.get('translation_id')
    name = data.get('name')
    description = data.get('description')

    if not translation_id:
        return jsonify({"error": "translation_id is required"}), 400

    if not name and not description:
        return jsonify({"error": "At least one of 'name' or 'description' must be provided"}), 400

    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if translation exists
            cursor.execute(
                "SELECT translation_id FROM service_translation WHERE translation_id = %s",
                (translation_id,)
            )
            if not cursor.fetchone():
                return jsonify({"error": "Service translation not found"}), 404

            # Build dynamic SET clause
            fields = []
            values = []

            if name is not None:
                fields.append("name = %s")
                values.append(name)

            if description is not None:
                fields.append("description = %s")
                values.append(description)

            values.append(translation_id)  # For WHERE clause

            update_query = f"""
                UPDATE service_translation
                SET {', '.join(fields)}
                WHERE translation_id = %s
            """
            cursor.execute(update_query, tuple(values))

            return jsonify({
                "status": "success",
                "message": f"Service translation {translation_id} has been updated",
                "translation_id": translation_id
            })

    except mysql.connector.Error as err:
        error_msg = f"Database error: {str(err)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500

@bp.route('', methods=['DELETE'])
def delete_service():
    """
    Permanently delete a service by ID (hard delete)
    
    Request body: {
        "service_id": 1    # ID of the service to delete
    }
    
    Returns: Success message or error
    """
    data = request.get_json() or {}
    service_id = data.get('service_id')
    
    if not service_id:
        return jsonify({"error": "service_id is required"}), 400
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # First check if the service exists
            cursor.execute(
                "SELECT service_id FROM service WHERE service_id = %s",
                (service_id,)
            )
            if not cursor.fetchone():
                return jsonify({"error": "Service not found"}), 404
            
            # Perform hard delete
            cursor.execute(
                "DELETE FROM service WHERE service_id = %s",
                (service_id,)
            )
            # Perform hard delete
            cursor.execute(
                "DELETE FROM service_translation WHERE service_id = %s",
                (service_id,)
            )
            # Verify the service was deleted
            cursor.execute(
                "SELECT service_id FROM service WHERE service_id = %s",
                (service_id,)
            )
            if not cursor.fetchone():
                return jsonify({
                    "status": "success",
                    "message": f"Service {service_id} has been permanently deleted",
                    "service_id": service_id
                })
            else:
                return jsonify({
                    "error": "Failed to delete service",
                    "details": "The service record was not deleted as expected"
                }), 500
                
    except mysql.connector.Error as err:
        error_msg = f"Database error: {str(err)}"
        print(error_msg)  # Log the error for debugging
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)  # Log the error for debugging
        return jsonify({"error": error_msg}), 500

@bp.route('', methods=['POST', 'PUT'])
@validate_business_id
def upsert_service():
    """
    Create or update a service
    
    Request body: {
        "service_id": 1,              # Required for update, omit for create
        "business_id": 123,           # Required, validated by decorator
        "name": "Haircut",            # Required
        "description": "Basic haircut service",
        "duration_minutes": 30,       # Required
        "price": 25.00,
        "buffer_before_minutes": 5,
        "buffer_after_minutes": 5,
        "is_active": true             # Optional, defaults to true
    }
    
    Returns: The created/updated service
    """
    data = request.get_json() or {}
    business_id = data.get('business_id')
    service_id = data.get('service_id')
    
    # Validate required fields
    required_fields = ['name', 'duration_minutes']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    # Prepare service data
    service_data = {
        'business_id': business_id,
        'name': data['name'],
        'description': data.get('description', ''),
        'duration_minutes': data['duration_minutes'],
        'price': data.get('price'),
        'buffer_before_minutes': data.get('buffer_before_minutes', 0),
        'buffer_after_minutes': data.get('buffer_after_minutes', 0),
        'is_active': data.get('is_active', True) if service_id is None else data.get('is_active', True)
    }
    
    try:
        with get_db_cursor(commit=True) as cursor:
            if service_id:
                # Update existing service
                # First verify the service belongs to the business
                cursor.execute(
                    "SELECT service_id FROM service WHERE service_id = %s AND business_id = %s",
                    (service_id, business_id)
                )
                if not cursor.fetchone():
                    return jsonify({"error": "Service not found or access denied"}), 404
                
                # Build the update query
                set_clause = ", ".join([f"{k} = %s" for k in service_data.keys()])
                values = list(service_data.values()) + [service_id]
                
                # Build the query with parameter placeholders
                query = f"""
                    UPDATE service 
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE service_id = %s
                """
                
                # Execute with all parameters in the correct order
                cursor.execute(query, values)
                
                action = "updated"
            else:
                # Create new service
                columns = ", ".join(service_data.keys())
                placeholders = ", ".join(["%s"] * len(service_data))
                
                cursor.execute(
                    f"""
                    INSERT INTO service ({columns})
                    VALUES ({placeholders})
                    """,
                    list(service_data.values())
                )
                service_id = cursor.lastrowid
                action = "created"
            
            # Get the created/updated service
            cursor.execute(
                """
                SELECT 
                    service_id, name, description, duration_minutes, 
                    price, buffer_before_minutes, buffer_after_minutes, is_active
                FROM service 
                WHERE service_id = %s
                """,
                (service_id,)
            )

            # Get the column names from the cursor
            column_names = cursor.column_names

            # Fetch one row of results
            row_data = cursor.fetchone()

            # Create an empty dictionary to store the result
            service = {}

            # Pair each column name with its corresponding value and add to the dictionary
            for i, column_name in enumerate(column_names):
                service[column_name] = row_data[column_name]
            
            # Convert decimal to float for JSON serialization
            if 'price' in service and service['price'] is not None:
                service['price'] = float(service['price'])
            
            return jsonify({
                "status": "success",
                "message": f"Service {action} successfully",
                "service": service
            })
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
