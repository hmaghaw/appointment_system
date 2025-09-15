#!/usr/bin/env python3
"""
Restaurant Order API
Handles order related operations including creating, updating, deleting, and listing orders
"""

from flask import Blueprint, request, jsonify
import mysql.connector
import os
import logging
from datetime import timedelta, datetime
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def execute_query(query, params=None, fetch=False, fetch_all=False):
    """Execute a database query and return results if fetch is True"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            if fetch_all:
                return cursor.fetchall()
            return cursor.fetchone()
        else:
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Query error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Create Blueprint
bp = Blueprint('restaurant_orders', __name__, url_prefix='/api/restaurants')


@bp.route('/create_order', methods=['POST'])
def create_order():
    """
    Create a new order with the following payload structure:
    {
        "order": {
            "business_id": 73,
            "customer_id": 21,
            "items": [
                {
                    "item_id": 51,
                    "name": "Ful Sandwich",
                    "quantity": 1,
                    "base_price": 7.50,
                    "price": 12.00,
                    "options": [{
                        "option_group_id": 14,
                        "option_id": 24,
                        "name": "Full Balady bread",
                        "price_delta": 4.5
                    }],
                    "modifiers": []
                }
            ],
            "total": 12.00
        }
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if 'order' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Order data is required',
                'error_code': 'MISSING_ORDER_DATA'
            }), 400

        order_data = data['order']

        required_fields = ['customer_id', 'business_id', 'items']
        for field in required_fields:
            if field not in order_data:
                return jsonify({
                    'status': 'error',
                    'message': f'{field} is required',
                    'error_code': f'MISSING_{field.upper()}'
                }), 400

        if not isinstance(order_data['items'], list) or len(order_data['items']) == 0:
            return jsonify({
                'status': 'error',
                'message': 'At least one order item is required',
                'error_code': 'NO_ITEMS_PROVIDED'
            }), 400

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Start transaction
            cursor.execute("START TRANSACTION")

            # Create order
            cursor.execute(
                """
                INSERT INTO restaurant_order
                    (customer_id, business_id, order_status, order_time)
                VALUES (%s, %s, 'confirmed', NOW())
                """,
                (
                    order_data['customer_id'],
                    order_data['business_id']
                )
            )
            order_id = cursor.lastrowid

            # Add order items
            for item in order_data['items']:
                # Validate required fields
                if 'item_id' not in item or 'quantity' not in item or 'price' not in item:
                    conn.rollback()
                    return jsonify({
                        'status': 'error',
                        'message': 'Each item must have item_id, quantity, and price',
                        'error_code': 'INVALID_ITEM_DATA'
                    }), 400

                # Add order item
                cursor.execute(
                    """
                    INSERT INTO restaurant_order_item
                        (order_id, item_id, quantity, base_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item['item_id'],
                        item['quantity'],
                        item.get('base_price', item['price']),
                        item['price'] * item['quantity']
                    )
                )
                order_item_id = cursor.lastrowid

                # Add options if any
                if 'options' in item and isinstance(item['options'], list):
                    for option in item['options']:
                        cursor.execute(
                            """
                            INSERT INTO restaurant_order_item_option
                                (order_item_id, option_id, name, price_delta)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                order_item_id,
                                option.get('option_id'),
                                option.get('name', ''),
                                option.get('price_delta', 0.0)
                            )
                        )

                # Add modifiers if any
                if 'modifiers' in item and isinstance(item['modifiers'], list):
                    for modifier in item['modifiers']:
                        cursor.execute(
                            """
                            INSERT INTO restaurant_order_item_modifier
                                (order_item_id, modifier_id, name, price_delta)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                order_item_id,
                                modifier.get('modifier_id'),
                                modifier.get('name', ''),
                                modifier.get('price_delta', 0.0)
                            )
                        )

            # Calculate and update the total price for the order
            total_price = sum(item['price'] * item['quantity'] for item in order_data['items'])
            cursor.execute(
                "UPDATE restaurant_order SET total_price = %s WHERE order_id = %s",
                (total_price, order_id)
            )

            # Commit the transaction
            conn.commit()

            # Get the created order details
            cursor.execute(
                """
                SELECT *
                FROM restaurant_order
                WHERE order_id = %s
                """,
                (order_id,)
            )
            order = cursor.fetchone()

            # Get order items with options and modifiers
            cursor.execute(
                """
                SELECT oi.*,
                       i.name        as item_name,
                       i.description as item_description
                FROM restaurant_order_item oi
                         LEFT JOIN restaurant_item i ON oi.item_id = i.item_id
                WHERE oi.order_id = %s
                """,
                (order_id,)
            )
            order_items = cursor.fetchall()

            # Get options and modifiers for each item
            for item in order_items:
                cursor.execute(
                    "SELECT * FROM restaurant_order_item_option WHERE order_item_id = %s",
                    (item['order_item_id'],)
                )
                item['options'] = cursor.fetchall()

                cursor.execute(
                    "SELECT * FROM restaurant_order_item_modifier WHERE order_item_id = %s",
                    (item['order_item_id'],)
                )
                item['modifiers'] = cursor.fetchall()

            order['items'] = order_items

            return jsonify({
                'status': 'success',
                'message': 'Order created successfully',
                'order': order
            }), 201

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating order: {str(e)}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': 'An error occurred while creating the order',
                'error_code': 'ORDER_CREATION_FAILED',
                'details': str(e)
            }), 500

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': str(e)
        }), 500

def get_order_details(order_id):
    """Helper function to get order details by ID"""
    # Get order basic info
    order = execute_query(
        """
        SELECT * FROM restaurant_order 
        WHERE order_id = %s
        """,
        (order_id,),
        fetch=True
    )

    if not order:
        return None

    # Get order items
    order_items = execute_query(
        """
        SELECT 
            oi.*,
            ri.name as item_name,
            ri.image_url as item_image
        FROM restaurant_order_item oi
        JOIN restaurant_item ri ON oi.item_id = ri.item_id
        WHERE oi.order_id = %s
        """,
        (order_id,),
        fetch=True,
        fetch_all=True
    )

    # Get modifiers for each item
    for item in order_items:
        item['modifiers'] = execute_query(
            """
            SELECT 
                oim.*,
                rm.name as modifier_name
            FROM restaurant_order_item_modifier oim
            JOIN restaurant_modifier rm ON oim.modifier_id = rm.modifier_id
            WHERE oim.order_item_id = %s
            """,
            (item['order_item_id'],),
            fetch=True,
            fetch_all=True
        )

        # Convert Decimal to float for JSON serialization
        item['base_price'] = float(item['base_price']) if item['base_price'] is not None else 0.0

        # Calculate total price for the item (including modifiers)
        item_total = item['base_price'] * item['quantity']
        for mod in item['modifiers']:
            item['base_price'] = float(item['base_price']) if item['base_price'] is not None else 0.0
            item_total += item['base_price'] * item['quantity']

        item['total_price'] = item_total

    # Calculate order total
    order_total = sum(item['total_price'] for item in order_items)

    # Format the response
    order_data = {
        'order_id': order['order_id'],
        'customer_id': order['customer_id'],
        'business_id': order['business_id'],
        'order_status': order['order_status'],
        'notes': order['notes'],
        'order_time': order['order_time'].isoformat() if order['order_time'] else None,
        'total_amount': order_total,
        'items': order_items
    }

    return order_data

@bp.route('/update_order', methods=['POST'])
def update_order():
    """
    Update an existing order

    Request body (all fields are optional except order_id):
    {
        "order_id": 1,  // Required
        "order_status": "preparing",  // Optional
        "notes": "Updated instructions"  // Optional
    }

    Returns:
        JSON response with the updated order details
    """
    try:
        data = request.get_json()

        if not data or 'order_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Order ID is required',
                'error_code': 'MISSING_ORDER_ID'
            }), 400

        order_id = data['order_id']

        # Check if order exists
        existing_order = execute_query(
            "SELECT * FROM restaurant_order WHERE order_id = %s",
            (order_id,),
            fetch=True
        )

        if not existing_order:
            return jsonify({
                'status': 'error',
                'message': 'Order not found',
                'error_code': 'ORDER_NOT_FOUND'
            }), 404

        # Build update query
        update_fields = []
        update_values = []

        # Map request fields to database fields
        field_mapping = {
            'order_status': 'order_status',  # Map order_status in request to status in DB
            'notes': 'notes'
        }

        for request_field, db_field in field_mapping.items():
            if request_field in data and data[request_field] is not None:
                update_fields.append(f"{db_field} = %s")
                update_values.append(data[request_field])

        if not update_fields:
            return jsonify({
                'status': 'error',
                'message': 'No valid fields to update',
                'error_code': 'NO_VALID_FIELDS'
            }), 400

        # Add order_id to values
        update_values.append(order_id)

        # Update order
        execute_query(
            f"""
            UPDATE restaurant_order 
            SET {', '.join(update_fields)}
            WHERE order_id = %s
            """,
            tuple(update_values),
            fetch=False
        )

        # Get updated order
        updated_order = get_order_details(order_id)

        return jsonify({
            'status': 'success',
            'message': 'Order updated successfully',
            'data': updated_order
        })

    except Exception as e:
        logger.error(f"Error in update_order: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating the order',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/delete_order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """
    Delete an order

    URL Parameters:
        order_id: ID of the order to delete

    Returns:
        JSON response with success/error message
    """
    try:
        # Check if order exists
        existing_order = execute_query(
            "SELECT * FROM restaurant_order WHERE order_id = %s",
            (order_id,),
            fetch=True
        )

        if not existing_order:
            return jsonify({
                'status': 'error',
                'message': 'Order not found',
                'error_code': 'ORDER_NOT_FOUND'
            }), 404

        # Start transaction
        execute_query("START TRANSACTION", fetch=False)

        try:
            # Delete order item modifiers
            execute_query(
                """
                DELETE oim FROM restaurant_order_item_modifier oim
                JOIN restaurant_order_item oi ON oim.order_item_id = oi.order_item_id
                WHERE oi.order_id = %s
                """,
                (order_id,),
                fetch=False
            )

            # Delete order items
            execute_query(
                "DELETE FROM restaurant_order_item WHERE order_id = %s",
                (order_id,),
                fetch=False
            )

            # Delete the order
            execute_query(
                "DELETE FROM restaurant_order WHERE order_id = %s",
                (order_id,),
                fetch=False
            )

            # Commit transaction
            execute_query("COMMIT", fetch=False)

            return jsonify({
                'status': 'success',
                'message': 'Order deleted successfully',
                'deleted_order_id': order_id
            })

        except Exception as e:
            execute_query("ROLLBACK", fetch=False)
            raise e

    except Exception as e:
        logger.error(f"Error in delete_order: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting the order',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500


@bp.route('/list_orders', methods=['POST'])
def list_orders():
    """
    List orders with optional filtering and pagination

    Request Body (JSON):
    {
        "business_id": 1,               // Required
        "customer_id": 1,               // Optional
        "status": "completed",          // Optional
        "from_date": "2025-09-01",      // Optional (YYYY-MM-DD)
        "to_date": "2025-09-14",        // Optional (YYYY-MM-DD)
        "page": 1,                      // Optional, default: 1
        "per_page": 10                  // Optional, default: 10, max: 100
    }
    """
    try:
        data = request.get_json()

        # Validate required business_id
        if not data or 'business_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'business_id is required in the request body',
                'error_code': 'MISSING_BUSINESS_ID'
            }), 400

        # Get parameters from request body
        business_id = data.get('business_id')
        customer_id = data.get('customer_id')
        status = data.get('status')
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        page = max(1, data.get('page', 1))
        per_page = min(100, data.get('per_page', 10))

        # Build base query
        base_query = """
        FROM restaurant_order o
        WHERE o.business_id = %s
        """

        query_params = [business_id]

        # Add optional filters
        if customer_id is not None:
            base_query += " AND o.customer_id = %s"
            query_params.append(customer_id)

        if status:
            base_query += " AND o.order_status = %s"
            query_params.append(status)

        if from_date:
            try:
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
                base_query += " AND DATE(o.order_time) >= %s"
                query_params.append(from_date.strftime('%Y-%m-%d'))
            except (ValueError, TypeError):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid from_date format. Use YYYY-MM-DD',
                    'error_code': 'INVALID_DATE_FORMAT'
                }), 400

        if to_date:
            try:
                to_date = datetime.strptime(to_date, '%Y-%m-%d')
                base_query += " AND DATE(o.order_time) <= %s"
                query_params.append(to_date.strftime('%Y-%m-%d'))
            except (ValueError, TypeError):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid to_date format. Use YYYY-MM-DD',
                    'error_code': 'INVALID_DATE_FORMAT'
                }), 400

        # Get total count for pagination
        count_result = execute_query(
            f"SELECT COUNT(*) as total {base_query}",
            tuple(query_params),
            fetch=True
        )

        total_orders = count_result['total']
        total_pages = max(1, math.ceil(total_orders / per_page))

        # Apply pagination
        offset = (page - 1) * per_page
        base_query += " ORDER BY o.order_time DESC LIMIT %s OFFSET %s"
        query_params.extend([per_page, offset])

        # Get paginated orders
        orders = execute_query(
            f"""
            SELECT o.order_id
            {base_query}
            """,
            tuple(query_params),
            fetch=True,
            fetch_all=True
        )

        # Get detailed information for each order
        result_orders = []
        for order in orders:
            order_id = order['order_id']

            # Get order details
            order_details = execute_query(
                """
                SELECT o.order_id,
                       o.customer_id,
                       o.business_id,
                       o.order_status as status,
                       o.order_time,
                       o.total_price  as total
                FROM restaurant_order o
                WHERE o.order_id = %s
                """,
                (order_id,),
                fetch=True
            )

            if not order_details:
                continue

            # Get order items with options and modifiers
            order_items = execute_query(
                """
                SELECT oi.order_item_id,
                       oi.item_id,
                       oi.quantity,
                       oi.base_price,
                       oi.total_price as price,
                       ri.name
                FROM restaurant_order_item oi
                         JOIN restaurant_item ri ON oi.item_id = ri.item_id
                WHERE oi.order_id = %s
                """,
                (order_id,),
                fetch=True,
                fetch_all=True
            )

            # Process each item to include options and modifiers
            items_with_details = []
            for item in order_items:
                # Get options for this item
                options = execute_query(
                    """
                    SELECT oo.option_id,
                           oo.name,
                           oo.price_delta
                    FROM restaurant_order_item_option oo
                    WHERE oo.order_item_id = %s
                    """,
                    (item['order_item_id'],),
                    fetch=True,
                    fetch_all=True
                )

                # Get modifiers for this item
                modifiers = execute_query(
                    """
                    SELECT om.modifier_id,
                           om.name,
                           om.price_delta
                    FROM restaurant_order_item_modifier om
                    WHERE om.order_item_id = %s
                    """,
                    (item['order_item_id'],),
                    fetch=True,
                    fetch_all=True
                )

                # Format the item
                item_data = {
                    'item_id': item['item_id'],
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'base_price': float(item['base_price']),
                    'price': float(item['price']),
                    'options': [{
                        'option_id': opt['option_id'],
                        'name': opt['name'],
                        'price_delta': float(opt['price_delta'])
                    } for opt in options],
                    'modifiers': [{
                        'modifier_id': mod['modifier_id'],
                        'name': mod['name'],
                        'price_delta': float(mod['price_delta'])
                    } for mod in modifiers]
                }
                items_with_details.append(item_data)

            # Format the order
            order_data = {
                'order': {
                    'order_id': order_details['order_id'],
                    'items': items_with_details,
                    'total': float(order_details['total'])
                }
            }
            result_orders.append(order_data)

        return jsonify({
            'status': 'success',
            'orders': result_orders,
            'pagination': {
                'total': total_orders,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })

    except Exception as e:
        logger.error(f"Error in list_orders: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching orders',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': str(e)
        }), 500