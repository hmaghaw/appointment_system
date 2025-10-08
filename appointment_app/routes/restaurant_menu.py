from flask import Blueprint, jsonify, request
import mysql.connector
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'autocommit': True
}

def get_db_connection():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Error connecting to database: {err}")
        raise

# Create blueprint
bp = Blueprint('menu', __name__, url_prefix='/api/restaurants')

@bp.route('/get_menu', methods=['POST'])
def get_menu():
    """
    Get the complete menu for a restaurant, with items grouped by category.

    Request body:
    {
        "business_id": 1  # Required
    }

    Returns:
        JSON response with menu items grouped by category
        {
            "menu": [
                {
                    "category": "Category Name",
                    "items": [
                        {
                            "item_id": 1,
                            "name": "Item Name",
                            "base_price": 10.00,
                            "price": 10.00,
                            "options": [...],
                            "modifiers": [...]
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()
        if not data or 'business_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Business ID is required',
                'error_code': 'MISSING_BUSINESS_ID'
            }), 400

        business_id = data['business_id']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all active menu items with their categories
        cursor.execute("""
            SELECT 
                i.item_id,
                i.name,
                i.base_price,
                i.description,
                ic.item_category_id,
                ic.name as category_name
            FROM restaurant_item i
            LEFT JOIN restaurant_item_category_map icm ON i.item_id = icm.item_id
            LEFT JOIN restaurant_item_category ic ON icm.item_category_id = ic.item_category_id
            WHERE i.business_id = %s AND i.is_active = 1
            ORDER BY ic.name, i.name
        """, (business_id,))

        items = cursor.fetchall()

        if not items:
            return jsonify({
                'status': 'success',
                'menu': []
            })

        # Get all item IDs for fetching options and modifiers
        item_ids = [str(item['item_id']) for item in items]
        item_ids_placeholders = ','.join(['%s'] * len(item_ids))

        # Get all option groups and options for these items
        cursor.execute(f"""
            SELECT 
                iog.item_id,
                o.option_id,
                o.name as option_name,
                o.price_delta as option_price_delta,
                o.is_default,
                o.display_order,
                og.name as option_group_name,
                og.is_required as option_required
            FROM restaurant_item_option_group iog
            JOIN restaurant_option_group og ON iog.option_group_id = og.option_group_id
            JOIN restaurant_option o ON og.option_group_id = o.option_group_id
            WHERE iog.item_id IN ({item_ids_placeholders})
            ORDER BY o.display_order, o.name
        """, tuple(item_ids))

        options = cursor.fetchall()

        # Get all modifier groups and modifiers for these items
        cursor.execute(f"""
            SELECT 
                img.item_id,
                m.modifier_id,
                m.name as modifier_name,
                m.price_delta as modifier_price_delta,
                m.is_active,
                m.display_order,
                mg.name as modifier_group_name,
                mg.is_required as modifier_required
            FROM restaurant_item_modifier_group img
            JOIN restaurant_modifier_group mg ON img.modifier_group_id = mg.modifier_group_id
            JOIN restaurant_modifier m ON mg.modifier_group_id = m.modifier_group_id
            WHERE img.item_id IN ({item_ids_placeholders}) AND m.is_active = 1
            ORDER BY m.display_order, m.name
        """, tuple(item_ids))

        modifiers = cursor.fetchall()

        # Organize the data by category
        categories = {}
        for item in items:
            category_name = item['category_name'] or 'Uncategorized'
            if category_name not in categories:
                categories[category_name] = []

            # Format item options
            item_options = []
            for opt in [o for o in options if o['item_id'] == item['item_id']]:
                item_options.append({
                    'option_id': opt['option_id'],
                    'name': opt['option_name'],
                    'price_delta': float(opt['option_price_delta']) if opt['option_price_delta'] is not None else 0.00,
                    'is_default': bool(opt['is_default']),
                    'display_order': opt['display_order'],
                    'group_name': opt['option_group_name'],
                    'is_required': bool(opt['option_required'])
                })

            # Format item modifiers
            item_modifiers = []
            for mod in [m for m in modifiers if m['item_id'] == item['item_id']]:
                item_modifiers.append({
                    'modifier_id': mod['modifier_id'],
                    'name': mod['modifier_name'],
                    'price_delta': float(mod['modifier_price_delta']) if mod['modifier_price_delta'] is not None else 0.00,
                    'is_active': bool(mod['is_active']),
                    'display_order': mod['display_order'],
                    'group_name': mod['modifier_group_name'],
                    'is_required': bool(mod['modifier_required'])
                })

            # Add item to its category
            categories[category_name].append({
                'item_id': item['item_id'],
                'name': item['name'],
                'base_price': float(item['base_price']) if item['base_price'] is not None else 0.00,
                'description': item['description'],
                'options': item_options,
                'modifiers': item_modifiers,
                'price': float(item['base_price']) if item['base_price'] is not None else 0.00
            })

        # Convert categories to the required format
        menu = [{
            'category': category_name,
            'items': category_items
        } for category_name, category_items in categories.items()]

        return jsonify({
            'categories':list(categories.keys()),
            'menu': menu
        })

    except mysql.connector.Error as err:
        logger.error(f"Database error in get_menu: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR',
            'details': str(err)
        }), 500

    except Exception as e:
        logger.error(f"Unexpected error in get_menu: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
