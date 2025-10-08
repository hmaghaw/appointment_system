from flask import Blueprint, request, jsonify, current_app, redirect, url_for
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import requests
import json
from ..services.clover_integration import CloverIntegration
from ..database import get_db_cursor
from appointment_app.services.auth_token_validator import generate_jwt_token, verify_bearer_token, generate_clover_jwt_token
import os
from ..services.one_time_token_manager import OneTimeTokenManager
from ..services.entity_integration import EntityIntegrationManager
from appointment_app.services.restaurant import restaurant_service

bp = Blueprint('clover', __name__, url_prefix='/api/clover')



integration = EntityIntegrationManager(provider='clover')

# SANDBOX URL
# CLOVER_URL=https://sandbox.dev.clover.com
# PRODUCTION URL
# CLOVER_URL=https://www.clover.com

# Configure APP
# - Web App
# - site URL: <polydial>/api/clover/oauth/callback
# Permissions
# Inventory Read
# Merchant Read
# Orders Read Write

def get_clover_credentials(business_id: int) -> Optional[Dict]:
    """Retrieve Clover credentials from the business_integration table"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT access_token, refresh_token, merchant_id, provider_data
            FROM business_integration
            WHERE business_id = %s AND provider = 'clover' AND status = 'active'
        """, (business_id,))
        return cursor.fetchone()


def update_clover_credentials(business_id: int, merchant_id: str, access_token: str) -> None:
    """Update or insert Clover credentials in the business_integration table"""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO business_integration 
                (business_id, provider, merchant_id, access_token, status)
            VALUES (%s, 'clover', %s, %s, 'active')
            ON DUPLICATE KEY UPDATE
                access_token = VALUES(access_token),
                merchant_id = VALUES(merchant_id),
                updated_at = CURRENT_TIMESTAMP,
                status = 'active'
        """, (
            business_id,
            merchant_id,
            access_token
        ))



# Add these imports at the top of the file

def get_business_id(merchant_id):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
                       SELECT business_id
                       FROM business_integration
                       WHERE merchant_id = %s
                         AND provider = 'clover'
                       """, (merchant_id,))
        result = cursor.fetchone()
        if result:
            return result['business_id']
        else:
            return None

def get_or_create_business_for_merchant(merchant_id: str, merchant_name: str, cursor) -> int:
    """Get existing business ID for merchant or create a new one."""
    business_id = get_business_id(merchant_id)
    if business_id:
        return business_id
    # Create new business
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO business (name, business_type, status)
            VALUES (%s, 'restaurant', 'active')
            """,
            (merchant_name,),
        )
        business_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO business_languages (business_id, language_code, is_default, language_voice_id)
            VALUES (%s, %s, %s, %s)
            """,
            (business_id, 'en', True, 14)  ## Polly.Salli
        )
        return business_id


def create_clover_admin_user(business_id: int, merchant_id: str, cursor) -> int:
    """Create an admin user for the Clover-connected business."""
    cursor.execute("""
                   INSERT INTO users (first_name, last_name, email, password_hash,
                                      business_id, role, email_verified, active, auth_provider)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                   """, (
                       f"Clover-{merchant_id}",
                       "User",
                       f"clover-{merchant_id}@example.com",
                       None,  # No password for OAuth users
                       business_id,
                       'admin',
                       True,  # email_verified
                       True,  # active
                       'clover'
                   ))
    return cursor.fetchone()['id']


def exchange_auth_code(business_id, code: str) -> Dict:
    """Exchange authorization code for access token."""
    clover_client_id, clover_client_secret, clover_url = get_clover_app(business_id)
    clover_token_url = f"{clover_url}/oauth/token"
    response = requests.post(
        clover_token_url,
        data={
            'client_id': clover_client_id,
            'client_secret': clover_client_secret,
            'code': code
        }
    )
    response.raise_for_status()
    return response.json()

@bp.route('/login', methods=['POST'])
def clover_login():
    data = request.get_json()
    token = data['token']
    temp_token = OneTimeTokenManager()
    business_id = temp_token.consume_token(token,"clover")
    if business_id:
        polydial_token = generate_clover_jwt_token(business_id)
        # Get business info
        business = get_business_info(business_id)

        return jsonify({
            'success': True,
            'access_token': polydial_token,
            'token_type': 'Bearer',
            'expires_in': 86400,
            'admin': {},
            'business': business
        }), 200
    else:
        return {
          'success': False,
          'error': 'invalid_or_expired_token',
          'message': 'The one-time token is invalid, expired, or has already been used.'
        }

def get_business_name(clover_url, merchant_id, access_token):
    url = f"{clover_url}/v3/merchants/{merchant_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers).json()
    result = resp.get("name")
    return result

def get_business_info(business_id):
    """Get business information"""
    with get_db_cursor() as cursor:
        query = "SELECT * FROM business WHERE business_id = %s"
        cursor.execute(query, (business_id,))
        business = cursor.fetchone()   # fetch one row

    if business:
        return {
            'id': business['business_id'],
            'name': business['name'],
            'business_type': business['business_type'],
            'slogan': "Business Slogan",  # static for now
            'timezone': business['timezone'],
            'status': business['status'],
            'provider': 'clover'
        }
    return None

def get_clover_app(business_id):
    with get_db_cursor() as cursor:
        cursor.execute("""
                       SELECT app_id, app_secret, clover_url
                       FROM restaurant_clover_app
                       WHERE business_id = %s
                         LIMIT 1
                       """, (business_id,))

        result = cursor.fetchone()
        if result:
            clover_client_id = result['app_id']
            clover_client_secret = result['app_secret']
            clover_url = result['clover_url']
        else:
            clover_client_id = os.getenv('CLOVER_APP_ID')
            clover_client_secret = os.getenv('CLOVER_APP_SECRET')
            clover_url = os.getenv('CLOVER_URL')

    return clover_client_id, clover_client_secret, clover_url

@bp.route('/oauth/callback')
def clover_oauth_callback():
    """
    Handle Clover OAuth callback
    Expected query params: client_id, merchant_id, code
    """
    try:
        # Get and validate parameters
        FRONTEND_URL = os.getenv('FRONTEND_URL')
        client_id = request.args.get('client_id')
        merchant_id = request.args.get('merchant_id')
        auth_code = request.args.get('code')
        business_id = get_business_id(merchant_id)
        clover_client_id, clover_client_secret, clover_url = get_clover_app(business_id)
        if not all([client_id, merchant_id, auth_code]):
            return jsonify({
                'success': False,
                'message': 'Missing required parameters: client_id, merchant_id, and code are required'
            }), 400

        # Get app credentials
        token_info = exchange_auth_code(business_id, auth_code)


        temp_token = OneTimeTokenManager()

        if business_id:
            one_time_token = temp_token.add_token(business_id, 'clover')
            return redirect(f"{FRONTEND_URL}/login-clover?token=" + one_time_token)
        else:
            merchant_name = get_business_name(clover_url, merchant_id, token_info['access_token'])

            # Handle business and user setup
            with get_db_cursor(commit=True) as cursor:
                business_id = get_or_create_business_for_merchant(merchant_id, merchant_name, cursor)
            # Store the credentials
            update_clover_credentials(
                business_id=business_id,
                merchant_id=merchant_id,
                access_token=token_info['access_token']
            )
            one_time_token = temp_token.add_token(business_id, 'clover')
            return redirect(f"{FRONTEND_URL}/onboarding-clover?token=" + one_time_token)

    except requests.RequestException as e:
        current_app.logger.error(f"Clover OAuth error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error authenticating with Clover: {str(e)}'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in Clover OAuth: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred'
        }), 500


def business_exists(business_id: int, cursor) -> bool:
    """Check if a business exists in the database."""
    cursor.execute("SELECT 1 FROM business WHERE business_id = %s", (business_id,))
    result = cursor.fetchone()
    return bool(result)

@bp.route('/sync', methods=['POST'])
def sync_clover_data():
    """
    Sync Clover data with the local database

    Request body: {
        "business_id": int  # ID of the business to sync data for
    }

    Returns: {
        "success": bool,
        "message": str,
        "data": {
            "items_synced": int,
            "modifiers_synced": int,
            "options_synced": int,
            "combos_synced": int
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'business_id' not in data:
            return jsonify({
                "success": False,
                "message": "business_id is required"
            }), 400

        business_id = data['business_id']
        
        # Check if business has Clover connected
        credentials = get_clover_credentials(business_id)
        if not credentials:
            return jsonify({
                "success": False,
                "message": "Clover is not connected for this business"
            }), 400
            
        # Initialize Clover client with the stored credentials
        clover = CloverIntegration(
            business_id=business_id,
            access_token=credentials['access_token'],
            merchant_id=credentials['merchant_id']
        )

        # Initialize counters
        stats = {
            'items_synced': 0,
            'modifiers_synced': 0,
            'options_synced': 0,
            'combos_synced': 0
        }
        categories = clover.list_categories()
        sync_categories(categories, business_id)
        # Sync modifiers
        modifiers = clover.list_modifiers()
        sync_modifier_group(modifiers, business_id)
        # Sync regular items
        items = clover.list_items()
        sync_items(items, business_id)
        # Link Categories to items
        item_categories = clover.list_categories(expand_items=True)
        sync_item_categories(item_categories, business_id)

        # Options and Combos are not handled

        return jsonify({
            "success": True,
            "message": "Sync completed successfully",
            "data": stats
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error during sync: {str(e)}",
            "data": stats if 'stats' in locals() else None
        }), 500

def sync_items(items, business_id):
    for item in items:
        item_id = integration.entity_exists('item',item['id'], business_id)
        if not item_id:
            item_id = restaurant_service.create_item(business_id, item)
            integration.create_entity('item', item_id, item['id'], business_id, item['name'])
        else:
            restaurant_service.update_item(item_id, item)
            restaurant_service.delete_item_category_maps(item_id)

        for modifier_group in item['modifierGroups']['elements']:
            modifier_group_id = integration.entity_exists('modifier_group',modifier_group['id'], business_id)
            if modifier_group['deleted']:
                restaurant_service.delete_item_modifier_group(item_id, modifier_group_id)
            else:
                restaurant_service.create_item_modifier_group(item_id, modifier_group_id)

def sync_item_categories(item_categories, business_id):
    for category in item_categories:
        category_id = category['category_id']
        category_id = integration.entity_exists('category', category_id, business_id)
        items = category.get('items', [])
        for item in items:
            item_id = integration.entity_exists('item',item['id'], business_id)

            restaurant_service.create_item_category_map(item_id, category_id)
        pass

def sync_modifier_group(modifiers, business_id):
    """Sync modifier groups and their modifiers with the database"""
    for group in modifiers:
        group_name = group['group_name']
        external_group_id = group['group_id']
        modifier_group_id = integration.entity_exists('modifier_group',external_group_id, business_id)
        if not external_group_id:
            # Create new modifier group
            modifier_group_id = restaurant_service.create_modifier_group(group_name, business_id)
            integration.create_entity('modifier_group', modifier_group_id, external_group_id, business_id, group_name)
            # Process each modifier in the group
            for modifier in group.get('modifiers', []):
                external_modifier_id = modifier['id']
                modifier_name = modifier['name']
                modifier_price = modifier['price']
                modifier_id = integration.entity_exists('modifier', external_modifier_id, business_id)
                # Create the modifier
                if not modifier_id:
                    modifier_id = restaurant_service.create_modifier(
                        modifier_group_id=modifier_group_id,
                        modifier_name=modifier_name,
                        modifier_price=modifier_price
                    )
                    integration.create_entity('modifier', modifier_id, external_modifier_id, business_id, modifier_name)
                else:
                    restaurant_service.update_modifier(modifier_group_id, modifier_id, modifier_name, modifier_price)
        else:
            restaurant_service.update_modifier_group(modifier_group_id, group_name, False)

def sync_categories(categories, business_id):
    """Sync categories and their items with the database"""
    for category in categories:
        category_name = category['category_name']
        external_category_id = category['category_id']

        category_id = integration.entity_exists('category', external_category_id, business_id)
        # Check if this category already exists
        if not category_id:
            # Create new category
            category_id = restaurant_service.create_category(category_name, business_id)
            integration.create_entity(
                'category',
                category_id,
                external_category_id,
                business_id,
                category_name
            )
        else:
            restaurant_service.update_category(category_id, category_name)
