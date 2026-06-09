#!/usr/bin/env python3
"""Debug exact parsing paths in dashboard_routes.py for float error."""
import os, sys, json, traceback

# Get password
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
            elif k == 'API_KEY':
                os.environ['API_KEY'] = v

PW = ***'MPW', '')
KEY = ***'API_KEY', '')

import pymysql, urllib.request, json

# Test 1: Read dashboard_routes.py and find ALL float conversion points
print("=== Scanning dashboard_routes.py for float( ===")
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    for i, line in enumerate(f, 1):
        if 'float(' in line and ('payment_method' in line.lower() or 'pm ' in line.lower() or '_val' in line.lower() or 'part' in line.lower() or '_pm' in line.lower() or '_part' in line.lower()):
            print(f"  L{i}: {line.strip()[:120]}")

# Test 2: Try to login and call each endpoint with full traceback
print("\n=== Testing endpoints with traceback ===")
login = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request('http://localhost:8000/auth/login', data=login, headers={'Content-Type':'application/json'})
res = json.load(urllib.request.urlopen(req, timeout=5))
token = res.get('access_token','')
print(f"Token: {token[:30]}...")

# Call balance sheet with details
req_bs = urllib.request.Request('http://localhost:8000/api/dashboard/financial/balance-sheet', headers={'Authorization': f'Bearer {token}'})
try:
    res_bs = json.load(urllib.request.urlopen(req_bs, timeout=30))
    print("BS:", res_bs.get('success'))
    if not res_bs.get('success'):
        print("ERR:", res_bs.get('error',''))
except Exception as e:
    print(f"BS error: {e}")

# Call finance/balances with details
req_fb = urllib.request.Request('http://localhost:8000/api/dashboard/finance/balances', headers={'Authorization': f'Bearer {token}'})
try:
    res_fb = json.load(urllib.request.urlopen(req_fb, timeout=30))
    print("FB:", res_fb.get('success'))
    if not res_fb.get('success'):
        print("ERR:", res_fb.get('error',''))
except Exception as e:
    print(f"FB error: {e}")
