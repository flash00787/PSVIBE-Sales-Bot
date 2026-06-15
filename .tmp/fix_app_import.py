with open('/root/psvibe-sales-bot/bot/app.py', 'r') as f:
    c = f.read()

# Add BTN_FOOD_NOTE to the explicit import in app.py
# Since 'from bot import (...)' is used, add BTN_FOOD_NOTE before BTN_FOOD_SALE
# The import has 'BTN_FOOD_SALE' which was already from the earlier fix
# But the NameError shows it's not resolving through wildcard

old = 'BTN_FOOD_NOTE, BTN_FOOD_SALE, BTN_STAFF_BOOK'
# This was added earlier, but the error persists because the wildcard chain doesn't expose it
# Let me check if we need to also import from bot directly

# Actually, the simplest fix: add BTN_FOOD_NOTE to the from bot import (...) list
import re
# Find the import block
idx1 = c.find('from bot import (')
if idx1 >= 0:
    # Find end of import block
    idx2 = c.find(')', idx1)
    import_block = c[idx1:idx2]
    # Check if BTN_FOOD_NOTE is NOT in this block but IS defined in bot
    if 'BTN_FOOD_NOTE' not in import_block:
        # Add it into the block near BTN_FOOD_SALE
        c = c.replace(
            'BTN_FOOD_SALE, BTN_STAFF_BOOK',
            'BTN_FOOD_NOTE, BTN_FOOD_SALE, BTN_STAFF_BOOK'
        )
        print('Added BTN_FOOD_NOTE to explicit import')
    else:
        print('BTN_FOOD_NOTE already in explicit import')
else:
    print('No from bot import block found')

with open('/root/psvibe-sales-bot/bot/app.py', 'w') as f:
    f.write(c)

import ast
ast.parse(c)
print('SYNTAX OK')
