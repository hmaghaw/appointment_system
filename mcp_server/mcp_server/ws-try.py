import asyncio
import json
import websockets

async def try_mcp_server():
    uri = "ws://localhost:7000/mcp"
    # Connect to your MCP WebSocket server
    async with websockets.connect(uri) as websocket:
        print(f"✅ Connected to MCP server at {uri}")
        order = {'language_code':'en','business_id': 97, 'customer_id': 33,'business_phone': "+13657995270", 'customer_phone': "+16476248506", 'items': [{'base_price': 13.5, 'item_id': 1163, 'modifiers': [
            {'is_active': True, 'modifier_group_id': 131, 'modifier_id': 377, 'name': 'Crispy Onions',
             'price_delta': 3.0, 'quantity': 1},
            {'is_active': True, 'modifier_group_id': 131, 'modifier_id': 378, 'name': 'Tomato Souce',
             'price_delta': 2.0, 'quantity': 1}], 'name': 'Koshary', 'note': 'Crispy onions, Tomato sauce',
                                                                  'options': [], 'price': 18.5, 'quantity': 1},
                                                                 {'base_price': 10.25, 'item_id': 1129, 'modifiers': [],
                                                                  'name': 'Basbusa Masrawy', 'note': '', 'options': [],
                                                                  'price': 10.25, 'quantity': 1}]}
        action = "create_order"
        if action == "validate_order":
            payload = {
                "type": "tool_call",
                "name": "validate_order",
                "arguments": {"order": order}
            }
        elif action == "create_order":
            payload = {
                "type": "tool_call",
                "name": "create_order",
                "arguments": {"order": order}
            }
        elif action == "update_customer_language":
            payload = {
                "type": "tool_call",
                "name": "update_customer_language",
                "arguments": {
                    "customer_id": 33,
                    "language": "ar"
                }
            }
        elif action == "update_customer":
            # Example payload: call validate_order
            payload = {
                "type": "tool_call",
                "name": "update_customer",
                "arguments": {
                    "customer_id": 33,
                    "first_name": "Hani",
                    "last_name": "Elmaghawri",
                    }
            }

        # Send tool_call message
        await websocket.send(json.dumps(payload))
        print("📤 Sent:", json.dumps(payload, indent=2))

        # Wait for tool_result
        response = await websocket.recv()
        print("📥 Received:", response)

# Run
if __name__ == "__main__":
    asyncio.run(try_mcp_server())
