#!/usr/bin/env python3
"""Full Web Finance verification - login + check all endpoints."""
import os, json, urllib.request

# Read env
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

# Step 1: Login to get JWT token
try:
    login_data = json.dumps({"username": "admin", "password": "admin123"}).encode()
    req = urllib.request.Request('http://localhost:8000/auth/login',
        data=login_data,
        headers={'Content-Type': 'application/json'})
    res = json.load(urllib.request.urlopen(req, timeout=5))
    token = res.get('access_token', '')
    print(f"✅ Login OK: access_token={token[:30]}...")
except Exception as e:
    print(f"❌ Login failed: {e}")
    token = ''

if not token:
    print("Cannot proceed without token")
    exit(1)

auth_hdr = {'Authorization': f'Bearer {token}'}

# Step 2: Check all financial endpoints
endpoints = {
    'Dashboard Stats': '/api/dashboard/stats',
    'Dashboard Consoles': '/api/dashboard/consoles',
    'Dashboard Schedule': '/api/dashboard/schedule',
    'Dashboard Revenue Trend': '/api/dashboard/revenue-trend?days=7',
    'Dashboard Bookings': '/api/dashboard/bookings?limit=5',
    'Dashboard Members': '/api/dashboard/members?limit=5',
    'Dashboard Inventory': '/api/dashboard/inventory',
    'Dashboard Topups': '/api/dashboard/topups?limit=5',
    'Dashboard Coupons': '/api/dashboard/coupons?limit=15',
    'Dashboard Promotions': '/api/dashboard/promotions',
    'Dashboard P&L': '/api/dashboard/financial/pnl',
    'Dashboard Balance Sheet': '/api/dashboard/financial/balance-sheet',
    'Dashboard Cash Flow': '/api/dashboard/financial/cashflow',
    'Dashboard Finance Balances': '/api/dashboard/finance/balances',
    'Dashboard Financial Report': '/api/dashboard/financial-report',
    'Dashboard OPEX': '/api/dashboard/opex',
    'Dashboard Stock In': '/api/dashboard/stock-in?limit=5',
    'Dashboard Stock Out': '/api/dashboard/stock-out?limit=5',
    'Dashboard Account Balances': '/api/dashboard/finance/balances',
}

results = {}
for name, ep in endpoints.items():
    url = f'http://localhost:8000{ep}'
    try:
        req = urllib.request.Request(url, headers=auth_hdr)
        res = json.load(urllib.request.urlopen(req, timeout=10))
        success = res.get('success', False)
        data = res.get('data', 'N/A')
        error = res.get('error', '')
        total = res.get('total', len(data) if isinstance(data, list) else None)
        results[name] = {'status': '✅' if success else '⚠️', 'success': success, 'total': total, 'data': data, 'error': error}
    except urllib.request.HTTPError as e:
        body = e.read().decode()[:200]
        results[name] = {'status': '❌', 'error': f'HTTP {e.code}', 'body': body}
    except Exception as e:
        results[name] = {'status': '❌', 'error': str(e)[:200]}

# Print summary
print(f"\n{'='*60}")
print(f"WEB FINANCE VERIFICATION REPORT")
print(f"{'='*60}")
for name, r in results.items():
    status = r['status']
    if status == '✅':
        total_str = f" | total={r['total']}" if r.get('total') is not None else ""
        data_len = len(r['data']) if isinstance(r.get('data'), list) else (len(str(r.get('data',''))[:50]))
        print(f"  {status} {name}: OK{total_str}")
    elif status == '⚠️':
        print(f"  {status} {name}: success=False | error={r.get('error','')[:80]}")
    else:
        print(f"  {status} {name}: {r.get('error','')} | {r.get('body','')[:120]}")

# Step 3: Show financial data details
print(f"\n{'='*60}")
print(f"FINANCIAL DATA SUMMARY")
print(f"{'='*60}")

# P&L detail
pnl = results.get('Dashboard P&L', {})
if pnl.get('status') == '✅':
    data = pnl.get('data', {})
    if isinstance(data, dict):
        print(f"\n📊 P&L:")
        for k, v in data.items():
            if not k.startswith('_'):
                print(f"  {k}: {v}")

# Balance Sheet detail
bs = results.get('Dashboard Balance Sheet', {})
if bs.get('status') == '✅':
    data = bs.get('data', {})
    if isinstance(data, dict):
        print(f"\n📊 Balance Sheet:")
        for section in ['assets', 'liabilities', 'equity']:
            vals = data.get(section, {})
            if isinstance(vals, dict):
                print(f"  {section}:")
                for k, v in vals.items():
                    if k == 'member_details' and isinstance(v, list):
                        for md in v:
                            print(f"    - {md.get('member_id','?')}: {md.get('liability',0)} Ks ({md.get('balance_mins',0)} mins @ {md.get('rate_per_min',0)} Ks/min)")
                    else:
                        print(f"    {k}: {v}")

# Cash Flow detail
cf = results.get('Dashboard Cash Flow', {})
if cf.get('status') == '✅':
    data = cf.get('data', {})
    if isinstance(data, dict):
        print(f"\n📊 Cash Flow:")
        for k, v in data.items():
            print(f"  {k}: {v}")

# Account Balances
ab = results.get('Dashboard Account Balances', {})
if ab.get('status') == '✅':
    data = ab.get('data', [])
    if isinstance(data, list):
        print(f"\n💰 Account Balances:")
        for a in data:
            print(f"  {a.get('account','?')}: {a.get('balance',0)} Ks")

# Coupons detail
cp = results.get('Dashboard Coupons', {})
if cp.get('status') == '✅':
    data = cp.get('data', [])
    if isinstance(data, list):
        print(f"\n🎫 Coupons ({len(data)}):")
        active = [c for c in data if c.get('status') == 'active']
        used = [c for c in data if c.get('status') == 'used']
        print(f"  Active: {len(active)} | Used: {len(used)}")
        for c in data[:5]:
            print(f"  {c.get('code','?')}: {c.get('member_id','?')} | {c.get('balance_minutes',0)}/{c.get('original_minutes',0)} mins | {c.get('status','?')}")

print(f"\n{'='*60}")
print(f"VERIFICATION COMPLETE")
print(f"{'='*60}")
