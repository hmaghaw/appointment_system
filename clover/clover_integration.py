from appointment_app.services.clover_integration import CloverIntegration

# Example usage
if __name__ == "__main__":
    try:
        # Initialize with business_id
        clover = CloverIntegration(business_id=69)  # Replace with actual business_id
        items = clover.list_combos()
        items = clover.list_items()

        # List ALL modifier groups across merchant
        modifiers = clover.list_modifiers()

        # List ALL option groups (combos) across merchant
        options = clover.list_options()

        # Example 1: Create an order with multiple items
        items_to_order = [
            {"id": 'QH1M3GWR3D0DP', "quantity": 1},
            {"id": 'C2DNHVFJ0ZRGM', "quantity": 2},
            {"id": '25K24H0TYXA3G', "quantity": 1}
        ]
        order = clover.create_order_with_items(items_to_order, "Family Package Order")
        print(f"Order created successfully: {order['id']}")

        # Example 2: List items and their modifiers
        items = clover.list_items()
        if items:
            first_item = items[0]
            print(f"\n🔎 Checking modifiers for item: {first_item['name']} (ID: {first_item['id']})")

            groups = clover.list_item_modifiers(first_item["id"])
            if groups:
                for group in groups:
                    print(f"Modifier Group: {group['group_name']} (ID: {group['group_id']})")
                    for mod in group["modifiers"]:
                        price = mod["price"] / 100.0  # Clover stores price in cents
                        #print(f"  - {mod['name']} (ID: {mod['id']} | +${price:.2f})")

    except Exception as e:
        print(f"❌ Error: {e}")