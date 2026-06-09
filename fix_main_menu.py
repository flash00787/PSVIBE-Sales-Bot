path = '/root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py'
with open(path) as f:
    lines = f.readlines()

# Line 0: from bot.handlers import * instead of from bot import *
lines[0] = 'from bot.handlers import *\n'

# Insert line 1 with BTN constants
lines.insert(1, 'from bot import BTN_DAILY_SALES, BTN_NEW_SALE, BTN_MEMBER_MGMT, BTN_CONSOLES, BTN_TODAY_REPORT, BTN_STAFF_BOOK, BTN_INVENTORY_VIEW, BTN_FINANCIAL_REPORT, BTN_ADMIN, BTN_GAMES, BTN_STOCK_MGMT, BTN_DISC_MGMT, BTN_SSD_DISC, BTN_FOOD_SETUP, now_mmt, fetch_allowed_staff_ids\n')

with open(path, 'w') as f:
    f.writelines(lines)

print('DONE: main_menu.py fixed')
print('Line 1:', lines[1].strip())
print('Line 2:', lines[2].strip() if len(lines) > 2 else 'N/A')
