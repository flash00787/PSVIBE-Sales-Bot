#!/usr/bin/env python3
"""Fix api_add_sales_record mapping to match API endpoint expectations."""
import sys

filepath = sys.argv[1]
with open(filepath, 'r') as f:
    content = f.read()

old_func_start = 'def api_add_sales_record(data: dict) -> dict | None:'
new_func = '''def api_add_sales_record(data: dict) -> dict | None:
    """Add a sales record.

    Transforms caller field names to match /api/sales/record endpoint expectations.
    """
    mapped: dict = {
        "voucher_no": data.get("voucher_no", ""),
        "member_id": data.get("member_id", ""),
        "console_id": data.get("console_id", ""),
        "mins": data.get("play_mins", 0),
        "game_amt": data.get("game_amount", 0),
        "food_total": data.get("food_total", 0),
        "discount": data.get("discount", 0),
        "net_total": data.get("net_total", 0),
        "payment_method": f"KPay:{data.get('kpay',0)}|Cash:{data.get('cash',0)}",
        "staff": data.get("staff", ""),
        "food_items": str(data.get("food_items", "")),
        "notes": data.get("notes", ""),
        "coupon_code": data.get("coupon_code", ""),
    }
    return _api_call("POST", "sales/record", json_data=mapped)'''

# Find the start and end of the old function
if old_func_start not in content:
    print("ERROR: function start not found!")
    sys.exit(1)

start_idx = content.index(old_func_start)
# Find the end: next 'def ' at same indent level or EOF
rest = content[start_idx:]
lines = rest.split('\n')
end_idx = len(rest)
for i, line in enumerate(lines[1:], 1):
    if line.startswith('def ') and not line.startswith('def ' + ' ' * 8) and i > 1:
        # Adjust for the first line offset
        end_idx = sum(len(l) + 1 for l in lines[:i])
        break

content = content[:start_idx] + new_func + '\n\n\n' + content[start_idx + end_idx:]

with open(filepath, 'w') as f:
    f.write(content)

print("FIXED: api_add_sales_record updated successfully")
