# Find the KEY step functions from V.1 that handle button presses
# These are the logic that makes bot buttons work

with open('/root/Sales-Tele-Bot/main.py.bak.phase4') as f:
    v1_text = f.read()

# The 3 most critical step functions:
# step_main_menu - handles main menu button presses
# step_mm_menu - handles member management
# show_main_menu - shows the main menu keyboard

targets = ['def step_main_menu', 'def show_main_menu', 'def step_mm_menu', 'def step_mm_lookup']

for target in targets:
    if target not in v1_text:
        print(f'NOT FOUND: {target}')
        continue
    idx = v1_text.index(target)
    # Find the function body - next def
    next_def = v1_text.find('\ndef ', idx + 1)
    if next_def == -1:
        next_def = len(v1_text)
    
    body = v1_text[idx:next_def]
    print(f'\n{"="*60}')
    print(f'=== {target} ===')
    print(f'{"="*60}')
    print(body[:1500])
    if len(body) > 1500:
        print(f'\n... ({len(body) - 1500} more chars) ...')
