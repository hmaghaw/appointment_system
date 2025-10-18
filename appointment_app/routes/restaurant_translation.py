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


@bp.route('/get_menu_by_language', methods=['POST'])
def get_menu_by_language():
    """
    Get the complete menu for a restaurant with translations, including modifiers and options.
    """
    try:
        data = request.get_json()
        if not data or 'business_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'business_id is required'
            }), 400

        business_id = data['business_id']
        language = data.get('language', 'ar')

        with get_db_cursor(dictionary=True) as cursor:
            # Get all active menu items with their categories
            cursor.execute("""
                           SELECT i.item_id,
                                  i.name,
                                  i.base_price,
                                  i.description,
                                  ic.item_category_id,
                                  ic.name as category_name
                           FROM restaurant_item i
                                    LEFT JOIN restaurant_item_category_map icm ON i.item_id = icm.item_id
                                    LEFT JOIN restaurant_item_category ic ON icm.item_category_id = ic.item_category_id
                           WHERE i.business_id = %s
                             AND i.is_active = 1
                           ORDER BY ic.name, i.name
                           """, (business_id,))
            items = cursor.fetchall()

            if not items:
                return jsonify({
                    'status': 'success',
                    'menu': []
                }), 200

            # Get all item IDs for fetching options and modifiers
            item_ids = [str(item['item_id']) for item in items]
            item_ids_placeholders = ','.join(['%s'] * len(item_ids))

            # Get all modifiers for the items
            cursor.execute(f"""
                SELECT 
                    img.item_id,
                    m.modifier_id,
                    m.name as modifier_name,
                    m.price_delta as modifier_price_delta,
                    m.is_active,
                    m.display_order,
                    mg.modifier_group_id,
                    mg.name as modifier_group_name,
                    mg.is_required as modifier_required
                FROM restaurant_item_modifier_group img
                JOIN restaurant_modifier_group mg ON img.modifier_group_id = mg.modifier_group_id
                JOIN restaurant_modifier m ON mg.modifier_group_id = m.modifier_group_id
                WHERE img.item_id IN ({item_ids_placeholders}) 
                AND m.is_active = 1
                ORDER BY img.item_id, m.display_order, m.name
            """, tuple(item_ids))
            all_modifiers = cursor.fetchall()

            # Get all options for the items
            cursor.execute(f"""
                SELECT 
                    iog.item_id,
                    o.option_id,
                    o.name as option_name,
                    o.price_delta as option_price_delta,
                    o.is_default,
                    o.display_order,
                    og.option_group_id,
                    og.name as option_group_name,
                    og.is_required as option_required
                FROM restaurant_item_option_group iog
                JOIN restaurant_option_group og ON iog.option_group_id = og.option_group_id
                JOIN restaurant_option o ON og.option_group_id = o.option_group_id
                WHERE iog.item_id IN ({item_ids_placeholders})
                ORDER BY iog.item_id, o.display_order, o.name
            """, tuple(item_ids))
            all_options = cursor.fetchall()

            # Get translations for all items, categories, modifiers, and options
            cursor.execute("""
                           SELECT table_name,
                                  record_id,
                                  field_name, translation
                           FROM restaurant_translation
                           WHERE business_id = %s
                             AND language_code = %s
                             AND (
                               (table_name = 'restaurant_item'
                             AND field_name IN ('name'
                               , 'description'))
                              OR (table_name = 'restaurant_item_category'
                             AND field_name = 'name')
                              OR (table_name = 'restaurant_modifier'
                             AND field_name = 'name')
                              OR (table_name = 'restaurant_modifier_group'
                             AND field_name = 'name')
                               )
                           """, (business_id, language))
            translations = cursor.fetchall()

            # Create a map for translations
            translation_map = {}
            for trans in translations:
                key = f"{trans['table_name']}_{trans['record_id']}_{trans['field_name']}"
                translation_map[key] = trans['translation']

            # Organize the data by category
            categories = {}
            for item in items:
                # Get translations for item name and description
                name_key = f"restaurant_item_{item['item_id']}_name"
                desc_key = f"restaurant_item_{item['item_id']}_description"
                category_name_key = f"restaurant_item_category_{item['item_category_id']}_name"

                # Apply translations if available
                translated_name = translation_map.get(name_key, item['name'])
                translated_desc = translation_map.get(desc_key, item.get('description', ''))
                translated_category = translation_map.get(category_name_key, item.get('category_name', 'Uncategorized'))

                if translated_category not in categories:
                    categories[translated_category] = []

                # Get modifiers for this item with translations
                item_modifiers = []
                for mod in [m for m in all_modifiers if m['item_id'] == item['item_id']]:
                    # Create translation keys
                    mod_name_key = f"restaurant_modifier_{mod['modifier_id']}_name"
                    mod_group_key = f"restaurant_modifier_group_{mod['modifier_group_id']}_name"

                    # Get translations
                    translated_mod_name = translation_map.get(mod_name_key, mod['modifier_name'])
                    translated_group_name = translation_map.get(mod_group_key, mod['modifier_group_name'])

                    item_modifiers.append({
                        'modifier_id': mod['modifier_id'],
                        'name': translated_mod_name,
                        'original_name': mod['modifier_name'],
                        'price_delta': float(mod['modifier_price_delta']) if mod[
                                                                                 'modifier_price_delta'] is not None else 0.00,
                        'is_active': bool(mod['is_active']),
                        'display_order': mod['display_order'],
                        'modifier_group_id': mod['modifier_group_id'],
                        'group_name': translated_group_name,
                        'original_group_name': mod['modifier_group_name'],
                        'is_required': bool(mod['modifier_required'])
                    })

                # Get options for this item with translations
                item_options = []
                for opt in [o for o in all_options if o['item_id'] == item['item_id']]:
                    # Create translation keys
                    opt_name_key = f"restaurant_option_{opt['option_id']}_name"
                    opt_group_key = f"restaurant_option_group_{opt['option_group_id']}_name"

                    # Get translations
                    translated_opt_name = translation_map.get(opt_name_key, opt['option_name'])
                    translated_opt_group = translation_map.get(opt_group_key, opt['option_group_name'])

                    item_options.append({
                        'option_id': opt['option_id'],
                        'name': translated_opt_name,
                        'original_name': opt['option_name'],
                        'price_delta': float(opt['option_price_delta']) if opt[
                                                                               'option_price_delta'] is not None else 0.00,
                        'is_default': bool(opt['is_default']),
                        'display_order': opt['display_order'],
                        'option_group_id': opt['option_group_id'],
                        'group_name': translated_opt_group,
                        'original_group_name': opt['option_group_name'],
                        'is_required': bool(opt['option_required'])
                    })

                # Add item to its category with modifiers and options
                categories[translated_category].append({
                    'item_id': item['item_id'],
                    'name': translated_name,
                    'original_name': item['name'],
                    'description': translated_desc,
                    'original_description': item.get('description', ''),
                    'base_price': float(item['base_price']) if item['base_price'] is not None else 0.00,
                    'price': float(item['base_price']) if item['base_price'] is not None else 0.00,
                    'modifiers': item_modifiers,
                    'options': item_options
                })

            # Convert categories to the required format
            menu = [{
                'category': category_name,
                'items': category_items
            } for category_name, category_items in categories.items()]

            return jsonify({
                'status': 'success',
                'language': language,
                'categories': list(categories.keys()),
                'menu': menu
            }), 200

    except mysql.connector.Error as err:
        print(f"Database error in get_menu_by_language: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err)
        }), 500

    except Exception as e:
        print(f"Unexpected error in get_menu_by_language: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e)
        }), 500