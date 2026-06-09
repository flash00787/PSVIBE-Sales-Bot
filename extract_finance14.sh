#!/bin/bash

echo "=== Search for 'Rent' as a string in __init__.py ==="
grep -n '"Rent"' /root/psvibe-sale-bot/bot/__init__.py
echo ""

echo "=== Search for '\"Utility\"'  ==="
grep -n 'Utility' /root/psvibe-sale-bot/bot/__init__.py
echo ""

echo "=== Search for list of strings pattern containing these keywords ==="
grep -n "Rent\|Utility\|Marketing\|Maintenance\|Cash Box\|MMQR\|KBZ Bank\|AYA Bank\|Bank Transfer" /root/psvibe-sale-bot/bot/__init__.py | head -20
echo ""

echo "=== Check bot/handlers/finance.py for any variable definition after functions ==="
grep -n "^[A-Z_]\+\s*=" /root/psvibe-sale-bot/bot/handlers/finance.py | head -20
