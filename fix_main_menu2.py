path = '/root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py'
with open(path) as f:
    lines = f.readlines()

new = [lines[0]]  # keep from bot.handlers import *
new.append('# BTN constants (inline to avoid circular import)\n')
new.append('BTN_DAILY_SALES = "\U0001f6d2 Daily Sales"\n')
new.append('BTN_NEW_SALE = "\U0001f195 New Sale"\n')
new.append('BTN_MEMBER_MGMT = "\U0001f465 Member Management"\n')
new.append('BTN_CONSOLES = "\U0001f579\ufe0f Consoles"\n')
new.append('BTN_TODAY_REPORT = "\U0001f4cb Today Report"\n')
new.append('BTN_STAFF_BOOK = "\U0001f4c5 Customer Booking"\n')
new.append('BTN_INVENTORY_VIEW = "\U0001f4e6 View Inventory"\n')
new.append('BTN_FINANCIAL_REPORT = "\U0001f4b0 Financial Report"\n')
new.append('BTN_ADMIN = "\u2699\ufe0f Admin Panel"\n')
new.append('BTN_GAMES = "\U0001f3ae Games"\n')
new.append('BTN_STOCK_MGMT = "\U0001f4ca Stock Management"\n')
new.append('BTN_DISC_MGMT = "\U0001f3f7\ufe0f Discount Management"\n')
new.append('BTN_SSD_DISC = "\U0001f504 SSD Discount"\n')
new.append('BTN_FOOD_SETUP = "\U0001f37d\ufe0f Food Setup"\n')
new.append('\n')
new.extend(lines[2:])

with open(path, 'w') as f:
    f.writelines(new)
print('DONE:', len(new), 'lines')
