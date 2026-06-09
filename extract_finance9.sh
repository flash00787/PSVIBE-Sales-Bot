#!/bin/bash
BOT="/root/psvibe-sale-bot"

echo "=== Last 60 lines of finance.py ==="
tail -60 "$BOT/bot/handlers/finance.py"

echo ""
echo "=== Check if constants defined in root psvibe-sale-bot ==="
ls "$BOT/"*.py 2>/dev/null
echo ""

echo "=== Search whole project for OPEX_CATEGORIES ==="
grep -rn "OPEX_CATEGORIES" "$BOT/" --include="*.py" 2>/dev/null
