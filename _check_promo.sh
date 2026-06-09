echo "=== Sheet defs in bot/__init__.py ==="
sed -n '95,135p' "/root/Aung Chan Myint/Sales-Tele-Bot/bot/__init__.py"

echo "==="
echo "=== Sheet defs in main.py ==="
sed -n '100,130p' "/root/Aung Chan Myint/Sales-Tele-Bot/main.py"

echo "==="
echo "=== Promotions refs (after fix) ==="
grep -n 'Promotions_Discounts\|\"Promotions\"\|\"Promotions_Log\"' "/root/Aung Chan Myint/Sales-Tele-Bot/bot/"*.py 2>/dev/null | head -5
grep -n 'Promotions_Discounts\|\"Promotions\"\|\"Promotions_Log\"' "/root/Aung Chan Myint/Sales-Tele-Bot/main.py" 2>/dev/null | head -5
grep -n 'Promotions_Discounts\|\"Promotions\"\|\"Promotions_Log\"' "/root/Aung Chan Myint/Sales-Tele-Bot/api_server/api_server.js" 2>/dev/null | head -5
