import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

from appointment_app.services.utils import generate_jwt_token

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

restuarant_tools = RestaurantTools()