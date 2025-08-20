from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import mysql.connector
from database import get_db_cursor
from functools import wraps
import logging
from typing import List, Dict, Any, Optional
from .create_service_endpoint import create_service_blueprint
from ..services.auth_token_validator import verify_bearer_token

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
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

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
            query += " ORDER BY s.business_id"
            
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
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

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
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

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

@bp.route('', methods=['PUT', 'OPTIONS'])
def update_service():
    """
    Update a service record by service_id.

    Request body example:
    {
        "service_id": 11,                 # Required
        "duration_minutes": 30,           # Optional
        "price": 100,                      # Optional
        "buffer_before_minutes": 10,      # Optional
        "is_active": true                  # Optional
    }

    Returns: Success message or error
    """
    if request.method == 'OPTIONS':
        return '', 200

    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json(silent=True) or {}
    service_id = data.get('service_id')
    duration_minutes = data.get('duration_minutes')
    price = data.get('price')
    buffer_before_minutes = data.get('buffer_before_minutes')
    is_active = data.get('is_active')

    if not service_id:
        return jsonify({"error": "service_id is required"}), 400

    if all(v is None for v in [duration_minutes, price, buffer_before_minutes, is_active]):
        return jsonify({"error": "At least one field to update must be provided"}), 400

    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if service exists
            cursor.execute(
                "SELECT service_id FROM service WHERE service_id = %s",
                (service_id,)
            )
            if not cursor.fetchone():
                return jsonify({"error": "Service not found"}), 404

            # Build dynamic SET clause
            fields, values = [], []
            if duration_minutes is not None:
                fields.append("duration_minutes = %s")
                values.append(duration_minutes)
            if price is not None:
                fields.append("price = %s")
                values.append(price)
            if buffer_before_minutes is not None:
                fields.append("buffer_before_minutes = %s")
                values.append(buffer_before_minutes)
            if is_active is not None:
                fields.append("is_active = %s")
                values.append(is_active)

            values.append(service_id)

            update_query = f"""
                UPDATE service
                SET {', '.join(fields)}
                WHERE service_id = %s
            """
            cursor.execute(update_query, tuple(values))

            return jsonify({
                "status": "success",
                "message": f"Service {service_id} has been updated",
                "service_id": service_id
            })

    except mysql.connector.Error as err:
        error_msg = f"Database error: {str(err)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500
