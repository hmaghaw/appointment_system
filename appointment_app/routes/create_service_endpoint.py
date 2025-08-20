from flask import jsonify, request
import mysql.connector
from database import get_db_cursor
from functools import wraps
import logging
from ..services.ai_translate import AITranslate
from ..services.auth_token_validator import verify_bearer_token
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_service_translation(cursor, service_id, language_code, name, description):
    """
    Inserts a service translation record.
    Assumes the cursor is inside an open transaction.
    """

    translation_data = {
        'service_id': service_id,
        'language_code': language_code,
        'name': name,
        'description': description
    }

    cursor.execute("""
                   INSERT INTO service_translation
                       (service_id, language_code, name, description)
                   VALUES (%(service_id)s, %(language_code)s, %(name)s, %(description)s)
                   """, translation_data)

def insert_service_translations(cursor, business_id, service_id, language_code, name, description):
    trans = AITranslate()
    cursor.execute("""
                   select * from business_languages where business_id=%s
                   """, (business_id, ))

    result = cursor.fetchall()
    for row in result:
        if row['language_code']==language_code:
            insert_service_translation(
                cursor,
                service_id,
                language_code,
                name,
                description
            )
        else:
            from_lang = language_code
            to_lang = row['language_code']
            translated_name = trans.translate(from_lang, to_lang, name)
            translated_description = trans.translate(from_lang, to_lang, description)
            insert_service_translation(
                cursor,
                service_id,
                to_lang,
                translated_name,
                translated_description
            )

def create_service_blueprint(bp):
    """
    Create and return a blueprint with the create service endpoint
    This function is used to avoid circular imports
    """

    @bp.route('/create', methods=['POST'])
    @validate_business_id
    def create_service():
        """
        Create a new service with a specific language
        """
        payload, error = verify_bearer_token(request)
        if error:
            return jsonify({"error": error}), 401

        data = request.get_json() or {}

        required_fields = ['business_id', 'name', 'description', 'duration_minutes', 'language']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("START TRANSACTION")

                try:
                    # 1. Create the base service
                    service_data = {
                        'business_id': data['business_id'],
                        'name': data['name'],
                        'description': data['description'],
                        'duration_minutes': data['duration_minutes'],
                        'price': data.get('price'),
                        'buffer_before_minutes': data.get('buffer_before_minutes', 0),
                        'buffer_after_minutes': data.get('buffer_after_minutes', 0),
                        'is_active': data.get('is_active', True)
                    }

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

                    # 2. Create the translation record (via helper function)
                    insert_service_translations(
                        cursor,
                        data['business_id'],
                        service_id,
                        data['language'],
                        data['name'],
                        data['description']
                    )

                    cursor.execute("COMMIT")

                    # Retrieve the created service with its translation
                    cursor.execute("""
                                   SELECT s.*,
                                          st.language_code,
                                          st.name        as translated_name,
                                          st.description as translated_description
                                   FROM service s
                                            LEFT JOIN service_translation st
                                                      ON s.service_id = st.service_id
                                   WHERE s.service_id = %s
                                     AND st.language_code = %s
                                   """, (service_id, data['language']))

                    result = cursor.fetchone()
                    if not result:
                        return jsonify({"error": "Failed to retrieve created service"}), 500

                    service = {}
                    for key, value in result.items():
                        if key == 'price' and value is not None:
                            service[key] = float(value)
                        elif key in ['created_at', 'updated_at'] and value is not None:
                            service[key] = value.isoformat()
                        else:
                            service[key] = value

                    return jsonify({
                        "status": "success",
                        "message": "Service created successfully",
                        "service": service
                    })

                except mysql.connector.Error as err:
                    cursor.execute("ROLLBACK")
                    logger.error(f"Database error in create_service: {str(err)}", exc_info=True)
                    return jsonify({"error": f"Database error: {str(err)}"}), 500
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    logger.error(f"Error in create_service: {str(e)}", exc_info=True)
                    return jsonify({"error": f"Failed to create service: {str(e)}"}), 500

        except Exception as e:
            logger.error(f"Unexpected error in create_service: {str(e)}", exc_info=True)
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    return bp


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
