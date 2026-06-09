import os

# For ALL handler files that use from bot import *:
# Change to from bot.handlers import * 
# AND add inline BTN constants where needed
# 
# This is the only way to break the circular dependency:
# bot/__init__.py -> imports handlers -> handler.py -> imports bot (CIRCULAR!)
# bot/handlers/__init__.py -> imports handler.py -> handler.py -> imports bot.handlers (OK!)

base = '/root/Sales-Tele-Bot_refactored/bot/handlers'

# BTN constants needed across files
BTN_VARS = {
    'BTN_DAILY_SALES': '"🛒 Daily Sales"',
    'BTN_NEW_SALE': '"🆕 New Sale"',
    'BTN_MEMBER_MGMT': '"👥 Member Management"', 
    'BTN_CONSOLES': '"🕹️ Consoles"',
    'BTN_TODAY_REPORT': '"📋 Today Report"',
    'BTN_STAFF_BOOK': '"📅 Customer Booking"',
    'BTN_INVENTORY_VIEW': '"📦 View Inventory"',
    'BTN_FINANCIAL_REPORT': '"💰 Financial Report"',
    'BTN_ADMIN': '"⚙️ Admin Panel"',
    'BTN_GAMES': '"🎮 Games"',
    'BTN_STOCK_MGMT': '"📊 Stock Management"',
    'BTN_DISC_MGMT': '"🏷️ Discount Management"',
    'BTN_SSD_DISC': '"🔄 SSD Discount"',
    'BTN_FOOD_SETUP': '"🍽️ Food Setup"',
    'BTN_ATTEND_DONE': '"✅ ပြီးပါပြီ"',
    'BTN_ATTEND_NEXT': '"➡️ နောက် Staff"',
    'BTN_ATTEND_SKIP': '"⏩ Skip (0)"',
}

files = sorted(os.listdir(base))
for fname in files:
    if not fname.endswith('.py') or fname == '__init__.py':
        continue
    fpath = os.path.join(base, fname)
    with open(fpath) as f:
        content = f.read()
    
    modified = False
    lines = content.split('\n')
    
    # Fix 1: Replace 'from bot import *' with 'from bot.handlers import *'
    if 'from bot import *' in lines[0] if lines else '':
        lines[0] = 'from bot.handlers import *'
        modified = True
        print(f'{fname}: changed from bot import * -> from bot.handlers import *')
    elif 'from bot import *' in content:
        # Find which line it's on
        for i, line in enumerate(lines):
            if 'from bot import *' in line:
                lines[i] = 'from bot.handlers import *'
                modified = True
                print(f'{fname}: changed from bot import * -> from bot.handlers import * (line {i+1})')
                break
    elif 'from bot import' in content and 'now_mmt' in content:
        # Replace: from bot import now_mmt -> from bot.handlers import *
        for i, line in enumerate(lines):
            if 'from bot import' in line:
                lines[i] = 'from bot.handlers import *'
                modified = True
                print(f'{fname}: changed from bot import now_mmt -> from bot.handlers import *')
                break
    # Also handle app.py which is not in handlers dir
    # It should keep its own imports
    
    # Fix 2: Add inline BTN constants if the file uses them and doesn't have from bot import at all
    if not modified and not any('from bot' in line for line in lines[:5]):
        # File has no bot import at all - add from bot.handlers import *
        first_import = None
        for i, line in enumerate(lines[:5]):
            if line.startswith('import ') or line.startswith('from '):
                first_import = i
                break
        
        if first_import is not None:
            lines.insert(first_import, 'from bot.handlers import *\n')
            print(f'{fname}: added from bot.handlers import *')
        else:
            # No imports at all - add after docstring
            for i, line in enumerate(lines[:5]):
                if '"""' in line or "'''" in line:
                    continue
                if line.strip() == '':
                    lines.insert(i, 'from bot.handlers import *')
                    print(f'{fname}: added from bot.handlers import * after docstring')
                    break
            else:
                if lines[0].startswith('"'):
                    lines.insert(1, 'from bot.handlers import *')
                    print(f'{fname}: added from bot.handlers import * early')
                else:
                    lines.insert(0, 'from bot.handlers import *')
                    print(f'{fname}: added from bot.handlers import * at top')
    
    # Fix 3: Remove line with from bot import * that might be left as duplicate
    lines = [l for l in lines if l.strip() != 'from bot import *']
    
    # Clean up multiple consecutive blank lines at top
    cleaned = []
    blank_count = 0
    for line in lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 2:
                cleaned.append(line)
        else:
            blank_count = 0
            cleaned.append(line)
    
    if modified or cleaned != lines:
        with open(fpath, 'w') as f:
            f.write('\n'.join(cleaned))
        print(f'  Written to {fname}')
