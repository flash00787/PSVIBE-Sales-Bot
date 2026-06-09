import sys

with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()

# Find insertion point after fetch_food_costs, before fetch_games
marker = '# ═══════════════════════════════════════\n#  fetch_games / fetch_game_library'
pos = content.find(marker)
if pos < 0:
    print("ERROR: marker not found")
    sys.exit(1)

endpoint = '''@app.post("/api/inventory/stock-out", response_model=GenericResponse, tags=["Inventory"], summary="Record stock-out (sale) and update inventory [MySQL]")
async def api_inventory_stock_out(data: dict, auth=Depends(verify_api_key)):
    """Record a stock-out from a food sale and decrement inventory quantity."""
    try:
        item_name = data.get("item_name", "")
        qty = int(data.get("qty", 0))
        unit_price = float(data.get("unit_price", 0))
        subtotal = float(data.get("subtotal", 0))
        sale_date = data.get("date", "")
        voucher_no = data.get("voucher_no", "")

        if not item_name or qty <= 0:
            return error_response(message="item_name and qty > 0 required")

        # Insert into stock_out table
        _mysql_exec(
            "INSERT INTO stock_out (item_name, quantity, unit_price, total, sale_date, notes) VALUES (%s, %s, %s, %s, %s, %s)",
            (item_name, qty, unit_price, subtotal, sale_date, f"Voucher: {voucher_no}")
        )

        # Decrement inventory quantity (best-effort)
        _mysql_exec(
            "UPDATE inventory SET quantity = GREATEST(0, quantity - %s), last_updated = NOW() WHERE item_name = %s",
            (qty, item_name)
        )

        return ok({"success": True, "item_name": item_name, "qty_deducted": qty})
    except Exception as e:
        return error_response(message=str(e))

'''

content = content[:pos] + endpoint + "\n" + content[pos:]

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.write(content)

print('BUG 2: stock-out endpoint added to app.py')
