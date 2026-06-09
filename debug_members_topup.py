#!/usr/bin/env python3
"""Fix coupons table query and balance sheet parsing issues."""
import os, json

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

import pymysql

conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password=*** database='psvibe_api', charset='utf8mb4')
cur = conn.cursor()

# 1. Check members table columns
cur.execute("DESCRIBE members")
print("=== members columns ===")
cols = [r[0] for r in cur.fetchall()]
print(cols)

# 2. Check if name column exists
name_col = None
for c in cols:
    if c in ('member_name', 'name', 'full_name', 'customer_name', 'memberName'):
        name_col = c
        break
print(f"Name column: {name_col}")

# 3. Check member data sample
if name_col:
    cur.execute(f"SELECT member_id, `{name_col}`, phone FROM members LIMIT 5")
    print("\n=== member data ===")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]} | {r[2]}")
else:
    cur.execute("SELECT * FROM members LIMIT 3")
    print("\n=== member data (all cols) ===")
    for r in cur.fetchall():
        print(f"  {r}")

# 4. Check topup_log sample
cur.execute("SELECT id, member_id, payment_method, amount FROM topup_log LIMIT 5")
print(f"\n=== topup_log sample ===")
for r in cur.fetchall():
    print(f"  #{r[0]}: {r[1]} | pm={r[2]} | amount={r[3]}")

# 5. Test the balance sheet issue - check what query returns
cur.execute("""
    SELECT tl.member_id, tl.amount, tl.mins_added, mw.balance_mins
    FROM topup_log tl
    LEFT JOIN member_wallets mw ON tl.member_id = mw.member_id
    WHERE tl.member_id IS NOT NULL AND tl.member_id != ''
    ORDER BY tl.id
""")
print(f"\n=== topup_log + wallets ===")
for r in cur.fetchall():
    print(f"  {r[0]}: amount={r[1]} | mins={r[2]} | wallet_balance={r[3]}")

conn.close()
