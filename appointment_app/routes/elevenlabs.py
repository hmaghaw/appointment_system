from flask import Blueprint, request, jsonify
import logging
from dotenv import load_dotenv
import os
# Add this import at the top with other imports
from appointment_app.services.restaurant_tools import restuarant_tools
from elevenlabs.conversational_ai.conversation import Conversation, ConversationInitiationData
from elevenlabs import ElevenLabs
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Initialize ElevenLabs client
client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
    base_url="https://api.elevenlabs.io"
)


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for ElevenLabs routes
bp = Blueprint('elevenlabs', __name__, url_prefix='/elevenlabs/tools/')

@bp.route('/call_init', methods=['POST'])
def handle_call_init():
    data = request.get_json()
    customer_phone = data.get('caller_id')
    business_phone = data.get('called_number')
    call_sid = data.get('call_sid')

    customer_data = restuarant_tools.upsert_customer(
        customer_phone=customer_phone,
        business_phone=business_phone
    )
    customer_id = customer_data.get('customer_id')
    customer_language = customer_data.get('language')
    first_name = customer_data.get('first_name')
    last_name = customer_data.get('last_name')

    business_data = restuarant_tools.get_business_by_phone(business_phone=business_phone)
    business_id = business_data.get('business_id')
    business_name = business_data.get('name')
    business_language = business_data.get('language_code')

    if first_name == "Guest":
        first_name = ""

    custom_first_message = f"Hi {first_name}, thank you for calling {business_name}. How can I help you today?"

    if customer_language:
        language = customer_language
    else:
        language = business_language
    # Log the received data
    logger.info(f"Received call init webhook: {data}")

    return jsonify({
  "type": "conversation_initiation_client_data",
  "conversation_config_override": {
    "agent": {
      "first_message": custom_first_message,
      "language": "en"
    }
  },
  "dynamic_variables": {
    "user_name": "John",
    "account_type": "premium"
  }
})



# Add these new routes before the end of the file
@bp.route('/update_customer_language', methods=['POST'])
def update_language():
    try:
        data = request.get_json()
        language = data.get('language')
        if not language:
            return jsonify({"error": "Language parameter is required"}), 400

        result = restuarant_tools.update_customer_language(language=language)
        return jsonify({"status": "success", "message": result})
    except Exception as e:
        logger.error(f"Error in update_language: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/update_customer', methods=['POST'])
def update_customer():
    try:
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not all([first_name, last_name]):
            return jsonify({"error": "Both first_name and last_name are required"}), 400

        result = restuarant_tools.update_customer(first_name=first_name, last_name=last_name)
        return jsonify({"status": "success", "message": result})
    except Exception as e:
        logger.error(f"Error in update_customer: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/create_order', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        order = data.get('order')

        if not order:
            return jsonify({"error": "Order data is required"}), 400

        result = restuarant_tools.create_order(order=order)
        return jsonify({"status": "success", "message": result})
    except Exception as e:
        logger.error(f"Error in create_order: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/validate_order', methods=['POST'])
def validate_order():
    try:
        data = request.get_json()
        order = data.get('order')

        if not order:
            return jsonify({"error": "Order data is required"}), 400

        result = restuarant_tools.validate_order(order=order)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        logger.error(f"Error in validate_order: {str(e)}")
        return jsonify({"error": str(e)}), 500