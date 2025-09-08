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
                a.day_of_week,
                a.start_time,
                a.end_time
            FROM restaurant_menu m
            LEFT JOIN restaurant_menu_availability ma ON m.menu_id = ma.menu_id
            LEFT JOIN restaurant_availability a ON ma.availability_id = a.availability_id
            WHERE m.business_id = %s 
            ORDER BY m.menu_id, a.day_of_week, a.start_time
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
            JOIN restaurant_menu_item_section_map sm 
                ON s.menu_section_id = sm.menu_section_id
            JOIN restaurant_menu_item i 
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
        # Get request data
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
                FROM restaurant_menu_item i
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

        # Build and execute update query
        query = f"""
            UPDATE restaurant_menu 
            SET {', '.join(update_fields)}
            WHERE menu_id = %s
        """
        execute_query(query, params)

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

        # Add modifier_group_id to params for WHERE clause
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
                      SELECT 1 \
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
                    "is_required": 1,
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

        # Check if the association already exists
        check_query = """
                      SELECT 1
                      FROM restaurant_item_modifier_group
                      WHERE item_id = %s \
                        AND modifier_group_id = %s \
                      """
        if execute_query(check_query, (data['item_id'], data['modifier_group_id']), fetch=True):
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
        execute_query(insert_query, (data['item_id'], data['modifier_group_id']))

        return jsonify({
            'status': 'success',
            'message': 'Modifier group added to item successfully',
            'data': {
                'item_id': data['item_id'],
                'modifier_group_id': data['modifier_group_id']
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

        # Check if the association exists first
        check_query = """
            SELECT 1 
            FROM restaurant_item_modifier_group 
            WHERE item_id = %s AND modifier_group_id = %s
            LIMIT 1
        """
        if not execute_query(check_query, (data['item_id'], data['modifier_group_id']), fetch=True):
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
        execute_query(delete_query, (data['item_id'], data['modifier_group_id']))

        return jsonify({
            'status': 'success',
            'message': 'Modifier group removed from item successfully',
            'data': {
                'item_id': data['item_id'],
                'modifier_group_id': data['modifier_group_id']
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
            FROM restaurant_menu_item
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
            JOIN restaurant_menu_item i 
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

            # Get all availabilities for the business
            query = """
                    SELECT availability_id, name
                    FROM restaurant_availability
                    WHERE business_id = %s
                    ORDER BY name \
                    """

            cursor.execute(query, (data['business_id'],))
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
                'error_code': 'DATABASE_ERROR'
            }), 500
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    except Exception as e:
        logger.error(f"Error in list_availabilities: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching availabilities',
            'error_code': str(e)
        }), 500


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