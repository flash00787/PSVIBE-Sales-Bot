#!/bin/bash
# Look at the split_handlers_v3.py which may contain the original definitions
echo "=== grep in split_handlers_v3.py ==="
grep -n "OPEX_CATEGORIES\|ASSET_CATEGORIES\|FINANCE_ACCOUNTS\|PAY_METHODS\|PREPAID_CATEGORIES\|_BIZ_START" /root/psvibe-sale-bot/split_handlers_v3.py | head -20

echo ""
echo "=== Read first 100 lines of bot/__init__.py for any list definition ==="
grep -n "^OPEX_CATEGORIES\|^ASSET_CATEGORIES\|^FINANCE_ACCOUNTS\|^PAY_METHODS\|^PREPAID_CATEGORIES\|^_BIZ_START\|^= \[" /root/psvibe-sale-bot/bot/__init__.py | head -30

echo ""
echo "=== Lines 100-130 (before __all__) ==="
sed -n '100,130p' /root/psvibe-sale-bot/bot/__init__.py

echo ""
echo "=== Lines 1200-1230 (around button definitions) ==="
sed -n '1200,1230p' /root/psvibe-sale-bot/bot/__init__.py
