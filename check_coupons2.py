#!/usr/bin/env python3
"""Check coupons - no env dependency, direct MySQL."""
import os, json, re

# Read API key from env file directly
with open('/etc/psvibe/secrets.env') as f:
    env = f.read()
api_key = ''
for line in env.split('\n'):
    line = line.strip()
    if line.startswith('export API_KEY='):
        api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
        break

import pymysql, urllib.request
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password='PsVib…d!', database='psvibe_api')
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
                cur.execute(f"SELECT * FROM `{t}` LIMIT 3")
                for r in cur.fetchall():
                    print(f"  {r}")
    except Exception as e:
        print(f"\n{e}")

# Try API endpoints
headers = {'X-API-Key': api_key}
for ep in ['/api/fetch_coupons', '/api/coupons', '/api/coupon', '/api/promo']:
    try:
        req = urllib.request.Request(f'http://localhost:8000{ep}', headers=headers)
        res = json.load(urllib.request.urlopen(req, timeout=3))
        print(f"\n{ep}: {json.dumps(res, indent=2)[:300]}")
    except Exception as e:
        print(f"\n{ep}: {type(e).__name__}: {e}")

# Check if coupons were stored in bot memory
import pathlib
bot_py = pathlib.Path('/root/psvibe-sales-bot/bot/__init__.py')
if bot_py.exists():
    text = bot_py.read_text()
    # Look for coupon-related code
    coupon_lines = [(i+1, l) for i,l in enumerate(text.split('\n')) if 'coupon' in l.lower()]
    print(f"\n=== Coupon refs in bot/__init__.py ({len(coupon_lines)}) ===")
    for ln, line in coupon_lines[:20]:
        print(f"  L{ln}: {line.strip()[:120]}")
