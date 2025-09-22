import pandas as pd
from appointment_app.database import get_db_cursor
class Restaurant:
    def __init__(self, business_id=69):
        self.business_id = business_id

    def get_item(self):
        """
        Fetch restaurant items from the database for a specific business.

        Args:
            business_id (int): The ID of the business to filter items by

        Returns:
            list: List of dictionaries containing item information in Clover format
        """
        query = """
                SELECT ri.item_id    as "Clover ID", \
                       ri.name       as "Name", \
                       ''            as "Alternate Name", \
                       ri.base_price as "Price", \
                       'Fixed'       as "Price Type", \
                       ''            as "Price Unit", \
                       'DEFAULT'     as "Tax Rates", \
                       ''            as "Cost", \
                       ''            as "Product Code", \
                       ''            as "SKU", \
                       ''            as "Modifier Groups", \
                       0             as "Quantity", \
                       ''            as "Printer Labels", \
                       'No'          as "Hidden", \
                       'No'          as "Non-revenue item"
                FROM restaurant_item ri
                WHERE ri.business_id = %s \
                """

        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, (self.business_id,))
                items = cursor.fetchall()

                # Convert Decimal to float for JSON serialization
                for item in items:
                    if 'Price' in item and item['Price'] is not None:
                        item['Price'] = float(item['Price'])

                return items

        except Exception as e:
            print(f"Error fetching items: {e}")
            return []

    def get_modifier_groups(self):
        """
        Fetch modifier groups from the database for the current business.

        Returns:
            list: List of dictionaries containing modifier group information in Clover format
        """
        query = """
                SELECT rmg.name       as "Modifier Group Name", \
                       CASE \
                           WHEN rmg.is_required = 1 THEN 'Yes' \
                           ELSE 'No' \
                           END        as "Pop-up Automatically", \
                       rm.name        as "Modifier", \
                       rm.price_delta as "Price"
                FROM restaurant_modifier_group rmg
                         JOIN restaurant_modifier rm ON rmg.modifier_group_id = rm.modifier_group_id
                WHERE rmg.business_id = %s
                ORDER BY rmg.name, rm.display_order \
                """

        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, (self.business_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching modifier groups: {e}")
            return []

    def get_categories(self):
        """
        Fetch categories from the database for the current business.

        Returns:
            list: List of dictionaries containing category information in Clover format
        """
        query = """
                WITH item_categories AS (SELECT ric.name as category_name, \
                                                ri.name  as item_name \
                                         FROM restaurant_item ri \
                                                  JOIN restaurant_item_category_map ricm ON ri.item_id = ricm.item_id \
                                                  JOIN restaurant_item_category ric \
                                                       ON ricm.item_category_id = ric.item_category_id \
                                         WHERE ri.business_id = %s \
                                         ORDER BY ric.name, ri.name)
                SELECT category_name                                   as "Category Name", \
                       GROUP_CONCAT(DISTINCT item_name SEPARATOR ', ') as "Items in Category"
                FROM item_categories
                GROUP BY category_name \
                """

        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, (self.business_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return []

    def get_tax_rates(self):
        return [
            {"Name": "Sales Tax", "Tax Rate": 0.09, "Default": "Yes"},
            {"Name": "Tax 2", "Tax Rate": 0.06, "Default": "No"},
            {"Name": "Tax 3", "Tax Rate": 0.02, "Default": "No"}
        ]

    def get_instructions(self):
        return [
            {"Instructions": (
                "Use this template for fast, efficient setup of your inventory or menu. "
                "Enter your Items and their respective Categories, Modifier Groups (and modifiers), "
                "and applicable Taxes & Flat Fees. Included in each tab are examples—please clear those "
                "before you enter your information."
            )}
        ]


# ----------- MAIN SCRIPT -------------

restaurant = Restaurant(business_id=73)
estaurant = Restaurant()
items = restaurant.get_item()

# Build DataFrames from methods
df_items = pd.DataFrame(restaurant.get_item())
df_modifiers = pd.DataFrame(restaurant.get_modifier_groups())
df_categories = pd.DataFrame(restaurant.get_categories())
df_tax_rates = pd.DataFrame(restaurant.get_tax_rates())
df_instructions = pd.DataFrame(restaurant.get_instructions())

# Write Excel
with pd.ExcelWriter("inventory-masrawy.xlsx", engine="openpyxl") as writer:
    df_items.to_excel(writer, sheet_name="Items", index=False)
    df_modifiers.to_excel(writer, sheet_name="Modifier Groups", index=False)
    df_categories.to_excel(writer, sheet_name="Categories", index=False)
    df_tax_rates.to_excel(writer, sheet_name="Tax Rates", index=False)
    df_instructions.to_excel(writer, sheet_name="Instructions", index=False)

print("✅ inventory-template.xlsx created successfully")
