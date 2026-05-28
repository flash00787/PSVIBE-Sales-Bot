# Add re-exports to handlers/__init__.py so all handler files can access
# bot-level constants via from bot.handlers import *
path = '/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py'
with open(path) as f:
    content = f.read()

# Add re-exports after the existing imports but before __all__
re_exports = '''
# Re-export bot-level constants for handler files
from bot import (
    now_mmt,
    fetch_allowed_staff_ids,
    STOCK_ACCESS_PIN,
    ADMIN_PIN,
    BTN_DAILY_SALES, BTN_NEW_SALE,
    BTN_MEMBER_MGMT, BTN_CONSOLES,
    BTN_TODAY_REPORT, BTN_STAFF_BOOK,
    BTN_INVENTORY_VIEW, BTN_FINANCIAL_REPORT,
    BTN_ADMIN, BTN_GAMES,
    BTN_STOCK_MGMT, BTN_DISC_MGMT,
    BTN_SSD_DISC, BTN_FOOD_SETUP,
    BTN_ATTEND_DONE, BTN_ATTEND_NEXT, BTN_ATTEND_SKIP,
)
'''

# Find insertion point: after the last cross-module import but before __all__
# Or at the end of the file
if '__all__' in content:
    insertion_idx = content.index('__all__')
else:
    # Insert at end
    insertion_idx = len(content)

new_content = content[:insertion_idx] + re_exports + '\n' + content[insertion_idx:]

with open(path, 'w') as f:
    f.write(new_content)

print(f'DONE: Added re-exports to {path}')
print(f'File size: {len(new_content)} chars')
