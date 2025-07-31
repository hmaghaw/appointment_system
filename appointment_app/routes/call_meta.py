import json
import random
import string
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import mysql.connector
from database import get_db_cursor, get_db_connection

bp = Blueprint('call_history', __name__, url_prefix='/api/call-meta')

def _get_call_meta(call_sid):
    """Helper function to get call metadata by call_sid"""
    with get_db_cursor(dictionary=True, database='appointment_db') as cursor:
        cursor.execute("""
            SELECT * FROM call_meta 
            WHERE call_sid = %s
        """, (call_sid,))
        return cursor.fetchone()


def _get_call_conversation(call_sid):
    """
    Helper function to get call conversation by call_sid, excluding system messages
    
    Args:
        call_sid (str): The call SID to get conversation for
        
    Returns:
        list: List of conversation messages (excluding system messages)
    """
    with get_db_cursor(dictionary=True, database='appointment_db') as cursor:
        cursor.execute("""
            SELECT 
                call_conversation_id,
                call_sid,
                name,
                role,
                content,
                function_call,
                created_at,
                updated_at
            FROM call_conversation 
            WHERE call_sid = %s 
            AND role != 'system'
            ORDER BY created_at ASC
        """, (call_sid,))
        return cursor.fetchall()

@bp.route('/create', methods=['POST'])
def create_or_update_call_meta():
    """
    Create or update call metadata
    
    Request Body:
    {
        "call_sid": "CA123...",
        "meta": { ... }  # Any JSON-serializable data
    }
    """
    data = request.get_json()
    
    if not data or 'call_sid' not in data or 'meta' not in data:
        return jsonify({"error": "call_sid and meta are required"}), 400
    
    call_sid = data['call_sid']
    meta = data['meta']
    
    try:
        meta_json = json.dumps(meta) if not isinstance(meta, str) else meta
        
        with get_db_cursor(database='appointment_db', commit=True) as cursor:
            cursor.execute("""
                INSERT INTO call_meta (call_sid, meta)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    meta = VALUES(meta),
                    updated_at = NOW()
            """, (call_sid, meta_json))
            
            return jsonify({
                "status": "success",
                "call_sid": call_sid,
                "action": "created" if cursor.rowcount == 1 else "updated"
            }), 200
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/conversation', methods=['POST'])
def get_call_conversation():
    """
    Get all conversation records for a specific call_sid, excluding system messages
    
    Request Body:
    {
        "call_sid": "CA123..."  // Required: The call SID to get conversation for
    }
    
    Returns:
    {
        "call_sid": "CA123...",
        "conversation": [
            {
                "call_conversation_id": 1,
                "call_sid": "CA123...",
                "name": "Assistant",
                "role": "assistant",
                "content": "Hello, how can I help you today?",
                "function_call": null,
                "created_at": "2025-07-30T10:30:00",
                "updated_at": "2025-07-30T10:30:00"
            }
            // ... more messages
        ]
    }
    """
    data = request.get_json() or {}
    
    # Validate required fields
    if 'call_sid' not in data:
        return jsonify({"error": "call_sid is required in the request body"}), 400
    
    call_sid = data['call_sid']
    
    try:
        with get_db_cursor(dictionary=True, database='appointment_db') as cursor:
            # Query the call_conversation table directly
            cursor.execute("""
                SELECT 
                    call_conversation_id,
                    call_sid,
                    name,
                    role,
                    content,
                    function_call,
                    created_at,
                    updated_at
                FROM call_conversation 
                WHERE call_sid = %s 
                AND role != 'system'
                ORDER BY created_at ASC
            """, (call_sid,))
            
            conversation = cursor.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for msg in conversation:
                for field in ['created_at', 'updated_at']:
                    if msg.get(field) and isinstance(msg[field], datetime):
                        msg[field] = msg[field].isoformat()
                
                # Parse function_call if it's a string
                if 'function_call' in msg and msg['function_call'] and isinstance(msg['function_call'], str):
                    try:
                        msg['function_call'] = json.loads(msg['function_call'])
                    except json.JSONDecodeError:
                        pass  # Keep as string if not valid JSON
            
            return jsonify({
                "call_sid": call_sid,
                "conversation": conversation
            })
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@bp.route('/list', methods=['POST'])
def list_call_meta():
    """
    List call metadata with optional filtering
    
    Request Body:
    {
        "business_id": 17,            # Required: Business ID to filter by
        "customer_id": 123,           # Optional: Customer ID to filter by
        "status": "Completed",        # Optional: Filter by call status
        "start_date": "2025-01-01",   # Optional: Filter calls on or after this date (YYYY-MM-DD)
        "end_date": "2025-12-31"      # Optional: Filter calls on or before this date (YYYY-MM-DD)
    }
    
    Returns:
    {
        "calls": [list of call objects],
        "count": number of calls
    }
    """
    data = request.get_json() or {}
    
    # Validate required fields
    if 'business_id' not in data:
        return jsonify({"error": "business_id is required"}), 400
    
    business_id = data['business_id']
    customer_id = data.get('customer_id')
    status = data.get('status')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    try:
        # First, try to get the customer names if we can access the customer table
        with get_db_cursor(dictionary=True, database='appointment_db') as cursor:
            cursor.execute("SHOW TABLES LIKE 'customer'")
            has_customer_access = cursor.fetchone() is not None
            
        if has_customer_access:
            # If we have access to the customer table, include the customer name
            query = """
                SELECT 
                    cm.call_sid,
                    cm.business_id,
                    cm.customer_id,
                    cm.call_start,
                    cm.call_end,
                    cm.call_duration,
                    cm.call_status,
                    cm.communication_channel,
                    cm.direction,
                    cm.created_at,
                    cm.updated_at,
                    CONCAT(COALESCE(c.first_name, ''), ' ', COALESCE(c.last_name, '')) as customer_name
                FROM call_meta cm
                LEFT JOIN appointment_db.customer c ON cm.customer_id = c.customer_id
                WHERE cm.business_id = %s
            """
        else:
            # Fallback query without customer name if we don't have access
            query = """
                SELECT 
                    call_sid,
                    business_id,
                    customer_id,
                    call_start,
                    call_end,
                    call_duration,
                    call_status,
                    communication_channel,
                    direction,
                    created_at,
                    updated_at,
                    NULL as customer_name
                FROM call_meta
                WHERE business_id = %s
            """
    except Exception as e:
        # If we can't check the customer table, use the fallback query
        query = """
            SELECT 
                call_sid,
                business_id,
                customer_id,
                call_start,
                call_end,
                call_duration,
                call_status,
                communication_channel,
                direction,
                created_at,
                updated_at,
                NULL as customer_name
            FROM call_meta
            WHERE business_id = %s
        """
    params = [business_id]
    
    # Add customer_id filter if provided
    if customer_id:
        query += " AND cm.customer_id = %s"
        params.append(customer_id)
    
    # Add status filter if provided
    if status:
        query += " AND cm.call_status = %s"
        params.append(status)
    
    # Add date range filters if provided
    if start_date:
        try:
            # Convert to datetime and format for SQL
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query += " AND DATE(call_start) >= %s"
            params.append(start_dt.strftime('%Y-%m-%d'))
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    
    if end_date:
        try:
            # Convert to datetime, add one day, and format for SQL
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query += " AND DATE(call_start) < %s"
            params.append(end_dt.strftime('%Y-%m-%d'))
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    
    # Add sorting
    query += " ORDER BY created_at DESC"
    
    try:
        with get_db_cursor(dictionary=True, database='appointment_db') as cursor:
            cursor.execute(query, tuple(params))
            calls = cursor.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for call in calls:
                for field in ['call_start', 'call_end', 'created_at', 'updated_at']:
                    if call[field] and isinstance(call[field], datetime):
                        call[field] = call[field].isoformat()
                # Parse meta if it's a string
                if 'meta' in call and isinstance(call['meta'], str):
                    try:
                        call['meta'] = json.loads(call['meta'])
                    except json.JSONDecodeError:
                        pass  # Keep as string if not valid JSON
            
            return jsonify({
                "calls": calls,
                "count": len(calls)
            })
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@bp.route('/read', methods=['POST'])
def read_call_meta():
    """
    Read call metadata
    
    Request Body:
    {
        "call_sid": "CA123..."
    }
    
    Returns:
    - If call exists: {call data}
    - If call doesn't exist: {"exists": false, "call_sid": "..."}
    """
    data = request.get_json()
    
    if not data or 'call_sid' not in data:
        return jsonify({"error": "call_sid is required"}), 400
    
    call_sid = data['call_sid']
    
    try:
        call = _get_call_meta(call_sid)
        if not call:
            return jsonify({
                "exists": False,
                "call_sid": call_sid
            })
        
        # Convert datetime objects to strings
        if 'created_at' in call and call['created_at']:
            call['created_at'] = call['created_at'].isoformat()
        if 'updated_at' in call and call['updated_at']:
            call['updated_at'] = call['updated_at'].isoformat()
        
        # Parse meta if it's a string
        if 'meta' in call and isinstance(call['meta'], str):
            try:
                call['meta'] = json.loads(call['meta'])
            except json.JSONDecodeError:
                pass
        
        call['exists'] = True
        return jsonify(call), 200
        
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def _generate_sms_sid():
    """Generate a random 20-character string for SMS SID"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(20))

@bp.route('/get_sms_sid', methods=['POST'])
def get_sms_sid():
    """
    Get or create an SMS SID for a business-customer pair with expiry check
    
    Request Body:
    {
        "business_phone": "+1234567890",  # Required: Phone number of the business
        "customer_phone": "+1987654321",  # Required: Phone number of the customer
        "expiry_minutes": 5               # Optional: expiry time in minutes (default: 5)
    }
    
    Returns:
    {
        "sms_id": "generated_or_existing_sid"
    }
    """
    data = request.get_json()
    
    if not data or 'business_phone' not in data or 'customer_phone' not in data:
        return jsonify({"error": "business_phone and customer_phone are required"}), 400
    
    business_phone = data['business_phone']
    customer_phone = data['customer_phone']
    expiry_minutes = int(data.get('expiry_minutes', 5))
    
    try:
        # Get a connection first
        with get_db_connection() as conn:  # Using default database for business/customer lookup
            with conn.cursor(dictionary=True) as cursor:
                # Get business ID from phone number using the business_phone table
                cursor.execute("""
                    SELECT bp.business_id, b.name 
                    FROM business_phone bp
                    JOIN business b ON bp.business_id = b.business_id
                    WHERE bp.business_phone = %s AND bp.is_primary = TRUE
                """, (business_phone,))
                business = cursor.fetchone()
                if not business:
                    return jsonify({"error": "Business not found with the provided phone number"}), 404
                
                business_id = business['business_id']
                
                # Get customer ID from phone number and business_id
                cursor.execute("""
                    SELECT customer_id, first_name, last_name 
                    FROM customer 
                    WHERE customer_phone = %s AND business_id = %s
                """, (customer_phone, business_id))
                customer = cursor.fetchone()
                if not customer:
                    return jsonify({"error": "Customer not found with the provided phone number for this business"}), 404
                
                customer_id = customer['customer_id']
                
                # Switch to call_history database
                cursor.close()
                conn.close()
                
                # Now work with call_history database
                with get_db_connection(database='appointment_db') as conn_hist:
                    with conn_hist.cursor(dictionary=True) as cursor_hist:
                        # Check for existing valid SID
                        cursor_hist.execute("""
                            SELECT sms_sid, created_at 
                            FROM sms_sid 
                            WHERE business_id = %s 
                            AND customer_id = %s
                        """, (business_id, customer_id))
                        
                        existing = cursor_hist.fetchone()
                        if existing:
                            # Check if the existing SID is still valid
                            expiry_time = existing['created_at'].replace(tzinfo=timezone.utc) + timedelta(minutes=expiry_minutes)
                            if expiry_time > datetime.now(timezone.utc):
                                return jsonify({"sms_id": existing['sms_sid']})
                        
                        # If we get here, we need to generate a new SID
                        new_sid = _generate_sms_sid()
                        
                        # Insert or update the SID
                        now = datetime.now(timezone.utc)
                        cursor_hist.execute("""
                            INSERT INTO sms_sid (business_id, customer_id, sms_sid, created_at)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                sms_sid = VALUES(sms_sid),
                                created_at = VALUES(created_at)
                        """, (business_id, customer_id, new_sid, now))
                        
                        # Commit the transaction
                        conn_hist.commit()
                        
                        return jsonify({"sms_id": new_sid})
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/is_business_admin_phone', methods=['POST'])
def is_business_admin_phone():
    """
    Check if a customer phone is a business admin phone
    
    Request Body:
    {
        "business_phone": "1234567890",
        "customer_phone": "9876543210"
    }
    
    Returns:
    {
        "admin_phone": true/false
    }
    """
    data = request.get_json()
    
    if not data or 'business_phone' not in data or 'customer_phone' not in data:
        return jsonify({"error": "business_phone and customer_phone are required"}), 400
    
    business_phone = data['business_phone']
    customer_phone = data['customer_phone']
    
    try:
        with get_db_cursor(dictionary=True) as cursor:
            # First, get the business ID from the business_phone
            cursor.execute("""
                SELECT business_id 
                FROM business_phone 
                WHERE business_phone = %s 
                AND is_primary = TRUE
                LIMIT 1
            """, (business_phone,))
            
            business = cursor.fetchone()
            if not business:
                return jsonify({"admin_phone": False})
                
            business_id = business['business_id']
            
            # Check if the customer phone is an admin for this business
            cursor.execute("""
                SELECT 1 
                FROM business_admin_phone 
                WHERE business_id = %s 
                AND admin_phone = %s
                LIMIT 1
            """, (business_id, customer_phone))
            
            is_admin = cursor.fetchone() is not None
            return jsonify({"admin_phone": is_admin})
            
    except mysql.connector.Error as err:
        current_app.logger.error(f"Database error checking admin phone: {str(err)}")
        return jsonify({"error": "Database error checking admin status"}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error checking admin phone: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
