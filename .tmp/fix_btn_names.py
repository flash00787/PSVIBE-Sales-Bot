# Fix 1: __init__.py - rename BTN_FOOD_SALE and add BTN_FOOD_NOTE
with open('/root/psvibe-sales-bot/bot/__init__.py', 'r') as f:
    content = f.read()

# 1a. Add BTN_FOOD_NOTE to __all__
content = content.replace(
    "'BTN_FOOD_SALE', 'BTN_YES_END_SESSION'",
    "'BTN_FOOD_NOTE', 'BTN_FOOD_SALE', 'BTN_YES_END_SESSION'"
)

# 1b. Rename constant and add new one
old_btn = 'BTN_FOOD_SALE      = "\U0001f4dd Food Note"'
new_btn = 'BTN_FOOD_SALE      = "Food Sale"\nBTN_FOOD_NOTE      = "\U0001f4dd Food Note"'
content = content.replace(old_btn, new_btn)

with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
    f.write(content)
print('init DONE')

# Fix 2: console.py - use BTN_FOOD_NOTE
with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'r') as f:
    content = f.read()

content = content.replace('BTN_FOOD_SALE', 'BTN_FOOD_NOTE')

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'w') as f:
    f.write(content)
print('console DONE')

# Fix 3: app.py - add BTN_FOOD_NOTE handler
with open('/root/psvibe-sales-bot/bot/app.py', 'r') as f:
    content = f.read()

# Import BTN_FOOD_NOTE
content = content.replace(
    'BTN_FOOD_SALE, BTN_STAFF_BOOK',
    'BTN_FOOD_NOTE, BTN_FOOD_SALE, BTN_STAFF_BOOK'
)

# Add entry point handler for BTN_FOOD_NOTE
old_line = 'MessageHandler(filters.Regex(r"^" + re.escape(BTN_FOOD_SALE) + r"$"), cmd_food_sale),'
new_line = old_line + '\n            MessageHandler(filters.Regex(r"^" + re.escape(BTN_FOOD_NOTE) + r"$"), cmd_food_sale),'

# Replace both occurrences (entry + fallback)
content = content.replace(old_line, new_line)

with open('/root/psvibe-sales-bot/bot/app.py', 'w') as f:
    f.write(content)
print('app DONE')
