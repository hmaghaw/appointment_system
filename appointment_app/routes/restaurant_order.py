#!/usr/bin/env python3
"""
Restaurant Order API
Handles order related operations including creating, updating, deleting, and listing orders
"""
from flask import Blueprint, request, jsonify, current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
import mysql.connector
import os
import logging
from datetime import timedelta, datetime
import math
import json
from appointment_app.services.clover_integration import CloverIntegration
from appointment_app.services.restaurant import restaurant_service
from ..services.entity_integration import EntityIntegrationManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Whitelist of safe order fields
ORDER_FIELDS = {
    "amount": "o.total_price",
    "date": "o.order_time",
    "status": "o.order_status"
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

def notify_new_order(business_id, order_data):
    """Emit a new order notification to the business room"""
    try:
        # socketio.emit('new_order', {
        #     'business_id': business_id,
        #     'order': order_data,
        #     'message': 'New order received!',
        #     'timestamp': datetime.utcnow().isoformat()
        # }, room=f'business_{business_id}')
        socketio.emit('new_order', {
            'business_id': 73,
            'order': {
                'order_id': 999,
                'total': 15.50,
                'items': [],
                'order_status': 'pending'
            },
            'message': 'Test order',
            'timestamp': '2025-09-17T10:30:00Z'
        }, room='business_73')
        logger.info(f"Notified business {business_id} about new order")
    except Exception as e:
        logger.error(f"Error sending new order notification: {str(e)}")

# Create Blueprint
bp = Blueprint('restaurant_orders', __name__, url_prefix='/api/restaurants')

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('join_business')
def on_join(data):
    business_id = data.get('business_id')
    if business_id:
        join_room(f'business_{business_id}')
        logger.info(f'Client joined business room: business_{business_id}')

@socketio.on('leave_business')
def on_leave(data):
    business_id = data.get('business_id')
    if business_id:
        leave_room(f'business_{business_id}')
        logger.info(f'Client left business room: business_{business_id}')

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
        business_id = order_data['business_id']
        business_integration = restaurant_service.get_business_integration(business_id)
        provider = business_integration['provider']
        if provider != 'polydial':
            integration = EntityIntegrationManager(provider=provider)


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
            if provider == 'polydial':
                order_id = restaurant_service.create_order(order_data)
                for item in order_data['items']:
                    item_id = item['item_id']
                    order_item_id = restaurant_service.create_polydial_line_item(order_id, item)
                    total_price = sum(item['price'] * item['quantity'] for item in order_data['items'])
                    restaurant_service.update_order(order_id, total_price=total_price)
            elif provider == 'clover':
                clover = CloverIntegration(order_data['business_id'])
                order_id = restaurant_service.create_order(order_data)
                externals_order = clover.create_order()
                externals_order_id=externals_order['id']
                integration.create_entity("order", order_id, externals_order_id,business_id)
                for item in order_data['items']:
                    item_id = item['item_id']
                    order_line_item_id = restaurant_service.create_polydial_line_item(order_id, item)
                    externals_order_line_item = clover.add_line_item(externals_order_id=externals_order_id, item=item)
                    externals_order_line_item_id = externals_order_line_item['id']
                    integration.create_entity("order_line_item", order_line_item_id, externals_order_line_item_id, business_id)
            elif provider == 'square':
               pass

            # Calculate and update the total price for the order

            # Commit the transaction
            conn.commit()

            return jsonify({
                'status': 'success',
                'message': 'Order created successfully'
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

def build_order_clause(order_mode):
    """Convert safe order_mode array into SQL ORDER BY clause."""
    if not order_mode:
        return "ORDER BY o.order_time DESC"

    if isinstance(order_mode, str):  # allow single value
        order_mode = [order_mode]

    clauses = []
    for spec in order_mode:
        try:
            field, direction = spec.split(":")
            field = field.strip().lower()
            direction = direction.strip().lower()
        except ValueError:
            continue

        if field not in ORDER_FIELDS:
            continue
        if direction not in ("asc", "desc"):
            direction = "asc"

        clauses.append(f"{ORDER_FIELDS[field]} {direction.upper()}")

    if not clauses:
        return "ORDER BY o.order_time DESC"

    return "ORDER BY " + ", ".join(clauses)

@bp.route('/list_orders', methods=['POST'])
def list_orders():
    """
    List orders with filtering, ordering, and pagination.

    Request Body:
    {
        "business_id": 73,               # required
        "status": ["confirmed","completed"],  # optional (string or array)
        "from_date": "2025-09-01",       # optional (YYYY-MM-DD)
        "to_date": "2025-09-14",         # optional (YYYY-MM-DD)
        "order_mode": ["amount:desc"],   # optional, array of field:direction
        "page": 1,                       # optional, default 1
        "per_page": 10                   # optional, default 10, max 100
    }
    """
    try:
        data = request.get_json()
        if not data or "business_id" not in data:
            return jsonify({
                "status": "error",
                "message": "business_id is required"
            }), 400

        business_id = data["business_id"]
        status = data.get("status")
        from_date = data.get("from_date")
        to_date = data.get("to_date")
        order_mode = data.get("order_mode")
        page = max(1, data.get("page", 1))
        per_page = min(100, data.get("per_page", 10))
        offset = (page - 1) * per_page

        # Build WHERE filters
        filters = ["o.business_id = %s"]
        params = [business_id]

        if status:
            if isinstance(status, list):
                placeholders = ", ".join(["%s"] * len(status))
                filters.append(f"o.order_status IN ({placeholders})")
                params.extend(status)
            else:
                filters.append("o.order_status = %s")
                params.append(status)

        if from_date:
            try:
                datetime.strptime(from_date, "%Y-%m-%d")
                filters.append("DATE(o.order_time) >= %s")
                params.append(from_date)
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid from_date"}), 400

        if to_date:
            try:
                datetime.strptime(to_date, "%Y-%m-%d")
                filters.append("DATE(o.order_time) <= %s")
                params.append(to_date)
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid to_date"}), 400

        where_clause = " AND ".join(filters)
        order_clause = build_order_clause(order_mode)

        # Count total for pagination
        count_sql = f"SELECT COUNT(*) AS total FROM restaurant_order o WHERE {where_clause}"
        count_result = execute_query(count_sql, tuple(params), fetch=True)
        total_orders = count_result["total"]
        total_pages = max(1, math.ceil(total_orders / per_page))

        # Main query with joins
        sql = f"""
        SELECT
            o.order_id,
            o.customer_id,
            c.first_name,
            c.last_name,
            o.business_id,
            o.order_status,
            o.order_time,
            o.total_price,
            o.notes,

            oi.order_item_id,
            oi.item_id,
            oi.quantity,
            oi.base_price,
            oi.total_price AS item_price,
            ri.name AS item_name,

            oo.option_id,
            oo.name AS option_name,
            oo.price_delta AS option_price,

            om.modifier_id,
            om.name AS modifier_name,
            om.price_delta AS modifier_price
        FROM restaurant_order o
        LEFT JOIN customer c ON o.customer_id = c.customer_id
        LEFT JOIN restaurant_order_item oi ON o.order_id = oi.order_id
        LEFT JOIN restaurant_item ri ON oi.item_id = ri.item_id
        LEFT JOIN restaurant_order_item_option oo ON oi.order_item_id = oo.order_item_id
        LEFT JOIN restaurant_order_item_modifier om ON oi.order_item_id = om.order_item_id
        WHERE {where_clause}
        {order_clause}
        LIMIT %s OFFSET %s
        """
        rows = execute_query(sql, tuple(params + [per_page, offset]), fetch=True, fetch_all=True)

        # Aggregate results
        orders = {}
        for row in rows:
            oid = row["order_id"]
            if oid not in orders:
                orders[oid] = {
                    "order": {
                        "order_id": oid,
                        "customer_id": row["customer_id"],
                        "customer_name": f"{row['first_name']} {row['last_name']}".strip(),
                        "status": row["order_status"],
                        "order_time": row["order_time"].isoformat() if row["order_time"] else None,
                        "total": float(row["total_price"] or 0),
                        "notes": row["notes"],
                        "items": []
                    },
                    "_items": {}
                }

            # Handle items
            if row["order_item_id"] and row["order_item_id"] not in orders[oid]["_items"]:
                orders[oid]["_items"][row["order_item_id"]] = {
                    "item_id": row["item_id"],
                    "name": row["item_name"],
                    "quantity": row["quantity"],
                    "base_price": float(row["base_price"] or 0),
                    "price": float(row["item_price"] or 0),
                    "options": [],
                    "modifiers": []
                }
                orders[oid]["order"]["items"].append(orders[oid]["_items"][row["order_item_id"]])

            item = orders[oid]["_items"].get(row["order_item_id"])
            if item:
                if row["option_id"]:
                    item["options"].append({
                        "option_id": row["option_id"],
                        "name": row["option_name"],
                        "price_delta": float(row["option_price"] or 0)
                    })
                if row["modifier_id"]:
                    item["modifiers"].append({
                        "modifier_id": row["modifier_id"],
                        "name": row["modifier_name"],
                        "price_delta": float(row["modifier_price"] or 0)
                    })

        result_orders = [v["order"] for v in orders.values()]

        return jsonify({
            "status": "success",
            "orders": result_orders,
            "pagination": {
                "total": total_orders,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        })

    except Exception as e:
        logger.error(f"Error in list_orders: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal Server Error",
            "details": str(e)
        }), 500

@bp.route('/push_notification', methods=['POST'])
def push_notification():
    """
    Send a push notification for a new order
    
    Request Body (JSON):
    {
        "business_id": 1,
        "order": {
            "id": 123,
            "customer_id": 21,
            "total": 25.99,
            "status": "received",
            "items": [
                {
                    "item_id": 51,
                    "name": "Ful Sandwich",
                    "quantity": 1,
                    "price": 12.00,
                    "options": [
                        {
                            "option_group_id": 14,
                            "option_id": 24,
                            "name": "Full Balady bread",
                            "price_delta": 4.5
                        }
                    ]
                }
            ],
            "created_at": "2025-09-17T18:30:00Z"
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'business_id' not in data or 'order' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: business_id and order are required'
            }), 400
            
        business_id = data['business_id']
        order = data['order']
        
        # Send the notification via WebSocket
        notify_new_order(business_id, order)
        
        return jsonify({
            'status': 'success',
            'message': 'Notification sent successfully',
            'business_id': business_id,
            'order_id': order.get('id')
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to send notification',
            'error': str(e)
        }), 500