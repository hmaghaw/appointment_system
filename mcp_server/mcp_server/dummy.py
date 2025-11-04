import asyncio
from mcp_server.restaurant_mcp_server import mcp

async def main():
    order = {'business_id': 97, 'customer_id': 33, 'items': [{'base_price': 13.5, 'item_id': 1163, 'modifiers': [{'is_active': True, 'modifier_group_id': 131, 'modifier_id': 377, 'name': 'Crispy Onions', 'price_delta': 3.0, 'quantity': 1}, {'is_active': True, 'modifier_group_id': 131, 'modifier_id': 378, 'name': 'Tomato Souce', 'price_delta': 2.0, 'quantity': 1}], 'name': 'Koshary', 'note': 'Crispy onions, Tomato sauce', 'options': [], 'price': 18.5, 'quantity': 1}, {'base_price': 10.25, 'item_id': 1129, 'modifiers': [], 'name': 'Basbusa Masrawy', 'note': '', 'options': [], 'price': 10.25, 'quantity': 1}]}
    action = "update_customer"
    if action == "validate_order":
        result = await mcp.call_tool(
            "validate_order",
            {"order": order}
        )
    elif action == "create_order":
        result = await mcp.call_tool(
            "create_order",
            {"order": order}
        )
    elif action == "update_customer_language":
        result = await mcp.call_tool("update_customer_language", {
        "customer_id": 33,
        "language": "ar"
        })
    elif action == "update_customer":
        result = await mcp.call_tool("update_customer", {
        "customer_id": 33,
        "first_name": "Hany",
        "last_name": "Elgaml",
        })
    print("Tool result:", result)

if __name__ == "__main__":
    asyncio.run(main())