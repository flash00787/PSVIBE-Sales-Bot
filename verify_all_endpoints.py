#!/usr/bin/env python3
"""Verify all Web Finance endpoints after fixes."""
import json, urllib.request

# Login
login = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request('http://localhost:8000/auth/login', data=login, headers={'Content-Type':'application/json'})
res = json.load(urllib.request.urlopen(req, timeout=5))
token = res.get('access_token','')
auth = {'Authorization': f'Bearer {token}'}

# Test ALL endpoints
endpoints = [
    ('Dashboard Stats', '/api/dashboard/stats'),
    ('Dashboard Consoles', '/api/dashboard/consoles'),
    ('Dashboard Coupons', '/api/dashboard/coupons?limit=10'),
    ('Dashboard Promotions', '/api/dashboard/promotions'),
    ('P&L', '/api/dashboard/financial/pnl'),
    ('Balance Sheet', '/api/dashboard/financial/balance-sheet'),
    ('Cash Flow', '/api/dashboard/financial/cashflow'),
    ('Finance Balances', '/api/dashboard/finance/balances'),
    ('Inventory', '/api/dashboard/inventory'),
    ('Stock In', '/api/dashboard/stock-in?limit=3'),
    ('Stock Out', '/api/dashboard/stock-out?limit=3'),
    ('OPEX', '/api/dashboard/opex'),
    ('Assets', '/api/dashboard/assets'),
    ('Topups', '/api/dashboard/topups?limit=3'),
    ('Members', '/api/dashboard/members?limit=3'),
    ('Bookings', '/api/dashboard/bookings?limit=3'),
    ('Schedule', '/api/dashboard/schedule'),
    ('Revenue Trend', '/api/dashboard/revenue-trend?days=7'),
    ('Financial Report', '/api/dashboard/financial-report'),
]

success, fail = 0, 0
print("=== Web Finance Verification ===")
for name, ep in endpoints:
    try:
        req = urllib.request.Request(f'http://localhost:8000{ep}', headers=auth)
        res = json.load(urllib.request.urlopen(req, timeout=15))
        s = res.get('success', False)
        d = res.get('data', {})
        if isinstance(d, list):
            info = f" ({len(d)} items)"
        elif isinstance(d, dict):
            info = f" (keys: {list(d.keys())[:5]})"
        else:
            info = ""
        if s:
            success += 1
            print(f"  ✅ {name}{info}")
        else:
            fail += 1
            print(f"  ❌ {name}: success=False | error={str(res.get('error',''))[:100]}")
    except Exception as e:
        fail += 1
        print(f"  ❌ {name}: {type(e).__name__}: {str(e)[:120]}")

# Show Balance Sheet details
print("\n=== Balance Sheet Detail ===")
req_bs = urllib.request.Request('http://localhost:8000/api/dashboard/financial/balance-sheet', headers=auth)
res_bs = json.load(urllib.request.urlopen(req_bs, timeout=15))
if res_bs.get('success'):
    d = res_bs.get('data', {})
    print(f"Assets: {d.get('total_current_assets','?')} + {d.get('total_fixed_assets','?')}")
    print(f"Liabilities: {d.get('liabilities',{}).get('member_liability','?')}")
    md = d.get('liabilities',{}).get('member_details',[])
    if md:
        print("  Member breakdown:")
        for m in md:
            print(f"    {m.get('member_id','?')}: {m.get('liability',0)} Ks ({m.get('balance_mins',0)} mins)")
    print(f"Equity retained: {d.get('equity',{}).get('retained','?')}")
    print(f"Diff (A - L - E): {d.get('diff','?')}")
    print(f"Total A = L+E: {d.get('total_liabilities_equity','?')}")

# Show P&L
print("\n=== P&L Detail ===")
req_pnl = urllib.request.Request('http://localhost:8000/api/dashboard/financial/pnl', headers=auth)
res_pnl = json.load(urllib.request.urlopen(req_pnl, timeout=15))
if res_pnl.get('success'):
    d = res_pnl.get('data', {})
    rev = d.get('revenue', {})
    print(f"Total Revenue: {rev.get('total_revenue','?')}")
    print(f"  Game Rev: {rev.get('game_revenue','?')}")
    print(f"  Food Rev: {rev.get('food_revenue','?')}")
    print(f"  Wallet Consumed: {rev.get('wallet_consumed','?')}")
    print(f"  Topup Deferred: {rev.get('topup_deferred','?')}")
    print(f"COGS: {d.get('cogs','?')}")
    print(f"Gross Profit: {d.get('gross_profit','?')}")
    print(f"Net Profit: {d.get('net_profit','?')}")

# Show Account Balances
print("\n=== Account Balances ===")
req_fb = urllib.request.Request('http://localhost:8000/api/dashboard/finance/balances', headers=auth)
res_fb = json.load(urllib.request.urlopen(req_fb, timeout=15))
if res_fb.get('success'):
    for a in res_fb.get('data', []):
        print(f"  {a.get('label','?')}: {a.get('balance',0)} Ks")

# Show Coupons
print("\n=== Coupons ===")
req_cp = urllib.request.Request('http://localhost:8000/api/dashboard/coupons?limit=5', headers=auth)
res_cp = json.load(urllib.request.urlopen(req_cp, timeout=15))
if res_cp.get('success'):
    print(f"Total: {res_cp.get('total',0)}")
    for c in res_cp.get('data', [])[:5]:
        print(f"  {c.get('code','?')}: {c.get('member_id','?')} | {c.get('balance_minutes',0)}/{c.get('original_minutes',0)} mins | {c.get('status','?')}")

print(f"\n{'='*50}")
print(f"✅ {success} passed | ❌ {fail} failed")
