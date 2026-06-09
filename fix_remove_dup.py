#!/usr/bin/env python3
"""Remove the misplaced duplicate normalization line."""
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'cid.replace' in line and 'normalize' in line:
        # Check if the NEXT line has bk_console (means this is misplaced)
        for j in range(i+1, min(i+3, len(lines))):
            if 'bk_console' in lines[j]:
                print(f"Removing misplaced line {i+1}: {line.rstrip()}")
                del lines[i]
                with open(filepath, 'w') as f:
                    f.writelines(lines)
                print("Done")
                sys.exit(0)

print("No misplaced line found")
