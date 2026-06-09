import sys
path = '/root/Sales-Tele-Bot_refactored/bot/__init__.py'
with open(path) as f:
    content = f.read()

# Add missing BTN constants from V.1
missing = [
    '\nBTN_ATTEND_DONE  = "✅ ပြီးပါပြီ"\n',
    'BTN_ATTEND_NEXT  = "➡️ နောက် Staff"\n',
    'BTN_ATTEND_SKIP  = "⏩ Skip (0)"\n',
]

# Fix wrong Burmese characters
content = content.replace('မထည့်', 'မထည့်')

# Also check for FINANCE_MENU which might be missing
# Find insertion point - after BTN_ADD_CONSOLE block area, before BotState
# Actually let's just find a good place to insert after all BTN_* definitions
# Look for where all BTN_* defs end - after last BTN_ definition
lines = content.split('\n')
last_btn_idx = -1
for i, line in enumerate(lines):
    if line.strip().startswith('BTN_') and '=' in line:
        last_btn_idx = i

if last_btn_idx >= 0 and 'BTN_ATTEND_DONE' not in content:
    for j, ins in enumerate(missing):
        lines.insert(last_btn_idx + 1 + j, ins)
    content = '\n'.join(lines)
    print('Added missing BTN_ATTEND_* constants')
else:
    print('ATTEND constants already present or not found')

# Fix the SKIP_DISC/EMAIL Burmese character
if 'မထည့်' in content:
    print('Burmese chars fixed')

# Also add to __all__ if needed
if 'BTN_ATTEND_DONE' in content and 'BTN_ATTEND_DONE' not in content.split('__all__')[0]:
    # Need to add to __all__  - find __all__ list
    all_idx = content.find('__all__')
    if all_idx >= 0:
        # Add after BTN_ADMIN_SAL_ADV in __all__ list
        all_end = content.find(']', all_idx)
        if all_end >= 0 and 'BTN_ATTEND_DONE' not in content[all_idx:all_end]:
            insert_all = ", 'BTN_ATTEND_DONE', 'BTN_ATTEND_NEXT', 'BTN_ATTEND_SKIP'"
            content = content[:all_end] + insert_all + content[all_end:]
            print('Added to __all__')

with open(path, 'w') as f:
    f.write(content)
print('DONE')
