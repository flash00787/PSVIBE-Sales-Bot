#!/bin/bash
BOT="/root/psvibe-sale-bot"

echo "=== Line 1-12 of finance.py ==="
head -12 "$BOT/bot/handlers/finance.py"
echo ""

echo "=== Search for OPEX_CATEGORIES ==="
grep -n "OPEX_CATEGORIES\|= \[" "$BOT/bot/handlers/finance.py" | head -20
echo ""

echo "=== Line 2520-2560 of finance.py (bottom) ==="
wc -l "$BOT/bot/handlers/finance.py"
echo ""
echo "=== Discount.py full file (first 100 lines) ==="
head -100 "$BOT/bot/handlers/discount.py"
echo ""

echo "=== Discount.py remaining lines 100-350 ==="
sed -n '100,350p' "$BOT/bot/handlers/discount.py"
