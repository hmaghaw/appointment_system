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
