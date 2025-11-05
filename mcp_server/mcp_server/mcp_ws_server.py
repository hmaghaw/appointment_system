import os
import logging
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from mcp.server.fastmcp import FastMCP
from restaurants_tools import RestaurantTools
from pydantic import BaseModel
from typing import List, Optional
# ---------- Pydantic Models ----------

class Modifier(BaseModel):
    is_active: bool
    modifier_group_id: int
    modifier_id: int
    name: str
    price_delta: float
    quantity: int

class Item(BaseModel):
    base_price: float
    item_id: int
    name: str
    note: Optional[str] = ""
    options: List[dict]
    modifiers: List[Modifier]
    price: float
    quantity: int

class Order(BaseModel):
    language_code: str
    business_id: int
    customer_id: int
    business_phone: str
    customer_phone: str
    items: List[Item]



# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI and FastMCP
app = FastAPI(title="Restaurant MCP Server")
mcp = FastMCP(name="restaurant_mcp")

# Restaurant tools setup
restaurant_tools = RestaurantTools()

# Register MCP tools
@mcp.tool()
def update_customer(customer_id, first_name: str, last_name: str):
    """Update customer name and details."""
    return restaurant_tools.update_customer(customer_id, first_name, last_name)

@mcp.tool()
def update_customer_language(customer_id, language: str):
    """Update customer's preferred language."""
    return restaurant_tools.update_customer_language(customer_id, language)

@mcp.tool()
def create_order(order: Order):
    """Create a restaurant order."""
    return restaurant_tools.create_order(order)

@mcp.tool()
def validate_order(order: Order):
    """Validate order items and calculate totals."""
    # This is a simplified version - you might want to implement more robust validation
    if not isinstance(order, dict) or 'items' not in order:
        return "Error: Invalid order format. Expected a dictionary with an 'items' key."
    return restaurant_tools.validate_order(order)

@mcp.tool()
def hangup_call() -> str:
    """End call politely."""
    return "Call ended gracefully"

# WebSocket endpoint
@app.websocket("/")
async def mcp_ws_endpoint(websocket: WebSocket):
    """Main MCP WebSocket endpoint"""
    await websocket.accept()
    logger.info("✅ New WebSocket connection accepted")

    try:
        while True:
            # Receive message from client (ElevenLabs Agent)
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.debug(f"📩 Received: {message}")

            # Expecting { "type": "tool_call", "name": "...", "arguments": {...} }
            if message.get("type") == "tool_call":
                tool_name = message["name"]
                args = message.get("arguments", {})

                try:
                    # Run the tool using FastMCP
                    result = await mcp.call_tool(tool_name, args)
                    response = {"type": "tool_result", "result": result}
                except Exception as e:
                    response = {"type": "error", "message": str(e)}

                await websocket.send_text(str(response))
                logger.info(f"✅ Executed tool '{tool_name}' successfully")

    except WebSocketDisconnect:
        logger.info("❌ WebSocket client disconnected")
    except Exception as e:
        logger.error(f"⚠️ MCP WebSocket error: {e}", exc_info=True)
        await websocket.close()

# Entry point
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "7000"))

    logger.info(f"🚀 Starting Restaurant MCP WebSocket Server on ws://{host}:{port}/mcp")
    uvicorn.run(app, host=host, port=port)
