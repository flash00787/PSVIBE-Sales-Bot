#!/bin/bash
export BOT_TOKEN="8545665013:AAFgEuw4V_715Q9yzGOYloinIdbdYXYb8zU"
export SHEET_ID="1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA"
export REPLIT_DOMAINS="07a3cf31-be6c-4d8c-b122-3082fdfc84b0-00-3lcqto7dw05k3.worf.replit.dev"
export STOCK_PIN="123123"

cd /root/Sales-Tele-Bot
pkill -f "python3 main.py" 2>/dev/null; sleep 1
nohup .venv/bin/python3 main.py >> bot.log 2>&1 &
echo "Bot started (PID $!)"
