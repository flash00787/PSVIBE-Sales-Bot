with open('/root/psvibe-sales-bot/bot/handlers/__init__.py', 'r') as f:
    c = f.read()

# Fix: add BTN_FOOD_NOTE import AFTER the docstring closes
old = 'backward compatibility.\n"""'

new = 'backward compatibility.\n"""\nfrom bot import BTN_FOOD_NOTE  # noqa: F401'

# But the current file has the import INSIDE the docstring which is broken
# Let me fix by first finding the correct structure
if 'from bot import BTN_FOOD_NOTE' in c:
    # Already added but maybe in wrong place - fix it
    print('BTN_FOOD_NOTE import found')
    idx = c.find('from bot import BTN_FOOD_NOTE')
    print(f'Found at {idx}')
else:
    print('BTN_FOOD_NOTE import NOT found')

# Just rewrite the whole file properly
lines = c.split('\n')
new_lines = []
for line in lines:
    if 'from bot import BTN_FOOD_NOTE' in line:
        # Skip broken line inside docstring
        # The docstring line already has this text embedded
        print(f'Skipping broken import line: {repr(line)}')
    else:
        new_lines.append(line)

c = '\n'.join(new_lines)

# Fix the docstring
c = c.replace(
    '"""PS VIBE Bot \u2014 Handlers package\nfrom bot import BTN_FOOD_NOTE (Phase 6 refactor).',
    '"""PS VIBE Bot \u2014 Handlers package (Phase 6 refactor).'
)

# Now add proper import after docstring
c = c.replace(
    '"""\n# \u2550\u2550\u2550\u2550\u2550\u2550\u2550 Domain handler modules \u2550\u2550\u2550\u2550\u2550\u2550\u2550',
    '"""\nfrom bot import BTN_FOOD_NOTE  # noqa: F401\n# \u2550\u2550\u2550\u2550\u2550\u2550\u2550 Domain handler modules \u2550\u2550\u2550\u2550\u2550\u2550\u2550'
)

with open('/root/psvibe-sales-bot/bot/handlers/__init__.py', 'w') as f:
    f.write(c)

import ast
ast.parse(c)
print('FIXED AND SYNTAX OK')
