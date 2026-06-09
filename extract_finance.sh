#!/bin/bash
# Extract all finance/staff/payroll handler details from PS Vibe bot
BOT_DIR="/root/psvibe-sale-bot"

echo "======== FINANCE HANDLERS (finance.py) ========"
cat "$BOT_DIR/bot/handlers/finance.py"

echo ""
echo "======== ATTENDANCE HANDLERS (attendance.py) ========"
cat "$BOT_DIR/bot/handlers/attendance.py"

echo ""
echo "======== PAYROLL HANDLERS (payroll.py) ========"
cat "$BOT_DIR/bot/handlers/payroll.py"

echo ""
echo "======== SALARY ADVANCE HANDLERS (salary_adv.py) ========"
cat "$BOT_DIR/bot/handlers/salary_adv.py"

echo ""
echo "======== DISCOUNT HANDLERS (discount.py) ========"
cat "$BOT_DIR/bot/handlers/discount.py"

echo ""
echo "======== REPORTS HANDLERS (reports.py) ========"
cat "$BOT_DIR/bot/handlers/reports.py"

echo ""
echo "======== REFERRAL HANDLERS (referral.py) ========"
cat "$BOT_DIR/bot/handlers/referral.py"

echo ""
echo "======== STATE DEFINITIONS from __init__.py ========"
grep -n "= range(" "$BOT_DIR/bot/__init__.py" | head -80

echo ""
echo "======== SHEET REFERENCES from __init__.py ========"
grep -n "worksheet\|_sh\s*=\|\.open\|sheet1\|get_worksheet" "$BOT_DIR/bot/__init__.py" | head -60
