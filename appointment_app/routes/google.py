"""
Google OAuth2 callback routes.
Handles OAuth2 callbacks from Google services.
"""
import logging
from flask import Blueprint, request, jsonify

# Create blueprint
bp = Blueprint('google', __name__, url_prefix='/rest/oauth2-credential')

# Set up logging
logger = logging.getLogger(__name__)

@bp.route('/callback', methods=['POST'])
def oauth2_callback():
    """
    Handle OAuth2 callback from Google.
    This endpoint receives the authorization code from Google after user grants permission.
    
    Request format (JSON):
    {
        "code": "authorization_code_from_google",
        "state": "optional_state_parameter",
        "scope": "space_separated_list_of_scopes",
        "authuser": "user_identifier",
        "prompt": "consent"
    }
    
    Returns:
        JSON response with success status and the received payload
    """
    try:
        # Log the incoming request data for debugging
        request_data = request.get_json()
        logger.info(f"Received OAuth2 callback with data: {request_data}")
        
        # Basic validation
        if not request_data:
            logger.warning("No JSON data received in OAuth2 callback")
            return jsonify({
                'success': False,
                'error': 'no_data',
                'message': 'No data received in request'
            }), 400
            
        # Log the authorization code if present
        auth_code = request_data.get('code')
        if auth_code:
            logger.info(f"Received authorization code: {auth_code[:10]}...")
            
            # Here you would typically exchange the authorization code for tokens
            # and process the user authentication/authorization
            # For now, we'll just log and return success
            
            return jsonify({
                'success': True,
                'message': 'OAuth2 callback received successfully',
                'code_received': True,
                'state': request_data.get('state')
            })
            
        return jsonify({
            'success': False,
            'error': 'missing_code',
            'message': 'No authorization code found in request',
            'received_data': request_data
        }), 400
        
    except Exception as e:
        logger.error(f"Error processing OAuth2 callback: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'server_error',
            'message': 'An error occurred while processing the OAuth2 callback'
        }), 500
