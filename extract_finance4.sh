#!/bin/bash
BOT="/root/psvibe-sale-bot"

echo "=== CONSTANTS FROM FINANCE.PY ==="
grep -n "^OPEX_CATEGORIES\|^ASSET_CATEGORIES\|^FINANCE_ACCOUNTS\|^PAY_METHODS\|^PREPAID_CATEGORIES\|^_BIZ_START\b" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== OPEX_CATEGORIES definition ==="
grep -A 20 "^OPEX_CATEGORIES" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== ASSET_CATEGORIES definition ==="
grep -A 10 "^ASSET_CATEGORIES" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== FINANCE_ACCOUNTS definition ==="
grep -A 10 "^FINANCE_ACCOUNTS" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== PAY_METHODS definition ==="
grep -A 10 "^PAY_METHODS" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== PREPAID_CATEGORIES definition ==="
grep -A 10 "^PREPAID_CATEGORIES" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== Advance Payment append_row details ==="
grep -B5 -A10 "get_advpay_sh.*append_row\|sh.append_row" "$BOT/bot/handlers/finance.py" | tail -80
echo ""

echo "=== Payable settle append_row details ==="
grep -B2 -A15 "update_cell\|_handle_settle_confirm" "$BOT/bot/handlers/finance.py" | head -60
echo ""

echo "=== Capital account append_row ==="
grep -B5 -A10 "sh.append_row.*Capital\|Capital.*append_row\|cap_acct.*append_row" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== Discount.py: full append logic ==="
grep -B5 -A10 "def step_discount" "$BOT/bot/handlers/discount.py"
echo ""

echo "=== Discount.py: promo apply ==="
grep -B5 -A10 "def step_promo_select\|\"Promo\"\|promo_applied\|def apply_" "$BOT/bot/handlers/discount.py" | head -80
echo ""

echo "=== cmd_financial_report (reports.py) ==="
grep -A 70 "^async def cmd_financial_report" "$BOT/bot/handlers/reports.py"
echo ""

echo "=== cmd_today_report (reports.py) ==="
grep -A 60 "^async def cmd_today_report" "$BOT/bot/handlers/reports.py"
