#!/usr/bin/env python3
"""Re-apply coupon generation fix to sales.py (restored from backup before the fix)."""
import re
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    content = f.read()

changes = 0

# ── Fix 1: Coupon in step_sale_confirm ──
# Find the relevant section
old1 = """    # ── CashBack Coupon: Auto-generate via MySQL API (ALL sales flows) ──
    if play_mins > 0 and not d.get("_cashback_coupon"):
        try:
            from bot.api_client import api_post
            gen_result = await asyncio.to_thread(
                api_post, "coupons/generate",
                {"member_id": m_id, "session_minutes": play_mins}
            )"""

new1 = """    # ── CashBack Coupon: Auto-generate via MySQL API (ALL sales flows) ──
    if play_mins > 0 and not d.get("_cashback_coupon"):
        _cpn_mins = wallet_deduct if wallet_deduct > play_mins else play_mins
        try:
            from bot.api_client import api_post
            gen_result = await asyncio.to_thread(
                api_post, "coupons/generate",
                {"member_id": m_id, "session_minutes": _cpn_mins}
            )"""

if old1 in content:
    content = content.replace(old1, new1)
    changes += 1
    print("Fix 1 applied: coupon uses wallet_deduct")
else:
    print("WARNING: Fix 1 pattern not found!")
    # Try looking for the coupon block differently
    idx = content.find('# ── CashBack Coupon: Auto-generate via MySQL API')
    if idx >= 0:
        print(f"  Found coupon block at position {idx}")
        print(f"  Content: {content[idx:idx+300]}")

# ── Fix 2: Coupon in launch_session_sale ──
old2 = """    # ── CashBack Coupon: Auto-generate via MySQL API ──
    if total_mins > 0 and not context.user_data.get("_cashback_coupon"):
        try:
            from bot.api_client import api_post
            gen_result = await asyncio.to_thread(
                api_post, "coupons/generate",
                {"member_id": member_id, "session_minutes": total_mins}
            )"""

new2 = """    # ── CashBack Coupon: Auto-generate via MySQL API ──
    if total_mins > 0 and not context.user_data.get("_cashback_coupon"):
        _cpn_mins2 = effective_cost_mins if effective_cost_mins > total_mins else total_mins
        try:
            from bot.api_client import api_post
            gen_result = await asyncio.to_thread(
                api_post, "coupons/generate",
                {"member_id": member_id, "session_minutes": _cpn_mins2}
            )"""

if old2 in content:
    content = content.replace(old2, new2)
    changes += 1
    print("Fix 2 applied: launch_session_sale uses effective_cost_mins")
else:
    print("WARNING: Fix 2 pattern not found!")
    idx = content.find('# ── CashBack Coupon: Auto-generate via MySQL API', 500)
    if idx >= 0:
        print(f"  Found second coupon block at position {idx}")
        print(f"  Content: {content[idx:idx+300]}")

# ── Fix 3: Add effective_cost_mins to launch_session_sale user_data ──
# Find where user_data is populated in launch_session_sale
old3 = '''        "v_no":             d.get("v_no") or "",'''

new3 = '''        "effective_cost_mins": pre_effective_mins if pre_effective_mins > 0 else round(total_mins * multiplier),
        "v_no":             d.get("v_no") or "",'''

if old3 in content and new3 not in content:
    content = content.replace(old3, new3)
    changes += 1
    print("Fix 3 applied: effective_cost_mins in user_data")
else:
    if new3 in content:
        print("Fix 3 already present")
    else:
        print(f"WARNING: Fix 3 pattern not found - old3:{old3 in content}")

with open(filepath, 'w') as f:
    f.write(content)

print(f"\nTotal changes applied: {changes}")
