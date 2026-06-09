#!/bin/bash
echo "=== Root-level handlers/finance.py imports ==="
head -15 /root/psvibe-sale-bot/handlers/finance.py
echo ""

echo "=== Root-level handlers/finance.py OPEX_CATEGORIES ==="
grep -n "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|PREPAID_CATEGORIES\|_BIZ_START" /root/psvibe-sale-bot/handlers/finance.py
echo ""

echo "=== bot keep_alive.py ==="
cat /root/psvibe-sale-bot/bot/keep_alive.py
echo ""

echo "=== Search for these constants in handlers/ ==="
grep -rn "^OPEX_CATEGORIES\|^ASSET_CATEGORIES\|^FINANCE_ACCOUNTS\|^PAY_METHODS\|^PREPAID_CATEGORIES\|^_BIZ_START" /root/psvibe-sale-bot/handlers/ --include="*.py"
echo ""

echo "=== Search in main app.py for these ==="
grep -n "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS" /root/psvibe-sale-bot/app.py
