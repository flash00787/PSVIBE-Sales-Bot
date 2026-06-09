#!/usr/bin/env python3
"""Check coupons database and API endpoints."""
import os, json

env_file = '/etc/psvibe/secrets.env'
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:]
        if '=' in line:
            k, _, v = line.partition('=')
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                os.environ.setdefault(k, v)

import pymysql, urllib.request
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password='PsVib…d!', database='psvibe_api')
cur = conn.cursor()

# Check all tables for coupons
cur.execute("SHOW TABLES")
tables = [r[0] for r in cur.fetchall()]
print("=== Tables ===")
coupon_tables = [t for t in tables if 'coupon' in t.lower() or 'voucher' in t.lower() or 'promo' in t.lower()]
print(f"Coupon-related tables: {coupon_tables}")
print(f"All tables: {tables}")

# Check coupon table content
for t in tables:
    cur.execute(f"DESCRIBE `{t}`")
    cols = [r[0] for r in cur.fetchall()]
    if any(c in cols for c in ['code', 'coupon', 'voucher', 'discount', 'promo']):
        cur.execute(f"SELECT COUNT(*) FROM `{t}`")
        cnt = cur.fetchone()[0]
        print(f"\n{t}: {cnt} rows")
        if cnt > 0:
            cur.execute(f"SELECT * FROM `{t}` LIMIT 5")
            for r in cur.fetchall():
                print(f"  {r}")

# Check API coupon endpoints
KEY = ***'API_KEY', '')
try:
    req = urllib.request.Request('http://localhost:8000/api/fetch_coupons', headers={'X-API-Key': KEY})
    res = json.load(urllib.request.urlopen(req, timeout=5))
    print(f"\nAPI /api/fetch_coupons:\n{json.dumps(res, indent=2)[:500]}")
except Exception as e:
    print(f"\nAPI /api/fetch_coupons error: {e}")

# Check if coupons were in GSheet pre-migration
try:
    req = urllib.request.Request('http://localhost:8000/api/fetch_coupon', headers={'X-API-Key': KEY})
    res = json.load(urllib.request.urlopen(req, timeout=5))
    print(f"\nAPI /api/fetch_coupon:\n{json.dumps(res, indent=2)[:500]}")
except Exception as e:
    print(f"\nAPI /api/fetch_coupon error: {e}")
