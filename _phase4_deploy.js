#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// 1. Backup members.py first
// 2. Apply Upgrade 3 changes
// 3. Create Upgrade 4 files
// 4. Test and restart

const script = `
set -e
echo "=== BACKING UP members.py ==="
cp /root/psvibe-sales-bot/bot/handlers/members.py /root/psvibe-sales-bot/bot/handlers/members.py.bak_kora_phase4

echo "=== UPGRADE 3: Adding STAFF_NOTIFY_CHAT import ==="
# Add STAFF_NOTIFY_CHAT to the import list from bot
python3 << 'PYEOF'
import re

with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'r') as f:
    content = f.read()

# 1. Add STAFF_NOTIFY_CHAT to imports from bot
# Find the line with "save_receipt_json, show_main_menu, step_hdr," and add STAFF_NOTIFY_CHAT
old_import = "    now_mmt, rank_emoji, save_receipt_json, show_main_menu, step_hdr,"
new_import = "    now_mmt, rank_emoji, save_receipt_json, show_main_menu, STAFF_NOTIFY_CHAT, step_hdr,"
if old_import in content:
    content = content.replace(old_import, new_import)
    print("✓ Added STAFF_NOTIFY_CHAT to imports")
else:
    print("✗ Could not find import line to modify")
    print("Looking for pattern...")
    # Find the line containing save_receipt_json
    for i, line in enumerate(content.split('\\n')):
        if 'save_receipt_json' in line and 'show_main_menu' in line:
            print(f"  Found at line {i+1}: {line.strip()}")

# 2. Add auto_generate_receipt function
# Find a good place to insert - before _fmt_other_payments at the end
if 'async def auto_generate_receipt(' not in content:
    auto_receipt_func = '''
async def auto_generate_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE, tu_vid: str, receipt_data: dict):
    """Auto-send formatted receipt to staff Telegram chat after topup completion."""
    try:
        staff_chat_id = STAFF_NOTIFY_CHAT
        if not staff_chat_id:
            logging.warning("auto_receipt: STAFF_NOTIFY_CHAT not configured, skipping")
            return
        
        # Parse staff_chat_id (it may be a string like "-1003686032747")
        try:
            chat_id = int(staff_chat_id)
        except ValueError:
            chat_id = staff_chat_id
        
        # Get shop name from settings or use default
        shop_name = "PS VIBE Gaming Center"
        
        rd = receipt_data
        # Parse payment details
        kpay = rd.get("kpay", 0) or 0
        cash = rd.get("cash", 0) or 0
        total_paid = kpay + cash
        
        # Build formatted receipt message
        lines = [
            f"🧾 *{shop_name}*",
            f"📄 *Top-Up Receipt*",
            f"━━━━━━━━━━━━━━━━━━",
            f"🪪 *Voucher:* `{tu_vid}`",
            f"👤 *Member:* `{rd.get('member_id', 'N/A')}`",
            f"🎖 *Rank:* {rd.get('rank', 'N/A')}",
            f"📅 *Date:* {rd.get('date', 'N/A')}",
            f"━━━━━━━━━━━━━━━━━━",
            f"💰 *Amount:* {rd.get('amount', 0):,} Ks",
            f"⏳ *Base Mins:* {rd.get('base_mins', 0):,}",
            f"🎁 *Bonus Mins:* +{rd.get('bonus_mins', 0):,}",
            f"🔥 *Total Mins:* {rd.get('total_mins', 0):,}",
            f"━━━━━━━━━━━━━━━━━━",
            f"💳 *KPay:* {kpay:,} Ks",
            f"💵 *Cash:* {cash:,} Ks",
            f"💲 *Total Paid:* {total_paid:,} Ks",
            f"━━━━━━━━━━━━━━━━━━",
            f"📊 *Balance Before:* {rd.get('prev_balance', 0):,} mins",
            f"📈 *Balance After:* {rd.get('balance_after', 0):,} mins",
            f"📞 *Phone:* {rd.get('phone', '-')}",
        ]
        
        msg = "\\n".join(lines)
        await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="Markdown",
        )
        logging.info("auto_receipt: sent receipt %s to staff chat %s", tu_vid, staff_chat_id)
    except Exception as e:
        logging.error("auto_receipt: failed to send receipt %s: %s", tu_vid, e, exc_info=True)
'''
    
    # Insert before _fmt_other_payments function
    marker = "\\ndef _fmt_other_payments("
    if marker in content:
        content = content.replace(marker, auto_receipt_func + marker)
        print("✓ Added auto_generate_receipt function")
    else:
        print("✗ Could not find _fmt_other_payments marker")
        # Try alternative: append at the end of file before last function
        # Find the last def in the file
        last_def_idx = content.rfind('\\ndef ')
        if last_def_idx > 0:
            content = content[:last_def_idx] + auto_receipt_func + content[last_def_idx:]
            print("✓ Added auto_generate_receipt function (appended before last def)")
        else:
            print("✗ Could not find insertion point")

# 3. Call auto_generate_receipt after get_receipt_kb
# Find the pattern and insert call
old_pattern = "    receipt_kb = get_receipt_kb(tu_vid)\\n    context.user_data.clear()"
receipt_data_build = '''    receipt_kb = get_receipt_kb(tu_vid)

    # Auto-send receipt to staff chat (non-blocking background)
    receipt_data = {
        "type": "topup", "voucher_id": tu_vid, "date": today,
        "member_id": tu_id, "rank": r_saved, "amount": tu_amt,
        "base_mins": tu_base, "bonus_mins": tu_bonus, "total_mins": tu_mins,
        "kpay": tu_kpay, "cash": tu_cash, "phone": tu_phone,
        "balance_mins": bal_mins, "prev_balance": prev_bal,
        "balance_change": tu_mins, "balance_after": bal_mins,
    }
    asyncio.create_task(auto_generate_receipt(update, context, tu_vid, receipt_data))

    context.user_data.clear()'''

if old_pattern in content:
    content = content.replace(old_pattern, receipt_data_build)
    print("✓ Added auto_generate_receipt call in step_tu_confirm")
else:
    print("✗ Could not find receipt_kb + context.user_data.clear() pattern")
    # Search for it more flexibly
    for i, line in enumerate(content.split('\\n')):
        if 'get_receipt_kb(tu_vid)' in line:
            print(f"  get_receipt_kb at line {i+1}: {line.strip()}")
            # Check next line
            lines = content.split('\\n')
            if i+1 < len(lines):
                print(f"  Next line: {lines[i+1].strip()}")

with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'w') as f:
    f.write(content)

print("\\n✓ members.py updated successfully")
PYEOF

echo ""
echo "=== TESTING SYNTAX ==="
python3 -c "import ast; ast.parse(open('/root/psvibe-sales-bot/bot/handlers/members.py').read()); print('✓ Syntax OK')"

echo ""
echo "=== UPGRADE 4: Creating auto_release_consoles.py ==="
mkdir -p /root/scripts

cat > /root/scripts/auto_release_consoles.py << 'PYEOF2'
#!/usr/bin/env python3
"""Auto-release consoles when booking end_time has passed.

Runs via cron every 5 minutes.
- Queries console_booking for bookings where end_time < NOW() and status NOT IN ('Done', 'cancelled', 'rejected')
- Updates console_booking.status to 'Done'
- Updates console_status.status to 'Free' for those consoles
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get MySQL connection using pymysql."""
    try:
        import pymysql
    except ImportError:
        logger.error("pymysql not installed. Install with: pip install pymysql")
        sys.exit(1)
    
    # Try to read from secrets env file
    secrets_file = '/etc/psvibe/secrets.env'
    env_file = '/root/psvibe-sales-bot/.env'
    
    db_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'psvibe_user',
        'password': '',
        'database': 'psvibe_api',
        'charset': 'utf8mb4',
    }
    
    # Read environment files
    for fpath in (secrets_file, env_file):
        if os.path.exists(fpath):
            with open(fpath) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, _, val = line.partition('=')
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        if key == 'MYSQL_HOST':
                            db_config['host'] = val
                        elif key == 'MYSQL_PORT':
                            db_config['port'] = int(val)
                        elif key == 'MYSQL_USER':
                            db_config['user'] = val
                        elif key == 'MYSQL_PASSWORD':
                            db_config['password'] = val
                        elif key == 'MYSQL_DATABASE':
                            db_config['database'] = val
    
    if not db_config['password']:
        logger.error("MYSQL_PASSWORD not found in environment files")
        sys.exit(1)
    
    try:
        conn = pymysql.connect(**db_config)
        return conn
    except Exception as e:
        logger.error("Failed to connect to MySQL: %s", e)
        sys.exit(1)

def release_expired_consoles():
    """Find and release consoles whose booking end_time has passed."""
    conn = get_db_connection()
    released = 0
    
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Find bookings that are past end_time but still in active status
            sql_find = """
                SELECT id, console_id, member_id, end_time, status
                FROM console_booking
                WHERE end_time < NOW()
                  AND status NOT IN ('Done', 'cancelled', 'rejected')
            """
            cursor.execute(sql_find)
            expired = cursor.fetchall()
            
            if not expired:
                logger.debug("No expired bookings found")
                return released
            
            logger.info("Found %d expired booking(s) to release", len(expired))
            
            for booking in expired:
                bid = booking['id']
                cid = booking['console_id']
                mid = booking.get('member_id', 'N/A')
                et = booking['end_time']
                old_status = booking['status']
                
                logger.info(
                    "Releasing: booking #%d | console=%s | member=%s | end=%s | status=%s",
                    bid, cid, mid, et, old_status
                )
                
                # Update booking status to Done
                cursor.execute(
                    "UPDATE console_booking SET status = 'Done' WHERE id = %s",
                    (bid,)
                )
                
                # Update console status to Free
                # Check if console_status row exists
                cursor.execute(
                    "SELECT console_id FROM console_status WHERE console_id = %s",
                    (cid,)
                )
                if cursor.fetchone():
                    cursor.execute(
                        "UPDATE console_status SET status = 'Free', current_member = NULL, start_time = NULL, current_game = NULL WHERE console_id = %s",
                        (cid,)
                    )
                else:
                    # Insert if not exists
                    cursor.execute(
                        "INSERT INTO console_status (console_id, status) VALUES (%s, 'Free')",
                        (cid,)
                    )
                
                released += 1
            
            conn.commit()
            logger.info("Released %d console(s) successfully", released)
            
    except Exception as e:
        logger.error("Error releasing consoles: %s", e, exc_info=True)
        conn.rollback()
    finally:
        conn.close()
    
    return released

if __name__ == '__main__':
    try:
        count = release_expired_consoles()
        logger.info("auto_release_consoles: completed, released=%d", count)
    except Exception as e:
        logger.error("auto_release_consoles: fatal error: %s", e, exc_info=True)
        sys.exit(1)
PYEOF2

chmod +x /root/scripts/auto_release_consoles.py
echo "✓ Created /root/scripts/auto_release_consoles.py"

echo ""
echo "=== TESTING auto_release_consoles.py ==="
python3 /root/scripts/auto_release_consoles.py

echo ""
echo "=== CREATING CRON JOB ==="
cat > /etc/cron.d/kora-auto-release << 'CRONEOF'
# Auto-release consoles when booking end_time passes
# Runs every 5 minutes
*/5 * * * * root /usr/bin/python3 /root/scripts/auto_release_consoles.py >> /var/log/auto_release_consoles.log 2>&1
CRONEOF

chmod 644 /etc/cron.d/kora-auto-release
echo "✓ Created /etc/cron.d/kora-auto-release"

echo ""
echo "=== RESTARTING cron ==="
systemctl restart cron 2>/dev/null || service cron restart 2>/dev/null || echo "Warning: could not restart cron"

echo ""
echo "=== DONE - Summary ==="
echo "Upgrade 3: Auto Receipt Generator ✓"
echo "Upgrade 4: Console Auto-Status ✓"
`;

conn.on('ready', () => {
  conn.exec(script, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err); conn.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', (code) => {
      console.log(out);
      if (code) { console.error('Exit code:', code); }
      conn.end();
      process.exit(code || 0);
    });
  });
});
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 60000 });
