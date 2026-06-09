#!/usr/bin/env node
const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`
echo '=== Verifying all app.py handler functions are defined ==='
python3 -c "
import re
import sys

# Read app.py
with open('/root/Sales-Tele-Bot_refactored/bot/app.py') as f:
    app_content = f.read()

# Extract all function names referenced in add_handler / MessageHandler / CommandHandler / ConversationHandler states
all_refs = set()
for m in re.finditer(r'(?:step_|show_|cmd_|error_handler|cb_|_auth_middleware|fetch_|handle_|prompt_|launch_)[a-z_]+', app_content):
    all_refs.add(m.group())

# Read all handler files
all_funcs = set()
for mod_name in ['bot/handlers/main_menu.py', 'bot/handlers/admin.py', 'bot/handlers/admin_bookings.py',
                 'bot/handlers/attendance.py', 'bot/handlers/booking.py', 'bot/handlers/booking_flow.py',
                 'bot/handlers/broadcast.py', 'bot/handlers/commands.py', 'bot/handlers/console.py',
                 'bot/handlers/console_mgmt.py', 'bot/handlers/discount.py', 'bot/handlers/finance.py',
                 'bot/handlers/games.py', 'bot/handlers/ginst.py', 'bot/handlers/help.py',
                 'bot/handlers/members.py', 'bot/handlers/notify.py', 'bot/handlers/payroll.py',
                 'bot/handlers/referral.py', 'bot/handlers/reports.py', 'bot/handlers/salary_adv.py',
                 'bot/handlers/sales.py', 'bot/handlers/ssd_disc.py', 'bot/handlers/stock.py',
                 'bot/handlers/stock_in.py', 'bot/handlers/waitlist.py']:
    try:
        with open('/root/Sales-Tele-Bot_refactored/' + mod_name) as f:
            content = f.read()
        for m in re.finditer(r'^def ([a-z_]+)|^async def ([a-z_]+)', content, re.MULTILINE):
            all_funcs.add(m.group(1) or m.group(2))
    except FileNotFoundError:
        print(f'  [WARN] {mod_name} not found', file=sys.stderr)

# Check missing functions
missing = all_refs - all_funcs
if missing:
    print(f'MISSING {len(missing)} functions in handler files:')
    for fn in sorted(missing):
        print(f'  - {fn}')
else:
    print('ALL functions present in handler modules!')
"
`, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d.toString());
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
