#!/usr/bin/env python3
"""Remove the dedup check from coupon generate API - create new coupon each time."""
import sys

APP_PY = "/root/psvibe_api_server/app.py"
BACKUP = APP_PY + ".bak." + __import__("datetime").datetime.now().strftime("%Y%m%d%H%M%S")

with open(APP_PY, "r") as f:
    content = f.read()

# Backup
with open(BACKUP, "w") as f:
    f.write(content)
print(f"Backup: {BACKUP}")

# Remove the dedup check block
old = """        # Check if member already has active coupon (prevent duplicates)
        existing_coupons = _mysql_query("SELECT id, coupon_code, original_minutes, balance_minutes FROM member_coupons WHERE member_id=%s AND status='active' AND expiry_date > NOW() ORDER BY issued_date DESC LIMIT 1", (member_id,))
        if existing_coupons:
            e = existing_coupons[0]
            print('REUSING existing coupon:', e['coupon_code'], 'for member:', member_id)
            return ok({"coupon": {
                "id": e["id"],
                "code": e["coupon_code"],
                "member_id": member_id,
                "minutes": e.get("original_minutes", session_minutes),
                "balance": e.get("balance_minutes", e.get("original_minutes", session_minutes)),
                "expiry": expiry_date,
                "existing": True
            }})
        
        # Generate unique code"""

new = """        # Generate unique code"""

if old in content:
    content = content.replace(old, new, 1)
    with open(APP_PY, "w") as f:
        f.write(content)
    print("✅ Dedup check REMOVED")
    print("   → Every sale creates a new coupon with correct minutes")
else:
    print("❌ Pattern not found!")
    # Show what's around that area
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "Check if member already" in line:
            for j in range(i, min(i+15, len(lines))):
                print(f"  L{j+1}: {lines[j]}")
            break
    else:
        print("   (Could not find the pattern at all)")
