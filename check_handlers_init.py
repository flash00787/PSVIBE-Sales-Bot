# Check what handlers/__init__.py actually exports in __all__
import os, re

handlers_init = '/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py'
with open(handlers_init) as f:
    content = f.read()

# Find __all__ assignment
all_match = re.search(r'__all__\s*=\s*\[(.*?)\]', content, re.DOTALL)
if all_match:
    all_items = all_match.group(1)
    print('__all__ items:')
    for item in all_items.split(','):
        item = item.strip().strip("'").strip('"').strip()
        if item:
            print(f'  - {item}')
    print(f'\nTotal: {all_items.count(",") + 1} items')
else:
    print('No __all__ found in handlers/__init__.py')
    
# Check if handlers/__init__.py imports from bot
if 'from bot import' in content:
    print('\nhandlers/__init__.py DOES import from bot')
else:
    print('\nhandlers/__init__.py does NOT import from bot')
