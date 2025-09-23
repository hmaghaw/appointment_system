import requests
from typing import List, Dict, Any, Optional
from appointment_app.database import get_db_cursor


class CloverIntegration:
    def __init__(self, business_id: int):
        """
        Initialize Clover integration with business_id to fetch credentials

        Args:
            business_id: The ID of the business to fetch Clover credentials for
        """
        self.business_id = business_id
        self.merchant_id = None
        self.access_token = None
        self.base_url = None
        self.headers = None

        # Fetch and set credentials
        self._fetch_credentials()

    def _fetch_credentials(self) -> None:
        """Fetch Clover credentials from the database for the given business_id"""
        query = """
                SELECT merchant_id, access_token
                FROM business_integration
                WHERE business_id = %s \
                  AND provider = 'clover' \
                  AND status = 'active' LIMIT 1 \
                """

        try:
            with get_db_cursor(dictionary=True) as cursor:
                cursor.execute(query, (self.business_id,))
                result = cursor.fetchone()

                if not result:
                    raise ValueError("No active Clover integration found for this business")

                self.merchant_id = result['merchant_id']
                self.access_token = result['access_token']
                self.base_url = f"https://sandbox.dev.clover.com/v3/merchants/{self.merchant_id}"
                self.headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }

        except Exception as e:
            print(f"Error fetching Clover credentials: {e}")
            raise

    def create_order(self, title: str = "Customer Order") -> Dict[str, Any]:
        """
        Create a new order in Clover

        Args:
            title: Title/name for the order

        Returns:
            dict: The created order details
        """
        url = f"{self.base_url}/orders"
        payload = {"state": "open", "title": title}
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def add_line_item(self, order_id: str, item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Add a line item to an existing order

        Args:
            order_id: ID of the order to add the item to
            item_id: ID of the item to add
            quantity: Quantity of the item to add

        Returns:
            dict: The created line item details
        """
        url = f"{self.base_url}/orders/{order_id}/line_items"
        payload = {
            "item": {"id": item_id},
            "quantity": quantity
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def create_order_with_items(self, items: List[Dict[str, Any]], title: str = "Customer Order") -> Dict[str, Any]:
        """
        Create a new order with multiple items

        Args:
            items: List of dictionaries containing item details with 'id' and 'name' keys
            title: Title/name for the order

        Returns:
            dict: The created order details
        """
        order = self.create_order(title)
        order_id = order["id"]
        print(f"✅ Created Order ID: {order_id}")

        for item in items:
            li = self.add_line_item(order_id, item["id"], quantity=item.get("quantity", 1))
            #print(f"   ➕ Added {item['name']} x{item.get('quantity', 1)} (Line Item ID: {li['id']})")

        return order

    def list_items(self) -> List[Dict[str, Any]]:
        """List all items from Clover"""
        url = f"{self.base_url}/items"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get("elements", [])

    def list_item_modifiers(self, item_id: str) -> List[Dict[str, Any]]:
        """List modifier groups for a specific item"""
        url = f"{self.base_url}/items/{item_id}?expand=modifierGroups"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        groups = data.get("modifierGroups", {}).get("elements", [])
        result = []

        for group in groups:
            group_name = group["name"]
            group_id = group["id"]

            # Each group contains its own modifiers
            modifiers = group.get("modifiers", {}).get("elements", [])
            result.append({
                "group_id": group_id,
                "group_name": group_name,
                "modifiers": [{
                    "id": m["id"],
                    "name": m["name"],
                    "price": m.get("price", 0)
                } for m in modifiers]
            })

        return result


# Example usage
if __name__ == "__main__":
    try:
        # Initialize with business_id
        clover = CloverIntegration(business_id=69)  # Replace with actual business_id
        items = clover.list_items()
        # Example 1: Create an order with multiple items
        items_to_order = [
            {"id": 'QH1M3GWR3D0DP', "quantity": 1},
            {"id": 'C2DNHVFJ0ZRGM', "quantity": 2},
            {"id": '25K24H0TYXA3G', "quantity": 1}
        ]
        order = clover.create_order_with_items(items_to_order, "Family Package Order")
        print(f"Order created successfully: {order['id']}")

        # Example 2: List items and their modifiers
        items = clover.list_items()
        if items:
            first_item = items[0]
            print(f"\n🔎 Checking modifiers for item: {first_item['name']} (ID: {first_item['id']})")

            groups = clover.list_item_modifiers(first_item["id"])
            if groups:
                for group in groups:
                    print(f"Modifier Group: {group['group_name']} (ID: {group['group_id']})")
                    for mod in group["modifiers"]:
                        price = mod["price"] / 100.0  # Clover stores price in cents
                        #print(f"  - {mod['name']} (ID: {mod['id']} | +${price:.2f})")

    except Exception as e:
        print(f"❌ Error: {e}")