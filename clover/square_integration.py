import requests
from typing import List, Dict, Any, Optional
from appointment_app.database import get_db_cursor


class SquareIntegration:
    def __init__(self, business_id: int, use_sandbox: bool = True):
        """
        Initialize Square integration with business_id to fetch credentials

        Args:
            business_id: The ID of the business to fetch Square credentials for
            use_sandbox: Whether to use Square sandbox environment
        """
        self.business_id = business_id
        self.access_token = None
        self.location_id = None
        self.base_url = (
            "https://connect.squareupsandbox.com/v2"
            if use_sandbox else
            "https://connect.squareup.com/v2"
        )
        self.headers = None

        # Fetch and set credentials
        self._fetch_credentials()

    def _fetch_credentials(self) -> None:
        """Fetch Square credentials from the database for the given business_id"""
        query = """
                SELECT access_token, location_id
                FROM business_integration
                WHERE business_id = %s
                  AND provider = 'square'
                  AND status = 'active'
                LIMIT 1
                """
        try:
            with get_db_cursor(dictionary=True) as cursor:
                cursor.execute(query, (self.business_id,))
                result = cursor.fetchone()

                if not result:
                    raise ValueError("No active Square integration found for this business")

                self.access_token = result["access_token"]
                self.location_id = result["location_id"]
                self.headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }

        except Exception as e:
            print(f"Error fetching Square credentials: {e}")
            raise

    def list_items(self) -> List[Dict[str, Any]]:
        """List all catalog items from Square"""
        url = f"{self.base_url}/catalog/list"
        params = {"types": "ITEM"}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("objects", [])

    def list_item_modifiers(self, item_id: str) -> List[Dict[str, Any]]:
        """List modifier groups for a specific item"""
        url = f"{self.base_url}/catalog/object/{item_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        obj = response.json().get("object", {})

        result = []
        if "item_data" in obj:
            for mg in obj["item_data"].get("modifier_list_info", []):
                group_id = mg["modifier_list_id"]

                # Fetch the modifier list details
                mod_url = f"{self.base_url}/catalog/object/{group_id}"
                mod_resp = requests.get(mod_url, headers=self.headers)
                mod_resp.raise_for_status()
                group_obj = mod_resp.json().get("object", {})

                group_name = group_obj.get("modifier_list_data", {}).get("name", "")
                modifiers = group_obj.get("modifier_list_data", {}).get("modifiers", [])

                result.append({
                    "group_id": group_id,
                    "group_name": group_name,
                    "modifiers": [
                        {
                            "id": m["id"],
                            "name": m["modifier_data"]["name"],
                            "price": m["modifier_data"].get("price_money", {}).get("amount", 0)
                        }
                        for m in modifiers
                    ]
                })
        return result

    def create_order_with_items(self, items: List[Dict[str, Any]], title: str = "Customer Order") -> Dict[str, Any]:
        """
        Create a new order with multiple items in Square

        Args:
            items: List of dicts containing 'id' (Square catalog object_id) and 'quantity'
            title: Not directly supported, but we can include in 'note'

        Returns:
            dict: The created order details
        """
        url = f"{self.base_url}/orders"
        payload = {
            "order": {
                "location_id": self.location_id,
                "line_items": [
                    {
                        "catalog_object_id": item["id"],
                        "quantity": str(item.get("quantity", 1))
                    }
                    for item in items
                ],
                "note": title
            }
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    try:
        square = SquareIntegration(business_id=69)  # Replace with actual business_id
        items = square.list_items()
        print(f"Found {len(items)} items")

        if items:
            print(f"First Item: {items[0]['item_data']['name']} (ID: {items[0]['id']})")

        # Example: create an order
        items_to_order = [
            {"id": items[0]["id"], "quantity": 1}
        ]
        order = square.create_order_with_items(items_to_order, "Family Package Order")
        print(f"✅ Order created successfully: {order}")

    except Exception as e:
        print(f"❌ Error: {e}")
