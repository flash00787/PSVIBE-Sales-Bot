# Check the ACTUAL function definitions in V.2 handler files
import os, re

handlers_dir = '/root/Sales-Tele-Bot_refactored/bot/handlers'

targets = {
    'prompt_member': ['sales.py'],
    'show_mm_menu': ['members.py'],
    'cmd_inventory': ['reports.py'],
    'cmd_today_report': ['reports.py'],
    'show_console_menu': ['console.py'],
    'cmd_staff_book_hub': ['booking.py'],
    'cmd_waitlist_mgmt': ['waitlist.py'],
    'cmd_staff_booking': ['booking.py'],
    'cmd_confirmed_bookings': ['booking.py'],
    'show_game_menu': ['games.py'],
    'cmd_financial_report': ['reports.py'],
    'show_main_menu': ['main_menu.py'],
    'next_voucher': ['sales.py'],
}

for func, expected_files in targets.items():
    for fname in expected_files:
        fpath = os.path.join(handlers_dir, fname)
        with open(fpath) as f:
            content = f.read()
        
        # Find the function definition including decorators
        lines = content.split('\n')
        found = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Check for various def patterns
            if (stripped == f'def {func}(' or 
                stripped.startswith(f'def {func}(') or
                stripped.startswith(f'async def {func}(') or
                stripped == f'async def {func}('):
                # Show the function signature
                print(f'{func:25s} → {fname}:{i+1} {stripped[:60]}')
                found = True
                # Check if it's just a stub
                next_lines = lines[i+1:i+5]
                for nl in next_lines:
                    if nl.strip():
                        print(f'  {nl.strip()[:80]}')
                break
        
        if not found:
            print(f'{func:25s} → {fname}: ❌ NOT FOUND (exact match)')
            # Check what IS in that file
            print(f'  Functions in {fname}:')
            for line in lines[:20]:
                stripped = line.strip()
                if stripped.startswith('def ') or stripped.startswith('async def '):
                    print(f'    {stripped[:50]}')
            print('  ... (first 20 lines shown)')
