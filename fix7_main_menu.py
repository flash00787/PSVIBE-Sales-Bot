#!/usr/bin/env python3
"""Fix 7: Remove BTN_FINANCIAL_REPORT and BTN_HELP from main menu keyboard."""
path = '/root/psvibe-sales-bot/bot/handlers/main_menu.py'
content = open(path).read()

# Remove BTN_FINANCIAL_REPORT and BTN_HELP from the keyboard layout
# Current layout:
# kb = [
#     [BTN_DAILY_SALES,      BTN_MEMBER_MGMT],
#     [BTN_CONSOLES,         BTN_TODAY_REPORT],
#     [BTN_STAFF_BOOK,       BTN_INVENTORY_VIEW],
#     [BTN_FINANCIAL_REPORT, BTN_ADMIN],
#     [BTN_HELP],
# ]
# New layout: remove BTN_FINANCIAL_REPORT row and BTN_HELP row, make BTN_ADMIN stand alone

old_kb = '''    kb = [
        [BTN_DAILY_SALES,      BTN_MEMBER_MGMT],
        [BTN_CONSOLES,         BTN_TODAY_REPORT],
        [BTN_STAFF_BOOK,       BTN_INVENTORY_VIEW],
        [BTN_FINANCIAL_REPORT, BTN_ADMIN],
        [BTN_HELP],
    ]'''

new_kb = '''    kb = [
        [BTN_DAILY_SALES,      BTN_MEMBER_MGMT],
        [BTN_CONSOLES,         BTN_TODAY_REPORT],
        [BTN_STAFF_BOOK,       BTN_INVENTORY_VIEW],
        [BTN_ADMIN],
    ]'''

if old_kb in content:
    content = content.replace(old_kb, new_kb)
    print('FIX 7 DONE: Removed BTN_FINANCIAL_REPORT and BTN_HELP from main menu')
else:
    print('FIX 7: Old keyboard pattern not found')
    idx = content.find('kb = [')
    if idx >= 0:
        print(f'  Found at position {idx}:')
        print(content[idx:idx+400])

open(path, 'w').write(content)
print('main_menu.py saved')
