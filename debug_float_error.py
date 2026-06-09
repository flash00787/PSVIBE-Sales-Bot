#!/usr/bin/env python3
"""Debug the float conversion error - run Balance Sheet with full traceback."""
import os, json, traceback

with open('/etc/psvibe/secrets.env') as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:]
        if '=' in line:
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == 'MYSQL_PASSWORD':
                os.environ['MYSQL_PW'] = v

# Replicate the balance sheet parsing
import pymysql
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password=*** database='psvibe_api', charset='utf8mb4')
cur = conn.cursor()

# 1. Test topup_log parsing
print("=== Topup Log Parsing ===")
cur.execute("SELECT payment_method, amount FROM topup_log WHERE amount > 0 AND payment_method IS NOT NULL")
for _tr in cur.fetchall():
    _pm = (_tr[0] or "").strip()
    _amt = float(_tr[1] or 0)
    print(f"PM='{_pm}', amount={_amt}")
    if not _pm or _amt <= 0:
        continue
    for _part in _pm.split("/"):
        _part = _part.strip()
        print(f"  Part='{_part}'")
        if ":" in _part:
            _method, _, _val = _part.partition(":")
            _method = _method.strip().lower().replace(" ", "_")
            print(f"    method={_method}, val_str='{_val.strip()}'")
            _val_f = float(_val.strip() or 0) if _val.strip() else 0
            print(f"    parsed_val={_val_f}")
        else:
            _method = _part.lower().replace(" ", "_")
            print(f"    method={_method}, amt={_amt}")

# 2. Check sales_daily parsing (pipe-delimited)
print("\n=== Sales Daily Parsing ===")
cur.execute("SELECT payment_method, net FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != '' LIMIT 3")
for row in cur.fetchall():
    pm = (row[0] or "").strip()
    net = float(row[1] or 0)
    print(f"PM='{pm}', net={net}")
    if not pm: continue
    for part in pm.split("|"):
        part = part.strip()
        print(f"  Part='{part}'")
        if ":" in part:
            method, _, val = part.partition(":")
            method = method.strip().lower().replace(" ", "_")
            val_f = float(val.strip() or 0) if val.strip() else 0
            print(f"    method={method}, val={val_f}")
        else:
            print(f"    raw={part}")

# 3. Check opex parsing
print("\n=== OPEX Parsing ===")
cur.execute("SELECT payment_method, COALESCE(SUM(amount),0) FROM opex GROUP BY payment_method LIMIT 3")
for row in cur.fetchall():
    pm = (row[0] or "").strip().lower().replace(" ", "_")
    amt = float(row[1] or 0)
    print(f"PM='{pm}', amount={amt}")

# 4. Check stock_in payment_method parsing (composite payments with /)
print("\n=== Stock In Parsing ===")
cur.execute("SELECT payment_method FROM stock_in WHERE payment_method LIKE '%/%'")
for row in cur.fetchall():
    print(f"Composite PM: '{row[0]}'")
if cur.rowcount == 0:
    print("  (none found)")

conn.close()
print("\n✅ No float conversion errors found in parsing")
