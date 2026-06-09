echo "=== RECENT PY FILES ==="
find "/root/Aung Chan Myint/Sales-Tele-Bot" -name "*.py" -printf "%T+ %p\n" 2>&1 | sort -r | head -10

echo "==="
echo "=== PAYMENT CODE ==="
grep -c "Payment" "/root/Aung Chan Myint/Sales-Tele-Bot/main.py" 2>&1
grep -c "Wave\|CB Pay\|AYA Pay" "/root/Aung Chan Myint/Sales-Tele-Bot/main.py" 2>&1

echo "==="
echo "=== BOT PYTHON ==="
ps aux | grep python | grep -v grep

echo "==="
echo "=== NODE ==="
ps aux | grep node | grep -v grep

echo "==="
echo "=== SERVICE LIST ==="
systemctl list-units --type=service --all 2>&1 | head -30

echo "==="
echo "=== SCREEN/TMUX ==="
screen -ls 2>&1
tmux list-sessions 2>&1

echo "==="
echo "=== START_SH ==="
cat "/root/Aung Chan Myint/Sales-Tele-Bot/start.sh" 2>&1 | head -20

echo "==="
echo "=== MAIN_PY LAST 5 LINES ==="
tail -5 "/root/Aung Chan Myint/Sales-Tele-Bot/main.py" 2>&1

echo "==="
echo "=== MAIN_PY HEADER ==="
head -30 "/root/Aung Chan Myint/Sales-Tele-Bot/main.py" 2>&1
