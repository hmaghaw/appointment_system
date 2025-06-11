import json
from flask import Blueprint, jsonify, request
import mysql.connector
from datetime import datetime
from database import get_db_cursor

bp = Blueprint('call_history', __name__, url_prefix='/api/call-history')

def _get_call_meta(call_sid):
    """Helper function to get call metadata by call_sid"""
    with get_db_cursor(dictionary=True, database='call_history') as cursor:
        cursor.execute("""
            SELECT * FROM call_meta 
            WHERE call_sid = %s
        """, (call_sid,))
        
        call = cursor.fetchone()
        
        if call:
            # Convert datetime objects to ISO format for JSON serialization
            call['created_at'] = call['created_at'].isoformat() if call['created_at'] else None
            call['updated_at'] = call['updated_at'].isoformat() if call['updated_at'] else None
        
        return call

def _call_exists(call_sid):
    """Helper function to check if a call exists"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM call_meta 
            WHERE call_sid = %s
        """, (call_sid,))
        return cursor.fetchone() is not None

@bp.route('/create', methods=['POST'])
def create_or_update_call_meta():
    """
    Create or update call metadata
    
    Request Body:
    {
        "call_sid": "CA1234567890abcdef1234567890abcdef",
        "meta": {
            "from": "+1234567890",
            "to": "+1987654321",
            "status": "completed",
            "duration": "120",
            "direction": "inbound",
            "recording_url": "https://example.com/recording.mp3"
        }
    }
    """
    data = request.get_json()
    
    if not data or 'call_sid' not in data or 'meta' not in data:
        return jsonify({"error": "call_sid and meta are required"}), 400
    
    call_sid = data['call_sid']
    meta = data['meta']
    
    try:
        # Convert meta dictionary to JSON string if it's a dictionary
        meta_json = json.dumps(meta) if isinstance(meta, dict) else meta
        
        with get_db_cursor(database='call_history', commit=True) as cursor:
            # First try to update if record exists
            cursor.execute("""
                INSERT INTO call_meta (call_sid, meta)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    meta = VALUES(meta),
                    updated_at = NOW()
            """, (call_sid, meta_json))
            
            return jsonify({
                "call_sid": call_sid,
                "status": "success",
                "action": "created" if cursor.rowcount == 1 else "updated"
            }), 200
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@bp.route('/read', methods=['POST'])
def read_call_meta():
    """
    Read call metadata and check if it exists
    
    Request Body:
    {
        "call_sid": "CA1234567890abcdef1234567890abcdef"
    }
    
    Returns:
    - If call exists:
    {
        "exists": true,
        "call_sid": "CA123...",
        "meta": { ... },
        "created_at": "...",
        "updated_at": "..."
    }
    
    - If call doesn't exist:
    {
        "exists": false,
        "call_sid": "CA123..."
    }
    """
    data = request.get_json()
    
    if not data or 'call_sid' not in data:
        return jsonify({"error": "call_sid is required"}), 400
    
    call_sid = data['call_sid']
    
    try:
        call = _get_call_meta(call_sid)
        if call:
            call['exists'] = True
            return jsonify(call), 200
        else:
            return jsonify({
                "exists": False,
                "call_sid": call_sid
            }), 200
            
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
