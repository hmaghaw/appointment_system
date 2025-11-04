from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for ElevenLabs routes
bp = Blueprint('elevenlabs', __name__, url_prefix='/webhook')

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
        data = request.get_json()
        
        # Log the received data
        logger.info(f"Received call init webhook: {data}")
        
        # Validate required fields
        required_fields = [
            'type', 'caller_number', 'called_number', 
            'call_sid', 'agent_id', 'direction', 
            'integration', 'timestamp'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Process the call initialization data
        # TODO: Add your custom logic here to handle the call initiation
        # For example, you might want to store this information in a database
        # or trigger some other action in your application
        
        # Log the processed data
        logger.info(f"Processed call from {data['caller_number']} to {data['called_number']} "
                   f"with agent {data['agent_id']}")
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Call initiation received successfully',
            'data': data
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing call init webhook: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Failed to process webhook: {str(e)}'
        }), 500
