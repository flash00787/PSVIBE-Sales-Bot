#!/usr/bin/env python3
"""Fix: Add topup_log income to P&L and Balance Sheet calculations.

Current bug:
- P&L: topup_rev is calculated but NOT added to total_revenue
- Balance Sheet: income_by_account comes ONLY from sales_daily, NOT topup_log
- Result: 180,000 Ks (topup income) missing from both reports
"""
FILE = "/root/psvibe_api_server/dashboard_routes.py"
with open(FILE) as f:
    code = f.read()

# ===== FIX 1: P&L — Add topup_rev to total_revenue =====
old_pnl_rev = '        total_revenue = game_rev + food_rev + wallet_consumed'
new_pnl_rev = '        total_revenue = game_rev + food_rev + topup_rev + wallet_consumed'

if old_pnl_rev in code:
    code = code.replace(old_pnl_rev, new_pnl_rev, 1)
    print("✅ P&L: topup_rev added to total_revenue")
else:
    print("❌ P&L pattern not found")
    idx = code.find('total_revenue = game_rev')
    if idx >= 0:
        print(f"Found: {repr(code[idx:idx+80])}")

# ===== FIX 2: Balance Sheet — Add topup_log income =====
# After the sales_daily income loop, add topup_log income
old_bs = """        for a in accounts:
            key = a["key"]
            income = income_by_account.get(key, 0.0)"""

new_bs = """        # 🆕 ADD topup_log income (member card purchases were MISSING!)
        trows = _mq("SELECT payment_method, amount FROM topup_log WHERE amount > 0 AND payment_method IS NOT NULL")
        for _tr in trows:
            _pm = (_tr.get("payment_method") or "").strip()
            _amt = float(_tr.get("amount") or 0)
            if not _pm or _amt <= 0:
                continue
            # Topup PM format: "KPay:90000/Cash:0" (pipe-delimited with :amount)
            for _part in _pm.split("/"):
                _part = _part.strip()
                if ":" in _part:
                    _method, _, _val = _part.partition(":")
                    _method = _method.strip().lower().replace(" ", "_")
                    _val = float(_val.strip() or 0) if _val.strip() else 0
                else:
                    _method = _part.lower().replace(" ", "_")
                    _val = _amt
                if _method == "wavepay":
                    _method = "wave"
                if _method in income_by_account:
                    income_by_account[_method] += _val

        for a in accounts:
            key = a["key"]
            income = income_by_account.get(key, 0.0)"""

if old_bs in code:
    code = code.replace(old_bs, new_bs, 1)
    print("✅ Balance Sheet: topup_log income added to income_by_account")
else:
    print("❌ BS income_by_account pattern not found")
    idx = code.find('for a in accounts:')
    if idx >= 0:
        print(f"Context: {repr(code[idx-50:idx+30])}")

with open(FILE, "w") as f:
    f.write(code)
compile(code, FILE, "exec")
print("✅ File written + compiled OK")
