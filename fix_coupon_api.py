#!/usr/bin/env python3
"""Fix duplicate coupon generation in the API endpoint."""
import re
import sys

APP_PATH = "/root/psvibe_api_server/app.py"
BACKUP_PATH = APP_PATH + ".bak." + __import__("datetime").datetime.now().strftime("%Y%m%d%H%M%S")

with open(APP_PATH, "r") as f:
    content = f.read()

# Backup
with open(BACKUP_PATH, "w") as f:
    f.write(content)
print(f"Backup saved to {BACKUP_PATH}")

# Find the coupon generate function and add dedup check
old = """        promo = rows[0]
        promo_id = promo["id"]
        expiry_date = str(promo["coupon_expiry_date"]) + " 23:59:59"
        
        # Generate unique code"""

new = """        promo = rows[0]
        promo_id = promo["id"]
        expiry_date = str(promo["coupon_expiry_date"]) + " 23:59:59"
        
        # Check if member already has active coupon (prevent duplicates)
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

if old in content:
    content = content.replace(old, new, 1)
    with open(APP_PATH, "w") as f:
        f.write(content)
    print("✅ Dedup check added successfully!")
else:
    print("❌ Pattern not found!")
    # Debug
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "expiry_date" in line and "23:59:59" in line:
            for j in range(max(0, i-2), min(len(lines), i+5)):
                print(f"  Line {j+1}: {lines[j]}")
    sys.exit(1)
