import pandas as pd
from appointment_app.database import get_db_cursor

class Restaurant:
    def __init__(self, business_id=69, xlsx_file = 'to_clover.xlsx'):
        self.business_id = business_id
        self.xlsx_file = xlsx_file

    def get_item(self):
        """
        Fetch restaurant items from the database for a specific business.

        Returns:
            list: List of dictionaries containing item information in Clover format with Modifier Groups
        """
        query = """
            SELECT
                '' as "Clover ID",
                ri.name as "Name",
                '' as "Alternate Name",
                ri.base_price as "Price",
                'Fixed' as "Price Type",
                '' as "Price Unit",
                'DEFAULT' as "Tax Rates",
                '' as "Cost",
                '' as "Product Code",
                '' as "SKU",
                COALESCE(
                    (SELECT GROUP_CONCAT(DISTINCT mg.name SEPARATOR '|')
                     FROM restaurant_item_modifier_group rim
                     JOIN restaurant_modifier_group mg ON rim.modifier_group_id = mg.modifier_group_id
                     WHERE rim.item_id = ri.item_id),
                    ''
                ) as "Modifier Groups",
                0 as "Quantity",
                '' as "Printer Labels",
                'No' as "Hidden",
                'No' as "Non-revenue item"
            FROM
                restaurant_item ri
            WHERE
                ri.business_id = %s
            GROUP BY
                ri.item_id, ri.name, ri.base_price
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
                resp = cursor.fetchall()
                result = []
                count = 0
                for item in resp:
                    if count>0:
                        if modifier_group_name == item['Modifier Group Name']:
                            item['Modifier Group Name'] = ""
                            item['Pop-up Automatically'] = ""
                            result.append(item)
                        else:
                            count = 0
                    if count == 0:
                        modifier_group_name = item['Modifier Group Name']
                        result.append(item)
                    count += 1



                return result
        except Exception as e:
            print(f"Error fetching modifier groups: {e}")
            return []

    import pandas as pd

    def get_categories(self):
        """
        Fetch categories from the database for the current business and return as a DataFrame
        with category groups as columns and item names listed under each.

        Returns:
            pandas.DataFrame: category groups as columns, rows filled with item names.
        """
        query = """
                SELECT ri.name  AS item_name,
                       rig.name AS item_category_group
                FROM restaurant_item ri
                         JOIN restaurant_item_category_map rm ON ri.item_id = rm.item_id
                         JOIN restaurant_item_category rig ON rm.item_category_id = rig.item_category_id
                WHERE ri.business_id = %s
                ORDER BY rig.name, ri.name;
                """

        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, (self.business_id,))
                resp = cursor.fetchall()

                if not resp:
                    return pd.DataFrame()

                # Convert to DataFrame
                df = pd.DataFrame(resp)

                # Group items by category
                grouped = df.groupby("item_category_group")["item_name"].apply(list).to_dict()

                # Find max number of items in any category
                max_len = max(len(items) for items in grouped.values())

                # Pad each list to the same length with empty strings
                padded = {cat: items + [""] * (max_len - len(items)) for cat, items in grouped.items()}

                # Create DataFrame with categories as columns
                df_out = pd.DataFrame(padded)
                column_0=["Items in Category"]
                for i in range(1, max_len):
                    column_0.append("")

                df_out.insert(0, "Category Name", column_0)
                return df_out

        except Exception as e:
            print(f"Error fetching categories: {e}")
            return pd.DataFrame()

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
    def export_items(self):
        # Build DataFrames from methods
        df_items = pd.DataFrame(self.get_item())
        df_modifiers = pd.DataFrame(self.get_modifier_groups())
        df_categories = pd.DataFrame(self.get_categories())
        df_tax_rates = pd.DataFrame(self.get_tax_rates())
        df_instructions = pd.DataFrame(self.get_instructions())

        # Write Excel
        with pd.ExcelWriter(self.xlsx_file , engine="openpyxl") as writer:
            df_items.to_excel(writer, sheet_name="Items", index=False)
            df_modifiers.to_excel(writer, sheet_name="Modifier Groups", index=False)
            df_categories.to_excel(writer, sheet_name="Categories", index=False)
            df_tax_rates.to_excel(writer, sheet_name="Tax Rates", index=False)
            df_instructions.to_excel(writer, sheet_name="Instructions", index=False)

        print("✅ to_clover.xlsx created successfully")

if __name__ == "__main__":
    restaurant = Restaurant(business_id=73,xlsx_file = 'inventory-masrawy1.xlsx')
    items = restaurant.export_items()