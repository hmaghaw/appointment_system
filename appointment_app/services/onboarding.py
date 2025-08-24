from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import requests
import os
import json

from pyasn1_modules.rfc2985 import FriendlyName

from appointment_app.services.auth_token_validator import verify_bearer_token
from appointment_app.database import get_db_cursor
import mysql.connector
from auth_token_validator import generate_jwt_token
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
        # signup_result = signup(signup_data)
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
                                   recharge_amount       = %s,
                                   recharge_threshold    = %s,
                                   balance               = COALESCE(balance, 0) + %s,
                                   updated_at            = NOW()
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


def signup(signup_data, headers):
    try:
        signup_response = requests.post(
            f"{os.getenv('API_BASE_URL', 'http://localhost:5000')}/api/auth/signup",
            json=signup_data,
            headers=headers
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

        signup_result = signup_response.json()

    return signup_result


def choose_number(business_id, business_name, phone_data, headers):
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
                headers=headers
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
                headers=headers
            )

        reserve_response.raise_for_status()
        phone_setup_success = True
        return reserve_response.json()

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

def update_friendly_number(phone_sid, friendly_name, headers):
    reserve_response = requests.post(
        f"{os.getenv('API_BASE_URL', 'http://localhost:5000')}/api/twilio/update-friendly-name",
        json={
            "phone_sid": phone_sid,
            "friendly_name": friendly_name
        },
        headers=headers
    )


metadata = {
  "create_account" : {
    "businessName" : "CardaMax 1985",
    "adminFirstName" : "Hany",
    "adminLastName" : "Elgaml",
    "email" : "hani_elmaghawri@yahoo.com",
    "password" : "password",
    "confirmPassword" : "password",
    "adminPhone" : "+11112223333"
  },
  "choose_number" : {
    "phone_number" : "+13656155550",
    "price" : 50,
    "is_premium" : 1,
    "locality" : "",
    "region" : ""
  },
  "activate_account" : {
    "top_up_value" : 20,
    "autoRechargeEnabled" : 0,
    "rechargeThreshold" : 10,
    "rechargeAmount" : 20
  }
}
def start_onboarding(metadata):
    user = {
        "id": 999,
        "email": "hanyelgaml@ideationmax.com",
        "business_id": 999,
        "role": "admin"
    }
    auth_token = generate_jwt_token(user, validity=3600)
    headers = {"Content-Type": "application/json"}
    headers["Authorization"] = f"Bearer {auth_token}"

    signup_data = metadata['create_account']
    # business_name = data.get('businessName')
    # first_name = data.get('adminFirstName')
    # last_name = data.get('adminLastName')
    # email = data.get('email')
    # password = data.get('password')
    # admin_phone = data.get('adminPhone')
    #
    signup_result = signup(signup_data, headers=headers)
    user_id = signup_result['user']['id']
    business_id = signup_result['user']['business_id']
    business_name = metadata['create_account']['businessName']
    pass
    response = choose_number(business_id, business_name, metadata['choose_number'],headers=headers)
    friendly_name = business_name
    update_friendly_number(response['data']['phone_sid'], friendly_name, headers)

x = start_onboarding(metadata)

pass