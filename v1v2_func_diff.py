# Find ALL functions in V.2 handler files
import os, re

handlers_dir = '/root/Sales-Tele-Bot_refactored/bot/handlers'
V1_PATH = '/root/Sales-Tele-Bot/main.py.bak.phase4'

# Read V.1 functions
with open(V1_PATH) as f:
    v1_text = f.read()

v1_funcs = set()
for m in re.finditer(r'^def (\w+)\(', v1_text, re.MULTILINE):
    v1_funcs.add(m.group(1))

# Read all V.2 functions
v2_funcs = {}
for fname in sorted(os.listdir(handlers_dir)):
    if not fname.endswith('.py'):
        continue
    fpath = os.path.join(handlers_dir, fname)
    with open(fpath) as f:
        content = f.read()
    for m in re.finditer(r'^def (\w+)\(', content, re.MULTILINE):
        v2_funcs[m.group(1)] = fname
    for m in re.finditer(r'^async def (\w+)\(', content, re.MULTILINE):
        v2_funcs[m.group(1)] = fname

# Find V.1 functions MISSING in V.2
missing_in_v2 = set()
for func in v1_funcs:
    if func not in v2_funcs:
        missing_in_v2.add(func)

print(f'=== V.1 functions: {len(v1_funcs)}')
print(f'=== V.2 functions: {len(v2_funcs)}')
print(f'=== Missing in V.2: {len(missing_in_v2)}')
print()

# Show functions that step_main_menu needs but are missing
step_needs = {
    'next_voucher', 'prompt_member', 'show_mm_menu', 'cmd_inventory',
    'cmd_today_report', 'show_console_menu', 'cmd_staff_book_hub',
    'cmd_waitlist_mgmt', 'cmd_staff_booking', 'cmd_confirmed_bookings',
    'show_game_menu', 'cmd_financial_report', 'show_main_menu'
}

print('=== Critical functions missing:')
for fn in sorted(step_needs & missing_in_v2):
    print(f'  {fn}')

# Also show _ prefixed helper functions missing
underscore_missing = [f for f in sorted(missing_in_v2) if f.startswith('_')]
print(f'\n=== Missing helper functions (_*): {len(underscore_missing)}')
for fn in underscore_missing[:30]:
    print(f'  {fn}')
if len(underscore_missing) > 30:
    print(f'  ... and {len(underscore_missing)-30} more')

# Show all missing
print(f'\n=== ALL missing functions:')
for fn in sorted(missing_in_v2):
    print(f'  {fn}')
