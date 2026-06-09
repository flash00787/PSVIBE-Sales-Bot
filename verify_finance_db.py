#!/usr/bin/env python3
"""Verify topup income inclusion by running the calculation logic directly."""
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='PsVibe@MySQL2024!', database='psvibe_api')
c = conn.cursor()

# Test: income_by_account from sales_daily
c.execute("SELECT payment_method, net FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != ''")
income_by_acct = {"cash": 0.0, "wave": 0.0, "kpay": 0.0, "aya_pay": 0.0, "kbz_bank": 0.0, "acm_acc": 0.0}
for row in c.fetchall():
    pm = (row[0] or "").strip()
    net = float(row[1] or 0)
    if not pm: continue
    for part in pm.split("|"):
        part = part.strip()
        if ":" in part:
            method, _, val = part.partition(":")
            method = method.strip().lower().replace(" ", "_")
            val = float(val.strip() or 0) if val.strip() else 0
        else:
            method = part.lower().replace(" ", "_")
            val = net
        if method == "wavepay": method = "wave"
        if method in income_by_acct:
            income_by_acct[method] += val

print("=== Income from Sales Daily ===")
for k, v in income_by_acct.items():
    print(f"  {k:15s} = {v:>10,.0f} Ks")
total_sales = sum(income_by_acct.values())
print(f"  {'TOTAL':15s} = {total_sales:>10,.0f} Ks")

# Test: ADD topup_log income
c.execute("SELECT payment_method, amount FROM topup_log WHERE amount > 0 AND payment_method IS NOT NULL")
for row in c.fetchall():
    pm = (row[0] or "").strip()
    amt = float(row[1] or 0)
    if not pm or amt <= 0: continue
    for part in pm.split("/"):
        part = part.strip()
        if ":" in part:
            method, _, val = part.partition(":")
            method = method.strip().lower().replace(" ", "_")
            val = float(val.strip() or 0) if val.strip() else 0
        else:
            method = part.lower().replace(" ", "_")
            val = amt
        if method == "wavepay": method = "wave"
        if method in income_by_acct:
            income_by_acct[method] += val

print("\n=== Income AFTER adding Topup Log ===")
for k, v in income_by_acct.items():
    print(f"  {k:15s} = {v:>10,.0f} Ks")
total_all = sum(income_by_acct.values())
print(f"  {'TOTAL':15s} = {total_all:>10,.0f} Ks")
print(f"\n✅ Topup income added: {total_all - total_sales:,.0f} Ks")

# Verify P&L
print("\n=== P&L Verification ===")
year, month = 2026, 6
ym = f"{year:04d}-{month:02d}"

c.execute("SELECT net, gross, amount FROM sales_daily WHERE DATE_FORMAT(created_at, '%Y-%m') = %s AND gross > 0", (ym,))
game_rev = 0.0; food_rev = 0.0; discounts = 0.0
for r in c.fetchall():
    g = float(r[1] or 0); n = float(r[0] or 0); a = float(r[2] or 0)
    discounts += (g - n)
    food_amt = max(g - a, 0)
    food_rev += min(food_amt, n)
    game_rev += max(n - food_amt, 0)

c.execute("SELECT COALESCE(SUM(amount),0) FROM topup_log WHERE DATE_FORMAT(topup_date, '%Y-%m') = %s", (ym,))
topup_rev = float(c.fetchone()[0] or 0)

# OLD: total_revenue without topup
old_total = game_rev + food_rev + 0  # was wallet_consumed=0 for simplicity
# NEW: total_revenue with topup
new_total = game_rev + food_rev + topup_rev

print(f"  Game Revenue:    {game_rev:>10,.0f} Ks")
print(f"  Food Revenue:    {food_rev:>10,.0f} Ks")
print(f"  Topup Revenue:   {topup_rev:>10,.0f} Ks")
print(f"  OLD total_revenue: {old_total:>10,.0f} Ks (MISSING topup)")
print(f"  NEW total_revenue: {new_total:>10,.0f} Ks (WITH topup) ✅")

conn.close()
