from flask import Blueprint, request, jsonify
import logging
import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ClientTools

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
    """
    Create a new agent in ElevenLabs
    Expected payload:
    {
        "name": "Agent Name",
        "prompt": "Agent's prompt text",
        "voice_id": "voice_id_string",
        "model_id": "model_id_string"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'prompt', 'voice_id', 'model_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400

        # Create agent using the ElevenLabs client
        agent = client.conversational_ai.agents.create(
            name=data['name'],
            prompt=data['prompt'],
            voice_id=data['voice_id'],
            model_id=data['model_id'],
            settings=data.get('settings', {
                'stability': 0.5,
                'similarity_boost': 0.75,
                'style': 0.0,
                'use_speaker_boost': True
            })
        )

        return jsonify({
            'status': 'success',
            'data': agent
        }), 201

    except Exception as e:
        logger.error(f"Error in create_agent: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'details': str(e)
        }), 500

@bp.route('/update/<agent_id>', methods=['POST'])
def update_agent(agent_id):
    """
    Update an existing agent in ElevenLabs
    Expected payload (all fields optional except agent_id in URL):
    {
        "name": "Updated Agent Name",
        "prompt": "Updated prompt",
        "voice_id": "new_voice_id",
        "model_id": "new_model_id"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No update data provided'
            }), 400

        # Update agent using the ElevenLabs client
        updated_agent = client.conversational_ai.agents.update(
            agent_id=agent_id,
            conversation_config={
                "agent": {
                    "prompt": {
                        "prompt": "You are a nice person helping others"
                    }
                }
            }
        )

        return jsonify({
            'status': 'success',
            'data': updated_agent
        })

    except Exception as e:
        logger.error(f"Error in update_agent: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'details': str(e)
        }), 500

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

        # Create the tool using the ElevenLabs client
        tool = client.conversational_ai.tools.create(
            name=data['name'],
            description=data['description'],
            type="server_tool",
            config={
                "endpoint_url": data['endpoint_url'],
                "auth": {
                    "type": auth_type,
                    "config": auth_config
                }
            }
        )

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