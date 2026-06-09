# Fix: remove erroneously added cash_movements from stock_out function
with open('/root/psvibe_api_server/dashboard_routes.py', 'r') as f:
    content = f.read()

# The stock-out function now has an incorrect cash_movements block.
# Remove it by targeting the exact block that should not be in stock_out.

bad_block = """        )

        # Record cash_movements eject for payment
        total_cost_val = quantity * unit_cost
        if payment_method and total_cost_val > 0:
            note = f"Stock In: {item['item_name']} x{quantity}"
            _mysql_execute(
                "INSERT INTO cash_movements (movement_type, account, amount, note, staff_name, created_at) VALUES (%s, %s, %s, %s, %s, NOW())",
                ("eject", payment_method, total_cost_val, note, staff_name)
            )

        return {
            "success": True,
            "data": {
                "item_name": item["item_name"],
                "quantity_deducted": quantity,"""

good_block = """        )

        return {
            "success": True,
            "data": {
                "item_name": item["item_name"],
                "quantity_deducted": quantity,"""

if bad_block in content:
    content = content.replace(bad_block, good_block)
    print("OK: Removed erroneous cash_movements from stock_out")
else:
    print("FAIL: Could not find bad block in stock_out")
    # Check if it's there at all
    count = content.count("# Record cash_movements eject for payment")
    print(f"Found {count} occurrences of cash_movements comment in file")

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(content)
print("OK: File saved")
