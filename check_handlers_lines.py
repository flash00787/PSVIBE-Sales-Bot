# Fix bot/__init__.py to re-export all handler functions at bot level
# Then change ALL handler files to use from bot import * (which will include 
# handler functions via the __init__.py re-export chain)

# Step 1: Find where bot/__init__.py imports handlers
# Step 2: Add re-export line
path = '/root/Sales-Tele-Bot_refactored/bot/__init__.py'
with open(path) as f:
    content = f.read()

# Check if there's a handlers import
if 'from bot.handlers import' in content:
    # It already re-exports handlers. The problem is circular import.
    print('bot/__init__.py already imports handlers')
    print('The issue is in individual handler files not seeing each other')
else:
    print('No handlers import found in bot/__init__.py')

# The REAL fix: Each handler file should use from bot.handlers import * 
# instead of from bot import *
# AND have BTN constants available another way

# Check which handler files need fixing
import os
handlers_dir = '/root/Sales-Tele-Bot_refactored/bot/handlers'
for fname in sorted(os.listdir(handlers_dir)):
    if not fname.endswith('.py') or fname == '__init__.py':
        continue
    fpath = os.path.join(handlers_dir, fname)
    with open(fpath) as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip() if fpath else ''
    # Skip main_menu.py (already fixed with inline BTN constants)
    print(f'{fname}: {first_line[:50]}')
