from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional
from datetime import datetime
from ..services.clover_integration import CloverIntegration
from ..database import get_db_cursor

bp = Blueprint('clover', __name__, url_prefix='/api/clover')


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
        clover = CloverIntegration(business_id)

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
                                   int(float(item_data.get('price', 0)) * 100),  # Convert to cents
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
                                   int(float(item_data.get('price', 0)) * 100),  # Convert to cents
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
    """Sync a modifier group and its modifiers"""
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
                # Update existing group
                cursor.execute("""
                    UPDATE restaurant_modifier_group
                    SET name        = %s,
                        is_required = %s,
                        min_select  = %s,
                        max_select  = %s
                    WHERE modifier_group_id = %s
                """, (
                    group_data.get('group_name', ''),
                    group_data.get('is_required', False),
                    group_data.get('min_required', 0),
                    group_data.get('max_allowed', 1),
                    group_id
                ))
            else:
                # Insert new modifier group
                cursor.execute("""
                    INSERT INTO restaurant_modifier_group
                        (business_id, name, is_required, min_select, max_select)
                    VALUES (%s, %s, %s, %s, %s)
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
                VALUES (%s, 'clover', %s, %s)
                ON DUPLICATE KEY UPDATE
                    modifier_group_id = VALUES(modifier_group_id),
                    business_id = VALUES(business_id)
            """, (group_id, group_data['group_id'], business_id))

            # Sync modifiers
            for mod in group_data.get('modifiers', []):
                cursor.execute("""
                    SELECT rm.modifier_id
                    FROM restaurant_modifier rm
                    JOIN restaurant_modifier_integration rmi
                      ON rm.modifier_id = rmi.modifier_id
                    WHERE rmi.provider = 'clover'
                      AND rmi.external_modifier_id = %s
                """, (mod['id'],))
                existing_mod = cursor.fetchone()

                if existing_mod:
                    modifier_id = existing_mod['modifier_id']
                    cursor.execute("""
                        UPDATE restaurant_modifier
                        SET name        = %s,
                            price_delta = %s,
                            is_active   = TRUE
                        WHERE modifier_id = %s
                    """, (
                        mod.get('name', ''),
                        int(float(mod.get('price', 0))),  # Clover usually returns cents
                        modifier_id
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO restaurant_modifier
                            (modifier_group_id, name, price_delta, is_active)
                        VALUES (%s, %s, %s, TRUE)
                    """, (
                        group_id,
                        mod.get('name', ''),
                        int(float(mod.get('price', 0)))
                    ))
                    modifier_id = cursor.lastrowid

                # Sync modifier integration mapping
                cursor.execute("""
                    INSERT INTO restaurant_modifier_integration
                        (modifier_id, provider, external_modifier_id, business_id)
                    VALUES (%s, 'clover', %s, %s)
                    ON DUPLICATE KEY UPDATE
                        modifier_id = VALUES(modifier_id),
                        business_id = VALUES(business_id)
                """, (modifier_id, mod['id'], business_id))

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
                                   int(float(combo_data.get('price', 0)) * 100),  # Convert to cents
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
                                   int(float(combo_data.get('price', 0)) * 100)  # Convert to cents
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
                                       int(float(option.get('price', 0)) * 100)  # Convert to cents
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
                                       int(float(option.get('price', 0)) * 100),  # Convert to cents
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
                                       int(float(option.get('price', 0)) * 100),  # Convert to cents
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