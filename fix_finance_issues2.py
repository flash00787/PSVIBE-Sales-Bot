#!/usr/bin/env python3
"""Fix finance issues - read env directly, no os.environ.get."""
import sys

# Read password from file directly
mpw = ''
with open('/etc/psvibe/secrets.env') as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:]
        if '=' in line:
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == 'MYSQL_PASSWORD':
                mpw = v
                break

# ── Fix 0: Fix sales_daily entries with wrong payment_method ──
import pymysql
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password=mpw, database='psvibe_api', charset='utf8mb4')
cur = conn.cursor()

cur.execute("SELECT id, payment_method FROM sales_daily WHERE payment_method LIKE '%/%'")
for r in cur.fetchall():
    old_pm = r[1]
    new_pm = old_pm.replace("/", "|")
    cur.execute("UPDATE sales_daily SET payment_method=%s WHERE id=%s", (new_pm, r[0]))
    print(f"Fixed sales_daily #{r[0]}: '{old_pm}' -> '{new_pm}'")
conn.commit()

cur.execute("SELECT COUNT(*) FROM sales_daily WHERE payment_method LIKE '%/%'")
cnt = cur.fetchone()[0]
print(f"Remaining sales_daily with '/': {cnt}")
conn.close()

# ── Fix 1: Coupons endpoint ──
f = '/root/psvibe_api_server/dashboard_routes.py'
with open(f) as fh:
    src = fh.read()

src = src.replace("m.member_name", "m.name")
src = src.replace("m.phone", "COALESCE(m.phone,'')")
print("Coupons: m.member_name -> m.name + phone COALESCE")

# ── Fix 2: Balance Sheet sales_daily parsing edge case ──
old_bs = """        for row in rows:
            pm = (row.get("payment_method") or "").strip()
            net_amount = float(row.get("net") or 0)
            if not pm: continue
            for part in pm.split("|"):"""

new_bs = """        for row in rows:
            pm = (row.get("payment_method") or "").strip()
            net_amount = float(row.get("net") or 0)
            if not pm: continue
            sep = "|" if "|" in pm else ("/" if "/" in pm else "|")
            for part in pm.split(sep):"""

src = src.replace(old_bs, new_bs, 1)
print("BS: sales_daily parsing handles both | and /")

# ── Fix 3: Finance Balances sales_daily parsing edge case ──
old_fb = """        for part in parts:
                part = part.strip()
                if ":" in part:
                    method, _, val = part.partition(":")
                    method = method.strip().lower().replace(" ", "_")
                    val = float(val.strip() or 0) if val.strip() else 0
                else:
                    method = part.lower().replace(" ", "_")
                    val = net_amount / len(parts) if parts else 0"""

new_fb = """        for part in parts:
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

src = src.replace(old_fb, new_fb, 1)
print("FB: sales_daily parsing added try/except for float")

# ── Write ──
with open(f, 'w') as fh:
    fh.write(src)

# Verify syntax
try:
    compile(src, f, 'exec')
    print("Syntax check passed")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    sys.exit(1)

print("All fixes applied!")
