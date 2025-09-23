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

    def add_line_item(
            self,
            order_id: str,
            item_id: str,
            quantity: int = 1,
            modifiers: Optional[List[str]] = None,
            options: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add a line item (with optional modifiers/options) to an existing order.

        Args:
            order_id: ID of the order
            item_id: ID of the item to add
            quantity: quantity
            modifiers: list of modifier IDs
            options: list of option IDs

        Returns:
            dict: line item details
        """
        url = f"{self.base_url}/orders/{order_id}/line_items"

        payload = {
            "item": {"id": item_id},
            "quantity": quantity
        }

        if modifiers:
            payload["modifications"] = [
                {"modifier": {"id": mid}} for mid in modifiers
            ]

        if options:
            payload["options"] = [
                {"option": {"id": oid}} for oid in options
            ]

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def create_order_with_items(
            self,
            items: List[Dict[str, Any]],
            title: str = "Customer Order"
    ) -> Dict[str, Any]:
        """
        Create a new order with multiple items, modifiers, and options
        """
        order = self.create_order(title)
        order_id = order["id"]
        print(f"✅ Created Order ID: {order_id}")

        for item in items:
            li = self.add_line_item(
                order_id,
                item["id"],
                quantity=item.get("quantity", 1),
                modifiers=item.get("modifiers", []),
                options=item.get("options", [])
            )
            print(
                f"   ➕ Added {item['id']} with {len(item.get('modifiers', []))} modifiers and {len(item.get('options', []))} options")

        return order

    def list_items(self) -> List[Dict[str, Any]]:
        """List all items from Clover"""
        url = f"{self.base_url}/items?expand=modifierGroups,optionGroups"
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

    def list_modifiers(self) -> List[Dict[str, Any]]:
        """List all modifier groups and modifiers across the merchant"""
        url = f"{self.base_url}/modifier_groups?expand=modifiers"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        groups = response.json().get("elements", [])

        result = []
        for group in groups:
            group_id = group["id"]
            group_name = group.get("name", "")
            modifiers = group.get("modifiers", {}).get("elements", [])
            result.append({
                "group_id": group_id,
                "group_name": group_name,
                "modifiers": [
                    {
                        "id": m["id"],
                        "name": m.get("name", ""),
                        "price": m.get("price", 0)
                    }
                    for m in modifiers
                ]
            })
        return result

    def list_options(self) -> List[Dict[str, Any]]:
        """List all option groups and options across the merchant by scanning items"""
        items = self.list_items()  # already expands optionGroups
        groups_seen = {}

        for item in items:
            option_groups = item.get("optionGroups", {}).get("elements", [])
            for group in option_groups:
                group_id = group["id"]
                if group_id not in groups_seen:
                    # Fetch group details with options expanded
                    url = f"{self.base_url}/option_groups/{group_id}?expand=options"
                    resp = requests.get(url, headers=self.headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        groups_seen[group_id] = {
                            "group_id": group_id,
                            "group_name": data.get("name", ""),
                            "min_required": data.get("minRequired", 1),
                            "max_allowed": data.get("maxAllowed", 1),
                            "options": [
                                {
                                    "id": o["id"],
                                    "name": o.get("name", ""),
                                    "price": o.get("price", 0)
                                }
                                for o in data.get("options", {}).get("elements", [])
                            ]
                        }
        return list(groups_seen.values())

    def list_combos(self) -> List[Dict[str, Any]]:
        """List all combo items (items with optionGroups)"""
        items = self.list_items()  # expands optionGroups
        combos = []

        for item in items:
            option_groups = item.get("optionGroups", {}).get("elements", [])
            if option_groups:
                combo = {
                    "combo_id": item["id"],
                    "combo_name": item.get("name", ""),
                    "price": item.get("price", 0),
                    "groups": []
                }
                for group in option_groups:
                    group_id = group["id"]
                    # fetch group with options expanded
                    url = f"{self.base_url}/option_groups/{group_id}?expand=options"
                    resp = requests.get(url, headers=self.headers)
                    if resp.status_code == 200:
                        gdata = resp.json()
                        combo["groups"].append({
                            "group_id": group_id,
                            "group_name": gdata.get("name", ""),
                            "min_required": gdata.get("minRequired", 1),
                            "max_allowed": gdata.get("maxAllowed", 1),
                            "options": [
                                {
                                    "id": o["id"],
                                    "name": o.get("name", ""),
                                    "price": o.get("price", 0)
                                }
                                for o in gdata.get("options", {}).get("elements", [])
                            ]
                        })
                combos.append(combo)
        return combos
