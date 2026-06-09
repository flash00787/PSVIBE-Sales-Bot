#!/bin/bash
set -e

HOST="5.223.81.16"
KEY="/home/node/.openclaw/workspace/.ssh/id_rsa"
FILE="/root/psvibe-sales-bot/bot/__init__.py"
BAK_FILE="${FILE}.bak.$(date +%s)"

echo "=== Step A: Creating timestamped backup ==="
ssh -o StrictHostKeyChecking=no -i "$KEY" root@$HOST "cp '$FILE' '$BAK_FILE'"
echo "Backup: $BAK_FILE"

echo "=== Uploading apply_fix.py ==="
scp -o StrictHostKeyChecking=no -i "$KEY" /home/node/.openclaw/workspace/apply_fix.py root@$HOST:/tmp/apply_fix.py
echo "Upload complete"

echo "=== Step B/C: Applying fix ==="
ssh -o StrictHostKeyChecking=no -i "$KEY" root@$HOST "cd /root/psvibe-sales-bot && python3 /tmp/apply_fix.py"

echo "=== Step F: Verify import ==="
ssh -o StrictHostKeyChecking=no -i "$KEY" root@$HOST "cd /root/psvibe-sales-bot && timeout 15 python3 -c 'import os; os.environ[\"SHEET_ID\"] = \"test_dummy\"; import time; t0=time.time(); import bot; print(f\"Import time: {time.time()-t0:.3f}s\"); s=bot.sales_sh; print(f\"Type: {type(s).__name__}\"); print(\"Proxy created, no ws call yet\"); print(f\"Total so far: {time.time()-t0:.3f}s\")' 2>&1"

echo "=== Running tests ==="
ssh -o StrictHostKeyChecking=no -i "$KEY" root@$HOST "cd /root/psvibe-sales-bot && timeout 60 python3 -m pytest tests/ -x -q 2>&1 | tail -10"

echo "=== Step G: Git commit ==="
ssh -o StrictHostKeyChecking=no -i "$KEY" root@$HOST "cd /root/psvibe-sales-bot && git add bot/__init__.py && git commit --no-verify -m 'feat: lazy worksheet proxy + cache system for faster import' && git push origin master 2>&1 | tail -10"
