from flask import Blueprint, jsonify, request
import logging
import mysql.connector
import os
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a new Blueprint for combo-related endpoints
bp = Blueprint('restaurant_combo', __name__, url_prefix='/api/restaurants')

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'appointment_db')
    )

def execute_query(query, params=None, fetch=False, fetch_all=False):
    """Execute a database query and return the results if fetch is True"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(query, params or ())
        
        if fetch:
            if fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()
            return result if result else ([] if fetch_all else None)
        
        connection.commit()
        return cursor.lastrowid
        
    except mysql.connector.Error as e:
        logger.error(f"Database error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@bp.route('/list_combos', methods=['POST'])
def list_combos():
    """
    List all combo menu items for a business

    Request body:
    {
        "business_id": 123  // Required
    }

    Returns:
        JSON response with list of combo items
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'business_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Business ID is required',
                'error_code': 'MISSING_BUSINESS_ID'
            }), 400

        business_id = data['business_id']

        # Get all combo items for the business
        combos = execute_query(
            """
            SELECT ri.item_id,
                   ri.name,
                   ri.description,
                   ri.base_price,
                   ri.image_url,
                   ri.is_active,
                   ri.preparation_time,
                   ri.calories,
                   GROUP_CONCAT(DISTINCT rt.name) as tags
            FROM restaurant_item ri
                     LEFT JOIN
                 restaurant_item_tag rit ON ri.item_id = rit.item_id
                     LEFT JOIN
                 restaurant_tag rt ON rit.tag_id = rt.tag_id
            WHERE ri.business_id = %s
              AND ri.is_combo = 1
            GROUP BY ri.item_id
            ORDER BY ri.name
            """,
            (business_id,),
            fetch=True,
            fetch_all=True
        )

        # Format the response
        formatted_combos = [{
            'item_id': row['item_id'],
            'name': row['name'],
            'description': row['description'],
            'base_price': float(row['base_price']) if row['base_price'] is not None else 0.0,
            'image_url': row['image_url'],
            'is_active': bool(row['is_active']),
            'preparation_time': row['preparation_time'],
            'calories': row['calories'],
            'tags': row['tags'].split(',') if row['tags'] else []
        } for row in combos]

        return jsonify({
            'status': 'success',
            'data': formatted_combos
        })

    except Exception as e:
        logger.error(f"Error in list_combos: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching combo items',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/list_combo_groups', methods=['POST'])
def list_combo_groups():
    """
    List all combo groups for a specific item

    Request body:
    {
        "item_id": 123  // Required
    }

    Returns:
        JSON response with list of combo groups for the item
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'item_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Item ID is required',
                'error_code': 'MISSING_ITEM_ID'
            }), 400

        item_id = data['item_id']

        # Get all combo groups for the item
        groups = execute_query(
            """
            SELECT cg.combo_group_id,
                   cg.name,
                   cg.min_select,
                   cg.max_select,
                   cg.display_order
            FROM restaurant_combo_group cg
            WHERE cg.item_id = %s
            ORDER BY cg.display_order
            """,
            (item_id,),
            fetch=True,
            fetch_all=True
        )

        # Format the response
        formatted_groups = [{
            'combo_group_id': row['combo_group_id'],
            'name': row['name'],
            'min_select': row['min_select'],
            'max_select': row['max_select'],
            'display_order': row['display_order']
        } for row in groups]

        return jsonify({
            'status': 'success',
            'data': formatted_groups
        })

    except Exception as e:
        logger.error(f"Error in list_combo_groups: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching combo groups',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/list_combo_group_items', methods=['POST'])
def list_combo_group_items():
    """
    List all items in a specific combo group

    Request body:
    {
        "combo_group_id": 123  // Required
    }

    Returns:
        JSON response with list of items in the combo group
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'combo_group_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Combo Group ID is required',
                'error_code': 'MISSING_COMBO_GROUP_ID'
            }), 400

        combo_group_id = data['combo_group_id']

        # Get all items in the combo group
        items = execute_query(
            """
            SELECT cgi.combo_group_item_id,
                   cgi.allowed_item_id,
                   ri.name as item_name,
                   ri.description,
                   ri.base_price,
                   ri.image_url,
                   cgi.price_delta,
                   cgi.is_default,
                   cgi.display_order
            FROM restaurant_combo_group_item cgi
                     JOIN
                 restaurant_item ri ON cgi.allowed_item_id = ri.item_id
            WHERE cgi.combo_group_id = %s
            ORDER BY cgi.display_order
            """,
            (combo_group_id,),
            fetch=True,
            fetch_all=True
        )

        # Format the response
        formatted_items = [{
            'combo_group_item_id': row['combo_group_item_id'],
            'item_id': row['allowed_item_id'],
            'name': row['item_name'],
            'description': row['description'],
            'base_price': float(row['base_price']) if row['base_price'] is not None else 0.0,
            'image_url': row['image_url'],
            'price_delta': float(row['price_delta']) if row['price_delta'] is not None else 0.0,
            'is_default': bool(row['is_default']),
            'display_order': row['display_order']
        } for row in items]

        return jsonify({
            'status': 'success',
            'data': formatted_items
        })

    except Exception as e:
        logger.error(f"Error in list_combo_group_items: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching combo group items',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500