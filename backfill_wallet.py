#!/usr/bin/env python3
"""Backfill member_wallets balance from sales_daily notes (Mins: N)."""
import pymysql

conn = pymysql.connect(
    host="localhost", user="psvibe_user", password="PsVibe@2026_Rotated!",
    database="psvibe_api", charset="utf8mb4"
)
cur = conn.cursor(pymysql.cursors.DictCursor)

# Get all sales with notes containing "Mins: N"
cur.execute("""
    SELECT member_id, notes FROM sales_daily 
    WHERE member_id NOT IN ('','0 (Guest)','-')
    AND notes LIKE '%Mins: %'
    ORDER BY member_id
""")
sales = cur.fetchall()

# Aggregate mins per member
usage = {}
for s in sales:
    mid = s["member_id"]
    notes = s["notes"]
    # Extract Mins: NNN
    import re
    m = re.search(r'Mins:\s*(\d+)', notes)
    if m:
        mins = int(m.group(1))
        usage[mid] = usage.get(mid, 0) + mins

print("Calculated usage per member:")
for mid, mins in sorted(usage.items()):
    print(f"  {mid}: {mins} mins used")

# Update each member
for mid, used_mins in usage.items():
    cur.execute(
        "UPDATE member_wallets SET total_used_mins = %s, balance_mins = GREATEST(0, COALESCE(total_bought_mins, 0) - %s) WHERE member_id = %s",
        (used_mins, used_mins, mid)
    )
    print(f"  ✅ {mid}: total_used_mins={used_mins}, balance = total_bought_mins - {used_mins}")

conn.commit()

# Verify
cur.execute("SELECT member_id, total_bought_mins, total_used_mins, balance_mins FROM member_wallets WHERE member_id IN ('PSV_A_002','PSV_A_003','PSV_A_004') ORDER BY member_id")
for r in cur.fetchall():
    print(f"  ✓ {r['member_id']}: bought={r['total_bought_mins']} used={r['total_used_mins']} balance={r['balance_mins']} (expected: {r['total_bought_mins'] - r['total_used_mins']})")

conn.close()
print("Done")
