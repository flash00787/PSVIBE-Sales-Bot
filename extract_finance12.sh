#!/bin/bash
echo "=== Check root __init__.py for constants ==="
grep -n "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|PREPAID_CATEGORIES\|_BIZ_START" /root/psvibe-sale-bot/__init__.py 2>/dev/null

echo ""
echo "=== Check refactored __init__ for constants ==="
grep -n "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|PREPAID_CATEGORIES\|_BIZ_START" /root/psvibe-sale-bot/__init___refactored.py 2>/dev/null

echo ""
echo "=== Check outer_minimal for constants ==="
grep -n "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|PREPAID_CATEGORIES\|_BIZ_START" /root/psvibe-sale-bot/__init___outer_minimal.py 2>/dev/null

echo ""
echo "=== Check main.py ==="
grep -n "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|PREPAID_CATEGORIES\|_BIZ_START" /root/psvibe-sale-bot/main.py 2>/dev/null

echo ""
echo "=== Check create_refactored_init.py ==="
grep -n "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|PREPAID_CATEGORIES\|_BIZ_START" /root/psvibe-sale-bot/create_refactored_init.py 2>/dev/null

echo ""
echo "=== Check handlers/ directory listing ==="
ls /root/psvibe-sale-bot/handlers/ 2>/dev/null

echo ""
echo "=== Check root handlers/__init__.py ==="
cat /root/psvibe-sale-bot/handlers/__init__.py 2>/dev/null | head -20

echo ""
echo "=== Grep recursively for the definition in handlers/ ==="
grep -rn "^OPEX_CATEGORIES\b" /root/psvibe-sale-bot/handlers/

echo ""
echo "=== Grep for in api_client ==="
grep -n "OPEX_CATEGORIES" /root/psvibe-sale-bot/bot/api_client.py
