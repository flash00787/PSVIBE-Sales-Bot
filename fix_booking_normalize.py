#!/usr/bin/env python3
"""Fix: Add console_id space normalization in prompt_book_game."""
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    lines = f.readlines()

target_line = '    cid       = context.user_data.get("bk_console", "")\n'

# Find the target
for i, line in enumerate(lines):
    if line == target_line and i > 935:
        # Check if normalization already exists after it
        if i + 1 < len(lines) and 'replace' in lines[i+1] and ' ' in lines[i+1]:
            print(f"Normalization already at line {i+2}")
            break
        # Insert after the cid assignment
        lines.insert(i+1, '    cid = cid.replace(" ", "")  # normalize spaces in console ID\n')
        print(f"Added normalization at line {i+2}")
        break

# Also remove any lingering misplaced normalization line
for i, line in enumerate(lines):
    if 'cid.replace' in line and 'normalize' in line and 'bk_console' not in line:
        # Check if this is before the actual cid assignment (wrong position)
        for j in range(max(0, i-5), i):
            if 'bk_console' in lines[j]:
                break
        else:
            # This is BEFORE the cid assignment - remove it
            # Check if the NEXT line is the actual cid assignment
            if i+1 < len(lines) and 'bk_console' in lines[i+1]:
                print(f"Removing misplaced normalization at line {i+1}")
                del lines[i]
                break

with open(filepath, 'w') as f:
    f.writelines(lines)

print("Done!")
