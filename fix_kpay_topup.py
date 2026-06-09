#!/usr/bin/env python3
"""Fix topup parsing in Finance Balances - replace GROUP BY with per-row."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

old = '''        # Topup income
        topup_rows = _mq("SELECT payment_method, COALESCE(SUM(amount), 0) as total FROM topup_log WHERE topup_date >= '2026-01-01' GROUP BY payment_method")
        for r in topup_rows:
            pm = (r.get("payment_method") or "").lower()
            topup_amount = float(r.get("total", 0))
            if "kpay" in pm:
                income_by_account["kpay"] = income_by_account.get("kpay", 0) + topup_amount
            elif "cash" in pm:
                income_by_account["cash"] = income_by_account.get("cash", 0) + topup_amount'''

new = '''        # Topup income
        topup_rows = _mq("SELECT payment_method, amount FROM topup_log WHERE amount > 0 AND payment_method IS NOT NULL")
        for _tr in topup_rows:
            _pm = (_tr.get("payment_method") or "").strip()
            if not _pm: continue
            for _part in _pm.split("/"):
                _part = _part.strip()
                if ":" in _part:
                    _method, _, _val = _part.partition(":")
                    _method = _method.strip().lower().replace(" ", "_")
                    try:
                        _val = float(_val.strip() or 0) if _val.strip() else 0
                    except ValueError:
                        continue
                    if _method == "wavepay": _method = "wave"
                    if _method in income_by_account:
                        income_by_account[_method] += _val'''

src = src.replace(old, new, 1)
print("Topup parsing fixed ✅")

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
print("Syntax OK ✅")
