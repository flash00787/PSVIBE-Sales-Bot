#!/usr/bin/env python3
"""Verify P&L and Balance Sheet now include topup income."""
import os, json, urllib.request

key = ""
base = "http://localhost:8000"
with open("/etc/psvibe/secrets.env") as f:
    for line in f:
        line = line.strip()
        if line.startswith("API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("API_BASE="):
            base = line.split("=", 1)[1].strip().strip('"')

headers = {"X-API-Key": key}

print("=== P&L (June 2026) ===")
req = urllib.request.Request(f"{base}/api/dashboard/financial/pnl?year=2026&month=6", headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
d = json.loads(resp.read().decode())
data = d.get("data", {})
rev = data.get("revenue", {})
print(f"  Game Revenue:     {rev.get('game_revenue', 0):>10,.0f} Ks")
print(f"  Food Revenue:     {rev.get('food_revenue', 0):>10,.0f} Ks")
print(f"  Topup Revenue:    {rev.get('topup_revenue', 0):>10,.0f} Ks")
print(f"  Wallet Consumed:  {rev.get('wallet_consumed', 0):>10,.0f} Ks")
print(f"  -----------------------------------------")
print(f"  TOTAL Revenue:    {rev.get('total_revenue', 0):>10,.0f} Ks")
print(f"  Gross Profit:     {data.get('gross_profit', 0):>10,.0f} Ks")
print(f"  Net Profit:       {data.get('net_profit', 0):>10,.0f} Ks")

print(f"\n=== Balance Sheet ===")
req = urllib.request.Request(f"{base}/api/dashboard/financial/balance-sheet", headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
d = json.loads(resp.read().decode())
data = d.get("data", {})
print(f"  Cash Accounts:")
for a in data.get("accounts", data.get("bank_accounts", data.get("assets", []))):
    if isinstance(a, dict) and a.get("account"):
        print(f"    {a['account']:15s} = {a.get('balance', 0):>10,.0f} Ks")
    elif isinstance(a, dict) and a.get("name"):
        print(f"    {a['name']:15s} = {a.get('nbv', 0):>10,.0f} Ks")
print(f"  Total Assets: {data.get('total_assets', '?')}")
print(f"  Total Equity: {data.get('total_equity', '?')}")
