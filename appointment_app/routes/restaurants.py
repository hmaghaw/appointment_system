#!/usr/bin/env python3
"""
Restaurant API
Handles restaurant related operations including menu management
"""

from flask import Blueprint, request, jsonify
import mysql.connector
import os
import logging
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Restaurant blueprint loaded.")

# Create Blueprint
bp = Blueprint('restaurants', __name__, url_prefix='')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def get_db_connection():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        raise

def execute_query(query, params=None, fetch=False):
    """Execute a database query and return the results if fetch is True"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Create Blueprint with /api/restaurants prefix
bp = Blueprint('restaurants', __name__, url_prefix='/api/restaurants')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def get_db_connection():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        raise

@bp.route('/create_modifier', methods=['POST'])
def create_modifier():
    """
    Create a new modifier for a modifier group

    Request body:
    {
        "modifier_group_id": 1,
        "name": "Extra Cheese",
        "price_delta": 1.50,
        "is_active": true
    }

    Returns:
        JSON response with the created modifier details
    """
    try:
        data = request.get_json()
        required_fields = ['modifier_group_id', 'name']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'error_code': 'MISSING_FIELDS'
            }), 400

        # Set default values for optional fields
        price_delta = float(data.get('price_delta', 0))
        is_active = data.get('is_active', True)
        
        # Check if modifier group exists
        check_query = """
            SELECT 1 FROM restaurant_modifier_group 
            WHERE modifier_group_id = %s
        """
        if not execute_query(check_query, (data['modifier_group_id'],), fetch=True):
            return jsonify({
                'status': 'error',
                'message': 'Modifier group not found',
                'error_code': 'NOT_FOUND'
            }), 404

        # Insert the new modifier
        insert_query = """
            INSERT INTO restaurant_modifier 
            (modifier_group_id, name, price_delta, is_active)
            VALUES (%s, %s, %s, %s)
        """
        params = (
            data['modifier_group_id'],
            data['name'],
            price_delta,
            is_active
        )
        
        # Execute the insert and get the last inserted ID
        modifier_id = execute_query(insert_query, params)
        
        # Get the created modifier using the returned ID
        get_query = """
            SELECT * FROM restaurant_modifier 
            WHERE modifier_id = %s
        """
        modifier = execute_query(get_query, (modifier_id,), fetch=True)[0]

        return jsonify({
            'status': 'success',
            'data': modifier,
            'message': 'Modifier created successfully'
        }), 201

    except ValueError as ve:
        logger.error(f"Invalid input value: {ve}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid input value',
            'error_code': 'INVALID_INPUT'
        }), 400
    except mysql.connector.Error as err:
        logger.error(f"Database error in create_modifier: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in create_modifier: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': e
        }), 500

@bp.route('/update_modifier', methods=['POST'])
def update_modifier():
    """
    Update an existing modifier

    Request body:
    {
        "modifier_id": 1,  # Required
        "name": "Gluten-Free Crust",  # Optional
        "price_delta": 2.00,  # Optional
        "is_active": true,  # Optional
        "modifier_group_id": 1  # Optional (only needed if changing the group)
    }

    Returns:
        JSON response with the updated modifier details
    """
    try:
        data = request.get_json()
        if 'modifier_id' not in data or data['modifier_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: modifier_id',
                'error_code': 'MISSING_FIELDS'
            }), 400

        # Check if modifier exists
        check_query = """
            SELECT modifier_group_id FROM restaurant_modifier 
            WHERE modifier_id = %s
        """
        result = execute_query(check_query, (data['modifier_id'],), fetch=True)
        if not result:
            return jsonify({
                'status': 'error',
                'message': 'Modifier not found',
                'error_code': 'NOT_FOUND'
            }), 404
            
        current_group_id = result[0]['modifier_group_id']

        # Build the update query dynamically based on provided fields
        update_fields = []
        params = []
        
        if 'name' in data and data['name'] is not None:
            update_fields.append("name = %s")
            params.append(data['name'])
            
        if 'price_delta' in data and data['price_delta'] is not None:
            try:
                update_fields.append("price_delta = %s")
                params.append(float(data['price_delta']))
            except (ValueError, TypeError):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid price_delta value',
                    'error_code': 'INVALID_INPUT'
                }), 400
            
        if 'is_active' in data and data['is_active'] is not None:
            update_fields.append("is_active = %s")
            params.append(bool(data['is_active']))
            
        if 'display_order' in data and data['display_order'] is not None:
            try:
                update_fields.append("display_order = %s")
                params.append(int(data['display_order']))
            except (ValueError, TypeError):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid display_order value. Must be an integer.',
                    'error_code': 'INVALID_INPUT'
                }), 400
        
        if not update_fields:
            return jsonify({
                'status': 'error',
                'message': 'No fields to update',
                'error_code': 'NO_UPDATE_FIELDS'
            }), 400
            
        # If modifier_group_id is provided, update it
        if 'modifier_group_id' in data and data['modifier_group_id'] is not None:
            update_fields.append("modifier_group_id = %s")
            params.append(data['modifier_group_id'])
            
        # Add modifier_id to params for WHERE clause
        params.append(data['modifier_id'])
        
        # Build and execute the update query
        update_query = f"""
            UPDATE restaurant_modifier 
            SET {', '.join(update_fields)}
            WHERE modifier_id = %s
        """
        
        execute_query(update_query, params)
        
        # Get the updated modifier with group name
        get_query = """
            SELECT rm.*, rmg.name as group_name 
            FROM restaurant_modifier rm
            JOIN restaurant_modifier_group rmg ON rm.modifier_group_id = rmg.modifier_group_id
            WHERE rm.modifier_id = %s
        """
        modifier = execute_query(get_query, (data['modifier_id'],), fetch=True)[0]
        
        return jsonify({
            'status': 'success',
            'data': modifier,
            'message': 'Modifier updated successfully'
        })

    except mysql.connector.Error as err:
        logger.error(f"Database error in update_modifier: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in update_modifier: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/list_menus', methods=['POST'])
def list_menus():
    """
    List all menus for a given business
    
    Request body:
    {
        "business_id": 31
    }
    
    Returns:
        JSON response with list of menus or error message
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or 'business_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Business ID is required',
                'error_code': 'MISSING_BUSINESS_ID'
            }), 400
            
        business_id = data['business_id']
        
        # Query to get all active menus for the business
        query = """
            SELECT 
                m.menu_id,
                m.name AS menu_name,
                m.description,
                m.is_active,
                a.availability_id,
                a.name AS availability_name,
                ad.day_of_week,
                ad.open_time AS start_time,
                ad.close_time AS end_time,
                ad.is_closed
            FROM restaurant_menu m
            LEFT JOIN restaurant_menu_availability ma ON m.menu_id = ma.menu_id
            LEFT JOIN restaurant_availability a ON ma.availability_id = a.availability_id
            LEFT JOIN restaurant_availability_detail ad ON a.availability_id = ad.availability_id
            WHERE m.business_id = %s 
            ORDER BY m.menu_id, a.availability_id, ad.day_of_week, ad.open_time
        """
        
        results = execute_query(query, (business_id,), fetch=True)
        
        # Group availability by menu
        menus = {}
        for row in results:
            menu_id = row['menu_id']
            if menu_id not in menus:
                menus[menu_id] = {
                    'menu_id': menu_id,
                    'name': row['menu_name'],
                    'description': row['description'],
                    'is_active': bool(row['is_active']),
                    'availability': []
                }
            
            # Add availability if it exists
            if row['availability_id'] is not None:
                menus[menu_id]['availability'].append({
                    'availability_id': row['availability_id'],
                    'name': row['availability_name'],
                    'day_of_week': row['day_of_week'],
                    'start_time': str(row['start_time']) if row['start_time'] else None,
                    'end_time': str(row['end_time']) if row['end_time'] else None
                })
        
        # Convert to list and return
        menu_list = list(menus.values())
        return jsonify({
            'status': 'success',
            'data': {
                'menus': menu_list,
                'count': len(menu_list)
            }
        })
        
    except mysql.connector.Error as err:
        logger.error(f"Database error in list_menus: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in list_menus: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/list_menu_items', methods=['POST'])
def list_menu_items():
    """
    List all menu items with their sections for a given menu
    
    Request body:
    {
        "menu_id": 1
    }
    
    Returns:
        JSON response with list of menu sections and their items
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or 'menu_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Menu ID is required',
                'error_code': 'MISSING_MENU_ID'
            }), 400
            
        menu_id = data['menu_id']
        
        # Query to get menu items with their sections
        query = """
            SELECT 
                m.menu_id,
                m.name AS menu_name,
                s.menu_section_id,
                s.name AS section_name,
                i.item_id,
                i.name AS item_name,
                i.description,
                i.base_price,
                i.is_combo,
                i.is_active,
                i.image_url
            FROM restaurant_menu m
            JOIN restaurant_menu_section s 
                ON m.menu_id = s.menu_id
            JOIN restaurant_menu_section_item sm 
                ON s.menu_section_id = sm.menu_section_id
            JOIN restaurant_item i 
                ON sm.item_id = i.item_id
            WHERE m.menu_id = %s
            ORDER BY s.display_order, i.name
        """
        
        results = execute_query(query, (menu_id,), fetch=True)
        
        if not results:
            return jsonify({
                'status': 'success',
                'data': {
                    'menu_id': menu_id,
                    'menu_name': None,
                    'sections': [],
                    'count': 0
                }
            })
        
        # Group items by section
        menu_data = {
            'menu_id': results[0]['menu_id'],
            'menu_name': results[0]['menu_name'],
            'sections': [],
            'count': 0
        }
        
        current_section = None
        for row in results:
            # If this is a new section
            if not current_section or current_section['menu_section_id'] != row['menu_section_id']:
                if current_section:  # Add previous section if exists
                    menu_data['sections'].append(current_section)
                
                current_section = {
                    'menu_section_id': row['menu_section_id'],
                    'name': row['section_name'],
                    'items': []
                }
            
            # Add item to current section
            current_section['items'].append({
                'item_id': row['item_id'],
                'name': row['item_name'],
                'description': row['description'],
                'base_price': float(row['base_price']) if row['base_price'] is not None else None,
                'is_combo': bool(row['is_combo']),
                'is_active': bool(row['is_active']),
                'image_url': row['image_url']
            })
            menu_data['count'] += 1
        
        # Add the last section
        if current_section:
            menu_data['sections'].append(current_section)
        
        return jsonify({
            'status': 'success',
            'data': menu_data
        })
        
    except mysql.connector.Error as err:
        logger.error(f"Database error in list_menu_items: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in list_menu_items: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/list_item_categories', methods=['POST'])
def list_item_categories():
    """
    List all item categories for a business
    
    Request body:
    {
        "business_id": 73
    }
    
    Returns:
        JSON response with list of item categories
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or 'business_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Business ID is required',
                'error_code': 'MISSING_BUSINESS_ID'
            }), 400
            
        business_id = data['business_id']
        
        # Query to get item categories for the business
        query = """
            SELECT 
                item_category_id,
                name AS category_name,
                description
            FROM restaurant_item_category
            WHERE business_id = %s
            ORDER BY name
        """
        
        categories = execute_query(query, (business_id,), fetch=True)
        
        return jsonify({
            'status': 'success',
            'data': {
                'business_id': business_id,
                'categories': categories,
                'count': len(categories)
            }
        })
        
    except mysql.connector.Error as err:
        logger.error(f"Database error in list_item_categories: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in list_item_categories: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/list_menu_sections', methods=['POST'])
def list_menu_sections():
    """
    List all sections for a given menu

    Request body:
    {
        "menu_id": 1
    }

    Returns:
        JSON response with list of menu sections
    """
    try:
        data = request.get_json()
        if not data or 'menu_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Menu ID is required',
                'error_code': 'MISSING_MENU_ID'
            }), 400

        menu_id = data['menu_id']

        # Query to get all sections for the menu
        query = """
                SELECT s.menu_section_id, \
                       s.name AS section_name, \
                       s.description, \
                       s.display_order
                FROM restaurant_menu_section s
                WHERE s.menu_id = %s
                ORDER BY s.display_order \
                """

        sections = execute_query(query, (menu_id,), fetch=True)

        return jsonify({
            'status': 'success',
            'data': {
                'menu_id': menu_id,
                'sections': sections,
                'count': len(sections)
            }
        })

    except mysql.connector.Error as err:
        logger.error(f"Database error in list_menu_sections: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in list_menu_sections: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/list_items', methods=['POST'])
def list_items():
    """
    List all menu items for a business

    Request body:
    {
        "business_id": 73
    }

    Returns:
        JSON response with list of menu items for the business
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or 'business_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Business ID is required',
                'error_code': 'MISSING_BUSINESS_ID'
            }), 400

        business_id = data['business_id']

        # Query to get all menu items for the business
        query = """
                SELECT 
                    i.item_id,
                    i.name AS item_name,
                    i.description,
                    i.base_price,
                    i.is_combo,
                    i.is_active,
                    i.image_url,
                    i.item_category_id,
                    ic.name AS category_name
                FROM restaurant_item i
                LEFT JOIN restaurant_item_category ic 
                    ON i.item_category_id = ic.item_category_id
                WHERE ic.business_id = %s
                ORDER BY i.name;
                """

        items = execute_query(query, (business_id,), fetch=True)

        # Convert Decimal to float for JSON serialization
        for item in items:
            if 'base_price' in item and item['base_price'] is not None:
                item['base_price'] = float(item['base_price'])

        return jsonify({
            'status': 'success',
            'data': {
                'business_id': business_id,
                'items': items,
                'count': len(items)
            }
        })

    except mysql.connector.Error as err:
        logger.error(f"Database error in list_items: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500

    except Exception as e:
        logger.error(f"Unexpected error in list_items: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/create_menu', methods=['POST'])
def create_menu():
    """
    Create a new menu for a business

    Request body:
    {
        "business_id": 73,
        "name": "Dinner Menu",
        "description": "Our delicious dinner options",
        "is_active": true
    }

    Returns:
        JSON response with the created menu details
    """
    try:
        # Get request data
        data = request.get_json()
        required_fields = ['business_id', 'name']

        if not data or not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields',
                'error_code': 'MISSING_REQUIRED_FIELDS'
            }), 400

        # Insert new menu
        query = """
                INSERT INTO restaurant_menu
                    (business_id, name, description, is_active)
                VALUES (%s, %s, %s, %s) \
                """
        params = (
            data['business_id'],
            data['name'],
            data.get('description'),
            data.get('is_active', True)
        )

        menu_id = execute_query(query, params)

        # Get the created menu
        query = "SELECT * FROM restaurant_menu WHERE menu_id = %s"
        menu = execute_query(query, (menu_id,), fetch=True)[0]

        return jsonify({
            'status': 'success',
            'data': {
                'menu': menu,
                'message': 'Menu created successfully'
            }
        }), 201

    except mysql.connector.Error as err:
        logger.error(f"Database error in create_menu: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in create_menu: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/update_menu', methods=['POST'])
def update_menu():
    """
    Update an existing menu

    Request body:
    {
        "menu_id": 1,
        "name": "Updated Menu Name",
        "description": "Updated description",
        "is_active": false
    }

    Returns:
        JSON response with the updated menu details
    """
    try:
        data = request.get_json()
        if not data or 'menu_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Menu ID is required',
                'error_code': 'MISSING_MENU_ID'
            }), 400

        menu_id = data['menu_id']

        # Build dynamic update query based on provided fields
        update_fields = []
        params = []

        if 'name' in data:
            update_fields.append("name = %s")
            params.append(data['name'])

        if 'description' in data:
            update_fields.append("description = %s")
            params.append(data['description'])

        if 'is_active' in data:
            update_fields.append("is_active = %s")
            params.append(data['is_active'])

        if not update_fields:
            return jsonify({
                'status': 'error',
                'message': 'No fields to update',
                'error_code': 'NO_FIELDS_TO_UPDATE'
            }), 400

        # Add menu_id to params
        params.append(menu_id)

        # Build and execute the update query
        update_query = f"""
            UPDATE restaurant_menu 
            SET {', '.join(update_fields)}
            WHERE menu_id = %s
        """
        execute_query(update_query, params)

        # Get the updated menu
        query = "SELECT * FROM restaurant_menu WHERE menu_id = %s"
        menu = execute_query(query, (menu_id,), fetch=True)[0]

        return jsonify({
            'status': 'success',
            'data': {
                'menu': menu,
                'message': 'Menu updated successfully'
            }
        })

    except mysql.connector.Error as err:
        logger.error(f"Database error in update_menu: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': err
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in update_menu: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/delete_menu', methods=['POST'])
def delete_menu():
    """
    Delete a menu

    Request body:
    {
        "menu_id": 1
    }

    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        if not data or 'menu_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Menu ID is required',
                'error_code': 'MISSING_MENU_ID'
            }), 400

        menu_id = data['menu_id']

        # First check if menu exists
        query = "SELECT * FROM restaurant_menu WHERE menu_id = %s"
        menu = execute_query(query, (menu_id,), fetch=True)

        if not menu:
            return jsonify({
                'status': 'error',
                'message': 'Menu not found',
                'error_code': 'MENU_NOT_FOUND'
            }), 404

        # Delete the menu
        query = "DELETE FROM restaurant_menu WHERE menu_id = %s"
        execute_query(query, (menu_id,))

        return jsonify({
            'status': 'success',
            'data': {
                'menu_id': menu_id,
                'message': 'Menu deleted successfully'
            }
        })

    except mysql.connector.Error as err:
        logger.error(f"Database error in delete_menu: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': err
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in delete_menu: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': e
        }), 500


@bp.route('/list_modifier_groups', methods=['POST'])
def list_modifier_groups():
    """
    List all modifier groups for a business

    Request body:
    {
        "business_id": 1
    }

    Returns:
        JSON response with list of modifier groups
    """
    try:
        data = request.get_json()
        if not data or 'business_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: business_id',
                'error_code': 'MISSING_FIELD'
            }), 400

        business_id = data['business_id']

        # Get all modifier groups for the business
        query = """
            SELECT 
                modifier_group_id,
                business_id,
                name,
                is_required,
                min_select,
                max_select
            FROM restaurant_modifier_group
            WHERE business_id = %s
            ORDER BY name
        """
        
        modifier_groups = execute_query(query, (business_id,), fetch=True)

        if not modifier_groups:
            return jsonify({
                'status': 'success',
                'data': [],
                'message': 'No modifier groups found for this business'
            })

        return jsonify({
            'status': 'success',
            'data': modifier_groups,
            'message': 'Modifier groups retrieved successfully'
        })

    except mysql.connector.Error as err:
        logger.error(f"Database error in list_modifier_groups: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in list_modifier_groups: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/list_modifiers', methods=['POST'])
def list_modifiers():
    """
    List all modifiers for a specific modifier group

    Request body:
    {
        "modifier_group_id": 1
    }

    Returns:
        JSON response with list of modifiers for the specified modifier group
    """
    try:
        data = request.get_json()
        if not data or 'modifier_group_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: modifier_group_id',
                'error_code': 'MISSING_FIELD'
            }), 400

        modifier_group_id = data['modifier_group_id']

        # Check if modifier group exists
        check_query = """
            SELECT 1 FROM restaurant_modifier_group 
            WHERE modifier_group_id = %s
        """
        if not execute_query(check_query, (modifier_group_id,), fetch=True):
            return jsonify({
                'status': 'error',
                'message': 'Modifier group not found',
                'error_code': 'NOT_FOUND'
            }), 404

        # Get all modifiers for the specified modifier group
        query = """
            SELECT 
                m.modifier_id,
                m.modifier_group_id,
                m.name,
                m.price_delta,
                m.is_active,
                m.display_order
            FROM restaurant_modifier m
            WHERE m.modifier_group_id = %s
            ORDER BY m.display_order
        """
        
        modifiers = execute_query(query, (modifier_group_id,), fetch=True)

        if not modifiers:
            return jsonify({
                'status': 'success',
                'data': [],
                'message': 'No modifiers found for this modifier group'
            })

        return jsonify({
            'status': 'success',
            'data': modifiers,
            'message': 'Modifiers retrieved successfully'
        })

    except mysql.connector.Error as err:
        logger.error(f"Database error in list_modifiers: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in list_modifiers: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/delete_modifier', methods=['POST'])
def delete_modifier():
    """
    Delete a modifier

    Request body:
    {
        "modifier_id": 1  # Required
    }

    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        if 'modifier_id' not in data or data['modifier_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: modifier_id',
                'error_code': 'MISSING_FIELDS'
            }), 400

        # Check if modifier exists
        check_query = """
                      SELECT 1 \
                      FROM restaurant_modifier
                      WHERE modifier_id = %s \
                      """
        if not execute_query(check_query, (data['modifier_id'],), fetch=True):
            return jsonify({
                'status': 'error',
                'message': 'Modifier not found',
                'error_code': 'NOT_FOUND'
            }), 404

        # Delete the modifier
        delete_query = """
                       DELETE \
                       FROM restaurant_modifier
                       WHERE modifier_id = %s \
                       """
        execute_query(delete_query, (data['modifier_id'],))

        return jsonify({
            'status': 'success',
            'message': 'Modifier deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error in delete_modifier: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting the modifier',
            'error_code': str(e)
        }), 500


@bp.route('/create_modifier_group', methods=['POST'])
def create_modifier_group():
    """
    Create a new modifier group

    Request body:
    {
        "business_id": 1,      # Required
        "name": "Toppings",    # Required
        "is_required": false,  # Optional, defaults to false
        "min_select": 0,       # Optional, defaults to 0
        "max_select": 3        # Optional, defaults to 3
    }

    Returns:
        JSON response with the created modifier group details
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['business_id', 'name']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]

        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'error_code': 'MISSING_FIELDS'
            }), 400

        # Set default values for optional fields
        is_required = data.get('is_required', False)
        min_select = data.get('min_select', 0)
        max_select = data.get('max_select', 3)

        # Insert the new modifier group
        insert_query = """
                       INSERT INTO restaurant_modifier_group
                           (business_id, name, is_required, min_select, max_select)
                       VALUES (%s, %s, %s, %s, %s) \
                       """
        params = (
            data['business_id'],
            data['name'],
            is_required,
            min_select,
            max_select
        )

        modifier_group_id = execute_query(insert_query, params)

        # Get the created modifier group
        get_query = """
                    SELECT * \
                    FROM restaurant_modifier_group
                    WHERE modifier_group_id = %s \
                    """
        modifier_group = execute_query(get_query, (modifier_group_id,), fetch=True)[0]

        return jsonify({
            'status': 'success',
            'data': modifier_group,
            'message': 'Modifier group created successfully'
        }), 201

    except Exception as e:
        logger.error(f"Error in create_modifier_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while creating the modifier group',
            'error_code': str(e)
        }), 500


@bp.route('/update_modifier_group', methods=['POST'])
def update_modifier_group():
    """
    Update an existing modifier group

    Request body:
    {
        "modifier_group_id": 1,  # Required
        "name": "Updated Name",  # Optional
        "is_required": true,     # Optional
        "min_select": 1,         # Optional
        "max_select": 5          # Optional
    }

    Returns:
        JSON response with the updated modifier group details
    """
    try:
        data = request.get_json()

        # Validate required fields
        if 'modifier_group_id' not in data or data['modifier_group_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: modifier_group_id',
                'error_code': 'MISSING_FIELDS'
            }), 400

        # Check if modifier group exists
        check_query = """
                      SELECT * \
                      FROM restaurant_modifier_group
                      WHERE modifier_group_id = %s \
                      """
        existing_group = execute_query(check_query, (data['modifier_group_id'],), fetch=True)

        if not existing_group:
            return jsonify({
                'status': 'error',
                'message': 'Modifier group not found',
                'error_code': 'NOT_FOUND'
            }), 404

        # Build the update query dynamically based on provided fields
        update_fields = []
        params = []

        if 'name' in data and data['name'] is not None:
            update_fields.append("name = %s")
            params.append(data['name'])

        if 'is_required' in data and data['is_required'] is not None:
            update_fields.append("is_required = %s")
            params.append(bool(data['is_required']))

        if 'min_select' in data and data['min_select'] is not None:
            update_fields.append("min_select = %s")
            params.append(int(data['min_select']))

        if 'max_select' in data and data['max_select'] is not None:
            update_fields.append("max_select = %s")
            params.append(int(data['max_select']))

        if not update_fields:
            return jsonify({
                'status': 'error',
                'message': 'No fields to update',
                'error_code': 'NO_UPDATE_FIELDS'
            }), 400

        # Add modifier_group_id to params
        params.append(data['modifier_group_id'])

        # Build and execute the update query
        update_query = f"""
            UPDATE restaurant_modifier_group 
            SET {', '.join(update_fields)}
            WHERE modifier_group_id = %s
        """
        execute_query(update_query, params)

        # Get the updated modifier group
        get_query = """
                    SELECT * \
                    FROM restaurant_modifier_group
                    WHERE modifier_group_id = %s \
                    """
        updated_group = execute_query(get_query, (data['modifier_group_id'],), fetch=True)[0]

        return jsonify({
            'status': 'success',
            'data': updated_group,
            'message': 'Modifier group updated successfully'
        })

    except Exception as e:
        logger.error(f"Error in update_modifier_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating the modifier group',
            'error_code': str(e)
        }), 500


@bp.route('/delete_modifier_group', methods=['POST'])
def delete_modifier_group():
    """
    Delete a modifier group

    Request body:
    {
        "modifier_group_id": 1  # Required
    }

    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()

        # Validate required fields
        if 'modifier_group_id' not in data or data['modifier_group_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: modifier_group_id',
                'error_code': 'MISSING_FIELDS'
            }), 400

        # Check if modifier group exists
        check_query = """
                      SELECT * \
                      FROM restaurant_modifier_group
                      WHERE modifier_group_id = %s \
                      """
        if not execute_query(check_query, (data['modifier_group_id'],), fetch=True):
            return jsonify({
                'status': 'error',
                'message': 'Modifier group not found',
                'error_code': 'NOT_FOUND'
            }), 404

        # First, delete all modifiers in this group to maintain referential integrity
        delete_modifiers_query = """
                                 DELETE \
                                 FROM restaurant_modifier
                                 WHERE modifier_group_id = %s \
                                 """
        execute_query(delete_modifiers_query, (data['modifier_group_id'],))

        # Then delete the modifier group
        delete_group_query = """
                             DELETE \
                             FROM restaurant_modifier_group
                             WHERE modifier_group_id = %s \
                             """
        execute_query(delete_group_query, (data['modifier_group_id'],))

        return jsonify({
            'status': 'success',
            'message': 'Modifier group and all associated modifiers deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error in delete_modifier_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting the modifier group',
            'error_code': str(e)
        }), 500


@bp.route('/list_item_modifier_groups', methods=['POST'])
def list_item_modifier_groups():
    """
    List all modifier groups associated with a specific menu item along with their modifiers

    Request body:
    {
        "item_id": 1  # Required
    }

    Returns:
        JSON response with list of modifier groups and their modifiers for the specified item
        {
            "status": "success",
            "data": [
                {
                    "modifier_group_id": 1,
                    "group_name": "Toppings",
                    "is_required": true,
                    "min_select": 1,
                    "max_select": 3,
                    "modifiers": [
                        {
                            "modifier_id": 1,
                            "name": "Extra Cheese",
                            "price_delta": 1.50,
                            "is_active": true
                        },
                        ...
                    ]
                }
            ],
            "count": 1
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if 'item_id' not in data or data['item_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: item_id',
                'error_code': 'MISSING_FIELDS'
            }), 400

        # Get all modifier groups for the item
        groups_query = """
                       SELECT g.modifier_group_id, \
                              g.name AS group_name, \
                              g.is_required, \
                              g.min_select, \
                              g.max_select
                       FROM restaurant_item_modifier_group ig
                                JOIN restaurant_modifier_group g
                                     ON ig.modifier_group_id = g.modifier_group_id
                       WHERE ig.item_id = %s
                       ORDER BY g.name \
                       """

        modifier_groups = execute_query(groups_query, (data['item_id'],), fetch=True)

        if not modifier_groups:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0
            })

        # Get all modifier group IDs
        group_ids = [str(group['modifier_group_id']) for group in modifier_groups]
        placeholders = ','.join(['%s'] * len(group_ids))

        # Get all active modifiers for these groups
        modifiers_query = f"""
            SELECT 
                modifier_id,
                modifier_group_id,
                name,
                price_delta,
                is_active
            FROM restaurant_modifier
            WHERE modifier_group_id IN ({placeholders})
            AND is_active = 1
            ORDER BY name
        """

        modifiers = execute_query(modifiers_query, tuple(group_ids), fetch=True)

        # Group modifiers by modifier_group_id
        modifiers_by_group = {}
        for modifier in modifiers:
            group_id = modifier['modifier_group_id']
            if group_id not in modifiers_by_group:
                modifiers_by_group[group_id] = []
            modifiers_by_group[group_id].append({
                'modifier_id': modifier['modifier_id'],
                'name': modifier['name'],
                'price_delta': float(modifier['price_delta']),
                'is_active': bool(modifier['is_active'])
            })

        # Add modifiers to each group
        for group in modifier_groups:
            group_id = group['modifier_group_id']
            group['modifiers'] = modifiers_by_group.get(group_id, [])

        return jsonify({
            'status': 'success',
            'data': modifier_groups,
            'count': len(modifier_groups)
        })

    except Exception as e:
        logger.error(f"Error in list_item_modifier_groups: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving modifier groups',
            'error_code': str(e)
        }), 500


@bp.route('/add_item_modifier_group', methods=['POST'])
def add_item_modifier_group():
    """
    Associate a modifier group with a menu item

    Request body:
    {
        "item_id": 1,            # Required
        "modifier_group_id": 1   # Required
    }

    Returns:
        JSON response with success/error message
        {
            "status": "success",
            "message": "Modifier group added to item successfully",
            "data": {
                "item_id": 1,
                "modifier_group_id": 1
            }
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['item_id', 'modifier_group_id']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]

        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'error_code': 'MISSING_FIELDS'
            }), 400

        item_id = data['item_id']
        option_group_id = data['modifier_group_id']

        # Check if the association already exists
        check_query = """
                      SELECT 1
                      FROM restaurant_item_modifier_group
                      WHERE item_id = %s \
                        AND modifier_group_id = %s \
                      """
        if execute_query(check_query, (item_id, option_group_id), fetch=True):
            return jsonify({
                'status': 'error',
                'message': 'This modifier group is already associated with the item',
                'error_code': 'DUPLICATE_ASSOCIATION'
            }), 400

        # Insert the new association
        insert_query = """
                       INSERT INTO restaurant_item_modifier_group
                           (item_id, modifier_group_id)
                       VALUES (%s, %s) \
                       """
        execute_query(insert_query, (item_id, option_group_id))

        return jsonify({
            'status': 'success',
            'message': 'Modifier group added to item successfully',
            'data': {
                'item_id': item_id,
                'modifier_group_id': option_group_id
            }
        }), 201

    except Exception as e:
        logger.error(f"Error in add_item_modifier_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while adding the modifier group to the item',
            'error_code': str(e)
        }), 500

@bp.route('/delete_item_modifier_group', methods=['POST'])
def delete_item_modifier_group():
    """
    Remove the association between a menu item and a modifier group

    Request body:
    {
        "item_id": 10,           # Required
        "modifier_group_id": 5   # Required
    }

    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['item_id', 'modifier_group_id']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]

        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'error_code': 'MISSING_FIELDS'
            }), 400

        item_id = data['item_id']
        option_group_id = data['modifier_group_id']

        # Check if the association exists first
        check_query = """
            SELECT 1 
            FROM restaurant_item_modifier_group 
            WHERE item_id = %s AND modifier_group_id = %s
            LIMIT 1
        """
        if not execute_query(check_query, (item_id, option_group_id), fetch=True):
            return jsonify({
                'status': 'error',
                'message': 'No matching association found between item and modifier group',
                'error_code': 'NOT_FOUND'
            }), 404

        # Delete the association
        delete_query = """
            DELETE FROM restaurant_item_modifier_group
            WHERE item_id = %s AND modifier_group_id = %s
        """
        execute_query(delete_query, (item_id, option_group_id))

        return jsonify({
            'status': 'success',
            'message': 'Modifier group removed from item successfully',
            'data': {
                'item_id': item_id,
                'modifier_group_id': option_group_id
            }
        })

    except Exception as e:
        logger.error(f"Error in delete_item_modifier_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while removing the modifier group from the item',
            'error_code': str(e)
        }), 500


@bp.route('/list_combos', methods=['POST'])
def list_combos():
    """
    List all combo menu items for a business
    
    Request body:
    {
        "business_id": 73  # Required
    }
    
    Returns:
        JSON response with list of combo items
        {
            "status": "success",
            "data": [
                {
                    "item_id": 1,
                    "name": "Combo Meal",
                    "description": "Combo description",
                    "price": 12.99,
                    "image_url": "http://example.com/image.jpg"
                },
                ...
            ]
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'business_id' not in data or data['business_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'business_id is required',
                'error_code': 'MISSING_BUSINESS_ID'
            }), 400
            
        # Query for combo items
        query = """
            SELECT 
                item_id,
                name,
                description,
                base_price,
                image_url
            FROM restaurant_item
            WHERE business_id = %s 
            AND is_combo = TRUE
            AND is_active = TRUE
            ORDER BY name
        """
        
        combos = execute_query(query, (data['business_id'],), fetch=True)
        
        return jsonify({
            'status': 'success',
            'data': combos or []
        })
        
    except Exception as e:
        logger.error(f"Error in list_combos: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching combo items',
            'error_code': str(e)
        }), 500


@bp.route('/list_combo_groups', methods=['POST'])
def list_combo_groups():
    """
    List all combo groups for a specific item
    
    Request body:
    {
        "item_id": 10  # Required
    }
    
    Returns:
        JSON response with list of combo groups for the specified item
        {
            "status": "success",
            "data": [
                {
                    "combo_group_id": 1,
                    "name": "Main Item",
                    "description": "Choose one main item",
                    "is_required": true,
                    "min_select": 1,
                    "max_select": 1
                },
                ...
            ]
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'item_id' not in data or data['item_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'item_id is required',
                'error_code': 'MISSING_ITEM_ID'
            }), 400
            
        # Query for combo groups
        query = """
            SELECT 
                cg.combo_group_id,
                cg.name,
                cg.min_select,
                cg.max_select
            FROM restaurant_combo_group cg
            WHERE cg.item_id = %s
            ORDER BY cg.combo_group_id
        """
        
        combo_groups = execute_query(query, (data['item_id'],), fetch=True)
        
        return jsonify({
            'status': 'success',
            'data': combo_groups or []
        })
        
    except Exception as e:
        logger.error(f"Error in list_combo_groups: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching combo groups',
            'error_code': str(e)
        }), 500


@bp.route('/list_combo_group_items', methods=['POST'])
def list_combo_group_items():
    """
    List all items in a specific combo group
    
    Request body:
    {
        "combo_group_id": 1  # Required
    }
    
    Returns:
        JSON response with list of items in the specified combo group
        {
            "status": "success",
            "data": [
                {
                    "combo_group_item_id": 1,
                    "combo_group_id": 1,
                    "allowed_item_id": 5,
                    "price_delta": 0.0,
                    "item_id": 5,
                    "item_name": "Cheeseburger",
                    "item_description": "Delicious cheeseburger",
                    "base_price": 8.99,
                    "is_combo": false,
                    "is_active": true,
                    "image_url": "http://example.com/burger.jpg",
                    "item_category_id": 1,
                    "category_name": "Burgers"
                },
                ...
            ]
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'combo_group_id' not in data or data['combo_group_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'combo_group_id is required',
                'error_code': 'MISSING_COMBO_GROUP_ID'
            }), 400
            
        # Query for combo group items
        query = """
            SELECT 
                gi.combo_group_item_id,
                gi.combo_group_id,
                gi.allowed_item_id,
                gi.price_delta,
                i.item_id,
                i.name AS item_name,
                i.description AS item_description,
                i.base_price,
                i.is_combo,
                i.is_active,
                i.image_url,
                i.item_category_id,
                ic.name AS category_name
            FROM restaurant_combo_group_item gi
            JOIN restaurant_item i 
                ON gi.allowed_item_id = i.item_id
            LEFT JOIN restaurant_item_category ic 
                ON i.item_category_id = ic.item_category_id
            WHERE gi.combo_group_id = %s
            ORDER BY i.name
        """
        
        items = execute_query(query, (data['combo_group_id'],), fetch=True)
        
        return jsonify({
            'status': 'success',
            'data': items or []
        })
        
    except Exception as e:
        logger.error(f"Error in list_combo_group_items: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching combo group items',
            'error_code': str(e)
        }), 500


@bp.route('/create_availability', methods=['POST'])
def create_availability():
    """
    Create a new availability record with time slots based on business hours

    Request body:
    {
        "business_id": 73,  # Required
        "name": "Standard Hours"  # Optional, default empty string
    }

    Returns:
        JSON response with created availability and its time slots
    """
    try:
        data = request.get_json()

        if 'business_id' not in data or data['business_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'business_id is required',
                'error_code': 'MISSING_BUSINESS_ID'
            }), 400

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Start transaction
            conn.start_transaction()

            # Create the main availability record
            insert_availability = """
                                  INSERT INTO restaurant_availability (business_id, name)
                                  VALUES (%s, %s) \
                                  """
            name = data.get('name', '')
            cursor.execute(insert_availability, (data['business_id'], name))
            availability_id = cursor.lastrowid

            # Get business hours for this business
            get_business_hours = """
                                 SELECT day_of_week, open_time, close_time, is_closed
                                 FROM business_hours
                                 WHERE business_id = %s \
                                 """
            cursor.execute(get_business_hours, (data['business_id'],))
            business_hours = cursor.fetchall()

            # Create availability details from business hours
            if business_hours:
                insert_detail = """
                                INSERT INTO restaurant_availability_detail
                                    (availability_id, day_of_week, open_time, close_time, is_closed)
                                VALUES (%s, %s, %s, %s, %s) \
                                """
                for hour in business_hours:
                    cursor.execute(insert_detail, (
                        availability_id,
                        hour['day_of_week'],
                        hour['open_time'],
                        hour['close_time'],
                        hour.get('is_closed', False)
                    ))

            # Commit the transaction
            conn.commit()

            # Get the created availability with its details
            get_availability = """
                               SELECT a.*,
                                      d.availability_detail_id, \
                                      d.day_of_week,
                                      d.open_time, \
                                      d.close_time, \
                                      d.is_closed
                               FROM restaurant_availability a
                                        LEFT JOIN restaurant_availability_detail d \
                                                  ON a.availability_id = d.availability_id
                               WHERE a.availability_id = %s
                               ORDER BY d.day_of_week, d.open_time \
                               """
            cursor.execute(get_availability, (availability_id,))
            rows = cursor.fetchall()

            # Format the response
            if not rows:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to create availability',
                    'error_code': 'CREATION_FAILED'
                }), 500

            availability = {
                'availability_id': rows[0]['availability_id'],
                'business_id': rows[0]['business_id'],
                'name': rows[0]['name'],
                'time_slots': []
            }

            for row in rows:
                if row['availability_detail_id']:  # Only add if there are details
                    availability['time_slots'].append({
                        'detail_id': row['availability_detail_id'],
                        'day_of_week': row['day_of_week'],
                        'open_time': str(row['open_time']) if row['open_time'] else None,
                        'close_time': str(row['close_time']) if row['close_time'] else None,
                        'is_closed': bool(row['is_closed'])
                    })

            return jsonify({
                'status': 'success',
                'message': 'Availability created successfully',
                'data': availability
            })

        except mysql.connector.Error as err:
            if conn and conn.is_connected():
                conn.rollback()
            logger.error(f"Database error in create_availability: {err}")
            return jsonify({
                'status': 'error',
                'message': 'Database error',
                'error_code': 'DATABASE_ERROR'
            }), 500
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    except Exception as e:
        logger.error(f"Error in create_availability: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while creating availability',
            'error_code': str(e)
        }), 500


@bp.route('/delete_availability', methods=['POST'])
def delete_availability():
    """
    Delete an availability record and all its associated time slots

    Request body:
    {
        "availability_id": 1  # Required
    }

    Returns:
        JSON response with success/error message
        {
            "status": "success",
            "message": "Availability and all associated time slots deleted successfully",
            "deleted_availability_id": 1
        }
    """
    try:
        data = request.get_json()

        if 'availability_id' not in data or data['availability_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'availability_id is required',
                'error_code': 'MISSING_AVAILABILITY_ID'
            }), 400

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Start transaction
            conn.start_transaction()

            # First, check if the availability exists
            check_query = """
                          SELECT * \
                          FROM restaurant_availability
                          WHERE availability_id = %s \
                          """
            cursor.execute(check_query, (data['availability_id'],))
            existing = cursor.fetchone()

            if not existing:
                return jsonify({
                    'status': 'error',
                    'message': 'Availability not found',
                    'error_code': 'NOT_FOUND'
                }), 404

            # First delete from restaurant_availability_detail
            delete_details_query = """
                                   DELETE \
                                   FROM restaurant_availability_detail
                                   WHERE availability_id = %s \
                                   """
            cursor.execute(delete_details_query, (data['availability_id'],))

            # Then delete from restaurant_menu_availability
            delete_menu_assoc_query = """
                                      DELETE \
                                      FROM restaurant_menu_availability
                                      WHERE availability_id = %s \
                                      """
            cursor.execute(delete_menu_assoc_query, (data['availability_id'],))

            # Finally, delete the main availability record
            delete_availability_query = """
                                        DELETE \
                                        FROM restaurant_availability
                                        WHERE availability_id = %s \
                                        """
            cursor.execute(delete_availability_query, (data['availability_id'],))

            # Commit the transaction
            conn.commit()

            return jsonify({
                'status': 'success',
                'message': 'Availability and all associated time slots deleted successfully',
                'deleted_availability_id': data['availability_id']
            })

        except mysql.connector.Error as err:
            if conn and conn.is_connected():
                conn.rollback()
            logger.error(f"Database error in delete_availability: {err}")
            return jsonify({
                'status': 'error',
                'message': 'Database error',
                'error_code': 'DATABASE_ERROR'
            }), 500
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    except Exception as e:
        logger.error(f"Error in delete_availability: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting availability',
            'error_code': str(e)
        }), 500


@bp.route('/assign_availability_to_menu', methods=['POST'])
def assign_availability_to_menu():
    """
    Assign an availability to a menu
    
    Request body:
    {
        "availability_id": 1,  # Required
        "menu_id": 1           # Required
    }
    
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        required_fields = ['availability_id', 'menu_id']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'error_code': 'MISSING_FIELDS'
            }), 400
            
        # Check if assignment already exists
        check_query = """
            SELECT * FROM restaurant_menu_availability
            WHERE menu_id = %s AND availability_id = %s
        """
        existing = execute_query(
            check_query, 
            (data['menu_id'], data['availability_id']), 
            fetch=True
        )
        
        if existing:
            return jsonify({
                'status': 'success',
                'message': 'This availability is already assigned to the menu',
                'data': existing[0]
            })
            
        # Create new assignment
        query = """
            INSERT INTO restaurant_menu_availability (menu_id, availability_id)
            VALUES (%s, %s)
        """
        execute_query(query, (data['menu_id'], data['availability_id']))
        
        return jsonify({
            'status': 'success',
            'message': 'Availability assigned to menu successfully'
        }), 201
        
    except mysql.connector.Error as err:
        logger.error(f"Database error in assign_availability_to_menu: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        logger.error(f"Error in assign_availability_to_menu: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while assigning availability to menu',
            'error_code': str(e)
        }), 500


@bp.route('/create_menu_section', methods=['POST'])
def create_menu_section():
    """
    Create a new menu section
    
    Request body:
    {
        "menu_id": 1,           # Required
        "name": "Appetizers",   # Required
        "description": "Start your meal right",  # Optional
        "display_order": 1      # Optional, defaults to 0
    }
    
    Returns:
        JSON response with the created menu section details
        {
            "status": "success",
            "data": {
                "menu_section_id": 1,
                "menu_id": 1,
                "name": "Appetizers",
                "description": "Start your meal right",
                "display_order": 1
            }
        }
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'menu_id' not in data or 'name' not in data:
        return jsonify({
            'status': 'error',
            'message': 'menu_id and name are required fields'
        }), 400
        
    menu_id = data['menu_id']
    name = data['name']
    description = data.get('description', '')
    display_order = data.get('display_order', 0)
    
    # Get business_id from menu to validate ownership
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get business_id from menu
        cursor.execute(
            "SELECT business_id FROM restaurant_menu WHERE menu_id = %s",
            (menu_id,)
        )
        menu = cursor.fetchone()
        
        if not menu:
            return jsonify({
                'status': 'error',
                'message': 'Menu not found'
            }), 404
            
        business_id = menu['business_id']
        
        # Insert the new menu section
        insert_query = """
            INSERT INTO restaurant_menu_section 
            (business_id, menu_id, name, description, display_order)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_query,
            (business_id, menu_id, name, description, display_order)
        )
        menu_section_id = cursor.lastrowid
        
        # Get the created menu section
        cursor.execute(
            "SELECT * FROM restaurant_menu_section WHERE menu_section_id = %s",
            (menu_section_id,)
        )
        created_section = cursor.fetchone()
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'data': created_section
        }), 201
        
    except mysql.connector.Error as err:
        conn.rollback()
        logger.error(f"Database error in create_menu_section: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'details': str(err)
        }), 500
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logger.error(f"Error in create_menu_section: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn is not None and conn.is_connected():
            conn.close()


@bp.route('/update_menu_section', methods=['POST'])
def update_menu_section():
    """
    Update an existing menu section
    
    Request body:
    {
        "menu_section_id": 1,      # Required
        "name": "Updated Name",    # Optional
        "description": "Updated description",  # Optional
        "display_order": 2         # Optional
    }
    
    Returns:
        JSON response with the updated menu section details
        {
            "status": "success",
            "data": {
                "menu_section_id": 1,
                "menu_id": 1,
                "name": "Updated Name",
                "description": "Updated description",
                "display_order": 2
            }
        }
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'menu_section_id' not in data:
        return jsonify({
            'status': 'error',
            'message': 'menu_section_id is required'
        }), 400
        
    menu_section_id = data['menu_section_id']
    
    # Build the update query based on provided fields
    update_fields = []
    params = []
    
    if 'name' in data:
        update_fields.append("name = %s")
        params.append(data['name'])
        
    if 'description' in data:
        update_fields.append("description = %s")
        params.append(data['description'])
        
    if 'display_order' in data:
        update_fields.append("display_order = %s")
        params.append(data['display_order'])
    
    if not update_fields:
        return jsonify({
            'status': 'error',
            'message': 'No fields to update. Provide at least one field to update (name, description, or display_order)'
        }), 400
    
    params.append(menu_section_id)  # For the WHERE clause
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if menu section exists
        cursor.execute(
            "SELECT * FROM restaurant_menu_section WHERE menu_section_id = %s",
            (menu_section_id,)
        )
        menu_section = cursor.fetchone()
        
        if not menu_section:
            return jsonify({
                'status': 'error',
                'message': 'Menu section not found'
            }), 404
        
        # Build and execute the update query
        update_query = """
            UPDATE restaurant_menu_section
            SET {}
            WHERE menu_section_id = %s
        """.format(", ".join(update_fields))
        
        cursor.execute(update_query, params)
        
        # Get the updated menu section
        cursor.execute(
            "SELECT * FROM restaurant_menu_section WHERE menu_section_id = %s",
            (menu_section_id,)
        )
        updated_section = cursor.fetchone()
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'data': updated_section
        })
        
    except mysql.connector.Error as err:
        conn.rollback()
        logger.error(f"Database error in update_menu_section: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'details': str(err)
        }), 500
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logger.error(f"Error in update_menu_section: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn is not None and conn.is_connected():
            conn.close()


@bp.route('/delete_menu_section', methods=['POST'])
def delete_menu_section():
    """
    Delete a menu section
    
    Request body:
    {
        "menu_section_id": 1  # Required
    }
    
    Returns:
        JSON response with success/error message
        {
            "status": "success",
            "message": "Menu section deleted successfully",
            "deleted_id": 1
        }
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'menu_section_id' not in data:
        return jsonify({
            'status': 'error',
            'message': 'menu_section_id is required'
        }), 400
        
    menu_section_id = data['menu_section_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if menu section exists
        cursor.execute(
            "SELECT menu_section_id FROM restaurant_menu_section WHERE menu_section_id = %s",
            (menu_section_id,)
        )
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Menu section not found'
            }), 404
        
        # First, delete all menu item associations with this section
        cursor.execute(
            "DELETE FROM restaurant_menu_section_item WHERE menu_section_id = %s",
            (menu_section_id,)
        )
        
        # Then delete the menu section
        cursor.execute(
            "DELETE FROM restaurant_menu_section WHERE menu_section_id = %s",
            (menu_section_id,)
        )
        
        if cursor.rowcount == 0:
            return jsonify({
                'status': 'error',
                'message': 'No menu section was deleted. It may have already been deleted.'
            }), 404
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Menu section deleted successfully',
            'deleted_id': menu_section_id
        })
        
    except mysql.connector.Error as err:
        conn.rollback()
        logger.error(f"Database error in delete_menu_section: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'details': str(err)
        }), 500
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logger.error(f"Error in delete_menu_section: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn is not None and conn.is_connected():
            conn.close()


@bp.route('/add_item_to_menu_section', methods=['POST'])
def add_item_to_menu_section():
    """
    Add a menu item to a menu section
    
    Request body:
    {
        "item_id": 1,           // Required
        "menu_section_id": 10   // Required
    }
    
    Returns:
        JSON response with success/error message
        {
            "status": "success",
            "message": "Menu item added to section successfully",
            "data": {
                "item_id": 1,
                "menu_section_id": 10
            }
        }
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'item_id' not in data or 'menu_section_id' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Both item_id and menu_section_id are required'
        }), 400
        
    item_id = data['item_id']
    menu_section_id = data['menu_section_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if the item exists
        cursor.execute(
            "SELECT item_id FROM restaurant_item WHERE item_id = %s",
            (item_id,)
        )
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Menu item not found'
            }), 404
        
        # Check if the menu section exists
        cursor.execute(
            "SELECT menu_section_id FROM restaurant_menu_section WHERE menu_section_id = %s",
            (menu_section_id,)
        )
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Menu section not found'
            }), 404
            
        # Check if the association already exists
        cursor.execute(
            """
            SELECT * FROM restaurant_menu_section_item 
            WHERE item_id = %s AND menu_section_id = %s
            """,
            (item_id, menu_section_id)
        )
        if cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'This menu item is already in the specified section'
            }), 400
        
        # Create the association
        cursor.execute(
            """
            INSERT INTO restaurant_menu_section_item 
            (item_id, menu_section_id)
            VALUES (%s, %s)
            """,
            (item_id, menu_section_id)
        )
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Menu item added to section successfully',
            'data': {
                'item_id': item_id,
                'menu_section_id': menu_section_id
            }
        }), 201
        
    except mysql.connector.Error as err:
        conn.rollback()
        logger.error(f"Database error in add_item_to_menu_section: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'details': str(err)
        }), 500
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logger.error(f"Error in add_item_to_menu_section: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn is not None and conn.is_connected():
            conn.close()


@bp.route('/delete_item_from_menu_section', methods=['POST'])
def delete_item_from_menu_section():
    """
    Remove a menu item from a menu section

    Request body:
    {
        "menu_section_id": 6,  # Required
        "item_id": 10          # Required
    }

    Returns:
        JSON response with success/error message
        {
            "status": "success",
            "message": "Item removed from menu section successfully",
            "data": {
                "item_id": 10,
                "menu_section_id": 6
            }
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'menu_section_id' not in data or 'item_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'menu_section_id and item_id are required'
            }), 400

        menu_section_id = data['menu_section_id']
        item_id = data['item_id']

        # First check if the menu section exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Check if the menu section exists
            cursor.execute(
                "SELECT menu_section_id FROM menu_section WHERE menu_section_id = %s",
                (menu_section_id,)
            )
            if not cursor.fetchone():
                return jsonify({
                    'status': 'error',
                    'message': 'Menu section not found'
                }), 404

            # Check if the item exists in the menu section
            cursor.execute(
                """
                SELECT item_id, menu_section_id
                FROM menu_section_item
                WHERE item_id = %s
                  AND menu_section_id = %s
                """,
                (item_id, menu_section_id)
            )
            if not cursor.fetchone():
                return jsonify({
                    'status': 'error',
                    'message': 'Item not found in the specified menu section'
                }), 404

            # Delete the item from the menu section
            cursor.execute(
                """
                DELETE
                FROM menu_section_item
                WHERE item_id = %s
                  AND menu_section_id = %s
                """,
                (item_id, menu_section_id)
            )

            conn.commit()

            return jsonify({
                'status': 'success',
                'message': 'Item removed from menu section successfully',
                'data': {
                    'item_id': item_id,
                    'menu_section_id': menu_section_id
                }
            })

        except mysql.connector.Error as err:
            conn.rollback()
            logger.error(f"Database error: {err}")
            return jsonify({
                'status': 'error',
                'message': 'Database error',
                'details': str(err)
            }), 500

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error in delete_item_from_menu_section: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while removing item from menu section',
            'details': str(e)
        }), 500

@bp.route('/list_availabilities', methods=['POST'])
def list_availabilities():
    """
    List all availabilities for a business with just ID and name

    Request body:
    {
        "business_id": 1  # Required
    }

    Returns:
        JSON response with list of availabilities containing only ID and name
        {
            "status": "success",
            "data": [
                {
                    "availability_id": 1,
                    "name": "Lunch Hours"
                },
                ...
            ]
        }
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'business_id' not in data:
        return jsonify({
            'status': 'error',
            'message': 'business_id is required'
        }), 400
        
    business_id = data['business_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query to get all availabilities for the business
        query = """
            SELECT availability_id, name
            FROM restaurant_availability
            WHERE business_id = %s
            ORDER BY name
        """
        cursor.execute(query, (business_id,))
        availabilities = cursor.fetchall()
        
        return jsonify({
            'status': 'success',
            'data': availabilities
        })
        
    except mysql.connector.Error as err:
        logger.error(f"Database error in list_availabilities: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'details': str(err)
        }), 500
        
    except Exception as e:
        logger.error(f"Error in list_availabilities: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn is not None and conn.is_connected():
            conn.close()


@bp.route('/list_availability_details', methods=['POST'])
def list_availability_details():
    """
    List all time slot details for a specific availability

    Request body:
    {
        "availability_id": 1  # Required
    }

    Returns:
        JSON response with list of time slot details
        {
            "status": "success",
            "data": [
                {
                    "availability_detail_id": 1,
                    "availability_id": 1,
                    "day_of_week": 1,
                    "open_time": "09:00:00",
                    "close_time": "17:00:00",
                    "is_closed": false
                },
                ...
            ]
        }
    """
    try:
        data = request.get_json()

        if 'availability_id' not in data or data['availability_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'availability_id is required',
                'error_code': 'MISSING_AVAILABILITY_ID'
            }), 400

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # First, verify the availability exists
            check_query = """
                          SELECT 1 \
                          FROM restaurant_availability
                          WHERE availability_id = %s \
                          """
            cursor.execute(check_query, (data['availability_id'],))
            if not cursor.fetchone():
                return jsonify({
                    'status': 'error',
                    'message': 'Availability not found',
                    'error_code': 'NOT_FOUND'
                }), 404

            # Get all time slot details for the availability
            query = """
                    SELECT 
                        availability_detail_id,
                        availability_id,
                        day_of_week,
                        open_time,
                        close_time,
                        is_closed
                    FROM restaurant_availability_detail
                    WHERE availability_id = %s
                    ORDER BY day_of_week, open_time
                    """

            cursor.execute(query, (data['availability_id'],))
            details = cursor.fetchall()

            # Convert boolean values from TINYINT(1) to Python bool
            for detail in details:
                if detail['open_time'] is not None:
                    if isinstance(detail['open_time'], timedelta):
                        # Convert timedelta to HH:MM:SS string
                        total_seconds = int(detail['open_time'].total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        detail['open_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        detail['open_time'] = str(detail['open_time'])

                if detail['close_time'] is not None:
                    if isinstance(detail['close_time'], timedelta):
                        # Convert timedelta to HH:MM:SS string
                        total_seconds = int(detail['close_time'].total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        detail['close_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        detail['close_time'] = str(detail['close_time'])

                detail['is_closed'] = bool(detail['is_closed'])

            return jsonify({
                'status': 'success',
                'data': details
            })

        except mysql.connector.Error as err:
            logger.error(f"Database error in list_availability_details: {err}")
            return jsonify({
                'status': 'error',
                'message': 'Database error',
                'error_code': 'DATABASE_ERROR'
            }), 500
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    except Exception as e:
        logger.error(f"Error in list_availability_details: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching availability details',
            'error_code': str(e)
        }), 500

@bp.route('/update_availability_detail', methods=['POST'])
def update_availability_detail():
    """
    Update an availability detail record

    Request body:
    {
        "availability_detail_id": 6,  # Required
        "day_of_week": 1,            # Optional: 1-7 (Monday-Sunday)
        "open_time": "09:00:00",     # Optional: Format "HH:MM:SS"
        "close_time": "17:00:00",    # Optional: Format "HH:MM:SS"
        "is_closed": false           # Optional: boolean
    }

    Returns:
        JSON response with the updated availability detail
        {
            "status": "success",
            "message": "Availability detail updated successfully",
            "data": {
                "availability_detail_id": 6,
                "availability_id": 1,
                "day_of_week": 1,
                "open_time": "09:00:00",
                "close_time": "17:00:00",
                "is_closed": false
            }
        }
    """
    try:
        data = request.get_json()

        if 'availability_detail_id' not in data or data['availability_detail_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'availability_detail_id is required',
                'error_code': 'MISSING_AVAILABILITY_DETAIL_ID'
            }), 400

        # Check if at least one field to update is provided
        updatable_fields = ['day_of_week', 'open_time', 'close_time', 'is_closed']
        if not any(field in data for field in updatable_fields):
            return jsonify({
                'status': 'error',
                'message': 'At least one field to update is required',
                'error_code': 'NO_FIELDS_TO_UPDATE'
            }), 400

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Start transaction
            conn.start_transaction()

            # Check if the detail exists
            check_query = """
                          SELECT * \
                          FROM restaurant_availability_detail
                          WHERE availability_detail_id = %s
                              FOR UPDATE \
                          """
            cursor.execute(check_query, (data['availability_detail_id'],))
            existing = cursor.fetchone()

            if not existing:
                return jsonify({
                    'status': 'error',
                    'message': 'Availability detail not found',
                    'error_code': 'NOT_FOUND'
                }), 404

            # Build the update query
            update_fields = []
            update_values = []

            if 'day_of_week' in data and data['day_of_week'] is not None:
                if not isinstance(data['day_of_week'], int) or data['day_of_week'] < 1 or data['day_of_week'] > 7:
                    return jsonify({
                        'status': 'error',
                        'message': 'day_of_week must be between 1 and 7',
                        'error_code': 'INVALID_DAY_OF_WEEK'
                    }), 400
                update_fields.append("day_of_week = %s")
                update_values.append(data['day_of_week'])

            if 'open_time' in data and data['open_time'] is not None:
                update_fields.append("open_time = %s")
                update_values.append(data['open_time'])

            if 'close_time' in data and data['close_time'] is not None:
                update_fields.append("close_time = %s")
                update_values.append(data['close_time'])

            if 'is_closed' in data and data['is_closed'] is not None:
                update_fields.append("is_closed = %s")
                update_values.append(bool(data['is_closed']))

            # Add the ID for the WHERE clause
            update_values.append(data['availability_detail_id'])

            # Execute the update
            update_query = f"""
                UPDATE restaurant_availability_detail
                SET {', '.join(update_fields)}
                WHERE availability_detail_id = %s
            """
            cursor.execute(update_query, update_values)

            # Get the updated record
            get_updated_query = """
                                SELECT availability_detail_id, \
                                       availability_id, \
                                       day_of_week, \
                                       open_time, \
                                       close_time, \
                                       is_closed
                                FROM restaurant_availability_detail
                                WHERE availability_detail_id = %s \
                                """
            cursor.execute(get_updated_query, (data['availability_detail_id'],))
            updated_detail = cursor.fetchone()

            # Format the time values
            if updated_detail:
                updated_detail['is_closed'] = bool(updated_detail['is_closed'])

                # Format open_time
                if updated_detail['open_time'] is not None:
                    if isinstance(updated_detail['open_time'], timedelta):
                        # Convert timedelta to HH:MM:SS string
                        total_seconds = int(updated_detail['open_time'].total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        updated_detail['open_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        updated_detail['open_time'] = str(updated_detail['open_time'])

                # Format close_time
                if updated_detail['close_time'] is not None:
                    if isinstance(updated_detail['close_time'], timedelta):
                        # Convert timedelta to HH:MM:SS string
                        total_seconds = int(updated_detail['close_time'].total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        updated_detail['close_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        updated_detail['close_time'] = str(updated_detail['close_time'])

            # Commit the transaction
            conn.commit()

            if not updated_detail:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to retrieve updated availability detail',
                    'error_code': 'UPDATE_FAILED'
                }), 500

            return jsonify({
                'status': 'success',
                'message': 'Availability detail updated successfully',
                'data': updated_detail
            })

        except mysql.connector.Error as err:
            if conn and conn.is_connected():
                conn.rollback()
            logger.error(f"Database error in update_availability_detail: {err}")
            return jsonify({
                'status': 'error',
                'message': 'Database error',
                'error_code': 'DATABASE_ERROR'
            }), 500
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    except Exception as e:
        logger.error(f"Error in update_availability_detail: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating availability detail',
            'error_code': str(e)
        }), 500

@bp.route('/create_item_category', methods=['POST'])
def create_item_category():
    """
    Create a new item category
    
    Request body:
    {
        "business_id": 1,              # Required
        "name": "Appetizers",         # Required
        "description": "Starters"     # Optional
    }
    
    Returns:
        JSON response with the created category details or error message
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['business_id', 'name']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                    'error_code': 'MISSING_REQUIRED_FIELD'
                }), 400
        
        business_id = data['business_id']
        name = data['name']
        description = data.get('description', '')
        
        # Check if category with same name already exists for this business
        existing = execute_query(
            """
            SELECT * 
            FROM restaurant_item_category 
            WHERE business_id = %s AND name = %s
            """,
            (business_id, name),
            fetch=True
        )
        
        if existing:
            return jsonify({
                'status': 'error',
                'message': 'An item category with this name already exists for this business',
                'error_code': 'DUPLICATE_CATEGORY_NAME'
            }), 400
            
        # Create new category
        result = execute_query(
            """
            INSERT INTO restaurant_item_category (business_id, name, description)
            VALUES (%s, %s, %s)
            """,
            (business_id, name, description),
            fetch=False
        )
        
        # Get the newly created category
        new_category = execute_query(
            """
            SELECT * 
            FROM restaurant_item_category 
            WHERE business_id = %s AND name = %s
            """,
            (business_id, name),
            fetch=True
        )
        
        if not new_category:
            raise Exception("Failed to create item category")
            
        return jsonify({
            'status': 'success',
            'message': 'Item category created successfully',
            'data': new_category[0]
        }), 201
        
    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err),
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/update_item_category', methods=['POST'])
def update_item_category():
    """
    Update an existing item category
    
    Request body:
    {
        "item_category_id": 1,         # Required
        "name": "Updated Name",        # Optional
        "description": "New description" # Optional
    }
    
    Returns:
        JSON response with the updated category details or error message
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'item_category_id' not in data or not data['item_category_id']:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: item_category_id',
                'error_code': 'MISSING_REQUIRED_FIELD'
            }), 400
        
        item_category_id = data['item_category_id']
        
        # Check if category exists
        category = execute_query(
            """
            SELECT * 
            FROM restaurant_item_category 
            WHERE item_category_id = %s
            """,
            (item_category_id,),
            fetch=True
        )
        
        if not category:
            return jsonify({
                'status': 'error',
                'message': 'Item category not found',
                'error_code': 'CATEGORY_NOT_FOUND'
            }), 404
            
        category = category[0]  # Get the first (and should be only) result
        
        # Prepare update fields
        update_fields = []
        update_values = []
        
        if 'name' in data and data['name'] != category['name']:
            # Check if the new name already exists for this business
            existing = execute_query(
                """
                SELECT * 
                FROM restaurant_item_category 
                WHERE business_id = %s 
                  AND name = %s 
                  AND item_category_id != %s
                """,
                (category['business_id'], data['name'], item_category_id),
                fetch=True
            )
            
            if existing:
                return jsonify({
                    'status': 'error',
                    'message': 'An item category with this name already exists for this business',
                    'error_code': 'DUPLICATE_CATEGORY_NAME'
                }), 400
            
            update_fields.append("name = %s")
            update_values.append(data['name'])
        
        if 'description' in data and data['description'] != category.get('description'):
            update_fields.append("description = %s")
            update_values.append(data['description'])
        
        # If no fields to update, return current data
        if not update_fields:
            return jsonify({
                'status': 'success',
                'message': 'No changes detected',
                'data': category
            })
        
        # Add the WHERE clause value
        update_values.append(item_category_id)
        
        # Build and execute update query
        update_query = """
            UPDATE restaurant_item_category 
            SET """ + ", ".join(update_fields) + """
            WHERE item_category_id = %s
        """
        
        # Execute the update
        execute_query(update_query, update_values, fetch=False)
        
        # Get the updated category
        updated_category = execute_query(
            """
            SELECT * 
            FROM restaurant_item_category 
            WHERE item_category_id = %s
            """,
            (item_category_id,),
            fetch=True
        )
        
        if not updated_category:
            raise Exception("Failed to update item category")
        
        return jsonify({
            'status': 'success',
            'message': 'Item category updated successfully',
            'data': updated_category[0]
        })
        
    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err),
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/delete_item_category', methods=['POST'])
def delete_item_category():
    """
    Delete an item category

    Request body:
    {
        "item_category_id": 1  # Required
    }

    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()

        # Validate required fields
        if 'item_category_id' not in data or not data['item_category_id']:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: item_category_id',
                'error_code': 'MISSING_REQUIRED_FIELD'
            }), 400

        item_category_id = data['item_category_id']

        # Check if category exists and get its details
        category = execute_query(
            "SELECT * FROM restaurant_item_category WHERE item_category_id = %s",
            (item_category_id,),
            fetch=True
        )

        if not category:
            return jsonify({
                'status': 'error',
                'message': 'Item category not found',
                'error_code': 'CATEGORY_NOT_FOUND'
            }), 404

        # Check if there are items using this category
        item_count = execute_query(
            "SELECT COUNT(*) as item_count FROM restaurant_item WHERE item_category_id = %s",
            (item_category_id,),
            fetch=True
        )

        if item_count and item_count[0]['item_count'] > 0:
            return jsonify({
                'status': 'error',
                'message': f'Cannot delete category: {item_count[0]["item_count"]} item(s) are using this category',
                'error_code': 'CATEGORY_IN_USE',
                'item_count': item_count[0]['item_count']
            }), 400

        # Delete the category
        execute_query(
            "DELETE FROM restaurant_item_category WHERE item_category_id = %s",
            (item_category_id,),
            fetch=False
        )

        return jsonify({
            'status': 'success',
            'message': 'Item category deleted successfully',
            'deleted_id': item_category_id
        })

    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err),
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/list_item_option_groups', methods=['POST'])
def list_item_option_groups():
    """
    List all option groups for a specific menu item
    
    Request body:
    {
        "item_id": 1  # Required
    }
    
    Returns:
        JSON response with list of option groups for the specified item
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'item_id' not in data or not data['item_id']:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: item_id',
                'error_code': 'MISSING_REQUIRED_FIELD'
            }), 400
        
        item_id = data['item_id']
        
        # Fetch option groups for the item
        option_groups = execute_query(
            """
            SELECT 
                option_group_id, 
                item_id
            FROM restaurant_item_option_group
            WHERE item_id = %s
            """,
            (item_id,),
            fetch=True
        )
        
        return jsonify({
            'status': 'success',
            'data': option_groups if option_groups else [],
            'count': len(option_groups) if option_groups else 0
        })
        
    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err),
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/create_item_option_group', methods=['POST'])
def create_item_option_group():
    """
    Create a new option group for a menu item

    Request body:
    {
        "item_id": 1,          # Required
        "option_group_id": 1   # Required
    }

    Returns:
        JSON response with the created option group details
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['item_id', 'option_group_id']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                    'error_code': 'MISSING_REQUIRED_FIELD'
                }), 400

        item_id = data['item_id']
        option_group_id = data['option_group_id']

        # Check if the option group is already associated with the item
        existing = execute_query(
            """
            SELECT * 
            FROM restaurant_item_option_group 
            WHERE item_id = %s AND option_group_id = %s
            """,
            (item_id, option_group_id),
            fetch=True
        )
        
        if existing:
            return jsonify({
                'status': 'error',
                'message': 'This option group is already associated with the specified item',
                'error_code': 'DUPLICATE_OPTION_GROUP',
                'item_id': item_id,
                'option_group_id': option_group_id
            }), 409  # 409 Conflict

        # Check if the item exists
        item = execute_query(
            "SELECT * FROM restaurant_item WHERE item_id = %s",
            (item_id,),
            fetch=True
        )
        if not item:
            return jsonify({
                'status': 'error',
                'message': f'Item with ID {item_id} not found',
                'error_code': 'ITEM_NOT_FOUND'
            }), 404

        # Check if the option group exists
        option_group = execute_query(
            "SELECT * FROM restaurant_option_group WHERE option_group_id = %s",
            (option_group_id,),
            fetch=True
        )
        if not option_group:
            return jsonify({
                'status': 'error',
                'message': f'Option group with ID {option_group_id} not found',
                'error_code': 'OPTION_GROUP_NOT_FOUND'
            }), 404

        # Insert the new option group
        execute_query(
            """
            INSERT INTO restaurant_item_option_group 
                (item_id, option_group_id)
            VALUES (%s, %s)
            """,
            (item_id, option_group_id),
            fetch=False
        )

        # Get the created option group
        option_group = execute_query(
            """
            SELECT * 
            FROM restaurant_item_option_group 
            WHERE item_id = %s AND option_group_id = %s
            """,
            (item_id, option_group_id),
            fetch=True
        )

        return jsonify({
            'status': 'success',
            'message': 'Option group created successfully',
            'data': option_group[0] if option_group else None
        }), 201

    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err),
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/list_option', methods=['POST'])
def list_item_options():
    """
    List all options for a specific option group
    
    Request body:
    {
        "option_group_id": 1  # Required
    }
    
    Returns:
        JSON response with list of options for the specified option group
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'option_group_id' not in data or not data['option_group_id']:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: option_group_id',
                'error_code': 'MISSING_REQUIRED_FIELD'
            }), 400
        
        option_group_id = data['option_group_id']
        
        # Check if option group exists
        option_group = execute_query(
            "SELECT * FROM restaurant_option_group WHERE option_group_id = %s",
            (option_group_id,),
            fetch=True
        )
        
        if not option_group:
            return jsonify({
                'status': 'error',
                'message': 'Option group not found',
                'error_code': 'OPTION_GROUP_NOT_FOUND'
            }), 404
        
        # Fetch options for the option group
        options = execute_query(
            """
            SELECT 
                option_id,
                option_group_id,
                name,
                price_delta,
                is_default
            FROM restaurant_option
            WHERE option_group_id = %s
            ORDER BY is_default DESC, name
            """,
            (option_group_id,),
            fetch=True
        )
        
        return jsonify({
            'status': 'success',
            'data': options if options else [],
            'count': len(options) if options else 0
        })
        
    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err),
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/create_option', methods=['POST'])
def create_option():
    """
    Create a new option for an option group

    Request body:
    {
        "option_group_id": 1,  // Required
        "name": "Large",      // Required
        "price": 2.99,        // Optional, defaults to 0
        "is_default": true,   // Optional, defaults to false
        "is_available": true  // Optional, defaults to true
    }
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['option_group_id', 'name']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {required_fields}',
                'error_code': 'MISSING_REQUIRED_FIELDS'
            }), 400

        # Set default values
        price = float(data.get('price', 0))
        is_default = bool(data.get('is_default', False))
        is_available = bool(data.get('is_available', True))

        # Get database connection and cursor
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if option group exists
        cursor.execute(
            "SELECT * FROM restaurant_option_group WHERE option_group_id = %s",
            (data['option_group_id'],)
        )
        option_group = cursor.fetchone()

        if not option_group:
            return jsonify({
                'status': 'error',
                'message': 'Option group not found',
                'error_code': 'OPTION_GROUP_NOT_FOUND'
            }), 404

        # Check if this is the first option in the group
        cursor.execute(
            "SELECT COUNT(*) as count FROM restaurant_option WHERE option_group_id = %s",
            (data['option_group_id'],)
        )
        count_result = cursor.fetchone()
        is_first_option = count_result['count'] == 0

        # If this is the first option, set it as default
        if is_first_option:
            is_default = True

        # If this option is being set as default, update other options in the group
        if is_default:
            cursor.execute(
                "UPDATE restaurant_option SET is_default = FALSE WHERE option_group_id = %s",
                (data['option_group_id'],)
            )

        # Create the option
        cursor.execute(
            """
            INSERT INTO restaurant_option
                (option_group_id, name, price_delta, is_default)
            VALUES (%s, %s, %s, %s)
            """,
            (
                data['option_group_id'],
                data['name'].strip(),
                price,
                is_default
            )
        )

        option_id = cursor.lastrowid

        # Get the created option
        cursor.execute(
            "SELECT * FROM restaurant_option WHERE option_id = %s",
            (option_id,)
        )
        new_option = cursor.fetchone()

        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Option created successfully',
            'data': {
                'option_id': new_option['option_id'],
                'option_group_id': new_option['option_group_id'],
                'name': new_option['name'],
                'price': float(new_option['price_delta']),
                'is_default': bool(new_option['is_default'])
            }
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error in create_option: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while creating the option',
            'error_code': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

@bp.route('/update_option', methods=['POST'])
def update_option():
    """
    Update an existing option

    Request body:
    {
        "option_id": 1,          // Required
        "name": "Updated Name",  // Optional
        "price": 3.99,           // Optional
        "is_default": true,      // Optional
        "is_available": true     // Optional
    }
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        if 'option_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'option_id is required',
                'error_code': 'MISSING_OPTION_ID'
            }), 400

        option_id = data['option_id']

        # Get database connection and cursor
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if option exists and get its current data
        cursor.execute(
            "SELECT * FROM restaurant_option WHERE option_id = %s",
            (option_id,)
        )
        option = cursor.fetchone()

        if not option:
            return jsonify({
                'status': 'error',
                'message': 'Option not found',
                'error_code': 'OPTION_NOT_FOUND'
            }), 404

        # Build update fields
        update_fields = []
        params = []

        if 'name' in data:
            update_fields.append("name = %s")
            params.append(data['name'].strip())

        if 'price_delta' in data:
            update_fields.append("price_delta = %s")
            params.append(float(data['price_delta']))

        # Handle is_default
        is_default_changed = 'is_default' in data
        new_is_default = bool(data.get('is_default', False))

        if is_default_changed:
            update_fields.append("is_default = %s")
            params.append(new_is_default)

            # If setting to default, update other options in the group
            if new_is_default:
                cursor.execute(
                    "UPDATE restaurant_option SET is_default = FALSE WHERE option_group_id = %s AND option_id != %s",
                    (option['option_group_id'], option_id)
                )

        # If there are fields to update
        if update_fields:
            params.append(option_id)  # For the WHERE clause

            query = f"""
                UPDATE restaurant_option 
                SET {', '.join(update_fields)}
                WHERE option_id = %s
            """

            cursor.execute(query, tuple(params))

        # Get the updated option
        cursor.execute(
            "SELECT * FROM restaurant_option WHERE option_id = %s",
            (option_id,)
        )
        updated_option = cursor.fetchone()

        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Option updated successfully',
            'data': {
                'option_id': updated_option['option_id'],
                'option_group_id': updated_option['option_group_id'],
                'name': updated_option['name'],
                'price': float(updated_option['price_delta']),
                'is_default': bool(updated_option['is_default'])
            }
        })

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error in update_option: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating the option',
            'error_code': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

@bp.route('/delete_option', methods=['POST'])
def delete_item_option():
    """
    Delete an option
    
    Request body:
    {
        "option_id": 1  # Required
    }
    
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'option_id' not in data or not data['option_id']:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: option_id',
                'error_code': 'MISSING_REQUIRED_FIELD'
            }), 400
        
        option_id = data['option_id']
        
        # Check if option exists
        option = execute_query(
            """
            SELECT o.*
            FROM restaurant_option o
            WHERE o.option_id = %s
            """,
            (option_id,),
            fetch=True
        )
        
        if not option:
            return jsonify({
                'status': 'error',
                'message': 'Option not found',
                'error_code': 'OPTION_NOT_FOUND'
            }), 404
        
        # Check if this option is used in any orders
        # Note: You may need to add this check if you have order_items_options table
        # order_count = execute_query(
        #     """
        #     SELECT COUNT(*) as count 
        #     FROM order_items_options 
        #     WHERE option_id = %s
        #     """,
        #     (option_id,),
        #     fetch=True
        # )
        # 
        # if order_count and order_count[0]['count'] > 0:
        #     return jsonify({
        #         'status': 'error',
        #         'message': f'Cannot delete option: used in {order_count[0]["count"]} order(s)',
        #         'error_code': 'OPTION_IN_USE',
        #         'order_count': order_count[0]['count']
        #     }), 400
        
        # Delete the option
        execute_query(
            "DELETE FROM restaurant_option WHERE option_id = %s",
            (option_id,),
            fetch=False
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Option deleted successfully',
            'deleted_id': option_id
        })
        
    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err),
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/delete_item_option_group', methods=['POST'])
def delete_item_option_group():
    """
    Delete an option group association from an item
    
    Request body:
    {
        "item_id": 4,          # Required
        "option_group_id": 2   # Required
    }
    
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['item_id', 'option_group_id']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                    'error_code': 'MISSING_REQUIRED_FIELD'
                }), 400
        
        item_id = data['item_id']
        option_group_id = data['option_group_id']
        
        # Check if the association exists
        existing = execute_query(
            """
            SELECT * 
            FROM restaurant_item_option_group 
            WHERE item_id = %s AND option_group_id = %s
            """,
            (item_id, option_group_id),
            fetch=True
        )
        
        if not existing:
            return jsonify({
                'status': 'error',
                'message': 'No matching association found between item and option group',
                'error_code': 'ASSOCIATION_NOT_FOUND',
                'item_id': item_id,
                'option_group_id': option_group_id
            }), 404
        
        # Delete the association
        execute_query(
            """
            DELETE FROM restaurant_item_option_group 
            WHERE item_id = %s AND option_group_id = %s
            """,
            (item_id, option_group_id),
            fetch=False
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Option group association removed successfully',
            'data': {
                'item_id': item_id,
                'option_group_id': option_group_id
            }
        })
        
    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err),
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/list_items_in_menu_section', methods=['POST'])
def list_items_in_menu_section():
    """
    List all items in a specific menu section with their option groups and modifier groups
    
    Request body:
    {
        "menu_section_id": 6  # Required
    }
    
    Returns:
        JSON response containing menu section items with their details
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'menu_section_id' not in data or data['menu_section_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: menu_section_id',
                'error_code': 'MISSING_REQUIRED_FIELD'
            }), 400
        
        menu_section_id = data['menu_section_id']
        
        # Get menu section details
        section = execute_query(
            """
            SELECT menu_section_id, name, description, display_order
            FROM restaurant_menu_section 
            WHERE menu_section_id = %s
            """,
            (menu_section_id,),
            fetch=True
        )
        
        if not section:
            return jsonify({
                'status': 'error',
                'message': 'Menu section not found',
                'error_code': 'SECTION_NOT_FOUND'
            }), 404
        
        # Get all items in the section with their details
        items = execute_query(
            """
            SELECT 
                i.item_id, 
                i.name, 
                i.description, 
                i.base_price,                
                i.image_url,
                i.calories,
                i.preparation_time,
                i.vegetarian,
                i.vegan,
                i.gluten_free,
                ms.display_order as section_display_order
            FROM restaurant_menu_section_item msi
            JOIN restaurant_item i ON msi.item_id = i.item_id
            JOIN restaurant_menu_section ms ON msi.menu_section_id = ms.menu_section_id
            WHERE msi.menu_section_id = %s
            ORDER BY ms.display_order, msi.display_order
            """,
            (menu_section_id,),
            fetch=True
        )
        
        if not items:
            return jsonify({
                'status': 'success',
                'data': {
                    'section': section[0],
                    'items': []
                }
            })
        
        # Get item IDs for batch queries
        item_ids = [str(item['id']) for item in items]
        item_ids_str = ','.join(item_ids)
        
        # Get all option groups for these items
        option_groups = execute_query(
            f"""
            SELECT 
                og.option_group_id,
                og.name as option_group_name,
                og.description as option_group_description,
                og.min_selections,
                og.max_selections,
                og.is_required,
                iog.item_id
            FROM restaurant_item_option_group iog
            JOIN restaurant_option_group og ON iog.option_group_id = og.option_group_id
            WHERE iog.item_id IN ({item_ids_str})
            ORDER BY iog.display_order
            """,
            fetch=True
        )
        
        # Get all options for these option groups
        if option_groups:
            option_group_ids = [str(og['option_group_id']) for og in option_groups]
            option_group_ids_str = ','.join(option_group_ids)
            
            options = execute_query(
                f"""
                SELECT 
                    o.option_id,
                    o.option_group_id,
                    o.name,
                    o.description,
                    o.price_adjustment,
                    o.display_order
                FROM restaurant_option o
                WHERE o.option_group_id IN ({option_group_ids_str})
                ORDER BY o.display_order
                """,
                fetch=True
            )
            
            # Group options by option group
            option_groups_with_options = {}
            for og in option_groups:
                og_id = og['option_group_id']
                option_groups_with_options[og_id] = {
                    'id': og_id,
                    'name': og['option_group_name'],
                    'description': og['option_group_description'],
                    'min_selections': og['min_selections'],
                    'max_selections': og['max_selections'],
                    'is_required': og['is_required'],
                    'options': [o for o in options if o['option_group_id'] == og_id]
                }
        
        # Get all modifier groups for these items
        modifier_groups = execute_query(
            f"""
            SELECT 
                mg.modifier_group_id,
                mg.name as modifier_group_name,
                mg.description as modifier_group_description,
                mg.min_selections,
                mg.max_selections,
                mg.is_required,
                img.item_id
            FROM restaurant_item_modifier_group img
            JOIN restaurant_modifier_group mg ON img.modifier_group_id = mg.modifier_group_id
            WHERE img.item_id IN ({item_ids_str})
            ORDER BY img.display_order
            """,
            fetch=True
        )
        
        # Get all modifiers for these modifier groups
        if modifier_groups:
            modifier_group_ids = [str(mg['modifier_group_id']) for mg in modifier_groups]
            modifier_group_ids_str = ','.join(modifier_group_ids)
            
            modifiers = execute_query(
                f"""
                SELECT 
                    m.modifier_id,
                    m.modifier_group_id,
                    m.name,
                    m.description,
                    m.price_adjustment,
                    m.display_order
                FROM restaurant_modifier m
                WHERE m.modifier_group_id IN ({modifier_group_ids_str})
                ORDER BY m.display_order
                """,
                fetch=True
            )
            
            # Group modifiers by modifier group
            modifier_groups_with_modifiers = {}
            for mg in modifier_groups:
                mg_id = mg['modifier_group_id']
                modifier_groups_with_modifiers[mg_id] = {
                    'id': mg_id,
                    'name': mg['modifier_group_name'],
                    'description': mg['modifier_group_description'],
                    'min_selections': mg['min_selections'],
                    'max_selections': mg['max_selections'],
                    'is_required': mg['is_required'],
                    'modifiers': [m for m in modifiers if m['modifier_group_id'] == mg_id]
                }
        
        # Build the response
        response_data = {
            'section': section[0],
            'items': []
        }
        
        for item in items:
            item_id = item['id']
            
            # Get option groups for this item
            item_option_groups = [
                option_groups_with_options[og['option_group_id']]
                for og in option_groups 
                if og['item_id'] == item_id and og['option_group_id'] in option_groups_with_options
            ]
            
            # Get modifier groups for this item
            item_modifier_groups = [
                modifier_groups_with_modifiers[mg['modifier_group_id']]
                for mg in modifier_groups 
                if mg['item_id'] == item_id and mg['modifier_group_id'] in modifier_groups_with_modifiers
            ]
            
            # Add item with its option groups and modifier groups
            response_data['items'].append({
                'id': item_id,
                'name': item['name'],
                'description': item['description'],
                'price': float(item['price']) if item['price'] is not None else None,
                'display_order': item['display_order'],
                'image_url': item['image_url'],
                'calories': item['calories'],
                'preparation_time': item['preparation_time'],
                'dietary_info': {
                    'vegetarian': bool(item['vegetarian']),
                    'vegan': bool(item['vegan']),
                    'gluten_free': bool(item['gluten_free'])
                },
                'option_groups': item_option_groups,
                'modifier_groups': item_modifier_groups
            })
        
        return jsonify({
            'status': 'success',
            'data': response_data
        })
        
    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error': str(err),
            'error_code': 'DATABASE_ERROR'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/list_tags', methods=['POST'])
def list_tags():
    """
    List all available restaurant tags for a business
    
    Request body:
    {
        "business_id": 73  // Required
    }
    
    Returns:
        JSON response with list of all tags for the business
        {
            "status": "success",
            "data": [
                {
                    "tag_id": 1,
                    "business_id": 73,
                    "name": "Vegetarian"
                },
                ...
            ]
        }
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
        
        # Get all tags for the business
        tags = execute_query(
            """
            SELECT tag_id, business_id, name 
            FROM restaurant_tag 
            WHERE business_id = %s
            ORDER BY name
            """,
            (business_id,),
            fetch=True
        )
        
        return jsonify({
            'status': 'success',
            'data': tags or []
        })
        
    except Exception as e:
        logger.error(f"Error in list_tags: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching tags',
            'error_code': str(e)
        }), 500

@bp.route('/create_tag', methods=['POST'])
def create_tag():
    """
    Create a new restaurant tag
    
    Request body:
    {
        "business_id": 73,  // Required
        "name": "Gluten Free"  // Required, must be unique per business
    }
    
    Returns:
        JSON response with the created tag
        {
            "status": "success",
            "message": "Tag created successfully",
            "data": {
                "tag_id": 1,
                "business_id": 73,
                "name": "Gluten Free"
            }
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'business_id' not in data or 'name' not in data or not data['name'].strip():
            return jsonify({
                'status': 'error',
                'message': 'Business ID and tag name are required',
                'error_code': 'MISSING_FIELDS'
            }), 400
            
        business_id = data['business_id']
        tag_name = data['name'].strip()
        
        # Check if tag already exists for this business
        existing_tag = execute_query(
            """
            SELECT tag_id, name 
            FROM restaurant_tag 
            WHERE business_id = %s AND name = %s
            """,
            (business_id, tag_name),
            fetch=True
        )
        
        if existing_tag:
            return jsonify({
                'status': 'error',
                'message': f'A tag with the name "{tag_name}" already exists for this business',
                'error_code': 'DUPLICATE_TAG'
            }), 400
            
        # Create new tag
        tag_id = execute_query(
            """
            INSERT INTO restaurant_tag (business_id, name) 
            VALUES (%s, %s)
            """,
            (business_id, tag_name)
        )
        
        # Get the created tag
        created_tag = execute_query(
            """
            SELECT tag_id, business_id, name 
            FROM restaurant_tag 
            WHERE tag_id = %s
            """,
            (tag_id,),
            fetch=True
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Tag created successfully',
            'data': created_tag[0] if created_tag else None
        })
        
    except Exception as e:
        logger.error(f"Error in create_tag: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while creating the tag',
            'error_code': str(e)
        }), 500

@bp.route('/update_tag', methods=['POST'])
def update_tag():
    """
    Update an existing restaurant tag
    
    Request body:
    {
        "tag_id": 1,           // Required
        "name": "Vegetarian"   // Required, new name for the tag
    }
    
    Returns:
        JSON response with the updated tag
        {
            "status": "success",
            "message": "Tag updated successfully",
            "data": {
                "tag_id": 1,
                "name": "Vegetarian"
            }
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'tag_id' not in data or 'name' not in data or not data['name'].strip():
            return jsonify({
                'status': 'error',
                'message': 'Tag ID and name are required',
                'error_code': 'MISSING_FIELDS'
            }), 400
            
        tag_id = data['tag_id']
        new_name = data['name'].strip()
        
        # Check if tag exists
        existing_tag = execute_query(
            "SELECT tag_id FROM restaurant_tag WHERE tag_id = %s",
            (tag_id,),
            fetch=True
        )
        
        if not existing_tag:
            return jsonify({
                'status': 'error',
                'message': 'Tag not found',
                'error_code': 'TAG_NOT_FOUND'
            }), 404
            
        # Check if new name is already taken
        name_taken = execute_query(
            "SELECT tag_id FROM restaurant_tag WHERE name = %s AND tag_id != %s",
            (new_name, tag_id),
            fetch=True
        )
        
        if name_taken:
            return jsonify({
                'status': 'error',
                'message': 'A tag with this name already exists',
                'error_code': 'DUPLICATE_TAG'
            }), 400
            
        # Update tag
        execute_query(
            "UPDATE restaurant_tag SET name = %s WHERE tag_id = %s",
            (new_name, tag_id)
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Tag updated successfully',
            'data': {
                'tag_id': tag_id,
                'name': new_name
            }
        })
        
    except Exception as e:
        logger.error(f"Error in update_tag: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating the tag',
            'error_code': str(e)
        }), 500

@bp.route('/delete_tag', methods=['POST'])
def delete_tag():
    """
    Delete a restaurant tag and its associations
    
    Request body:
    {
        "tag_id": 1  // Required
    }
    
    Returns:
        JSON response with success/error message
        {
            "status": "success",
            "message": "Tag deleted successfully"
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'tag_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Tag ID is required',
                'error_code': 'MISSING_FIELD'
            }), 400
            
        tag_id = data['tag_id']
        
        # Check if tag exists
        existing_tag = execute_query(
            "SELECT tag_id FROM restaurant_tag WHERE tag_id = %s",
            (tag_id,),
            fetch=True
        )
        
        if not existing_tag:
            return jsonify({
                'status': 'error',
                'message': 'Tag not found',
                'error_code': 'TAG_NOT_FOUND'
            }), 404
            
        # First, delete all item associations
        execute_query(
            "DELETE FROM restaurant_item_tag WHERE tag_id = %s",
            (tag_id,)
        )
        
        # Then delete the tag
        execute_query(
            "DELETE FROM restaurant_tag WHERE tag_id = %s",
            (tag_id,)
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Tag deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in delete_tag: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting the tag',
            'error_code': str(e)
        }), 500

@bp.route('/list_item_tags', methods=['POST'])
def list_item_tags():
    """
    List all tags for a specific menu item
    
    Request body:
    {
        "item_id": 1  // Required
    }
    
    Returns:
        JSON response with list of tags for the item
        {
            "status": "success",
            "data": [
                {
                    "tag_id": 1,
                    "name": "Vegetarian"
                },
                ...
            ]
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'item_id' not in data or not data['item_id']:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: item_id',
                'error_code': 'MISSING_REQUIRED_FIELD'
            }), 400
            
        item_id = data['item_id']
        
        # Get all tags for the item
        tags = execute_query(
            """
            SELECT t.tag_id, t.name 
            FROM restaurant_tag t
            JOIN restaurant_item_tag it ON t.tag_id = it.tag_id
            WHERE it.item_id = %s
            ORDER BY t.name
            """,
            (item_id,),
            fetch=True
        )
        
        return jsonify({
            'status': 'success',
            'data': tags or []
        })
        
    except Exception as e:
        logger.error(f"Error in list_item_tags: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching item tags',
            'error_code': str(e)
        }), 500

@bp.route('/create_item_tag', methods=['POST'])
def add_item_tag():
    """
    Add a tag to a menu item
    
    Request body:
    {
        "item_id": 1,  // Required
        "tag_id": 1    // Required
    }
    
    Returns:
        JSON response with success/error message
        {
            "status": "success",
            "message": "Tag added to item successfully"
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'item_id' not in data or 'tag_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Item ID and Tag ID are required',
                'error_code': 'MISSING_FIELDS'
            }), 400
            
        item_id = data['item_id']
        tag_id = data['tag_id']
        
        # Check if item exists
        item = execute_query(
            "SELECT item_id FROM restaurant_item WHERE item_id = %s",
            (item_id,),
            fetch=True
        )
        
        if not item:
            return jsonify({
                'status': 'error',
                'message': 'Menu item not found',
                'error_code': 'ITEM_NOT_FOUND'
            }), 404
            
        # Check if tag exists
        tag = execute_query(
            "SELECT tag_id FROM restaurant_tag WHERE tag_id = %s",
            (tag_id,),
            fetch=True
        )
        
        if not tag:
            return jsonify({
                'status': 'error',
                'message': 'Tag not found',
                'error_code': 'TAG_NOT_FOUND'
            }), 404
            
        # Check if association already exists
        existing = execute_query(
            "SELECT * FROM restaurant_item_tag WHERE item_id = %s AND tag_id = %s",
            (item_id, tag_id),
            fetch=True
        )
        
        if existing:
            return jsonify({
                'status': 'error',
                'message': 'This tag is already associated with the item',
                'error_code': 'DUPLICATE_ASSOCIATION'
            }), 400
            
        # Create the association
        execute_query(
            "INSERT INTO restaurant_item_tag (item_id, tag_id) VALUES (%s, %s)",
            (item_id, tag_id)
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Tag added to item successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in add_item_tag: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while adding the tag to the item',
            'error_code': str(e)
        }), 500

@bp.route('/delete_item_tag', methods=['POST'])
def delete_item_tag():
    """
    Remove a tag association from a menu item
    
    Request body:
    {
        "item_id": 1,  # Required
        "tag_id": 1    # Required
    }
    
    Returns:
        JSON response with success/error message
        {
            "status": "success",
            "message": "Tag removed from item successfully"
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'item_id' not in data or 'tag_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'item_id and tag_id are required',
                'error_code': 'MISSING_REQUIRED_FIELDS'
            }), 400
            
        item_id = data['item_id']
        tag_id = data['tag_id']
        
        # Check if the association exists first
        association = execute_query(
            "SELECT * FROM restaurant_item_tag WHERE item_id = %s AND tag_id = %s",
            (item_id, tag_id),
            fetch=True
        )
        
        if not association:
            return jsonify({
                'status': 'error',
                'message': 'The specified tag is not associated with this item',
                'error_code': 'ASSOCIATION_NOT_FOUND'
            }), 404
            
        # Delete the association
        execute_query(
            "DELETE FROM restaurant_item_tag WHERE item_id = %s AND tag_id = %s",
            (item_id, tag_id)
        )
            
        return jsonify({
            'status': 'success',
            'message': 'Tag removed from item successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in delete_item_tag: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while removing the tag from the item',
            'error_code': str(e)
        }), 500

@bp.route('/list_option_groups', methods=['POST'])
def list_option_groups():
    """
    List all option groups for a business
    
    Request body:
    {
        "business_id": 73  // Required
    }
    
    Returns:
        JSON response with list of option groups
        {
            "status": "success",
            "data": [
                {
                    "option_group_id": 1,
                    "name": "Size",
                    "is_required": true,
                    "min_select": 1,
                    "max_select": 1,
                    "display_order": 0,
                    "options": [
                        {
                            "option_id": 1,
                            "name": "Small",
                            "price_delta": 0.00,
                            "is_default": false,
                            "display_order": 0
                        }
                    ]
                }
            ]
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'business_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'business_id is required in the request body',
                'error_code': 'MISSING_BUSINESS_ID'
            }), 400
            
        business_id = data['business_id']
            
        # Get all option groups for the business
        option_groups = execute_query(
            """
            SELECT 
                option_group_id, name, is_required, 
                min_select, max_select, display_order
            FROM restaurant_option_group 
            WHERE business_id = %s
            ORDER BY display_order, name
            """,
            (business_id,),
            fetch=True
        )
        
        if not option_groups:
            return jsonify({
                'status': 'success',
                'data': []
            })
        
        # Get options for each group
        result = []
        for group in option_groups:
            options = execute_query(
                """
                SELECT 
                    option_id, name, price_delta, 
                    is_default, display_order
                FROM restaurant_option 
                WHERE option_group_id = %s
                ORDER BY display_order, name
                """,
                (group['option_group_id'],),
                fetch=True
            )
            
            result.append({
                'option_group_id': group['option_group_id'],
                'name': group['name'],
                'is_required': bool(group['is_required']),
                'min_select': group['min_select'],
                'max_select': group['max_select'],
                'display_order': group['display_order'],
                'options': [{
                    'option_id': opt['option_id'],
                    'name': opt['name'],
                    'price_delta': float(opt['price_delta']) if opt['price_delta'] is not None else 0.00,
                    'is_default': bool(opt['is_default']),
                    'display_order': opt['display_order']
                } for opt in (options or [])]
            })
            
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error in list_option_groups: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving option groups',
            'error_code': str(e)
        }), 500


@bp.route('/create_option_group', methods=['POST'])
def create_option_group():
    """
    Create a new option group

    Request body:
    {
        "business_id": 73,      // Required
        "name": "Drink Size",  // Required
        "is_required": true,   // Optional, defaults to false
        "min_select": 1,       // Optional, defaults to 0
        "max_select": 1,       // Optional, defaults to 1
        "display_order": 0     // Optional, defaults to 0
    }

    Returns:
        JSON response with the created option group details
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['business_id', 'name']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {required_fields}',
                'error_code': 'MISSING_REQUIRED_FIELDS'
            }), 400

        # Set default values for optional fields
        is_required = data.get('is_required', False)
        min_select = data.get('min_select', 0)
        max_select = data.get('max_select', 1)
        display_order = data.get('display_order', 0)

        # Validate min_select and max_select
        if min_select < 0 or max_select < 1 or min_select > max_select:
            return jsonify({
                'status': 'error',
                'message': 'Invalid min_select or max_select values',
                'error_code': 'INVALID_SELECTION_LIMITS'
            }), 400

        # Get database connection and cursor
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if business exists
        cursor.execute(
            "SELECT business_id FROM business WHERE business_id = %s",
            (data['business_id'],)
        )
        business = cursor.fetchone()

        if not business:
            return jsonify({
                'status': 'error',
                'message': 'Business not found',
                'error_code': 'BUSINESS_NOT_FOUND'
            }), 404

        # Check if option group with same name already exists for this business
        cursor.execute(
            """
            SELECT *
            FROM restaurant_option_group
            WHERE business_id = %s
              AND name = %s
            """,
            (data['business_id'], data['name'].strip())
        )
        existing = cursor.fetchone()

        if existing:
            return jsonify({
                'status': 'error',
                'message': 'An option group with this name already exists for this business',
                'error_code': 'DUPLICATE_OPTION_GROUP_NAME'
            }), 400

        # Create the option group
        cursor.execute(
            """
            INSERT INTO restaurant_option_group
                (business_id, name, is_required, min_select, max_select, display_order)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                data['business_id'],
                data['name'].strip(),
                is_required,
                min_select,
                max_select,
                display_order
            )
        )

        # Get the ID of the newly created option group
        option_group_id = cursor.lastrowid

        # Get the newly created option group
        cursor.execute(
            """
            SELECT *
            FROM restaurant_option_group
            WHERE option_group_id = %s
            """,
            (option_group_id,)
        )
        new_option_group = cursor.fetchone()

        if not new_option_group:
            conn.rollback()
            return jsonify({
                'status': 'error',
                'message': 'Failed to create option group',
                'error_code': 'CREATION_FAILED'
            }), 500

        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Option group created successfully',
            'data': {
                'option_group_id': option_group_id,
                'business_id': new_option_group['business_id'],
                'name': new_option_group['name'],
                'is_required': bool(new_option_group['is_required']),
                'min_select': new_option_group['min_select'],
                'max_select': new_option_group['max_select'],
                'display_order': new_option_group['display_order']
            }
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error in create_option_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while creating the option group',
            'error_code': str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@bp.route('/update_option_group', methods=['POST'])
def update_option_group():
    """
    Update an existing option group

    Request body:
    {
        "option_group_id": 1,      // Required
        "name": "Updated Name",    // Optional
        "is_required": true,       // Optional
        "min_select": 1,           // Optional
        "max_select": 3,           // Optional
        "display_order": 2         // Optional
    }

    Returns:
        JSON response with the updated option group details
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        if 'option_group_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'option_group_id is required',
                'error_code': 'MISSING_OPTION_GROUP_ID'
            }), 400

        option_group_id = data['option_group_id']

        # Get database connection and cursor
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if option group exists
        cursor.execute(
            "SELECT * FROM restaurant_option_group WHERE option_group_id = %s",
            (option_group_id,)
        )
        option_group = cursor.fetchone()

        if not option_group:
            return jsonify({
                'status': 'error',
                'message': 'Option group not found',
                'error_code': 'OPTION_GROUP_NOT_FOUND'
            }), 404

        # Build update fields
        update_fields = []
        params = []

        if 'name' in data:
            update_fields.append("name = %s")
            params.append(data['name'].strip())

        if 'is_required' in data:
            update_fields.append("is_required = %s")
            params.append(bool(data['is_required']))

        if 'min_select' in data or 'max_select' in data:
            # Get current values if not all are provided
            min_select = data.get('min_select', option_group['min_select'])
            max_select = data.get('max_select', option_group['max_select'])

            # Validate min_select and max_select
            if min_select < 0 or max_select < 1 or min_select > max_select:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid min_select or max_select values',
                    'error_code': 'INVALID_SELECTION_LIMITS'
                }), 400

            if 'min_select' in data:
                update_fields.append("min_select = %s")
                params.append(min_select)
            if 'max_select' in data:
                update_fields.append("max_select = %s")
                params.append(max_select)

        if 'display_order' in data:
            update_fields.append("display_order = %s")
            params.append(int(data['display_order']))

        # If there are fields to update
        if update_fields:
            params.append(option_group_id)  # For the WHERE clause

            query = f"""
                UPDATE restaurant_option_group 
                SET {', '.join(update_fields)}
                WHERE option_group_id = %s
            """

            cursor.execute(query, tuple(params))
            conn.commit()

        # Get the updated option group
        cursor.execute(
            "SELECT * FROM restaurant_option_group WHERE option_group_id = %s",
            (option_group_id,)
        )
        updated_group = cursor.fetchone()

        if not updated_group:
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve updated option group',
                'error_code': 'UPDATE_RETRIEVAL_FAILED'
            }), 500

        return jsonify({
            'status': 'success',
            'message': 'Option group updated successfully',
            'data': {
                'option_group_id': updated_group['option_group_id'],
                'business_id': updated_group['business_id'],
                'name': updated_group['name'],
                'is_required': bool(updated_group['is_required']),
                'min_select': updated_group['min_select'],
                'max_select': updated_group['max_select'],
                'display_order': updated_group['display_order']
            }
        })

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error in update_option_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating the option group',
            'error_code': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@bp.route('/delete_option_group', methods=['POST'])
def delete_option_group():
    """
    Delete an option group

    Request body:
    {
        "option_group_id": 1  // Required
    }

    Returns:
        JSON response with success or error message
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        if 'option_group_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'option_group_id is required',
                'error_code': 'MISSING_OPTION_GROUP_ID'
            }), 400

        option_group_id = data['option_group_id']

        # Get database connection and cursor
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if option group exists
        cursor.execute(
            "SELECT * FROM restaurant_option_group WHERE option_group_id = %s",
            (option_group_id,)
        )
        option_group = cursor.fetchone()

        if not option_group:
            return jsonify({
                'status': 'error',
                'message': 'Option group not found',
                'error_code': 'OPTION_GROUP_NOT_FOUND'
            }), 404

        # First, check if there are any menu items using this option group
        cursor.execute(
            "SELECT COUNT(*) as count FROM restaurant_item_option_group WHERE option_group_id = %s",
            (option_group_id,)
        )
        count_result = cursor.fetchone()

        if count_result and count_result['count'] > 0:
            return jsonify({
                'status': 'error',
                'message': 'Cannot delete option group because it is being used by one or more menu items',
                'error_code': 'OPTION_GROUP_IN_USE'
            }), 400

        # Delete the option group
        cursor.execute(
            "DELETE FROM restaurant_option_group WHERE option_group_id = %s",
            (option_group_id,)
        )

        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Option group deleted successfully'
        })

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error in delete_option_group: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting the option group',
            'error_code': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@bp.route('/list_item_category_map', methods=['POST'])
def list_item_category_map():
    """
    List all category mappings for an item
    
    Request body:
    {
        "item_id": 1  # Required
    }
    
    Returns:
        JSON response with list of category mappings for the specified item
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'item_id' not in data or not data['item_id']:
            return jsonify({
                'status': 'error',
                'message': 'Item ID is required',
                'error_code': 'MISSING_ITEM_ID'
            }), 400
            
        # Get category mappings for the item
        category_mappings = execute_query(
            """
            SELECT m.item_id, m.item_category_id, c.name as category_name
            FROM restaurant_item_category_map m
            JOIN restaurant_item_category c ON m.item_category_id = c.item_category_id
            WHERE m.item_id = %s
            ORDER BY c.name
            """,
            (data['item_id'],),
            fetch=True
        )
        
        return jsonify({
            'status': 'success',
            'data': category_mappings or [],
            'count': len(category_mappings) if category_mappings else 0
        })
        
    except mysql.connector.Error as err:
        logger.error(f"Database error in list_item_category_map: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR'
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in list_item_category_map: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/create_item', methods=['POST'])
def create_item():
    """
    Create a new menu item

    Request body:
    {
        "business_id": 1,           # Required
        "name": "Cheeseburger",     # Required
        "description": "Delicious cheeseburger with cheese",  # Optional
        "base_price": 9.99,        # Required
        "calories": 800,           # Optional
        "preparation_time": 15,     # Optional, in minutes
        "is_combo": false,         # Optional, defaults to false
        "is_active": true,         # Optional, defaults to true
        "image_url": "http://example.com/burger.jpg"  # Optional
    }

    Returns:
        JSON response with the created item details or error message
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['business_id', 'name', 'base_price']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                    'error_code': f'MISSING_{field.upper()}'
                }), 400

        # Set default values for optional fields
        description = data.get('description', '')
        calories = data.get('calories')
        preparation_time = data.get('preparation_time')
        is_combo = data.get('is_combo', False)
        is_active = data.get('is_active', True)
        image_url = data.get('image_url')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if business exists
        cursor.execute(
            "SELECT business_id FROM business WHERE business_id = %s",
            (data['business_id'],)
        )
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Business not found',
                'error_code': 'BUSINESS_NOT_FOUND'
            }), 404

        # Check for duplicate item name in the same business
        cursor.execute(
            """
            SELECT item_id
            FROM restaurant_item
            WHERE business_id = %s
              AND name = %s
            """,
            (data['business_id'], data['name'].strip())
        )
        if cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'An item with this name already exists for this business',
                'error_code': 'DUPLICATE_ITEM_NAME'
            }), 400

        # Create the item
        cursor.execute(
            """
            INSERT INTO restaurant_item (business_id, name, description, base_price,
                                         calories, preparation_time, is_combo, is_active, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data['business_id'],
                data['name'].strip(),
                description,
                float(data['base_price']),
                calories,
                preparation_time,
                is_combo,
                is_active,
                image_url
            )
        )

        item_id = cursor.lastrowid

        # Get the created item
        cursor.execute(
            """
            SELECT *
            FROM restaurant_item
            WHERE item_id = %s
            """,
            (item_id,)
        )

        item = cursor.fetchone()
        conn.commit()

        # Convert Decimal to float for JSON serialization
        if item:
            item['base_price'] = float(item['base_price']) if item['base_price'] is not None else None

        return jsonify({
            'status': 'success',
            'message': 'Menu item created successfully',
            'data': item
        }), 201

    except ValueError as ve:
        if conn:
            conn.rollback()
        logger.error(f"Value error in create_item: {ve}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid value provided',
            'error_code': 'INVALID_VALUE',
            'details': str(ve)
        }), 400

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        logger.error(f"Database error in create_item: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR',
            'details': str(err)
        }), 500

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Unexpected error in create_item: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@bp.route('/update_item', methods=['POST'])
def update_item():
    """
    Update an existing menu item

    Request body:
    {
        "item_id": 1,                   # Required
        "name": "Updated Burger",       # Optional
        "description": "New description", # Optional
        "base_price": 10.99,           # Optional
        "calories": 850,                # Optional
        "preparation_time": 20,         # Optional, in minutes
        "is_combo": false,              # Optional
        "is_active": true,              # Optional
        "image_url": "http://example.com/new.jpg"  # Optional (set to empty string to remove)
    }

    Returns:
        JSON response with the updated item details or error message
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        if 'item_id' not in data or data['item_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'Item ID is required',
                'error_code': 'MISSING_ITEM_ID'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if item exists
        cursor.execute(
            "SELECT * FROM restaurant_item WHERE item_id = %s",
            (data['item_id'],)
        )
        existing_item = cursor.fetchone()

        if not existing_item:
            return jsonify({
                'status': 'error',
                'message': 'Item not found',
                'error_code': 'ITEM_NOT_FOUND'
            }), 404

        # Prepare update fields
        update_fields = []
        params = []

        # Check each possible field to update
        if 'name' in data and data['name'] is not None:
            # Check for duplicate name in the same business
            cursor.execute(
                """
                SELECT item_id
                FROM restaurant_item
                WHERE business_id = %s
                  AND name = %s
                  AND item_id != %s
                """,
                (existing_item['business_id'], data['name'].strip(), data['item_id'])
            )
            if cursor.fetchone():
                return jsonify({
                    'status': 'error',
                    'message': 'An item with this name already exists for this business',
                    'error_code': 'DUPLICATE_ITEM_NAME'
                }), 400

            update_fields.append("name = %s")
            params.append(data['name'].strip())

        if 'description' in data:
            update_fields.append("description = %s")
            params.append(data['description'])

        if 'base_price' in data and data['base_price'] is not None:
            try:
                price = float(data['base_price'])
                update_fields.append("base_price = %s")
                params.append(price)
            except (ValueError, TypeError):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid price format',
                    'error_code': 'INVALID_PRICE_FORMAT'
                }), 400

        if 'calories' in data:
            update_fields.append("calories = %s")
            params.append(data['calories'] if data['calories'] is not None else None)

        if 'preparation_time' in data:
            update_fields.append("preparation_time = %s")
            params.append(data['preparation_time'] if data['preparation_time'] is not None else None)

        if 'is_combo' in data and data['is_combo'] is not None:
            update_fields.append("is_combo = %s")
            params.append(bool(data['is_combo']))

        if 'is_active' in data and data['is_active'] is not None:
            update_fields.append("is_active = %s")
            params.append(bool(data['is_active']))

        if 'image_url' in data:
            update_fields.append("image_url = %s")
            # Allow empty string to remove the image URL
            params.append(data['image_url'] if data['image_url'] else None)

        # If no fields to update
        if not update_fields:
            return jsonify({
                'status': 'success',
                'message': 'No changes detected',
                'data': existing_item
            })

        # Add item_id to params for WHERE clause
        params.append(data['item_id'])

        # Build and execute update query
        update_query = f"""
            UPDATE restaurant_item
            SET {', '.join(update_fields)}
            WHERE item_id = %s
        """

        cursor.execute(update_query, tuple(params))

        # Get the updated item
        cursor.execute(
            """
            SELECT *
            FROM restaurant_item
            WHERE item_id = %s
            """,
            (data['item_id'],)
        )

        updated_item = cursor.fetchone()
        conn.commit()

        # Convert Decimal to float for JSON serialization
        if updated_item and 'base_price' in updated_item:
            updated_item['base_price'] = float(updated_item['base_price']) if updated_item[
                                                                                  'base_price'] is not None else None

        return jsonify({
            'status': 'success',
            'message': 'Menu item updated successfully',
            'data': updated_item
        })

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        logger.error(f"Database error in update_item: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR',
            'details': str(err)
        }), 500

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Unexpected error in update_item: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@bp.route('/delete_item', methods=['POST'])
def delete_item():
    """
    Delete a menu item

    Request body:
    {
        "item_id": 1  # Required
    }

    Returns:
        JSON response with success/error message
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        if 'item_id' not in data or data['item_id'] is None:
            return jsonify({
                'status': 'error',
                'message': 'Item ID is required',
                'error_code': 'MISSING_ITEM_ID'
            }), 400

        item_id = data['item_id']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if item exists
        cursor.execute(
            "SELECT * FROM restaurant_item WHERE item_id = %s",
            (item_id,)
        )
        item = cursor.fetchone()

        if not item:
            return jsonify({
                'status': 'error',
                'message': 'Item not found',
                'error_code': 'ITEM_NOT_FOUND'
            }), 404

        # Check for existing references in other tables
        # For example, check if the item is used in any orders or menus
        # This is a simplified example - you might want to add more checks

        # Check if item is in any menu sections
        cursor.execute(
            "SELECT 1 FROM restaurant_menu_section_item WHERE item_id = %s LIMIT 1",
            (item_id,)
        )
        if cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Cannot delete item as it is currently used in one or more menu sections',
                'error_code': 'ITEM_IN_USE'
            }), 400

        # Check if item has any category mappings
        cursor.execute(
            "SELECT 1 FROM restaurant_item_category_map WHERE item_id = %s LIMIT 1",
            (item_id,)
        )
        if cursor.fetchone():
            # Option 1: Return error
            return jsonify({
                'status': 'error',
                'message': 'Cannot delete item as it has category mappings. Please remove all category mappings first.',
                'error_code': 'ITEM_HAS_CATEGORIES'
            }), 400

            # Option 2: Or automatically delete the mappings (uncomment if preferred)
            # cursor.execute(
            #     "DELETE FROM restaurant_item_category_map WHERE item_id = %s",
            #     (item_id,)
            # )

        # Delete the item
        cursor.execute(
            "DELETE FROM restaurant_item WHERE item_id = %s",
            (item_id,)
        )

        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Menu item deleted successfully',
            'deleted_item_id': item_id
        })

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        logger.error(f"Database error in delete_item: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR',
            'details': str(err)
        }), 500

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Unexpected error in delete_item: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@bp.route('/create_item_category_map', methods=['POST'])
def create_item_category_map():
    """
    Create a mapping between an item and a category

    Request body:
    {
        "item_id": 1,           # Required
        "item_category_id": 2   # Required
    }

    Returns:
        JSON response with the created mapping or error message
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['item_id', 'item_category_id']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                    'error_code': f'MISSING_{field.upper()}'
                }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if item exists
        cursor.execute(
            "SELECT 1 FROM restaurant_item WHERE item_id = %s",
            (data['item_id'],)
        )
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Item not found',
                'error_code': 'ITEM_NOT_FOUND'
            }), 404

        # Check if category exists
        cursor.execute(
            "SELECT 1 FROM restaurant_item_category WHERE item_category_id = %s",
            (data['item_category_id'],)
        )
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Category not found',
                'error_code': 'CATEGORY_NOT_FOUND'
            }), 404

        # Check if mapping already exists
        cursor.execute(
            """
            SELECT *
            FROM restaurant_item_category_map
            WHERE item_id = %s
              AND item_category_id = %s
            """,
            (data['item_id'], data['item_category_id'])
        )
        if cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'This category is already mapped to the item',
                'error_code': 'DUPLICATE_MAPPING'
            }), 400

        # Create the mapping
        cursor.execute(
            """
            INSERT INTO restaurant_item_category_map (item_id, item_category_id)
            VALUES (%s, %s)
            """,
            (data['item_id'], data['item_category_id'])
        )

        # Get the created mapping with details
        cursor.execute(
            """
            SELECT m.*, i.name as item_name, c.name as category_name
            FROM restaurant_item_category_map m
                     JOIN restaurant_item i ON m.item_id = i.item_id
                     JOIN restaurant_item_category c ON m.item_category_id = c.item_category_id
            WHERE m.item_id = %s
              AND m.item_category_id = %s
            """,
            (data['item_id'], data['item_category_id'])
        )

        mapping = cursor.fetchone()
        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Category mapping created successfully',
            'data': mapping
        }), 201

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        logger.error(f"Database error in create_item_category_map: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR',
            'details': str(err)
        }), 500

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Unexpected error in create_item_category_map: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@bp.route('/delete_item_category_map', methods=['POST'])
def delete_item_category_map():
    """
    Delete a mapping between an item and a category

    Request body:
    {
        "item_id": 1,           # Required
        "item_category_id": 2   # Required
    }

    Returns:
        JSON response with success/error message
    """
    conn = None
    cursor = None

    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['item_id', 'item_category_id']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                    'error_code': f'MISSING_{field.upper()}'
                }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if mapping exists
        cursor.execute(
            """
            SELECT m.*, i.name as item_name, c.name as category_name
            FROM restaurant_item_category_map m
                     JOIN restaurant_item i ON m.item_id = i.item_id
                     JOIN restaurant_item_category c ON m.item_category_id = c.item_category_id
            WHERE m.item_id = %s
              AND m.item_category_id = %s
            """,
            (data['item_id'], data['item_category_id'])
        )

        mapping = cursor.fetchone()

        if not mapping:
            return jsonify({
                'status': 'error',
                'message': 'Category mapping not found',
                'error_code': 'MAPPING_NOT_FOUND'
            }), 404

        # Delete the mapping
        cursor.execute(
            """
            DELETE
            FROM restaurant_item_category_map
            WHERE item_id = %s
              AND item_category_id = %s
            """,
            (data['item_id'], data['item_category_id'])
        )

        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Category mapping deleted successfully',
            'data': {
                'item_id': mapping['item_id'],
                'item_name': mapping['item_name'],
                'category_id': mapping['item_category_id'],
                'category_name': mapping['category_name']
            }
        })

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        logger.error(f"Database error in delete_item_category_map: {err}")
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'error_code': 'DATABASE_ERROR',
            'details': str(err)
        }), 500

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Unexpected error in delete_item_category_map: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()