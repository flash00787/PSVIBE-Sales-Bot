#!/bin/bash
# Multi-Branch Analysis - Read-Only Data Collection
# Run on VPS via SSH

echo "=== DATABASE TABLES ==="
docker exec psvibe-mysql mysql -u root -p"PsVibe@MySQL2024!" psvibe_api -e "SHOW TABLES" 2>&1

echo ""
echo "=== TABLE STRUCTURES (columns per table) ==="
for t in $(docker exec psvibe-mysql mysql -u root -p"PsVibe@MySQL2024!" psvibe_api -N -e "SHOW TABLES" 2>/dev/null); do
  echo "--- $t ---"
  docker exec psvibe-mysql mysql -u root -p"PsVibe@MySQL2024!" psvibe_api -e "DESCRIBE $t" 2>/dev/null
done

echo ""
echo "=== API SERVER STRUCTURE ==="
find /root/psvibe_api_server/ -type f -name "*.py" | sort

echo ""
echo "=== APP.PY FIRST 100 LINES ==="
head -100 /root/psvibe_api_server/app.py 2>/dev/null

echo ""
echo "=== DASHBOARD ROUTES FIRST 100 LINES ==="
head -100 /root/psvibe_api_server/dashboard_routes.py 2>/dev/null

echo ""
echo "=== API ROUTES (find all route decorators) ==="
grep -rn "@app\.route\|@bp\.route\|@.*\.route" /root/psvibe_api_server/ 2>/dev/null | head -80

echo ""
echo "=== SALE BOT STRUCTURE ==="
find /root/psvibe-sales-bot/bot/ -type f -name "*.py" 2>/dev/null | sort
echo "---"
find /root/psvibe-sales-bot/customer_bot/ -type f -name "*.py" 2>/dev/null | sort

echo ""
echo "=== SALE BOT MAIN HANDLER ==="
head -100 /root/psvibe-sales-bot/bot/main.py 2>/dev/null

echo ""
echo "=== CUSTOMER BOT MAIN HANDLER ==="
head -100 /root/psvibe-sales-bot/customer_bot/main.py 2>/dev/null

echo ""
echo "=== DASHBOARD STRUCTURE ==="
find /root/psvibe-dashboard/ -type f \( -name "*.vue" -o -name "*.ts" -o -name "*.js" \) 2>/dev/null | head -60

echo ""
echo "=== MODELS.PY ==="
head -200 /root/psvibe_api_server/models.py 2>/dev/null

echo ""
echo "=== DASHBOARD PACKAGE.JSON ==="
cat /root/psvibe-dashboard/package.json 2>/dev/null
