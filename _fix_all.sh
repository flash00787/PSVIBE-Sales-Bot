#!/bin/bash
# Fix all bugs on VPS - run via SSH
DIR="/root/Aung Chan Myint/Sales-Tele-Bot"

echo "=== FIX 1: Auth check for main.py ==="
# Read current show_main_menu
CUR=$(sed -n '1461,1500p' "$DIR/main.py")
if echo "$CUR" | grep -q "Access Denied"; then
    echo "Auth already exists in main.py"
else
    # Add _ALLOWED_USER_IDS and auth check before show_main_menu
    python3 << 'PYEOF'
import re
with open("/root/Aung Chan Myint/Sales-Tele-Bot/main.py") as f:
    content = f.read()

# Add _ALLOWED_USER_IDS before show_main_menu
old = "async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):"
new = '''_ALLOWED_USER_IDS: set[int] = {8539344655, 8336350778, 6296803251}

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Auth check
    user = update.effective_user
    if not user or user.id not in _ALLOWED_USER_IDS:
        await update.message.reply_text(
            "🚫 *Access Denied*\\n"
            "ဒီ bot ကို authorized staff တွေသာ သုံးနိုင်ပါတယ်။",
            parse_mode="Markdown",
        )
        return

'''

if old in content and "_ALLOWED_USER_IDS" not in content:
    content = content.replace(old, new, 1)
    with open("/root/Aung Chan Myint/Sales-Tele-Bot/main.py", "w") as f:
        f.write(content)
    print("AUTH ADDED")
else:
    if "_ALLOWED_USER_IDS" in content:
        print("AUTH ALREADY EXISTS")
    else:
        print("FAIL: show_main_menu not found!")
PYEOF
fi

echo "=== FIX 2: Fix start script with BOT_TOKEN ==="
python3 << 'PYEOF'
import re
with open("/root/Aung Chan Myint/Sales-Tele-Bot/start_bots_v3.sh") as f:
    content = f.read()

# The main.py line needs BOT_TOKEN and API_KEY
old_main_line = "SHEET_ID=\"1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA\" API_BASE_URL=http://localhost:3000"
new_main_line = "SHEET_ID=\"1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA\" API_BASE_URL=http://localhost:3000 BOT_TOKEN=\"8545665013:AAFgEuw4V_715Q9yzGOYloinIdbdYXYb8zU\" API_KEY=\"JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ\""

if old_main_line in content and "BOT_TOKEN" not in content:
    content = content.replace(old_main_line, new_main_line, 1)
    with open("/root/Aung Chan Myint/Sales-Tele-Bot/start_bots_v3.sh", "w") as f:
        f.write(content)
    print("START SCRIPT FIXED")
else:
    print("START SCRIPT OK or already fixed")
PYEOF

echo "=== FIX 3: Reduce API timeouts in main.py ==="
python3 << 'PYEOF'
with open("/root/Aung Chan Myint/Sales-Tele-Bot/main.py") as f:
    content = f.read()

# Reduce default timeouts from 30s to 8s
changes = 0
old_get = "def _replit_get(path: str, timeout: int = 30):"
new_get = "def _replit_get(path: str, timeout: int = 8):"
if old_get in content:
    content = content.replace(old_get, new_get)
    changes += 1

old_post = "def _replit_post(path: str, body: dict, timeout: int = 30):"
new_post = "def _replit_post(path: str, body: dict, timeout: int = 8):"
if old_post in content:
    content = content.replace(old_post, new_post)
    changes += 1

# Also reduce the hardcoded 10s timeout to 6s for patch
old_patch_timeout = "timeout=10)"
new_patch_timeout = "timeout=6)"
if "timeout=10)" in content:
    content = content.replace(old_patch_timeout, new_patch_timeout)
    changes += 1

with open("/root/Aung Chan Myint/Sales-Tele-Bot/main.py", "w") as f:
    f.write(content)
print(f"TIMEOUTS REDUCED: {changes} changes")
PYEOF

echo "=== FIX 4: Start API server ==="
# Check if port 3000 already in use
if ss -tlnp | grep -q ":3000 "; then
    echo "API already running on port 3000"
else
    cd "$DIR/api_server" && nohup node api_server.js >> api_server.log 2>&1 &
    API_PID=$!
    echo "API started with PID: $API_PID"
    sleep 2
    if ss -tlnp | grep -q ":3000 "; then
        echo "API is listening on port 3000 ✅"
    else
        echo "API failed to start ❌"
        tail -5 api_server.log
    fi
fi

echo "=== FIX 5: Verify all syntax ==="
python3 -c "import ast; ast.parse(open('$DIR/main.py').read()); print('main.py PASS')" 2>&1
python3 -c "import ast; ast.parse(open('$DIR/bot/__init__.py').read()); print('__init__.py PASS')" 2>&1
python3 -c "import ast; ast.parse(open('$DIR/bot/handlers.py').read()); print('handlers.py PASS')" 2>&1
python3 -c "import ast; ast.parse(open('$DIR/bot/app.py').read()); print('app.py PASS')" 2>&1

echo "=== ALL FIXES COMPLETE ==="
