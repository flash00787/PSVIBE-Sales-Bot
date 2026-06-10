#!/usr/bin/env python3
"""Fix conftest: add ALL async re-export aliases + STOCK_PIN env var"""

# Fix 1: conftest.py - add ALL async re-export aliases
with open('/root/psvibe-sales-bot/tests/conftest.py', 'r') as f:
    content = f.read()

# All async re-export aliases from bot/__init__.py (both early and late definitions)
all_async_aliases = [
    # Early definitions (lines 59-63, inside try block)
    "create_booking_async", "end_booking_async", "cancel_booking_async",
    "fetch_console_status_async", "fetch_games_async",
    # Late definitions (lines 2638-2648)
    "fetch_members_async", "fetch_base_rate_async",
    "fetch_console_multiplier_async", "fetch_allowed_staff_ids_async",
    "fetch_wallet_mins_async", "fetch_balance_mins_async",
    "fetch_member_tier_async", "fetch_member_data_async",
    "fetch_promotions_cached_async", "fetch_food_menu_async",
    # async versions of other functions used by handlers
    "fetch_console_games_async", "get_consoles_with_game_async",
    "get_games_on_console_async", "add_console_game_async",
    "remove_console_game_async", "fetch_game_library_async",
]

# Check which ones are already in _handler_reexports
handler_start = content.find('_handler_reexports = [')
handler_end = content.find(']', handler_start)

# Get existing entries
existing_section = content[handler_start:handler_end]
for alias in all_async_aliases:
    if alias not in existing_section:
        # Insert before the closing bracket
        indent = '            '
        insert_line = f'{indent}"{alias}",\n{indent}'
        content = content[:handler_end] + insert_line + content[handler_end:]
        handler_end = content.find(']', handler_start)  # re-find after insertion
        print(f'Added: {alias}')
    else:
        print(f'Already present: {alias}')

# Also ensure these are set as AsyncMock (not MagicMock) in the auto-population
# The _handler_reexports for loop uses: if starts with cmd_/show_ → AsyncMock, else MagicMock
# We need async aliases to be AsyncMock
# Add explicit mocks after the auto-population section

# Find the "Ensure async mocks survive auto-population" section
ensure_idx = content.find('# ── Ensure async mocks survive auto-population ──')
if ensure_idx >= 0:
    # Add explicit AsyncMock assignments before this section
    async_mock_block = '\n    # ── Async re-export alias mocks ──\n'
    for alias in all_async_aliases:
        async_mock_block += f'    bot.{alias} = AsyncMock()\n'
    
    # Insert before the ensure section
    content = content[:ensure_idx] + async_mock_block + content[ensure_idx:]
    print('Added explicit AsyncMock assignments for all async aliases')

with open('/root/psvibe-sales-bot/tests/conftest.py', 'w') as f:
    f.write(content)
print('conftest.py: UPDATED')

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
    print(f'STOCK_PIN: already fixed or pattern not found')

print('ALL DONE')
