import pymysql, re

c = pymysql.connect(host="127.0.0.1", port=3306, user="psvibe_user",
    password=*** 
    database="psvibe_api", charset="utf8mb4")
cur = c.cursor(pymysql.cursors.DictCursor)

accounts = [
    {"key": "cash", "label": "Cash"},
    {"key": "wave", "label": "WavePay"},
    {"key": "aya_pay", "label": "AYA Pay"},
    {"key": "kpay", "label": "KPay"},
    {"key": "kbz_bank", "label": "KBZ Bank"},
    {"key": "acm_acc", "label": "ACM's Acc"}
]

# 1. Sales income (exclude Topup/New member notes)
cur.execute("SELECT payment_method, net, notes FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != ''")
income_by_account = {a["key"]: 0.0 for a in accounts}
for row in cur.fetchall():
    note = (row.get("notes") or "")
    if note.startswith("Topup") or note.startswith("New member"): continue
    pm = (row.get("payment_method") or "").strip()
    net_amount = float(row.get("net") or 0)
    if not pm: continue
    parts = pm.split("|")
    for part in parts:
        part = part.strip()
        if ":" in part:
            method, _, val = part.partition(":")
            method = method.strip().lower().replace(" ", "_")
            try:
                val = float(val.strip() or 0) if val.strip() else 0
            except ValueError:
                val = net_amount / len(parts) if parts else 0
        else:
            method = part.lower().replace(" ", "_")
            val = net_amount / len(parts) if parts else 0
        if method == "wavepay": method = "wave"
        if method in income_by_account:
            income_by_account[method] += val

# 2. Topup income
cur.execute("SELECT payment_method, amount FROM topup_log WHERE amount > 0 AND payment_method IS NOT NULL")
for tr in cur.fetchall():
    _pm = (tr.get("payment_method") or "").strip()
    if not _pm: continue
    for _part in _pm.split("/"):
        _part = _part.strip()
        if ":" in _part:
            _method, _, _val = _part.partition(":")
            _method = _method.strip().lower().replace(" ", "_")
            try:
                _val = float(_val.strip() or 0) if _val.strip() else 0
            except ValueError: continue
            if _method == "wavepay": _method = "wave"
            if _method in income_by_account:
                income_by_account[_method] += _val

# 3. OPEX (excluding Prepaid Rent Amortization)
cur.execute("SELECT payment_method, COALESCE(SUM(amount), 0) as total FROM opex WHERE description NOT LIKE %s GROUP BY payment_method", ("%Prepaid Rent Amortization%",))
opex_by_acct = {a["key"]: 0.0 for a in accounts}
for row in cur.fetchall():
    pm = (row.get("payment_method") or "").strip().lower().replace(" ", "_")
    if pm in opex_by_acct:
        opex_by_acct[pm] += float(row["total"] or 0)

# 4. Cash movements
cur.execute("SELECT movement_type, account, COALESCE(SUM(amount), 0) as total FROM cash_movements GROUP BY movement_type, account")
cash_map = {}
for row in cur.fetchall():
    key = str(row['movement_type']) + "|" + str(row['account'])
    cash_map[key] = cash_map.get(key, 0) + float(row["total"] or 0)

# Subtract inject entries that overlap with topup
cur.execute("SELECT account, COALESCE(SUM(amount), 0) as total FROM cash_movements WHERE movement_type = 'inject' AND (note IS NOT NULL AND (note LIKE CONCAT('Topup', CHAR(37)) OR note LIKE CONCAT('New member', CHAR(37)))) GROUP BY account")
for r in cur.fetchall():
    k = "inject|" + r["account"]
    if k in cash_map:
        cash_map[k] -= float(r["total"] or 0)

key_to_name = {"cash": "Cash", "wave": "Wave", "kpay": "KPay", "aya_pay": "AYA Pay", "kbz_bank": "KBZ Bank", "acm_acc": "ACM's Acc"}

# 5. Capital expenditure (KBZ only)
cur.execute("SELECT COALESCE(SUM(per_price * qty), 0) as total FROM finance_assets WHERE status = 'active'")
_asset_purchases = float(cur.fetchone()["total"] or 0)
cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM finance_advances")
_advances_total = float(cur.fetchone()["total"] or 0)
cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM finance_prepaid")
_prepaid_total = float(cur.fetchone()["total"] or 0)
cur.execute("SELECT COALESCE(SUM(disposal_amount), 0) as total FROM finance_assets WHERE status = 'disposed' AND disposal_amount > 0")
_disposal_proceeds = float(cur.fetchone()["total"] or 0)
capex_total = _asset_purchases + _advances_total + _prepaid_total - _disposal_proceeds

print("")
print("=" * 92)
print("=== ORIGINAL FORMULA from /finance/balances endpoint ===")
print("=" * 92)
print("  Formula: balance = income - opex + transfer_in - |transfer_out| + inject - eject - capex")
print("  (KBZ only: capex = assets + advances + prepaid - disposal proceeds)")
print("")
header = "{:<12s} {:>10s} {:>10s} {:>10s} {:>10s} {:>10s} {:>10s} {:>10s} {:>12s}".format(
    "Account", "Income", "OPEX", "TxIn", "TxOut", "Inj", "Ej", "CapEx", "= BAL")
print(header)
print("-" * 92)

results = []
for a in accounts:
    k, lbl = a["key"], a["label"]
    inc = income_by_account[k]
    o = opex_by_acct[k]
    ti = cash_map.get("transfer_in|" + lbl, 0)
    to = abs(cash_map.get("transfer_out|" + lbl, 0))
    ij = cash_map.get("inject|" + lbl, 0)
    ej = cash_map.get("eject|" + lbl, 0)
    capex = capex_total if k == "kbz_bank" else 0
    bal = inc - o + ti - to + ij - ej - capex
    results.append((lbl, inc, o, ti, to, ij, ej, capex, bal))
    line = "{:<12s} {:>10,.0f} {:>10,.0f} {:>10,.0f} {:>10,.0f} {:>10,.0f} {:>10,.0f} {:>10,.0f} {:>+12,.0f}".format(
        lbl, inc, o, ti, to, ij, ej, capex, bal)
    print(line)

total_bal = sum(r[8] for r in results)
print("-" * 92)
total_line = "{:<12s} {:>10s} {:>10s} {:>10s} {:>10s} {:>10s} {:>10s} {:>10s} {:>+12,.0f}".format(
    "TOTAL", "", "", "", "", "", "", "", total_bal)
print(total_line)

# Compare with accounts table
print("")
print("=" * 48)
print("=== VS CURRENT ACCOUNTS TABLE ===")
print("=" * 48)
cur.execute("SELECT account_name, balance FROM accounts")
cur_accounts = {}
for r in cur.fetchall():
    cur_accounts[r["account_name"]] = float(r["balance"])
h2 = "{:<12s} {:>12s} {:>12s} {:>12s}".format("Account", "Current", "Formula", "Diff")
print(h2)
print("-" * 48)
for lbl, inc, o, ti, to, ij, ej, capex, bal in results:
    current = cur_accounts.get(lbl, 0)
    line2 = "{:<12s} {:>12,.0f} {:>12,.0f} {:>+12,.0f}".format(lbl, current, bal, bal - current)
    print(line2)

c.close()
