import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
import logging
import time
from appointment_app.services.utils import generate_jwt_token

logger = logging.getLogger(__name__)

# Load environment variables from the root .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get API base URL from environment variables with fallback
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')

class RestaurantTools:
    def __init__(self):
        auth_token = generate_jwt_token()
        self.headers = {"Content-Type": "application/json"}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

        self.base_url = API_BASE_URL
        pass

    def update_customer_language(self, language: str, **kwargs) -> str:
        """
        Update customer's preferred language.

        Args:
            customer_id: The ID of the customer to update
            language: New language code (e.g., 'en', 'fr', 'ar', 'zh')

        Returns:
            str: Success or error message
        """
        customer_id = 33

        url = f"{self.base_url}/api/customers"
        payload = {
            "customer_id": customer_id,
            "language": language
        }
        response = requests.put(url, json=payload, headers=self.headers)
        res = response.json()

        if 'success' in res:
            return f'language_pref = "{language}'
        return "An error occurred while updating customer language"

    def update_customer(self, first_name: str, last_name: str) -> str:
        """
        Update customer information.

        Args:
            customer_id: The ID of the customer to update
            first_name: New first name for the customer
            last_name: New last name for the customer

        Returns:
            str: Success or error message
        """
        customer_id = 33
        url = f"{self.base_url}/api/customers"
        payload = {
            "customer_id": customer_id,
            "first_name": first_name,
            "last_name": last_name
        }
        response = requests.put(url, json=payload, headers=self.headers)
        res = response.json()

        if 'success' in res:
            return "Customer information updated successfully"
        return "An error occurred while updating customer information"

    def create_order(self, order: dict, **kwargs):
        """
        Process a restaurant order.

        Args:
            order (dict): Dictionary containing the order details,
                               matching the schema with items, modifiers, and total.

        Returns:
            dict: A confirmation response with calculated totals.
        """
        order["customer_id"] = 33
        order["business_id"] = 97
        url = f"{self.base_url}/api/restaurants/create_order"
        payload = {
            "order": order
        }
        response = requests.post(url, json=payload, headers=self.headers)
        res = response.json()
        if res['status'] == "success":
            message_body = self.generate_detailed_sms_invoice(res)
            self.send_confirmation_sms(message_body)
            return "Order created successfully"
        else:
            return "Order creation Failed"

    def validate_order(self, order: dict, **kwargs):
        items = order['items']
        language_code = "en"
        item_lines, total, tax, grand_total = self.prepare_invoice_lines(items, language_code, show_prices=False)
        result = {"order_lines": item_lines, "grand_Total": grand_total}
        res = json.dumps(result)
        response = f"list 'order_lines' and show 'grand_Total' value and ask the customer to confirm the order: {res}"
        return response

    def prepare_invoice_lines(self, items, lang: str = "en", show_prices: bool = True):
        lines = []
        invoice_total = 0
        tax_percentage = 0.09
        for item in items:
            name = item.get("name", "Unknown Item")
            qty = float(item.get("quantity", 1))
            unit_price = float(item.get("base_price", item.get("price", 0)))
            note = item.get("note", "")
            modifiers = item.get("modifiers", [])

            base_total = unit_price * qty
            item_total = base_total

            # Item line
            if show_prices:
                lines.append(f"{name} {qty:g}x${unit_price:.2f} = ${base_total:.2f}")
            else:
                lines.append(f"{qty:g} {name}")

            # Modifiers
            for mod in modifiers:
                if mod.get("is_active", True):
                    mod_qty = float(mod.get("quantity", 1))
                    mod_price = float(mod.get("price_delta", 0))
                    mod_name = mod.get("name", "")
                    mod_line_total = mod_qty * mod_price
                    item_total += mod_line_total

                    if show_prices:
                        lines.append(f"{mod_name}  {mod_qty:g}x${mod_price:.2f} = ${mod_line_total:.2f}")
                    else:
                        lines.append(f"{mod_qty:g} {mod_name}")
            # Note
            if note:
                lines.append(f"{note}")
            invoice_total += item_total
        tax = round(invoice_total * tax_percentage, 2)
        grand_total = round(invoice_total + tax, 2)
        return lines, invoice_total, tax, grand_total

    def generate_detailed_sms_invoice(self, order: dict, lang: str = "en", show_prices: bool = True) -> str:
        """
        Generate a detailed, itemized SMS invoice (Arabic RTL or English LTR).
        """
        order_data = order.get("order", {})
        items = order_data.get("items", [])
        thank_you = "شكرا لطلبك من مصراوي" if lang == "ar" else "Thank you for your order from Masrawy"
        order_id_label = "رقم الطلب" if lang == "ar" else "Order ID"
        total_label = "المجموع" if lang == "ar" else "Total"
        tax_label = "الضريبة" if lang == "ar" else "Tax"
        grand_total_label = "الاجمالي" if lang == "ar" else "Grand Total"

        lines = [thank_you, f"{order_id_label}: {order.get('externals_order_id', '')}", "\n"]

        # Extracted logic
        item_lines, total, tax, grand_total = self.prepare_invoice_lines(items, lang, show_prices)
        lines.extend(item_lines)

        # Totals — always show grand total
        if show_prices:
            lines.append(f"{total_label}: ${total:.2f}")
            lines.append(f"{tax_label}: ${tax:.2f}")
        lines.append(f"{grand_total_label}: ${grand_total:.2f}")

        lines.append("شكراً لطلبك!" if lang == "ar" else "Thank you for your order!")

        return "\n".join(lines)

    def send_confirmation_sms(self, body):
        from twilio.rest import Client
        customer_phone = "+16476248506"
        business_phone = "+13657995270"

        twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        message = twilio_client.messages.create(
            body=body,
            from_=business_phone,  # Your Twilio phone number
            to=customer_phone  # The recipient's phone number
        )

    def upsert_customer(self, customer_phone: str, business_phone: str):
        """Create or update a customer record."""
        url = f"{self.base_url}/api/customers/upsert"
        payload = {
            "customer_phone": customer_phone,
            "business_phone": business_phone
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    def get_business_by_phone(self, business_phone: str) :
        """Get business details by phone number."""
        url = f"{self.base_url}/api/business/by-phone"
        payload = {"business_phone": business_phone}

        # Add request timeout and retry logic
        max_retries = 3
        timeout_seconds = 10  # Increased timeout

        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries} - Fetching business details for {business_phone}")

                # Add debug logging for headers (without sensitive info)
                safe_headers = {k: v for k, v in self.headers.items() if k.lower() != 'authorization'}
                logger.debug(f"Request headers: {safe_headers}")
                logger.debug(f"Request payload: {payload}")

                # Make the request with timeout
                response = requests.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=timeout_seconds
                )

                # Log response status and headers
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(
                    f"Request timed out after {timeout_seconds} seconds (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:  # Last attempt
                    raise Exception("Request timed out after multiple retries. Please check your network connection.")

            except requests.exceptions.HTTPError as http_err:
                error_msg = f"HTTP error: {http_err}"
                if hasattr(http_err, 'response') and http_err.response is not None:
                    error_msg += f"\nResponse: {http_err.response.text}"
                    error_msg += f"\nStatus Code: {http_err.response.status_code}"
                    logger.error(error_msg)

                    if http_err.response.status_code == 401:
                        # Log more details about the auth issue
                        logger.error("Authentication failed. Please verify:")
                        logger.error("1. JWT_SECRET_KEY in .env is correct")
                        logger.error("2. The token is being properly included in the Authorization header")
                        logger.error(f"3. The API endpoint is correct: {url}")

                        # Print the actual token for debugging (be careful with this in production)
                        auth_header = self.headers.get('Authorization', '')
                        if auth_header.startswith('Bearer '):
                            logger.debug(f"JWT Token: {auth_header[7:]}")

                        raise Exception(
                            "Authentication failed. Please check your API credentials and ensure the JWT token is valid.")

                    # For other HTTP errors, include the status code in the error message
                    raise Exception(f"HTTP error {http_err.response.status_code}: {http_err}")

                raise Exception(f"Failed to get business details: {http_err}")

            except requests.exceptions.RequestException as req_err:
                logger.error(f"Request failed: {req_err}")
                if attempt == max_retries - 1:  # Last attempt
                    raise Exception(f"Failed to connect to the server: {req_err}")

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise Exception(f"An unexpected error occurred: {str(e)}")

            # Wait before retrying (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s, etc.
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        # This should theoretically never be reached due to the raises above
        raise Exception("Failed to get business details after multiple attempts")

restuarant_tools = RestaurantTools()