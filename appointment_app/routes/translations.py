from flask import Blueprint, request, jsonify
from database import get_db_cursor
import mysql.connector

bp = Blueprint('translations', __name__, url_prefix='/api/translations')

def get_translation(phrase: str, language_code: str) -> str:
    """
    Get the translation of a phrase in the specified language.
    If the language is not found, returns the English translation.
    If the phrase is not found in any language, returns the original phrase.
    
    Args:
        phrase: The phrase to translate
        language_code: The target language code (e.g., 'en', 'ar')
        
    Returns:
        str: The translated phrase, English translation, or original phrase if not found
    """
    with get_db_cursor(dictionary=True) as cursor:
        try:
            # First try to get the translation in the requested language
            cursor.execute(
                """
                SELECT translated_phrase 
                FROM translations 
                WHERE phrase = %s AND language_code = %s
                """,
                (phrase, language_code)
            )
            result = cursor.fetchone()
            
            # If not found and not English, try English
            if not result and language_code != 'en':
                cursor.execute(
                    """
                    SELECT translated_phrase 
                    FROM translations 
                    WHERE phrase = %s AND language_code = 'en'
                    """,
                    (phrase,)
                )
                result = cursor.fetchone()
            
            # If still not found, return the original phrase
            return result['translated_phrase'] if result else phrase
            
        except mysql.connector.Error as e:
            print(f"Database error in get_translation: {e}")
            return phrase

@bp.route('', methods=['GET'])
def get_translation_endpoint():
    """
    Get translation for a phrase in the specified language.
    
    Query Parameters:
        phrase: The phrase to translate (required)
        language: The target language code (e.g., 'en', 'ar') (default: 'en')
        
    Returns:
        JSON with the translated phrase or original phrase if not found
    """
    phrase = request.args.get('phrase')
    language = request.args.get('language', 'en')
    
    if not phrase:
        return jsonify({"error": "Missing required parameter: phrase"}), 400
    
    translated_phrase = get_translation(phrase, language)
    
    return jsonify({
        "phrase": phrase,
        "language": language,
        "translated_phrase": translated_phrase
    })

@bp.route('', methods=['POST'])
def get_translation_post():
    """
    Get translation for a phrase in the specified language (POST version).
    
    Request Body (JSON):
        {
            "phrase": "Hello",
            "language": "ar"
        }
    
    Returns:
        JSON with the translated phrase or original phrase if not found
    """
    data = request.get_json()
    
    if not data or 'phrase' not in data:
        return jsonify({"error": "Missing required parameter: phrase"}), 400
    
    phrase = data['phrase']
    language = data.get('language', 'en')
    
    translated_phrase = get_translation(phrase, language)
    
    return jsonify({
        "phrase": phrase,
        "language": language,
        "translated_phrase": translated_phrase
    })
