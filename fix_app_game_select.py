#!/usr/bin/env python3
"""Register SALE_GAME_SELECT state in app.py."""
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    content = f.read()

# 1. Add SALE_GAME_SELECT to imports
if 'SALE_GAME_SELECT' not in content:
    # Find the import block and add after SALE_CONFIRM
    content = content.replace(
        'SALE_CONFIRM,',
        'SALE_CONFIRM,\n    SALE_GAME_SELECT,'
    )
    print("1. Added SALE_GAME_SELECT to imports")

# 2. Register state in conv handler
# Find the place to insert - after PAY_AMOUNT and before SALE_CONFIRM
# Actually, insert it between ADJUST_TIME and FOOD_MENU
# Since game select happens after console and before mins
registration = '''
            SALE_GAME_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_select)],
'''
# Insert after the MINS registration
marker = "            MINS:            [MessageHandler(filters.TEXT & ~filters.COMMAND, step_mins)],"
if marker in content:
    content = content.replace(marker, marker + registration)
    print("2. Registered SALE_GAME_SELECT state")
else:
    print("2. WARNING: MINS registration not found")

# 3. Import step_game_select from sales.py
# step_game_select should be imported from sales
# Check if sales handlers are imported
marker2 = "from bot.handlers.sales import ("
if marker2 in content:
    # Check if step_game_select is already imported
    if 'step_game_select' not in content:
        content = content.replace(
            'step_sale_confirm,',
            'step_game_select,\n    step_sale_confirm,'
        )
        print("3. Added step_game_select import")
else:
    print("3. WARNING: sales import not found")

with open(filepath, 'w') as f:
    f.write(content)

print("Done!")
