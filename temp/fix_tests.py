#!/usr/bin/env python3
"""Fix tests: conftest async re-exports + STOCK_PIN env var"""
import re

# Fix 1: conftest.py - add async re-export aliases
with open('/root/psvibe-sales-bot/tests/conftest.py', 'r') as f:
    content = f.read()

old = '_handler_reexports = ['
if old in content:
    idx = content.index(old)
    # Find the closing bracket
    close_idx = content.index(']', idx)
    # Find last comma before closing bracket
    before_close = content[idx:close_idx]
    # Insert new entries before the ]
    insert = (
        '            "create_booking_async", "end_booking_async", "cancel_booking_async",\n'
        '            "fetch_console_status_async", "fetch_games_async",\n'
        '            "fetch_console_games_async", "get_consoles_with_game_async",\n'
        '            "get_games_on_console_async", "add_console_game_async",\n'
        '            "remove_console_game_async", "fetch_promotions_cached_async",\n'
        '            "fetch_game_library_async",\n'
        '        '
    )
    content = content[:close_idx] + insert + content[close_idx:]
    with open('/root/psvibe-sales-bot/tests/conftest.py', 'w') as f:
        f.write(content)
    print('conftest.py: FIXED - added async re-exports')
else:
    print('conftest.py: _handler_reexports not found')

# Fix 2: STOCK_PIN env var
with open('/root/psvibe-sales-bot/bot/__init__.py', 'r') as f:
    content2 = f.read()

old2 = 'STOCK_ACCESS_PIN    = os.environ["STOCK_PIN"]'
new2 = 'STOCK_ACCESS_PIN    = os.environ.get("STOCK_PIN", "")'

if old2 in content2:
    content2 = content2.replace(old2, new2)
    with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
        f.write(content2)
    print('STOCK_PIN: FIXED')
else:
    print(f'STOCK_PIN: PATTERN NOT FOUND. Looking for: {repr(old2)}')
    # Try alternative
    pattern = r'STOCK_ACCESS_PIN\s*=\s*os\.environ\["STOCK_PIN"\]'
    if re.search(pattern, content2):
        content2 = re.sub(pattern, 'STOCK_ACCESS_PIN    = os.environ.get("STOCK_PIN", "")', content2)
        with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
            f.write(content2)
        print('STOCK_PIN: FIXED (regex)')

print('ALL DONE')
