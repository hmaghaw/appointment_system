import requests
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Configuration
BASE_URL = "http://localhost:7000"
API_KEY = os.getenv("API_KEY", "default_key")
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}


def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_update_customer():
    """Test updating customer information"""
    print("\n=== Testing Update Customer ===")
    url = f"{BASE_URL}/api/customers"
    data = {
        "customer_id": 123,
        "first_name": "John",
        "last_name": "Doe",
        "language": "en"
    }

    try:
        response = requests.put(url, json=data, headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_validate_order():
    """Test order validation"""
    print("\n=== Testing Order Validation ===")
    url = f"{BASE_URL}/api/orders/validate"
    order = {
        "language_code": "en",
        "business_id": 97,
        "customer_id": 33,
        "business_phone": "+13657995270",
        "customer_phone": "+16476248506",
        "items": [
            {
                "base_price": 13.5,
                "item_id": 1163,
                "modifiers": [
                    {
                        "is_active": True,
                        "modifier_group_id": 131,
                        "modifier_id": 377,
                        "name": "Crispy Onions",
                        "price_delta": 3.0,
                        "quantity": 1
                    },
                    {
                        "is_active": True,
                        "modifier_group_id": 131,
                        "modifier_id": 378,
                        "name": "Tomato Sauce",
                        "price_delta": 2.0,
                        "quantity": 1
                    }
                ],
                "name": "Koshary",
                "note": "Crispy onions, Tomato sauce",
                "options": [],
                "price": 18.5,
                "quantity": 1
            },
            {
                "base_price": 10.25,
                "item_id": 1129,
                "modifiers": [],
                "name": "Basbusa Masrawy",
                "note": "",
                "options": [],
                "price": 10.25,
                "quantity": 1
            }
        ]
    }

    try:
        response = requests.post(url, json=order, headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_create_order():
    """Test order creation"""
    print("\n=== Testing Order Creation ===")
    url = f"{BASE_URL}/api/orders"
    order = {
        "language_code": "en",
        "business_id": 97,
        "customer_id": 33,
        "business_phone": "+13657995270",
        "customer_phone": "+16476248506",
        "items": [
            {
                "base_price": 13.5,
                "item_id": 1163,
                "modifiers": [
                    {
                        "is_active": True,
                        "modifier_group_id": 131,
                        "modifier_id": 377,
                        "name": "Crispy Onions",
                        "price_delta": 3.0,
                        "quantity": 1
                    },
                    {
                        "is_active": True,
                        "modifier_group_id": 131,
                        "modifier_id": 378,
                        "name": "Tomato Sauce",
                        "price_delta": 2.0,
                        "quantity": 1
                    }
                ],
                "name": "Koshary",
                "note": "Crispy onions, Tomato sauce",
                "options": [],
                "price": 18.5,
                "quantity": 1
            },
            {
                "base_price": 10.25,
                "item_id": 1129,
                "modifiers": [],
                "name": "Basbusa Masrawy",
                "note": "",
                "options": [],
                "price": 10.25,
                "quantity": 1
            }
        ]
    }

    try:
        response = requests.post(url, json=order, headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def run_all_tests():
    """Run all test cases"""
    print("=== Starting HTTP MCP Tester ===")

    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Update Customer", test_update_customer),
        ("Validate Order", test_validate_order),
        ("Create Order", test_create_order)
    ]

    results = []
    for name, test in tests:
        print(f"\nRunning test: {name}")
        result = test()
        results.append((name, result))
        status = "PASSED" if result else "FAILED"
        print(f"Test {name}: {status}")

    # Print summary
    print("\n=== Test Summary ===")
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")

    # Return non-zero exit code if any test failed
    if not all(result for _, result in results):
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()