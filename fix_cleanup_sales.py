#!/usr/bin/env python3
"""Remove SALE_GAME_SELECT feature from sales.py - revert to original."""
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    c = f.read()

# 1. Remove unused import
c = c.replace('    get_games_on_console_async,\n', '')
print("1. Removed get_games_on_console_async import")

# 2. Remove SALE_GAME_SELECT import
c = c.replace('    SALE_GAME_SELECT,', '')
print("2. Removed SALE_GAME_SELECT import")

# 3. Remove prompt_game_select function (from def to before step_game_select)
marker1 = 'async def prompt_game_select(update: Update, context: ContextTypes.DEFAULT_TYPE):'
marker2 = 'async def step_game_select(update: Update, context: ContextTypes.DEFAULT_TYPE):'
marker3 = 'async def step_ds_console_in_session'

if marker1 in c:
    idx1 = c.index(marker1)
    idx2 = c.index(marker2)
    idx3 = c.index(marker3)
    # Remove from prompt_game_select to just before step_ds_console_in_session
    c = c[:idx1] + c[idx3:]
    print(f"3. Removed from prompt_game_select to step_ds_console_in_session")
else:
    print("3. prompt_game_select not found (already removed)")

with open(filepath, 'w') as f:
    f.write(c)

print("Done!")
