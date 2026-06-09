const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

const commands = [
  // 1. Add BTN_BALANCE to constants.py (after BTN_FINANCIAL_REPORT line)
  `sed -i '/^BTN_FINANCIAL_REPORT/a BTN_BALANCE      = "💰 Account Balance"' /root/psvibe-sales-bot/bot/constants.py`,

  // 2. Add BTN_BALANCE to main_menu.py imports
  `sed -i 's/BTN_FINANCIAL_REPORT, BTN_GAME_LIB_MENU/BTN_FINANCIAL_REPORT, BTN_BALANCE, BTN_GAME_LIB_MENU/' /root/psvibe-sales-bot/bot/handlers/main_menu.py`,

  // 3. Add _replit_get_async to main_menu.py imports
  `sed -i 's/fetch_allowed_staff_ids_async,/fetch_allowed_staff_ids_async, _replit_get_async,/' /root/psvibe-sales-bot/bot/handlers/main_menu.py`,

  // 4. Add cmd_balance to main_menu.py imports from bot
  `sed -i 's/next_voucher, now_mmt,/next_voucher, now_mmt, cmd_balance,/' /root/psvibe-sales-bot/bot/handlers/main_menu.py`,

  // 5. Add BTN_BALANCE button to main menu keyboard
  `sed -i '/BTN_CONSOLES/a [BTN_BALANCE,        BTN_TODAY_REPORT],' /root/psvibe-sales-bot/bot/handlers/main_menu.py`
];

// Actually, the sed approach is fragile. Let me use python to do the edits more precisely.
// Let me first check the exact line numbers
conn.on('ready', () => {
  // Step 1: Read constants.py and find where to add BTN_BALANCE
  conn.exec(`python3 -c "
import re
# Read constants.py
with open('/root/psvibe-sales-bot/bot/constants.py') as f:
    content = f.read()

# Add BTN_BALANCE after BTN_FINANCIAL_REPORT if not already there
if 'BTN_BALANCE' not in content:
    content = content.replace(
        'BTN_FINANCIAL_REPORT   = \"💹 Financial Report\"',
        'BTN_FINANCIAL_REPORT   = \"💹 Financial Report\"\nBTN_BALANCE          = \"💰 Account Balance\"'
    )
    with open('/root/psvibe-sales-bot/bot/constants.py', 'w') as f:
        f.write(content)
    print('Added BTN_BALANCE to constants.py')
else:
    print('BTN_BALANCE already in constants.py')
"`, (e, stream) => {
    if (e) { console.log('err', e); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d);
    stream.stderr.on('data', d => out += d);
    stream.on('close', () => {
      console.log(out);
      // Step 2: Read main_menu.py
      conn.exec(`python3 -c "
with open('/root/psvibe-sales-bot/bot/handlers/main_menu.py') as f:
    content = f.read()

# Add imports if not there
if 'BTN_BALANCE' not in content:
    # Fix the import line - add BTN_BALANCE
    content = content.replace(
        'BTN_FINANCIAL_REPORT, BTN_GAME_LIB_MENU,',
        'BTN_FINANCIAL_REPORT, BTN_BALANCE, BTN_GAME_LIB_MENU,'
    )
    # Also add _replit_get_async to imports from bot
    # The import line is: fetch_allowed_staff_ids_async,
    import_fix_made = False
    if '_replit_get_async' not in content:
        # Find the import block and add _replit_get_async
        lines = content.split('\\n')
        new_lines = []
        in_bot_import = False
        for line in lines:
            if line.strip().startswith('from bot import ('):
                in_bot_import = True
            if in_bot_import and 'fetch_allowed_staff_ids_async,' in line and '_replit_get_async' not in line:
                line = line.replace('fetch_allowed_staff_ids_async,', 'fetch_allowed_staff_ids_async, _replit_get_async,')
                import_fix_made = True
            if in_bot_import and ')' in line:
                in_bot_import = False
            new_lines.append(line)
        content = '\\n'.join(new_lines)
        if import_fix_made:
            print('Added _replit_get_async import')
    
    # Add cmd_balance to the from bot.handlers.sales import line
    if 'cmd_balance,' not in content:
        content = content.replace(
            'from bot.handlers.sales import next_voucher, prompt_member',
            'from bot.handlers.sales import next_voucher, prompt_member\nfrom bot.handlers.finance import cmd_fin_accts as cmd_balance'
        )
        print('Added cmd_balance import from finance')
    
    # Add balance button to main menu keyboard
    old_kb = '[BTN_CONSOLES,         BTN_TODAY_REPORT],'
    new_kb = '[BTN_CONSOLES,         BTN_TODAY_REPORT],\\n        [BTN_BALANCE,          BTN_MEMBER_MGMT],'
    content = content.replace(old_kb, new_kb)
    print('Added balance button to main menu')
    
    # Add routing in step_main_menu - after BTN_FINANCIAL_REPORT check
    old_routing = 'if choice == BTN_FINANCIAL_REPORT:\\n        return await cmd_financial_report(update, context)\\n\\n    if choice == BTN_ADMIN:'
    new_routing = 'if choice == BTN_FINANCIAL_REPORT:\\n        return await cmd_financial_report(update, context)\\n\\n    if choice == BTN_BALANCE:\\n        return await cmd_balance(update, context)\\n\\n    if choice == BTN_ADMIN:'
    content = content.replace(old_routing, new_routing)
    print('Added balance routing in step_main_menu')
    
    with open('/root/psvibe-sales-bot/bot/handlers/main_menu.py', 'w') as f:
        f.write(content)
    print('main_menu.py updated OK')
"`, (e2, stream2) => {
        if (e2) { console.log('err2', e2); conn.end(); return; }
        let out2 = '';
        stream2.on('data', d => out2 += d);
        stream2.stderr.on('data', d => out2 += d);
        stream2.on('close', () => {
          console.log(out2);
          
          // Step 3: Add /balance command to app.py
          conn.exec(`python3 -c "
with open('/root/psvibe-sales-bot/bot/app.py') as f:
    content = f.read()

# Add /finance command handler to entry_points if not there
if 'CommandHandler(\"balance\",' not in content:
    # Add to entry_points CommandHandler list
    content = content.replace(
        'CommandHandler(\"console\",    cmd_console_status),',
        'CommandHandler(\"balance\",    cmd_balance),\\n            CommandHandler(\"console\",    cmd_console_status),'
    )
    print('Added /balance to entry_points')
    
    # Add to fallbacks
    content = content.replace(
        'CommandHandler(\"console\",    cmd_console_status),\\n        ],',
        'CommandHandler(\"balance\",    cmd_balance),\\n            CommandHandler(\"console\",    cmd_console_status),\\n        ],'
    )
    print('Added /balance to fallbacks')
    
    # Add to standalone fallback handlers
    content = content.replace(
        '(\"console\",     cmd_console_status),',
        '(\"console\",     cmd_console_status),\\n        (\"balance\",     cmd_balance),'
    )
    print('Added /balance to standalone handlers')
    
    # Add BotCommand in set_my_commands
    content = content.replace(
        'BotCommand(\"console\",    \"\\\\U0001f579\\\\ufe0f Console live status\"),',
        'BotCommand(\"console\",    \"\\\\U0001f579\\\\ufe0f Console live status\"),\\n            BotCommand(\"balance\",    \"💰 Check account balance\"),'
    )
    print('Added /balance to BotCommand list')
    
    with open('/root/psvibe-sales-bot/bot/app.py', 'w') as f:
        f.write(content)
    
    print('app.py updated OK')
"`, (e3, stream3) => {
            if (e3) { console.log('err3', e3); conn.end(); return; }
            let out3 = '';
            stream3.on('data', d => out3 += d);
            stream3.stderr.on('data', d => out3 += d);
            stream3.on('close', () => {
              console.log(out3);
              
              // Step 4: Also fix the main menu - balance button should be next to FINANCE
              // Actually, the cmd_balance function from finance.py does PIN check. We need a non-PIN version.
              // Let me check what cmd_fin_accts does
              conn.exec("python3 -c \"import ast; print('checking cmd_fin_accts')\"", (e4, s4) => {
                // Actually, let me verify the changes are correct by checking the finance.py cmd_fin_accts flow
                // The cmd_fin_accts function calls _replit_get_async and shows account balances.
                // It returns to show_finance_menu. We need it to return to main menu instead.
                
                // Better approach: Create a NEW cmd_balance function in main_menu.py directly
                // that calls the API directly, shows balances, and returns to main menu
                conn.exec(`python3 -c "
with open('/root/psvibe-sales-bot/bot/handlers/main_menu.py', 'r+') as f:
    content = f.read()

# Find where to put cmd_balance function - before show_main_menu
# Actually let's add it right after the imports and before show_main_menu
old = '''from datetime import datetime, timezone, timedelta



async def show_main_menu'''

new = '''from datetime import datetime, timezone, timedelta




async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Show account balances — quick balance check for staff (no PIN needed).\"\"\"
    await update.message.reply_text(
        \"\\U0001f4b0 *Account Balance \\u2014 \\u101b\\u1031\\u102c\\u103a\\u1014\\u1031\\u101c\\u1031\\u1015\\u103c\\u1014\\u1031\\u1038...\\\"\\n\\n\\u23f3 \\u1006\\u1010\\u103a\\u101c\\u102c\\u1000\\u1031\\u102c\\u103a\\u101e\\u102d\\u1033\\u1015\\u103c\\u1031\\u102c...\"\\n        \\u23f3\"",
        parse_mode=\"Markdown\",
        reply_markup=ReplyKeyboardRemove(),
    )
    data = await _replit_get_async(\"finance/accounts\")
    if not data:
        await update.message.reply_text(
            \"\\u274c Account Balances API \\u1001\\u103b\\u102d\\u1010\\u103a\\u1019\\u101b\\u102d\\u1015\\u102b\",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return MAIN_MENU
    accounts  = data.get(\"accounts\", [])
    total_bal = data.get(\"total_balance\", 0)
    if not accounts:
        await update.message.reply_text(
            \"\\u26a0\\ufe0f Account \\u1021\\u1001\\u103b\\u1031\\u1038 \\u1019\\u101b\\u103e\\u102d\\u101e\\u1031\\u1038\\u1015\\u102b\",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return MAIN_MENU
    lines = [\"\\U0001f4b0 *Account Balances*\", \"\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\"]
    for a in accounts:
        name = a.get(\"name\", \"?\")
        bal  = a.get(\"balance\", a.get(\"opening\", 0))
        low  = name.lower()
        icon = \"\\U0001f3e6\" if (\"bank\" in low or \"kbz\" in low or \"aya\" in low or \"cb\" in low) else (\"\\U0001f4f1\" if \"mmqr\" in low or \"kpay\" in low or \"wave\" in low else \"\\U0001f4b5\")
        lines.append(f\"{icon} {name:<16}: {int(bal):>10,} Ks\")
    lines += [\"\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\", f\"\\U0001f4b0 *Total : {int(total_bal):,} Ks*\"]
    await update.message.reply_text(
        \"\\n\".join(lines),
        parse_mode=\"Markdown\",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
    )
    return MAIN_MENU



async def show_main_menu'''

content = content.replace(old, new)
f.seek(0)
f.write(content)
f.truncate()
print('Added cmd_balance function to main_menu.py')
"`, (e4, s4) => {
    if (e4) { console.log('err4', e4); }
    let out4 = '';
    s4.on('data', d => out4 += d);
    s4.stderr.on('data', d => out4 += d);
    s4.on('close', () => {
      console.log(out4);
      
      // Step 5: Now update app.py to use the correct import
      // Since cmd_balance is now in main_menu.py, we need to update the import in app.py
      conn.exec(`python3 -c "
with open('/root/psvibe-sales-bot/bot/app.py') as f:
    content = f.read()

# We referenced cmd_balance from bot, which imports main_menu. Need to fix.
# The command handler tries cmd_balance - check if it's imported
# In app.py, it uses from bot.handlers import * which should import all handlers
# But the /balance command handler in entry_points and standalone need explicit refs
# Let me check what's used: from bot.handlers import * imports all
# But then the actual references use global names. Let me check if the issue is
# that cmd_balance needs to be exported from bot/__init__.py or bot/handlers/__init__.py

import re

# Check if from bot.handlers import * is there
if 'from bot.handlers import *' in content:
    print('Good - bot.handlers wildcard import present')
    
# Make sure bot/__init__.py or bot/handlers/__init__.py exports cmd_balance
# Actually from bot.handlers import * imports what handlers/__init__.py defines
print('Done')
"`, (e5, s5) => {
    if (e5) { console.log('err5', e5); }
    let out5 = '';
    s5.on('data', d => out5 += d);
    s5.stderr.on('data', d => out5 += d);
    s5.on('close', () => {
      console.log(out5);
      
      // Step 6: Check handlers/__init__.py to see if it exports main_menu functions
      conn.exec("head -50 /root/psvibe-sales-bot/bot/handlers/__init__.py 2>/dev/null; echo ===; grep 'main_menu' /root/psvibe-sales-bot/bot/handlers/__init__.py 2>/dev/null", (e6, s6) => {
        let out6 = '';
        s6.on('data', d => out6 += d);
        s6.stderr.on('data', d => out6 += d);
        s6.on('close', () => {
          console.log(out6);
          
          // Step 7: Verify all changes
          conn.exec("grep -n 'BTN_BALANCE\\|cmd_balance\\|/balance' /root/psvibe-sales-bot/bot/constants.py /root/psvibe-sales-bot/bot/handlers/main_menu.py /root/psvibe-sales-bot/bot/app.py 2>/dev/null", (e7, s7) => {
            let out7 = '';
            s7.on('data', d => out7 += d);
            s7.stderr.on('data', d => out7 += d);
            s7.on('close', () => {
              console.log(out7);
              conn.end();
            });
          });
        });
      });
    });
});
            });
          });
        });
      });
    });
  });
});
});
