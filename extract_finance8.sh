#!/bin/bash
BOT="/root/psvibe-sale-bot"

echo "=== Full search for category definitions in __init__.py ==="
grep -n "OPEX_CATEGORIES\b\|= \[\"Rent\|= \[\"Utility\|= \[\"Salary\|= \[\"Marketing" "$BOT/bot/__init__.py"
echo ""

echo "=== Read lines 1350-1450 of __init__.py ==="
sed -n '1350,1450p' "$BOT/bot/__init__.py"
echo ""

echo "=== Read lines 1450-1550 of __init__.py ==="
sed -n '1450,1550p' "$BOT/bot/__init__.py"
