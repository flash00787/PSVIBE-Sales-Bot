#!/bin/bash
echo "=== Read lines 1300-1395 of __init__.py ==="
sed -n '1300,1395p' /root/psvibe-sale-bot/bot/__init__.py
echo ""
echo "=== Search __init__.py for list assignments ==="
grep -n "= \[" /root/psvibe-sale-bot/bot/__init__.py | grep -i "opex\|asset\|prepaid\|account\|pay_method\|biz_start\|category\|categories" 
echo ""
echo "=== Read lines around common locations for lists ==="
grep -n "Rent\|Utility\|Salary\|Marketing\|Maintenance\|Supplies\|Equipment\|Furniture\|Electronics\|Console\|Cash\|MMQR\|KBZ\|AYA\|Bank Transfer\|KPay" /root/psvibe-sale-bot/bot/__init__.py | head -30
