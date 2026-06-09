#!/usr/bin/env python3
"""Add cash_movements entries to topup and registration endpoints."""
API_FILE = "/root/psvibe_api_server/app.py"
with open(API_FILE) as f:
    code = f.read()

# ===== FIX 1: api_topup_log — add cash_movements inject =====
old_topup = """        _mysql_exec(
            "INSERT INTO member_wallets (member_id, balance_mins, total_bought_mins, total_spend) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE balance_mins=%s, total_bought_mins=%s, total_spend=%s, last_updated=NOW()",
            (member_id, bal_after, bought, new_spend, bal_after, bought, new_spend))

        return ok({"success": True, "balance_mins": bal_after, "total_spend": new_spend})"""

new_topup = """        _mysql_exec(
            "INSERT INTO member_wallets (member_id, balance_mins, total_bought_mins, total_spend) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE balance_mins=%s, total_bought_mins=%s, total_spend=%s, last_updated=NOW()",
            (member_id, bal_after, bought, new_spend, bal_after, bought, new_spend))

        # 🆕 Record cash_movements for top-up income
        if float(amount) > 0:
            try:
                _parse_pm_and_inject(amount, pm, f"Topup {member_id} + {mins_added} mins", staff)
            except Exception as _e:
                logger.warning("Topup cash_movements failed: %s", _e)

        return ok({"success": True, "balance_mins": bal_after, "total_spend": new_spend})"""

if old_topup in code:
    code = code.replace(old_topup, new_topup, 1)
    print("✅ api_topup_log: cash_movements inject added")
else:
    print("❌ api_topup_log pattern not found")

# ===== FIX 2: register_member — add cash_movements inject =====
old_reg = """        # Log into topup_log
        if mins_added > 0:"""

new_reg = """        # 🆕 Record cash_movements for member registration income
        if float(amount) > 0:
            try:
                _parse_pm_and_inject(amount, f"KPay:{kpay}/Cash:{cash}", f"New member {member_id} + {mins_added} mins", staff)
            except Exception as _e:
                logger.warning("Reg cash_movements failed: %s", _e)

        # Log into topup_log
        if mins_added > 0:"""

if old_reg in code:
    code = code.replace(old_reg, new_reg, 1)
    print("✅ register_member: cash_movements inject added")
else:
    print("❌ register_member pattern not found")

# ===== FIX 3: Add helper function _parse_pm_and_inject =====
# Find a good insertion point (after imports, before routes)
helper_fn = """
def _parse_pm_and_inject(total_amount: float, payment_method: str, note: str, staff_name: str) -> None:
    \"\"\"Parse payment method string (e.g. 'KPay:31000|Cash:20000' or 'KPay:90000/Cash:0')
    and inject cash_movements entries for each account.\"\"\"
    if not payment_method or float(total_amount) <= 0:
        return
    import re
    # Handle both | and / separators
    parts = re.split(r'[|/]', payment_method)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            method, _, val_str = part.partition(":")
            val = float(val_str.strip() or 0) if val_str.strip() else 0
        else:
            method = part
            val = float(total_amount) / len(parts)
        method = method.strip()
        val = float(val)
        # Map internal method names to cash_movements account names
        acct_map = {
            "cash": "Cash",
            "kpay": "KPay",
            "wavepay": "WavePay",
            "aya pay": "AYA Pay",
            "aya_pay": "AYA Pay",
            "kbz bank": "KBZ Bank",
            "kbz_bank": "KBZ Bank",
            "acm acc": "ACM's Acc",
            "acm_acc": "ACM's Acc",
        }
        account = acct_map.get(method.strip().lower().replace("  ", " "), method)
        if val > 0:
            _mysql_exec(
                "INSERT INTO cash_movements (movement_type, account, amount, note, staff_name, created_at) VALUES (%s, %s, %s, %s, %s, NOW())",
                ("inject", account, val, note, staff_name)
            )
            logger.info("Cash movement inject: %s +%.0f Ks (%s)", account, val, note)
"""

# Insert _parse_pm_and_inject helper. Find a good place — after the imports/globals, before first route
# Look for a unique marker like the first @app decorator
insert_point = "#  MUTATION — topup/log"
if insert_point in code:
    code = code.replace(insert_point, helper_fn + "\n" + insert_point, 1)
    print("✅ _parse_pm_and_inject helper added")
else:
    print("❌ Insert point not found")

with open(API_FILE, "w") as f:
    f.write(code)
compile(code, API_FILE, "exec")
print("✅ File written + compiled OK")
