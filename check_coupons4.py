#!/usr/bin/env python3
"""Check coupon tables directly."""
import os, json

with open('/etc/psvibe/secrets.env') as f:
    envlines = f.readlines()

api_key, db_pass = '', ''
for line in envlines:
    line = line.strip()
    if line.startswith('export '):
        line = line[7:]
    if '=' in line:
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k == 'API_KEY': api_key = v
        elif k == 'MYSQL_PASSWORD': db_pass = v

import pymysql
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password=db_pass, database='psvibe_api', charset='utf8mb4')
cur = conn.cursor()

# Check coupon tables
for t in ['member_coupons', 'promotions', 'promotions_log']:
    try:
        cur.execute(f"DESCRIBE `{t}`")
        cols = [r for r in cur.fetchall()]
        print(f"\n=== {t} ===")
        for c in cols:
            print(f"  {c[0]} ({c[1]})")
        cur.execute(f"SELECT COUNT(*) FROM `{t}`")
        cnt = cur.fetchone()[0]
        print(f"  Total: {cnt} rows")
        if cnt > 0:
            cur.execute(f"SELECT * FROM `{t}` LIMIT 20")
            for r in cur.fetchall():
                print(f"  {r}")
    except Exception as e:
        print(f"\n❌ {t}: {e}")

# Also check bot code for coupon reference
import urllib.request
headers = {'X-API-Key': api_key}
print(f"\n=== Checking Bot Coupon Code ===")
req = urllib.request.Request('http://localhost:8000/api/coupons/list', headers=headers)
try:
    res = json.load(urllib.request.urlopen(req, timeout=3))
    print(f"coupons/list: {json.dumps(res, indent=2)[:300]}")
except Exception as e:
    print(f"coupons/list: {e}")

req2 = urllib.request.Request('http://localhost:8000/api/fetch_member_coupons', headers=headers)
try:
    res = json.load(urllib.request.urlopen(req2, timeout=3))
    print(f"fetch_member_coupons: {json.dumps(res, indent=2)[:300]}")
except Exception as e:
    print(f"fetch_member_coupons: {e}")

# Check bot coupons reference in __init__.py
req3 = urllib.request.Request('http://localhost:8000/api/search-coupons', headers=headers)
try:
    res = json.load(urllib.request.urlopen(req3, timeout=3))
    print(f"search-coupons: {json.dumps(res, indent=2)[:300]}")
except Exception as e:
    print(f"search-coupons: {e}")
