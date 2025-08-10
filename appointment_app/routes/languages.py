from flask import Blueprint, jsonify, request, current_app
from database import get_db_cursor, get_db_connection
import mysql.connector
import logging
from typing import Dict, List, Any, Tuple, Optional, Union
from functools import wraps

# Type aliases
BusinessVoicesResponse = List[Dict[str, Any]]

# Set up logging
logger = logging.getLogger(__name__)

def business_required(f):
    """Decorator to ensure business_id is provided and valid."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json(silent=True) or {}
        business_id = data.get('business_id')
        
        if not business_id:
            return jsonify({"error": "business_id is required"}), 400
            
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT business_id FROM business WHERE business_id = %s", (business_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Business not found"}), 404
                
        return f(*args, **kwargs)
    return decorated_function

bp = Blueprint('languages', __name__, url_prefix='/api')

def get_language_data() -> Dict[str, Any]:
    """
    Fetches language data including dialects and voices from the database.
    
    Returns:
        Dict containing language data in the format:
        {
            "ar": {
                "name": "Arabic",
                "dialects": {
                    "AE": {"name": "Gulf Arabic", "voices": ["Hala", "Zayd"]},
                    "SA": {"name": "Modern Standard Arabic", "voices": ["Hamed", "Zariyah"]}
                }
            },
            "en": {
                "name": "English",
                "dialects": {
                    "US": {"name": "American English", "voices": ["Salli", "Joey"]},
                    "GB": {"name": "British English", "voices": ["Emma", "Brian"]}
                }
            },
            ...
        }
    """
    result = {}
    
    try:
        with get_db_cursor(dictionary=True) as cursor:
            # First, get all languages with their full tags
            cursor.execute("""
                SELECT l.lang_code, l.language_name, ld.full_tag
                FROM language l
                LEFT JOIN (
                    SELECT language_id, MIN(full_tag) as full_tag
                    FROM language_dialect
                    GROUP BY language_id
                ) ld ON l.language_id = ld.language_id
                ORDER BY l.language_name
            """)
            
            # Initialize the result dictionary with language codes and names
            for lang in cursor.fetchall():
                result[lang['lang_code']] = {
                    'name': lang['language_name'],
                    'full_tag': lang['full_tag'] or f"{lang['lang_code']}",
                    'dialects': {}
                }
            
            # Get all dialects with their regions and language codes
            cursor.execute("""
                SELECT 
                    l.lang_code,
                    COALESCE(lr.region_code, '') as region_code,
                    COALESCE(lr.region_name, '') as region_name,
                    ld.dialect_name,
                    ld.tag_code
                FROM language_dialect ld
                JOIN language l ON ld.language_id = l.language_id
                LEFT JOIN language_region lr ON ld.region_id = lr.region_id
                ORDER BY l.lang_code, COALESCE(lr.region_code, ''), ld.dialect_name
            """)
            
            # Add dialects to their respective languages
            for dialect in cursor.fetchall():
                lang_code = dialect['lang_code']
                region_code = dialect['region_code'] or 'default'  # Use 'default' if no region code
                
                if lang_code in result:
                    if region_code not in result[lang_code]['dialects']:
                        result[lang_code]['dialects'][region_code] = {
                            'name': dialect['dialect_name'] or f"{result[lang_code]['name']} ({region_code})",
                            'voices': []
                        }
            
            # Get all voices with their dialects and providers
            cursor.execute("""
                SELECT 
                    l.lang_code,
                    COALESCE(lr.region_code, '') as region_code,
                    lv.voice_name,
                    vp.provider_name,
                    lv.is_neural
                FROM language_voice lv
                JOIN language_dialect ld ON lv.dialect_id = ld.dialect_id
                JOIN language l ON ld.language_id = l.language_id
                LEFT JOIN language_region lr ON ld.region_id = lr.region_id
                JOIN voice_provider vp ON lv.provider_id = vp.provider_id
                ORDER BY l.lang_code, COALESCE(lr.region_code, ''), lv.voice_name
            """)
            
            # Add voices to their respective dialects
            voices = cursor.fetchall()
            print(f"Found {len(voices)} voices in the database")  # Debug log
            
            for voice in voices:
                lang_code = voice['lang_code']
                region_code = voice['region_code'] or 'default'  # Use 'default' if no region code
                voice_name = voice['voice_name']
                print(f"Processing voice: {voice_name} for {lang_code} ({region_code})")  # Debug log
                
                if lang_code in result and region_code in result[lang_code]['dialects']:
                    # Add the voice if it's not already in the list
                    if voice_name not in result[lang_code]['dialects'][region_code]['voices']:
                        print(f"Adding voice: {voice_name} to {lang_code} ({region_code})")  # Debug log
                        result[lang_code]['dialects'][region_code]['voices'].append(voice_name)
            
            # Remove languages with no dialects
            result = {k: v for k, v in result.items() if v['dialects']}
            
            # Sort voices alphabetically within each dialect
            for lang_data in result.values():
                for dialect in lang_data['dialects'].values():
                    dialect['voices'].sort()
            
            return result
            
    except mysql.connector.Error as e:
        print(f"Database error in get_language_data: {e}")
        raise

@bp.route('/business/set_default_language', methods=['POST'])
@business_required
def set_default_language():
    """
    Set a language as default for a business.
    
    Request Body:
        {
            "business_id": 32,
            "language_code": "fr"
        }
        
    Returns:
        JSON response with success or error message
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    business_id = data.get('business_id')
    language_code = data.get('language_code')
    
    logger.info(f"Received request to set default language. Business ID: {business_id}, Language: {language_code}")
    
    if not language_code:
        return jsonify({"error": "language_code is required"}), 400
        
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Check if the language exists for this business
                cursor.execute("""
                    SELECT 1 FROM business_languages 
                    WHERE business_id = %s AND language_code = %s
                """, (business_id, language_code))
                
                if not cursor.fetchone():
                    return jsonify({
                        "error": f"Language '{language_code}' not found for this business"
                    }), 404
                
                try:
                    # Start transaction if not already in one
                    if not conn.in_transaction:
                        conn.start_transaction()
                    
                    # Set all languages to not default for this business
                    cursor.execute("""
                        UPDATE business_languages 
                        SET is_default = FALSE 
                        WHERE business_id = %s
                    """, (business_id,))
                    
                    # Set the specified language as default
                    cursor.execute("""
                        UPDATE business_languages 
                        SET is_default = TRUE 
                        WHERE business_id = %s AND language_code = %s
                    """, (business_id, language_code))
                    
                    # Verify the update
                    cursor.execute("""
                        SELECT COUNT(*) as updated 
                        FROM business_languages 
                        WHERE business_id = %s AND language_code = %s AND is_default = TRUE
                    """, (business_id, language_code))
                    
                    updated = cursor.fetchone()['updated']
                    
                    if updated == 0:
                        if conn.in_transaction:
                            conn.rollback()
                        return jsonify({"error": "Failed to set default language"}), 500
                        
                    if conn.in_transaction:
                        conn.commit()
                    return jsonify({
                        "message": f"Successfully set '{language_code}' as default language"
                    })
                    
                except Exception as e:
                    if conn.in_transaction:
                        try:
                            conn.rollback()
                        except:
                            pass  # Ignore rollback errors
                    logger.error(f"Error in set_default_language transaction: {str(e)}", exc_info=True)
                    return jsonify({"error": f"Failed to update default language: {str(e)}"}), 500
                
    except mysql.connector.Error as e:
        logger.error(f"Database error in set_default_language: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in set_default_language: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to set default language: {str(e)}"}), 500

@bp.route('/business/language_voices', methods=['POST'])
@business_required
def get_business_language_voices() -> tuple[jsonify, int]:
    """
    Get all language voices for a business.
    
    Request Body:
        {
            "business_id": 22
        }
        
    Returns:
        JSON response with list of language voices for the business
        [
            {
                "language_voice_id": 11,
                "voice_name": "poly.kjhjh",
                "language_code": "en",
                "region_code": "US",
                "voice_provider": "aws",
                "is_default": true
            },
            ...
        ]
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    business_id = data.get('business_id')
    
    if not business_id:
        return jsonify({"error": "business_id is required"}), 400
    
    logger.info(f"Fetching language voices for business ID: {business_id}")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Get all language voices for the business's languages with language names
                cursor.execute("""
                    SELECT 
                        lv.language_voice_id,
                        lv.voice_name,
                        lv.language_code,
                        l.language_name,
                        lv.region_code,
                        lv.voice_provider,
                        lv.is_default
                    FROM language_voice lv
                    JOIN business_languages bl ON lv.language_code = bl.language_code
                    JOIN language l ON lv.language_code = l.language_code
                    WHERE bl.business_id = %s
                    ORDER BY 
                        lv.is_default DESC,
                        lv.language_code,
                        lv.region_code
                """, (business_id,))
                
                voices = cursor.fetchall()
                
                # Convert to the required response format
                result = [{
                    "language_voice_id": v["language_voice_id"],
                    "voice_name": v["voice_name"],
                    "language_code": v["language_code"],
                    "language_name": v["language_name"],
                    "region_code": v["region_code"],
                    "voice_provider": v["voice_provider"],
                    "is_default": bool(v["is_default"])
                } for v in voices]
                
                return jsonify(result)
                
    except mysql.connector.Error as e:
        logger.error(f"Database error in get_business_language_voices: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_business_language_voices: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to fetch language voices: {str(e)}"}), 500

@bp.route('/business/phone/language_voice', methods=['PUT'])
def update_business_phone_voice() -> tuple[jsonify, int]:
    """
    Update the language voice for a business phone.
    
    Request Body:
        {
            "business_phone_id": 32,
            "language_voice_id": 3
        }
        
    Returns:
        JSON response with success or error message
        {
            "message": "Successfully updated language voice for phone",
            "business_phone_id": 32,
            "language_voice_id": 3
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    business_phone_id = data.get('business_phone_id')
    language_voice_id = data.get('language_voice_id')
    
    if not business_phone_id or language_voice_id is None:
        return jsonify({"error": "Both business_phone_id and language_voice_id are required"}), 400
    
    logger.info(f"Updating language voice for business_phone_id: {business_phone_id} to language_voice_id: {language_voice_id}")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Check if the phone exists and get its business_id for verification
                cursor.execute(
                    "SELECT business_id FROM business_phone WHERE business_phone_id = %s",
                    (business_phone_id,)
                )
                phone = cursor.fetchone()
                
                if not phone:
                    return jsonify({"error": "Business phone not found"}), 404
                
                # If language_voice_id is provided, verify it exists
                if language_voice_id is not None:
                    cursor.execute(
                        "SELECT 1 FROM language_voice WHERE language_voice_id = %s",
                        (language_voice_id,)
                    )
                    if not cursor.fetchone():
                        return jsonify({"error": f"Language voice with ID {language_voice_id} not found"}), 404
                
                # Update the language_voice_id
                cursor.execute(
                    """
                    UPDATE business_phone 
                    SET language_voice_id = %s 
                    WHERE business_phone_id = %s
                    """,
                    (language_voice_id, business_phone_id)
                )
                
                if cursor.rowcount == 0:
                    return jsonify({"error": "No changes made or phone not found"}), 404
                
                conn.commit()
                
                return jsonify({
                    "message": "Successfully updated language voice for phone",
                    "business_phone_id": business_phone_id,
                    "language_voice_id": language_voice_id
                })
                
    except mysql.connector.Error as e:
        logger.error(f"Database error in update_business_phone_voice: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in update_business_phone_voice: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to update phone language voice: {str(e)}"}), 500

@bp.route('/list_supported_languages', methods=['GET'])
def list_supported_languages():
    """
    Get all supported languages from the language table.
    
    Returns:
        JSON response with list of supported languages and their codes
        {
            "languages": [
                {
                    "language_code": "en",
                    "language_name": "English"
                },
                ...
            ]
        }
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT language_code, language_name
                    FROM language 
                    ORDER BY language_name
                """)
                languages = cursor.fetchall()
                return jsonify({"languages": languages})
    except mysql.connector.Error as e:
        logger.error(f"Database error in list_supported_languages: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in list_supported_languages: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to fetch supported languages: {str(e)}"}), 500

@bp.route('/business/list_languages', methods=['POST'])
@business_required
def list_business_languages():
    """
    List all languages for a specific business.
    
    Request Body:
        {
            "business_id": 1
        }
        
    Returns:
        JSON response with list of languages for the business
    """
    try:
        data = request.get_json()
        business_id = data.get('business_id')
        if not business_id:
            return jsonify({"error": "business_id is required in request body"}), 400
            
        with get_db_cursor(dictionary=True) as cursor:
            # Check if business exists
            cursor.execute("SELECT business_id FROM business WHERE business_id = %s", (business_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Business not found"}), 404
                
            # Get all languages for the business
            cursor.execute("""
                SELECT bl.language_code, l.language_name, bl.is_default
                FROM business_languages bl
                JOIN language l ON bl.language_code = l.language_code
                WHERE bl.business_id = %s
                ORDER BY bl.is_default DESC, l.language_name
            """, (business_id,))
            
            languages = cursor.fetchall()
            return jsonify({"languages": languages})
            
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to fetch business languages: {str(e)}"}), 500

@bp.route('/business/language', methods=['POST'])
@business_required
def add_business_language():
    """
    Add a language to a business.
    
    Request Body:
        {
            "business_id": 1,
            "language_code": "ar"
        }
        
    Returns:
        JSON response with success or error message
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    business_id = data.get('business_id')
    language_code = data.get('language_code')
    
    logger.info(f"Received request to add language. Business ID: {business_id}, Language: {language_code}")
    
    if not language_code:
        return jsonify({"error": "language_code is required"}), 400
        
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Check if language exists in the system
                cursor.execute("SELECT language_code FROM language WHERE language_code = %s", (language_code,))
                if not cursor.fetchone():
                    return jsonify({"error": f"Language '{language_code}' is not supported"}), 400
                    
                # Check if business already has this language
                cursor.execute(
                    "SELECT 1 FROM business_languages WHERE business_id = %s AND language_code = %s",
                    (business_id, language_code)
                )
                if cursor.fetchone():
                    return jsonify({"error": f"Business already has language '{language_code}'"}), 400
                    
                # Check if this is the first language for the business
                cursor.execute(
                    "SELECT COUNT(*) as count FROM business_languages WHERE business_id = %s",
                    (business_id,)
                )
                count = cursor.fetchone()['count']
                is_default = count == 0  # First language will be default
                
                # Add the language
                cursor.execute("""
                    INSERT INTO business_languages (business_id, language_code, is_default)
                    VALUES (%s, %s, %s)
                """, (business_id, language_code, is_default))
                
                conn.commit()
                return jsonify({
                    "message": f"Language '{language_code}' added successfully",
                    "is_default": is_default
                }), 201
                
    except mysql.connector.Error as e:
        logger.error(f"Database error in add_business_language: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in add_business_language: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to add language: {str(e)}"}), 500

@bp.route('/business/language', methods=['DELETE'])
@business_required
def remove_business_language():
    """
    Remove a language from a business.
    
    Request Body:
        {
            "business_id": 1,
            "language_code": "ar"
        }
        
    Returns:
        JSON response with success or error message
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    business_id = data.get('business_id')
    language_code = data.get('language_code')
    
    logger.info(f"Received request to remove language. Business ID: {business_id}, Language: {language_code}")
    
    if not language_code:
        return jsonify({"error": "language_code is required"}), 400
        
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                logger.info(f"Checking languages for business {business_id}")
                # Check if this is the only language for the business
                cursor.execute("""
                    SELECT COUNT(*) as count, 
                           MAX(CASE WHEN language_code = %s THEN 1 ELSE 0 END) as is_current_language
                    FROM business_languages 
                    WHERE business_id = %s
                """, (language_code, business_id))
                
                result = cursor.fetchone()
                total_languages = result['count']
                is_current_language = result['is_current_language']
                
                if total_languages == 0 or not is_current_language:
                    return jsonify({"error": f"Language '{language_code}' not found for this business"}), 404
                    
                if total_languages == 1:
                    return jsonify({"error": "Cannot remove the only language for a business"}), 400
                    
                # Delete the language
                cursor.execute(
                    "DELETE FROM business_languages WHERE business_id = %s AND language_code = %s",
                    (business_id, language_code)
                )
                
                # If we deleted the default language, set another one as default
                if cursor.rowcount > 0:
                    cursor.execute("""
                        UPDATE business_languages 
                        SET is_default = TRUE 
                        WHERE business_id = %s 
                        ORDER BY language_code = 'en' DESC, language_code
                        LIMIT 1
                    """, (business_id,))
                
                conn.commit()
                return jsonify({"message": f"Language '{language_code}' removed successfully"})
                
    except mysql.connector.Error as e:
        logger.error(f"Database error in remove_business_language: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in remove_business_language: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to remove language: {str(e)}"}), 500
