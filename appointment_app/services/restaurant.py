from typing import Dict, Any
from functools import lru_cache
from appointment_app.database import get_db_cursor

class RestaurantService:
    """
    Service class for restaurant-related database operations.
    Handles operations related to menu items, modifiers, and other restaurant-specific entities.
    """

    def __init__(self):
        # Lazy import to avoid circular imports

        self.get_db_cursor = get_db_cursor

    def create_modifier(self, business_id,  modifier_group_id: int, modifier_name: str, modifier_price: int) -> int:
        """
        Create a new modifier and return its ID

        Args:
            modifier_group_id: ID of the modifier group this modifier belongs to
            modifier_name: Name of the modifier
            modifier_price: Price delta for this modifier (in cents)

        Returns:
            int: The ID of the created modifier
        """
        with self.get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           INSERT INTO restaurant_modifier
                               (business_id, modifier_group_id, name, price_delta, is_active, display_order)
                           VALUES (%s, %s, %s, %s, TRUE, 0)
                           """, (business_id, modifier_group_id, modifier_name, modifier_price / 100))
            return cursor.lastrowid

    def update_modifier(self, modifier_id: int, modifier_name: str, modifier_price: int) -> bool:
        """
        Update an existing modifier.

        Args:
            modifier_id: ID of the modifier to update
            modifier_name: New name of the modifier
            modifier_price: New price delta for this modifier (in cents)

        Returns:
            bool: True if a row was updated, False if no such modifier exists
        """
        with self.get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE restaurant_modifier
                SET name = %s,
                    price_delta = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE modifier_id = %s
            """, (modifier_name, modifier_price / 100, modifier_id))
            return cursor.rowcount > 0

    def delete_modifier(self, modifier_id: int) -> bool:
        """
        Delete a modifier by its ID.

        Args:
            modifier_id: ID of the modifier to delete

        Returns:
            bool: True if a row was deleted, False if no such modifier exists
        """
        with self.get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           DELETE
                           FROM restaurant_modifier
                           WHERE modifier_id = %s
                           """, (modifier_id,))
            return cursor.rowcount > 0

    def create_modifier_group(self, group_name, business_id):
        """Create a new modifier group and return its ID"""
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           INSERT INTO restaurant_modifier_group
                               (business_id, name, is_required)
                           VALUES (%s, %s, FALSE)
                           """, (business_id, group_name))
            return cursor.lastrowid

    def update_modifier_group(self, group_id: int, group_name: str, is_required: bool) -> bool:
        """
        Update an existing modifier group.

        Args:
            group_id: ID of the modifier group to update
            group_name: New name of the group
            is_required: Whether the group is required (True/False)

        Returns:
            bool: True if a row was updated, False if not found
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           UPDATE restaurant_modifier_group
                           SET name        = %s,
                               is_required = %s
                           WHERE modifier_group_id = %s
                           """, (group_name, is_required, group_id))
            return cursor.rowcount > 0

    def delete_modifier_group(self, group_id: int) -> bool:
        """
        Delete a modifier group by its ID.

        Args:
            group_id: ID of the modifier group to delete

        Returns:
            bool: True if a row was deleted, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           DELETE
                           FROM restaurant_modifier_group
                           WHERE modifier_group_id = %s
                           """, (group_id,))
            return cursor.rowcount > 0

    def create_category(self, category_name: str, business_id: int) -> int:
        """Create a new category and return its ID"""
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           INSERT INTO restaurant_item_category
                               (business_id, name)
                           VALUES (%s, %s)
                           """, (business_id, category_name))
            return cursor.lastrowid

    def update_category(self, category_id: int, category_name: str) -> bool:
        """
        Update an existing category.

        Args:
            category_id: ID of the category to update
            category_name: New name of the category

        Returns:
            bool: True if a row was updated, False if not found
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           UPDATE restaurant_item_category
                           SET name       = %s
                           WHERE item_category_id = %s
                           """, (category_name, category_id))
            return cursor.rowcount > 0

    def delete_category(self, category_id: int) -> bool:
        """
        Delete a category by its ID.

        Args:
            category_id: ID of the category to delete

        Returns:
            bool: True if a row was deleted, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                DELETE FROM restaurant_item_category
                WHERE item_category_id = %s
            """, (category_id,))
            return cursor.rowcount > 0

    def create_item(self, business_id: int, item_data: dict) -> int:
        """
        Create a new item and return its ID.

        Args:
            business_id: Business this item belongs to
            item_data: Dictionary with item fields (name, description, price in cents, hidden flag)

        Returns:
            int: The ID of the created item
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           INSERT INTO restaurant_item
                               (business_id, name, description, base_price, is_active)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (
                               business_id,
                               item_data.get('name', ''),
                               item_data.get('description', ''),
                               float(item_data.get('price', 0)) / 100,  # Convert cents → dollars
                               item_data.get('hidden', False) is False  # hidden=False → active
                           ))
            return cursor.lastrowid

    def update_item(self, item_id: int, item_data: dict) -> bool:
        """
        Update an existing item.

        Args:
            item_id: ID of the item to update
            item_data: Dictionary with fields to update: name, description, price (in cents), hidden flag

        Returns:
            bool: True if the item was updated, False if no such item exists
        """
        with get_db_cursor(commit=True) as cursor:
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
                               float(item_data.get('price', 0)) / 100,
                               (item_data.get('hidden', False) is False),
                               item_id
                           ))
            return cursor.rowcount > 0

    def delete_item(self, item_id: int) -> bool:
        """
        Permanently delete an item by its ID.

        Args:
            item_id: ID of the item to delete

        Returns:
            bool: True if the row was deleted, False if no such item exists
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           DELETE
                           FROM restaurant_item
                           WHERE item_id = %s
                           """, (item_id,))
            return cursor.rowcount > 0

    def create_option_group(self, business_id: int, group_data: dict) -> int:
        """
        Create a new option group and return its ID.

        Args:
            business_id: The business this option group belongs to
            group_data: Dict with keys group_name, description, min_required, max_allowed, required

        Returns:
            int: The ID of the created option group
        """
        with get_db_cursor(commit=True) as cursor:
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
            return cursor.lastrowid

    def update_option_group(self, group_id: int, group_data: dict) -> bool:
        """
        Update an existing option group.

        Args:
            group_id: ID of the option group to update
            group_data: Dict with keys group_name, description, min_required, max_allowed, required

        Returns:
            bool: True if a row was updated, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE restaurant_option_group
                SET name = %s,
                    description = %s,
                    min_select = %s,
                    max_select = %s,
                    is_required = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE option_group_id = %s
            """, (
                group_data.get('group_name', ''),
                group_data.get('description', ''),
                group_data.get('min_required', 1),
                group_data.get('max_allowed', 1),
                group_data.get('required', False),
                group_id
            ))
            return cursor.rowcount > 0

    def delete_option_group(self, group_id: int) -> bool:
        """
        Delete an option group by its ID.

        Args:
            group_id: ID of the option group to delete

        Returns:
            bool: True if a row was deleted, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                DELETE FROM restaurant_option_group
                WHERE option_group_id = %s
            """, (group_id,))
            return cursor.rowcount > 0

    def create_combo_group(self, item_id: int, group: dict) -> int:
        """
        Create a new combo group for an item.

        Args:
            item_id: The item this combo group belongs to
            group: Dict with keys group_name, min_required, max_allowed

        Returns:
            int: The ID of the created combo group
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           INSERT INTO restaurant_combo_group
                               (item_id, name, min_select, max_select)
                           VALUES (%s, %s, %s, %s)
                           """, (
                               item_id,
                               group.get('group_name', ''),
                               group.get('min_required', 1),
                               group.get('max_allowed', 1)
                           ))
            return cursor.lastrowid

    def update_combo_group(self, combo_group_id: int, group: dict) -> bool:
        """
        Update an existing combo group.

        Args:
            combo_group_id: ID of the combo group to update
            group: Dict with keys group_name, min_required, max_allowed

        Returns:
            bool: True if a row was updated, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           UPDATE restaurant_combo_group
                           SET name       = %s,
                               min_select = %s,
                               max_select = %s,
                               updated_at = CURRENT_TIMESTAMP
                           WHERE combo_group_id = %s
                           """, (
                               group.get('group_name', ''),
                               group.get('min_required', 1),
                               group.get('max_allowed', 1),
                               combo_group_id
                           ))
            return cursor.rowcount > 0

    def delete_combo_group(self, combo_group_id: int) -> bool:
        """
        Delete a combo group by its ID.

        Args:
            combo_group_id: ID of the combo group to delete

        Returns:
            bool: True if a row was deleted, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           DELETE
                           FROM restaurant_combo_group
                           WHERE combo_group_id = %s
                           """, (combo_group_id,))
            return cursor.rowcount > 0

    def create_item_modifier_group(self, item_id: int, modifier_group_id: int) -> bool:
        """
        Link an item to a modifier group.

        Args:
            item_id: The item ID
            modifier_group_id: The modifier group ID

        Returns:
            bool: True if inserted successfully, False if duplicate
        """
        with get_db_cursor(commit=True) as cursor:
            try:
                cursor.execute("""
                               INSERT INTO restaurant_item_modifier_group (item_id, modifier_group_id)
                               VALUES (%s, %s)
                               """, (item_id, modifier_group_id))
                return True
            except Exception:
                # Likely duplicate key if already linked
                return False

    def delete_item_modifier_group(self, item_id: int, modifier_group_id: int) -> bool:
        """
        Unlink an item from a modifier group.

        Args:
            item_id: The item ID
            modifier_group_id: The modifier group ID

        Returns:
            bool: True if a row was deleted, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           DELETE
                           FROM restaurant_item_modifier_group
                           WHERE item_id = %s
                             AND modifier_group_id = %s
                           """, (item_id, modifier_group_id))
            return cursor.rowcount > 0

    def create_item_category_map(self, item_id: int, item_category_id: int) -> bool:
        """
        Link an item to a category.

        Args:
            item_id: The item ID
            item_category_id: The category ID

        Returns:
            bool: True if inserted successfully, False if duplicate
        """
        with get_db_cursor(commit=True) as cursor:
            try:
                cursor.execute("""
                               INSERT INTO restaurant_item_category_map (item_id, item_category_id)
                               VALUES (%s, %s)
                               """, (item_id, item_category_id))
                return True
            except Exception:
                # Duplicate key (already linked)
                return False

    def delete_item_category_map(self, item_id: int, item_category_id: int) -> bool:
        """
        Unlink an item from a category.

        Args:
            item_id: The item ID
            item_category_id: The category ID

        Returns:
            bool: True if a row was deleted, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           DELETE
                           FROM restaurant_item_category_map
                           WHERE item_id = %s
                             AND item_category_id = %s
                           """, (item_id, item_category_id))
            return cursor.rowcount > 0

    def delete_item_category_maps(self, item_id: int) -> bool:
        """
        Unlink an item from a category.

        Args:
            item_id: The item ID
            item_category_id: The category ID

        Returns:
            bool: True if a row was deleted, False otherwise
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           DELETE
                           FROM restaurant_item_category_map
                           WHERE item_id = %s
                           """, (item_id, ))
            return cursor.rowcount > 0

    def create_order(self, order_data: dict) -> int:
        """
        Create a new order and return its ID.

        Args:
            order_data: Dict with keys customer_id, business_id

        Returns:
            int: The ID of the created order
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           INSERT INTO restaurant_order
                               (customer_id, business_id, order_status, order_time)
                           VALUES (%s, %s, 'confirmed', NOW())
                           """, (
                               order_data['customer_id'],
                               order_data['business_id']
                           ))
            return cursor.lastrowid

    def update_order(self, order_id: int, **kwargs) -> bool:
        """
        Update an order. All params are optional.

        Args:
            order_id: The order ID to update
            kwargs: Any of [customer_id, business_id, order_status, total_price, order_time]

        Returns:
            bool: True if a row was updated, False otherwise
        """
        if not kwargs:
            return False  # nothing to update

        fields = []
        values = []

        allowed_fields = ["customer_id", "business_id", "order_status", "total_price", "order_time"]

        for key, value in kwargs.items():
            if key in allowed_fields:
                fields.append(f"{key} = %s")
                values.append(value)

        if not fields:
            return False  # no valid fields

        query = f"""
            UPDATE restaurant_order
            SET {", ".join(fields)}
            WHERE order_id = %s
        """
        values.append(order_id)

        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(values))
            return cursor.rowcount > 0


    def create_order_item(self, order_id: int, item: dict) -> int:
        """
        Create a new order item and return its ID.

        Args:
            order_id: The order this item belongs to
            item: Dict with keys item_id, quantity, price (and optionally base_price)

        Returns:
            int: The ID of the created order item
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           INSERT INTO restaurant_order_item
                               (order_id, item_id, quantity, base_price, total_price)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (
                               order_id,
                               item['item_id'],
                               item['quantity'],
                               item.get('base_price', item['price']),
                               item['price'] * item['quantity']
                           ))
            return cursor.lastrowid

    def create_order_item_option(self, order_item_id: int, option: dict) -> int:
        """
        Create a new order item option and return its ID.

        Args:
            order_item_id: The parent order item ID
            option: Dict with keys option_id, name, price_delta

        Returns:
            int: The ID of the created order item option
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           INSERT INTO restaurant_order_item_option
                               (order_item_id, option_id, name, price_delta)
                           VALUES (%s, %s, %s, %s)
                           """, (
                               order_item_id,
                               option.get('option_id'),
                               option.get('name', ''),
                               option.get('price_delta', 0.0)
                           ))
            return cursor.lastrowid

    def create_order_item_modifier(self, order_item_id: int, modifier: dict) -> int:
        """
        Create a new order item modifier and return its ID.

        Args:
            order_item_id: The parent order item ID
            modifier: Dict with keys modifier_id, name, price_delta

        Returns:
            int: The ID of the created order item modifier
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                           INSERT INTO restaurant_order_item_modifier
                               (order_item_id, modifier_id, name, price_delta)
                           VALUES (%s, %s, %s, %s)
                           """, (
                               order_item_id,
                               modifier.get('modifier_id'),
                               modifier.get('name', ''),
                               modifier.get('price_delta', 0.0)
                           ))
            return cursor.lastrowid

    def create_polydial_line_item(self, order_id, item):
        # Add order item
        order_item_id = restaurant_service.create_order_item(order_id, item)
        # Add options if any
        if 'options' in item and isinstance(item['options'], list):
            for option in item['options']:
                restaurant_service.create_order_item_option(order_item_id, option)

        # Add modifiers if any
        if 'modifiers' in item and isinstance(item['modifiers'], list):
            for modifier in item['modifiers']:
                restaurant_service.create_order_item_modifier(order_item_id, modifier)

        return order_item_id

    def get_business_integration(self, business_id: int) -> dict | None:
        """
        Get integration details for a business.

        Args:
            business_id: The business ID

        Returns:
            dict: Integration record, or None if not found
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                           SELECT integration_id,
                                  business_id,
                                  provider,
                                  merchant_id,
                                  access_token,
                                  refresh_token,
                                  status,
                                  created_at,
                                  updated_at,
                                  provider_data
                           FROM business_integration
                           WHERE business_id = %s
                           """, (business_id,))

            result =cursor.fetchone()
            if result:
                return result
            else:
                return {"provider":"polydial"}



# Create a singleton instance for easy importing
restaurant_service = RestaurantService()
