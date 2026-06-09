const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`

echo "============================================"
echo " COUPON BUG FIX - PS VIBE GRAND OPENING"
echo " $(date)"
echo "============================================"

# ── STEP 1: Backups ──
echo ""
echo "=== Creating backups ==="
cp /root/psvibe-sales-bot/bot/handlers/sales.py /root/psvibe-sales-bot/bot/handlers/sales.py.bak.$(date +%s)
cp /root/psvibe-sales-bot/bot/handlers/console.py /root/psvibe-sales-bot/bot/handlers/console.py.bak.$(date +%s)
echo "✓ Backups created"

# ── STEP 2: Fix sales.py - Add coupon generation to launch_session_sale ──
echo ""
echo "=== FIX 1: Add coupon generation to launch_session_sale ==="
python3 << 'PYEOF'
import re

path = "/root/psvibe-sales-bot/bot/handlers/sales.py"
with open(path, "r") as f:
    content = f.read()

# Find the line: context.user_data["effective_cost_mins"] = effective_cost_mins
# And insert coupon generation BEFORE the wallet balance check
old = '''    context.user_data["effective_cost_mins"] = effective_cost_mins

    if wallet_balance >= effective_cost_mins:'''

new = '''    context.user_data["effective_cost_mins"] = effective_cost_mins

    # ── CashBack Coupon: Auto-generate via MySQL API ──
    if not is_guest and total_mins > 0 and not context.user_data.get("_cashback_coupon"):
        try:
            from bot.api_client import api_post
            gen_result = await asyncio.to_thread(
                api_post, "coupons/generate",
                {"member_id": member_id, "session_minutes": total_mins}
            )
            if gen_result and isinstance(gen_result, dict):
                cd = gen_result.get("coupon") or (gen_result.get("data") or {}).get("coupon")
                if cd and cd.get("code"):
                    context.user_data["_cashback_coupon"] = cd["code"]
                    context.user_data["_cashback_coupon_mins"] = cd.get("minutes", total_mins)
                    logger.warning("COUPON GEN OK (launch_sale): code=%s mins=%s member=%s", cd["code"], cd.get("minutes", total_mins), member_id)
                else:
                    logger.warning("COUPON GEN (launch_sale): no coupon in response: gen_result=%s", gen_result)
        except Exception as cb_e:
            logger.warning("Cashback coupon generation failed (non-critical): %s", cb_e)

    if wallet_balance >= effective_cost_mins:'''

if old in content:
    content = content.replace(old, new, 1)
    print("✓ Added coupon generation to launch_session_sale")
else:
    print("✗ Old pattern not found in launch_session_sale. Showing context:")
    # Try to find the line
    idx = content.find('context.user_data["effective_cost_mins"]')
    if idx >= 0:
        print(content[idx:idx+300])
    else:
        print("CANNOT FIND effective_cost_mins line!")

with open(path, "w") as f:
    f.write(content)
PYEOF

echo "Exit code: $?"

# ── STEP 3: Fix sales.py - Remove dead coupon reading from _end_single_session_and_launch ──
echo ""
echo "=== FIX 2: Remove dead coupon reading in _end_single_session_and_launch ==="
python3 << 'PYEOF'
path = "/root/psvibe-sales-bot/bot/handlers/sales.py"
with open(path, "r") as f:
    content = f.read()

# Remove the dead coupon reading lines
old = '''    # Capture coupon vars before clear
    coupon_code = d.get("_cashback_coupon", "")
    coupon_mins = d.get("_cashback_coupon_mins", 0)

    context.user_data.clear()'''

new = '''    context.user_data.clear()'''

if old in content:
    content = content.replace(old, new, 1)
    print("✓ Removed dead coupon reading from _end_single_session_and_launch")
else:
    # Try with different whitespace
    old2 = '''    # Capture coupon vars before clear
    coupon_code = d.get("_cashback_coupon", "")
    coupon_mins = d.get("_cashback_coupon_mins", 0)
    
    context.user_data.clear()'''
    if old2 in content:
        content = content.replace(old2, new, 1)
        print("✓ Removed dead coupon reading (alt whitespace)")
    else:
        print("✗ Dead coupon pattern not found in _end_single_session_and_launch")
        # Search for the pattern
        idx = content.find('Capture coupon vars before clear')
        if idx >= 0:
            print(f"  Found at offset {idx}:")
            print(content[idx:idx+200])
        else:
            print("  Pattern not found anywhere")

with open(path, "w") as f:
    f.write(content)
PYEOF

echo "Exit code: $?"

# ── STEP 4: Verify changes ──
echo ""
echo "=== VERIFY: Checking key sections ==="
echo ""
echo "--- launch_session_sale coupon block ---"
grep -n -A5 "CashBack Coupon: Auto-generate" /root/psvibe-sales-bot/bot/handlers/sales.py

echo ""
echo "--- Dead coupon reading removed? ---"
grep -n "Capture coupon vars before clear" /root/psvibe-sales-bot/bot/handlers/sales.py && echo "STILL PRESENT (BUG!)" || echo "✓ Removed"

echo ""
echo "--- console.py coupon generation still present? ---"
grep -n "CashBack Coupon: Auto-generate" /root/psvibe-sales-bot/bot/handlers/console.py

# ── STEP 5: Python syntax check ──
echo ""
echo "=== Python syntax check ==="
python3 -m py_compile /root/psvibe-sales-bot/bot/handlers/sales.py && echo "✓ sales.py syntax OK" || echo "✗ sales.py SYNTAX ERROR"
python3 -m py_compile /root/psvibe-sales-bot/bot/handlers/console.py && echo "✓ console.py syntax OK" || echo "✗ console.py SYNTAX ERROR"

echo ""
echo "============================================"
echo " FIXES APPLIED"
echo "============================================"
  `, (err, stream) => {
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.stderr.on('data', (chunk) => { data += 'STDERR: ' + chunk.toString(); });
    stream.on('close', () => {
      console.log(data);
      conn.end();
    });
  });
});
conn.on('error', (err) => { console.error('SSH Error:', err.message); });
conn.connect({ host: HOST, username: 'root', privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 25000 });
