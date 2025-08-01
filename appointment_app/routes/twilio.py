from flask import Blueprint, request, jsonify
from database import get_db_cursor
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import re
import functools
import traceback
import json
from twilio.rest import Client
import os

bp = Blueprint('twilio', __name__, url_prefix='/api/twilio')

def safe_serialize(obj):
    """Safely serialize objects to JSON string, handling Response objects and other non-serializable types"""
    from flask import Response as FlaskResponse
    
    if obj is None:
        return None
        
    try:
        # Handle Flask Response objects
        if isinstance(obj, FlaskResponse):
            try:
                # Try to get JSON data from the response
                response_data = obj.get_json()
                return json.dumps(response_data) if response_data else None
            except:
                # If we can't get JSON, return the response status and data as a string
                return json.dumps({
                    '_type': 'flask.Response',
                    'status_code': obj.status_code,
                    'content_type': obj.content_type,
                    'data': obj.data.decode('utf-8') if obj.data else None
                })
        
        # Handle dictionaries and lists
        if isinstance(obj, (dict, list, tuple, set)):
            return json.dumps(obj)
            
        # For any other type, convert to string
        return str(obj)
        
    except Exception as e:
        # If anything goes wrong, return a string representation
        return str(obj)

def log_twilio_transaction(endpoint_name):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            payload = request.get_json() or {}
            response_data = None
            success = False
            error_message = None
            http_status_code = 500

            try:
                result = f(*args, **kwargs)
                if isinstance(result, tuple):
                    response_data, http_status_code = result
                else:
                    response_data = result
                    http_status_code = 200
                success = True
                return result
            except Exception as e:
                error_message = str(e)
                traceback.print_exc()
                raise
            finally:
                # Log to database using get_db_cursor
                try:
                    with get_db_cursor(commit=True) as cursor:
                        cursor.execute("""
                            INSERT INTO twilio_transaction_log (
                                endpoint, payload, response, success, error_message, http_status_code, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            endpoint_name,
                            safe_serialize(payload) if payload else None,
                            safe_serialize(response_data) if response_data else None,
                            success,
                            error_message,
                            http_status_code,
                            datetime.now()
                        ))
                except Exception as log_err:
                    print("❌ Failed to log Twilio transaction:", str(log_err))

        return wrapper
    return decorator

@bp.route('/available-numbers', methods=['POST'])
@log_twilio_transaction('/available-numbers')
def get_available_numbers():
    """
    Get available Twilio phone numbers based on search criteria

    Request body: {
        "country": "US",
        "type": "local",
        "sms_enabled": true,
        "voice_enabled": true,
        "area_code": "415",
        "contains": "555"
    }

    Returns: List of available phone numbers
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        country = data.get("country", "US")
        number_type = data.get("type", "local")
        sms_enabled = data.get("sms_enabled", None)
        voice_enabled = data.get("voice_enabled", None)
        area_code = data.get("area_code", None)
        contains = data.get("contains", None)

        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        params = {}
        if sms_enabled is not None:
            params["sms_enabled"] = sms_enabled
        if voice_enabled is not None:
            params["voice_enabled"] = voice_enabled
        if area_code:
            params["area_code"] = area_code
        if contains:
            params["contains"] = contains

        number_list_method = getattr(client.available_phone_numbers(country), number_type)
        available_numbers = number_list_method.list(limit=10, **params)

        result = [
            {
                "friendly_name": n.friendly_name,
                "phone_number": n.phone_number,
                "region": n.region,
                "capabilities": n.capabilities
            } for n in available_numbers
        ]

        return jsonify({
            "status": "success",
            "message": "Available numbers retrieved successfully",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve available numbers: {str(e)}"
        }), 500


@bp.route('/purchase-number', methods=['POST'])
@log_twilio_transaction('/purchase-number')
def purchase_number():
    """
    Purchase a Twilio phone number

    Request body: {
        "phone_number": "+14155551234",
        "country": "US"
    }

    Returns: Confirmation of the purchased number
    """
    try:
        data = request.get_json()
        if not data or 'phone_number' not in data or 'country' not in data:
            return jsonify({
                "status": "error",
                "message": "phone_number and country are required"
            }), 400

        phone_number = data['phone_number']

        # Initialize Twilio client
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        # Purchase the number
        purchased_number = client.incoming_phone_numbers.create(
            phone_number=phone_number
        )

        return jsonify({
            "status": "success",
            "message": "Number purchased successfully",
            "data": {
                "sid": purchased_number.sid,
                "phone_number": purchased_number.phone_number,
                "friendly_name": purchased_number.friendly_name,
                "capabilities": purchased_number.capabilities
            }
        }), 200

    except Exception as e:
        print(f"[purchase_number] Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to purchase number",
            "error": str(e)
        }), 500

@bp.route('/purchased-numbers', methods=['GET'])
@log_twilio_transaction('/purchased-numbers')
def list_numbers():
    """
    List all purchased Twilio numbers with optional filters

    Query parameters:
    - contains: Filter numbers containing this sequence
    - country: Filter by country code
    - friendly_name: Filter by friendly name
    - voice_enabled: Filter by voice capability
    - sms_enabled: Filter by SMS capability

    Returns: List of purchased numbers
    """
    try:
        # Extract filters from query params
        filters = {
            'contains': request.args.get('contains'),
            'country': request.args.get('country'),
            'friendly_name': request.args.get('friendly_name'),
            'voice_enabled': request.args.get('voice_enabled', type=lambda v: v.lower() == 'true'),
            'sms_enabled': request.args.get('sms_enabled', type=lambda v: v.lower() == 'true')
        }

        # Remove None values
        clean_filters = {k: v for k, v in filters.items() if v is not None}

        # Initialize Twilio client
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        # Fetch purchased numbers
        purchased_numbers = client.incoming_phone_numbers.list()

        # Apply filters manually (Twilio API has limited server-side filters)
        filtered_numbers = []
        for number in purchased_numbers:
            if filters['contains'] and filters['contains'] not in number.phone_number:
                continue
            if filters['country'] and filters['country'].upper() != number.iso_country.upper():
                continue
            if filters['friendly_name'] and filters['friendly_name'].lower() not in (number.friendly_name or '').lower():
                continue
            if filters['voice_enabled'] is not None and filters['voice_enabled'] != number.capabilities.get('voice', False):
                continue
            if filters['sms_enabled'] is not None and filters['sms_enabled'] != number.capabilities.get('sms', False):
                continue

            filtered_numbers.append({
                "sid": number.sid,
                "phone_number": number.phone_number,
                "friendly_name": number.friendly_name,
                "capabilities": number.capabilities
            })

        return jsonify({
            "status": "success",
            "message": "Numbers retrieved successfully",
            "data": {
                "filters": clean_filters,
                "numbers": filtered_numbers,
                "date_created": number.date_created.isoformat() if number.date_created else None,
                "date_updated": number.date_updated.isoformat() if number.date_updated else None
            }
        }), 200

    except Exception as e:
        print(f"[list_numbers] Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to retrieve numbers",
            "error": str(e)
        }), 500


@bp.route('/configure-number', methods=['POST'])
@log_twilio_transaction('/configure-number')
def configure_number():
    """
    Configure a Twilio phone number

    Request body: {
        "phone_sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "voice_url": "https://example.com/voice",
        "sms_url": "https://example.com/sms",
        "status_callback": "https://example.com/status",
        "voice_method": "POST",
        "sms_method": "POST"
    }

    Returns: Confirmation of the configuration
    """
    try:
        data = request.get_json()
        required_fields = ['phone_sid', 'voice_url', 'sms_url']

        if not data or any(field not in data for field in required_fields):
            return jsonify({
                "status": "error",
                "message": f"Missing required fields. Required: {', '.join(required_fields)}"
            }), 400

        phone_sid = data['phone_sid']
        update_payload = {
            "voice_url": data['voice_url'],
            "sms_url": data['sms_url'],
        }

        if 'status_callback' in data:
            update_payload['status_callback'] = data['status_callback']
        if 'voice_method' in data:
            update_payload['voice_method'] = data['voice_method']
        if 'sms_method' in data:
            update_payload['sms_method'] = data['sms_method']

        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        updated = client.incoming_phone_numbers(phone_sid).update(**update_payload)

        return jsonify({
            "status": "success",
            "message": "Number configured successfully",
            "data": {
                "phone_sid": updated.sid,
                "phone_number": updated.phone_number,
                "voice_url": updated.voice_url,
                "sms_url": updated.sms_url,
                "status_callback": updated.status_callback,
                "voice_method": updated.voice_method,
                "sms_method": updated.sms_method
            }
        }), 200

    except Exception as e:
        print(f"[configure_number] Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to configure number",
            "error": str(e)
        }), 500


@bp.route('/release-number', methods=['POST'])
@log_twilio_transaction('/release-number')
def release_number():
    """
    Release a Twilio phone number

    Request body: {
        "phone_sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }

    Returns: Confirmation of the release
    """
    try:
        data = request.get_json()
        if not data or 'phone_sid' not in data:
            return jsonify({
                "status": "error",
                "message": "phone_sid is required"
            }), 400

        phone_sid = data['phone_sid']

        # Initialize Twilio client
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        # Delete (release) the number
        client.incoming_phone_numbers(phone_sid).delete()

        return jsonify({
            "status": "success",
            "message": "Number released successfully",
            "data": {
                "phone_sid": phone_sid
            }
        }), 200

    except Exception as e:
        print(f"[release_number] Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to release number",
            "error": str(e)
        }), 500


@bp.route('/number-details', methods=['POST'])
@log_twilio_transaction('/number-details')
def get_number_details():
    """
    Get details for a specific Twilio number

    Request body:
    {
        "phone_sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }

    Returns: Details of the specified phone number
    """
    try:
        data = request.get_json()
        phone_sid = data.get('phone_sid') if data else None

        if not phone_sid:
            return jsonify({
                "status": "error",
                "message": "Missing required field: phone_sid"
            }), 400

        # Initialize Twilio client
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        number = client.incoming_phone_numbers(phone_sid).fetch()

        return jsonify({
            "status": "success",
            "message": "Number details retrieved successfully",
            "data": {
                "sid": number.sid,
                "phone_number": number.phone_number,
                "friendly_name": number.friendly_name,
                "voice_url": number.voice_url,
                "sms_url": number.sms_url,
                "status_callback": number.status_callback,
                "voice_method": number.voice_method,
                "sms_method": number.sms_method,
                "capabilities": number.capabilities,
                "date_created": number.date_created.isoformat() if number.date_created else None,
                "date_updated": number.date_updated.isoformat() if number.date_updated else None
            }
        }), 200

    except Exception as e:
        print(f"[get_number_details] Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to retrieve number details",
            "error": str(e)
        }), 500

@bp.route('/update-friendly-name', methods=['POST'])
@log_twilio_transaction('/update-friendly-name')
def update_friendly_name():
    """
    Update the friendly name of a Twilio number

    Request body: {
        "phone_sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "friendly_name": "Support Line - Toronto"
    }

    Returns: Confirmation of the update
    """
    try:
        data = request.get_json()
        required_fields = ['phone_sid', 'friendly_name']

        if not data or any(field not in data for field in required_fields):
            return jsonify({
                "status": "error",
                "message": f"Missing required fields. Required: {', '.join(required_fields)}"
            }), 400

        phone_sid = data['phone_sid']
        friendly_name = data['friendly_name']

        # Initialize Twilio client
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        # Update the friendly name
        updated = client.incoming_phone_numbers(phone_sid).update(
            friendly_name=friendly_name
        )

        return jsonify({
            "status": "success",
            "message": "Friendly name updated successfully",
            "data": {
                "sid": updated.sid,
                "phone_number": updated.phone_number,
                "friendly_name": updated.friendly_name
            }
        }), 200

    except Exception as e:
        print(f"[update_friendly_name] Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to update friendly name",
            "error": str(e)
        }), 500

@bp.route('/number-usage', methods=['POST'])
@log_twilio_transaction('/number-usage')
def get_usage():
    """
    Get usage statistics for a Twilio number

    Request body:
    {
        "phone_sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "start_date": "2025-07-01",   # Optional
        "end_date": "2025-07-31"      # Optional
    }

    Returns: Usage statistics for the specified number and date range
    """
    try:
        data = request.get_json()
        phone_sid = data.get('phone_sid')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not phone_sid:
            return jsonify({
                "status": "error",
                "message": "phone_sid is required"
            }), 400

        # Parse dates if present
        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        # Twilio client
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )

        # Fetch the actual phone number (E.164 format) from SID
        twilio_number = client.incoming_phone_numbers(phone_sid).fetch()
        e164_number = twilio_number.phone_number  # e.g. "+14155556666"

        # Build kwargs for date filters
        usage_kwargs = {}
        if start:
            usage_kwargs["start_date"] = start
        if end:
            usage_kwargs["end_date"] = end

        # Get all usage records
        usage_records = client.usage.records.list(limit=1000, **usage_kwargs)

        # Filter by phone number in description (best-effort)
        filtered = []
        for record in usage_records:
            filtered.append({
                "category": record.category,
                "description": record.description,
                "usage": float(record.usage) if record.usage is not None else None,
                "usage_unit": record.usage_unit,
                "price": float(record.price) if record.price is not None else None,
                "price_unit": record.price_unit,
                "start_date": str(record.start_date),
                "end_date": str(record.end_date)
            })

        return jsonify({
            "status": "success",
            "message": "Usage statistics retrieved successfully",
            "data": {
                "phone_sid": phone_sid,
                "phone_number": e164_number,
                "start_date": start_date,
                "end_date": end_date,
                "usage": filtered
            }
        }), 200

    except Exception as e:
        print(f"[get_usage] Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to retrieve usage statistics",
            "error": str(e)
        }), 500


