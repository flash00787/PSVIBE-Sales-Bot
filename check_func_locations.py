# Check where each function called by step_main_menu is DEFINED
import os, re

handlers_dir = '/root/Sales-Tele-Bot_refactored/bot/handlers'

targets = [
    'prompt_member', 'show_mm_menu', 'cmd_inventory',
    'cmd_today_report', 'show_console_menu', 'cmd_staff_book_hub',
    'cmd_waitlist_mgmt', 'cmd_staff_booking', 'cmd_confirmed_bookings',
    'show_game_menu', 'cmd_financial_report', 'show_main_menu',
    'next_voucher'
]

for target in targets:
    found_in = []
    for fname in sorted(os.listdir(handlers_dir)):
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(handlers_dir, fname)
        with open(fpath) as f:
            content = f.read()
        # Look for def target(
        if re.search(r'^def ' + re.escape(target) + r'\(', content, re.MULTILINE):
            found_in.append(fname)
    
    if found_in:
        print(f'{target:25s} → {", ".join(found_in)}')
    else:
        print(f'{target:25s} → ❌ NOT FOUND in any handler file')
