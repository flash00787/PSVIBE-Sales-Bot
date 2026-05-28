# Find how _replit_get etc are defined in V.2
# These are missing from handler file comparison

import os, re

base_dir = '/root/Sales-Tele-Bot_refactored/bot'

# Search across ALL .py files in the bot package
replit_funcs = ['_replit_get', '_replit_post', '_replit_patch', '_api_base', '_do', '_f']

for target_func in replit_funcs:
    found_in = []
    for root, dirs, files in os.walk(base_dir):
        for fname in files:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath) as f:
                content = f.read()
            if re.search(r'^def ' + re.escape(target_func) + r'\(', content, re.MULTILINE):
                found_in.append(os.path.relpath(fpath, base_dir))
    
    if found_in:
        print(f'{target_func:20s} → {", ".join(found_in)}')
    else:
        print(f'{target_func:20s} → ❌ NOT FOUND ANYWHERE')

# Also check how handlers access data:
# Is there a shared data module?
print('\n=== Search for shared data modules ===')
for root, dirs, files in os.walk(base_dir):
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath) as f:
            content = f.read()
        if '_replit' in content.lower() or 'gspread' in content.lower():
            rel = os.path.relpath(fpath, '/root/Sales-Tele-Bot_refactored')
            print(f'  {rel}')
