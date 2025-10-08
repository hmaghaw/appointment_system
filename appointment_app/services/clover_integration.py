import requests
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from appointment_app.database import get_db_cursor
import os
from ..services.entity_integration import EntityIntegrationManager
CLOVER_URL = os.getenv('CLOVER_URL')
integration = EntityIntegrationManager(provider='clover')

class CloverIntegration:
    def __init__(self, business_id: int, access_token: str = None, merchant_id: str = None):
        """
        Initialize Clover integration.
        
        Can be initialized with either:
        1. Just business_id: Will fetch credentials from database
        2. business_id + access_token + merchant_id: Use provided credentials
        
        Args:
            business_id: The ID of the business
            access_token: Optional access token (if not provided, will fetch from DB)
            merchant_id: Optional merchant ID (if not provided, will fetch from DB)
        """
        self.business_id = business_id
        self.merchant_id = merchant_id
        self.access_token = access_token
        self.clover_base_url = None
        self.headers = None
        self.provider_data = {}

        if not all([self.access_token, self.merchant_id]):
            self._fetch_credentials()
            
        if not all([self.access_token, self.merchant_id]):
            raise ValueError("Missing required Clover credentials. Please connect your Clover account first.")
            
        self._setup_client()

    def _fetch_credentials(self) -> None:
        """Fetch Clover credentials from the database"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT merchant_id, access_token, refresh_token, provider_data
                FROM business_integration
                WHERE business_id = %s 
                  AND provider = 'clover' 
                  AND status = 'active'
                LIMIT 1
            """, (self.business_id,))
            
            result = cursor.fetchone()
            if result:
                self.merchant_id = result['merchant_id']
                self.access_token = result['access_token']
                self.provider_data = json.loads(result['provider_data']) if result['provider_data'] else {}
                
                # Check if token is expired and refresh if needed
                if self._is_token_expired():
                    self._refresh_access_token(result['refresh_token'])

    def _is_token_expired(self) -> bool:
        """Check if the access token is expired"""
        if not self.provider_data.get('expires_at'):
            return False
            
        expires_at = datetime.fromisoformat(self.provider_data['expires_at'])
        return datetime.utcnow() >= expires_at - timedelta(minutes=5)  # 5-minute buffer

    def get_clover_app(self):
        with get_db_cursor() as cursor:
            cursor.execute("""
                           SELECT app_id, app_secret
                           FROM restaurant_clover_app
                           WHERE business_id = %s
                             LIMIT 1
                           """, (self.business_id,))

            result = cursor.fetchone()
            if result:
                clover_client_id = result['app_id']
                clover_client_secret = result['app_secret']
            else:
                clover_client_id = os.getenv('CLOVER_APP_ID')
                clover_client_secret = os.getenv('CLOVER_APP_SECRET')

        return clover_client_id, clover_client_secret

    def _refresh_access_token(self, refresh_token: str) -> None:
        """Refresh the access token using the refresh token"""
        if not refresh_token:
            raise ValueError("No refresh token available")

        clover_client_id, clover_client_secret = self.get_clover_app()
        
        if not all([clover_client_id, clover_client_secret]):
            raise ValueError("Missing Clover app credentials in configuration")
            
        response = requests.post(
            f'{CLOVER_URL}/oauth/token',
            data={
                'client_id': clover_client_id,
                'client_secret': clover_client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to refresh token: {response.text}")
            
        token_data = response.json()
        self.access_token = token_data['access_token']
        
        # Update stored credentials
        self._update_credentials(
            access_token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token', refresh_token),
            expires_in=token_data.get('expires_in')
        )

    def _update_credentials(self, access_token: str, refresh_token: str = None, 
                          expires_in: int = None) -> None:
        """Update stored credentials in the database"""
        if expires_in:
            expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
            self.provider_data['expires_at'] = expires_at
            
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE business_integration
                SET access_token = %s,
                    refresh_token = COALESCE(%s, refresh_token),
                    provider_data = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE business_id = %s AND provider = 'clover'
            """, (
                access_token,
                refresh_token,
                json.dumps(self.provider_data),
                self.business_id
            ))

    def _setup_client(self) -> None:
        """Set up the HTTP client with the current credentials"""
        #self.clover_base_url = f"https://sandbox.dev.clover.com/v3"
        self.clover_base_url = f"{CLOVER_URL}/v3/merchants/{self.merchant_id}"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an API request to Clover"""
        url = f"{self.clover_base_url}/{endpoint.lstrip('/')}"
        
        # Add default headers if not provided
        if 'headers' not in kwargs:
            kwargs['headers'] = self.headers
            
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Handle empty responses
            if not response.text.strip():
                return {}
                
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401 and 'access token' in str(e).lower():
                # Token might be expired, try to refresh it once
                self._refresh_access_token()
                # Retry the request with the new token
                return self._make_request(method, endpoint, **kwargs)
            raise

    def create_order(self, title: str = "Customer Order") -> Dict[str, Any]:
        """
        Create a new order in Clover

        Args:
            title: Title/name for the order

        Returns:
            dict: The created order details
        """
        url = f"/orders"
        payload = {"state": "open", "title": title}
        response = self._make_request('POST', url, json=payload)
        return response

    def add_line_item(
            self,
            externals_order_id: str,
            item) -> Dict[str, Any]:
        """
        Add a line item (with optional modifiers/options) to an existing order.

        Args:
            externals_order_id: ID of the order
            item_id: ID of the item to add
            quantity: quantity
            modifiers: list of modifier IDs
            options: list of option IDs

        Returns:
            dict: line item details
        """
        url = f"/orders/{externals_order_id}/line_items"

        payload = self.prapare_line_item(item)

        response = self._make_request('POST', url, json=payload)
        return response


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
                item['external_item_id'],
                quantity=item.get("quantity", 1),
                modifiers=item.get("modifiers", []),
                options=item.get("options", [])
            )
            print(
                f"   ➕ Added {item['external_item_id']} with {len(item.get('modifiers', []))} modifiers and {len(item.get('options', []))} options")

        return order

    def list_items(self) -> List[Dict[str, Any]]:
        """List all items from Clover"""
        url = f"/items?expand=categories,modifierGroups,optionGroups"
        response = self._make_request('GET', url)
        return response.get("elements", [])

    def list_item_modifiers(self, item_id: str) -> List[Dict[str, Any]]:
        """List modifier groups for a specific item"""
        url = f"{self.clover_base_url}/modifier_groups"
        response = self._make_request('GET', url)
        data = response

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
        url = f"/modifier_groups?expand=modifiers"
        response = self._make_request('GET', url)
        groups = response.get("elements", [])

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

    def list_categories(self, expand_items: bool = False) -> List[Dict[str, Any]]:
        """List all categories (optionally with items) across the merchant"""
        url = "/categories"
        if expand_items:
            url += "?expand=items"

        response = self._make_request("GET", url)
        groups = response.get("elements", [])

        result = []
        for group in groups:
            group_id = group["id"]
            group_name = group.get("name", "")
            items = group.get("items", {}).get("elements", []) if expand_items else []
            result.append({
                "category_id": group_id,
                "category_name": group_name,
                "items": [
                    {
                        "id": i["id"],
                        "name": i.get("name", "")
                    }
                    for i in items
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
                    url = f"{self.clover_base_url}/option_groups/{group_id}?expand=options"
                    resp = self._make_request('GET', url)
                    if resp:
                        data = resp
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
                    url = f"{self.clover_base_url}/option_groups/{group_id}?expand=options"
                    resp = self._make_request('GET', url)
                    if resp:
                        gdata = resp
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

    def prapare_line_item(self, item):
        external_item_id = integration.get_external_id("item", item['item_id'])
        payload = {
            "item": {"id": external_item_id},
            "unitQty": item['quantity'],
            "note": "Extra Spicy",
            "modifications":[],
            "options":[]
        }
        if len(item['modifiers'])>0:
            for modifier in item['modifiers']:
                external_item_id = integration.get_external_id("modifier", modifier['modifier_id'])
                payload["modifications"].append({"modifier": {"id": external_item_id}})

        return payload




