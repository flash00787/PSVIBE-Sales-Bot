#!/usr/bin/env python3
"""Check coupons - direct MySQL with correct password."""
import os, json

# Read env from VPS
with open('/etc/psvibe/secrets.env') as f:
    envlines = f.readlines()

api_key = ''
db_pass = ''
for line in envlines:
    line = line.strip()
    if line.startswith('export '):
        line = line[7:]
    if '=' in line:
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k == 'API_KEY':
            api_key = v
        elif k == 'MYSQL_PASSWORD':
            db_pass = v

import pymysql, urllib.request
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password=db_pass, database='psvibe_api', charset='utf8mb4')
cur = conn.cursor()

# Show all tables
cur.execute("SHOW TABLES")
tables = [r[0] for r in cur.fetchall()]
print(f"All tables ({len(tables)}): {tables}")

# Search for coupon-related content across all tables
for t in tables:
    try:
        cur.execute(f"DESCRIBE `{t}`")
        cols = [r[0] for r in cur.fetchall()]
        if any(c in cols for c in ['code', 'coupon', 'voucher', 'promo', 'discount']):
            cur.execute(f"SELECT COUNT(*) FROM `{t}`")
            cnt = cur.fetchone()[0]
            print(f"\n✅ {t}: {cnt} rows (has coupon fields)")
            if cnt > 0:
                cur.execute(f"SELECT * FROM `{t}` LIMIT 5")
                for r in cur.fetchall():
                    print(f"  {r}")
    except Exception as e:
        print(f"\n❌ {t}: {e}")

# Try API endpoints
headers = {'X-API-Key': api_key}
for ep in ['/api/fetch_coupons', '/api/coupons', '/api/coupon', '/api/promo']:
    try:
        req = urllib.request.Request(f'http://localhost:8000{ep}', headers=headers)
        res = json.load(urllib.request.urlopen(req, timeout=3))
        print(f"\n{ep}: {json.dumps(res, indent=2)[:300]}")
    except Exception as e:
        print(f"\n{ep}: {type(e).__name__}: {e}")
