import json
from flask import Blueprint, jsonify, request
import mysql.connector
from database import get_db_cursor

bp = Blueprint('call_history', __name__, url_prefix='/api/call-meta')

def _get_call_meta(call_sid):
    """Helper function to get call metadata by call_sid"""
    with get_db_cursor(dictionary=True, database='call_history') as cursor:
        cursor.execute("""
            SELECT * FROM call_meta 
            WHERE call_sid = %s
        """, (call_sid,))
        return cursor.fetchone()

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
        
        with get_db_cursor(database='call_history', commit=True) as cursor:
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
        return jsonify(call)
        
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
