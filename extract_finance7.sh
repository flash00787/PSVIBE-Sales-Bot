#!/bin/bash
BOT="/root/psvibe-sale-bot"

echo "=== __init__.py: Search for OPEX string ==="
grep -n "OPEX\|Asset\|Prepaid\|Capital" "$BOT/bot/__init__.py" | grep -v "BTN_\|#\|__all__\|State\." | head -20

echo ""
echo "=== Search for list assignments with these names ==="
grep -n "OPEX_CATEGORIES\s*=" "$BOT/bot/"*.py
grep -rn "OPEX_CATEGORIES\s*=" "$BOT/bot/" --include="*.py"

echo ""
echo "=== finance.py - check what's imported ==="
grep "^from\|^import" "$BOT/bot/handlers/finance.py"

echo ""
echo "=== all .py files in bot/ ==="
ls "$BOT/bot/"*.py

echo ""
echo "=== api_client.py - check for constants ==="
grep "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|PREPAID_CATEGORIES\|_BIZ_START" "$BOT/bot/api_client.py" | head -10
