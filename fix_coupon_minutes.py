#!/usr/bin/env python3
"""Fix coupon generation to use wallet_deduct minutes instead of play_mins."""
import re
import sys

SALES_PY = "/root/psvibe-sales-bot/bot/handlers/sales.py"
BACKUP = SALES_PY + ".bak." + __import__("datetime").datetime.now().strftime("%Y%m%d%H%M%S")

with open(SALES_PY, "r") as f:
    content = f.read()

# Backup
with open(BACKUP, "w") as f:
    f.write(content)
print(f"Backup: {BACKUP}")

changes = 0

# Fix 1: step_sale_confirm - use wallet_deduct instead of play_mins
old1 = '    if play_mins > 0 and not d.get("_cashback_coupon"):\n        try:\n            from bot.api_client import api_post\n            gen_result = await asyncio.to_thread(\n                api_post, "coupons/generate",\n                {"member_id": m_id, "session_minutes": play_mins}\n            )'

new1 = '    if play_mins > 0 and not d.get("_cashback_coupon"):\n        _cpn_mins = wallet_deduct if wallet_deduct > play_mins else play_mins\n        try:\n            from bot.api_client import api_post\n            gen_result = await asyncio.to_thread(\n                api_post, "coupons/generate",\n                {"member_id": m_id, "session_minutes": _cpn_mins}\n            )'

if old1 in content:
    content = content.replace(old1, new1, 1)
    changes += 1
    print("Fix 1: Applied wallet_deduct to step_sale_confirm")
else:
    print("Fix 1: Pattern not found - checking...")
    # Show what's actually there
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "play_mins > 0 and not d.get" in line:
            for j in range(i, min(i+8, len(lines))):
                print(f"  L{j+1}: {lines[j]}")

# Fix 2: launch_session_sale - use effective_cost_mins
old2 = '    if total_mins > 0 and not context.user_data.get("_cashback_coupon"):\n        try:\n            from bot.api_client import api_post\n            gen_result = await asyncio.to_thread(\n                api_post, "coupons/generate",\n                {"member_id": member_id, "session_minutes": total_mins}\n            )'

new2 = '    if total_mins > 0 and not context.user_data.get("_cashback_coupon"):\n        _cpn_mins2 = effective_cost_mins if effective_cost_mins > total_mins else total_mins\n        try:\n            from bot.api_client import api_post\n            gen_result = await asyncio.to_thread(\n                api_post, "coupons/generate",\n                {"member_id": member_id, "session_minutes": _cpn_mins2}\n            )'

if old2 in content:
    content = content.replace(old2, new2, 1)
    changes += 1
    print("Fix 2: Applied effective_cost_mins to launch_session_sale")
else:
    print("Fix 2: Pattern not found")

# Fix 3: Also update _cashback_coupon_mins in launch_session_sale
old3 = '                    context.user_data["_cashback_coupon_mins"] = cd.get("minutes", total_mins)'
new3 = '                    context.user_data["_cashback_coupon_mins"] = cd.get("minutes", _cpn_mins2)'

if old3 in content:
    content = content.replace(old3, new3, 1)
    changes += 1
    print("Fix 3: Updated coupon_mins in launch_session_sale")
else:
    print("Fix 3: Pattern not found")

with open(SALES_PY, "w") as f:
    f.write(content)

print(f"\nTotal changes: {changes}")
if changes > 0:
    print("File saved successfully!")
