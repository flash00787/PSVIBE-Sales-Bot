#!/usr/bin/env python3
"""Test coupon API endpoints."""
import os, json

with open('/etc/psvibe/secrets.env') as f:
    envlines = f.readlines()

api_key = ''
for line in envlines:
    line = line.strip()
    if line.startswith('export '):
        line = line[7:]
    if '=' in line:
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k == 'API_KEY':
            api_key = v
            break

import urllib.request
headers = {'X-API-Key': api_key}

# Test 1: coupons/list with valid member_id
for mid in ['PSV_A_002', '0 (Guest)', '']:
    url = f'http://localhost:8000/api/coupons/list?member_id={mid}'
    try:
        req = urllib.request.Request(url, headers=headers)
        res = json.load(urllib.request.urlopen(req, timeout=3))
        cnt = len(res.get('data',{}).get('coupons',[]))
        print(f"coupons/list?member_id={mid}: {cnt} coupons")
    except Exception as e:
        print(f"coupons/list?member_id={mid}: {type(e).__name__}: {str(e)[:100]}")

# Test 2: promotions/active
try:
    req = urllib.request.Request('http://localhost:8000/api/promotions/active', headers=headers)
    res = json.load(urllib.request.urlopen(req, timeout=3))
    print(f"\npromotions/active: {json.dumps(res, indent=2)[:200]}")
except Exception as e:
    print(f"\npromotions/active: {e}")

# Test 3: Coupon validate with a real coupon code
try:
    req = urllib.request.Request('http://localhost:8000/api/coupons/validate',
        data=json.dumps({"code": "CBGBY5VT"}).encode(),
        headers={**headers, 'Content-Type': 'application/json'})
    res = json.load(urllib.request.urlopen(req, timeout=3))
    print(f"\ncoupons/validate CBGBY5VT: {json.dumps(res, indent=2)[:200]}")
except Exception as e:
    print(f"\ncoupons/validate: {e}")

# Test 4: fetch_promotions_cached
try:
    req = urllib.request.Request('http://localhost:8000/api/fetch_promotions_cached', headers=headers)
    res = json.load(urllib.request.urlopen(req, timeout=3))
    print(f"\nfetch_promotions_cached: {json.dumps(res, indent=2)[:200]}")
except Exception as e:
    print(f"\nfetch_promotions_cached: {e}")
