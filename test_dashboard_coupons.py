#!/usr/bin/env python3
"""Test new dashboard coupons endpoint."""
import os, json

with open('/etc/psvibe/secrets.env') as f:
    for line in f:
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

for ep in ['/api/dashboard/coupons', '/api/dashboard/promotions', '/api/dashboard/stats']:
    url = f'http://localhost:8000{ep}'
    try:
        req = urllib.request.Request(url, headers=headers)
        res = json.load(urllib.request.urlopen(req, timeout=5))
        if isinstance(res, dict):
            s = res.get('success', False)
            d = res.get('data', [])
            t = res.get('total', len(d) if isinstance(d, list) else 'N/A')
            print(f"✅ {ep}: success={s} | total={t} | data_len={len(d) if isinstance(d, list) else 'dict'}")
        else:
            print(f"✅ {ep}: {str(res)[:100]}")
    except Exception as e:
        print(f"❌ {ep}: {type(e).__name__}: {str(e)[:100]}")
