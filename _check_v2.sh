echo "=== V2 BOT FILES ==="
wc -l "/root/Aung Chan Myint/Sales-Tele-Bot/bot/app.py" "/root/Aung Chan Myint/Sales-Tele-Bot/bot/handlers.py" "/root/Aung Chan Myint/Sales-Tele-Bot/bot/__init__.py" 2>&1

echo "==="
echo "=== bot/app.py HEAD ==="
head -50 "/root/Aung Chan Myint/Sales-Tele-Bot/bot/app.py" 2>&1

echo "==="
echo "=== bot/app.py IMPORT CHECKS ==="
grep -n "^import\|^from\|^def \|^class \|^async def" "/root/Aung Chan Myint/Sales-Tele-Bot/bot/app.py" 2>&1 | head -30

echo "==="
echo "=== bot/__init__.py IMPORT CHECKS ==="
grep -n "^import\|^from\|^def \|^class \|^async def" "/root/Aung Chan Myint/Sales-Tele-Bot/bot/__init__.py" 2>&1 | head -30

echo "==="
echo "=== bot/handlers.py HEAD ==="
head -30 "/root/Aung Chan Myint/Sales-Tele-Bot/bot/handlers.py" 2>&1

echo "==="
echo "=== API SERVER HEAD ==="
head -50 "/root/Aung Chan Myint/Sales-Tele-Bot/api_server/api_server.js" 2>&1

echo "==="
echo "=== API SERVER RECEIPT==="
grep -n "receipt\|recipt\|RECEIPT" "/root/Aung Chan Myint/Sales-Tele-Bot/api_server/api_server.js" 2>&1 | head -20

echo "==="
echo "=== API HOME BTN ==="
grep -n "home\|Home\|HOME\|back\|Back\|BACK\|start\|Start\|START" "/root/Aung Chan Myint/Sales-Tele-Bot/api_server/api_server.js" 2>&1 | head -20

echo "==="
echo "=== BOT STRUCTURE ==="
ls -la "/root/Aung Chan Myint/Sales-Tele-Bot/bot/" 2>&1

echo "==="
echo "=== All Python files ==="
ls -la "/root/Aung Chan Myint/Sales-Tele-Bot/"*.py "/root/Aung Chan Myint/Sales-Tele-Bot/bot/"*.py 2>&1
