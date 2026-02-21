from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from typing import Dict, Any
from appointment_app.database import get_db_cursor, get_db_connection

bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')


@bp.route('/receive_message', methods=['POST'])
def receive_message():
    """
    Receive WhatsApp message payload and print it
    
    Expected payload format varies by WhatsApp Business API provider,
    but typically includes message content, sender info, and metadata.
    """
    try:
        # Get the incoming payload
        payload = request.get_json()
        
        # Print the payload for debugging/monitoring
        print(f"WhatsApp message received at {datetime.now()}:")
        print(f"Payload: {payload}")
        
        # You can add additional processing here later
        # For now, just acknowledge receipt
        
        return jsonify({
            "status": "success",
            "message": "WhatsApp message received",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing WhatsApp message: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to process WhatsApp message",
            "error": str(e)
        }), 500


@bp.route('/webhook', methods=['GET', 'POST'])
def webhook_verify():
    """
    WhatsApp webhook verification endpoint
    Used during webhook setup with WhatsApp Business API
    """
    # Get verification parameters
    if request.method == 'GET':
        hub_mode = request.args.get('hub.mode')
        hub_challenge = request.args.get('hub.challenge')
        hub_verify_token = request.args.get('hub.verify_token')

        # You should configure this token in your environment
        verify_token = current_app.config.get('WHATSAPP_VERIFY_TOKEN', 'your_verify_token')

        if hub_mode == 'subscribe' and hub_verify_token == verify_token:
            print(f"WhatsApp webhook verified at {datetime.now()}")
            return hub_challenge, 200
        else:
            print(f"WhatsApp webhook verification failed")
            return jsonify({"status": "error", "message": "Verification failed"}), 403

    payload = request.get_json(silent=True)
    #message = payload['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
    business_phone = payload['entry'][0]['changes'][0]['value']['metadata']['display_phone_number']
    customer_phone = payload['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
    user_input = payload['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
    current_app.logger.info(f"Webhook event received at {datetime.now()}: {payload}")
    # IMPORTANT: Always ack fast
    return "EVENT_RECEIVED", 200
        # IMPORTANT: Always ack fast


@bp.route('/get_call_sid', methods=['POST'])
def get_call_sid():
    """
    Get or create call_sid based on business_phone and customer_phone
    
    Payload: {"business_phone": "", "customer_phone": ""}
    
    Returns the call_sid of the latest record if timestamp is within 20 minutes,
    otherwise creates a new record and returns its call_sid
    """
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"status": "error", "message": "No payload provided"}), 400
        
        business_phone = payload.get('business_phone')
        customer_phone = payload.get('customer_phone')
        
        if not business_phone or not customer_phone:
            return jsonify({
                "status": "error", 
                "message": "business_phone and customer_phone are required"
            }), 400
        
        # Check for existing record within last 20 minutes
        twenty_minutes_ago = datetime.now() - timedelta(minutes=20)

        with get_db_cursor(commit=True) as cursor:
            # Query for latest record matching the phone numbers within 20 minutes
            query = """
                SELECT call_sid 
                FROM whatsapp_call_sid 
                WHERE business_phone = %s 
                AND customer_phone = %s 
                AND timestamp >= %s 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            cursor.execute(query, (business_phone, customer_phone, twenty_minutes_ago))
            result = cursor.fetchone()
            new_call_sid = result['call_sid']
            call_sid = f"whatsapp_{new_call_sid:08d}"
            if result:
                # Return existing call_sid
                return jsonify({
                    "status": "success",
                    "call_sid": call_sid,
                    "action": "retrieved_existing"
                }), 200
            else:
                # Insert new record and get the call_sid
                delete_query = """
                               DELETE \
                               FROM whatsapp_call_sid
                               WHERE business_phone = %s \
                                 AND customer_phone = %s \
                               """
                cursor.execute(delete_query, (business_phone, customer_phone))

                insert_query = """
                    INSERT INTO whatsapp_call_sid (business_phone, customer_phone)
                    VALUES (%s, %s)
                """
                cursor.execute(insert_query, (business_phone, customer_phone))
                
                # Get the ID of the inserted record
                cursor.execute("SELECT LAST_INSERT_ID() as call_sid")
                new_call_sid = cursor.fetchone()['call_sid']
                call_sid = f"whatsapp_{new_call_sid:08d}"
                return jsonify({
                    "status": "success",
                    "call_sid": call_sid,
                    "action": "created_new"
                }), 200
                
    except Exception as e:
        current_app.logger.error(f"Error in get_call_sid: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to process call_sid request",
            "error": str(e)
        }), 500


@bp.route('/create_call_sid', methods=['POST'])
def create_sid():
    """
    Create a new call_sid record unconditionally
    
    Payload: {"business_phone": "", "customer_phone": ""}
    
    Always creates a new record and returns its call_sid
    """
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"status": "error", "message": "No payload provided"}), 400
        
        business_phone = payload.get('business_phone')
        customer_phone = payload.get('customer_phone')
        
        if not business_phone or not customer_phone:
            return jsonify({
                "status": "error", 
                "message": "business_phone and customer_phone are required"
            }), 400
        
        with get_db_cursor(commit=True) as cursor:
            # Delete all existing records with the same business_phone and customer_phone
            delete_query = """
                DELETE FROM whatsapp_call_sid 
                WHERE business_phone = %s AND customer_phone = %s
            """
            cursor.execute(delete_query, (business_phone, customer_phone))
            
            # Insert new record and get the call_sid
            insert_query = """
                INSERT INTO whatsapp_call_sid (business_phone, customer_phone)
                VALUES (%s, %s)
            """
            cursor.execute(insert_query, (business_phone, customer_phone))
            
            # Get the ID of the inserted record
            cursor.execute("SELECT LAST_INSERT_ID() as call_sid")
            new_call_sid = cursor.fetchone()['call_sid']
            
            return jsonify({
                "status": "success",
                "call_sid": new_call_sid,
                "action": "created_new"
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"Error in create_sid: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to create call_sid record",
            "error": str(e)
        }), 500


@bp.route('/status', methods=['GET'])
def status():
    """Check WhatsApp integration status"""
    return jsonify({
        "status": "active",
        "service": "WhatsApp integration",
        "timestamp": datetime.now().isoformat()
    }), 200
