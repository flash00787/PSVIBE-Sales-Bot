#!/bin/bash
cd "/root/Aung Chan Myint/Sales-Tele-Bot"
pkill -f "python3 main.py" 2>/dev/null
pkill -f "python3 customer_bot.py" 2>/dev/null
sleep 2
SHEET_ID="1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA" API_BASE_URL=http://localhost:3000 REPLIT_DOMAINS="07a3cf31-be6c-4d8c-b122-3082fdfc84b0-00-3lcqto7dw05k3.worf.replit.dev" STOCK_PIN=481999 nohup .venv/bin/python3 main.py >> main.log 2>&1 &
echo "MAIN=$!"
sleep 2
CUSTOMER_BOT_TOKEN=8639289328:AAEltJxEgcGbc5D09EHcmMpmCgaaB71vWYs API_BASE_URL=http://localhost:3000 STAFF_NOTIFY_CHAT=-1003686032747 GEMINI_API_KEY=AIzaSyBTYPxX-GZQ1kBuQ-KVGZ19C6cdbO_jWOg nohup .venv/bin/python3 customer_bot.py >> customer.log 2>&1 &
echo "CUST=$!"
sleep 8
echo "---BOTS---"
ps aux | grep python3 | grep -v grep
echo "---MAIN_LOG---"
tail -5 main.log
echo "---CUST_LOG---"
tail -10 customer.log
