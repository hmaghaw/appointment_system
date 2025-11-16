from flask import Blueprint, request, jsonify
import logging
import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ClientTools
import json
from pathlib import Path
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

@bp.route('/create', methods=['POST'])
def create_agent():
    data = request.get_json()
    business_id = data.get('business_id')
    language = data.get('language',"en")

    restaurant_agent = RestaurantAgent(business_id, language)
    result = restaurant_agent.create_elevenlabs_agent(business_id, language)
    if result['status'] == 'success':
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@bp.route('/update', methods=['POST'])
def update_agent():
    data = request.get_json()
    business_id = data.get('business_id')
    language = data.get('language', "en")

    restaurant_agent = RestaurantAgent(business_id, language)
    result = restaurant_agent.update_elevenlabs_agent(business_id, language)
    if result['status'] == 'success':
        return jsonify(result), 200
    else:
        return jsonify(result), 500

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

@bp.route('/assign_tool_to_agent', methods=['POST'])
def assign_tool_to_agent():
    """
    Assign a tool to an agent in ElevenLabs
    Expected payload:
    {
        "agent_id": "agent_id_string",
        "tool_id": "tool_id_string"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['agent_id', 'tool_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400


        # Assign tool to agent using the ElevenLabs client
        response = client.conversational_ai.agents.add_tool(
            agent_id=data['agent_id'],
            tool_id=data['tool_id']
        )

        return jsonify({
            'status': 'success',
            'message': 'Tool assigned to agent successfully',
            'data': response.dict() if hasattr(response, 'dict') else str(response)
        })

    except Exception as e:
        logger.error(f"Error in assign_tool_to_agent: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to assign tool to agent',
            'details': str(e)
        }), 500

@bp.route('/create_server_tool', methods=['POST'])
def create_server_tool():
    """
    Create a new server tool in ElevenLabs
    Expected payload:
    {
        "name": "Tool Name",
        "description": "Tool description",
        "endpoint_url": "https://your-server.com/webhook",
        "auth_type": "none",  # or "api_key", "bearer_token"
        "auth_config": {}  # Optional, depends on auth_type
    }
    """
    try:
        data = request.get_json()

        tools_path = str(Path(__file__).parent.parent) + "/eleven_labs_tools"
        filename = f"{tools_path}/new_create_order.json"

        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        tool = client.conversational_ai.tools.create(
                   {
                        "type": "webhook",
                        "name": "new_create_order",
                        "description": "Create a restaurant order with items, options, and modifiers",
                        "api_schema": {
                            "url": "https://a90e100653fd.ngrok-free.app/elevenlabs/tools/create_order",
                            "method": "POST",
                            "request_body_schema": {}
                        },
                        "response_timeout_secs": 20,
                        "dynamic_variables": {}
                    }
                )

        print(tool.id)


        # Validate required fields
        required_fields = ['name', 'description', 'endpoint_url']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400

        # Set default auth type if not provided
        auth_type = data.get('auth_type', 'none')
        auth_config = data.get('auth_config', {})



        return jsonify({
            'status': 'success',
            'message': 'Server tool created successfully',
            'data': tool.dict() if hasattr(tool, 'dict') else str(tool)
        }), 201

    except Exception as e:
        logger.error(f"Error in create_server_tool: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to create server tool',
            'details': str(e)
        }), 500