#!/bin/bash
BOT="/root/psvibe-sale-bot"

echo "=== __init__.py: OPEX_CATEGORIES, ASSET_CATEGORIES, FINANCE_ACCOUNTS, PAY_METHODS, PREPAID_CATEGORIES ==="
grep -n "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|PREPAID_CATEGORIES\|_BIZ_START\b" "$BOT/bot/__init__.py"

echo ""
echo "=== Lines around first match ==="
grep -n "OPEX_CATEGORIES" "$BOT/bot/__init__.py" | head -3
echo "--- Reading around line for OPEX_CATEGORIES in __init__.py ---"

echo ""
echo "=== Search in all .py files for definitions ==="
grep -rn "^OPEX_CATEGORIES\|^ASSET_CATEGORIES\|^FINANCE_ACCOUNTS\|^PAY_METHODS\|^PREPAID_CATEGORIES\|^_BIZ_START" "$BOT/bot/" --include="*.py"
