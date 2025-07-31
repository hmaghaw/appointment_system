import json
from flask import Blueprint, jsonify, request
import mysql.connector
from database import get_db_cursor
from datetime import datetime

bp = Blueprint('call_conversation', __name__, url_prefix='/api/call-conversation')

@bp.route('/add', methods=['POST'])
def add_conversation_item():
    """
    Add a new conversation item
    
    Request Body:
    {
        "call_sid": "CA123...",
        "name": "optional_name",  # Optional name for the message
        "role": "user|assistant|system|function",
        "content": "The message content (can be null for function calls)",
        "function_call": {  # Optional, for function calls
            "name": "function_name",
            "arguments": "{...}"  # JSON string of arguments
        }
    }
    """
    data = request.get_json()
    
    if not data or 'call_sid' not in data or 'role' not in data:
        return jsonify({"error": "call_sid and role are required"}), 400
    
    call_sid = data['call_sid']
    name = data.get('name')
    role = data['role']
    content = data.get('content')
    function_call = data.get('function_call')
    
    # Validate role
    valid_roles = ['user', 'assistant', 'system', 'function']
    if role not in valid_roles:
        return jsonify({
            "error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        }), 400
    
    # Validate function_call structure if provided
    if function_call is not None:
        if not isinstance(function_call, dict):
            return jsonify({"error": "function_call must be an object"}), 400
        
        # Only validate function_call structure if it's not empty
        if function_call:
            if 'name' not in function_call or 'arguments' not in function_call:
                return jsonify({"error": "function_call must contain 'name' and 'arguments' when provided"}), 400
            try:
                # Try to parse arguments to validate it's valid JSON
                if isinstance(function_call['arguments'], str):
                    json.loads(function_call['arguments'])
            except (json.JSONDecodeError, TypeError):
                return jsonify({"error": "function_call.arguments must be a valid JSON string"}), 400
    
    try:
        with get_db_cursor(database='appointment_db', commit=True) as cursor:
            # Convert function_call to JSON string
            function_call_json = json.dumps(function_call) if function_call is not None else None
            
            cursor.execute("""
                INSERT INTO call_conversation 
                (call_sid, name, role, content, function_call)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                call_sid,
                name,
                role,
                content,
                function_call_json
            ))
            
            # Get the inserted record
            cursor.execute("""
                SELECT * FROM call_conversation 
                WHERE call_conversation_id = %s
            """, (cursor.lastrowid,))
            
            item = cursor.fetchone()
            if item:
                item = dict(item)
                # Convert datetime objects to strings and handle JSON fields
                if 'created_at' in item and item['created_at']:
                    item['created_at'] = item['created_at'].isoformat()
                if 'updated_at' in item and item['updated_at']:
                    item['updated_at'] = item['updated_at'].isoformat()
                if 'function_call' in item and item['function_call']:
                    try:
                        item['function_call'] = json.loads(item['function_call'])
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            return jsonify({
                "status": "success",
                "item": item
            }), 201
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/list', methods=['POST'])
def list_conversation_items():
    """
    List all conversation items for a call
    
    Request Body:
    {
        "call_sid": "CA123..."
    }
    
    Optional Query Parameters:
    - name: Filter by name
    - role: Filter by role
    - has_function: If 'true', only include items with function_calls
    """
    data = request.get_json()
    
    if not data or 'call_sid' not in data:
        return jsonify({"error": "call_sid is required"}), 400
    
    call_sid = data['call_sid']
    name_filter = request.args.get('name')
    role_filter = request.args.get('role')
    has_function = request.args.get('has_function') == 'true'
    
    try:
        with get_db_cursor(dictionary=True, database='appointment_db') as cursor:
            # Build the query
            query = """
                SELECT call_conversation_id, call_sid, name, role, content, 
                       function_call, created_at, updated_at
                FROM call_conversation 
                WHERE call_sid = %s
            """
            params = [call_sid]
            
            # Add filters
            if name_filter:
                query += " AND name = %s"
                params.append(name_filter)
                
            if role_filter:
                query += " AND role = %s"
                params.append(role_filter)
                
            if has_function:
                query += " AND function_call IS NOT NULL"
            
            # Add ordering
            query += " ORDER BY call_conversation_id ASC"
            
            cursor.execute(query, tuple(params))
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                # Convert datetime objects to strings and handle JSON fields
                if 'created_at' in item and item['created_at']:
                    item['created_at'] = item['created_at'].isoformat()
                if 'updated_at' in item and item['updated_at']:
                    item['updated_at'] = item['updated_at'].isoformat()
                if 'function_call' in item and item['function_call']:
                    try:
                        item['function_call'] = json.loads(item['function_call'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                items.append(item)
            
            return jsonify({
                "status": "success",
                "call_sid": call_sid,
                "count": len(items),
                "items": items
            })
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/save-bulk-messages', methods=['POST'])
def save_bulk_messages():
    """
    Save multiple conversation items for a call in bulk
    
    Request Body:
    {
        "call_sid": "CA123...",
        "messages": [
            {"content": "message 1", "role": "user"},
            {"content": "message 2", "role": "assistant"}
        ]
    }
    """
    data = request.get_json()
    
    if not data or 'call_sid' not in data or 'messages' not in data:
        return jsonify({"error": "Missing required fields: call_sid and messages are required"}), 400
    
    call_sid = data['call_sid']
    messages = data['messages']
    
    if not isinstance(messages, list):
        return jsonify({"error": "messages must be a list of message objects"}), 400
    
    # Prepare the values to insert
    values = []
    current_time = datetime.utcnow()
    
    for msg in messages:
        if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
            continue  # Skip invalid message formats
            
        values.append((
            call_sid,
            msg.get('role'),
            msg.get('content'),
            current_time
        ))
    
    if not values:
        return jsonify({"error": "No valid messages to save"}), 400
    
    try:
        with get_db_cursor(commit=True, use_call_db=True, database='appointment_db') as cursor:
            # Prepare the insert query
            query = """
            INSERT INTO call_conversation (call_sid, role, content, created_at)
            VALUES (%s, %s, %s, %s)
            """
            
            # Execute the bulk insert
            cursor.executemany(query, values)
            
            return jsonify({
                "status": "success",
                "message": f"Successfully saved {len(values)} messages",
                "call_sid": call_sid
            }), 200
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/update-system-prompt', methods=['POST'])
def update_system_prompt():
    """
    Update the system prompt for a call
    
    Request Body:
    {
        "call_sid": "CA123...",
        "content": "Updated system prompt content"
    }
    """
    data = request.get_json()
    
    if not data or 'call_sid' not in data or 'content' not in data:
        return jsonify({"error": "call_sid and content are required"}), 400
    
    call_sid = data['call_sid']
    content = data['content']
    
    try:
        with get_db_cursor(database='appointment_db', commit=True) as cursor:
            # Check if a system prompt already exists for this call
            cursor.execute("""
                SELECT call_conversation_id 
                FROM call_conversation 
                WHERE call_sid = %s AND role = 'system'
                ORDER BY call_conversation_id DESC
                LIMIT 1
            """, (call_sid,))
            
            existing_prompt = cursor.fetchone()
            
            if existing_prompt:
                # Update existing system prompt
                cursor.execute("""
                    UPDATE call_conversation 
                    SET content = %s, updated_at = NOW()
                    WHERE call_conversation_id = %s
                """, (content, existing_prompt['call_conversation_id']))
                action = "updated"
            else:
                # Insert new system prompt
                cursor.execute("""
                    INSERT INTO call_conversation 
                    (call_sid, role, content, created_at, updated_at)
                    VALUES (%s, 'system', %s, NOW(), NOW())
                """, (call_sid, content))
                action = "created"
            
            return jsonify({
                "status": "success",
                "action": action,
                "call_sid": call_sid
            })
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
