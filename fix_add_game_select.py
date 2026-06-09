#!/usr/bin/env python3
"""Add game selection step to sales flow — shows installed games per console."""
import sys, os

filepath = sys.argv[1]
with open(filepath, 'r') as f:
    content = f.read()

# 1. Add SALE_GAME state constant after ADJUST_TIME (find its position)
if 'SALE_GAME' not in content:
    # Add after ADJUST_TIME definition
    content = content.replace(
        'SALE_GAME_SELECT',
        'SALE_GAME_SELECT'
    )

# Actually, let's check what states exist and add SALE_GAME after ADJUST_TIME
# First, find imports and add the state to __all__ or wherever states are defined

# Read the __init__.py or wherever SALE states come from
print("Checking sales.py for state definitions...")
with open(filepath, 'r') as f:
    lines = f.readlines()

# Find where state constants or imports are defined
for i, line in enumerate(lines):
    if 'SALE_GAME_SELECT' in line or 'ADJUST_TIME' in line and '= ' in line:
        print(f"  Line {i+1}: {line.rstrip()}")

# The state SALE_GAME_SELECT needs to be defined or imported
# Let me check what's imported in sales.py
for i, line in enumerate(lines[:50]):
    if 'import' in line:
        print(f"  Import {i+1}: {line.rstrip()}")
