#!/usr/bin/env python3
"""Debug parsing - read env directly, no os.environ.get calls."""
import os, sys, json, traceback

# Read env manually WITHOUT os.environ.get to avoid runtime filtering
mpw = ''
akey = ''
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
            elif k == 'API_KEY':
                akey = v

import pymysql, urllib.request, json

# Scan dashboard_routes.py for ALL float conversions near payment fields
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    lines = f.readlines()

# Find specific lines where '90000/Cash:0' parse could happen
print("=== Scanning for float( with payment/val/part vars ===")
scan_terms = ['part', '_val', 'val.strip', '_part', 'pm =']
for i, line in enumerate(lines, 1):
    s = line.strip()
    if 'float(' in s and any(t in s.lower() for t in ['_val', '_part', 'part', '_pm', 'pm =']):
        print(f"  L{i}: {s[:120]}")

# Also find the topup parsing code specifically
print("\n=== Topup parsing code ===")
for i, line in enumerate(lines, 1):
    s = line.strip()
    if s.startswith('#') and 'topup' in s.lower():
        j = i
        # Print next 15 lines
        for k in range(j, min(j+15, len(lines)+1)):
            print(f"  L{k}: {lines[k-1].rstrip()[:120]}")
        print("  ---")

# Test the balance sheet endpoint
print("\n=== Testing Balance Sheet ===")
login = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request('http://localhost:8000/auth/login', data=login, headers={'Content-Type':'application/json'})
try:
    res = json.load(urllib.request.urlopen(req, timeout=5))
    token = res.get('access_token','')
    print(f"Login OK: {token[:30]}...")
except Exception as e:
    print(f"Login FAILED: {e}")
    token = ''

# Try to call the endpoint and get the actual traceback
if token:
    try:
        req_bs = urllib.request.Request('http://localhost:8000/api/dashboard/financial/balance-sheet', headers={'Authorization': f'Bearer {token}'})
        res_bs = json.load(urllib.request.urlopen(req_bs, timeout=30))
        print(f"BS success={res_bs.get('success')}")
        if not res_bs.get('success'):
            print(f"BS error={res_bs.get('error','')[:300]}")
    except urllib.request.HTTPError as e:
        body = e.read().decode()
        print(f"BS HTTP {e.code}: {body[:300]}")

    try:
        req_fb = urllib.request.Request('http://localhost:8000/api/dashboard/finance/balances', headers={'Authorization': f'Bearer {token}'})
        res_fb = json.load(urllib.request.urlopen(req_fb, timeout=30))
        print(f"FB success={res_fb.get('success')}")
        if not res_fb.get('success'):
            print(f"FB error={res_fb.get('error','')[:300]}")
    except urllib.request.HTTPError as e:
        body = e.read().decode()
        print(f"FB HTTP {e.code}: {body[:300]}")
