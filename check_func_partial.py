# Search for PARTIAL matches - V.2 might have renamed these functions
import os, re

handlers_dir = '/root/Sales-Tele-Bot_refactored/bot/handlers'

targets = [
    'prompt_member', 'show_mm_menu', 'cmd_inventory',
    'cmd_today_report', 'show_console_menu', 'cmd_staff_book_hub',
    'cmd_waitlist_mgmt', 'cmd_staff_booking', 'cmd_confirmed_bookings',
    'show_game_menu', 'cmd_financial_report', 'show_main_menu',
    'next_voucher'
]

# Search broader - maybe async def, maybe different prefix
for target in targets:
    found_in = {}
    for fname in sorted(os.listdir(handlers_dir)):
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(handlers_dir, fname)
        with open(fpath) as f:
            content = f.read()
        
        # Look for def target( anywhere (including async def)
        if re.search(r'^async?\s+def\s+' + re.escape(target) + r'\(', content, re.MULTILINE):
            found_in[fname] = 'exact'
        # Look for function containing parts of the name
        elif target.replace('cmd_', '') in content and target[:4] == 'cmd_':
            alt = target.replace('cmd_', 'handle_')
            if alt in content:
                found_in[fname] = f'~{alt}'
        # Check if any function the file defines matches the concept
        elif target.replace('cmd_', '') in content.lower():
            found_in[fname] = 'similar_name'
    
    if found_in:
        print(f'{target:30s}')
        for fname, match_type in found_in.items():
            print(f'  → {fname} ({match_type})')
    else:
        print(f'{target:30s} → ❌ Complete MISS')
