from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import requests
import os
import json
from typing import Dict, Any, Optional
import logging
from pyasn1_modules.rfc2985 import FriendlyName
#from appointment_app.services.auth_token_validator import verify_bearer_token
from appointment_app.database import get_db_cursor
import mysql.connector
from appointment_app.services.auth_token_validator import generate_jwt_token

# Configure logging
logger = logging.getLogger(__name__)
def business_phone_exists(business_id: int, phone_number: str) -> bool:
    with get_db_cursor(database='appointment_db', commit=False, dictionary=True) as cursor:
        cursor.execute("""
            SELECT business_phone_id
            FROM business_phone
            WHERE business_id = %s
              AND business_phone = %s
            LIMIT 1
        """, (business_id, phone_number))

        row = cursor.fetchone()
        return row is not None

def reserve_phone_number(
    business_id: int,
    business_name: str,
    phone_number: str,
    is_premium: bool,
    headers: dict
) -> dict:
    """
    Reserve a phone number (premium or regular) and update its friendly name.

    Always returns a dict with "success": True/False.
    """

    endpoint = (
        "/api/premium-numbers/reserve" if is_premium
        else "/api/twilio/purchase-and-configure"
    )

    payload = {
        "phone_number": phone_number,
        "business_id": business_id,
        "friendly_name": business_name
    }

    try:
        # Make the API request to reserve/purchase the number
        response = requests.post(
            f"{os.getenv('API_BASE_URL', '')}{endpoint}",
            json=payload,
            headers=headers
        )
        response.raise_for_status()

        result = response.json()

        # If we have a phone_sid in the response, update the friendly name
        if "data" in result and "phone_sid" in result["data"]:
            update_friendly_name(
                phone_sid=result["data"]["phone_sid"],
                friendly_name=business_name,
                headers=headers
            )

        return {
            "success": True,
            "data": result.get("data"),
            "message": result.get("message", "Phone number reserved successfully")
        }

    except requests.exceptions.RequestException as e:
        error_message = f"Failed to reserve phone number: {str(e)}"
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.json()
                error_message = error_details.get("message", error_message)
            except ValueError:
                error_message = e.response.text or error_message

        logger.error(error_message)
        return {
            "success": False,
            "error": error_message
        }

    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message)
        return {
            "success": False,
            "error": error_message
        }



def update_friendly_name(phone_sid: str, friendly_name: str, headers: dict) -> dict:
    """
    Update the friendly name of a phone number.
    
    Args:
        phone_sid: The SID of the phone number to update
        friendly_name: The new friendly name to set
        headers: Request headers for authentication
        
    Returns:
        dict: {
            "success": bool,  # Whether the update was successful
            "message": str,   # Status message
            "data": dict      # Response data if successful, or error details if failed
        }
        
    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    if not phone_sid or not friendly_name:
        error_msg = "Missing phone_sid or friendly_name for update"
        logger.warning(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "data": {}
        }
    
    try:
        response = requests.post(
            f"{os.getenv('API_BASE_URL', '')}/api/twilio/update-friendly-name",
            json={
                "phone_sid": phone_sid,
                "friendly_name": friendly_name
            },
            headers=headers,
            timeout=10  # 10 seconds timeout
        )
        response.raise_for_status()
        
        response_data = response.json()
        return {
            "success": True,
            "message": "Friendly name updated successfully",
            "data": response_data
        }
        
    except requests.exceptions.RequestException as e:
        error_message = f"Failed to update friendly name: {str(e)}"
        error_data = {}
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_message = error_data.get('message', error_message)
            except ValueError:
                error_message = e.response.text or error_message
        
        logger.error(error_message)
        
        return {
            "success": False,
            "message": error_message,
            "data": error_data
        }

def get_provisioning_info(provisioning_id: int) -> dict:
    """
    Fetch provisioning info and related business name.
    Always returns a dict with success flag.
    """
    try:
        with get_db_cursor(database='appointment_db', commit=False, dictionary=True) as cursor:
            # Get provisioning record
            cursor.execute("""
                SELECT provisioning_id,
                       business_id,
                       phone_number,
                        monthly_fee,
                        first_time_fee,
                       is_premium,
                       payment_intent_id,
                       status
                FROM provisioning
                WHERE provisioning_id = %s
            """, (provisioning_id,))
            provisioning_row = cursor.fetchone()

            if not provisioning_row:
                return {"success": False, "error": "Provisioning record not found"}

            # Get business name
            cursor.execute("""
                SELECT name AS business_name
                FROM business
                WHERE business_id = %s
            """, (provisioning_row['business_id'],))
            business_row = cursor.fetchone()

            if not business_row:
                return {"success": False, "error": "Business not found"}

        return {
            "success": True,
            "provisioning_id": provisioning_row['provisioning_id'],
            "business_id": provisioning_row['business_id'],
            "business_name": business_row['business_name'],
            "phone_number": provisioning_row['phone_number'],
            "is_premium": provisioning_row['is_premium'],
            "monthly_fee": provisioning_row['monthly_fee'],
            "first_time_fee": provisioning_row['first_time_fee'],
            "payment_intent_id": provisioning_row['payment_intent_id'],
            "status": provisioning_row['status']
        }

    except mysql.connector.Error as err:
        return {"success": False, "error": f"Database error: {str(err)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def update_business_ledger(result):
    business_id = result['business_id']
    monthly_fee = result['monthly_fee']
    first_time_fee = result['first_time_fee']
    payment_intent_id = result['payment_intent_id']
    phone_number = result['phone_number']

    with get_db_cursor(database='appointment_db', commit=True) as cursor:
        # 1. Monthly fee entry
        cursor.execute("""
            INSERT INTO business_ledger (business_id, amount_cents, reason, comments, request_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            business_id,
            monthly_fee,
            "Phone monthly fee",
            f"Phone number: {phone_number}",
            f"{payment_intent_id}_monthly"
        ))

        # 2. First month fee entry
        cursor.execute("""
            INSERT INTO business_ledger (business_id, amount_cents, reason, comments, request_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            business_id,
            first_time_fee,
            "Phone first month fee",
            f"Phone number: {phone_number}",
            f"{payment_intent_id}_first"
        ))


def update_provisioning_status(provisioning_id: int, status: str) -> dict:
    """
    Update the status of a provisioning record.

    Args:
        provisioning_id (int): The ID of the provisioning record
        status (str): New status ('pending', 'success', 'failed')

    Returns:
        dict: { "success": True/False, "provisioning_id": ..., "status": ... }
    """
    try:
        with get_db_cursor(database='appointment_db', commit=True, dictionary=True) as cursor:
            cursor.execute("""
                UPDATE provisioning
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE provisioning_id = %s
            """, (status, provisioning_id))

            if cursor.rowcount == 0:
                return {"success": False, "error": "Provisioning record not found"}

        return {"success": True, "provisioning_id": provisioning_id, "status": status}

    except mysql.connector.Error as err:
        return {"success": False, "error": f"Database error: {str(err)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def provision_phone_number(provisioning_id):
    user = {"id": 999, "email": "hanyelgaml@ideationmax.com", "business_id": 999, "role": "admin"}
    auth_token = generate_jwt_token(user, validity=3600)
    headers = {
        'Authorization': f"Bearer {auth_token}",
        'Content-Type': 'application/json'
    }
    result = get_provisioning_info(provisioning_id)

    if result["success"]:
        if business_phone_exists(result["business_id"], result["phone_number"]):
            logger.warning("This looks like a repeated transaction: Phone number already exists for this business.")
            success = True
            return {
                "success": True,
                "message": "Phone number already exists for this business."
            }
        else:
            reserve_result = reserve_phone_number(
                business_id=result["business_id"],
                business_name=result["business_name"],
                phone_number=result["phone_number"],
                is_premium=result["is_premium"],
                headers=headers
            )
            if reserve_result['success']:
                update_business_ledger(result)
                update_provisioning_status(provisioning_id, 'success')
                return {
                    "success": True,
                    "provisioning_id": result["provisioning_id"],
                    "reservation": reserve_result,
                    "message": reserve_result['message']
                }
            else:
                refund_result = process_refund(provisioning_id,
                    business_id=result["business_id"],
                    payment_intent_id=result["payment_intent_id"],
                    headers=headers
                )
                return refund_result

def process_refund(provisioning_id, business_id: int, payment_intent_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Process a refund for a failed phone number provisioning.
    
    Args:
        business_id: ID of the business requesting the refund
        payment_intent_id: Stripe payment intent ID to refund
        headers: Request headers for authentication
        
    Returns:
        dict: {
            "success": bool,  # Whether the refund was successful
            "message": str,   # Status message
            "data": dict      # Response data if successful, or error details if failed
        }
    """
    payload = {
        "business_id": business_id,
        "payment_intent_id": payment_intent_id,
        "reason": "provisioning_failed"
    }
    
    try:
        response = requests.post(
            f"{os.getenv('API_BASE_URL', '')}/api/stripe/refund",
            json=payload,
            headers=headers
        )
        response.raise_for_status()

        result = response.json()
        if not isinstance(result, dict):
            return {"success": False, "error": "Invalid response format"}

        # Normalize success flag
        if result.get("success") is True:
            update_provisioning_status(provisioning_id, 'failed')
            return {"success": True, **result}
        return {"success": False, **result}

    except requests.exceptions.RequestException as e:
        error_message = f"Failed to call refund API: {str(e)}"
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.json()
                error_message = error_details.get("message", error_message)
            except ValueError:
                error_message = e.response.text or error_message

        return {"success": False, "error": error_message}


#provision_phone_number(2)