#!/usr/bin/env python3
"""
Restaurant API
Handles restaurant related operations including menu management
"""

from flask import Blueprint, request, jsonify
import mysql.connector
import os
import logging

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
    """Execute database query"""
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
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

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
                m.is_active
            FROM restaurant_modifier m
            WHERE m.modifier_group_id = %s
            ORDER BY m.name
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