from flask import Blueprint, request, jsonify
import logging
# Add this import at the top with other imports
from appointment_app.services.elevenlabs_tools import restuarant_tools

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for ElevenLabs routes
bp = Blueprint('elevenlabs', __name__, url_prefix='/elevenlabs/tools/')

@bp.route('/call_init', methods=['POST'])
def handle_call_init():
    """
    Handle call initialization webhook from ElevenLabs
    Expected payload:
    {
        "type": "conversation_initiation_client_data",
        "caller_number": "+16475550123",
        "called_number": "+14165550999",
        "call_sid": " CAc9302b7e34f64970b92e15fb41a37c18",
        "agent_id": "agent_73eaa0a4e28d",
        "direction": "inbound",
        "integration": "twilio",
        "timestamp": "2025-11-02T18:10:44.321Z"
    }
    """


    try:
        # Get JSON data from request
        language = "en"
        data = request.get_json()
        # Validate required fields
        required_fields = [
            'caller_id', 'called_number',
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400


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

        if customer_language:
            language = customer_language

        # Log the received data
        logger.info(f"Received call init webhook: {data}")
        

        
        # Process the call initialization data
        # TODO: Add your custom logic here to handle the call initiation
        # For example, you might want to store this information in a database
        # or trigger some other action in your application
        
        # Log the processed data
        logger.info(f"Processed call from {customer_phone} to {business_phone} ")
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Call initiation received successfully',
            'customer': {
                'customer_id': customer_id,
                'first_name': first_name,
                'last_name': last_name,
                'language': customer_language,
                'phone': customer_phone
            },
            'business': {
                'business_id': business_id,
                'name': business_name,
                'language': business_language,
                'phone': business_phone
            },
            'call': {
                'call_sid': call_sid,
                'preferred_language': language
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing call init webhook: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Failed to process webhook: {str(e)}'
        }), 500



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