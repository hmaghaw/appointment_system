from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import requests
import os
import json
import logging
from pyasn1_modules.rfc2985 import FriendlyName
from appointment_app.services.auth_token_validator import verify_bearer_token
from appointment_app.database import get_db_cursor
import mysql.connector
from appointment_app.services.auth_token_validator import generate_jwt_token

# Configure logging
logger = logging.getLogger(__name__)

def reserve_phone_number(business_id: int, business_name: str, phone_data: dict) -> dict:
    """
    Reserve a phone number (premium or regular) and update its friendly name.
    
    Args:
        business_id: ID of the business
        business_name: Name of the business for friendly name
        phone_data: Dictionary containing phone number details
        headers: Request headers for authentication
        
    Returns:
        dict: Response from the phone number reservation API
        
    Raises:
        requests.exceptions.RequestException: If the API request fails
        ValueError: If required data is missing or invalid
    """
    user = {"id": 999, "email": "hanyelgaml@ideationmax.com", "business_id": 999, "role": "admin"}
    auth_token = generate_jwt_token(user, validity=3600)
    headers = {
        'Authorization': f"Bearer {auth_token}",
        'Content-Type': 'application/json'
    }
    required_fields = ['phone_number']
    if not all(field in phone_data for field in required_fields):
        raise ValueError(f"Missing required fields in phone_data. Required: {required_fields}")

    is_premium = phone_data.get('is_premium', False)
    endpoint = (
        "/api/premium-numbers/reserve" if is_premium 
        else "/api/twilio/purchase-and-configure"
    )
    
    payload = {
        "phone_number": phone_data['phone_number'],
        "business_id": business_id,
        "friendly_name": business_name
    }
    
    try:
        # Make the API request to reserve/purchase the number
        response = requests.post(
            f"{os.getenv('API_BASE_URL', '')}{endpoint}",
            json=payload,
            headers=headers,
            timeout=30  # 30 seconds timeout
        )
        response.raise_for_status()
        
        result = response.json()
        
        # If we have a phone_sid in the response, update the friendly name
        if 'data' in result and 'phone_sid' in result['data']:
            update_friendly_name(
                phone_sid=result['data']['phone_sid'],
                friendly_name=business_name,
                headers=headers
            )
            
        return result
        
    except requests.exceptions.RequestException as e:
        error_message = f"Failed to reserve phone number: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                error_message = error_details.get('message', error_message)
            except ValueError:
                error_message = e.response.text or error_message
        
        logger.error(error_message)
        raise


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
