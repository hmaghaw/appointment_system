from fastapi import FastAPI, HTTPException, status, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from restaurants_tools import RestaurantTools

# Load environment variables
if not os.getenv("ENVIRONMENT"):
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Restaurant API",
    description="RESTful API for restaurant operations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize restaurant tools
restaurant_tools = RestaurantTools()

# Request/Response Models
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
    options: List[Dict[str, Any]] = Field(default_factory=list)
    modifiers: List[Modifier] = Field(default_factory=list)
    price: float
    quantity: int

class OrderRequest(BaseModel):
    language_code: str
    business_id: int
    customer_id: int
    business_phone: str
    customer_phone: str
    items: List[Item]

class OrderResponse(BaseModel):
    success: bool
    message: str
    order_id: Optional[str] = None
    total: Optional[float] = None

class CustomerUpdateRequest(BaseModel):
    customer_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: Optional[str] = None

class CustomerResponse(BaseModel):
    success: bool
    message: str

# Helper function to verify API key (if needed)
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY", "default_key"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return x_api_key


@app.get("/.well-known/mcp.json")
def get_manifest():
    """
    Returns a manifest of all available API endpoints with their details.
    This follows the MCP (Machine Communication Protocol) specification.
    """
    return {
        "name": "RestaurantMCP",
        "version": "1.0.0",
        "description": "RESTful API for restaurant operations",
        "endpoints": [
            {
                "name": "create_order",
                "path": "/api/orders",
                "method": "POST",
                "description": "Create a new restaurant order",
                "request_model": {
                    "type": "object",
                    "properties": {
                        "language_code": {"type": "string"},
                        "business_id": {"type": "integer"},
                        "customer_id": {"type": "integer"},
                        "business_phone": {"type": "string"},
                        "customer_phone": {"type": "string"},
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/OrderItem"}
                        }
                    },
                    "required": ["language_code", "business_id", "customer_id", "business_phone", "customer_phone", "items"]
                },
                "response_model": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"},
                        "order_id": {"type": "string"},
                        "total": {"type": "number"}
                    }
                }
            },
            {
                "name": "validate_order",
                "path": "/api/orders/validate",
                "method": "POST",
                "description": "Validate an order and return calculated totals",
                "request_model": {
                    "$ref": "#/definitions/OrderRequest"
                },
                "response_model": {
                    "type": "object",
                    "properties": {
                        "response": {"type": "string"}
                    }
                }
            },
            {
                "name": "update_customer",
                "path": "/api/customers",
                "method": "PUT",
                "description": "Update customer information and/or preferred language",
                "request_model": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "integer"},
                        "first_name": {"type": "string", "nullable": True},
                        "last_name": {"type": "string", "nullable": True},
                        "language": {"type": "string", "nullable": True}
                    },
                    "required": ["customer_id"]
                },
                "response_model": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"}
                    }
                }
            },
            {
                "name": "health_check",
                "path": "/health",
                "method": "GET",
                "description": "Health check endpoint",
                "response_model": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "version": {"type": "string"}
                    }
                }
            }
        ],
        "definitions": {
            "OrderRequest": {
                "type": "object",
                "properties": {
                    "language_code": {"type": "string"},
                    "business_id": {"type": "integer"},
                    "customer_id": {"type": "integer"},
                    "business_phone": {"type": "string"},
                    "customer_phone": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/OrderItem"}
                    }
                },
                "required": ["language_code", "business_id", "customer_id", "business_phone", "customer_phone", "items"]
            },
            "OrderItem": {
                "type": "object",
                "properties": {
                    "base_price": {"type": "number"},
                    "item_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "note": {"type": "string"},
                    "options": {"type": "array", "items": {}},
                    "modifiers": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/Modifier"}
                    },
                    "price": {"type": "number"},
                    "quantity": {"type": "integer"}
                },
                "required": ["base_price", "item_id", "name", "options", "modifiers", "price", "quantity"]
            },
            "Modifier": {
                "type": "object",
                "properties": {
                    "is_active": {"type": "boolean"},
                    "modifier_group_id": {"type": "integer"},
                    "modifier_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "price_delta": {"type": "number"},
                    "quantity": {"type": "integer"}
                },
                "required": ["is_active", "modifier_group_id", "modifier_id", "name", "price_delta", "quantity"]
            }
        }
    }

# API Endpoints
@app.post("/api/orders", response_model=OrderResponse, tags=["Orders"])
async def create_order(order: OrderRequest):
    """
    Create a new restaurant order.

    - **language_code**: Language code (e.g., 'en', 'ar')
    - **business_id**: ID of the business
    - **customer_id**: ID of the customer
    - **business_phone**: Business phone number
    - **customer_phone**: Customer phone number
    - **items**: List of order items with modifiers
    """
    try:
        result = restaurant_tools.create_order(order.dict())
        return {
            "success": True,
            "message": "Order created successfully",
            "order_id": "ORD-" + str(hash(str(order.dict())))[:8].upper()
        }
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )

@app.post("/api/orders/validate", tags=["Orders"])
async def validate_order(order: OrderRequest):
    """
    Validate an order and return the calculated totals.
    """
    try:
        return restaurant_tools.validate_order(order.dict())
    except Exception as e:
        logger.error(f"Error validating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order format"
        )

@app.put("/api/customers", response_model=CustomerResponse, tags=["Customers"])
async def update_customer(customer_data: CustomerUpdateRequest):
    """
    Update customer information.

    - **customer_id**: ID of the customer to update (required)
    - **first_name**: New first name (optional)
    - **last_name**: New last name (optional)
    - **language**: New preferred language (optional)
    """
    try:
        if customer_data.first_name or customer_data.last_name:
            result = restaurant_tools.update_customer(
                customer_data.customer_id,
                customer_data.first_name or "",
                customer_data.last_name or ""
            )
            if "error" in result.get("response", "").lower():
                raise Exception(result["response"])

        if customer_data.language:
            result = restaurant_tools.update_customer_language(
                customer_data.customer_id,
                customer_data.language
            )
            if "error" in result.get("response", "").lower():
                raise Exception(result["response"])

        return {"success": True, "message": "Customer updated successfully"}
    except Exception as e:
        logger.error(f"Error updating customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "7000"))

    logger.info(f"🚀 Starting Restaurant API Server on http://{host}:{port}")
    uvicorn.run("mcp_http_server:app", host=host, port=port, reload=True)
