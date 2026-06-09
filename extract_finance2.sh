#!/bin/bash
BOT="/root/psvibe-sale-bot"

echo "=== FINANCE.PY: FUNCTIONS & SHEET WRITES ==="
grep -n "^async def \|^def \|get_.*_sh\|\.append_row\|STATES\|OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|_BIZ_START\|BTN_FIN_" "$BOT/bot/handlers/finance.py"

echo ""
echo "=== ATTENDANCE.PY ==="
cat "$BOT/bot/handlers/attendance.py"

echo ""
echo "=== PAYROLL.PY ==="
cat "$BOT/bot/handlers/payroll.py"

echo ""
echo "=== SALARY_ADV.PY ==="
cat "$BOT/bot/handlers/salary_adv.py"

echo ""
echo "=== DISCOUNT.PY: FUNCTIONS & SHEET WRITES ==="
grep -n "^async def \|^def \|\.append_row\|worksheet\|_sh" "$BOT/bot/handlers/discount.py"

echo ""
echo "=== REPORTS.PY: FUNCTIONS ==="
grep -n "^async def \|^def " "$BOT/bot/handlers/reports.py"

echo ""
echo "=== REFERRAL.PY: FUNCTIONS ==="
grep -n "^async def \|^def \|\.append_row\|\.update\|member_sh\|save_referral_code\|fetch_referral_code" "$BOT/bot/handlers/referral.py"

echo ""
echo "=== __init__.py: BUTTON CONSTANTS ==="
grep -n "BTN_FIN_\|BTN_DISCOUNT\|BTN_PROMO\|BTN_FOOD\|BTN_BUNDLE\|OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|ATTEND_NAMES\|NAV_ROW\|BTN_BACK\|BTN_CANCEL\|BTN_CONFIRM_SAVE\|BTN_BACK_MAIN" "$BOT/bot/__init__.py"

echo ""
echo "=== __init__.py: STATE CONSTANTS ==="
grep -n "^FINANCE_MENU\|^OPEX_CAT\|^ASSET_NAME\|^PREPAID_DESC\|^ACCT_TRF_FROM\|^PAY_VENDOR\|^REC_CUST\|^FIN_REPORT_MENU\|^CAP_ACCT\|^SHARE_NAME\|^PAY_SETTLE_LIST\|^REC_SETTLE_LIST\|^ADVPAY_PARTY\|^ATTEND_STAFF\|^SAL_ADV_STAFF\|^DISCOUNT\|^REFERRAL_CODE\b\|^PROMO_SELECT\|^BUNDLE_FOC" "$BOT/bot/__init__.py"

echo ""
echo "=== __init__.py: SPECIAL API FUNCTIONS ==="
grep -n "def fetch_referral_code\|def save_referral_code\|def fetch_financial_report\|def fetch_payroll\|def fetch_salary_adv\|def fetch_attendance\|Salary_Advance\|Attendance_Log\|Payroll" "$BOT/bot/__init__.py"

echo ""
echo "=== __init__.py: PAYROLL REPORT FUNCTIONS ==="
grep -n "cmd_payroll_cmd\|cmd_payroll\b\|cmd_setattend\|cmd_finance\|cmd_financial_report\|cmd_kpi_cmd\|cmd_staff_kpi\|fetch_base_salaries\|fetch_attendance\|fetch_salary_adv\|payroll_sh\|get_payroll" "$BOT/bot/__init__.py"

echo ""
echo "=== HANDLERS/__init__.py ==="
cat "$BOT/bot/handlers/__init__.py" 2>/dev/null || echo "NOT FOUND"
