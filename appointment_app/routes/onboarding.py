from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import requests
import os
import json
from appointment_app.services.auth_token_validator import verify_bearer_token
from appointment_app.database import get_db_cursor
import mysql.connector

# Create blueprint
bp = Blueprint('onboarding', __name__, url_prefix='/api/onboarding')

@bp.route('', methods=['POST', 'OPTIONS'], strict_slashes=False)
@bp.route('/', methods=['POST', 'OPTIONS'])
@cross_origin()
def handle_onboarding():
    """
    Handle the complete onboarding process including:
    1. Account creation
    2. Phone number setup (premium or regular)
    
    Request body should contain:
    {
        "activate_account": {
            "autoRechargeEnabled": bool,
            "rechargeAmount": float,
            "rechargeThreshold": float,
            "top_up_value": float
        },
        "choose_number": {
            "is_premium": bool,
            "locality": str,
            "phone_number": str,
            "price": float,
            "region": str
        },
        "create_account": {
            "adminFirstName": str,
            "adminLastName": str,
            "adminPhone": str,
            "businessName": str,
            "confirmPassword": str,
            "email": str,
            "password": str
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided in request body"
            }), 400
        
        # Validate required sections
        required_sections = ['activate_account', 'choose_number', 'create_account']
        for section in required_sections:
            if section not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required section: {section}",
                    "required_sections": required_sections
                }), 400
        
        # Step 1: Create the account
        signup_data = data.get('create_account', {})
        #signup_result = signup(signup_data)
        # user_id = signup_result['user']['id']
        # business_id = signup_result['user']['business_id']

        user_id = "user_ee34eee9471a2d6c"
        business_id = 31
        business_name = data['create_account']['businessName']
        # Step 2: Handle phone number setup
        phone_data = data.get('choose_number', {})
        choose_number(business_id, business_name, phone_data)
        
        # Step 3: Update account with auto-recharge settings
        activate_data = data.get('activate_account', {})
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    UPDATE business 
                    SET auto_recharge_enabled = %s,
                        recharge_amount = %s,
                        recharge_threshold = %s,
                        balance = COALESCE(balance, 0) + %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    bool(activate_data.get('autoRechargeEnabled', False)),
                    float(activate_data.get('rechargeAmount', 0)),
                    float(activate_data.get('rechargeThreshold', 0)),
                    float(activate_data.get('top_up_value', 0)),
                    business_id
                ))
                
                if cursor.rowcount == 0:
                    print(f"Warning: No rows updated when setting business preferences for business_id: {business_id}")
                    
        except (mysql.connector.Error, ValueError) as err:
            print(f"Warning: Failed to update business settings: {str(err)}")
            # Continue with onboarding even if settings update fails
        
        return jsonify({
            "success": True,
            "message": "Onboarding completed successfully",
            "user_id": user_id,
            "business_id": business_id,
            "phone_setup_success": phone_setup_success,
            "business_updated": True
        }), 201
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Critical error in onboarding: {error_trace}")
        
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred during onboarding",
            "details": str(e)
        }), 500

def signup(signup_data):
    try:
        signup_response = requests.post(
            f"{os.getenv('API_BASE_URL', 'http://localhost:5000')}/api/auth/signup",
            json=signup_data,
            timeout=30  # 30 seconds timeout
        )
        signup_response.raise_for_status()  # Raises an HTTPError for bad responses
        signup_result = signup_response.json()
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                error_message = error_details.get('message', str(e))
            except:
                error_message = e.response.text or str(e)

        return jsonify({
            "success": False,
            "error": f"Failed to create account: {error_message}",
            "step": "account_creation"
        }), 500
        signup_result = signup_response.json()

    return signup_result

def choose_number(business_id, business_name, phone_data):
    phone_setup_success = False

    try:
        if phone_data.get('is_premium'):
            # Reserve premium number
            reserve_response = requests.post(
                f"{os.getenv('API_BASE_URL', 'http://localhost:5000')}/api/premium-numbers/reserve",
                json={
                    "phone_number": phone_data.get('phone_number'),
                    "business_id": business_id,
                    "friendly_name": business_name
                },
                timeout=30
            )
            pass
        else:
            # Purchase and configure regular number
            reserve_response = requests.post(
                f"{os.getenv('API_BASE_URL', 'http://localhost:5000')}/api/twilio/purchase-and-configure",
                json={
                    "business_id": business_id,
                    "phone_number": phone_data.get('phone_number'),
                    "friendly_name": business_name
                },
                timeout=30
            )

        reserve_response.raise_for_status()
        phone_setup_success = True

    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                error_message = error_details.get('message', str(e))
            except:
                error_message = e.response.text or str(e)

        print(f"Warning: Phone number setup failed: {error_message}")
        # Continue with onboarding even if phone setup fails


value = {'signup_payload': '{"create_account":{"businessName":"CardaMax 1975","adminFirstName":"Hany","adminLastName":"Elgaml","email":"hanyelgaml@ideationmax.com","password":"password","confirmPassword":"password","adminPhone":"hanyelgaml@ideationmax.com"},"choose_number":{"phone_number":"+13656155550","price":50,"is_premium":true,"locality":"","region":""},"activate_account":{"top_up_value":20,"autoRechargeEnabled":false,"rechargeThreshold":10,"rechargeAmount":20}}', 'topup_amount': '20', 'type': 'onboarding'}