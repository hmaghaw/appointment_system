from flask import Blueprint, request, jsonify
from appointment_app.database import get_db_connection
import json

prompt_bp = Blueprint('prompt', __name__)

def get_english_prompt(cursor, business_id):
    """Helper function to get English prompt content"""
    query = """
    SELECT 
        pst.section_type,
        COALESCE(psb.custom_content, pst.default_content) AS final_content
    FROM prompt_section_template pst
    LEFT JOIN prompt_section_for_business psb
        ON pst.template_section_id = psb.template_section_id
       AND psb.business_id = %s
    ORDER BY pst.section_order;
    """
    cursor.execute(query, (business_id,))
    return {row['section_type']: row['final_content'] for row in cursor.fetchall()}

@prompt_bp.route('/api/get_prompt', methods=['POST'])
def get_prompt():
    try:
        data = request.get_json()
        business_id = data.get('business_id')
        language = data.get('language', 'en').lower()
        
        if not business_id:
            return jsonify({"error": "business_id is required"}), 400
            
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                if language == 'en':
                    result = get_english_prompt(cursor, business_id)
                else:
                    # First try to get the requested language
                    query = """
                    SELECT 
                        pst.section_type,
                        COALESCE(ptt.translated_content, psb.custom_content, pst.default_content) AS final_content
                    FROM prompt_section_template pst
                    LEFT JOIN prompt_section_for_business psb
                        ON pst.template_section_id = psb.template_section_id
                       AND psb.business_id = %s
                    LEFT JOIN prompt_section_translation ptt
                        ON (
                            (ptt.reference_type = 'business' AND ptt.reference_id = psb.business_prompt_section_id)
                            OR (ptt.reference_type = 'template' AND ptt.reference_id = pst.template_section_id)
                        )
                       AND ptt.language_code = %s
                    ORDER BY pst.section_order;
                    """
                    cursor.execute(query, (business_id, language))
                    results = cursor.fetchall()
                    
                    # Check if we got any results with translations
                    if not results or all(not row['final_content'] for row in results):
                        # Fall back to English if no translations found
                        result = get_english_prompt(cursor, business_id)
                    else:
                        result = {row['section_type']: row['final_content'] for row in results}
            
            return jsonify({
                "status": "success",
                "data": result,
                "language_used": language if result and any(result.values()) else 'en'
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
