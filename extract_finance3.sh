#!/bin/bash
BOT="/root/psvibe-sale-bot"

echo "=== OPEX_CATEGORIES ==="
grep -n "OPEX_CATEGORIES" "$BOT/bot/__init__.py"
echo ""

echo "=== ASSET_CATEGORIES ==="
grep -n "ASSET_CATEGORIES" "$BOT/bot/__init__.py"
echo ""

echo "=== FINANCE_ACCOUNTS ==="
grep -n "FINANCE_ACCOUNTS" "$BOT/bot/__init__.py"
echo ""

echo "=== PAY_METHODS ==="
grep -n "PAY_METHODS" "$BOT/bot/__init__.py"
echo ""

echo "=== PREPAID_CATEGORIES ==="
grep -n "PREPAID_CATEGORIES" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== fetch_salary_advances ==="
grep -A 40 "^def fetch_salary_advances" "$BOT/bot/__init__.py"
echo ""

echo "=== fetch_base_salaries ==="
grep -A 20 "^def fetch_base_salaries" "$BOT/bot/__init__.py"
echo ""

echo "=== fetch_attendance ==="
grep -A 40 "^def fetch_attendance" "$BOT/bot/__init__.py"
echo ""

echo "=== save_attendance ==="
grep -A 30 "^def save_attendance" "$BOT/bot/__init__.py"
echo ""

echo "=== get_salary_adv_sh ==="
grep -A 15 "^def get_salary_adv_sh" "$BOT/bot/__init__.py"
echo ""

echo "=== get_att_sh ==="
grep -A 15 "^def get_att_sh" "$BOT/bot/__init__.py"
echo ""

echo "=== fetch_referral_code / save_referral_code ==="
grep -A 30 "^def fetch_referral_code\|^def save_referral_code" "$BOT/bot/__init__.py"
echo ""

echo "=== Capital sheet writes ==="
grep -n "get_capital_sh\|Capital_" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== cmd_finance_setup ==="
grep -A 30 "^async def cmd_finance_setup" "$BOT/bot/handlers/finance.py"
echo ""

echo "=== Discount/Promo append_row ==="
grep -A5 -B2 "append_row" "$BOT/bot/handlers/discount.py"
echo ""

echo "=== Stock Access PIN ==="
grep -n "STOCK_ACCESS_PIN" "$BOT/bot/__init__.py"
echo ""

echo "=== ADMIN_PIN ==="
grep -n "ADMIN_PIN\|ADMIN_PIN_VAL" "$BOT/bot/__init__.py" | head -10
