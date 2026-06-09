#!/usr/bin/env python3
"""Fix wallet deduction: update total_used_mins + backfill all member balances."""
APP_FILE = "/root/psvibe_api_server/app.py"

with open(APP_FILE) as f:
    code = f.read()

# Step 1: Update API to also track total_used_mins
old = (
    '        if _wallet_deduct > 0 and member_id and member_id.strip() not in ("", "0 (Guest)", "-"):\n'
    '            _mysql_exec(\n'
    '                "UPDATE member_wallets SET balance_mins = GREATEST(0, COALESCE(balance_mins, 0) - %s) WHERE member_id=%s",\n'
    '                (_wallet_deduct, member_id)\n'
    '            )\n'
    '            logger.info("Wallet deducted: %s mins for member %s", _wallet_deduct, member_id)'
)

new = (
    '        if _wallet_deduct > 0 and member_id and member_id.strip() not in ("", "0 (Guest)", "-"):\n'
    '            _mysql_exec(\n'
    '                "UPDATE member_wallets SET balance_mins = GREATEST(0, COALESCE(balance_mins, 0) - %s), total_used_mins = COALESCE(total_used_mins, 0) + %s WHERE member_id=%s",\n'
    '                (_wallet_deduct, _wallet_deduct, member_id)\n'
    '            )\n'
    '            logger.info("Wallet deducted: %s mins for member %s (total_used +%s)", _wallet_deduct, member_id, _wallet_deduct)'
)

if old in code:
    code = code.replace(old, new, 1)
    with open(APP_FILE, "w") as f:
        f.write(code)
    compile(code, APP_FILE, "exec")
    print("✅ API: total_used_mins tracking added to wallet deduction")
else:
    print("❌ Pattern not found in app.py")

# Step 2: Recalculate all member balances from sales_daily + member_wallets total_bought_mins
CMD = (
    "docker exec psvibe-mysql mysql -u psvibe_user -pPsVibe@2026_Rotated! psvibe_api -e "
    '"UPDATE member_wallets mw '
    "JOIN (SELECT member_id, COALESCE(SUM(wallet_deduct), 0) as used "
    "FROM sales_daily WHERE member_id IS NOT NULL AND member_id NOT IN ('','0 (Guest)','-') "
    "GROUP BY member_id) sd ON mw.member_id = sd.member_id "
    "SET mw.total_used_mins = sd.used, "
    "mw.balance_mins = GREATEST(0, COALESCE(mw.total_bought_mins, 0) - sd.used) "
    "WHERE sd.used > 0;"
    ' SELECT member_id, total_bought_mins, total_used_mins, balance_mins FROM member_wallets ORDER BY member_id;"'
)
import subprocess
r = subprocess.run(CMD, shell=True, capture_output=True, text=True)
print("DB Backfill:")
for line in r.stdout.split("\n"):
    if line.strip() and not line.startswith("mysql"):
        print(line)
print(r.stderr[:200] if r.stderr else "")
