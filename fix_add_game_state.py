#!/usr/bin/env python3
"""Add SALE_GAME_SELECT state to BotState enum + exports + sales flow."""
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    lines = f.readlines()

# 1. Add to BotState enum: insert after SESSION_SHORTFALL = 64
for i, line in enumerate(lines):
    if 'SESSION_SHORTFALL = 64' in line:
        lines.insert(i+1, '    SALE_GAME_SELECT = 154\n')
        print(f"Added to BotState at line {i+2}")
        break

# 2. Add SALE_GAME_SELECT to __all__ (the huge list)
# Find __all__ definition
all_start = None
all_end = None
for i, line in enumerate(lines):
    if line.strip().startswith("__all__ = [") or line.strip().startswith("__all__= ["):
        all_start = i
        # Find the end of __all__ (closing bracket)
        for j in range(i, min(i+300, len(lines))):
            if ']' in lines[j] and not lines[j].strip().startswith('#'):
                # Check if this is the closing of __all__
                # __all__ might be one long line
                if j == i:
                    # Single line __all__
                    lines[j] = lines[j].rstrip()
                    if not lines[j].endswith(']'):
                        lines[j] += ','
                    # Actually, let's find the proper spot to insert
                    pass
                all_end = j
                break
        break

# Simpler approach: just find 'SESSION_SHORTFALL' in __all__ line and add after it
for i, line in enumerate(lines):
    if i == all_start and all_start is not None:
        # The __all__ is a single long line
        if "'SESSION_SHORTFALL'" in line:
            lines[i] = line.replace("'SESSION_SHORTFALL'", "'SESSION_SHORTFALL', 'SALE_GAME_SELECT'")
            print(f"Added SALE_GAME_SELECT to __all__ at line {i+1}")
        elif 'SESSION_SHORTFALL' in line:
            lines[i] = line.replace("SESSION_SHORTFALL", "SESSION_SHORTFALL, SALE_GAME_SELECT")
            print(f"Added SALE_GAME_SELECT to __all__ at line {i+1} (no quotes)")
        break

# 3. Add SALE_GAME_SELECT constant export after the BotState enum
# Find SESSION_SHORTFALL = BotState... line
for i, line in enumerate(lines):
    if 'SESSION_SHORTFALL = BotState.SESSION_SHORTFALL' in line:
        lines.insert(i+1, 'SALE_GAME_SELECT = BotState.SALE_GAME_SELECT\n')
        print(f"Added export at line {i+2}")
        break

# 4. Add to imports in from bot import tuple
# Find where imports end (the closing paren of the import block)
in_import_block = False
for i, line in enumerate(lines):
    if 'from bot import (' in line or line.strip().startswith('from bot import (') or 'from bot import (' in line.replace(' ', '').replace('\\n',''):
        in_import_block = True
        continue
    if in_import_block:
        if ')' in line and line.strip() == ')':
            # Add SALE_GAME_SELECT before closing paren
            lines[i] = '    SALE_GAME_SELECT,\n)\n'
            print(f"Added to import block at line {i+1}")
            break

with open(filepath, 'w') as f:
    f.writelines(lines)

print("Done!")
