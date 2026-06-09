#!/bin/bash
cd /root/psvibe-sales-bot
python3 -c "
import ast
with open('bot/handlers/console.py') as f:
    ast.parse(f.read())
print('SYNTAX OK')
"
echo "---GIT STATUS---"
git status --short bot/handlers/console.py
echo "---COMMIT---"
git add bot/handlers/console.py
git commit -m "fix: console status time display 24h->12h AM/PM format"
echo "---VERIFY LINES---"
sed -n '53p;74p' bot/handlers/console.py
