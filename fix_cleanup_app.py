#!/usr/bin/env python3
"""Remove SALE_GAME_SELECT from app.py."""
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    c = f.read()

# Remove state registration
old = '            SALE_GAME_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_select)],\n'
if old in c:
    c = c.replace(old, '')
    print("Removed state registration")
else:
    print("State registration not found as-is, checking...")
    # Alternative pattern
    if 'SALE_GAME_SELECT' in c:
        print("  SALE_GAME_SELECT still present but different format")

# Remove from imports
c = c.replace('    SALE_GAME_SELECT,\n', '')
c = c.replace('    SALE_GAME_SELECT,', '')
print("Cleaned imports")

with open(filepath, 'w') as f:
    f.write(c)

print("Done!")
