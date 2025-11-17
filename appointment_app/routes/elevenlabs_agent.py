from flask import Blueprint, request, jsonify
import logging
import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ClientTools
import json
from pathlib import Path

from pycparser.ply.yacc import resultlimit

from appointment_app.services.restaurant_agent import RestaurantAgent
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

# Create a Blueprint for ElevenLabs Agent routes
bp = Blueprint('elevenlabs_agent', __name__, url_prefix='/elevenlabs/agent')



@bp.route('/list', methods=['GET'])
def list_agents():
    """
    List all agents in ElevenLabs
    """
    try:
        # List agents using the ElevenLabs client
        agents_response = client.conversational_ai.agents.list()

        # Convert the response to a dictionary
        agents_data = {
            'agents': [agent.dict() for agent in agents_response.agents],
            'pagination': agents_response.pagination.dict() if hasattr(agents_response, 'pagination') else None
        }

        return jsonify({
            'status': 'success',
            'data': agents_data
        })

    except Exception as e:
        logger.error(f"Error in list_agents: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'details': str(e)
        }), 500

@bp.route('/upsert', methods=['POST'])
def upsert_agent():
    data = request.get_json()
    business_id = data.get('business_id')
    language = data.get('language', "en")

    restaurant_agent = RestaurantAgent(business_id, language)
    result = restaurant_agent.upsert_elevenlabs_agent(business_id, language)
    if result['status'] == 'success':
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@bp.route('/assign_phone_number', methods=['POST'])
def assign_phone_number():
    data = request.get_json()
    business_id = data.get('business_id')
    business_phone = data.get('business_phone')
    restaurant_agent = RestaurantAgent(business_id)
    result = restaurant_agent.assign_phone_number(business_phone)
    if result['status'] == 'success':
        return jsonify(result), 200
    else:
        return jsonify(result), 500
