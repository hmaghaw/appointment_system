import json

from flask import Blueprint, request, jsonify
from appointment_app.database import get_db_cursor
import mysql.connector
from appointment_app.services.ai_translate import AITranslate

bp = Blueprint('restaurant_translations', __name__, url_prefix='/api/translate')


def save_fields_translations(business_id: int, table_name: str, field: str, table_pk: str = 'id', language='ar') -> dict:
    """
    Get translations for restaurant items based on the provided parameters.

    Args:
        business_id (int): ID of the business.
        table_name (str): Name of the table to query.
        field (str): Field name to translate.
        table_pk (str): Primary key field name (default: 'id').

    Returns:
        dict: JSON response with the structure {
            "business_id": int,
            "table": str,
            "field": str,
            "values": [{"id": int, "value": str}, ...]
        }
    """


    try:
        with get_db_cursor(dictionary=True) as cursor:
            # Query to get all items that need translation
            query = f"""
                SELECT {table_pk} AS id, {field} AS value 
                FROM {table_name} 
                WHERE business_id = %s AND {field} IS NOT NULL
            """
            cursor.execute(query, (business_id,))
            results = cursor.fetchall()

            # Format the response
            response = {
                "business_id": business_id,
                "table": table_name,
                "field": field,
                "values": [{"id": row['id'], "value": row['value']} for row in results]
            }
            translated = translate(response, language)
            save_translation(translated)
            return translated

    except mysql.connector.Error as e:
        return {
            "error": f"Database error: {str(e)}"
        }, 500


def save_translation(translated_json):
    """
    Save translations to the restaurant_translation table.

    Args:
        translated_json (dict): Dictionary containing the translated values in the format:
            {
                "business_id": int,
                "table": str,
                "field": str,
                "language_code": str,
                "values": [
                    {"id": int, "value": str, "translation": str},
                    ...
                ]
            }

    Returns:
        dict: A dictionary containing the status and number of records updated
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            business_id = translated_json.get('business_id')
            table_name = translated_json.get('table')
            field_name = translated_json.get('field')
            language_code = translated_json.get('language_code', 'ar')

            # Prepare the insert query
            insert_query = """
                INSERT INTO restaurant_translation 
                    (business_id, table_name, record_id, field_name, language_code, value, translation)
                VALUES (%s, %s, %s, %s, %s, %s, %s) 
                ON DUPLICATE KEY UPDATE 
                    value = VALUES(value),
                    translation = VALUES(translation)
            """

            # Prepare batch insert data
            batch_data = []
            for item in translated_json.get('values', []):
                if all(k in item for k in ['id', 'value', 'translation']):
                    batch_data.append((
                        business_id,
                        table_name,
                        item['id'],
                        field_name,
                        language_code,
                        item['value'],
                        item['translation']
                    ))

            # Execute batch insert
            if batch_data:
                cursor.executemany(insert_query, batch_data)
                # The commit will be handled by the context manager
                return {"status": "success", "records_updated": len(batch_data)}

            return {"status": "success", "records_updated": 0}

    except mysql.connector.Error as e:
        # Log the error and re-raise
        print(f"Error saving translations: {str(e)}")
        raise

def translate(user_input, language='ar'):
    tran = AITranslate()
    system_prompt = """I will provide you with an input json like:
{
  "business_id":97,
  "field":"name",
  "table":"restaurant_item",
  "language_code":"%s"
  "values":[
    {
      "id":1106,
      "value":"Masrawy Grand Breakfast"
    },
    {
      "id":1107,
      "value":"Sweet Cleopatra"
    }
	]
}
and I want you to generate an output like this:
{
  "business_id":97,
  "field":"name",
  "table":"restaurant_item",
  "language_code":"ar"
  "values":[
    {
      "id":1106,
      "value":"Masrawy Grand Breakfast",
	  "translation":"افطار مصراوي الكبير"
    },
    {
      "id":1107,
      "value":"Sweet Cleopatra",
	  "translation":حلوى كليوباترا"
    }
	]
}""" % language

    result = tran.translate_json(system_prompt, json.dumps(user_input))
    return result

@bp.route('', methods=['POST'])
def get_restaurant_translations_endpoint():
    """
    Endpoint to translate all restaurant content for a business.

    Request Body (JSON):
        {
            "business_id": 97,       # Required: Business ID
            "language": "ar"         # Optional: Language code (default: 'ar')
        }

    Returns:
        JSON with success/error status and translation details
    """
    try:
        data = request.get_json()
        if not data or 'business_id' not in data:
            return jsonify({
                "status": "error",
                "message": "business_id is required"
            }), 400

        business_id = data['business_id']
        language = data.get('language', 'ar')

        # List of tables and fields to translate
        translation_tasks = [
            {"table": "restaurant_modifier", "field": "name", "pk": "modifier_id"},
            {"table": "restaurant_modifier_group", "field": "name", "pk": "modifier_group_id"},
            {"table": "restaurant_item_category", "field": "name", "pk": "item_category_id"},
            {"table": "restaurant_item_category", "field": "description", "pk": "item_category_id"},
            {"table": "restaurant_item", "field": "name", "pk": "item_id"},
            {"table": "restaurant_item", "field": "description", "pk": "item_id"}
        ]

        results = []
        for task in translation_tasks:
            try:
                result = save_fields_translations(
                    business_id=business_id,
                    table_name=task['table'],
                    field=task['field'],
                    table_pk=task['pk'],
                    language=language
                )
                results.append({
                    "table": task['table'],
                    "field": task['field'],
                    "success": True,
                    "items_processed": len(result.get('values', []))
                })
            except Exception as e:
                results.append({
                    "table": task['table'],
                    "field": task['field'],
                    "success": False,
                    "error": str(e)
                })

        # Count successful operations
        success_count = sum(1 for r in results if r.get('success'))
        total_items = sum(r.get('items_processed', 0) for r in results if r.get('success'))

        return jsonify({
            "status": "success",
            "message": f"Translation completed: {success_count}/{len(translation_tasks)} tasks successful",
            "total_items_translated": total_items,
            "details": results
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500