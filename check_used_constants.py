# Check what bot-level constants each handler file uses
import os
import re

handlers_dir = '/root/Sales-Tele-Bot_refactored/bot/handlers'

# Constants defined in bot/__init__.py (not handler functions)
# These are the ones that won't be available via from bot.handlers import *
bot_constants = [
    'STOCK_ACCESS_PIN', 'ADMIN_PIN', 'ADMIN_ATTEND_LIMIT',
    'WAITLIST_LIMIT', 'CANCELLATION_REASON', 'PAYMENT_OPTIONS',
    'BUNDLE_GAMES_CONFIG', 'FOC_ITEMS', 'BOOKING_DEFAULTS',
    'SHIFT_TIMES', 'CONSOLE_PRICES',
    'BTN_DAILY_SALES', 'BTN_NEW_SALE', 'BTN_MEMBER_MGMT',
    'BTN_CONSOLES', 'BTN_TODAY_REPORT', 'BTN_STAFF_BOOK',
    'BTN_INVENTORY_VIEW', 'BTN_FINANCIAL_REPORT', 'BTN_ADMIN',
    'BTN_GAMES', 'BTN_STOCK_MGMT', 'BTN_DISC_MGMT',
    'BTN_SSD_DISC', 'BTN_FOOD_SETUP',
    'BTN_ATTEND_DONE', 'BTN_ATTEND_NEXT', 'BTN_ATTEND_SKIP',
    'now_mmt', 'fetch_allowed_staff_ids',
]

for fname in sorted(os.listdir(handlers_dir)):
    if not fname.endswith('.py') or fname == '__init__.py':
        continue
    fpath = os.path.join(handlers_dir, fname)
    with open(fpath) as f:
        content = f.read()
    
    # Find which constants are USED in this file (not defined)
    used = []
    for const in bot_constants:
        if const in content:
            # Check it's actually used (not a comment or string)
            for line in content.split('\n'):
                if const in line and not line.strip().startswith('#') and 'def ' not in line:
                    used.append(const)
                    break
    
    if used:
        print(f'{fname}: needs {len(used)} bot constants')
        for c in used:
            print(f'    {c}')
