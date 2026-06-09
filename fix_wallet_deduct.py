#!/usr/bin/env python3
"""Fix wallet balance deduction on daily sale save.

2 fixes:
1. api_client.py: Add wallet_deduct to mapped dict sent to API
2. app.py: Deduct balance_mins from member_wallets after saving sales record
"""

import re

# === FIX 1: api_client.py ===
CLIENT_FILE = "/root/psvibe-sales-bot/bot/api_client.py"
with open(CLIENT_FILE) as f:
    client_code = f.read()

old_map = (
    '        "coupon_code": data.get("coupon_code", ""),\n'
    '    }\n'
    '    return _api_call("POST", "sales/record", json_data=mapped)'
)

new_map = (
    '        "coupon_code": data.get("coupon_code", ""),\n'
    '        "wallet_deduct": data.get("wallet_deduct", 0),\n'
    '    }\n'
    '    return _api_call("POST", "sales/record", json_data=mapped)'
)

if old_map in client_code:
    client_code = client_code.replace(old_map, new_map, 1)
    with open(CLIENT_FILE, "w") as f:
        f.write(client_code)
    compile(client_code, CLIENT_FILE, "exec")
    print("✅ api_client.py: wallet_deduct field added to mapped dict")
else:
    print("❌ api_client.py: pattern not found")
    idx = client_code.find('"coupon_code"')
    if idx >= 0:
        print(f"  Found coupon_code at {idx}")
        print(f"  Context: {client_code[idx:idx+200]}")

# === FIX 2: app.py ===
APP_FILE = "/root/psvibe_api_server/app.py"
with open(APP_FILE) as f:
    app_code = f.read()

# Find the INSERT into sales_daily and add wallet deduction after it
old_save = (
    '        _mysql_exec(\n'
    '            "INSERT INTO sales_daily (voucher_no, sale_date, console_id, member_id, amount, gross, discount, net, staff_name, payment_method, notes) "\n'
    '            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",\n'
    '            (voucher_no, sale_date, console_id, member_id, game_amt, gross, discount, net_total, staff, payment_method, combined_notes)\n'
    '        )\n'
    '\n'
    '        logger.info("Sales record saved: voucher=%s member=%s console=%s net=%s", voucher_no, member_id, console_id, net_total)'
)

new_save = (
    '        _mysql_exec(\n'
    '            "INSERT INTO sales_daily (voucher_no, sale_date, console_id, member_id, amount, gross, discount, net, staff_name, payment_method, notes) "\n'
    '            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",\n'
    '            (voucher_no, sale_date, console_id, member_id, game_amt, gross, discount, net_total, staff, payment_method, combined_notes)\n'
    '        )\n'
    '\n'
    '        # Deduct wallet balance for member sales\n'
    '        _wallet_deduct = int(req.get("wallet_deduct", 0))\n'
    '        if _wallet_deduct > 0 and member_id and member_id.strip() not in ("", "0 (Guest)", "-"):\n'
    '            _mysql_exec(\n'
    '                "UPDATE member_wallets SET balance_mins = GREATEST(0, COALESCE(balance_mins, 0) - %s) WHERE member_id=%s",\n'
    '                (_wallet_deduct, member_id)\n'
    '            )\n'
    '            logger.info("Wallet deducted: %s mins for member %s", _wallet_deduct, member_id)\n'
    '\n'
    '        logger.info("Sales record saved: voucher=%s member=%s console=%s net=%s", voucher_no, member_id, console_id, net_total)'
)

if old_save in app_code:
    app_code = app_code.replace(old_save, new_save, 1)
    with open(APP_FILE, "w") as f:
        f.write(app_code)
    compile(app_code, APP_FILE, "exec")
    print("✅ app.py: wallet deduction added after sales record save")
else:
    print("❌ app.py: pattern not found")
    idx = app_code.find("INSERT INTO sales_daily")
    if idx >= 0:
        print(f"  Found INSERT at {idx}")
        print(f"  Context: {app_code[idx:idx+400]}")
