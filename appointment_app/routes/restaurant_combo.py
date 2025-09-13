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

@bp.route('/create_combo_group', methods=['POST'])
def create_combo_group():
    """
    Create a new combo group
    
    Request body:
    {
        "item_id": 1,             // Required
        "name": "Choose a Pizza", // Required
        "display_order": 1,       // Required
        "max_select": 1,          // Required
        "min_select": 1           // Required
    }
    
    Returns:
        JSON response with the created combo group details
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['item_id', 'name', 'display_order', 'max_select', 'min_select']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'All fields are required',
                'error_code': 'MISSING_REQUIRED_FIELDS'
            }), 400
            
        # Insert new combo group
        combo_group_id = execute_query(
            """
            INSERT INTO restaurant_combo_group 
            (item_id, name, display_order, max_select, min_select)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (data['item_id'], data['name'], data['display_order'], 
             data['max_select'], data['min_select'])
        )
        
        # Get the created combo group
        combo_group = execute_query(
            """
            SELECT * FROM restaurant_combo_group 
            WHERE combo_group_id = %s
            """,
            (combo_group_id,),
            fetch=True
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Combo group created successfully',
            'data': combo_group
        })
        
    except Exception as e:
        logger.error(f"Error in create_combo_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while creating combo group',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/update_combo_group', methods=['POST'])
def update_combo_group():
    """
    Update an existing combo group
    
    Request body:
    {
        "combo_group_id": 1,     // Required
        "name": "Choose a Pizza", // Optional
        "display_order": 1,       // Optional
        "max_select": 1,          // Optional
        "min_select": 1           // Optional
    }
    
    Returns:
        JSON response with the updated combo group details
    """
    try:
        data = request.get_json()
        
        # Validate required field
        if 'combo_group_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'combo_group_id is required',
                'error_code': 'MISSING_COMBO_GROUP_ID'
            }), 400
            
        # Build update query dynamically based on provided fields
        update_fields = []
        update_values = []
        
        for field in ['name', 'display_order', 'max_select', 'min_select']:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])
                
        if not update_fields:
            return jsonify({
                'status': 'error',
                'message': 'No fields to update',
                'error_code': 'NO_FIELDS_TO_UPDATE'
            }), 400
            
        # Add combo_group_id to values for WHERE clause
        update_values.append(data['combo_group_id'])
        
        # Execute update
        execute_query(
            f"""
            UPDATE restaurant_combo_group 
            SET {', '.join(update_fields)}
            WHERE combo_group_id = %s
            """,
            tuple(update_values)
        )
        
        # Get the updated combo group
        updated_group = execute_query(
            """
            SELECT * FROM restaurant_combo_group 
            WHERE combo_group_id = %s
            """,
            (data['combo_group_id'],),
            fetch=True
        )
        
        if not updated_group:
            return jsonify({
                'status': 'error',
                'message': 'Combo group not found',
                'error_code': 'COMBO_GROUP_NOT_FOUND'
            }), 404
            
        return jsonify({
            'status': 'success',
            'message': 'Combo group updated successfully',
            'data': updated_group
        })
        
    except Exception as e:
        logger.error(f"Error in update_combo_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating combo group',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/delete_combo_group', methods=['POST'])
def delete_combo_group():
    """
    Delete a combo group
    
    Request body:
    {
        "combo_group_id": 1  // Required
    }
    
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        
        # Validate required field
        if 'combo_group_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'combo_group_id is required',
                'error_code': 'MISSING_COMBO_GROUP_ID'
            }), 400
            
        # First, check if the combo group exists
        existing_group = execute_query(
            """
            SELECT * FROM restaurant_combo_group 
            WHERE combo_group_id = %s
            """,
            (data['combo_group_id'],),
            fetch=True
        )
        
        if not existing_group:
            return jsonify({
                'status': 'error',
                'message': 'Combo group not found',
                'error_code': 'COMBO_GROUP_NOT_FOUND'
            }), 404
            
        # Delete the combo group
        execute_query(
            """
            DELETE FROM restaurant_combo_group 
            WHERE combo_group_id = %s
            """,
            (data['combo_group_id'],)
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Combo group deleted successfully',
            'deleted_id': data['combo_group_id']
        })
        
    except Exception as e:
        logger.error(f"Error in delete_combo_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting combo group',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/list_combo_group_items', methods=['POST'])
def list_combo_group_items():
    """
    List all items in a specific combo group
    
    Request body:
    {
        "combo_group_id": 1  // Required
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
                'message': 'combo_group_id is required',
                'error_code': 'MISSING_COMBO_GROUP_ID'
            }), 400
            
        # Get all items in the combo group
        items = execute_query(
            """
            SELECT 
                cgi.combo_group_item_id,
                cgi.combo_group_id,
                cgi.allowed_item_id,
                cgi.price_delta,
                ri.name as item_name,
                ri.description,
                ri.base_price,
                ri.image_url
            FROM restaurant_combo_group_item cgi
            JOIN restaurant_item ri ON cgi.allowed_item_id = ri.item_id
            WHERE cgi.combo_group_id = %s
            """,
            (data['combo_group_id'],),
            fetch=True,
            fetch_all=True
        )
        
        # Format the response
        formatted_items = [{
            'combo_group_item_id': row['combo_group_item_id'],
            'combo_group_id': row['combo_group_id'],
            'item_id': row['allowed_item_id'],
            'name': row['item_name'],
            'description': row['description'],
            'base_price': float(row['base_price']) if row['base_price'] is not None else 0.0,
            'image_url': row['image_url'],
            'price_delta': float(row['price_delta']) if row['price_delta'] is not None else 0.0
        } for row in items]
        
        return jsonify({
            'status': 'success',
            'data': formatted_items
        })
        
    except Exception as e:
        logger.error(f"Error in list_combo_group_items: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'An error occurred while fetching combo group items: {str(e)}',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/create_combo_group_item', methods=['POST'])
def create_combo_group_item():
    """
    Add an item to a combo group
    
    Request body:
    {
        "combo_group_id": 1,    // Required
        "allowed_item_id": 2,   // Required
        "price_delta": 1.5      // Optional, defaults to 0
    }
    
    Returns:
        JSON response with the created combo group item details
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['combo_group_id', 'allowed_item_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'{field} is required',
                    'error_code': f'MISSING_{field.upper()}'
                }), 400
        
        # Set default values for optional fields
        price_delta = data.get('price_delta', 0)
        
        # Insert the new combo group item
        item_id = execute_query(
            """
            INSERT INTO restaurant_combo_group_item 
            (combo_group_id, allowed_item_id, price_delta)
            VALUES (%s, %s, %s)
            """,
            (data['combo_group_id'], data['allowed_item_id'], price_delta)
        )
        
        # Get the created item with details
        created_item = execute_query(
            """
            SELECT cgi.*, ri.name as item_name, ri.description, ri.base_price, ri.image_url
            FROM restaurant_combo_group_item cgi
            JOIN restaurant_item ri ON cgi.allowed_item_id = ri.item_id
            WHERE cgi.combo_group_item_id = %s
            """,
            (item_id,),
            fetch=True
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Combo group item created successfully',
            'data': {
                'combo_group_item_id': created_item['combo_group_item_id'],
                'combo_group_id': created_item['combo_group_id'],
                'item_id': created_item['allowed_item_id'],
                'name': created_item['item_name'],
                'description': created_item['description'],
                'base_price': float(created_item['base_price']) if created_item['base_price'] is not None else 0.0,
                'image_url': created_item['image_url'],
                'price_delta': float(created_item['price_delta'])
            }
        }), 201
        
    except mysql.connector.IntegrityError as e:
        if 'foreign key constraint' in str(e).lower():
            return jsonify({
                'status': 'error',
                'message': 'Invalid combo_group_id or allowed_item_id',
                'error_code': 'INVALID_IDS'
            }), 400
        elif 'duplicate entry' in str(e).lower():
            return jsonify({
                'status': 'error',
                'message': 'This item is already in the combo group',
                'error_code': 'DUPLICATE_ITEM'
            }), 400
        raise
    except Exception as e:
        logger.error(f"Error in create_combo_group_item: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while creating combo group item',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/update_combo_group_item', methods=['POST'])
def update_combo_group_item():
    """
    Update a combo group item
    
    Request body:
    {
        "combo_group_item_id": 1,  // Required
        "price_delta": 2.0         // Optional
    }
    
    Returns:
        JSON response with the updated combo group item details
    """
    try:
        data = request.get_json()
        
        # Validate required field
        if 'combo_group_item_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'combo_group_item_id is required',
                'error_code': 'MISSING_COMBO_GROUP_ITEM_ID'
            }), 400
            
        # Check if there are any fields to update
        if 'price_delta' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No fields to update',
                'error_code': 'NO_FIELDS_TO_UPDATE'
            }), 400
            
        # Update the combo group item
        execute_query(
            """
            UPDATE restaurant_combo_group_item 
            SET price_delta = %s
            WHERE combo_group_item_id = %s
            """,
            (data['price_delta'], data['combo_group_item_id'])
        )
        
        # Get the updated item with details
        updated_item = execute_query(
            """
            SELECT cgi.*, ri.name as item_name, ri.description, ri.base_price, ri.image_url
            FROM restaurant_combo_group_item cgi
            JOIN restaurant_item ri ON cgi.allowed_item_id = ri.item_id
            WHERE cgi.combo_group_item_id = %s
            """,
            (data['combo_group_item_id'],),
            fetch=True
        )
        
        if not updated_item:
            return jsonify({
                'status': 'error',
                'message': 'Combo group item not found',
                'error_code': 'ITEM_NOT_FOUND'
            }), 404
            
        return jsonify({
            'status': 'success',
            'message': 'Combo group item updated successfully',
            'data': {
                'combo_group_item_id': updated_item['combo_group_item_id'],
                'combo_group_id': updated_item['combo_group_id'],
                'item_id': updated_item['allowed_item_id'],
                'name': updated_item['item_name'],
                'description': updated_item['description'],
                'base_price': float(updated_item['base_price']) if updated_item['base_price'] is not None else 0.0,
                'image_url': updated_item['image_url'],
                'price_delta': float(updated_item['price_delta'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error in update_combo_group_item: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'An error occurred while updating combo group item: {str(e)}',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/delete_combo_group_item', methods=['POST'])
def delete_combo_group_item():
    """
    Remove an item from a combo group
    
    Request body:
    {
        "combo_group_item_id": 1  // Required
    }
    
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        
        # Validate required field
        if 'combo_group_item_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'combo_group_item_id is required',
                'error_code': 'MISSING_COMBO_GROUP_ITEM_ID'
            }), 400
            
        # First, check if the item exists
        existing_item = execute_query(
            """
            SELECT * FROM restaurant_combo_group_item 
            WHERE combo_group_item_id = %s
            """,
            (data['combo_group_item_id'],),
            fetch=True
        )
        
        if not existing_item:
            return jsonify({
                'status': 'error',
                'message': 'Combo group item not found',
                'error_code': 'ITEM_NOT_FOUND'
            }), 404
            
        # Delete the item
        execute_query(
            """
            DELETE FROM restaurant_combo_group_item 
            WHERE combo_group_item_id = %s
            """,
            (data['combo_group_item_id'],)
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Item removed from combo group successfully',
            'deleted_id': data['combo_group_item_id']
        })
        
    except Exception as e:
        logger.error(f"Error in delete_combo_group_item: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while removing item from combo group',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500