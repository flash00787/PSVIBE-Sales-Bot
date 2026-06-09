# Fix stock-in: add cash_movements eject + PUT endpoint
import re

with open('/root/psvibe_api_server/dashboard_routes.py', 'r') as f:
    content = f.read()

# 1. Add cash_movements INSERT after stock_in POST
old_post_block = """            (new_qty, item_id)
        )

        return {"""
new_post_block = """            (new_qty, item_id)
        )

        # Record cash_movements eject for payment
        total_cost_val = quantity * unit_cost
        if payment_method and total_cost_val > 0:
            note = f"Stock In: {item['item_name']} x{quantity}"
            _mysql_execute(
                "INSERT INTO cash_movements (movement_type, account, amount, note, staff_name, created_at) VALUES (%s, %s, %s, %s, %s, NOW())",
                ("eject", payment_method, total_cost_val, note, staff_name)
            )

        return {"""

if old_post_block in content:
    content = content.replace(old_post_block, new_post_block)
    print("OK: Added cash_movements to POST /stock-in")
else:
    print("FAIL: Could not find POST /stock-in inventory update block")
    # Debug: show what's around
    idx = content.find('(new_qty, item_id)')
    if idx >= 0:
        print('Found at:', idx)
        print(repr(content[idx:idx+200]))

# 2. Add PUT /stock-in/{entry_id} endpoint
put_endpoint = """

@router.put("/stock-in/{entry_id}")
async def dashboard_update_stock_in(entry_id: int, req: dict, user: dict = Depends(get_current_user)):
    \"\"\"Update a stock-in record.\"\"\"
    try:
        existing = _mysql_query_one("SELECT * FROM stock_in WHERE id = %s", (entry_id,))
        if not existing:
            return {"success": False, "error": "Stock-in record not found"}

        item_name = req.get("item_name", existing.get("item_name"))
        quantity = req.get("quantity", existing.get("quantity"))
        unit_cost = req.get("unit_cost", existing.get("unit_cost"))
        source = req.get("source", existing.get("source"))
        receipt_no = req.get("receipt_no", existing.get("receipt_no"))
        payment_method = req.get("payment_method", existing.get("payment_method"))
        paid_by = req.get("paid_by", existing.get("paid_by"))
        staff_name = req.get("staff_name", existing.get("staff_name"))

        old_qty = int(existing.get("quantity") or 0)
        new_qty = int(quantity or 0)

        # Reverse old inventory
        old_item = _mysql_query_one("SELECT * FROM inventory WHERE item_name = %s", (existing["item_name"],))
        if old_item:
            old_inv_qty = max(0, int(old_item["quantity"] or 0) - old_qty)
            _mysql_execute(
                "UPDATE inventory SET quantity = %s, last_updated = NOW() WHERE id = %s",
                (old_inv_qty, old_item["id"])
            )

        # Apply new inventory
        new_item = _mysql_query_one("SELECT * FROM inventory WHERE item_name = %s", (item_name,))
        if new_item:
            new_inv_qty = int(new_item["quantity"] or 0) + new_qty
            _mysql_execute(
                "UPDATE inventory SET quantity = %s, last_updated = NOW() WHERE id = %s",
                (new_inv_qty, new_item["id"])
            )

        _mysql_execute(
            \"\"\"UPDATE stock_in SET item_name=%s, quantity=%s, unit_cost=%s, source=%s,
               receipt_no=%s, payment_method=%s, paid_by=%s, staff_name=%s WHERE id=%s\"\"\",
            (item_name, quantity, unit_cost, source, receipt_no, payment_method, paid_by, staff_name, entry_id)
        )

        # Update cash_movements: delete old, create new eject entry
        old_note = f"Stock In: {existing['item_name']} x{old_qty}"
        _mysql_delete("DELETE FROM cash_movements WHERE note = %s", (old_note,))

        new_total = new_qty * float(unit_cost or 0)
        if payment_method and new_total > 0:
            note = f"Stock In: {item_name} x{new_qty}"
            _mysql_execute(
                "INSERT INTO cash_movements (movement_type, account, amount, note, staff_name, created_at) VALUES (%s, %s, %s, %s, %s, NOW())",
                ("eject", payment_method, new_total, note, staff_name)
            )

        return {"success": True, "data": {"id": entry_id, "updated": item_name}}
    except Exception as e:
        logger.error(f"PUT /stock-in/{entry_id} error: {e}")
        return {"success": False, "error": str(e)}

"""

old_marker = """

@router.post("/stock-out")"""
new_marker = put_endpoint + """
@router.post("/stock-out")"""

if old_marker in content:
    content = content.replace(old_marker, new_marker)
    print("OK: Added PUT /stock-in/{entry_id} endpoint")
else:
    print("FAIL: Could not find insertion point for PUT endpoint")

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(content)
print("OK: File saved")
