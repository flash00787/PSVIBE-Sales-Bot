#!/usr/bin/env python3
"""Full cash flow audit - all payment accounts reconciliation."""
import pymysql, re
from collections import defaultdict

conn = pymysql.connect(host="127.0.0.1", port=3306, user="psvibe_user",
    password="PsVib…d!",
    database="psvibe_api", charset="utf8mb4")
cur = conn.cursor(pymysql.cursors.DictCursor)

def parse_payments(pm_str):
    """Parse payment method strings like 'KPay:31000|Cash:20000|WavePay:17000'"""
    result = defaultdict(float)
    if not pm_str:
        return result
    parts = re.split(r'[|/]', pm_str)
    for part in parts:
        part = part.strip()
        m = re.match(r'(\w+)\s*:\s*([\d,.]+)', part)
        if m:
            amt = float(m.group(2).replace(',', ''))
            if amt > 0:
                result[m.group(1)] += amt
    return dict(result)

# === SALES REVENUE ===
cur.execute("SELECT payment_method, net FROM sales_daily WHERE net > 0")
rows = cur.fetchall()
rev_by_method = defaultdict(float)
rev_count = defaultdict(int)
for r in rows:
    parsed = parse_payments(r["payment_method"])
    net = float(r["net"])
    sum_p = sum(parsed.values())
    for method, amt in parsed.items():
        if sum_p > 0:
            rev_by_method[method] += net * (amt / sum_p)
            rev_count[method] += 1

print("=== 1. SALES REVENUE by Payment Method ===")
for m in sorted(rev_by_method, key=lambda x: rev_by_method[x], reverse=True):
    print(f"  {m:12s}: {rev_by_method[m]:>10,.0f} Ks ({rev_count[m]} tx)")

# === TOPUPS ===
cur.execute("SELECT payment_method, amount FROM topup_log WHERE amount > 0")
rows = cur.fetchall()
topup_by_method = defaultdict(float)
for r in rows:
    parsed = parse_payments(r["payment_method"])
    amt = float(r["amount"])
    sum_p = sum(parsed.values())
    for m, pa in parsed.items():
        if sum_p > 0:
            topup_by_method[m] += amt * (pa / sum_p)

print("\n=== 2. TOPUPS by Payment Method ===")
for m in sorted(topup_by_method, key=lambda x: topup_by_method[x], reverse=True):
    print(f"  {m:12s}: {topup_by_method[m]:>10,.0f} Ks")

# === CASH MOVEMENTS (Internal Transfers) ===
cur.execute("SELECT account, movement_type, SUM(amount) as total FROM cash_movements GROUP BY account, movement_type")
rows = cur.fetchall()
cm_by_account = {}
for r in rows:
    acc = r["account"]
    if acc not in cm_by_account:
        cm_by_account[acc] = {}
    cm_by_account[acc][r["movement_type"]] = float(r["total"])

print("\n=== 3. CASH MOVEMENTS (Internal Transfers) ===")
cm_net = {}
for acc in sorted(cm_by_account.keys()):
    entries = cm_by_account[acc]
    net = sum(entries.values())
    cm_net[acc] = net
    items = ", ".join(f"{k}: {v:,.0f}" for k, v in sorted(entries.items()))
    sign = "+" if net >= 0 else ""
    print(f"  {acc:12s}: {items} = net: {sign}{net:,.0f}")

# === OPEX ===
cur.execute("SELECT payment_method, SUM(amount) as total FROM opex GROUP BY payment_method")
rows = cur.fetchall()
opex_by_method = {}
print("\n=== 4. OPEX EXPENSES by Payment Method ===")
for r in rows:
    opex_by_method[r["payment_method"]] = float(r["total"])
    print(f"  {r['payment_method']:12s}: {float(r['total']):>10,.0f} Ks")

# === CAPITAL MOVEMENTS ===
cur.execute("SELECT type, payment_method, amount, notes FROM capital_movements")
rows = cur.fetchall()
cap_inject = defaultdict(float)
cap_eject = defaultdict(float)
print(f"\n=== 5. CAPITAL MOVEMENTS ({len(rows)} entries) ===")
for r in rows:
    amt = float(r["amount"])
    pm = r["payment_method"] or "N/A"
    notes = r["notes"] or ""
    if r["type"] == "inject":
        cap_inject[pm] += amt
    else:
        cap_eject[pm] += amt
    print(f"  {r['type']:6s} | {pm:12s} | {amt:>10,.0f} | {notes[:60]}")

# === GRAND RECONCILIATION ===
print("\n" + "=" * 70)
print("=== MASTER RECONCILIATION by Account ===")
print("=" * 70)
print(f"{'Account':12s} {'Revenue':>10s} {'Topups':>10s} {'CapIn':>10s} {'CapOut':>10s} {'Transfers':>10s} {'OPEX':>10s} {'= BAL':>12s}")
print("-" * 82)

all_accounts = ["Cash", "KBZ Bank", "KPay", "Wave", "AYA Pay", "ACM's Acc"]
total_check = 0

for acc in all_accounts:
    rev = rev_by_method.get(acc, 0)
    topup = topup_by_method.get(acc, 0)
    cap_in = cap_inject.get(acc, 0)
    cap_out = cap_eject.get(acc, 0)
    cm_net_val = cm_net.get(acc, 0)
    opex_val = opex_by_method.get(acc, 0)

    # net = sales_revenue + topups + capital_in - capital_out + transfers - opex
    net_bal = rev + topup + cap_in - cap_out + cm_net_val - opex_val
    total_check += net_bal
    
    sign_bal = "+" if net_bal >= 0 else ""
    sign_cm = "+" if cm_net_val >= 0 else ""
    print(f"{acc:12s} {rev:>10,.0f} {topup:>10,.0f} {cap_in:>10,.0f} {cap_out:>10,.0f} {sign_cm}{cm_net_val:>9,.0f} {opex_val:>10,.0f} {sign_bal}{net_bal:>11,.0f}")

print("-" * 82)
sign_t = "+" if total_check >= 0 else ""
print(f"{'TOTAL':12s} {'':>10s} {'':>10s} {'':>10s} {'':>10s} {'':>10s} {'':>10s} {sign_t}{total_check:>11,.0f}")

# Current accounts table
print("\n=== CURRENT ACCOUNTS TABLE vs CORRECT BALANCES ===")
cur.execute("SELECT account_name, balance FROM accounts")
print(f"{'Account':12s} {'Current':>12s} {'Correct':>12s} {'Diff':>12s}")
print("-" * 48)
for r in cur.fetchall():
    acc = r["account_name"]
    current = float(r["balance"])
    rev = rev_by_method.get(acc, 0)
    topup = topup_by_method.get(acc, 0)
    cap_in = cap_inject.get(acc, 0)
    cap_out = cap_eject.get(acc, 0)
    cm = cm_net.get(acc, 0)
    ox = opex_by_method.get(acc, 0)
    correct = rev + topup + cap_in - cap_out + cm - ox
    diff = correct - current
    print(f"{acc:12s} {current:>12,.0f} {correct:>12,.0f} {diff:>+12,.0f}")

conn.close()
