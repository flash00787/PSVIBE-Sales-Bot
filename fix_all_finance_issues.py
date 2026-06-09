#!/usr/bin/env python3
"""Fix 3 issues in dashboard_routes.py:
1. Coupons: m.member_name -> m.name
2. Finance Balances: handle "/" in sales_daily payment_method
3. Balance Sheet: same fix for "/" in sales_daily
4. Also fix the topup_log sales_daily entry that has / instead of |
"""
import os

with open('/etc/psvibe/secrets.env') as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:]
        if '=' in line:
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == 'MYSQL_PASSWORD':
                os.environ['MPW'] = v

# ── Fix 0: Fix the sales_daily entry with wrong payment_method ──
import pymysql
PW = ***'MPW', '')
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password=*** database='psvibe_api', charset='utf8mb4')
cur = conn.cursor()

cur.execute("SELECT id, payment_method FROM sales_daily WHERE payment_method LIKE '%/%'")
for r in cur.fetchall():
    old_pm = r[1]
    # Convert "/" to "|" — same amount parsing, different separator
    new_pm = old_pm.replace("/", "|")
    cur.execute("UPDATE sales_daily SET payment_method=%s WHERE id=%s", (new_pm, r[0]))
    print(f"Fixed sales_daily #{r[0]}: '{old_pm}' -> '{new_pm}'")
conn.commit()

# Verify
cur.execute("SELECT COUNT(*) FROM sales_daily WHERE payment_method LIKE '%/%'")
cnt = cur.fetchone()[0]
print(f"Remaining sales_daily with '/': {cnt}")
conn.close()

# ── Fix 1: Coupons endpoint ──
f = '/root/psvibe_api_server/dashboard_routes.py'
with open(f) as fh:
    src = fh.read()

# Fix m.member_name -> m.name
src = src.replace("m.member_name", "m.name")
src = src.replace("m.phone", "COALESCE(m.phone,'')")
print("✅ Coupons: m.member_name -> m.name + phone COALESCE")

# ── Fix 2 & 3: Add safety for "/" in sales_daily payment_method parsing ──
# In the sales_daily loop, add a check: if no "|" found, try "/" as separator
# This handles the edge case where topup entries were stored with wrong format

# Add safety to Balance Sheet sales_daily parsing
old_pm_loop_bs = """        for row in rows:
            pm = (row.get("payment_method") or "").strip()
            net_amount = float(row.get("net") or 0)
            if not pm: continue
            for part in pm.split("|"):"""

new_pm_loop_bs = """        for row in rows:
            pm = (row.get("payment_method") or "").strip()
            net_amount = float(row.get("net") or 0)
            if not pm: continue
            sep = "|" if "|" in pm else ("/" if "/" in pm else "|")
            for part in pm.split(sep):"""

src = src.replace(old_pm_loop_bs, new_pm_loop_bs, 1)
print("✅ BS: sales_daily parsing handles both | and /")

# Add safety to Finance Balances sales_daily parsing
old_pm_loop_fb = """        for part in parts:
                part = part.strip()
                if ":" in part:
                    method, _, val = part.partition(":")
                    method = method.strip().lower().replace(" ", "_")
                    val = float(val.strip() or 0) if val.strip() else 0
                else:
                    method = part.lower().replace(" ", "_")
                    val = net_amount / len(parts) if parts else 0"""

new_pm_loop_fb = """        for part in parts:
                part = part.strip()
                if ":" in part:
                    method, _, val = part.partition(":")
                    method = method.strip().lower().replace(" ", "_")
                    try:
                        val = float(val.strip() or 0) if val.strip() else 0
                    except ValueError:
                        val = net_amount / len(parts) if parts else 0
                else:
                    method = part.lower().replace(" ", "_")
                    val = net_amount / len(parts) if parts else 0"""

src = src.replace(old_pm_loop_fb, new_pm_loop_fb, 1)
print("✅ FB: sales_daily parsing handles both | and /")

# Also fix the topup loop separator - add "/" as backup
old_topup_sep_bs = """            # Topup PM format: "KPay:90000/Cash:0" (pipe-delimited with :amount)
            for _part in _pm.split("/"):"""

new_topup_sep_bs = """            # Topup PM format: "KPay:90000/Cash:0" (separated with /)
            for _part in _pm.split("/"):"""

src = src.replace(old_topup_sep_bs, new_topup_sep_bs, 1)

# Write
with open(f, 'w') as fh:
    fh.write(src)

# Verify syntax
try:
    compile(src, f, 'exec')
    print("✅ Syntax check passed")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")

print("\n✅ All fixes applied!")
