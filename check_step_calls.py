# Check main_menu.py step_main_menu for cross-module function calls
# Identify which functions it calls from OTHER handler files

import ast, re

mm_path = '/root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py'
with open(mm_path) as f:
    mm_text = f.read()

# Find step_main_menu body
if 'def step_main_menu' in mm_text:
    idx = mm_text.index('def step_main_menu')
    # Find next def at same indent level
    rest = mm_text[idx + len('def step_main_menu'):]
    # Find function signatures at column 0
    next_def = None
    for m in re.finditer(r'^def \w+\(', rest, re.MULTILINE):
        next_def = idx + len('def step_main_menu') + m.start()
        break
    
    if next_def is None:
        body = mm_text[idx:]
    else:
        body = mm_text[idx:next_def]
    
    print(f'step_main_menu body: {len(body)} chars')
    print('=' * 60)
    print(body[:2000])
    print('\n... (truncated) ...' if len(body) > 2000 else '')
    
    # Extract function calls made from step_main_menu
    # Look for await some_function(...
    calls = re.findall(r'await\s+(\w+)\(', body)
    print(f'\n\n=== Calls made from step_main_menu:')
    for call in sorted(set(calls)):
        # Find which file defines this function
        print(f'  await {call}()')
