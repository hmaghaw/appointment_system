from flask import Blueprint, request, jsonify, current_app, redirect, url_for
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import requests
import json
from ..services.clover_integration import CloverIntegration
from ..database import get_db_cursor

bp = Blueprint('clover', __name__, url_prefix='/api/clover')

# Clover OAuth endpoints
CLOVER_AUTH_URL = "https://sandbox.dev.clover.com/oauth/authorize"
CLOVER_TOKEN_URL = "https://sandbox.dev.clover.com/oauth/token"


def get_clover_credentials(business_id: int) -> Optional[Dict]:
    """Retrieve Clover credentials from the business_integration table"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT access_token, refresh_token, merchant_id, provider_data
            FROM business_integration
            WHERE business_id = %s AND provider = 'clover' AND status = 'active'
        """, (business_id,))
        return cursor.fetchone()


def update_clover_credentials(business_id: int, merchant_id: str, access_token: str, 
                            refresh_token: str = None, provider_data: dict = None) -> None:
    """Update or insert Clover credentials in the business_integration table"""
    with get_db_cursor(commit=True) as cursor:
        provider_data_json = json.dumps(provider_data) if provider_data else None
        
        cursor.execute("""
            INSERT INTO business_integration 
                (business_id, provider, merchant_id, access_token, refresh_token, provider_data, status)
            VALUES (%s, 'clover', %s, %s, %s, %s, 'active')
            ON DUPLICATE KEY UPDATE
                access_token = VALUES(access_token),
                refresh_token = COALESCE(VALUES(refresh_token), refresh_token),
                merchant_id = VALUES(merchant_id),
                provider_data = COALESCE(VALUES(provider_data), provider_data),
                updated_at = CURRENT_TIMESTAMP,
                status = 'active'
        """, (
            business_id,
            merchant_id,
            access_token,
            refresh_token,
            provider_data_json
        ))


@bp.route('/oauth/callback')
def clover_oauth_callback():
    """
    Handle Clover OAuth callback
    Expected query params: client_id, merchant_id, code, business_id
    """
    try:
        # Get query parameters
        client_id = request.args.get('client_id')
        merchant_id = request.args.get('merchant_id')
        auth_code = request.args.get('code')
        business_id = request.args.get('business_id')
        
        if not all([client_id, merchant_id, auth_code, business_id]):
            return jsonify({
                'success': False,
                'message': 'Missing required parameters: client_id, merchant_id, code, and business_id are required'
            }), 400
        
        # Get app credentials from config
        clover_client_id = current_app.config.get('CLOVER_APP_ID')
        clover_client_secret = current_app.config.get('CLOVER_APP_SECRET')
        
        if not all([clover_client_id, clover_client_secret]):
            return jsonify({
                'success': False,
                'message': 'Server configuration error: Missing Clover credentials'
            }), 500
        
        # Exchange auth code for access token
        token_data = {
            'client_id': clover_client_id,
            'client_secret': clover_client_secret,
            'code': auth_code
        }
        
        response = requests.post(CLOVER_TOKEN_URL, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        
        # Store the credentials
        update_clover_credentials(
            business_id=business_id,
            merchant_id=merchant_id,
            access_token=token_info['access_token'],
            refresh_token=token_info.get('refresh_token'),
            provider_data={
                'token_type': token_info.get('token_type'),
                'expires_in': token_info.get('expires_in'),
                'first_name': token_info.get('first_name'),
                'last_name': token_info.get('last_name')
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Successfully connected to Clover',
            'merchant_id': merchant_id
        })
        
    except requests.RequestException as e:
        current_app.logger.error(f"Clover OAuth error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error authenticating with Clover: {str(e)}'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in Clover OAuth: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred'
        }), 500


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

        # Sync regular items
        items = clover.list_items()
        for item in items:
            if sync_item(business_id, item):
                stats['items_synced'] += 1

        # Sync modifiers
        modifiers = clover.list_modifiers()
        for group in modifiers:
            if sync_modifier_group(business_id, group):
                stats['modifiers_synced'] += len(group.get('modifiers', []))

        # Sync options (for combos)
        options = clover.list_options()
        for group in options:
            if sync_option_group(business_id, group):
                stats['options_synced'] += len(group.get('options', []))

        # Sync combos
        combos = clover.list_combos()
        for combo in combos:
            if sync_combo(business_id, combo):
                stats['combos_synced'] += 1

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


def sync_item(business_id: int, item_data: Dict[str, Any]) -> bool:
    """Sync a single item from Clover to the database"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if item already exists
            cursor.execute("""
                           SELECT ri.item_id
                           FROM restaurant_item ri
                                    JOIN restaurant_item_integration rii ON ri.item_id = rii.item_id
                           WHERE rii.provider = 'clover'
                             AND rii.external_item_id = %s
                           """, (item_data.get('id'),))
            existing = cursor.fetchone()

            if existing:
                # Update existing item
                item_id = existing['item_id']
                cursor.execute("""
                               UPDATE restaurant_item
                               SET name        = %s,
                                   description = %s,
                                   base_price  = %s,
                                   is_active   = %s
                               WHERE item_id = %s
                               """, (
                                   item_data.get('name', ''),
                                   item_data.get('description', ''),
                                   float(item_data.get('price', 0)) / 100,  # Convert to dollars
                                   item_data.get('hidden', False) is False,  # Map hidden to is_active
                                   item_id
                               ))
            else:
                # Insert new item
                cursor.execute("""
                               INSERT INTO restaurant_item
                               (business_id, name, description, base_price, is_active)
                               VALUES (%s, %s, %s, %s, %s)
                               """, (
                                   business_id,
                                   item_data.get('name', ''),
                                   item_data.get('description', ''),
                                   float(item_data.get('price', 0)) / 100,  # Convert to cents
                                   item_data.get('hidden', False) is False  # Map hidden to is_active
                               ))
                item_id = cursor.lastrowid

            # Sync item integration mapping
            sync_item_integration(cursor, item_id, 'clover', item_data['id'], business_id)

            return True

    except Exception as e:
        print(f"Error syncing item {item_data.get('id')}: {e}")
        return False


def sync_item_integration(cursor, item_id: int, provider: str, external_id: str, business_id: int) -> None:
    """Create or update item integration mapping (external_id is unique per provider)"""
    cursor.execute("""
        INSERT INTO restaurant_item_integration (item_id, provider, external_item_id, business_id)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            item_id = VALUES(item_id),
            business_id = VALUES(business_id)
    """, (item_id, provider, external_id, business_id))


def sync_modifier_group(business_id: int, group_data: Dict[str, Any]) -> bool:
    """Sync a modifier group and its modifiers from Clover to the database"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if modifier group exists
            cursor.execute("""
                SELECT rmg.modifier_group_id
                FROM restaurant_modifier_group rmg
                JOIN restaurant_modifier_group_integration rmgi
                  ON rmg.modifier_group_id = rmgi.modifier_group_id
                WHERE rmgi.provider = 'clover'
                  AND rmgi.external_group_id = %s
            """, (group_data['group_id'],))
            existing = cursor.fetchone()

            if existing:
                group_id = existing['modifier_group_id']
                # Update existing group without description
                cursor.execute("""
                    UPDATE restaurant_modifier_group
                    SET name = %s,
                        is_required = %s,
                        min_select = %s,
                        max_select = %s,
                        business_id = %s
                    WHERE modifier_group_id = %s
                """, (
                    group_data.get('group_name', ''),
                    group_data.get('is_required', False),
                    group_data.get('min_required', 0),
                    group_data.get('max_allowed', 1),
                    business_id,
                    group_id
                ))
            else:
                # Insert new modifier group without description
                cursor.execute("""
                    INSERT INTO restaurant_modifier_group (
                        business_id, 
                        name, 
                        is_required, 
                        min_select, 
                        max_select
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    business_id,
                    group_data.get('group_name', ''),
                    group_data.get('is_required', False),
                    group_data.get('min_required', 0),
                    group_data.get('max_allowed', 1)
                ))
                group_id = cursor.lastrowid

            # Sync group integration mapping
            cursor.execute("""
                INSERT INTO restaurant_modifier_group_integration
                    (modifier_group_id, provider, external_group_id, business_id)
                VALUES (%s, 'clover', %s, %s) ON DUPLICATE KEY
                UPDATE
                    modifier_group_id = VALUES(modifier_group_id),
                    business_id = VALUES(business_id)
            """, (group_id, group_data['group_id'], business_id))

            # Get existing modifiers to track what needs to be deactivated
            cursor.execute("""
                SELECT rmi.external_modifier_id, rm.modifier_id, rm.is_active
                FROM restaurant_modifier rm
                JOIN restaurant_modifier_integration rmi ON rm.modifier_id = rmi.modifier_id
                WHERE rmi.provider = 'clover' 
                AND rm.modifier_group_id = %s
            """, (group_id,))
            existing_modifiers = {row['external_modifier_id']: row for row in cursor.fetchall()}
            processed_modifier_ids = set()

            # Sync modifiers
            for mod in group_data.get('modifiers', []):
                external_id = mod['id']
                cursor.execute("""
                    SELECT rm.modifier_id
                    FROM restaurant_modifier rm
                    JOIN restaurant_modifier_integration rmi ON rm.modifier_id = rmi.modifier_id
                    WHERE rmi.provider = 'clover'
                    AND rmi.external_modifier_id = %s
                """, (external_id,))
                existing_mod = cursor.fetchone()

                modifier_data = (
                    mod.get('name', ''),
                    float(mod.get('price', 0)) / 100,  # Convert to dollars
                    mod.get('available', True),
                    group_id
                )

                if existing_mod:
                    modifier_id = existing_mod['modifier_id']
                    # Update existing modifier with all fields
                    cursor.execute("""
                        UPDATE restaurant_modifier
                        SET name = %s,
                            price_delta = %s,
                            is_active = %s,
                            modifier_group_id = %s
                        WHERE modifier_id = %s
                    """, modifier_data + (modifier_id,))
                else:
                    cursor.execute("""
                        INSERT INTO restaurant_modifier (
                            name,
                            price_delta,
                            is_active,
                            modifier_group_id
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, modifier_data)
                    modifier_id = cursor.lastrowid

                # Track processed modifiers
                processed_modifier_ids.add(external_id)

                # Sync modifier integration mapping
                cursor.execute("""
                    INSERT INTO restaurant_modifier_integration
                        (modifier_id, provider, external_modifier_id, business_id)
                    VALUES (%s, 'clover', %s, %s) ON DUPLICATE KEY
                    UPDATE
                        modifier_id = VALUES(modifier_id),
                        business_id = VALUES(business_id)
                """, (modifier_id, external_id, business_id))

            # Deactivate any modifiers that exist in our DB but weren't in the API response
            if processed_modifier_ids:
                placeholders = ','.join(['%s'] * len(processed_modifier_ids))
                cursor.execute(f"""
                    UPDATE restaurant_modifier rm
                    JOIN restaurant_modifier_integration rmi ON rm.modifier_id = rmi.modifier_id
                    SET rm.is_active = FALSE
                    WHERE rmi.provider = 'clover'
                    AND rm.modifier_group_id = %s
                    AND rmi.external_modifier_id NOT IN ({placeholders})
                """, [group_id] + list(processed_modifier_ids))

            return True

    except Exception as e:
        print(f"Error syncing modifier group {group_data.get('group_id')}: {e}")
        return False


# Similar updates needed for sync_option_group and sync_combo functions
# Let me know if you'd like to see those as well

def sync_combo(business_id: int, combo_data: Dict[str, Any]) -> bool:
    """Sync a combo item and its groups"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if combo exists
            cursor.execute("""
                           SELECT ri.item_id
                           FROM restaurant_item ri
                                    JOIN restaurant_item_integration rii ON ri.item_id = rii.item_id
                           WHERE rii.provider = 'clover'
                             AND rii.external_item_id = %s
                           """, (combo_data.get('id'),))
            existing = cursor.fetchone()

            if existing:
                item_id = existing['item_id']
                # Update existing combo
                cursor.execute("""
                               UPDATE restaurant_item
                               SET name       = %s,
                                   base_price = %s,
                                   is_combo   = TRUE
                               WHERE item_id = %s
                               """, (
                                   combo_data.get('combo_name', ''),
                                   float(combo_data.get('price', 0)) / 100,  # Convert to dollars
                                   item_id
                               ))
            else:
                # Insert new combo
                cursor.execute("""
                               INSERT INTO restaurant_item
                               (business_id, name, description, base_price, is_combo, is_active)
                               VALUES (%s, %s, %s, %s, TRUE, TRUE)
                               """, (
                    business_id,
                                   combo_data.get('combo_name', ''),
                                   combo_data.get('description', ''),
                                   float(combo_data.get('price', 0)) / 100  # Convert to dollars
                               ))
                item_id = cursor.lastrowid

            # Ensure item integration exists
            sync_item_integration(cursor, item_id, 'clover', combo_data['id'], business_id)

            # Sync combo groups
            for group in combo_data.get('groups', []):
                # Get the option group ID from the integration table
                cursor.execute("""
                               SELECT rog.option_group_id
                               FROM restaurant_option_group rog
                                        JOIN restaurant_option_group_integration rogi
                                             ON rog.option_group_id = rogi.restaurant_option_group_id
                               WHERE rogi.provider = 'clover'
                                 AND rogi.external_group_id = %s
                               """, (group['group_id'],))
                group_row = cursor.fetchone()

                if not group_row:
                    print(f"Option group {group['group_id']} not found")
                    continue

                option_group_id = group_row['option_group_id']

                # Create or update combo group
                cursor.execute("""
                               INSERT INTO restaurant_combo_group
                                   (item_id, name, min_select, max_select)
                               VALUES (%s, %s, %s, %s) ON DUPLICATE KEY
                               UPDATE
                                   name =
                               VALUES (name), min_select =
                               VALUES (min_select), max_select =
                               VALUES (max_select)
                               """, (
                                   item_id,
                                   group.get('group_name', ''),
                                   group.get('min_required', 1),
                                   group.get('max_allowed', 1)
                               ))
                combo_group_id = cursor.lastrowid

                # Sync combo group integration
                cursor.execute("""
                               INSERT INTO restaurant_combo_group_integration
                                   (combo_group_id, provider, external_group_id, business_id)
                               VALUES (%s, 'clover', %s, %s) ON DUPLICATE KEY
                               UPDATE
                                   external_group_id =
                               VALUES (external_group_id), 
                               """, (combo_group_id, group['group_id'], business_id))

                # Sync combo group items
                for option in group.get('options', []):
                    # Get the option ID from the integration table
                    cursor.execute("""
                                   SELECT ro.option_id
                                   FROM restaurant_option ro
                                            JOIN restaurant_option_integration roi
                                                 ON ro.option_id = roi.restaurant_option_id
                                   WHERE roi.provider = 'clover'
                                     AND roi.external_option_id = %s
                                   """, (option['id'],))
                    option_row = cursor.fetchone()

                    if not option_row:
                        print(f"Option {option['id']} not found")
                        continue

                    option_id = option_row['option_id']

                    # Create combo group item
                    cursor.execute("""
                                   INSERT INTO restaurant_combo_group_item
                                       (combo_group_id, option_id, price_delta)
                                   VALUES (%s, %s, %s) ON DUPLICATE KEY
                                   UPDATE
                                       price_delta =
                                   VALUES (price_delta)
                                   """, (
                                       combo_group_id,
                                       option_id,
                                       float(option.get('price', 0)) / 100 # Convert to dollars
                                   ))
                    combo_item_id = cursor.lastrowid

                    # Sync combo group item integration
                    cursor.execute("""
                                   INSERT INTO restaurant_combo_group_item_integration
                                       (combo_group_item_id, provider, external_item_id, business_id)
                                   VALUES (%s, 'clover', %s, %s) ON DUPLICATE KEY
                                   UPDATE
                                       external_item_id =
                                   VALUES (external_item_id), 
                                   """, (combo_item_id, option['id'], business_id))

            return True

    except Exception as e:
        print(f"Error syncing combo {combo_data.get('id')}: {e}")
        return False


def sync_option_group(business_id: int, group_data: Dict[str, Any]) -> bool:
    """Sync an option group and its options from Clover to the database"""
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if option group exists
            cursor.execute("""
                           SELECT rog.option_group_id
                           FROM restaurant_option_group rog
                                    JOIN restaurant_option_group_integration rogi
                                         ON rog.option_group_id = rogi.option_group_id
                           WHERE rogi.provider = 'clover'
                             AND rogi.external_group_id = %s
                           """, (group_data.get('group_id'),))
            existing = cursor.fetchone()

            if existing:
                group_id = existing['option_group_id']
                # Update existing option group
                cursor.execute("""
                               UPDATE restaurant_option_group
                               SET name        = %s,
                                   description = %s,
                                   min_select  = %s,
                                   max_select  = %s,
                                   is_required = %s
                               WHERE option_group_id = %s
                               """, (
                                   group_data.get('group_name', ''),
                                   group_data.get('description', ''),
                                   group_data.get('min_required', 1),
                                   group_data.get('max_allowed', 1),
                                   group_data.get('required', False),
                                   group_id
                               ))
            else:
                # Insert new option group
                cursor.execute("""
                               INSERT INTO restaurant_option_group (business_id,
                                                                    name,
                                                                    description,
                                                                    min_select,
                                                                    max_select,
                                                                    is_required)
                               VALUES (%s, %s, %s, %s, %s, %s)
                               """, (
                                   business_id,
                                   group_data.get('group_name', ''),
                                   group_data.get('description', ''),
                                   group_data.get('min_required', 1),
                                   group_data.get('max_allowed', 1),
                                   group_data.get('required', False)
                               ))
                group_id = cursor.lastrowid

            # Sync group integration mapping
            cursor.execute("""
                           INSERT INTO restaurant_option_group_integration (option_group_id,
                                                                            provider,
                                                                            external_group_id,
                                                                            business_id)
                           VALUES (%s, 'clover', %s, %s) ON DUPLICATE KEY
                           UPDATE
                               external_group_id =
                           VALUES (external_group_id), 
                           """, (group_id, group_data['group_id'], business_id))

            # Sync options
            for option in group_data.get('options', []):
                # Check if option exists
                cursor.execute("""
                               SELECT ro.option_id
                               FROM restaurant_option ro
                                        JOIN restaurant_option_integration roi
                                             ON ro.option_id = roi.option_id
                               WHERE roi.provider = 'clover'
                                 AND roi.external_option_id = %s
                               """, (option.get('id'),))
                existing_opt = cursor.fetchone()

                if existing_opt:
                    option_id = existing_opt['option_id']
                    # Update existing option
                    cursor.execute("""
                                   UPDATE restaurant_option
                                   SET name        = %s,
                                       description = %s,
                                       price_delta = %s,
                                       is_active   = %s
                                   WHERE option_id = %s
                                   """, (
                                       option.get('name', ''),
                                       option.get('description', ''),
                                       float(option.get('price', 0)) / 100,  # Convert to dollars
                                       option.get('available', True),
                                       option_id
                                   ))
                else:
                    # Insert new option
                    cursor.execute("""
                                   INSERT INTO restaurant_option (option_group_id,
                                                                  name,
                                                                  description,
                                                                  price_delta,
                                                                  is_active)
                                   VALUES (%s, %s, %s, %s, %s)
                                   """, (
                                       group_id,
                                       option.get('name', ''),
                                       option.get('description', ''),
                                       float(option.get('price', 0)) / 100,  # Convert to dollars
                                       option.get('available', True)
                                   ))
                    option_id = cursor.lastrowid

                # Sync option integration mapping
                cursor.execute("""
                               INSERT INTO restaurant_option_integration (option_id,
                                                                          provider,
                                                                          external_option_id,
                                                                          business_id)
                               VALUES (%s, 'clover', %s, %s) ON DUPLICATE KEY
                               UPDATE
                                   external_option_id =
                               VALUES (external_option_id), 
                               """, (option_id, option['id'], business_id))

            return True

    except Exception as e:
        print(f"Error syncing option group {group_data.get('group_id')}: {e}")
        return False